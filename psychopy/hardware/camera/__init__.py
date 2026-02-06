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
    'Camera',
    'CameraInfo',
    'getCameras',
    'getCameraDescriptions',
    'getOpenCameras',
    'closeAllOpenCameras',
    'renderVideo'
]

import platform
import inspect
import os
import os.path
import sys
import math
import uuid
import threading
import queue
import time
import numpy as np
import ctypes
import collections

from psychopy import core
from psychopy.constants import NOT_STARTED
from psychopy.hardware import DeviceManager
from psychopy.hardware.base import BaseDevice
from psychopy.visual.movies.frame import MovieFrame, NULL_MOVIE_FRAME_INFO
from psychopy.sound.microphone import Microphone
from psychopy.hardware.microphone import MicrophoneDevice
from psychopy.tools import systemtools as st
import psychopy.tools.movietools as movietools
import psychopy.logging as logging
from psychopy.localization import _translate

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
# Keep track of open capture interfaces so we can close them at shutdown in the
# event that the user forrgets or the program crashes.
#

_openCaptureInterfaces = set()


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
    captureLib : str
        Camera library to use for opening the camera stream. This can be either
        'ffpyplayer' or 'opencv'. If `None`, the default recommend library is 
        used.
    frameSize : tuple
        Frame size of the camera stream. This is a tuple of the form
        `(width, height)`. 
    frameRate : float
        Frame rate of the camera stream. This is the number of frames per
        second that the camera will capture. If `None`, the default frame rate
        is used. The default value is 30.0.
    pixelFormat : str or None
        Pixel format of the camera stream. This is the format in which the
        camera will capture frames. If `None`, the default pixel format is used.
        The default value is `None`.
    codecFormat : str or None
        Codec format of the camera stream. This is the codec that will be used
        to encode the camera stream. If `None`, the default codec format is
        used. The default value is `None`.
    captureAPI: str
        Camera API to use for opening the camera stream. This can be either
        'AVFoundation', 'DirectShow', or 'Video4Linux2'. If `None`, the default
        camera API is used based on the platform. The default value is `None`.
    decoderOpts : dict or None
        Decoder options for the camera stream. This is a dictionary of options
        that will be passed to the decoder when opening the camera stream. If
        `None`, the default decoder options are used. The default value is an
        empty dictionary.
    bufferSecs : float
        Number of seconds to buffer frames from the capture stream. This allows 
        frames to be buffered in memory until they are needed. This allows
        the camera stream to be read asynchronously and prevents frames from
        being dropped if the main thread is busy. The default value is 5.0 
        seconds.

    """
    def __init__(self, device, captureLib='ffpyplayer', frameSize=(640, 480), 
                 frameRate=30.0, pixelFormat=None, codecFormat=None, 
                 captureAPI=None, decoderOpts=None, bufferSecs=5.0):
        
        BaseDevice.__init__(self)

        # transform some of the params
        pixelFormat = pixelFormat if pixelFormat is not None else ''
        codecFormat = codecFormat if codecFormat is not None else ''

        # if device is an integer, get name from index
        foundProfile = None
        if isinstance(device, int):
            for profile in self.getAvailableDevices(False):
                if profile['device'] == device:
                    foundProfile = profile
                    device = profile['deviceName']
                    break
        elif isinstance(device, str):
            # if device is a string, use it as the device name
            for profile in self.getAvailableDevices(False):
                # find a device which best matches the settings
                if profile['deviceName'] != device:
                    continue

                # check if all the other params match
                paramsMatch = all([
                    profile['deviceName'] == device,
                    profile['captureLib'] == captureLib if captureLib else True,
                    profile['frameSize'] == frameSize if frameSize else True,
                    profile['frameRate'] == frameRate if frameRate else True,
                    profile['pixelFormat'] == pixelFormat if pixelFormat else True,
                    profile['codecFormat'] == codecFormat if codecFormat else True,
                    profile['captureAPI'] == captureAPI if captureAPI else True
                ])

                if not paramsMatch:
                    continue
                
                foundProfile = profile
                device = profile['deviceName']

                break

        if foundProfile is None:
            raise CameraNotFoundError(
                "Cannot find camera with index or name '{}'.".format(device))

        self._device = device

        # camera settings from profile
        self._frameSize = foundProfile['frameSize']
        self._frameRate = foundProfile['frameRate']
        self._pixelFormat = foundProfile['pixelFormat']
        self._codecFormat = foundProfile['codecFormat']
        self._captureLib = foundProfile['captureLib']
        self._captureAPI = foundProfile['captureAPI']

        # capture interface
        self._capture = None  # camera stream capture object
        self._decoderOpts = decoderOpts if decoderOpts is not None else {}
        self._bufferSecs = bufferSecs  # number of seconds to buffer frames
        self._absRecStreamStartTime = -1.0  # absolute recording start time
        self._absRecExpStartTime = -1.0

        # stream properties
        self._metadata = {}  # metadata about the camera stream

        # recording properties
        self._frameStore = []  # store frames read from the camera stream
        self._isRecording = False  # `True` if the camera is recording and frames will be captured

        # camera API to use with FFMPEG
        if captureAPI is None:
            if platform.system() == 'Windows':
                self._cameraAPI = CAMERA_API_DIRECTSHOW
            elif platform.system() == 'Darwin':
                self._cameraAPI = CAMERA_API_AVFOUNDATION
            elif platform.system() == 'Linux':
                self._cameraAPI = CAMERA_API_VIDEO4LINUX2
            else:
                raise RuntimeError(
                    "Unsupported platform: {}. Supported platforms are: {}".format(
                        platform.system(), ', '.join(self._supportedPlatforms)))
        else:
            self._cameraAPI = captureAPI
        
        # store device info
        # NB - Move above logic into `getDeviceProfile` at some point
        profile = foundProfile   # self.getDeviceProfile()
        if profile:
            self.info = CameraInfo(
                name=profile['deviceName'],
                frameSize=profile['frameSize'],
                frameRate=profile['frameRate'],
                pixelFormat=profile['pixelFormat'],
                codecFormat=profile['codecFormat'],
                cameraLib=profile['captureLib'],
                cameraAPI=profile['captureAPI']
            )
        else:
            self.info = CameraInfo()

    def isSameDevice(self, other):
        """
        Determine whether this object represents the same physical device as a given other object.

        Parameters
        ----------
        other : BaseDevice, dict
            Other device object to compare against, or a dict of params.

        Returns
        -------
        bool
            True if the two objects represent the same physical device
        """
        if isinstance(other, CameraDevice):
            return other._device == self._device
        elif isinstance(other, Camera):
            return getattr(other, "_capture", None) == self
        elif isinstance(other, dict) and "device" in other:
            return other['deviceName'] == self._device
        else:
            return False

    @staticmethod
    def getAvailableDevices(best=True):
        """
        Get all available devices of this type.

        Parameters
        ----------
        best : bool
            If True, return only the best available frame rate/resolution for each device, rather 
            than returning all. Best available spec is chosen as the highest resolution with a 
            frame rate above 30fps (or just highest resolution, if none are over 30fps).

        Returns
        -------
        list[dict]
            List of dictionaries containing the parameters needed to initialise each device.
        """
        profiles = []
        # iterate through cameras
        for cams in CameraDevice.getCameras().values():
            # if requested, filter for best spec for each device
            if best:
                allCams = cams.copy()
                lastBest = {
                    'pixels': 0,
                    'frameRate': 0
                }
                bestResolution = None
                minFrameRate = max(28, min([cam.frameRate for cam in allCams]))
                for cam in allCams:
                    # summarise spec of this cam
                    current = {
                        'pixels': cam.frameSize[0] * cam.frameSize[1],
                        'frameRate': cam.frameRate
                    }
                    # store best frame rate as a fallback
                    if bestResolution is None or current['pixels'] > lastBest['pixels']:
                        bestResolution = cam
                    # if it's better than the last, set it as the only cam
                    if current['pixels'] > lastBest['pixels'] and current['frameRate'] >= minFrameRate:
                        cams = [cam]
                # if no cameras meet frame rate requirement, use one with best resolution
                cams = [bestResolution]
            # iterate through all (possibly filtered) cameras
            for cam in cams:
                # construct a dict profile from the CameraInfo object
                profiles.append({
                    'deviceName': cam.name,
                    'deviceClass': "psychopy.hardware.camera.CameraDevice",
                    'device': cam.index,
                    'captureLib': cam.cameraLib, 
                    'frameSize': cam.frameSize, 
                    'frameRate': cam.frameRate, 
                    'pixelFormat': cam.pixelFormat, 
                    'codecFormat': cam.codecFormat, 
                    'captureAPI': cam.cameraAPI
                })

        return profiles

    @staticmethod
    def getCameras(cameraLib=None):
        """Get a list of devices this interface can open.

        Parameters  
        ----------
        cameraLib : str or None
            Camera library to use for opening the camera stream. This can be 
            either 'ffpyplayer' or 'opencv'. If `None`, the default recommend 
            library is used.

        Returns
        -------
        dict 
            List of objects which represent cameras that can be opened by this
            interface. Pass any of these values to `device` to open a stream.

        """
        if cameraLib is None:
            cameraLib = CAMERA_LIB_FFPYPLAYER

        if cameraLib == CAMERA_LIB_FFPYPLAYER:
            global _cameraGetterFuncTbl
            systemName = platform.system()  # get the system name

            # lookup the function for the given platform
            getCamerasFunc = _cameraGetterFuncTbl.get(systemName, None)
            if getCamerasFunc is None:  # if unsupported
                raise OSError(
                    "Cannot get cameras, unsupported platform '{}'.".format(
                        systemName))

            return getCamerasFunc()
    
    def _clearFrameStore(self):
        """Clear the frame store.
        """
        self._frameStore.clear()
    
    @property
    def device(self):
        """Camera device this interface is using (`Any`).
        
        This is the camera device that was passed to the constructor. It may be
        a `CameraInfo` object or a string representing the camera device.
        
        """
        return self._device
    
    @property
    def cameraLib(self):
        """Camera library this interface is using (`str`).
        
        This is the camera library that was passed to the constructor. It may be
        'ffpyplayer' or 'opencv'. If `None`, the default recommend library is 
        used.
        
        """
        return self.info.captureLib if self.info else None
    
    @property
    def frameSize(self):
        """Frame size of the camera stream (`tuple`).
        
        This is the frame size of the camera stream. It is a tuple of the form
        `(width, height)`. If the camera stream is not open, this will return
        `None`.
        
        """
        return self.info.frameSize if self.info else None
    
    @property
    def frameRate(self):
        """Frame rate of the camera stream (`float`).
        
        This is the frame rate of the camera stream. If the camera stream is
        not open, this will return `None`.
        
        """
        return self.info.frameRate if self.info else None
    
    @property
    def frameInterval(self):
        """Frame interval of the camera stream (`float`).
        
        This is the time between frames in seconds. It is calculated as
        `1.0 / frameRate`. If the camera stream is not open, this will return
        `None`.
        
        """
        return self._frameInterval
    
    @property
    def pixelFormat(self):
        """Pixel format of the camera stream (`str`).
        
        This is the pixel format of the camera stream. If the camera stream is
        not open, this will return `None`.
        
        """
        return self.info.pixelFormat if self.info else None
    
    @property
    def codecFormat(self):
        """Codec format of the camera stream (`str`).
        
        This is the codec format of the camera stream. If the camera stream is
        not open, this will return `None`.
        
        """
        return self.info.codecFormat if self.info else None
    
    @property
    def cameraAPI(self):
        """Camera API used to access the camera stream (`str`).
        
        This is the camera API used to access the camera stream. If the camera
        stream is not open, this will return `None`.
        
        """
        return self.info.cameraAPI if self.info else None
    
    @property
    def bufferSecs(self):
        """Number of seconds to buffer frames from the camera stream (`float`).
        
        This is the number of seconds to buffer frames from the camera stream.
        This allows frames to be buffered in memory until they are needed. This
        allows the camera stream to be read asynchronously and prevents frames
        from being dropped if the main thread is busy.
        
        """
        return self._bufferSecs
    
    def getMetadata(self):
        """Get metadata about the camera stream.

        Returns
        -------
        dict
            Dictionary containing metadata about the camera stream. Returns an
            empty dictionary if no metadata is available.

        """
        if self._capture is None:
            return {}

        # get metadata from the capture stream
        if self._captureLib == CAMERA_LIB_FFPYPLAYER:
            return self._capture.get_metadata() if self._capture else {}
        elif self._captureLib == CAMERA_LIB_OPENCV:
            return self._metadata
        else:
            return {}

    @property
    def frameSizeBytes(self):
        """Size of the image in bytes (`int`).
        
        This is the size of the image in bytes. It is calculated as 
        `width * height * 3`, where `width` and `height` are the dimensions of
        the camera stream. If the camera stream is not open, this will return
        `0`.
        
        """
        if self._frameSize is None:
            return 0
        
        return self._frameSizeBytes
    
    @property
    def frameCount(self):
        """Number of frames read from the camera stream (`int`).
        
        This is the number of frames read from the camera stream since the last
        time the camera was opened. If the camera stream is not open, this will
        return `0`.
        
        """
        return self._frameCount
    
    @property
    def streamTime(self):
        """Current stream time in seconds (`float`).
        
        This is the current stream time in seconds. It is calculated as the
        difference between the current time and the absolute recording start
        time. If the camera stream is not open, this will return `-1.0`.
        
        """
        if self._cameraAPI == CAMERA_API_AVFOUNDATION:
            return time.time() if self._capture is not None else -1.0
        else:
            return self._capture.get_pts() if self._capture is not None else -1.0
    
    def _toNumpyView(self, frame):
        """Convert a frame to a Numpy view.

        This function converts a frame to a Numpy view. The frame is returned as
        a Numpy array. The resulting array will be in the correct format to
        upload to OpenGL as a texture.

        Parameters
        ----------
        frame : Any
            The frame to convert.

        Returns
        -------
        numpy.ndarray
            The converted frame in RGB format.

        """
        return np.asarray(frame, dtype=np.uint8)
    
    # --------------------------------------------------------------------------
    # Platform-specific camera frame aquisition methods
    #
    # These methods are used to open, close, and read frames from the camera
    # stream. They are platform-specific and are called depending on the
    # camera library being used.
    # 

    # --------------------------------------------------------------------------
    # FFPyPlayer-specific methods 
    #

    def _openFFPyPlayer(self):
        """Open the camera stream using FFmpeg (ffpyplayer).
        
        This method should be called to open the camera stream using FFmpeg.
        It should initialize the camera and prepare it for reading frames.

        """
        # configure the camera stream reader
        ff_opts = {}  # ffmpeg options
        lib_opts = {}  # ffpyplayer options
        _camera = CAMERA_NULL_VALUE
        _frameRate = CAMERA_NULL_VALUE

        # setup commands for FFMPEG
        if self._captureAPI == CAMERA_API_DIRECTSHOW:  # windows
            ff_opts['f'] = 'dshow'
            _camera = 'video={}'.format(self.info.name)
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

            # this needs to be exactly specified if using NTSC
            if math.isclose(CAMERA_FRAMERATE_NTSC, self._frameRate):
                _frameRate = CAMERA_FRAMERATE_NOMINAL_NTSC
            else:
                _frameRate = str(self._frameRate)

            # need these since hardware acceleration is not possible on Mac yet
            lib_opts['fflags'] = 'nobuffer'
            lib_opts['flags'] = 'low_delay'
            lib_opts['pixel_format'] = self._pixelFormat
            lib_opts['use_wallclock_as_timestamps'] = '1'
            # ff_opts['framedrop'] = True
            # ff_opts['fast'] = True
        elif self._captureAPI == CAMERA_API_VIDEO4LINUX2:
            raise OSError(
                "Sorry, camera does not support Linux at this time. However, "
                "it will in future versions.")
        
        else:
            raise RuntimeError("Unsupported camera API specified.")

        # set library options
        camWidth, camHeight = self._frameSize
        logging.debug(
            "Using camera mode {}x{} at {} fps".format(
                camWidth, camHeight, _frameRate))
        
        # configure the real-time buffer size, we compute using RGB8 since this 
        # is uncompressed and represents the largest size we can expect
        self._frameSizeBytes = int(camWidth * camHeight * 3)
        framesToBufferCount = int(self._bufferSecs * self._frameRate)
        _bufferSize = int(self._frameSizeBytes * framesToBufferCount)
        logging.debug(
            "Setting real-time buffer size to {} bytes "
            "for {} seconds of video ({} frames @ {} fps)".format(
                _bufferSize, 
                self._bufferSecs,
                framesToBufferCount,
                self._frameRate)
        )

        # common settings across libraries
        ff_opts['low_delay'] = True  # low delay for real-time playback
        # ff_opts['framedrop'] = True
        # ff_opts['use_wallclock_as_timestamps'] = True
        ff_opts['fast'] = True
        # ff_opts['sync'] = 'ext'
        ff_opts['rtbufsize'] = str(_bufferSize)  # set the buffer size
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
        
        # get metadata from the capture stream
        tStart = time.time()  # start time for the stream
        metadataTimeout = 5.0  # timeout for metadata retrieval
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

        # check if the camera metadata matches the requested settings
        if streamMetadata['src_vid_size'] != tuple(self._frameSize):
            raise CameraFrameSizeNotSupportedError(
                "Camera does not support the requested frame size "
                "{size}. Supported sizes are: {supportedSizes}".format(
                    size=self._frameSize,
                    supportedSizes=streamMetadata['src_vid_size']))
        
        # pause the camera stream
        self._capture.set_pause(True)

    def _closeFFPyPlayer(self):
        """Close the camera stream opened with FFmpeg (ffpyplayer).
        
        This method should be called to close the camera stream and release any
        resources associated with it.

        """
        if self._capture is not None:
            # self._capture.set_pause(True)  # pause the stream
            self._capture.close_player()

    def _getFramesFFPyPlayer(self):
        """Get the most recent frames from the camera stream opened with FFmpeg
        (ffpyplayer).
        
        Returns
        -------
        numpy.ndarray
            Most recent frames from the camera stream. Returns `None` if no
            frames are available.

        """
        if self._capture is None:
            raise PlayerNotAvailableError(
                "Camera stream is not open. Call `open()` first.")
        
        # read all buffered frames from the camera stream until we get nothing
        recentFrames = []
        while 1:
            frame, status = self._capture.get_frame()
            
            if status == CAMERA_STATUS_EOF or status == CAMERA_STATUS_PAUSED: 
                break

            if frame is None:  # ditto 
                break

            img, curPts = frame
            if curPts < self._absRecStreamStartTime and self._isRecording:
                del img  # free the memory used by the frame
                # if the frame is before the recording start time, skip it
                continue

            self._frameCount += 1  # increment the frame count

            recentFrames.append((
                img, 
                curPts-self._absRecStreamStartTime,
                curPts))

        return recentFrames
    
    # --------------------------------------------------------------------------
    # OpenCV-specific methods
    # 

    def _convertFrameToRGBOpenCV(self, frame):
        """Convert a frame to RGB format using OpenCV.
        
        This function converts a frame to RGB format. The frame is returned as
        a Numpy array. The resulting array will be in the correct format to
        upload to OpenGL as a texture.

        Parameters
        ----------
        frame : numpy.ndarray
            The frame to convert.

        Returns
        -------
        numpy.ndarray
            The converted frame in RGB format.

        """
        import cv2 

        # this can be done in the shader to save CPU use, will figure out later
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def _openOpenCV(self):
        """Open the camera stream using OpenCV.
        
        This method should be called to open the camera stream using OpenCV.
        It should initialize the camera and prepare it for reading frames.

        """
        import cv2

        # open the camera stream
        self._capture = cv2.VideoCapture(self._device, cv2.CAP_DSHOW)
        if not self._capture.isOpened():
            raise CameraNotReadyError(
                "Failed to open camera stream (possibly caused by a device "
                "already in use by other application).")
        
        # set the camera properties
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self._frameSize[0])
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self._frameSize[1])

        # fourcc is needed to get the right pixel format
        codecFormat4cc = self._codecFormat if self._codecFormat is not None else 'MJPG'
        codecFormat4cc = codecFormat4cc.upper()  # ensure it is uppercase
        if len(codecFormat4cc) != 4:
            raise ValueError(
                "Codec format must be a 4-character string. "
                "Got: {}".format(codecFormat4cc))
        self._capture.set(
            cv2.CAP_PROP_FOURCC, 
            cv2.VideoWriter_fourcc(*codecFormat4cc))

        # set the buffer size (number of frames to buffer)
        self._capture.set(cv2.CAP_PROP_FPS, self._frameRate)
        bufferFrames = int(self._bufferSecs * self._frameRate)
        self._capture.set(cv2.CAP_PROP_BUFFERSIZE, bufferFrames)

        # compute the frame interval, needed for generating timestamps
        self._frameInterval = 1.0 / self._frameRate
        self._frameSizeBytes = int(self._frameSize[0] * self._frameSize[1] * 3)
        self._metadata = {}  # OpenCV does not provide metadata

        # populater metadata using the ffpyplayer format
        self._metadata['src_vid_size'] = tuple(self._frameSize)
        self._metadata['src_vid_fps'] = self._frameRate
        self._metadata['pixel_format'] = self._pixelFormat
        self._metadata['codec_format'] = self._codecFormat
        self._metadata['capture_lib'] = self._captureLib

        self._frameCount = 0  # reset the frame count

        logging.debug(
            "Using camera mode {}x{} at {} fps".format(
                self._frameSize[0], self._frameSize[1], self._frameRate))
        logging.debug("Camera metadata: {}".format(self._metadata))

    def _closeOpenCV(self):
        """Close the camera stream opened with OpenCV.
        
        This method should be called to close the camera stream and release any
        resources associated with it.

        """
        if self._capture is not None:
            self._capture.release()

        self._capture = None

    def _getFramesOpenCV(self):
        """Get the most recent frames from the camera stream opened with OpenCV.
        
        Returns
        -------
        numpy.ndarray
            Most recent frames from the camera stream. Returns `None` if no
            frames are available.

        """
        import cv2 

        if self._capture is None:
            raise PlayerNotAvailableError(
                "Camera stream is not open. Call `open()` first.")
        
        # read a frame from the camera stream
        recentFrames = []
        while 1:  # read frames until there are no more in the buffer
            ret, frame = self._capture.read()
            if not ret:
                break  # no more frames available

            # get timestamp
            pts = self._capture.get(cv2.CAP_PROP_POS_MSEC) / 1000.0  # convert to seconds
            if pts < self._absRecStreamStartTime and self._isRecording:
                del frame
                continue

            recentFrames.append((
                self._convertFrameToRGBOpenCV(frame), 
                self._frameCount * self._frameInterval,
                pts))

            self._frameCount += 1

        return recentFrames

    # --------------------------------------------------------------------------
    # Public methods for camera stream management
    #

    def __hash__(self):
        """Hash on the camera device name and library used."""
        return hash((self._device, self._captureLib))
    
    def open(self):
        """Open the camera stream.
        
        This method should be called to open the camera stream. It should
        initialize the camera and prepare it for reading frames.

        """
        if self._captureLib == 'ffpyplayer':
            self._openFFPyPlayer()
        elif self._captureLib == 'opencv':
            self._openOpenCV()
        else:
            raise RuntimeError(
                "Unsupported camera library: {}. Supported libraries are: {}".format(
                    self._captureLib, 
                    ', '.join([CAMERA_LIB_FFPYPLAYER, CAMERA_LIB_OPENCV])))

        global _openCaptureInterfaces
        _openCaptureInterfaces.add(self)

    def close(self):
        """Close the camera stream.
        
        This method should be called to close the camera stream and release any
        resources associated with it.

        """
        if self.isRecording:
            self.stop()  # stop the recording if it is in progress
            logging.warning(
                "CameraDevice.close() called while recording. Stopping.")

        if self._captureLib == 'ffpyplayer':
            self._closeFFPyPlayer()
        elif self._captureLib == 'opencv':
            self._closeOpenCV()

        self._capture = None  # reset the capture object

        global _openCaptureInterfaces
        if self in _openCaptureInterfaces:
            _openCaptureInterfaces.remove(self)

    @property
    def isOpen(self):
        """Check if the camera stream is open.

        Returns
        -------
        bool
            `True` if the camera stream is open, `False` otherwise.

        """
        return self._capture is not None
    
    def record(self):
        """Start recording camera frames to memory.

        This method should be called to start recording the camera stream.
        Frame timestamps will be generated based on the current time when
        this method is called. The frames will be stored and made available
        through the `getFrames()` method.

        To get precise audio synchronization:
        
            1. Start the microphone recording
            2. Store samples somehwere keeping track of the absolute time of the
               first audio sample.
            3. Call this method to start the camera recording and store the 
               returned start time.
            4. When the recording is stopped, compute the offset between the
               absolute start time of the audio recording and the absolute start
               time of the camera recording. Compute the postion of the first
               audio sample in the audio buffer by multiplying the offset by the
               sample rate of the audio recording. This will give you the
               position of the first audio sample in the audio buffer
               corresponding to the very beginning of the first camera frame.

        Returns
        -------
        float
            The absolute start time of the recording in seconds. Use this value
            to syncronize audio recording with the capture stream.

        """
        if not self.isOpen:
            raise RuntimeError("Camera stream is not open. Call `open()` first.")
        
        self._frameCount = 0  # reset the frame count
        self._clearFrameStore()  # clear the frame store
        self._capture.set_pause(False)  # start the capture stream

        # need to use a different timebase on macOS, due to a bug
        if self._captureLib == 'ffpyplayer':
            if self._cameraAPI == CAMERA_API_AVFOUNDATION:
                self._absRecStreamStartTime = time.time()
            else:
                self._absRecStreamStartTime = self._capture.get_pts()  # get the absolute start time
        else:
            self._absRecStreamStartTime = time.time()

        self._absRecExpStartTime = core.getTime()  # experiment start time in seconds
        self._isRecording = True 

        return self._absRecStreamStartTime
    
    def start(self):
        """Start recording the camera stream.

        Alias for `record()`. This method is provided for compatibility with
        other camera interfaces that may use `start()` to begin recording.

        """
        return self.record()  # start recording and return the start time

    def stop(self): 
        """Stop recording the camera stream.

        This method should be called to stop recording the camera stream. It
        will stop capturing frames from the camera and clear the frame store.

        """
        self._capture.set_pause(True)  # pause the capture stream

        if self._captureLib == 'ffpyplayer':
            if self._cameraAPI == CAMERA_API_AVFOUNDATION:
                absStopTime = time.time()
            else:
                absStopTime = self._capture.get_pts()
        else:
            absStopTime = time.time()

        self._isRecording = False

        return absStopTime

    @property
    def isRecording(self):
        """Check if the camera stream is currently recording (`bool`).

        Returns
        -------
        bool
            `True` if the camera stream is currently recording, `False`
            otherwise.

        """
        return self._isRecording
    
    def getFrames(self):
        """Get the most recent frames from the camera stream.

        This method returns frame captured since the last call to this method.
        If no frames are available or `record()` has not been previously called, 
        it returns an empty list.

        You must call this method periodically at an interval of at least 
        `bufferSecs` seconds or risk losing frames.

        Returns
        -------
        list
            List of frames from the camera stream. Returns an empty list if no
            frames are available.

        """
        if self._captureLib == 'ffpyplayer':
            return self._getFramesFFPyPlayer()
        elif self._captureLib == 'opencv':
            return self._getFramesOpenCV()
        else:
            raise RuntimeError(
                "Unsupported camera library: {}. Supported libraries are: {}".format(
                    self._captureLib, 
                    ', '.join([CAMERA_LIB_FFPYPLAYER, CAMERA_LIB_OPENCV])))
        

# class name alias for legacy support
CameraInterface = CameraDevice


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
        'opencv').

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
        elif self._captureLib == CAMERA_LIB_OPENCV:
            return 'BGR'
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
        elif self._captureLib == CAMERA_LIB_OPENCV:
            # OpenCV frames are transposed
            return (self.colorData.shape[1], self.colorData.shape[0])
    
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
            The absolute time in seconds when this frame was captured.

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

        # get the frame data in the correct format
        if self._captureLib == CAMERA_LIB_FFPYPLAYER:
            frameW, frameH = self.frameSize
            cameraFrameBuffer = self.colorData.to_memoryview()[0].memview
            cameraFrameArray = np.frombuffer(
                cameraFrameBuffer, dtype=np.uint8).reshape(
                    (frameH, frameW, 3))
            convMode = cv2.COLOR_RGB2GRAY
        elif self._captureLib == CAMERA_LIB_OPENCV:
            cameraFrameArray = self.colorData
            convMode = cv2.COLOR_BGR2GRAY

        # convert to grayscale for detection
        grayFrame = cv2.cvtColor(cameraFrameArray, convMode)

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


# keep track of camera devices that are opened
_openCameras = {}


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

    GNU/Linux is supported only by the OpenCV backend (`cameraLib='opencv'`).

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
    mic : :class:`~psychopy.sound.microphone.Microphone` or None
        Microphone to record audio samples from during recording. The microphone
        input device must not be in use when `record()` is called. The audio
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
        Interface library (backend) to use for accessing the camera. May either
        be `ffpyplayer` or `opencv`. If `None`, the default library for the
        recommended by the PsychoPy developers will be used. Switching camera 
        libraries could help resolve issues with camera compatibility. More 
        camera libraries may be installed via extension packages.
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
        mode even if a microphone is provided.

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
        
        self._cameraLib = cameraLib

        # handle device
        self._capture = None
        if isinstance(device, CameraDevice):
            # if given a device object, use it
            self._capture = device
        elif device is None:
            # if given None, get the first available device
            for name, obj in DeviceManager.getInitialisedDevices(CameraDevice).items():
                self._capture = obj
                break
            # if there are none, set one up
            if self._capture is None:
                for profile in CameraDevice.getAvailableDevices():
                    self._capture = DeviceManager.addDevice(**profile)
                    break
        elif isinstance(device, str):
            if DeviceManager.getDevice(device):
                self._capture = DeviceManager.getDevice(device)
            else:
                # get available devices
                availableDevices = CameraDevice.getAvailableDevices()
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
                self._capture = CameraDevice(
                    device=device,
                    captureLib=cameraLib,
                    frameRate=frameRate,
                    frameSize=frameSize,
                    pixelFormat=None,  # use default pixel format
                    codecFormat=None,  # use default codec format
                    captureAPI=None  # use default capture API
                )
        else:
            # anything else, try to initialise a new device from params
            self._capture = CameraDevice(
                device=device,
                captureLib=cameraLib,
                frameRate=frameRate,
                frameSize=frameSize,
                pixelFormat=None,  # use default pixel format
                codecFormat=None,  # use default codec format
                captureAPI=None  # use default capture API
            )
        # from here on in the init, use the device index as `device`
        device = self._capture.device
        # get info from device
        self._cameraInfo = self._capture.info

        # handle microphone
        self.mic = None
        if isinstance(mic, MicrophoneDevice):
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

        self._absVideoRecStartTime = -1.0
        self._absVideoRecStopTime = -1.0
        self._absAudioRecStartTime = -1.0
        self._absAudioRecStopTime = -1.0

        # computed timestamps for when 
        self._absAudioActualRecStartTime = -1.0
    
        self._absAudioRecStartPos = -1.0  # in samples
        self._absAudioRecStopPos = -1.0

        self._curPTS = 0.0  # current display timestamp
        self._isRecording = False
        self._generatePTS = False  # use genreated PTS values for frames
        
        # movie writer instance, this runs in a separate thread
        self._movieWriter = None
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
    def recordingTime(self):
        """Time in seconds since the recording started (`float`).

        This is the time since the recording started. This is useful for
        generating timestamps for frames in the recording. If the recording has
        not started, this will return `0.0`.

        """
        if self._absRecStreamStartTime < 0:
            return 0.0
        
        if self._cameraAPI == CAMERA_API_AVFOUNDATION:
            return time.time() - self._absRecStreamStartTime
        
        # for other APIs, use the PTS value
        curPts = self._capture.get_pts()
        if curPts is None:
            return 0.0
        
        # return the difference between the current PTS and the absolute start time
        return self._capture.get_pts() - self._absRecStreamStartTime

    @property
    def isReady(self):
        """Is the camera ready (`bool`)?

        The camera is ready when the following conditions are met. First, we've
        created a player interface and opened it. Second, we have received
        metadata about the stream. At this point we can assume that the camera
        is 'hot' and the stream is being read.

        This is a legacy property used to support older versions of PsychoPy. 
        The `isOpened` property should be used instead.

        """
        return self.isStarted

    @property
    def frameSize(self):
        """Size of the video frame obtained from recent metadata (`float` or
        `None`).

        Only valid after an `open()` and successive `_enqueueFrame()` call as
        metadata needs to be obtained from the stream. Returns `None` if not
        valid.
        """
        if self._cameraInfo is None:
            return None

        return self._cameraInfo.frameSize

    @property
    def frameRate(self):
        """Frame rate of the video stream (`float` or `None`).

        Only valid after an `open()` and successive `_enqueueFrame()` call as
        metadata needs to be obtained from the stream. Returns `None` if not
        valid.

        """
        if self._cameraInfo is None:
            return None

        return self._cameraInfo.frameRate

    @property
    def frameInterval(self):
        """Frame interval in seconds (`float`).

        This is the time between frames in the video stream. This is computed
        from the frame rate of the video stream. If the frame rate is not set,
        this will return `None`.

        """
        if self._cameraInfo is None or self._cameraInfo.frameRate is None:
            return -1.0

        return 1.0 / self._cameraInfo.frameRate

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
    def getCameras(cameraLib='ffpyplayer'):
        """Get information about installed cameras on this system.

        Returns
        -------
        dict
            Mapping of camera information objects.

        """
        # not pluggable yet, needs to be made available via extensions
        return CameraDevice.getCameras(
            cameraLib=cameraLib)

    @staticmethod
    def getAvailableDevices():
        devices = []
        for dev in st.getCameras():
            for spec in dev:
                devices.append({
                    'device': spec['index'],
                    'name': spec['device_name'],
                    'frameRate': spec['frameRate'],
                    'frameSize': spec['frameSize'],
                    'pixelFormat': spec['pixelFormat'],
                    'codecFormat': spec['codecFormat'],
                    'cameraAPI': spec['cameraAPI']
                })

        return devices

    @staticmethod
    def getCameraDescriptions(collapse=False):
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

        Returns
        -------
        dict or list
            Mapping (`dict`) of camera descriptions, where keys are camera names
            (`str`) and values are a `list` of format description strings
            associated with the camera. If `collapse=True`, all descriptions
            will be returned in a single flat list. This might be more useful
            for specifying camera formats from a single GUI list control.

        """
        return getCameraDescriptions(collapse=collapse)

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
    def win(self):
        """Window which frames are being presented (`psychopy.visual.Window` or 
        `None`).
        """
        return self._win
    
    @win.setter
    def win(self, value):
        self._win = value

    @property
    def frameCount(self):
        """Number of frames captured in the present recording (`int`).
        """
        if not self._isRecording:
            return 0

        totalFramesBuffered = (
            len(self._captureFrames) + self._captureThread.framesWaiting)
        
        return totalFramesBuffered

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

        """
        return self.frameCount * self._capture.frameInterval

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
        
        self._capture.open()
        self.setWin(self._win)  # set the window (if any)
        
        # open the mic when the camera opens
        if hasattr(self.mic, "open"):
            self.mic.open()

        self._isStarted = True

    def record(self, clearLastRecording=True, waitForStart=False):
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

        self._capture._clearFrameStore()

        # reset the movie writer
        self._openMovieFileWriter()

        # reset audio flags
        self._audioReady = self._videoReady = False

        # reset the last frame
        self._lastFrame = None

        # start camera recording
        self._absVideoRecStartTime = self._capture.record()

        # start microphone recording
        if self._usageMode == CAMERA_MODE_VIDEO:
            if self.mic is not None:
                audioStartTime = self.mic.start(
                    waitForStart=int(waitForStart),  # wait until the mic is ready
                )
                self._absAudioRecStartTime = self._capture.streamTime
                if waitForStart:
                    self._absAudioActualRecStartTime = audioStartTime  # time it will be ready
                else:
                    self._absAudioActualRecStartTime = self._absAudioRecStartTime

        self._isRecording = True  # set recording flag
        # do an initial poll to avoid frame dropping
        self.update()
        # mark that there's unsaved footage
        self._unsaved = True

    def start(self, waitForStart=True):
        """Start the camera stream.

        This will start the camera stream and begin decoding frames. If the
        camera is already started, this will do nothing. Use `record()` to start
        recording frames to memory.

        """
        return self.record(clearLastRecording=False, waitForStart=waitForStart)

    def stop(self):
        """Stop recording frames and audio (if available).
        """
        # poll any remaining frames and stop
        self.update()

        # stop the camera stream
        self._absVideoRecStopTime = self._capture.stop()
        
        # stop audio recording if we have a microphone
        if self.hasMic and not self.mic._stream._closed:
            _, overflows = self.mic.poll()

            if overflows > 0:
                logging.warning(
                    "Audio recording overflowed {} times before stopping, "
                    "some audio samples may be lost.".format(overflows))
            audioStopTime, _, _, _ = self.mic.stop(
                blockUntilStopped=0)
            
        self._audioReady = self._videoReady = False  # reset camera ready flags
        self._isRecording = False

        self._closeMovieFileWriter()
            
    def close(self):
        """Close the camera.

        This will close the camera stream and free up any resources used by the
        device. If the camera is currently recording, this will stop the 
        recording, but will not discard any frames. You may still call `save()`
        to save the frames to disk.

        """
        self._closeMovieFileWriter()

        self._capture.close()  # close the camera stream
        self._capture = None  # clear the capture object

        if self.mic is not None:
            self.mic.close()

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
        
        # check if we have an active movie writer
        if self._movieWriter is not None:
            self._movieWriter.close()  # close the movie writer

        # check if we have a temp movie file
        videoTrackFile = self._tempVideoFile
        
        # write the temporary audio track to file if we have one
        tStart = time.time()  # start time for the operation
        if self.mic is not None:
            audioTrack = self.mic.getRecording()
        
        if audioTrack is not None:
            logging.debug(
                "Saving audio track to file `{}`...".format(filename))
            
            # trim off samples before the recording started
            audioTrack = audioTrack.trimmed(
                direction='start',
                duration=self._absAudioRecStartPos,
                units='samples')
            
            if mergeAudio:
                logging.debug("Merging audio track with video track...")
                # save it to a temp file
                import tempfile
                tempAudioFile = tempfile.NamedTemporaryFile(
                    suffix='.wav', delete=False)
                audioTrackFile = tempAudioFile.name
                tempAudioFile.close()  # close the file so we can use it later
                audioTrack.save(audioTrackFile)

                # # composite audio a video tracks using MoviePy (huge thanks to 
                # # that team)
                # from moviepy.video.io.VideoFileClip import VideoFileClip
                # from moviepy.audio.io.AudioFileClip import AudioFileClip
                # from moviepy.audio.AudioClip import CompositeAudioClip

                # videoClip = VideoFileClip(videoTrackFile)
                # audioClip = AudioFileClip(audioTrackFile)
                # videoClip.audio = CompositeAudioClip([audioClip])

                # # default options for the writer, needed or we can crash
                # moviePyOpts = {
                #     'logger': None
                # }

                # if writerOpts is not None:  # make empty dict if not provided
                #     moviePyOpts.update(writerOpts)

                # # transcode with the format the user wants
                # videoClip.write_videofile(
                #     filename, 
                #     **moviePyOpts)  # expand out options

                # videoClip.close()  # close the video clip
                # audioClip.close()

                # merge audio and video tracks using FFMPEG
                mergedVideo = self._mergeAudioVideoTracks(
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
        numpy.ndarray
            The converted frame in RGB format.

        """
        from ffpyplayer.pic import SWScale
        if frame.get_pixel_format() == 'rgb24':  # already converted
            return frame

        rgbImg = SWScale(
            self._metadata.size[0], self._metadata.size[1],  # width, height
            frame.get_pixel_format(), 
            ofmt='rgb24').scale(frame)
        
        return rgbImg
    
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

        Examples
        --------
        Capture camera frames in a loop::

            while cam.recordingTime < 10.0:  # record for 10 seconds
                numFrames = cam.update()  # update the camera stream
                if numFrames > 0:
                    frame = cam.getVideoFrame()  # get the most recent frame
                    # do something with the frame, e.g. display it
                else:
                    # return last frame or placeholder frame if nothing new

        """
        # poll camera for new frames
        newFrames = self._capture.getFrames()  # get new frames from the camera

        if not self._videoReady and newFrames:
            # if we have new frames, we can set the video ready flag
            self._videoReady = True

        if self.hasMic and not self.mic._stream._closed:
            # poll the microphone for audio samples
            audioPos, overflows = self.mic.poll()

            if (not self._audioReady) and self._videoReady:
                nNewFrames = len(newFrames)
                # determine which video frame the audio starts at that we aquired
                keepFrames = []
                for i, frame in enumerate(newFrames):
                    _, _, streamTime = frame
                    if streamTime >= self._absAudioActualRecStartTime:
                        keepFrames.append(frame)

                # If we arrived at the audio start time and there is a video 
                # frame captured after that, we can compute the exact position
                # of the sample in the audio track that corresponds to that 
                # frame. This will allow us to align the audio and video streams
                # when saving the video file.
                if keepFrames:
                    _, _, streamTime = keepFrames[0]

                    # delta between the first video frame's capture timestamp 
                    # and the time the mic reported itself as ready. Used to 
                    # align the audio and video streams
                    frameSyncFudge = (
                        streamTime - self._absAudioActualRecStartTime)
                    
                    # compute exact time the first audio sample was recorded
                    # from the audio position and actual recording start time
                    absFirstAudioSampleTime = \
                        self._absAudioActualRecStartTime - (
                            audioPos / self.mic.sampleRateHz)

                    # compute how many samples we will discard from the audio
                    # track to align it with the video stream
                    self._absAudioRecStartPos = \
                        ((streamTime - absFirstAudioSampleTime) + \
                            frameSyncFudge + self._latencyBias) * self.mic.sampleRateHz
                    self._absAudioRecStartPos = int(self._absAudioRecStartPos)

                    # convert to samples
                    self._audioReady = True

                newFrames = keepFrames  # keep only frames after the audio start time

        else:
            self._audioReady = True  # no mic, so we just set the flag

        if not self.isReady:
            # if the camera is not ready, return -1 to indicate that we are not
            # ready to process frames yet
            return -1
        
        if not newFrames:
            # if no new frames were captured, return 0 to indicate that we have
            # no new frames to process
            return 0
        
        # put last frames into the frame store
        nNewFrames = len(newFrames)
        if nNewFrames > self._frameStore.maxlen:
            logging.warning(
                "Frame store overflowed, some frames may have been lost. "
                "Consider increasing the `keepFrames` parameter when creating "
                "the camera object or polling the camera more frequently."
            )
        
        self._frameCount += nNewFrames  # update total frames count
        # push all frames into the frame store
        for colorData, pts, streamTime in newFrames:
            # if camera is in CV mode, convert the frame to RGB by default
            # otherwise frames are converted only when needed
            if self._usageMode == CAMERA_MODE_CV:
                colorData = self._convertFrameToRGBFFPyPlayer(colorData)

            # add the frame to the frame store
            self._frameStore.append(
                CameraFrame(
                    colorData, 
                    pts, 
                    streamTime, 
                    captureLib=CAMERA_LIB_FFPYPLAYER))
        
        # if we have frames, update the last frame
        # colorData, pts, streamTime = newFrames[-1]
        # self._lastFrame = (
        #     self._convertFrameToRGBFFPyPlayer(colorData),  # convert to RGB, nop if already
        #     pts,  # presentation timestamp
        #     streamTime
        # )
        self._lastFrame = self._frameStore[-1]  # most recent frame

        self._pixelTransfer()  # transfer frames to the GPU if we have a window

        # write frames out to video file
        if self._usageMode == CAMERA_MODE_VIDEO:
            for frame in newFrames:
                self._submitFrameToFile(frame)
        elif self._usageMode == CAMERA_MODE_CV:
            pass

        return nNewFrames  # return number of frames we got
    
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
            self._convertFrameToRGBFFPyPlayer(frame) for frame in self._frameStore]

        return recentFrames
    
    def getRecentVideoFrame(self):
        """Get the most recent video frame from the camera.

        Returns
        -------
        VideoFrame or None
            Most recent video frame. Returns `None` if no frame was available,
            or we timed out.

        """
        self.update()

        return self._lastFrame[0] if self._lastFrame else None
    
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
        return self.mic.getRecording() if self.mic else None
    
    # --------------------------------------------------------------------------
    # Video rendering
    #
    # These methods are used to render live video frames to a window. If a 
    # window is set, this class will automamatically create the nessisary 
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

        # map the video frame to a memoryview
        # suggested by Alex Forrence (aforren1) originally in PR #6439
        # videoBuffer = self._lastFrame[0].to_memoryview()[0].memview
        videoBuffer = self._lastFrame.colorData.to_memoryview()[0].memview
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
            raise RuntimeError(
                "Attempting to call `_submitFrameToFileFFPyPlayer()` before "
                "`_openMovieFileWriterFFPyPlayer()`.")
        
        from ffpyplayer.pic import SWScale
        
        if not isinstance(frames, list):
            frames = [frames]  # ensure frames is a list

        # write frames to the movie file writer
        bytesOut = 0
        for colorData, pts, _ in frames:
            # do color conversion if needed
            frameWidth, frameHeight = colorData.get_size()
            sws = SWScale(
                frameWidth, frameHeight,
                colorData.get_pixel_format(),
                ofmt='yuv420p')
            
            if self._generatePTS:
                pts = self._curPTS  # use current for PTS
                self._curPTS += self._capture.frameInterval  # increment dts by frame interval
       
            bytesOut = self._movieWriter.write_frame(
                img=sws.scale(colorData),
                pts=pts,
                stream=0)

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
        else:
            logging.debug(
                "Attempting to call `_closeMovieFileWriterFFPyPlayer()` "
                "without an open movie file writer.")

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
            Encoder library to use for saving the video. This can be either
            `'ffpyplayer'` or `'opencv'`. If `None`, the same library that was
            used to open the camera stream. Default is `None`.
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
            
        # check if the encoder library name string is valid
        if encoderLib not in ('ffpyplayer'):
            raise ValueError(
                "Invalid value for parameter `encoderLib`, expected one of "
                "`'ffpyplayer'` or `'opencv'`.")
        
        if encoderLib == 'ffpyplayer':
            self._openMovieFileWriterFFPyPlayer(
                self._tempVideoFile, encoderOpts=encoderOpts)
        else:
            raise ValueError(
                "Invalid value for parameter `encoderLib`, expected one of "
                "`'ffpyplayer'` or `'opencv'`.")

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
        if self._movieWriter is None:
            raise RuntimeError(
                "Attempting to call `_submitFrameToFile()` before "
                "`_openMovieFileWriter()`.")

        tStart = time.time()  # start time for the operation
        if self._cameraLib == 'ffpyplayer':
            toReturn = self._submitFrameToFileFFPyPlayer(frames)
        else:
            raise ValueError(
                "Invalid value for parameter `encoderLib`, expected "
                "`'ffpyplayer'.")
        
        logging.debug(
            "Submitted {} frames to the movie file writer (took {:.6f} seconds)".format(
                len(frames), time.time() - tStart))
        
        return toReturn
        
    def _closeMovieFileWriter(self):
        """Close the movie file writer.

        This will close the movie file writer and free up any resources used by
        the writer. If the writer is not open, this will do nothing.
        """
        if self._movieWriter is None:
            logging.warning(
                "Attempting to call `_closeMovieFileWriter()` without an open "
                "movie file writer.")
            return
        
        if self._cameraLib == 'ffpyplayer':
            self._closeMovieFileWriterFFPyPlayer()
        else:
            raise ValueError(
                "Invalid value for parameter `encoderLib`, expected one of "
                "`'ffpyplayer'` or `'opencv'`.")

        self._movieWriter = None

    # --------------------------------------------------------------------------
    # Destructor
    #

    def __del__(self):
        """Try to cleanly close the camera and output file.
        """
        if hasattr(self, '_capture'):
            if self._capture is not None:
                try:
                    self.close()
                except AttributeError:
                    pass

        if hasattr(self, '_movieWriter'):
            if self._movieWriter is not None:
                try:
                    self._movieWriter.close()
                except AttributeError:
                    pass


DeviceManager.registerClassAlias("camera", "psychopy.hardware.camera.Camera")


# ------------------------------------------------------------------------------
# Functions
#

def _getCameraInfoMacOS():
    """Get a list of capabilities associated with a camera attached to the 
    system.

    This is used by `getCameraInfo()` for querying camera details on MacOS.
    Don't call this function directly unless testing.

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
                codecFormat=CAMERA_NULL_VALUE,
                frameSize=(int(frameWidth), int(frameHeight)),
                frameRate=frameRateMax,
                cameraAPI=CAMERA_API_AVFOUNDATION,
                cameraLib="ffpyplayer",
            )

            supportedFormats.append(thisCamInfo)

            devIdx += 1

        # add to output dictionary
        videoDevices[cameraName] = supportedFormats

    return videoDevices


