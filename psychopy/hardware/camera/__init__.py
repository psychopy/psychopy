#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for reading and writing camera streams.

A camera may be used to document participant responses on video or used by the
experimenter to create movie stimuli or instructions.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'VIDEO_DEVICE_ROOT_LINUX',
    'CAMERA_UNKNOWN_VALUE',
    'CAMERA_NULL_VALUE',
    'CAMERA_MODE_VIDEO',
    'CAMERA_MODE_CV',
    # 'CAMERA_MODE_PHOTO',
    'CAMERA_API_AVFOUNDATION',
    'CAMERA_API_DIRECTSHOW',
    'CAMERA_API_VIDEO4LINUX2',
    'CAMERA_API_ANY',
    'CAMERA_API_UNKNOWN',
    'CAMERA_API_NULL',
    'CAMERA_LIB_FFPYPLAYER',
    'CAMERA_LIB_PYAV',
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
    'Camera',
    'CameraInfo',
    'CameraFrame',
    'FFPyPlayerCameraDevice',
    'PyAVCameraDevice',
    'OpenCVCameraDevice',
    'getCameras',
    'getCameraDescriptions',
    'getOpenCameras',
    'closeAllOpenCameras',
    'renderVideo'
]

import os
import os.path
import sys
import platform
import inspect
import atexit
import time
import ctypes
import collections
import queue
import numpy as np
import threading

from psychopy.constants import NOT_STARTED
from psychopy.hardware import DeviceManager, BaseDevice
from psychopy.sound.audioclip import AudioClip
from psychopy.sound.microphone import Microphone
from psychopy.hardware.microphone import MicrophoneDevice
import psychopy.logging as logging

# ------------------------------------------------------------------------------
# Constants
#

# camera status 
CAMERA_STATUS_OK = 'ok'
CAMERA_STATUS_PAUSED = 'paused'
CAMERA_STATUS_EOF = 'eof'

CAMERA_UNKNOWN_VALUE = u'Unknown'  # fields where we couldn't get a value
CAMERA_NULL_VALUE = u'Null'  # fields where we couldn't get a value
CAMERA_NULL_FRAMERATE = -1.0  # frame rate when we couldn't get a value
CAMERA_NULL_FRAMESIZE = (-1, -1)  # frame size when we couldn't get a value

# camera operating modes
CAMERA_MODE_VIDEO = u'video'
CAMERA_MODE_CV = u'cv'
# CAMERA_MODE_PHOTO = u'photo'  # planned, single shot at specified time

# camera libraries for playback and recording
CAMERA_LIB_FFPYPLAYER = u'ffpyplayer'
CAMERA_LIB_PYAV = u'pyav'
CAMERA_LIB_OPENCV = u'opencv'
CAMERA_LIB_UNKNOWN = u'unknown'
CAMERA_LIB_NULL = u'null'

# special values
CAMERA_FRAMERATE_NOMINAL_NTSC = '30.000030'
CAMERA_FRAMERATE_NTSC = 30.000030
VIDEO_DEVICE_ROOT_LINUX = '/dev'

# camera API flags, these specify which API camera settings were queried with
CAMERA_API_AVFOUNDATION = u'AVFoundation'  # mac
CAMERA_API_DIRECTSHOW = u'DirectShow'      # windows
CAMERA_API_VIDEO4LINUX2 = u'Video4Linux2'  # linux
CAMERA_API_ANY = u'Any'                    # any API (OpenCV only)
CAMERA_API_UNKNOWN = u'Unknown'            # unknown API
CAMERA_API_NULL = u'Null'                  # empty field

# FourCC and pixel format mappings, mostly used with AVFoundation to determine
# the FFMPEG decoder which is most suitable for it. Please expand this if you
# know any more!
pixelFormatTbl = {
    'yuvs': 'yuyv422',  # 4:2:2
    '420v': 'nv12',     # 4:2:0
    '2vuy': 'uyvy422'   # QuickTime 4:2:2
}

# Mapping of Video4Linux2 FourCC codes (as `v4l2-ctl` reports them, lower-cased)
# onto the pixel format and codec names FFmpeg knows them by. Formats absent
# from this table are passed to FFmpeg unchanged. Please expand this if you know
# any more!
v4l2FormatTbl = {
    'yuyv': 'yuyv422',    # 4:2:2 packed
    'yvyu': 'yvyu422',
    'uyvy': 'uyvy422',
    'vyuy': 'uyvy422',
    'yu12': 'yuv420p',    # 4:2:0 planar
    'yv12': 'yuv420p',
    'nv12': 'nv12',
    'nv21': 'nv21',
    'yuv420': 'yuv420p',
    'mjpg': 'mjpeg',      # compressed
    'jpeg': 'mjpeg',
    'h264': 'h264',
    'hevc': 'hevc',
    'rgb3': 'rgb24',      # packed RGB
    'bgr3': 'bgr24',
    'rgb4': 'rgba',
    'bgr4': 'bgra',
    'rgbp': 'rgb565le',
    'grey': 'gray',       # monochrome
    'y16 ': 'gray16le',
    'y16': 'gray16le'
}

# Mapping of capture format names, as the rest of this module spells them,
# onto the FourCC codes OpenCV asks drivers for them by. Both the FFmpeg names
# used on Windows and MacOS and the Video4Linux2 ones used on Linux are listed,
# since either can reach `OpenCVCameraDevice`. Please expand this if you know
# any more!
openCVFourCCTbl = {
    'mjpeg': 'MJPG',      # compressed
    'mjpg': 'MJPG',
    'jpeg': 'MJPG',
    'h264': 'H264',
    'hevc': 'HEVC',
    'yuyv422': 'YUYV',    # 4:2:2 packed
    'yuyv': 'YUYV',
    'yvyu422': 'YVYU',
    'yvyu': 'YVYU',
    'uyvy422': 'UYVY',
    'uyvy': 'UYVY',
    'yuv420p': 'YU12',    # 4:2:0 planar
    'yu12': 'YU12',
    'yv12': 'YV12',
    'nv12': 'NV12',
    'nv21': 'NV21',
    'rgb24': 'RGB3',      # packed RGB
    'rgb3': 'RGB3',
    'bgr24': 'BGR3',
    'bgr3': 'BGR3',
    'gray': 'GREY',       # monochrome
    'grey': 'GREY'
}

# Camera/frame dimension standards
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
    '720p': (1280, 720),
    '1080p': (1920, 1080),
    '2160p': (3840, 2160),
    'uhd': (3840, 2160),
    'dci': (4096, 2160)
}

PREFERED_CAMERA_LIB = CAMERA_LIB_PYAV
CAMERA_LIBS = [  # list of supported camera libraries
    CAMERA_LIB_FFPYPLAYER, 
    CAMERA_LIB_PYAV,
    CAMERA_LIB_OPENCV]  

# used to determine which video backend to use when opening camera interfaces,
# when cameraLib is None.
backend = PREFERED_CAMERA_LIB  

# Keep track of open capture interfaces so we can close them at shutdown in the
# event that the user forgets or the program crashes.
#
_openCaptureInterfaces = set()

# ------------------------------------------------------------------------------
# Helper functions
#

def _isNullFormat(value):
    """Check whether a pixel or codec format value means 'not set'.

    Camera capabilities are reported by a mix of sources which disagree about
    how to say that a field does not apply, and `CameraInfo` coerces whatever
    it is given to a string. This treats all of the spellings in use, including
    the string `'None'` produced by stringifying `None`, as unset.

    Parameters
    ----------
    value : str or None
        Pixel or codec format value to check.

    Returns
    -------
    bool
        `True` if the value does not name a format.

    """
    if value is None:
        return True

    return str(value).strip() in (
        '', 'None', CAMERA_NULL_VALUE, CAMERA_UNKNOWN_VALUE)


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

class _RGBFrameAdapter:
    """Lightweight adapter exposing an `ffpyplayer`-like interface around raw
    RGB24 frame bytes obtained from other capture backends (currently `PyAV`).

    Higher level code in this module (`CameraFrame`, `Camera`) was originally
    written around `ffpyplayer`'s `Image` objects, which expose
    `to_memoryview()` (returning a list whose first element has a `.memview`
    attribute), `get_pixel_format()` and `get_size()`. Wrapping frames decoded
    by other backends in this adapter lets that code stay backend-agnostic
    instead of branching on `captureLib` throughout.

    The same adapter is used by `psychopy.visual.movies` for movie playback, so
    frames from either source can be passed to the same downstream routines.

    Parameters
    ----------
    rgbData : numpy.ndarray or bytes
        Raw RGB24 pixel data, row-major, 3 bytes per pixel. An array is kept
        as-is (made contiguous first if needed) rather than converted to
        `bytes`, which would cost a whole-frame copy per captured frame for no
        benefit; everything downstream reads this through the buffer protocol.
    size : tuple or None
        Frame size as `(width, height)` in pixels. If `None` (the default), the
        size is taken from the shape of `rgbData`, which requires it to be a
        Numpy array.

    """
    __slots__ = ['_data', '_size']

    def __init__(self, rgbData, size=None):
        if isinstance(rgbData, np.ndarray):
            rgbData = np.ascontiguousarray(rgbData)
            if size is None:
                size = (rgbData.shape[1], rgbData.shape[0])

        if size is None:
            raise ValueError(
                "Cannot determine frame size, pass `size` explicitly when "
                "`rgbData` is not a Numpy array.")

        self._data = rgbData
        self._size = (int(size[0]), int(size[1]))

    def to_memoryview(self):
        return [self]

    @property
    def memview(self):
        return self._data

    def get_pixel_format(self):
        return 'rgb24'

    def get_size(self):
        return self._size

    @property
    def width(self):
        return self._size[0]

    @property
    def height(self):
        return self._size[1]

    def to_ndarray(self, format='rgb24'):
        """Get the frame as a Numpy array.

        Provided so that this adapter can stand in for an `av.VideoFrame` as
        well as an `ffpyplayer` image. Only `format='rgb24'` is supported since
        the data held here has already been converted.

        Parameters
        ----------
        format : str
            Pixel format to return the data in. Must be `'rgb24'`.

        Returns
        -------
        numpy.ndarray
            Frame data with shape `(height, width, 3)`.

        """
        if format != 'rgb24':
            raise ValueError(
                "`_RGBFrameAdapter` can only provide 'rgb24' data, got "
                "'{}'.".format(format))

        frameWidth, frameHeight = self._size
        arr = np.frombuffer(self._data, dtype=np.uint8)

        return arr.reshape((frameHeight, frameWidth, 3))


class CameraFrame:
    """Class representing a single frame from a camera stream.

    This class encapsulates a single frame captured from a camera stream,
    along with its associated timestamp information.

    Parameters
    ----------
    image : numpy.ndarray
        The image data of the frame as a Numpy array.
    pts : float
        Presentation timestamp in seconds when this frame was captured since the
        start of the recording.
    absTime : float
        The absolute time in seconds when this frame was captured using the 
        camera's timebase.
    captureLib : str
        The camera library used to capture this frame (e.g., 'ffpyplayer',
        'pyav', 'opencv'). This helps routines passed this object determine the 
        color format and other properties of the frame which may be platform and 
        library dependent.

    """
    _colorData = None
    _pts = -1.0
    _absTime = -1.0
    _captureLib = None

    def __init__(self, colorData, pts=-1.0, absTime=-1.0, captureLib=None):
        self.colorData = colorData
        self.pts = pts
        self.absTime = absTime
        self.captureLib = captureLib

        # detection results
        self._detectedObjects = {}

    @property
    def colorData(self):
        """Get the image data of the frame (`numpy.ndarray`).

        Returns
        -------
        numpy.ndarray
            The image data of the frame as a Numpy array.

        """
        return self._colorData
    
    @colorData.setter
    def colorData(self, value):
        self._colorData = value
    
    @property
    def colorFormat(self):
        """Get the color (pixel) format of the image data (`str`).

        Returns
        -------
        str
            The color format of the image data (e.g., 'RGB', 'BGR').

        """
        if self._captureLib == CAMERA_LIB_FFPYPLAYER:
            return 'RGB'
        elif self._captureLib == CAMERA_LIB_PYAV:
            # PyAV hands over frames in whatever format the camera is streaming
            # in until they are converted, so report the frame's own format
            if isinstance(self._colorData, _RGBFrameAdapter):
                return 'RGB'
            pixFmt = getattr(
                getattr(self._colorData, 'format', None), 'name', None)
            if pixFmt is None:
                return 'Unknown'

            return 'RGB' if pixFmt == 'rgb24' else pixFmt
        elif self._captureLib == CAMERA_LIB_OPENCV:
            # `OpenCVCameraDevice` converts frames on its capture thread, so
            # only frames taken from OpenCV directly are still BGR
            return 'BGR' if isinstance(self._colorData, np.ndarray) else 'RGB'
        else:
            return 'Unknown'
    
    @property
    def frameSize(self):
        """Get the size of the image data (`tuple`).

        Returns
        -------
        tuple
            The size of the image data as a tuple (width, height).

        """
        if self._captureLib == CAMERA_LIB_FFPYPLAYER:
            frameW, frameH = self.colorData.get_size()
            return (frameW, frameH)
        elif self._captureLib == CAMERA_LIB_PYAV:
            # works for both `av.VideoFrame` and `_RGBFrameAdapter`
            return (self.colorData.width, self.colorData.height)
        elif self._captureLib == CAMERA_LIB_OPENCV:
            if isinstance(self.colorData, np.ndarray):
                # OpenCV frames are transposed
                return (self.colorData.shape[1], self.colorData.shape[0])

            return (self.colorData.width, self.colorData.height)
    
    @property
    def pts(self):
        """Get the presentation timestamp of the frame (`float`).

        Returns
        -------
        float
            The presentation timestamp in seconds when this frame was captured 
            since the start of the recording.

        """
        return self._pts
    
    @pts.setter
    def pts(self, value):
        self._pts = float(value)
    
    @property
    def absTime(self):
        """Get the absolute time of the frame (`float`).

        Returns
        -------
        float
            The absolute time in seconds when this frame was captured, on the
            same clock as `Camera.streamTime`.

        """
        return self._absTime

    @absTime.setter
    def absTime(self, value):
        self._absTime = float(value)
    
    @property
    def captureLib(self):
        """Get the camera library used to capture this frame (`str`).

        Returns
        -------
        str
            The camera library used to capture this frame (e.g., 'ffpyplayer',
            'opencv').

        """
        return self._captureLib
    
    @captureLib.setter
    def captureLib(self, value):
        self._captureLib = value
    
    def detectObjects(self, recognizer, refresh=False, **kwargs):
        """Detect objects in the frame using the specified recognizer.

        Multiple recognizers can be passed as a list for batch processing which 
        is more efficient than calling this method multiple times on the same 
        frame with different recognizers.

        Parameters
        ----------
        recognizer : Any
            The object recognizer to use for detecting objects in the frame.
            Usually an instance of a class derived from
            `psychopy.tools.imagetools.BaseObjectRecognizer`.
        refresh : bool, optional
            If `True`, forces re-detection of objects even if results are
            already cached. Default is `False`.
        **kwargs : dict
            Additional keyword arguments to pass to the recognizer's
            `detectObjects()` method.
        
        Returns
        -------
        dict
            A dictionary containing detection results for each recognizer. The
            keys are the recognizer names and the values are dictionaries with 
            the following keys:
                - 'pts': Presentation timestamp of the frame.
                - 'count': Number of objects detected.
                - 'objects': List of detected objects with their details.

            The structure of each detected object depends on the recognizer, see
            the documentation of the specific recognizer for details.

        Example
        -------
        Detect faces in a camera frame using Haar cascade classifiers:

            import psychopy.tools.imagetools as imagetools

            # load the pre-trained face recognizer
            faceRecognizer = imagetools.HaarCascadeObjectRecognizer(
                'haarcascade_frontalface_default.xml')

            # in main loop after opening a camera interface with handle 'cam'
            cam.update()  # update the camera to get the latest frame
            recentFrame = cam.lastFrame  

            detected = recentFrame.detectObjects(faceRecognizer)
        
        Passing a list of recognizers for batch processing:

            # A list of recognizers, index indicates detection order. We are
            # assigning names to each recognizer which will be used as keys in 
            # the results dictionary.
            recognizers = [
                imagetools.HaarCascadeObjectRecognizer(
                    'haarcascade_frontalface_default.xml', name='face'),
                imagetools.HaarCascadeObjectRecognizer(
                    'haarcascade_eye.xml', name='eye')
            ]

            detected = recentFrame.detectObjects(recognizers)

            # get references to detected objects
            faces = detected['face']['objects']
            eyes = detected['eye']['objects']

            # get position of the first detected face (if any)
            if faces['count'] > 0:
                firstFace = faces['objects'][0]
                x, y, w, h = firstFace['rect']

        """
        if not refresh and self._detectedObjects:
            return self._detectedObjects  # return cached results
        
        if not isinstance(recognizer, (list, tuple)):
            recognizer = [recognizer]

        import cv2

        # Get the frame data as a grayscale array for detection. PyAV can hand
        # over grayscale directly, avoiding a full colour conversion we would
        # only throw away again.
        if self._captureLib == CAMERA_LIB_FFPYPLAYER:
            frameW, frameH = self.frameSize
            cameraFrameBuffer = self.colorData.to_memoryview()[0].memview
            cameraFrameArray = np.frombuffer(
                cameraFrameBuffer, dtype=np.uint8).reshape(
                    (frameH, frameW, 3))
            grayFrame = cv2.cvtColor(cameraFrameArray, cv2.COLOR_RGB2GRAY)
        elif self._captureLib == CAMERA_LIB_PYAV:
            if isinstance(self.colorData, _RGBFrameAdapter):
                grayFrame = cv2.cvtColor(
                    self.colorData.to_ndarray(format='rgb24'),
                    cv2.COLOR_RGB2GRAY)
            else:
                grayFrame = self.colorData.to_ndarray(format='gray')
        elif self._captureLib == CAMERA_LIB_OPENCV:
            if isinstance(self.colorData, _RGBFrameAdapter):
                grayFrame = cv2.cvtColor(
                    self.colorData.to_ndarray(format='rgb24'),
                    cv2.COLOR_RGB2GRAY)
            else:
                grayFrame = cv2.cvtColor(self.colorData, cv2.COLOR_BGR2GRAY)
        else:
            raise ValueError(
                "Cannot detect objects in a frame captured with "
                "'{}'.".format(self._captureLib))

        results = {}
        for recog in recognizer:
            recogName = recog.name if hasattr(recog, 'name') else str(
                type(recog))
            detectedObjs = recog.detectObjects(
                grayFrame, **kwargs)
            
            results[recogName] = {
                'pts': self.pts,  
                'count': len(detectedObjs),
                'objects': detectedObjs
            }

        self._detectedObjects = results  # store the detection results

        return results


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
    _device = None  # name/path/index identifying the device to the backend
    _cameraClients = ()  # clients bound to this stream, see `bind()`
    _ptsAnchor = None  # (pts, local time) of the first frame, see `_absTimeForPTS()`
    _pollingTimerThread = None  # thread driving `_poll()`, see `_setupAutoPolling()`
    _pollingInterval = None  # seconds between polls

    def __init__(self, *args, **kwargs):
        super().__init__()

        self._cameraClients = []
        self._ptsAnchor = None

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

    # --------------------------------------------------------------------------
    # Client registration and polling
    #
    # These are shared by all capture backends. Backends are responsible only
    # for producing frames in `_getFrames()`; dispatching them to clients and
    # scheduling the polling which drives that is handled here.
    #

    @property
    def clientCount(self):
        """Get the number of clients registered to receive frames from this 
        camera stream.

        Returns
        -------
        int
            Number of registered clients.

        """
        return len(self._cameraClients)

    def bind(self, client):
        """Register a client to receive new frames from the camera stream.

        Parameters
        ----------
        client : object
            Client object that has an `onNewFrames(frames)` method to receive 
            new frames.

        """
        if client not in self._cameraClients:
            self._cameraClients.append(client)

    def unbind(self, client):
        """Unregister a client from receiving new frames from the camera stream.

        Parameters
        ----------
        client : object
            Client object that was previously registered to receive new frames.

        """
        if client in self._cameraClients:
            self._cameraClients.remove(client)

    def _onNewFrames(self, frames):
        """Callback function called when new frames are available from the 
        camera stream.
        
        Parameters
        ----------
        frames : list of tuples
            List of tuples containing the frames and their timestamps. Each tuple
            contains (frame, frame index, timestamp).

        """
        for client in self._cameraClients:
            client._onNewFrames(frames)

    def _absTimeForPTS(self, pts, tReceived):
        """Map a stream presentation timestamp onto the local clock.

        Cameras timestamp frames on a clock of their own choosing: some count
        from zero at the start of the stream, others report a system clock which
        may or may not be the one `time.monotonic()` reads. Callers wanting to
        line frames up against events elsewhere in the experiment need a time
        they can compare, so the first frame seen anchors the stream's clock to
        the local one and every frame after that is placed relative to it.

        Anchoring rather than simply timestamping frames on arrival keeps the
        spacing between frames as the camera reported it, which matters because
        frames are usually handed over in bursts when the stream is polled.

        Parameters
        ----------
        pts : float or None
            Presentation timestamp of the frame in seconds, as the camera
            reported it. If `None` or negative, the arrival time is used
            instead.
        tReceived : float
            Local time in seconds, from `time.monotonic()`, at which the frame
            was received.

        Returns
        -------
        float
            Time the frame was captured, on the local monotonic clock.

        """
        if pts is None or pts < 0:
            return tReceived

        if self._ptsAnchor is None:  # first frame of the stream sets the anchor
            self._ptsAnchor = (pts, tReceived)

        ptsAtAnchor, tAtAnchor = self._ptsAnchor
        absTime = tAtAnchor + (pts - ptsAtAnchor)

        if absTime > tReceived:
            # A frame cannot have been captured after it was handed to us, so an
            # anchor which puts it there was itself set on a frame that had been
            # sitting in a buffer. Re-anchor on this frame, which was delivered
            # sooner; over the first few frames this settles on the lowest
            # latency the stream has shown.
            self._ptsAnchor = (pts, tReceived)
            absTime = tReceived

        return absTime

    def _getFrames(self):
        """Get the most recent frames from the camera stream.

        This is called by the `_poll()` method to read frames from the camera
        stream. It reads all available frames until there are no more and
        dispatches them to bound clients via the `_onNewFrames()` method.

        Returns
        -------
        list
            List of tuples containing the frames and their timestamps. Each
            tuple contains `(frame, frame index, pts, absTime)`, where `pts` is
            the timestamp the camera reported and `absTime` is that mapped onto
            the local monotonic clock by `_absTimeForPTS()`.

        """
        raise NotImplementedError(
            "This method must be implemented by subclasses.")

    def _poll(self):
        """Poll the camera stream for new frames.

        This method must be called at regular intervals to read frames from the 
        camera stream. It reads all available frames until there are no more and
        dispatches them to bound clients via the `_onNewFrames()` method. If
        this method is not called before the camera stream buffer fills up, 
        frames will be dropped.

        If the camera stream is paused, this method will not read any frames and
        will return immediately.

        If automatic polling is setup via `_setupAutoPolling()`, this method
        will be called automatically. Otherwise, the user must call this method
        manually using a code component.

        """
        self._getFrames()  # get the most recent frames

    def _setupAutoPolling(self):
        """Set up automatic polling of the camera stream to read frames at 
        regular intervals.
        
        This method sets up a thread that calls the `_poll` method at regular 
        intervals defined by `self._pollingInterval`. The `_poll` method reads 
        frames from the camera stream and processes them.

        """
        if self._pollingTimerThread is not None:
            self._pollingTimerThread.cancel()

        logging.debug(
            "Setting up automatic polling of the camera stream every {} seconds.".format(
                self._pollingInterval))

        # set up a thread to call the poll method at regular intervals
        class PollingTimerThread(threading.Thread):
            """Thread class used to call the poll method at regular 
            intervals.
            """
            def __init__(self, interval, function):
                super().__init__()
                self.interval = interval
                self.function = function
                self._stop_event = threading.Event()

            def run(self):
                # `wait()` returns True once the event is set, so a thread
                # cancelled while sleeping stops there rather than polling one
                # last time against a stream which is being torn down
                while not self._stop_event.wait(self.interval):
                    self.function()

            def cancel(self):
                self._stop_event.set()

        # set up a thread to call the poll method at regular intervals
        self._pollingTimerThread = PollingTimerThread(
            self._pollingInterval, 
            self._poll)
        self._pollingTimerThread.daemon = True
        self._pollingTimerThread.start()

    def _stopAutoPolling(self):
        """Stop automatic polling of the camera stream, if it is running.

        This waits for the polling thread to finish, so that it cannot be part
        way through reading the stream when the caller goes on to close it.

        """
        if self._pollingTimerThread is None:
            return

        self._pollingTimerThread.cancel()

        # the thread sleeps for one polling interval at a time, so this returns
        # promptly; guard against joining ourselves if a client ever calls this
        # from within a poll
        if self._pollingTimerThread is not threading.current_thread():
            self._pollingTimerThread.join(
                timeout=max(5.0, (self._pollingInterval or 0.0) * 5.0))
            if self._pollingTimerThread.is_alive():
                logging.error(
                    "Timed out waiting for the polling thread for camera '{}' "
                    "to stop.".format(self._device))

        self._pollingTimerThread = None
        logging.debug(
            "Stopped automatic polling of the camera stream for device "
            "'{}'.".format(self._device))

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

    def getMetadata(self):
        """Get metadata about the camera stream.

        Returns
        -------
        dict
            Mapping describing the stream, with the keys `'name'`,
            `'src_vid_size'`, `'frame_rate'`, `'pixel_format'`,
            `'codec_format'`, `'capture_lib'` and `'capture_api'`. Values are
            only meaningful once the stream has been opened.

        """
        frameSize = self.frameSize if self.frameSize is not None else (-1, -1)

        return {
            'name': self.name,
            'src_vid_size': tuple(frameSize),
            'frame_rate': self.frameRate,
            'pixel_format': self.pixelFormat,
            'codec_format': self.codecFormat,
            'capture_lib': self.captureLib,
            'capture_api': self.captureAPI}

    @classmethod
    def getDeviceCapabilities(cls, device, by=None):
        """
        Get the capabilities of a specific camera device.

        Parameters
        ----------
        device : str or int
            The name or index of the camera device.
        by : str, optional
            If specified, filter the capabilities by a specific attribute (e.g.,
            'frameSize', 'frameRate', 'pixelFormat', 'codecFormat'). If `None`,
            return all capabilities.

        Returns
        -------
        list
            List of dictionaries containing the capabilities of the specified
            camera device. Each dictionary contains the following keys:
                - 'frameSize': Tuple (width, height) of the frame size.
                - 'frameRate': Frame rate in frames per second.
                - 'pixelFormat': Pixel format of the frame.
                - 'codecFormat': Codec format used for the frame.
            If `by` is specified, the list will only include capabilities that 
            match the specified attribute.

        """
        # find the specified device
        deviceModes = []
        for dev in cls.getCameras().values():
            for mode in dev:
                if mode.name != device:
                    continue

                if by is None:
                    deviceModes.append({
                        'frameSize': mode.frameSize,
                        'frameRate': mode.frameRate,
                        'pixelFormat': mode.pixelFormat,
                        'codecFormat': mode.codecFormat
                    })
                else:
                    if hasattr(mode, by):
                        modeStr = str(getattr(mode, by))
                        if modeStr not in deviceModes:
                            deviceModes.append(modeStr)
                    else:
                        raise ValueError(
                            "Invalid filter attribute '{}'. Must be one of: "
                            "'frameSize', 'frameRate', 'pixelFormat', "
                            "'codecFormat'.".format(by))
            
        return deviceModes

    @classmethod
    def getSupportedFrameRates(cls, index, resolution=None):
        """
        List supported frame rate options for a given device at a given resolution.

        Parameters
        ----------
        index : str
            Index (name) of the camera
        resolution : tuple[int]
            Resolution at which to get frame rates. Leave as None to list all frame rate options.

        Returns
        -------
        list[int]
            List of supported frame rates; the first item will always be None (as this is an option 
            which tells the device to use the default)
        """
        frameRates = set()
        # Iterate through the modes this camera reports. `getAvailableDevices`
        # gives one profile per camera rather than per format, so the per-format
        # detail has to come from the capability list.
        for mode in cls.getDeviceCapabilities(index):
            # skip non-matching resolutions
            if resolution is not None and tuple(mode['frameSize']) != tuple(resolution):
                continue
            # append if we got this far
            frameRates.add(mode['frameRate'])
        # sort
        frameRates = sorted(frameRates)

        return [None] + frameRates

    @classmethod
    def getSupportedResolutions(cls, index, frameRate=None):
        """
        List supported resolution options for a given device at a given frame rate.

        Parameters
        ----------
        index : str
            Index (name) of the camera
        frameRate : tuple[int]
            Frame rate at which to get resolutions. Leave as None to list all frame rate options.

        Returns
        -------
        list[int]
            List of supported resolutions; the first item will always be None (as this is an option 
            which tells the device to use the default)
        """
        resolutions = set()
        # Iterate through the modes this camera reports. `getAvailableDevices`
        # gives one profile per camera rather than per format, so the per-format
        # detail has to come from the capability list.
        for mode in cls.getDeviceCapabilities(index):
            # skip non-matching frame rates
            if frameRate is not None and mode['frameRate'] != frameRate:
                continue
            # append if we got this far
            resolutions.add(tuple(mode['frameSize']))
        # sort
        resolutions = sorted(resolutions, key=lambda x: x[0] * x[1])

        return [None] + resolutions


