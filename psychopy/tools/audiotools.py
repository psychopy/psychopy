#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tools for working with audio data.

This module provides routines for saving/loading and manipulating audio samples.

"""

__all__ = [
    'array2wav',
    'wav2array',
    'audioClipSize',
    'SAMPLE_RATE_8kHz', 'SAMPLE_RATE_TELCOM_QUALITY',
    'SAMPLE_RATE_16kHz', 'SAMPLE_RATE_VOIP_QUALITY',
    'SAMPLE_RATE_44p1kHz', 'SAMPLE_RATE_CD_QUALITY',
    'SAMPLE_RATE_48kHz', 'SAMPLE_RATE_DVD_QUALITY',
    'SAMPLE_RATE_96kHz',
    'SAMPLE_RATE_192kHz'
]

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import os
import numpy as np
from scipy.io import wavfile

# pydub is needed for saving and loading MP3 files among others
_has_pydub = True
try:
    import pydub
except (ImportError, ModuleNotFoundError):
    _has_pydub = False

# Constants for common sample rates. Some are aliased to give the programmer an
# idea to the quality they would expect from each. It is recommended to only use
# these values since most hardware supports them for recording and playback.
#
SAMPLE_RATE_8kHz = SAMPLE_RATE_TELCOM_QUALITY = 8000
SAMPLE_RATE_16kHz = SAMPLE_RATE_VOIP_QUALITY = 16000
SAMPLE_RATE_44p1kHz = SAMPLE_RATE_CD_QUALITY = 44100
SAMPLE_RATE_48kHz = SAMPLE_RATE_DVD_QUALITY = 48000
SAMPLE_RATE_96kHz = 96000
SAMPLE_RATE_192kHz = 192000  # high-def


# needed for converting float to int16, not exported by __all__
MAX_16BITS_SIGNED = 1 << 15


def array2wav(filename, samples, freq=48000):
    """Write audio samples stored in an array to WAV file.

    Parameters
    ----------
    filename : str
        File name for the output.
    samples : ArrayLike
        Nx1 or Nx2 array of audio samples with values ranging between -1 and 1.
    freq : int or float
        Sampling frequency used to capture the audio samples in Hertz (Hz).
        Default is 48kHz (specified as `48000`) which is considered DVD quality
        audio.

    """
    # rescale
    clipData = np.asarray(samples * MAX_16BITS_SIGNED, dtype=np.int16)

    # write out file
    wavfile.write(filename, freq, clipData)


def wav2array(filename, normalize=True):
    """Read a WAV file and write samples to an array.

    Parameters
    ----------
    filename : str
        File name for WAV file to read.
    normalize : bool
        Convert samples to floating point format with values ranging between
        -1 and 1. If `False`, values will be kept in `int16` format. Default is
        `True` since normalized floating-point is the typical format for audio
        samples in PsychoPy.

    Returns
    -------
    samples : ArrayLike
        Nx1 or Nx2 array of samples.
    freq : int
        Sampling frequency for playback specified by the audio file.

    """
    fullpath = os.path.abspath(filename)  # get the full path

    if not os.path.isfile(fullpath):  # check if the file exists
        raise FileNotFoundError(
            "Cannot find WAV file `{}` to open.".format(filename))

    # read the file
    freq, samples = wavfile.read(filename, mmap=False)

    # transpose samples
    samples = samples[:, np.newaxis]

    # check if we need to normalize things
    if normalize:
        samples = np.asarray(
            samples / MAX_16BITS_SIGNED, dtype=np.float32)

    return samples, int(freq)


def audioClipSize(duration=1.0, freq=SAMPLE_RATE_48kHz):
    """Estimate the memory footprint of an audio clip of given duration. Assumes
    that data is stored in 32-bit floating point format.

    Parameters
    ----------
    duration : float
        Length of the clip in seconds.
    freq : int
        Sampling frequency in Hz.

    Returns
    -------
    int
        Estimated number of bytes.

    """
    # Right now we are just computing for single precision floats, we can expand
    # this to other types in the future.

    sizef32 = 32  # duh

    return int(duration * freq * sizef32)


if __name__ == "__main__":
    pass

