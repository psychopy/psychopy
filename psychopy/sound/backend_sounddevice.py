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
from ..hardware import DeviceManager
from psychopy.hardware.speaker import SpeakerDevice

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
                                             callback=self._callback)
            self._sdStream.start()
            self.device = self._sdStream.device
            self.latency = self._sdStream.latency
            self.cpu_load = self._sdStream.cpu_load
            atexit.register(self.__del__)

        # self._tSoundRequestPlay = -1  # time the sound was requested to play
        self._isPlaying = False

    @property
    def isPlaying(self):
        """`True` if the audio playback is ongoing."""
        return self._isPlaying

    def _callback(self, toSpk, blockSize, timepoint, status):
        """Callback function for the sound stream. 
        
        This is called internally by the `sounddevice` library to fetch the next 
        block of audio data to be played when the input output buffer is starved. 
        It iterates through all currently playing sounds, fetches the next block 
        of audio data for each sound, applies the volume, and adds it to the 
        output buffer. If a sound has finished playing (i.e., the fetched block is 
        shorter than the buffer size), it is removed from the list of currently 
        playing sounds.

        Parameters
        ----------
        toSpk : np.ndarray
            A numpy array to be populated with the audio data to be played.
        blockSize : int
            The number of frames to be included in each block of audio data.
        timepoint : object
            An object containing timing information for the callback, with 
            attributes `currentTime`, `inputBufferAdcTime`, and 
            `outputBufferDacTime`.
        status : int
            Status flags for the callback (e.g., indicating underflow or 
            overflow).
        
        """
        if self.takeTimeStamp and hasattr(self, 'lastFrameTime'):
            logging.info("Entered callback: {} ms after last frame end"
                         .format((time.monotonic() - self.lastFrameTime) * 1000))
            # logging.info("Entered callback: {} ms after sound start"
            #              .format(
            #     (time.monotonic() - self._tSoundRequestPlay) * 1000))
        
        toSpk.fill(0.0)  # fill buffer with silence to start with

        # check if we have reached the requested play time
        outputBufferDacTime = timepoint.outputBufferDacTime

        self.frameN += 1
        for thisSound in self.sounds.copy():
            if thisSound._tSoundRequestPlay > outputBufferDacTime:
                continue  # not time to play this sound yet

            dat = thisSound._nextBlock(blockSize)
            if dat is None:  # no data for some reason (e.g., sound finished)
                continue

            if thisSound.volume != 1.0:
                dat *= thisSound.volume  # Set the volume block by block

            datSize = len(dat)
            datDims = len(dat.shape)

            # old method
            if self.channels == 2 and datDims == 2:
                toSpk[:datSize, :] += dat  # add to out stream
            elif self.channels == 2 and datDims == 1:
                toSpk[:datSize, 0] += dat 
                toSpk[:datSize, 1] += dat  
            elif self.channels == 1 and datDims == 2:
                toSpk[:datSize, :] += dat
            else:
                toSpk[:datSize, 0:self.channels] += dat 

            # check if that was a short block (sound is finished)
            if datSize < len(toSpk[:, :]):
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