# keep track of camera devices that are opened
_openCameras = {}


# ~~~ Library specific camera device classes ~~~

class FFPyPlayerCameraDevice(CameraDevice):
    """Class providing an interface with a camera attached to the system 
    using FFmpeg (ffpyplayer).
    
    This interface handles the opening, closing, and reading of camera streams.
    Client objects can register themselves to receive new frames from the camera
    stream. The camera stream is polled at regular intervals to read new frames
    and notify registered clients.

    Parameters
    ----------
    device : Any
        Camera device to open a stream with. The type of this value is dependent
        on the platform and the camera library being used. This can be an integer
        index, a string representing the camera device name.
    frameSize : ArrayLike or None
        Resolution of the frame `(w, h)` in pixels. If `None`, the default frame 
        size is used which is `(640, 480)`. The default value is `None`.
    frameRate : float or None
        Frame rate in frames per second. If `None`, the default frame rate is
        used which is `30.0`. The default value is `None`.
    decoderOpts : dict or None
        Dictionary of options to pass to the FFmpeg decoder. If `None`, default
        options are used. The default value is `None`.
    bufferSecs : float
        Number of seconds of video to buffer in memory. This is used to set the
        real-time buffer size for the camera stream. The default value is `5.0`
        for 5 seconds of video.
    pollingInterval : float or None
        Interval in seconds to poll the camera stream for new frames. If `None`,
        the default polling interval is used which is equal to the frame rate. 
        The default value is `None`.

    """
    _streams = {}
    backend = 'ffpyplayer'
    _captureLib = CAMERA_LIB_FFPYPLAYER
    _deviceClassPath = "psychopy.hardware.camera.CameraDevice"

    def __init__(self, 
                 device, 
                 frameSize=None, 
                 frameRate=None,
                 pixelFormat=None,
                 codecFormat=None,
                 decoderOpts=None, 
                 bufferSecs=5.0, 
                 pollingInterval=None, 
                 **kwargs):
        # if device is an integer, get name from index
        foundProfile = None
        
        if isinstance(device, int):
            device = self.getAvailableDevices()[device]['deviceName']

        # if device is a string, get profile from name
        if isinstance(device, str):
            for profile in self.getAvailableDevices():
                if profile['deviceName'] == device:
                    foundProfile = profile
                    break
        # if device is a dict, use it directly
        elif isinstance(device, dict):
            foundProfile = device

        if foundProfile is None:
            raise CameraNotFoundError(
                "Cannot find camera with index or name '{}'.".format(device))

        self.info = foundProfile
        self._frameSize = frameSize if frameSize is not None else [640, 480]
        self._frameRate = frameRate if frameRate is not None else 30.0
        self._device = self.info['deviceName']
        self._decoderOpts = decoderOpts if decoderOpts is not None else {}
        self._pollingInterval = pollingInterval if pollingInterval is not None else self.frameInterval
        self._pollingTimerThread = None
        self._pollingLock = threading.Lock()
        self._bufferSecs = bufferSecs
        self._frameCount = 0

        # gat all the capabilities of the camera device, including supported 
        # frame sizes, frame rates, pixel formats, and codec formats
        allCaps = FFPyPlayerCameraDevice.getDeviceCapabilities(self._device)

        # get the best matching capabilities for the requested frame size and frame rate
        for cap in allCaps:
            if cap['frameSize'] == self._frameSize and cap['frameRate'] == self._frameRate:
                self._pixelFormat = cap['pixelFormat']
                self._codecFormat = cap['codecFormat']
                break
        else:
            # if no exact match, use the first available capability
            self._pixelFormat = allCaps[0]['pixelFormat']
            self._codecFormat = allCaps[0]['codecFormat']

        if platform.system() == 'Darwin':
            self._captureAPI = CAMERA_API_AVFOUNDATION
            self._pixelFormat = pixelFormat if pixelFormat is not None else 'yuvs'
            self._codecFormat = codecFormat if codecFormat is not None else 'h264'
        elif platform.system() == 'Windows':
            self._captureAPI = CAMERA_API_DIRECTSHOW
            self._pixelFormat = pixelFormat if pixelFormat is not None else 'yuyv422'
        elif platform.system() == 'Linux':
            self._captureAPI = CAMERA_API_VIDEO4LINUX2
            self._pixelFormat = pixelFormat if pixelFormat is not None else 'yuyv422'
        else:
            raise OSError(
                "Unsupported platform '{}', cannot select capture API.".format(
                    platform.system()))

        self._capture = None  # will hold the ffpyplayer MediaPlayer object
        # keep track of clients attached to this camera stream
        self._cameraClients = []

        self.open()  # open the camera stream

    @property
    def captureAPI(self):
        """Camera API in use (`str`), one of `'AVFoundation'`, `'DirectShow'`
        or `'Video4Linux2'`.
        """
        return self._captureAPI

    @property
    def pollingInterval(self):
        """Interval in seconds between polls of the camera stream (`float`).
        """
        return self._pollingInterval

    @property
    def name(self):
        """Camera name (`str`). This is the camera name retrieved by the OS.
        """
        return self._device

    @property
    def frameSize(self):
        """Get the frame size of the camera stream.

        Returns
        -------
        tuple
            Frame size as (width, height). Returns `None` if the camera stream
            is not open or if metadata needs to be obtained from the stream.

        """
        if self._capture is None:
            return None

        return self._frameSize
    
    @property
    def frameRate(self):
        """Get the frame rate of the camera stream.

        Returns
        -------
        float
            Frame rate in frames per second. Returns `None` if the camera stream
            is not open or if metadata needs to be obtained from the stream.

        """
        if self.info is None:
            return None

        return self._frameRate

    @property
    def frameInterval(self):
        """Get the frame interval of the camera stream.

        Returns
        -------
        float
            Frame interval in seconds. Returns `-1.0` if the camera stream is 
            not open or if metadata needs to be obtained from the stream.

        """
        if self.info is None:
            return -1.0

        return 1.0 / self._frameRate if self._frameRate > 0 else -1.0

    def _getFrames(self):
        """Get the most recent frames from the camera stream.

        This is called by the `poll()` method to read frames from the camera 
        stream. It reads all available frames until there are no more and 
        dispatches them to bound clients via the `_onNewFrames()` method.
        
        Returns
        -------
        list
            List of tuples containing the frames and their timestamps. Each tuple
            contains (frame, frame index, timestamp).

        """
        if self._capture is None:
            raise PlayerNotAvailableError(
                "Camera stream is not open. Call `open()` first.")
        
        # read all buffered frames from the camera stream until we get nothing
        recentFrames = []
        with self._pollingLock:
            tReceived = time.monotonic()
            while 1:
                frame, status = self._capture.get_frame()

                if status == CAMERA_STATUS_EOF or status == CAMERA_STATUS_PAUSED: 
                    break

                if frame is None:  # ditto 
                    break

                img, curPts = frame
                # if curPts < 0.0:
                #     del img  # free the memory used by the frame
                #     # if the frame is before the recording start time, skip it
                #     continue

                recentFrames.append((
                    img, 
                    self._frameCount,  # frame index
                    curPts,
                    self._absTimeForPTS(curPts, tReceived)))

                self._frameCount += 1  # increment the frame count

        self._onNewFrames(recentFrames)  # dispatch to clients any new frames
            
        return recentFrames
    
    @property
    def paused(self):
        """Check if the camera stream is paused.

        Returns
        -------
        bool
            `True` if the camera stream is paused, `False` otherwise.

        """
        if self._capture is None:
            raise PlayerNotAvailableError(
                "Camera stream is not open. Call `open()` first.")

        return self._capture.get_pause()
    
    @paused.setter
    def paused(self, value):
        """Pause or resume the camera stream.

        Parameters
        ----------
        value : bool
            If `True`, pause the camera stream. If `False`, resume the camera 
            stream.

        """
        self.setPause(value)

    def setPause(self, pause):
        """Pause or resume the camera stream.

        This method allows pausing or resuming the camera stream. When paused, 
        the camera stream will not provide new frames until resumed. This can 
        lower latency and reduce CPU usage when the camera is not needed.

        Parameters
        ----------
        pause : bool
            If `True`, pause the camera stream. If `False`, resume the camera 
            stream.

        """
        if self._capture is None:
            raise PlayerNotAvailableError(
                "Camera stream is not open. Call `open()` first.")

        self._capture.set_pause(pause)

    @property
    def isOpen(self):
        """Check if the camera stream is open.

        Returns
        -------
        bool
            `True` if the camera stream is open, `False` otherwise.

        """
        return self._capture is not None

    def _obtainInitialStreamMetadata(self, timeout=5.0):
        """Obtain initial metadata from the camera stream.

        This is called within the `open()` method after the camera stream is 
        opened. It waits for the metadata to become available, returning the 
        metadata once it is ready. If the metadata is not available within the
        specified timeout, a `CameraNotReadyError` is raised. This error usually
        occurs when the camera is already in use by another application or if 
        the camera is not ready for any other reason.

        This function sets the `self._metadata` attribute with the obtained 
        metadata for later use which is accessible via the `metadata` property.

        Parameters
        ----------
        timeout : float
            Maximum time in seconds to wait for metadata to become available. 
            If the metadata is not available within this time, a 
            `CameraNotReadyError` is raised.

        """
        if self._capture is None:
            raise CameraNotReadyError(
                "Camera stream is not open. Call `open()` first.")

        # get metadata from the capture stream
        tStart = time.time()  # start time for the stream
        metadataTimeout = timeout  # timeout for metadata retrieval
        while time.time() - tStart < metadataTimeout:  # wait for metadata
            streamMetadata = self._capture.get_metadata()
            if streamMetadata['src_vid_size'] != (0, 0):
                break
            time.sleep(0.001)  # wait for metadata to be available
        else:
            msg = (
                "Failed to obtain stream metadata (possibly caused by a device " 
                "already in use by other application)."
            )
            logging.error(msg)
            raise CameraNotReadyError(msg)

        self._metadata = streamMetadata  # store the metadata for later use

    def open(self):
        """Open the camera stream using FFmpeg (ffpyplayer).
        
        This method should be called to open the camera stream using FFmpeg.
        It should initialize the camera and prepare it for reading frames.

        """
        if self.isOpen:
            logging.debug(
                "Camera stream for device '{}' is already open.".format(
                    self._device))
            return
        
        # get settings from the profile
        self._bufferSecs = self._bufferSecs  # default buffer size in seconds

        # if we already have a stream for this device, reuse it
        if self._device in FFPyPlayerCameraDevice._streams.keys():
            if self.isSameDevice(FFPyPlayerCameraDevice._streams[self._device]):
                self._capture = FFPyPlayerCameraDevice._streams[self._device]._capture
                logging.debug(
                    "Reusing existing camera stream for device '{}'.".format(
                        self._device))
                return

        # configure the camera stream reader
        ff_opts = {}  # ffmpeg options
        lib_opts = {}  # ffpyplayer options
        _camera = CAMERA_NULL_VALUE
        _frameRate = CAMERA_NULL_VALUE

        # setup commands for FFMPEG
        if self._captureAPI == CAMERA_API_DIRECTSHOW:  # windows
            ff_opts['f'] = 'dshow'
            _camera = 'video={}'.format(self.info['name'])
            _frameRate = self._frameRate
            if self._pixelFormat:
                ff_opts['pixel_format'] = self._pixelFormat
            if self._codecFormat:
                ff_opts['vcodec'] = self._codecFormat
        elif self._captureAPI == CAMERA_API_AVFOUNDATION:  # darwin
            ff_opts['f'] = 'avfoundation'
            ff_opts['i'] = _camera = self._device

            # handle pixel formats using FourCC
            global pixelFormatTbl
            ffmpegPixFmt = pixelFormatTbl.get(self._pixelFormat, None)

            if ffmpegPixFmt is None:
                raise FormatNotFoundError(
                    "Cannot find suitable FFMPEG pixel format for '{}'. Try a "
                    "different format or camera.".format(
                        self._pixelFormat))

            self._pixelFormat = ffmpegPixFmt
            _frameRate = self._frameRate

            # need these since hardware acceleration is not possible on Mac yet
            lib_opts['fflags'] = 'nobuffer'
            lib_opts['flags'] = 'low_delay'
            lib_opts['pixel_format'] = self._pixelFormat
            lib_opts['use_wallclock_as_timestamps'] = '1'
            # ff_opts['framedrop'] = True
            # ff_opts['fast'] = True
        elif self._captureAPI == CAMERA_API_VIDEO4LINUX2:
            ff_opts['f'] = 'v4l2'
            # ff_opts['thread_queue_size'] = 1024
            # ff_opts['preset'] = 'ultrafast'
            _camera = self._device
            _frameRate = self._frameRate
        else:
            raise RuntimeError("Unsupported camera API specified.")

        # set library options
        camWidth, camHeight = self._frameSize
        logging.info(
            "Using camera mode {}x{} at {} fps".format(
                camWidth, camHeight, _frameRate))
        
        # configure the real-time buffer size, we compute using RGB8 since this 
        # is uncompressed and represents the largest size we can expect
        self._frameSizeBytes = int(camWidth * camHeight * 3)
        framesToBufferCount = int(self._bufferSecs * float(_frameRate))
        rtBufferSize = int(self._frameSizeBytes * framesToBufferCount)
        logging.debug(
            "Setting real-time buffer size to {} bytes "
            "for {} seconds of video ({} frames @ {} fps)".format(
                rtBufferSize, 
                self._bufferSecs,
                framesToBufferCount,
                _frameRate)
        )

        # common settings across libraries
        ff_opts['low_delay'] = True  # low delay for real-time playback
        # ff_opts['framedrop'] = True
        # ff_opts['use_wallclock_as_timestamps'] = True
        ff_opts['fast'] = True
        # ff_opts['sync'] = 'ext'
        ff_opts['rtbufsize'] = str(rtBufferSize)  # set the buffer size
        ff_opts['an'] = True
        # ff_opts['infbuf'] = True  # enable infinite buffering

        # for ffpyplayer, we need to set the video size and framerate
        lib_opts['video_size'] = '{width}x{height}'.format(
            width=camWidth, height=camHeight)
        lib_opts['framerate'] = str(_frameRate)
        ff_opts['loglevel'] = 'error'
        ff_opts['nostdin'] = True

        # open the media player
        from ffpyplayer.player import MediaPlayer
        self._capture = MediaPlayer(
            _camera, 
            ff_opts=ff_opts, 
            lib_opts=lib_opts)

        # compute the frame interval, needed for generating timestamps
        self._frameInterval = 1.0 / self._frameRate 

        # obtain stream metadata, frames are valid after this succeeds
        self._obtainInitialStreamMetadata()

        # register stream in the class-level dictionary
        FFPyPlayerCameraDevice._streams[self._device] = self._capture

        if self._pollingTimerThread is None:
            self._setupAutoPolling()  # set up automatic polling of the camera stream

    def close(self):
        """Close the camera stream.
        
        This method should be called to close the camera stream and release any
        resources associated with it.

        Camera clients should unregister themselves before calling this method from 
        their own `close()` method.

        """
        if self._cameraClients:
            logging.debug(
                "Closed called for camera stream for device '{}' that has {} registered "
                "clients remaining. Keeping stream active.".format(
                    self._device, self.clientCount))
            return
            
        if self._capture is not None:
            # self._capture.set_pause(True)  # pause the stream
            self._capture.close_player()
            self._capture = None
        else:
            logging.debug(
                "Camera stream for device '{}' is already closed.".format(
                    self._device))

        self._stopAutoPolling()

        self._ptsAnchor = None
        self._frameCount = 0  # reset the frame count

    def isSameDevice(self, other):
        """
        Check if this camera device is the same as another camera device.

        Parameters
        ----------
        other : FFPyPlayerCameraDevice
            Another camera device to compare with.

        Returns
        -------
        bool
            True if both devices are the same, False otherwise.
        """
        if isinstance(other, FFPyPlayerCameraDevice):
            return self.info['device'] == other.info['device']
        elif isinstance(other, dict) and 'device' in other:
            return self.info['device'] == other['device']

    @staticmethod
    def getAvailableDevices(best=False):
        """
        Get all available devices of this type.

        Parameters
        ----------
        best : bool
            If True, return only the best available frame rate/resolution for 
            each device, rather than returning all. Best available spec is 
            chosen as the highest resolution with a frame rate above 30fps (or 
            just highest resolution, if none are over 30fps).

        Returns
        -------
        list[dict]
            List of dictionaries containing the parameters needed to initialise 
            each device.

        """
        profiles = []
        foundCameras = []  # keep track of cameras we've already seen to avoid duplicates
        # iterate through cameras
        for cams in FFPyPlayerCameraDevice.getCameras().values():
            # Skip devices with no available formats
            if not cams:
                continue

            if cams[0].name in foundCameras:
                continue  # skip duplicate camera names
            foundCameras.append(cams[0].name)
            profiles.append({
                'deviceName': cams[0].name,
                'deviceClass': "psychopy.hardware.camera.CameraDevice",
                # the camera to open, named as `__init__` takes it; profiles are
                # splatted straight into the constructor by
                # `DeviceManager.addDevice()`, so this has to be here
                'device': cams[0].name,
                # 'device': cam.index,
                # 'captureLib': cam.cameraLib, 
                # 'frameSize': cam.frameSize, 
                # 'frameRate': cam.frameRate, 
                # 'pixelFormat': cam.pixelFormat, 
                # 'codecFormat': cam.codecFormat, 
                # 'captureAPI': cam.cameraAPI
            })

            # # if requested, filter for best spec for each device
            # if best:
            #     allCams = cams.copy()
            #     lastBest = {
            #         'pixels': 0,
            #         'frameRate': 0
            #     }
            #     bestResolution = None
            #     minFrameRate = max(28, min([cam.frameRate for cam in allCams]))
            #     for cam in allCams:
            #         # summarise spec of this cam
            #         current = {
            #             'pixels': cam.frameSize[0] * cam.frameSize[1],
            #             'frameRate': cam.frameRate
            #         }
            #         # store best frame rate as a fallback
            #         if bestResolution is None or current['pixels'] > lastBest['pixels']:
            #             bestResolution = cam
            #         # if it's better than the last, set it as the only cam
            #         if current['pixels'] > lastBest['pixels'] and current['frameRate'] >= minFrameRate:
            #             cams = [cam]
            #     # if no cameras meet frame rate requirement, use one with best resolution
            #     cams = [bestResolution]
            # iterate through all (possibly filtered) cameras
            # for cam in cams:
            #     # construct a dict profile from the CameraInfo object
            #     profiles.append({
            #         'deviceName': cam.name,
            #         'deviceClass': "psychopy.hardware.camera.CameraDevice",
            #         # 'device': cam.index,
            #         # 'captureLib': cam.cameraLib, 
            #         # 'frameSize': cam.frameSize, 
            #         # 'frameRate': cam.frameRate, 
            #         # 'pixelFormat': cam.pixelFormat, 
            #         # 'codecFormat': cam.codecFormat, 
            #         # 'captureAPI': cam.cameraAPI
            #     })

        return profiles

    @staticmethod
    def getCameras(cameraLib=None):
        """Get a list of devices this interface can open.

        Parameters  
        ----------
        cameraLib : str or None
            If specified, only return cameras that can be opened with the given
            library. If `None`, return all cameras that can be opened by this
            interface. **Deprecated**: this parameter is ignored since this 
            interface only supports 'ffpyplayer'.

        Returns
        -------
        dict 
            List of objects which represent cameras that can be opened by this
            interface. Pass any of these values to `device` to open a stream.

        """
        global _cameraGetterFuncTbl
        systemName = platform.system()

        # lookup the function for the given platform
        getCamerasFunc = _cameraGetterFuncTbl.get(systemName, None)
        if getCamerasFunc is None:  # if unsupported
            raise OSError(
                "Cannot get cameras, unsupported platform '{}'.".format(
                    systemName))

        return getCamerasFunc()


