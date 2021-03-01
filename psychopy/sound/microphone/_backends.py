#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Audio recording using a microphone.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).


from __future__ import absolute_import, division, print_function

import sys
import os
import time
import re
import weakref

from psychopy import prefs, logging, exceptions
from psychopy.constants import (STARTED, PAUSED, FINISHED, STOPPING,
                                NOT_STARTED)
from psychopy.exceptions import SoundFormatError, DependencyError

try:
    from psychtoolbox import audio
    import psychtoolbox as ptb
except Exception:
    raise DependencyError("psychtoolbox audio failed to import")
try:
    import soundfile as sf
except Exception:
    raise DependencyError("soundfile not working")

import numpy as np

# used to register backends for the (future) plugin system
audioInputLib = {
    'ptb': 'PTBMicrophone'
}


class BaseMicrophoneInterface(object):
    """Base class for microphone input backends. Defines the API common to all
    microphone recording backends.
    """
    audioInputLib = None  # identify the backend for plugins

    def __init__(self):
        self._statusFlag = NOT_STARTED
        self._audioData = dict()  # store previously recorded audio

    @property
    def isRecording(self):
        """`True` if we currently recording audio (`bool`)."""
        return self._statusFlag == STARTED

    @property
    def status(self):
        """Symbolic constant for recording status (`int`)."""
        return self._statusFlag

    def start(self):
        """Start an audio recording."""
        pass

    def stop(self):
        """Stop recording audio."""
        pass


class PTBMicrophone(BaseMicrophoneInterface):
    """Class for the Psychtoolbox microphone input.

    Parameters
    ----------
    recBufferSecs : float
        Allocate an internal buffer large enough to store an audio recording of
        a given number of seconds.
    sampleRateHz : int
        Sampling rate for audio recording in Hertz (Hz). By default, 48kHz
        (``sampleRateHz=480000``) is used which is adequate for most consumer
        grade microphones (headsets and built-in). Sampling rates should be at
        least greater than 20kHz to minimize distortion perceptible to humans
        due to aliasing.

    """
    audioInputLib = 'ptb'

    def __init__(self, recBufferSecs=10.0, sampleRateHz=48000):
        super(BaseMicrophoneInterface, self).__init__(self)

        # internal recording buffer size in seconds
        assert isinstance(recBufferSecs, (float, int))
        self._recBufferSecs = float(recBufferSecs)

        # PTB specific stuff (for now, might move to base class)
        assert isinstance(sampleRateHz, (int, float))
        self._sampleRateHz = int(sampleRateHz)
        self._mode = 2
        self._channels = 2

        # this can only be set after initialization
        self._stopTime = None   # optional, stop time to end recording

        # handle for the recording stream
        self._recording = audio.Stream(
            mode=self._mode,
            freq=self._sampleRateHz,
            channels=self._channels)

        # pre-allocate recording buffer
        self._recording.get_audio_data(self._recBufferSecs)

        # status flag
        self._statusFlag = NOT_STARTED

    @property
    def recordingBufferSecs(self):
        """Size of the internal audio storage buffer in seconds (`float`).
        Cannot be set while recording.

        """
        return self._recBufferSecs

    @property
    def stopTime(self):
        """Duration of the audio recording (`float`). Cannot be set while a
        recording is in progress.

        """
        return self._stopTime

    @stopTime.setter
    def stopTime(self, value):
        assert isinstance(value, (float, int))
        self._stopTime = float(value)

    def start(self):
        """Start an audio recording.

        Calling this method will open a stream and begin capturing samples from
        the microphone.

        """
        # check if the stream has been
        if self._statusFlag == STARTED:  # raise warning, error, or ignore?
            pass

        assert self._recording is not None  # must have a handle
        self._recording.start(repetitions=0, stop_time=self._stopTime)
        self._statusFlag = STARTED  # recording has begun

    def stop(self):
        """Stop recording audio.

        Call this method to end an audio recording if in progress. This will
        close the audio stream.

        """
        self._recording.close()
        self._statusFlag = NOT_STARTED

    def getAudioData(self, clipName=None):
        """Get samples from a previous recording."""
        pass


if __name__ == "__main__":
    pass
