#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import numpy
from os import path
from psychopy import logging,exceptions
from psychopy.constants import (STARTED, PLAYING, PAUSED, FINISHED, STOPPED,
                                NOT_STARTED, FOREVER)
from ._base import _SoundBase

try:
    import pygame
    from pygame import mixer, sndarray
except ImportError as err:
    # convert this import error to our own, pyo probably not installed
    raise exceptions.DependencyError(repr(err))

def init(rate=22050, bits=16, stereo=True, buffer=1024):
    """If you need a specific format for sounds you need to run this init
    function. Run this *before creating your visual.Window*.

    The format cannot be changed once initialised or once a Window has been
    created.

    If a Sound object is created before this function is run it will be
    executed with default format (signed 16bit stereo at 22KHz).

    For more details see pygame help page for the mixer.
    """
    global Sound, audioDriver
    Sound = SoundPygame
    audioDriver = 'n/a'
    if stereo == True:
        stereoChans = 2
    else:
        stereoChans = 0
    if bits == 16:
        # for pygame bits are signed for 16bit, signified by the minus
        bits = -16
    # defaults: 22050Hz, 16bit, stereo,
    mixer.init(rate, bits, stereoChans, buffer)
    sndarray.use_arraytype("numpy")
    setRate, setBits, setStereo = mixer.get_init()
    if setRate != rate:
        logging.warn('Requested sound sample rate was not poossible')
    if setBits != bits:
        logging.warn('Requested sound depth (bits) was not possible')
    if setStereo != 2 and stereo == True:
        logging.warn('Requested stereo setting was not possible')


class SoundPygame(_SoundBase):
    """Create a sound object, from one of many ways.

    :parameters:
        value: can be a number, string or an array:
            * If it's a number between 37 and 32767 then a tone will be
              generated at that frequency in Hz.
            * It could be a string for a note ('A', 'Bfl', 'B', 'C',
              'Csh', ...). Then you may want to specify which octave as well
            * Or a string could represent a filename in the current
              location, or mediaLocation, or a full path combo
            * Or by giving an Nx2 numpy array of floats (-1:1) you
              can specify the sound yourself as a waveform

        secs: duration (only relevant if the value is a note name or a
            frequency value)

        octave: is only relevant if the value is a note name.
            Middle octave of a piano is 4. Most computers won't
            output sounds in the bottom octave (1) and the top
            octave (8) is generally painful

        sampleRate(=44100): If a sound has already been created or if the

        bits(=16):  Pygame uses the same bit depth for all sounds once
            initialised
    """

    def __init__(self, value="C", secs=0.5, octave=4, sampleRate=44100,
                 bits=16, name='', autoLog=True, loops=0, stereo=True):
        """
        """
        self.name = name  # only needed for autoLogging
        self.autoLog = autoLog

        if stereo == True:
            stereoChans = 2
        else:
            stereoChans = 0
        if bits == 16:
            # for pygame bits are signed for 16bit, signified by the minus
            bits = -16

        # check initialisation
        if not mixer.get_init():
            pygame.mixer.init(sampleRate, bits, stereoChans, 3072)

        inits = mixer.get_init()
        if inits is None:
            init()
            inits = mixer.get_init()
        self.sampleRate, self.format, self.isStereo = inits

        # try to create sound
        self._snd = None
        # distinguish the loops requested from loops actual because of
        # infinite tones (which have many loops but none requested)
        # -1 for infinite or a number of loops
        self.requestedLoops = self.loops = int(loops)
        self.setSound(value=value, secs=secs, octave=octave)

    def play(self, fromStart=True, log=True, loops=None):
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

        :Notes:

            If no sound channels are available, it will not play and return
            None. This runs off a separate thread i.e. your code won't wait
            for the sound to finish before continuing. You need to use a
            psychopy.core.wait() command if you want things to pause.
            If you call play() whiles something is already playing the sounds
            will be played over each other.

        """
        if loops is None:
            loops = self.loops
        self._snd.play(loops=loops)
        self.status = STARTED
        if log and self.autoLog:
            logging.exp("Sound %s started" % (self.name), obj=self)
        return self

    def stop(self, log=True):
        """Stops the sound immediately
        """
        self._snd.stop()
        self.status = STOPPED
        if log and self.autoLog:
            logging.exp("Sound %s stopped" % (self.name), obj=self)

    def fadeOut(self, mSecs):
        """fades out the sound (when playing) over mSecs.
        Don't know why you would do this in psychophysics but it's easy
        and fun to include as a possibility :)
        """
        self._snd.fadeout(mSecs)
        self.status = STOPPED

    def getDuration(self):
        """Get's the duration of the current sound in secs
        """
        return self._snd.get_length()

    def getVolume(self):
        """Returns the current volume of the sound (0.0:1.0)
        """
        return self._snd.get_volume()

    def setVolume(self, newVol, log=True):
        """Sets the current volume of the sound (0.0:1.0)
        """
        self._snd.set_volume(newVol)
        if log and self.autoLog:
            msg = "Set Sound %s volume=%.3f"
            logging.exp(msg % (self.name, newVol), obj=self)
        return self.getVolume()

    def _setSndFromFile(self, fileName):
        # load the file
        if not path.isfile(fileName):
            msg = "Sound file %s could not be found." % fileName
            logging.error(msg)
            raise ValueError(msg)
        self.fileName = fileName
        # in case a tone with inf loops had been used before
        self.loops = self.requestedLoops
        try:
            self._snd = mixer.Sound(self.fileName)
        except Exception:
            msg = "Sound file %s could not be opened using pygame for sound."
            logging.error(msg % fileName)
            raise ValueError(msg % fileName)

    def _setSndFromArray(self, thisArray):
        # get a mixer.Sound object from an array of floats (-1:1)

        # make stereo if mono
        if (self.isStereo == 2 and
                (len(thisArray.shape) == 1 or
                 thisArray.shape[1] < 2)):
            tmp = numpy.ones((len(thisArray), 2))
            tmp[:, 0] = thisArray
            tmp[:, 1] = thisArray
            thisArray = tmp
        # get the format right
        if self.format == -16:
            thisArray = (thisArray * 2**15).astype(numpy.int16)
        elif self.format == 16:
            thisArray = ((thisArray + 1) * 2**15).astype(numpy.uint16)
        elif self.format == -8:
            thisArray = (thisArray * 2**7).astype(numpy.Int8)
        elif self.format == 8:
            thisArray = ((thisArray + 1) * 2**7).astype(numpy.uint8)

        self._snd = sndarray.make_sound(thisArray)
