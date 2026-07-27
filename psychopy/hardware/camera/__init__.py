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

import os
import os.path
import sys
import platform
import inspect
import atexit
import time
import ctypes
import collections
import numpy as np
import threading

from psychopy.constants import NOT_STARTED
from psychopy.hardware import DeviceManager
from psychopy.sound.audioclip import AudioClip
from psychopy.sound.microphone import Microphone
from psychopy.hardware.microphone import MicrophoneDevice
import psychopy.logging as logging
from psychopy.hardware.camera._base import CameraDevice

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

# Keep track of open capture interfaces so we can close them at shutdown in the
# event that the user forgets or the program crashes.
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
        'opencv'). This helps routines passed this object determine the color 
        format and other properties of the frame which may be platform and 
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
            contains (frame, timestamp).

        """
        for client in self._cameraClients:
            client._onNewFrames(frames)

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
                    curPts))

                self._frameCount += 1  # increment the frame count

        self._onNewFrames(recentFrames)  # dispatch to clients any new frames
            
        return recentFrames
    
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
                while not self._stop_event.is_set():
                    time.sleep(self.interval)
                    self.function()

            def cancel(self):
                self._stop_event.set()

        # set up a thread to call the poll method at regular intervals
        self._pollingTimerThread = PollingTimerThread(
            self._pollingInterval, 
            self._poll)
        self._pollingTimerThread.daemon = True
        self._pollingTimerThread.start()

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

        if self._pollingTimerThread is not None:
            self._pollingTimerThread.cancel()
            self._pollingTimerThread = None
            logging.debug(
                "Stopped automatic polling of the camera stream for device '{}'.".format(
                    self._device))
            
        self._frameCount = 0  # reset the frame count

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
    def getDeviceCapabilities(device, by=None):
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
        for dev in FFPyPlayerCameraDevice.getCameras().values():
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

# class name alias for legacy support
CameraDevice = CameraInterface = FFPyPlayerCameraDevice

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
            )

        # from here on in the init, use the device index as `device`
        # device = self._capture.device
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

        self._tRecordingStartRequested = -1.0
        self._tRecordingStopRequested = None
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
        
        return time.time() - self._absRecStreamStartTime
        
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
        """Get a list of available camera devices on this system.

        Returns
        -------
        list
            List of available camera devices. Each device is represented as a
            dictionary containing information about the device.

        """
        return FFPyPlayerCameraDevice.getAvailableDevices()

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
        return FFPyPlayerCameraDevice.getCameraDescriptions(collapse=collapse)

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

        self._openMovieFileWriter()

        if self._capture is not None and not self._capture.isOpen:
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

        # reset audio flags
        self._audioReady = self._videoReady = False

        # reset the last frame
        self._lastFrame = None

        # start camera recording
        self._tRecordingStartRequested = \
            self._getTime() if when is None else when + self._getTime()

        # start microphone recording
        if self._usageMode == CAMERA_MODE_VIDEO:
            if self.mic is not None:
                self.mic.record(when=self._tRecordingStartRequested)

        self._isRecording = False  # set in callback or polling function
        # do an initial poll to avoid frame dropping
        # self.update()

        # mark that there's unsaved footage
        self._unsaved = True

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
        
        # # stop audio recording if we have a microphone
        if self.hasMic:
            self.mic.stop(when=self._absVideoRecStopTime)
            
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
        if self._capture is not None and self._capture.isOpen:
            self._capture.unbind(self)

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
        
        # check if we have an active movie writer
        if self._movieWriter is not None:
            self._movieWriter.close()  # close the movie writer

        # check if we have a temp movie file
        videoTrackFile = self._tempVideoFile
        
        # write the temporary audio track to file if we have one
        tStart = time.time()  # start time for the operation
        audioTrack = None
        if self.mic is not None:
            self._mergeAudioFragments()  # merge audio fragments into a single track
            audioTrack = AudioClip(
                self._recordingBuffer[0], 
                sampleRateHz=self.mic.sampleRateHz)

        if audioTrack is not None:
            logging.debug(
                "Saving audio track to file `{}`...".format(filename))
            
            # trim off samples before the recording started
            if self._startRecOffset > 0:
                audioTrack = audioTrack.trimmed(
                    direction='start',
                    duration=self._startRecOffset,
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
    
    def _onNewFrames(self, frames):
        """Callback for when new frames are available from the camera.

        This is called by the camera stream when new frames are available. It
        will update the frame store and last frame, and transfer the frames to
        the GPU if a window is set.

        Parameters
        ----------
        frames : list of tuple
            List of tuples containing the frame data, presentation timestamp, and
            stream time.

        """
        # iterate over frames and add them to the frame store
        if not frames:
            return  # no frames to process
        
        for colorData, pts, streamTime in frames:
            if not self._isRecording or streamTime < self._tRecordingStartRequested:
                # if the frame was captured before the recording started, skip it
                continue

            # if camera is in CV mode, convert the frame to RGB by default
            # otherwise frames are converted only when needed
            if self._usageMode == CAMERA_MODE_CV:
                colorData = self._convertFrameToRGBFFPyPlayer(colorData)
            elif self._usageMode == CAMERA_MODE_VIDEO:
                # if we are recording video, pass the frame to the movie writer
                self._submitFrameToFile((colorData, pts, streamTime))

            # add the frame to the frame store
            self._frameStore.append(
                CameraFrame(
                    colorData, 
                    pts, 
                    streamTime, 
                    captureLib=CAMERA_LIB_FFPYPLAYER))
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
            self._convertFrameToRGBFFPyPlayer(frame.colorData) for frame in self._frameStore]

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
            return 0
            # raise RuntimeError(
            #     "Attempting to call `_submitFrameToFileFFPyPlayer()` before "
            #     "`_openMovieFileWriterFFPyPlayer()`, or writer was closed.")
        
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
            
            # if self._generatePTS:
            self._curPTS += self._capture.frameInterval  # increment dts by frame interval

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
        if self._movieWriter is None:
            pass
            # raise RuntimeError(
            #     "Attempting to call `_submitFrameToFile()` before "
            #     "`_openMovieFileWriter()`.")

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
            # logging.warning(
            #     "Attempting to call `_closeMovieFileWriter()` without an open "
            #     "movie file writer.")
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
                codecFormat=u'Null',
                frameSize=(int(frameWidth), int(frameHeight)),
                frameRate=frameRateMax,
                cameraAPI=u'AVFoundation',
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
                cameraAPI=u'DirectShow',
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
                    cameraAPI=u'Video4Linux2',
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
    
    from psychopy.tools import movietools
    
    # merge video and audio, now using the new `movietools` module
    movietools.addAudioToMovie(
        videoFile, 
        audioFile, 
        outputFile, 
        useThreads=False,  # didn't use this before
        removeFiles=removeFiles)

    return os.path.getsize(outputFile)


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
    dev = CameraDevice.getAvailableDevices()[0]['deviceName']
    print(CameraDevice.getDeviceCapabilities(dev, by='frameRate'))

    cam = Camera(0, mic=1)
    #cam.open()
    cam.record(when=0.0)

    t0 = time.time()
    while time.time() - t0 < 5.0:
        time.sleep(0.001)

    cam.stop()
    cam.save('./test_camera_output.mp4')
    cam.close()