class PyAVCameraDevice(CameraDevice):
    """Class providing an interface with a camera attached to the system using
    FFmpeg by way of PyAV (the `av` package).

    This is an alternative to :class:`~psychopy.hardware.camera.FFPyPlayerCameraDevice`
    which uses the same underlying FFmpeg libraries, but binds to them directly
    rather than going through `ffpyplayer`'s media player. It is the backend to
    prefer on Python versions for which `ffpyplayer` has no wheels available.

    Like the `ffpyplayer` backend, frames are pulled from the camera by a
    background thread so that capture can run at the camera's own rate
    independently of the main thread. Client objects register themselves with
    `bind()` to be handed new frames whenever the stream is polled.

    Frames are converted to RGB before leaving the capture thread and are handed
    out as `_RGBFrameAdapter` objects, which present the same interface as
    `ffpyplayer`'s images. This keeps downstream code identical for both
    backends, and is also required for safety: PyAV frames are views onto memory
    owned by the decoder, and touching one after the stream has been closed
    crashes the interpreter.

    Parameters
    ----------
    device : Any
        Camera device to open a stream with. This can be an integer index into
        the list returned by `getAvailableDevices()`, the name of the device
        (e.g. `'/dev/video0'` on Linux), or a device profile `dict`.
    frameSize : ArrayLike or None
        Resolution of the frame `(w, h)` in pixels. If `None`, the default frame
        size is used which is `(640, 480)`. The default value is `None`.
    frameRate : float or None
        Frame rate in frames per second. If `None`, the default frame rate is
        used which is `30.0`. The default value is `None`.
    pixelFormat : str or None
        Pixel format to request from the camera (e.g. `'yuyv422'`). If `None`,
        a format is chosen from the capabilities the camera reports for the
        requested frame size and rate.
    codecFormat : str or None
        Codec format to request from the camera (e.g. `'mjpeg'`), used instead
        of `pixelFormat` for compressed stream formats. If `None`, a format is
        chosen from the camera's reported capabilities.
    decoderOpts : dict or None
        Additional options to pass through to FFmpeg when opening the stream.
        These are merged over the options computed from the other parameters,
        so they can be used to override any of them. If `None`, no additional
        options are passed. The default value is `None`.
    bufferSecs : float
        Number of seconds of video to buffer in memory between polls. Frames
        captured while the buffer is full are dropped, oldest first. The default
        value is `5.0` for 5 seconds of video.
    pollingInterval : float or None
        Interval in seconds to poll the camera stream for new frames. If `None`,
        the default polling interval is used which is equal to the frame
        interval. The default value is `None`.
    readTimeout : float or None
        Maximum time in seconds to wait for data from the camera before
        checking whether the stream has been asked to close. This bounds how
        long `close()` can block for; it does not need to be short. If `None`,
        a value is derived from the frame rate. The default value is `None`.

    Examples
    --------
    Open a camera stream with PyAV and read frames from it::

        cam = PyAVCameraDevice('/dev/video0', frameSize=(640, 480),
                               frameRate=30)
        while True:
            for colorData, frameIndex, pts in cam._getFrames():
                ...  # do something with the frame
        cam.close()

    """
    _streams = {}  # open streams, keyed by device name
    backend = 'pyav'
    _captureLib = CAMERA_LIB_PYAV
    _deviceClassPath = "psychopy.hardware.camera.PyAVCameraDevice"

    # libavdevice input format to use for each capture API
    _containerFormats = {
        CAMERA_API_DIRECTSHOW: 'dshow',
        CAMERA_API_AVFOUNDATION: 'avfoundation',
        CAMERA_API_VIDEO4LINUX2: 'video4linux2'
    }

    def __init__(self,
                 device,
                 frameSize=None,
                 frameRate=None,
                 pixelFormat=None,
                 codecFormat=None,
                 decoderOpts=None,
                 bufferSecs=5.0,
                 pollingInterval=None,
                 readTimeout=None,
                 **kwargs):
        super().__init__()

        # resolve whatever we were given to a device profile
        foundProfile = None

        if isinstance(device, int):
            availableDevices = self.getAvailableDevices()
            if not 0 <= device < len(availableDevices):
                raise CameraNotFoundError(
                    "Cannot find camera with index {}, {} camera(s) are "
                    "available.".format(device, len(availableDevices)))
            device = availableDevices[device]['deviceName']

        if isinstance(device, str):
            for profile in self.getAvailableDevices():
                if profile['deviceName'] == device:
                    foundProfile = profile
                    break
        elif isinstance(device, dict):
            foundProfile = device

        if foundProfile is None:
            raise CameraNotFoundError(
                "Cannot find camera with index or name '{}'.".format(device))

        self.info = foundProfile
        self._device = self.info['deviceName']
        self._frameSize = list(frameSize) if frameSize is not None else [640, 480]
        self._frameRate = float(frameRate) if frameRate is not None else 30.0
        self._frameInterval = 1.0 / self._frameRate if self._frameRate > 0 else -1.0
        self._decoderOpts = dict(decoderOpts) if decoderOpts is not None else {}
        self._bufferSecs = float(bufferSecs)
        self._pollingInterval = \
            pollingInterval if pollingInterval is not None else self.frameInterval
        self._pollingTimerThread = None
        self._pollingLock = threading.Lock()
        self._frameCount = 0
        self._framesDropped = 0
        self._frameSizeBytes = -1

        # How long to block waiting on the camera before looping back to check
        # whether the stream has been closed. Generous by default since a
        # camera which has gone quiet for this long has stalled anyway.
        if readTimeout is None:
            readTimeout = max(1.0, 10.0 * max(self._frameInterval, 0.0))
        self._readTimeout = float(readTimeout)
        self._openTimeout = 10.0

        # pick a capture format from what the camera says it supports, falling
        # back to the first mode it offers if the requested one is not listed
        self._pixelFormat = pixelFormat
        self._codecFormat = codecFormat
        # whether the format was asked for by the caller rather than picked from
        # the camera's reported capabilities, which decides whether a format we
        # cannot translate is an error or just something to let FFmpeg settle
        self._formatIsExplicit = not (pixelFormat is None and codecFormat is None)
        if not self._formatIsExplicit:
            self._selectCaptureFormat()

        systemName = platform.system()
        if systemName == 'Darwin':
            self._captureAPI = CAMERA_API_AVFOUNDATION
        elif systemName == 'Windows':
            self._captureAPI = CAMERA_API_DIRECTSHOW
        elif systemName == 'Linux':
            self._captureAPI = CAMERA_API_VIDEO4LINUX2
        else:
            raise OSError(
                "Unsupported platform '{}', cannot select capture API.".format(
                    systemName))

        # PyAV state, all created in `open()`
        self._container = None  # av.container.InputContainer
        self._videoStream = None  # av video stream being captured
        self._frameIterator = None  # generator yielding decoded frames
        self._timeBase = None  # stream time base, for turning PTS into seconds
        # cached colour converter, reused across frames since building the
        # `swscale` context per frame costs an order of magnitude more than the
        # conversion itself
        self._reformatter = None

        # capture thread state
        self._readerThread = None
        self._stopReaderEvent = threading.Event()
        self._pausedEvent = threading.Event()
        self._streamStartTime = -1.0

        # Frames waiting to be picked up by `_getFrames()`. Bounded so that a
        # client which stops polling cannot grow this without limit; the oldest
        # frames are dropped once it is full.
        self._frameQueue = collections.deque(maxlen=1)
        self._frameLock = threading.Lock()

        # keep track of clients attached to this camera stream
        self._cameraClients = []

        self.open()  # open the camera stream

    def _selectCaptureFormat(self):
        """Choose a pixel/codec format from the camera's reported capabilities.

        Sets `_pixelFormat` and `_codecFormat` to the formats belonging to the
        mode which matches the requested frame size and rate, or to those of the
        first mode the camera reports if there is no exact match. Both are left
        as `None` if the camera reports no capabilities at all, in which case
        FFmpeg is left to pick a format itself.

        """
        try:
            allCaps = self.getDeviceCapabilities(self._device)
        except Exception as err:
            logging.warning(
                "Could not query capabilities for camera '{}' ({}), letting "
                "FFmpeg select a capture format.".format(self._device, err))
            return

        if not allCaps:
            logging.warning(
                "Camera '{}' reports no capture formats, letting FFmpeg select "
                "one.".format(self._device))
            return

        for cap in allCaps:
            if (list(cap['frameSize']) == list(self._frameSize) and
                    cap['frameRate'] == self._frameRate):
                break
        else:
            cap = allCaps[0]
            logging.warning(
                "Camera '{}' does not report a {}x{}@{}fps mode, using "
                "'{}' instead.".format(
                    self._device,
                    self._frameSize[0], self._frameSize[1], self._frameRate,
                    cap.get('codecFormat') or cap.get('pixelFormat')))

        self._pixelFormat = cap['pixelFormat']
        self._codecFormat = cap['codecFormat']

    # --------------------------------------------------------------------------
    # Stream properties
    #

    @property
    def index(self):
        """Camera index (`int`). This is the enumerated index of this camera.
        """
        return self.info.get('index', -1)

    @property
    def name(self):
        """Camera name (`str`). This is the camera name retrieved by the OS.
        """
        return self._device

    @property
    def captureAPI(self):
        """Camera API in use (`str`), one of `'AVFoundation'`, `'DirectShow'`
        or `'Video4Linux2'`.
        """
        return self._captureAPI

    @property
    def pollingInterval(self):
        """Interval in seconds between polls of the camera stream (`float`).
        """
        return self._pollingInterval

    @property
    def frameSize(self):
        """Get the frame size of the camera stream.

        Returns
        -------
        tuple
            Frame size as (width, height). Returns `None` if the camera stream
            is not open.

        """
        if self._container is None:
            return None

        return tuple(self._frameSize)

    @property
    def frameRate(self):
        """Get the frame rate of the camera stream.

        Returns
        -------
        float
            Frame rate in frames per second. Returns `None` if the camera stream
            is not open.

        """
        if self.info is None:
            return None

        return self._frameRate

    @property
    def frameInterval(self):
        """Get the frame interval of the camera stream.

        Returns
        -------
        float
            Frame interval in seconds. Returns `-1.0` if the frame rate is not
            known.

        """
        if self.info is None:
            return -1.0

        return 1.0 / self._frameRate if self._frameRate > 0 else -1.0

    @property
    def frameCount(self):
        """Number of frames captured since the stream was opened (`int`).
        """
        return self._frameCount

    @property
    def framesDropped(self):
        """Number of frames dropped because the buffer was full (`int`).

        Frames are dropped when `_poll()` is not called often enough to keep up
        with the camera. A non-zero value here means the stream is being polled
        less often than it is producing frames.

        """
        return self._framesDropped

    @property
    def pixelFormat(self):
        """Pixel format the camera is streaming in (`str`).
        """
        return self._pixelFormat if self._pixelFormat is not None else ''

    @property
    def codecFormat(self):
        """Codec the camera is streaming with (`str`).
        """
        return self._codecFormat if self._codecFormat is not None else ''

    @property
    def streamTime(self):
        """Time in seconds since the camera stream was opened (`float`).

        Returns `-1.0` if the stream is not open. This uses the same time base
        as the presentation timestamps handed out with frames.

        """
        if self._streamStartTime < 0:
            return -1.0

        return time.monotonic() - self._streamStartTime

    @property
    def isOpen(self):
        """Check if the camera stream is open.

        Returns
        -------
        bool
            `True` if the camera stream is open, `False` otherwise.

        """
        return self._container is not None

    @property
    def isReady(self):
        """`True` if the camera stream is open and producing frames (`bool`).
        """
        return self.isOpen and self._frameCount > 0

    @property
    def paused(self):
        """Check if the camera stream is paused.

        Returns
        -------
        bool
            `True` if the camera stream is paused, `False` otherwise.

        """
        if self._container is None:
            raise PlayerNotAvailableError(
                "Camera stream is not open. Call `open()` first.")

        return self._pausedEvent.is_set()

    @paused.setter
    def paused(self, value):
        self.setPause(value)

    def setPause(self, pause):
        """Pause or resume the camera stream.

        While paused the stream keeps being read from the camera, but the
        frames are discarded rather than buffered for clients. The camera's own
        buffers therefore cannot overflow while the stream is paused.

        Parameters
        ----------
        pause : bool
            If `True`, pause the camera stream. If `False`, resume the camera
            stream.

        """
        if self._container is None:
            raise PlayerNotAvailableError(
                "Camera stream is not open. Call `open()` first.")

        if pause:
            self._pausedEvent.set()
            with self._frameLock:
                self._frameQueue.clear()
        else:
            self._pausedEvent.clear()

    # --------------------------------------------------------------------------
    # Opening, reading and closing the stream
    #

    def _getOpenOptions(self):
        """Build the FFmpeg input URL and options for the requested settings.

        Returns
        -------
        tuple
            The container format name to open the device with (`str`), the URL
            identifying the device (`str`), and the options to pass to FFmpeg
            (`dict`).

        """
        camWidth, camHeight = self._frameSize
        containerFormat = self._containerFormats[self._captureAPI]

        # FFmpeg wants the frame rate as a number it can parse as a rational,
        # so drop the trailing '.0' integral rates would otherwise carry
        frameRate = self._frameRate
        if float(frameRate).is_integer():
            frameRate = int(frameRate)

        openOpts = {
            'video_size': '{width}x{height}'.format(
                width=camWidth, height=camHeight),
            'framerate': str(frameRate)}

        pixelFormat = self._pixelFormat
        codecFormat = self._codecFormat

        if self._captureAPI == CAMERA_API_DIRECTSHOW:
            deviceURL = 'video={}'.format(self.info.get('name', self._device))

            # Configure the real-time buffer, computed using RGB8 since that is
            # uncompressed and so the largest size we can expect a frame to be.
            self._frameSizeBytes = int(camWidth * camHeight * 3)
            framesToBufferCount = int(self._bufferSecs * self._frameRate)
            rtBufferSize = int(self._frameSizeBytes * framesToBufferCount)
            openOpts['rtbufsize'] = str(rtBufferSize)
            logging.debug(
                "Setting real-time buffer size to {} bytes for {} seconds of "
                "video ({} frames @ {} fps)".format(
                    rtBufferSize, self._bufferSecs, framesToBufferCount,
                    self._frameRate))

            if not _isNullFormat(codecFormat):
                openOpts['vcodec'] = codecFormat
            elif not _isNullFormat(pixelFormat):
                openOpts['pixel_format'] = pixelFormat
        elif self._captureAPI == CAMERA_API_AVFOUNDATION:
            deviceURL = str(self._device)

            # AVFoundation reports formats as FourCC codes, which need mapping
            # onto the names FFmpeg knows them by
            if not _isNullFormat(pixelFormat):
                global pixelFormatTbl
                ffmpegPixFmt = pixelFormatTbl.get(pixelFormat, None)
                if ffmpegPixFmt is not None:
                    openOpts['pixel_format'] = ffmpegPixFmt
                elif self._formatIsExplicit:
                    raise FormatNotFoundError(
                        "Cannot find suitable FFMPEG pixel format for '{}'. "
                        "Try a different format or camera.".format(pixelFormat))
                else:
                    # the format came from the camera's own capability list, so
                    # leave FFmpeg to negotiate one rather than refusing to open
                    logging.warning(
                        "No FFmpeg pixel format is known for the AVFoundation "
                        "format '{}', letting FFmpeg select one.".format(
                            pixelFormat))
        elif self._captureAPI == CAMERA_API_VIDEO4LINUX2:
            deviceURL = self._device

            # v4l2 selects the capture format with `input_format`, which takes
            # either a pixel format or a codec name (e.g. 'mjpeg'). The names
            # `v4l2-ctl` reports are FourCC codes, which have to be translated
            # to the ones FFmpeg uses.
            captureFormat = codecFormat if not _isNullFormat(codecFormat) \
                else pixelFormat
            if not _isNullFormat(captureFormat):
                global v4l2FormatTbl
                captureFormat = str(captureFormat).strip().lower()
                captureFormat = v4l2FormatTbl.get(captureFormat, captureFormat)
                openOpts['input_format'] = captureFormat
        else:
            raise RuntimeError("Unsupported camera API specified.")

        # let the caller override anything we computed above
        openOpts.update(self._decoderOpts)

        return containerFormat, deviceURL, openOpts

    def open(self):
        """Open the camera stream using PyAV.

        This opens the camera device, works out the format it is actually
        streaming in, and starts the background thread which reads frames from
        it.

        """
        if self.isOpen:
            logging.debug(
                "Camera stream for device '{}' is already open.".format(
                    self._device))
            return

        try:
            import av
        except ImportError:
            raise ImportError(
                "The `av` (PyAV) library is required to open camera streams "
                "with `cameraLib='pyav'`. Install it with `pip install av`.")

        # Refuse to open a camera a second time rather than fight the previous
        # stream for it. Multiple clients share one stream by binding to the
        # same device object, see `bind()`.
        openStream = PyAVCameraDevice._streams.get(self._device, None)
        if openStream is not None and openStream is not self and openStream.isOpen:
            raise CameraNotReadyError(
                "Camera '{}' has already been opened by another "
                "`PyAVCameraDevice`. Use that device object and bind extra "
                "clients to it with `bind()` instead of opening the camera "
                "again.".format(self._device))

        containerFormat, deviceURL, openOpts = self._getOpenOptions()

        logging.info(
            "Opening camera '{}' with PyAV using the '{}' input at {}x{} "
            "@{}fps".format(
                deviceURL, containerFormat, self._frameSize[0],
                self._frameSize[1], self._frameRate))
        logging.debug("PyAV camera options: {}".format(openOpts))

        try:
            self._container = av.open(
                deviceURL,
                format=containerFormat,
                options=openOpts,
                timeout=(self._openTimeout, self._readTimeout))
        except av.FFmpegError as err:
            self._container = None
            msg = (
                "Failed to open camera '{}' with PyAV: {} (possibly caused by "
                "a device already in use by another application, or by a "
                "format the camera does not support).".format(
                    self._device, err))
            logging.error(msg)
            raise CameraNotReadyError(msg)

        videoStream = next(
            (s for s in self._container.streams if s.type == 'video'), None)

        if videoStream is None:
            self._container.close()
            self._container = None
            raise CameraNotReadyError(
                "Camera '{}' does not provide a video stream.".format(
                    self._device))

        # use multi-threaded decoding where available, which matters for
        # cameras streaming compressed formats such as MJPEG
        try:
            videoStream.thread_type = 'AUTO'
        except Exception:
            pass  # not fatal if the codec doesn't support threaded decoding

        self._videoStream = videoStream
        self._timeBase = videoStream.time_base

        # Take the settings the camera actually gave us rather than the ones we
        # asked for, since FFmpeg silently substitutes the nearest it can do.
        codecContext = videoStream.codec_context
        if codecContext.width and codecContext.height:
            self._frameSize = [codecContext.width, codecContext.height]
        if codecContext.format is not None:
            self._pixelFormat = codecContext.format.name
        if codecContext.codec is not None:
            self._codecFormat = codecContext.codec.name

        actualRate = videoStream.average_rate or videoStream.guessed_rate
        if actualRate:
            self._frameRate = float(actualRate)
        self._frameInterval = \
            1.0 / self._frameRate if self._frameRate > 0 else -1.0

        camWidth, camHeight = self._frameSize
        self._frameSizeBytes = int(camWidth * camHeight * 3)
        logging.info(
            "Camera '{}' opened, streaming {}x{} @{}fps as '{}'".format(
                self._device, camWidth, camHeight, self._frameRate,
                self._pixelFormat))

        # size the frame buffer to hold `bufferSecs` worth of frames
        bufferedFrameCount = max(1, int(self._bufferSecs * self._frameRate))
        self._frameQueue = collections.deque(maxlen=bufferedFrameCount)
        self._framesDropped = 0
        self._frameCount = 0

        from av.video.reformatter import VideoReformatter
        self._reformatter = VideoReformatter()

        self._frameIterator = self._container.decode(video=0)
        self._streamStartTime = time.monotonic()
        self._ptsAnchor = None  # re-anchor the stream clock on the next frame

        self._startReaderThread()

        # register the stream in the class-level dictionary
        PyAVCameraDevice._streams[self._device] = self

        if self._pollingTimerThread is None:
            self._setupAutoPolling()

    def _startReaderThread(self):
        """Start the background thread which reads frames from the camera.
        """
        self._stopReaderEvent.clear()
        self._readerThread = threading.Thread(
            target=self._readFramesAsync,
            name='PsychoPy-PyAVCamera-{}'.format(self._device),
            daemon=True)
        self._readerThread.start()

    def _stopReaderThread(self):
        """Stop the background reader thread and wait for it to finish.

        The thread may be blocked waiting on the camera, so this can take up to
        `readTimeout` seconds to return.

        """
        if self._readerThread is None:
            return

        self._stopReaderEvent.set()
        self._readerThread.join(timeout=self._readTimeout + 5.0)

        if self._readerThread.is_alive():
            logging.error(
                "Timed out waiting for the capture thread for camera '{}' to "
                "stop.".format(self._device))

        self._readerThread = None

    def _readFramesAsync(self):
        """Read frames from the camera until asked to stop.

        This runs in the background thread started by `_startReaderThread()`.
        Frames are converted to RGB here, off the main thread, and buffered for
        `_getFrames()` to pick up.

        """
        import av

        while not self._stopReaderEvent.is_set():
            try:
                frame = next(self._frameIterator)
            except StopIteration:
                logging.debug(
                    "Camera '{}' reached the end of its stream.".format(
                        self._device))
                break
            except (av.error.ExitError, av.error.TimeoutError):
                # the read timed out, loop back around to check whether we have
                # been asked to stop
                continue
            except av.FFmpegError as err:
                logging.error(
                    "Error reading from camera '{}': {}".format(
                        self._device, err))
                break

            if self._pausedEvent.is_set():
                del frame  # discard, but keep reading so the camera drains
                continue

            tReceived = time.monotonic()
            if frame.pts is not None and self._timeBase is not None:
                curPts = float(frame.pts * self._timeBase)
            else:  # camera gave us no timestamp, generate one
                curPts = self._frameCount * self._frameInterval
            absTime = self._absTimeForPTS(curPts, tReceived)

            # Convert here rather than on the main thread, and copy the pixels
            # out of the decoder's buffers while doing so. Frames handed to
            # clients must not reference decoder memory, since that is freed
            # when the stream closes.
            colorData = _RGBFrameAdapter(
                self._reformatter.reformat(frame, format='rgb24').to_ndarray())
            del frame

            with self._frameLock:
                if len(self._frameQueue) == self._frameQueue.maxlen:
                    self._framesDropped += 1
                self._frameQueue.append(
                    (colorData, self._frameCount, curPts, absTime))

            self._frameCount += 1

    def _getFrames(self):
        """Get the frames captured since the last call to this method.

        This is called by the `_poll()` method to collect frames from the
        capture thread. It takes everything buffered since the last call and
        dispatches it to bound clients via the `_onNewFrames()` method.

        Returns
        -------
        list
            List of tuples containing the frames and their timestamps. Each
            tuple contains (frame, frame index, timestamp).

        """
        if self._container is None:
            raise PlayerNotAvailableError(
                "Camera stream is not open. Call `open()` first.")

        with self._pollingLock:
            with self._frameLock:
                recentFrames = list(self._frameQueue)
                self._frameQueue.clear()

        self._onNewFrames(recentFrames)  # dispatch to clients any new frames

        return recentFrames

    def close(self):
        """Close the camera stream.

        This stops the capture thread and releases the camera. Camera clients
        should unregister themselves with `unbind()` before calling this from
        their own `close()` method; the stream is left running while any client
        is still bound to it.

        """
        if self._cameraClients:
            logging.debug(
                "Closed called for camera stream for device '{}' that has {} "
                "registered clients remaining. Keeping stream active.".format(
                    self._device, self.clientCount))
            return

        if self._container is None:
            logging.debug(
                "Camera stream for device '{}' is already closed.".format(
                    self._device))
            return

        self._stopReaderThread()
        self._stopAutoPolling()

        # Order matters here. The decoder owns the memory the stream, iterator
        # and reformatter refer to, so all of them have to be released before
        # the container is closed or the interpreter crashes when they are
        # finalised later.
        self._frameIterator = None
        self._videoStream = None
        self._reformatter = None
        self._timeBase = None

        try:
            self._container.close()
        except Exception as err:
            logging.error(
                "Error closing camera '{}': {}".format(self._device, err))
        finally:
            self._container = None

        with self._frameLock:
            self._frameQueue.clear()

        PyAVCameraDevice._streams.pop(self._device, None)

        self._streamStartTime = -1.0
        self._ptsAnchor = None
        self._frameCount = 0  # reset the frame count

    def isSameDevice(self, other):
        """
        Check if this camera device is the same as another camera device.

        Parameters
        ----------
        other : PyAVCameraDevice or dict
            Another camera device, or a device profile, to compare with.

        Returns
        -------
        bool
            True if both refer to the same physical device, False otherwise.
        """
        if isinstance(other, PyAVCameraDevice):
            return self._device == other._device
        elif isinstance(other, dict):
            return self._device == other.get('deviceName', None)

        return False

    def __del__(self):
        """Release the camera if the interface is garbage collected.
        """
        try:
            self._cameraClients = []  # nothing left to keep the stream open for
            self.close()
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # Device enumeration
    #

    @staticmethod
    def getCameras(cameraLib=None):
        """Get a list of devices this interface can open.

        Parameters
        ----------
        cameraLib : str or None
            Ignored, present for signature compatibility with the other camera
            interfaces. This interface only supports `'pyav'`.

        Returns
        -------
        dict
            Mapping where camera names (`str`) are keys and values are an array
            of `CameraInfo` objects describing the modes that camera supports.

        """
        return getCameras(cameraLib=CAMERA_LIB_PYAV)

    @staticmethod
    def getAvailableDevices(best=False):
        """
        Get all available devices of this type.

        Parameters
        ----------
        best : bool
            Unused, retained for compatibility with the other camera
            interfaces.

        Returns
        -------
        list[dict]
            List of dictionaries containing the parameters needed to initialise
            each device.

        """
        profiles = []
        foundCameras = []  # cameras already seen, to avoid duplicates

        for cams in PyAVCameraDevice.getCameras().values():
            if not cams:  # skip devices with no available formats
                continue

            if cams[0].name in foundCameras:
                continue  # skip duplicate camera names
            foundCameras.append(cams[0].name)

            profiles.append({
                'deviceName': cams[0].name,
                'deviceClass': PyAVCameraDevice._deviceClassPath,
                # the camera to open, named as `__init__` takes it; profiles are
                # splatted straight into the constructor by
                # `DeviceManager.addDevice()`, so this has to be here
                'device': cams[0].name})

        return profiles


