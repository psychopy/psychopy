import sys
import time

from psychtoolbox import audio as audio

from psychopy import logging as logging, prefs
from psychopy.constants import NOT_STARTED
from psychopy.hardware import BaseDevice
from psychopy.sound import AudioDeviceInfo, AudioDeviceStatus, AudioClip
from psychopy.sound.exceptions import AudioInvalidCaptureDeviceError, AudioInvalidDeviceError, \
    AudioStreamError
from psychopy.sound.microphone import _hasPTB, RecordingBuffer
from psychopy.tools import systemtools as st


class MicrophoneDevice(BaseDevice, aliases=["mic", "microphone"]):
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
        continuous audio being recorded before the buffer is full.
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

    Examples
    --------
    Capture 10 seconds of audio from the primary microphone::

        import psychopy.core as core
        import psychopy.sound.Microphone as Microphone

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

    def __init__(self,
                 index=None,
                 sampleRateHz=None,
                 channels=None,
                 streamBufferSecs=2.0,
                 maxRecordingSize=24000,
                 policyWhenFull='warn',
                 audioLatencyMode=None,
                 audioRunMode=0):

        if not _hasPTB:  # fail if PTB is not installed
            raise ModuleNotFoundError(
                "Microphone audio capture requires package `psychtoolbox` to "
                "be installed.")

        def _getDeviceByIndex(deviceIndex):
            """Subroutine to get a device by index. Used to handle the case
            where the user specifies a device by index.

            Parameters
            ----------
            deviceIndex : int, float or str
                Index of the device to get.

            Returns
            -------
            AudioDeviceInfo
                Audio device information object.

            """
            # convert to `int` first, sometimes strings can specify the enum
            # value from builder
            deviceIndex = int(deviceIndex)
            # get all audio devices
            devices_ = MicrophoneDevice.getDevices()

            # get information about the selected device
            devicesByIndex = {d.deviceIndex: d for d in devices_}
            if deviceIndex in devicesByIndex:
                useDevice = devicesByIndex[deviceIndex]
            else:
                raise AudioInvalidCaptureDeviceError(
                    'No suitable audio recording devices found matching index '
                    '{}.'.format(deviceIndex))

            return useDevice

        # get information about the selected device
        if isinstance(index, AudioDeviceInfo):
            self._device = index
        elif isinstance(index, (int, float, str)):
            self._device = _getDeviceByIndex(index)
        else:
            # get default device, first enumerated usually
            devices = MicrophoneDevice.getDevices()
            if not devices:
                raise AudioInvalidCaptureDeviceError(
                    'No suitable audio recording devices found on this system. '
                    'Check connections and try again.')

            self._device = devices[0]  # use first

        logging.info('Using audio device #{} ({}) for audio capture'.format(
            self._device.deviceIndex, self._device.deviceName))

        # error if specified device is not suitable for capture
        if not self._device.isCapture:
            raise AudioInvalidCaptureDeviceError(
                'Specified audio device not suitable for audio recording. '
                'Has no input channels.')

        # get the sample rate
        self._sampleRateHz = \
            self._device.defaultSampleRate if sampleRateHz is None else int(
                sampleRateHz)

        logging.debug('Set stream sample rate to {} Hz'.format(
            self._sampleRateHz))

        # set the audio latency mode
        if audioLatencyMode is None:
            self._audioLatencyMode = int(prefs.hardware["audioLatencyMode"])
        else:
            self._audioLatencyMode = audioLatencyMode

        logging.debug('Set audio latency mode to {}'.format(
            self._audioLatencyMode))

        assert 0 <= self._audioLatencyMode <= 4  # sanity check for pref

        # set the number of recording channels
        self._channels = \
            self._device.inputChannels if channels is None else int(channels)

        logging.debug('Set recording channels to {} ({})'.format(
            self._channels, 'stereo' if self._channels > 1 else 'mono'))

        if self._channels > self._device.inputChannels:
            raise AudioInvalidDeviceError(
                'Invalid number of channels for audio input specified.')

        # internal recording buffer size in seconds
        assert isinstance(streamBufferSecs, (float, int))
        self._streamBufferSecs = float(streamBufferSecs)

        # PTB specific stuff
        self._mode = 2  # open a stream in capture mode

        # Handle for the recording stream, should only be opened once per
        # session
        logging.debug('Opening audio stream for device #{}'.format(
            self._device.deviceIndex))

        self._stream = audio.Stream(
            device_id=self._device.deviceIndex,
            latency_class=self._audioLatencyMode,
            mode=self._mode,
            freq=self._sampleRateHz,
            channels=self._channels)

        logging.debug('Stream opened')

        assert isinstance(audioRunMode, (float, int)) and \
               (audioRunMode == 0 or audioRunMode == 1)
        self._audioRunMode = int(audioRunMode)
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

        # status flag for Builder
        self._statusFlag = NOT_STARTED

        # setup recording buffer
        self._recording = RecordingBuffer(
            sampleRateHz=self._sampleRateHz,
            channels=self._channels,
            maxRecordingSize=maxRecordingSize,
            policyWhenFull=policyWhenFull
        )

        self._isStarted = False  # internal state

        logging.debug('Audio capture device #{} ready'.format(
            self._device.deviceIndex))

    def isSameDevice(self, params):
        return params['device'] == self._device

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
            MicrophoneDevice.enforceWASAPI = bool(prefs.hardware["audioForceWASAPI"])
        except KeyError:
            pass  # use default if option not present in settings

        # query PTB for devices
        if MicrophoneDevice.enforceWASAPI and sys.platform == 'win32':
            allDevs = audio.get_devices(device_type=13)
        else:
            allDevs = audio.get_devices()

        # make sure we have an array of descriptors
        allDevs = [allDevs] if isinstance(allDevs, dict) else allDevs

        # create list of descriptors only for capture devices
        inputDevices = [desc for desc in [
            AudioDeviceInfo.createFromPTBDesc(dev) for dev in allDevs]
                     if desc.isCapture]

        return inputDevices

    @staticmethod
    def getAvailableDevices():
        devices = []
        for profile in st.getAudioCaptureDevices():
            device = {
                'deviceName': profile.get('device_name', "Unknown Microphone"),
                'index': profile.get('index', None),
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
    def recording(self):
        """Reference to the current recording buffer (`RecordingBuffer`)."""
        return self._recording

    @property
    def recBufferSecs(self):
        """Capacity of the recording buffer in seconds (`float`)."""
        return self.recording.bufferSecs

    @property
    def maxRecordingSize(self):
        """Maximum recording size in kilobytes (`int`).

        Since audio recordings tend to consume a large amount of system memory,
        one might want to limit the size of the recording buffer to ensure that
        the application does not run out. By default, the recording buffer is
        set to 64000 KB (or 64 MB). At a sample rate of 48kHz, this will result
        in about. Using stereo audio (``nChannels == 2``) requires twice the
        buffer over mono (``nChannels == 2``) for the same length clip.

        Setting this value will allocate another recording buffer of appropriate
        size. Avoid doing this in any time sensitive parts of your application.

        """
        return self._recording.maxRecordingSize

    @maxRecordingSize.setter
    def maxRecordingSize(self, value):
        self._recording.maxRecordingSize = value

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
        return self._recording.isFull

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
            self.poll()
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
        # check if the stream has been
        if self.isStarted:
            return None

        if self._stream is None:
            raise AudioStreamError("Stream not ready.")

        # reset the writing 'head'
        self._recording.seek(0, absolute=True)

        # reset warnings
        # self._warnedRecBufferFull = False

        startTime = self._stream.start(
            repetitions=0,
            when=when,
            wait_for_start=int(waitForStart),
            stop_time=stopTime)

        # recording has begun or is scheduled to do so
        self._isStarted = True

        logging.debug(
            'Scheduled start of audio capture for device #{} at t={}.'.format(
                self._device.deviceIndex, startTime))

        return startTime

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
        if not self.isStarted:
            return

        # poll remaining samples, if any
        if not self.isRecBufferFull:
            self.poll()

        startTime, endPositionSecs, xruns, estStopTime = self._stream.stop(
            block_until_stopped=int(blockUntilStopped),
            stopTime=stopTime)
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
        return self.stop(blockUntilStopped=blockUntilStopped, stopTime=stopTime)

    def close(self):
        """Close the stream.

        Should not be called until you are certain you're done with it. Ideally,
        you should never close and reopen the same stream within a single
        session.

        """
        self._stream.close()
        logging.debug('Stream closed')

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
        int
            Number of overruns in sampling.

        """
        if not self.isStarted:
            raise AudioStreamError(
                "Cannot poll samples from audio device, not started.")

        # figure out what to do with this other information
        audioData, absRecPosition, overflow, cStartTime = \
            self._stream.get_audio_data()

        if overflow:
            logging.warning(
                "Audio stream buffer overflow, some audio samples have been "
                "lost! To prevent this, ensure `Microphone.poll()` is being "
                "called often enough, or increase the size of the audio buffer "
                "with `bufferSecs`.")

        overruns = self._recording.write(audioData)

        return overruns

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
            raise AudioStreamError(
                "Cannot get audio clip, recording was in progress. Be sure to "
                "call `Microphone.stop` first.")

        return self._recording.getSegment()  # full recording