#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Audio capture and analysis using pyo"""

# Author: Jeremy R. Gray, March 2012, March 2013

from __future__ import absolute_import, division, print_function

# from future import standard_library
# standard_library.install_aliases()
from builtins import str
from past.builtins import basestring
from builtins import object
import os
import glob
import threading
from psychopy.constants import PY3
from psychopy.tools.filetools import pathToString

if PY3:
    import urllib.request
    import urllib.error
    import urllib.parse
else:
    import urllib2
    # import urllib.request, urllib.error, urllib.parse

    class FakeURLlib(object):

        def __init__(self, lib):
            self.request = lib
            self.error = lib
            self.parse = lib
    urllib = FakeURLlib(urllib2)

import json
import numpy as np
from scipy.io import wavfile
from psychopy import core, logging, sound, web, prefs
from psychopy.constants import NOT_STARTED, PLAYING, PSYCHOPY_USERAGENT
# import pyo is done within switchOn to better encapsulate it, can be very
# slow and don't want to delay up to 3 sec when importing microphone
# downside: to make this work requires some trickiness with globals

haveMic = False  # goes True in switchOn, if can import pyo

# flac is used for audio compression; user needs to install it
FLAC_PATH = None  # set on first call to _getFlacPath()


class AudioCapture(object):
    """Capture sound sample from the default sound input, and save to a file.

        Untested whether you can have two recordings going on simultaneously.

        **Examples**::

            from psychopy import microphone
            from psychopy import event, visual  # for key events

            microphone.switchOn(sampleRate=16000)  # do once

            # Record for 1.000 seconds, save to mic.savedFile
            mic = microphone.AudioCapture()
            mic.record(1)
            mic.playback()

            # Resample, creates a new file discards orig
            mic.resample(48000, keep=False)

            # Record new file for 60 sec or until key 'q'
            w = visual.Window()  # needed for key-events
            mic.reset()
            mic.record(60, block=False)
            while mic.recorder.running:
                if 'q' in event.getKeys():
                    mic.stop()

        Also see Builder Demo "voiceCapture".

        :Author: Jeremy R. Gray, March 2012
    """

    class _Recorder(object):
        """Class for internal object to make an audio recording using pyo.

        Never needed by end-users; only used internally in __init__:
            self.recorder = _Recorder(None) # instantiate, global
        Then in record(), do:
            self.recorder.run(filename, sec)
        This sets recording parameters, starts recording.
        To stop a recording that is in progress, do
            self.stop()
        This class never handles blocking; AudioCapture has to do that.

        Motivation: Doing pyo Record from within a function worked most of
        the time, but failed catastrophically ~1% of time with a bus error.
        Seemed to be due to a namespace scoping issue, which using globals
        seemed to fix; see pyo mailing list, 7 April 2012. This draws
        heavily on Olivier Belanger's solution.
        """

        def __init__(self):
            self.running = False

        def run(self, filename, sec, sampletype=0, buffering=16,
                chnl=0, chnls=2):
            filename = pathToString(filename)
            self.running = True
            # chnl from psychopy.sound.backend.get_input_devices()
            inputter = pyo.Input(chnl=chnl, mul=1)
            self.recorder = pyo.Record(inputter, filename, chnls=chnls,
                                       fileformat=0, sampletype=sampletype,
                                       buffering=buffering)
            # handles recording offset
            pyo.Clean_objects(sec, self.recorder).start()
            threading.Timer(sec, self._stop).start()  # set running flag False

        def stop(self):
            self.recorder.stop()
            self._stop()

        def _stop(self):
            self.running = False

    def __init__(self, name='mic', filename='', saveDir='', sampletype=0,
                 buffering=16, chnl=0, stereo=True, autoLog=True):
        """
        :Parameters:
            name :
                Stem for the output file, also used in logging.
            filename :
                optional file name to use; default = 'name-onsetTimeEpoch.wav'
            saveDir :
                Directory to use for output .wav files.
                If a saveDir is given, it will return 'saveDir/file'.
                If no saveDir, then return abspath(file)
            sampletype : bit depth
                pyo recording option:
                0=16 bits int, 1=24 bits int; 2=32 bits int
            buffering : pyo argument
            chnl : which audio input channel to record (default=0)
            stereo : how many channels to record
                (default True, stereo; False = mono)
        """
        if not haveMic:
            raise MicrophoneError('Need to call microphone.switchOn()'
                                  ' before AudioCapture or AdvancedCapture')
        self.name = name
        self.saveDir = saveDir
        filename = pathToString(filename)
        if filename:
            self.wavOutFilename = filename
        else:
            self.wavOutFilename = os.path.join(self.saveDir, name + '.wav')
        if not self.saveDir:
            self.wavOutFilename = os.path.abspath(self.wavOutFilename)
        else:
            if not os.path.isdir(self.saveDir):
                os.makedirs(self.saveDir, 0o770)

        self.onset = None  # becomes onset time, used in filename
        self.savedFile = False  # becomes saved file name
        self.status = NOT_STARTED  # for Builder component

        # pyo server good to go?
        if not pyo.serverCreated():
            raise AttributeError('pyo server not created')
        if not pyo.serverBooted():
            raise AttributeError('pyo server not booted')

        self.autoLog = autoLog
        self.loggingId = self.__class__.__name__
        if self.name:
            self.loggingId += ' ' + self.name

        # the recorder object needs to persist, or else get bus errors:
        self.recorder = self._Recorder()
        self.options = {'sampletype': sampletype, 'buffering': buffering,
                        'chnl': chnl, 'chnls': 1 + int(stereo == True)}

    def stop(self, log=True):
        """Interrupt a recording that is in progress; close & keep the file.

        Ends the recording before the duration that was initially specified.
        The same file name is retained, with the same onset time but a
        shorter duration.

        The same recording cannot be resumed after a stop (it is not a pause),
        but you can start a new one.
        """
        if not self.recorder.running:
            if log and self.autoLog:
                msg = '%s: Stop requested, but no record() in progress'
                logging.exp(msg % self.loggingId)
            return
        self.duration = core.getTime() - self.onset  # new shorter duration
        self.recorder.stop()
        if log and self.autoLog:
            msg = '%s: Record stopped early, new duration %.3fs'
            logging.data(msg % (self.loggingId, self.duration))

    def reset(self, log=True):
        """Restores to fresh state, ready to record again
        """
        if log and self.autoLog:
            msg = '%s: resetting at %.3f'
            logging.exp(msg % (self.loggingId, core.getTime()))
        self.__init__(name=self.name, saveDir=self.saveDir)

    def record(self, sec, filename='', block=True):
        """Capture sound input for duration <sec>, save to a file.

        Return the path/name to the new file. Uses onset time (epoch) as
        a meaningful identifier for filename and log.
        """
        return self._record(sec, filename=filename, block=block)

    def _record(self, sec, filename='', block=True, log=True):
        filename = pathToString(filename)
        while self.recorder.running:
            pass
        self.duration = float(sec)
        # for duration estimation, high precision:
        self.onset = core.getTime()
        # use time for unique log and filename, 1 sec precision
        self.fileOnset = core.getAbsTime()
        ms = "%.3f" % (core.getTime() - int(core.getTime()))
        if log and self.autoLog:
            msg = '%s: Record: onset %d, capture %.3fs'
            logging.data(msg % (self.loggingId, self.fileOnset,
                                self.duration))
        if not filename:
            onsettime = '-%d' % self.fileOnset + ms[1:]
            self.savedFile = onsettime.join(
                os.path.splitext(self.wavOutFilename))
        else:
            self.savedFile = os.path.abspath(filename)
            if not self.savedFile.endswith('.wav'):
                self.savedFile += '.wav'

        t0 = core.getTime()
        self.recorder.run(self.savedFile, self.duration, **self.options)

        self.rate = sound.backend.pyoSndServer.getSamplingRate()
        if block:
            core.wait(self.duration, 0)
            if log and self.autoLog:
                msg = '%s: Record: stop. %.3f, capture %.3fs (est)'
                logging.exp(msg % (self.loggingId, core.getTime(),
                                   core.getTime() - t0))
            while self.recorder.running:
                core.wait(.001, 0)
        else:
            if log and self.autoLog:
                msg = '%s: Record: return immediately, no blocking'
                logging.exp(msg % (self.loggingId))

        return self.savedFile

    def playback(self, block=True, loops=0, stop=False, log=True):
        """Plays the saved .wav file, as just recorded or resampled. Execution
        blocks by default, but can return immediately with `block=False`.

        `loops` : number of extra repetitions; 0 = play once

        `stop` : True = immediately stop ongoing playback (if there is one),
        and return
        """
        if not self.savedFile or not os.path.isfile(self.savedFile):
            msg = '%s: Playback requested but no saved file' % self.loggingId
            logging.error(msg)
            raise ValueError(msg)

        if stop:
            if (hasattr(self, 'current_recording') and
                    self.current_recording.status == PLAYING):
                self.current_recording.stop()
            return

        # play this file:
        name = self.name + '.current_recording'
        self.current_recording = sound.Sound(
            self.savedFile, name=name, loops=loops)
        self.current_recording.play()
        if block:
            core.wait(self.duration * (loops + 1))  # set during record()

        if log and self.autoLog:
            if loops:
                msg = '%s: Playback: play %.3fs x %d (est) %s'
                vals = (self.loggingId, self.duration, loops + 1,
                        self.savedFile)
                logging.exp(msg % vals)
            else:
                msg = '%s: Playback: play %.3fs (est) %s'
                logging.exp(msg % (self.loggingId, self.duration,
                                   self.savedFile))

    def resample(self, newRate=16000, keep=True, log=True):
        """Re-sample the saved file to a new rate, return the full path.

        Can take several visual frames to resample a 2s recording.

        The default values for resample() are for Google-speech, keeping the
        original (presumably recorded at 48kHz) to archive.
        A warning is generated if the new rate not an integer factor /
        multiple of the old rate.

        To control anti-aliasing, use pyo.downsamp() or upsamp() directly.
        """
        if not self.savedFile or not os.path.isfile(self.savedFile):
            msg = '%s: Re-sample requested but no saved file' % self.loggingId
            logging.error(msg)
            raise ValueError(msg)
        if newRate <= 0 or type(newRate) != int:
            msg = '%s: Re-sample bad new rate = %s' % (self.loggingId,
                                                       repr(newRate))
            logging.error(msg)
            raise ValueError(msg)

        # set-up:
        if self.rate >= newRate:
            ratio = float(self.rate) / newRate
            info = '-ds%i' % ratio
        else:
            ratio = float(newRate) / self.rate
            info = '-us%i' % ratio
        if ratio != int(ratio):
            msg = '%s: old rate is not an integer factor of new rate'
            logging.warn(msg % self.loggingId)
        ratio = int(ratio)
        newFile = info.join(os.path.splitext(self.savedFile))

        # use pyo's downsamp or upsamp based on relative rates:
        if not ratio:
            msg = '%s: Re-sample by %sx is undefined, skipping'
            logging.warn(msg % (self.loggingId, str(ratio)))
        elif self.rate >= newRate:
            t0 = core.getTime()
            # default 128-sample anti-aliasing
            pyo.downsamp(self.savedFile, newFile, ratio)
            if log and self.autoLog:
                msg = '%s: Down-sampled %sx in %.3fs to %s'
                vals = (self.loggingId, str(ratio), core.getTime() - t0,
                        newFile)
                logging.exp(msg % vals)
        else:
            t0 = core.getTime()
            # default 128-sample anti-aliasing
            pyo.upsamp(self.savedFile, newFile, ratio)
            if log and self.autoLog:
                msg = '%s: Up-sampled %sx in %.3fs to %s'
                vals = (self.loggingId, str(ratio), core.getTime() - t0,
                        newFile)
                logging.exp(msg % vals)

        # clean-up:
        if not keep:
            os.unlink(self.savedFile)
            self.savedFile = newFile
            self.rate = newRate

        return os.path.abspath(newFile)