class OpenCVCameraDevice(CameraDevice):
    """Class providing an interface with a camera attached to the system using
    OpenCV (the `cv2` package).

    This is an alternative to the FFmpeg based interfaces
    (:class:`~psychopy.hardware.camera.FFPyPlayerCameraDevice` and
    :class:`~psychopy.hardware.camera.PyAVCameraDevice`) which talks to the
    platform's own capture API through OpenCV instead. It is the backend to
    reach for when neither `ffpyplayer` nor `av` can be installed, or when the
    experiment is already using OpenCV for computer vision work and would
    rather not pull in a second capture library.

    Like the other backends, frames are pulled from the camera by a background
    thread so that capture runs at the camera's own rate independently of the
    main thread. This matters more here than it looks: an experiment's main
    thread spends most of every display frame blocked inside `flip()` waiting
    for the vertical retrace, and a camera recording faster than the display
    refreshes would otherwise have nowhere to put the frames it produced in the
    meantime. OpenCV keeps only a handful of buffers, so those frames would be
    lost. Client objects register themselves with `bind()` to be handed new
    frames whenever the stream is polled.

    Frames are converted from OpenCV's native BGR to RGB before leaving the
    capture thread and are handed out as `_RGBFrameAdapter` objects, which
    present the same interface as `ffpyplayer`'s images. This keeps downstream
    code identical for all backends.

    Parameters
    ----------
    device : Any
        Camera device to open a stream with. This can be an integer index into
        the list returned by `getAvailableDevices()`, the name of the device
        (e.g. `'/dev/video0'` on Linux), or a device profile `dict`.
    frameSize : ArrayLike or None
        Resolution of the frame `(w, h)` in pixels. If `None`, the default frame
        size is used which is `(640, 480)`. The default value is `None`.
    frameRate : float or None
        Frame rate in frames per second. If `None`, the default frame rate is
        used which is `30.0`. The default value is `None`.
    pixelFormat : str or None
        Pixel format to request from the camera (e.g. `'yuyv422'`). If `None`,
        a format is chosen from the capabilities the camera reports for the
        requested frame size and rate.
    codecFormat : str or None
        Codec format to request from the camera (e.g. `'mjpeg'`), used instead
        of `pixelFormat` for compressed stream formats. Asking for a compressed
        format is usually what gets a camera to deliver its higher frame rates
        and resolutions over USB. If `None`, a format is chosen from the
        camera's reported capabilities.
    captureProps : dict or None
        Additional `cv2.CAP_PROP_*` properties to set on the capture, as a
        mapping of property name (e.g. `'CAP_PROP_AUTOFOCUS'`) or value onto the
        value to set it to. These are applied after the frame size, rate and
        format requested above, so they can be used to override any of them. If
        `None`, no additional properties are set. The default value is `None`.
    bufferSecs : float
        Number of seconds of video to buffer in memory between polls. Frames
        captured while the buffer is full are dropped, oldest first. The default
        value is `5.0` for 5 seconds of video.
    pollingInterval : float or None
        Interval in seconds to poll the camera stream for new frames. If `None`,
        the default polling interval is used which is equal to the frame
        interval. The default value is `None`.
    readTimeout : float or None
        Maximum time in seconds to wait for the capture thread to return when
        the stream is closed. OpenCV gives no way to interrupt a read which is
        waiting on the camera, so this bounds how long `close()` blocks before
        giving up on the thread. If `None`, a value is derived from the frame
        rate. The default value is `None`.

    Examples
    --------
    Open a camera stream with OpenCV and read frames from it::

        cam = OpenCVCameraDevice('/dev/video0', frameSize=(640, 480),
                                 frameRate=30)
        while True:
            for colorData, frameIndex, pts, absTime in cam._getFrames():
                ...  # do something with the frame
        cam.close()

    """
    _streams = {}  # open streams, keyed by device name
    backend = 'opencv'
    _captureLib = CAMERA_LIB_OPENCV
    _deviceClassPath = "psychopy.hardware.camera.OpenCVCameraDevice"

    # Name of the OpenCV capture backend to use for each capture API. These are
    # looked up on the `cv2` module when the stream is opened rather than
    # stored as values, so that this table costs nothing to define on systems
    # where OpenCV is not installed.
    _captureBackends = {
        CAMERA_API_DIRECTSHOW: 'CAP_DSHOW',
        CAMERA_API_AVFOUNDATION: 'CAP_AVFOUNDATION',
        CAMERA_API_VIDEO4LINUX2: 'CAP_V4L2'
    }

    # How many failed reads in a row mean the camera has gone away rather than
    # simply being slow to produce the next frame.
    _maxReadFailures = 60

    def __init__(self,
                 device,
                 frameSize=None,
                 frameRate=None,
                 pixelFormat=None,
                 codecFormat=None,
                 captureProps=None,
                 bufferSecs=5.0,
                 pollingInterval=None,
                 readTimeout=None,
                 **kwargs):
        super().__init__()

        # resolve whatever we were given to a device profile
        foundProfile = None

        if isinstance(device, int):
            availableDevices = self.getAvailableDevices()
            if not 0 <= device < len(availableDevices):
                raise CameraNotFoundError(
                    "Cannot find camera with index {}, {} camera(s) are "
                    "available.".format(device, len(availableDevices)))
            device = availableDevices[device]['deviceName']

        if isinstance(device, str):
            for profile in self.getAvailableDevices():
                if profile['deviceName'] == device:
                    foundProfile = profile
                    break
        elif isinstance(device, dict):
            foundProfile = device

        if foundProfile is None:
            raise CameraNotFoundError(
                "Cannot find camera with index or name '{}'.".format(device))

        self.info = foundProfile
        self._device = self.info['deviceName']
        self._frameSize = list(frameSize) if frameSize is not None else [640, 480]
        self._frameRate = float(frameRate) if frameRate is not None else 30.0
        self._frameInterval = 1.0 / self._frameRate if self._frameRate > 0 else -1.0
        self._captureProps = dict(captureProps) if captureProps is not None else {}
        self._bufferSecs = float(bufferSecs)
        # remembered so that a polling interval derived from the frame rate can
        # be recomputed if the camera turns out to run at a different one
        self._pollingIntervalRequested = pollingInterval
        self._pollingInterval = \
            pollingInterval if pollingInterval is not None else self.frameInterval
        self._pollingTimerThread = None
        self._pollingLock = threading.Lock()
        self._frameCount = 0
        self._framesDropped = 0
        self._frameSizeBytes = -1

        # How long `close()` waits for the capture thread to come back from the
        # camera. OpenCV offers no way to interrupt a read in progress, so this
        # is the only bound on it.
        if readTimeout is None:
            readTimeout = max(1.0, 10.0 * max(self._frameInterval, 0.0))
        self._readTimeout = float(readTimeout)
        # how long to wait before trying again after a failed read, short
        # enough that a camera which is simply slow to start is not missed
        self._readRetryInterval = 0.05

        # pick a capture format from what the camera says it supports, falling
        # back to the first mode it offers if the requested one is not listed
        self._pixelFormat = pixelFormat
        self._codecFormat = codecFormat
        # whether the format was asked for by the caller rather than picked from
        # the camera's reported capabilities
        self._formatIsExplicit = not (pixelFormat is None and codecFormat is None)
        if not self._formatIsExplicit:
            self._selectCaptureFormat()

        systemName = platform.system()
        if systemName == 'Darwin':
            self._captureAPI = CAMERA_API_AVFOUNDATION
        elif systemName == 'Windows':
            self._captureAPI = CAMERA_API_DIRECTSHOW
        elif systemName == 'Linux':
            self._captureAPI = CAMERA_API_VIDEO4LINUX2
        else:
            raise OSError(
                "Unsupported platform '{}', cannot select capture API.".format(
                    systemName))

        # index OpenCV knows this camera by, worked out when the stream opens
        self._captureIndex = -1

        # OpenCV state, created in `open()`
        self._capture = None  # cv2.VideoCapture
        self._fourCC = ''  # capture format the camera settled on

        # Whether the camera reports usable presentation timestamps. Most do
        # not, in which case frames are timestamped by when they arrived, see
        # `_ptsForGrabbedFrame()`.
        self._usePosMsec = True
        self._lastPosMsec = -1.0

        # capture thread state
        self._readerThread = None
        self._stopReaderEvent = threading.Event()
        self._pausedEvent = threading.Event()
        self._streamStartTime = -1.0

        # Frames waiting to be picked up by `_getFrames()`. Bounded so that a
        # client which stops polling cannot grow this without limit; the oldest
        # frames are dropped once it is full.
        self._frameQueue = collections.deque(maxlen=1)
        self._frameLock = threading.Lock()

        # keep track of clients attached to this camera stream
        self._cameraClients = []

        self.open()  # open the camera stream

    def _selectCaptureFormat(self):
        """Choose a pixel/codec format from the camera's reported capabilities.

        Sets `_pixelFormat` and `_codecFormat` to the formats belonging to the
        mode which matches the requested frame size and rate, or to those of the
        first mode the camera reports if there is no exact match. Both are left
        as `None` if the camera reports no capabilities at all, in which case
        OpenCV is left to pick a format itself.

        """
        try:
            allCaps = self.getDeviceCapabilities(self._device)
        except Exception as err:
            logging.warning(
                "Could not query capabilities for camera '{}' ({}), letting "
                "OpenCV select a capture format.".format(self._device, err))
            return

        # Entries without a frame size come from a camera we could not query
        # properly, and say nothing about what it can be asked for.
        allCaps = [cap for cap in allCaps if cap.get('frameSize') is not None]

        if not allCaps:
            logging.warning(
                "Camera '{}' reports no capture formats, letting OpenCV select "
                "one.".format(self._device))
            return

        for cap in allCaps:
            if (list(cap['frameSize']) == list(self._frameSize) and
                    cap['frameRate'] == self._frameRate):
                break
        else:
            cap = allCaps[0]
            logging.warning(
                "Camera '{}' does not report a {}x{}@{}fps mode, using "
                "'{}' instead.".format(
                    self._device,
                    self._frameSize[0], self._frameSize[1], self._frameRate,
                    cap.get('codecFormat') or cap.get('pixelFormat')))

        self._pixelFormat = cap['pixelFormat']
        self._codecFormat = cap['codecFormat']

    @classmethod
    def _captureIndexFor(cls, deviceName):
        """Get the index OpenCV identifies a camera by.

        OpenCV addresses cameras by an index into its own enumeration rather
        than by name. On Linux that index is the number in the device file's
        name, which is how cameras are named here. Elsewhere the position in the
        enumerated device list is the best guess available, since both
        DirectShow and AVFoundation hand OpenCV their devices in the same order
        they are enumerated in.

        Parameters
        ----------
        deviceName : str
            Name of the camera, as `getAvailableDevices()` reports it.

        Returns
        -------
        int
            Index to open the camera with.

        """
        if (platform.system() == 'Linux' and
                deviceName.startswith(VIDEO_DEVICE_ROOT_LINUX)):
            digits = ''.join(
                c for c in os.path.basename(deviceName) if c.isdigit())
            if digits:
                return int(digits)

        for devIndex, profile in enumerate(cls.getAvailableDevices()):
            if profile['deviceName'] == deviceName:
                return devIndex

        raise CameraNotFoundError(
            "Cannot work out which camera OpenCV knows '{}' as.".format(
                deviceName))

    def _requestedFourCC(self):
        """Get the FourCC code to ask the camera to stream in.

        OpenCV asks a driver for a capture format by its FourCC code rather
        than by name, so the format names the rest of this module deals in have
        to be translated. Which format is used matters for more than colour
        fidelity: cameras commonly offer their higher resolutions and frame
        rates only over a compressed format such as MJPEG, and will silently
        drop to a few frames per second if asked for raw frames instead.

        Returns
        -------
        str or None
            FourCC code to request, or `None` if the format is unknown or was
            not specified, in which case the driver's own choice is kept.

        """
        global openCVFourCCTbl

        # a compressed format, where there is one, is what the camera is
        # actually streaming; the pixel format only describes what comes out of
        # the decoder
        for formatName in (self._codecFormat, self._pixelFormat):
            if _isNullFormat(formatName):
                continue

            formatName = str(formatName).strip().lower()
            fourCC = openCVFourCCTbl.get(formatName, None)
            if fourCC is not None:
                return fourCC

            if len(formatName) == 4:  # already a FourCC code, e.g. from V4L2
                return formatName.upper()

            logging.warning(
                "No FourCC code known for capture format '{}', letting the "
                "camera driver choose one.".format(formatName))

        return None

    @staticmethod
    def _decodeFourCC(value):
        """Turn the number OpenCV reports a FourCC code as into its characters.

        Parameters
        ----------
        value : float or int
            Value of the `CAP_PROP_FOURCC` property.

        Returns
        -------
        str
            The FourCC code as four characters, or an empty string if the
            camera did not report one.

        """
        value = int(value)
        if value <= 0:
            return ''

        return ''.join(chr((value >> (8 * i)) & 0xFF) for i in range(4)).strip()

    # --------------------------------------------------------------------------
    # Stream properties
    #

    @property
    def index(self):
        """Camera index (`int`). This is the enumerated index of this camera.
        """
        return self.info.get('index', -1)

    @property
    def name(self):
        """Camera name (`str`). This is the camera name retrieved by the OS.
        """
        return self._device

    @property
    def captureAPI(self):
        """Camera API in use (`str`), one of `'AVFoundation'`, `'DirectShow'`
        or `'Video4Linux2'`.
        """
        return self._captureAPI

    @property
    def pollingInterval(self):
        """Interval in seconds between polls of the camera stream (`float`).
        """
        return self._pollingInterval

    @property
    def frameSize(self):
        """Get the frame size of the camera stream.

        Returns
        -------
        tuple
            Frame size as (width, height). Returns `None` if the camera stream
            is not open.

        """
        if self._capture is None:
            return None

        return tuple(self._frameSize)

    @property
    def frameRate(self):
        """Get the frame rate of the camera stream.

        Returns
        -------
        float
            Frame rate in frames per second. Returns `None` if the camera stream
            is not open.

        """
        if self.info is None:
            return None

        return self._frameRate

    @property
    def frameInterval(self):
        """Get the frame interval of the camera stream.

        Returns
        -------
        float
            Frame interval in seconds. Returns `-1.0` if the frame rate is not
            known.

        """
        if self.info is None:
            return -1.0

        return 1.0 / self._frameRate if self._frameRate > 0 else -1.0

    @property
    def frameCount(self):
        """Number of frames captured since the stream was opened (`int`).
        """
        return self._frameCount

    @property
    def framesDropped(self):
        """Number of frames dropped because the buffer was full (`int`).

        Frames are dropped when `_poll()` is not called often enough to keep up
        with the camera. A non-zero value here means the stream is being polled
        less often than it is producing frames.

        """
        return self._framesDropped

    @property
    def pixelFormat(self):
        """Pixel format the camera is streaming in (`str`).
        """
        return self._pixelFormat if self._pixelFormat is not None else ''

    @property
    def codecFormat(self):
        """Codec the camera is streaming with (`str`).
        """
        return self._codecFormat if self._codecFormat is not None else ''

    @property
    def streamTime(self):
        """Time in seconds since the camera stream was opened (`float`).

        Returns `-1.0` if the stream is not open. This uses the same time base
        as the presentation timestamps handed out with frames.

        """
        if self._streamStartTime < 0:
            return -1.0

        return time.monotonic() - self._streamStartTime

    @property
    def isOpen(self):
        """Check if the camera stream is open.

        Returns
        -------
        bool
            `True` if the camera stream is open, `False` otherwise.

        """
        return self._capture is not None

    @property
    def isReady(self):
        """`True` if the camera stream is open and producing frames (`bool`).
        """
        return self.isOpen and self._frameCount > 0

    @property
    def paused(self):
        """Check if the camera stream is paused.

        Returns
        -------
        bool
            `True` if the camera stream is paused, `False` otherwise.

        """
        if self._capture is None:
            raise PlayerNotAvailableError(
                "Camera stream is not open. Call `open()` first.")

        return self._pausedEvent.is_set()

    @paused.setter
    def paused(self, value):
        self.setPause(value)

    def setPause(self, pause):
        """Pause or resume the camera stream.

        While paused the stream keeps being read from the camera, but the
        frames are discarded rather than buffered for clients. The camera's own
        buffers therefore cannot overflow while the stream is paused.

        Parameters
        ----------
        pause : bool
            If `True`, pause the camera stream. If `False`, resume the camera
            stream.

        """
        if self._capture is None:
            raise PlayerNotAvailableError(
                "Camera stream is not open. Call `open()` first.")

        if pause:
            self._pausedEvent.set()
            with self._frameLock:
                self._frameQueue.clear()
        else:
            self._pausedEvent.clear()

    # --------------------------------------------------------------------------
    # Opening, reading and closing the stream
    #

    def _applyCaptureSettings(self, capture):
        """Ask the camera for the requested format, size and frame rate.

        Whatever the camera actually gives us is taken back off it afterwards
        and recorded, since drivers substitute the nearest mode they can manage
        without reporting an error.

        Parameters
        ----------
        capture : cv2.VideoCapture
            Open capture to configure.

        """
        import cv2

        # The format goes first: changing it resets the frame size and rate on
        # a good number of drivers, which would throw away anything set before
        # it.
        fourCC = self._requestedFourCC()
        if fourCC is not None:
            if not capture.set(
                    cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourCC)):
                logging.warning(
                    "Camera '{}' would not stream in '{}', using whatever "
                    "format it defaults to.".format(self._device, fourCC))

        capture.set(cv2.CAP_PROP_FRAME_WIDTH, float(self._frameSize[0]))
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, float(self._frameSize[1]))
        capture.set(cv2.CAP_PROP_FPS, float(self._frameRate))

        # anything the caller wants set beyond that, applied last so it can
        # override the settings above
        for propName, propValue in self._captureProps.items():
            propId = getattr(cv2, propName, None) if isinstance(
                propName, str) else propName
            if propId is None:
                logging.warning(
                    "OpenCV has no capture property named '{}', "
                    "ignoring.".format(propName))
                continue

            if not capture.set(propId, float(propValue)):
                logging.warning(
                    "Camera '{}' would not accept capture property '{}' = "
                    "{}.".format(self._device, propName, propValue))

    def _readBackCaptureSettings(self, capture):
        """Record the format the camera actually settled on.

        Parameters
        ----------
        capture : cv2.VideoCapture
            Open capture to read the settings back off.

        """
        global v4l2FormatTbl

        import cv2

        actualWidth = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        actualHeight = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if actualWidth > 0 and actualHeight > 0:
            if [actualWidth, actualHeight] != list(self._frameSize):
                logging.warning(
                    "Camera '{}' gave a frame size of {}x{} rather than the "
                    "{}x{} requested.".format(
                        self._device, actualWidth, actualHeight,
                        self._frameSize[0], self._frameSize[1]))
            self._frameSize = [actualWidth, actualHeight]

        actualRate = float(capture.get(cv2.CAP_PROP_FPS))
        if actualRate > 0:
            if abs(actualRate - self._frameRate) > 0.01:
                logging.warning(
                    "Camera '{}' gave a frame rate of {} fps rather than the "
                    "{} fps requested.".format(
                        self._device, actualRate, self._frameRate))
            self._frameRate = actualRate

        self._frameInterval = \
            1.0 / self._frameRate if self._frameRate > 0 else -1.0
        if self._pollingIntervalRequested is None:
            self._pollingInterval = self._frameInterval

        self._fourCC = self._decodeFourCC(capture.get(cv2.CAP_PROP_FOURCC))
        if self._fourCC:
            # report the format under the name the rest of the module uses for
            # it, where we have one for it
            formatName = v4l2FormatTbl.get(
                self._fourCC.lower(), self._fourCC.lower())
            if formatName in ('mjpeg', 'h264', 'hevc'):
                self._codecFormat = formatName
                self._pixelFormat = None
            else:
                self._pixelFormat = formatName
                self._codecFormat = None

    def open(self):
        """Open the camera stream using OpenCV.

        This opens the camera device, works out the format it is actually
        streaming in, and starts the background thread which reads frames from
        it.

        """
        if self.isOpen:
            logging.debug(
                "Camera stream for device '{}' is already open.".format(
                    self._device))
            return

        try:
            import cv2
        except ImportError:
            raise ImportError(
                "The `opencv-python` library is required to open camera "
                "streams with `cameraLib='opencv'`. Install it with "
                "`pip install opencv-python`.")

        # Refuse to open a camera a second time rather than fight the previous
        # stream for it. Multiple clients share one stream by binding to the
        # same device object, see `bind()`.
        openStream = OpenCVCameraDevice._streams.get(self._device, None)
        if openStream is not None and openStream is not self and openStream.isOpen:
            raise CameraNotReadyError(
                "Camera '{}' has already been opened by another "
                "`OpenCVCameraDevice`. Use that device object and bind extra "
                "clients to it with `bind()` instead of opening the camera "
                "again.".format(self._device))

        self._captureIndex = self._captureIndexFor(self._device)
        apiPreference = getattr(
            cv2, self._captureBackends[self._captureAPI], cv2.CAP_ANY)

        logging.info(
            "Opening camera '{}' (OpenCV index {}) with the '{}' backend at "
            "{}x{} @{}fps".format(
                self._device, self._captureIndex,
                self._captureBackends[self._captureAPI],
                self._frameSize[0], self._frameSize[1], self._frameRate))

        try:
            capture = cv2.VideoCapture(self._captureIndex, apiPreference)
        except cv2.error as err:
            raise CameraNotReadyError(
                "Failed to open camera '{}' with OpenCV: {}".format(
                    self._device, err))

        if not capture.isOpened():
            capture.release()
            raise CameraNotReadyError(
                "Failed to open camera '{}' with OpenCV (possibly caused by a "
                "device already in use by another application, or one which "
                "this OpenCV build has no backend for).".format(self._device))

        self._applyCaptureSettings(capture)
        self._readBackCaptureSettings(capture)

        camWidth, camHeight = self._frameSize
        self._frameSizeBytes = int(camWidth * camHeight * 3)
        logging.info(
            "Camera '{}' opened, streaming {}x{} @{}fps as '{}'".format(
                self._device, camWidth, camHeight, self._frameRate,
                self._fourCC or CAMERA_UNKNOWN_VALUE))

        # size the frame buffer to hold `bufferSecs` worth of frames
        bufferedFrameCount = max(1, int(self._bufferSecs * self._frameRate))
        self._frameQueue = collections.deque(maxlen=bufferedFrameCount)
        self._framesDropped = 0
        self._frameCount = 0

        self._capture = capture
        self._streamStartTime = time.monotonic()
        self._ptsAnchor = None  # re-anchor the stream clock on the next frame
        self._usePosMsec = True
        self._lastPosMsec = -1.0

        self._startReaderThread()

        # register the stream in the class-level dictionary
        OpenCVCameraDevice._streams[self._device] = self

        if self._pollingTimerThread is None:
            self._setupAutoPolling()

    def _startReaderThread(self):
        """Start the background thread which reads frames from the camera.
        """
        self._stopReaderEvent.clear()
        self._readerThread = threading.Thread(
            target=self._readFramesAsync,
            name='PsychoPy-OpenCVCamera-{}'.format(self._device),
            daemon=True)
        self._readerThread.start()

    def _stopReaderThread(self):
        """Stop the background reader thread and wait for it to finish.

        The thread may be blocked waiting on the camera, and OpenCV gives no
        way to interrupt that, so this can take up to `readTimeout` seconds to
        return.

        """
        if self._readerThread is None:
            return

        self._stopReaderEvent.set()
        self._readerThread.join(timeout=self._readTimeout + 5.0)

        if self._readerThread.is_alive():
            logging.error(
                "Timed out waiting for the capture thread for camera '{}' to "
                "stop.".format(self._device))

        self._readerThread = None

    def _ptsForGrabbedFrame(self, capture, tReceived):
        """Get the presentation timestamp for the frame just grabbed.

        Cameras are supposed to report where each frame sits in the stream
        through `CAP_PROP_POS_MSEC`, but most webcams report nothing usable
        there, so this falls back to timing frames by when they arrived. The
        fallback is decided once, on the first frame that fails to produce a
        sane timestamp, rather than per frame, so that a stream cannot end up
        with its frames timed against two different clocks.

        Parameters
        ----------
        capture : cv2.VideoCapture
            Capture the frame was grabbed from.
        tReceived : float
            Local time in seconds, from `time.monotonic()`, at which the frame
            was grabbed.

        Returns
        -------
        float
            Presentation timestamp of the frame, in seconds since the stream
            was opened.

        """
        import cv2

        if self._usePosMsec:
            try:
                posMsec = float(capture.get(cv2.CAP_PROP_POS_MSEC))
            except Exception:
                posMsec = -1.0

            if posMsec > 0.0 and posMsec > self._lastPosMsec:
                self._lastPosMsec = posMsec
                return posMsec / 1000.0

            logging.debug(
                "Camera '{}' does not report usable frame timestamps, timing "
                "frames by when they arrive instead.".format(self._device))
            self._usePosMsec = False

        return tReceived - self._streamStartTime

    def _frameToRGB(self, frame):
        """Convert a frame as OpenCV read it into RGB.

        Parameters
        ----------
        frame : numpy.ndarray
            Frame as returned by `cv2.VideoCapture.retrieve()`.

        Returns
        -------
        numpy.ndarray
            The frame as RGB24, with shape `(height, width, 3)`.

        """
        import cv2

        if frame.ndim == 2:  # monochrome camera
            return cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

        if frame.shape[2] == 4:  # some cameras hand over an alpha channel
            return cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def _readFramesAsync(self):
        """Read frames from the camera until asked to stop.

        This runs in the background thread started by `_startReaderThread()`.
        Frames are converted to RGB here, off the main thread, and buffered for
        `_getFrames()` to pick up.

        """
        failedReads = 0

        while not self._stopReaderEvent.is_set():
            capture = self._capture
            if capture is None:  # stream closed from under us
                break

            # `grab()` returns as soon as the camera has handed a frame over,
            # before anything is decoded, so the time taken here is as close as
            # OpenCV lets us get to when the frame was actually captured
            try:
                grabbed = capture.grab()
            except Exception as err:
                logging.error(
                    "Error reading from camera '{}': {}".format(
                        self._device, err))
                break

            tReceived = time.monotonic()

            if not grabbed:
                failedReads += 1
                if failedReads >= self._maxReadFailures:
                    logging.error(
                        "Camera '{}' stopped delivering frames after {} failed "
                        "reads in a row.".format(
                            self._device, failedReads))
                    break

                # the camera may simply be slow to come up, so back off rather
                # than spinning on a device which is not producing yet
                self._stopReaderEvent.wait(self._readRetryInterval)
                continue

            failedReads = 0
            curPts = self._ptsForGrabbedFrame(capture, tReceived)

            if self._pausedEvent.is_set():
                # keep draining the camera so its buffers cannot overflow, but
                # do not pay for decoding frames nobody will see
                continue

            try:
                retrieved, frame = capture.retrieve()
            except Exception as err:
                logging.error(
                    "Error decoding a frame from camera '{}': {}".format(
                        self._device, err))
                break

            if not retrieved or frame is None:
                continue

            absTime = self._absTimeForPTS(curPts, tReceived)

            # Convert here rather than on the main thread. Frames come off
            # OpenCV as BGR, which nothing downstream expects, and the main
            # thread is typically blocked waiting on the display's vertical
            # retrace while this runs.
            colorData = _RGBFrameAdapter(self._frameToRGB(frame))
            del frame

            with self._frameLock:
                if len(self._frameQueue) == self._frameQueue.maxlen:
                    self._framesDropped += 1
                self._frameQueue.append(
                    (colorData, self._frameCount, curPts, absTime))

            self._frameCount += 1

    def _getFrames(self):
        """Get the frames captured since the last call to this method.

        This is called by the `_poll()` method to collect frames from the
        capture thread. It takes everything buffered since the last call and
        dispatches it to bound clients via the `_onNewFrames()` method.

        Returns
        -------
        list
            List of tuples containing the frames and their timestamps. Each
            tuple contains (frame, frame index, pts, absTime).

        """
        if self._capture is None:
            raise PlayerNotAvailableError(
                "Camera stream is not open. Call `open()` first.")

        with self._pollingLock:
            with self._frameLock:
                recentFrames = list(self._frameQueue)
                self._frameQueue.clear()

        self._onNewFrames(recentFrames)  # dispatch to clients any new frames

        return recentFrames

    def close(self):
        """Close the camera stream.

        This stops the capture thread and releases the camera. Camera clients
        should unregister themselves with `unbind()` before calling this from
        their own `close()` method; the stream is left running while any client
        is still bound to it.

        """
        if self._cameraClients:
            logging.debug(
                "Closed called for camera stream for device '{}' that has {} "
                "registered clients remaining. Keeping stream active.".format(
                    self._device, self.clientCount))
            return

        if self._capture is None:
            logging.debug(
                "Camera stream for device '{}' is already closed.".format(
                    self._device))
            return

        self._stopReaderThread()
        self._stopAutoPolling()

        # Hold on to the capture until both threads which touch it have
        # stopped, since releasing it from under a read in progress crashes
        # some backends.
        capture, self._capture = self._capture, None
        try:
            capture.release()
        except Exception as err:
            logging.error(
                "Error closing camera '{}': {}".format(self._device, err))

        with self._frameLock:
            self._frameQueue.clear()

        OpenCVCameraDevice._streams.pop(self._device, None)

        self._streamStartTime = -1.0
        self._ptsAnchor = None
        self._frameCount = 0  # reset the frame count

    def isSameDevice(self, other):
        """
        Check if this camera device is the same as another camera device.

        Parameters
        ----------
        other : OpenCVCameraDevice or dict
            Another camera device, or a device profile, to compare with.

        Returns
        -------
        bool
            True if both refer to the same physical device, False otherwise.
        """
        if isinstance(other, OpenCVCameraDevice):
            return self._device == other._device
        elif isinstance(other, dict):
            return self._device == other.get('deviceName', None)

        return False

    def __del__(self):
        """Release the camera if the interface is garbage collected.
        """
        try:
            self._cameraClients = []  # nothing left to keep the stream open for
            self.close()
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # Device enumeration
    #

    @staticmethod
    def getCameras(cameraLib=None):
        """Get a list of devices this interface can open.

        Parameters
        ----------
        cameraLib : str or None
            Ignored, present for signature compatibility with the other camera
            interfaces. This interface only supports `'opencv'`.

        Returns
        -------
        dict
            Mapping where camera names (`str`) are keys and values are an array
            of `CameraInfo` objects describing the modes that camera supports.

        """
        videoDevices = getCameras(cameraLib=CAMERA_LIB_OPENCV)

        if videoDevices or platform.system() != 'Linux':
            return videoDevices

        # Cameras are enumerated on Linux with `v4l2-ctl`, which OpenCV does
        # not otherwise need. Fall back to the device files themselves so that
        # cameras are still selectable on systems without it, accepting that
        # nothing can be said about the formats they support.
        import glob
        devFiles = sorted(
            glob.glob(os.path.join(VIDEO_DEVICE_ROOT_LINUX, 'video*')))

        if not devFiles:
            return videoDevices

        logging.warning(
            "Could not query camera formats (is `v4l2-ctl` installed?), "
            "falling back to listing video devices in '{}'. Some of these may "
            "not be cameras.".format(VIDEO_DEVICE_ROOT_LINUX))

        for devIndex, devFile in enumerate(devFiles):
            videoDevices[devFile] = [CameraInfo(
                index=devIndex,
                name=devFile,
                pixelFormat=CAMERA_UNKNOWN_VALUE,
                codecFormat=CAMERA_UNKNOWN_VALUE,
                frameSize=None,
                frameRate=CAMERA_NULL_FRAMERATE,
                cameraAPI=CAMERA_API_VIDEO4LINUX2,
                cameraLib=CAMERA_LIB_OPENCV)]

        return videoDevices

    @staticmethod
    def getAvailableDevices(best=False):
        """
        Get all available devices of this type.

        Parameters
        ----------
        best : bool
            Unused, retained for compatibility with the other camera
            interfaces.

        Returns
        -------
        list[dict]
            List of dictionaries containing the parameters needed to initialise
            each device.

        """
        profiles = []
        foundCameras = []  # cameras already seen, to avoid duplicates

        for cams in OpenCVCameraDevice.getCameras().values():
            if not cams:  # skip devices with no available formats
                continue

            if cams[0].name in foundCameras:
                continue  # skip duplicate camera names
            foundCameras.append(cams[0].name)

            profiles.append({
                'deviceName': cams[0].name,
                'deviceClass': OpenCVCameraDevice._deviceClassPath,
                # the camera to open, named as `__init__` takes it; profiles are
                # splatted straight into the constructor by
                # `DeviceManager.addDevice()`, so this has to be here
                'device': cams[0].name})

        return profiles


# Base class for all camera interfaces, kept under its own name because the
# `CameraDevice` name below is taken by the legacy alias for the `ffpyplayer`
# interface.
BaseCameraDevice = CameraDevice

# class name alias for legacy support
CameraDevice = CameraInterface = FFPyPlayerCameraDevice

# Camera interface to use for each supported capture library.
_cameraDeviceLibTbl = {
    CAMERA_LIB_FFPYPLAYER: FFPyPlayerCameraDevice,
    CAMERA_LIB_PYAV: PyAVCameraDevice,
    CAMERA_LIB_OPENCV: OpenCVCameraDevice
}


