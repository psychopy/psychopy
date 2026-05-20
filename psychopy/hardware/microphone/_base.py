# -*- coding: utf-8 -*-

"""Device interfaces for physical microphone devices.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    "MicrophoneResponse",
    "BaseMicrophoneDevice",
]

import psychopy.logging as logging
from psychopy.preferences import prefs
from psychtoolbox import audio as audio
from psychopy import logging as logging, prefs, core
from psychopy.hardware.exceptions import DeviceNotConnectedError
from psychopy.localization import _translate
from psychopy.hardware import BaseDevice, BaseResponse, BaseResponseDevice
from psychopy.sound.audiodevice import AudioDeviceInfo, AudioDeviceStatus
from psychopy.tools import systemtools as st
from psychopy.tools.audiotools import SAMPLE_RATE_48kHz

# set the audio backend from preferences
try:
    backend = prefs.hardware['audioLib'][0]
except (KeyError, IndexError):
    logging.warning(
        "Audio library preference not found or empty, defaulting to 'sounddevice' for "
        "audio capture. To specify a different library, set the 'audioLib' preference "
        "to a list with the desired library name as the first element."
    )
    backend = 'sounddevice'


class MicrophoneResponse(BaseResponse):
    """Base class for microphone responses, used by listeners attached to MicrophoneDevice 
    instances.
    """
    pass


class BaseMicrophoneDevice(BaseDevice):
    """Base class for microphone devices.

    This class opens a stream to a physical microphone device and passes the data to 
    clients of type `psychopy.sound.Microphone`. Whether samples are passed to clients 
    is determined by the requested start time of each client; if the current time of 
    the stream is before the requested start time of a client, samples will not be passed 
    to that client.

    """
    # other instances of MicrophoneDevice, stored by index
    _streams = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._recording = None
        self._stream = None
        self._isStarted = False

        # settings for the mic interface
        self._sampleRateHz = kwargs.get('sampleRateHz', SAMPLE_RATE_48kHz) 
        self._channels = kwargs.get('channels', 1)

        # sampling settings
        self._pollingInterval = kwargs.get('pollingInterval', 0.1)
        self._absStreamStartTime = -1.0  # absolute time the stream was started

        # Real-time buffer for storing the latest audio samples from the stream. This is
        # used for computing various properties of the incoming audio, e.g. current volume 
        # level. This updates every time the stream is polled for new audio data, and is 
        # cleared when the stream is closed.
        self._rtBuffer = []  

        # List of Microphone objects attached to this device stream. If present, the stream will
        # remain open until all attached Microphone objects have been removed. When samples
        # are recorded, they will be written to the recording buffer of each attached Microphone
        # object according to the requested start time of each Microphone.
        self._clients = []

        # listeners for liason
        self.listeners = []
    
    # --- device management methods ---

    def addListener(self, listener, startLoop=False):
        """
        Add a listener, which will receive all the same messages as this device.

        Parameters
        ----------
        listener : str or psychopy.hardware.listener.BaseListener
            Either a Listener object, or use one of the following strings to create one:
            - "liaison": Create a LiaisonListener with DeviceManager.liaison as the server
            - "print": Create a PrintListener with default settings
            - "log": Create a LoggingListener with default settings
        startLoop : bool
            If True, then upon adding the listener, start up an asynchronous loop to 
            dispatch messages.

        """
        # add listener as normal
        listener = BaseResponseDevice.addListener(
            self, listener, startLoop=startLoop)

        # if we're starting a listener loop, start recording
        if startLoop:
            self.start()
        
        return listener

    def clearListeners(self):
        """
        Remove any listeners from this device.

        Returns
        -------
        bool
            True if completed successfully
        """
        # clear listeners as normal
        resp = BaseResponseDevice.clearListeners(self)

        # stop recording
        self.stop()

        return resp

    def dispatchMessages(self, clear=True):
        """
        Dispatch current volume as a MicrophoneResponse object to any attached listeners.

        Parameters
        ----------
        clear : bool
            If True, will clear the recording up until now after dispatching the volume. This is
            useful if you're just sampling volume and aren't wanting to store the recording.
        """
        # if mic is not recording, there's nothing to dispatch
        if not self.isStarted:
            return
        
        # poll the mic now
        self.poll()
        # create a response object
        message = MicrophoneResponse(
            logging.defaultClock.getTime(),
            self.getCurrentVolume(),
            device=self,
        )
        # dispatch to listeners
        for listener in self.listeners:
            listener.receiveMessage(message)
        
        return message

    # --- methods for managing the microphone stream ---

    @property
    def isOpen(self):
        """Whether the microphone stream is currently open (`bool`).
        """
        return self._stream is not None

    @property
    def isStarted(self):
        """Whether the microphone stream is currently started and taking samples (`bool`).
        """
        return self._isStarted

    def open(self):
        """Open the microphone device for recording.

        This intializes a stream to the physical microphone device and prepares it 
        for recording. The stream will remain open until `close()` is called, or 
        until all attached Microphone clients have been removed.

        """
        raise NotImplementedError("open() method must be implemented by subclass")
    
    def close(self):
        """Close the microphone device and release any resources.
        """
        raise NotImplementedError("close() method must be implemented by subclass")

    def start(self, *args, **kwargs):
        """Start the taking samples from the microphone. Alias of `open()`.
        """
        try:
            self.open()
        except NotImplementedError:
            NotImplementedError(
                'Called start() on a MicrophoneDevice subclass that does not ' \
                'implement open().')
    
    def stop(self, *args, **kwargs):
        """Stop recording audio from the microphone. Alias of `close()`.
        """
        try:
            self.close()
        except NotImplementedError:
            NotImplementedError(
                'Called stop() on a MicrophoneDevice subclass that does not '
                'implement close().')
    
    def poll(self):
        """Poll the microphone device for new audio data.

        This method should be called at regular intervals while the microphone stream 
        is open in order to process incoming audio data and pass it to attached
        Microphone clients. Be aware that not all backends require polling to be done
        manually.

        """
        raise NotImplementedError("poll() method must be implemented by subclass")
    
    # --- methods for managing attached Microphone clients ---

    @property
    def clients(self):
        """Microphone objects presently attached to this device stream (`list`).
        
        If present, the stream will remain open until all attached Microphone objects 
        have been removed.

        """
        return self._clients
    
    @property
    def clientCount(self):
        """The number of Microphone objects presently attached to this device 
        stream (`int`).
        """
        return len(self._clients)
    
    @property
    def canClose(self):
        """Whether the stream can be closed, i.e. whether there are any attached 
        Microphone clients that are currently using this stream.
        """
        return self.clientCount == 0

    def bind(self, mic):
        """Bind a Microphone object to this device stream.

        If an object of type `psychopy.sound.Microphone` is bound to this stream, 
        audio data will be written to the recording buffer of that object according 
        to the requested start time.

        Parameters
        ----------
        mic : `psychopy.sound.Microphone`
            The microphone object to bind.

        """
        # check if the microphone is already attached
        for m in self._clients:
            if m is mic:
                logging.warning(
                    "Attempted to bind a Microphone object to a stream that " \
                    "it is already bound to."
                )
                return
            
        self._clients.append(mic)

    def unbind(self, mic):
        """Unbind a Microphone object from this device stream.

        Parameters
        ----------
        mic : `psychopy.sound.Microphone`
            The microphone object to unbind.

        """
        # probably better to use `set()` here, maybe later we can do that
        for i, m in enumerate(self._clients):
            if m is mic:
                del self._clients[i]
                return
        
        logging.warning(
            "Attempted to unbind a Microphone object from a stream that " \
            "it is not bound to."
        )

    def unbindAll(self):
        """Unbind all Microphone objects from this device stream.
        """
        self._clients.clear()

    # --- utility methods ---

    def getTime(self):
        """Get the current time of the microphone stream in seconds.

        This is used for determining when to start writing audio data to attached 
        Microphone clients based on their requested start time.

        Returns
        -------
        float
            The current time of the microphone stream in seconds.

        """
        return -1.0

    @property
    def currentVolume(self):
        """Get the current volume level of the microphone input. 
        
        This method is intended to be used for visualizing the input level of 
        the microphone, e.g. in a volume meter.

        Returns
        -------
        float
            The current volume level, normalized to the range [0.0, 1.0].

        """
        return self.getCurrentVolume()

    def getCurrentVolume(self):
        """Get the current volume level of the microphone input. 
        
        This method is intended to be used for visualizing the input level of 
        the microphone, e.g. in a volume meter.

        Returns
        -------
        float
            The current volume level, normalized to the range [0.0, 100.0].

        """
        if self._rtBuffer is None:
            return 0.0
        
        # compute the root mean square (RMS) of the samples in the real-time buffer
        rms = ((self._rtBuffer ** 2).mean() ** 0.5) * 10.0
       
        return rms[0] if len(rms) > 1 else rms
    

if __name__ == "__main__":
    pass