class AdvAudioCapture(AudioCapture):
    """Class extends AudioCapture, plays marker sound as a "start" indicator.

    Has method for retrieving the marker onset time from the file, to allow
    calculation of vocal RT (or other sound-based RT).

    See Coder demo > input > latencyFromTone.py
    """

    def __init__(self, name='advMic', filename='', saveDir='', sampletype=0,
                 buffering=16, chnl=0, stereo=True, autoLog=True):
        AudioCapture.__init__(self, name=name, filename=filename,
                              saveDir=saveDir, sampletype=sampletype,
                              buffering=buffering, chnl=chnl, stereo=stereo)
        self.setMarker()
        self.autoLog = autoLog

    def record(self, sec, filename='', block=False):
        """Starts recording and plays an onset marker tone just prior
        to returning. The idea is that the start of the tone in the
        recording indicates when this method returned, to enable you to sync
        a known recording onset with other events.
        """
        # get effectively the same timing if play after starting the record
        self.playMarker()
        self.filename = self._record(sec, filename=filename, block=block)
        return self.filename

    def setFile(self, filename):
        """Sets the name of the file to work with.
        """
        self.filename = filename

    def setMarker(self, tone=19000, secs=0.015, volume=0.03, log=True):
        """Sets the onset marker, where `tone` is either in hz or a custom
        sound.

        The default tone (19000 Hz) is recommended for auto-detection,
        as being easier to isolate from speech sounds (and so reliable
        to detect). The default duration and volume are appropriate for
        a quiet setting such as a lab testing room. A louder volume, longer
        duration, or both may give better results when recording loud sounds
        or in noisy environments, and will be auto-detected just fine
        (even more easily). If the hardware microphone in use is not
        physically near the speaker hardware, a louder volume is likely
        to be required.

        Custom sounds cannot be auto-detected, but are supported anyway for
        presentation purposes. E.g., a recording of someone saying "go" or
        "stop" could be passed as the onset marker.
        """
        if hasattr(tone, 'play'):
            self.marker_hz = 0
            self.marker = tone
            if log and self.autoLog:
                logging.exp('custom sound set as marker; getMarkerOnset()'
                            ' will not be able to auto-detect onset')
        else:
            self.marker_hz = float(tone)
            sampleRate = sound.backend.pyoSndServer.getSamplingRate()
            if sampleRate < 2 * self.marker_hz:
                # NyquistError
                msg = ("Recording rate (%i Hz) too slow for %i Hz-based"
                       " marker detection.")
                logging.warning(msg % (int(sampleRate), self.marker_hz))
            if log and self.autoLog:
                msg = 'frequency of recording onset marker: %.1f'
                logging.exp(msg % self.marker_hz)
            self.marker = sound.Sound(self.marker_hz, secs, volume=volume,
                                      name=self.name + '.marker_tone')

    def playMarker(self):
        """Plays the current marker sound. This is automatically called at the
        start of recording, but can be called anytime to insert a marker.
        """
        self.marker.play()

    def getMarkerInfo(self):
        """Returns (hz, duration, volume) of the marker sound.
        Custom markers always return 0 hz (regardless of the sound).
        """
        dur, vol = self.marker.getDuration(), self.marker.getVolume()
        return self.marker_hz, dur, vol

    def getMarkerOnset(self, chunk=128, secs=0.5, filename=''):
        """Return (onset, offset) time of the first marker within the
        first `secs` of the saved recording.

        Has approx ~1.33ms resolution at 48000Hz, chunk=64. Larger chunks
        can speed up processing times, at a sacrifice of some resolution,
        e.g., to pre-process long recordings with multiple markers.

        If given a filename, it will first set that file as the one to
        work with, and then try to detect the onset marker.
        """
        while self.recorder.running:
            core.wait(0.10, 0)
        if filename:
            self.setFile(filename)
        else:
            filename = self.filename

        return getMarkerOnset(chunk=chunk, secs=secs,
                              filename=filename,
                              marker_hz=self.marker_hz,
                              marker_duration=self.marker.getDuration())

    def getLoudness(self):
        """Return the RMS loudness of the saved recording.
        """
        # use cached value unless the file has changed, based on its mod time:
        try:
            mtime = os.path.getmtime(self.savedFile)
        except (OSError, TypeError):
            logging.error('%s no .savedFile, try again' % self.name)
            core.wait(0.01, 0)
            if not self.savedFile or not os.path.exists(self.savedFile):
                raise ValueError('no such file')
            mtime = os.path.getmtime(self.savedFile)
        if not hasattr(self, 'rms') or self.mtime != mtime:
            self.rms = getRMS(self.savedFile)  # ~3ms for 2s file
            self.mtime = mtime
        return self.rms

    def compress(self, keep=False):
        """Compress using FLAC (lossless compression).
        """
        if os.path.isfile(self.savedFile) and self.savedFile.endswith('.wav'):
            self.savedFile = wav2flac(self.savedFile, keep=keep)

    def uncompress(self, keep=False):
        """Uncompress from FLAC to .wav format.
        """
        isFlac = self.savedFile.endswith('.flac')
        if os.path.isfile(self.savedFile) and isFlac:
            self.savedFile = flac2wav(self.savedFile, keep=keep)


