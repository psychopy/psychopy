#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Audio recording using a microphone.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['Microphone']

from psychopy.constants import NOT_STARTED
from psychopy.hardware import DeviceManager
from psychopy.hardware.microphone import MicrophoneDevice



class Microphone:
    def __init__(
            self,
            device=None,
            sampleRateHz=None,
            channels=None,
            streamBufferSecs=2.0,
            maxRecordingSize=24000,
            policyWhenFull='warn',
            audioLatencyMode=None,
            audioRunMode=0):
        # look for device if initialised
        self.device = DeviceManager.getDevice(device)
        # if no matching name, try matching index
        if self.device is None:
            self.device = DeviceManager.getDeviceBy("index", device)
        # if still no match, make a new device
        if self.device is None:
            self.device = DeviceManager.addDevice(
                deviceClass="psychopy.hardware.microphone.MicrophoneDevice", deviceName=device,
                index=device,
                sampleRateHz=sampleRateHz,
                channels=channels,
                streamBufferSecs=streamBufferSecs,
                maxRecordingSize=maxRecordingSize,
                policyWhenFull=policyWhenFull,
                audioLatencyMode=audioLatencyMode,
                audioRunMode=audioRunMode
            )
        # setup clips and transcripts dicts
        self.clips = {}
        self.lastClip = None
        self.scripts = {}
        self.lastScript = None
        # set initial status
        self.status = NOT_STARTED

    @property
    def recording(self):
        return self.device.recording

    @property
    def recBufferSecs(self):
        return self.device.recBufferSecs

    @property
    def maxRecordingSize(self):
        return self.device.maxRecordingSize

    @maxRecordingSize.setter
    def maxRecordingSize(self, value):
        self.device.maxRecordingSize = value

    @property
    def latencyBias(self):
        return self.device.latencyBias

    @latencyBias.setter
    def latencyBias(self, value):
        self.device.latency_bias = value

    @property
    def audioLatencyMode(self):
        return self.device.audioLatencyMode

    @property
    def streamBufferSecs(self):
        return self.device.streamBufferSecs

    @property
    def streamStatus(self):
        return self.device.streamStatus

    @property
    def isRecBufferFull(self):
        return self.device.isRecBufferFull

    @property
    def isStarted(self):
        return self.device.isStarted

    @property
    def isRecording(self):
        return self.device.isRecording

    def start(self, when=None, waitForStart=0, stopTime=None):
        return self.device.start(
            when=when, waitForStart=waitForStart, stopTime=stopTime
        )

    def record(self, when=None, waitForStart=0, stopTime=None):
        return self.start(
            when=when, waitForStart=waitForStart, stopTime=stopTime
        )

    def stop(self, blockUntilStopped=True, stopTime=None):
        return self.device.stop(
            blockUntilStopped=blockUntilStopped, stopTime=stopTime
        )

    def pause(self, blockUntilStopped=True, stopTime=None):
        return self.stop(
            blockUntilStopped=blockUntilStopped, stopTime=stopTime
        )

    def close(self):
        return self.device.close()

    def poll(self):
        return self.device.poll()

    def bank(self, tag=None, transcribe=False, **kwargs):
        """Store current buffer as a clip within the microphone object.

        This method is used internally by the Microphone component in Builder,
        don't use it for other applications. Either `stop()` or `pause()` must
        be called before calling this method.

        Parameters
        ----------
        tag : str or None
            Label for the clip.
        transcribe : bool or str
            Set to the name of a transcription engine (e.g. "GOOGLE") to
            transcribe using that engine, or set as `False` to not transcribe.
        kwargs : dict
            Additional keyword arguments to pass to
            :class:`~psychopy.sound.AudioClip.transcribe()`.

        """
        # make sure the tag exists in both clips and transcripts dicts
        if tag not in self.clips:
            self.clips[tag] = []

        if tag not in self.scripts:
            self.scripts[tag] = []

        # append current recording to clip list according to tag
        self.lastClip = self.getRecording()
        self.clips[tag].append(self.lastClip)

        # synonymise null values
        nullVals = (
            'undefined', 'NONE', 'None', 'none', 'False', 'false', 'FALSE')
        if transcribe in nullVals:
            transcribe = False

        # append current clip's transcription according to tag
        if transcribe:
            if transcribe in ('Built-in', True, 'BUILT_IN', 'BUILT-IN',
                              'Built-In', 'built-in'):
                engine = "sphinx"
            elif type(transcribe) == str:
                engine = transcribe
            else:
                raise ValueError(
                    "Invalid transcription engine {} specified.".format(
                        transcribe))

            self.lastScript = self.lastClip.transcribe(
                engine=engine, **kwargs)
        else:
            self.lastScript = "Transcription disabled."

        self.scripts[tag].append(self.lastScript)

        # clear recording buffer
        self.device._recording.clear()

        # return banked items
        if transcribe:
            return self.lastClip, self.lastScript
        else:
            return self.lastClip

    def clear(self):
        """Wipe all clips. Deletes previously banked audio clips.
        """
        # clear clips
        self.clips = {}
        # clear recording
        self._recording.clear()

    def flush(self):
        """Get a copy of all banked clips, then clear the clips from storage."""
        # get copy of clips dict
        clips = self.clips.copy()
        self.clear()

        return clips

    def getRecording(self):
        return self.device.getRecording()


if __name__ == "__main__":
    pass