def _getCameraInfoWindows():
    """Get a list of capabilities for the specified associated with a camera
    attached to the system.

    This is used by `getCameraInfo()` for querying camera details on Windows.
    Don't call this function directly unless testing.

    Returns
    -------
    list of CameraInfo
        List of camera descriptors.

    """
    if platform.system() != 'Windows':
        raise OSError(
            "Cannot query cameras with this function, platform not 'Windows'.")

    # FFPyPlayer can query the OS via DirectShow for Windows cameras
    from ffpyplayer.tools import list_dshow_devices
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
                cameraAPI=CAMERA_API_DIRECTSHOW,
                cameraLib="ffpyplayer",
            )
            supportedFormats.append(temp)
            devIndex += 1

        videoDevices[names[devURI]] = supportedFormats

    return videoDevices


def _getCameraInfoLinux():
    """Get camera information on Linux systems.

    This is used by `getCameraInfo()` for querying camera details on Linux. Don't
    call this function directly unless testing. Requires `v4l2-ctl` to be installed
    on the host system. If the command is not found, an empty list is returned.

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
                    cameraAPI=CAMERA_API_VIDEO4LINUX2,
                    cameraLib="ffpyplayer",
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


def getCameras():
    """Get information about installed cameras and their formats on this system.

    Use `getCameraDescriptions` to get a mapping or list of human-readable
    camera formats.

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

    return getCamerasFunc()


