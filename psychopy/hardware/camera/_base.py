#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Base classes for camera devices and associated exceptions
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'CameraDevice'
]

from psychopy.hardware.base import BaseDevice

# ------------------------------------------------------------------------------
# Classes
#

class CameraDevice(BaseDevice):
    """Class providing an interface with a camera attached to the system.
    
    This interface handles the opening, closing, and reading of camera streams.

    Parameters
    ----------
    device : Any
        Camera device to open a stream with. The type of this value is dependent
        on the platform and the camera library being used. This can be an integer
        index, a string representing the camera device name.
    pollingInterval : float or None
        Interval in seconds to poll the camera stream for new frames. If `None`,
        the default polling interval is used which is equal to the frame rate. 
        The default value is `None`.

    """
    _captureLib = ''
    def __init__(self, *args, **kwargs):
        super().__init__()

    @staticmethod
    def getCameras():
        """Get a list of available camera devices on the system.

        Returns
        -------
        list[CameraInfo]
            List of available camera devices on the system.

        """
        raise NotImplementedError(
            "This method must be implemented by subclasses.")

    @staticmethod
    def getAvailableDevices(best=False):
        """Get a list of available camera devices on the system.

        Parameters
        ----------
        best : bool, optional
            If True, return only the best available camera device. The definition
            of "best" is dependent on the platform and the camera library being
            used. The default value is False, which returns all available camera
            devices.

        Returns
        -------
        list[CameraInfo]
            List of available camera devices on the system.

        """
        raise NotImplementedError(
            "This method must be implemented by subclasses.")

    @property
    def captureLib(self):
        """Camera library in use (`str`). This is the camera library being used
        to access the camera. This can be either, 'ffpyplayer', 'opencv'.
        """
        return self._captureLib
    
    @property
    def captureAPI(self):
        """Camera API in use (`str`). This is the camera API being used to access
        the camera. This can be either, 'AVFoundation', 'DirectShow' or 
        'Video4Linux2'.
        """
        raise NotImplementedError(
            "This method must be implemented by subclasses.")
    
    @property
    def pollingInterval(self):
        """Polling interval in seconds (`float` or `None`). This is the interval
        in seconds to poll the camera stream for new frames. If `None`, the
        default polling interval is used which is equal to the frame rate.
        """
        raise NotImplementedError(
            "This method must be implemented by subclasses.")
    
    @property
    def streamTime(self):
        """Current stream time in seconds (`float`).
        
        This is the current stream time in seconds. It is calculated as the
        difference between the current time and the absolute recording start
        time. If the camera stream is not open, this will return `-1.0`.
        
        """
        return -1.0
    
    @property
    def index(self):
        """Camera index (`int`). This is the enumerated index of this camera.
        """
        raise NotImplementedError(
            "This method must be implemented by subclasses.")
    
    @property
    def name(self):
        """Camera name (`str`). This is the camera name retrieved by the OS.
        """
        raise NotImplementedError(
            "This method must be implemented by subclasses.")
    
    @property
    def frameSize(self):
        """Current frame size in pixels (`tuple` of `int`).
        
        This is the current frame size in pixels. It is calculated as the
        difference between the current time and the absolute recording start
        time. If the camera stream is not open, this will return `(-1, -1)`.
        
        """
        return (-1, -1)

    @property
    def frameRate(self):
        """Current frame rate in frames per second (`float`).
        
        This is the current frame rate in frames per second. It is calculated as the
        difference between the current time and the absolute recording start
        time. If the camera stream is not open, this will return `-1.0`.
        
        """
        return -1.0
    
    @property
    def frameCount(self):
        """Current frame count (`int`).
        
        This is the current frame count. It is calculated as the
        difference between the current time and the absolute recording start
        time. If the camera stream is not open, this will return `-1`.
        
        """
        return -1
    
    @property
    def codecFormat(self):
        """Current codec format (`str`).
        
        This is the current codec format. It is calculated as the
        difference between the current time and the absolute recording start
        time. If the camera stream is not open, this will return `u'Null'`.
        
        """
        return ''

    @property
    def pixelFormat(self):
        """Current pixel format (`str`).
        
        This is the current pixel format. It is calculated as the
        difference between the current time and the absolute recording start
        time. If the camera stream is not open, this will return `u'Null'`.
        
        """
        return ''
    
    @property
    def isOpen(self):
        """Whether the camera stream is open (`bool`).
        
        This is a boolean value indicating whether the camera stream is open.
        If the camera stream is not open, this will return `False`.
        
        """
        return False
    
    @property
    def isReady(self):
        """Whether the camera stream is ready to read frames (`bool`).
        
        This is a boolean value indicating whether the camera stream is ready
        to read frames. If the camera stream is not open, this will return `False`.
        
        """
        return False
    
    def open(self, *args, **kwargs):
        """Open the camera stream.

        This method opens the camera stream and prepares it for reading frames.
        If the camera stream is already open, this method will do nothing.

        """
        raise NotImplementedError(
            "This method must be implemented by subclasses.")
    
    def close(self):
        """Close the camera stream.

        This method closes the camera stream and releases any resources
        associated with it. If the camera stream is not open, this method will
        do nothing.

        """
        raise NotImplementedError(
            "This method must be implemented by subclasses.")
    
    def createStream(self, *args, **kwargs):
        """Create a camera stream.

        This method creates a camera stream and prepares it for reading frames.
        If the camera stream is already open, this method will do nothing.

        """
        raise NotImplementedError(
            "This method must be implemented by subclasses.")
    
    # def update(self, *args, **kwargs):
    #     """Update the camera stream.

    #     This method updates the camera stream and retrieves any new frames
    #     available. If the camera stream is not open, this method will do nothing.

    #     """
    #     raise NotImplementedError(
    #         "This method must be implemented by subclasses.")

    def description(self):
        """Get a description of the camera stream.

        This method returns a string description of the camera stream, including
        information about the camera device, frame size, frame rate, and pixel
        format.

        Returns
        -------
        str
            Description of the camera stream.

        """
        return self.descriptionAsFormattedString()

    def frameSizeAsFormattedString(self):
        """Get image size as as formatted string.

        Returns
        -------
        str
            Size formatted as `'WxH'` (e.g. `'480x320'`).

        """
        frameSize = self.frameSize if self.frameSize is not None else (-1, -1)

        return '{width}x{height}'.format(
            width=frameSize[0],
            height=frameSize[1])
    
    def descriptionAsFormattedString(self):
        """Get a formatted string description of the camera stream.

        Returns
        -------
        str
            Formatted string description of the camera stream.

        """
        frameSize = self.frameSize if self.frameSize is not None else (-1, -1)
        
        return "[{name}] {width}x{height}@{frameRate}fps, {codec}".format(
            name=self.name,
            width=str(frameSize[0]),
            height=str(frameSize[1]),
            frameRate=str(self.frameRate),
            codec=self.codecFormat if self.codecFormat != '' else self.pixelFormat
        )
    

if __name__ == "__main__":
    pass 
