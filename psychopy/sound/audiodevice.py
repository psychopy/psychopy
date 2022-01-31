#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for managing audio devices.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'AudioDeviceInfo',
    'AudioDeviceStatus',
    'NULL_AUDIO_DEVICE',
    'NULL_AUDIO_DEVICE_STATUS',
    'sampleRateQualityLevels',
    'latencyClassLevels',
    'runModeLevels',
    'SAMPLE_RATE_8kHz',
    'SAMPLE_RATE_TELCOM_QUALITY',
    'SAMPLE_RATE_16kHz',
    'SAMPLE_RATE_VOIP_QUALITY',
    'SAMPLE_RATE_VOICE_QUALITY',
    'SAMPLE_RATE_44p1kHz',
    'SAMPLE_RATE_CD_QUALITY',
    'SAMPLE_RATE_48kHz',
    'SAMPLE_RATE_DVD_QUALITY',
    'SAMPLE_RATE_96kHz',
    'SAMPLE_RATE_192kHz',
    'AUDIO_PTB_LATENCY_CLASS0',
    'AUDIO_PTB_LATENCY_CLASS1',
    'AUDIO_PTB_LATENCY_CLASS2',
    'AUDIO_PTB_LATENCY_CLASS3',
    'AUDIO_PTB_LATENCY_CLASS4',
    'AUDIO_PTB_LATENCY_CLASS_DONT_CARE',
    'AUDIO_PTB_LATENCY_CLASS_SHARE',
    'AUDIO_PTB_LATENCY_CLASS_EXCLUSIVE',
    'AUDIO_PTB_LATENCY_CLASS_AGGRESSIVE',
    'AUDIO_PTB_LATENCY_CLASS_CRITICAL',
    'AUDIO_PTB_RUN_MODE0',
    'AUDIO_PTB_RUN_MODE1',
    'AUDIO_PTB_RUN_MODE_STANDBY',
    'AUDIO_PTB_RUN_MODE_KEEP_HOT',
    'AUDIO_LIBRARY_PTB'
]

from psychopy.tools.audiotools import *

# audio library identifiers
AUDIO_LIBRARY_PTB = 'ptb'  # PsychPortAudio from Psychtoolbox

# Quality levels as strings and values. Used internally by the PsychoPy UI for
# dropdowns and preferences. Persons using PsychoPy as a library would typically
# use constants `SAMPLE_RATE_*` instead of looking up values in here.
#
# For voice recording applications, the recommended sample rate is `Voice`
# (16kHz) and should appear as the default option in preferences and UI
# dropdowns.
#
sampleRateQualityLevels = {
    0: (SAMPLE_RATE_8kHz, 'Telephone/Two-way radio (8kHz)'),
    1: (SAMPLE_RATE_16kHz, 'Voice (16kHz)'),  # <<< recommended for voice
    2: (SAMPLE_RATE_44p1kHz, 'CD Audio (44.1kHz)'),
    3: (SAMPLE_RATE_48kHz, 'DVD Audio (48kHz)'),  # <<< usually system default
    4: (SAMPLE_RATE_96kHz, 'High-Def (96kHz)'),
    5: (SAMPLE_RATE_192kHz, 'Ultra High-Def (192kHz)')
}

# Latency classes for the PsychPortAudio backend. These are used to set how
# aggressive PsychPortAudio should be at minimizing sound latency and getting
# precise timing. Exclusive mode `AUDIO_PTB_LATENCY_CLASS2` is usually used
# for the best timing and maximum compatibility.
#
AUDIO_PTB_LATENCY_CLASS0 = AUDIO_PTB_LATENCY_CLASS_DONT_CARE = 0
AUDIO_PTB_LATENCY_CLASS1 = AUDIO_PTB_LATENCY_CLASS_SHARE = 1
AUDIO_PTB_LATENCY_CLASS2 = AUDIO_PTB_LATENCY_CLASS_EXCLUSIVE = 2
AUDIO_PTB_LATENCY_CLASS3 = AUDIO_PTB_LATENCY_CLASS_AGGRESSIVE = 3
AUDIO_PTB_LATENCY_CLASS4 = AUDIO_PTB_LATENCY_CLASS_CRITICAL = 4