def getMarkerOnset(filename, chunk=128, secs=0.5, marker_hz=19000,
                   marker_duration=0.015):
    """Returns marker sound (onset, offset) in sec, as read from filename.
    """
    def thresh2SD(data, mult=2, thr=None):
        """Return index of first value in abs(data) exceeding 2 * std(data),
        or length of the data + 1 if nothing > threshold

        Return threshold so can re-use the same threshold later
        """
        # this algorithm could use improvement
        data = abs(data)
        if not thr:
            thr = mult * np.std(data)
        val = data[(data > thr)]
        if not len(val):
            return len(data) + 1, thr
        first = val[0]
        for i, v in enumerate(data):
            if v == first:
                return i, thr

    # read data from file:
    data, sampleRate = readWavFile(filename)
    if marker_hz == 0:
        raise ValueError("Custom marker sounds cannot be auto-detected.")
    if sampleRate < 2 * marker_hz:
        # NyquistError
        msg = "Recording rate (%i Hz) too slow for %i Hz-based marker detection."
        raise ValueError(msg % (int(sampleRate), marker_hz))

    # extract onset:
    chunk = max(16, chunk)  # trades-off against size of bandpass filter
    # precision in time-domain (= smaller chunks) requires wider freq
    # {16: 2400, 32: 1200, 64: 600, 128: 300}
    bandSize = 150 * 2 ** (8 - int(np.log2(chunk)))
    dataToUse = data[:int(sampleRate * secs)]  # only look at first secs
    lo = max(0, marker_hz - bandSize)  # for bandpass filter
    hi = marker_hz + bandSize
    dftProfile = getDftBins(dataToUse, sampleRate, lo, hi, chunk)
    # leading edge of startMarker in chunks
    onsetChunks, thr = thresh2SD(dftProfile)
    onsetSecs = onsetChunks * chunk / sampleRate  # in secs

    # extract offset:
    ratio = chunk / sampleRate
    start = onsetChunks - 4
    stop = int(onsetChunks + marker_duration / ratio) + 4
    backwards = dftProfile[max(start, 0):min(stop, len(dftProfile))]
    offChunks, _junk = thresh2SD(backwards[::-1], thr=thr)
    offSecs = (start + len(backwards) - offChunks) * ratio
    # in secs

    return onsetSecs, offSecs


