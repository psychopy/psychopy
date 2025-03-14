#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tools for working with audio data.

This module provides routines for saving/loading and manipulating audio samples.

"""

__all__ = [
    'array2wav',
    'wav2array',
    'sinetone',
    'squaretone',
    'sawtone',
    'whiteNoise',
    'audioBufferSize',
    'sampleRateQualityLevels',
    'SAMPLE_RATE_8kHz', 'SAMPLE_RATE_TELCOM_QUALITY',
    'SAMPLE_RATE_16kHz', 'SAMPLE_RATE_VOIP_QUALITY', 'SAMPLE_RATE_VOICE_QUALITY',
    'SAMPLE_RATE_22p05kHz', 'SAMPLE_RATE_AM_RADIO_QUALITY',
    'SAMPLE_RATE_32kHz', 'SAMPLE_RATE_FM_RADIO_QUALITY',
    'SAMPLE_RATE_44p1kHz', 'SAMPLE_RATE_CD_QUALITY',
    'SAMPLE_RATE_48kHz', 'SAMPLE_RATE_DVD_QUALITY',
    'SAMPLE_RATE_96kHz',
    'SAMPLE_RATE_192kHz',
    'AUDIO_SUPPORTED_CODECS',
    'knownNoteNames', 'stepsFromA'
]

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import os
import numpy as np
from scipy.io import wavfile
from scipy import signal

# pydub is needed for saving and loading MP3 files among others
# _has_pydub = True
# try:
#     import pydub
# except (ImportError, ModuleNotFoundError):
#     _has_pydub = False


# note names mapped to steps from A, used in Sound stimulus and Component
stepsFromA = {
    'C': -9,
    'Csh': -8, 'C#': -8,
    'Dfl': -8, 'D♭': -8,
    'D': -7,
    'Dsh': -6, 'D#': -6,
    'Efl': -6, 'E♭': -6,
    'E': -5,
    'F': -4,
    'Fsh': -3, 'F#': -3,
    'Gfl': -3, 'G♭': -3,
    'G': -2,
    'Gsh': -1, 'G#': -1,
    'Afl': -1, 'A♭': -1,
    'A': +0,
    'Ash': +1, 'A#': +1,
    'Bfl': +1, 'B♭': +1,
    'B': +2,
    'Bsh': +2, 'B#': +2}
knownNoteNames = sorted(stepsFromA.keys())

# Constants for common sample rates. Some are aliased to give the programmer an
# idea to the quality they would expect from each. It is recommended to only use
# these values since most hardware supports them for recording and playback.
#
SAMPLE_RATE_8kHz = SAMPLE_RATE_TELCOM_QUALITY = 8000
SAMPLE_RATE_16kHz = SAMPLE_RATE_VOIP_QUALITY = SAMPLE_RATE_VOICE_QUALITY = 16000
SAMPLE_RATE_22p05kHz = SAMPLE_RATE_AM_RADIO_QUALITY = 22050
SAMPLE_RATE_32kHz = SAMPLE_RATE_FM_RADIO_QUALITY = 32000  # wireless headphones
SAMPLE_RATE_44p1kHz = SAMPLE_RATE_CD_QUALITY = 44100
SAMPLE_RATE_48kHz = SAMPLE_RATE_DVD_QUALITY = 48000
SAMPLE_RATE_96kHz = 96000
SAMPLE_RATE_192kHz = 192000  # high-def

# needed for converting float to int16, not exported by __all__
MAX_16BITS_SIGNED = 1 << 15

# Quality levels as strings and values. Used internally by the PsychoPy UI for
# dropdowns and preferences. Persons using PsychoPy as a library would typically
# use constants `SAMPLE_RATE_*` instead of looking up values in here.
#
# For voice recording applications, the recommended sample rate is `Voice`
# (16kHz) and should appear as the default option in preferences and UI
# dropdowns.
#
sampleRateQualityLevels = {
    0: (SAMPLE_RATE_8kHz, 'Telephone/Two-way radio (8kHz)'),
    1: (SAMPLE_RATE_16kHz, 'Voice (16kHz)'),  # <<< recommended for voice
    2: (SAMPLE_RATE_44p1kHz, 'CD Audio (44.1kHz)'),
    3: (SAMPLE_RATE_48kHz, 'DVD Audio (48kHz)'),  # <<< usually system default
    4: (SAMPLE_RATE_96kHz, 'High-Def (96kHz)'),
    5: (SAMPLE_RATE_192kHz, 'Ultra High-Def (192kHz)')
}
sampleRateLabels = {
    r[1]: r[0] for r in sampleRateQualityLevels.values()
}

# supported formats for loading and saving audio samples to file
try:
    import soundfile as sf
    AUDIO_SUPPORTED_CODECS = [s.lower() for s in sf.available_formats().keys()]
except ImportError:
    AUDIO_SUPPORTED_CODECS = []


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
    clipData = np.asarray(samples * (MAX_16BITS_SIGNED - 1), dtype=np.int16)

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
            samples / (MAX_16BITS_SIGNED - 1), dtype=np.float32)

    return samples, int(freq)


def sinetone(duration, freqHz, gain=0.8, sampleRateHz=SAMPLE_RATE_48kHz):
    """Generate audio samples for a tone with a sine waveform.

    Parameters
    ----------
    duration : float or int
        Length of the sound in seconds.
    freqHz : float or int
        Frequency of the tone in Hertz (Hz). Note that this differs from the
        `sampleRateHz`.
    gain : float
        Gain factor ranging between 0.0 and 1.0.
    sampleRateHz : int
        Samples rate of the audio for playback.

    Returns
    -------
    ndarray
        Nx1 array containing samples for the tone (single channel).

    """
    assert 0.0 <= gain <= 1.0   # check if gain range is valid

    nsamp = sampleRateHz * duration
    samples = np.arange(nsamp, dtype=np.float32)
    samples[:] = 2 * np.pi * samples[:] * freqHz / sampleRateHz
    samples[:] = np.sin(samples)

    if gain != 1.0:
        samples *= gain

    return samples.reshape(-1, 1)


def squaretone(duration, freqHz, dutyCycle=0.5, gain=0.8,
               sampleRateHz=SAMPLE_RATE_48kHz):
    """Generate audio samples for a tone with a square waveform.

    Parameters
    ----------
    duration : float or int
        Length of the sound in seconds.
    freqHz : float or int
        Frequency of the tone in Hertz (Hz). Note that this differs from the
        `sampleRateHz`.
    dutyCycle : float
        Duty cycle between 0.0 and 1.0.
    gain : float
        Gain factor ranging between 0.0 and 1.0.
    sampleRateHz : int
        Samples rate of the audio for playback.

    Returns
    -------
    ndarray
        Nx1 array containing samples for the tone (single channel).

    """
    assert 0.0 <= gain <= 1.0  # check if gain range is valid

    nsamp = sampleRateHz * duration
    samples = np.arange(nsamp, dtype=np.float32)
    samples[:] = 2 * np.pi * samples[:] * freqHz / sampleRateHz
    samples[:] = signal.square(samples, duty=dutyCycle)

    if gain != 1.0:
        samples *= gain

    return samples.reshape(-1, 1)


def sawtone(duration, freqHz, peak=0.5, gain=0.8,
            sampleRateHz=SAMPLE_RATE_48kHz):
    """Generate audio samples for a tone with a sawtooth waveform.

    Parameters
    ----------
    duration : float or int
        Length of the sound in seconds.
    freqHz : float or int
        Frequency of the tone in Hertz (Hz). Note that this differs from the
        `sampleRateHz`.
    peak : float
        Location of the peak between 0.0 and 1.0. If the peak is at 0.5, the
        resulting wave will be triangular. A value of 1.0 will cause the peak to
        be located at the very end of a cycle.
    gain : float
        Gain factor ranging between 0.0 and 1.0.
    sampleRateHz : int
        Samples rate of the audio for playback.

    Returns
    -------
    ndarray
        Nx1 array containing samples for the tone (single channel).

    """
    assert 0.0 <= gain <= 1.0  # check if gain range is valid

    nsamp = sampleRateHz * duration
    samples = np.arange(nsamp, dtype=np.float32)
    samples[:] = 2 * np.pi * samples[:] * freqHz / sampleRateHz
    samples[:] = signal.sawtooth(samples, width=peak)

    if gain != 1.0:
        samples *= gain

    return samples.reshape(-1, 1)


def whiteNoise(duration=1.0, sampleRateHz=SAMPLE_RATE_48kHz):
    """Generate gaussian white noise.

    Parameters
    ----------
    duration : float or int
        Length of the sound in seconds.
    sampleRateHz : int
        Samples rate of the audio for playback.

    Returns
    -------
    ndarray
        Nx1 array containing samples for the sound.

    """
    samples = np.random.randn(int(duration * sampleRateHz)).reshape(-1, 1)

    # clip range
    samples = samples.clip(-1, 1)

    return samples


def audioBufferSize(duration=1.0, freq=SAMPLE_RATE_48kHz):
    """Estimate the memory footprint of an audio clip of given duration. Assumes
    that data is stored in 32-bit floating point format.

    This can be used to determine how large of a buffer is needed to store
    enough samples for `durations` seconds of audio using the specified
    frequency (`freq`).

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


def audioMaxDuration(bufferSize=1536000, freq=SAMPLE_RATE_48kHz):
    """
    Work out the max duration of audio able to be recorded given the buffer size (kb) and frequency (Hz).

    Parameters
    ----------
    bufferSize : int, float
        Size of the buffer in bytes
        freq : int
        Sampling frequency in Hz.

    Returns
    -------
    float
        Estimated max duration
    """
    sizef32 = 32  # duh

    return bufferSize / (sizef32 * freq)


if __name__ == "__main__":
    pass
