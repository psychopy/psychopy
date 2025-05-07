#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for working with audio data.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'AudioClip',
    'load',
    'save',
    'AUDIO_SUPPORTED_CODECS',
    'AUDIO_CHANNELS_MONO',
    'AUDIO_CHANNELS_STEREO',
    'AUDIO_CHANNEL_LEFT',
    'AUDIO_EAR_LEFT',
    'AUDIO_CHANNEL_RIGHT',
    'AUDIO_EAR_RIGHT',
    'AUDIO_CHANNEL_COUNT',
    'AUDIO_EAR_COUNT'
]

from pathlib import Path
import shutil
import tempfile
import numpy as np
import soundfile as sf
from psychopy import prefs
from psychopy import logging
from psychopy.tools.audiotools import *
from psychopy.tools import filetools as ft
from .exceptions import *


# constants for specifying the number of channels
AUDIO_CHANNELS_MONO = 1
AUDIO_CHANNELS_STEREO = 2

# constants for indexing channels
AUDIO_CHANNEL_LEFT = AUDIO_EAR_LEFT = 0
AUDIO_CHANNEL_RIGHT = AUDIO_EAR_RIGHT = 1
AUDIO_CHANNEL_COUNT = AUDIO_EAR_COUNT = 2


class AudioSynthesisError(Exception):
    """Error raised when an issue occurs during audio synthesis."""
    pass