def readWavFile(filename):
    """Return (data, sampleRate) as read from a wav file, expects int16 data.
    """
    filename = pathToString(filename)
    try:
        sampleRate, data = wavfile.read(filename)
    except Exception:
        if os.path.exists(filename) and os.path.isfile(filename):
            core.wait(0.01, 0)
        try:
            sampleRate, data = wavfile.read(filename)
        except Exception:
            msg = 'Failed to open wav sound file "%s"'
            raise SoundFileError(msg % filename)
    if data.dtype != 'int16':
        msg = 'expected `int16` data in .wav file %s'
        raise AttributeError(msg % filename)
    if len(data.shape) == 2 and data.shape[1] == 2:
        data = data.transpose()
        data = data[0]  # left channel only? depends on how the file was made
    return data, sampleRate


def getDftBins(data=None, sampleRate=None, low=100, high=8000, chunk=64):
    """Return DFT (discrete Fourier transform) of ``data``, doing so in
    time-domain bins, each of size ``chunk`` samples.

    e.g., for getting FFT magnitudes in a ms-by-ms manner.

    If given a sampleRate, the data are bandpass filtered (low, high).
    """
    # good to reshape & vectorize data rather than use a python loop
    if data is None:
        data = []
    bins = []
    i = chunk
    if sampleRate:
        # just to get freq vector
        _junk, freq = getDft(data[:chunk], sampleRate)
        band = (freq > low) & (freq < high)  # band (frequency range)
    while i <= len(data):
        magn = getDft(data[i - chunk:i])
        if sampleRate:
            bins.append(np.std(magn[band]))  # filtered by frequency
        else:
            bins.append(np.std(magn))  # unfiltered
        i += chunk
    return np.array(bins)