def getCameraDeviceClass(cameraLib=None):
    """Get the camera interface class which uses the given capture library.

    Parameters
    ----------
    cameraLib : str or None
        Capture library the interface should use, one of `'ffpyplayer'`,
        `'pyav'` or `'opencv'`. If `None`, the library named by
        `camera.backend` is used.

    Returns
    -------
    type
        Subclass of `BaseCameraDevice` which opens camera streams using
        `cameraLib`.

    """
    global backend, _cameraDeviceLibTbl

    if cameraLib is None:
        cameraLib = backend

    try:
        return _cameraDeviceLibTbl[cameraLib]
    except KeyError:
        raise ValueError(
            "Invalid value for parameter `cameraLib`, expected one of {}, got "
            "'{}'.".format(
                ", ".join(repr(k) for k in _cameraDeviceLibTbl), cameraLib))


class _OpenCVMovieWriter:
    """Movie file writer which encodes frames with OpenCV on a thread of its
    own.

    OpenCV's `VideoWriter` has no notion of presentation timestamps: it writes
    frames one after another and the container is told they are spaced at a
    fixed rate, so a recording only lines up with real time if exactly one
    frame is written per frame interval. Cameras rarely oblige, dropping below
    their nominal rate whenever auto-exposure or the USB bus asks them to, so
    each frame is instead placed on the output's fixed grid according to when
    it was captured. Gaps left by a camera running slow are filled by repeating
    the previous frame, and frames arriving closer together than the output
    rate can represent are dropped. Both keep the recording the same length as
    the wall clock time it was captured over, which is what keeps it lined up
    with the audio track it is later merged with.

    Encoding runs on its own thread because the thread submitting frames is
    usually the experiment's main thread, which spends most of every display
    frame blocked inside `flip()` waiting for the vertical retrace. A camera
    recording faster than the display refreshes hands over several frames per
    poll, and encoding those inline would routinely push the main thread past
    the retrace it was waiting for, dropping a display frame.

    Parameters
    ----------
    filename : str
        File to write the video to, should include the extension.
    frameSize : ArrayLike
        Size `(w, h)` of the frames to be written, in pixels. Frames which do
        not match this are rescaled, since the container's frame size is fixed
        once the file is opened.
    frameRate : float
        Rate in frames per second the file is written at.
    fourcc : str
        FourCC code of the codec to encode with. Defaults to `'mp4v'`
        (MPEG-4 Part 2), which every build of OpenCV can write into an MP4
        container; `'avc1'` gives smaller files but is missing from many
        builds for licensing reasons.
    queueSecs : float
        Seconds of video the encoder is allowed to fall behind by before frames
        start being dropped. This bounds both the memory the backlog can take
        up and how long closing the file can block for.
    maxGapSecs : float
        Longest gap in the recording, in seconds, that will be filled by
        repeating frames. A gap longer than this means the camera stalled, and
        is logged and left unfilled rather than padded out with thousands of
        copies of the same frame.

    """
    def __init__(self, filename, frameSize, frameRate, fourcc='mp4v',
                 queueSecs=10.0, maxGapSecs=10.0):
        import cv2

        self._filename = filename
        self._frameSize = (int(frameSize[0]), int(frameSize[1]))
        self._frameRate = float(frameRate) if frameRate > 0 else 30.0
        self._closed = False

        self._writer = cv2.VideoWriter(
            filename,
            cv2.VideoWriter_fourcc(*fourcc),
            self._frameRate,
            self._frameSize)

        if not self._writer.isOpened():
            self._writer.release()
            self._writer = None
            raise RuntimeError(
                "OpenCV could not open '{}' for writing with the '{}' codec at "
                "{}x{} @{} fps.".format(
                    filename, fourcc, self._frameSize[0], self._frameSize[1],
                    self._frameRate))

        self._queue = queue.Queue(
            maxsize=max(1, int(queueSecs * self._frameRate)))
        self._maxGapFrames = max(1, int(round(maxGapSecs * self._frameRate)))

        # How long `close()` waits for the encoder to work through its backlog.
        # The queue is bounded, so the worst case is encoding `queueSecs` of
        # video, which is allowed to take rather longer than real time.
        self._closeTimeout = max(30.0, queueSecs * 3.0)

        self._lastIndex = -1  # output slot the last frame written landed on
        self._lastFrame = None  # repeated to fill gaps, see the class docstring
        # How far into the recording the last frame handed over sat, whether or
        # not it reached the file. `_padToEnd()` needs this to know how long the
        # recording was meant to be.
        self._lastSubmittedElapsed = 0.0
        self._framesWritten = 0
        # Frames dropped are counted separately by cause, which also keeps each
        # counter to a single thread: frames too close together are dropped by
        # the encoder thread, frames arriving with the queue full by whichever
        # thread submitted them.
        self._framesTooClose = 0
        self._framesNotQueued = 0
        # An encoder which cannot keep up drops every frame from then on, so
        # the warning for it is logged once and then only every so often,
        # rather than once per frame.
        self._dropWarningInterval = max(1, int(round(self._frameRate * 10.0)))
        self._nextDropWarning = 1  # drop count the next warning is logged at

        self._writerThread = threading.Thread(
            target=self._writeFramesAsync,
            name='PsychoPy-OpenCVMovieWriter',
            daemon=True)
        self._writerThread.start()

        logging.debug(
            "Opened movie file writer using OpenCV, writing {}x{} @{} fps as "
            "'{}' to '{}'".format(
                self._frameSize[0], self._frameSize[1], self._frameRate,
                fourcc, filename))

    @property
    def isOpen(self):
        """`True` while the file is open for writing (`bool`).
        """
        return not self._closed

    @property
    def framesWritten(self):
        """Number of frames written to the file so far (`int`).

        This includes frames repeated to fill gaps left by the camera, so it
        counts the frames in the file rather than the frames captured.

        """
        return self._framesWritten

    @property
    def framesDropped(self):
        """Number of submitted frames which did not reach the file (`int`).

        Frames are dropped either because the camera delivered them faster than
        the output's frame rate can represent, or because the encoder fell far
        enough behind to fill its queue.

        """
        return self._framesTooClose + self._framesNotQueued

    def write(self, colorData, elapsed):
        """Hand a frame over to the encoder.

        This returns as soon as the frame is queued; the conversion and
        encoding happen on the writer's own thread.

        Parameters
        ----------
        colorData : _RGBFrameAdapter or numpy.ndarray
            Frame to write, in RGB.
        elapsed : float
            Time in seconds between the start of the recording and the capture
            of this frame, which is what decides where it lands in the file.

        Returns
        -------
        bool
            `True` if the frame was queued, `False` if it was dropped because
            the encoder is too far behind or the file has been closed.

        """
        if self._closed:
            return False

        if elapsed > self._lastSubmittedElapsed:
            self._lastSubmittedElapsed = elapsed

        try:
            self._queue.put_nowait((colorData, elapsed))
        except queue.Full:
            # The encoder cannot keep up with the camera. The gap this leaves
            # is filled by repeating the previous frame, so the recording keeps
            # its timing and only loses the content of this frame.
            self._framesNotQueued += 1
            if self._framesNotQueued >= self._nextDropWarning:
                self._nextDropWarning = \
                    self._framesNotQueued + self._dropWarningInterval
                logging.warning(
                    "The OpenCV movie writer is not keeping up with the "
                    "camera, dropping frames ({} dropped so far). Try a "
                    "smaller frame size, a lower frame rate, or a codec which "
                    "is cheaper to encode.".format(self._framesNotQueued))
            return False

        return True

    def _writeFramesAsync(self):
        """Encode queued frames until asked to stop.

        This runs on the thread started by the constructor. It returns once the
        sentinel `close()` puts on the queue comes around, which is only after
        every frame queued before it has been written.

        """
        while True:
            item = self._queue.get()
            if item is None:  # sentinel, no more frames are coming
                self._padToEnd()
                break

            try:
                self._writeFrame(*item)
            except Exception as err:
                logging.error(
                    "Error writing frame {} to movie file '{}': {}".format(
                        self._framesWritten, self._filename, err))

    def _writeFrame(self, colorData, elapsed):
        """Place a single frame on the output's frame grid and encode it.

        Parameters
        ----------
        colorData : _RGBFrameAdapter or numpy.ndarray
            Frame to write, in RGB.
        elapsed : float
            Time in seconds between the start of the recording and the capture
            of this frame.

        """
        import cv2

        if hasattr(colorData, 'to_ndarray'):
            colorData = colorData.to_ndarray(format='rgb24')

        frame = cv2.cvtColor(colorData, cv2.COLOR_RGB2BGR)

        frameHeight, frameWidth = frame.shape[:2]
        if (frameWidth, frameHeight) != self._frameSize:
            # the container's frame size was fixed when the file was opened, so
            # anything else has to be made to fit
            frame = cv2.resize(
                frame, self._frameSize, interpolation=cv2.INTER_AREA)

        # where this frame belongs in a file whose frames are evenly spaced
        targetIndex = int(round(elapsed * self._frameRate))

        if targetIndex <= self._lastIndex:
            # The camera delivered this frame within the interval already
            # covered by the last one written, so a fixed rate file has nowhere
            # to put it. Keep it as the frame to repeat, since it is the most
            # recent picture we have of what the camera is seeing.
            self._framesTooClose += 1
            self._lastFrame = frame
            return

        gapFrames = targetIndex - self._lastIndex - 1
        if gapFrames > 0 and self._lastFrame is not None:
            if gapFrames > self._maxGapFrames:
                logging.error(
                    "The camera produced no frames for {:.2f} seconds, longer "
                    "than this writer will pad over. The recording will be "
                    "{:.2f} seconds shorter than the time it was captured "
                    "over, and will no longer line up with the audio "
                    "track.".format(
                        gapFrames / self._frameRate,
                        (gapFrames - self._maxGapFrames) / self._frameRate))
                gapFrames = self._maxGapFrames

            for _ in range(gapFrames):
                self._writer.write(self._lastFrame)
                self._framesWritten += 1

        self._writer.write(frame)
        self._framesWritten += 1
        self._lastIndex = targetIndex
        self._lastFrame = frame

    def _padToEnd(self):
        """Pad the file out to cover the whole of the recording.

        A gap left by dropped frames is normally closed by the next frame which
        does reach the file, but nothing follows the last one. If the encoder
        was still behind when the recording stopped, the file would end early
        and the tail of the audio track would have no video against it, so the
        final gap is filled the same way as any other.

        """
        if self._lastFrame is None:  # nothing was ever written
            return

        endIndex = int(round(self._lastSubmittedElapsed * self._frameRate))
        gapFrames = endIndex - self._lastIndex
        if gapFrames <= 0:  # the last frame submitted was also the last written
            return

        if gapFrames > self._maxGapFrames:
            logging.error(
                "The last {:.2f} seconds of the recording were dropped before "
                "they could be encoded. The video will be shorter than the "
                "audio recorded alongside it by about that much.".format(
                    (gapFrames - self._maxGapFrames) / self._frameRate))
            gapFrames = self._maxGapFrames

        logging.debug(
            "Padding the end of '{}' with {} repeated frame(s) to cover the "
            "whole recording.".format(self._filename, gapFrames))

        for _ in range(gapFrames):
            self._writer.write(self._lastFrame)
            self._framesWritten += 1

        self._lastIndex += gapFrames

    def close(self):
        """Finish encoding and close the file.

        This blocks until every frame handed over has been written, so that
        nothing captured before the recording stopped is lost. Calling it more
        than once does nothing.

        """
        if self._closed:
            return

        self._closed = True  # stop `write()` adding to a queue being drained

        if self._writerThread is not None:
            try:
                self._queue.put(None, timeout=self._closeTimeout)
            except queue.Full:
                logging.error(
                    "Timed out waiting for the OpenCV movie writer to work "
                    "through its backlog, the end of the recording may be "
                    "missing.")

            self._writerThread.join(timeout=self._closeTimeout)
            if self._writerThread.is_alive():
                logging.error(
                    "Timed out waiting for the OpenCV movie writer to finish "
                    "encoding, the end of the recording may be missing.")

            self._writerThread = None

        if self._writer is not None:
            try:
                self._writer.release()
            except Exception as err:
                logging.error(
                    "Error closing the movie file '{}': {}".format(
                        self._filename, err))

            self._writer = None

        logging.debug(
            "Closed movie file writer using OpenCV, wrote {} frames to '{}' "
            "({} frames arrived too close together to be written, {} were "
            "dropped because the encoder could not keep up)".format(
                self._framesWritten, self._filename, self._framesTooClose,
                self._framesNotQueued))

        if self._framesNotQueued:
            logging.warning(
                "The OpenCV movie writer could not keep up with the camera and "
                "dropped {} frame(s) from '{}'. The recording is still the "
                "right length, but those frames show the picture before "
                "them.".format(self._framesNotQueued, self._filename))

    def __del__(self):
        """Flush and close the file if the writer is garbage collected.
        """
        try:
            self.close()
        except Exception:
            pass


