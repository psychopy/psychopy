#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Audio recording using a microphone.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['Microphone']

from . import _backends


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
