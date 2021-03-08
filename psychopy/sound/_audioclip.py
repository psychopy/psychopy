#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for working with audio data.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'AudioClip',
    'load',
    'save',
    'SUPPORTED_AUDIO_CODECS'
]

import numpy as np
import soundfile as sf
from psychopy.tools.audiotools import *
from ._audiodevice import AudioDevice
from ._exceptions import AudioUnsupportedCodec

# supported formats for loading and saving audio samples to file
SUPPORTED_AUDIO_CODECS = [s.lower() for s in sf.available_formats().keys()]


class AudioClip(object):
    """Class for storing audio clip data.

    This class is used to store and handle raw audio data, such as those
    obtained from microphone recordings or loaded from files. PsychoPy stores
    audio samples in contiguous arrays of 32-bit floating-point values ranging
    between -1 and 1.

    The `AudioClip` class provides basic audio editing capabilities too. You can
    use operators on `AudioClip` instances to combine audio clips together. For
    instance, the ``+`` operator will return a new `AudioClip` instance whose
    samples are the concatenation of the two operands::

        sndCombined = sndClip1 + sndClip2

    Note that audio clips must have the same sample rates in order to be joined
    using the addition operator.

    There are also numerous static methods available to generate various tones
    (e.g., sine-, saw-, and square-waves). Audio samples can also be loaded and
    saved to files in various formats (e.g., WAV, MP3, FLAC, OGG, etc.)

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
    audioDevice : :class:`~psychopy.sound._audioclip.AudioClip` or None
        Optional descriptor for the audio device which captured samples. Mainly
        used internally.
    userData : dict or None
        Optional user data to associated with the audio clip.

    """
    def __init__(self, samples, sampleRateHz=SAMPLE_RATE_48kHz,
                 audioDevice=None, userData=None):
        # samples should be a 2D array where columns represent channels
        self._samples = np.atleast_2d(
            np.asarray(samples, dtype=np.float32, order='C'))
        self._samples.clip(-1, 1)  # force values to be clipped

        # set the sample rate of the clip
        self._sampleRateHz = int(sampleRateHz)

        # the duration of the audio clip
        self._duration = len(self.samples) / float(self.sampleRateHz)

        # Audio device descriptor, used to associate samples with the device
        # that actually captured it
        assert isinstance(audioDevice, AudioDevice) or audioDevice is None
        self._audioDevice = audioDevice

        # user data
        self._userData = userData if userData is not None else {}

    @staticmethod
    def _checkCodecSupported(codec, raiseError=False):
        """Check if the audio format string corresponds to a supported codec.
        Used internally to check if the user specified a valid codec identifier.

        Parameters
        ----------
        codec: str
            Codec identifier (e.g., 'wav', 'mp3', etc.)
        raiseError : bool
            Raise an error (``) instead of returning a value. Default is
            `False`.

        Returns
        -------
        bool
            `True` if the format is supported.

        """
        if not isinstance(codec, str):
            raise ValueError('Codec identifier must be a string.')

        hasCodec = codec.lower() in SUPPORTED_AUDIO_CODECS

        if raiseError and not hasCodec:
            fmtList = ["'{}'".format(s) for s in SUPPORTED_AUDIO_CODECS]
            raise AudioUnsupportedCodec(
                "Unsupported audio codec specified, must be either: " +
                ", ".join(fmtList))

        return hasCodec

    @staticmethod
    def load(filename, codec=None):
        """Load audio samples from a file.

        Parameters
        ----------
        filename : str
            File name to load.
        codec : str or None
            Format to use. If `None`, the format will be implied from the file
            name.

        Returns
        -------
        AudioClip
            Audio clip containing samples loaded from the file.

        """
        if codec is not None:
            AudioClip._checkCodecSupported(codec, raiseError=True)

        samples, sampleRateHz = sf.read(
            filename,
            dtype='float32',
            always_2d=True,
            format=codec)

        return AudioClip(
            samples=samples,
            sampleRateHz=sampleRateHz)

    @staticmethod
    def silence(duration=1.0, sampleRateHz=SAMPLE_RATE_48kHz, channels=2):
        """Generate audio samples for a silent period.

        This is used to create silent periods of a very specific duration
        between other audio clips.

        Parameters
        ----------
        duration : float or int
            Length of the sound in seconds.
        sampleRateHz : int
            Samples rate of the audio for playback.
        channels : int
            Number of channels for the output.

        Returns
        -------
        ndarray
            Nx1 array containing samples for the tone (single channel).

        Examples
        --------
        Generate 5 seconds of silence to enjoy::

            import psychopy.sound as sound
            silence = sound.AudioClip.silence(10.)

        Use the silence as a break between two audio clips when concatenating
        them::

            fullClip = clip1 + sound.AudioClip.silence(10.) + clip2

        """
        samples = np.zeros((duration * sampleRateHz, channels), dtype=np.float32)

        return AudioClip(samples, sampleRateHz=sampleRateHz)

    @staticmethod
    def sine(duration=1.0, freqHz=440, gain=0.8, sampleRateHz=SAMPLE_RATE_48kHz,
             channels=2):
        """Generate audio samples for a tone with a sine waveform.

        Parameters
        ----------
        duration : float or int
            Length of the sound in seconds.
        freqHz : float or int
            Frequency of the tone in Hertz (Hz). Note that this differs from the
            `sampleRateHz`.
        gain : float
            Gain factor ranging between 0.0 and 1.0. Default is 0.8.
        sampleRateHz : int
            Samples rate of the audio for playback.
        channels : int
            Number of channels for the output.

        Returns
        -------
        ndarray
            Nx1 array containing samples for the tone (single channel).

        Examples
        --------
        Generate an audio clip of a tone 10 seconds long with a frequency of
        400Hz::

            import psychopy.sound as sound
            tone400Hz = sound.AudioClip.sine(10., 400.)

        Create a marker/cue tone and append it to pre-recorded instructions::

            import psychopy.sound as sound
            voiceInstr = sound.AudioClip.load('/path/to/instructions.wav')
            markerTone = sound.AudioClip.sine(
                1.0, 440.,  # duration and freq
                sampleRateHz=voiceInstr.sampleRateHz)  # must be the same!

            fullInstr = voiceInstr + markerTone  # create instructions with cue
            fullInstr.save('/path/to/instructions_with_tone.wav')  # save it

        """
        samples = sinewave(duration, freqHz, gain, sampleRateHz)

        if channels > 1:
            samples = np.tile(samples, (1, channels)).astype(np.float32)

        return AudioClip(samples, sampleRateHz=sampleRateHz)

    @staticmethod
    def square(duration=1.0, freqHz=440, dutyCycle=0.5, gain=0.8,
               sampleRateHz=SAMPLE_RATE_48kHz, channels=2):
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
            Gain factor ranging between 0.0 and 1.0. Default is 0.8.
        sampleRateHz : int
            Samples rate of the audio for playback.
        channels : int
            Number of channels for the output.

        Returns
        -------
        ndarray
            Nx1 array containing samples for the tone (single channel).

        """
        samples = squarewave(duration, freqHz, dutyCycle, gain, sampleRateHz)

        if channels > 1:
            samples = np.tile(samples, (1, channels)).astype(np.float32)

        return AudioClip(samples, sampleRateHz=sampleRateHz)

    @staticmethod
    def sawtooth(duration=1.0, freqHz=440, peak=1.0, gain=0.8,
                 sampleRateHz=SAMPLE_RATE_48kHz, channels=2):
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
            resulting wave will be triangular. A value of 1.0 will cause the
            peak to be located at the very end of a cycle.
        gain : float
            Gain factor ranging between 0.0 and 1.0. Default is 0.8.
        sampleRateHz : int
            Samples rate of the audio for playback.
        channels : int
            Number of channels for the output.

        Returns
        -------
        ndarray
            Nx1 array containing samples for the tone (single channel).

        """
        samples = squarewave(duration, freqHz, peak, gain, sampleRateHz)

        if channels > 1:
            samples = np.tile(samples, (1, channels)).astype(np.float32)

        return AudioClip(samples, sampleRateHz=sampleRateHz)

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

    def copy(self):
        """Create a copy of this `AudioClip`.

        Returns
        -------
        AudioClip

        """
        return AudioClip(
            samples=self._samples.copy(),
            sampleRateHz=self._sampleRateHz)

    def rms(self):
        """Compute the root mean square (RMS) of the samples to determine the
        signal level.

        Returns
        -------
        ndarray
            RMS for each channel.

        """
        rms = np.sqrt(np.mean(np.square(self.samples), axis=1))

        return rms

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
    def audioDevice(self):
        """Descriptor (`AudioDevice`) for the audio device that captured the
        sound, has value of `None` if that information is not available.
        """
        return self._audioDevice

    @audioDevice.setter
    def audioDevice(self, value):
        assert isinstance(value, AudioDevice) or value is None
        self._audioDevice = value

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

    def save(self, filename, codec=None):
        """Save an audio clip to file.

        Parameters
        ----------
        filename : str
            File name to write audio clip to.
        codec : str or None
            Format to save audio clip data as. If `None`, the format will be
            implied from the extension at the end of `filename`.
        """
        if codec is not None:
            AudioClip._checkCodecSupported(codec, raiseError=True)

        sf.write(
            filename,
            data=self._samples,
            samplerate=self._sampleRateHz,
            format=codec)


def load(filename, codec=None):
    """Load an audio clip from file.

    """
    return AudioClip.load(filename, codec)


def save(filename, clip, codec=None):
    """Save an audio clip to a file.

    """
    clip.save(filename, codec)


if __name__ == "__main__":
    pass
