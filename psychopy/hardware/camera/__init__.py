#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for reading and writing camera streams.

A camera may be used to document participant responses on video or used by the
experimenter to create movie stimuli or instructions.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'VIDEO_DEVICE_ROOT_LINUX',
    'CAMERA_UNKNOWN_VALUE',
    'CAMERA_NULL_VALUE',
    # 'CAMERA_MODE_VIDEO',
    # 'CAMERA_MODE_CV',
    # 'CAMERA_MODE_PHOTO',
    'CAMERA_TEMP_FILE_VIDEO',
    'CAMERA_TEMP_FILE_AUDIO',
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
    'CameraInterfaceFFmpeg',
    'CameraInterfaceOpenCV',
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

from psychopy.constants import NOT_STARTED
from psychopy.hardware import DeviceManager
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
# CAMERA_MODE_VIDEO = u'video'
# CAMERA_MODE_CV = u'cv'
# CAMERA_MODE_PHOTO = u'photo'

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
CAMERA_LIB_FFPYPLAYER = u'FFPyPlayer'
CAMERA_LIB_OPENCV = u'OpenCV'
CAMERA_LIB_UNKNOWN = u'Unknown'
CAMERA_LIB_NULL = u'Null'

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


class CameraInterface:
    """Base class providing an interface with a camera attached to the system.

    This interface handles the opening, closing, and reading of camera streams.
    Subclasses provide a specific implementation for a camera interface. 
    
    Calls to any instance methods should be asynchronous and non-blocking, 
    returning immediately with the same data as before if no new frame data is
    available. This is to ensure that the main thread is not blocked by the
    camera interface and can continue to process other events.

    Parameters
    ----------
    device : Any
        Camera device to open a stream with. The type of this value is platform
        dependent. Calling `start()` will open a stream with this device. 
        Afterwards, `getRecentFrame()` can be called to get the most recent
        frame from the camera.

    """
    # default values for class variables, these are read-only and should not be
    # changed at runtime
    _cameraLib = u'Null'
    _frameIndex = 0
    _lastPTS = 0.0  # presentation timestamp of the last frame
    _supportedPlatforms = ['linux', 'windows', 'darwin']
    _device = None
    _lastFrame = None
    _isReady = False  # `True` if the camera is 'hot' and yielding frames

    def __init__(self, device):
        self._device = device
        self._mic = None

    @staticmethod
    def getCameras():
        """Get a list of devices this interface can open.

        Returns
        -------
        list 
            List of objects which represent cameras that can be opened by this
            interface. Pass any of these values to `device` to open a stream.

        """
        return []

    @property
    def device(self):
        """Camera device this interface is using (`Any`).
        """
        return self._device
    
    @property
    def frameCount(self):
        """Number of new frames read from the camera since initialization 
        (`int`).
        """
        return self._frameCount

    @property
    def streamTime(self):
        """Current stream time in seconds (`float`). This time increases
        monotonically from startup.
        """
        return self._streamTime

    def lastFrame(self):
        """The last frame read from the camera. If `None`, no frames have been
        read yet.
        """
        return self._lastFrame
    
    def _assertMediaPlayer(self):
        """Assert that the media player is available.
        
        Returns
        -------
        bool
            `True` if the media player is available.

        """
        return False
    
    def open(self):
        """Open the camera stream.
        """
        pass

    def isOpen(self):
        """Check if the camera stream is open.

        Returns
        -------
        bool
            `True` if the camera stream is open.

        """
        return False
    
    def enable(self):
        """Enable passing camera frames to the main thread.
        """
        pass

    def disable(self):
        """Disable passing camera frames to the main thread.
        """
        pass

    def close(self):
        """Close the camera stream.
        """
        pass

    def getMetadata(self):
        """Get metadata about the camera stream.

        Returns
        -------
        dict
            Dictionary containing metadata about the camera stream. Returns an
            empty dictionary if no metadata is available.

        """
        return {}
    
    def _enqueueFrame(self):
        """Enqueue a frame from the camera stream.
        """
        pass

    def update(self):
        """Update the camera stream.
        """
        pass

    def getRecentFrame(self):
        """Get the most recent frame from the camera stream.

        Returns
        -------
        numpy.ndarray
            Most recent frame from the camera stream. Returns `None` if no
            frames are available.

        """
        return NULL_MOVIE_FRAME_INFO