class Camera:
    """Class for displaying and recording video from a USB/PCI connected camera.

    This class is capable of opening, recording, and saving camera video streams
    to disk. Camera stream reading/writing is done in a separate thread, 
    allowing capture to occur in the background while the main thread is free to 
    perform other tasks. This allows for capture to occur at higher frame rates
    than the display refresh rate. Audio recording is also supported if a 
    microphone interface is provided, where recording will be synchronized with 
    the video stream (as best as possible). Video and audio can be saved to disk 
    either as a single file or as separate files.

    Parameters
    ----------
    device : str or int
        Camera to open a stream with. If the ID is not valid, an error will be
        raised when `open()` is called. Value can be a string or number. String
        values are platform-dependent: a DirectShow URI or camera name on
        Windows, or a camera name/index on MacOS. Specifying a number (>=0) is a
        platform-independent means of selecting a camera. PsychoPy enumerates
        possible camera devices and makes them selectable without explicitly
        having the name of the cameras attached to the system. Use caution when
        specifying an integer, as the same index may not reference the same
        camera every time.
    mic : :class:`~psychopy.sound.microphone.Microphone`, None or False
        Microphone to record audio samples from during recording. Pass `None`
        to use the first microphone available, or `False` for no audio at all.
        The microphone input device must not be in use when `record()` is 
        called. The audio
        track will be merged with the video upon calling `save()`. Make sure 
        that `Microphone.maxRecordingSize` is specified to a reasonable value to 
        prevent the audio track from being truncated. Specifying a microphone
        adds some latency to starting and stopping camera recording due to the 
        added overhead involved with synchronizing the audio and video streams.
    frameRate : int or None
        Frame rate to record the camera stream at. If `None`, the camera's
        default frame rate will be used.
    frameSize : tuple or None
        Size (width, height) of the camera stream frames to record. If `None`,
        the camera's default frame size will be used. 
    cameraLib : str
        Interface library (backend) to use for accessing the camera, one of
        `'ffpyplayer'`, `'pyav'` or `'opencv'`. The first two use FFmpeg
        underneath but bind to it differently; `'pyav'` is the one to use on
        Python versions for which `ffpyplayer` provides no wheels. `'opencv'`
        talks to the platform's capture API through OpenCV instead, which is
        worth reaching for when neither FFmpeg binding can be installed or when
        the experiment is using OpenCV for computer vision work anyway; note
        that it gives less control over how the video is encoded. If `None`, the
        default library recommended by the PsychoPy developers will be used.
        Switching camera libraries could help resolve issues with camera
        compatibility. More camera libraries may be installed via extension
        packages.
    bufferSecs : float
        Size of the real-time camera stream buffer specified in seconds. This 
        will tell the library to allocate a buffer that can hold enough 
        frames to cover the specified number of seconds of video. This should
        be large enough to cover the time it takes to process frames in the
        main thread.
    win : :class:`~psychopy.visual.Window` or None
        Optional window associated with this camera. Some functionality may
        require an OpenGL context for presenting frames to the screen. If you 
        are not planning to display the camera stream, this parameter can be
        safely ignored.
    name : str
        Label for the camera for logging purposes.
    keepFrames : int
        Number of frames to keep in memory for the camera stream. Calling 
        `getVideoFrames()` will return the most recent `keepFrames` frames from
        the camera stream. If `keepFrames` is set to `0`, no frames will be kept
        in memory and the camera stream will not be buffered. This is useful if 
        the user desires to access raw frame data from the camera stream.
    latencyBias : float
        Latency bias to correct for asychrony between the camera and the
        microphone. This is the amount of time in seconds to add to the
        microphone recording start time to shift the audio track to match 
        corresponding events in the video stream. This is needed for some
        cameras whose drivers do not accurately report timestamps for camera 
        frames. Positive values will shift the audio track forward in time, and 
        negative values will shift backwards.
    usageMode : str
        Usage mode hint for the camera aquisition. This with enable 
        optimizations for specific applications that will improve performance 
        and reduce memory usage. The default value is 'video', which is suitable 
        for recording video streams with audio efficently. The 'cv' mode is for 
        computer vision applications where frames from the camera stream are 
        processed in real-time (e.g. object detection, tracking, etc.) and the 
        video is not being saved to disk. Audio will not be recorded in this
        mode even if a microphone is provided. Frames are available as soon as
        the camera is open in 'cv' mode, without calling `record()` first, so a
        live view can be shown straight away. In 'video' mode frames are kept
        only while a recording is in progress, since that is what they are
        captured for.

    Examples
    --------
    Opening a camera stream and closing it::

        camera = Camera(device=0)
        camera.open()  # exception here on invalid camera
        camera.close()

    Recording 5 seconds of video and saving it to disk::

        cam = Camera(0)
        cam.open()
        cam.record()  # starts recording

        while cam.recordingTime < 5.0:  # record for 5 seconds
            if event.getKeys('q'):
                break
            cam.update()

        cam.stop()  # stops recording
        cam.save('myVideo.mp4')
        cam.close()
    
    Providing a microphone as follows enables audio recording::

        mic = Microphone(0)
        cam = Camera(0, mic=mic)
    
    Overriding the default frame rate and size (if `cameraLib` supports it)::

        cam = Camera(0, frameRate=30, frameSize=(640, 480), cameraLib=u'opencv')

    Showing a live view of the camera on screen. Pass the window the frames are
    to be drawn to, then hand the camera to an `ImageStim` as its image. In
    `'cv'` usage mode the stream is live as soon as the camera is open, so no
    recording is needed just to see it::

        cam = Camera(0, win=win, usageMode='cv')
        cam.open()

        # the stim pulls the most recent frame each time it is drawn
        camView = visual.ImageStim(win, image=cam, size=cam.frameSize)

        while not event.getKeys('q'):
            camView.draw()
            win.flip()

        cam.close()

    """
    def __init__(self, device=0, mic=None, cameraLib=u'ffpyplayer',
                 frameRate=None, frameSize=None, bufferSecs=4, win=None,
                 name='cam', keepFrames=5, usageMode='video'):
        # add attributes for setters
        self.__dict__.update(
            {'_device': None,
             '_captureThread': None,
             '_mic': None,
             '_outFile': None,
             '_mode': u'video',
             '_frameRate': None,
             '_frameRateFrac': None,
             '_frameSize': None,
             '_size': None,
             '_cameraLib': u''})
        
        if cameraLib is None:
            cameraLib = backend
        self._cameraLib = cameraLib

        # The device this camera was asked for, kept so that the capture
        # device can be resolved again if `open()` is called after `close()`
        # has released it.
        self._deviceSpec = {
            'device': device,
            'frameRate': frameRate,
            'frameSize': frameSize,
            'bufferSecs': bufferSecs}

        # find (or create) the device which does the actual capturing
        self._capture = None
        self._resolveCaptureDevice()

        # handle microphone
        self.mic = None
        if mic is False or usageMode == CAMERA_MODE_CV:
            # `False` explicitly asks for no audio, and CV mode never records it
            self.mic = None
        elif isinstance(mic, MicrophoneDevice):
            # if given a device object, use it
            self.mic = mic
        elif isinstance(mic, Microphone):
            # if given a Microphone, use its device
            self.mic = mic.device
        elif mic is None:
            # if given None, get the first available device
            for name, obj in DeviceManager.getInitialisedDevices(MicrophoneDevice).items():
                self.mic = obj
                break
            # if there are none, set one up
            if self.mic is None:
                for profile in MicrophoneDevice.getAvailableDevices():
                    self.mic = DeviceManager.addDevice(**profile)
                    break
        elif isinstance(mic, str) and DeviceManager.getDevice(mic) is not None:
            # if given a device name, get the device
            self.mic = DeviceManager.getDevice(mic)
        else:
            # anything else, try to initialise a new device from params
            self.mic = MicrophoneDevice(
                index=mic
            )

        # current camera frame since the start of recording
        self.status = NOT_STARTED
        self._startRecOffset = 0  # offset in samples 
        self._recording = False
        self._bufferSecs = float(bufferSecs)
        self._lastFrame = None  # use None to avoid imports for ImageStim
        self._keepFrames = keepFrames  # number of frames to keep in memory
        self._frameCount = 0  # number of frames read from the camera stream
        self._frameStore = collections.deque(maxlen=keepFrames)
        self._usageMode = usageMode  # usage mode for the camera
        self._unsaved = False  # is there any footage not saved?

        # other information
        self.name = name
        # timestamp data
        self._streamTime = 0.0
        # store win (unused but needs to be set/got safely for parity with JS)
        self._win = None

        # recording properties
        self._isStarted = False  # is the stream started?
        self._audioReady = False
        self._videoReady = False

        self._latencyBias = 0.0  # latency bias in seconds

        # `_recordingRequested` says a recording has been asked for, while
        # `_isRecording` says frames are actually being kept. They differ while
        # waiting for the camera to reach `_tRecordingStartRequested`.
        #
        # `_isRecording` is shared: microphone backends which stream into their
        # clients' buffers set it on us too, as soon as audio starts arriving.
        # The video side therefore tracks its own start with
        # `_videoRecordingStarted`, so that whichever stream begins first cannot
        # stop the other from recording that it has begun.
        self._recordingRequested = False
        self._videoRecordingStarted = False
        # Microphone backends which stream into their clients' buffers read
        # these directly off us to decide which samples belong to the recording,
        # so the idle value has to be one that excludes everything rather than
        # one that lets every block through.
        self._tRecordingStartRequested = float('inf')
        self._tRecordingStopRequested = None
        self._tRecordingStart = -1.0  # when the first frame actually arrived
        # how long `record(waitForStart=True)` waits for both streams to come up
        self._startTimeout = 10.0
        self._recordingBuffer = []  # buffer for storing frames during recording
        self._nRecordedFrames = 0  # number of frames recorded during recording

        # Computed timestamps for when the first audio within the recording
        # interval was received. This is used to compute the offset within the
        # audio track to start merging with the video track.
        self._tFirstAudioBlockStart = -1.0
    
        self._absAudioRecStartPos = -1.0  # in samples
        self._absAudioRecStopPos = -1.0

        self._curPTS = 0.0  # current display timestamp
        self._isRecording = False
        self._generatePTS = False  # use generated PTS values for frames
        
        # Movie writer instance. Frames are handed to it from the camera's
        # polling thread while the main thread may be opening or closing it, so
        # all access to it is serialised through `_movieWriterLock`.
        self._movieWriterLock = threading.RLock()
        self._movieWriter = None
        self._encoderLib = None  # library the open writer was created with
        self._movieWriterStream = None  # output stream (PyAV writer only)
        self._movieWriterReformatter = None  # colour converter for the encoder
        self._movieWriterTimeBase = None  # time base output PTS are counted in
        self._nFramesWritten = 0  # frames handed to the encoder so far
        self._tempVideoFile = None  # temporary video file for recording

        # thread for polling the microphone
        self._audioTrack = None  # audio track from the recent recording
        # keep track of the last video file saved
        self._lastVideoFile = None

        # OpenGL stuff, just declare these attributes for now
        self._pixbuffId = None
        self._textureId = None
        self._interpolate = True  # use bilinear interpolation by default
        self._texFilterNeedsUpdate = True  # flag to update texture filtering
        self._texBufferSizeBytes = None  # size of the texture buffer

        # Cached colour conversion context, built on first use and reused for
        # every frame after that. Creating one per frame costs far more than the
        # conversion itself. `_swsContextKey` records the frame format the
        # context was built for, so it can be rebuilt if that ever changes.
        self._swsContext = None
        self._swsContextKey = None

        # computer vison mode 
        self._cascadeClassifiers = {}  # list of classifiers for CV mode

        # keep track of files to merge
        self._filesToMerge = []  # list of tuples (videoFile, audioFile)

        self.setWin(win)  # sets up OpenGL stuff if needed

    def authorize(self):
        """Get permission to access the camera. Not implemented locally yet.
        """
        pass  # NOP

    @property
    def latencyBias(self):
        """Latency bias in seconds (`float`).

        This is the latency bias that is applied to the timestamps of the frames
        in the camera stream. This is useful for synchronizing the camera stream
        with other devices such as microphones or audio interfaces. The default
        value is `0.0`, which means no latency bias is applied.

        """
        return self._latencyBias
    
    @latencyBias.setter
    def latencyBias(self, value):
        """Set the latency bias in seconds (`float`).

        This is the latency bias that is applied to the timestamps of the frames
        in the camera stream. This is useful for synchronizing the camera stream
        with other devices such as microphones or audio interfaces. The default
        value is `0.0`, which means no latency bias is applied.

        Parameters
        ----------
        value : float
            Latency bias in seconds.

        """
        if not isinstance(value, (int, float)):
            raise TypeError("Latency bias must be a number.")
        
        self._latencyBias = float(value)

    @property
    def streamTime(self):
        """Current stream time in seconds (`float`).

        This is the current absolute time in seconds from the time the PC was 
        booted. This is not the same as the recording time, which is the time
        since the recording started. This is useful for generating timestamps 
        across multiple cameras or devices using the same time source.

        """
        return self._capture.streamTime
    
    @property
    def frameSize(self):
        """Size of the video frame obtained from recent metadata (`float` or
        `None`).

        Only valid after an `open()` and successive `_enqueueFrame()` call as
        metadata needs to be obtained from the stream. Returns `None` if not
        valid.
        """
        if self._capture is None:
            return None

        return self._capture.frameSize

    @property
    def frameRate(self):
        """Frame rate of the video stream (`float` or `None`).

        Only valid after an `open()` and successive `_enqueueFrame()` call as
        metadata needs to be obtained from the stream. Returns `None` if not
        valid.

        """
        if self._capture is None:
            return None

        return self._capture.frameRate

    @property
    def frameInterval(self):
        """Frame interval in seconds (`float`).

        This is the time between frames in the video stream. This is computed
        from the frame rate of the video stream. If the frame rate is not set,
        this will return `None`.

        """
        if self._capture is None or self._capture.frameRate is None:
            return -1.0

        return 1.0 / self._capture.frameRate

    def _assertCameraReady(self):
        """Assert that the camera is ready. Raises a `CameraNotReadyError` if
        the camera is not ready.
        """
        if not self.isReady:
            raise CameraNotReadyError("Camera is not ready.")

    @property
    def isRecording(self):
        """`True` if the video is presently recording (`bool`)."""
        # Status flags as properties are pretty useful for users since they are
        # self documenting and prevent the user from touching the status flag
        # attribute directly.
        #
        return self._isRecording
    
    @property
    def isStarted(self):
        """`True` if the stream has started (`bool`). This status is given after
        `open()` has been called on this object.
        """
        if hasattr(self, "_isStarted"):
            return self._isStarted

    @property
    def isNotStarted(self):
        """`True` if the stream may not have started yet (`bool`). This status
        is given before `open()` or after `close()` has been called on this
        object.
        """
        return not self.isStarted

    @property
    def isStopped(self):
        """`True` if the recording has stopped (`bool`). This does not mean that
        the stream has stopped, `getVideoFrame()` will still yield frames until
        `close()` is called.
        """
        return not self._isRecording

    @property
    def metadata(self):
        """Video metadata retrieved during the last frame update
        (`MovieMetadata`).
        """
        return self.getMetadata()

    def getMetadata(self):
        """Get stream metadata.

        Returns
        -------
        MovieMetadata vor None
            Metadata about the video stream, retrieved during the last frame
            update (`_enqueueFrame` call). If no metadata is available,
            returns `None`. This is useful for getting information about the
            video stream such as frame size, frame rate, pixel format, etc.

        """
        return self._capture.getMetadata() if self._capture else None

    _getCamerasCache = {}

    @staticmethod
    def getCameras(cameraLib=CAMERA_LIB_FFPYPLAYER):
        """Get information about installed cameras on this system.

        Parameters
        ----------
        cameraLib : str
            Capture library the cameras are to be opened with, either
            `'ffpyplayer'` or `'pyav'`.

        Returns
        -------
        dict
            Mapping of camera information objects.

        """
        # not pluggable yet, needs to be made available via extensions
        return getCameraDeviceClass(cameraLib).getCameras(
            cameraLib=cameraLib)

    @staticmethod
    def getAvailableDevices(cameraLib=CAMERA_LIB_FFPYPLAYER):
        """Get a list of available camera devices on this system.

        Parameters
        ----------
        cameraLib : str
            Capture library the cameras are to be opened with, either
            `'ffpyplayer'` or `'pyav'`.

        Returns
        -------
        list
            List of available camera devices. Each device is represented as a
            dictionary containing information about the device.

        """
        return getCameraDeviceClass(cameraLib).getAvailableDevices()

    @staticmethod
    def getCameraDescriptions(collapse=False, cameraLib=CAMERA_LIB_FFPYPLAYER):
        """Get a mapping or list of camera descriptions.

        Camera descriptions are a compact way of representing camera settings
        and formats. Description strings can be used to specify which camera
        device and format to use with it to the `Camera` class.

        Descriptions have the following format (example)::

            '[Live! Cam Sync 1080p] 160x120@30fps, mjpeg'

        This shows a specific camera format for the 'Live! Cam Sync 1080p'
        webcam which supports 160x120 frame size at 30 frames per second. The
        last value is the codec or pixel format used to decode the stream.
        Different pixel formats and codecs vary in performance.

        Parameters
        ----------
        collapse : bool
            Return camera information as string descriptions instead of
            `CameraInfo` objects. This provides a more compact way of
            representing camera formats in a (reasonably) human-readable format.
        cameraLib : str
            Capture library the cameras are to be opened with, either
            `'ffpyplayer'` or `'pyav'`.

        Returns
        -------
        dict or list
            Mapping (`dict`) of camera descriptions, where keys are camera names
            (`str`) and values are a `list` of format description strings
            associated with the camera. If `collapse=True`, all descriptions
            will be returned in a single flat list. This might be more useful
            for specifying camera formats from a single GUI list control.

        """
        return getCameraDescriptions(
            collapse=collapse, cameraLib=cameraLib)

    @property
    def device(self):
        """Camera to use (`str` or `None`).

        String specifying the name of the camera to open a stream with. This
        must be set prior to calling `start()`. If the name is not valid, an
        error will be raised when `start()` is called.

        """
        return self._device

    @device.setter
    def device(self, value):
        if value in (None, "None", "none", "Default", "default"):
            value = 0

        self._device = value

    @property
    def _hasPlayer(self):
        """`True` if we have an active media player instance.
        """
        # deprecated - remove in future versions and use `isStarted` instead
        return self.isStarted

    @property
    def mic(self):
        """Microphone to record audio samples from during recording
        (:class:`~psychopy.sound.microphone.Microphone` or `None`). 
        
        If `None`, no audio will be recorded. Cannot be set after opening a 
        camera stream.
        """
        return self._mic

    @mic.setter
    def mic(self, value):
        if self.isStarted:
            raise CameraError("Cannot set microphone after starting camera.")
        
        self._mic = value

    @property
    def _hasAudio(self):
        """`True` if we have a microphone object for audio recording.
        """
        return self._mic is not None
    
    @property
    def keepFrames(self):
        """Number of frames to keep in memory for the camera stream (`int`).
        """
        return self._keepFrames
    
    @keepFrames.setter
    def keepFrames(self, value):
        if value < 0:
            raise ValueError("`keepFrames` must be a non-negative integer.")
        
        self._keepFrames = value
        oldFrames = self._frameStore
        oldStoreSize = len(self._frameStore)

        if oldStoreSize == self._keepFrames:
            # nothing to do, size is the same
            return

        # change the size of the frame store
        self._frameStore = collections.deque(maxlen=self._keepFrames)

        if oldStoreSize > self._keepFrames:
            logging.warning(
                "Reducing `keepFrames` from {} to {} will discard the oldest "
                "frames in the buffer.".format(oldStoreSize, self._keepFrames))

        # add back frames
        if oldStoreSize > 0:
            # copy the last `keepFrames` frames to the new store
            for i in range(oldStoreSize - self._keepFrames, oldStoreSize):
                self._frameStore.append(oldFrames[i])

    @property
    def recordingTime(self):
        """Current recording timestamp (`float`).

        This returns the timestamp of the last frame captured in the recording.

        This value increases monotonically from the last `record()` call. It
        will reset once `stop()` is called. This value is invalid outside
        `record()` and `stop()` calls.

        This is taken from the capture time of the most recent frame rather than
        from the number of frames captured, so that it still reports real
        elapsed time when the camera delivers below its nominal frame rate.

        """
        if self._lastFrame is None or self._tRecordingStart < 0:
            return 0.0

        return self._elapsedInRecording(self._lastFrame.absTime)

    @property
    def recordingBytes(self):
        """Current size of the recording in bytes (`int`).
        """
        if not self._isRecording:
            return 0

        return -1

    def _assertMediaPlayer(self):
        """Assert that we have a media player instance open.

        This will raise a `RuntimeError` if there is no player open. Use this
        function to ensure that a player is present before running subsequent
        code.
        """
        if self._capture is not None:
            return

        raise PlayerNotAvailableError('Media player not initialized.')
    
    @property
    def isReady(self):
        """`True` if the video and audio capture devices are in a ready state 
        (`bool`).

        When this is `True`, the audio and video streams are properly started.

        """
        return self._audioReady and self._videoReady

    def _resolveCaptureDevice(self):
        """Find or create the capture device this camera streams from.

        The capture device is what actually talks to the camera hardware; a
        `Camera` is one of possibly several clients of it. This works out which
        device the `device` value passed to the constructor refers to, reusing
        an already initialised device where one matches and creating one
        otherwise, then stores it as `_capture` and takes its info.

        This is also called by `open()` when the camera is being reopened after
        `close()`, which releases the device, so the lookup is repeated rather
        than done only once at construction.

        """
        device = self._deviceSpec['device']
        frameRate = self._deviceSpec['frameRate']
        frameSize = self._deviceSpec['frameSize']
        bufferSecs = self._deviceSpec['bufferSecs']
        cameraLib = self._cameraLib

        # interface class which talks to the camera using `cameraLib`, raises
        # if the library named is not one we have an interface for
        cameraDeviceClass = getCameraDeviceClass(cameraLib)

        # handle device
        self._capture = None
        if isinstance(device, BaseCameraDevice):
            # if given a device object, use it
            self._capture = device
        elif device is None:
            # if given None, get the first available device
            for devName, obj in DeviceManager.getInitialisedDevices(
                    cameraDeviceClass).items():
                self._capture = obj
                break
            # if there are none, set one up
            if self._capture is None:
                for profile in cameraDeviceClass.getAvailableDevices():
                    self._capture = DeviceManager.addDevice(**profile)
                    break
        elif isinstance(device, str):
            if DeviceManager.getDevice(device):
                self._capture = DeviceManager.getDevice(device)
            else:
                # get available devices
                availableDevices = cameraDeviceClass.getAvailableDevices()
                # if given a device name, try to find it
                for profile in availableDevices:
                    if profile['deviceName'] != device:
                        continue
                    paramsMatch = all([
                        profile.get(key) == value
                        for key, value in {
                            'deviceName': device,
                            'captureLib': cameraLib,
                            'frameRate': frameRate if frameRate is not None else True,  # get first
                            'frameSize': frameSize if frameSize is not None else True
                        }.items() if value is not None
                    ])
                    if not paramsMatch:
                        continue
                    
                    device = profile['device']
                    break

                # anything else, try to initialise a new device from params
                self._capture = cameraDeviceClass(
                    device=device,
                    captureLib=cameraLib,
                    frameRate=frameRate,
                    frameSize=frameSize,
                    bufferSecs=bufferSecs,
                    pixelFormat=None,  # use default pixel format
                    codecFormat=None,  # use default codec format
                    captureAPI=None  # use default capture API
                )
        else:
            # anything else, try to initialise a new device from params
            self._capture = cameraDeviceClass(
                device=device,
                frameRate=frameRate,
                frameSize=frameSize,
                bufferSecs=bufferSecs,
            )

        # get info from device
        self._cameraInfo = self._capture.info

        return self._capture

    def open(self):
        """Open the camera stream and begin decoding frames (if available).

        This function returns when the camera is ready to start getting
        frames.

        Call `record()` to start recording frames to memory. Captured frames
        came be saved to disk using `save()`.

        """
        if self._hasPlayer:
            raise RuntimeError('Cannot open `MediaPlayer`, already opened.')

        # Camera interface to use, these are hard coded but support for each is
        # provided by an extension.
        # desc = self._cameraInfo.description()

        # `close()` releases the capture device, so look it up again if this is
        # a reopen. Doing so here rather than holding on to the closed device
        # means a device shared through `DeviceManager` is picked up in
        # whatever state it is now in. This comes before the movie file writer
        # is opened, as the writer needs the frame size the device reports.
        if self._capture is None:
            self._resolveCaptureDevice()

        # CV mode never writes frames to disk, so opening a writer for it would
        # only create a temporary file and an encoder nothing ever reaches.
        if self._usageMode == CAMERA_MODE_VIDEO:
            self._openMovieFileWriter()

        if not self._capture.isOpen:
            self._capture.open()

        # register this client with the camera device
        self._capture.bind(self)        
        self.setWin(self._win)  # set the window (if any)
        
        # open the mic when the camera opens
        if hasattr(self.mic, "open"):
            self.mic.open()  # should NOP if already open
            self.mic.bind(self)

        self._isStarted = True

    def _getTime(self):
        """Get the current time in seconds.

        This is a helper function to get the current time in seconds. It uses
        `time.monotonic()` to get a monotonic clock value that is not affected
        by system clock changes. This is useful for measuring elapsed time
        without being affected by system clock changes.

        Returns
        -------
        float
            Current time in seconds.

        """
        return time.monotonic()  # timebase of the stream

    def record(self, clearLastRecording=True, waitForStart=False, when=None):
        """Start recording frames.

        This function will start recording frames and audio (if available). The
        value of `lastFrame` will be updated as new frames arrive and the
        `frameCount` will increase. You can access image data for the most 
        recent frame to be captured using `lastFrame`.

        If this is called before `open()` the camera stream will be opened
        automatically. This is not recommended as it may incur a longer than
        expected delay in the recording start time.

        Warnings
        --------
        If a recording has been previously made without calling `save()` it will
        be discarded if `record()` is called again unless 
        `clearLastRecording=False`.

        Parameters
        ----------
        clearLastRecording : bool
            Clear the frame buffer before starting the recording. If `True`,
            the frame buffer will be cleared before starting the recording. If
            `False`, the frame buffer will be kept and new frames will be added
            to the buffer. Default is `True`. This is deprecated and will
            eventually be removed in a future version of PsychoPy. The recording 
            is always cleared when `record()` is called, so this parameter is
            ignored.
        waitForStart : bool
            Capture video only when the camera and microphone are ready. This 
            will result in a longer delay before the recording starts, but will
            ensure the microphone is actually recording valid samples. In some 
            cases this will result in a delay of up to 1 second before the
            recording starts.
        when : float or None
            Absolute time in seconds to start recording. If `None`, recording
            will start immediately. If a time is specified, the recording will
            start at the specified time. This is useful for synchronizing the
            recording with other devices or events.

        """
        if self.isNotStarted:
            self.open()   # open the camera stream if we call record() first
            logging.warning(
                "Called `Camera.record()` before opening the camera stream, "
                "opening now. This is not recommended as it may incur a longer "
                "than expected delay in the recording start time."
            )
        
        if self._isRecording:
            logging.warning(
                "Called `Camera.record()` while already recording, stopping "
                "the previous recording first."
            )
            self.stop()

        # clear previous frames
        if clearLastRecording:
            self._frameStore.clear()  # clear frames from last recording

        # self._capture._clearFrameStore()

        # reset per-recording counters and flags
        self._frameCount = 0
        self._tRecordingStart = -1.0
        self._videoRecordingStarted = False
        self._audioReady = self._videoReady = False

        # Discard audio captured for any previous recording. A fresh list is
        # assigned rather than cleared in place because the microphone's own
        # thread appends to this one.
        self._recordingBuffer = []
        self._nRecordedFrames = 0
        self._startRecOffset = 0
        self._tRecordingStopRequested = None

        # reset the last frame
        self._lastFrame = None

        # Reopen the file writer if a previous recording closed it, otherwise
        # only the first recording of a session would be written to disk. This
        # is a no-op if the writer is already open.
        if self._usageMode == CAMERA_MODE_VIDEO:
            self._openMovieFileWriter()

        # start camera recording
        self._tRecordingStartRequested = \
            self._getTime() if when is None else when + self._getTime()

        # start microphone recording
        if self._usageMode == CAMERA_MODE_VIDEO:
            if self.mic is not None:
                self.mic.record(when=self._tRecordingStartRequested)
            else:
                self._audioReady = True  # no audio stream to wait on
        else:
            self._audioReady = True  # audio is not recorded in CV mode

        # `_isRecording` is set once a frame captured at or after the requested
        # start time arrives, see `_onNewFrames()`
        self._isRecording = False
        self._recordingRequested = True

        # mark that there's unsaved footage
        self._unsaved = True

        if waitForStart:
            self._waitForRecordingStart()

    def _waitForRecordingStart(self):
        """Block until both streams are recording, or until we give up waiting.

        Frames arrive on the camera's polling thread, so this just waits for the
        flags that thread sets. Returns either way; a camera which never reaches
        a ready state logs a warning rather than hanging the experiment.

        Returns
        -------
        bool
            `True` if the streams came up, `False` if we timed out waiting.

        """
        # a recording scheduled for the future cannot start before then, so
        # measure the timeout from the requested start rather than from now
        tTimeout = max(
            self._getTime(), self._tRecordingStartRequested) + self._startTimeout

        while not self.isReady:
            if self._getTime() > tTimeout:
                logging.warning(
                    "Timed out after {}s waiting for the camera and microphone "
                    "to start recording. Recording may be missing its first "
                    "frames or its audio track.".format(self._startTimeout))
                return False

            time.sleep(0.001)

        return True

    def start(self, waitForStart=True):
        """Start the camera stream.

        This will start the camera stream and begin decoding frames. If the
        camera is already started, this will do nothing. Use `record()` to start
        recording frames to memory.

        """
        return self.record(clearLastRecording=False, waitForStart=waitForStart)

    def stop(self, when=None):
        """Stop recording frames and audio (if available).

        Parameters
        ----------
        when : float or None
            Absolute time in seconds to stop recording. If `None`, recording
            will stop immediately. If a time is specified, the recording will
            stop at the specified time. This is useful for synchronizing the
            recording with other devices or events.

        """
        # poll any remaining frames and stop
        # self.update()

        # stop the camera stream
        self._absVideoRecStopTime = self._getTime() if when is None else when + self._getTime()

        # Close the gate first so that frames still in flight on the polling
        # thread are not written to a file which is about to be closed. Setting
        # the stop time also tells microphone backends which stream into our
        # buffer to stop adding to it.
        self._tRecordingStopRequested = self._absVideoRecStopTime
        self._recordingRequested = False
        self._videoRecordingStarted = False
        self._isRecording = False

        # stop audio recording if we have a microphone
        if self.hasMic:
            # the microphone calls its scheduled stop time `stopTime`
            self.mic.stop(stopTime=self._absVideoRecStopTime)

        self._audioReady = self._videoReady = False  # reset camera ready flags

        self._closeMovieFileWriter()
            
    def close(self):
        """Close the camera.

        This will close the camera stream and free up any resources used by the
        device. If the camera is currently recording, this will stop the 
        recording, but will not discard any frames. You may still call `save()`
        to save the frames to disk.

        """
        self._recordingRequested = False
        self._videoRecordingStarted = False
        self._isRecording = False

        if self._capture is not None and self._capture.isOpen:
            self._capture.unbind(self)
            # Release the camera itself now that we are no longer using it.
            # This is a no-op while any other client is still bound to the same
            # stream, and `open()` reopens the device if it is needed again, so
            # a stream shared through DeviceManager survives one client leaving.
            self._capture.close()

        self._capture = None  # clear the capture object

        if self.mic is not None:
            self.mic.unbind(self)
            self.mic.close()

        self._closeMovieFileWriter()

        self._isStarted = False

    def _mergeAudioVideoTracks(self, videoTrackFile, audioTrackFile,
                               filename, writerOpts=None):
        """Use FFMPEG to merge audio and video tracks into a single file.
        
        Parameters
        ----------
        videoTrackFile : str
            Path to the video track file to merge.
        audioTrackFile : str
            Path to the audio track file to merge.
        filename : str
            Path to the output file to save the merged audio and video tracks.
        writerOpts : dict or None
            Options to pass to the movie writer. If `None`, default options
            will be used. This is useful for specifying the codec, bitrate,
            etc. for the output file.

        Returns
        -------
        str
            Path to the output file with merged audio and video tracks.
        
        """
        import subprocess as sp

        # check if the video and audio track files exist
        if not os.path.exists(videoTrackFile):
            raise FileNotFoundError(
                "Video track file `{}` does not exist.".format(videoTrackFile))
        if not os.path.exists(audioTrackFile):
            raise FileNotFoundError(
                "Audio track file `{}` does not exist.".format(audioTrackFile))
        
        # check if the output file already exists
        if os.path.exists(filename):
            logging.warning(
                "Output file `{}` already exists, it will be overwritten.".format(filename))
            os.remove(filename)

        # build the command to merge audio and video tracks
        cmd = [
            'ffmpeg', 
            '-loglevel', 'error',  # suppress output except errors
            '-nostdin',  # do not read from stdin
            '-y',  # overwrite output file if it exists
            '-i', videoTrackFile,  # input video track
            '-i', audioTrackFile,  # input audio track
            '-c:v', 'copy',  # copy video codec
            '-c:a', 'aac',  # use AAC for audio codec
            '-strict', 'experimental',  # allow experimental codecs
            '-threads', 'auto',  # use all available threads
            '-shortest'  # stop when the shortest input ends
        ]
        # add output file
        cmd.append(filename)

        # apply any writer options if provided
        if writerOpts is not None:
            for key, value in writerOpts.items():
                if isinstance(value, str):
                    cmd.append('-' + key)
                    cmd.append(value)
                elif isinstance(value, bool) and value:
                    cmd.append('-' + key)
                elif isinstance(value, (int, float)):
                    cmd.append('-' + key)
                    cmd.append(str(value))

        logging.debug(
            "Merging audio and video tracks with command: {}".format(' '.join(cmd))
        )

        # run the command to merge audio and video tracks
        try:
            proc = sp.Popen(
                cmd, 
                stdout=sp.PIPE, 
                stderr=sp.PIPE, 
                stdin=sp.DEVNULL if hasattr(sp, 'DEVNULL') else None,
                universal_newlines=True,  # use text mode for output
                text=True
            )
            proc.wait()  # wait for the process to finish
            if proc.returncode != 0:
                logging.error(
                    "FFMPEG returned non-zero exit code {} for command: {}".format(
                        proc.returncode, cmd
                    )
                )
            # wait for the process to finish
        except sp.CalledProcessError as e:
            logging.error(
                "Failed to merge audio and video tracks: {}".format(e))
            return None
        
        logging.info(
            "Merged audio and video tracks into `{}`".format(filename))

        return filename
    
    def _isAudioRecording(self):
        """Whether the microphone has actually started capturing samples.

        Microphone backends split into two camps and report this differently.
        Backends such as `ptb` record on the device itself and say so through
        `isRecording`/`isStarted`. Backends such as `sounddevice` keep one
        always-running stream and write samples into the buffers of the clients
        bound to it, so the device never reports itself as recording at all and
        the only honest signal is that samples have started arriving here.

        Returns
        -------
        bool
            `True` if audio is being captured for this recording.

        """
        if self.mic is None:
            return False

        # backends which record device-side report it directly
        for attrName in ('isRecording', 'isStarted'):
            if getattr(self.mic, attrName, False):
                return True

        # backends which stream into their clients' buffers do not, so take
        # samples having reached us as the signal that audio is running
        return self._nRecordedFrames > 0

    def _getRecordedAudio(self):
        """Get the audio captured during the last recording.

        Handles both of the microphone models described in
        `_isAudioRecording()`, so callers do not need to know which backend is
        in use.

        Returns
        -------
        AudioClip or None
            The audio track, or `None` if there is no microphone or nothing was
            captured.

        """
        if self.mic is None:
            return None

        # Backends which stream into their clients' buffers have left the
        # samples with us, so those are the recording.
        if self._recordingBuffer:
            self._mergeAudioFragments()
            audioTrack = AudioClip(
                self._recordingBuffer[0],
                sampleRateHz=self.mic.sampleRateHz)

            # drop the samples captured before the recording was asked to start
            if self._startRecOffset > 0:
                audioTrack = audioTrack.trimmed(
                    direction='start',
                    duration=self._startRecOffset,
                    units='samples')

            return audioTrack

        # otherwise the recording is held by the device itself
        try:
            recording = self.mic.getRecording()
        except Exception as err:
            logging.error(
                "Could not get the audio track from the microphone: "
                "{}".format(err))
            return None

        if recording is None:
            return None

        if isinstance(recording, AudioClip):
            return recording

        # some backends hand back a raw array of samples
        return AudioClip(
            np.asarray(recording), sampleRateHz=self.mic.sampleRateHz)

    def _mergeAudioFragments(self):
        """Merge audio fragments within the recording buffer.
        """
        if not self._recordingBuffer:
            return None

        # concatenate all audio frames into a single audio track
        # collapse recording buffer into a single array
        self._recordingBuffer = [
            np.concatenate(self._recordingBuffer, axis=0, dtype=np.float32)]
            
    def save(self, filename, useThreads=True, mergeAudio=True, writerOpts=None):
        """Save the last recording to file.

        This will write frames to `filename` acquired since the last call of 
        `record()` and subsequent `stop()`. If `record()` is called again before 
        `save()`, the previous recording will be deleted and lost.

        This is a slow operation and will block for some time depending on the 
        length of the video. This can be sped up by setting `useThreads=True` if
        supported.

        Parameters
        ----------
        filename : str
            File to save the resulting video to, should include the extension.
        useThreads : bool
            Use threading where possible to speed up the saving process.
        mergeAudio : bool
            Merge the audio track from the microphone with the video into a 
            single file if `True`. If `False`, the audio track will be saved
            to a separate file with the same name as `filename`, but with a
            `.wav` extension. This is useful if you want to process the audio
            track separately, or merge it with the video later on as the process
            is computationally expensive and memory consuming. Default is 
            `True`.
        writerOpts : dict or None
            Options to pass to the movie writer. If `None`, default options
            will be used.

        """
        # stop if still recording
        if self._isRecording:
            self.stop()
            logging.warning(
                "Called `Camera.save()` while recording, stopping the "
                "recording first."
            )
        
        # if there's nothing to unsaved, do nothing
        if not self._unsaved:
            return

        if self._usageMode != CAMERA_MODE_VIDEO:
            # Frames are handed to the experiment in CV mode rather than
            # written to a file, so there is no video track to save. Keep the
            # footage marked unsaved, since nothing has been written out.
            logging.warning(
                "Called `Camera.save()` on a camera opened in '{}' usage mode, "
                "which does not record video to disk. Nothing was saved to "
                "`{}`. Use `usageMode='{}'` if you want a recording of the "
                "stream.".format(self._usageMode, filename, CAMERA_MODE_VIDEO))
            return

        # check if we have an active movie writer
        if self._movieWriter is not None:
            self._movieWriter.close()  # close the movie writer

        # check if we have a temp movie file
        videoTrackFile = self._tempVideoFile
        
        # write the temporary audio track to file if we have one
        tStart = time.time()  # start time for the operation
        # this is `None` if there is no microphone or nothing was captured, and
        # has already had any pre-recording samples trimmed off it
        audioTrack = self._getRecordedAudio()

        if audioTrack is not None:
            logging.debug(
                "Saving audio track to file `{}`...".format(filename))

            if mergeAudio:
                logging.debug("Merging audio track with video track...")
                # save it to a temp file
                import tempfile
                tempAudioFile = tempfile.NamedTemporaryFile(
                    suffix='.wav', delete=False)
                audioTrackFile = tempAudioFile.name
                tempAudioFile.close()  # close the file so we can use it later
                audioTrack.save(audioTrackFile)

                # merge audio and video tracks using FFMPEG
                self._mergeAudioVideoTracks(
                    videoTrackFile, 
                    audioTrackFile, 
                    filename, 
                    writerOpts=writerOpts)
                
                os.remove(audioTrackFile)  # remove the temp file

            else:
                tAudioStart = time.time()  # start time for audio saving
                # just save the audio file seperatley
                # check if the filename has an extension
                if '.' not in filename:
                    audioTrackFile = filename + '.wav'
                else:
                    # if it has an extension, use the same name but with .wav
                    # extension
                    rootName, _ = os.path.splitext(filename)
                    audioTrackFile = rootName + '.wav' 

                audioTrack.save(audioTrackFile)

                logging.info(
                    "Saved recorded audio track to `{}` (took {:.6f} seconds)".format(
                        audioTrackFile, time.time() - tAudioStart))

                # just copy the video from the temp file to the final file
                import shutil
                shutil.copyfile(videoTrackFile, filename)

        else:
            # just copy the video file to the destination
            import shutil
            shutil.copyfile(videoTrackFile, filename)

        os.remove(videoTrackFile)  # remove the temp file

        logging.info(
            "Saved recorded video to `{}` (took {:.6f} seconds)".format(
                filename, time.time() - tStart))
        
        self._frameStore.clear()  # clear the frame store
        # mark that there's no longer unsaved footage
        self._unsaved = False

        self._lastVideoFile = filename  # store the last video file saved

        return self._lastVideoFile

    def _upload(self):
        """Upload video file to an online repository. Not implemented locally,
        needed for auto translate to JS.
        """
        pass  # NOP

    def _download(self):
        """Download video file to an online repository. Not implemented locally,
        needed for auto translate to JS.
        """
        pass  # NOP

    @property
    def lastClip(self):
        """File path to the last recording (`str` or `None`).

        This value is only valid if a previous recording has been saved
        successfully (`save()` was called), otherwise it will be set to `None`.

        """
        return self.getLastClip()

    def getLastClip(self):
        """File path to the last saved recording.

        This value is only valid if a previous recording has been saved to disk
        (`save()` was called).

        Returns
        -------
        str or None
            Path to the file the most recent call to `save()` created. Returns
            `None` if no file is ready.

        """
        return self._lastVideoFile 

    @property
    def lastFrame(self):
        """Most recent frame pulled from the camera (`VideoFrame`) since the
        last call of `getVideoFrame`.
        """
        return self._lastFrame
    
    @property
    def frameCount(self):
        """Total number of frames captured in the current recording (`int`).

        This is the total number of frames captured since the last call to
        `record()`. This value is reset when `record()` is called again.

        """
        return self._frameCount

    @property
    def hasMic(self):
        """`True` if the camera has a microphone attached (`bool`).

        This is `True` if the camera has a microphone attached and is ready to
        record audio. If the camera does not have a microphone, this will be
        `False`.

        """
        return self.mic is not None

    def _convertFrameToRGB(self, frame):
        """Convert a frame from the capture library in use to RGB format.

        Parameters
        ----------
        frame : Any
            Frame to convert, as handed over by the camera interface.

        Returns
        -------
        object
            The frame in RGB format. Whatever the capture library, the returned
            object exposes `to_memoryview()`, `get_size()` and
            `get_pixel_format()`, so callers do not need to know which backend
            produced it.

        """
        if self._cameraLib == CAMERA_LIB_FFPYPLAYER:
            return self._convertFrameToRGBFFPyPlayer(frame)
        elif self._cameraLib == CAMERA_LIB_PYAV:
            return self._convertFrameToRGBPyAV(frame)
        elif self._cameraLib == CAMERA_LIB_OPENCV:
            return self._convertFrameToRGBOpenCV(frame)

        raise ValueError(
            "Cannot convert frames captured with '{}', expected one of "
            "`'ffpyplayer'`, `'pyav'` or `'opencv'`.".format(self._cameraLib))

    def _convertFrameToRGBPyAV(self, frame):
        """Convert a PyAV frame to RGB format.

        Frames coming off `PyAVCameraDevice` have already been converted on the
        capture thread, so this is usually a no-op. It is still needed for
        frames obtained from PyAV directly, which are handed over in whatever
        format the camera is streaming in.

        Parameters
        ----------
        frame : av.VideoFrame or _RGBFrameAdapter
            The frame to convert. If already an `_RGBFrameAdapter` (i.e.
            previously converted), it is returned unchanged.

        Returns
        -------
        _RGBFrameAdapter
            The converted frame, wrapped to present an `ffpyplayer`-like
            interface to downstream code.

        """
        if isinstance(frame, _RGBFrameAdapter):
            return frame  # already converted

        if self._swsContext is None:
            from av.video.reformatter import VideoReformatter
            self._swsContext = VideoReformatter()

        return _RGBFrameAdapter(
            self._swsContext.reformat(frame, format='rgb24').to_ndarray())

    def _convertFrameToRGBOpenCV(self, frame):
        """Convert an OpenCV frame to RGB format.

        Frames coming off `OpenCVCameraDevice` have already been converted on
        the capture thread, so this is usually a no-op. It is still needed for
        frames obtained from OpenCV directly, which are handed over as BGR
        arrays.

        Parameters
        ----------
        frame : numpy.ndarray or _RGBFrameAdapter
            The frame to convert. If already an `_RGBFrameAdapter` (i.e.
            previously converted), it is returned unchanged.

        Returns
        -------
        _RGBFrameAdapter
            The converted frame, wrapped to present an `ffpyplayer`-like
            interface to downstream code.

        """
        if isinstance(frame, _RGBFrameAdapter):
            return frame  # already converted

        import cv2

        return _RGBFrameAdapter(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    def _convertFrameToRGBFFPyPlayer(self, frame):
        """Convert a frame to RGB format.

        This function converts a frame to RGB format. The frame is returned as
        a Numpy array. The resulting array will be in the correct format to
        upload to OpenGL as a texture.

        Parameters
        ----------
        frame : FFPyPlayer frame
            The frame to convert.

        Returns
        -------
        ffpyplayer.pic.Image
            The converted frame in RGB format.

        """
        from ffpyplayer.pic import SWScale

        srcPixFmt = frame.get_pixel_format()
        if srcPixFmt == 'rgb24':  # already converted
            return frame

        frameWidth, frameHeight = frame.get_size()

        # Rebuild the scaling context only when the frame format or size
        # changes; creating one per frame costs far more than the conversion.
        contextKey = (frameWidth, frameHeight, srcPixFmt)
        if self._swsContext is None or self._swsContextKey != contextKey:
            self._swsContext = SWScale(
                frameWidth, frameHeight, srcPixFmt, ofmt='rgb24')
            self._swsContextKey = contextKey

        return self._swsContext.scale(frame)
    
    def _onNewFrames(self, frames):
        """Callback for when new frames are available from the camera.

        This is called by the camera stream when new frames are available. It
        will update the frame store and last frame, and transfer the frames to
        the GPU if a window is set.

        Parameters
        ----------
        frames : list of tuple
            Frames from the camera interface, each a tuple of the frame data,
            its index in the stream, the presentation timestamp the camera
            reported, and the time it was captured on the local clock.

        """
        # iterate over frames and add them to the frame store
        if not frames:
            return  # no frames to process

        # CV mode has nothing to write to disk and no audio track to line up
        # with, so a frame is useful the moment it arrives rather than only
        # within a recording. Keeping such frames is what lets the live view
        # work without calling `record()` first, whether that is an `ImageStim`
        # showing the stream or code pulling frames to process. Video mode
        # keeps waiting for `record()`, since a frame outside the recording
        # interval has no file to go to.
        liveView = self._usageMode == CAMERA_MODE_CV

        if not self._recordingRequested and not liveView:
            return  # not recording, nothing to do with these

        for colorData, frameIndex, pts, absTime in frames:
            # Whether this frame belongs to a recording, as opposed to one only
            # passing through for the live view. Frames captured before the
            # recording was asked to start are not part of it.
            inRecording = (self._recordingRequested and
                           absTime >= self._tRecordingStartRequested)

            if not inRecording and not liveView:
                continue

            if inRecording and not self._videoRecordingStarted:
                # This is the first frame at or after the requested start time,
                # so the video recording begins here. The flag is set from this
                # side rather than in `record()` because the camera may not
                # reach the requested start time until some frames later.
                self._videoRecordingStarted = True
                self._isRecording = True
                self._videoReady = True
                self._tRecordingStart = absTime
                logging.debug(
                    "Recording started on frame {} of the stream (requested "
                    "{:.6f}, started {:.6f})".format(
                        frameIndex, self._tRecordingStartRequested, absTime))

            # the microphone is started alongside the camera, but takes its own
            # time to come up, so keep checking until it reports it is running
            if inRecording and not self._audioReady and self.hasMic:
                self._audioReady = self._isAudioRecording()

            # if camera is in CV mode, convert the frame to RGB by default
            # otherwise frames are converted only when needed
            if self._usageMode == CAMERA_MODE_CV:
                colorData = self._convertFrameToRGB(colorData)
            elif inRecording:
                # if we are recording video, pass the frame to the movie writer
                self._submitFrameToFile(
                    (colorData, frameIndex, pts, absTime))

            # add the frame to the frame store
            cameraFrame = CameraFrame(
                colorData, 
                pts, 
                absTime, 
                captureLib=self._cameraLib)
            self._frameStore.append(cameraFrame)
            self._lastFrame = cameraFrame  # most recent frame, for display

            if inRecording:
                # `frameCount` counts the current recording, so frames shown
                # only in the live view are left out of it
                self._frameCount += 1  # increment the frame count
        
    def update(self):
        """Acquire the newest data from the camera and audio streams.

        This must be called periodically to ensure that stream buffers are 
        flushed before they overflow to prevent data loss. Furthermore, 
        calling this too infrequently may result also result in more frames 
        needing to be processed at once, which may result in performance issues.

        Returns
        -------
        int
            Number of frames captured since the last call to this method. This
            will be `0` if no new frames were captured since the last call, 
            indicating that the poll function is getting called too 
            frequently or that the camera is not producing new frames (i.e.
            paused or closed). If `-1` is returned, it indicates that the
            either or both the camera and microphone are not in a ready state 
            albiet both interfaces are open. This can happen if `update()` is
            called very shortly after `record()`.

        """
        # Nothing to poll before `open()` or after `close()`, which clears the
        # capture object. This is not an error: a stimulus handed this camera
        # as its image goes on drawing after the camera is closed, and the
        # texture already uploaded stays valid, so it simply keeps showing the
        # last frame instead of raising.
        if self._capture is None or not self._capture.isOpen:
            return

        # force the device interface to poll to ensure most recent frame
        self._capture._poll() 
        # transfer most recent frames to the GPU if we have a window
        self._pixelTransfer()  
                
    def poll(self):
        """Poll the camera for new frames.
        
        Alias for `update()`.
        """
        return self.update()

    def getVideoFrames(self):
        """Get the most recent frame from the stream (if available).

        Returns
        -------
        list of tuple
            List of recent video frames. This will return a list of frame images 
            as numpy arrays, their presentation timestamp in the recording, and 
            the absolute stream time in seconds. Frames will be converted
            to RGB format if they are not already. The number of frames returned
            will be limited by the `keepFrames` parameter set when creating the
            camera object. If no frames are available, an empty list will be
            returned.

        """
        self.update()
        recentFrames = [
            self._convertFrameToRGB(frame.colorData) for frame in self._frameStore]

        return recentFrames
    
    def getRecentVideoFrame(self):
        """Get the most recent video frame from the camera.

        Returns
        -------
        CameraFrame or None
            Most recent video frame. Returns `None` if no frame was available,
            or we timed out.

        """
        self.update()

        return self._lastFrame
    
    # --------------------------------------------------------------------------
    # Audio track
    #

    def getAudioTrack(self):
        """Get the audio track data.

        Returns
        -------
        AudioClip or None
            Audio track data from the microphone if available, or `None` if
            no microphone is set or no audio was recorded.

        """
        return self._getRecordedAudio()
    
    # --------------------------------------------------------------------------
    # Video rendering
    #
    # These methods are used to render live video frames to a window. If a 
    # window is set, this class will automatically create the necessary
    # OpenGL texture buffers and transfers the most recent video frame to the
    # GPU when `update` is called. The `ImageStim` class can access these 
    # buffers for rendering by setting this class as the `image`.
    #

    @property
    def win(self):
        """Window to render the video frames to (`psychopy.visual.Window` or
        `None`).

        If `None`, no rendering will be done and the video frames will not be
        displayed. If a window is set, the video frames will be rendered to the
        window using OpenGL textures.

        """
        return self._win
    
    @win.setter
    def win(self, value):
        """Set the window to render the video frames to.

        This will set the window to render the video frames to. If the window
        is not `None`, it will automatically create OpenGL texture buffers for
        rendering the video frames. If the window is `None`, no rendering will
        be done and the video frames will not be displayed.

        Parameters
        ----------
        value : psychopy.visual.Window or None
            Window to render the video frames to. If `None`, no rendering will
            be done and the video frames will not be displayed.

        """
        self.setWin(value)

    def setWin(self, win):
        """Set the window to render the video frames to.

        Parameters
        ----------
        win : psychopy.visual.Window
            Window to render the video frames to. If `None`, no rendering will
            be done and the video frames will not be displayed.

        """
        self._win = win

        if self._capture is None or not self._capture.isOpen:
            return  # nothing to do if we don't have a player

        # if we have a window, setup texture buffers for displaying
        if self._win is not None:
            self._setupTextureBuffers()
            return
        
        # if we don't have a window, free any texture buffers
        self._freeTextureBuffers()  # free any existing buffers

    @property
    def interpolate(self):
        """Whether the video texture should be filtered using linear or nearest
        neighbor interpolation (`bool`).

        If `True`, the video texture will be filtered using linear interpolation.
        If `False`, the video texture will be filtered using nearest neighbor
        interpolation (pass-through). Default is `True`.

        """
        return self._interpolate
    
    @interpolate.setter
    def interpolate(self, value):
        """Set whether the video texture should be filtered using linear or 
        nearest neighbor interpolation.

        Parameters
        ----------
        value : bool
            If `True`, the video texture will be filtered using linear
            interpolation. If `False`, the video texture will be filtered using
            nearest neighbor interpolation (pass-through). Default is `True`.

        """
        self.setTextureFilter(value)

    def setTextureFilter(self, smooth=True):
        """Set whether the video texture should be filtered using linear or 
        nearest neighbor interpolation.

        Parameters
        ----------
        smooth : bool
            If `True`, the video texture will be filtered using linear
            interpolation. If `False`, the video texture will be filtered using
            nearest neighbor interpolation (pass-through.) Default is `True`.

        """
        self._interpolate = bool(smooth)
        self._texFilterNeedsUpdate = True  # flag to update texture filtering

    def _freeTextureBuffers(self):
        """Free any texture buffers used by the camera.

        This is used to free up any texture buffers used by the camera. This
        is called when the camera is closed or when the window is closed.
        """
        import pyglet.gl as GL  # needed for OpenGL texture management

        try:
            # delete buffers and textures if previously created
            if self._pixbuffId is not None and self._pixbuffId.value > 0:
                GL.glDeleteBuffers(1, self._pixbuffId)
            # delete the old texture if present
            if self._textureId is not None and self._textureId.value > 0:
                GL.glDeleteTextures(1, self._textureId)
        except (TypeError, AttributeError):
            pass
        
        # clear the IDs
        self._pixbuffId = GL.GLuint(0)
        self._textureId = GL.GLuint(0)

    def _setupTextureBuffers(self):
        """Setup texture buffers for the camera.

        This allocates OpenGL texture buffers for video frames to be written
        to which then can be rendered to the screen. This is only called if the
        camera is opened and a window is set.

        """
        if self.win is None:
            return 

        self._freeTextureBuffers()  # free any existing buffers

        import pyglet.gl as GL

        # get the size of the movie frame and compute the buffer size
        vidWidth, vidHeight = self.frameSize
        nBufferBytes = self._texBufferSizeBytes = (
            vidWidth * vidHeight * 3)

        # Create the pixel buffer object which will serve as the texture memory
        # store. Pixel data will be copied to this buffer each frame.
        GL.glGenBuffers(1, ctypes.byref(self._pixbuffId))
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, self._pixbuffId)
        GL.glBufferData(
            GL.GL_PIXEL_UNPACK_BUFFER,
            nBufferBytes * ctypes.sizeof(GL.GLubyte),
            None,
            GL.GL_STREAM_DRAW)  # one-way app -> GL
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)

        # Create a texture which will hold the data streamed to the pixel
        # buffer. Only one texture needs to be allocated.
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glGenTextures(1, ctypes.byref(self._textureId))
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._textureId)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGB8,
            vidWidth, vidHeight,  # frame dims in pixels
            0,
            GL.GL_RGB,
            GL.GL_UNSIGNED_BYTE,
            None)

        # setup texture filtering
        if self._interpolate:
            texFilter = GL.GL_LINEAR
        else:
            texFilter = GL.GL_NEAREST

        GL.glTexParameteri(
            GL.GL_TEXTURE_2D,
            GL.GL_TEXTURE_MAG_FILTER,
            texFilter)
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D,
            GL.GL_TEXTURE_MIN_FILTER,
            texFilter)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)

        GL.glFlush()  # make sure all buffers are ready

    def _pixelTransfer(self):
        """Copy pixel data from most recent video frame to texture.

        This is called when a new frame is available. The pixel data is copied
        from the video frame to the texture store on the GPU.

        """
        if self.win is None:
            return  # no window to render to
    
        if self._lastFrame is None:
            return  # no frame to upload
        
        import pyglet.gl as GL
        
        # get the size of the movie frame and compute the buffer size
        vidWidth, vidHeight = self.frameSize
        
        # compute the buffer size
        nBufferBytes = self._texBufferSizeBytes

        # bind pixel unpack buffer
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, self._pixbuffId)

        # Free last storage buffer before mapping and writing new frame
        # data. This allows the GPU to process the extant buffer in VRAM
        # uploaded last cycle without being stalled by the CPU accessing it.
        GL.glBufferData(
            GL.GL_PIXEL_UNPACK_BUFFER,
            nBufferBytes * ctypes.sizeof(GL.GLubyte),
            None,
            GL.GL_STREAM_DRAW)

        # Map the buffer to client memory, `GL_WRITE_ONLY` to tell the
        # driver to optimize for a one-way write operation if it can.
        bufferPtr = GL.glMapBuffer(
            GL.GL_PIXEL_UNPACK_BUFFER,
            GL.GL_WRITE_ONLY)

        # Make sure the frame is in RGB before uploading it, since the camera
        # hands frames over in whatever format it is streaming in. The result is
        # stored back on the frame so that redisplaying it costs nothing.
        colorData = self._lastFrame.colorData = self._convertFrameToRGB(
            self._lastFrame.colorData)

        # map the video frame to a memoryview
        # suggested by Alex Forrence (aforren1) originally in PR #6439
        # videoBuffer = self._lastFrame[0].to_memoryview()[0].memview
        videoBuffer = colorData.to_memoryview()[0].memview
        videoFrameArray = np.frombuffer(videoBuffer, dtype=np.uint8)

        # copy the frame data to the buffer
        ctypes.memmove(bufferPtr,
            videoFrameArray.ctypes.data,
            nBufferBytes)

        # Very important that we unmap the buffer data after copying, but
        # keep the buffer bound for setting the texture.
        GL.glUnmapBuffer(GL.GL_PIXEL_UNPACK_BUFFER)

        # bind the texture in OpenGL
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._textureId)

        # copy the PBO to the texture (blocks on AMD for some reason)
        GL.glTexSubImage2D(
            GL.GL_TEXTURE_2D, 0, 0, 0,
            vidWidth, vidHeight,
            GL.GL_RGB,
            GL.GL_UNSIGNED_BYTE,
            0)  # point to the presently bound buffer

        # update texture filtering only if needed
        if self._texFilterNeedsUpdate:
            if self._interpolate:
                texFilter = GL.GL_LINEAR
            else:
                texFilter = GL.GL_NEAREST

            GL.glTexParameteri(
                GL.GL_TEXTURE_2D,
                GL.GL_TEXTURE_MAG_FILTER,
                texFilter)
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D,
                GL.GL_TEXTURE_MIN_FILTER,
                texFilter)

            self._texFilterNeedsUpdate = False

        # important to unbind the PBO
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)

    @property
    def colorTexture(self):
        """OpenGL texture ID for the most recent video frame (`int` or `None`).

        This is the OpenGL texture ID that can be used to render the most
        recent video frame to a window. If no window is set, this will be `None`.
        """
        if self._textureId is None or self._textureId.value <= 0:
            return None
        
        return self._textureId

    @property
    def colorTextureSizeBytes(self):
        """Size of the texture buffer used for rendering video frames 
        (`int` or `None`).

        This returns the size of the texture buffer in bytes used for rendering
        video frames. This is only valid if the camera is opened.

        """
        if self._cameraInfo is None:
            return None

        return self._texBufferSizeBytes
    
    # --------------------------------------------------------------------------
    # Movie writer platform-specific methods
    # 
    # These are used to write frames to a movie file. We used to use the 
    # `MovieFileWriter` class for this, but for now were implimenting this 
    # directly in the camera class. This may change in the future.
    #

    def _elapsedInRecording(self, absTime):
        """Get how far into the current recording a frame was captured.

        Parameters
        ----------
        absTime : float
            Time the frame was captured, on the local monotonic clock.

        Returns
        -------
        float
            Seconds from the start of the recording, never negative.

        """
        if self._tRecordingStart < 0:  # no frame has started the recording yet
            return 0.0

        return max(0.0, absTime - self._tRecordingStart)

    def _openMovieFileWriterFFPyPlayer(self, filename, encoderOpts=None):
        """Open a movie file writer using the FFPyPlayer library.

        Parameters
        ----------
        filename : str
            File to save the resulting video to, should include the extension.
        encoderOpts : dict or None
            Options to pass to the encoder. This is a dictionary of options
            specific to the encoder library being used. See the documentation
            for `~psychopy.tools.movietools.MovieFileWriter` for more details.

        """
        from ffpyplayer.writer import MediaWriter

        encoderOpts = encoderOpts or {}

        # options to configure the writer
        frameWidth, frameHeight = self.frameSize

        writerOptions = {
            'pix_fmt_in': 'yuv420p',  # default for now using mp4
            'width_in': frameWidth,
            'height_in': frameHeight,
            'codec': 'libx264',
            'frame_rate': (int(self._capture.frameRate), 1)}

        self._curPTS = 0.0  # current pts for the movie writer
        # `MediaWriter` derives the stream time base from the frame rate it is
        # given, so timestamps can only land on multiples of the frame interval.
        # Frames are snapped to those ticks, and `_lastWrittenTick` keeps that
        # from ever producing two frames with the same timestamp, which the
        # muxer rejects.
        self._movieWriterTicksPerSec = float(writerOptions['frame_rate'][0])
        self._lastWrittenTick = -1

        self._generatePTS = False  # whether to generate PTS for the movie writer
        if filename.endswith('.mp4'): 
            self._generatePTS = True  # generate PTS for mp4 files
            logging.debug(
                "MP4 format detected, PTS will be generated for the movie " \
                "writer.")

        self._movieWriter = MediaWriter(
            filename, 
            [writerOptions], 
            fmt='mp4',
            overwrite=True,  # overwrite existing file
            libOpts=encoderOpts)

    def _submitFrameToFileFFPyPlayer(self, frames):
        """Submit a frame to the movie file writer thread using FFPyPlayer.

        This is used to submit frames to the movie file writer thread. It is
        called by the camera interface when a new frame is captured.

        Parameters
        ----------
        frames : list of tuples
            Color data and presentation timestamps to submit to the movie file 
            writer thread.

        Returns
        -------
        int
            Number of bytes written the the movie file.

        """
        if self._movieWriter is None:
            return 0
            # raise RuntimeError(
            #     "Attempting to call `_submitFrameToFileFFPyPlayer()` before "
            #     "`_openMovieFileWriterFFPyPlayer()`, or writer was closed.")
        
        from ffpyplayer.pic import SWScale
        
        if not isinstance(frames, list):
            frames = [frames]  # ensure frames is a list

        # write frames to the movie file writer
        bytesOut = 0
        for colorData, _, _, absTime in frames:
            # do color conversion if needed
            frameWidth, frameHeight = colorData.get_size()
            sws = SWScale(
                frameWidth, frameHeight,
                colorData.get_pixel_format(),
                ofmt='yuv420p')

            # Place the frame at the point in the recording it was captured,
            # rather than counting frames off at the nominal rate, which would
            # play the recording back too fast whenever the camera ran slow.
            # Snap to the stream's tick grid, keeping timestamps increasing.
            tick = int(round(
                self._elapsedInRecording(absTime) * self._movieWriterTicksPerSec))
            tick = max(tick, self._lastWrittenTick + 1)
            self._lastWrittenTick = tick
            self._curPTS = tick / self._movieWriterTicksPerSec

            # we get an EOF error when the movie writer is fully drained, catch 
            # it and ignore it
            try:
                bytesOut = self._movieWriter.write_frame(
                    img=sws.scale(colorData),
                    pts=self._curPTS,
                    stream=0)
            except Exception as e:
                pass

        return bytesOut

    def _closeMovieFileWriterFFPyPlayer(self):
        """Close the movie file writer using the FFPyPlayer library.

        This will close the movie file writer and free up any resources used by
        the writer. If the writer is not open, this will do nothing.
        """
        if self._movieWriter is not None:
            logging.debug(
                "Closing movie file writer using FFPyPlayer...")
            self._movieWriter.close()
        # else:
        #     logging.debug(
        #         "Attempting to call `_closeMovieFileWriterFFPyPlayer()` "
        #         "without an open movie file writer.")

        self._movieWriter = None

    def _openMovieFileWriterPyAV(self, filename, encoderOpts=None):
        """Open a movie file writer using PyAV.

        Parameters
        ----------
        filename : str
            File to save the resulting video to, should include the extension.
        encoderOpts : dict or None
            Options to pass to the encoder, as a mapping of FFmpeg option names
            to values (e.g. `{'crf': '23', 'preset': 'veryfast'}`).

        """
        import av
        from fractions import Fraction

        encoderOpts = encoderOpts or {}

        frameWidth, frameHeight = self.frameSize

        # The encoder needs an exact rational frame rate, but cameras report
        # theirs as a float (often something like 29.97), so approximate it.
        frameRate = self._capture.frameRate
        outFrameRate = Fraction(frameRate).limit_denominator(1001)

        # Frames are timestamped by when they were actually captured rather than
        # counted off at the nominal rate, because cameras routinely deliver
        # below the rate they advertise (auto-exposure alone can halve it).
        # Counting frames would make those recordings play back too fast and
        # drift against the audio track, so the time base here is a fine one
        # that can express whatever intervals the camera actually produced.
        self._movieWriterTimeBase = Fraction(1, 90000)

        self._movieWriter = av.open(filename, mode='w')
        self._movieWriterStream = self._movieWriter.add_stream(
            'libx264', rate=outFrameRate)
        self._movieWriterStream.width = frameWidth
        self._movieWriterStream.height = frameHeight
        self._movieWriterStream.pix_fmt = 'yuv420p'
        self._movieWriterStream.codec_context.time_base = \
            self._movieWriterTimeBase
        if encoderOpts:
            self._movieWriterStream.options = {
                str(key): str(val) for key, val in encoderOpts.items()}

        # cached converter to yuv420p, reused for every frame written
        from av.video.reformatter import VideoReformatter
        self._movieWriterReformatter = VideoReformatter()

        self._nFramesWritten = 0
        self._curPTS = 0.0  # current pts for the movie writer

        logging.debug(
            "Opened movie file writer using PyAV, writing {}x{} @{} fps to "
            "'{}'".format(frameWidth, frameHeight, outFrameRate, filename))

    def _frameToAVVideoFrame(self, colorData):
        """Get a captured frame as an `av.VideoFrame` ready to be encoded.

        Parameters
        ----------
        colorData : av.VideoFrame or _RGBFrameAdapter
            Frame as handed over by the camera interface.

        Returns
        -------
        av.VideoFrame
            The frame converted to the pixel format the encoder wants.

        """
        import av

        if isinstance(colorData, _RGBFrameAdapter):
            colorData = av.VideoFrame.from_ndarray(
                colorData.to_ndarray(format='rgb24'), format='rgb24')

        return self._movieWriterReformatter.reformat(
            colorData, format='yuv420p')

    def _submitFrameToFilePyAV(self, frames):
        """Submit a frame to the movie file writer using PyAV.

        This is used to submit frames to the movie file writer. It is called by
        the camera interface when a new frame is captured.

        Parameters
        ----------
        frames : list of tuples
            Color data and presentation timestamps to submit to the movie file
            writer.

        Returns
        -------
        int
            Number of bytes written to the movie file.

        """
        if self._movieWriter is None:
            return 0

        if not isinstance(frames, list):
            frames = [frames]  # ensure frames is a list

        bytesOut = 0
        for colorData, _, _, absTime in frames:
            avFrame = self._frameToAVVideoFrame(colorData)

            # place the frame at the point in the recording it was captured
            self._curPTS = self._elapsedInRecording(absTime)
            avFrame.pts = int(round(self._curPTS / self._movieWriterTimeBase))
            avFrame.time_base = self._movieWriterTimeBase

            try:
                for packet in self._movieWriterStream.encode(avFrame):
                    bytesOut += packet.size
                    self._movieWriter.mux(packet)
            except Exception as e:
                logging.error(
                    "Error writing frame {} to movie file: {}".format(
                        self._nFramesWritten, e))

            self._nFramesWritten += 1

        return bytesOut

    def _closeMovieFileWriterPyAV(self):
        """Close the movie file writer using PyAV.

        This flushes any frames still held by the encoder and closes the output
        file. If the writer is not open, this will do nothing.
        """
        if self._movieWriter is None:
            return

        logging.debug("Closing movie file writer using PyAV...")

        try:
            # flush whatever the encoder is still holding on to
            if self._movieWriterStream is not None:
                for packet in self._movieWriterStream.encode(None):
                    self._movieWriter.mux(packet)
        except Exception as e:
            logging.error(
                "Error flushing the movie file writer: {}".format(e))
        finally:
            self._movieWriterStream = None
            self._movieWriterReformatter = None
            try:
                self._movieWriter.close()
            except Exception as e:
                logging.error("Error closing the movie file: {}".format(e))
            self._movieWriter = None

    def _openMovieFileWriterOpenCV(self, filename, encoderOpts=None):
        """Open a movie file writer using OpenCV.

        Parameters
        ----------
        filename : str
            File to save the resulting video to, should include the extension.
        encoderOpts : dict or None
            Options for the encoder. OpenCV exposes very little of its encoder,
            so only `'fourcc'` (the FourCC code of the codec to write with,
            `'mp4v'` by default) and `'bufferSecs'` (how many seconds of video
            the encoder may fall behind by before frames are dropped) are
            understood here. Anything else is ignored.

        """
        encoderOpts = encoderOpts or {}

        frameSize = self.frameSize
        if frameSize is None:
            raise CameraNotReadyError(
                "Cannot open a movie file writer before the camera stream is "
                "open, since the size of the frames it will be given is not "
                "known yet.")

        frameWidth, frameHeight = frameSize

        # Frames are placed in the file by when they were captured rather than
        # counted off at this rate, so a camera delivering below its nominal
        # rate still produces a recording which plays back at the right speed.
        # See `_OpenCVMovieWriter` for how that is done without timestamps.
        frameRate = self._capture.frameRate
        if not frameRate or frameRate <= 0:
            frameRate = 30.0
            logging.warning(
                "Camera did not report a frame rate, writing the video at {} "
                "fps.".format(frameRate))

        unknownOpts = set(encoderOpts) - {'fourcc', 'bufferSecs'}
        if unknownOpts:
            logging.warning(
                "The OpenCV movie writer does not understand the encoder "
                "option(s) {}, they will be ignored.".format(
                    ", ".join(repr(opt) for opt in sorted(unknownOpts))))

        self._movieWriter = _OpenCVMovieWriter(
            filename,
            frameSize=(frameWidth, frameHeight),
            frameRate=frameRate,
            fourcc=encoderOpts.get('fourcc', 'mp4v'),
            queueSecs=float(encoderOpts.get('bufferSecs', 10.0)))

        self._nFramesWritten = 0
        self._curPTS = 0.0  # current pts for the movie writer

    def _submitFrameToFileOpenCV(self, frames):
        """Submit a frame to the movie file writer using OpenCV.

        This is used to submit frames to the movie file writer. It is called by
        the camera interface when a new frame is captured. Frames are queued
        rather than encoded here, so this returns without waiting for the
        encoder; see `_OpenCVMovieWriter`.

        Parameters
        ----------
        frames : list of tuples
            Color data and presentation timestamps to submit to the movie file
            writer.

        Returns
        -------
        int
            Always `0`. OpenCV does not report how much it has written, unlike
            the FFmpeg based writers.

        """
        if self._movieWriter is None:
            return 0

        if not isinstance(frames, list):
            frames = [frames]  # ensure frames is a list

        for colorData, _, _, absTime in frames:
            # place the frame at the point in the recording it was captured
            self._curPTS = self._elapsedInRecording(absTime)
            self._movieWriter.write(
                self._convertFrameToRGB(colorData), self._curPTS)
            self._nFramesWritten += 1

        return 0

    def _closeMovieFileWriterOpenCV(self):
        """Close the movie file writer using OpenCV.

        This waits for the encoder to work through any frames still queued and
        closes the output file. If the writer is not open, this will do
        nothing.
        """
        if self._movieWriter is None:
            return

        logging.debug("Closing movie file writer using OpenCV...")

        try:
            self._movieWriter.close()
        except Exception as e:
            logging.error("Error closing the movie file: {}".format(e))
        finally:
            self._movieWriter = None

    # 
    # Movie file writer methods
    #
    # These methods are used to open and close a movie file writer to save
    # frames to disk. We don't expose these methods to the user directly, but
    # they are used internally.
    #

    def _openMovieFileWriter(self, encoderLib=None, encoderOpts=None):
        """Open a movie file writer to save frames to disk.

        This will open a movie file writer to save frames to disk. The frames
        will be saved to a temporary file and then merged with the audio 
        track (if available) when `save()` is called.

        Parameters
        ----------
        encoderLib : str or None
            Encoder library to use for saving the video. This can be
            `'ffpyplayer'`, `'pyav'` or `'opencv'`. If `None`, the same library
            that was used to open the camera stream. Default is `None`.
        encoderOpts : dict or None
            Options to pass to the encoder. This is a dictionary of options
            specific to the encoder library being used. See the documentation
            for `~psychopy.tools.movietools.MovieFileWriter` for more details.

        Returns
        -------
        str
            Path to the temporary file that will be used to save the video. The
            file will be deleted when the movie file writer is closed or when
            `save()` is called.

        """
        with self._movieWriterLock:
            return self._openMovieFileWriterLocked(encoderLib, encoderOpts)

    def _openMovieFileWriterLocked(self, encoderLib=None, encoderOpts=None):
        """Body of `_openMovieFileWriter()`, called with the writer lock held.
        """
        if self._movieWriter is not None:
            return self._tempVideoFile  # already open, return temp file
        
        if encoderLib is None:
            encoderLib = self._cameraLib
        logging.debug(
            "Using encoder library '{}' to save video.".format(encoderLib))
        
        # check if we have a temporary file to write to
        import tempfile
        # create a temporary file to write the video to
        tempVideoFile = tempfile.NamedTemporaryFile(
            suffix='.mp4', delete=True)
        self._tempVideoFile = tempVideoFile.name
        tempVideoFile.close()
        
        logging.debug("Using temporary file '{}' for video.".format(self._tempVideoFile))  
            
        if encoderLib == CAMERA_LIB_FFPYPLAYER:
            self._openMovieFileWriterFFPyPlayer(
                self._tempVideoFile, encoderOpts=encoderOpts)
        elif encoderLib == CAMERA_LIB_PYAV:
            self._openMovieFileWriterPyAV(
                self._tempVideoFile, encoderOpts=encoderOpts)
        elif encoderLib == CAMERA_LIB_OPENCV:
            self._openMovieFileWriterOpenCV(
                self._tempVideoFile, encoderOpts=encoderOpts)
        else:
            raise ValueError(
                "Invalid value for parameter `encoderLib`, expected one of "
                "`'ffpyplayer'`, `'pyav'` or `'opencv'`.")

        # Remember which writer was opened, since frames have to be submitted
        # to it and it has to be closed through the same library that opened
        # it, which is not necessarily the one the camera is captured with.
        self._encoderLib = encoderLib

        self._curPTS = 0.0  # reset the current PTS for the movie writer

        return self._tempVideoFile

    def _submitFrameToFile(self, frames, pts=None):
        """Submit a frame to the movie file writer thread.

        This is used to submit frames to the movie file writer thread. It is
        called by the camera interface when a new frame is captured.

        Parameters
        ----------
        frames : MovieFrame
            Frame to submit to the movie file writer thread.
        pts : float or None
            Presentation timestamp for the frame. If `None`, timestamps will be
            generated automatically by the movie file writer. This is only used
            if the movie file writer is configured to generate PTS values.

        """
        tStart = time.time()  # start time for the operation
        with self._movieWriterLock:
            if self._movieWriter is None:
                # the writer has been closed (or was never opened), drop the
                # frames rather than write to a file which is going away
                return 0

            if self._encoderLib == CAMERA_LIB_FFPYPLAYER:
                toReturn = self._submitFrameToFileFFPyPlayer(frames)
            elif self._encoderLib == CAMERA_LIB_PYAV:
                toReturn = self._submitFrameToFilePyAV(frames)
            elif self._encoderLib == CAMERA_LIB_OPENCV:
                toReturn = self._submitFrameToFileOpenCV(frames)
            else:
                raise ValueError(
                    "Invalid value for parameter `encoderLib`, expected one of "
                    "`'ffpyplayer'`, `'pyav'` or `'opencv'`.")
        
        logging.debug(
            "Submitted {} frames to the movie file writer (took {:.6f} seconds)".format(
                len(frames), time.time() - tStart))
        
        return toReturn
        
    def _closeMovieFileWriter(self):
        """Close the movie file writer.

        This will close the movie file writer and free up any resources used by
        the writer. If the writer is not open, this will do nothing.
        """
        with self._movieWriterLock:
            if self._movieWriter is None:
                # logging.warning(
                #     "Attempting to call `_closeMovieFileWriter()` without an "
                #     "open movie file writer.")
                return
            
            if self._encoderLib == CAMERA_LIB_FFPYPLAYER:
                self._closeMovieFileWriterFFPyPlayer()
            elif self._encoderLib == CAMERA_LIB_PYAV:
                self._closeMovieFileWriterPyAV()
            elif self._encoderLib == CAMERA_LIB_OPENCV:
                self._closeMovieFileWriterOpenCV()
            else:
                raise ValueError(
                    "Invalid value for parameter `encoderLib`, expected one of "
                    "`'ffpyplayer'`, `'pyav'` or `'opencv'`.")

            self._movieWriter = None

    # --------------------------------------------------------------------------
    # Destructor
    #

    def __del__(self):
        """Try to cleanly close the camera and output file.
        """
        # Exceptions here are swallowed rather than handled: this may run during
        # interpreter shutdown, when the module globals it needs are already
        # gone, and there is nothing useful to be done about a failure anyway.
        if hasattr(self, '_capture'):
            if self._capture is not None:
                try:
                    self.close()
                except Exception:
                    pass

        if hasattr(self, '_movieWriter'):
            if self._movieWriter is not None:
                try:
                    # go through the writer's own close so the encoder is
                    # flushed, otherwise the last frames never reach the file
                    self._closeMovieFileWriter()
                except Exception:
                    pass