def getCameraDescriptions(collapse=False):
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

    Returns
    -------
    dict or list
        Mapping (`dict`) of camera descriptions, where keys are camera names
        (`str`) and values are a `list` of format description strings associated
        with the camera. If `collapse=True`, all descriptions will be returned
        in a single flat list. This might be more useful for specifying camera
        formats from a single GUI list control.

    """
    connectedCameras = getCameras()

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


def getFormatsForDevice(device):
    """Get a list of formats available for the given device.

    Parameters
    ----------
    device : str or int
        Name or index of the device

    Returns
    -------
    list
        List of formats, specified as strings in the format 
        `{width}x{height}@{frame rate}fps`
    """
    # get all devices
    connectedCameras = getCameras()
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
        if issubclass(cls, CameraDevice):
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


def renderVideo(outputFile, videoFile, audioFile=None, removeFiles=False):
    """Render a video.

    Combine visual and audio streams into a single movie file. This is used
    mainly for compositing video and audio data for the camera. Video and audio
    should have roughly the same duration.

    This is a legacy function used originally for compositing video and audio
    data from the camera. It is not used anymore internally, but is kept here 
    for reference and may be removed in the future. If you need to composite
    video and audio data, use `movietools.addAudioToMovie` instead.

    Parameters
    ----------
    outputFile : str
        Filename to write the movie to. Should have the extension of the file
        too.
    videoFile : str
        Video file path.
    audioFile : str or None
        Audio file path. If not provided the movie file will simply be copied
        to `outFile`.
    removeFiles : bool
        If `True`, the video (`videoFile`) and audio (`audioFile`) files will be 
        deleted after the movie is rendered.

    Returns
    -------
    int
        Size of the resulting file in bytes.

    """
    # if no audio file, just copy the video file
    if audioFile is None:
        import shutil
        shutil.copyfile(videoFile, outputFile)
        if removeFiles:
            os.remove(videoFile)  # delete the old movie file
        return os.path.getsize(outputFile)
    
    # merge video and audio, now using the new `movietools` module
    movietools.addAudioToMovie(
        videoFile, 
        audioFile, 
        outputFile, 
        useThreads=False,  # didn't use this before
        removeFiles=removeFiles)

    return os.path.getsize(outputFile)


# ------------------------------------------------------------------------------
# Cleanup functions
#
# These functions are used to clean up resources when the application exits, 
# usually unexpectedly. This helps to ensure hardware interfaces are closed
# and resources are freed up as best we can.
#

import atexit


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

# ------------------------------------------------------------------------------
if __name__ == "__main__":
    pass
