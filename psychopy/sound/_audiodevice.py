#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for managing audio devices.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'AudioDevice',
    'AudioDeviceStatus',
    'sampleRateQualityLevels',
    'NULL_AUDIO_DEVICE',
    'NULL_AUDIO_DEVICE_STATUS',
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
    'SAMPLE_RATE_192kHz'
]

from psychopy.tools.audiotools import *

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
    1: (SAMPLE_RATE_16kHz, 'Voice (16kHz)'),  # <<< recommended
    2: (SAMPLE_RATE_44p1kHz, 'CD Audio (44.1kHz)'),
    3: (SAMPLE_RATE_48kHz, 'DVD Audio (48kHz)'),
    4: (SAMPLE_RATE_96kHz, 'High-Def (96kHz)'),
    5: (SAMPLE_RATE_192kHz, 'Ultra High-Def (192kHz)')
}


class AudioDevice(object):
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
        Enumerated index of the audio device.
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
        AudioDevice
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

        audioDevDesc = AudioDevice(
            deviceIndex=desc['DeviceIndex'],
            deviceName=desc['DeviceName'],
            hostAPIName=desc['HostAudioAPIName'],
            outputChannels=desc['NrOutputChannels'],
            outputLatency=(desc['LowOutputLatency'], desc['HighOutputLatency']),
            inputChannels=desc['NrInputChannels'],
            inputLatency=(desc['LowInputLatency'], desc['HighInputLatency']),
            defaultSampleRate=desc['DefaultSampleRate'],
            audioLib='ptb')  # queried with psychtoolbox

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
        """Default sample rate (`int`) for this device."""
        return self._defaultSampleRate

    @defaultSampleRate.setter
    def defaultSampleRate(self, value):
        self._defaultSampleRate = int(value)

    @property
    def isPlayback(self):
        """`True` if this is a capture device (`bool`)."""
        return self._outputChannels > 0

    @property
    def isCapture(self):
        """`True` if this is a capture device (`bool`)."""
        return self._inputChannels > 0

    @property
    def isDuplex(self):
        """`True` if this is a capture and playback device (`bool`)."""
        return self.isPlayback and self.isCapture


