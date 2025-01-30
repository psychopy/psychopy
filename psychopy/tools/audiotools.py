#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tools for working with audio data.

This module provides routines for saving/loading and manipulating audio samples.

"""

__all__ = [
    'AudioFileWriter',
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
    'knownNoteNames', 
    'stepsFromA',
    'closeAllAudioWriters'
]

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import os
import numpy as np
from scipy.io import wavfile
from scipy import signal
import queue
import threading
import atexit
import time
from psychopy import logging

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

# sentinel value to indicate end of audio data
AUDIO_DATA_EOF = object() 


# keep track of open audio writers
_openAudioWriters = set()


class AudioFileWriter:
    """Asyncronous audio file writer.

    This class is used to write audio samples to a file in a separate thread.
    This is useful for recording audio in real-time and writing to disk without
    blocking the main thread.

    A single audio writer can only be associated with a single file. If you need
    to write to multiple files, create a new writer for each file.

    Parameters
    ----------
    filename : str
        File name for the output. This can be a relative or absolute path.
    sampleRate : int
        Samples rate of the audio for playback in Hertz (Hz). Adjust to match
        the sample rate of the audio data being written. Default is `48000`.
    channels : int
        Number of audio channels in the file. Either `1` (mono) or `2` (stereo).
        Default is `1`.
    codec : str
        Codec used to encode the audio file. Default is `'wav'`.
    encoderLib : str
        Library used to encode the audio file. Default is `'soundfile'`.
    encoderOpts : dict
        Options used to encode the audio file. These are settings that are 
        passed to the encoder when opening the file for writing. Use this to 
        specify additional options that are specific to the encoder. Default is 
        `None`.
    keepTempFile : bool
        Keep any temporary files created during encoding. This is usually not 
        needed, however it can be useful for debugging or to retain the original
        audio data that can be recovered in the event of a crash. Temporary
        files usually have the same name as the final file with an additional
        extension (e.g., `.raw`). Default is `False`.
    fileExistsPolicy : str
        Policy to use when the output file already exists. Options are 
        `'overwrite'` (default), `'append'`, `'raise'`, `'rename'`, and
        `'increment'`. If `'overwrite'`, the file will be overwritten. If
        `'append'`, the file will be opened for appending. If `'raise'`, an
        exception will be raised. If `'rename'`, the file will be renamed. If
        `'increment'`, the file will be incremented. Default is `'overwrite'`.

    Examples
    --------
    Open a writer and write some samples to a file::

        # create a writer object and open the file
        writer = AudioFileWriter('test.wav', SAMPLE_RATE_48kHz)
        writer.open()

        # generate and add audio samples to the file
        writer.addSamples(
            sinetone(0.5, 440.0, gain=0.8, sampleRateHz=SAMPLE_RATE_48kHz))
        writer.addSamples(
            squaretone(0.5, 440.0, gain=0.8, sampleRateHz=SAMPLE_RATE_48kHz))
        writer.addSamples(
            sawtone(0.5, 440.0, gain=0.8, sampleRateHz=SAMPLE_RATE_48kHz))

        # close the file
        writer.close()

    Notes
    -----
    * Some encoders require a temporary file to be created since they cannot
      write directly to the final file. The audio data is converted to the
      requested format upon closing the file.
    * The `close()` method is registered to be called at exit, any samples in
      the queue will be written to the file before closing. While this is not
      garanteed to work in all cases, it helps prevent data loss in the event of
      a crash.
    
    """
    def __init__(self, filename, sampleRate, channels=1, codec=None, 
            encoderLib='soundfile', encoderOpts=None, keepTempFile=False,
            fileExistsPolicy='overwrite'):

        self._writerThread = None
        self._sampleQueue = queue.Queue()
        self._dataLock = threading.Lock()
        self._keepTempFile = keepTempFile
        self._absPath = self._filename = None
        self._lastAudioFile = self._tempFileName = None
        self._sampleRate = sampleRate
        self._channels = channels
        self._codec = codec
        self._encoderLib = encoderLib
        self._encoderOpts = encoderOpts
        self._fileExistsPolicy = fileExistsPolicy

        # codec specific settings, the value of these will be determined based
        # on the requirments of the endocer used
        self._formatInfo = None

        # determine codec from file extension if not specified
        if self._codec is None:
            # check if the specified file names has an extension
            if '.' in filename:
                _, ext = filename.rsplit('.', 1)
                if ext:
                    self._codec = ext.lower()
                    logging.info("Detected codec '%s' from output file name.",
                        self._codec)
                else:
                    # weird case if the file ends with a period
                    logging.warning(
                        "Cannot determine codec from output file name. "
                        "Defaulting to 'wav'.")
                    self._codec = 'wav'
                    filename += self._codec
            else:
                # no extension, use default codec
                logging.warning("Cannot determine codec from output file name. "
                    "Defaulting to 'wav'.")
                self._codec = 'wav'
                filename += '.' + self._codec

        # set the file name
        self.filename = filename

    def __hash__(self):
        return hash(self._filename)

    @property
    def isOpen(self):
        """Is the audio file writer is open (`bool`)?
        """
        return self._writerThread.is_alive() if self._writerThread else False

    @property
    def filename(self):
        """The name (path) of the movie file (`str`).

        This cannot be changed after the writer has been opened.

        """
        return self._filename

    @filename.setter
    def filename(self, value):
        if self.isOpen:
            raise RuntimeError("Cannot change the filename while the writer is "
                    "open.")

        self._filename = value
        self._absPath = os.path.abspath(self._filename)

    @property
    def sampleRate(self):
        """The sample rate of the audio file (`int`).

        This cannot be changed after the writer has been opened.

        """
        return self._sampleRate

    @property
    def channels(self):
        """The number of audio channels in the file (`int`).

        This cannot be changed after the writer has been opened.

        """
        return self._channels
    
    @property
    def codec(self):
        """The codec used to encode the audio file (`str`).

        This cannot be changed after the writer has been opened.

        """
        return self._codec

    @property
    def encoderLib(self):
        """The library used to encode the audio file (`str`).

        This cannot be changed after the writer has been opened.

        """
        return self._encoderLib

    @property
    def encoderOpts(self):
        """The options used to encode the audio file (`dict`).

        This cannot be changed after the writer has been opened.

        """
        return self._encoderOpts

    @property
    def lastAudioFile(self):
        """The last audio file written to disk (`str`).

        This is the file that was written to disk when the writer was closed. 
        This name may differ from the original file name, therefore it is 
        recommended to use this property to get the final file name after
        writing.

        """
        return self._lastAudioFile

    def _finalize(self):
        """Finalize the audio file writer.

        This will do any cleanup necessary when the writer is closed. This 
        includes converting the temporary file to the proper format if the 
        encoder requires it.

        """
        if self._encoderLib == 'soundfile':
            # Using soundfile requires a temporary file to be converted to the
            # proper format after writing all the samples to disk. This is done
            # by reading the temporary file and writing it to the final file.
            import soundfile as sf

            # read the file
            with sf.SoundFile(self._tempFileName, 'r', 
                    samplerate=self._sampleRate, 
                    channels=self._channels,
                    format='RAW', 
                    subtype=self._formatInfo['subtype']) as f:
                data = f.read()

            # write out file
            with sf.SoundFile(self._absPath, 'w', 
                    samplerate=self._sampleRate, 
                    channels=self._channels, 
                    format='WAV', 
                    subtype=self._formatInfo['subtype']) as f:
                f.write(data)
        else:
            raise NotImplementedError("Unsupported encoder library.")
        
        # delete the temporary files if they exist
        if self._tempFileName is not None:
            if not self._keepTempFile:
                logging.debug("Deleting temporary audio file '%s'...", 
                    self._tempFileName)
                os.remove(self._tempFileName)
                self._tempFileName = None

    def _openSoundFile(self):
        """Open the audio file for writing.

        This will create a new thread for writing audio samples to the file. The
        thread will be started and the file will be opened for writing.

        """
        import soundfile as sf

        # check if the file is already open
        if self.isOpen:
            raise RuntimeError("Audio file writer is already open.")

        # mapping for the soundfile library settings for the codec, these need 
        # to be deteremined based on the codec used
        codecMap = {
            'wav': ('WAV', sf.default_subtype('WAV'), np.int16),
            'wav16': ('WAV', 'PCM_16', np.int16),
            'flac': ('FLAC', sf.default_subtype('FLAC'), np.int16),
            'ogg': ('OGG', sf.default_subtype('OGG'), np.int16),
            'mp3': ('MP3', sf.default_subtype('MP3'), np.int16)
        }

        def _writeSamplesAsync(filename, writerOpts, sampleQueue, readyBarrier, 
                dataLock):
            """Write audio samples to a file asynchronously.

            This function is used to write audio samples to a file in a separate
            thread. It will write samples to the file as they are added to the
            sample queue.

            Parameters
            ----------
            filename : str
                File name for the output.
            writerOpts : dict
                Options used to write the audio file.
            sampleQueue : queue.Queue
                Queue used to store audio samples to be written to the file.
            readyBarrier : threading.Barrier
                Barrier used to synchronize the writer thread with other threads.
            dataLock : threading.Lock
                Lock used to when writing data to attribute of the writer class
                instance from inside the thread.

            """
            # Open a RAW file for writing since saoundfile cannoty append to
            # files in other formats. This will be converted to the proper format
            # after all samples have been written.
            with sf.SoundFile(filename, 'r+', 
                    samplerate=writerOpts['samplerate'], 
                    channels=writerOpts['channels'], 
                    format='RAW', 
                    subtype=writerOpts['subtype']) as f:

                # hold until file is ready for writing
                if readyBarrier is not None:  
                    readyBarrier.wait()

                # main loop to write samples to the file
                while True:
                    samples = sampleQueue.get()  # waited on until a frame is added
                    if samples is AUDIO_DATA_EOF:
                        break  # stop writing to file if we get a None

                    f.seek(0, sf.SEEK_END)
                    f.write(samples)

        logging.debug("Opening temporary audio file '%s' for writing...", 
            self._filename)

        # create a temporary file for writing
        self._tempFileName = self._absPath + '.raw'

        # create a barrier to synchronize the movie writer with other threads
        self._syncBarrier = threading.Barrier(2)

        writerMode = 'w'  # default to write mode
        if self._fileExistsPolicy == 'append':
            writerMode = 'r+'

        # format information for the writer, keep track of this so we know how
        # to write the final file
        self._formatInfo = {
            'samplerate': self._sampleRate,
            'channels': self._channels,
            'format': self._codec,
            'subtype': codecMap[self._codec][1],
            'writerMode': writerMode
        }

        # create the thread
        self._writerThread = threading.Thread(
            target=_writeSamplesAsync,
            args=(self._tempFileName, 
                  self._formatInfo, 
                  self._sampleQueue, 
                  self._syncBarrier, 
                  self._dataLock))

        self._writerThread.start()

        logging.debug("Waiting for audio writer thread to start...")
        self._syncBarrier.wait()  # wait for the thread to start
        logging.debug("Audio writer thread started.")

    def open(self):
        """Open the audio file for writing.

        Calling `submit()` will add audio samples to the file.

        """
        if self.isOpen:
            raise RuntimeError("Audio file writer is already open.")

        global _openAudioWriters
        if self in _openAudioWriters:
            raise RuntimeError("Another audio file writer is already open on "
                    "file.")

        # check if the file exists
        if os.path.exists(self._absPath):
            if self._fileExistsPolicy == 'error':
                raise FileExistsError("Audio file '{}' already exists.".format(
                    self._filename))

        if self._encoderLib == 'soundfile':
            self._openSoundFile()
        else:
            raise NotImplementedError("Unsupported encoder library.")

        _openAudioWriters.add(self)
        logging.info("Audio file '%s' opened for writing.", self._filename)

    def close(self):
        """Close the audio file writer.

        This stops the thread writing audio samples to disk and closes the file.
        After calling this, calling `open()` on the writer will overwrite the 
        file if the filename is the same.

        """
        if self._writerThread is None:
            raise RuntimeError("Audio file writer is not open.")

        # signal the thread to stop
        self.flush()  # wait until the queue is empty
        self._sampleQueue.put(AUDIO_DATA_EOF)
        self._writerThread.join()  # wait on thread to complete

        # clean up
        self._writerThread = None

        self._finalize()  # convert temp file to proper format

        _openAudioWriters.remove(self)
        logging.info("Audio file '%s' closed.", self._filename)

        self._lastAudioFile = self._filename

    def flush(self):
        """Flush the audio file writer.

        This will flush any queued audio samples to the file, waiting until all
        samples have been written.

        """
        if not self.isOpen:
            raise RuntimeError(
                "Cannot flush audio samples. Writer is not open.")

        while self._sampleQueue.qsize() > 0:  # wait until the queue is empty
            time.sleep(0.001)

    def _convertSampleFormat(self, samples):
        """Convert audio samples to a format suitable for writing.

        This will convert the audio samples to the proper format for writing to
        the file. This includes converting the samples to the proper data type
        and scaling the values to the proper range for the encoder used.

        Parameters
        ----------
        samples : ArrayLike
            Nx1 or Nx2 array of audio samples with values ranging between -1 and
            1.

        Returns
        -------
        ndarray
            Nx1 or Nx2 array of audio samples in the proper format for writing.

        """
        if self._encoderLib == 'soundfile':  # soundfile specific conversion
            if isinstance(samples, np.ndarray):  # got a numpy array
                samples = np.atleast_2d(samples)
                if self._formatInfo['subtype'] == 'PCM_16' and samples.dtype != np.int16:
                    # rescale samples and change type to int16
                    samples = np.ascontiguousarray(
                        samples * (MAX_16BITS_SIGNED - 1), dtype=np.int16)
                elif self._formatInfo['subtype'] == 'PCM_24' and samples.dtype != np.int32:
                    # rescale samples and change type to int32
                    samples = np.ascontiguousarray(
                        samples * (MAX_16BITS_SIGNED - 1), dtype=np.int32)
            else:
                raise ValueError("Unsupported sample format.")

        assert samples.shape[1] == self._channels, "Invalid number of channels."

        return samples

    def submit(self, samples):
        """Submit audio samples to be written to the file.

        This is a non-blocking call that will add audio samples to the file. The
        samples will be written to the file in a separate thread. Can be called
        at any time between `open()` and `close()` calls.

        Parameters
        ----------
        samples : ArrayLike
            Nx1 or Nx2 array of audio samples.

        """
        if self._writerThread is None:
            raise RuntimeError("Audio file writer is not open.")

        if samples is None:
            raise ValueError("Cannot write `None` samples to audio file.")

        # transform audio samples to proper format
        samples = self._convertSampleFormat(samples)

        self._sampleQueue.put(samples)

    def addSamples(self, samples):
        """Add audio samples to the file.

        This is an alias for `submit()`. See `submit()` for more information.

        Parameters
        ----------
        samples : ArrayLike
            Nx1 or Nx2 array of audio samples.

        """
        self.submit(samples)

    def __del__(self):
        if self._writerThread is not None:
            self.close()


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
    Work out the max duration of audio able to be recorded given the buffer size 
    (kb) and frequency (Hz).

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


def closeAllAudioWriters():
    """Close all open audio file writers.

    This will close all audio file writers that are currently open. This 
    function is registered to be called at exit automatically to ensure that
    all audio files are closed properly.

    """
    global _openAudioWriters

    if len(_openAudioWriters) == 0:
        logging.debug("No audio file writers to close.")
        return

    logging.debug("Closing all open audio file writers (%d)...",
                  len(_openAudioWriters))

    for writer in _openAudioWriters:
        logging.debug("Closing audio file writer '%s'...", writer._filename)
        writer.close()

    _openAudioWriters.clear()


atexit.register(closeAllAudioWriters)


def test_audio_writer():
    import time

    writer = AudioFileWriter('test3', SAMPLE_RATE_48kHz, keepTempFile=True)
    print(writer._absPath)
    writer.open()

    sineSamples = sawtone(0.5, 440.0, gain=0.8, sampleRateHz=SAMPLE_RATE_48kHz)
    sineSamples2 = sawtone(0.5, 440.0 * 2, gain=0.8, sampleRateHz=SAMPLE_RATE_48kHz)
    noiseSamples = whiteNoise(0.5, sampleRateHz=SAMPLE_RATE_48kHz)

    # generate a 0.5 second ramp
    ramp = np.linspace(0, 1, int(SAMPLE_RATE_48kHz * 0.5)).reshape(-1, 1)  
    print(sineSamples * ramp)

    for i in range(10):
        writer.submit(sineSamples * ramp)

    writer.close()


if __name__ == "__main__":
    test_audio_writer()
