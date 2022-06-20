#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for reading and writing camera streams.

A camera may be used to document participant responses on video or used by the
experimenter to create movie stimuli or instructions.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['CameraNotFoundError', 'Camera', 'CameraInfo', 'StreamData',
           'getCameras', 'getCameraDescriptions']

import platform
import numpy as np
import tempfile
import os
import os.path
import shutil
import math
from psychopy.constants import STOPPED, NOT_STARTED, RECORDING
from psychopy.visual.movies.metadata import MovieMetadata, NULL_MOVIE_METADATA
from psychopy.visual.movies.frame import MovieFrame, NULL_MOVIE_FRAME_INFO
from psychopy.sound.microphone import Microphone
import psychopy.logging as logging
from ffpyplayer.player import MediaPlayer
from ffpyplayer.writer import MediaWriter
from ffpyplayer.pic import SWScale
from ffpyplayer.tools import list_dshow_devices, get_format_codec
# Something in moviepy.editor's initialisation breaks Mouse, so import these
# from the source instead
# from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip
import uuid
import threading
import queue
import time
import cv2  # used to get camera information


# ------------------------------------------------------------------------------
# Constants
#

VIDEO_DEVICE_ROOT_LINUX = '/dev'
CAMERA_UNKNOWN_VALUE = u'Unknown'  # fields where we couldn't get a value
CAMERA_NULL_VALUE = u'Null'  # fields where we couldn't get a value
# camera operating modes
CAMERA_MODE_VIDEO = u'video'
CAMERA_MODE_CV = u'cv'
CAMERA_MODE_PHOTO = u'photo'
# default names for video and audio tracks in the temp directory
CAMERA_TEMP_FILE_VIDEO = u'video.mp4'
CAMERA_TEMP_FILE_AUDIO = u'audio.wav'

# camera API flags, these specify which API camera settings were queried with
CAMERA_API_AVFOUNDATION = u'AVFoundation'  # mac
CAMERA_API_DIRECTSHOW = u'DirectShow'      # windows
CAMERA_API_VIDEO4LINUX = u'Video4Linux'    # linux
CAMERA_API_OPENCV = u'OpenCV'              # opencv, cross-platform API
CAMERA_API_UNKNOWN = u'Unknown'            # unknown API
CAMERA_API_NULL = u'Null'                  # empty field

# camera libraries for playback nad recording
CAMERA_LIB_FFPYPLAYER = u'FFPyPlayer'
CAMERA_LIB_UNKNOWN = u'Unknown'
CAMERA_LIB_NULL = u'Null'

# special values
CAMERA_FRAMERATE_NOMINAL_NTSC = '30.000030'
CAMERA_FRAMERATE_NTSC = 30.000030

# default values for camera settings
cameraCodecs = []


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
    name : str
        Camera name retrieved by the OS. This may be a human-readable name
        (i.e. DirectShow on Windows), an index on MacOS or a path (e.g.,
        `/dev/video0` on Linux).
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
                 frameRate=(-1, -1),
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
        """Resolution (w, h) in pixels (`ArrayLike`).
        """
        return self._frameSize

    @frameSize.setter
    def frameSize(self, value):
        assert len(value) == 2, "Value for `frameSize` must have length 2."
        assert all([isinstance(i, int) for i in value]), (
            "Values for `frameSize` must be integers.")

        self._frameSize = value

    @property
    def frameRate(self):
        """Resolution (min, max) in pixels (`ArrayLike`).
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

        Returns
        -------
        str
            Description of the camera format as a human readable string.

        """
        codecFormat = self._codecFormat
        pixelFormat = self._pixelFormat
        codec = codecFormat if not pixelFormat else pixelFormat

        return "[{name}] {width}x{height}@{frameRate}fps, {codec}".format(
            #index=self.index,
            name=self.name,
            width=str(self.frameSize[0]),
            height=str(self.frameSize[1]),
            frameRate=str(self.frameRate),
            codec=codec
        )