# used for GUI dropdowns
latencyClassLevels = {
    0: (AUDIO_PTB_LATENCY_CLASS0, 'Latency not important'),
    1: (AUDIO_PTB_LATENCY_CLASS1, 'Share low-latency driver'),
    2: (AUDIO_PTB_LATENCY_CLASS2, 'Exclusive low-latency'),  # <<< default
    3: (AUDIO_PTB_LATENCY_CLASS3, 'Aggressive low-latency'),
    4: (AUDIO_PTB_LATENCY_CLASS4, 'Latency critical'),
}

# Run modes for the PsychPortAudio backend.
AUDIO_PTB_RUN_MODE0 = AUDIO_PTB_RUN_MODE_STANDBY = 0
AUDIO_PTB_RUN_MODE1 = AUDIO_PTB_RUN_MODE_KEEP_HOT = 1

runModeLevels = {
    0: (AUDIO_PTB_RUN_MODE0, 'Standby (low resource use, higher latency)'),
    1: (AUDIO_PTB_RUN_MODE1, 'Keep hot (higher resource use, low latency)')
}


class AudioDeviceInfo:
    """Descriptor for an audio device (playback or recording) on this system.

    Properties associated with this class provide information about a specific
    audio playback or recording device. An object can be then passed to
    :class:`~psychopy.sound._microphone.Microphone` to open a stream using the
    device described by the object.

    This class is usually instanced only by calling
    :meth:`~psychopy.sound._microphone.Microphone.getDevices()`. Users should
    avoid creating instances of this class themselves unless they have good
    reason to.

    Parameters
    ----------
    deviceIndex : int
        Enumerated index of the audio device. This number is specific to the
        engine used for audio.
    deviceName : str
        Human-readable name of the device.
    hostAPIName : str
        Human-readable name of the host API used for audio.
    outputChannels : int
        Number of output channels.
    outputLatency : tuple
        Low (`float`) and high (`float`) output latency in milliseconds.
    inputChannels : int
        Number of input channels.
    inputLatency : tuple
        Low (`float`) and high (`float`) input latency in milliseconds.
    defaultSampleRate : int
        Default sample rate for the device in Hertz (Hz).
    audioLib : str
        Audio library that queried device information used to populate the
        properties of this descriptor (e.g., ``'ptb'`` for Psychtoolbox).

    Examples
    --------
    Get a list of available devices::

        import psychopy.sound as sound
        recordingDevicesList = sound.Microphone.getDevices()

    Get the low and high input latency of the first recording device::

        recordingDevice = recordingDevicesList[0]  # assume not empty
        inputLatencyLow, inputLatencyHigh = recordingDevice.inputLatency

    Get the device name as it may appear in the system control panel or sound
    settings::

        deviceName = recordingDevice.deviceName

    Specifying the device to use for capturing audio from a microphone::

        # get the first suitable capture device found by the sound engine
        recordingDevicesList = sound.Microphone.getDevices()
        recordingDevice = recordingDevicesList[0]

        # pass the descriptor to microphone to configure it
        mic = sound.Microphone(device=recordingDevice)
        mic.start()  # start recording sound

    """
    __slots__ = [
        '_deviceIndex',
        '_deviceName',
        '_hostAPIName',
        '_outputChannels',
        '_inputChannels',
        '_lowInputLatency',
        '_highInputLatency',
        '_lowOutputLatency',
        '_highOutputLatency',
        '_defaultSampleRate',
        '_audioLib'
    ]

    def __init__(self,
                 deviceIndex=-1,
                 deviceName=u'Null Device',
                 hostAPIName=u'Null Audio Driver',
                 outputChannels=0,
                 outputLatency=(0., 0.),
                 inputChannels=0,
                 inputLatency=(0., 0.),
                 defaultSampleRate=SAMPLE_RATE_48kHz,
                 audioLib=u''):

        # values based off Psychtoolbox audio device descriptors
        self.deviceIndex = deviceIndex
        self.deviceName = deviceName
        self.hostAPIName = hostAPIName
        self.outputChannels = outputChannels
        self.inputChannels = inputChannels
        self.inputLatency = inputLatency
        self.outputLatency = outputLatency
        self.defaultSampleRate = defaultSampleRate
        self.audioLib = audioLib

    def __repr__(self):
        return (f"AudioDeviceInfo(deviceIndex={self.deviceIndex}, "
                f"deviceName={self.deviceName}, "
                f"hostAPIName={self.hostAPIName}, "
                f"outputChannels={self.outputChannels}, "
                f"outputLatency={repr(self.outputLatency)}, "
                f"inputChannels={self.inputChannels}, "
                f"inputLatency={repr(self.inputLatency)}, "
                f"defaultSampleRate={self.defaultSampleRate}, "
                f"audioLib={repr(self.audioLib)})")

    @staticmethod
    def createFromPTBDesc(desc):
        """Create an `AudioDevice` instance with values populated using a
        descriptor (`dict`) returned from the PTB `audio.get_devices` API call.

        Parameters
        ----------
        desc : dict
            Audio device descriptor returned from Psychtoolbox's `get_devices`
            function.

        Returns
        -------
        AudioDeviceInfo
            Audio device descriptor with properties set using `desc`.

        """
        assert isinstance(desc, dict)

        # required fields, sanity check to see if something changed in PTB land
        reqFields = [
            'DeviceIndex', 'DeviceName', 'HostAudioAPIName', 'NrOutputChannels',
            'NrInputChannels', 'LowOutputLatency', 'HighOutputLatency',
            'LowInputLatency', 'HighInputLatency', 'DefaultSampleRate'
        ]

        assert all([field in desc.keys() for field in reqFields])

        audioDevDesc = AudioDeviceInfo(
            deviceIndex=desc['DeviceIndex'],
            deviceName=desc['DeviceName'],
            hostAPIName=desc['HostAudioAPIName'],
            outputChannels=desc['NrOutputChannels'],
            outputLatency=(desc['LowOutputLatency'], desc['HighOutputLatency']),
            inputChannels=desc['NrInputChannels'],
            inputLatency=(desc['LowInputLatency'], desc['HighInputLatency']),
            defaultSampleRate=desc['DefaultSampleRate'],
            audioLib=AUDIO_LIBRARY_PTB)  # queried with psychtoolbox

        return audioDevDesc

    @property
    def audioLib(self):
        """Audio library used to query device information (`str`)."""
        return self._audioLib

    @audioLib.setter
    def audioLib(self, value):
        self._audioLib = str(value)

    @property
    def inputChannels(self):
        """Number of input channels (`int`). If >0, this is likely a audio
        capture device.
        """
        return self._inputChannels

    @inputChannels.setter
    def inputChannels(self, value):
        self._inputChannels = int(value)

    @property
    def outputChannels(self):
        """Number of output channels (`int`). If >0, this is likely a audio
        playback device.
        """
        return self._outputChannels

    @outputChannels.setter
    def outputChannels(self, value):
        self._outputChannels = int(value)

    @property
    def deviceIndex(self):
        """Enumerated index (`int`) of the audio device."""
        return self._deviceIndex

    @deviceIndex.setter
    def deviceIndex(self, value):
        self._deviceIndex = int(value)

    @property
    def deviceName(self):
        """Human-readable name (`str`) for the audio device reported by the
        driver.
        """
        return self._deviceName

    @deviceName.setter
    def deviceName(self, value):
        self._deviceName = str(value)

    @property
    def hostAPIName(self):
        """Human-readable name (`str`) for the host API."""
        return self._hostAPIName

    @hostAPIName.setter
    def hostAPIName(self, value):
        self._hostAPIName = str(value)

    @property
    def outputLatency(self):
        """Low and high output latency in milliseconds `(low, high)`."""
        return self._lowOutputLatency, self._highOutputLatency

    @outputLatency.setter
    def outputLatency(self, value):
        assert len(value) == 2
        self._lowOutputLatency = float(value[0])
        self._highOutputLatency = float(value[1])

    @property
    def inputLatency(self):
        """Low and high input latency in milliseconds `(low, high)`."""
        return self._lowInputLatency, self._highInputLatency

    @inputLatency.setter
    def inputLatency(self, value):
        assert len(value) == 2
        self._lowInputLatency = float(value[0])
        self._highInputLatency = float(value[1])

    @property
    def defaultSampleRate(self):
        """Default sample rate in Hertz (Hz) for this device (`int`)."""
        return self._defaultSampleRate

    @defaultSampleRate.setter
    def defaultSampleRate(self, value):
        self._defaultSampleRate = int(value)

    @property
    def isPlayback(self):
        """`True` if this device is suitable for playback (`bool`)."""
        return self._outputChannels > 0

    @property
    def isCapture(self):
        """`True` if this device is suitable for capture (`bool`)."""
        return self._inputChannels > 0

    @property
    def isDuplex(self):
        """`True` if this device is suitable for capture and playback (`bool`).

        """
        return self.isPlayback and self.isCapture


