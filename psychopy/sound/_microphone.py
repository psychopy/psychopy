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
from ._audioclip import *
from ._audiodevice import *
from ._exceptions import *

_hasPTB = True
try:
    import psychtoolbox.audio as audio
except (ImportError, ModuleNotFoundError):
    logging.warning(
        "The 'psychtoolbox' library cannot be loaded but is required for audio "
        "capture. Microphone recording is unavailable this session. Note that "
        "opening a microphone stream will raise an error.")
    _hasPTB = False


class Microphone(object):
    """Class for recording audio from a microphone.

    Parameters
    ----------
    device : int or `~psychopy.sound.AudioDevice`
        Audio capture device to use. You may specify the device either by index
        (`int`) or descriptor (`AudioDevice`).
    sampleRateHz : int
        Sampling rate for audio recording in Hertz (Hz). By default, 48kHz
        (``sampleRateHz=480000``) is used which is adequate for most consumer
        grade microphones (headsets and built-in). Sampling rates should be at
        least greater than 20kHz to minimize distortion perceptible to humans
        due to aliasing.
    channels : int
        Number of channels to record samples to `1=Mono` and `2=Stereo`.

    Examples
    --------
    Capture 10 seconds of audio from the primary microphone::

        import psychopy.core as core
        import psychopy.sound.Microphone as Microphone

        mic = Microphone()  # open the microphone
        mic.start()  # start recording
        core.wait(10.0)  # wait 10 seconds
        audioClip = mic.getAudioClip()  # get the audio data
        mic.stop()  # stop recording

        print(audioClip.duration)  # should be ~10 seconds
        audioClip.save('test.wav')  # save the recorded audio as a 'wav' file

    """
    # Force the use of WASAPI for audio capture on Windows. If `True`, only
    # WASAPI devices will be returned when calling static method
    # `Microphone.getDevices()`
    enforceWASAPI = True

    def __init__(self,
                 device=None,
                 sampleRateHz=None,
                 channels=2,
                 recBufferSecs=10.0):

        if not _hasPTB:  # fail if PTB is not installed
            raise ModuleNotFoundError(
                "Microphone audio capture requires package `psychtoolbox` to "
                "be installed.")

        # get information about the selected device
        if isinstance(device, AudioDevice):
            self._device = device
        else:
            # get default device, first enumerated usually
            devices = Microphone.getDevices()

            if not devices:
                raise AudioInvalidCaptureDeviceError(
                    'No suitable audio recording devices found on this system. '
                    'Check connections and try again.')

            self._device = devices[0] if devices else None

        # error if specified device was not a microphone
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
        assert isinstance(recBufferSecs, (float, int))
        self._recBufferSecs = float(recBufferSecs)

        # PTB specific stuff
        self._mode = 2  # open a stream in capture mode

        # this can only be set after initialization
        self._stopTime = None   # optional, stop time to end recording

        # Handle for the recording stream, should only be opened once per
        # session
        self._stream = audio.Stream(
            device_id=self._device.deviceIndex,
            mode=self._mode,
            freq=self._sampleRateHz,
            channels=self._channels)

        # pre-allocate recording buffer
        self._stream.get_audio_data(self._recBufferSecs)

        # status flag
        self._statusFlag = NOT_STARTED

    # def setDevice(self, device=None):
    #     """Set the device and open a stream. Calling this will close the
    #     previous stream and create a new one. Do not call this while recording
    #     or if anything is trying to access the stream.
    #
    #     Parameters
    #     ----------
    #     device : AudioDevice or None
    #         Audio device to use. Must be an input device. If `None`, the first
    #         suitable input device to be enumerated is used.
    #
    #     """
    #     pass

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
            AudioDevice.createFromPTBDesc(dev) for dev in allDevs]
                     if desc.isCapture]

        return inputDevices

    @property
    def recordingBufferSecs(self):
        """Size of the internal audio storage buffer in seconds (`float`).
        Cannot be set while recording.

        """
        return self._recBufferSecs

    @property
    def status(self):
        """Status of the audio stream (`AudioDeviceStatus` or `None`).

        """
        currentStatus = self._stream.status
        if currentStatus != -1:
            return AudioDeviceStatus.createFromPTBDesc(currentStatus)

    def start(self, when=None, waitForStart=0, stopTime=None):
        """Start an audio recording.

        Calling this method will open a stream and begin capturing samples from
        the microphone.

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
        if self._statusFlag == STARTED:  # raise warning, error, or ignore?
            pass

        assert self._stream is not None  # must have a handle

        startTime = self._stream.start(
            repetitions=0,
            when=when,
            wait_for_start=int(waitForStart),
            stop_time=stopTime)

        self._statusFlag = STARTED  # recording has begun

        return startTime

    def stop(self):
        """Stop recording audio.

        Call this method to end an audio recording if in progress. This will
        close the audio stream.

        """
        self._stream.stop()
        self._statusFlag = NOT_STARTED

    def close(self):
        """Close the stream."""
        self._stream.close()

    def getAudioClip(self, clipName=None):
        """Get samples from a previous recording."""
        if self._statusFlag == NOT_STARTED:
            raise AudioStreamError(
                "Cannot get stream data while stream is closed.")

        # REM - write these other values to the clip header
        audioData, _, _, _ = self._stream.get_audio_data()

        return AudioClip(
            samples=audioData,
            sampleRateHz=self._sampleRateHz)


if __name__ == "__main__":
    pass
