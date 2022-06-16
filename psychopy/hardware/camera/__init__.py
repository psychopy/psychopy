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
           'getCameras']

import glob
import platform
import numpy as np
import tempfile
import os
import shutil
from psychopy.constants import STOPPED, NOT_STARTED, RECORDING
from psychopy.visual.movies.metadata import MovieMetadata, NULL_MOVIE_METADATA
from psychopy.visual.movies.frame import MovieFrame, NULL_MOVIE_FRAME_INFO
from psychopy.sound.microphone import Microphone
from ffpyplayer.player import MediaPlayer
from ffpyplayer.writer import MediaWriter
from ffpyplayer.pic import SWScale
from ffpyplayer.tools import list_dshow_devices, get_format_codec
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
import uuid
import threading
import queue
import time


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


# ------------------------------------------------------------------------------
# Exceptions
#

class CameraError(Exception):
    """Base class for errors around the camera."""


class CameraNotReadyError(CameraError):
    """Camera is not ready."""


class CameraNotFoundError(CameraError):
    """Raised when a camera cannot be found on the system."""


class CameraModeNotSupportedError(CameraError):
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
        (i.e. DirectShow on Windows) or a path (e.g., `/dev/video0` on Linux).
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
        '_name',
        '_frameSize',
        '_frameRate',
        '_pixelFormat',
        '_codecFormat',
        '_cameraLib',
        '_cameraAPI'  # API in use, e.g. DirectShow on Windows
    ]

    def __init__(self,
                 name=CAMERA_NULL_VALUE,
                 frameSize=(-1, -1),
                 frameRate=(-1, -1),
                 pixelFormat=CAMERA_UNKNOWN_VALUE,
                 codecFormat=CAMERA_UNKNOWN_VALUE,
                 cameraLib=CAMERA_NULL_VALUE,
                 cameraAPI=CAMERA_NULL_VALUE):

        self.name = name
        self.frameSize = frameSize
        self.frameRate = frameRate
        self.pixelFormat = pixelFormat
        self.codecFormat = codecFormat
        self._cameraLib = cameraLib
        self._cameraAPI = cameraAPI

    def __repr__(self):
        return (f"CameraInfo(name={repr(self.name)}, "
                f"frameSize={repr(self.frameSize)}, "
                f"frameRate={self.frameRate}, "
                f"pixelFormat={repr(self.pixelFormat)}, "
                f"codecFormat={repr(self.codecFormat)}, "
                f"cameraLib={repr(self._cameraLib)}, "
                f"cameraAPI={repr(self._cameraAPI)})")

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
    """Descriptor for video frame data.

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
        self._frameQueue = queue.Queue(maxsize=bufferFrames)  # frames for the monitor

        # some values the user might want
        self._status = NOT_STARTED
        self._recordingTime = 0.0
        self._recordingBytes = 0
        self._streamTime = 0.0

        self._isReadyEvent = threading.Event()
        self._isRecording = threading.Event()
        self._isStreamingEvent = threading.Event()
        self._stopSignal = threading.Event()

    def run(self):
        """Main sub-routine for this thread.

        When the thread is running, data about captured frames are put into the
        `frameQueue` as `(metadata, img, pts)`. If the queue is empty, that
        means the main application thread is running faster than the encoder
        can get frames.

        """
        if self._player is None:
            return  # exit thread if no player

        self._isStreamingEvent.set()
        self._isReadyEvent.clear()
        frameInterval = 0.001  # dynamic poll interval, start at 1ms
        ptsStart = 0.0
        recordingJustStarted = True
        streaming = True
        while streaming:
            # consume frames until we get a valid one
            frameData = None
            val = ''
            while frameData is None or val == 'not ready':
                frameData, val = self._player.get_frame()
                time.sleep(frameInterval)  # sleep a bit to warm-up
            else:
                self._isReadyEvent.set()

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
            if self._isRecording.is_set():
                if recordingJustStarted:
                    ptsStart = self._streamTime
                    self._status = RECORDING

                    # start the microphone
                    if self._mic is not None:
                        self._mic.record()

                    recordingJustStarted = False

                # compute timestamp for the writer for the current frame
                self._recordingTime = self._streamTime - ptsStart

                if self._writer is not None:
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
                    # start the microphone
                    if self._mic is not None:
                        self._mic.stop()

                    # reset stream recording vars when done
                    ptsStart = 0.0
                    self._recordingBytes = 0
                    self._recordingTime = 0.0
                    self._status = STOPPED
                    recordingJustStarted = True

            # Put the frame in the queue to allow the main thread to safely
            # access it. If the queue is full, the frame data will be discarded
            # at this point. The image will be lost unless the encoder is
            # recording.
            if not self._frameQueue.full():
                streamStatus = StreamStatus(
                    status=self._status,
                    streamTime=self._streamTime,
                    recTime=self._recordingTime,
                    recBytes=self._recordingBytes)

                # Object to pass video frame data back to the application thread
                # for presentation or processing.
                img, _ = frameData
                toReturn = StreamData(metadata, img, streamStatus, u'ffpyplayer')
                self._frameQueue.put(toReturn)  # put frame data in here

            # signal to close a thread
            if self._stopSignal.is_set() or val == 'eof':
                streaming = False

        # out of this loop, we're done
        self._isReadyEvent.clear()
        self._isStreamingEvent.clear()

    @property
    def isReady(self):
        """`True` if the stream reader is ready (`bool`).
        """
        return self._isReadyEvent.is_set()

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

        self._isRecording.set()

    def stop(self):
        """Stop recording frames to the output file.
        """
        self._isRecording.clear()
        self._writer = None
        self._mic = None

    def shutdown(self):
        """Stop the thread.
        """
        self._stopSignal.set()

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
    """Class of displaying and recording video from a USB/PCI connected camera
    (usually a camera).

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
        on GNU/Linux (e.g., `'/dev/video0'`), and a camera name on MacOS.
        Specifying a number (>=0) is a platform-independent means of selecting a
        camera. PsychoPy enumerates possible camera devices and makes them
        selectable without explicitly having the name of the cameras attached to
        the system. Use caution when specifying an integer, as the same index
        may not reference the same camera everytime.
    mic : :class:`~psychopy.sound.microphone.Microphone` or None
        Microphone to record audio samples from during recording. The microphone
        input device must not be in use when `record()` is called. The audio
        track will be merged with the video upon calling `save()`.
    size : ArrayLike
        Requested resolution `(w, h)` of the camera video.
    frameRate : int
        Requested framerate for the camera video.
    cameraLib : str
        Interface library (backend) to use for accessing the camera. Only
        `ffpyplayer` is available at this time.
    codecOpts : dict or None
        Options to pass to the codec. See the documentation for the camera
        library for details. Some options may be set by this class.
    libOpts : dict or None
        Additional options to configure the camera interface library (if
        applicable).
    bufferSecs : float
        Size of the camera stream buffer specified in seconds (only valid on
        Windows).
    win : :class:`~psychopy.visual.Window` or None
        Optional window associated with this camera. Some functionality may
        require an OpenGL context.
    name : str
        Label for the camera for logging purposes.

    Examples
    --------
    Opening a camera stream and closing it::

        camera = Webcam(camera='/dev/video0')
        camera.open()  # exception here on invalid camera
        # camera.status == NOT_STARTED
        camera.start()
        # camera.status == PLAYING
        camera.stop()
        # camera.status == STOPPED
        camera.close()

    """
    def __init__(self, device=0, mic=None, size=(320, 240), frameRate=30,
                 cameraLib=u'ffpyplayer', codecOpts=None, libOpts=None,
                 bufferSecs=4, win=None, name='cam'):

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

        # alias device None or Default as being device 0
        if device in (None, "None", "none", "Default", "default"):
            device = 0
        # resolve getting the camera identifier
        if isinstance(device, int):  # get camera if integer
            try:
                self.device = getCameras()[device]
            except IndexError:  # catch as
                raise CameraNotFoundError(
                    'Could not enumerate camera with index `{}`.'.format(
                        device))
        elif isinstance(device, str):  # get camera if integer
            self.device = device
        else:
            raise TypeError(
                "Incorrect type for `camera`, expected `int` or `str`.")

        # get the frame rate, needs to be fractional and float to config
        if isinstance(frameRate, (int, float)):  # atomic
            self._frameRate = int(frameRate)
            self._frameRateFrac = (self._frameRate, 1)
        elif isinstance(frameRate, (tuple, list, np.ndarray)):  # sequence
            if len(frameRate) != 2:
                raise ValueError(
                    "Value for parameter `size` must be length 2 if a sequence."
                )
            self._frameRateFrac = numer, denom = [int(i) for i in frameRate]
            self._frameRate = numer / denom

        assert len(size) == 2, "Value for parameter `size` must be length 2"
        self._size = tuple(size)  # needs to be hashable

        # get camera mode information, see if the values specified by the user
        # match something that is supported
        devModes = getCameraInfo(self._device)
        for devMode in devModes:
            sameFrameRate = np.array(devMode.frameRate) == np.array(self._frameRateFrac)
            sameFrameSize = np.array(devMode.frameSize) == np.array(self._size)
            if sameFrameRate.all() and sameFrameSize.all():
                break
        else:
            raise CameraModeNotSupportedError(
                "Camera '{}' does not support the specified framerate and "
                "frame size. Call `getCameraInfo() to query the system for "
                "valid configurations for the desired capture device.".format(
                    self._device
                )
            )

        # name for builder
        self.name = name

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

        # current camera frame since the start of recording
        self._player = None  # media player instance
        self._status = NOT_STARTED
        self._frameIndex = -1
        self._isRecording = False
        self._isReady = False
        self._bufferSecs = float(bufferSecs)

        # timestamp data
        self._recordingTime = 0.0
        self._recordingBytes = 0
        self._streamTime = 0.0

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
    def getWebcams():
        """Get information about installed cameras on this system.

        Returns
        -------
        list
            Camera identifiers.

        """
        return getCameras()

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
            # 'pix_fmt_in': 'rgb24',
            'width_in': frameWidth,
            'height_in': frameHeight,
            'codec': useCodec,
            'frame_rate': frameRate
        }

        # initialize the writer to transcode the video stream to file
        self._writer = MediaWriter(self._tempVideoFileName, [writerOptions])

    def _closeWriter(self):
        """Close the video writer.
        """
        if self._writer is None:
            return

        # cleanup
        self._writer.close()
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

    def _enqueueFrame(self, blockUntilFrame=True):
        """Grab the latest frame from the stream.

        Parameters
        ----------
        blockUntilFrame : bool
            Block until the decoder thread returns a valid frame. This can be
            used to hold the application thread until frames are available.

        Returns
        -------
        bool
            `True` if a frame has been enqueued. Returns `False` if the camera
            is not ready or if the stream was closed.

        """
        self._assertMediaPlayer()

        # If the queue is empty, the decoder thread has not yielded a new frame
        # since the last call.
        enqueuedFrame = None
        if blockUntilFrame:
            while enqueuedFrame is None:
                enqueuedFrame = self._tStream.getRecentFrame()
                time.sleep(0.001)  # sleep a bit
        else:
            enqueuedFrame = self._tStream.getRecentFrame()

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
        if platform.system() == 'Windows':  # DirectShow specific stuff
            ff_opts['f'] = 'dshow'

            # get device configuration options
            camW, camH = self._size
            pixelFormat = 'yuyv422'

            # library options
            framerate = str(self._frameRate)
            videoSize = '{width}x{height}'.format(width=camW, height=camH)
            bufferSize = camW * camH * 3 * self._bufferSecs

            # build dict for library options
            lib_opts.update({
                'framerate': framerate,
                'video_size': videoSize,
                'pixel_format': pixelFormat,  # e.g. 'yuyv422'
                'rtbufsize': str(bufferSize)}
            )
            _camera = 'video={}'.format(self._device)
        else:
            _camera = self._device

        # open a stream and pause it until ready
        self._player = MediaPlayer(_camera, ff_opts=ff_opts, lib_opts=lib_opts)

        # pass off the player to the thread which will process the stream
        self._tStream = MovieStreamIOThread(self._player)
        self._tStream.start()

        self._enqueueFrame(blockUntilFrame=True)  # pull a frame, gets metadata too

    def record(self):
        """Start recording frames.
        """
        self._assertMediaPlayer()

        while not self._enqueueFrame():
            time.sleep(0.001)

        self._openWriter()

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

        self._player.close_player()
        self._player = None  # reset

        # close the file writer
        if self._writer is not None:
            self._writer.close()

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

    # def update(self):
    #     """Acquire the newest data from the camera stream. If the `Camera`
    #     object is not being monitored by a `ImageStim`, this must be explicitly
    #     called.
    #     """
    #     self._assertMediaPlayer()

    def getVideoFrame(self):
        """Pull the next frame from the stream (if available).

        Returns
        -------
        MovieFrame
            Most recent video frame. Returns `NULL_MOVIE_FRAME_INFO` if no
            frame was available, or we timed out.

        """
        self._assertMediaPlayer()

        self._enqueueFrame()

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