class CameraInterfaceFFmpeg(CameraInterface):
    """Camera interface using FFmpeg (ffpyplayer) to open and read camera 
    streams.

    Parameters
    ----------
    device : CameraInfo
        Camera device to open a stream with. Calling `start()` will open a
        stream with this device. Afterwards, `getRecentFrame()` can be called
        to get the most recent frame from the camera.
    mic : MicrophoneInterface or None
        Microphone interface to use for audio recording. If `None`, no audio
        recording is performed.

    """
    _cameraLib = u'ffpyplayer'

    def __init__(self, device, mic=None):
        super().__init__(device=device)

        self._bufferSecs = 0.5  # number of seconds to buffer
        self._cameraInfo = device
        self._mic = mic  # microphone interface
        self._frameQueue = queue.Queue()
        self._enableEvent = threading.Event()
        self._enableEvent.clear()
        self._exitEvent = threading.Event()
        self._exitEvent.clear()
        self._syncBarrier = None
        self._recordBarrier = None  # created in `open()`
        self._playerThread = None

    def _assertMediaPlayer(self):
        return self._playerThread is not None
    
    def _getCameraInfo(self):
        """Get camera information in the format expected by FFmpeg.
        """
        pass

    def getCameras():
        """Get a list of devices this interface can open.

        Returns
        -------
        list 
            List of objects which represent cameras that can be opened by this
            interface. Pass any of these values to `device` to open a stream.

        """
        global _cameraGetterFuncTbl
        systemName = platform.system()  # get the system name

        # lookup the function for the given platform
        getCamerasFunc = _cameraGetterFuncTbl.get(systemName, None)
        if getCamerasFunc is None:  # if unsupported
            raise OSError(
                "Cannot get cameras, unsupported platform '{}'.".format(
                    systemName))

        return getCamerasFunc()

    @property
    def frameRate(self):
        """Frame rate of the camera stream (`float`).
        """
        return self._cameraInfo.frameRate
    
    @property
    def frameSize(self):
        """Frame size of the camera stream (`tuple`).
        """
        return self._cameraInfo.frameSize

    @property
    def framesWaiting(self):
        """Get the number of frames currently buffered (`int`).

        Returns the number of frames which have been pulled from the stream and
        are waiting to be processed. This value is decremented by calls to 
        `_enqueueFrame()`.

        """
        return self._frameQueue.qsize()

    def isOpen(self):
        """Check if the camera stream is open (`bool`).
        """
        if self._playerThread is not None:
            return self._playerThread.is_alive()
        
        return False
    
    def open(self):
        """Open the camera stream and begin decoding frames (if available).

        The value of `lastFrame` will be updated as new frames from the camera
        arrive.

        """
        if self._playerThread is not None:
            raise RuntimeError('Cannot open `MediaPlayer`, already opened.')
        
        self._exitEvent.clear()  # signal the thread to stop
        
        def _frameGetterAsync(videoCapture, frameQueue, exitEvent, recordEvent, 
                              warmUpBarrier, recordingBarrier, audioCapture):
            """Get frames from the camera stream asynchronously.

            Parameters
            ----------
            videoCapture : ffpyplayer.player.MediaPlayer
                FFmpeg media player object. This object will be under direct 
                control of this function.
            frameQueue : queue.Queue
                Queue to put frames into. The queue has an unlimited size, so 
                be careful with memory use. This queue should be flushed when
                camera thread is paused.
            exitEvent : threading.Event
                Event used to signal the thread to stop.
            recordEvent : threading.Event
                Event used to signal the thread to pass frames along to the main 
                thread.
            warmUpBarrier : threading.Barrier
                Barrier which is used hold until camera capture is ready.
            recordingBarrier : threading.Barrier
                Barrier which is used to synchronize audio and video recording.
                This ensures that the audio device is ready before buffering 
                frames captured by the camera. 
            audioCapture : psychopy.sound.Microphone or None
                Microphone object to use for audio capture. This will be used to
                synchronize the audio and video streams. If `None`, no audio
                will be captured.

            """           
            # warmup the stream, wait for metadata
            ptsStart = 0.0  # may be used in the future
            while True:
                frame, val = videoCapture.get_frame()
                if frame is not None:
                    ptsStart = videoCapture.get_pts()
                    break
                
                time.sleep(0.001)

            # if we have a valid frame, determine the polling rate
            metadata = videoCapture.get_metadata()
            numer, divisor = metadata['frame_rate']

            # poll interval is half the frame period, this makes sure we don't
            # miss frames while not wasting CPU cycles
            pollInterval = (1.0 / float(numer / divisor)) * 0.5

            # holds main-thread execution until its ready for frames
            # frameQueue.put((frame, val, metadata))  # put the first frame

            warmUpBarrier.wait()  # wait for main thread to be ready

            # start capturing frames in background thread
            isRecording = False
            lastAbsTime = -1.0  # presentation timestamp of the last frame
            while not exitEvent.is_set():  # quit if signaled
                # pull a frame from the stream, we keep this running 'hot' so
                # that we don't miss frames, we just discard them if we don't
                # need them
                frame, val = videoCapture.get_frame(force_refresh=False)

                if val == 'eof':  # thread should exit if stream is done
                    break
                elif val == 'paused':
                    continue
                elif frame is None:
                    continue
                else:
                    # don't queue frames unless they are newer than the last
                    if isRecording:
                        thisFrameAbsTime = videoCapture.get_pts()
                        if lastAbsTime < thisFrameAbsTime:
                            frameQueue.put((frame, val, metadata))
                            lastAbsTime = thisFrameAbsTime

                if recordEvent.is_set() and not isRecording:
                    if audioCapture is not None:
                        audioCapture.start(waitForStart=1)
                    recordingBarrier.wait()
                    isRecording = True
                elif not recordEvent.is_set() and isRecording:
                    if audioCapture is not None:
                        audioCapture.stop(blockUntilStopped=1)
                    recordingBarrier.wait()
                    isRecording = False

                if not isRecording:
                    time.sleep(pollInterval)
                    continue

                if audioCapture is not None:
                    if audioCapture.isRecording:
                        audioCapture.poll()

                time.sleep(pollInterval)
            
            videoCapture.close_player()

            if audioCapture is not None:
                audioCapture.stop(blockUntilStopped=1)

            # thread is dead when we get here

        # configure the camera stream reader
        ff_opts = {}  # ffmpeg options
        lib_opts = {}  # ffpyplayer options
        _camera = CAMERA_NULL_VALUE
        _frameRate = CAMERA_NULL_VALUE
        _cameraInfo = self._cameraInfo

        # setup commands for FFMPEG
        if _cameraInfo.cameraAPI == CAMERA_API_DIRECTSHOW:  # windows
            ff_opts['f'] = 'dshow'
            _camera = 'video={}'.format(_cameraInfo.name)
            _frameRate = _cameraInfo.frameRate
            if _cameraInfo.pixelFormat:
                ff_opts['pixel_format'] = _cameraInfo.pixelFormat
            if _cameraInfo.codecFormat:
                ff_opts['vcodec'] = _cameraInfo.codecFormat
        elif _cameraInfo.cameraAPI == CAMERA_API_AVFOUNDATION:  # darwin
            ff_opts['f'] = 'avfoundation'
            ff_opts['i'] = _camera = self._cameraInfo.name

            # handle pixel formats using FourCC
            global pixelFormatTbl
            ffmpegPixFmt = pixelFormatTbl.get(_cameraInfo.pixelFormat, None)

            if ffmpegPixFmt is None:
                raise FormatNotFoundError(
                    "Cannot find suitable FFMPEG pixel format for '{}'. Try a "
                    "different format or camera.".format(
                        _cameraInfo.pixelFormat))

            _cameraInfo.pixelFormat = ffmpegPixFmt

            # this needs to be exactly specified if using NTSC
            if math.isclose(CAMERA_FRAMERATE_NTSC, _cameraInfo.frameRate):
                _frameRate = CAMERA_FRAMERATE_NOMINAL_NTSC
            else:
                _frameRate = str(_cameraInfo.frameRate)

            # need these since hardware acceleration is not possible on Mac yet
            lib_opts['fflags'] = 'nobuffer'
            lib_opts['flags'] = 'low_delay'
            lib_opts['pixel_format'] = _cameraInfo.pixelFormat
            ff_opts['framedrop'] = True
            ff_opts['fast'] = True
        elif _cameraInfo.cameraAPI == CAMERA_API_VIDEO4LINUX2:
            raise OSError(
                "Sorry, camera does not support Linux at this time. However, "
                "it will in future versions.")
        
        else:
            raise RuntimeError("Unsupported camera API specified.")

        # set library options
        camWidth = _cameraInfo.frameSize[0]
        camHeight = _cameraInfo.frameSize[1]

        # configure the real-time buffer size
        _bufferSize = camWidth * camHeight * 3 * self._bufferSecs

        # common settings across libraries
        lib_opts['rtbufsize'] = str(int(_bufferSize))
        lib_opts['video_size'] = _cameraInfo.frameSizeAsFormattedString()
        lib_opts['framerate'] = str(_frameRate)

        self._warmupBarrier = threading.Barrier(2)
        self._recordBarrier = threading.Barrier(2)

        # open the media player
        from ffpyplayer.player import MediaPlayer
        cap = MediaPlayer(_camera, ff_opts=ff_opts, lib_opts=lib_opts)

        # open a stream thread and pause wait until ready
        self._playerThread = threading.Thread(
            target=_frameGetterAsync,
            args=(cap, 
                  self._frameQueue, 
                  self._exitEvent,
                  self._enableEvent,
                  self._warmupBarrier,
                  self._recordBarrier,
                  self._mic))
        self._playerThread.daemon=True
        self._playerThread.start()

        self._warmupBarrier.wait()

        # pass off the player to the thread which will process the stream
        self._enqueueFrame()  # pull metadata from first frame

    def _enqueueFrame(self):
        """Grab the latest frame from the stream.

        Returns
        -------
        bool
            `True` if a frame has been enqueued. Returns `False` if the camera 
            has not acquired a new frame yet.

        """
        self._assertMediaPlayer()

        try:
            frameData = self._frameQueue.get_nowait()
        except queue.Empty:
            return False

        frame, val, metadata = frameData  # update the frame

        if val == CAMERA_STATUS_EOF:  # handle end of stream
            return False
        elif val == CAMERA_STATUS_PAUSED:  # handle when paused
            return False
        elif frame is None:  # handle when no frame is available
            return False
        
        frameImage, pts = frame  # otherwise, unpack the frame

        # if we have a new frame, update the frame information
        videoBuffer = frameImage.to_bytearray()[0]
        videoFrameArray = np.frombuffer(videoBuffer, dtype=np.uint8)

        # provide the last frame
        self._lastFrame = MovieFrame(
            frameIndex=self._frameIndex,
            absTime=pts,
            # displayTime=self._recentMetadata['frame_size'],
            size=frameImage.get_size(),
            colorData=videoFrameArray,
            audioChannels=0,
            audioSamples=None,
            metadata=metadata,
            movieLib=self._cameraLib,
            userData=None)

        return True

    def close(self):
        """Close the camera stream and release resources. 
        
        This blocks until the camera stream thread is no longer alive.

        """
        if self._playerThread is None:
            raise RuntimeError('Cannot close `MediaPlayer`, already closed.')
        
        self._exitEvent.set()  # signal the thread to stop
        self._playerThread.join()  # wait for the thread to stop

        self._playerThread = None

    @property
    def isEnabled(self):
        """`True` if the camera is enabled.
        """
        return self._enableEvent.is_set()

    def enable(self, state=True):
        """Start passing frames to the frame queue.

        This method returns when the video and audio stream are both starting to
        record or stop recording.

        Parameters
        ----------
        state : bool
            `True` to enable recording frames to the queue, `False` to disable.
            On state change, the audio interface will be started or stopped.

        """
        if state:
            self._enableEvent.set()
        else:
            self._enableEvent.clear()
        
        self._recordBarrier.wait()
        self._enqueueFrame()
    
    def disable(self):
        """Stop passing frames to the frame queue.
        
        Calling this is equivalent to calling `enable(False)`.

        """
        self.enable(False)

    def getFrames(self):
        """Get all frames from the camera stream which are waiting to be 
        processed. 

        Returns
        -------
        list
            List of `MovieFrame` objects. The most recent frame is the last one 
            in the list.

        """
        self._assertMediaPlayer()

        frames = []
        while self._enqueueFrame():
            frames.append(self._lastFrame)

        return frames

    def getRecentFrame(self):
        """Get the most recent frame captured from the camera, discarding all 
        others.

        Returns
        -------
        MovieFrame
            The most recent frame from the stream.

        """
        while self._enqueueFrame():
            pass

        return self._lastFrame


