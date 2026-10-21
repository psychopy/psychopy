from psychopy.sound._base import apodize, HammingWindow
import numpy as np
import pytest

"""
We need to test that the block-by-block hamming (`HammingWindow.nextBlock`,
used by backends that stream sounds in blocks, i.e. sounddevice) works the same
as the (simpler) method of applying the window to the initial complete array
(using the apodize function)
"""

sampleRate = 44100
secs = 0.3
nSamples = int(secs * sampleRate)
winSecs = 0.005  # 5 ms, as the sounddevice backend uses for sounds this long


def _blockwiseEnvelope(win, blockSize):
    """Assemble the full envelope from `win.nextBlock`, as a streaming backend
    would request it, with a short final block if blockSize doesn't divide the
    sound.
    """
    blocks = []
    startSample = 0
    while startSample < nSamples:
        thisSize = min(blockSize, nSamples - startSample)
        block = win.nextBlock(startSample / sampleRate, thisSize)
        if block is None:  # in the middle of the sound, so no window
            block = np.ones(thisSize)
        blocks.append(np.ravel(block))
        startSample += thisSize
    return np.concatenate(blocks)


# block sizes that do and don't divide the window and sound lengths, and
# sizes larger than the window
@pytest.mark.parametrize("blockSize", [64, 100, 128, 220, 441, 512, 4096])
def test_HammingSmallBlock(blockSize):
    win = HammingWindow(winSecs=winSecs, soundSecs=secs, sampleRate=sampleRate)
    blockwise = _blockwiseEnvelope(win, blockSize)
    assert len(blockwise) == nSamples

    # the window applied in one go to the complete array
    expected = np.ones(nSamples)
    expected[:win.winSamples] = win.startWindow
    expected[win.finalWinStart:] = win.endWindow
    np.testing.assert_allclose(blockwise, expected)

    # and close to apodize, whose Hanning window differs only by a sample
    np.testing.assert_allclose(
        blockwise, apodize(np.ones(nSamples), sampleRate), atol=0.005)
