"""Tests for the sounddevice backend of PsychoPy.
"""
import types
import numpy as np
import pytest

from psychopy.exceptions import DependencyError

# importorskip only catches ImportError, but a missing PortAudio/libsndfile
# raises OSError from sounddevice/soundfile, which the backend re-raises as
# DependencyError
try:
    import psychopy.sound.backend_sounddevice as bsd
except (ImportError, OSError, DependencyError) as err:
    pytest.skip("sounddevice backend unavailable: {}".format(err),
                allow_module_level=True)
import soundfile as sf  # importable once the backend is
from psychopy.sound.backend_sounddevice import SoundDeviceSound
from psychopy.hardware.speaker.speaker_sounddevice import \
    SoundDeviceSpeakerDevice


SR = 44100
BLOCK = 64
OFFSET = 20          # requested onset, in samples, inside the first block
N = 10 * BLOCK       # long enough that the sound never ends during the test
NBLOCKS = 4
NOW = 5.0            # the backend's (frozen) time.monotonic() during a test


@pytest.fixture(autouse=True)
def headless(monkeypatch):
    """No audio device, a private stream registry and a frozen backend clock."""
    monkeypatch.setattr(bsd, "travisCI", True)
    monkeypatch.setattr(bsd, "streams", bsd._StreamsDict())
    # SoundDeviceSound requires a speaker of the backend resolved from prefs
    monkeypatch.setattr(bsd.SpeakerDevice, "backend", "sounddevice")
    # stub only the backend's reference to the time module, not time itself
    monkeypatch.setattr(bsd, "time", types.SimpleNamespace(monotonic=lambda: NOW))


def _ramp(n):
    """n distinct, nonzero samples, so any gap, repeat or shift is visible."""
    return ((np.arange(n) + 1) / n).reshape(n, 1)


def _new_sound(value, hamming=False, **kwargs):
    """A real SoundDeviceSound playing ``value``, no device opened."""
    return SoundDeviceSound(
        value, blockSize=BLOCK,
        speaker=SoundDeviceSpeakerDevice(name="test speaker"),
        hamming=hamming, autoLog=False, **kwargs)


def _make_sound(n=N, **kwargs):
    """A real SoundDeviceSound playing ``_ramp(n)``, no device opened."""
    return _new_sound(_ramp(n), sampleRate=SR, **kwargs)


def _render(sound, nblocks=NBLOCKS, dac0=NOW, jitter=None):
    """Run the sound's stream callback for ``nblocks`` blocks, the first
    starting at DAC time ``dac0``. ``jitter`` maps a block index to how many
    seconds early PortAudio's ``outputBufferDacTime`` estimate is for that
    block. Returns the first output channel."""
    stream = sound.stream
    jitter = jitter or {}
    out = []
    for i in range(nblocks):
        dac = dac0 + i * BLOCK / SR - jitter.get(i, 0.0)
        tp = types.SimpleNamespace(currentTime=dac, inputBufferAdcTime=0.0,
                                   outputBufferDacTime=dac)
        toSpk = np.zeros((BLOCK, stream.channels), dtype="float32")
        stream._callback(toSpk, BLOCK, tp, 0)
        out.append(toSpk.copy())
    return np.vstack(out)[:, 0]


def _nblocksFor(nsamples):
    """Enough blocks to play ``nsamples`` to the end, plus one."""
    return int(np.ceil(nsamples / BLOCK)) + 1


@pytest.mark.parametrize("offset", [0, 1, 13, OFFSET, BLOCK - 1])
def test_onset_lands_on_exact_sample(offset):
    sound = _make_sound()
    sound.play(when=offset / SR, log=False)
    out = _render(sound)
    # onset is at the requested sample, not quantised to the block boundary
    assert int(np.flatnonzero(out)[0]) == offset
    assert np.allclose(out[:offset], 0.0)


def test_first_partial_block_is_gapless_and_not_truncated():
    """The partial first block must not be mistaken for end-of-stream, and the
    time cursor must advance by the samples produced (no dropped samples)."""
    sound = _make_sound()
    sound.play(when=OFFSET / SR, log=False)
    out = _render(sound)
    played = out[OFFSET:]                       # everything after the onset
    assert np.allclose(played, _ramp(N)[:len(played), 0])  # contiguous, no gap
    assert sound in sound.stream.sounds         # not removed after partial block


def test_full_sound_reconstructed_through_eos():
    """Run a short sound to completion: every source sample must be emitted
    (guards the samplesLeft fix — truncating (duration - t) drops the last
    sample once the onset offset pushes the time cursor off the sample grid)."""
    n = 5 * BLOCK
    sound = _make_sound(n)
    sound.play(when=OFFSET / SR, log=False)
    out = _render(sound, nblocks=_nblocksFor(OFFSET + n))

    assert np.allclose(out[OFFSET:OFFSET + n], _ramp(n)[:, 0])  # every sample
    assert np.allclose(out[OFFSET + n:], 0.0)                   # and no more
    assert sound not in sound.stream.sounds                     # removed at EOS