# ------------------------------------------------------------------------------
# Functions
#

def getCameraInfo(camera):
    """Query the system to get information about a specified camera.

    Parameters
    ----------
    camera : int or str
        Camera index or name.

    Returns
    -------
    List or CameraInfo
        Camera information descriptors for the specified camera.

    """
    systemName = platform.system()  # get the system name
    supportedModes = []
    if systemName == 'Windows':
        videoDevs, _, names = list_dshow_devices()
        names = {v: k for k, v in names.items()}  # flip since we use HR names
        if isinstance(camera, (int, float)):
            name = list(names.keys())[int(camera)]
        else:
            name = camera

        # get all the supported modes for the camera
        videoDevModes = videoDevs[names[name]]

        for mode in videoDevModes:
            pixelFormat, codec, frameSize, frameRate = mode

            # Make sure the frame rate is in a reasonable format, usually the
            # ranges are not reported, so we just convert them into fractions
            # here.
            frameRateMin, frameRateMax = frameRate
            if frameRateMin == frameRateMax:
                frameRate = (frameRateMax, 1)
            else:
                continue  # do nothing if they don't match for now

            # object to return with camera settings
            temp = CameraInfo(
                name=name,
                pixelFormat=pixelFormat,
                codecFormat=codec,
                frameSize=frameSize,
                frameRate=frameRate
            )
            supportedModes.append(temp)
    else:
        raise OSError(
            "Cannot get cameras, unsupported platform '{}'.".format(
                systemName))

    return supportedModes