DeviceManager.registerClassAlias("camera", "psychopy.hardware.camera.Camera")

# ------------------------------------------------------------------------------
# Functions
#

def _getCameraInfoMacOS(cameraLib=CAMERA_LIB_FFPYPLAYER):
    """Get a list of capabilities associated with a camera attached to the 
    system.

    This is used by `getCameraInfo()` for querying camera details on MacOS.
    Don't call this function directly unless testing.

    Cameras are enumerated through AVFoundation, which is independent of the
    capture library which will later open them, so the same information serves
    every backend.

    Parameters
    ----------
    cameraLib : str
        Capture library to record against the returned descriptors, one of
        `'ffpyplayer'` or `'pyav'`.

    Returns
    -------
    list of CameraInfo
        List of camera descriptors.

    """
    if platform.system() != 'Darwin':
        raise OSError(
            "Cannot query cameras with this function, platform not 'Darwin'.")

    # import objc  # may be needed in the future for more advanced stuff
    import AVFoundation as avf  # only works on MacOS
    import CoreMedia as cm

    # get a list of capture devices
    allDevices = avf.AVCaptureDevice.devices()

    # get video devices
    videoDevices = {}
    devIdx = 0
    for device in allDevices:
        devFormats = device.formats()
        if devFormats[0].mediaType() != 'vide':  # not a video device
            continue

        # camera details
        cameraName = device.localizedName()

        # found video formats
        supportedFormats = []
        for _format in devFormats:
            # get the format description object
            formatDesc = _format.formatDescription()

            # get dimensions in pixels of the video format
            dimensions = cm.CMVideoFormatDescriptionGetDimensions(formatDesc)
            frameHeight = dimensions.height
            frameWidth = dimensions.width

            # Extract the codec in use, pretty useless since FFMPEG uses its
            # own conventions, we'll need to map these ourselves to those
            # values
            codecType = cm.CMFormatDescriptionGetMediaSubType(formatDesc)

            # Convert codec code to a FourCC code using the following byte
            # operations.
            #
            # fourCC = ((codecCode >> 24) & 0xff,
            #           (codecCode >> 16) & 0xff,
            #           (codecCode >> 8) & 0xff,
            #           codecCode & 0xff)
            #
            pixelFormat4CC = ''.join(
                [chr((codecType >> bits) & 0xff) for bits in (24, 16, 8, 0)])

            # Get the range of supported framerate, use the largest since the
            # ranges are rarely variable within a format.
            frameRateRange = _format.videoSupportedFrameRateRanges()[0]
            frameRateMax = frameRateRange.maxFrameRate()
            # frameRateMin = frameRateRange.minFrameRate()  # don't use for now

            # Create a new camera descriptor
            thisCamInfo = CameraInfo(
                index=devIdx,
                name=cameraName,
                pixelFormat=pixelFormat4CC,  # macs only use pixel format
                codecFormat=u'Null',
                frameSize=(int(frameWidth), int(frameHeight)),
                frameRate=frameRateMax,
                cameraAPI=u'AVFoundation',
                cameraLib=cameraLib,
            )

            supportedFormats.append(thisCamInfo)

            devIdx += 1

        # add to output dictionary
        videoDevices[cameraName] = supportedFormats

    return videoDevices