class AudioDeviceStatus(object):
    """Descriptor for audio device status information.

    Properties of this class are standardized on the structure of the returned
    `dict` when calling PsychPortAudio with `GetStatus`. Other audio backends
    should try to populate these fields as best they can.

    Users should never instance this class themselves unless they have good
    reason to.

    Parameters
    ----------
    active
    state
    requestedStartTime
    startTime
    captureStartTime
    requestedStopTime
    estimatedStopTime
    currentStopTime
    elapsedOutSamples
    positionSecs
    recordedSecs
    readSecs
    schedulePosition
    xRuns
    totalCalls
    timeFailed
    bufferSize
    cpuLoad
    predictedLatency
    latencyBias
    sampleRate
    outDeviceIndex
    inDeviceIndex
    audioLib

    """
    __slots__ = [
        '_active',
        '_state',
        '_requestedStartTime',
        '_startTime',
        '_captureStartTime',
        '_requestedStopTime',
        '_estimatedStopTime',
        '_currentStopTime',
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
                 currentStopTime=0.0,
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
                 audioLib=u''):

        self.active = active
        self.state = state
        self.requestedStartTime = requestedStartTime
        self.startTime = startTime
        self.captureStartTime = captureStartTime
        self.requestedStopTime = requestedStopTime
        self.estimatedStopTime = estimatedStopTime
        self.currentStopTime = currentStopTime
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
            currentStopTime=desc['CurrentStreamTime'],
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
    def active(self):
        """`True` if this device is active."""
        return self._active

    @active.setter
    def active(self, value):
        self._active = bool(value)

    @property
    def state(self):
        """Current state of the device (`int`)."""
        return self._state

    @state.setter
    def state(self, value):
        self._state = bool(value)

    @property
    def requestedStartTime(self):
        """Start time requested by the user (`float`)."""
        return self._requestedStartTime

    @requestedStartTime.setter
    def requestedStartTime(self, value):
        self._requestedStartTime = float(value)

    @property
    def startTime(self):
        """(`float`)."""
        return self._startTime

    @startTime.setter
    def startTime(self, value):
        self._startTime = float(value)

    @property
    def captureStartTime(self):
        """(`float`)."""
        return self._startTime

    @captureStartTime.setter
    def captureStartTime(self, value):
        self._captureStartTime = float(value)

    @property
    def requestedStopTime(self):
        """(`float`)."""
        return self._requestedStopTime

    @requestedStopTime.setter
    def requestedStopTime(self, value):
        self._requestedStopTime = float(value)

    @property
    def estimatedStopTime(self):
        """(`float`)."""
        return self._requestedStopTime

    @estimatedStopTime.setter
    def estimatedStopTime(self, value):
        self._estimatedStopTime = float(value)

    @property
    def currentStopTime(self):
        """(`float`)."""
        return self._currentStopTime

    @currentStopTime.setter
    def currentStopTime(self, value):
        self._currentStopTime = float(value)

    @property
    def elapsedOutSamples(self):
        """(`int`)."""
        return self._elapsedOutSamples

    @elapsedOutSamples.setter
    def elapsedOutSamples(self, value):
        self._elapsedOutSamples = int(value)

    @property
    def positionSecs(self):
        """(`float`)."""
        return self._positionSecs

    @positionSecs.setter
    def positionSecs(self, value):
        self._positionSecs = float(value)

    @property
    def positionSecs(self):
        """(`float`)."""
        return self._positionSecs

    @positionSecs.setter
    def positionSecs(self, value):
        self._positionSecs = float(value)

    @property
    def recordedSecs(self):
        """(`float`)."""
        return self._recordedSecs

    @recordedSecs.setter
    def recordedSecs(self, value):
        self._recordedSecs = float(value)

    @property
    def readSecs(self):
        """(`float`)."""
        return self._readSecs

    @readSecs.setter
    def readSecs(self, value):
        self._readSecs = float(value)

    @property
    def schedulePosition(self):
        """(`float`)."""
        return self._schedulePosition

    @schedulePosition.setter
    def schedulePosition(self, value):
        self._schedulePosition = float(value)

    @property
    def schedulePosition(self):
        """(`float`)."""
        return self._schedulePosition

    @schedulePosition.setter
    def schedulePosition(self, value):
        self._schedulePosition = float(value)

    @property
    def xRuns(self):
        """(`int`)."""
        return self._xRuns

    @xRuns.setter
    def xRuns(self, value):
        self._xRuns = int(value)

    @property
    def totalCalls(self):
        """(`int`)."""
        return self._xRuns

    @totalCalls.setter
    def totalCalls(self, value):
        self._xRuns = int(value)

    @property
    def timeFailed(self):
        """(`float`)."""
        return self._timeFailed

    @timeFailed.setter
    def timeFailed(self, value):
        self._timeFailed = float(value)

    @property
    def bufferSize(self):
        """(`int`)."""
        return self._bufferSize

    @bufferSize.setter
    def bufferSize(self, value):
        self._bufferSize = int(value)

    @property
    def cpuLoad(self):
        """(`float`)."""
        return self._cpuLoad

    @cpuLoad.setter
    def cpuLoad(self, value):
        self._cpuLoad = float(value)

    @property
    def predictedLatency(self):
        """(`float`)."""
        return self._predictedLatency

    @predictedLatency.setter
    def predictedLatency(self, value):
        self._predictedLatency = float(value)

    @property
    def latencyBias(self):
        """(`float`)."""
        return self._latencyBias

    @latencyBias.setter
    def latencyBias(self, value):
        self._latencyBias = float(value)

    @property
    def sampleRate(self):
        """(`int`)."""
        return self._sampleRate

    @sampleRate.setter
    def sampleRate(self, value):
        self._sampleRate = int(value)

    @property
    def outDeviceIndex(self):
        """(`int`)."""
        return self._outDeviceIndex

    @outDeviceIndex.setter
    def outDeviceIndex(self, value):
        self._outDeviceIndex = int(value)

    @property
    def inDeviceIndex(self):
        """(`int`)."""
        return self._inDeviceIndex

    @inDeviceIndex.setter
    def inDeviceIndex(self, value):
        self._inDeviceIndex = int(value)

    @property
    def audioLib(self):
        """(`str`)."""
        return self._audioLib

    @audioLib.setter
    def audioLib(self, value):
        self._audioLib = str(value)


# Theses are used as sentinels or for testing. Instancing these here behaves as
# a self-test, providing coverage to most of the setter methods.
#
NULL_AUDIO_DEVICE = AudioDevice()
NULL_AUDIO_DEVICE_STATUS = AudioDeviceStatus()


if __name__ == "__main__":
    pass