def getCameras():
    """Get information about installed cameras on this system.

    Returns
    -------
    list
        Camera identifiers.

    """
    systemName = platform.system()  # get the system name
    foundCameras = []
    if systemName == 'Darwin':  # MacOS
        import psychopy.tools.systemtools as st
        import json
        # query camera names using `system_profiler`
        systemReportJSON = st.systemProfilerMacOS(
            "SPCameraDataType",
            detailLevel='mini')
        sysReport = json.loads(systemReportJSON)
        # get camera names and return them
        cameras = sysReport.get('SPCameraDataType', None)
        if cameras is not None:  # no cameras
            for camera in cameras:
                camera = camera.get('_name', None)
                if camera is None:
                    continue
                foundCameras.append(camera)
    elif systemName == 'Linux':
        # use glob to get possible cameras connected to the system
        globResult = glob.glob(
            'video*',
            root_dir=VIDEO_DEVICE_ROOT_LINUX,
            recursive=False)
        foundCameras.extend(globResult)
        # ensure the glob gives values in the same order
        foundCameras.sort()
    elif systemName == 'Windows':
        videoDevs, _, names = list_dshow_devices()
        for devKey in videoDevs.keys():
            nameHR = names.get(devKey, None)
            ident = devKey if nameHR is None else nameHR
            foundCameras.append(ident)
    else:
        raise OSError(
            "Cannot get cameras, unsupported platform '{}'.".format(
                systemName))

    return foundCameras


if __name__ == "__main__":
    pass
