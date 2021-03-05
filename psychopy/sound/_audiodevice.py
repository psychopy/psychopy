#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for managing audio devices.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['AudioDevice']

from psychopy.tools.audiotools import SAMPLE_RATE_48kHz


class AudioDevice(object):
    """Descriptor for an audio device (playback or recording) on this system.

    Properties associated with this class provide information about a specific
    audio playback or recording device.

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
        '_defaultSampleRate'
    ]

    def __init__(self,
                 deviceIndex=-1,
                 deviceName=u'',
                 hostAPIName=u'',
                 outputChannels=0,
                 outputLatency=(0., 0.),
                 inputChannels=0,
                 inputLatency=(0., 0.),
                 defaultSampleRate=SAMPLE_RATE_48kHz):

        # values based off Psychtoolbox audio device descriptors
        self._deviceIndex = int(deviceIndex)
        self._deviceName = str(deviceName)
        self._hostAPIName = str(hostAPIName)
        self._outputChannels = int(outputChannels)
        self._inputChannels = int(inputChannels)
        self._lowInputLatency = float(inputLatency[0])
        self._highInputLatency = float(inputLatency[1])
        self._lowOutputLatency = float(outputLatency[0])
        self._highOutputLatency = float(outputLatency[1])
        self._defaultSampleRate = int(defaultSampleRate)

    @staticmethod
    def createFromPTBDeviceDesc(desc):
        """Create an `AudioDevice` instance with values populated using a
        descriptor (`dict`) returned from the PTB `get_devices` API call.

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
            defaultSampleRate=desc['DefaultSampleRate'])

        return audioDevDesc

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


if __name__ == "__main__":
    pass
