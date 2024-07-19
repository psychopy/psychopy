#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path

from psychopy import logging, prefs
from .exceptions import DependencyError
from psychopy.constants import (STARTED, PLAYING, PAUSED, FINISHED, STOPPED,
                                NOT_STARTED, FOREVER)
from psychopy.tools import attributetools, filetools as ft
from ._base import _SoundBase

try:
    import pysoundcard as soundcard
    import soundfile as sndfile
except ImportError as err:
    # convert this import error to our own, pysoundcard probably not installed
    raise DependencyError(repr(err.msg))

import numpy
from os import path
import weakref


def init(rate=44100, stereo=True, buffer=128):
    pass
    # for compatibility with other backends but not needed


def getDevices(kind=None):
    """Returns a dict of dict of audio devices of specified `kind`

    The dict keys are names and items are dicts of properties
    """
    devs = {}
    for ii, dev in enumerate(soundcard.device_info()):
        if (dev['max_output_channels'] == 0 and kind == 'output' or
                dev['max_input_channels'] == 0 and kind == 'input'):
            continue
        # newline characters must be removed
        devName = dev['name'].replace('\r\n', '')
        devs[devName] = dev
        dev['id'] = ii
    return devs


# these will be controlled by sound.__init__.py
defaultInput = None
defaultOutput = None


class _PySoundCallbackClass():
    """To use callbacks without creating circular references we need a
    callback class.

    Both the Stream and the sound object (SoundPySoundCard) point to this.

    This receives data and current sample from SoundPySoundCard and is
    stored by the c functions in the pysoundcard.Stream. We can't store
    a reference here to the original sound instance that created it (or
    we would create a circular ref again).

    """

    def __init__(self, sndInstance):
        self.status = NOT_STARTED
        self._sampleIndex = 0
        self.bufferSize = sndInstance.bufferSize
        self.sndInstance = weakref.ref(sndInstance)

    def fillBuffer(self, inData, outData, timeInfo, status):
        # inData to record from a buffer(?)
        # outData a buffer to write to (length of self.bufferSize)
        # timeInfo is a dict
        # status = 0 unless

        # In tests on a macbook air this function takes around 7microsec
        # to run so shouldn't impact on performance. Tested with this code:
        #    s1 = sound.SoundPySoundCard(secs=10, bufferSize=bSize)
        #    s1.play()
        #
        #    inDat = numpy.zeros([bSize,2], dtype='f')
        #    outDat = numpy.zeros([bSize,2], dtype='f')
        #    t0 = time.time()
        #    for n in range(nRuns):
        #        s1._callbacks.fillBuffer(inDat, outDat,
        #               time_info=None, status=0)
        #    print("%fms per repeat" %((time.time()-t0)*1000/nRuns))
        snd = self.sndInstance()
        chansIn, chansOut = snd._stream.channels
        nSamples = len(snd.sndArr)
        if snd.status == STOPPED:
            outData[:] = 0
            return soundcard.abort_flag
        if self._sampleIndex + self.bufferSize > nSamples:
            outData[:] = 0  # set buffer to zero
            # then insert the data
            place = nSamples - self._sampleIndex
            outData[0:place, :] = snd.sndArr[self._sampleIndex:, :]
            self._sampleIndex = nSamples
            snd._onEOS()
            return soundcard.abort_flag
        else:
            place = self._sampleIndex + self.bufferSize
            outData[:, :] = snd.sndArr[self._sampleIndex:place, :] * snd.volume
            self._sampleIndex += self.bufferSize
            return soundcard.continue_flag

    def eos(self, log=True):
        """This is potentially given directly to the paStream but we don't use
        it. Instead we're calling our own Sound.eos() from within the
        fillBuffer callback
        """
        self.sndInstance()._onEOS()


