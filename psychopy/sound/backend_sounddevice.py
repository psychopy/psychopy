#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from builtins import str
from builtins import object
import sys
import os
import time
import re
import atexit

try:
    import readline  # Work around GH-2230
except ImportError:
    pass  # all that will happen is the stderr/stdout might get redirected

from psychopy import logging, exceptions
from psychopy.constants import (PLAYING, PAUSED, FINISHED, STOPPED,
                                NOT_STARTED, PY3)
from psychopy.exceptions import SoundFormatError, DependencyError
from ._base import _SoundBase, HammingWindow

try:
    import sounddevice as sd
except Exception:
    raise DependencyError("sounddevice not working")
try:
    import soundfile as sf
except Exception:
    raise DependencyError("soundfile not working")

import numpy as np

travisCI = bool(str(os.environ.get('TRAVIS')).lower() == 'true')

logging.info("Loaded SoundDevice with {}".format(sd.get_portaudio_version()[1]))


def init(rate=44100, stereo=True, buffer=128):
    pass  # for compatibility with other backends


def getDevices(kind=None):
    """Returns a dict of dict of audio devices of specified `kind`

    The dict keys are names and items are dicts of properties
    """
    devs = {}
    if travisCI:  # travis-CI testing does not have a sound device
        return devs
    else:
        allDevs = sd.query_devices(kind=kind)
    # annoyingly query_devices is a DeviceList or a dict depending on number
    if type(allDevs) == dict:
        allDevs = [allDevs]
    for ii, dev in enumerate(allDevs):
        # newline characters must be removed
        devName = dev['name'].replace('\r\n','')
        devs[devName] = dev
        dev['id'] = ii
    return devs


# these will be controlled by sound.__init__.py
defaultInput = None
defaultOutput = None


def getStreamLabel(sampleRate, channels, blockSize):
    """Returns the string repr of the stream label
    """
    return "{}_{}_{}".format(sampleRate, channels, blockSize)


class _StreamsDict(dict):
    """Keeps track of what streams have been created. On macOS we can have
    multiple streams under portaudio but under windows we can only have one.

    use the instance `streams` rather than creating a new instance of this
    """

    def getStream(self, sampleRate, channels, blockSize):
        """Gets a stream of exact match or returns a new one
        (if possible for the current operating system)
        """
        # if the query looks flexible then try getSimilar
        if channels == -1 or blockSize == -1:
            return self._getSimilar(sampleRate,
                                    channels=channels,
                                    blockSize=blockSize)
        else:
            return self._getStream(sampleRate,
                                   channels=channels,
                                   blockSize=blockSize)

    def _getSimilar(self, sampleRate, channels=-1, blockSize=-1):
        """Do we already have a compatible stream?

        Many sounds can allow channels and blocksize to change but samplerate
        is generally fixed. Any values set to -1 above will be flexible. Any
        values set to an alternative number will be fixed

        usage:

            label, stream = streams._getSimilar(sampleRate=44100,  # must match
                                               channels=-1,  # any
                                               blockSize=-1)  # wildcard
        """
        label = getStreamLabel(sampleRate, channels, blockSize)
        # replace -1 with any regex integer
        simil = re.compile(label.replace("-1", r"[-+]?(\d+)"))  # I hate REGEX!
        for thisFormat in self:
            if simil.match(thisFormat):  # we found a close-enough match
                return thisFormat, self[thisFormat]
        # if we've been given values in each place then create stream
        if (sampleRate not in [None, -1, 0] and
                    channels not in [None, -1] and
                    blockSize not in [None, -1]):
            return self._getStream(sampleRate, channels, blockSize)

    def _getStream(self, sampleRate, channels, blockSize):
        """Strict check for this format or create new
        """
        label = getStreamLabel(sampleRate, channels, blockSize)
        # try to retrieve existing stream of that name
        if label in self:
            pass
        # on some systems more than one stream isn't supported so check
        elif sys.platform == 'win32' and len(self):
            raise exceptions.SoundFormatError(
                "Tried to create audio stream {} but {} already exists "
                "and {} doesn't support multiple portaudio streams"
                    .format(label, list(self.keys())[0], sys.platform)
            )
        else:
            # create new stream
            self[label] = _SoundStream(sampleRate, channels, blockSize,
                                       device=defaultOutput)
        return label, self[label]