class StreamStatus:
    """Descriptor class for stream status.

    This class is used to report the current status of the stream read/writer.

    Parameters
    ----------
    status : int
        Status flag for the stream.
    streamTime : float
        Current stream time in seconds. This value increases monotonically and
        is common to all webcams attached to the system.
    recTime : float
        If recording, this field will report the current timestamp within the
        output file. Otherwise, this value is zero.
    recBytes : float
        If recording, this value indicates the number of bytes that have been
        written out to file.

    """
    __slots__ = ['_status',
                 '_streamTime',
                 '_recTime',
                 '_recBytes']

    def __init__(self,
                 status=NOT_STARTED,
                 streamTime=0.0,
                 recTime=0.0,
                 recBytes=0):

        self._status = int(status)
        self._streamTime = float(streamTime)
        self._recTime = float(recTime)
        self._recBytes = int(recBytes)

    @property
    def status(self):
        """Status flag for the stream (`int`).
        """
        return self._status

    @property
    def streamTime(self):
        """Current stream time in seconds (`float`).

        This value increases monotonically and is common timebase for all
        cameras attached to the system.
        """
        return self._streamTime

    @property
    def recBytes(self):
        """Current recording size on disk (`int`).

        If recording, this value indicates the number of bytes that have been
        written out to file.
        """
        return self._recBytes

    @property
    def recTime(self):
        """Current recording time (`float`).

        If recording, this field will report the current timestamp within the
        output file. Otherwise, this value is zero.
        """
        return self._recTime


class StreamData:
    """Descriptor for camera stream data.

    Instances of this class are produced by the stream reader/writer thread
    which contain: metadata about the stream, frame image data (i.e. pixel
    values), and the stream status.

    Parameters
    ----------
    metadata : MovieMetadata
        Stream metadata.
    frameImage : object
        Video frame image data.
    streamStatus : StreamStatus
        Video stream status.
    cameraLib : str
        Camera library in use to process the stream.

    """
    __slots__ = ['_metadata',
                 '_frameImage',
                 '_streamStatus',
                 '_cameraLib']

    def __init__(self, metadata, frameImage, streamStatus, cameraLib):
        self._metadata = metadata
        self._frameImage = frameImage
        self._streamStatus = streamStatus
        self._cameraLib = cameraLib

    @property
    def metadata(self):
        """Stream metadata at the time the video frame was acquired
        (`MovieMetadata`).
        """
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        if not isinstance(value, MovieMetadata) or value is not None:
            raise TypeError("Incorrect type for property `metadata`, expected "
                            "`MovieMetadata` or `None`.")

        self._metadata = value

    @property
    def frameImage(self):
        """Frame image data from the codec (`ffpyplayer.pic.Image`).
        """
        return self._frameImage

    @frameImage.setter
    def frameImage(self, value):
        self._frameImage = value

    @property
    def streamStatus(self):
        """Stream status (`StreamStatus`).
        """
        return self._streamStatus

    @streamStatus.setter
    def streamStatus(self, value):
        if not isinstance(value, StreamStatus) or value is not None:
            raise TypeError("Incorrect type for property `streamStatus`, "
                            "expected `StreamStatus` or `None`.")

        self._streamStatus = value

    @property
    def cameraLib(self):
        """Camera library in use to obtain the stream (`str`). Value is
        blank if `metadata` is `None`.
        """
        if self._metadata is not None:
            return self._metadata.movieLib

        return u''


