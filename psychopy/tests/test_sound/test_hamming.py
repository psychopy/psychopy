from psychopy.sound._base import apodize, HammingWindow
from psychopy.constants import FINISHED
from psychopy.exceptions import DependencyError
import numpy as np
import pytest

import psychopy.sound.backend_ptb as ptb

"""
We need to test that the new block-by-block hamming works the same as the
(simpler) method of adding the hamming window to the initial complete array
(using the apodize function)
"""

sampleRate = 44100
thisFreq = 100
secs = 0.3
nSamples = int(secs * sampleRate)
t = np.arange(0.0, 1.0, 1.0 / nSamples)*secs
sndArray = np.sin(t*2*np.pi*thisFreq)

plotting = False
if plotting:
    import matplotlib.pyplot as plt


@pytest.mark.needs_sound
def test_HammingSmallBlock():
    blockSize = 64
    snd1 = apodize(sndArray, sampleRate)  # is 5 ms
    sndDev = ptb.SoundPTB(thisFreq, sampleRate=sampleRate, secs=secs,
                          hamming=True, blockSize=blockSize)
    snd2 = []
    while sndDev.status != FINISHED:
        block = sndDev._nextBlock()
        snd2.extend(block)
    snd2 = np.array(snd2)

    if plotting:
        plt.subplot(2,1,1)
        plt.plot(snd1, 'b-')
        plt.plot(snd2, 'r--')
        plt.subplot(2,1,2)
        plt.plot(t, snd2[0:sampleRate*secs]-snd1)
        plt.show()
