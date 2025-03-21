#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path
import numpy
import copy
import itertools
from os import path
from psychopy import logging
from psychopy.constants import (STARTED, PLAYING, PAUSED, FINISHED, STOPPED,
                                NOT_STARTED, FOREVER)
from psychopy.tools.filetools import pathToString, defaultStim, defaultStimRoot
from psychopy.tools.audiotools import knownNoteNames, stepsFromA
from psychopy.tools.attributetools import AttributeGetSetMixin, attributeSetter
from .exceptions import SoundFormatError, DependencyError
from sys import platform
from .audioclip import AudioClip
from ..hardware import DeviceManager
from ..preferences.preferences import prefs
try:
    import soundfile as sf
except Exception:
    raise DependencyError("soundfile not working")

if platform == 'win32':
    mediaLocation = "C:\\Windows\\Media"
elif platform == 'darwin':
    mediaLocation = "/System/Library/Sounds/"
elif platform.startswith("linux"):
    mediaLocation = "/usr/share/sounds"




def apodize(soundArray, sampleRate):
    """Apply a Hanning window (5ms) to reduce a sound's 'click' onset / offset
    """
    hwSize = int(min(sampleRate // 200, len(soundArray) // 15))
    hanningWindow = numpy.hanning(2 * hwSize + 1)
    soundArray = copy.copy(soundArray)
    soundArray[:hwSize] *= hanningWindow[:hwSize]
    soundArray[-hwSize:] *= hanningWindow[hwSize + 1:]
    return soundArray


class HammingWindow():
    def __init__(self, winSecs, soundSecs, sampleRate):
        """

        :param winSecs:
        :param soundSecs:
        :param sampleRate:
        """
        self.sampleRate = sampleRate
        self.winSecs = winSecs
        self.winSamples = int(round(sampleRate*winSecs))
        self.soundSecs = soundSecs
        self.soundSamples = int(round(sampleRate*soundSecs))
        self.startWindow = numpy.hanning(self.winSamples*2)[0:self.winSamples]
        self.endWindow = numpy.hanning(self.winSamples*2)[self.winSamples:]
        self.finalWinStart = self.soundSamples-self.winSamples

    def nextBlock(self, t, blockSize):
        """Returns a block to be multiplied with the current sound block or 1.0

        :param t: current position in time (secs)
        :param blockSize: block size for the sound needing the hanning window
        :return: numpy array of length blockSize
        """
        startSample = int(t*self.sampleRate)
        if startSample < self.winSamples:
            # we're in beginning hanning window (start of sound)
            # 2 options:
            #  - block is fully within window
            #  - block starts in window but ends after window
            block = numpy.ones(blockSize)
            winEndII = min(self.winSamples,  # if block goes beyond hann win
                           startSample+blockSize)  # if block shorter
            blockEndII = min(self.winSamples-startSample,  # if block beyond
                             blockSize)  # if block shorter
            block[0:blockEndII] = self.startWindow[startSample:winEndII]
        elif startSample >= self.soundSamples:
            block = None  # the sound has finished (shouldn't have got here!)
        elif startSample >= self.finalWinStart-blockSize:
            # we're in final hanning window (end of sound)
            # More complicated, with 3 options:
            #  - block starts before win
            #  - start/end during win
            #  - start during but end after win
            block = numpy.ones(blockSize)  # the initial flat part
            blockStartII = max(self.finalWinStart-startSample,
                         0)  # if block start inside window
            blockEndII = min(blockSize,  # if block ends in hann win
                             self.soundSamples-startSample)  # ends after snd
            winStartII = max(0,  # current block ends in win but starts before
                             startSample-self.finalWinStart)
            winEndII = min(self.winSamples,
                           startSample+blockSize-self.finalWinStart)
            block[blockStartII:blockEndII] = \
                self.endWindow[winStartII:winEndII]
        else:
            block = None  # we're in the middle of sound so no need for window
        if block is not None:
            block.shape = [len(block), 1]
        return block


class _SoundBase(AttributeGetSetMixin):
    """Base class for sound object, from one of many ways.
    """
    # Must be provided by class SoundPygame or SoundPyo:
    # def __init__()
    # def play(self, fromStart=True, **kwargs):
    # def stop(self, log=True):
    # def getDuration(self):
    # def getVolume(self):
    # def setVolume(self, newVol, log=True):
    # def _setSndFromFile(self, fileName):
    # def _setSndFromArray(self, thisArray):

    autoLog = True

    def setSound(self, value, secs=0.5, octave=4, hamming=True, log=True):
        """Set the sound to be played.

        Often this is not needed by the user - it is called implicitly during
        initialisation.

        Parameters
        ----------
        value : ArrayLike, AudioClip, int or str
            If it's a number between 37 and 32767 then a tone will be generated
            at that frequency in Hz. It could be a string for a note ('A',
            'Bfl', 'B', 'C', 'Csh'. ...). Then you may want to specify which
            octave.O r a string could represent a filename in the current
            location, or media location, or a full path combo. Or by giving an
            Nx2 numpy array of floats (-1:1) or
            :class:`~psychopy.sound.AudioClip` instance.
        secs : float
            Duration of a tone if a note name is to `value`.
        octave : int
            Is only relevant if the value is a note name. Middle octave of a
            piano is 4. Most computers won't output sounds in the bottom octave
            (1) and the top octave (8) is generally painful.
        hamming : bool
            To indicate if the sound should be apodized (i.e., the onset and
            offset smoothly ramped up from down to zero). The function apodize
            uses a Hanning window, but arguments named 'hamming' are preserved
            so that existing code is not broken by the change from Hamming to
            Hanning internally. Not applied to sounds from files.

        """
        # Re-init sound to ensure bad values will raise error during setting:
        self._snd = None
        # make references to default stim into absolute paths
        if isinstance(value, str) and value in defaultStim:
            value = defaultStimRoot / defaultStim[value]
        # if directly given a Microphone, get its last recording
        if hasattr(value, "lastClip"):
            value = value.lastClip
        # Coerces pathlib obj to string, else returns inputted value
        value = pathToString(value)
        try:
            # could be '440' meaning 440
            value = float(value)
        except (ValueError, TypeError):
            # this is a string that can't be a number, eg, a file or note
            pass
        else:
            # we've been asked for a particular Hz
            if value < 37 or value > 20000:
                msg = 'Sound: bad requested frequency %.0f'
                raise ValueError(msg % value)
            self._setSndFromFreq(value, secs, hamming=hamming)
        if isinstance(value, str):
            if value.capitalize() in knownNoteNames:
                self._setSndFromNote(value.capitalize(), secs, octave,
                                     hamming=hamming)
            else:
                # try finding a file
                self.fileName = None
                valid_paths = ['', mediaLocation]
                valid_endings = ['', '.wav', '.mp3', '.flac', '.ogg']
                for pre, suf in itertools.product(valid_paths, valid_endings):
                    media_filepath = path.join(pre, value)
                    if path.isfile(media_filepath + suf):
                        self.fileName = media_filepath + suf
                        break

                if self.fileName is None:
                    msg = "setSound: could not find a sound file named "
                    raise ValueError(msg + value)
                else:
                    self._setSndFromFile(self.fileName)

        elif isinstance(value, (list, numpy.ndarray,)):
            # create a sound from the input array/list
            self._setSndFromArray(numpy.array(value))
        elif isinstance(value, AudioClip):  # from an audio clip object
            # check if we should resample the audio clip to match the device
            if self.sampleRate is None:
                logging.warning(
                    "Sound output sample rate not set. The provided AudioClip "
                    "requires a sample rate of {} Hz for playback which may "
                    "not match the device settings.".format(value.sampleRateHz))

                self.sampleRate = value.sampleRateHz

            if self.sampleRate != value.sampleRateHz:
                logging.warning(
                    "Resampling to match sound device sample rate (from {} "
                    "to {} Hz), distortion may occur.".format(
                        value.sampleRateHz, self.sampleRate))

                # resample with the new sample rate using the AudioClip method
                value = value.resample(self.sampleRate, copy=True)

            self._setSndFromArray(value.samples)

        # did we succeed?
        if self._snd is None:
            pass  # raise ValueError, "Could not make a "+value+" sound"
        else:
            if log and self.autoLog:
                logging.exp("Set %s sound=%s" % (self.name, value), obj=self)
            self.status = NOT_STARTED

    @attributeSetter
    def sampleRate(self, sampleRate):
        # if given None, use sample rate from speaker
        if sampleRate is None and hasattr(self.speaker, "sampleRateHz"):
            sampleRate = self.speaker.sampleRateHz
        # set as normal
        self.__dict__['sampleRate'] = sampleRate

    # alias channels, stereo and isStereo for the sake of the different backends

    @attributeSetter
    def channels(self, channels):
        self.__dict__['channels'] = channels
        self.__dict__['stereo'] = self.__dict__['isStereo'] = channels is None or channels > 1

    @attributeSetter
    def stereo(self, stereo):
        self.channels = 2 if stereo else 1

    @attributeSetter
    def isStereo(self, stereo):
        self.stereo = stereo

    def _setSndFromNote(self, thisNote, secs, octave, hamming=True):
        # note name -> freq -> sound
        freqA = 440.0
        thisOctave = octave - 4
        mult = 2.0**(stepsFromA[thisNote] / 12.)
        thisFreq = freqA * mult * 2.0 ** thisOctave
        self._setSndFromFreq(thisFreq, secs, hamming=hamming)

    def _setSndFromFreq(self, thisFreq, secs, hamming=True):
        # note freq -> array -> sound
        if secs < 0:
            # want infinite duration - create 1 sec sound and loop it
            secs = 10.0
            self.loops = -1
        if not self.sampleRate:
            self.sampleRate = self._getDefaultSampleRate()
        nSamples = int(secs * self.sampleRate)
        outArr = numpy.arange(0.0, 1.0, 1.0 / nSamples)
        outArr *= 2 * numpy.pi * thisFreq * secs
        outArr = numpy.sin(outArr)
        if hamming and nSamples > 30:
            outArr = apodize(outArr, self.sampleRate)
        self._setSndFromArray(outArr)

    def _setSndFromFile(self, filename):
        # alias default names (so it always points to default.png)
        if filename in defaultStim:
            filename = Path(prefs.paths['assets']) / defaultStim[filename]
        self.sndFile = f = sf.SoundFile(filename)
        self.sourceType = 'file'
        self.sampleRate = f.samplerate
        if self.channels == -1:  # if channels was auto then set to file val
            self.channels = f.channels
        fileDuration = float(len(f)) / f.samplerate  # needed for duration?
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
        self._channelCheck(
            self.sndArr)  # Check for fewer channels in stream vs data array

    def _setSndFromArray(self, thisArray):
        self.sndArr = numpy.asarray(thisArray).astype('float32')
        if thisArray.ndim == 1:
            self.sndArr.shape = [len(thisArray), 1]  # make 2D for broadcasting

        # is this stereo?
        if self.stereo == -1:  # auto stereo. Try to detect
            if self.sndArr.shape[1] == 1:
                self.stereo = 0
            elif self.sndArr.shape[1] == 2:
                self.stereo = 1
            else:
                raise IOError("Couldn't determine whether array is "
                              "stereo. Shape={}".format(self.sndArr.shape))
        # store details about array
        self._nSamples = thisArray.shape[0]
        self.sourceType = "array"

        # catch when array is empty
        if not len(self.sndArr):
            logging.warning(
                "Received a blank array for sound, playing nothing instead."
            )
            self.sndArr = numpy.zeros(shape=(self.blockSize, self.channels))

        # create audio clip
        clip = AudioClip(
            samples=self.sndArr,
            sampleRateHz=self.sampleRate
        )
        # set from clip
        self._setSndFromClip(clip)

    def _setSndFromClip(self, clip: AudioClip):
        """
        Set current sound from an AudioClip object. All other setSound methods eventually lead to
        this - they just transform the given sound (be it an array, file, note, etc.) to an
        AudioClip first.

        Each subclass of _SoundBase (so each sound backend; ptb, pygame, etc.) will implement this
        method in their own way.

        Parameters
        ----------
        clip : AudioClip
            AudioClip object to set.
        """
        raise NotImplementedError()

    def _getDefaultSampleRate(self):
        """For backends this might depend on what streams are open"""
        return 44100

    def getDuration(self):
        """Return the duration of the sound"""
        return self.duration

    def getVolume(self):
        """Returns the current volume of the sound (0.0 to 1.0, inclusive)
        """
        return self.volume

    def getLoops(self):
        """Returns the current requested loops value for the sound (int)
        """
        return self.loops

    def setVolume(self, newVol, log=True):
        """Sets the current volume of the sound (0.0 to 1.0, inclusive)
        """
        self.volume = min(1.0, max(0.0, newVol))
        self.needsUpdate = True
        if log and self.autoLog:
            logging.exp("Sound %s set volume %.3f" %
                        (self.name, self.volume), obj=self)

    def setLoops(self, newLoops, log=True):
        """Sets the current requested extra loops (int)"""
        self.loops = int(newLoops)
        self.needsUpdate = True
        if log and self.autoLog:
            logging.exp("Sound %s set loops %s" %
                        (self.name, self.loops), obj=self)