class _FakeWindow:
    """Stands in for a Window: ``getFutureFlipTime(clock='now')`` returns the
    delay until the next flip, as `Window.getFutureFlipTime` does."""

    def __init__(self, flipIn):
        self.flipIn = flipIn

    def getFutureFlipTime(self, targetTime=0, clock=None):
        return self.flipIn if clock == 'now' else 100.0 + self.flipIn


@pytest.mark.parametrize("offset", [0, 7, 41, BLOCK - 1])
def test_play_when_window_lands_on_flip_sample(offset):
    """``play(when=win)`` schedules the onset at the next flip time; the onset
    must land on that exact sample, whatever its phase within the block."""
    flipIn = 0.0123
    sound = _make_sound()
    sound.play(when=_FakeWindow(flipIn), log=False)
    # the flip falls `offset` samples into the first block we render
    out = _render(sound, dac0=NOW + flipIn - offset / SR)
    assert int(np.flatnonzero(out)[0]) == offset


class _RacingWindow(_FakeWindow):
    """A window that runs an audio callback from inside ``play()``, while the
    flip time is being queried, as the audio thread can."""

    def __init__(self, flipIn, sound):
        super().__init__(flipIn)
        self.sound = sound
        self.early = []  # output of the callbacks that ran during play()

    def getFutureFlipTime(self, targetTime=0, clock=None):
        self.early.append(_render(self.sound, nblocks=1))
        return super().getFutureFlipTime(targetTime, clock)


def test_callback_during_play_does_not_start_early():
    """An audio callback that runs part way through ``play()`` must not see
    the sound as playing before its onset time has been set."""
    flipIn, offset = 0.0123, 7
    sound = _make_sound()
    win = _RacingWindow(flipIn, sound)
    sound.play(when=win, log=False)
    assert win.early and not np.any(win.early)  # silent until the flip

    out = _render(sound, dac0=NOW + flipIn - offset / SR)
    played = out[offset:]
    assert np.allclose(out[:offset], 0.0)
    assert np.allclose(played, _ramp(N)[:len(played), 0])  # from sample 0


@pytest.mark.parametrize("onset, jitter", [(BLOCK - 2, 80e-6), (40, 1e-3)])
def test_dac_jitter_after_onset_leaves_no_gap(onset, jitter):
    """Once the onset is placed, an early ``outputBufferDacTime`` estimate in a
    later block (normal PortAudio jitter) must not re-gate the sound and write
    silence into the middle of it."""
    sound = _make_sound()
    sound.play(when=onset / SR, log=False)
    out = _render(sound, jitter={1: jitter})
    played = out[onset:]
    assert np.allclose(played, _ramp(N)[:len(played), 0])  # contiguous, no gap


@pytest.mark.parametrize("n, secs, nPlayed", [
    (2 * BLOCK, None, 2 * BLOCK),  # whole clip, ending on a block boundary
    (100, -1, 100),          # -1 also plays the whole clip
    (100, 100.6 / SR, 100),  # duration not a whole number of samples
    (100, 150 / SR, 100),    # secs longer than the array: the whole clip
    (200, 100.6 / SR, 100),  # ... and shorter than it: whole samples only
])
def test_sound_ends_cleanly_and_replays(n, secs, nPlayed):
    """Whatever the duration set by secs, the sound must play ``nPlayed``
    samples and end once: a second _EOS, or one fired before the time cursor
    advances, leaves t non-zero, so the next play() skips samples."""
    sound = _make_sound(n, secs=secs)
    clipped = n / SR if secs in (None, -1) else min(n / SR, secs)
    assert sound.duration == pytest.approx(clipped)

    for _ in range(2):  # the replay must start from the first sample again
        sound.play(log=False)
        out = _render(sound, nblocks=_nblocksFor(n))
        assert np.allclose(out[:nPlayed], _ramp(n)[:nPlayed, 0])  # every sample
        assert np.allclose(out[nPlayed:], 0.0)                    # and no more
        assert sound.isFinished
        assert sound not in sound.stream.sounds


@pytest.mark.parametrize("n", [5 * BLOCK, 5 * BLOCK + 17])
def test_next_block_ends_without_stream(n):
    """Pulling blocks straight from ``_nextBlock`` (as test_hamming does) must
    reach the end of the sound, including when it ends on a block boundary."""
    sound = _make_sound(n)
    sound.play(log=False)
    blocks = []
    for _ in range(_nblocksFor(n) + 1):
        blocks.append(sound._nextBlock())
        if not sound.isPlaying:  # the block that ends the sound is still data
            break
    assert not sound.isPlaying
    assert np.allclose(np.vstack(blocks)[:, 0], _ramp(n)[:, 0])


