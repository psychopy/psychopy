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


def _make_sound(n=N, hamming=False, **kwargs):
    """A real SoundDeviceSound playing ``_ramp(n)``, no device opened."""
    return SoundDeviceSound(
        _ramp(n), sampleRate=SR, blockSize=BLOCK,
        speaker=SoundDeviceSpeakerDevice(name="test speaker"),
        hamming=hamming, autoLog=False, **kwargs)


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


@pytest.mark.parametrize("n, durSamples, nPlayed", [
    (2 * BLOCK, None, 2 * BLOCK),  # ends exactly on a block boundary
    (100, 100.6, 100),  # duration not a whole number of samples
    (100, 150, 100),    # duration longer than the array
    (200, 100.6, 100),  # ... and shorter than it: plays whole samples only
])
def test_sound_ends_cleanly_and_replays(n, durSamples, nPlayed):
    """Whatever the duration (set via secs and stopTime, in samples here), the
    sound must play ``nPlayed`` samples and end once: a second _EOS, or one
    fired before the time cursor advances, leaves t non-zero, so the next
    play() skips samples."""
    kwargs = {}
    if durSamples is not None:
        kwargs = dict(secs=durSamples / SR, stopTime=durSamples / SR)
    sound = _make_sound(n, **kwargs)

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
    ref = _make_sound(n, hamming=True, secs=n / SR)
    ref.play(log=False)
    expected = _render(ref, nblocks=_nblocksFor(n))[:n]
    assert expected[0] < _ramp(n)[0, 0]  # the window was applied

    sound = _make_sound(n, hamming=True, secs=n / SR)
    sound.play(when=onset / SR, log=False)
    out = _render(sound, nblocks=_nblocksFor(onset + n))
    assert np.allclose(out[onset:onset + n], expected)


def test_hanning_window_does_not_modify_source():
    """Applying the window must not scale the stored array in place, or each
    replay would apply the ramps again."""
    n = 60 * BLOCK
    sound = _make_sound(n, hamming=True, secs=n / SR)
    sound.play(log=False)
    first = _render(sound, nblocks=_nblocksFor(n))
    sound.play(log=False)
    second = _render(sound, nblocks=_nblocksFor(n))
    assert np.allclose(sound.sndArr, _ramp(n))
    assert np.allclose(first, second)
