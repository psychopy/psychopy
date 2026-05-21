# -*- coding: utf-8 -*-

"""Psychotoolbox interface for microphones.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    "PsychtoolboxMicrophoneDevice",
]

import sys
import time
from ._base import BaseMicrophoneDevice, MicrophoneResponse
import numpy as np
from psychtoolbox import audio as audio
from psychopy import logging as logging, prefs, core
from psychopy.hardware.exceptions import DeviceNotConnectedError
from psychopy.localization import _translate
from psychopy.constants import NOT_STARTED
from psychopy.hardware import BaseDevice, BaseResponse, BaseResponseDevice
from psychopy.sound.audiodevice import AudioDeviceInfo, AudioDeviceStatus
from psychopy.sound.audioclip import AudioClip
from psychopy.sound.exceptions import AudioInvalidCaptureDeviceError, AudioInvalidDeviceError, \
    AudioStreamError, AudioRecordingBufferFullError
from psychopy.tools import systemtools as st
from psychopy.tools.audiotools import SAMPLE_RATE_48kHz
import threading


_hasPTB = True
try:
    import psychtoolbox.audio as audio
except (ImportError, ModuleNotFoundError):
    logging.warning(
        "The 'psychtoolbox' library cannot be loaded but is required for audio "
        "capture (use `pip install psychtoolbox` to get it). Microphone "
        "recording will be unavailable this session. Note that opening a "
        "microphone stream will raise an error.")
    _hasPTB = False


class PsychtoolboxMicrophoneDevice(BaseMicrophoneDevice, aliases=["mic", "microphone"]):
    """Class for recording audio from a microphone or input stream.

    Creating an instance of this class will open a stream using the specified
    device. Streams should remain open for the duration of your session. When a
    stream is opened, a buffer is allocated to store samples coming off it.
    Samples from the input stream will writen to the buffer once
    :meth:`~MicrophoneDevice.start()` is called.

    Parameters
    ----------
    index : int or `~psychopy.sound.AudioDevice`
        Audio capture device to use. You may specify the device either by index
        (`int`) or descriptor (`AudioDevice`).
    sampleRateHz : int
        Sampling rate for audio recording in Hertz (Hz). By default, 48kHz
        (``sampleRateHz=48000``) is used which is adequate for most consumer
        grade microphones (headsets and built-in).
    channels : int
        Number of channels to record samples to `1=Mono` and `2=Stereo`.
    streamBufferSecs : float
        Stream buffer size to pre-allocate for the specified number of seconds.
        The default is 2.0 seconds which is usually sufficient.
    maxRecordingSize : int
        Maximum recording size in kilobytes (Kb). Since audio recordings tend to
        consume a large amount of system memory, one might want to limit the
        size of the recording buffer to ensure that the application does not run
        out of memory. By default, the recording buffer is set to 24000 KB (or
        24 MB). At a sample rate of 48kHz, this will result in 62.5 seconds of
        continuous audio being recorded before the buffer is full. You may 
        specify how to handle the buffer when it is full using the 
        `policyWhenFull` parameter.
    policyWhenFull : str
        Policy to use when the recording buffer is full. Options are:
        - "ignore": When full, just don't record any new samples
        - "warn"/"warning": Same as ignore, but will log a warning
        - "error": When full, will raise an error
    audioLatencyMode : int or None
        Audio latency mode to use, values range between 0-4. If `None`, the
        setting from preferences will be used. Using `3` (exclusive mode) is
        adequate for most applications and required if using WASAPI on Windows
        for other settings (such audio quality) to take effect. Symbolic
        constants `psychopy.sound.audiodevice.AUDIO_PTB_LATENCY_CLASS_` can also
        be used.
    audioRunMode : int
        Run mode for the recording device. Default is standby-mode (`0`) which
        allows the system to put the device to sleep. However, when the device
        is needed, waking the device results in some latency. Using a run mode
        of `1` will keep the microphone running (or 'hot') with reduces latency
        when th recording is started. Cannot be set when after initialization at
        this time.
    pollingInterval : float or None
        Time in seconds to poll the audio stream for new samples. If `None`, the 
        stream will not be polled automatically and the user will need to call 
        `poll()` manually to update the recording buffer. This should be less than 
        the `streamBufferSecs` parameter to ensure that the buffer does not 
        overflow. By default, polling occurs every 0.1 seconds.

    Examples
    --------
    Capture 10 seconds of audio from the primary microphone::

        import psychopy.core as core
        import psychopy.sound.microphone.Microphone as Microphone

        mic = Microphone(bufferSecs=10.0)  # open the microphone
        mic.start()  # start recording
        core.wait(10.0)  # wait 10 seconds
        mic.stop()  # stop recording

        audioClip = mic.getRecording()

        print(audioClip.duration)  # should be ~10 seconds
        audioClip.save('test.wav')  # save the recorded audio as a 'wav' file

    The prescribed method for making long recordings is to poll the stream once
    per frame (or every n-th frame)::

        mic = Microphone(bufferSecs=2.0)
        mic.start()  # start recording

        # main trial drawing loop
        mic.poll()
        win.flip()  # calling the window flip function

        mic.stop()  # stop recording
        audioClip = mic.getRecording()

    """
    # Force the use of WASAPI for audio capture on Windows. If `True`, only
    # WASAPI devices will be returned when calling static method
    # `Microphone.getDevices()`
    enforceWASAPI = True

    def __init__(
            self,
            index=None,
            sampleRateHz=None,
            channels=None,
            streamBufferSecs=2.0,
            maxRecordingSize=-1,
            policyWhenFull='warn',
            exclusive=False,
            audioRunMode=1,
            pollingInterval=0.1,
            # legacy
            audioLatencyMode=None,
        ):
        super().__init__()

        if not _hasPTB:  # fail if PTB is not installed
            raise ModuleNotFoundError(
                "Microphone audio capture requires package `psychtoolbox` to "
                "be installed.")

        from psychopy.hardware import DeviceManager

        # numericise index if needed
        if isinstance(index, str):
            try:
                index = int(index)
            except ValueError:
                pass

        # get information about the selected device
        if isinstance(index, AudioDeviceInfo):
            # if already an AudioDeviceInfo object, great!
            self._device = index
        elif index in (-1, None):
            # get all devices
            _devices = PsychtoolboxMicrophoneDevice.getDevices()
            # if there are none, error
            if not len(_devices):
                raise DeviceNotConnectedError(
                    _translate(
                        "Could not choose default recording device as no recording "
                        "devices are connected."
                    ), 
                    deviceClass=PsychtoolboxMicrophoneDevice
                )

            # Try and get the best match which are compatible with the user's
            # specified settings.
            if sampleRateHz is not None or channels is not None:
                self._device = self.findBestDevice(
                    index=_devices[0].deviceIndex,  # use first that shows up
                    sampleRateHz=sampleRateHz,
                    channels=channels
                )
            else:
                self._device = _devices[0]
            
            # Check if the default device settings are differnt than the ones 
            # specified by the user, if so, warn them that the default device
            # settings are overwriting their settings.
            if channels is None:
                channels = self._device.inputChannels
            elif channels != self._device.inputChannels:
                logging.warning(
                    "Number of channels specified ({}) does not match the "
                    "default device's number of input channels ({}).".format(
                        channels, self._device.inputChannels))
                channels = self._device.inputChannels

            if sampleRateHz is None:
                sampleRateHz = self._device.defaultSampleRate
            elif sampleRateHz != self._device.defaultSampleRate:
                logging.warning(
                    "Sample rate specified ({}) does not match the default "
                    "device's sample rate ({}).".format(
                        sampleRateHz, self._device.defaultSampleRate))
                sampleRateHz = self._device.defaultSampleRate

        elif isinstance(index, str):
            # if given a str that's a name from DeviceManager, get info from device
            device = DeviceManager.getDevice(index)
            # try to duplicate and fail if not found
            if isinstance(device, PsychtoolboxMicrophoneDevice):
                self._device = device._device
            else:
                # if not found, find best match
                self._device = self.findBestDevice(
                    index=index,
                    sampleRateHz=sampleRateHz,
                    channels=channels
                )
        else:
            # get best match
            self._device = self.findBestDevice(
                index=index,
                sampleRateHz=sampleRateHz,
                channels=channels
            )

        devInfoText = ('Using audio device #{} ({}) for audio capture. '
            'Full spec: {}').format(
                self._device.deviceIndex, 
                self._device.deviceName, 
                self._device)
        
        logging.info(devInfoText)

        # error if specified device is not suitable for capture
        if not self._device.isCapture:
            raise AudioInvalidCaptureDeviceError(
                'Specified audio device not suitable for audio recording. '
                'Has no input channels.')

        # get these values from the configured device
        self._channels = self._device.inputChannels
        logging.debug('Set recording channels to {} ({})'.format(
            self._channels, 'stereo' if self._channels > 1 else 'mono'))

        self._sampleRateHz = self._device.defaultSampleRate
        logging.debug('Set stream sample rate to {} Hz'.format(
            self._sampleRateHz))

        # set the audio latency mode
        if exclusive:
            self._audioLatencyMode = 2
        else:
            self._audioLatencyMode = 1
        logging.debug(
            'Set audio latency mode to {}'.format(self._audioLatencyMode)
        )

        # internal recording buffer size in seconds
        assert isinstance(streamBufferSecs, (float, int))
        self._streamBufferSecs = float(streamBufferSecs)

        # PTB specific stuff
        self._mode = 2  # open a stream in capture mode

        # get audio run mode
        assert isinstance(audioRunMode, (float, int)) and \
               (audioRunMode == 0 or audioRunMode == 1)
        self._audioRunMode = int(audioRunMode)

        # polling, may be None if user doesn't want to use auto polling
        self._pollingInterval = pollingInterval
        self._pollingTimerThread = None  # set later
        self._pollingLock = threading.Lock()  # lock to prevent race conditions

        # status flag for Builder
        self._statusFlag = NOT_STARTED

        # recording buffer information
        self._recordingBuffer = []  # use a list
        self._totalSamples = 0
        self._absRecStartTime = self._absRecStopTime = -1.0
        self._recPositionSecs = 0.0

        self._maxRecordingSize = (
            -1 if maxRecordingSize is None else int(maxRecordingSize))
        self._policyWhenFull = policyWhenFull

        logging.debug('Audio capture device #{} ready'.format(
            self._device.deviceIndex))

        # open stream
        self._opening = self._closing = False
        self.open()

        # list to store listeners in
        self.listeners = []
    
    @property
    def maxRecordingSize(self):
        """
        Until a file is saved, the audio data from a Microphone needs to be stored in RAM. To avoid 
        a memory leak, we limit the amount which can be stored by a single Microphone object. The 
        `maxRecordingSize` parameter defines what this limit is.

        Parameters
        ----------
        value : int
            How much data (in kb) to allow, default is 24mb (so 24,000kb)
        """
        return self._maxRecordingSize
    
    @maxRecordingSize.setter
    def maxRecordingSize(self, value):
        self._maxRecordingSize = int(value)
    
    @property
    def policyWhenFull(self):
        """
        Until a file is saved, the audio data from a Microphone needs to be stored in RAM. To avoid 
        a memory leak, we limit the amount which can be stored by a single Microphone object. The 
        `policyWhenFull` parameter tells the Microphone what to do when it's reached that limit.

        Parameters
        ----------
        value : str
            One of:
            - "ignore": When full, just don't record any new samples
            - "warn"/"warning": Same as ignore, but will log a warning
            - "error": When full, will raise an error
            - "roll"/"rolling": When full, clears the start of the buffer to make room for new samples
        """
        return self._policyWhenFull
    
    @policyWhenFull.setter
    def policyWhenFull(self, value):
        self._policyWhenFull = value

    def findBestDevice(self, index, sampleRateHz, channels):
        """
        Find the closest match among the microphone profiles listed by psychtoolbox as valid.

        Parameters
        ----------
        index : int
            Index of the device
        sampleRateHz : int
            Sample rate of the device
        channels : int
            Number of audio channels in input stream

        Returns
        -------
        AudioDeviceInfo
            Device info object for the chosen configuration

        Raises
        ------
        logging.Warning
            If an exact match can't be found, will use the first match to the device index and
            raise a warning.
        KeyError
            If no match is found whatsoever, will raise a KeyError
        """
        # start off with no chosen device and no fallback
        fallbackDevice = None
        chosenDevice = None
        # iterate through device profiles
        for profile in self.getDevices():
            # if same index, keep as fallback
            if index in (profile.deviceIndex, profile.deviceName):
                fallbackDevice = profile
            # if same everything, we got it!
            if all((
                index in (profile.deviceIndex, profile.deviceName),
                profile.defaultSampleRate == sampleRateHz,
                profile.inputChannels == channels,
            )):
                chosenDevice = profile

        if chosenDevice is None and fallbackDevice is not None:
            # if no exact match found, use fallback and raise warning
            logging.warning(
                f"Could not find exact match for specified parameters (index={index}, sampleRateHz="
                f"{sampleRateHz}, channels={channels}), falling back to best approximation ("
                f"index={fallbackDevice.deviceIndex}, "
                f"name={fallbackDevice.deviceName},"
                f"sampleRateHz={fallbackDevice.defaultSampleRate}, "
                f"channels={fallbackDevice.inputChannels})"
            )
            chosenDevice = fallbackDevice
        elif chosenDevice is None:
            # if no index match found, raise error
            raise DeviceNotConnectedError(
                _translate(
                    "Could not find any audio recording device with index {index}", 
                ).format(index=index), 
                deviceClass=PsychtoolboxMicrophoneDevice
            )

        return chosenDevice

    def isSameDevice(self, other):
        """
        Determine whether this object represents the same physical microphone as a given other
        object.

        Parameters
        ----------
        other : MicrophoneDevice, dict
            Other MicrophoneDevice to compare against, or a dict of params (which must include
            `index` as a key)

        Returns
        -------
        bool
            True if the two objects represent the same physical device
        """
        if isinstance(other, type(self)):
            # if given another object, get index
            index = other.index
        elif isinstance(other, dict) and "index" in other:
            # if given a dict, get index from key
            index = other['index']
        else:
            # if the other object is the wrong type or doesn't have an index, it's not this
            return False

        return index in (self.index, self._device.deviceName)

    @staticmethod
    def getDevices():
        """Get a `list` of audio capture device (i.e. microphones) descriptors.
        On Windows, only WASAPI devices are used.

        Returns
        -------
        list
            List of `AudioDevice` descriptors for suitable capture devices. If
            empty, no capture devices have been found.

        """
        try:
            PsychtoolboxMicrophoneDevice.enforceWASAPI = bool(prefs.hardware["audioForceWASAPI"])
        except KeyError:
            pass  # use default if option not present in settings

        # query PTB for devices
        if PsychtoolboxMicrophoneDevice.enforceWASAPI and sys.platform == 'win32':
            allDevs = audio.get_devices(device_type=13)
        else:
            allDevs = audio.get_devices()

        # make sure we have an array of descriptors
        allDevs = [allDevs] if isinstance(allDevs, dict) else allDevs

        # create list of descriptors only for capture devices
        devObjs = [AudioDeviceInfo.createFromPTBDesc(dev) for dev in allDevs]
        inputDevices = [desc for desc in devObjs if desc.isCapture]

        return inputDevices

    @staticmethod
    def getAvailableDevices():
        devices = []
        for profile in st.getAudioCaptureDevices():
            # get index as a name if possible
            index = profile.get('device_name', None)
            if index is None:
                index = profile.get('index', None)
            device = {
                'deviceName': profile.get('device_name', "Unknown Microphone"),
                'deviceClass': "psychopy.hardware.microphone.MicrophoneDevice",
                'index': index,
                'sampleRateHz': profile.get('defaultSampleRate', None),
                'channels': profile.get('inputChannels', None),
            }
            devices.append(device)

        return devices

    # def warmUp(self):
    #     """Warm-/wake-up the audio stream.
    #
    #     On some systems the first time `start` is called incurs additional
    #     latency, whereas successive calls do not. To deal with this, it is
    #     recommended that you run this warm-up routine prior to capturing audio
    #     samples. By default, this routine is called when instancing a new
    #     microphone object.
    #
    #     """
    #     # We should put an actual test here to see if timing stabilizes after
    #     # multiple invocations of this function.
    #     self._stream.start()
    #     self._stream.stop()

    @property
    def channels(self):
        """Number of audio channels to record samples to (`int`).
        """
        return self._channels
    
    @property
    def sampleRateHz(self):
        """Sampling rate for audio recording in Hertz (`int`).
        """
        return self._sampleRateHz
    
    @property
    def device(self):
        """Audio device descriptor (`AudioDeviceInfo`).
        """
        return self._device

    @property
    def recording(self):
        """Reference to the current recording buffer (`RecordingBuffer`)."""
        return self._recordingBuffer

    @property
    def recordingBuffer(self):
        return self._recordingBuffer
    
    @recordingBuffer.setter
    def recordingBuffer(self, value):
        self._recordingBuffer = value

    @property
    def recBufferSecs(self):
        """Capacity of the recording buffer in seconds (`float`)."""
        return self._totalSamples / float(self._sampleRateHz)
    
    @property
    def recSampleCount(self):
        """Total number of samples in the recording buffer (`int`).

        This is the total number of samples that have been recorded since the
        last `start` call. If the stream is not started, this will return `0`.

        """
        return self._totalSamples

    @property
    def latencyBias(self):
        """Latency bias to add when starting the microphone (`float`).
        """
        return self._stream.latency_bias

    @latencyBias.setter
    def latencyBias(self, value):
        self._stream.latency_bias = float(value)

    @property
    def audioLatencyMode(self):
        """Audio latency mode in use (`int`). Cannot be set after
        initialization.

        """
        return self._audioLatencyMode

    @property
    def streamBufferSecs(self):
        """Size of the internal audio storage buffer in seconds (`float`).

        To ensure all data is captured, there must be less time elapsed between
        subsequent `getAudioClip` calls than `bufferSecs`.

        """
        return self._streamBufferSecs

    @property
    def streamStatus(self):
        """Status of the audio stream (`AudioDeviceStatus` or `None`).

        See :class:`~psychopy.sound.AudioDeviceStatus` for a complete overview
        of available status fields. This property has a value of `None` if
        the stream is presently closed.

        Examples
        --------
        Get the capture start time of the stream::

            # assumes mic.start() was called
            captureStartTime = mic.status.captureStartTime

        Check if microphone recording is active::

            isActive = mic.status.active

        Get the number of seconds recorded up to this point::

            recordedSecs = mic.status.recordedSecs

        """
        currentStatus = self._stream.status
        if currentStatus != -1:
            return AudioDeviceStatus.createFromPTBDesc(currentStatus)

    @property
    def isRecBufferFull(self):
        """`True` if there is an overflow condition with the recording buffer.

        If this is `True`, then `poll()` is still collecting stream samples but
        is no longer writing them to anything, causing stream samples to be
        lost.

        """
        return self._totalSamples >= self._maxRecordingSize

    @property
    def isStarted(self):
        """``True`` if stream recording has been started (`bool`)."""
        return self._isStarted

    @property
    def isRecording(self):
        """``True`` if stream recording has been started (`bool`). Alias of
        `isStarted`."""
        return self.isStarted

    @property
    def index(self):
        return self._device.deviceIndex

    def testDevice(self, duration=1, testSound=None):
        """
        Make a recording to test the microphone.

        Parameters
        ----------
        duration : float, int
            How long to record for? In seconds.
        testSound : str, AudioClip, None
            Sound to play to test mic. Use "sine", "square" or "sawtooth" to generate a sound of correct
            duration using AudioClip. Use None to not play a test sound.

        Returns
        -------
        bool
            True if test passed. On fail, will log the error at level "debug".
        """
        # if given a string for testSound, generate
        if testSound in ("sine", "square", "sawtooth"):
            testSound = getattr(AudioClip, testSound)(duration=duration)

        try:
            # record
            self.start(stopTime=duration)
            # play testSound
            if testSound is not None:
                from psychopy.sound import Sound
                snd = Sound(value=testSound)
                snd.play()
            # sleep for duration
            time.sleep(duration)
            # poll to refresh recording
            self._pollWithLock()
            # get new clip
            clip = self.getRecording()
            # check that clip matches test sound
            if testSound is not None:
                # todo: check the recording against testSound
                pass

            return True

        except Exception as err:
            logging.debug(f"Microphone test failed. Error: {err}")

            raise err
        
    @property
    def recordingTime(self):
        """Current position in the recording buffer in seconds (`float`).

        This is the position of the next sample to be written to the recording
        buffer. If the stream is not started, this will return `0.0`.

        """
        return self._recPositionSecs
    
    def _setupAutoPolling(self):
        """Set up automatic polling of the stream at regular intervals.

        This is used to ensure that the recording buffer is updated with new
        samples from the stream even if the user does not call `poll()` manually.
        """
        if self._pollingInterval is None:
            logging.debug(
                "No polling interval specified, user must call `poll()` manually to update "
                "the recording buffer with new samples.")
            return  # do not set up polling if no interval specified
        
        class PollingTimerThread(threading.Thread):
            """Thread class used to call the poll method at regular 
            intervals.
            """
            def __init__(self, interval, function):
                super().__init__()
                self.interval = interval
                self.function = function
                self._stop_event = threading.Event()

            def run(self):
                while not self._stop_event.is_set():
                    time.sleep(self.interval)
                    self.function()

            def cancel(self):
                self._stop_event.set()

        if self._pollingTimerThread is not None:
            self._pollingTimerThread.cancel()

        # make sure the polling interval is a positive number
        self._pollingInterval = float(self._pollingInterval)
        if self._pollingInterval <= 0:
            raise ValueError("Polling interval must be a positive number.")
        
        logging.debug(
            "Setting up automatic polling of the audio stream every {} seconds.".format(
                self._pollingInterval))

        # make sure the polling interval is reasonable given the stream buffer size to avoid overflow
        if self._pollingInterval >= self._streamBufferSecs:
            logging.warning(
                "Polling interval ({}) is greater than or equal to the stream buffer size ({}). "
                "This may result in buffer overflow and lost samples. Consider reducing the polling "
                "interval or increasing the stream buffer size.".format(
                    self._pollingInterval, self._streamBufferSecs))
            
        # set up a thread to call the poll method at regular intervals
        self._pollingTimerThread = PollingTimerThread(
            self._pollingInterval, 
            self._pollWithLock)
        self._pollingTimerThread.daemon = True
        self._pollingTimerThread.start()
            
    def start(self, when=None, waitForStart=0, stopTime=None):
        """Start an audio recording.

        Calling this method will begin capturing samples from the microphone and
        writing them to the buffer.

        Parameters
        ----------
        when : float, int or None
            When to start the stream. If the time specified is a floating point
            (absolute) system time, the device will attempt to begin recording
            at that time. If `None` or zero, the system will try to start
            recording as soon as possible.
        waitForStart : bool
            Wait for sound onset if `True`.
        stopTime : float, int or None
            Number of seconds to record. If `None` or `-1`, recording will
            continue forever until `stop` is called.

        Returns
        -------
        float
            Absolute time the stream was started.

        """
        self.open()
        return self._absRecStartTime

    def record(self, when=None, waitForStart=0, stopTime=None):
        """Start an audio recording (alias of `.start()`).

        Calling this method will begin capturing samples from the microphone and
        writing them to the buffer.

        Parameters
        ----------
        when : float, int or None
            When to start the stream. If the time specified is a floating point
            (absolute) system time, the device will attempt to begin recording
            at that time. If `None` or zero, the system will try to start
            recording as soon as possible.
        waitForStart : bool
            Wait for sound onset if `True`.
        stopTime : float, int or None
            Number of seconds to record. If `None` or `-1`, recording will
            continue forever until `stop` is called.

        Returns
        -------
        float
            Absolute time the stream was started.

        """
        return self.start(
            when=when,
            waitForStart=waitForStart,
            stopTime=stopTime)

    def stop(self, blockUntilStopped=True, stopTime=None):
        """Stop recording audio.

        Call this method to end an audio recording if in progress. This will
        simply halt recording and not close the stream. Any remaining samples
        will be polled automatically and added to the recording buffer.

        Parameters
        ----------
        blockUntilStopped : bool
            Halt script execution until the stream has fully stopped.
        stopTime : float or None
            Scheduled stop time for the stream in system time. If `None`, the
            stream will stop as soon as possible.

        Returns
        -------
        tuple or None
            Tuple containing `startTime`, `endPositionSecs`, `xruns` and
            `estStopTime`. Returns `None` if `stop` or `pause` was called
            previously before `start`.

        """
        # This function must be idempotent since it can be invoked at any time
        # whether a stream is started or not.
        if not self._isStarted or self._stream._closed:
            return

        if self._pollingTimerThread is not None:
            self._pollingTimerThread.cancel()  # stop the polling thread if it's running

        # poll remaining samples, if any
        _ = self._pollWithLock()

        startTime, endPositionSecs, xruns, estStopTime = self._stream.stop(
            block_until_stopped=0,
            stopTime=None)

        self._isStarted = False

        logging.debug(
            ('Device #{} stopped capturing audio samples at estimated time '
             't={}. Total overruns: {} Total recording time: {}').format(
                self._device.deviceIndex, estStopTime, xruns, endPositionSecs))

        return startTime, endPositionSecs, xruns, estStopTime

    def pause(self, blockUntilStopped=True, stopTime=None):
        """Pause a recording (alias of `.stop`).

        Call this method to end an audio recording if in progress. This will
        simply halt recording and not close the stream. Any remaining samples
        will be polled automatically and added to the recording buffer.

        Parameters
        ----------
        blockUntilStopped : bool
            Halt script execution until the stream has fully stopped.
        stopTime : float or None
            Scheduled stop time for the stream in system time. If `None`, the
            stream will stop as soon as possible.

        Returns
        -------
        tuple or None
            Tuple containing `startTime`, `endPositionSecs`, `xruns` and
            `estStopTime`. Returns `None` if `stop()` or `pause()` was called
            previously before `start()`.

        """
        if self._pollingTimerThread is not None:
            self._pollingTimerThread.cancel() 

        return self.stop(blockUntilStopped=blockUntilStopped, stopTime=stopTime)

    def open(self):
        """
        Open the audio stream.
        """
        # do nothing if stream is already open
        if self._stream is not None and not self._stream._closed:
            return
        # set flag that it's mid-open
        self._opening = True
        # search for open streams and if there is one, use it
        if self._device.deviceIndex in PsychtoolboxMicrophoneDevice._streams:
            logging.debug(
                f"Assigning audio stream for device #{self._device.deviceIndex} to a new "
                f"MicrophoneDevice object."
            )
            self._stream = PsychtoolboxMicrophoneDevice._streams[self._device.deviceIndex]
            return
        
        # if no open streams, make one
        logging.debug(
            f"Opening new audio stream for device #{self._device.deviceIndex}."
        )
        self._stream = PsychtoolboxMicrophoneDevice._streams[self._device.deviceIndex] = audio.Stream(
            device_id=self._device.deviceIndex,
            latency_class=self._audioLatencyMode,
            mode=self._mode,
            freq=self._device.defaultSampleRate,
            channels=self._device.inputChannels
        )
        # set run mode
        self._stream.run_mode = self._audioRunMode
        logging.debug('Set run mode to `{}`'.format(
            self._audioRunMode))
        # set latency bias
        self._stream.latency_bias = 0.0
        logging.debug('Set stream latency bias to {} ms'.format(
            self._stream.latency_bias))
        # pre-allocate recording buffer, called once
        self._stream.get_audio_data(self._streamBufferSecs)
        logging.debug(
            'Allocated stream buffer to hold {} seconds of data'.format(
                self._streamBufferSecs))

        # check if the stream has been
        if self.isStarted:
            return None

        if self._stream is None:
            raise AudioStreamError("Stream not ready.")
        
        # reset timer for possibly asleep
        self._possiblyAsleep = False
        # reset the recording buffer
        self._recordingBuffer = []
        self._totalSamples = 0
        self._recPositionSecs = 0.0

        # reset warnings
        # self._warnedRecBufferFull = False

        # open the stream and take audio samples
        self._absRecStartTime = self._stream.start(
            repetitions=0,
            when=0,
            wait_for_start=0,
            stop_time=None)

        # recording has begun or is scheduled to do so
        self._isStarted = True

        # polling, this thread calls the `poll` method at regular intervals
        if self._pollingInterval is not None:
            self._setupAutoPolling()

        logging.debug(
            'Scheduled start of audio capture for device #{} at t={}.'.format(
                self._device.deviceIndex, self._absRecStartTime))

        # set flag that it's done opening
        self._opening = False
        
    def close(self):
        """Close the audio stream.

        If there are any clients still using the stream, the close operation
        will be deferred until all clients have released the stream.

        Parameters
        ----------
        force : bool
            If `True`, forces the stream to close even if there are still clients
            using it. Use with caution as this may cause errors in any clients
            still using the stream.

        """
        if self._clients:  # prevent closing until all clients have called their `close` method
            logging.debug(
                "Attempted to close microphone stream while there are still {} "
                "client(s) using it.".format(len(self._clients))
            )  
            return
        
        # stop polling thread if it's running
        if self._pollingTimerThread is not None:
            self._pollingTimerThread.cancel()
            self._pollingTimerThread = None

        # clear any attached listeners
        self.clearListeners()

        # do nothing further if already closed
        if self._stream._closed:
            return
        
        # set flag that it's mid-close
        self._closing = True

        # remove ref to stream
        if self._device.deviceIndex in PsychtoolboxMicrophoneDevice._streams:
            PsychtoolboxMicrophoneDevice._streams.pop(self._device.deviceIndex)

        # close stream
        self._stream.close()
        logging.debug('Stream closed')

        # set flag that it's done closing
        self._closing = False
    
    def reopen(self):
        """
        Calls self.close() then self.open() to reopen the stream.
        """
        # get status at close
        status = self.isStarted
        # start timer
        start = time.time()
        # close then open
        self.close()
        self.open()
        # log time it took
        logging.info(
            f"Reopened microphone #{self.index}, took {time.time() - start:.3f}s"
        )
        # if mic was running beforehand, start it back up again now
        if status:
            self.start()

    @property
    def recordingEmpty(self):
        """`True` if the recording buffer is empty (`bool`).
        """
        return len(self._recordingBuffer) == 0
    
    @property
    def recordingFull(self):
        """`True` if the recording buffer is full (`bool`).
        """
        if self._maxRecordingSize < 0:
            return False
        return self._totalSamples >= self._maxRecordingSize
    
    @property
    def recStartTime(self):
        """Absolute time when the recording started (`float`).

        This is the time when the first sample was recorded. If the recording
        has not started, this will be `-1.0`.

        """
        return self._absRecStartTime
    
    def _getTime(self):
        """Get the current system time in seconds (`float`).

        This is used internally to timestamp recordings. It is not guaranteed to
        be the same time base as the one used by the audio stream, so absolute
        times returned by the stream should be used when possible.

        """
        return time.time()
    
    def _pollWithLock(self):
        """Call `poll` with the polling lock acquired. This is used internally to
        prevent race conditions when `poll` is called from the polling thread and 
        from user code at the same time.
        """
        with self._pollingLock:
            return self.poll()

    def poll(self):
        """Poll audio samples.

        Calling this method adds audio samples collected from the stream buffer
        to the recording buffer that have been captured since the last `poll`
        call. Time between calls of this function should be less than
        `bufferSecs`. You do not need to call this if you call `stop` before
        the time specified by `bufferSecs` elapses since the `start` call.

        Can only be called between called of `start` (or `record`) and `stop`
        (or `pause`).

        Returns
        -------
        tuple of (float, bool)
            Current recording position in samples (`int`) and number of 
            overflows (`int`). If the returned position is less than zero
            (negative) then microphone is still starting up and wont be ready
            until the position is greater than or equal to zero. If overflow 
            occurs, this means that the recording buffer is full and no more 
            samples can be added until polled. To prevent this, ensure that 
            `poll()` is called often enough or increase the size of the audio 
            buffer with `bufferSecs`.

        """
        # if not self._isStarted:
        #     logging.warning(
        #         "Attempted to poll samples from mic which hasn't started."
        #     )
        #    return
        if self._stream is None:
            logging.warning(
                "Attempted to poll samples from mic which has no stream."
            )
            return
        if self._stream._closed:
            logging.warning(
                "Attempted to poll samples from mic which has been closed."
            )
            return
        if self._opening or self._closing:
            action = "opening" if self._opening else "closing"
            logging.warning(
                f"Attempted to poll microphone while the stream was still {action}. Samples will be "
                f"lost."
            )
            return

        # poll the buffer and get new audio samples
        audioData, absRecPosition, overflow, cStartTime = self._stream.get_audio_data()
        sampleCount = len(audioData)
        self._rtBuffer = audioData.copy()
        
        # detect and handle the microphone going to sleep
        if sampleCount:
            # if we got samples, the device is awake, so stop figuring out if it's asleep
            self._possiblyAsleep = False
        elif self._possiblyAsleep is False:
            # if it was awake and now we've got no samples, store the time
            self._possiblyAsleep = time.time()
        elif self._possiblyAsleep + 1 < time.time():
            # if we've not had any evidence of it being awake for 1s, reopen
            logging.error(
                f"Microphone device appears to have gone to sleep, reopening to wake it up."
            )
            # mark as stopped so we don't recursively poll forever when stopping
            self._isStarted = False
            # reopen
            self.reopen()
            # start again
            self.start()
            # mark as not asleep so we don't restart again if the first poll is empty
            self._possiblyAsleep = False

        if overflow:
            logging.warning(
                "Audio stream buffer overflow, some audio samples have been "
                "lost! To prevent this, ensure `Microphone.poll()` is being "
                "called often enough, or increase the size of the audio buffer "
                "with `bufferSecs`.")

        # add samples to recording buffer
        if sampleCount and self._clients:
            # compute the absulute time of the end of the current recording pos
            absBlockStartTime = cStartTime + (absRecPosition / self._sampleRateHz)
            absBlockEndTime = cStartTime + (
                (absRecPosition + sampleCount) / self._sampleRateHz)
            
            # iterate over attached microphone objects and write data to their 
            # recording buffers if we're past the requested start time
            for mic in self._clients:
                reqStartTime = mic._tRecordingStartRequested
                reqStopTime = mic._tRecordingStopRequested
                if reqStartTime < absBlockEndTime and (
                        reqStopTime is None or absBlockStartTime < reqStopTime):
                    mic._recordingBuffer.append(self._rtBuffer)
                    mic._nRecordedFrames += sampleCount

        # if self.recordingFull and not self._policyWhenFull == 'ignore':
        #     if self._policyWhenFull == 'warn':
        #         logging.warning(
        #             "Recording buffer is full, no more samples will be added.")
        #     elif self._policyWhenFull == 'error':
        #         raise AudioStreamError(
        #             "Recording buffer is full, no more samples will be added.")
        
        return absRecPosition, overflow
    
    def _mergeAudioFragments(self):
        """Merge audio fragments into a single segment.
        
        This merges all audio fragments in the recoding buffer into a single
        `AudioClip` object. The recording buffer is then cleared and the first
        element is set to the merged segment.

        Returns
        -------
        bool
            `False` if the recording buffer has no fragments to merge, `True`
            otherwise.

        """
        if len(self._recordingBuffer) < 2:
            return False
        
        # get the sum of all audio samples in the recording buffer
        totalSamples = sum(
            [segment.samples.shape[0] for segment in self._recordingBuffer])

        # create a new array to hold all samples
        fullSegment = np.zeros(
            (totalSamples, self._recordingBuffer[0].channels), 
            dtype=np.float32, 
            order='C')
        
        # copy samples from each segment into the full segment
        idx = 0
        for segment in self._recordingBuffer:
            nSamples = segment.shape[0]
            fullSegment[idx:idx + nSamples, :] = segment
            idx += nSamples

        # set the recording
        self._recordingBuffer = [fullSegment]  

        return True
    
    def _getSegment(self, start=0, end=None):
        """Get a segment of audio samples from the recording buffer.

        Parameters
        ----------
        start : float
            Start time of the segment in seconds.
        end : float or None
            End time of the segment in seconds. If `None`, the segment will
            extend to the end of the recording buffer.

        Returns
        -------
        AudioClip or None
            Segment of the recording buffer. Returns `None` if the recording
            buffer is empty.

        """
        if self.recordingEmpty:
            return None
        
        self._mergeAudioFragments()  # merge audio fragments

        if not len(self._recordingBuffer[0]):
            raise AudioStreamError(
                "Could not access recording as microphone has sent no samples."
            )
        
        if start == 0 and end is None:  # return full recording
            return self._recordingBuffer[0]

        # get a range of samples within the recording buffer
        idxStart = int(start * self._sampleRateHz)
        idxEnd = -1 if end is None else int(end * self._sampleRateHz)
        
        return AudioClip(
            np.array(self._recordingBuffer[0][idxStart:idxEnd, :],
                     dtype=np.float32, order='C'),
            sampleRateHz=self._sampleRateHz)

    def getRecording(self):
        """Get audio data from the last microphone recording.

        Call this after `stop` to get the recording as an `AudioClip` object.
        Raises an error if a recording is in progress.

        Returns
        -------
        AudioClip
            Recorded data between the last calls to `start` (or `record`) and
            `stop`.

        """
        if self.isStarted:
            logging.warn(
                "Cannot get audio clip while recording is in progress, so "
                "stopping recording now."
            )
            self.stop()

        # get the segment
        return self._getSegment()  # full recording
    
    def getCurrentVolume(self, timeframe=0.2):
        """
        Get the current volume measured by the mic.

        Parameters
        ----------
        timeframe : float
            Time frame (s) over which to take samples from. Default is 0.1s.

        Returns
        -------
        float
            Current volume registered by the mic, will depend on relative volume 
            of the mic but should mostly be between 0 (total silence) and 1 
            (very loud).

        """
        # if mic hasn't started yet, return 0 as it's recorded nothing
        if not self.isStarted or self._stream._closed:
            return 0
        
        # poll most recent samples
        self._pollWithLock()

        if self.recordingEmpty:
            return 0.0

        clip = AudioClip(self._rtBuffer, sampleRateHz=self._sampleRateHz)

        # get average volume
        rms = clip.rms() * 10

        # round
        rms = np.round(rms.astype(np.float64), decimals=3)

        return rms

    def addListener(self, listener, startLoop=False):
        """
        Add a listener, which will receive all the same messages as this device.

        Parameters
        ----------
        listener : str or psychopy.hardware.listener.BaseListener
            Either a Listener object, or use one of the following strings to create one:
            - "liaison": Create a LiaisonListener with DeviceManager.liaison as the server
            - "print": Create a PrintListener with default settings
            - "log": Create a LoggingListener with default settings
        startLoop : bool
            If True, then upon adding the listener, start up an asynchronous loop to dispatch messages.
        """
        # add listener as normal
        listener = BaseResponseDevice.addListener(self, listener, startLoop=startLoop)
        # if we're starting a listener loop, start recording
        if startLoop:
            self.start()
        
        return listener

    def clearListeners(self):
        """
        Remove any listeners from this device.

        Returns
        -------
        bool
            True if completed successfully
        """
        # clear listeners as normal
        resp = BaseResponseDevice.clearListeners(self)
        # stop recording
        self.stop()

        return resp

    def dispatchMessages(self, clear=True):
        """
        Dispatch current volume as a MicrophoneResponse object to any attached listeners.

        Parameters
        ----------
        clear : bool
            If True, will clear the recording up until now after dispatching the volume. This is
            useful if you're just sampling volume and aren't wanting to store the recording.
        """
        # if mic is not recording, there's nothing to dispatch
        if not self.isStarted:
            return
        
        # poll the mic now
        self._pollWithLock()
        # create a response object
        message = MicrophoneResponse(
            logging.defaultClock.getTime(),
            self.getCurrentVolume(),
            device=self,
        )
        # dispatch to listeners
        for listener in self.listeners:
            listener.receiveMessage(message)
        
        return message
    
    def findSpeakers(self, allowedSpeakers=None, threshold=0.01):
        """
        Find speakers which this microphone can hear.

        Parameters
        ----------
        allowedSpeakers : list[SpeakerDevice or dict] or None
            List of speakers to test, or leave as None to test all speakers. If speakers are given 
            as a dict, SpeakerDevice objects will be created via DeviceManager. 
        threshold : float
            Necessary difference in volume (dB) between sound playing and not playing to conclude 
            that this mic can hear the given speaker.

        Returns
        -------
        list[SpeakerDevice]
            List of speakers which this MicrophoneDevice can hear
        """
        from psychopy import sound
        from psychopy.hardware import DeviceManager

        def _takeReading(dur):
            """
            Take a reading from this MicrophoneDevice and return the average volume.

            Parameters
            ----------
            dur : float
                Time (s) to read for

            Returns
            -------
            float
                Average volume across samples and channels during the reading
            """
            # countdown for the duration
            countdown = core.CountdownTimer(dur)
            # start recording
            self.start()
            # poll while active
            while countdown.getTime() > 0:
                self._pollWithLock()
            # get volume
            vol = self.getCurrentVolume(timeframe=dur)
            # if multi-channel, take the max
            try:
                vol = max(vol)
            except TypeError:
                pass
            # stop recording
            self.stop()

            return vol
        
        # if no allowed speakers given, use all
        if allowedSpeakers is None:
            allowedSpeakers = DeviceManager.getAvailableDevices(
                "psychopy.hardware.speaker.SpeakerDevice"
            )
        # list of found speakers
        foundSpeakers = []
        # iterate through allowed speakers
        for speaker in allowedSpeakers:
            # if given a dict, actualise it
            if isinstance(speaker, dict):
                speakerProfile = speaker
                speaker = DeviceManager.getDevice(speakerProfile['deviceName'])
                if speaker is None:
                    speaker = DeviceManager.addDevice(**speakerProfile)
            # generate a sound for this speaker
            try:
                snd = sound.Sound("A", stereo=True, speaker=speaker)
            except Exception:
                # silently skip on error
                continue
            # get a baseline volume
            baseline = _takeReading(1)
            # start playing a beep
            snd.play()
            # get an active volume
            active = _takeReading(1)
            # stop the beep
            snd.stop()
            # if the difference is above the threshold, speaker is good
            if active - baseline > threshold:
                foundSpeakers.append(speaker)
        
        return foundSpeakers
    

if __name__ == "__main__":
    pass