@pytest.mark.parametrize("onset", [1, 4, 9, OFFSET, BLOCK - 1])
def test_hanning_window_independent_of_onset_phase(onset):
    """The onset/offset ramps must line up with the data whatever the onset's
    phase within the block, i.e. match the same sound started on a block
    boundary. Onsets 4 and 9 put the time cursor fractionally below a whole
    sample inside the start ramp (e.g. 59.99999 samples), which truncating it
    would place a sample early."""
    n = 60 * BLOCK  # long enough for the full 5 ms (220 sample) ramps
    ref = _make_sound(n, hamming=True)
    ref.play(log=False)
    expected = _render(ref, nblocks=_nblocksFor(n))[:n]
    assert expected[0] < _ramp(n)[0, 0]  # the window was applied

    sound = _make_sound(n, hamming=True)
    sound.play(when=onset / SR, log=False)
    out = _render(sound, nblocks=_nblocksFor(onset + n))
    assert np.allclose(out[onset:onset + n], expected)


def test_hanning_window_does_not_modify_source():
    """Applying the window must not scale the stored array in place, or each
    replay would apply the ramps again."""
    n = 60 * BLOCK
    sound = _make_sound(n, hamming=True)
    sound.play(log=False)
    first = _render(sound, nblocks=_nblocksFor(n))
    sound.play(log=False)
    second = _render(sound, nblocks=_nblocksFor(n))
    assert np.allclose(sound.sndArr, _ramp(n))
    assert np.allclose(first, second)


@pytest.mark.parametrize("n", [2 * BLOCK, 100])
def test_loops_play_back_to_back(n):
    """loops=N plays the sound N + 1 times with no gap between repeats, whether
    or not a repeat ends on a block boundary, then finishes."""
    loops = 2
    nPlayed = (loops + 1) * n
    sound = _make_sound(n, loops=loops)
    sound.play(when=OFFSET / SR, log=False)
    out = _render(sound, nblocks=_nblocksFor(OFFSET + nPlayed))
    assert np.allclose(out[OFFSET:OFFSET + nPlayed],
                       np.tile(_ramp(n)[:, 0], loops + 1))
    assert np.allclose(out[OFFSET + nPlayed:], 0.0)
    assert sound.isFinished
    assert sound not in sound.stream.sounds


def test_loop_forever_shorter_than_a_block():
    """loops=-1 keeps repeating, even a sound shorter than one block."""
    n = BLOCK // 3 + 1
    sound = _make_sound(n, loops=-1)
    sound.play(log=False)
    out = _render(sound, nblocks=10)
    reps = len(out) // n + 1
    assert np.allclose(out, np.tile(_ramp(n)[:, 0], reps)[:len(out)])
    assert sound.isPlaying
    assert sound in sound.stream.sounds


def test_replay_clears_finished():
    """Playing a finished sound again clears isFinished while it plays (Builder
    stops a sound as soon as isFinished is true) and plays all its loops."""
    n = 100
    sound = _make_sound(n)
    for _ in range(2):
        sound.play(loops=1, log=False)
        assert not sound.isFinished
        out = _render(sound, nblocks=_nblocksFor(2 * n))
        assert np.allclose(out[:2 * n], np.tile(_ramp(n)[:, 0], 2))
        assert np.allclose(out[2 * n:], 0.0)
        assert sound.isFinished


def test_stop_resets_loop_count():
    """Stopping part way through the loops means the next play() gets them all
    again, not just those that were left."""
    n = 100
    sound = _make_sound(n, loops=1)
    sound.play(log=False)
    _render(sound, nblocks=2)  # into the second repeat
    sound.stop()
    sound.play(log=False)
    out = _render(sound, nblocks=_nblocksFor(2 * n))
    assert np.allclose(out[:2 * n], np.tile(_ramp(n)[:, 0], 2))
    assert np.allclose(out[2 * n:], 0.0)


def test_pause_then_play_resumes():
    """play() after pause() puts the sound back in the stream and carries on
    from where it was paused."""
    sound = _make_sound()
    sound.play(log=False)
    first = _render(sound, nblocks=2)
    sound.pause()
    assert np.allclose(_render(sound, nblocks=2), 0.0)  # silent while paused
    sound.play(log=False)
    second = _render(sound, nblocks=2)
    assert np.allclose(np.concatenate([first, second]), _ramp(N)[:4 * BLOCK, 0])


