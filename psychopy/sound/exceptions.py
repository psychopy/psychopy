#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Errors and warnings associated with audio recording and playback.
"""

from ..exceptions import SoundFormatError, DependencyError

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'AudioStreamError',
    'AudioFrequencyRangeError',
    'AudioUnsupportedSampleRateError',
    'AudioInvalidDeviceError',
    'AudioUnsupportedCodecError',
    'AudioInvalidCaptureDeviceError',
    'AudioInvalidPlaybackDeviceError',
    'AudioRecordingBufferFullError',
    'RecognizerAPICredentialsError',
    'RecognizerLanguageNotSupportedError',
    'RecognizerEngineNotFoundError',
    'SoundFormatError',
    'DependencyError'
]


# ------------------------------------------------------------------------------
# Audio hardware and software exceptions
#

class AudioUnsupportedCodecError(Exception):
    """Error raise when trying to save or load and unsupported audio
    codec/format.

    """
    pass


class AudioStreamError(Exception):
    """Error raised when there is a problem during audio recording/streaming."""
    pass


class AudioFrequencyRangeError(Exception):  # might transform to a warning
    """Error raised when generating a tone with a frequency outside the audible
    range for humans (20Hz to 20kHz).

    """
    pass


class AudioUnsupportedSampleRateError(Exception):
    """Error raised when the sampling rate is not supported by the hardware.

    """
    pass


class AudioInvalidDeviceError(Exception):
    """Error raised when the audio device configuration does not match any
    supported configuration.

    """
    pass


class AudioInvalidCaptureDeviceError(AudioInvalidDeviceError):
    """Error raised when the audio device cannot be used for capture (i.e. not
    a microphone).

    """
    pass


class AudioInvalidPlaybackDeviceError(AudioInvalidDeviceError):
    """Error raised when the audio device is not suitable for playback.

    """
    pass


class AudioRecordingBufferFullError(Exception):
    """Error raised when the recording buffer is full."""
    pass


# ------------------------------------------------------------------------------
# Transcriber exceptions
#

class RecognizerAPICredentialsError(ValueError):
    """Raised when a given speech recognition is being given improper
    credentials (i.e. API key is invalid or not found).
    """


class RecognizerLanguageNotSupportedError(ValueError):
    """Raised when the specified language is not supported by the engine. If you
    get this, you need to install the appropriate language support or select
    another language.
    """


class RecognizerEngineNotFoundError(ModuleNotFoundError):
    """Raised when the specified recognizer cannot be found. Usually get this
    error if the required packages are not installed for a recognizer that is
    invoked.
    """


if __name__ == "__main__":
    pass
