#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
New backend for the Psychtoolbox portaudio engine
"""
import sys
import os
import time
import re
import weakref
from pathlib import Path

from psychopy import prefs, logging, exceptions
from psychopy.constants import (STARTED, PAUSED, FINISHED, STOPPING,
                                NOT_STARTED)
from psychopy.hardware.speaker import SpeakerDevice
from psychopy.tools import systemtools
from psychopy.tools import filetools as ft
from .exceptions import SoundFormatError, DependencyError
from ._base import _SoundBase, HammingWindow
from .audioclip import AudioClip
from ..hardware import DeviceManager

try:
    from psychtoolbox import audio
    import psychtoolbox as ptb
except Exception:
    raise DependencyError("psychtoolbox audio failed to import")
try:
    import soundfile as sf
except Exception:
    raise DependencyError("soundfile not working")

import numpy as np


defaultLatencyClass = 1
# suggestedLatency = 0.005  ## Not currently used. Keep < 1 scr refresh

if prefs.hardware['audioDriver']=='auto':
    audioDriver = None
else:
    audioDriver = prefs.hardware['audioDriver']

if prefs.hardware['audioDevice']=='auto':
    audioDevice = None
else:
    audioDevice = prefs.hardware['audioDevice']

# check if we should only use WAS host API (default is True on Windows)
audioWASAPIOnly = False
try:
    wasapiPref = prefs.hardware['audioWASAPIOnly']
except KeyError:
    wasapiPref = False
if sys.platform == 'win32' and wasapiPref:
    audioWASAPIOnly = True

# these will be used by sound.__init__.py
defaultInput = None
defaultOutput = audioDevice

logging.info("Loaded psychtoolbox audio version {}"
             .format(audio.get_version_info()['version']))

# ask PTB to align verbosity with our current logging level at console
_verbosities = ((logging.DEBUG, 5),
                (logging.INFO, 4),
                (logging.EXP, 3),
                (logging.WARNING, 2),
                (logging.ERROR, 1))

for _logLevel, _verbos in _verbosities:
    if logging.console.level <= _logLevel:
        audio.verbosity(_verbos)
        break


def init(rate=48000, stereo=True, buffer=128):
    pass  # for compatibility with other backends


class SoundPTB(_SoundBase):
    """Play a variety of sounds using the new PsychPortAudio library
    """

    def __init__(self, value="C", secs=0.5, octave=4, stereo=-1,
                 volume=1.0, loops=0,
                 sampleRate=None, blockSize=128,
                 preBuffer=-1,
                 hamming=True,
                 startTime=0, stopTime=-1,
                 name='', autoLog=True,
                 syncToWin=None, speaker=None):
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
        :param syncToWin: if you want start/stop to sync with win flips add this
        """
        # if given the name of a managed speaker, get it
        if isinstance(speaker, str) and DeviceManager.getDevice(speaker):
            speaker = DeviceManager.getDevice(speaker)
        # make sure speaker is a SpeakerDevice
        if not isinstance(speaker, SpeakerDevice):
            speaker = SpeakerDevice(speaker)
        self.speaker = speaker
        
        self.sound = value
        self.name = name
        self.secs = secs  # for any synthesised sounds (notesand freqs)
        self.octave = octave  # for note name sounds
        self.loops = self._loopsRequested = loops
        self._loopsFinished = 0
        self.volume = volume
        self.startTime = startTime  # for files
        self.stopTime = stopTime  # for files specify thesection to be played
        self.blockSize = blockSize  # can be per-sound unlike other backends
        self.preBuffer = preBuffer
        self.frameN = 0
        self._tSoundRequestPlay = 0
        self.sampleRate = sampleRate
        self.channels = None  # let this be set by stereo
        self.stereo = stereo
        self.duplex = None
        self.autoLog = autoLog
        self.sourceType = 'unknown'  # set to be file, array or freq
        self.sndFile = None
        self.sndArr = None
        self.hamming = hamming
        self._hammingWindow = None  # will be created during setSound
        self.win = syncToWin
        # setSound (determines sound type)
        self.setSound(value, secs=self.secs, octave=self.octave,
                      hamming=self.hamming)
        self._isPlaying = False  # set `True` after `play()` is called
        self._isFinished = False
        self.status = NOT_STARTED

    @property
    def isPlaying(self):
        """`True` if the audio playback is ongoing."""
        # This will update _isPlaying if sound has stopped by _EOS()
        _ = self._checkPlaybackFinished()
        return self._isPlaying

    @property
    def isFinished(self):
        """`True` if the audio playback has completed."""
        return self._checkPlaybackFinished()

    @property
    def statusDetailed(self):
        if not self.track:
            return None
        return self.track.status

    @property
    def volume(self):
        return self.__dict__['volume']

    @volume.setter
    def volume(self, newVolume):
        self.__dict__['volume'] = newVolume
        if 'track' in self.__dict__:
            # Update volume of an existing track, if it exists.
            # (BUGFIX, otherwise only the member variable is updated, but the sound
            # volume does not change while playing - Suddha Sourav, 14.10.2020)
            self.__dict__['track']().volume = newVolume
        else:
            return None

    @property
    def stereo(self):
        return self.__dict__['stereo']

    @stereo.setter
    def stereo(self, val):
        # if auto, get from speaker
        if val == -1:
            val = self.speaker.channels > 1
        # store value
        self.__dict__['stereo'] = val
        # convert to n channels
        if val is True:
            self.__dict__['channels'] = 2
        elif val is False:
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
        # reset self.loops to what was requested (in case altered for infinite play of tones)
        self.loops = self._loopsRequested
        # start with the base class method
        _SoundBase.setSound(self, value, secs, octave, hamming, log)
    
    def _setSndFromClip(self, clip: AudioClip):
        # store clip
        self.clip = clip
        # resample the clip if needed and allowed
        if self.speaker.resample:
            if clip.sampleRateHz != self.speaker.sampleRateHz:
                clip.resample(targetSampleRateHz=self.speaker.sampleRateHz)
        # work out stop time
        if self.stopTime == -1:
            self.duration = clip.samples.shape[0] / clip.sampleRateHz
        # handle stereo/mono
        if self.speaker.channels > 1:
            clip = clip.asStereo()
        else:
            clip = clip.asMono()
        # create/update track
        if  self.track:
            self.track.stop()
            self.track.fill_buffer(clip.samples)
        else:
            self.track = audio.Slave(
                self.stream.handle, 
                data=clip.samples,
                volume=self.volume
            )
        # seek to start
        self.seek(0)

    def _channelCheck(self, array):
        """Checks whether stream has fewer channels than data. If True, ValueError"""
        if self.channels < array.shape[1]:
            msg = (
                "The sound stream is set up incorrectly. You have fewer channels in the buffer "
                "than in data file ({} vs {}).\n**Ensure you have selected 'Force stereo' in "
                "experiment settings**".format(self.channels, array.shape[1]))
            logging.error(msg)
            raise ValueError(msg)

    def _checkPlaybackFinished(self):
        """Checks whether playback has finished by looking up the status.
        """
        # get detailed status from backend
        pa_status = self.statusDetailed
        # was the sound already finished?
        wasFinished = self._isFinished
        # is it finished now?
        isFinished = self._isFinished = not pa_status['Active'] and pa_status['State'] == 0
        # if it wasn't finished but now is, do end of stream behaviour
        if isFinished and not wasFinished:
            self._EOS()

        return self._isFinished

    def play(self, loops=None, when=None, log=True):
        """Start the sound playing.

        Calling this after the sound has finished playing will restart the
        sound.

        """
        if self._checkPlaybackFinished():
            self.stop(reset=True)

        if loops is not None and self.loops != loops:
            self.setLoops(loops)

        self._tSoundRequestPlay = time.time()

        if hasattr(when, 'getFutureFlipTime'):
            logTime = when.getFutureFlipTime(clock=None)
            when = when.getFutureFlipTime(clock='ptb')
        elif when is None and hasattr(self.win, 'getFutureFlipTime'):
            logTime = self.win.getFutureFlipTime(clock=None)
            when = self.win.getFutureFlipTime(clock='ptb')
        else:
            logTime = None
        self.track.start(repetitions=loops, when=when)
        self._isPlaying = True
        self._isFinished = False
        # time.sleep(0.)
        if log and self.autoLog:
            logging.exp(u"Playing sound %s on speaker %s" % (self.name, self.speaker.name), obj=self, t=logTime)

    def pause(self, log=True):
        """Stops the sound without reset, so that play will continue from here if needed
        """
        if self._isPlaying:
            self.stop(reset=False, log=False)
            if log and self.autoLog:
                logging.exp(u"Sound %s paused" % (self.name), obj=self)

    def stop(self, reset=True, log=True):
        """Stop the sound and return to beginning
        """
        # this uses FINISHED for some reason, all others use STOPPED
        if not self._isPlaying:
            return

        self.track.stop()
        self._isPlaying = False

        if reset:
            self.seek(0)
        if log and self.autoLog:
            logging.exp(u"Sound %s stopped" % (self.name), obj=self)

    def seek(self, t):
        self.t = t
        self.frameN = int(round(t * self.sampleRate))
        if self.sndFile and not self.sndFile.closed:
            self.sndFile.seek(self.frameN)
        self._isFinished = t >= self.duration

    def _EOS(self, reset=True, log=True):
        """Function called on End Of Stream
        """
        self._loopsFinished += 1
        if self._loopsFinished >= self._loopsRequested:
            # if we have finished all requested loops
            self.stop(reset=reset, log=False)
        else:
            # reset _isFinished back to False
            self._isFinished = False

        if log and self.autoLog:
            logging.exp(u"Sound %s reached end of file" % self.name, obj=self)

    @property
    def stream(self):
        """Read-only property returns the stream on which the sound
        will be played
        """
        return self.speaker.stream

    def __del__(self):
        if self.track:
            self.track.close()
        self.track = None

    @property
    def track(self):
        """The track on the master stream to which we belong"""
        # the track is actually a weak reference to avoid circularity
        if 'track' in self.__dict__:
            return self.__dict__['track']()
        else:
            return None

    @track.setter
    def track(self, track):
        if track is None:
            self.__dict__['track'] = None
        else:
            self.__dict__['track'] = weakref.ref(track)
