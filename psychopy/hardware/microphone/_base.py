__all__ = [
    "PsychtoolboxMicrophoneDevice",
]

import sys
import time

import psychopy.logging as logging
from psychopy.preferences import prefs
from psychtoolbox import audio as audio
from psychopy import logging as logging, prefs, core
from psychopy.hardware.exceptions import DeviceNotConnectedError
from psychopy.localization import _translate
from psychopy.hardware import BaseDevice, BaseResponse
from psychopy.tools import systemtools as st
from psychopy.tools.audiotools import SAMPLE_RATE_48kHz

# set the audio backend from preferences
try:
    backend = prefs.hardware['audioDriver'][0]
except (KeyError, IndexError):
    logging.warning(
        "Audio library preference not found or empty, defaulting to 'sounddevice' for "
        "audio capture. To specify a different library, set the 'audioDriver' preference "
        "to a list with the desired library name as the first element."
    )
    backend = 'sounddevice'


class MicrophoneResponse(BaseResponse):
    pass


class BaseMicrophoneDevice(BaseDevice):
    """Base class for microphone devices. Not intended to be used directly.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._recording = None
        self._stream = None
        self._sampleRateHz = SAMPLE_RATE_48kHz

    def open(self):
        """Open the microphone device for recording. Must be called before recording can begin.
        """
        raise NotImplementedError("open() method must be implemented by subclass")
    
    def close(self):
        """Close the microphone device and release any resources. Should be called when finished
        with the device.
        """
        raise NotImplementedError("close() method must be implemented by subclass")
    
    def record(self):
        """Start recording audio from the microphone. The recording will continue until stop() is called.
        """
        raise NotImplementedError("record() method must be implemented by subclass")
    
    def stop(self, *args, **kwargs):
        """Stop recording audio from the microphone. After calling this method, the recorded audio can be
        retrieved using getRecording().
        """
        raise NotImplementedError("stop() method must be implemented by subclass")
    
    def getRecording(self):
        """Return the recorded audio data as a numpy array. This method should be called after stop() to
        retrieve the recorded audio.
        """
        raise NotImplementedError("getRecording() method must be implemented by subclass")
    
    def poll(self):
        """Poll the microphone device for new audio data. This method can be called periodically while
        recording to check for new audio data.
        """
        raise NotImplementedError("poll() method must be implemented by subclass")
    

if __name__ == "__main__":
    pass
