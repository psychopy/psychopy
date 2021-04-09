#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Audio recording using a microphone.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['Microphone']

import sys
import psychopy.logging as logging
from psychopy.constants import NOT_STARTED, STARTED
from psychopy.preferences import prefs
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
        "capture. Microphone recording is unavailable this session. Note that "
        "opening a microphone stream will raise an error.")
    _hasPTB = False


class RecordingBuffer(object):
    """Class for a storing a recording from a stream.

    Think of instances of this class behaving like an audio tape whereas the
    `Microphone` class is the tape recorder. Samples taken from the stream are
    written to the tape which stores the data.

    Used internally by the `Microphone` class, users usually do not create
    instances of this class themselves.

    Parameters
    ----------
    sampleRateHz : int
        Sampling rate for audio recording in Hertz (Hz). By default, 48kHz
        (``sampleRateHz=480000``) is used which is adequate for most consumer
        grade microphones (headsets and built-in).
    channels : int
        Number of channels to record samples to `1=Mono` and `2=Stereo`.
    maxRecordingSize : int
        Maximum size of the recording in kilobytes. This specifies how much
        memory is available to store samples.
    loopback : bool
        Allow for continuous recording. Usually if the recording buffer is full
        no more samples can be saved to the buffer. If `loopback=True`, samples
        wil be written to the beginning of the track once there is no more
        space. Default is `False`.

    """
    def __init__(self, sampleRateHz=SAMPLE_RATE_48kHz, channels=2,
                 maxRecordingSize=24000, loopback=True,
                 policyWhenFull='ignore'):
        self._channels = channels
        self._sampleRateHz = sampleRateHz
        self._maxRecordingSize = maxRecordingSize
        self._samples = None  # `ndarray` created in _allocRecBuffer`
        self._offset = 0  # recording offset
        self._lastSample = 0  # offset of the last sample from stream
        self._spaceRemaining = None  # set in `_allocRecBuffer`
        self._totalSamples = None  # set in `_allocRecBuffer`

        self._loopback = loopback
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
        the application does not run out. By default, the recording buffer is
        set to 64000 KB (or 64 MB). At a sample rate of 48kHz, this will result
        in about. Using stereo audio (``nChannels == 2``) requires twice the
        buffer over mono (``nChannels == 2``) for the same length clip.

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


