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
from scipy.io import wavfile
import psychopy.tools.audiotools as audiotools

# pydub is needed for saving and loading MP3 files
_has_pydub = True
try:
    import pydub
except (ImportError, ModuleNotFoundError):
    _has_pydub = False


class AudioClip(object):
    """Class for storing audio clip data.

    This class is used to store raw audio data obtained from recordings or
    loaded from files.

    Parameters
    ----------
    samples : ArrayLike
        Nx1 or Nx2 array of audio samples for mono and stereo, respectively.
        Values in the array representing the amplitude of the sound should vary
        between -1 and 1.
    sampleRateHz : int
        Sampling rate used to obtain `samples`. Should match the frequency the
        clip was recorded at. If not, the audio may sound distorted when played
        back. Usually, a sample rate of 48kHz is acceptable for most
        applications (DVD audio quality).

    """
    def __init__(self, samples, sampleRateHz=48000):
        self._samples = np.atleast_2d(np.asarray(samples))
        self._sampleRateHz = sampleRateHz

        # the duration of the audio clip
        self._duration = len(self.samples) / float(self.sampleRateHz)

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
            if not _has_pydub:
                raise ModuleNotFoundError(
                    "Saving to `mp3` format requires package `pydub`.")
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

    Examples
    --------
    Capture 10 seconds of audio from the primary microphone::

        import psychopy.core as core
        import psychopy.sound.microphone as microphone

        mic = microphone.Microphone()  # open the microphone
        mic.start()  # start recording
        core.wait(10.0)  # wait 10 seconds
        audioClip = mic.getAudioClip()  # get the audio data
        mic.stop()  # stop recording

        print(audioClip.duration)  # should be ~10 seconds
        audioClip.save('test.wav')  # save the recorded audio as a 'wav' file

    """
    def __init__(self, sampleRateHz=48000, audioCaptureLib='ptb'):

        self._audioCaptureLib = audioCaptureLib
        self._sampleRateHz = sampleRateHz

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
        """Start recording audio samples from the capture device."""
        self._backend.start()

    def stop(self):
        """Stop recording audio samples."""
        self._backend.stop()

    def getAudioClip(self):
        """Get audio data."""
        return AudioClip(
            samples=self._backend.getAudioData(),
            sampleRateHz=self._sampleRateHz)


if __name__ == "__main__":
    pass
