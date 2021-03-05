#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for managing audio devices.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'AudioDevice',
    'sampleRateQualityLevels',
    'NULL_AUDIO_DEVICE',
    'SAMPLE_RATE_8kHz', 'SAMPLE_RATE_TELCOM_QUALITY',
    'SAMPLE_RATE_16kHz', 'SAMPLE_RATE_VOIP_QUALITY',
    'SAMPLE_RATE_44p1kHz', 'SAMPLE_RATE_CD_QUALITY',
    'SAMPLE_RATE_48kHz', 'SAMPLE_RATE_DVD_QUALITY',
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
    def createFromPTBDeviceDesc(desc):
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
        return self._outputChannels > 0 and self._inputChannels == 0

    @property
    def isCapture(self):
        """`True` if this is a capture device (`bool`)."""
        return not self.isPlayback


NULL_AUDIO_DEVICE = AudioDevice()  # used as a sentinel or for testing

if __name__ == "__main__":
    pass