class SoundPySoundCard(_SoundBase):

    def __init__(self, value="C", secs=0.5, octave=4, sampleRate=44100,
                 bits=None, name='', autoLog=True, loops=0, bufferSize=128,
                 volume=1, stereo=True, speaker=None):
        """Create a sound and get ready to play

        :parameters:

            value: can be a number, string or an array:
                * If it's a number then a tone will be generated at that
                  frequency in Hz.
                * It could be a string for a note ('A', 'Bfl', 'B', 'C',
                  'Csh', ...). Then you may want to specify which octave
                * Or a string could represent a filename in the current
                location, or mediaLocation, or a full path combo
                * Or by giving an Nx2 numpy array of floats (-1:1) you can
                specify the sound yourself as a waveform

            secs: duration (only relevant if the value is a note name
                  or a frequency value)

            octave: is only relevant if the value is a note name.
                Middle octave of a piano is 4. Most computers won't
                output sounds in the bottom octave (1) and the top
                octave (8) is generally painful

            sampleRate: int (default = 44100)
                Will be ignored if a file is used for the sound and the
                sampleRate can be determined from the file

            name: string
                Only used for logging purposes

            autoLog: bool (default = true)
                Determines whether changes to the object should be logged
                by default

            loops: int (default = 0)
                number of times to loop (0 means play once, -1 means loop
                forever)

            bufferSize: int (default = 128)
                How many samples should be loaded at a time to the sound
                buffer. A larger number will reduce speed to play a sound.
                If too small then audio artifacts will be heard where the
                buffer ran empty

            bits:
                currently serves no purpose (exists for backwards
                compatibility)

            volume: 0-1.0

            stereo:
                currently serves no purpose (exists for backwards
                compatibility)
        """
        self.name = name  # only needed for autoLogging
        self.autoLog = autoLog

        self.speaker = self._parseSpeaker(speaker)

        self.sampleRate = sampleRate
        self.bufferSize = bufferSize
        self.volume = volume

        # try to create sound
        self._snd = None
        # distinguish the loops requested from loops actual because of
        # infinite tones (which have many loops but none requested)
        # -1 for infinite or a number of loops
        self.requestedLoops = self.loops = int(loops)
        self.setSound(value=value, secs=secs, octave=octave)

        self._isPlaying = False

    @property
    def isPlaying(self):
        """`True` if the audio playback is ongoing."""
        return self._isPlaying

    def play(self, fromStart=True, log=True, loops=None, when=None):
        """Starts playing the sound on an available channel.

        :Parameters:

            fromStart : bool
                Not yet implemented.
            log : bool
                Whether or not to log the playback event.
            loops : int
                How many times to repeat the sound after it plays once. If
                `loops` == -1, the sound will repeat indefinitely until
                stopped.
            when: not used
                Included for compatibility purposes

        :Notes:

            If no sound channels are available, it will not play and return
            None. This runs off a separate thread, i.e. your code won't
            wait for the sound to finish before continuing. You need to
            use a psychopy.core.wait() command if you want things to pause.
            If you call play() whiles something is already playing the sounds
            will be played over each other.

        """
        if self.isPlaying:
            return

        if loops is not None:
            self.loops = loops
        self._stream.start()
        self._isPlaying = True
        if log and self.autoLog:
            logging.exp("Sound %s started" % (self.name), obj=self)
        return self

    def stop(self, log=True):
        """Stops the sound immediately"""
        if not self.isPlaying:  # already stopped
            return

        self._stream.abort()  # _stream.stop() finishes current buffer
        self._isPlaying = False
        if log and self.autoLog:
            logging.exp("Sound %s stopped" % (self.name), obj=self)

    def fadeOut(self, mSecs):
        """fades out the sound (when playing) over mSecs.
        Don't know why you would do this in psychophysics but it's easy
        and fun to include as a possibility :)
        """
        # todo
        self._isPlaying = False

    def getDuration(self):
        """Gets the duration of the current sound in secs
        """
        pass  # todo

    @attributetools.attributeSetter
    def volume(self, volume):
        """Returns the current volume of the sound (0.0:1.0)
        """
        self.__dict__['volume'] = volume

    def setVolume(self, value, operation="", log=None):
        """Sets the current volume of the sound (0.0:1.0)
        """
        attributetools.setAttribute(self, 'volume', value, log, operation)
        return value  # this is returned for historical reasons

    def _setSndFromFile(self, fileName):
        # alias default names (so it always points to default.png)
        if fileName in ft.defaultStim:
            fileName = Path(prefs.paths['assets']) / ft.defaultStim[fileName]
        # load the file
        if not path.isfile(fileName):
            msg = "Sound file %s could not be found." % fileName
            logging.error(msg)
            raise ValueError(msg)
        self.fileName = fileName
        # in case a tone with inf loops had been used before
        self.loops = self.requestedLoops
        try:
            self.sndFile = sndfile.SoundFile(fileName)
            sndArr = self.sndFile.read()
            self.sndFile.close()
            self._setSndFromArray(sndArr)

        except Exception:
            msg = "Sound file %s could not be opened using pysoundcard for sound."
            logging.error(msg % fileName)
            raise ValueError(msg % fileName)

    def _setSndFromArray(self, thisArray):
        """For pysoundcard all sounds are ultimately played as an array so
        other setSound methods are going to call this having created an arr
        """
        self._callbacks = _PySoundCallbackClass(sndInstance=self)
        if defaultOutput is not None and type(defaultOutput) != int:
            devs = getDevices()
            if defaultOutput not in devs:
                raise ValueError("Attempted to set use device {!r} to "
                                 "a device that is not available".format(defaultOutput))
            else:
                device = devs[defaultOutput]['id']
        else:
            device = defaultOutput
        self._stream = soundcard.Stream(samplerate=self.sampleRate,
                                        device=device,
                                        blocksize=self.bufferSize,
                                        channels=1,
                                        callback=self._callbacks.fillBuffer)
        self._snd = self._stream
        chansIn, chansOut = self._stream.channels
        if chansOut > 1 and thisArray.ndim == 1:
            # make mono sound stereo
            self.sndArr = numpy.resize(thisArray, [2, len(thisArray)]).T
        else:
            self.sndArr = numpy.asarray(thisArray)
        self._nSamples = thisArray.shape[0]
        # set to run from the start:
        self.seek(0)

    def seek(self, t):
        self._sampleIndex = t * self.sampleRate

    def _onEOS(self, log=True):
        if log and self.autoLog:
            logging.exp("Sound %s finished" % (self.name), obj=self)
        self._isPlaying = False

    def __del__(self):
        self._stream.close()