class MovieStreamIOThread(threading.Thread):
    """Class for reading and writing streams asynchronously.

    The rate of which frames are read is controlled dynamically based on values
    within stream metadata. This will ensure that CPU load is kept to a minimum,
    only polling for new frames at the rate they are being made available.

    Parameters
    ----------
    player : `ffpyplayer.player.MediaPlayer`
        Media player instance, should be configured and initialized. Note that
        player instance methods might not be thread-safe after handing off the
        object to this thread.
    bufferFrames : int
        Number of frames to buffer. Sets the frame queue size for the thread.

    """
    def __init__(self, player, bufferFrames=1):
        threading.Thread.__init__(self)
        self.daemon = False

        self._player = player  # player interface to FFMPEG
        self._writer = None  # writer interface
        self._mic = None
        self._frameQueue = queue.Queue(
            maxsize=bufferFrames)  # frames for the monitor
        self._cmdQueue = queue.Queue()  # command queue

        # some values the user might want
        self._status = NOT_STARTED
        self._recordingTime = 0.0
        self._recordingBytes = 0
        self._streamTime = 0.0

        self._isReadyEvent = threading.Event()
        self._isRecording = threading.Event()
        self._isStreamingEvent = threading.Event()
        self._stopSignal = threading.Event()

        # Locks for syncing the player and main application thread
        self._warmUpLock = threading.Lock()
        self._warmUpLock.acquire(blocking=False)

    def run(self):
        """Main sub-routine for this thread.

        When the thread is running, data about captured frames are put into the
        `frameQueue` as `(metadata, img, pts)`. If the queue is empty, that
        means the main application thread is running faster than the encoder
        can get frames.

        """
        if self._player is None:
            return  # exit thread if no player

        frameInterval = 0.001  # dynamic poll interval, start at 1ms
        ptsStart = 0.0
        recordingJustStarted = True
        streaming = True
        while 1:
            # process commands in queue
            while not self._cmdQueue.empty():
                cmdOpCode, cmdVal = self._cmdQueue.get()
                if cmdOpCode == 'record':
                    self._status = RECORDING
                elif cmdOpCode == 'stop':
                    self._status = STOPPED
                elif cmdOpCode == 'shutdown':
                    self._status = STOPPED
                    streaming = False

            if not streaming:
                break

            # consume frames until we get a valid one
            frameData, val = self._player.get_frame()
            if frameData is None or val == 'not ready':
                continue

            if val == 'eof':
                break

            if self._warmUpLock.locked():
                self._warmUpLock.release()  # release warmup lock

            # after getting a frame, we can get accurate metadata
            metadata = self._player.get_metadata()

            # compute frame interval for dynamic polling rate
            frameRate = metadata['frame_rate']
            numer, denom = frameRate
            if denom == 0:  # no valid framerate from metadata yet
                continue

            # compute the frame interval that will be used
            frameInterval = 1.0 / (numer / float(denom))

            # split the data
            colorData, pts = frameData
            self._streamTime = pts

            # handle writing to file
            if self._status == RECORDING and self._writer is not None:
                if recordingJustStarted:
                    ptsStart = self._streamTime
                    recordingJustStarted = False

                # compute timestamp for the writer for the current frame
                self._recordingTime = self._streamTime - ptsStart

                frameWidth, frameHeight = colorData.get_size()
                pixelFormat = colorData.get_pixel_format()

                # convert color format to rgb24 since we're doing raw video
                sws = SWScale(
                    frameWidth,
                    frameHeight,
                    pixelFormat,
                    ofmt='yuv420p')

                # write the frame to the file
                self._recordingBytes = self._writer.write_frame(
                    img=sws.scale(colorData),
                    pts=self._recordingTime,
                    stream=0)

                # poll the mic if available to flush the sample buffer
                if self._mic is not None:
                    self._mic.poll()

            else:
                if not recordingJustStarted:
                    # reset stream recording vars when done
                    ptsStart = 0.0
                    self._recordingBytes = 0
                    self._recordingTime = 0.0
                    recordingJustStarted = True

            # Put the frame in the queue to allow the main thread to safely
            # access it. If the queue is full, the frame data will be discarded
            # at this point. The image will be lost unless the encoder is
            # recording.
            streamStatus = StreamStatus(
                status=self._status,
                streamTime=self._streamTime,
                recTime=self._recordingTime,
                recBytes=self._recordingBytes)

            # Object to pass video frame data back to the application thread
            # for presentation or processing.
            img, _ = frameData
            toReturn = StreamData(metadata, img, streamStatus, u'ffpyplayer')

            try:
                self._frameQueue.put(toReturn)  # put frame data in here
            except queue.Full:
                pass

            time.sleep(frameInterval)

    @property
    def isReady(self):
        """`True` if the stream reader is ready (`bool`).
        """
        return self._isReadyEvent.is_set()

    def begin(self):
        """Stop the thread.
        """
        self.start()
        # hold until the lock is released when the thread gets a valid frame
        # this will prevent the main loop for executing until we're ready
        self._warmUpLock.acquire(blocking=True)

    def record(self, writer, mic=None):
        """Start recording frames to the output video file.

        Parameters
        ----------
        writer : MediaWriter
            Media writer object to record with.
        mic : Microphone or None
            Option audio capture device to use with the camera. This object will
            be controlled by the thread.

        """
        self._writer = writer
        self._mic = mic

        # need at least a writer to use this
        if not isinstance(self._writer, MediaWriter):
            raise TypeError(
                "Expected type `MediaWriter` for parameter `writer`.")

        self._cmdQueue.put(('record', None))

    def stop(self):
        """Stop recording frames to the output file.
        """
        self._cmdQueue.put(('stop', None))

    def shutdown(self):
        """Stop the thread.
        """
        self._cmdQueue.put(('shutdown', None))

    def getRecentFrame(self):
        """Get the most recent frame data from the feed (`tuple`).

        Returns
        -------
        tuple or None
            Frame data formatted as `(metadata, frameData, val)`. The `metadata`
            is a `dict`, `frameData` is a `tuple` with format (`colorData`,
            `pts`) and `val` is a `str` returned by the
            `MediaPlayer.get_frame()` method. Returns `None` if there is no
            frame data.

        """
        if self._frameQueue.empty():
            return None

        # hold only last frame and return that instead of None?
        return self._frameQueue.get_nowait()


