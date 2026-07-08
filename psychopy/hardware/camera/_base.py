#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Base classes for camera devices
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'VIDEO_DEVICE_ROOT_LINUX',
    'CAMERA_UNKNOWN_VALUE',
    'CAMERA_NULL_VALUE',
    # 'CAMERA_MODE_VIDEO',
    # 'CAMERA_MODE_CV',
    # 'CAMERA_MODE_PHOTO',
    'CAMERA_API_AVFOUNDATION',
    'CAMERA_API_DIRECTSHOW',
    'CAMERA_API_VIDEO4LINUX2',
    'CAMERA_API_ANY',
    'CAMERA_API_UNKNOWN',
    'CAMERA_API_NULL',
    'CAMERA_LIB_FFPYPLAYER',
    'CAMERA_LIB_OPENCV',
    'CAMERA_LIB_UNKNOWN',
    'CAMERA_LIB_NULL',
    'CameraError',
    'CameraNotReadyError',
    'CameraNotFoundError',
    'CameraFormatNotSupportedError',
    'CameraFrameRateNotSupportedError',
    'CameraFrameSizeNotSupportedError',
    'FormatNotFoundError',
    'PlayerNotAvailableError',
    'CameraInfo',
    'CameraDevice'
]

import logging
from psychopy.hardware.base import BaseDevice

# ------------------------------------------------------------------------------
# Constants
#

VIDEO_DEVICE_ROOT_LINUX = '/dev'
CAMERA_UNKNOWN_VALUE = u'Unknown'  # fields where we couldn't get a value
CAMERA_NULL_VALUE = u'Null'  # fields where we couldn't get a value

# camera operating modes
CAMERA_MODE_VIDEO = u'video'
CAMERA_MODE_CV = u'cv'
# CAMERA_MODE_PHOTO = u'photo'  # planned

# camera status 
CAMERA_STATUS_OK = 'ok'
CAMERA_STATUS_PAUSED = 'paused'
CAMERA_STATUS_EOF = 'eof'

# camera API flags, these specify which API camera settings were queried with
CAMERA_API_AVFOUNDATION = u'AVFoundation'  # mac
CAMERA_API_DIRECTSHOW = u'DirectShow'      # windows
CAMERA_API_VIDEO4LINUX2 = u'Video4Linux2'  # linux
CAMERA_API_ANY = u'Any'                    # any API (OpenCV only)
CAMERA_API_UNKNOWN = u'Unknown'            # unknown API
CAMERA_API_NULL = u'Null'                  # empty field

# camera libraries for playback nad recording
CAMERA_LIB_FFPYPLAYER = u'ffpyplayer'
CAMERA_LIB_OPENCV = u'opencv'
CAMERA_LIB_UNKNOWN = u'unknown'
CAMERA_LIB_NULL = u'null'

# special values
CAMERA_FRAMERATE_NOMINAL_NTSC = '30.000030'
CAMERA_FRAMERATE_NTSC = 30.000030

# FourCC and pixel format mappings, mostly used with AVFoundation to determine
# the FFMPEG decoder which is most suitable for it. Please expand this if you
# know any more!
pixelFormatTbl = {
    'yuvs': 'yuyv422',  # 4:2:2
    '420v': 'nv12',     # 4:2:0
    '2vuy': 'uyvy422'   # QuickTime 4:2:2
}

# Camera standards to help with selection. Some standalone cameras sometimes
# support an insane number of formats, this will help narrow them down. 
standardResolutions = {
    'vga': (640, 480),
    'svga': (800, 600),
    'xga': (1024, 768),
    'wxga': (1280, 768),
    'wxga+': (1440, 900),
    'sxga': (1280, 1024),
    'wsxga+': (1680, 1050),
    'uxga': (1600, 1200),
    'wuxga': (1920, 1200),
    'wqxga': (2560, 1600),
    'wquxga': (3840, 2400),
    '720p': (1280, 720),    # also known as HD
    '1080p': (1920, 1080),
    '2160p': (3840, 2160),
    'uhd': (3840, 2160),
    'dci': (4096, 2160)
}