def getDft(data, sampleRate=None, wantPhase=False):
    """Compute and return magnitudes of numpy.fft.fft() of the data.

    If given a sample rate (samples/sec), will return (magn, freq).
    If wantPhase is True, phase in radians is also returned
    (magn, freq, phase). data should have power-of-2 samples,
    or will be truncated.
    """
    # www.vibrationdata.com/Shock_and_Vibration_Signal_Analysis.pdf
    # and .../python/fft.py
    # truncate to power-of-2 slice; zero-padding to round up is ok too
    samples = 2 ** int(np.log2(len(data)))
    samplesHalf = samples // 2
    dataSlice = data[:samples]

    # get magn & phase from the DFT:
    dft = np.fft.fft(dataSlice)
    dftHalf = dft[:samplesHalf] / samples
    magn = abs(dftHalf) * 2
    magn[0] /= 2.
    if wantPhase:
        phase = np.arctan2(dftHalf.real, dftHalf.imag)  # in radians
    if sampleRate:
        deltaf = sampleRate / samplesHalf / 2.
        freq = np.linspace(0, samplesHalf * deltaf,
                           samplesHalf, endpoint=False)
        if wantPhase:
            return magn, freq, phase
        return magn, freq
    else:
        if wantPhase:
            return magn, phase
        return magn


def getRMSBins(data, chunk=64):
    """Return RMS (loudness) in bins of ``chunk`` samples
    """
    # better to vectorize
    bins = []
    i = chunk
    while i <= len(data):
        r = getRMS(data[i - chunk:i])
        bins.append(r)
        i += chunk
    return np.array(bins)


def getRMS(data):
    """Compute and return the audio power ("loudness").

    Uses numpy.std() as RMS. std() is same as RMS if the mean is 0,
    and .wav data should have a mean of 0.
    Returns an array if given stereo data (RMS computed within-channel).

    `data` can be an array (1D, 2D) or filename; .wav format only.
    data from .wav files will be normalized to -1..+1 before RMS is computed.
    """
    def _rms(data):
        """Audio loudness / power, as rms; ~2x faster than std()
        """
        if len(data.shape) > 1:
            return np.std(data, axis=1)  # np.sqrt(np.mean(data ** 2, axis=1))
        return np.std(data)  # np.sqrt(np.mean(data ** 2))
    if isinstance(data, basestring):
        if not os.path.isfile(data):
            raise ValueError('getRMS: could not find file %s' % data)
        _junk, data = wavfile.read(data)
        data_tr = np.transpose(data)
        data = data_tr / 32768.
    elif not isinstance(data, np.ndarray):
        data = np.array(data).astype(np.float)
    return _rms(data)


class SoundFormatNotSupported(Exception):
    """Class to report an unsupported sound format"""


class SoundFileError(Exception):
    """Class to report sound file failed to load"""


class MicrophoneError(Exception):
    """Class to report a microphone error"""


class _GSQueryThread(threading.Thread):
    """Internal thread class to send a sound file to Google, stash the response.
    """

    def __init__(self, request):
        threading.Thread.__init__(self, None, 'GoogleSpeechQuery', None)

        # request is a previously established urllib2.request() obj, namely:
        # request = urllib2.Request(url, audio, header) at end of
        # Speech2Text.__init__
        self.request = request

        # set vars and flags:
        self.t0 = None
        self.response = None
        self.duration = None
        self.stopflag = False
        self.running = False
        self.timedout = False
        self._reset()

    def _reset(self):
        # whether run() has been started, not thread start():
        self.started = False
        # initialize data fields that will be exposed:
        self.confidence = None
        self.json = None
        self.raw = ''
        self.word = ''
        self.detailed = ''
        self.words = []

    def elapsed(self):
        # report duration depending on the state of the thread:
        if self.started is False:
            return None
        elif self.running:
            return core.getTime() - self.t0
        else:  # whether timed-out or not:
            return self.duration

    def _unpackRaw(self):
        # parse raw url response from google, expose via data fields (see
        # _reset):
        if type(self.raw) != str:
            self.json = json.load(self.raw)
        else:
            self._reset()
            self.status = 'FAILED'
            self.stop()
            return
        self.status = self.json['status']
        report = []
        for utter_list in self.json["hypotheses"]:
            for k in utter_list:
                report.append("%-10s : %s" % (k, utter_list[k]))
                if k == 'confidence':
                    self.conf = self.confidence = float(utter_list[k])
        for key in self.json:
            if key != "hypotheses":
                report.append("%-10s : %s" % (key, self.json[key]))
        self.detailed = '\n'.join(report)
        self.words = tuple([line.split(':')[1].lstrip() for line in report
                            if line.startswith('utterance')])
        if len(self.words):
            self.word = self.words[0]
        else:
            self.word = ''

    def run(self):
        self.t0 = core.getTime()  # before .running goes True
        self.running = True
        self.started = True
        self.duration = 0
        try:
            self.raw = urllib.request.urlopen(self.request)
        except Exception:  # pragma: no cover
            # yeah, its the internet, stuff happens
            # maybe temporary HTTPError: HTTP Error 502: Bad Gateway
            try:
                self.raw = urllib.request.urlopen(self.request)
            except Exception as ex:  # or maybe a dropped connection, etc
                logging.error(str(ex))
                self.running = False  # proceeds as if "timedout"
        self.duration = core.getTime() - self.t0
        # if no one called .stop() in the meantime, unpack the data:
        if self.running:
            self._unpackRaw()
            self.running = False
            self.timedout = False
        else:
            self.timedout = True

    def stop(self):
        self.running = False