streams = _StreamsDict()


class _SoundStream(object):
    def __init__(self, sampleRate, channels, blockSize,
                 device=None, duplex=False):
        # initialise thread
        self.streams = []
        self.list = []
        # sound stream info
        self.sampleRate = sampleRate
        self.channels = channels
        self.duplex = duplex
        self.blockSize = blockSize
        self.label = getStreamLabel(sampleRate, channels, blockSize)
        if device == 'default':
            device = None
        self.sounds = []  # list of dicts for sounds currently playing
        self.takeTimeStamp = False
        self.frameN = 1
        # self.frameTimes = range(5)  # DEBUGGING: store the last 5 callbacks
        if not travisCI:  # travis-CI testing does not have a sound device
            self._sdStream = sd.OutputStream(samplerate=self.sampleRate,
                                             blocksize=self.blockSize,
                                             latency='low',
                                             device=device,
                                             channels=self.channels,
                                             callback=self.callback)
            self._sdStream.start()
            self.device = self._sdStream.device
            self.latency = self._sdStream.latency
            self.cpu_load = self._sdStream.cpu_load
            atexit.register(self.__del__)
        self._tSoundRequestPlay = 0

    def callback(self, toSpk, blockSize, timepoint, status):
        """This is a callback for the SoundDevice lib

        fromMic is data from the mic that can be extracted
        toSpk is a numpy array to be populated with data
        blockSize is the number of frames to be included each block
        timepoint has values:
            .currentTime
            .inputBufferAdcTime
            .outputBufferDacTime
        """
        if self.takeTimeStamp and hasattr(self, 'lastFrameTime'):
            logging.info("Entered callback: {} ms after last frame end"
                         .format((time.time() - self.lastFrameTime) * 1000))
            logging.info("Entered callback: {} ms after sound start"
                         .format(
                (time.time() - self._tSoundRequestPlay) * 1000))
        t0 = time.time()
        self.frameN += 1
        toSpk.fill(0)
        for thisSound in list(self.sounds): # copy (Py2 doesn't have list.copy)
            dat = thisSound._nextBlock()  # fetch the next block of data
            dat *= thisSound.volume  # Set the volume block by block
            if self.channels == 2 and len(dat.shape) == 2:
                toSpk[:len(dat), :] += dat  # add to out stream
            elif self.channels == 2 and len(dat.shape) == 1:
                toSpk[:len(dat), 0] += dat  # add to out stream
                toSpk[:len(dat), 1] += dat  # add to out stream
            elif self.channels == 1 and len(dat.shape) == 2:
                toSpk[:len(dat), :] += dat  # add to out stream
            else:
                toSpk[:len(dat), 0] += dat  # add to out stream
            # check if that was a short block (sound is finished)
            if len(dat) < len(toSpk[:, :]):
                self.remove(thisSound)
                thisSound._EOS()
                # check if that took a long time
                # t1 = time.time()
                # if (t1-t0) > 0.001:
                #     logging.debug("buffer_callback took {:.3f}ms that frame"
                #                  .format((t1-t0)*1000))
                # self.frameTimes.pop(0)
                # if hasattr(self, 'lastFrameTime'):
                #     self.frameTimes.append(time.time()-self.lastFrameTime)
                # self.lastFrameTime = time.time()
                # if self.takeTimeStamp:
                #     logging.debug("Callback durations: {}".format(self.frameTimes))
                #     self.takeTimeStamp = False

    def add(self, sound):
        # t0 = time.time()
        self.sounds.append(sound)
        # logging.debug("took {} ms to add".format((time.time()-t0)*1000))

    def remove(self, sound):
        if sound in self.sounds:
            self.sounds.remove(sound)

    def __del__(self):
        if hasattr(self, '_sdStream'):
            if not travisCI:
                self._sdStream.stop()
            del self._sdStream
        if hasattr(sys, 'stdout'):
            sys.stdout.flush()
        if PY3:
            atexit.unregister(self.__del__)