class Microphone(object):
    """Class for recording audio from a microphone or input stream.

    Creating an instance of this class will open a stream using the specified
    device. Streams should remain open for the duration of your session. When a
    stream is opened, a buffer is allocated to store samples coming off it.
    Samples from the input stream will written to the buffer once
    :meth:`~Microphone.start()` is called.

    Parameters
    ----------
    device : int or `~psychopy.sound.AudioDevice`
        Audio capture device to use. You may specify the device either by index
        (`int`) or descriptor (`AudioDevice`).
    sampleRateHz : int
        Sampling rate for audio recording in Hertz (Hz). By default, 48kHz
        (``sampleRateHz=480000``) is used which is adequate for most consumer
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
    warmUp : bool
        Warm-up the stream after opening it. This helps prevent additional
        latency the first time `start` is called on some systems.

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
                 device=None,
                 sampleRateHz=None,
                 channels=2,
                 streamBufferSecs=2.0,
                 maxRecordingSize=24000,
                 warmUp=True):

        if not _hasPTB:  # fail if PTB is not installed
            raise ModuleNotFoundError(
                "Microphone audio capture requires package `psychtoolbox` to "
                "be installed.")

        # get information about the selected device
        devices = Microphone.getDevices()
        if isinstance(device, AudioDeviceInfo):
            self._device = device
        elif isinstance(device, (int, float)):
            devicesByIndex = {d.deviceIndex: d for d in devices}
            if device in devicesByIndex:
                self._device = devicesByIndex[device]
            else:
                raise AudioInvalidCaptureDeviceError(
                    'No suitable audio recording devices found matching index '
                    '{}.'.format(device))
        else:
            # get default device, first enumerated usually
            if not devices:
                raise AudioInvalidCaptureDeviceError(
                    'No suitable audio recording devices found on this system. '
                    'Check connections and try again.')

            self._device = devices[0]  # use first

        # error if specified device is not suitable for capture
        if not self._device.isCapture:
            raise AudioInvalidCaptureDeviceError(
                'Specified audio device not suitable for audio recording. '
                'Has no input channels.')

        # get the sample rate
        self._sampleRateHz = \
            self._device.defaultSampleRate if sampleRateHz is None else int(
                sampleRateHz)

        # set the number of recording channels
        self._channels = \
            self._device.inputChannels if channels is None else int(channels)

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
        self._stream = audio.Stream(
            device_id=self._device.deviceIndex,
            latency_class=prefs.hardware["audioLatencyMode"],
            mode=self._mode,
            freq=self._sampleRateHz,
            channels=self._channels)

        # set latency bias
        self._stream.latency_bias = 0.0

        # pre-allocate recording buffer, called once
        self._stream.get_audio_data(self._streamBufferSecs)

        # status flag
        self._statusFlag = NOT_STARTED

        # setup recording buffer
        self._recording = RecordingBuffer(
            sampleRateHz=self._sampleRateHz,
            channels=self._channels,
            maxRecordingSize=maxRecordingSize)

        # do the warm-up
        if warmUp:
            self.warmUp()

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
        # query PTB for devices
        if Microphone.enforceWASAPI and sys.platform == 'win32':
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

    def warmUp(self):
        """Warm-/wake-up the audio stream.

        On some systems the first time `start` is called incurs additional
        latency, whereas successive calls do not. To deal with this, it is
        recommended that you run this warm-up routine prior to capturing audio
        samples. By default, this routine is called when instancing a new
        microphone object.

        """
        # We should put an actual test here to see if timing stabilizes after
        # multiple invocations of this function.
        self._stream.start()
        self._stream.stop()

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
    def streamBufferSecs(self):
        """Size of the internal audio storage buffer in seconds (`float`).

        To ensure all data is captured, there must be less time elapsed between
        subsequent `getAudioClip` calls than `bufferSecs`.

        """
        return self._streamBufferSecs

    @property
    def status(self):
        """Status flag for the microphone. Value can be one of
        ``psychopy.constants.STARTED`` or ``psychopy.constants.NOT_STARTED``.

        For detailed stream status information, use the
        :attr:`~psychopy.sound.microphone.Microphone.streamStatus` property.

        """
        if hasattr(self, "_statusFlag"):
            return self._statusFlag

    @status.setter
    def status(self, value):
        self._statusFlag = value

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
        return self.status == STARTED

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
            raise AudioStreamError(
                "Cannot start a stream, already started.")

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
        self._statusFlag = STARTED

        return startTime

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
        tuple
            Tuple containing `startTime`, `endPositionSecs`, `xruns` and
            `estStopTime`.

        """
        if not self.isStarted:
            raise AudioStreamError(
                "Cannot stop a stream that has not been started.")

        # poll remaining samples, if any
        if not self.isRecBufferFull:
            self.poll()

        startTime, endPositionSecs, xruns, estStopTime = self._stream.stop(
            block_until_stopped=int(blockUntilStopped),
            stopTime=stopTime)
        self._statusFlag = NOT_STARTED

        return startTime, endPositionSecs, xruns, estStopTime

    def close(self):
        """Close the stream.

        Should not be called until you are certain you're done with it. Ideally,
        you should never close and reopen the same stream within a single
        session.

        """
        self._stream.close()

    def poll(self):
        """Poll audio samples.

        Calling this method adds audio samples collected from the stream buffer
        to the recording buffer that have been captured since the last `poll`
        call. Time between calls of this function should be less than
        `bufferSecs`. You do not need to call this if you call `stop` before
        the time specified by `bufferSecs` elapses since the `start` call.

        Can only be called between called of `start` and `stop` (i.e.
        ``Microphone.status == STARTED``.

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

        Returns
        -------
        AudioClip
            Recorded data between the last calls to

        """
        if self.isStarted:
            raise AudioStreamError(
                "Cannot get audio clip, recording was in progress. Be sure to "
                "call `Microphone.stop` first.")

        return self._recording.getSegment()  # full recording


if __name__ == "__main__":
    pass