class AudioClip:
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
    using the addition operator. For online compatibility, use the `append()`
    method instead.

    There are also numerous static methods available to generate various tones
    (e.g., sine-, saw-, and square-waves). Audio samples can also be loaded and
    saved to files in various formats (e.g., WAV, FLAC, OGG, etc.)

    You can play `AudioClip` by directly passing instances of this object to
    the :class:`~psychopy.sound.Sound` class::

        import psychopy.core as core
        import psychopy.sound as sound

        myTone = AudioClip.sine(duration=5.0)  # generate a tone

        mySound = sound.Sound(myTone)
        mySound.play()
        core.wait(5.0)  # wait for sound to finish playing
        core.quit()

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
    userData : dict or None
        Optional user data to associated with the audio clip.

    """
    def __init__(self, samples, sampleRateHz=SAMPLE_RATE_48kHz, userData=None):
        # samples should be a 2D array where columns represent channels
        self._samples = np.atleast_2d(
            np.asarray(samples, dtype=np.float32, order='C'))
        self._samples.clip(-1, 1)  # force values to be clipped

        # set the sample rate of the clip
        self._sampleRateHz = int(sampleRateHz)

        # the duration of the audio clip
        self._duration = len(self.samples) / float(self.sampleRateHz)

        # user data
        self._userData = userData if userData is not None else {}
        assert isinstance(self._userData, dict)

    # --------------------------------------------------------------------------
    # Loading and saving
    #
    # These static methods are related to loading and saving audio clips from
    # files. The file types supported are those that `libsoundfile` supports.
    #
    # Additional codecs such as `mp3` require the pydub package which is
    # optional.
    #

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

        hasCodec = codec.lower() in AUDIO_SUPPORTED_CODECS

        if raiseError and not hasCodec:
            fmtList = ["'{}'".format(s) for s in AUDIO_SUPPORTED_CODECS]
            raise AudioUnsupportedCodecError(
                "Unsupported audio codec specified, must be either: " +
                ", ".join(fmtList))

        return hasCodec

    @staticmethod
    def load(filename, codec=None):
        """Load audio samples from a file. Note that this is a static method!

        Parameters
        ----------
        filename : str
            File name to load.
        codec : str or None
            Codec to use. If `None`, the format will be implied from the file
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
        # write file
        sf.write(
            filename,
            data=self._samples,
            samplerate=self._sampleRateHz,
            format=codec)
        # log
        logging.info(
            f"Saved audio data to {filename}"
        )

    # --------------------------------------------------------------------------
    # Tone and noise generation methods
    #
    # These static methods are used to generate audio samples, such as random
    # colored noise (e.g., white) and tones (e.g., sine, square, etc.)
    #
    # All of these methods return `AudioClip` objects containing the generated
    # samples.
    #

    @staticmethod
    def whiteNoise(duration=1.0, sampleRateHz=SAMPLE_RATE_48kHz, channels=2):
        """Generate gaussian white noise.

        **New feature, use with caution.**

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
        AudioClip

        """
        samples = whiteNoise(duration, sampleRateHz)

        if channels > 1:
            samples = np.tile(samples, (1, channels)).astype(np.float32)

        return AudioClip(samples, sampleRateHz=sampleRateHz)

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
        AudioClip

        Examples
        --------
        Generate 10 seconds of silence to enjoy::

            import psychopy.sound as sound
            silence = sound.AudioClip.silence(10.)

        Use the silence as a break between two audio clips when concatenating
        them::

            fullClip = clip1 + sound.AudioClip.silence(10.) + clip2

        """
        samples = np.zeros(
            (int(duration * sampleRateHz), channels), dtype=np.float32)

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
        AudioClip

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
        samples = sinetone(duration, freqHz, gain, sampleRateHz)

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
        AudioClip

        """
        samples = squaretone(duration, freqHz, dutyCycle, gain, sampleRateHz)

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
        AudioClip

        """
        samples = sawtone(duration, freqHz, peak, gain, sampleRateHz)

        if channels > 1:
            samples = np.tile(samples, (1, channels)).astype(np.float32)

        return AudioClip(samples, sampleRateHz=sampleRateHz)

    # --------------------------------------------------------------------------
    # Speech synthesis methods
    #
    # These static methods are used to generate audio samples from text using
    # text-to-speech (TTS) engines.
    #

    @staticmethod
    def synthesizeSpeech(text, engine='gtts', synthConfig=None, outFile=None):
        """Synthesize speech from text using a text-to-speech (TTS) engine.

        This method is used to generate audio samples from text using a
        text-to-speech (TTS) engine. The synthesized speech can be used for
        various purposes, such as generating audio cues for experiments or
        creating audio instructions for participants. 

        This method returns an `AudioClip` object containing the synthesized
        speech. The quality and format of the retured audio may vary depending 
        on the TTS engine used.

        Please note that online TTS engines may require an active internet
        connection to work. This also may send the text to a remote server for
        processing, so be mindful of privacy concerns.

        Parameters
        ----------
        text : str
            Text to synthesize into speech.
        engine : str
            TTS engine to use for speech synthesis. Default is 'gtts'.
        synthConfig : dict or None
            Additional configuration options for the specified engine. These
            are specified using a dictionary (ex. 
            `synthConfig={'slow': False}`). These paramters vary depending on 
            the engine in use. Default is `None` which uses the default
            configuration for the engine.
        outFile : str or None
            File name to save the synthesized speech to. This can be used to 
            save the audio to a file for later use. If `None`, the audio clip 
            will be returned in memory. If you plan on using the same audio 
            clip multiple times, it is recommended to save it to a file and load
            it later.

        Returns
        -------
        AudioClip
            Audio clip containing the synthesized speech.

        Examples
        --------
        Synthesize speech using the default gTTS engine::

            import psychopy.sound as sound
            voiceClip = sound.AudioClip.synthesizeSpeech(
                'How are you doing today?')

        Save the synthesized speech to a file for later use::

            voiceClip = sound.AudioClip.synthesizeSpeech(
                'How are you doing today?', outFile='/path/to/speech.mp3')

        Synthesize speech using the gTTS engine with a specific language, 
        timeout, and top-level domain::

            voiceClip = sound.AudioClip.synthesizeSpeech(
                'How are you doing today?', 
                engine='gtts', 
                synthConfig={'lang': 'en', 'timeout': 10, 'tld': 'us'})

        """
        if engine not in ['gtts']:
            raise ValueError('Unsupported TTS engine specified.')

        synthConfig = {} if synthConfig is None else synthConfig

        if engine == 'gtts':  # google's text-to-speech engine
            logging.info('Using Google Text-to-Speech (gTTS) engine.')

            try:
                import gtts
            except ImportError:
                raise ImportError(
                    'The gTTS package is required for speech synthesis.')

            # set defaults for parameters if not specified
            if 'timeout' not in synthConfig:
                synthConfig['timeout'] = None
                logging.warning(
                    'The gTTS speech-to-text engine has been configured with '
                    'an infinite timeout. The application may stall if the '
                    'server is unresponsive. To set a timeout, specify the '
                    '`timeout` key in `synthConfig`.')
            
            if 'lang' not in synthConfig:  # language
                synthConfig['lang'] = 'en'
                logging.info(
                    "Language not specified, defaulting to '{}' for speech "
                    "synthesis engine.".format(synthConfig['lang']))
            else:
                # check if the value is a valid language code
                if synthConfig['lang'] not in gtts.lang.tts_langs():
                    raise ValueError('Unsupported language code specified.')

            if 'tld' not in synthConfig:  # top-level domain
                synthConfig['tld'] = 'us'
                logging.info(
                    "Top-level domain (TLD) not specified, defaulting to '{}' "
                    "for synthesis engine.".format(synthConfig['tld']))

            if 'slow' not in synthConfig:  # slow mode
                synthConfig['slow'] = False
                logging.info(
                    "Slow mode not specified, defaulting to '{}' for synthesis "
                    "engine.".format(synthConfig['slow']))

            try:
                handle = gtts.gTTS(
                    text=text, 
                    **synthConfig)
            except gtts.gTTSError as e:
                raise AudioSynthesisError(
                    'Error occurred during speech synthesis: {}'.format(e))

            # this is online and needs a download, so we'll save it to a file
            with tempfile.TemporaryDirectory() as tmpdir:
                # always returns an MP3 file
                tmpfile = str(Path(tmpdir) / 'psychopy_tts_output.mp3')
                handle.save(tmpfile)

                # load audio clip samples to memory
                toReturn = AudioClip.load(tmpfile)

                # copy the file if we want to save it
                import shutil
                if outFile is not None:
                    shutil.copy(tmpfile, outFile)
                    
        return toReturn

    # --------------------------------------------------------------------------
    # Audio editing methods
    #
    # Methods related to basic editing of audio samples (operations such as
    # splicing clips and signal gain).
    #

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
        
        self._duration = len(self.samples) / float(self.sampleRateHz)

        return self

    def append(self, clip):
        """Append samples from another sound clip to the end of this one.

        The `AudioClip` object must have the same sample rate and channels as
        this object.

        Parameters
        ----------
        clip : AudioClip
            Audio clip to append.

        Returns
        -------
        AudioClip
            This object with samples from `clip` appended.

        Examples
        --------
        Join two sound clips together::

            snd1.append(snd2)

        """
        # if either clip is empty, just replace it
        if len(self.samples) == 0:
            return clip
        if len(clip.samples) == 0:
            return self

        assert self.channels == clip.channels
        assert self._sampleRateHz == clip.sampleRateHz

        self._samples = np.ascontiguousarray(
            np.vstack((self._samples, clip.samples)),
            dtype=np.float32)

        # recompute the duration of the new clip
        self._duration = len(self.samples) / float(self.sampleRateHz)

        return self

    def copy(self):
        """Create an independent copy of this `AudioClip`.

        Returns
        -------
        AudioClip

        """
        return AudioClip(
            samples=self._samples.copy(),
            sampleRateHz=self._sampleRateHz)

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

    def resample(self, targetSampleRateHz, resampleType='default', 
            equalEnergy=False, copy=False):
        """Resample audio to another sample rate.

        This method will resample the audio clip to a new sample rate. The
        method used for resampling can be specified using the `method` parameter.

        Parameters
        ----------
        targetSampleRateHz : int
            New sample rate.
        resampleType : str
            Fitler (or method) to use for resampling. The methods available
            depend on the packages installed. The 'default' method uses 
            `scipy.signal.resample` to resample the audio. Other methods require 
            the user to install `librosa` or `resampy`. Default is 'default'.
        equalEnergy : bool
            Make the output have similar energy to the input. Option not
            available for the 'default' method. Default is `False`.
        copy : bool
            Return a copy of the resampled audio clip at the new sample rate.
            If `False`, the audio clip will be resampled inplace. Default is
            `False`.
        
        Returns
        -------
        AudioClip
            Resampled audio clip.

        Notes
        -----
        * Resampling audio clip may result in distortion which is exacerbated by
          successive resampling.
        * When using `librosa` for resampling, the `fix` parameter is set to
          `False`.
        * The resampling types 'linear', 'zero_order_hold', 'sinc_best', 
          'sinc_medium' and 'sinc_fastest' require the `samplerate` package to
          be installed in addition to `librosa`.
        * Specifying either the 'fft' or 'scipy' method will use the same
          resampling method as the 'default' method, howwever it will allow for 
          the `equalEnergy` option to be used.

        Examples
        --------
        Resample an audio clip to 44.1kHz::

            snd.resample(44100)

        Use the 'soxr_vhq' method for resampling::

            snd.resample(44100, resampleType='soxr_vhq')

        Create a copy of the audio clip resampled to 44.1kHz::

            sndResampled = snd.resample(44100, copy=True)

        Resample the audio clip to be playable on a certain device::

            import psychopy.sound as sound
            from psychopy.sound.audioclip import AudioClip

            audioClip = sound.AudioClip.load('/path/to/audio.wav')
            
            deviceSampleRateHz = sound.Sound().sampleRate
            audioClip.resample(deviceSampleRateHz)

        """
        targetSampleRateHz = int(targetSampleRateHz)  # ensure it's an integer

        # sample rate is the same, return self
        if targetSampleRateHz == self._sampleRateHz:
            if copy:
                return AudioClip(
                    self._samples.copy(), 
                    sampleRateHz=self._sampleRateHz)

            logging.info('No resampling needed, sample rate is the same.')

            return self  # no need to resample

        if resampleType == 'default':  # scipy
            import scipy.signal  # hard dep, so we'll import here

            # the simplest method to resample audio using the libraries we have
            # already
            nSamp = round(
                len(self._samples) * float(targetSampleRateHz) / 
                self.sampleRateHz)
            newSamples = scipy.signal.resample(
                self._samples, nSamp, axis=0)

            if equalEnergy:
                logging.warning(
                    'The `equalEnergy` option is not available for the '
                    'default resampling method.')

        elif resampleType in ('kaiser_best', 'kaiser_fast'):  # resampy
            try:
                import resampy
            except ImportError:
                raise ImportError(
                    'The `resampy` package is required for this resampling '
                    'method ({}).'.format(resampleType))

            newSamples = resampy.resample(
                self._samples, 
                self._sampleRateHz, 
                targetSampleRateHz,
                filter=resampleType,
                scale=equalEnergy,
                axis=0)

        elif resampleType in ('soxr_vhq', 'soxr_hq', 'soxr_mq', 'soxr_lq', 
                'soxr_qq', 'polyphase', 'linear', 'zero_order_hold', 'fft',
                'scipy', 'sinc_best', 'sinc_medium', 'sinc_fastest'):  # librosa
            try:
                import librosa
            except ImportError:
                raise ImportError(
                    'The `librosa` package is required for this resampling '
                    'method ({}).'.format(resampleType))

            newSamples = librosa.resample(
                self._samples, 
                orig_sr=self._sampleRateHz, 
                target_sr=targetSampleRateHz,
                res_type=resampleType,
                scale=equalEnergy, 
                fix=False,
                axis=0)

        else:
            raise ValueError('Unsupported resampling method specified.')

        logging.info(
            "Resampled audio from {}Hz to {}Hz using method '{}'.".format(
                self._sampleRateHz, targetSampleRateHz, resampleType))

        if copy:  # return a new object
            return AudioClip(newSamples, sampleRateHz=targetSampleRateHz)

        # inplace resampling, need to clear the old array since the shape may
        # have changed
        self._samples = newSamples
        self._sampleRateHz = targetSampleRateHz

        return self

    # --------------------------------------------------------------------------
    # Audio analysis methods
    #
    # Methods related to basic analysis of audio samples, nothing too advanced
    # but still useful.
    #

    def rms(self, channel=None):
        """Compute the root mean square (RMS) of the samples to determine the
        average signal level.

        Parameters
        ----------
        channel : int or None
            Channel to compute RMS (zero-indexed). If `None`, the RMS of all
            channels will be computed.

        Returns
        -------
        ndarray or float
            An array of RMS values for each channel if ``channel=None`` (even if
            there is one channel an array is returned). If `channel` *was*
            specified, a `float` will be returned indicating the RMS of that
            single channel.

        """
        if channel is not None:
            assert 0 < channel < self.channels
        # get samples
        arr = self._samples if channel is None else self._samples[:, channel]
        # calculate rms
        rms = np.nan_to_num(np.sqrt(np.nanmean(np.square(arr), axis=0)), nan=0)

        return rms if len(rms) > 1 else rms[0]

    # --------------------------------------------------------------------------
    # Properties
    #

    @property
    def samples(self):
        """Nx1 or Nx2 array of audio samples (`~numpy.ndarray`).

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
        return not self.isMono  # are we moving in stereo? ;)

    @property
    def isMono(self):
        """`True` if there is only one channel of audio data.

        """
        return self._samples.shape[1] == 1

    @property
    def userData(self):
        """User data associated with this clip (`dict`). Can be used for storing
        additional data related to the clip. Note that `userData` is not saved
        with audio files!

        Example
        -------
        Adding fields to `userData`. For instance, we want to associated the
        start time the clip was recorded at with it::

            myClip.userData['date_recorded'] = t_start

        We can access that field later by::

            thisRecordingStartTime = myClip.userData['date_recorded']

        """
        return self._userData

    @userData.setter
    def userData(self, value):
        assert isinstance(value, dict)
        self._userData = value

    def convertToWAV(self):
        """Get a copy of stored audio samples in WAV PCM format.

        Returns
        -------
        ndarray
            Array with the same shapes as `.samples` but in 16-bit WAV PCM
            format.

        """
        return np.asarray(
            self._samples * ((1 << 15) - 1), dtype=np.int16).tobytes()

    def asMono(self, copy=True):
        """Convert the audio clip to mono (single channel audio).

        Parameters
        ----------
        copy : bool
            If `True` an :class:`~psychopy.sound.AudioClip` containing a copy
            of the samples will be returned. If `False`, channels will be
            mixed inplace resulting in the same object being returned. User data
            is not copied.

        Returns
        -------
        :class:`~psychopy.sound.AudioClip`
            Mono version of this object.

        """
        if self.channels == 1:
            return self
        # log
        logging.debug(
            "Converted audio clip from stereo to mono"
        )
        # enforce 2D
        samples = np.atleast_2d(self._samples)
        # reduce to mono
        if samples.shape[1] > 1:
            samplesMixed = np.atleast_2d(
                np.sum(samples, axis=1, dtype=np.float32) / np.float32(2.)).T
        else:
            samplesMixed = samples.copy()
        # create copy if requested
        if copy:
            return AudioClip(samplesMixed, self.sampleRateHz)
        # otherwise change self
        self._samples = samplesMixed
        return self
    
    def asStereo(self, copy=True):
        """Convert the audio clip to stereo (two channel audio).

        Parameters
        ----------
        copy : bool
            If `True` an :class:`~psychopy.sound.AudioClip` containing a copy
            of the samples will be returned. If `False`, channels will be
            mixed inplace resulting in the same object being returned. User data
            is not copied.

        Returns
        -------
        :class:`~psychopy.sound.AudioClip`
            Stereo version of this object.

        """
        if self.channels == 2:
            return self
        # log
        logging.debug(
            "Converted audio clip from mono to stereo"
        )
        # enforce 2D
        samples = np.atleast_2d(self._samples) 
        # expand to stereo
        samples = np.hstack((samples, samples))
        # create copy if requested
        if copy:
            return AudioClip(samples, self.sampleRateHz)
        # otherwise change self
        self._samples = samples
        return self

    def transcribe(self, engine='whisper', language='en-US', expectedWords=None,
                   config=None):
        """Convert speech in audio to text.

        This function accepts an audio clip and returns a transcription of the
        speech in the clip. The efficacy of the transcription depends on the 
        engine selected, audio quality, and language support.

        Speech-to-text conversion blocks the main application thread when used 
        on Python. Don't transcribe audio during time-sensitive parts of your
        experiment! Instead, initialize the transcriber before the experiment
        begins by calling this function with `audioClip=None`.

        Parameters
        ----------
        engine : str
            Speech-to-text engine to use.
        language : str
            BCP-47 language code (eg., 'en-US'). Note that supported languages
            vary between transcription engines.
        expectedWords : list or tuple
            List of strings representing expected words or phrases. This will
            constrain the possible output words to the ones specified which 
            constrains the model for better accuracy. Note not all engines 
            support this feature (only Sphinx and Google Cloud do at this time). 
            A warning will be logged if the engine selected does not support this 
            feature. CMU PocketSphinx has an additional feature where the 
            sensitivity can be specified for each expected word. You can 
            indicate the sensitivity level to use by putting a ``:`` after each 
            word in the list (see the Example below). Sensitivity levels range 
            between 0 and 100. A higher number results in the engine being more 
            conservative, resulting in a higher likelihood of false rejections. 
            The default sensitivity is 80% for words/phrases without one 
            specified.
        config : dict or None
            Additional configuration options for the specified engine. These
            are specified using a dictionary (ex. `config={'pfilter': 1}` will
            enable the profanity filter when using the `'google'` engine).

        Returns
        -------
        :class:`~psychopy.sound.transcribe.TranscriptionResult`
            Transcription result.

        Notes
        -----
        * The recommended transcriber is OpenAI Whisper which can be used locally
          without an internet connection once a model is downloaded to cache. It 
          can be selected by passing `engine='whisper'` to this function.
        * Online transcription services (eg., Google) provide robust and accurate 
          speech recognition capabilities with broader language support than 
          offline solutions. However, these services may require a paid
          subscription to use, reliable broadband internet connections, and may 
          not respect the privacy of your participants as their responses are 
          being sent to a third-party. Also consider that a track of audio data 
          being sent over the network can be large, users on metered connections 
          may incur additional costs to run your experiment. Offline 
          transcription services (eg., CMU PocketSphinx and OpenAI Whisper) do not 
          require an internet connection after the model has been downloaded and 
          installed.
        * If the audio clip has multiple channels, they will be combined prior to
          being passed to the transcription service if needed.

        """
        # avoid circular import
        from psychopy.sound.transcribe import (
            getActiveTranscriber,
            setupTranscriber)

        # get the active transcriber
        transcriber = getActiveTranscriber()
        if transcriber is None:
            logging.warning(
                'No active transcriber, creating one now! If this happens in '
                'a time sensitive part of your experiment, consider creating '
                'the transcriber before the experiment begins by calling '
                '`psychopy.sound.transcribe.setupTranscriber()` function.'
            )
            setupTranscriber(engine=engine, config=config)
            transcriber = getActiveTranscriber()  # get again

        return transcriber.transcribe(
            self,
            language=language,
            expectedWords=expectedWords,
            config=config)


def load(filename, codec=None):
    """Load an audio clip from file.

    Parameters
    ----------
    filename : str
        File name to load.
    codec : str or None
        Codec to use. If `None`, the format will be implied from the file name.

    Returns
    -------
    AudioClip
        Audio clip containing samples loaded from the file.

    """
    # alias default names (so it always points to default.png)
    if filename in ft.defaultStim:
        filename = Path(prefs.paths['assets']) / ft.defaultStim[filename]
    return AudioClip.load(filename, codec)


def save(filename, clip, codec=None):
    """Save an audio clip to file.

    Parameters
    ----------
    filename : str
        File name to write audio clip to.
    clip : AudioClip
        The clip with audio samples to write.
    codec : str or None
        Format to save audio clip data as. If `None`, the format will be
        implied from the extension at the end of `filename`.

    """
    clip.save(filename, codec)


if __name__ == "__main__":
    pass