def _getDShowDevicesPyAV():
    """Enumerate DirectShow video devices using PyAV.

    This is a fallback used by `_getCameraInfoWindows()` when `ffpyplayer` is
    not installed, so that the PyAV backend can be used on its own. FFmpeg has
    no API for listing devices, it only writes them to its log, so the device
    list is recovered by capturing that log.

    Only device names are recovered this way, not the formats each device
    supports, so a single descriptor with unknown settings is returned per
    camera. Install `ffpyplayer` to get the full format list.

    Returns
    -------
    list of str
        Names of the video capture devices DirectShow knows about.

    """
    import av

    deviceNames = []
    try:
        with av.logging.Capture(local=True) as logs:
            try:
                av.open(
                    'dummy', format='dshow',
                    options={'list_devices': 'true'})
            except av.FFmpegError:
                # FFmpeg always errors out after listing the devices, since
                # 'dummy' is not a device it can open
                pass
    except Exception as err:
        logging.error(
            "Could not enumerate DirectShow cameras with PyAV: {}".format(err))
        return deviceNames

    # Lines naming a device look like '"Integrated Camera" (video)' on modern
    # FFmpeg. Older builds omit the '(video)' suffix and instead group devices
    # under a 'DirectShow video devices' heading.
    inVideoSection = True
    for _, _, message in logs:
        message = message.strip()

        if message.startswith('DirectShow'):
            inVideoSection = 'video' in message
            continue

        if not message.startswith('"'):
            continue

        endQuote = message.find('"', 1)
        if endQuote < 0:
            continue

        suffix = message[endQuote + 1:].strip()
        if suffix.startswith('(') and suffix != '(video)':
            continue  # an audio device, or something else we can't capture
        if not suffix and not inVideoSection:
            continue

        deviceName = message[1:endQuote]
        if deviceName not in deviceNames:
            deviceNames.append(deviceName)

    return deviceNames


def _getCameraInfoWindows(cameraLib=CAMERA_LIB_FFPYPLAYER):
    """Get a list of capabilities for the specified associated with a camera
    attached to the system.

    This is used by `getCameraInfo()` for querying camera details on Windows.
    Don't call this function directly unless testing.

    Parameters
    ----------
    cameraLib : str
        Capture library to record against the returned descriptors, one of
        `'ffpyplayer'` or `'pyav'`.

    Returns
    -------
    list of CameraInfo
        List of camera descriptors.

    """
    if platform.system() != 'Windows':
        raise OSError(
            "Cannot query cameras with this function, platform not 'Windows'.")

    # FFPyPlayer can query the OS via DirectShow for Windows cameras. It is used
    # here even when the caller wants to capture with PyAV, since it is the only
    # one of the two which reports the formats each camera supports.
    try:
        from ffpyplayer.tools import list_dshow_devices
    except ImportError:
        if cameraLib != CAMERA_LIB_PYAV:
            raise

        logging.warning(
            "`ffpyplayer` is not installed, falling back to enumerating "
            "cameras with PyAV. Camera formats will not be reported.")

        videoDevices = {}
        for devIndex, cameraName in enumerate(_getDShowDevicesPyAV()):
            videoDevices[cameraName] = [CameraInfo(
                index=devIndex,
                name=cameraName,
                pixelFormat=CAMERA_UNKNOWN_VALUE,
                codecFormat=CAMERA_UNKNOWN_VALUE,
                frameSize=None,
                frameRate=CAMERA_NULL_FRAMERATE,
                cameraAPI=u'DirectShow',
                cameraLib=cameraLib)]

        return videoDevices

    videoDevs, _, names = list_dshow_devices()

    # get all the supported modes for the camera
    videoDevices = {}

    # iterate over names
    devIndex = 0
    for devURI in videoDevs.keys():
        supportedFormats = []
        cameraName = names[devURI]
        for _format in videoDevs[devURI]:
            pixelFormat, codecFormat, frameSize, frameRateRng = _format
            _, frameRateMax = frameRateRng
            temp = CameraInfo(
                index=devIndex,
                name=cameraName,
                pixelFormat=pixelFormat,
                codecFormat=codecFormat,
                frameSize=frameSize,
                frameRate=frameRateMax,
                cameraAPI=u'DirectShow',
                cameraLib=cameraLib,
            )
            supportedFormats.append(temp)
            devIndex += 1

        videoDevices[names[devURI]] = supportedFormats

    return videoDevices


def _getCameraInfoLinux(cameraLib=CAMERA_LIB_FFPYPLAYER):
    """Get camera information on Linux systems.

    This is used by `getCameraInfo()` for querying camera details on Linux. Don't
    call this function directly unless testing. Requires `v4l2-ctl` to be installed
    on the host system. If the command is not found, an empty list is returned.

    Cameras are enumerated through `v4l2-ctl`, which is independent of the
    capture library which will later open them, so the same information serves
    every backend.

    Parameters
    ----------
    cameraLib : str
        Capture library to record against the returned descriptors, one of
        `'ffpyplayer'` or `'pyav'`.

    Returns
    -------
    list of CameraInfo
        List of camera descriptors.
    
    """
    if platform.system() != 'Linux':
        raise OSError(
            "Cannot query cameras with this function, platform not 'Linux'.")

    # get video devices
    videoDevices = {}

    # find devices in /dev
    import glob
    devFiles = glob.glob('/dev/video*')

    if not devFiles:
        return videoDevices
    
    # sort the device files
    devFiles.sort()

    # call ffmpeg to get camera details
    import subprocess as sp
    for vf in devFiles:
        try:
            proc = sp.Popen(
                ['v4l2-ctl', '--list-formats-ext', '-d', vf],
                stderr=sp.PIPE,
                stdout=sp.PIPE
            )
            stdout, stderr = proc.communicate()
            output = stdout.decode('utf-8')
        except Exception as err:
            logging.error(f"Could not query cameras via v4l2-ctl: {err}")
            return videoDevices

        if not output:
            continue

        # parse the output
        lines = output.split('\n')
        lines = [line.strip() for line in lines]

        cameraModes = {}
        pixelFormat = None
        devIndex = 0
        for line in lines:
            if line.startswith('[') and line[1:2].isdigit():
                modeIdx = int(line[1:line.index(']')])
                # get the pixel format
                pixelFormat = line.split(' ')[1].strip("'").strip()
                cameraModes[modeIdx] = []
                continue

            if pixelFormat is None:  # no pixel format, skip
                continue
            
            # inside a valid mode description
            if line.startswith('Size:'):
                sizeStr = line.split(' ')[-1].strip()
                if 'x' in sizeStr:
                    width, height = sizeStr.split('x')
                    width = int(width.strip())
                    height = int(height.strip())
                else:
                    width = height = 0
                continue

            if line.startswith('Interval:'):
                fpsStr = line.split('(')[-1].rstrip(')').strip()
                fpsVal = float(fpsStr.split(' ')[0].strip())
                cameraModes[modeIdx].append(
                    (devIndex, pixelFormat, (width, height), fpsVal))
                devIndex += 1

        if not cameraModes:  # reject anything without modes
            continue

        # reformat into the output structure
        supportedFormats = []
        for modeIdx, modes in cameraModes.items():
            for mode in modes:
                devIndex, pixelFormat, frameSize, frameRate = mode

                pixelFormat = pixelFormat.lower()
                if pixelFormat == 'mjpg':
                    codecFormat = 'mjpg'
                    pixelFormat = None
                else:
                    codecFormat = None

                thisCamInfo = CameraInfo(
                    index=devIndex,
                    name=vf,
                    pixelFormat=pixelFormat,
                    codecFormat=codecFormat,    
                    frameSize=frameSize,
                    frameRate=frameRate,
                    cameraAPI=u'Video4Linux2',
                    cameraLib=cameraLib,
                )
                supportedFormats.append(thisCamInfo)

        videoDevices[vf] = supportedFormats

    return videoDevices


# Mapping for platform specific camera getter functions used by `getCameras`.
_cameraGetterFuncTbl = {
    'Darwin': _getCameraInfoMacOS,
    'Windows': _getCameraInfoWindows,
    'Linux': _getCameraInfoLinux, 
}


def getCameras(cameraLib=CAMERA_LIB_FFPYPLAYER):
    """Get information about installed cameras and their formats on this system.

    Use `getCameraDescriptions` to get a mapping or list of human-readable
    camera formats.

    Parameters
    ----------
    cameraLib : str
        Capture library the cameras are to be opened with, either
        `'ffpyplayer'` or `'pyav'`. Cameras are enumerated the same way for
        both; this only sets the `cameraLib` field of the descriptors returned,
        except on Windows where it decides whether enumeration may fall back to
        PyAV when `ffpyplayer` is not installed.

    Returns
    -------
    dict
        Mapping where camera names (`str`) are keys and values are and array of
        `CameraInfo` objects.

    """
    systemName = platform.system()  # get the system name

    # lookup the function for the given platform
    getCamerasFunc = _cameraGetterFuncTbl.get(systemName, None)
    if getCamerasFunc is None:  # if unsupported
        raise OSError(
            "Cannot get cameras, unsupported platform '{}'.".format(
                systemName))

    return getCamerasFunc(cameraLib=cameraLib)


def getCameraDescriptions(collapse=False, cameraLib=CAMERA_LIB_FFPYPLAYER):
    """Get a mapping or list of camera descriptions.

    Camera descriptions are a compact way of representing camera settings and
    formats. Description strings can be used to specify which camera device and
    format to use with it to the `Camera` class.

    Descriptions have the following format (example)::

        '[Live! Cam Sync 1080p] 160x120@30fps, mjpeg'

    This shows a specific camera format for the 'Live! Cam Sync 1080p' webcam
    which supports 160x120 frame size at 30 frames per second. The last value
    is the codec or pixel format used to decode the stream. Different pixel
    formats and codecs vary in performance.

    Parameters
    ----------
    collapse : bool
        Return camera information as string descriptions instead of `CameraInfo`
        objects. This provides a more compact way of representing camera formats
        in a (reasonably) human-readable format.
    cameraLib : str
        Capture library the cameras are to be opened with, either
        `'ffpyplayer'` or `'pyav'`.

    Returns
    -------
    dict or list
        Mapping (`dict`) of camera descriptions, where keys are camera names
        (`str`) and values are a `list` of format description strings associated
        with the camera. If `collapse=True`, all descriptions will be returned
        in a single flat list. This might be more useful for specifying camera
        formats from a single GUI list control.

    """
    connectedCameras = getCameras(cameraLib=cameraLib)

    cameraDescriptions = {}
    for devName, formats in connectedCameras.items():
        cameraDescriptions[devName] = [
            _format.description() for _format in formats]

    if not collapse:
        return cameraDescriptions

    # collapse to a list if requested
    collapsedList = []
    for _, formatDescs in cameraDescriptions.items():
        collapsedList.extend(formatDescs)

    return collapsedList


def getFormatsForDevice(device, cameraLib=CAMERA_LIB_FFPYPLAYER):
    """Get a list of formats available for the given device.

    Parameters
    ----------
    device : str or int
        Name or index of the device
    cameraLib : str
        Capture library the device is to be opened with, either `'ffpyplayer'`
        or `'pyav'`.

    Returns
    -------
    list
        List of formats, specified as strings in the format 
        `{width}x{height}@{frame rate}fps`
    """
    # get all devices
    connectedCameras = getCameras(cameraLib=cameraLib)
    # get formats for this device
    formats = connectedCameras.get(device, [])
    # sanitize
    formats = [f"{_format.frameSize[0]}x{_format.frameSize[1]}@{_format.frameRate}fps" for _format in formats]

    return formats


def getAllCameraInterfaces():
    """Get a list of all camera interfaces supported by the system.

    Returns
    -------
    dict
        Mapping of camera interface class names and references to the class.

    """
    # get all classes in this module
    classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)

    # filter for classes that are camera interfaces
    cameraInterfaces = {}
    for name, cls in classes:
        if issubclass(cls, BaseCameraDevice):
            cameraInterfaces[name] = cls

    return cameraInterfaces


def getOpenCameras():
    """Get a list of all open cameras.
    
    Returns
    -------
    list
        List of references to open camera objects.
    
    """
    global _openCameras

    return _openCameras.copy()


def closeAllOpenCameras():
    """Close all open cameras.
    
    This closes all open cameras and releases any resources associated with
    them. This should only be called before exiting the application or after you 
    are done using the cameras. 
    
    This is automatically called when the application exits to cleanly free up 
    resources, as it is registered with `atexit` when the module is imported.

    Returns
    -------
    int
        Number of cameras closed. Useful for debugging to ensure all cameras
        were closed.
    
    """
    global _openCameras

    numCameras = len(_openCameras)
    for cam in _openCameras:
        cam.close()

    _openCameras.clear()

    return numCameras

# ------------------------------------------------------------------------------
# Cleanup functions
#
# These functions are used to clean up resources when the application exits, 
# usually unexpectedly. This helps to ensure hardware interfaces are closed
# and resources are freed up as best we can.
#

def _closeAllCaptureInterfaces():
    """Close all open capture interfaces.

    This is registered with `atexit` to ensure that all open cameras are closed
    when the application exits. This is important to free up resources and
    ensure that cameras are not left open unintentionally.

    """
    global _openCaptureInterfaces

    for cap in _openCaptureInterfaces.copy():
        try:
            cap.close()
        except Exception as e:
            logging.error(f"Error closing camera interface {cap}: {e}")


# Register the function to close all cameras on exit
atexit.register(_closeAllCaptureInterfaces)


if __name__ == "__main__":
    ## Testing code for opening a camera and taking a short recording
    # dev = CameraDevice.getAvailableDevices()[0]
    # print(CameraDevice.getDeviceCapabilities(dev['deviceName'], by='frameRate'))

    # cam = Camera(dev, mic=5)
    # #cam.open()
    # cam.record(when=1.0)

    # t0 = time.time()
    # while time.time() - t0 < 6.0:
    #     time.sleep(0.001)

    # cam.stop()
    # cam.save('./test_camera_output.mp4')
    # cam.close()

    pass