class Camera:
    """Class of displaying and recording video from a USB/PCI connected camera.

    This class is capable of opening, recording, and saving camera video streams
    to disk. Camera stream reading/writing is done in a separate thread. Output
    video and audio tracks are written to a temp directory and composited into
    the final video when `save()` is called.

    Parameters
    ----------
    device : str or int
        Camera to open a stream with. If the ID is not valid, an error will be
        raised when `start()` is called. Value can be a string or number. String
        values are platform-dependent: a DirectShow URI on Windows, a path
        on GNU/Linux (e.g., `'/dev/video0'`), or a camera name/index on MacOS.
        Specifying a number (>=0) is a platform-independent means of selecting a
        camera. PsychoPy enumerates possible camera devices and makes them
        selectable without explicitly having the name of the cameras attached to
        the system. Use caution when specifying an integer, as the same index
        may not reference the same camera everytime.
    mic : :class:`~psychopy.sound.microphone.Microphone` or None
        Microphone to record audio samples from during recording. The microphone
        input device must not be in use when `record()` is called. The audio
        track will be merged with the video upon calling `save()`.
    cameraLib : str
        Interface library (backend) to use for accessing the camera. Only
        `ffpyplayer` is available at this time.
    codecOpts : dict or None
        Options to pass to the codec. See the documentation for the camera
        library for details. Some options may be set by this class already. Do
        not set these unless you know what you are doing!
    libOpts : dict or None
        Additional options to configure the camera interface library (if
        applicable). Do not set these unless you know what you are doing!
    bufferSecs : float
        Size of the real-time camera stream buffer specified in seconds (only
        valid on Windows and MacOS).
    win : :class:`~psychopy.visual.Window` or None
        Optional window associated with this camera. Some functionality may
        require an OpenGL context.
    name : str
        Label for the camera for logging purposes.

    Examples
    --------
    Opening a camera stream and closing it::

        camera = Camera(camera='/dev/video0')
        camera.open()  # exception here on invalid camera
        # camera.status == NOT_STARTED
        camera.record()
        # camera.status == RECORDING
        camera.stop()
        # camera.status == STOPPED
        camera.close()

    """
    def __init__(self, device=0, mic=None, cameraLib=u'ffpyplayer',
                 frameRate=None, frameSize=None,
                 codecOpts=None, libOpts=None, bufferSecs=4, win=None,
                 name='cam'):

        # add attributes for setters
        self.__dict__.update(
            {'_device': None,
             '_mic': None,
             '_outFile': None,
             '_mode': u'video',
             '_frameRate': None,
             '_frameRateFrac': None,
             '_size': None,
             '_cameraLib': u'',
             '_codecOpts': None,
             '_libOpts': None})

        # ----------------------------------------------------------------------
        # Process camera settings
        #

        # get all the cameras attached to the system
        supportedCameraSettings = getCameras()

        # create a mapping of supported camera formats
        _formatMapping = dict()
        for _, formats in supportedCameraSettings.items():
            for _format in formats:
                desc = _format.description()
                _formatMapping[desc] = _format

        # list of devices
        devList = list(_formatMapping)

        if not devList:  # no cameras found if list is empty
            raise CameraNotFoundError('No cameras found of the system!')

        # Best device usually shows up last on the list, this will be the
        # default when the index is 0 or the user specifies 'default'.
        bestDevice = _formatMapping[devList[-1]]

        self._origDevSpecifier = device  # what the user provided
        self._device = None  # device identifier

        # alias device None or Default as being device 0
        if device in (None, "None", "none", "Default", "default"):
            self._device = bestDevice
        else:
            # resolve getting the camera identifier
            if isinstance(device, int):  # get camera if integer
                try:
                    self._device = devList[device]
                except IndexError:
                    raise CameraNotFoundError(
                        'Cannot find camera at index={}'.format(device))
            elif isinstance(device, str):  # get camera if integer
                self._device = device
            else:
                raise TypeError(
                    "Incorrect type for `camera`, expected `int` or `str`.")

        # get the camera information
        self._cameraInfo = None
        for mode in _formatMapping.values():
            sameDevice = mode.name == self._device.name
            sameFrameRate = mode.frameRate == frameRate or frameRate is None
            sameFrameSize = mode.frameSize == frameSize or frameSize is None
            if sameDevice and sameFrameRate and sameFrameSize:
                self._cameraInfo = mode
        # raise error if couldn't find matching camera info
        if self._cameraInfo is None:
            raise CameraFormatNotSupportedError(
                'Specified camera format is not supported.'
            )

        # Check if the cameraAPI is suitable for the operating system. This is
        # a sanity check to ensure people aren't using formats obtained from
        # other platforms.
        api = self._cameraInfo.cameraAPI
        thisSystem = platform.system()
        if ((api == CAMERA_API_AVFOUNDATION and thisSystem != 'Darwin') or
                (api == CAMERA_API_DIRECTSHOW and thisSystem != 'Windows') or
                (api == CAMERA_API_VIDEO4LINUX and thisSystem != 'Linux')):
            raise RuntimeError(
                "Unsupported camera interface '{}' for platform '{}'".format(
                    api, thisSystem))

        # camera library in use
        self._cameraLib = cameraLib

        # # operating mode
        # if mode not in (CAMERA_MODE_VIDEO, CAMERA_MODE_CV, CAMERA_MODE_PHOTO):
        #     raise ValueError(
        #         "Invalid value for parameter `mode`, expected one of `'video'` "
        #         "`'cv'` or `'photo'`.")
        # self._mode = mode

        # FFMPEG and FFPyPlayer options
        self._codecOpts = codecOpts if codecOpts is not None else {}
        self._libOpts = libOpts if libOpts is not None else {}

        # parameters for the writer
        self._writer = None
        self._tempVideoFileName = u''
        self._tempAudioFileName = u''
        self._tempRootDir = u'.'

        if not isinstance(mic, Microphone):
            TypeError(
                "Expected type for parameter `mic`, expected `Microphone`.")
        self.mic = mic

        # other information
        self.name = name

        # current camera frame since the start of recording
        self._player = None  # media player instance
        self._status = NOT_STARTED
        self._frameIndex = -1
        self._isRecording = False
        self._isReady = False
        self._bufferSecs = float(bufferSecs)

        # timestamp data
        self._recordingTime = self._streamTime = 0.0
        self._recordingBytes = 0

        # store win (unused but needs to be set/got safely for parity with JS)
        self.win = win

        # thread for reading and writing streams
        self._tStream = None

        # video metadata
        self._recentMetadata = NULL_MOVIE_METADATA

        # last frame
        self._lastFrame = NULL_MOVIE_FRAME_INFO

        # last video file that has been saved, makes it easy to pass this value
        # along to a movie player
        self._lastClip = None

        # Keep track of temp dirs to clean up on error to prevent accumulating
        # files on the user's disk. On error during recordings we will clear
        # these files out.
        self._tempDirs = []

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

        """
        # The camera is ready when the following conditions are met. First,
        # we've created a player interface and opened it. Second, we have
        # received metadata about the stream. At this point we can assume that
        # the camera is 'hot' and the stream is being read.
        #
        return self._isReady

    @property
    def frameSize(self):
        """Size of the video frame obtained from recent metadata (`float` or
        `None`).

        Only valid after an `open()` and successive `_enqueueFrame()` call as
        metadata needs to be obtained from the stream. Returns `None` if not
        valid.
        """
        if self._recentMetadata is None:
            return None

        return self._recentMetadata.size

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
        return self.status == RECORDING

    @property
    def isNotStarted(self):
        """`True` if the stream may not have started yet (`bool`). This status
        is given after a video is loaded and play has yet to be called."""
        return self.status == NOT_STARTED

    @property
    def isStopped(self):
        """`True` if the recording has stopped (`bool`)."""
        return self.status == STOPPED

    @property
    def metadata(self):
        """Video metadata retrieved during the last frame update
        (`MovieMetadata`).
        """
        return self._recentMetadata

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

    @staticmethod
    def getCameras():
        """Get information about installed cameras on this system.

        Returns
        -------
        list
            Camera identifiers.

        """
        return getCameras()

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

    def _openWriter(self):
        """Initialize and configure the media writer.

        Must be called after the video stream has been opened and
        `_enqueueFrame` called at least once prior. This is needed since the
        stream metadata is required to configure the writer.

        """
        if self._writer is not None:
            raise RuntimeError(
                "Stream writer instance has already been created.")

        # need the stream started before setting up the writer
        self._assertMediaPlayer()

        # configure the temp directory and files for the recordings
        randFileName = str(uuid.uuid4().hex)
        self._tempRootDir = tempfile.mkdtemp(
            suffix=randFileName,
            prefix='psychopy-',
            dir=None)
        self._tempDirs.append(self._tempRootDir)  # keep track for clean-up
        self._tempVideoFileName = os.path.join(
            self._tempRootDir, CAMERA_TEMP_FILE_VIDEO)
        self._tempAudioFileName = os.path.join(
            self._tempRootDir, CAMERA_TEMP_FILE_AUDIO)

        # codec that best suits the output file type
        useCodec = get_format_codec(self._tempVideoFileName)

        frameWidth, frameHeight = self._lastFrame.metadata['src_vid_size']
        frameRate = self._lastFrame.metadata['frame_rate']

        # options to configure the writer, we use some default params for now
        # until we sort how to configure this easily for users
        writerOptions = {
            'pix_fmt_in': 'yuv420p',  # default for now using mp4
            # 'preset': 'medium',
            'width_in': frameWidth,
            'height_in': frameHeight,
            'codec': useCodec,
            'frame_rate': frameRate
        }

        # initialize the writer to transcode the video stream to file
        self._writer = MediaWriter(
            self._tempVideoFileName,
            [writerOptions],
            width_out=frameWidth, height_out=frameHeight,
            fmt='mp4',
            pix_fmt_out='yuv420p')

    def _closeWriter(self):
        """Close the video writer.
        """
        if self._writer is None:
            return

        # cleanup
        # self._writer.close()

        self._writer = None

    def _renderVideo(self, outFile):
        """Combine video and audio tracks of temporary video and audio files.
        Outputs a new file at `outFile` with merged video and audio tracks.

        Parameters
        ----------
        outFile : str
            Output file path for the composited video.

        """
        # this can only happen when stopped
        if self._status != STOPPED:
            raise RuntimeError(
                "Cannot render video, `stop` has not been called yet.")

        # merge audio and video tracks, we use MoviePy for this
        videoClip = VideoFileClip(self._tempVideoFileName)

        # if we have a microphone, merge the audio track in
        if self._mic is not None:
            audioClip = AudioFileClip(self._tempAudioFileName)
            # add audio track to the video
            videoClip.audio = CompositeAudioClip([audioClip])

        # transcode with the format the user wants
        videoClip.write_videofile(outFile)

        # delete the temp directory and files to clean up after composing the
        # video
        shutil.rmtree(self._tempRootDir)

        return True

    @property
    def status(self):
        """Status flag for the camera (`int`).

        Can be either `RECORDING`, `STOPPED`, `STOPPING`, or `NOT_STARTED`.

        """
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def outFile(self):
        """Output file for the video stream (`str`).
        """
        return self._outFile

    @outFile.setter
    def outFile(self, value):
        if self._writer is not None:
            raise ValueError("Cannot change `outFile` while recording.")

        self._outFile = value

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
    def mic(self):
        """Microphone to record audio samples from during recording
        (:class:`~psychopy.sound.microphone.Microphone` or `None`). If `None`,
        no audio will be recorded.
        """
        return self._mic

    @mic.setter
    def mic(self, value):
        self._mic = value

    @property
    def _hasPlayer(self):
        """`True` if we have an active media player instance.
        """
        return self._player is not None

    @property
    def _hasWriter(self):
        """`True` if we have an active file writer instance.
        """
        return self._writer is not None

    @property
    def streamTime(self):
        """Current stream time in seconds (`float`). This time increases
        monotonically from startup.
        """
        return self._streamTime

    @property
    def recordingTime(self):
        """Current recording timestamp (`float`).

        This value increases monotonically from the last `record()` call. It
        will reset once `stop()` is called. This value is invalid outside
        `record()` and `stop()` calls.

        """
        return self._recordingTime

    @property
    def recordingBytes(self):
        """Current size of the recording in bytes (`int`).
        """
        return self._recordingBytes

    def _assertMediaPlayer(self):
        """Assert that we have a media player instance open.

        This will raise a `RuntimeError` if there is no player open. Use this
        function to ensure that a player is present before running subsequent
        code.
        """
        if self._player is not None:
            return

        raise PlayerNotAvailableError('Media player not initialized.')

    def _enqueueFrame(self):
        """Grab the latest frame from the stream.

        Returns
        -------
        bool
            `True` if a frame has been enqueued. Returns `False` if the camera
            is not ready or if the stream was closed.

        """
        self._assertMediaPlayer()

        # If the queue is empty, the decoder thread has not yielded a new frame
        # since the last call.
        enqueuedFrame = self._tStream.getRecentFrame()

        if enqueuedFrame is None:
            return False

        # unpack the data we got back
        metadata = enqueuedFrame.metadata
        frameImage = enqueuedFrame.frameImage
        streamStatus = enqueuedFrame.streamStatus

        # status information
        self._streamTime = streamStatus.streamTime  # stream time for the camera
        self._recordingTime = streamStatus.recTime
        self._recordingBytes = streamStatus.recBytes

        # if we have a new frame, update the frame information
        videoBuffer = frameImage.to_bytearray()[0]
        videoFrameArray = np.frombuffer(videoBuffer, dtype=np.uint8)

        # provide the last frame
        self._lastFrame = MovieFrame(
            frameIndex=self._frameIndex,
            absTime=streamStatus.recTime,
            # displayTime=self._recentMetadata['frame_size'],
            size=frameImage.get_size(),
            colorData=videoFrameArray,
            audioChannels=0,
            audioSamples=None,
            metadata=metadata,
            movieLib=u'ffpyplayer',
            userData=None)

        return True

    def open(self):
        """Open the camera stream and begin decoding frames (if available).

        The value of `lastFrame` will be updated as new frames from the camera
        arrive.

        """
        if self._hasPlayer:
            raise RuntimeError('Cannot open `MediaPlayer`, already opened.')

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
        elif _cameraInfo.cameraAPI == CAMERA_API_AVFOUNDATION:  # darwin
            ff_opts['f'] = 'avfoundation'
            ff_opts['i'] = _camera = self._cameraInfo.name

            # handle pixel formats using FourCC
            if _cameraInfo.pixelFormat == 'yuvs':
                _cameraInfo.pixelFormat = 'yuyv422'  # only one we know about
            else:
                raise CameraFormatNotSupportedError(
                    'Pixel format is not supported.')

            # this needs to be exactly specified if using NTSC
            if math.isclose(CAMERA_FRAMERATE_NTSC, _cameraInfo.frameRate):
                _frameRate = CAMERA_FRAMERATE_NOMINAL_NTSC
            else:
                _frameRate = str(_cameraInfo.frameRate)

            # need these since hardware acceleration is not possible on Mac yet
            lib_opts['fflags'] = 'nobuffer'
            lib_opts['flags'] = 'low_delay'
            ff_opts['framedrop'] = True
            ff_opts['fast'] = True

        elif _cameraInfo.cameraAPI == CAMERA_API_VIDEO4LINUX:
            raise OSError(
                "Sorry, camera does not support Linux at this time. However it "
                "will in future versions.")
        else:
            raise RuntimeError("Unsupported camera API specified.")

        # set library options
        camWidth = _cameraInfo.frameSize[0]
        camHeight = _cameraInfo.frameSize[1]

        # configure the real-time buffer size
        _bufferSize = camWidth * camHeight * 3 * self._bufferSecs

        # get codec or pixel format
        _codecId = _cameraInfo.codecFormat
        _pixelId = _cameraInfo.pixelFormat

        # common settings across libraries
        lib_opts['rtbufsize'] = str(int(_bufferSize))
        lib_opts['video_size'] = _cameraInfo.frameSizeAsFormattedString()
        lib_opts['framerate'] = str(_frameRate)
        # lib_opts['pixel_format'] = 'yuyv422'
        if _cameraInfo.pixelFormat != '':
            lib_opts['pixel_format'] = _cameraInfo.pixelFormat
        if _cameraInfo.codecFormat != '':  # force codec
            ff_opts['vcodec'] = _cameraInfo.codecFormat

        ff_opts['framedrop'] = True
        ff_opts['fast'] = True

        # open a stream and pause it until ready
        self._player = MediaPlayer(_camera, ff_opts=ff_opts, lib_opts=lib_opts)

        # pass off the player to the thread which will process the stream
        self._tStream = MovieStreamIOThread(self._player)
        self._tStream.begin()

    def record(self):
        """Start recording frames.

        Warnings
        --------
        If a recording has been previously made without calling `save()` it will
        be discarded if `record()` is called again.

        """
        self._assertMediaPlayer()

        self._openWriter()

        # start the microphone
        if self._mic is not None:
            self._mic.record()

        self._tStream.record(self._writer, self._mic)
        self._status = RECORDING

    def snapshot(self):
        """Take a photo with the camera. The c
        amera must be in `'photo'` mode
        to use this method.
        """
        pass

    def stop(self):
        """Stop recording frames.
        """
        self._assertMediaPlayer()
        self._tStream.stop()
        self._status = STOPPED

        self._closeWriter()

        # stop audio recording if `mic` is available
        if self._mic is not None:
            self._mic.stop()
            audioTrack = self._mic.getRecording()
            audioTrack.save(self._tempAudioFileName, 'wav')

    def close(self):
        """Close the camera.
        """
        if not self._hasPlayer:
            raise RuntimeError("Cannot close stream, not opened yet.")

        # close the thread
        self._tStream.shutdown()  # close the stream
        self._tStream.join()  # wait until thread exits
        self._tStream = None

        # close the file writer
        if self._writer is not None:
            self._writer.close()

        self._player.close_player()
        self._player = None  # reset

        # cleanup temp files to prevent clogging up the user's hard disk
        self._cleanUpTempDirs()

    def save(self, filename):
        """Save the last recording to file.

        This will write the last video recording to `filename`. Method `stop()`
        must be called prior to saving a video. If `record()` is called again
        before `save()`, the previous recording will be deleted and lost.

        Returns
        -------
        int
            Final size of the output file at `filename` in bytes.

        """
        if self._status != STOPPED:
            raise RuntimeError(
                "Attempted to call `save()` a file before calling `stop()`.")

        # render the video
        if not self._renderVideo(outFile=filename):
            raise RuntimeError(
                "Failed to write file `filename`, check if the output path is "
                "writeable.")

        # make sure that `filename` is valid
        self._lastClip = os.path.abspath(filename)

        return os.path.getsize(self._lastClip)

    def _cleanUpTempDirs(self):
        """Cleanup temporary directories used by the video recorder.
        """
        if not hasattr(self, '_tempDirs'):  # crashed before declaration
            return  # nop

        logging.info("Cleaning up temporary video files ...")
        # total cleanup of all temp dirs
        for tempDir in self._tempDirs:
            absPathToTempDir = os.path.abspath(tempDir)
            if os.path.exists(absPathToTempDir):
                logging.info("Deleting temporary directory `{}` ...".format(
                    absPathToTempDir))
                shutil.rmtree(absPathToTempDir)

        logging.info("Done cleaning up temporary video files.")

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
        return self._lastClip

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
        """Pull the next frame from the stream (if available).

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
        if hasattr(self, '_player'):
            if self._player is not None:
                try:
                    self._player.close_player()
                except AttributeError:
                    pass

        if hasattr(self, '_writer'):
            if self._writer is not None:
                try:
                    self._writer.close()
                except AttributeError:
                    pass

        # close the microphone during teardown too
        if hasattr(self, '_mic'):
            if self._mic is not None:
                try:
                    self._mic.close()
                except AttributeError:
                    pass

        if hasattr(self, '_cleanUpTempDirs'):
            self._cleanUpTempDirs()