@pytest.mark.parametrize("restart", ["seek", "stop"])
def test_pause_then_restart_from_beginning(restart):
    """A paused sound can be sent back to the start: by seek(0), as Builder does
    between Routines (pause() at the end of one, seek(0) at the start of the
    next), or by stop()."""
    sound = _make_sound()
    sound.play(log=False)
    _render(sound, nblocks=2)
    sound.pause()
    if restart == "seek":
        sound.seek(0)
    else:
        sound.stop()
    sound.play(log=False)
    out = _render(sound)
    assert np.allclose(out, _ramp(N)[:len(out), 0])


def test_start_does_not_print(capsys):
    _make_sound().start()
    assert capsys.readouterr().out == ""


M = 1000  # samples in the test sound file


@pytest.fixture
def rampFile(tmp_path):
    """A mono WAV file holding ``_ramp(M)``, stored losslessly as floats."""
    path = tmp_path / "ramp.wav"
    sf.write(str(path), _ramp(M)[:, 0].astype("float32"), SR, subtype="FLOAT")
    return str(path)


@pytest.mark.parametrize("preBuffer", [0, -1])  # streamed, or loaded up front
@pytest.mark.parametrize("start, stop, end", [
    (300, 700, 700),    # a snippet from the middle
    (300, None, M),     # from startTime to the end of the file
    (0, 700, 700),      # from the start to stopTime
    (300, 2 * M, M),    # stopTime beyond the end of the file
])
def test_file_snippet_plays_and_replays(rampFile, preBuffer, start, stop, end):
    """startTime/stopTime select samples ``start:end`` of the file, on every
    play: t counts from the start of the snippet, not of the file."""
    kwargs = dict(startTime=start / SR)
    if stop is not None:
        kwargs["stopTime"] = stop / SR
    sound = _new_sound(rampFile, preBuffer=preBuffer, **kwargs)
    n = end - start
    assert sound.duration * SR == pytest.approx(n)  # clipped to the file
    assert sound.t == 0

    for _ in range(2):  # the replay must play the same snippet again
        sound.play(log=False)
        out = _render(sound, nblocks=_nblocksFor(n))
        assert np.allclose(out[:n], _ramp(M)[start:end, 0])
        assert np.allclose(out[n:], 0.0)
        assert sound.isFinished


def test_streamed_file_snippet_loops(rampFile):
    """Each repeat of a looped, streamed snippet goes back to startTime, not
    to the start of the file."""
    start, stop = 300, 700
    n = stop - start
    sound = _new_sound(rampFile, preBuffer=0, loops=1,
                       startTime=start / SR, stopTime=stop / SR)
    sound.play(log=False)
    out = _render(sound, nblocks=_nblocksFor(2 * n))
    assert np.allclose(out[:2 * n], np.tile(_ramp(M)[start:stop, 0], 2))
    assert np.allclose(out[2 * n:], 0.0)
    assert sound.isFinished


@pytest.mark.parametrize("preBuffer", [0, -1])
def test_secs_cuts_file_snippet_short(rampFile, preBuffer):
    """secs shorter than a file snippet cuts it short, streamed or not."""
    start, stop, nSecs = 300, 700, 100
    sound = _new_sound(rampFile, preBuffer=preBuffer, secs=nSecs / SR,
                       startTime=start / SR, stopTime=stop / SR)
    assert sound.duration * SR == pytest.approx(nSecs)
    sound.play(log=False)
    out = _render(sound, nblocks=_nblocksFor(nSecs))
    assert np.allclose(out[:nSecs], _ramp(M)[start:start + nSecs, 0])
    assert np.allclose(out[nSecs:], 0.0)


@pytest.mark.parametrize("secs, duration", [(None, 0.5), (0.2, 0.2)])
def test_tone_length(secs, duration):
    """A tone is secs long, or 0.5 s if secs is None."""
    sound = _new_sound(440, sampleRate=SR, secs=secs)
    assert sound.duration == pytest.approx(duration, abs=1 / SR)


def test_tone_secs_minus_one_plays_until_stopped():
    sound = _new_sound(440, sampleRate=SR, secs=-1)
    assert sound.loops == -1
    sound.play(log=False)
    _render(sound, nblocks=_nblocksFor(sound.duration * SR))  # one full pass
    assert sound.isPlaying


def test_set_sound_without_hamming_drops_window():
    """setSound(..., hamming=False) must not keep the previous sound's window."""
    n = 5 * BLOCK
    sound = _make_sound(n, hamming=True)
    sound.setSound(_ramp(n), hamming=False, log=False)
    sound.play(log=False)
    out = _render(sound, nblocks=_nblocksFor(n))
    assert np.allclose(out[:n], _ramp(n)[:, 0])
