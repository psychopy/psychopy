#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for reading and writing camera streams.

A camera may be used to document participant responses on video or used by the
experimenter to create movie stimuli or instructions.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['CameraNotFoundError', 'Camera', 'CameraInfo', 'getCameras']

import glob
import platform
import numpy as np
import tempfile
import os
from psychopy.constants import STOPPED, STOPPING, NOT_STARTED, RECORDING
from psychopy.visual.movies.metadata import MovieMetadata, NULL_MOVIE_METADATA
from psychopy.visual.movies.frame import MovieFrame, NULL_MOVIE_FRAME_INFO
from psychopy.sound.microphone import Microphone
from ffpyplayer.player import MediaPlayer
from ffpyplayer.writer import MediaWriter
from ffpyplayer.pic import SWScale
from ffpyplayer.tools import list_dshow_devices
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
import uuid
import threading
import queue
import time
from psychopy.preferences import prefs


# ------------------------------------------------------------------------------
# Constants
#

VIDEO_DEVICE_ROOT_LINUX = '/dev'
WEBCAM_UNKNOWN_VALUE = u'Unknown'  # fields where we couldn't get a value
WEBCAM_NULL_VALUE = u'Null'  # fields where we couldn't get a value

# camera operating modes
WEBCAM_MODE_VIDEO = u'video'
WEBCAM_MODE_CV = u'cv'
WEBCAM_MODE_PHOTO = u'photo'


# ------------------------------------------------------------------------------
# Exceptions
#

class CameraError(Exception):
    """Base class for errors around the camera."""


class CameraNotReadyError(CameraError):
    """Camera is not ready."""


class CameraNotFoundError(CameraError):
    """Raised when a camera cannot be found on the system."""


class PlayerNotAvailableError(Exception):
    """Raised when a player object is not available but is required."""


# ------------------------------------------------------------------------------
# Descriptors
#