# ------------------------------------------------------------------------------
# Functions
#

def _getCameraInfoMacOS():
    """Get a list of capabilities for the specified associated with a camera
    attached to the system.

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

            # Extract the codec in use, pretty useless since FFMPEG uses it's
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
            codecCode = ''.join(
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
                pixelFormat=codecCode,
                codecFormat=codecCode,
                frameSize=(int(frameWidth), int(frameHeight)),
                frameRate=frameRateMax,
                cameraAPI=CAMERA_API_AVFOUNDATION
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
                cameraAPI=CAMERA_API_DIRECTSHOW
            )
            supportedFormats.append(temp)
            devIndex += 1

        videoDevices[names[devURI]] = supportedFormats

    return videoDevices


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
    if systemName == 'Darwin':  # MacOS
        foundCameras = _getCameraInfoMacOS()
    # elif systemName == 'Linux':
    #     # use glob to get possible cameras connected to the system
    #     globResult = glob.glob(
    #         'video*',
    #         root_dir=VIDEO_DEVICE_ROOT_LINUX,
    #         recursive=False)
    #     foundCameras.extend(globResult)
    #     # ensure the glob gives values in the same order
    #     foundCameras.sort()
    elif systemName == 'Windows':
        foundCameras = _getCameraInfoWindows()
    else:
        raise OSError(
            "Cannot get cameras, unsupported platform '{}'.".format(
                systemName))

    return foundCameras


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


if __name__ == "__main__":
    pass