class Speech2Text(object):
    """Class for speech-recognition (voice to text), using Google's public API.

        Google's speech API is currently free to use, and seems to work well.
        Intended for within-experiment processing (near real-time, 1-2s delayed), in which
        it's often important to skip a slow or failed response, and not wait a long time;
        `BatchSpeech2Text()` reverses these priorities.

        It is possible (and
        perhaps even likely) that Google will start charging for usage. In addition, they
        can change the interface at any time, including in the middle of an experiment.
        (If so, please post to the user list and we'll try to develop a fix, but
        there could still be some downtime.) Presumably, confidential
        or otherwise sensitive voice data should not be sent to google.

        :Note:

            Requires that flac is installed (free download from  https://xiph.org/flac/download.html).
            If you download and install flac, but get an error that flac is missing,
            try setting the full path to flac in preferences -> general -> flac.

        :Usage:

        a) Always import and make an object; no data are available yet::

            from microphone import Speech2Text
            gs = Speech2Text('speech_clip.wav') # set-up only

        b) Then, either: Initiate a query and wait for response from google (or until the time-out limit is reached). This is "blocking" mode, and is the easiest to do::

            resp = gs.getResponse() # execution blocks here
            print(resp.word, resp.confidence)

        c) Or instead (advanced usage): Initiate a query, but do not wait for a response ("thread" mode: no blocking, no timeout, more control). `running` will change to False when a response is received (or hang indefinitely if something goes wrong--so you might want to implement a time-out as well)::

            resp = gs.getThread() # returns immediately
            while resp.running:
                print('.',) # displays dots while waiting
                sys.stdout.flush()
                core.wait(0.1)
            print(resp.words)

        d) Options: Set-up with a different language for the same speech clip; you'll get a different response (possibly having UTF-8 characters)::

            gs = Speech2Text('speech_clip.wav', lang='ja-JP')
            resp = gs.getResponse()

        :Example:

            See Coder demos / input / speech_recognition.py

        :Known limitations:

            Availability is subject to the whims of google. Any changes google
            makes along the way could either cause complete failure (disruptive),
            or could cause slightly different results to be obtained (without it being
            readily obvious that something had changed). For this reason,
            it's probably a good idea to re-run speech samples through `Speech2Text` at the end of
            a study; see `BatchSpeech2Text()`.

        :Author: Jeremy R. Gray, with thanks to Lefteris Zafiris for his help
            and excellent command-line perl script at https://github.com/zaf/asterisk-speech-recog (GPLv2)
    """

    def __init__(self, filename,
                 lang='en-US',
                 timeout=10,
                 samplingrate=16000,
                 pro_filter=2,
                 level=0):
        """
            :Parameters:

                `filename` : <required>
                    name of the speech file (.flac, .wav, or .spx) to process. wav files will be
                    converted to flac, and for this to work you need to have flac (as an
                    executable). spx format is speex-with-headerbyte (for Google).
                `lang` :
                    the presumed language of the speaker, as a locale code; default 'en-US'
                `timeout` :
                    seconds to wait before giving up, default 10
                `samplingrate` :
                    the sampling rate of the speech clip in Hz, either 16000 or 8000. You can
                    record at a higher rate, and then down-sample to 16000 for speech
                    recognition. `file` is the down-sampled file, not the original.
                    the sampling rate is auto-detected for .wav files.
                `pro_filter` :
                    profanity filter level; default 2 (e.g., f***)
                `level` :
                    flac compression level (0 less compression but fastest)
        """
        # set up some key parameters:
        results = 5  # how many words wanted
        self.timeout = timeout
        useragent = PSYCHOPY_USERAGENT
        host = "www.google.com/speech-api/v1/recognize"

        # determine file type, convert wav to flac if needed:
        if not os.path.isfile(filename):
            raise IOError("Cannot find file: %s" % filename)
        ext = os.path.splitext(filename)[1]
        if ext not in ['.flac', '.wav']:
            raise SoundFormatNotSupported("Unsupported filetype: %s\n" % ext)
        if ext == '.wav':
            _junk, samplingrate = readWavFile(filename)
        if samplingrate not in [16000, 8000]:
            raise SoundFormatNotSupported(
                'Speech2Text sample rate must be 16000 or 8000 Hz')
        self.filename = filename
        if ext == ".flac":
            filetype = "x-flac"
        elif ext == ".wav":  # convert to .flac
            filetype = "x-flac"
            filename = wav2flac(filename, level=level)  # opt for speed
        logging.info("Loading: %s as %s, audio/%s" %
                     (self.filename, lang, filetype))
        # occasional error; core.wait(.1) is not always enough; better slow
        # than fail
        c = 0
        while not os.path.isfile(filename) and c < 10:
            core.wait(.1, 0)
            c += 1
        audio = open(filename, 'rb').read()
        if ext == '.wav' and filename.endswith('.flac'):
            try:
                os.remove(filename)
            except Exception:
                pass

        # urllib2 makes no attempt to validate the server certificate. here's an idea:
        # http://thejosephturner.com/blog/2011/03/19/https-certificate-verification-in-python-with-urllib2/
        # set up the https request:
        url = 'https://' + host + '?xjerr=1&' +\
              'client=psychopy3&' +\
              'lang=' + lang + '&'\
              'pfilter=%d' % pro_filter + '&'\
              'maxresults=%d' % results
        header = {'Content-Type': 'audio/%s; rate=%d' % (filetype, samplingrate),
                  'User-Agent': useragent}
        web.requireInternetAccess()  # needed to access google's speech API
        try:
            self.request = urllib.request.Request(url, audio, header)
        except Exception:  # pragma: no cover
            # try again before accepting defeat
            logging.info("https request failed. %s, %s. trying again..." %
                         (filename, self.filename))
            core.wait(0.2, 0)
            self.request = urllib.request.Request(url, audio, header)

    def getThread(self):
        """Send a query to Google using a new thread, no blocking or timeout.

        Returns a thread which will **eventually** (not immediately) have the speech
        data in its namespace; see getResponse. In theory, you could have several
        threads going simultaneously (almost all the time is spent waiting for a
        response), rather than doing them sequentially (not tested).
        """
        gsqthread = _GSQueryThread(self.request)
        gsqthread.start()
        logging.info("Sending speech-recognition https request to google")
        gsqthread.file = self.filename
        while not gsqthread.running:
            # can return too quickly if thread is slow to start
            core.wait(0.001, 0)
        return gsqthread  # word and time data will eventually be in the namespace

    def getResponse(self):
        """Calls `getThread()`, and then polls the thread until there's a response.

        Will time-out if no response comes within `timeout` seconds. Returns an
        object having the speech data in its namespace. If there's no match,
        generally the values will be equivalent to `None` (e.g., an empty string).

        If you do `resp = getResponse()`, you'll be able to access the data
        in several ways:

            `resp.word` :
                the best match, i.e., the most probably word, or `None`
            `resp.confidence` :
                Google's confidence about `.word`, ranging 0 to 1
            `resp.words` :
                tuple of up to 5 guesses; so `.word` == `.words[0]`
            `resp.raw` :
                the raw response from Google (just a string)
            `resp.json` :
                a parsed version of raw, from `json.load(raw)`
        """
        gsqthread = self.getThread()
        while gsqthread.elapsed() < self.timeout:
            # don't need precise timing to poll an http connection
            core.wait(0.05, 0)
            if not gsqthread.running:
                break
        if gsqthread.running:  # timed out
            gsqthread.status = 408  # same as http code
        return gsqthread  # word and time data are already in the namespace