class CameraInterfaceOpenCV(CameraInterface):
    """Camera interface using OpenCV to open and read camera streams.

    Parameters
    ----------
    device : int
        Camera device to open a stream with. This value is platform dependent.
    mic : MicrophoneInterface or None
        Microphone interface to use for audio recording. If `None`, no audio
        recording is performed.

    """
    _cameraLib = u'opencv'

    def __init__(self, device, mic=None):
        super().__init__(device)
        try:
            import cv2   # just import to check if it's available
        except ImportError:
            raise ImportError(
                "Could not import `cv2`. Please install OpenCV2 to use this "
                "camera interface.")
        
        self._cameraInfo = device
        self._mic = mic  # microphone interface
        self._frameQueue = queue.Queue()
        self._enableEvent = threading.Event()
        self._exitEvent = threading.Event()
        self._warmUpBarrier = None
        self._recordBarrier = None

    def _assertMediaPlayer(self):
        """Assert that the media player thread is running.
        """
        return self._playerThread is not None
    
    @staticmethod
    def getCameras(maxCameraEnum=16):
        """Get information about available cameras.

        OpenCV is not capable of enumerating cameras and getting information
        about them. Therefore, we must open a stream with each camera index
        and query the information from the stream. This process is quite slow
        on systems with many cameras. It's best to run this function once and
        save the results for later use if the camera configuration is not
        expected to change.

        Parameters
        ----------
        maxCameraEnum : int
            Maximum number of cameras to check. This is the maximum camera index
            to check. For example, if `maxCameraEnum` is 16, then cameras 0-15
            will be checked.

        Returns
        -------
        dict
            Mapping containing information about each camera. The keys are the
            camera index, and the values are `CameraInfo` objects.

        """
        import cv2

        # recommended camera drivers for each platform
        cameraPlatformDrivers = {
            'Linux': (cv2.CAP_V4L2, CAMERA_API_VIDEO4LINUX2),
            'Windows': (cv2.CAP_DSHOW, CAMERA_API_DIRECTSHOW),
            'Darwin': (cv2.CAP_AVFOUNDATION, CAMERA_API_AVFOUNDATION)
        }

        # select the camera interface for the platform
        cameraDriver, cameraAPI = cameraPlatformDrivers.get(
            platform.system(), (cv2.CAP_ANY, CAMERA_API_ANY))

        logging.info(
            'Searching for connected cameras, this may take a while...')
        
        cameras = {}
        for cameraIndex in range(maxCameraEnum):
            # open a camera
            thisCamera = cv2.VideoCapture(cameraIndex, cameraDriver)

            # if the camera is not opened, we're done
            if not thisCamera.isOpened():
                break
            
            # get information about camera capabilities
            frameRate = thisCamera.get(cv2.CAP_PROP_FPS)
            frameSize = (
                int(thisCamera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(thisCamera.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            
            genName = 'camera:{}'.format(cameraIndex)
            cameraInfo = CameraInfo(
                index=cameraIndex,
                name=genName,
                frameSize=frameSize or (-1, -1),
                frameRate=frameRate or -1.0,
                pixelFormat='bgr24',  # always BGR with 8 bpc for OpenCV
                cameraLib=CameraInterfaceOpenCV._cameraLib,
                cameraAPI=cameraAPI
            )

            cameras.update({genName: [cameraInfo]})
            thisCamera.release()

        logging.info('Found {} cameras.'.format(len(cameras)))
        
        return cameras

    @property
    def framesWaiting(self):
        """Get the number of frames currently buffered (`int`).

        Returns the number of frames which have been pulled from the stream and
        are waiting to be processed. This value is decremented by calls to 
        `_enqueueFrame()`.

        """
        return self._frameQueue.qsize()
    
    @property
    def frameRate(self):
        """Get the frame rate of the camera stream (`float`).
        """
        if self._cameraInfo is None:
            return -1.0
        
        return self._cameraInfo.frameRate
    
    @property
    def frameSize(self):
        """Get the frame size of the camera stream (`tuple`).
        """
        if self._cameraInfo is None:
            return (-1, -1)
        
        return self._cameraInfo.frameSize

    def isOpen(self):
        """Check if the camera stream is open (`bool`).
        """
        if self._playerThread is not None:
            return self._playerThread.is_alive()
        
        return False
    
    def open(self):
        """Open the camera stream and start reading frames using OpenCV2.
        """
        import cv2
        
        def _frameGetterAsync(videoCapture, frameQueue, exitEvent, recordEvent, 
                              warmUpBarrier, recordingBarrier, audioCapture):
            """Get frames asynchronously from the camera stream.

            Parameters
            ----------
            videoCapture : cv2.VideoCapture
                Handle for the video capture object. This is opened outside the
                thread and passed in.
            frameQueue : queue.Queue
                Queue to store frames in.
            exitEvent : threading.Event
                Event to signal when the thread should stop.
            recordEvent : threading.Event
                Event used to signal the thread to pass frames along to the main 
                thread.
            warmUpBarrier : threading.Barrier
                Barrier which is used hold until camera capture is ready.
            recordingBarrier : threading.Barrier
                Barrier which is used to synchronize audio and video recording.
                This ensures that the audio device is ready before buffering 
                frames captured by the camera. 
            audioCapture : psychopy.sound.Microphone or None
                Microphone object to use for audio capture. This will be used to
                synchronize the audio and video streams. If `None`, no audio
                will be captured.

            """
            # poll interval is half the frame period, this makes sure we don't
            # miss frames while not wasting CPU cycles
            # fps = videoCapture.get(cv2.CAP_PROP_FPS)
            # if fps > 0.0:
            #     pollInterval = (1.0 / fps) * 0.5
            # else:
            #     pollInterval = 1 / 60.0
            
            # if the camera is opened, wait until the main thread is ready to
            # take frames
            warmUpBarrier.wait()

            # start capturing frames
            isRecording = False
            while not exitEvent.is_set():
                # Capture frame-by-frame
                ret, frame = videoCapture.read()

                # if frame is read correctly ret is True
                if not ret:  # eol or something else
                    # val = 'eof'
                    break
                else:
                    # don't queue frames unless they are newer than the last
                    if isRecording:
                        # color conversion is done in the thread here
                        colorData = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        # colorData = frame
                        frameQueue.put((colorData, 0.0, None))

                # check if we should start or stop recording
                if recordEvent.is_set() and not isRecording:
                    if audioCapture is not None:
                        audioCapture.start(waitForStart=1)
                    recordingBarrier.wait()
                    isRecording = True
                elif not recordEvent.is_set() and isRecording:
                    if audioCapture is not None:
                        audioCapture.stop(blockUntilStopped=1)
                    recordingBarrier.wait()
                    isRecording = False

                if not isRecording:
                    # time.sleep(pollInterval)
                    continue

                if audioCapture is not None:
                    if audioCapture.isRecording:
                        audioCapture.poll()

            # when everything done, release the capture device
            videoCapture.release()

            if audioCapture is not None:  # stop audio capture
                audioCapture.stop(blockUntilStopped=1)

            # thread is dead if we get here

        # barriers used for synchronizing
        parties = 2  # main + recording threads
        self._warmUpBarrier = threading.Barrier(parties)  # camera is ready
        self._recordBarrier = threading.Barrier(parties)  # audio/video is ready

        # drivers for the given camera API
        cameraDrivers = {
            CAMERA_API_ANY: cv2.CAP_ANY,
            CAMERA_API_VIDEO4LINUX2: cv2.CAP_V4L2,
            CAMERA_API_DIRECTSHOW: cv2.CAP_DSHOW,
            CAMERA_API_AVFOUNDATION: cv2.CAP_AVFOUNDATION
        }
        _cameraInfo = self._cameraInfo

        # create the camera capture object, we keep this internal to the thread
        # so that we can control when it is released
        cap = cv2.VideoCapture(
            _cameraInfo.index,
            cameraDrivers[_cameraInfo.cameraAPI])
        
        # check if the camera is opened
        if not cap.isOpened():
            raise RuntimeError("Cannot open camera using `cv2`")

        # if the user didn't specify a frame rate or size, use the defaults
        # pulled from the camera
        usingDefaults = False
        if _cameraInfo.frameRate is None:
            _cameraInfo.frameRate = cap.get(cv2.CAP_PROP_FPS)
            usingDefaults = True

        if _cameraInfo.frameSize is None:
            _cameraInfo.frameSize = (
                int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 
                int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            usingDefaults = True

        if not usingDefaults:
            # set frame rate and size and check if they were set correctly
            cap.set(cv2.CAP_PROP_FPS, _cameraInfo.frameRate)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, _cameraInfo.frameSize[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, _cameraInfo.frameSize[1])
            
            if cap.get(cv2.CAP_PROP_FPS) != _cameraInfo.frameRate:
                raise CameraFormatNotSupportedError(
                    "Unsupported frame rate (%s), try %s instead." % (
                    _cameraInfo.frameRate, cap.get(cv2.CAP_PROP_FPS)))
            
            frameSizeMismatch = (
                cap.get(cv2.CAP_PROP_FRAME_WIDTH) != _cameraInfo.frameSize[0] or
                cap.get(cv2.CAP_PROP_FRAME_HEIGHT) != _cameraInfo.frameSize[1])
            if frameSizeMismatch:
                raise CameraFormatNotSupportedError(
                    "Unsupported frame size: %s" % str(_cameraInfo.frameSize))
            
        # open a stream and pause it until ready
        self._playerThread = threading.Thread(
            target=_frameGetterAsync,
            args=(cap, 
                  self._frameQueue, 
                  self._exitEvent,
                  self._enableEvent,
                  self._warmUpBarrier,
                  self._recordBarrier,
                  self._mic))
        self._playerThread.daemon=True
        self._playerThread.start()

        self._warmUpBarrier.wait()  # wait until the camera is ready

        # pass off the player to the thread which will process the stream
        self._enqueueFrame()  # pull metadata from first frame

    def _enqueueFrame(self):
        """Grab the latest frame from the stream.

        Returns
        -------
        bool
            `True` if a frame has been enqueued. Returns `False` if the camera 
            has not acquired a new frame yet.

        """
        self._assertMediaPlayer()

        try:
            frameData = self._frameQueue.get_nowait()
        except queue.Empty:
            return False

        frame, val, _ = frameData  # update the frame

        if val == 'eof':  # handle end of stream
            return False
        elif val == 'paused':  # handle when paused, not used for OpenCV yet
            return False
        elif frame is None:  # handle when no frame is available
            return False
        
        frameImage = frame  # otherwise, unpack the frame

        # if we have a new frame, update the frame information
        # videoBuffer = frameImage.to_bytearray()[0]
        videoFrameArray = np.ascontiguousarray(
            frameImage.flatten(), dtype=np.uint8)

        # provide the last frame
        self._lastFrame = MovieFrame(
            frameIndex=self._frameIndex,
            absTime=0.0,
            # displayTime=self._recentMetadata['frame_size'],
            size=self._cameraInfo.frameSize,
            colorFormat='rgb24',  # converted in thread
            colorData=videoFrameArray,
            audioChannels=0,
            audioSamples=None,
            metadata=None,
            movieLib=self._cameraLib,
            userData=None)

        return True

    def close(self):
        """Close the camera stream and release resources.
        """
        self._exitEvent.set()  # signal the thread to stop
        self._playerThread.join()  # hold the thread until it stops

        self._playerThread = None

    @property
    def isEnabled(self):
        """`True` if the camera is enabled.
        """
        return self._enableEvent.is_set()

    def enable(self, state=True):
        """Start passing frames to the frame queue.

        This method returns when the video and audio stream are both starting to
        record or stop recording. If no audio stream is being recorded, this
        method returns quicker.

        Parameters
        ----------
        state : bool
            `True` to enable recording frames to the queue, `False` to disable.
            On state change, the audio interface will be started or stopped.

        """
        if state:
            self._enableEvent.set()
        else:
            self._enableEvent.clear()
        
        self._recordBarrier.wait()
        self._enqueueFrame()
    
    def disable(self):
        """Stop passing frames to the frame queue.
        
        Calling this is equivalent to calling `enable(False)`.

        """
        self.enable(False)

    def getFrames(self):
        """Get all frames from the camera stream which are waiting to be 
        processed. 

        Returns
        -------
        list
            List of `MovieFrame` objects. The most recent frame is the last one 
            in the list.

        """
        self._assertMediaPlayer()

        frames = []
        while self._enqueueFrame():
            frames.append(self._lastFrame)

        return frames

    def getRecentFrame(self):
        """Get the most recent frame captured from the camera, discarding all 
        others.

        Returns
        -------
        MovieFrame
            The most recent frame from the stream.

        """
        while self._enqueueFrame():
            pass

        return self._lastFrame


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
        Size of the real-time camera stream buffer specified in seconds (only
        valid on Windows and MacOS). This is not the same as the recording
        buffer size. This option might not be available for all camera
        libraries.
    win : :class:`~psychopy.visual.Window` or None
        Optional window associated with this camera. Some functionality may
        require an OpenGL context for presenting frames to the screen. If you 
        are not planning to display the camera stream, this parameter can be
        safely ignored.
    name : str
        Label for the camera for logging purposes.

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
                 name='cam'):
        # add attributes for setters
        self.__dict__.update(
            {'_device': None,
             '_captureThread': None,
             '_mic': None,
             '_outFile': None,
             '_mode': u'video',
             '_frameRate': None,
             '_frameRateFrac': None,
             '_size': None,
             '_cameraLib': u''})

        # ----------------------------------------------------------------------
        # Process camera settings
        #

        # camera library in use
        self._cameraLib = cameraLib
        
        if self._cameraLib == u'opencv':
            if device in (None, "None", "none", "Default", "default"):
                device = 0  # use the first enumerated camera

            # handle all possible input for `frameRate` and `frameSize`
            if frameRate is None:
                pass   # no change
            elif isinstance(frameRate, str):
                if frameRate in ("None", "none", "Default", "default"):
                    frameRate = None
                elif frameRate.lower() == 'ntsc':
                    frameRate = CAMERA_FRAMERATE_NTSC
                else:
                    try:  # try and convert to float
                        frameRate = float(frameRate)
                    except ValueError:
                        raise ValueError(
                            "`frameRate` must be a number, string or None")
            
            # catch the value converted to float and process it
            if isinstance(frameRate, (int, float)):
                if frameRate <= 0:
                    raise ValueError("`frameRate` must be a positive number")
            
            if frameSize is None:
                pass  # use the camera default
            elif isinstance(frameSize, str):
                if frameSize in ("None", "none", "Default", "default"):
                    frameSize = None
                elif len(frameSize.split('x')) == 2:
                    frameSize = tuple(map(int, frameSize.split('x')))
                elif frameSize.upper() in movietools.VIDEO_RESOLUTIONS.keys():
                    frameSize = movietools.VIDEO_RESOLUTIONS[frameSize.upper()]
                else:
                    raise ValueError("`frameSize` specified incorrectly")
            elif isinstance(frameSize, (tuple, list)):
                if len(frameSize) != 2:
                    raise ValueError("`frameSize` must be a 2-tuple or 2-list")
                frameSize = tuple(map(int, frameSize))
            else:
                raise ValueError("`frameSize` specified incorrectly")
                
            # recommended camera drivers for each platform
            cameraPlatformDrivers = {
                'Linux': CAMERA_API_VIDEO4LINUX2,
                'Windows': CAMERA_API_DIRECTSHOW,
                'Darwin': CAMERA_API_AVFOUNDATION
            }
            # get the recommended camera driver for the current platform
            cameraAPI = cameraPlatformDrivers[platform.system()]

            self._cameraInfo = CameraInfo(
                index=device, 
                frameRate=frameRate,   # dummy value
                frameSize=frameSize,  # dummy value
                pixelFormat='bgr24', 
                cameraLib=cameraLib, 
                cameraAPI=cameraAPI)
            
            self._device = self._cameraInfo.description()

        elif self._cameraLib == u'ffpyplayer':
            supportedCameraSettings = CameraInterfaceFFmpeg.getCameras()

            # create a mapping of supported camera formats
            _formatMapping = dict()
            for _, formats in supportedCameraSettings.items():
                for _format in formats:
                    desc = _format.description()
                    _formatMapping[desc] = _format
            # sort formats by resolution then frame rate
            orderedFormats = list(_formatMapping.values())
            orderedFormats.sort(key=lambda obj: obj.frameRate, reverse=True)
            orderedFormats.sort(key=lambda obj: np.prod(obj.frameSize), 
                                reverse=True)

            # list of devices
            devList = list(_formatMapping)

            if not devList:  # no cameras found if list is empty
                raise CameraNotFoundError('No cameras found of the system!')

            # Get best device
            bestDevice = _formatMapping[devList[-1]]
            for mode in orderedFormats:
                sameFrameRate = mode.frameRate == frameRate or frameRate is None
                sameFrameSize = mode.frameSize == frameSize or frameSize is None
                if sameFrameRate and sameFrameSize:
                    bestDevice = mode
                    break

            # if given just device name, use frameRate and frameSize to match it 
            # to a mode
            if device in supportedCameraSettings:
                match = None
                for mode in supportedCameraSettings[device]:
                    sameFrameRate = \
                        mode.frameRate == frameRate or frameRate is None
                    sameFrameSize = \
                        mode.frameSize == frameSize or frameSize is None
                    if sameFrameRate and sameFrameSize:
                        match = mode
                if match is not None:
                    device = match
                else:
                    # if no match found, find closest
                    byWidth = sorted(
                        supportedCameraSettings[device],
                        key=lambda mode: abs(frameSize[0] - mode.frameSize[0])
                    )
                    byHeight = sorted(
                        supportedCameraSettings[device],
                        key=lambda mode: abs(frameSize[1] - mode.frameSize[1])
                    )
                    byFrameRate = sorted(
                        supportedCameraSettings[device],
                        key=lambda mode: abs(mode.frameRate)
                    )
                    deltas = [
                        byWidth.index(mode) + byHeight.index(mode) + byFrameRate.index(mode)
                        for mode in supportedCameraSettings[device]
                    ]
                    i = deltas.index(min(deltas))
                    closest = supportedCameraSettings[device][i]
                    # log warning that settings won't match requested
                    logging.warn(_translate(
                        "Device {device} does not support frame rate of "
                        "{frameRate} and frame size of {frameSize}, using "
                        "closest supported format: {desc}"
                    ).format(device=device, 
                             frameRate=frameRate, 
                             frameSize=frameSize, 
                             desc=closest.description()))
                    # use closest
                    device = closest

            # self._origDevSpecifier = device  # what the user provided
            self._device = None  # device identifier

            # alias device None or Default as being device 0
            if device in (None, "None", "none", "Default", "default"):
                self._device = bestDevice.description()
            elif isinstance(device, CameraInfo):
                if self._cameraLib != device.cameraLib:
                    raise CameraFormatNotSupportedError(
                        'Wrong configuration for camera library!')
                self._device = device.description()
            else:
                # resolve getting the camera identifier
                if isinstance(device, int):  # get camera if integer
                    try:
                        self._device = devList[device]
                    except IndexError:
                        raise CameraNotFoundError(
                            'Cannot find camera at index={}'.format(device))
                elif isinstance(device, str):
                    self._device = device
                else:
                    raise TypeError(
                        f"Incorrect type for `camera`, expected `int` or `str` but received {repr(device)}")

            # get the camera information
            if self._device in _formatMapping:
                self._cameraInfo = _formatMapping[self._device]
            else:
                # raise error if couldn't find matching camera info
                raise CameraFormatNotSupportedError(
                    f'Specified camera format {repr(self._device)} is not supported.')

        # # operating mode
        # if mode not in (CAMERA_MODE_VIDEO, CAMERA_MODE_CV, CAMERA_MODE_PHOTO):
        #     raise ValueError(
        #         "Invalid value for parameter `mode`, expected one of `'video'` "
        #         "`'cv'` or `'photo'`.")
        # self._mode = mode

        _requestedMic = mic
        # if not given a Microphone or MicrophoneDevice, get it from DeviceManager
        if not isinstance(mic, (Microphone, MicrophoneDevice)):
            mic = DeviceManager.getDevice(mic)
        # if not known by name, try index
        if mic is None:
            mic = DeviceManager.getDeviceBy("index", mic, deviceClass="microphone")
        # if not known by name or index, raise error
        if mic is None:
            raise SystemError(f"Could not find microphone {_requestedMic}")

        # current camera frame since the start of recording
        self._player = None  # media player instance
        self.status = NOT_STARTED
        self._isRecording = False
        self._bufferSecs = float(bufferSecs)
        self._lastFrame = None  # use None to avoid imports for ImageStim

        # microphone instance, this is controlled by the camera interface and
        # is not meant to be used by the user
        self.mic = mic
        # other information
        self.name = name
        # timestamp data
        self._streamTime = 0.0
        # store win (unused but needs to be set/got safely for parity with JS)
        self.win = win
        
        # movie writer instance, this runs in a separate thread
        self._movieWriter = None
        # if we begin receiving frames, change this flag to `True`
        self._captureThread = None
        # self._audioThread = None
        self._captureFrames = []  # array for storing frames
        # thread for polling the microphone
        self._audioTrack = None  # audio track from the recent recording
        # used to sync threads spawned by this class, created on `open()`
        self._syncBarrier = None
        # keep track of the last video file saved
        self._lastVideoFile = None

    def authorize(self):
        """Get permission to access the camera. Not implemented locally yet.
        """
        pass  # NOP

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
        if self._captureThread is None:
            return False

        return self._captureThread.isOpen()

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
        MovieMetadata
            Metadata about the video stream, retrieved during the last frame
            update (`_enqueueFrame` call).

        """
        return self._recentMetadata

    # @property
    # def mode(self):
    #     """Operating mode in use for this camera.
    #     """
    #     return self._mode

    _getCamerasCache = {}

    @staticmethod
    def getCameras(cameraLib=None):
        """Get information about installed cameras on this system.

        Returns
        -------
        dict
            Mapping of camera information objects.

        """
        # not pluggable yet, needs to be made available via extensions
        if cameraLib == 'opencv':
            if 'opencv' not in Camera._getCamerasCache:
                Camera._getCamerasCache['opencv'] = \
                    CameraInterfaceOpenCV.getCameras()
            return Camera._getCamerasCache['opencv']
        elif cameraLib == 'ffpyplayer':
            if 'ffpyplayer' not in Camera._getCamerasCache:
                Camera._getCamerasCache['ffpyplayer'] = \
                    CameraInterfaceFFmpeg.getCameras()
            return Camera._getCamerasCache['ffpyplayer']
        else:
            raise ValueError("Invalid value for parameter `cameraLib`")

    @staticmethod
    def getAvailableDevices():
        devices = []
        for dev in st.getCameras():
            for spec in dev:
                devices.append({
                    'device': spec['index'],
                    'frameRate': spec['frameRate'],
                    'frameSize': spec['frameSize'],
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
    def streamTime(self):
        """Current stream time in seconds (`float`). This time increases
        monotonically from startup. 
        
        This is `-1.0` if there is no active stream running or if the backend 
        does not support this feature.

        """
        if self.isStarted and hasattr(self._captureThread, "streamTime"):
            return self._captureThread.streamTime
        
        return -1.0

    @property
    def recordingTime(self):
        """Current recording timestamp (`float`).

        This returns the timestamp of the last frame captured in the recording.

        This value increases monotonically from the last `record()` call. It
        will reset once `stop()` is called. This value is invalid outside
        `record()` and `stop()` calls.

        """
        if not self._isRecording:
            return 0.0

        frameInterval = 1.0 / float(self._captureThread.frameRate)

        return self.frameCount * frameInterval

    @property
    def recordingBytes(self):
        """Current size of the recording in bytes (`int`).
        """
        if not self._isRecording:
            return 0

        return self._captureThread.recordingBytes

    def _assertMediaPlayer(self):
        """Assert that we have a media player instance open.

        This will raise a `RuntimeError` if there is no player open. Use this
        function to ensure that a player is present before running subsequent
        code.
        """
        if self._captureThread is not None:
            return

        raise PlayerNotAvailableError('Media player not initialized.')

    def _enqueueFrame(self):
        """Pull waiting frames from the capture thread.

        This function will pull frames from the capture thread and add them to
        the buffer. The last frame in the buffer will be set as the most recent
        frame (`lastFrame`).

        Returns
        -------
        bool
            `True` if a frame has been enqueued. Returns `False` if the camera
            is not ready or if the stream was closed.

        """
        if self._captureThread is None:
            return False

        newFrames = self._captureThread.getFrames()
        if not newFrames:
            return False
        
        # add frames the the buffer
        self._captureFrames.extend(newFrames)
        
        # set the last frame in the buffer as the most recent
        self._lastFrame = self._captureFrames[-1]

        return True

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
        desc = self._cameraInfo.description()
        if self._cameraLib == u'ffpyplayer':
            logging.debug(
                "Opening camera stream using FFmpeg. (device={})".format(desc))
            self._captureThread = CameraInterfaceFFmpeg(
                device=self._cameraInfo, 
                mic=self._mic)
        elif self._cameraLib == u'opencv':
            logging.debug(
                "Opening camera stream using OpenCV. (device={})".format(desc))
            self._captureThread = CameraInterfaceOpenCV(
                device=self._cameraInfo, 
                mic=self._mic)
        else:
            raise ValueError(
                "Invalid value for parameter `cameraLib`, expected one of "
                "`'ffpyplayer'` or `'opencv'`.")
        
        self._captureThread.open()

    # def snapshot(self):
    #     """Take a photo with the camera. The camera must be in `'photo'` mode
    #     to use this method.
    #     """
    #     pass

    def record(self):
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
        be discarded if `record()` is called again.

        """
        if self.isNotStarted:
            self.open()   # open the camera stream if we call record() first
            logging.warning(
                "Called `Camera.record()` before opening the camera stream, "
                "opening now. This is not recommended as it may incur a longer "
                "than expected delay in the recording start time."
            )
        
        self._audioTrack = None
        self._lastFrame = None

        # start recording audio if available
        if self._mic is not None:
            logging.debug(
                "Microphone interface available, starting audio recording.")
        else:
            logging.debug(
                "No microphone interface provided, not recording audio.")

        self._captureThread.enable()  # start passing frames to queue
        self._enqueueFrame()

        self._isRecording = True

    def stop(self):
        """Stop recording frames and audio (if available).
        """
        if self._captureThread is None:  # do nothing if not open
            return

        if not self._captureThread.isOpen():
            raise RuntimeError("Cannot stop recording, stream is not open.")

        self._captureThread.disable()  # stop passing frames to queue
        self._enqueueFrame()

        # # stop audio recording if `mic` is available
        if self._mic is not None:
            self._audioTrack = self._mic.getRecording()

        self._isRecording = False

    def close(self):
        """Close the camera.

        This will close the camera stream and free up any resources used by the
        device. If the camera is currently recording, this will stop the 
        recording, but will not discard any frames. You may still call `save()`
        to save the frames to disk.

        """
        if self._captureThread is None:  # nop
            return

        if not self._captureThread.isOpen():
            raise RuntimeError("Cannot close stream, stream is not open.")
        
        if self._isRecording:
            logging.warning(
                "Closing camera stream while recording, stopping recording "
                "first.")
            self.stop()

        self._captureThread.close()
        self._captureThread = None

    def save(self, filename, useThreads=True, mergeAudio=True, 
             encoderLib=None, encoderOpts=None):
        """Save the last recording to file.

        This will write frames to `filename` acquired since the last call of 
        `record()` and subsequent `stop()`. If `record()` is called again before 
        `save()`, the previous recording will be deleted and lost.

        This is a slow operation and will block for some time depending on the 
        length of the video. This can be sped up by setting `useThreads=True`.

        Parameters
        ----------
        filename : str
            File to save the resulting video to, should include the extension.
        useThreads : bool
            Use threading where possible to speed up the saving process. If
            `True`, the video will be saved and composited in a separate thread
            and this function will return quickly. If `False`, the video will
            be saved and composited in the main thread and this function will
            block until the video is saved. Default is `True`.
        mergeAudio : bool
            Merge the audio track from the microphone with the video. If `True`,
            the audio track will be merged with the video. If `False`, the
            audio track will be saved to a separate file. Default is `True`.
        encoderLib : str or None
            Encoder library to use for saving the video. This can be either
            `'ffpyplayer'` or `'opencv'`. If `None`, the same library that was
            used to open the camera stream. Default is `None`.
        encoderOpts : dict
            Options to pass to the encoder. This is a dictionary of options
            specific to the encoder library being used. See the documentation
            for `~psychopy.tools.movietools.MovieFileWriter` for more details.

        """
        if self._isRecording:
            raise RuntimeError(
                "Attempting to call `save()` before calling `stop()`.")

        # check if a file exists at the given path, if so, delete it
        if os.path.exists(filename):
            msg = (
                "Video file '{}' already exists, overwriting.".format(filename))
            logging.warning(msg)
            os.remove(filename)

        # determine if the `encoderLib` to use
        if encoderLib is None:
            encoderLib = self._cameraLib
            
        logging.debug(
            "Using encoder library '{}' to save video.".format(encoderLib))

        # check if the encoder library name string is valid
        if encoderLib not in ('ffpyplayer', 'opencv'):
            raise ValueError(
                "Invalid value for parameter `encoderLib`, expected one of "
                "`'ffpyplayer'` or `'opencv'`.")

        # check if we have an audio track to save
        hasAudio = self._audioTrack is not None

        # create a temporary file names for the video and audio
        if hasAudio:
            if mergeAudio:
                tempPrefix = (uuid.uuid4().hex)[:16]   # 16 char prefix
                videoFileName = "{}_video.mp4".format(tempPrefix)
                audioFileName = "{}_audio.wav".format(tempPrefix)
            else:
                videoFileName = audioFileName = filename 
                audioFileName += '.wav'
        else:
            videoFileName = filename
            audioFileName = None

        # make sure filenames are absolute paths
        videoFileName = os.path.abspath(videoFileName)
        if audioFileName is not None:
            audioFileName = os.path.abspath(audioFileName)

        # flush outstanding frames from the camera queue
        self._enqueueFrame()

        # contain video and not audio
        logging.debug("Saving video to file: {}".format(videoFileName))
        self._movieWriter = movietools.MovieFileWriter(
            filename=videoFileName,
            size=self._cameraInfo.frameSize,  # match camera params
            fps=self._cameraInfo.frameRate,
            codec=None,  # mp4
            pixelFormat='rgb24',
            encoderLib=encoderLib,
            encoderOpts=encoderOpts)
        self._movieWriter.open()  # blocks main thread until opened and ready

        # flush remaining frames to the writer thread, this is really fast since
        # frames are not copied and don't require much conversion
        for frame in self._captureFrames:
            self._movieWriter.addFrame(frame.colorData)
        
        # push all frames to the queue for the movie recorder
        self._movieWriter.close()  # thread-safe call
        self._movieWriter = None

        # save audio track if available
        if hasAudio:
            logging.debug(
                "Saving audio track to file: {}".format(audioFileName))
            self._audioTrack.save(audioFileName, 'wav')
        
            # merge audio and video tracks
            if mergeAudio:
                logging.debug("Merging audio and video tracks.")
                movietools.addAudioToMovie(
                    filename,  # file after merging
                    videoFileName, 
                    audioFileName, 
                    useThreads=useThreads,
                    removeFiles=True)  # disable threading for now

        self._lastVideoFile = filename  # remember the last video we saved

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
    
    def update(self):
        """Acquire the newest data from the camera stream. If the `Camera`
        object is not being monitored by a `ImageStim`, this must be explicitly
        called.
        """
        self._assertMediaPlayer()
        self._enqueueFrame()

    def getVideoFrame(self):
        """Pull the most recent frame from the stream (if available).

        Returns
        -------
        MovieFrame
            Most recent video frame. Returns `NULL_MOVIE_FRAME_INFO` if no
            frame was available, or we timed out.

        """
        self.update()

        return self._lastFrame

    def __del__(self):
        """Try to cleanly close the camera and output file.
        """

        if hasattr(self, '_captureThread'):
            if self._captureThread is not None:
                try:
                    self._captureThread.close()
                except AttributeError:
                    pass

        # close the microphone during teardown too
        if hasattr(self, '_mic'):
            if self._mic is not None:
                try:
                    self._mic.close()
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


# Mapping for platform specific camera getter functions used by `getCameras`.
_cameraGetterFuncTbl = {
    'Darwin': _getCameraInfoMacOS,
    'Windows': _getCameraInfoWindows
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
        if issubclass(cls, CameraInterface):
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


if __name__ == "__main__":
    pass
