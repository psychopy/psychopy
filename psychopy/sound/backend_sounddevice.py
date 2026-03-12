#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Audio playback backend using SoundDevice.

These are optional components that can be obtained by installing the
`psychopy-sounddevice` extension into the current environment.

"""

__all__ = [
    'init',
    'getDevices',
    'getStreamLabel',
    'SoundDeviceSound'
]

import sys
import os
import time
import re
import atexit

try:
    import readline  # Work around GH-2230
except ImportError:
    pass  # all that will happen is the stderr/stdout might get redirected

from psychopy import logging
from psychopy.constants import (PLAYING, PAUSED, FINISHED, STOPPED,
                                NOT_STARTED)
from psychopy.sound.exceptions import SoundFormatError, DependencyError
from psychopy.sound._base import _SoundBase, HammingWindow

try:
    import sounddevice as sd
except (ImportError, OSError):
    raise DependencyError("sounddevice not working")
try:
    import soundfile as sf
except (ImportError, OSError):
    raise DependencyError("soundfile not working")

import numpy as np
_piTimes2 = 2 * np.pi  # computed a lot so store it here

travisCI = bool(str(os.environ.get('TRAVIS')).lower() == 'true')

logging.info("Loaded SoundDevice with {}".format(sd.get_portaudio_version()[1]))


def init(rate=44100, stereo=True, buffer=128):
    """Initialise the sound system with the specified settings.

    Parameters
    ----------
    rate : int
        Sample rate for audio playback (e.g., 44100).
    stereo : bool
        Whether to use stereo (2 channels) or mono (1 channel) audio.
    buffer : int
        The size of the buffer on the sound card (small for low latency, large 
        for stability).

    """
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
        # no compatible stream found, create new stream replacing flexible values with defaults
        if channels in [None, -1]:
            channels = 2
        if sampleRate in [None, -1, 0]:
            sampleRate = 44100
        if blockSize in [None, -1]:
            blockSize = 128
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
            raise SoundFormatError(
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


class _SoundStream:
    """A SoundStream is a single stream of audio data to the sound card. It can 
    be shared by multiple Sound objects, but only one stream of a given format 
    (sample rate, channels, block size) can exist at once.
    
    """
    def __init__(self, sampleRate, channels, blockSize,
                 device=None, duplex=False):
        """
        Parameters
        ----------
        sampleRate : int
            Sample rate of the stream (e.g., 44100).
        channels : int
            Number of audio channels (e.g., 1 for mono, 2 for stereo).
        blockSize : int
            The size of the buffer on the sound card (small for low latency, 
            large for stability).
        device : int or str or None
            The audio device to use for the stream. Can be specified by name 
            or index, or `None` to use the default device.
        duplex : bool
            Whether the stream should be duplex (i.e., support both input and 
            output). If `False`, the stream will be output-only.
        """
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

        self._isPlaying = False

    @property
    def isPlaying(self):
        """`True` if the audio playback is ongoing."""
        return self._isPlaying

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
                toSpk[:len(dat), 0:self.channels] += dat  # add to out stream
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
        atexit.unregister(self.__del__)


class SoundDeviceSound(_SoundBase):
    """Play a variety of sounds using the new SoundDevice library
    """
    def __init__(self, value="C", secs=0.5, octave=4, stereo=-1,
                 speaker=None,
                 volume=1.0, loops=0,
                 sampleRate=None, blockSize=128,
                 preBuffer=-1,
                 hamming=True,
                 startTime=0, stopTime=-1,
                 name='', 
                 autoLog=True):
        """
        Parameters
        ----------
        value : str or number or array
            The sound to be played. Can be a note name (e.g., "C", "Bfl"), a 
            filename, a frequency in Hz, or an Nx2 numpy array of floats in the 
            range -1:1 representing the sound waveform.
        secs : float
            Duration of the sound (for synthesised tones, ignored for sound files).
        octave : int
            Which octave to use for note names (4 is middle), ignored for sound 
            files.
        stereo : bool or int
            -1 (auto), True or False to force sounds to stereo or mono. Ignored 
            for sound files.
        speaker : str or None
            The speaker to use for playback. Can be a name or None to use the 
            default speaker.
        volume : float
            Volume of the sound, between 0 and 1.
        loops : int
            Number of loops to play (-1=forever, 0=single repeat).
        sampleRate : int or None
            Sample rate for synthesised tones (ignored for sound files). If None, 
            uses the sample rate of the current stream or a default of 44100 Hz.
        blockSize : int
            The size of the buffer on the sound card (small for low latency, 
            large for stability).
        preBuffer : int
            Integer to control streaming/buffering:
            - -1 means store all
            - 0 (no buffer) means stream from disk
            - potentially we could buffer a few secs(!?)
        hamming : bool
            Whether the sound should be apodized (i.e., the onset and offset 
            smoothly ramped up from down to zero). The function apodize uses a 
            Hanning window, but arguments named 'hamming' are preserved so that
             existing code is not broken by the change from Hamming to Hanning 
             internally. Not applied to sounds from files.
        startTime : float
            For sound files, this controls the start of the snippet to be played.
        stopTime : float
            For sound files, this controls the end of the snippet to be played.
        name : str
            String for logging purposes.
        autoLog : bool
            Whether to automatically log every change.

        """
        self.preBuffer = preBuffer
        self.sound = value
        self.speaker = speaker
        self.name = name
        self.secs = secs  # for any synthesised sounds (notesand freqs)
        self.octave = octave  # for note name sounds
        self.loops = loops
        self._loopsFinished = 0
        self.volume = volume
        self.startTime = startTime  # for files
        self.stopTime = stopTime  # for files specify thesection to be played
        self.blockSize = blockSize  # can be per-sound unlike other backends
        self.frameN = 0
        self._tSoundRequestPlay = 0

        if sampleRate:  #a rate was requested so use it
            self.sampleRate = sampleRate
        else:  # no requested rate so use current stream or a default of 44100
            rate = 44100  # start with a default
            for streamLabel in streams:  # then look to see if we have an open stream and use that
                rate = streams[streamLabel].sampleRate
            self.sampleRate = rate

        self.stereo = stereo

        self.channels = 2  # default to stereo but will be updated by setSound
        if isinstance(value, np.ndarray):
            self.channels = value.shape[1]  # let this be set by stereo

        self.multichannel = False
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

        self._isPlaying = False

    @property
    def isPlaying(self):
        """`True` if the audio playback is ongoing.
        """
        return self._isPlaying

    @property
    def stereo(self):
        """Whether the sound is stereo (2 channels) or mono (1 channel). 
        
        Setting this will update the `channels` property accordingly, but if 
        `stereo` is set to -1 (auto), then the number of channels will be
        determined automatically based on the sound data.

        """
        return self.__dict__['stereo']

    @stereo.setter
    def stereo(self, val):
        self.__dict__['stereo'] = val
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

        Parameters
        ----------
        value : int, str, np.ndarray or AudioClip
            The sound to be played. Can be a note name (e.g., "C", "Bfl"), a filename, 
            a frequency in Hz, or an Nx2 numpy array of floats in the range -1:1 
            representing the sound waveform.
        secs : float
            Duration of the sound (for synthesised tones, ignored for sound files).
        octave : int
            Which octave to use for note names (4 is middle), ignored for sound files.
            Middle octave of a piano is 4. Most computers won't output sounds in the 
            bottom octave (1) and the top octave (8) is generally painful.
        hamming : bool or None
            Whether the sound should be apodized (i.e., the onset and offset smoothly 
            ramped up from down to zero). The function apodize uses a Hanning window, 
            but arguments named 'hamming' are preserved so that existing code is not 
            broken by the change from Hamming to Hanning internally. Not applied to 
            sounds from files.
        log : bool
            Whether to log this change.

        """
        # start with the base class method
        _SoundBase.setSound(self, value, secs, octave, hamming, log)

        try:
            label, s = streams.getStream(
                sampleRate=self.sampleRate,
                channels=self.channels,
                blockSize=self.blockSize)
        except SoundFormatError as err:
            # try to use something similar (e.g. mono->stereo)
            # then check we have an appropriate stream open
            altern = streams._getSimilar(
                sampleRate=self.sampleRate,
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

        if not hamming:
            return
        
        # 5ms or 15th of stimulus (for short sounds)
        hammDur = min(0.005,  # 5ms
                        self.secs / 15.0)  # 15th of stim
        self._hammingWindow = HammingWindow(
            winSecs=hammDur,
            soundSecs=self.secs,
            sampleRate=self.sampleRate)

    def _setSndFromClip(self, clip):
        """Set the sound from an AudioClip object.
        
        Parameters
        ----------
        clip : AudioClip
            The AudioClip object containing the sound data to be set.

        """
        if self.channels == -1:
            if self.stereo == 0:
                self.channels = 1
            elif self.stereo == 1:
                self.channels = 2

        thisArray = clip.samples

        self.sndArr = np.asarray(thisArray)
        if thisArray.ndim == 1:
            self.sndArr.shape = [len(thisArray), 1]  # make 2D for broadcasting
        if self.channels == 2 and self.sndArr.shape[1] == 1:  # mono -> stereo
            self.sndArr = self.sndArr.repeat(2, axis=1)
        elif self.sndArr.shape[1] == 1:  # if channels in [-1,1] then pass
            pass
        else:
            try:
                self.sndArr.shape = [len(thisArray), self.channels]
            except ValueError:
                raise ValueError(
                    "Failed to format sound with shape {} into sound "
                    "with channels={}".format(
                        self.sndArr.shape, self.channels))

        # is this stereo?
        if self.stereo == -1:  # auto stereo. Try to detect
            if self.sndArr.shape[1] == 1:
                self.stereo = 0
            elif self.sndArr.shape[1] == 2:
                self.stereo = 1
            elif self.sndArr.shape[1] >= 2:
                self.multichannel = True
                # raise IOError("Couldn't determine whether array is "
                #               "stereo. Shape={}".format(self.sndArr.shape))

        self._nSamples = thisArray.shape[0]
        if self.stopTime == -1:
            self.duration = self._nSamples / float(self.sampleRate)
        else:
            self.duration = self.secs
        # set to run from the start:
        self.seek(0)
        self.sourceType = "array"

    def _channelCheck(self, array):
        """Checks whether stream has fewer channels than data. If so, raises an error 
        with instructions to user.
        
        """
        if self.channels < array.shape[1]:
            msg = ("The sound stream is set up incorrectly. You have fewer channels in the buffer "
                   "than in data file ({} vs {}).\n**Ensure you have selected 'Force stereo' in "
                   "experiment settings**".format(self.channels, array.shape[1]))
            logging.error(msg)
            raise ValueError(msg)

    def play(self, loops=None, when=None):
        """Start the sound playing

        Parameters
        --------------
        loops : int or None
            Number of loops to play (-1=forever, 0=single repeat). If `None`, uses the 
            value set during initialisation.
        when: float or None
            Time to begin playback, in seconds relative to the global clock. If `None`, 
            playback will start immediately.

        """
        if self.isPlaying:
            return

        if loops is not None and self.loops != loops:
            self.setLoops(loops)

        self._isPlaying = True
        self._tSoundRequestPlay = time.time()
        streams[self.streamLabel].takeTimeStamp = True
        streams[self.streamLabel].add(self)

    def pause(self):
        """Stop the sound but play will continue from here if needed.
        """
        # if self.status == PAUSED:
        #     return
        #
        # self.status = PAUSED
        streams[self.streamLabel].remove(self)

    def stop(self, reset=True):
        """Stop the sound and return to beginning.

        Parameters
        ----------
        reset : bool
            If `True`, the sound will be reset to the beginning (i.e., `t=0`) when
            stopped. If `False`, the sound will not be reset, so that if `play`
            is called again, the sound will resume from the current position rather 
            than the beginning.

        """
        if not self.isPlaying:
            return

        streams[self.streamLabel].remove(self)
        if reset:
            self.seek(0)

        self._isPlaying = False

    def _nextBlock(self):
        """Get the next block of sound data to be played.
        
        This is called internally by the sound stream during playback. It retrieves
        the next block of sound data based on the current time and the sound's properties, applies any necessary processing (e.g., Hamming window), and returns the block of data to be played.

        Returns
        -------
        block : np.ndarray
            The next block of sound data to be played that should be passed to the
            stream buffer. The shape is determined by the audio stream's channel 
            configuration (e.g., mono or stereo) and chunk size.

        """
        if not self.isPlaying:
            return
        
        samplesLeft = int((self.duration - self.t) * self.sampleRate)
        nSamples = min(self.blockSize, samplesLeft)
        
        if self.sourceType == 'file' and self.preBuffer == 0:
            # streaming sound block-by-block direct from file
            block = self.sndFile.read(nSamples)
            # TODO: check if we already finished using sndFile?
        elif (self.sourceType == 'file' and self.preBuffer == -1) \
                or self.sourceType == 'array':
            # An array, or a file entirely loaded into an array
            ii = int(round(self.t * self.sampleRate))
            if self.stereo == 1 or self.multichannel:  # don't treat as boolean. Might be -1
                block = self.sndArr[ii:ii + nSamples, :]
            elif self.stereo == 0:
                block = self.sndArr[ii:ii + nSamples]
            else:
                raise IOError("Unknown stereo type {!r}".format(self.stereo))
            if ii + nSamples > len(self.sndArr):
                self._EOS()
        elif self.sourceType == 'freq':
            startT = self.t
            stopT = self.t + self.blockSize / float(self.sampleRate)
            uu = self.freq * _piTimes2
            xx = np.linspace(
                start=startT * uu,
                stop=stopT * uu,
                num=self.blockSize, endpoint=False
            )
            xx.shape = [self.blockSize, 1]
            block = np.sin(xx)
            # if run beyond our desired t then set to zeros
            if stopT > (self.secs):
                tRange = np.linspace(
                    startT, stopT, 
                    num=self.blockSize, 
                    endpoint=False)
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

        self.t += self.blockSize / float(self.sampleRate)

        return block

    def seek(self, t):
        """Seek to a specific time in the sound.

        Parameters
        ----------
        t : float
            The time (in seconds) to seek to.

        """
        self.t = t
        self.frameN = int(round(t * self.sampleRate))
        if self.sndFile and not self.sndFile.closed:
            self.sndFile.seek(self.frameN)

    def _EOS(self, reset=True):
        """End-of-stream (EOS) callback for when a sound finishes playing. 
        
        This is called internally by the sound stream when a sound has finished 
        playing. It checks whether the number of loops has been completed and if so, 
        stops the sound and removes it from the stream.

        Parameters
        ----------
        reset : bool
            If `True`, the sound will be reset to the beginning (i.e., `t=0`) when
            stopped. If `False`, the sound will not be reset, so that if `play`
            is called again, the sound will resume from the current position rather 
            than the beginning.

        """
        self._loopsFinished += 1
        if self.loops == 0:
            self.stop(reset=reset)
        elif self.loops > 0 and self._loopsFinished >= self.loops:
            self.stop(reset=reset)

        streams[self.streamLabel].remove(self)
        self._isPlaying = False

    @property
    def stream(self):
        """Read-only property returns the the stream on which the sound
        will be played.
        """
        return streams[self.streamLabel]
    
        
    def _setSndFromArrayLegacy(self, thisArray):
        """
        Prior to 2025.1.0, _SoundBase didn't have a `_setSndFromArray` method to inherit. This legacy method can be substituted in if the version of PsychoPy installed is too old.
        """
        from psychopy.sound.audioclip import AudioClip
        clip = AudioClip(thisArray, sampleRateHz=self.sampleRate)
        self._setSndFromClip(clip)


if not hasattr(SoundDeviceSound, "_setSndFromArray"):
    SoundDeviceSound._setSndFromArray = SoundDeviceSound._setSndFromArrayLegacy

# entry point for sound module to import the correct Sound class
Sound = SoundDeviceSound


if __name__ == "__main__":
    pass