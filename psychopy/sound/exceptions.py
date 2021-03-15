#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Errors and warnings associated with audio recording and playback.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'AudioStreamError',
    'AudioFrequencyRangeError',
    'AudioUnsupportedSampleRateError',
    'AudioInvalidDeviceError',
    'AudioUnsupportedCodecError',
    'AudioInvalidCaptureDeviceError',
    'AudioInvalidPlaybackDeviceError'
]


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


if __name__ == "__main__":
    pass
