#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for working with audio data.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'AudioClip',
    'SAMPLE_RATE_8kHz', 'SAMPLE_RATE_TELCOM_QUALITY',
    'SAMPLE_RATE_16kHz', 'SAMPLE_RATE_VOIP_QUALITY',
    'SAMPLE_RATE_44p1kHz', 'SAMPLE_RATE_CD_QUALITY',
    'SAMPLE_RATE_48kHz', 'SAMPLE_RATE_DVD_QUALITY',
    'SAMPLE_RATE_96kHz',
    'SAMPLE_RATE_192kHz'
]

import numpy as np
from psychopy.tools.audiotools import *


class AudioClipInfo(object):
    """Class for audio clip meta-data.

    Instances of this class are used to store metadata for the associated
    `AudioClip` object. Usually, values for properties are set by the routine
    that yielded the `AudioClip` object.

    Parameters
    ----------
    parent : AudioClip

    """
    def __init__(self, parent=None):
        self.parent = parent

    @property
    def duration(self):
        """Duration of the audio clip in seconds."""
        if self.parent is not None:
            return self.parent.duration

    @property
    def sampleRateHz(self):
        """Sample rate of the audio clip."""
        if self.parent is not None:
            return self.parent.sampleRateHz

    @property
    def channels(self):
        """Sample rate of the audio clip."""
        if self.parent is not None:
            return self.parent.channels


class AudioClip(object):
    """Class for storing audio clip data.

    This class is used to store and handle raw audio data, such as those
    obtained from microphone recordings or loaded from files. PsychoPy stores
    audio samples in contiguous arrays of 32-bit floating-point values ranging
    between -1 and 1.

    You can use operators on `AudioClip` instances to combine audio clips
    together. For instance, the ``+`` operator will return a new `AudioClip`
    instance whose samples are the concatenation of the two operands::

        sndCombined = sndClip1 + sndClip2

    Parameters
    ----------
    samples : ArrayLike
        Nx1 or Nx2 array of audio samples for mono and stereo, respectively.
        Values in the array representing the amplitude of the sound waveform
        should vary between -1 and 1. If not, they will be clipped.
    sampleRateHz : int
        Sampling rate used to obtain `samples` in Hertz (Hz). The sample rate or
        frequency is related to the quality of the audio, where higher sample
        rates usually result in better sounding audio (albeit a larger memory
        footprint and file size). The value specified should match the frequency
        the clip was recorded at. If not, the audio may sound distorted when
        played back. Usually, a sample rate of 48kHz is acceptable for most
        applications (DVD audio quality). For convenience, module level
        constants with form ``SAMPLE_RATE_*`` are provided to specify many
        common samples rates.

    """
    def __init__(self, samples, sampleRateHz=SAMPLE_RATE_48kHz):
        # samples should be a 2D array where columns represent channels
        self._samples = np.atleast_2d(
            np.asarray(samples, dtype=np.float32, order='C'))
        self._samples.clip(-1, 1)  # force values to be clipped

        # set the sample rate of the clip
        self._sampleRateHz = int(sampleRateHz)

        # the duration of the audio clip
        self._duration = len(self.samples) / float(self.sampleRateHz)

        # meta-data header
        self._info = AudioClipInfo(self)

    def __add__(self, other):
        """Concatenate two audio clips."""
        assert other.sampleRateHz == self._sampleRateHz
        assert other.channels == self.channels

        newSamples = np.ascontiguousarray(
            np.vstack((self._samples, other.samples)),
            dtype=np.float32)

        toReturn = AudioClip(
            samples=newSamples,
            sampleRateHz=self._sampleRateHz)

        return toReturn

    def __iadd__(self, other):
        """Concatenate two audio clips inplace."""
        assert other.sampleRateHz == self._sampleRateHz
        assert other.channels == self.channels

        self._samples = np.ascontiguousarray(
            np.vstack((self._samples, other.samples)),
            dtype=np.float32)

        return self

    def gain(self, factor, channel=None):
        """Apply gain the audio samples.

        This will modify the internal store of samples inplace. Clipping is
        automatically applied to samples after applying gain.

        Parameters
        ----------
        factor : float or int
            Gain factor to multiply audio samples.
        channel : int or None
            Channel to apply gain to. If `None`, gain will be applied to all
            channels.

        """
        try:
            arrview = self._samples[:, :] \
                if channel is None else self._samples[:, channel]
        except IndexError:
            raise ValueError('Invalid value for `channel`.')

        # multiply and clip range
        arrview *= float(factor)
        arrview.clip(-1, 1)

    @property
    def info(self):
        """Meta-data related to the audio clip (`AudioClipInfo`).
        """
        return self._info

    @info.setter
    def info(self, value):
        assert isinstance(value, AudioClipInfo)
        self._info.parent = None  # remove the reference to self
        self._info = value
        self._info.parent = self

    @property
    def duration(self):
        """The duration of the audio in seconds (`float`).

        This value is computed using the specified sampling frequency and number
        of samples.

        """
        return self._duration

    @property
    def channels(self):
        """Number of audio channels in the clip (`int`).

        If `channels` > 1, the audio clip is in stereo.

        """
        return self._samples.shape[1]

    @property
    def isStereo(self):
        """`True` if there are two channels of audio samples.

        Usually one for each ear. The first channel is usually the left ear, and
        the second the right.

        """
        return not self.isMono

    @property
    def isMono(self):
        """`True` if there is only one channel of audio data.

        """
        return self._samples.shape[1] == 1

    @property
    def samples(self):
        """Nx1 array of audio samples (`~numpy.ndarray`).

        Values must range from -1 to 1. Values outside that range will be
        clipped, possibly resulting in distortion.

        """
        return self._samples

    @samples.setter
    def samples(self, value):
        self._samples = np.asarray(value, dtype=float)  # convert to array
        self._samples.clip(-1., 1.)  # do clipping to keep samples in range

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

    def save(self, filename, fmt=None):
        """Save an audio clip to file.

        Parameters
        ----------
        filename : str
            File name to write audio clip to.
        fmt : str or None
            Format to save audio clip data as. If `None`, the format will be
            implied from the extension at the end of `filename`. Possible
            formats are: `'wav'` for Waveform Audio File Format (.wav) for raw
            and uncompressed audio, or `'csv'` for a plain text file containing
            timestamped raw audio data samples (for plotting).

        """
        if fmt is None:  # imply format from file path
            fname = filename.lower()
            if fname.endswith('.wav'):
                fmt = 'wav'
            elif fname.endswith('.csv'):
                fmt = 'csv'
            elif fname.endswith('.mp3'):
                fmt = 'mp3'
            else:
                fmt = 'wav'  # cant be determined

        # code for saving the audio clip in various formats
        if fmt == 'wav':  # save as a wave file
            audiotools.array2wav(filename, self.samples, self._sampleRateHz)
        elif fmt == 'mp3':  # mp3 format
            pass
        elif fmt == 'csv':  # CSV format (for plotting)
            tsamp = 1.0 / float(self._sampleRateHz)
            with open(filename, 'w') as csv:
                csv.write('tsec,amplitude\n')  # header
                csv.writelines(
                    [(','.join(
                        (str(tsamp * i), str(v))) + '\n')
                     for i, v in enumerate(self.samples[:, 0])])
        else:
            pass


if __name__ == "__main__":
    pass