class BatchSpeech2Text(list):

    def __init__(self, files, threads=3, verbose=False):
        """Like `Speech2Text()`, but takes a list of sound files or a directory name to search
        for matching sound files, and returns a list of `(filename, response)` tuples.
        `response`'s are described in `Speech2Text.getResponse()`.

        Can use up to 5 concurrent threads. Intended for
        post-experiment processing of multiple files, in which waiting for a slow response
        is not a problem (better to get the data).

        If `files` is a string, it will be used as a directory name for glob
        (matching all `*.wav`, `*.flac`, and `*.spx` files).
        There's currently no re-try on http error."""
        list.__init__(self)  # [ (file1, resp1), (file2, resp2), ...]
        maxThreads = min(threads, 5)  # I get http errors with 6
        self.timeout = 30
        if type(files) == str and os.path.isdir(files):
            f = glob.glob(os.path.join(files, '*.wav'))
            f += glob.glob(os.path.join(files, '*.flac'))
            f += glob.glob(os.path.join(files, '*.spx'))
            fileList = f
        else:
            fileList = list(files)
        web.requireInternetAccess()  # needed to access google's speech API
        for i, filename in enumerate(fileList):
            gs = Speech2Text(filename, level=5)
            self.append((filename, gs.getThread()))  # tuple
            if verbose:
                logging.info("%i %s" % (i, filename))
            while self._activeCount() >= maxThreads:
                core.wait(.1, 0)  # idle at max count

    def _activeCount(self):
        # self is a list of (name, thread) tuples; count active threads
        count = len(
            [f for f, t in self if t.running and t.elapsed() <= self.timeout])
        return count


