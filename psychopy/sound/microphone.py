#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Audio recording using a microphone.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['Microphone']

import psychopy.logging as logging
from psychopy.constants import NOT_STARTED
from psychopy.hardware import DeviceManager
from .audioclip import *
from .audiodevice import *
from .exceptions import *
import numpy as np

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


class RecordingBuffer:
    """Class for a storing a recording from a stream.

    Think of instances of this class behaving like an audio tape whereas the
    `MicrophoneDevice` class is the tape recorder. Samples taken from the stream are
    written to the tape which stores the data.

    Used internally by the `MicrophoneDevice` class, users usually do not create
    instances of this class themselves.

    Parameters
    ----------
    sampleRateHz : int
        Sampling rate for audio recording in Hertz (Hz). By default, 48kHz
        (``sampleRateHz=48000``) is used which is adequate for most consumer
        grade microphones (headsets and built-in).
    channels : int
        Number of channels to record samples to `1=Mono` and `2=Stereo`.
    maxRecordingSize : int
        Maximum recording size in kilobytes (Kb). Since audio recordings tend to
        consume a large amount of system memory, one might want to limit the
        size of the recording buffer to ensure that the application does not run
        out of memory. By default, the recording buffer is set to 24000 KB (or
        24 MB). At a sample rate of 48kHz, this will result in 62.5 seconds of
        continuous audio being recorded before the buffer is full.
    policyWhenFull : str
        What to do when the recording buffer is full and cannot accept any more
        samples. If 'ignore', samples will be silently dropped and the `isFull`
        property will be set to `True`. If 'warn', a warning will be logged and
        the `isFull` flag will be set. Finally, if 'error' the application will
        raise an exception.

    """
    def __init__(self, sampleRateHz=SAMPLE_RATE_48kHz, channels=2,
                 maxRecordingSize=24000, policyWhenFull='ignore'):
        self._channels = channels
        self._sampleRateHz = sampleRateHz
        self._maxRecordingSize = maxRecordingSize
        self._samples = None  # `ndarray` created in _allocRecBuffer`
        self._offset = 0  # recording offset
        self._lastSample = 0  # offset of the last sample from stream
        self._spaceRemaining = None  # set in `_allocRecBuffer`
        self._totalSamples = None  # set in `_allocRecBuffer`

        # check if the value is valid
        if policyWhenFull not in ['ignore', 'warn', 'error']:
            raise ValueError("Invalid value for `policyWhenFull`.")

        self._policyWhenFull = policyWhenFull
        self._warnedRecBufferFull = False
        self._loops = 0

        self._allocRecBuffer()

    def _allocRecBuffer(self):
        """Allocate the recording buffer. Called internally if properties are
        changed."""
        # allocate another array
        nBytes = self._maxRecordingSize * 1000
        recArraySize = int((nBytes / self._channels) / (np.float32()).itemsize)

        self._samples = np.zeros(
            (recArraySize, self._channels), dtype=np.float32, order='C')

        # sanity check
        assert self._samples.nbytes == nBytes
        self._totalSamples = len(self._samples)
        self._spaceRemaining = self._totalSamples

    @property
    def samples(self):
        """Reference to the actual sample buffer (`ndarray`)."""
        return self._samples

    @property
    def bufferSecs(self):
        """Capacity of the recording buffer in seconds (`float`)."""
        return self._totalSamples / self._sampleRateHz

    @property
    def nbytes(self):
        """Number of bytes the recording buffer occupies in memory (`int`)."""
        return self._samples.nbytes

    @property
    def sampleBytes(self):
        """Number of bytes per sample (`int`)."""
        return np.float32().itemsize

    @property
    def spaceRemaining(self):
        """The space remaining in the recording buffer (`int`). Indicates the
        number of samples that the buffer can still add before overflowing.
        """
        return self._spaceRemaining

    @property
    def isFull(self):
        """Is the recording buffer full (`bool`)."""
        return self._spaceRemaining <= 0

    @property
    def totalSamples(self):
        """Total number samples the recording buffer can hold (`int`)."""
        return self._totalSamples

    @property
    def writeOffset(self):
        """Index in the sample buffer where new samples will be written when
        `write()` is called (`int`).
        """
        return self._offset

    @property
    def lastSample(self):
        """Index of the last sample recorded (`int`). This can be used to slice
        the recording buffer, only getting data from the beginning to place
        where the last sample was written to.
        """
        return self._lastSample

    @property
    def loopCount(self):
        """Number of times the recording buffer restarted (`int`). Only valid if
        `loopback` is ``True``."""
        return self._loops

    @property
    def maxRecordingSize(self):
        """Maximum recording size in kilobytes (`int`).

        Since audio recordings tend to consume a large amount of system memory,
        one might want to limit the size of the recording buffer to ensure that
        the application does not run out of memory. By default, the recording
        buffer is set to 24000 KB (or 24 MB). At a sample rate of 48kHz, this
        will result in 62.5 seconds of continuous audio being recorded before
        the buffer is full.

        Setting this value will allocate another recording buffer of appropriate
        size. Avoid doing this in any time sensitive parts of your application.

        """
        return self._maxRecordingSize

    @maxRecordingSize.setter
    def maxRecordingSize(self, value):
        value = int(value)

        # don't do this unless the value changed
        if value == self._maxRecordingSize:
            return

        # if different than last value, update the recording buffer
        self._maxRecordingSize = value
        self._allocRecBuffer()

    def seek(self, offset, absolute=False):
        """Set the write offset.

        Use this to specify where to begin writing samples the next time `write`
        is called. You should call `seek(0)` when starting a new recording.

        Parameters
        ----------
        offset : int
            Position in the sample buffer to set.
        absolute : bool
            Use absolute positioning. Use relative positioning if `False` where
            the value of `offset` will be added to the current offset. Default
            is `False`.

        """
        if not absolute:
            self._offset += offset
        else:
            self._offset = absolute

        assert 0 <= self._offset < self._totalSamples
        self._spaceRemaining = self._totalSamples - self._offset

    def write(self, samples):
        """Write samples to the recording buffer.

        Parameters
        ----------
        samples : ArrayLike
            Samples to write to the recording buffer, usually of a stream. Must
            have the same number of dimensions as the internal array.

        Returns
        -------
        int
            Number of samples overflowed. If this is zero then all samples have
            been recorded, if not, the number of samples rejected is given.

        """
        nSamples = len(samples)
        if self.isFull:
            if self._policyWhenFull == 'ignore':
                return nSamples  # samples lost
            elif self._policyWhenFull == 'warn':
                if not self._warnedRecBufferFull:
                    logging.warning(
                        f"Audio recording buffer filled! This means that no "
                        f"samples are saved beyond {round(self.bufferSecs, 6)} "
                        f"seconds. Specify a larger recording buffer next time "
                        f"to avoid data loss.")
                    logging.flush()
                    self._warnedRecBufferFull = True
                return nSamples
            elif self._policyWhenFull == 'error':
                raise AudioRecordingBufferFullError(
                    "Cannot write samples, recording buffer is full.")
            else:
                return nSamples  # whatever

        if not nSamples:  # no samples came out of the stream, just return
            return

        if self._spaceRemaining >= nSamples:
            self._lastSample = self._offset + nSamples
            audioData = samples[:, :]
        else:
            self._lastSample = self._offset + self._spaceRemaining
            audioData = samples[:self._spaceRemaining, :]

        self._samples[self._offset:self._lastSample, :] = audioData
        self._offset += nSamples

        self._spaceRemaining -= nSamples

        # Check if the recording buffer is now full. Next call to `poll` will
        # not record anything.
        if self._spaceRemaining <= 0:
            self._spaceRemaining = 0

        d = nSamples - self._spaceRemaining
        return 0 if d < 0 else d

    def clear(self):
        # reset all live attributes
        self._samples = None
        self._offset = 0
        self._lastSample = 0
        self._spaceRemaining = None
        self._totalSamples = None
        # reallocate buffer
        self._allocRecBuffer()

    def getSegment(self, start=0, end=None):
        """Get a segment of recording data as an `AudioClip`.

        Parameters
        ----------
        start : float or int
            Absolute time in seconds for the start of the clip.
        end : float or int
            Absolute time in seconds for the end of the clip. If `None` the time
            at the last sample is used.

        Returns
        -------
        AudioClip
            Audio clip object with samples between `start` and `end`.

        """
        idxStart = int(start * self._sampleRateHz)
        idxEnd = self._lastSample if end is None else int(
            end * self._sampleRateHz)

        return AudioClip(
            np.array(self._samples[idxStart:idxEnd, :],
                     dtype=np.float32, order='C'),
            sampleRateHz=self._sampleRateHz)


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
                deviceClass="psychopy.sound.MicrophoneDevice", deviceName=device,
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
