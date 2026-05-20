# -*- coding: utf-8 -*-

"""SoundDevice interface for microphones.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    "SoundDeviceMicrophoneDevice",
]

import sys
import time
from ._base import BaseMicrophoneDevice
import numpy as np
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
import atexit
import re

    
class SoundDeviceMicrophoneDevice(BaseMicrophoneDevice, aliases=["mic", "microphone"]):
    """Microphone device class for the SoundDevice audio library.

    This class is used internally by `MicrophoneDevice` when the SoundDevice
    audio library is selected. Users usually do not create instances of this
    class themselves.

    """
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
            # legacy
            audioLatencyMode=None
        ):
        super().__init__()
        
        try:
            import sounddevice  # load and check
        except ImportError:
             raise ModuleNotFoundError(
                "Microphone audio capture requires package `sounddevice` to "
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
            _devices = SoundDeviceMicrophoneDevice.getDevices()
            # if there are none, error
            if not len(_devices):
                raise DeviceNotConnectedError(
                    _translate(
                        "Could not choose default recording device as no recording "
                        "devices are connected."
                    ), 
                    deviceClass=SoundDeviceMicrophoneDevice
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
            if isinstance(device, SoundDeviceMicrophoneDevice):
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

        # open stream
        self._stream = None
        self._opening = self._closing = False
        self._recording = False
        self._tRecordingStartRequested = -1
        self._recordingBuffer = []  # list of samples
        self._nRecordedFrames = 0
        self._streamReady = False  # True when the mic is actually getting data

        self._microphones = []  # microphone objects bound to this device stream

        # window for timing the recording to start
        self.win = None

    def __hash__(self):
        # hash based on device index and name (which should be unique identifiers for the physical device)
        return hash((self._device.deviceIndex, self._device.deviceName))
    
    @property
    def sampleRateHz(self):
        """The sample rate of the audio stream in Hz. This is determined by the
        device and cannot be changed by the user.

        Returns
        -------
        float
            Sample rate of the audio stream in Hz.

        """
        return self._sampleRateHz

    def _callback(self, indata, frames, timedat, status):
        """Callback function for the sounddevice stream. This is called whenever
        new audio data is available from the stream.

        Parameters
        ----------
        indata : ndarray
            The recorded audio data.
        frames : int
            The number of frames in `indata`.
        timedat : CData
            Timing information about the callback.
        status : CallbackFlags
            Status of the callback.

        """
        if self._closing or self._opening:
            # if we're in the middle of opening or closing, ignore any callbacks as they may be unstable
            return
        
        timeAtADC = timedat.inputBufferAdcTime

        if status:
            logging.warning(f"SoundDevice stream callback returned with status: {status}")

        if len(indata) and self._clients:
            # compute the absulute time of the end of the current recording pos
            absBlockStartTime = timeAtADC
            absBlockEndTime = timeAtADC + (frames / self._sampleRateHz)
            
            # iterate over attached microphone objects and write data to their 
            # recording buffers if we're past the requested start time
            for mic in self._clients:
                reqStartTime = mic._tRecordingStartRequested
                reqStopTime = mic._tRecordingStopRequested
                if reqStartTime < absBlockEndTime and (
                        reqStopTime is None or absBlockStartTime < reqStopTime):
                    mic._recordingBuffer.append(indata.copy())
                    mic._nRecordedFrames += frames

    def open(self):
        """Open the stream for this microphone device.
        """
        if self._stream is not None and self._stream.active:
            logging.warning(
                "Attempted to open microphone stream which is already open."
            )
            return
        
        try:
            import sounddevice as sd
        except (ModuleNotFoundError, ImportError):
            msg = (
                "Failed to open microphone stream because the 'sounddevice' library is "
                "not installed."
            )
            logging.error(msg)
            raise DeviceNotConnectedError(
                _translate(msg),
                deviceClass=SoundDeviceMicrophoneDevice) from None

        # open a stream for this device
        try:
            self._stream = sd.InputStream(
                samplerate=self._sampleRateHz,
                channels=self._channels,
                device=self._device.deviceIndex,
                latency=self._audioLatencyMode,
                callback=self._callback,
                blocksize=0,  # use default blocksize
                dtype='float32',  # use 32-bit float for recording
            )
        except Exception as e:
            logging.error(f"Error occurred while opening microphone stream: {e}")
            raise AudioStreamError(
                "An error occurred while opening the microphone stream. See logs for details."
            ) from e

        self._stream.start()

    def close(self):
        """Close the stream for this microphone device.
        """
        # if we have microphones attached to this stream, don't close it until 
        # all microphones have been removed
        if self._clients:
            return 

        if self._stream is None or not self._stream.active:
            logging.warning(
                "Attempted to close microphone stream which is already closed."
            )
            return

        try:
            self._stream.stop()
            self._stream.close()
        except Exception as e:
            logging.error(f"Error occurred while closing microphone stream: {e}")
            raise AudioStreamError(
                "An error occurred while closing the microphone stream. See logs for details."
            ) from e
    
    def _getSegment(self, startTime, endTime):
        """Get a segment of the recorded audio data between `startTime` and `endTime`.

        Parameters
        ----------
        startTime : float
            Start time of the segment in seconds from the start of recording.
        endTime : float
            End time of the segment in seconds from the start of recording.

        Returns
        -------
        ndarray
            The audio data for the specified segment, with shape (n_samples, n_channels).

        """
        if not self._recordingBuffer:
            return np.empty((0, self._channels), dtype=np.float32)

        # concatenate all recorded blocks into a single array
        self._recordingBuffer = [np.concatenate(self._recordingBuffer, axis=0)]

        # calculate sample indices for the requested time range
        startSample = int(startTime * self._sampleRateHz)
        endSample = int(endTime * self._sampleRateHz)

        # clip to available data
        startSample = max(0, min(startSample, self._nRecordedFrames))
        endSample = max(0, min(endSample, self._nRecordedFrames))

        return self._recordingBuffer[0][startSample:endSample]

    def getRecording(self):
        """Get the recorded audio data as a numpy array.

        Returns
        -------
        ndarray
            The recorded audio data, with shape (n_samples, n_channels).

        """
        return self._getSegment(0, self._nRecordedFrames / self._sampleRateHz)

    def _getTime(self):
        """Get current time from the same timebase as the stream.
        
        Returns
        -------
        float
            Current time in seconds from the same timebase as the stream.
        
        """
        return time.monotonic()  # sounddevice uses monotonic timebase for its callbacks
    
    def record(self, when=None, waitForStart=0, stopTime=None):
        pass

    def start(self, when=None, waitForStart=0, stopTime=None):
        """Start recording from the microphone. Alias for `record()`.
        """
        self.record(when=when, waitForStart=waitForStart, stopTime=stopTime)
    
    def stop(self, *args, **kwargs):
        """Stop recording from the microphone.
        """
        self._tRecordingStartRequested = -1
        self._recording = False

    def pause(self):
        """Pause recording from the microphone. Can be resumed with `record()`."""
        pass

    @staticmethod
    def queryDevices():
        """Query devices using device manager.
        
        Returns
        -------
        list of dict 
            List of available microphone devices where configurations are given as
            dicts in a format similar to PTB.

        """
        """Query speaker devices using sounddevice.

        Returns
        -------
        list of dicts
            Device information.

        """
        try:
            import sounddevice as sd
        except (ModuleNotFoundError, ImportError):
            msg = (
                "Failed to query audio output devices because the 'sounddevice' library is "
                "not installed."
            )
            logging.error(msg)
            raise DeviceNotConnectedError(
                _translate(msg),
                deviceClass=SoundDeviceMicrophoneDevice)

        devices = []
        for dev in sd.query_devices():
            # skip input-only devices (microphones)
            if dev['max_input_channels'] == 0:
                continue

            # build a dict with the same keys as psychtoolbox for consistency
            devDict = {
                'DeviceIndex': dev['index'],
                'HostAudioAPIId': dev['hostapi'],
                'HostAudioAPIName': sd.query_hostapis(dev['hostapi'])['name'],
                'DeviceName': dev['name'],
                'NrInputChannels': dev['max_input_channels'],
                'NrOutputChannels': dev['max_output_channels'],
                'LowInputLatency': dev['default_low_input_latency'],
                'HighInputLatency': dev['default_high_input_latency'],
                'LowOutputLatency': dev['default_low_output_latency'],
                'HighOutputLatency': dev['default_high_output_latency'], 
                'DefaultSampleRate': dev['default_samplerate']
            }
            devices.append(devDict)

        return devices

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
                deviceClass=SoundDeviceMicrophoneDevice
            )

        return chosenDevice

    def isSameDevice(self, other):
        """
        Determine whether this object represents the same physical microphone as a given other
        object.

        Parameters
        ----------
        other : SoundDeviceMicrophoneDevice, dict
            Other SoundDeviceMicrophoneDevice to compare against, or a dict of params (which must 
            include `index` as a key)

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
        allDevs = SoundDeviceMicrophoneDevice.queryDevices()

        # make sure we have an array of descriptors
        allDevs = [allDevs] if isinstance(allDevs, dict) else allDevs

        # create list of descriptors only for capture devices
        devObjs = [AudioDeviceInfo.createFromPTBDesc(dev) for dev in allDevs]
        inputDevices = [desc for desc in devObjs if desc.isCapture]

        return inputDevices

    @staticmethod
    def getAvailableDevices():
        """Get available microphone devices using sounddevice.
        
        Returns
        -------
        list of dict
            List of available microphone devices where configurations are given as
            dicts in a format similar to PTB.

        """
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
    

if __name__ == "__main__":
    pass