class CameraInfo:
    """Descriptor for cameras connected to the system (such as webcams).

    Parameters
    ----------
    name : str
        Camera name retrieved by the OS. This may be a human-readable name
        (i.e. DirectShow on Windows) or a path (e.g., `/dev/video0` on Linux).
    frameSize : ArrayLike
        Resolution of the frame `(w, h)` in pixels.
    frameRateRange : ArrayLike
        Minimum and maximum frame rate supported by the camera at the specified
        color/pixel format and resolution.
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
        '_frameRateRange',
        '_pixelFormat',
        '_codecFormat',
        '_cameraLib',
        '_cameraAPI'  # API in use, e.g. DirectShow on Windows
    ]

    def __init__(self,
                 name=WEBCAM_NULL_VALUE,
                 frameSize=(-1, -1),
                 frameRateRange=(-1, -1),
                 pixelFormat=WEBCAM_UNKNOWN_VALUE,
                 codecFormat=WEBCAM_UNKNOWN_VALUE,
                 cameraLib=WEBCAM_NULL_VALUE,
                 cameraAPI=WEBCAM_NULL_VALUE):

        self.name = name
        self.frameSize = frameSize
        self.frameRateRange = frameRateRange
        self.pixelFormat = pixelFormat
        self.codecFormat = codecFormat
        self._cameraLib = cameraLib
        self._cameraAPI = cameraAPI

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
    def frameRateRange(self):
        """Resolution (min, max) in pixels (`ArrayLike`).
        """
        return self._frameRateRange

    @frameRateRange.setter
    def frameRateRange(self, value):
        assert len(value) == 2, "Value for `frameRateRange` must have length 2."
        assert all([isinstance(i, int) for i in value]), (
            "Values for `frameRateRange` must be integers.")
        assert value[0] <= value[1], (
            "Value for `frameRateRange` must be `min` <= `max`.")

        self._frameRateRange = value

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

    def supportedFrameRate(self, frameRate):
        """Check if the specified frame rate is supported by the camera
        configuration.

        Parameter
        ---------
        frameRate : int or float
            Framerate in Hertz (Hz).

        Returns
        -------
        bool
            `True` if the specified framerate is supported by the camera.

        """
        frameRateMin, frameRateMax = self._frameRateRange

        return frameRateMin <= frameRate <= frameRateMax


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
    def recTime(self):
        """Current recording size on disk (`float`).

        If recording, this value indicates the number of bytes that have been
        written out to file.
        """
        return self._recTime

    @property
    def recBytes(self):
        """Current recording time (`float`).

        If recording, this field will report the current timestamp within the
        output file. Otherwise, this value is zero.
        """
        return self._recBytes


# ------------------------------------------------------------------------------
# Classes
#


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
    writer : `ffpyplayer.player.MediaWriter` or `None`
        Media writer instance, should be configured and initialized.

    """
    def __init__(self, player, writer=None):
        threading.Thread.__init__(self)
        self.daemon = False

        self._player = player  # player interface to FFMPEG
        self._writer = writer  # writer interface
        self._frameQueue = queue.Queue(maxsize=1)  # frames for the monitor

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

            # after getting a frame, we can get accurate metadata
            metadata = self._player.get_metadata()

            # compute frame interval for dynamic polling rate
            frameRate = metadata['frame_rate']
            numer, denom = frameRate

            if denom == 0:  # no valid framerate from metadata yet
                continue

            frameInterval = 1.0 / (numer / float(denom))

            # put the frame in the queue
            if not self._frameQueue.full():
                toReturn = (metadata, frameData, val)
                self._frameQueue.put(toReturn)  # put frame data in here

            # handle writing to file
            if self._isRecording.is_set():
                colorData, pts = frameData
                if recordingJustStarted:
                    ptsStart = pts
                    self._status = RECORDING
                    recordingJustStarted = False

                # compute timestamp for the writer for the current frame
                self._streamTime = pts
                self._recordingTime = pts - ptsStart

                if self._writer is not None:
                    frameWidth, frameHeight = colorData.get_size()
                    pixelFormat = colorData.get_pixel_format()
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
            else:
                ptsStart = 0.0
                recordingJustStarted = True
                self._status = STOPPED

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

    def record(self):
        """Start recording frames to the output video file.
        """
        self._isRecording.set()

    def stop(self):
        """Stop recording frames to the output file.
        """
        self._isRecording.clear()

    def shutdown(self):
        """Stop the thread.
        """
        self._stopSignal.set()

    def getStatus(self):
        """Current recording time in seconds (`float`).
        """
        # thread-safe since value is immutable type and not settable
        return StreamStatus(
            NOT_STARTED,
            self._streamTime,
            self._recordingTime,
            self._recordingBytes)

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

    This class is capable of opening and recording camera video streams.

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
    mode : str
        Camera operating mode to use. Value can be either `'video'`, `'cv'` or
        `'photo'`. Use `'video'` for recording live-feeds to produce movies,
        `'cv'` for computer vision applications (same as `'video'` but frames
        are not buffered on disk, reduces CPU load), and `'photo'` for taking
        snapshots with the camera. Default operating mode is `'video'`, cannot
        be set after initialization.
    cameraLib : str
        Interface library (backend) to use for accessing the camera. Only
        `ffpyplayer` is available at this time.
    codecOpts : dict or None
        Options to pass to the codec. See the documentation for the camera
        library for details. Some options may be set by this class.
    libOpts : dict or None
        Additional options to configure the camera interface library (if
        applicable).

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
    def __init__(self, device=0, mic=None, mode='video',
                 cameraLib=u'ffpyplayer', codecOpts=None, libOpts=None, win=None):

        # add attributes for setters
        self.__dict__.update(
            {'_device': None,
             '_mic': None,
             '_outFile': None,
             '_mode': u'video',
             '_cameraLib': u'',
             '_codecOpts': None,
             '_libOpts': None})

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

        # camera library in use
        self._cameraLib = cameraLib

        # operating mode
        if mode not in (WEBCAM_MODE_VIDEO, WEBCAM_MODE_CV, WEBCAM_MODE_PHOTO):
            raise ValueError(
                "Invalid value for parameter `mode`, expected one of `'video'` "
                "`'cv'` or `'photo'`.")
        self._mode = mode

        # FFMPEG and FFPyPlayer options
        self._codecOpts = codecOpts if codecOpts is not None else {}
        self._libOpts = libOpts if libOpts is not None else {}

        # parameters for the writer
        self._writer = None
        self._tempVideoFileName = u''
        self._tempAudioFileName = u''
        self._tempRootDir = u'.'

        if not isinstance(mic, Microphone):
            TypeError("Expected type `Microphone` for parameter `mic`.")
        self.mic = mic

        # current camera frame since the start of recording
        self._player = None  # media player instance
        self._status = NOT_STARTED
        self._frameIndex = -1
        self._isRecording = False
        self._isReady = False

        # timestamp data
        self._startPts = -1.0  # absolute stream time at recording
        self._absPts = -1.0  # timestamp of the video stream in absolute time
        self._pts = -1.0  # timestamp used for writing the video stream
        self._lastPts = 0.0  # last timestamp
        self._recordingTime = 0.0
        self._recordingBytes = 0
        self._streamTime = 0.0
        self._isMonotonic = False
        self._outFile = ''

        # store win (unused but needs to be set/got safely for parity with JS)
        self.win = win

        # thread for reading a writing streams
        self._tStream = None

        # video metadata
        self._recentMetadata = NULL_MOVIE_METADATA

        # last frame
        self._lastFrame = NULL_MOVIE_FRAME_INFO

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

    @property
    def mode(self):
        """Operating mode in use for this camera.
        """
        return self._mode

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
        `_enqueueFrame` called at least once prior.
        """
        if self._writer is not None:
            raise RuntimeError(
                "Stream writer instance has already been created.")

        self._assertMediaPlayer()

        # configure the temp directory and files for the recordings
        randFileName = str(uuid.uuid4().hex)
        self._tempRootDir = tempfile.mkdtemp(
            suffix=randFileName,
            prefix='psychopy-',
            dir=None)
        self._tempVideoFileName = os.path.join(self._tempRootDir, 'video.avi')
        self._tempAudioFileName = os.path.join(self._tempRootDir, 'audio.wav')

        frameWidth, frameHeight = 320, 240
        frameRate = (32, 1)

        writerOptions = {
            'pix_fmt_in': 'yuv420p',  # default for now
            'width_in': frameWidth,
            'height_in': frameHeight,
            'frame_rate': frameRate
        }

        # initialize the writer to transcode the video stream to file
        self._writer = MediaWriter(self._tempVideoFileName, [writerOptions])

        # initialize audio recording if available
        if self._mic is not None:
            self._mic.start()

        # recording timestamp
        self._pts = -1.0

    def _closeWriter(self):
        """Close the video writer.
        """
        if self._writer is None:
            return

        # cleanup
        self._writer.close()
        self._writer = None

    def _renderVideo(self):
        """Combine video and audio tracks of temporary video and audio files.
        Outputs a new file at `outFile` with merged video and audio tracks.
        """
        # do nothing if there is no output file
        if self._outFile is None:
            return False

        # this can only happen when stopped
        if self._status != STOPPED:
            raise RuntimeError(
                "Cannot render video, `stop` has not been called yet.")

        # merge audio and video tracks, we use MoviePy for this
        videoClip = VideoFileClip(self._tempVideoFileName)

        if self._mic is not None:
            audioClip = AudioFileClip(self._tempAudioFileName)
            # add audio track to the video
            videoClip.audio = CompositeAudioClip([audioClip])

        # transcode with the format the user wants
        videoClip.write_videofile(self._outFile)

        return True

    @property
    def status(self):
        """Status flag for the camera (`int`).

        Can be either `RECORDING`, `STOPPED`, `STOPPING`, or `NOT_STARTED`.

        """
        return self._status

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

    def _writeFrame(self, colorData, timestamp):
        """Write the presently enqueued frame to the output file.

        Parameters
        ----------
        colorData : object
            Image frame to write.
        timestamp : float
            Timestamp of the frame in seconds.

        """
        if not self._hasWriter:  # NOP if no writer
            return

        if self._status != RECORDING:  # nop if not recording
            return

        isMonotonic = self._lastPts > timestamp

        if not isMonotonic:
            return

        self._lastPts = timestamp

        # convert the image to the appropriate format for the encoder
        frameWidth, frameHeight = colorData.get_size()
        pixelFormat = colorData.get_pixel_format()
        sws = SWScale(frameWidth, frameHeight, pixelFormat, ofmt='yuv420p')

        # write the frame to the file
        self._writer.write_frame(
            img=sws.scale(colorData),
            pts=timestamp,
            stream=0)

    def _enqueueFrame(self):
        """Grab the latest frame from the stream.

        Parameters
        ----------
        timeout : float
            Amount of time to wait for a frame in seconds. If -1.0, this method
            will return immediately. If a frame could not be pulled from the
            stream in the allotted time a warning will be logged.

        Returns
        -------
        bool
            `True` if a frame has been enqueued. Returns `False` if the camera
            is not ready or if the stream was closed.

        """
        self._assertMediaPlayer()

        # If the queue is empty, the decoder thread has not yielded a new frame
        # since the last call.
        streamStatus = self._tStream.getStatus()
        enqueuedFrame = self._tStream.getRecentFrame()
        if enqueuedFrame is None:
            return False

        # unpack the data we got back
        metadata, frameData, val = enqueuedFrame
        colorData, pts = frameData

        # if we have a new frame, update the frame information
        videoBuffer = colorData.to_bytearray()[0]
        videoFrameArray = np.frombuffer(videoBuffer, dtype=np.uint8)

        # provide the last frame
        self._lastFrame = MovieFrame(
            frameIndex=self._frameIndex,
            absTime=pts,
            # displayTime=self._recentMetadata['frame_size'],
            size=colorData.get_size(),
            colorData=videoFrameArray,
            audioChannels=0,
            audioSamples=None,
            movieLib=u'ffpyplayer',
            userData=None)

        # status information
        self._streamTime = streamStatus.streamTime  # stream time for the camera
        self._recordingTime = streamStatus.recTime
        self._recordingBytes = streamStatus.recBytes

        # if status == 'eof':  # end of stream but there is a valid frame
        #     self._status = STOPPING  # last frame, stopping ...

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

            # library options
            framerate = str(30)
            videoSize = '{width}x{height}'.format(width=320, height=240)
            bufferSize = 320 * 240 * 3 * 10

            # build dict for library options
            lib_opts.update({
                'framerate': framerate,
                'video_size': videoSize,
                'pixel_format': 'yuyv422',
                'rtbufsize': str(bufferSize)}
            )
            _camera = 'video={}'.format(self._device)
        else:
            _camera = self._device

        # open a stream and pause it until ready
        self._player = MediaPlayer(_camera, ff_opts=ff_opts, lib_opts=lib_opts)
        self._openWriter()

        # pass off the player to the thread which will process the stream
        self._tStream = MovieStreamIOThread(self._player, self._writer)
        self._tStream.start()

        self._enqueueFrame()  # pull a frame, gets metadata too

    def record(self):
        """Start recording frames.
        """
        self._assertMediaPlayer()

        self._lastFrame = NULL_MOVIE_FRAME_INFO
        # self._openWriter()
        self._tStream.record()

        self._status = RECORDING

        # start audio recording if possible
        if self._mic is not None:
            self._mic.record()

    def snapshot(self):
        """Take a photo with the camera. The camera must be in `'photo'` mode
        to use this method.
        """
        pass

    def stop(self):
        """Stop recording frames.
        """
        self._assertMediaPlayer()

        self._status = STOPPED
        self._tStream.shutdown()  # close the stream
        self._tStream.join()  # wait until thread exits

        self._closeWriter()

        # initialize audio recording if available
        if self._mic is not None:
            self._mic.stop()

        if self._writer is not None:
            self._writer.close()

    def close(self):
        """Close the camera.
        """
        if not self._hasPlayer:
            raise RuntimeError("Cannot close stream, not opened yet.")

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
            Size of the output file at `filename` in bytes.

        """
        if self._status != STOPPED:
            raise RuntimeError(
                "Attempted to call `save()` a file before calling `stop()`.")

        # render the video
        if not self._renderVideo():
            raise RuntimeError(
                "Failed to write file `filename`, check if the output path is "
                "writeable.")

        # make sure that `filename` is valid
        self._outFile = filename

        return os.path.getsize(self._outFile)

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
        return self._outFile  # change this to the actual value eventually

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


# ------------------------------------------------------------------------------
# Functions
#

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
        pass
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