def _getFlacPath(path=None):
    """Return a path to flac binary. Log flac version (if flac was found).
    """
    global FLAC_PATH
    if FLAC_PATH is None:
        if path:
            FLAC_PATH = path
        elif prefs.general['flac']:
            FLAC_PATH = prefs.general['flac']
        else:
            FLAC_PATH = 'flac'
        try:
            version, se = core.shellCall([FLAC_PATH, '-v'], stderr=True)
            if se:
                raise MicrophoneError
        except Exception:
            msg = ("flac not installed (or wrong path in prefs); "
                   "download from https://xiph.org/flac/download.html")
            logging.error(msg)
            raise MicrophoneError(msg)
        logging.info('Using ' + version)
    return FLAC_PATH


def flac2wav(path, keep=True):
    """Uncompress: convert .flac file (on disk) to .wav format (new file).

    If `path` is a directory name, convert all .flac files in the directory.

    `keep` to retain the original .flac file(s), default `True`.
    """
    flac_path = _getFlacPath()
    flac_files = []
    path = pathToString(path)
    if path.endswith('.flac'):
        flac_files = [path]
    elif type(path) == str and os.path.isdir(path):
        flac_files = glob.glob(os.path.join(path, '*.flac'))
    if len(flac_files) == 0:
        logging.warn('failed to find .flac file(s) from %s' % path)
        return None
    wav_files = []
    for flacfile in flac_files:
        wavname = flacfile.strip('.flac') + '.wav'
        flac_cmd = [flac_path, "-d", "--totally-silent",
                    "-f", "-o", wavname, flacfile]
        _junk, se = core.shellCall(flac_cmd, stderr=True)
        if se:
            logging.error(se)
        if not keep:
            os.unlink(flacfile)
        wav_files.append(wavname)
    if len(wav_files) == 1:
        return wav_files[0]
    else:
        return wav_files


def wav2flac(path, keep=True, level=5):
    """Lossless compression: convert .wav file (on disk) to .flac format.

    If `path` is a directory name, convert all .wav files in the directory.

    `keep` to retain the original .wav file(s), default `True`.

    `level` is compression level: 0 is fastest but larger,
        8 is slightly smaller but much slower.
    """
    flac_path = _getFlacPath()
    wav_files = []
    path = pathToString(path)
    if path.endswith('.wav'):
        wav_files = [path]
    elif type(path) == str and os.path.isdir(path):
        wav_files = glob.glob(os.path.join(path, '*.wav'))
    if len(wav_files) == 0:
        logging.warn('failed to find .wav file(s) from %s' % path)
        return None
    flac_files = []
    for wavname in wav_files:
        flacfile = wavname.replace('.wav', '.flac')
        flac_cmd = [flac_path, "-%d" % level, "-f",
                    "--totally-silent", "-o", flacfile, wavname]
        _junk, se = core.shellCall(flac_cmd, stderr=True)
        if se or not os.path.isfile(flacfile):  # just try again
            # ~2% incidence when recording for 1s, 650+ trials
            # never got two in a row; core.wait() does not help
            logging.warn('Failed to convert to .flac; trying again')
            _junk, se = core.shellCall(flac_cmd, stderr=True)
            if se:
                logging.error(se)
        if not keep:
            os.unlink(wavname)
        flac_files.append(flacfile)
    if len(wav_files) == 1:
        return flac_files[0]
    else:
        return flac_files


def switchOn(sampleRate=48000, outputDevice=None, bufferSize=None):
    """You need to switch on the microphone before use, which can take
    several seconds. The only time you can specify the sample rate (in Hz)
    is during switchOn().

    Considerations on the default sample rate 48kHz::

        DVD or video = 48,000
        CD-quality   = 44,100 / 24 bit
        human hearing: ~15,000 (adult); children & young adult higher
        human speech: 100-8,000 (useful for telephone: 100-3,300)
        Google speech API: 16,000 or 8,000 only
        Nyquist frequency: twice the highest rate, good to oversample a bit

    pyo's downsamp() function can reduce 48,000 to 16,000 in about 0.02s
    (uses integer steps sizes). So recording at 48kHz will generate
    high-quality archival data, and permit easy downsampling.

    outputDevice, bufferSize: set these parameters on the pyoSndServer
        before booting; None means use pyo's default values
    """
    # imports pyo, creates sound.pyoSndServer using sound.initPyo() if not yet
    # created
    t0 = core.getTime()
    try:
        global pyo
        import pyo
        global haveMic
        haveMic = True
    except ImportError:  # pragma: no cover
        msg = ('Microphone class not available, needs pyo; '
               'see http://code.google.com/p/pyo/')
        logging.error(msg)
        raise ImportError(msg)
    if pyo.serverCreated():
        sound.backend.pyoSndServer.setSamplingRate(sampleRate)
    else:
        # sound.init() will create pyoSndServer. We want there only
        # ever to be one server
        # will automatically use duplex=1 and stereo if poss
        sound.init(rate=sampleRate)
    if outputDevice:
        sound.backend.pyoSndServer.setOutputDevice(outputDevice)
    if bufferSize:
        sound.backend.pyoSndServer.setBufferSize(bufferSize)
    logging.exp('%s: switch on (%dhz) took %.3fs' %
                (__file__.strip('.py'), sampleRate, core.getTime() - t0))


def switchOff():
    """(Not needed as of v1.76.00; kept for backwards compatibility only.)
    """
    logging.info("deprecated:  microphone.switchOff() is no longer needed.")