class AudioDeviceStatus:
    """Descriptor for audio device status information.

    Properties of this class are standardized on the status information returned
    by Psychtoolbox. Other audio backends should try to populate these fields as
    best they can with their equivalent status values.

    Users should never instance this class themselves unless they have good
    reason to.

    Parameters
    ----------
    active : bool
        `True` if playback or recording has started, else `False`.
    state : int
        State of the device, either `1` for playback, `2` for recording or `3`
        for duplex (recording and playback).
    requestedStartTime : float
        Requested start time of the audio stream after the start of playback or
        recording.
    startTime : float
        The actual (real) start time of audio playback or recording.
    captureStartTime : float
        Estimate of the start time of audio capture. Only valid if audio capture
        is active. Usually, this time corresponds to the time when the first
        sound was captured.
    requestedStopTime : float
        Stop time requested when starting the stream.
    estimatedStopTime : float
        Estimated stop time given `requestedStopTime`.
    currentStreamTime : float
        Estimate of the time it will take for the most recently submitted sample
        to reach the speaker. Value is in absolute system time and reported for
        playback only.
    elapsedOutSamples : int
        Total number of samples submitted since the start of playback.
    positionSecs : float
        Current stream playback position in seconds this loop. Does not account
        for hardware of driver latency.
    recordedSecs : float
        Total amount of recorded sound data (in seconds) since start of capture.
    readSecs : float
        Total amount of sound data in seconds that has been fetched from the
        internal buffer.
    schedulePosition : float
        Current position in a running schedule in seconds.
    xRuns : int
        Number of dropouts due to buffer over- and under-runs. Such conditions
        can result is glitches during playback/recording. Even if the number
        remains zero, that does not mean that glitches did not occur.
    totalCalls : int
        **Debug** - Used for debugging the audio engine.
    timeFailed : float
        **Debug** - Used for debugging the audio engine.
    bufferSize : int
        **Debug** - Size of the buffer allocated to contain stream samples. Used
        for debugging the audio engine.
    cpuLoad : float
        Amount of load on the CPU imparted by the sound engine. Ranges between
        0.0 and 1.0 where 1.0 indicates maximum load on the core running the
        sound engine process.
    predictedLatency : float
        Latency for the given hardware and driver. This indicates how far ahead
        you need to start the device to ensure is starts at a scheduled time.
    latencyBias : float
        Additional latency bias added by the user.
    sampleRate : int
        Sample rate in Hertz (Hz) the playback recording is using.
    outDeviceIndex : int
        Enumerated index of the output device.
    inDeviceIndex : int
        Enumerated index of the input device.
    audioLib : str
        Identifier for the audio library which created this status.

    """
    __slots__ = [
        '_active',
        '_state',
        '_requestedStartTime',
        '_startTime',
        '_captureStartTime',
        '_requestedStopTime',
        '_estimatedStopTime',
        '_currentStreamTime',
        '_elapsedOutSamples',
        '_positionSecs',
        '_recordedSecs',
        '_readSecs',
        '_schedulePosition',
        '_xRuns',
        '_totalCalls',
        '_timeFailed',
        '_bufferSize',
        '_cpuLoad',
        '_predictedLatency',
        '_latencyBias',
        '_sampleRate',
        '_outDeviceIndex',
        '_inDeviceIndex',
        '_audioLib'
    ]

    def __init__(self,
                 active=0,
                 state=0,
                 requestedStartTime=0.0,
                 startTime=0.0,
                 captureStartTime=0.0,
                 requestedStopTime=0.0,
                 estimatedStopTime=0.0,
                 currentStreamTime=0.0,
                 elapsedOutSamples=0,
                 positionSecs=0.0,
                 recordedSecs=0.0,
                 readSecs=0.0,
                 schedulePosition=0.0,
                 xRuns=0,
                 totalCalls=0,
                 timeFailed=0,
                 bufferSize=0,
                 cpuLoad=0.0,
                 predictedLatency=0.0,
                 latencyBias=0.0,
                 sampleRate=SAMPLE_RATE_48kHz,
                 outDeviceIndex=0,
                 inDeviceIndex=0,
                 audioLib=u'Null Audio Library'):

        self.active = active
        self.state = state
        self.requestedStartTime = requestedStartTime
        self.startTime = startTime
        self.captureStartTime = captureStartTime
        self.requestedStopTime = requestedStopTime
        self.estimatedStopTime = estimatedStopTime
        self.currentStreamTime = currentStreamTime
        self.elapsedOutSamples = elapsedOutSamples
        self.positionSecs = positionSecs
        self.recordedSecs = recordedSecs
        self.readSecs = readSecs
        self.schedulePosition = schedulePosition
        self.xRuns = xRuns
        self.totalCalls = totalCalls
        self.timeFailed = timeFailed
        self.bufferSize = bufferSize
        self.cpuLoad = cpuLoad
        self.predictedLatency = predictedLatency
        self.latencyBias = latencyBias
        self.sampleRate = sampleRate
        self.outDeviceIndex = outDeviceIndex
        self.inDeviceIndex = inDeviceIndex
        self.audioLib = audioLib

    def __repr__(self):
        return (f"AudioDeviceStatus(active={self.active}, "
                f"state={self.state}, "
                f"requestedStartTime={self.requestedStartTime}, "
                f"startTime={self.startTime}, "
                f"captureStartTime={self.captureStartTime}, "
                f"requestedStopTime={self.requestedStopTime}, "
                f"estimatedStopTime={self.estimatedStopTime}, "
                f"currentStreamTime={self.currentStreamTime}, "
                f"elapsedOutSamples={self.elapsedOutSamples}, "
                f"positionSecs={self.positionSecs}, "
                f"recordedSecs={self.recordedSecs}, "
                f"readSecs={self.readSecs}, "
                f"schedulePosition={self.schedulePosition}, "
                f"xRuns={self.xRuns}, "
                f"totalCalls={self.totalCalls}, "
                f"timeFailed={self.timeFailed}, "
                f"bufferSize={self.bufferSize}, "
                f"cpuLoad={self.cpuLoad}, "
                f"predictedLatency={self.predictedLatency}, "
                f"latencyBias={self.latencyBias}, "
                f"sampleRate={self.sampleRate}, "
                f"outDeviceIndex={self.outDeviceIndex}, "
                f"inDeviceIndex={self.inDeviceIndex}, "
                f"audioLib={repr(self.audioLib)})")

    @staticmethod
    def createFromPTBDesc(desc):
        """Create an `AudioDeviceStatus` instance using a status descriptor
        returned by Psychtoolbox.

        Parameters
        ----------
        desc : dict
            Audio device status descriptor.

        Returns
        -------
        AudioDeviceStatus
            Audio device descriptor with properties set using `desc`.

        """
        audioStatusDesc = AudioDeviceStatus(
            active=desc['Active'],
            state=desc['State'],
            requestedStartTime=desc['RequestedStartTime'],
            startTime=desc['StartTime'],
            captureStartTime=desc['CaptureStartTime'],
            requestedStopTime=desc['RequestedStopTime'],
            estimatedStopTime=desc['EstimatedStopTime'],
            currentStreamTime=desc['CurrentStreamTime'],
            elapsedOutSamples=desc['ElapsedOutSamples'],
            positionSecs=desc['PositionSecs'],
            recordedSecs=desc['RecordedSecs'],
            readSecs=desc['ReadSecs'],
            schedulePosition=desc['SchedulePosition'],
            xRuns=desc['XRuns'],
            totalCalls=desc['TotalCalls'],
            timeFailed=desc['TimeFailed'],
            bufferSize=desc['BufferSize'],
            cpuLoad=desc['CPULoad'],
            predictedLatency=desc['PredictedLatency'],
            latencyBias=desc['LatencyBias'],
            sampleRate=desc['SampleRate'],
            outDeviceIndex=desc['OutDeviceIndex'],
            inDeviceIndex=desc['InDeviceIndex'],
            audioLib='ptb')

        return audioStatusDesc

    @property
    def audioLib(self):
        """Identifier for the audio library which created this status (`str`).
        """
        return self._audioLib

    @audioLib.setter
    def audioLib(self, value):
        self._audioLib = str(value)

    @property
    def active(self):
        """`True` if playback or recording has started (`bool`).

        """
        return self._active

    @active.setter
    def active(self, value):
        self._active = bool(value)

    @property
    def state(self):
        """State of the device (`int`). Either `1` for playback, `2` for
        recording or `3` for duplex (recording and playback).

        """
        return self._state

    @state.setter
    def state(self, value):
        self._state = int(value)

    @property
    def isPlayback(self):
        """`True` if this device is operating in playback mode (`bool`)."""
        return self._state == 1 or self._state == 3

    @property
    def isCapture(self):
        """`True` if this device is operating in capture mode (`bool`)."""
        return self._state == 2 or self._state == 3

    @property
    def isDuplex(self):
        """`True` if this device is operating capture and recording mode
        (`bool`).

        """
        return self._state == 3

    @property
    def requestedStartTime(self):
        """Requested start time of the audio stream after the start of playback
        or recording (`float`).

        """
        return self._requestedStartTime

    @requestedStartTime.setter
    def requestedStartTime(self, value):
        self._requestedStartTime = float(value)

    @property
    def startTime(self):
        """The actual (real) start time of audio playback or recording
        (`float`).

        """
        return self._startTime

    @startTime.setter
    def startTime(self, value):
        self._startTime = float(value)

    @property
    def captureStartTime(self):
        """Estimate of the start time of audio capture (`float`). Only valid if
        audio capture is active. Usually, this time corresponds to the time when
        the first sound was captured.

        """
        return self._startTime

    @captureStartTime.setter
    def captureStartTime(self, value):
        self._captureStartTime = float(value)

    @property
    def requestedStopTime(self):
        """Stop time requested when starting the stream (`float`)."""
        return self._requestedStopTime

    @requestedStopTime.setter
    def requestedStopTime(self, value):
        self._requestedStopTime = float(value)

    @property
    def estimatedStopTime(self):
        """Estimated stop time given `requestedStopTime` (`float`)."""
        return self._requestedStopTime

    @estimatedStopTime.setter
    def estimatedStopTime(self, value):
        self._estimatedStopTime = float(value)

    @property
    def currentStreamTime(self):
        """Estimate of the time it will take for the most recently submitted
        sample to reach the speaker (`float`). Value is in absolute system time
        and reported for playback mode only.

        """
        return self._currentStreamTime

    @currentStreamTime.setter
    def currentStreamTime(self, value):
        self._currentStreamTime = float(value)

    @property
    def elapsedOutSamples(self):
        """Total number of samples submitted since the start of playback
        (`int`).

        """
        return self._elapsedOutSamples

    @elapsedOutSamples.setter
    def elapsedOutSamples(self, value):
        self._elapsedOutSamples = int(value)

    @property
    def positionSecs(self):
        """Current stream playback position in seconds this loop (`float`). Does
        not account for hardware of driver latency.

        """
        return self._positionSecs

    @positionSecs.setter
    def positionSecs(self, value):
        self._positionSecs = float(value)

    @property
    def recordedSecs(self):
        """Total amount of recorded sound data (in seconds) since start of
        capture (`float`).

        """
        return self._recordedSecs

    @recordedSecs.setter
    def recordedSecs(self, value):
        self._recordedSecs = float(value)

    @property
    def readSecs(self):
        """Total amount of sound data in seconds that has been fetched from the
        internal buffer (`float`).

        """
        return self._readSecs

    @readSecs.setter
    def readSecs(self, value):
        self._readSecs = float(value)

    @property
    def schedulePosition(self):
        """Current position in a running schedule in seconds (`float`)."""
        return self._schedulePosition

    @schedulePosition.setter
    def schedulePosition(self, value):
        self._schedulePosition = float(value)

    @property
    def xRuns(self):
        """Number of dropouts due to buffer over- and under-runs (`int`). Such
        conditions can result is glitches during playback/recording. Even if the
        number remains zero, that does not mean that glitches did not occur.

        """
        return self._xRuns

    @xRuns.setter
    def xRuns(self, value):
        self._xRuns = int(value)

    @property
    def totalCalls(self):
        """**Debug** - Used for debugging the audio engine (`int`)."""
        return self._xRuns

    @totalCalls.setter
    def totalCalls(self, value):
        self._xRuns = int(value)

    @property
    def timeFailed(self):
        """**Debug** - Used for debugging the audio engine (`float`)."""
        return self._timeFailed

    @timeFailed.setter
    def timeFailed(self, value):
        self._timeFailed = float(value)

    @property
    def bufferSize(self):
        """**Debug** - Size of the buffer allocated to contain stream samples.
        Used for debugging the audio engine.

        """
        return self._bufferSize

    @bufferSize.setter
    def bufferSize(self, value):
        self._bufferSize = int(value)

    @property
    def cpuLoad(self):
        """Amount of load on the CPU imparted by the sound engine (`float`).
        Ranges between 0.0 and 1.0 where 1.0 indicates maximum load on the core
        running the sound engine process.

        """
        return self._cpuLoad

    @cpuLoad.setter
    def cpuLoad(self, value):
        self._cpuLoad = float(value)

    @property
    def predictedLatency(self):
        """Latency for the given hardware and driver (`float`). This indicates
        how far ahead you need to start the device to ensure is starts at a
        scheduled time.

        """
        return self._predictedLatency

    @predictedLatency.setter
    def predictedLatency(self, value):
        self._predictedLatency = float(value)

    @property
    def latencyBias(self):
        """Additional latency bias added by the user (`float`)."""
        return self._latencyBias

    @latencyBias.setter
    def latencyBias(self, value):
        self._latencyBias = float(value)

    @property
    def sampleRate(self):
        """Sample rate in Hertz (Hz) the playback recording is using (`int`)."""
        return self._sampleRate

    @sampleRate.setter
    def sampleRate(self, value):
        self._sampleRate = int(value)

    @property
    def outDeviceIndex(self):
        """Enumerated index of the output device (`int`)."""
        return self._outDeviceIndex

    @outDeviceIndex.setter
    def outDeviceIndex(self, value):
        self._outDeviceIndex = int(value)

    @property
    def inDeviceIndex(self):
        """Enumerated index of the input device (`int`)."""
        return self._inDeviceIndex

    @inDeviceIndex.setter
    def inDeviceIndex(self, value):
        self._inDeviceIndex = int(value)


# These are used as sentinels or for testing. Instancing these here behaves as
# a self-test, providing coverage to most of the setter methods when this module
# is imported.
#
NULL_AUDIO_DEVICE = AudioDeviceInfo()
NULL_AUDIO_DEVICE_STATUS = AudioDeviceStatus()

if __name__ == "__main__":
    pass