class SoundDeviceSound(_SoundBase):
    """Play a variety of sounds using the new SoundDevice library
    """

    def __init__(self, value="C", secs=0.5, octave=4, stereo=-1,
                 volume=1.0, loops=0,
                 sampleRate=None, blockSize=128,
                 preBuffer=-1,
                 hamming=True,
                 startTime=0, stopTime=-1,
                 name='', autoLog=True):
        """
        :param value: note name ("C","Bfl"), filename or frequency (Hz)
        :param secs: duration (for synthesised tones)
        :param octave: which octave to use for note names (4 is middle)
        :param stereo: -1 (auto), True or False
                        to force sounds to stereo or mono
        :param volume: float 0-1
        :param loops: number of loops to play (-1=forever, 0=single repeat)
        :param sampleRate: sample rate for synthesized tones
        :param blockSize: the size of the buffer on the sound card
                         (small for low latency, large for stability)
        :param preBuffer: integer to control streaming/buffering
                           - -1 means store all
                           - 0 (no buffer) means stream from disk
                           - potentially we could buffer a few secs(!?)
        :param hamming: boolean (default True) to indicate if the sound should
                        be apodized (i.e., the onset and offset smoothly ramped up from
                        down to zero). The function apodize uses a Hanning window, but
                        arguments named 'hamming' are preserved so that existing code
                        is not broken by the change from Hamming to Hanning internally.
                        Not applied to sounds from files.
        :param startTime: for sound files this controls the start of snippet
        :param stopTime: for sound files this controls the end of snippet
        :param name: string for logging purposes
        :param autoLog: whether to automatically log every change
        """
        self.sound = value
        self.name = name
        self.secs = secs  # for any synthesised sounds (notesand freqs)
        self.octave = octave  # for note name sounds
        self.loops = loops
        self._loopsFinished = 0
        self.volume = volume
        self.startTime = startTime  # for files
        self.stopTime = stopTime  # for files specify thesection to be played
        self.blockSize = blockSize  # can be per-sound unlike other backends
        self.preBuffer = preBuffer
        self.frameN = 0
        self._tSoundRequestPlay = 0
        if sampleRate:  #a rate was requested so use it
            self.sampleRate = sampleRate
        else:  # no requested rate so use current stream or a default of 44100
            rate = 44100  # start with a default
            for streamLabel in streams:  # then look to see if we have an open stream and use that
                rate = streams[streamLabel].sampleRate
            self.sampleRate = rate
        self.channels = None  # let this be set by stereo
        self.stereo = stereo
        self.duplex = None
        self.autoLog = autoLog
        self.streamLabel = ""
        self.sourceType = 'unknown'  # set to be file, array or freq
        self.sndFile = None
        self.sndArr = None
        self.hamming = hamming
        self._hammingWindow = None  # will be created during setSound

        # setSound (determines sound type)
        self.setSound(value, secs=self.secs, octave=self.octave,
                      hamming=self.hamming)
        self.status = NOT_STARTED
    @property
    def stereo(self):
        return self.__dict__['stereo']

    @stereo.setter
    def stereo(self, val):
        self.__dict__['stereo'] = val
        if val == True:
            self.__dict__['channels'] = 2
        elif val == False:
            self.__dict__['channels'] = 1
        elif val == -1:
            self.__dict__['channels'] = -1

    def setSound(self, value, secs=0.5, octave=4, hamming=None, log=True):
        """Set the sound to be played.

        Often this is not needed by the user - it is called implicitly during
        initialisation.

        :parameters:

            value: can be a number, string or an array:
                * If it's a number between 37 and 32767 then a tone will
                  be generated at that frequency in Hz.
                * It could be a string for a note ('A', 'Bfl', 'B', 'C',
                  'Csh'. ...). Then you may want to specify which octave.
                * Or a string could represent a filename in the current
                  location, or mediaLocation, or a full path combo
                * Or by giving an Nx2 numpy array of floats (-1:1) you can
                  specify the sound yourself as a waveform

            secs: duration (only relevant if the value is a note name or
                a frequency value)

            octave: is only relevant if the value is a note name.
                Middle octave of a piano is 4. Most computers won't
                output sounds in the bottom octave (1) and the top
                octave (8) is generally painful
        """
        # start with the base class method
        _SoundBase.setSound(self, value, secs, octave, hamming, log)
        try:
            label, s = streams.getStream(sampleRate=self.sampleRate,
                                         channels=self.channels,
                                         blockSize=self.blockSize)
        except SoundFormatError as err:
            # try to use something similar (e.g. mono->stereo)
            # then check we have an appropriate stream open
            altern = streams._getSimilar(sampleRate=self.sampleRate,
                                         channels=-1,
                                         blockSize=-1)
            if altern is None:
                raise err
            else:  # safe to extract data
                label, s = altern
            # update self in case it changed to fit the stream
            self.sampleRate = s.sampleRate
            self.channels = s.channels
            self.blockSize = s.blockSize
        self.streamLabel = label

        if hamming is None:
            hamming = self.hamming
        else:
            self.hamming = hamming
        if hamming:
            # 5ms or 15th of stimulus (for short sounds)
            hammDur = min(0.005,  # 5ms
                          self.secs / 15.0)  # 15th of stim
            self._hammingWindow = HammingWindow(winSecs=hammDur,
                                                soundSecs=self.secs,
                                                sampleRate=self.sampleRate)

    def _setSndFromFile(self, filename):
        self.sndFile = f = sf.SoundFile(filename)
        self.sourceType = 'file'
        self.sampleRate = f.samplerate
        if self.channels == -1:  # if channels was auto then set to file val
            self.channels = f.channels
        fileDuration = float(len(f))/f.samplerate  # needed for duration?
        # process start time
        if self.startTime and self.startTime > 0:
            startFrame = self.startTime * self.sampleRate
            self.sndFile.seek(int(startFrame))
            self.t = self.startTime
        else:
            self.t = 0
        # process stop time
        if self.stopTime and self.stopTime > 0:
            requestedDur = self.stopTime - self.t
            self.duration = min(requestedDur, fileDuration)
        else:
            self.duration = fileDuration - self.t
        # can now calculate duration in frames
        self.durationFrames = int(round(self.duration * self.sampleRate))
        # are we preloading or streaming?
        if self.preBuffer == 0:
            # no buffer - stream from disk on each call to nextBlock
            pass
        elif self.preBuffer == -1:
            # full pre-buffer. Load requested duration to memory
            sndArr = self.sndFile.read(
                frames=int(self.sampleRate * self.duration))
            self.sndFile.close()
            self._setSndFromArray(sndArr)
        self._channelCheck(self.sndArr)  # Check for fewer channels in stream vs data array

    def _setSndFromFreq(self, thisFreq, secs, hamming=True):
        self.freq = thisFreq
        self.secs = secs
        self.sourceType = 'freq'
        self.t = 0
        self.duration = self.secs
        if self.stereo == -1:
            self.stereo = 0

    def _setSndFromArray(self, thisArray):

        self.sndArr = np.asarray(thisArray)
        if thisArray.ndim == 1:
            self.sndArr.shape = [len(thisArray), 1]  # make 2D for broadcasting
        if self.channels == 2 and self.sndArr.shape[1] == 1:  # mono -> stereo
            self.sndArr = self.sndArr.repeat(2, axis=1)
        elif self.sndArr.shape[1] == 1:  # if channels in [-1,1] then pass
            pass
        else:
            try:
                self.sndArr.shape = [len(thisArray), 2]
            except ValueError:
                raise ValueError("Failed to format sound with shape {} "
                                 "into sound with channels={}"
                                 .format(self.sndArr.shape, self.channels))

        # is this stereo?
        if self.stereo == -1:  # auto stereo. Try to detect
            if self.sndArr.shape[1] == 1:
                self.stereo = 0
            elif self.sndArr.shape[1] == 2:
                self.stereo = 1
            else:
                raise IOError("Couldn't determine whether array is "
                              "stereo. Shape={}".format(self.sndArr.shape))
        self._nSamples = thisArray.shape[0]
        if self.stopTime == -1:
            self.stopTime = self._nSamples/float(self.sampleRate)
        # set to run from the start:
        self.seek(0)
        self.sourceType = "array"

    def _channelCheck(self, array):
        """Checks whether stream has fewer channels than data. If True, ValueError"""
        if self.channels < array.shape[1]:
            msg = ("The sound stream is set up incorrectly. You have fewer channels in the buffer "
                   "than in data file ({} vs {}).\n**Ensure you have selected 'Force stereo' in "
                   "experiment settings**".format(self.channels, array.shape[1]))
            logging.error(msg)
            raise ValueError(msg)

    def play(self, loops=None):
        """Start the sound playing
        """
        if loops is not None and self.loops != loops:
            self.setLoops(loops)
        self.status = PLAYING
        self._tSoundRequestPlay = time.time()
        streams[self.streamLabel].takeTimeStamp = True
        streams[self.streamLabel].add(self)

    def pause(self):
        """Stop the sound but play will continue from here if needed
        """
        self.status = PAUSED
        streams[self.streamLabel].remove(self)

    def stop(self, reset=True):
        """Stop the sound and return to beginning
        """
        streams[self.streamLabel].remove(self)
        if reset:
            self.seek(0)
        self.status = STOPPED

    def _nextBlock(self):
        if self.status == STOPPED:
            return
        samplesLeft = int((self.stopTime - self.t) * self.sampleRate)
        nSamples = min(self.blockSize, samplesLeft)
        if self.sourceType == 'file' and self.preBuffer == 0:
            # streaming sound block-by-block direct from file
            block = self.sndFile.read(nSamples)
            # TODO: check if we already finished using sndFile?
        elif (self.sourceType == 'file' and self.preBuffer == -1) \
                or self.sourceType == 'array':
            # An array, or a file entirely loaded into an array
            ii = int(round(self.t * self.sampleRate))
            if self.stereo == 1:  # don't treat as boolean. Might be -1
                block = self.sndArr[ii:ii + nSamples, :]
            elif self.stereo == 0:
                block = self.sndArr[ii:ii + nSamples]
            else:
                raise IOError("Unknown stereo type {!r}"
                              .format(self.stereo))
            if ii + nSamples > len(self.sndArr):
                self._EOS()

        elif self.sourceType == 'freq':
            startT = self.t
            stopT = self.t + self.blockSize/float(self.sampleRate)
            xx = np.linspace(
                start=startT * self.freq * 2 * np.pi,
                stop=stopT * self.freq * 2 * np.pi,
                num=self.blockSize, endpoint=False
            )
            xx.shape = [self.blockSize, 1]
            block = np.sin(xx)
            # if run beyond our desired t then set to zeros
            if stopT > (self.secs):
                tRange = np.linspace(startT, self.blockSize*self.sampleRate,
                                     num=self.blockSize, endpoint=False)
                block[tRange > self.secs] = 0
                # and inform our EOS function that we finished
                self._EOS(reset=False)  # don't set t=0

        else:
            raise IOError("SoundDeviceSound._nextBlock doesn't correctly handle"
                          "{!r} sounds yet".format(self.sourceType))

        if self._hammingWindow:
            thisWin = self._hammingWindow.nextBlock(self.t, self.blockSize)
            if thisWin is not None:
                if len(block) == len(thisWin):
                    block *= thisWin
                elif block.shape[0] == 0:
                    pass
                else:
                    block *= thisWin[0:len(block)]
        self.t += self.blockSize/float(self.sampleRate)
        return block

    def seek(self, t):
        self.t = t
        self.frameN = int(round(t * self.sampleRate))
        if self.sndFile and not self.sndFile.closed:
            self.sndFile.seek(self.frameN)

    def _EOS(self, reset=True):
        """Function called on End Of Stream
        """
        self._loopsFinished += 1
        if self.loops == 0:
            self.stop(reset=reset)
        elif self.loops > 0 and self._loopsFinished >= self.loops:
            self.stop(reset=reset)

        streams[self.streamLabel].remove(self)
        self.status = FINISHED

    @property
    def stream(self):
        """Read-only property returns the the stream on which the sound
        will be played
        """
        return streams[self.streamLabel]