# ------------------------------------------------------------------------------
# Exceptions
#

class CameraError(Exception):
    """Base class for errors around the camera."""


class CameraNotReadyError(CameraError):
    """Camera is not ready."""


class CameraNotFoundError(CameraError):
    """Raised when a camera cannot be found on the system."""


class CameraFormatNotSupportedError(CameraError):
    """Raised when a camera cannot use the settings requested by the user."""

class CameraFrameRateNotSupportedError(CameraFormatNotSupportedError):
    """Raised when a camera cannot use the frame rate settings requested by the 
    user."""

class CameraFrameSizeNotSupportedError(CameraFormatNotSupportedError):
    """Raised when a camera cannot use the frame size settings requested by the 
    user."""

class FormatNotFoundError(CameraError):
    """Cannot find a suitable pixel format for the camera."""


class PlayerNotAvailableError(Exception):
    """Raised when a player object is not available but is required."""


# ------------------------------------------------------------------------------
# Classes
#

class CameraInfo:
    """Information about a specific operating mode for a camera attached to the
    system.

    Parameters
    ----------
    index : int
        Index of the camera. This is the enumeration for the camera which is
        used to identify and select it by the `cameraLib`. This value may differ
        between operating systems and the `cameraLib` being used.
    name : str
        Camera name retrieved by the OS. This may be a human-readable name
        (i.e. DirectShow on Windows), an index on MacOS or a path (e.g.,
        `/dev/video0` on Linux). If the `cameraLib` does not support this 
        feature, then this value will be generated.
    frameSize : ArrayLike
        Resolution of the frame `(w, h)` in pixels.
    frameRate : ArrayLike
        Allowable framerate for this camera mode.
    pixelFormat : str
        Pixel format for the stream. If `u'Null'`, then `codecFormat` is being
        used to configure the camera.
    codecFormat : str
        Codec format for the stream.  If `u'Null'`, then `pixelFormat` is being
        used to configure the camera. Usually this value is used for high-def
        stream formats.
    cameraLib : str
        Library used to access the camera. This can be either, 'ffpyplayer',
        'opencv'.
    cameraAPI : str
        API used to access the camera. This relates to the external interface
        being used by `cameraLib` to access the camera. This value can be: 
        'AVFoundation', 'DirectShow' or 'Video4Linux2'.

    """
    __slots__ = [
        '_index',
        '_name',
        '_frameSize',
        '_frameRate',
        '_pixelFormat',
        '_codecFormat',
        '_cameraLib',
        '_cameraAPI'  # API in use, e.g. DirectShow on Windows
    ]

    def __init__(self,
                 index=-1,
                 name=CAMERA_NULL_VALUE,
                 frameSize=(-1, -1),
                 frameRate=-1.0,
                 pixelFormat=CAMERA_UNKNOWN_VALUE,
                 codecFormat=CAMERA_UNKNOWN_VALUE,
                 cameraLib=CAMERA_NULL_VALUE,
                 cameraAPI=CAMERA_API_NULL):

        self.index = index
        self.name = name
        self.frameSize = frameSize
        self.frameRate = frameRate
        self.pixelFormat = pixelFormat
        self.codecFormat = codecFormat
        self.cameraLib = cameraLib
        self.cameraAPI = cameraAPI

    def __repr__(self):
        return (f"CameraInfo(index={repr(self.index)}, "
                f"name={repr(self.name)}, "
                f"frameSize={repr(self.frameSize)}, "
                f"frameRate={self.frameRate}, "
                f"pixelFormat={repr(self.pixelFormat)}, "
                f"codecFormat={repr(self.codecFormat)}, "
                f"cameraLib={repr(self.cameraLib)}, "
                f"cameraAPI={repr(self.cameraAPI)})")

    def __str__(self):
        return self.description()

    @property
    def index(self):
        """Camera index (`int`). This is the enumerated index of this camera.
        """
        return self._index

    @index.setter
    def index(self, value):
        self._index = int(value)

    @property
    def name(self):
        """Camera name (`str`). This is the camera name retrieved by the OS.
        """
        return self._name

    @name.setter
    def name(self, value):
        self._name = str(value)

    @property
    def frameSize(self):
        """Resolution (w, h) in pixels (`ArrayLike` or `None`).
        """
        return self._frameSize

    @frameSize.setter
    def frameSize(self, value):
        if value is None:
            self._frameSize = None
            return
        
        assert len(value) == 2, "Value for `frameSize` must have length 2."
        assert all([isinstance(i, int) for i in value]), (
            "Values for `frameSize` must be integers.")

        self._frameSize = value

    @property
    def frameRate(self):
        """Frame rate (`float`) or range (`ArrayLike`). 
        
        Depends on the backend being used. If a range is provided, then the 
        first value is the maximum and the second value is the minimum frame 
        rate.
        """
        return self._frameRate

    @frameRate.setter
    def frameRate(self, value):
        # assert len(value) == 2, "Value for `frameRateRange` must have length 2."
        # assert all([isinstance(i, int) for i in value]), (
        #     "Values for `frameRateRange` must be integers.")
        # assert value[0] <= value[1], (
        #     "Value for `frameRateRange` must be `min` <= `max`.")

        self._frameRate = value

    @property
    def pixelFormat(self):
        """Video pixel format (`str`). An empty string indicates this field is
        not initialized.
        """
        return self._pixelFormat

    @pixelFormat.setter
    def pixelFormat(self, value):
        self._pixelFormat = str(value)

    @property
    def codecFormat(self):
        """Codec format, may be used instead of `pixelFormat` for some
        configurations. Default is `''`.
        """
        return self._codecFormat

    @codecFormat.setter
    def codecFormat(self, value):
        self._codecFormat = str(value)

    @property
    def cameraLib(self):
        """Camera library these settings are targeted towards (`str`).
        """
        return self._cameraLib

    @cameraLib.setter
    def cameraLib(self, value):
        self._cameraLib = str(value)

    @property
    def cameraAPI(self):
        """Camera API in use to obtain this information (`str`).
        """
        return self._cameraAPI

    @cameraAPI.setter
    def cameraAPI(self, value):
        self._cameraAPI = str(value)

    def frameSizeAsFormattedString(self):
        """Get image size as as formatted string.

        Returns
        -------
        str
            Size formatted as `'WxH'` (e.g. `'480x320'`).

        """
        return '{width}x{height}'.format(
            width=self.frameSize[0],
            height=self.frameSize[1])

    def description(self):
        """Get a description as a string.

        For all backends, this value is guaranteed to be valid after the camera
        has been opened. Some backends may be able to provide this information
        before the camera is opened.

        Returns
        -------
        str
            Description of the camera format as a human readable string.

        """
        codecFormat = self._codecFormat
        pixelFormat = self._pixelFormat
        codec = codecFormat if not pixelFormat else pixelFormat

        if self.frameSize is None:
            frameSize = (-1, -1)
        else:
            frameSize = self.frameSize

        return "[{name}] {width}x{height}@{frameRate}fps, {codec}".format(
            #index=self.index,
            name=self.name,
            width=str(frameSize[0]),
            height=str(frameSize[1]),
            frameRate=str(self.frameRate),
            codec=codec
        )
    

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
    _captureLib = CAMERA_LIB_NULL
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
        return CAMERA_NULL_VALUE

    @property
    def pixelFormat(self):
        """Current pixel format (`str`).
        
        This is the current pixel format. It is calculated as the
        difference between the current time and the absolute recording start
        time. If the camera stream is not open, this will return `u'Null'`.
        
        """
        return CAMERA_NULL_VALUE
    
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
            codec=self.codecFormat if self.codecFormat != CAMERA_NULL_VALUE else self.pixelFormat
        )
    

if __name__ == "__main__":
    pass 
