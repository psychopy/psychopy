#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Audio recording using a microphone.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['Microphone']

from . import _backends
import numpy as np


class AudioClip(object):
    """Class for storing audio clip data.
    """
    def __init__(self, samples, sampleRateHz=48000):
        self._samples = np.asarray(samples)
        self._sampleRateHz = sampleRateHz

        # the duration of the audio clip
        self._duration = len(self.samples) / float(self.sampleRateHz)

    @property
    def duration(self):
        """The duration of the audio in seconds (`float`)."""
        return self._duration

    @property
    def samples(self):
        """Nx1 array of audio samples (`~numpy.ndarray`)."""
        return self.samples

    @samples.setter
    def samples(self, value):
        self._samples = np.asarray(value)

        # recompute duration after updating samples
        self._duration = len(self._samples) / float(self._sampleRateHz)

    @property
    def sampleRateHz(self):
        """Sample rate of the audio clip in Hz (`int`). Should be the same
        value as the rate `samples` was captured at.

        """
        return self._sampleRateHz

    @sampleRateHz.setter
    def sampleRateHz(self, value):
        self._sampleRateHz = int(value)
        # recompute duration after updating sample rate
        self._duration = len(self._samples) / float(self._sampleRateHz)

    def save(self, filePath, fmt='wav'):
        """Save an audio clip to file.
        """
        pass


class Microphone(object):
    """Class for recording audio from a microphone.

    Parameters
    ----------
    sampleRateHz : int
        Sampling rate for audio recording in Hertz (Hz). By default, 48kHz
        (``sampleRateHz=480000``) is used which is adequate for most consumer
        grade microphones (headsets and built-in). Sampling rates should be at
        least greater than 20kHz to minimize distortion perceptible to humans
        due to aliasing.
    audioCaptureLib : str or None
        Library to use for capturing audio from the microphone. If `None`, the
        library specified in preferences in used.

    """
    def __init__(self, sampleRateHz=48000, audioCaptureLib='ptb'):

        self._audioCaptureLib = audioCaptureLib

        # create the backend instance
        cls = self._getBackend()  # unbound class
        self._backend = cls(sampleRateHz=sampleRateHz)

    def _getBackend(self):
        """Initialize the backend to use for microphone recording.

        Returns
        -------
        :class:`~psychopy.sound.microphone._backends.BaseMicrophoneInterface`
            Microphone interface class.

        """
        # get the backend to use
        clsName = _backends.audioInputLib[self._audioCaptureLib]
        cls = getattr(_backends, clsName)

        #  make sure the backend is a sub-class of `BaseMicrophoneInterface`
        assert issubclass(cls, _backends.BaseMicrophoneInterface)

        return cls

    def start(self):
        self._backend.start()

    def stop(self):
        self._backend.stop()

    def getAudioData(self):
        """Get audio data."""
        return self._backend.getAudioData()


if __name__ == "__main__":
    pass
