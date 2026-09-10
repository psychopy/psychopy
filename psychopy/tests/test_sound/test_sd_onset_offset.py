"""Sub-block (sample-accurate) onset scheduling for the SoundDevice backend.

Regression test for the fix that places a sound's onset at the exact sample
within an output block, rather than quantising it to the block boundary
(which added up to one blockSize of onset jitter).

The test drives the real ``_SoundStream._callback`` and ``SoundDeviceSound.
_nextBlock`` with synthetic PortAudio timing info, so it needs no audio device
and is safe in headless CI. We build the objects with ``object.__new__`` to
avoid opening a hardware stream.
"""
import types
import numpy as np
import pytest

sd = pytest.importorskip("sounddevice")
pytest.importorskip("soundfile")

import psychopy.sound.backend_sounddevice as bsd
from psychopy.sound.backend_sounddevice import _SoundStream, SoundDeviceSound


SR = 44100
BLOCK = 64
OFFSET = 20          # requested onset, in samples, inside the first block
N = 10 * BLOCK       # long enough that the sound never ends during the test
NBLOCKS = 4


def _make_sound(request_dac_time):
    """A real SoundDeviceSound playing a known ramp array, no device opened."""
    snd = object.__new__(SoundDeviceSound)
    # name/autoLog first: stereo, t, volume ... are logged attributeSetters that
    # call logAttrib(obj.name) on assignment (the real __init__ sets these first).
    snd.autoLog = False
    snd.name = "freqtest_sound"
    snd.sourceType = "array"
    snd.sndArr = ((np.arange(N) + 1) / N).reshape(N, 1)   # distinct, all nonzero
    snd.stereo = -1
    snd.multichannel = True            # → _nextBlock returns 2-D blocks
    snd.preBuffer = -1
    snd.t = 0.0
    snd.sampleRate = SR
    snd.blockSize = BLOCK
    snd.duration = N / SR
    snd._hammingWindow = None
    snd._isPlaying = True
    snd.volume = 1.0
    snd._tSoundRequestPlay = request_dac_time
    # attributes touched by the real _EOS()->stop() path (end-of-stream test)
    snd.loops = 0
    snd._loopsFinished = 0
    snd._isFinished = False
    snd._isStarted = True
    snd.sndFile = None
    snd.streamLabel = "freqtest"
    return snd


def _make_stream(sound):
    stream = object.__new__(_SoundStream)
    stream.sampleRate = SR
    stream.channels = 1
    stream.blockSize = BLOCK
    stream.frameN = 0
    stream.takeTimeStamp = False
    stream.sounds = [sound]
    return stream


def _run(dac0, request_dac_time):
    sound = _make_sound(request_dac_time)
    stream = _make_stream(sound)
    out = []
    for i in range(NBLOCKS):
        tp = types.SimpleNamespace(
            currentTime=dac0 + i * BLOCK / SR,
            inputBufferAdcTime=0.0,
            outputBufferDacTime=dac0 + i * BLOCK / SR,
        )
        toSpk = np.zeros((BLOCK, 1), dtype="float32")
        stream._callback(toSpk, BLOCK, tp, 0)
        out.append(toSpk.copy())
    return np.vstack(out)[:, 0], sound


def test_onset_lands_on_exact_sample():
    dac0 = 5.0
    out, _ = _run(dac0, request_dac_time=dac0 + OFFSET / SR)
    # onset is at the requested sample, not quantised to the block boundary
    assert int(np.flatnonzero(out)[0]) == OFFSET
    assert np.allclose(out[:OFFSET], 0.0)


def test_first_partial_block_is_gapless_and_not_truncated():
    """The partial first block must not be mistaken for end-of-stream, and the
    time cursor must advance by the samples produced (no dropped samples)."""
    dac0 = 5.0
    out, sound = _run(dac0, request_dac_time=dac0 + OFFSET / SR)
    src = sound.sndArr[:, 0]
    played = out[OFFSET:]                       # everything after the onset
    assert np.allclose(played, src[:len(played)])   # contiguous, no gap
    assert sound in [sound]                       # not removed after partial block


@pytest.mark.parametrize("offset", [0, 1, 13, BLOCK - 1])
def test_onset_offset_various_phases(offset):
    dac0 = 5.0
    out, _ = _run(dac0, request_dac_time=dac0 + offset / SR)
    assert int(np.flatnonzero(out)[0]) == offset


def test_full_sound_reconstructed_through_eos(monkeypatch):
    """Run a short sound to completion: every source sample must be emitted
    (guards the samplesLeft round() fix — a bare int() drops the last sample
    once the onset offset pushes the time cursor off the sample grid)."""
    sr, block, offset = SR, BLOCK, 20
    n = 5 * block
    dac0 = 5.0
    sound = object.__new__(SoundDeviceSound)
    sound.autoLog = False; sound.name = "freqtest_sound"   # before logged setters
    sound.sourceType = "array"
    sound.sndArr = ((np.arange(n) + 1) / n).reshape(n, 1)
    sound.stereo = -1; sound.multichannel = True; sound.preBuffer = -1
    sound.t = 0.0; sound.sampleRate = sr; sound.blockSize = block
    sound.duration = n / sr; sound._hammingWindow = None; sound._isPlaying = True
    sound.volume = 1.0; sound._tSoundRequestPlay = dac0 + offset / sr
    sound.loops = 0; sound._loopsFinished = 0; sound._isFinished = False
    sound._isStarted = True; sound.sndFile = None; sound.streamLabel = "freqtest"

    stream = _make_stream(sound)
    monkeypatch.setattr(bsd, "streams", {"freqtest": stream})

    nblocks = int(np.ceil((offset + n) / block)) + 1
    out = []
    for i in range(nblocks):
        tp = types.SimpleNamespace(currentTime=dac0 + i * block / sr,
                                   inputBufferAdcTime=0.0,
                                   outputBufferDacTime=dac0 + i * block / sr)
        toSpk = np.zeros((block, 1), dtype="float32")
        stream._callback(toSpk, block, tp, 0)
        out.append(toSpk.copy())
    out = np.vstack(out)[:, 0]

    assert np.allclose(out[offset:offset + n], sound.sndArr[:, 0])  # every sample emitted
    assert sound not in stream.sounds                               # removed at EOS