class SoundDeviceSound(_SoundBase):
    """Play a variety of sounds using the SoundDevice library.
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
        if isinstance(speaker, str) and DeviceManager.getDevice(speaker):
            speaker = DeviceManager.getDevice(speaker)
        # make sure speaker is a SpeakerDevice
        if not isinstance(speaker, SpeakerDevice):
            speaker = SpeakerDevice(speaker)
        self.speaker = speaker

        self.preBuffer = preBuffer
        self.volume = volume
        self.sound = value
        self.name = name
        self.secs = secs  # for any synthesised sounds (notesand freqs)
        self.octave = octave  # for note name sounds
        self.loops = loops
        self._loopsFinished = 0
        self.startTime = startTime  # for files
        self.stopTime = stopTime  # for files specify thesection to be played
        self.blockSize = blockSize  # can be per-sound unlike other backends
        self.frameN = 0 
        self.win = None  # for timing play with window flips
        self._tSoundRequestPlay = -1
        # offset within the block which the sound started at, for accurate 
        # timing of play requests
        self._blockOffset = -1  # sub-block offest

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

        self._isStarted = False
        self._isPlaying = False
        self._isFinished = False

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

    @property
    def sampleRateHz(self):
        """Get the sample rate of the sound stream, in Hz.

        This is an alias of the `sampleRate` property, provided for compatibility 
        with other backends.

        Returns
        -------
        float or None
            Sample rate of the sound stream, in Hz. Returns `None` if the sample 
            rate is not known (e.g., if the stream has not been created yet).

        """
        return self.sampleRate

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

    @property
    def isPlaying(self):
        """`True` if the audio playback is ongoing."""
        # This will update _isPlaying if sound has stopped by _EOS()
        return self._isPlaying

    @property
    def isFinished(self):
        """`True` if the audio playback has completed."""
        return self._isFinished

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
        
    def start(self):
        """Start the audio stream.

        This starts the audio stream and prepares it for playback. Calling this
        sometime before `play` can help to reduce latency when `play` is called, 
        as the stream will already be active and ready to receive audio data. 
        However, if `play` is called without first calling `start`, the stream will
        be started automatically.

        """
        print("Starting stream {}...".format(self.streamLabel))
        streams[self.streamLabel].takeTimeStamp = True
        streams[self.streamLabel].add(self)
        self._isStarted = True

    def play(self, loops=None, when=None, log=None):
        """Start playing the sound.

        Parameters
        --------------
        loops : int or None
            Number of loops to play (-1=forever, 0=single repeat). If `None`, uses the 
            value set during initialisation.
        when: float, `psychopy.visual.Window` or None
            Time to begin playback, in seconds relative to the global clock. If a 
            `psychopy.visual.Window` is passed, the audio will be played at the 
            next window flip. If 0.0 or `None`, playback will start immediately.

        """
        if self.isPlaying:
            return

        if not self._isStarted:
            self.start()

        if loops is not None and self.loops != loops:
            # TODO - loop logic doesn't work with generated sounds
            self.setLoops(loops)

        self._isPlaying = True
        self._tSoundRequestPlay = time.monotonic()

        # handle scheduling of play time
        logTime = None
        if when is not None:
            if isinstance(when, (int, float)):
                self._tSoundRequestPlay += when
            elif hasattr(when, 'getFutureFlipTime'):
                logTime = when.getFutureFlipTime(clock=None)
                when = when.getFutureFlipTime(clock='now')
                self._tSoundRequestPlay += when
        else:
            if hasattr(self.win, 'getFutureFlipTime'):
                logTime = self.win.getFutureFlipTime(clock=None)
                when = self.win.getFutureFlipTime(clock='now')
                self._tSoundRequestPlay += when           

        if log and self.autoLog:
            logging.exp(u"Playing sound %s on speaker %s" % (
                self.name, self.speaker.name), obj=self, t=logTime)

    def pause(self):
        """Stop the sound but play will continue from here if needed.
        """
        streams[self.streamLabel].remove(self)
        # eventually we will keep the stream 'hot' and `stop` will actually 
        # stop the stream and reset to the beginning
        self._isPlaying = False

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

        self._isPlaying = self._isStarted = False

    def _nextBlock(self, blockSize=None):
        """Get the next block of sound data to be played.
        
        This is called internally by the sound stream during playback. It retrieves
        the next block of sound data based on the current time and the sound's properties, 
        applies any necessary processing (e.g., Hamming window), and returns the block of 
        data to be played.

        Parameters
        ----------
        blockSize : int or None
            The size of the block of audio data to be returned. If `None`, uses the 
            block size configured for the stream.

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
        blockSize = blockSize or self.blockSize
        nSamples = min(blockSize, samplesLeft)
        
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
            stopT = self.t + blockSize / float(self.sampleRate)
            uu = self.freq * _piTimes2
            xx = np.linspace(
                start=startT * uu,
                stop=stopT * uu,
                num=blockSize, endpoint=False
            )
            xx.shape = [blockSize, 1]
            block = np.sin(xx)
            # if run beyond our desired t then set to zeros
            if stopT > (self.secs):
                tRange = np.linspace(
                    startT, stopT, 
                    num=blockSize, 
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
            self._isFinished = True
        elif self.loops > 0 and self._loopsFinished >= self.loops:
            self.stop(reset=reset)
            self._isFinished = True

    @property
    def stream(self):
        """Read-only property returns the the stream on which the sound
        will be played.
        """
        return streams[self.streamLabel]
    
        
    def _setSndFromArrayLegacy(self, thisArray):
        """
        Prior to 2025.1.0, _SoundBase didn't have a `_setSndFromArray` method to 
        inherit. This legacy method can be substituted in if the version of 
        PsychoPy installed is too old.
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
