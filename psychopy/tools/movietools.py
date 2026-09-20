#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for working with movies in PsychoPy.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'MovieWriter',
    'InvalidFrameSizeError',
    'closeAllMovieWriters',
    'addAudioToMovie',
    'MOVIE_WRITER_LIB_FFPYPLAYER',
    'MOVIE_WRITER_LIB_PYAV',
    'MOVIE_WRITER_LIB_OPENCV',
    'MOVIE_WRITER_LIB_NULL'
]

import os
import sys
import threading
import queue
import atexit
import numpy as np
import psychopy.logging as logging


MOVIE_WRITER_LIB_FFPYPLAYER = 'ffpyplayer'
MOVIE_WRITER_LIB_PYAV = 'pyav'
MOVIE_WRITER_LIB_OPENCV = 'opencv'
MOVIE_WRITER_LIB_NULL = 'null'

# default movie writer to use
PREFERED_MOVIE_WRITER_LIB = MOVIE_WRITER_LIB_PYAV


_openMovieWriters = set()  # keep track of all open movie writers
_ffmpegExe = None  # cached path to the FFMPEG executable


# ------------------------------------------------------------------------------
# Movie file writers
#

def _rgbFrameAsArray(colorData):
    """Get a frame which is already in RGB as a Numpy array.

    Each capture library hands its frames over in its own wrapper, so this
    takes whichever one a `Camera` produced and gives back the plain array the
    encoders want. Frames must already be in RGB; use the writer's
    `frameConverter` to get them there.

    Parameters
    ----------
    colorData : numpy.ndarray or object
        Frame in RGB. This may be an array already, an `_RGBFrameAdapter` or
        `av.VideoFrame` (anything with `to_ndarray()`), or an
        `ffpyplayer.pic.Image`.

    Returns
    -------
    numpy.ndarray
        Frame as an 8-bit, three channel array of shape `(height, width, 3)`
        with channels in RGB order. This may share memory with the frame it
        came from, so treat it as belonging to that frame rather than writing
        to it.

    Raises
    ------
    TypeError
        If the frame is not of a type image data can be got out of.

    """
    if isinstance(colorData, np.ndarray):
        return colorData

    if hasattr(colorData, 'to_ndarray'):  # `_RGBFrameAdapter`, PyAV frame
        return colorData.to_ndarray(format='rgb24')

    if hasattr(colorData, 'to_memoryview'):  # FFPyPlayer image
        # `to_memoryview()` hands plane data over packed, without any row
        # padding, so the plane can be reshaped by frame size alone
        frameWidth, frameHeight = colorData.get_size()

        return np.frombuffer(
            colorData.to_memoryview()[0].memview, dtype=np.uint8).reshape(
                (frameHeight, frameWidth, 3))

    raise TypeError(
        "Cannot get image data out of a frame of type `{}`.".format(
            type(colorData).__name__))


class InvalidFrameSizeError(ValueError):
    """Raised when a writer is given a frame size it cannot write.

    Bases `ValueError`, since the size is an argument the caller got wrong.

    """
    pass


class MovieWriter:
    """Base class for writers which encode frames into a movie file.

    Frames may come from anywhere which can produce them at a fixed size, a
    camera or a window buffer for instance.

    A writer is created with everything it needs to lay out the file, opened,
    handed frames as they are captured, and closed once the recording is done.
    Subclasses fill in the three hooks `_open()`, `_writeFrame()` and
    `_close()`; everything callers touch is defined here, so a caller never
    needs to know which library is doing the encoding.

    Frames are placed in the file by how far into the recording they were
    captured rather than counted off at the nominal frame rate, since cameras
    routinely deliver below the rate they advertise (auto-exposure alone can
    halve it). Counting frames would make such a recording play back too fast
    and drift against the audio track it is later merged with. How that
    placement is done depends on what the encoder can express, so it is left to
    the subclasses.

    Parameters
    ----------
    filename : str
        File to write the video to, should include the extension.
    frameSize : ArrayLike
        Size `(w, h)` of the frames to be written, in pixels, both greater than
        zero. The container's frame size is fixed when the file is opened, so
        this cannot change while the writer is open.
    frameRate : float
        Nominal rate in frames per second the file is written at. If the source
        could not report one, `30.0` is used and a warning is logged.
    encoderOpts : dict or None
        Options to pass to the encoder. Which options are understood depends on
        the encoder library, see the subclass for details.
    frameConverter : callable or None
        Callable taking a frame as the capture library hands it over and
        returning it in RGB. A writer only calls this for frames it cannot
        encode as they come, which is any frame from a capture library other
        than its own, so it may be left out when the two libraries match.

    Raises
    ------
    InvalidFrameSizeError
        If `frameSize` is not a pair of positive numbers. A source which is not
        ready to be recorded yet reports no frame size at all, `None`, which a
        camera does until its stream is open.

    """
    # Encoder library this writer encodes with, one of the `CAMERA_LIB_*`
    # values. Set by each subclass.
    _encoderLib = MOVIE_WRITER_LIB_NULL

    def __init__(self, filename, frameSize, frameRate, encoderOpts=None,
                 frameConverter=None):
        if frameSize is None:
            raise InvalidFrameSizeError(
                "A movie file writer needs the size of the frames it will be "
                "given, since the container's frame size is fixed when the "
                "file is opened. A source which is not ready to be recorded "
                "reports no size, a camera before its stream is open for "
                "instance.")

        # both ways a size can be malformed are the same mistake, so they are
        # reported the same way
        malformed = (
            "Expected `frameSize` to be a sequence of two numbers `(w, h)` in "
            "pixels, got {}.".format(repr(frameSize)))

        if isinstance(frameSize, str):
            raise InvalidFrameSizeError(malformed)

        try:
            # unpacking rather than indexing, so that a sequence of the wrong
            # length is rejected rather than silently cut down to its first two
            frameWidth, frameHeight = (int(dim) for dim in frameSize)
        except (TypeError, ValueError):
            raise InvalidFrameSizeError(malformed)

        if frameWidth < 1 or frameHeight < 1:
            raise InvalidFrameSizeError(
                "Frames must be at least one pixel in each direction, got "
                "`frameSize={}`.".format(repr(frameSize)))

        self._filename = filename
        self._frameSize = (frameWidth, frameHeight)

        if not frameRate or frameRate <= 0:
            frameRate = 30.0
            logging.warning(
                "Camera did not report a frame rate, writing the video at {} "
                "fps.".format(frameRate))

        self._frameRate = float(frameRate)
        self._encoderOpts = dict(encoderOpts) if encoderOpts else {}
        self._frameConverter = frameConverter

        self._isOpen = False
        self._framesWritten = 0  # frames handed to the encoder
        self._bytesWritten = 0  # bytes the encoder reported writing
        self._lastPTS = 0.0  # where in the recording the last frame was placed

    def __repr__(self):
        return "{}(filename={}, frameSize={}, frameRate={})".format(
            type(self).__name__, repr(self._filename), repr(self._frameSize),
            repr(self._frameRate))

    @property
    def encoderLib(self):
        """Library this writer encodes with (`str`).

        One of `'ffpyplayer'`, `'pyav'` or `'opencv'`.

        """
        return self._encoderLib

    @property
    def filename(self):
        """File the video is being written to (`str`).
        """
        return self._filename

    @property
    def frameSize(self):
        """Size `(w, h)` in pixels of the frames in the file (`tuple`).
        """
        return self._frameSize

    @property
    def frameRate(self):
        """Nominal rate in frames per second the file is written at (`float`).
        """
        return self._frameRate

    @property
    def encoderOpts(self):
        """Options the encoder was opened with (`dict`).
        """
        return self._encoderOpts

    @property
    def isOpen(self):
        """`True` while the file is open for writing (`bool`).
        """
        return self._isOpen

    @property
    def framesWritten(self):
        """Number of frames handed to the encoder so far (`int`).
        """
        return self._framesWritten

    @property
    def bytesWritten(self):
        """Number of bytes written to the file so far (`int`).

        Not every encoder reports this, so this may stay at zero even while
        frames are reaching the file.

        """
        return self._bytesWritten

    @property
    def lastPTS(self):
        """How far into the recording the last frame written sat, in seconds
        (`float`).
        """
        return self._lastPTS

    def open(self):
        """Open the file and get the encoder ready to take frames.

        Calling this on a writer which is already open does nothing.

        """
        if self._isOpen:
            return

        self._framesWritten = 0
        self._bytesWritten = 0
        self._lastPTS = 0.0

        self._open()

        self._isOpen = True

    def write(self, frames):
        """Hand frames over to the encoder.

        Frames given to a writer which is not open are dropped, since there is
        no file for them to go to.

        Parameters
        ----------
        frames : list or tuple
            Frames to write, each a tuple of the frame's color data and the
            time in seconds between the start of the recording and the capture
            of that frame. A single such tuple may be passed instead of a list.

        Returns
        -------
        int
            Number of bytes written to the file. This is zero for encoders
            which do not report it, whether or not anything was written.

        """
        if not self._isOpen:
            return 0

        if not isinstance(frames, list):
            frames = [frames]

        bytesOut = 0
        for colorData, elapsed in frames:
            try:
                bytesOut += int(self._writeFrame(colorData, elapsed) or 0)
            except Exception as err:
                logging.error(
                    "Error writing frame {} to movie file '{}': {}".format(
                        self._framesWritten, self._filename, err))

            self._framesWritten += 1

        self._bytesWritten += bytesOut

        return bytesOut

    def close(self):
        """Finish encoding and close the file.

        Calling this on a writer which is not open does nothing.

        """
        if not self._isOpen:
            return

        # cleared first so that frames arriving from the camera's thread while
        # the encoder is being drained are dropped rather than added to it
        self._isOpen = False

        logging.debug(
            "Closing movie file writer using {}...".format(self._encoderLib))

        self._close()

    def _convertToRGB(self, colorData):
        """Get a captured frame in RGB.

        Frames arrive in whatever format the camera is streaming in, which only
        the `Camera` which captured them knows how to convert, so the work is
        handed back to the converter it supplied. Writers which can encode the
        capture library's frames as they come do not need this.

        Parameters
        ----------
        colorData : Any
            Frame as the capture library handed it over.

        Returns
        -------
        object
            The frame in RGB, still in whichever wrapper the capture library
            uses. If no converter was given, the frame is returned unchanged.

        """
        if self._frameConverter is None:
            return colorData

        return self._frameConverter(colorData)

    def _asRGBArray(self, colorData):
        """Get a captured frame as an RGB Numpy array.

        Parameters
        ----------
        colorData : Any
            Frame as the capture library handed it over.

        Returns
        -------
        numpy.ndarray
            Frame as an 8-bit, three channel array of shape
            `(height, width, 3)` with channels in RGB order.

        """
        return _rgbFrameAsArray(self._convertToRGB(colorData))

    def _open(self):
        """Open the encoder and the file it writes to.

        Subclasses implement this. It is called by `open()`, which does the
        bookkeeping common to every writer.

        """
        raise NotImplementedError(
            "`{}` does not implement `_open()`.".format(type(self).__name__))

    def _writeFrame(self, colorData, elapsed):
        """Encode a single frame and write it to the file.

        Subclasses implement this. It is called by `write()` for each frame
        handed over, with exceptions logged rather than raised so that one bad
        frame does not end the recording.

        Parameters
        ----------
        colorData : Any
            Frame to write, as the capture library hands it over.
        elapsed : float
            Time in seconds between the start of the recording and the capture
            of this frame, which is what decides where it lands in the file.

        Returns
        -------
        int
            Number of bytes written, or zero if the encoder does not report it.

        """
        raise NotImplementedError(
            "`{}` does not implement `_writeFrame()`.".format(
                type(self).__name__))

    def _close(self):
        """Flush the encoder and close the file.

        Subclasses implement this. It is called by `close()`, which only calls
        it if the writer is actually open.

        """
        raise NotImplementedError(
            "`{}` does not implement `_close()`.".format(type(self).__name__))

    def __del__(self):
        """Flush and close the file if the writer is garbage collected.
        """
        try:
            self.close()
        except Exception:
            pass


class FFPyPlayerMovieWriter(MovieWriter):
    """Movie file writer which encodes frames with FFPyPlayer.

    FFPyPlayer's `MediaWriter` derives the stream's time base from the frame
    rate it is given, so timestamps can only land on multiples of the frame
    interval. Frames are snapped to those ticks, keeping the timestamps
    increasing so that two frames never share one, which the muxer rejects.

    Parameters
    ----------
    filename : str
        File to write the video to, should include the extension.
    frameSize : ArrayLike
        Size `(w, h)` of the frames to be written, in pixels.
    frameRate : float
        Rate in frames per second the file is written at.
    encoderOpts : dict or None
        Options passed straight to FFmpeg as `libOpts`, as a mapping of option
        names to values (e.g. `{'crf': '23', 'preset': 'veryfast'}`).
    frameConverter : callable or None
        Callable converting a frame as the capture library hands it over into
        RGB. Only needed when the camera is captured with a library other than
        FFPyPlayer, whose frames are encoded as they come.

    """
    _encoderLib = MOVIE_WRITER_LIB_FFPYPLAYER

    def __init__(self, *args, **kwargs):
        MovieWriter.__init__(self, *args, **kwargs)

        self._writer = None
        # ticks the stream's timestamps are counted in, set when the file is
        # opened since it follows from the frame rate the encoder is given
        self._ticksPerSec = 1.0
        self._lastWrittenTick = -1  # keeps timestamps strictly increasing
        self._generatePTS = False

    def _open(self):
        """Open the `MediaWriter` which encodes the file.
        """
        from ffpyplayer.writer import MediaWriter

        frameWidth, frameHeight = self._frameSize

        # options to configure the writer
        writerOptions = {
            'pix_fmt_in': 'yuv420p',  # default for now using mp4
            'width_in': frameWidth,
            'height_in': frameHeight,
            'codec': 'libx264',
            'frame_rate': (int(self._frameRate), 1)}

        self._ticksPerSec = float(writerOptions['frame_rate'][0])
        self._lastWrittenTick = -1

        self._generatePTS = False  # whether to generate PTS for the writer
        if self._filename.endswith('.mp4'):
            self._generatePTS = True  # generate PTS for mp4 files
            logging.debug(
                "MP4 format detected, PTS will be generated for the movie "
                "writer.")

        self._writer = MediaWriter(
            self._filename,
            [writerOptions],
            fmt='mp4',
            overwrite=True,  # overwrite existing file
            libOpts=self._encoderOpts)

        logging.debug(
            "Opened movie file writer using FFPyPlayer, writing {}x{} @{} fps "
            "to '{}'".format(
                frameWidth, frameHeight, self._frameRate, self._filename))

    def _writeFrame(self, colorData, elapsed):
        """Convert a frame to the encoder's pixel format and write it.
        """
        from ffpyplayer.pic import Image, SWScale

        if not isinstance(colorData, Image):
            # A frame from another capture library, which FFmpeg cannot scale
            # as it stands. Bring it to RGB and wrap it so that it goes through
            # the same path as a frame captured with FFPyPlayer.
            rgbData = self._asRGBArray(colorData)
            frameHeight, frameWidth = rgbData.shape[:2]
            colorData = Image(
                plane_buffers=[rgbData.tobytes()],
                pix_fmt='rgb24',
                size=(frameWidth, frameHeight))

        # do color conversion if needed
        frameWidth, frameHeight = colorData.get_size()
        sws = SWScale(
            frameWidth, frameHeight,
            colorData.get_pixel_format(),
            ofmt='yuv420p')

        # Place the frame at the point in the recording it was captured, rather
        # than counting frames off at the nominal rate. Snap to the stream's
        # tick grid, keeping timestamps increasing.
        tick = int(round(elapsed * self._ticksPerSec))
        tick = max(tick, self._lastWrittenTick + 1)
        self._lastWrittenTick = tick
        self._lastPTS = tick / self._ticksPerSec

        # we get an EOF error when the movie writer is fully drained, catch it
        # and ignore it
        try:
            return self._writer.write_frame(
                img=sws.scale(colorData),
                pts=self._lastPTS,
                stream=0)
        except Exception:
            pass

        return 0

    def _close(self):
        """Close the `MediaWriter`.
        """
        try:
            self._writer.close()
        except Exception as err:
            logging.error("Error closing the movie file: {}".format(err))

        self._writer = None


class PyAVMovieWriter(MovieWriter):
    """Movie file writer which encodes frames with PyAV.

    PyAV lets the stream's time base be chosen freely, so a fine one is used
    and each frame is timestamped with when it was actually captured. Frames
    therefore need no padding or dropping to keep the recording the same length
    as the wall clock time it was captured over.

    Parameters
    ----------
    filename : str
        File to write the video to, should include the extension.
    frameSize : ArrayLike
        Size `(w, h)` of the frames to be written, in pixels.
    frameRate : float
        Rate in frames per second the file is written at.
    encoderOpts : dict or None
        Options to pass to the encoder, as a mapping of FFmpeg option names to
        values (e.g. `{'crf': '23', 'preset': 'veryfast'}`).
    frameConverter : callable or None
        Callable converting a frame as the capture library hands it over into
        RGB. Only needed when the camera is captured with a library other than
        PyAV, whose frames are encoded as they come.

    """
    _encoderLib = MOVIE_WRITER_LIB_PYAV

    def __init__(self, *args, **kwargs):
        MovieWriter.__init__(self, *args, **kwargs)

        self._writer = None  # output container
        self._stream = None  # video stream within it
        self._reformatter = None  # colour converter, reused for every frame
        self._timeBase = None  # time base output timestamps are counted in

    def _open(self):
        """Open the output container and add the stream frames are written to.
        """
        import av
        from av.video.reformatter import VideoReformatter
        from fractions import Fraction

        frameWidth, frameHeight = self._frameSize

        # The encoder needs an exact rational frame rate, but cameras report
        # theirs as a float (often something like 29.97), so approximate it.
        outFrameRate = Fraction(self._frameRate).limit_denominator(1001)

        # A fine time base, so that it can express whatever intervals the
        # camera actually produced rather than only multiples of the nominal
        # frame interval.
        self._timeBase = Fraction(1, 90000)

        self._writer = av.open(self._filename, mode='w')
        self._stream = self._writer.add_stream('libx264', rate=outFrameRate)
        self._stream.width = frameWidth
        self._stream.height = frameHeight
        self._stream.pix_fmt = 'yuv420p'
        self._stream.codec_context.time_base = self._timeBase
        if self._encoderOpts:
            self._stream.options = {
                str(key): str(val) for key, val in self._encoderOpts.items()}

        # cached converter to yuv420p, reused for every frame written
        self._reformatter = VideoReformatter()

        logging.debug(
            "Opened movie file writer using PyAV, writing {}x{} @{} fps to "
            "'{}'".format(
                frameWidth, frameHeight, outFrameRate, self._filename))

    def _toAVVideoFrame(self, colorData):
        """Get a captured frame as an `av.VideoFrame` ready to be encoded.

        Parameters
        ----------
        colorData : Any
            Frame as handed over by the camera interface.

        Returns
        -------
        av.VideoFrame
            The frame converted to the pixel format the encoder wants.

        """
        import av

        if not isinstance(colorData, av.VideoFrame):
            # a frame from another capture library, brought to RGB and wrapped
            # so that PyAV can reformat it like any other
            colorData = av.VideoFrame.from_ndarray(
                self._asRGBArray(colorData), format='rgb24')

        return self._reformatter.reformat(colorData, format='yuv420p')

    def _writeFrame(self, colorData, elapsed):
        """Timestamp a frame with when it was captured and encode it.
        """
        avFrame = self._toAVVideoFrame(colorData)

        # place the frame at the point in the recording it was captured
        self._lastPTS = elapsed
        avFrame.pts = int(round(self._lastPTS / self._timeBase))
        avFrame.time_base = self._timeBase

        bytesOut = 0
        for packet in self._stream.encode(avFrame):
            bytesOut += packet.size
            self._writer.mux(packet)

        return bytesOut

    def _close(self):
        """Flush the encoder and close the output container.
        """
        try:
            # flush whatever the encoder is still holding on to
            if self._stream is not None:
                for packet in self._stream.encode(None):
                    self._writer.mux(packet)
        except Exception as err:
            logging.error(
                "Error flushing the movie file writer: {}".format(err))
        finally:
            self._stream = None
            self._reformatter = None
            try:
                self._writer.close()
            except Exception as err:
                logging.error("Error closing the movie file: {}".format(err))

            self._writer = None


class OpenCVMovieWriter(MovieWriter):
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
    encoderOpts : dict or None
        Options for the encoder. OpenCV exposes very little of its encoder, so
        only `'fourcc'` (the FourCC code of the codec to write with, `'mp4v'`
        by default) and `'bufferSecs'` (how many seconds of video the encoder
        may fall behind by before frames are dropped) are understood here.
        Anything else is ignored, with a warning. A codec the local OpenCV
        build cannot write with is swapped for one it can, with a warning; see
        `_fallbackFourCCs`.
    frameConverter : callable or None
        Callable converting a frame as the capture library hands it over into
        RGB. OpenCV cannot encode the other libraries' frames, so this is
        needed unless the camera is captured with OpenCV too.

    """
    _encoderLib = MOVIE_WRITER_LIB_OPENCV

    # encoder options this writer understands, anything else is ignored
    _knownEncoderOpts = {'fourcc', 'bufferSecs'}

    # Codecs tried, in order, when the one asked for cannot be written by the
    # local OpenCV build. Which codecs a build can write depends on which
    # backend it carries: with FFMPEG, which the Linux and Windows wheels have,
    # the default `'mp4v'` is written fine, but the macOS Intel wheels from
    # 4.13 onwards ship without a working FFMPEG backend
    # (opencv/opencv-python#1192), leaving AVFoundation, whose writer takes
    # only `'avc1'`/`'h264'`, `'mjpg'`/`'jpeg'` and `'hvc1'`/`'hevc'`. The
    # reverse does not hold: the FFMPEG those wheels are built with carries no
    # H.264 encoder, so `'avc1'` is not worth trying anywhere but macOS.
    _fallbackFourCCs = ('avc1',) if sys.platform == 'darwin' else ()

    # Longest gap in the recording, in seconds, that will be filled by
    # repeating frames. A gap longer than this means the camera stalled, and is
    # logged and left unfilled rather than padded out with thousands of copies
    # of the same frame.
    _maxGapSecs = 10.0

    def __init__(self, *args, **kwargs):
        MovieWriter.__init__(self, *args, **kwargs)

        unknownOpts = set(self._encoderOpts) - self._knownEncoderOpts
        if unknownOpts:
            logging.warning(
                "The OpenCV movie writer does not understand the encoder "
                "option(s) {}, they will be ignored.".format(
                    ", ".join(repr(opt) for opt in sorted(unknownOpts))))

        self._fourcc = self._encoderOpts.get('fourcc', 'mp4v')
        self._queueSecs = float(self._encoderOpts.get('bufferSecs', 10.0))

        self._writer = None
        self._queue = None
        self._writerThread = None
        self._maxGapFrames = 1
        self._closeTimeout = 30.0

        self._lastIndex = -1  # output slot the last frame written landed on
        self._lastFrame = None  # repeated to fill gaps, see the class docstring
        # How far into the recording the last frame handed over sat, whether or
        # not it reached the file. `_padToEnd()` needs this to know how long the
        # recording was meant to be.
        self._lastSubmittedElapsed = 0.0
        self._framesEncoded = 0
        # Frames dropped are counted separately by cause, which also keeps each
        # counter to a single thread: frames too close together are dropped by
        # the encoder thread, frames arriving with the queue full by whichever
        # thread submitted them.
        self._framesTooClose = 0
        self._framesNotQueued = 0
        # An encoder which cannot keep up drops every frame from then on, so
        # the warning for it is logged once and then only every so often,
        # rather than once per frame.
        self._dropWarningInterval = 1
        self._nextDropWarning = 1  # drop count the next warning is logged at

    @property
    def framesEncoded(self):
        """Number of frames written to the file so far (`int`).

        This includes frames repeated to fill gaps left by the camera, so it
        counts the frames in the file rather than the frames captured. Frames
        still waiting in the encoder's queue are not counted until they reach
        the file.

        """
        return self._framesEncoded

    @property
    def framesDropped(self):
        """Number of submitted frames which did not reach the file (`int`).

        Frames are dropped either because the camera delivered them faster than
        the output's frame rate can represent, or because the encoder fell far
        enough behind to fill its queue.

        """
        return self._framesTooClose + self._framesNotQueued

    def _open(self):
        """Open the `VideoWriter` and start the thread which feeds it.
        """
        import cv2

        # Backends to ask for, in order. Left to itself OpenCV works down the
        # backends its build has, and a backend which will not write the codec
        # asked for simply hands on to the next, ending at the writer which
        # writes a numbered image per frame and fails too. Naming FFMPEG first
        # means the codec is offered to the backend most likely to take it,
        # rather than to whichever one the build happens to list first.
        apiPrefs = (cv2.CAP_FFMPEG, cv2.CAP_ANY)

        # the codec asked for first, then the ones this platform can fall back
        # on, skipping any repeat of the one already tried
        fourccs = [self._fourcc]
        fourccs += [fourcc for fourcc in self._fallbackFourCCs
                    if fourcc != self._fourcc]

        writer = openedWith = None
        for fourcc in fourccs:
            for apiPref in apiPrefs:
                writer = cv2.VideoWriter(
                    self._filename,
                    apiPref,
                    cv2.VideoWriter_fourcc(*fourcc),
                    self._frameRate,
                    self._frameSize)

                if writer.isOpened():
                    openedWith = fourcc
                    break

                writer.release()
                writer = None

            if writer is not None:
                break

        if writer is None:
            raise RuntimeError(
                "OpenCV could not open '{}' for writing at {}x{} @{} fps with "
                "any of the codecs {}. The OpenCV in use may have been built "
                "without a backend which can write them; "
                "`cv2.getBuildInformation()` says which backends it has, and "
                "setting `OPENCV_VIDEOIO_DEBUG=1` in the environment makes "
                "OpenCV log what each one did with the codec.".format(
                    self._filename, self._frameSize[0], self._frameSize[1],
                    self._frameRate,
                    ", ".join(repr(fourcc) for fourcc in fourccs)))

        if openedWith != self._fourcc:
            logging.warning(
                "The OpenCV in use cannot write with the '{}' codec, so '{}' "
                "is being written with '{}' instead.".format(
                    self._fourcc, self._filename, openedWith))
            # kept so that reopening this writer goes straight to the codec
            # which works rather than failing its way back to it
            self._fourcc = openedWith

        self._writer = writer

        self._queue = queue.Queue(
            maxsize=max(1, int(self._queueSecs * self._frameRate)))
        self._maxGapFrames = max(
            1, int(round(self._maxGapSecs * self._frameRate)))

        # How long `close()` waits for the encoder to work through its backlog.
        # The queue is bounded, so the worst case is encoding `bufferSecs` of
        # video, which is allowed to take rather longer than real time.
        self._closeTimeout = max(30.0, self._queueSecs * 3.0)

        self._lastIndex = -1
        self._lastFrame = None
        self._lastSubmittedElapsed = 0.0
        self._framesEncoded = 0
        self._framesTooClose = 0
        self._framesNotQueued = 0
        self._dropWarningInterval = max(1, int(round(self._frameRate * 10.0)))
        self._nextDropWarning = 1

        self._writerThread = threading.Thread(
            target=self._writeFramesAsync,
            name='PsychoPy-OpenCVMovieWriter',
            daemon=True)
        self._writerThread.start()

        logging.debug(
            "Opened movie file writer using OpenCV, writing {}x{} @{} fps as "
            "'{}' to '{}'".format(
                self._frameSize[0], self._frameSize[1], self._frameRate,
                self._fourcc, self._filename))

    def _writeFrame(self, colorData, elapsed):
        """Hand a frame over to the encoder thread.

        This returns as soon as the frame is queued; the conversion to BGR and
        the encoding itself happen on the writer's own thread.

        """
        # place the frame at the point in the recording it was captured
        self._lastPTS = elapsed
        if elapsed > self._lastSubmittedElapsed:
            self._lastSubmittedElapsed = elapsed

        # Converted here rather than on the encoder thread, since only the
        # camera which captured the frame knows how to convert it, and it may
        # go on to reuse the buffer the frame was handed over in.
        colorData = self._convertToRGB(colorData)

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

        # OpenCV does not report how much it has written, unlike the FFmpeg
        # based writers
        return 0

    def _writeFramesAsync(self):
        """Encode queued frames until asked to stop.

        This runs on the thread started by `_open()`. It returns once the
        sentinel `_close()` puts on the queue comes around, which is only after
        every frame queued before it has been written.

        """
        while True:
            item = self._queue.get()
            if item is None:  # sentinel, no more frames are coming
                self._padToEnd()
                break

            try:
                self._encodeFrame(*item)
            except Exception as err:
                logging.error(
                    "Error writing frame {} to movie file '{}': {}".format(
                        self._framesEncoded, self._filename, err))

    def _encodeFrame(self, colorData, elapsed):
        """Place a single frame on the output's frame grid and encode it.

        This runs on the encoder thread.

        Parameters
        ----------
        colorData : Any
            Frame to write, in RGB.
        elapsed : float
            Time in seconds between the start of the recording and the capture
            of this frame.

        """
        import cv2

        frame = cv2.cvtColor(_rgbFrameAsArray(colorData), cv2.COLOR_RGB2BGR)

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
                self._framesEncoded += 1

        self._writer.write(frame)
        self._framesEncoded += 1
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
            self._framesEncoded += 1

        self._lastIndex += gapFrames

    def _close(self):
        """Wait for the encoder to drain its queue and close the file.

        This blocks until every frame handed over has been written, so that
        nothing captured before the recording stopped is lost.

        """
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
                self._framesEncoded, self._filename, self._framesTooClose,
                self._framesNotQueued))

        if self._framesNotQueued:
            logging.warning(
                "The OpenCV movie writer could not keep up with the camera and "
                "dropped {} frame(s) from '{}'. The recording is still the "
                "right length, but those frames show the picture before "
                "them.".format(self._framesNotQueued, self._filename))


# Movie writer to use for each supported encoder library. These should
# match the constants in the camera library which specify the backend.
_movieWriterLibTbl = {
    MOVIE_WRITER_LIB_FFPYPLAYER: FFPyPlayerMovieWriter,
    MOVIE_WRITER_LIB_PYAV: PyAVMovieWriter,
    MOVIE_WRITER_LIB_OPENCV: OpenCVMovieWriter
}


def getMovieWriterClass(encoderLib=None):
    """Get the movie writer class which encodes with the given library.

    Parameters
    ----------
    encoderLib : str or None
        Encoder library the writer should use, one of `'ffpyplayer'`, `'pyav'`
        or `'opencv'`. If `None`, the library named by `camera.backend` is
        used.

    Returns
    -------
    type
        Subclass of `MovieWriter` which encodes movie files using `encoderLib`.

    """
    global backend, _movieWriterLibTbl

    if encoderLib is None:
        encoderLib = backend

    try:
        return _movieWriterLibTbl[encoderLib]
    except KeyError:
        raise ValueError(
            "Invalid value for parameter `encoderLib`, expected one of {}, got "
            "'{}'.".format(
                ", ".join(repr(k) for k in _movieWriterLibTbl), encoderLib))


def closeAllMovieWriters():
    """Signal all movie writers to close.

    This function should only be called once at the end of the program. This can 
    be registered `atexit` to ensure that all movie writers are closed when the 
    program exits. If there are open file writers with frames still queued, this 
    function will block until all frames remaining are written to disk. 

    Use caution when calling this function when file writers are being used in a
    multi-threaded environment. Threads that are writing movie frames must be
    stopped prior to calling this function. If not, the thread may continue to
    write frames to the queue during the flush operation and never exit.

    """
    global _openMovieWriters

    if not _openMovieWriters:  # do nothing if no movie writers are open
        return

    logging.info('Closing all open ({}) movie writers now'.format(
        len(_openMovieWriters)))

    for movieWriter in _openMovieWriters.copy():
        # flush the movie writer, this will block until all frames are written
        movieWriter.close()
        
    _openMovieWriters.clear()  # clear the set to free references


# register the cleanup function to run when the program exits
atexit.register(closeAllMovieWriters)

# --- Movie editing functions ---

def _getFFMPEGExe():
    """Get the path to the FFMPEG executable to use for shell commands.

    A copy of FFMPEG installed on the system takes precedence over the one
    shipped with `imageio-ffmpeg`, which is used as a fallback. The result is
    cached after the first successful lookup.

    Returns
    -------
    str
        Path to (or name of) the FFMPEG executable.

    Raises
    ------
    FileNotFoundError
        If no FFMPEG executable could be found.

    """
    global _ffmpegExe
    if _ffmpegExe is not None:
        return _ffmpegExe

    import shutil

    foundExe = shutil.which('ffmpeg')

    if foundExe is None:  # fallback to the binary `imageio-ffmpeg` provides
        try:
            import imageio_ffmpeg
            foundExe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            foundExe = None

    if foundExe is None:
        raise FileNotFoundError(
            "Could not find an FFMPEG executable on this system. Install "
            "FFMPEG and make sure it is on the system path.")

    logging.debug("Using FFMPEG executable at `{}`".format(foundExe))

    _ffmpegExe = foundExe

    return _ffmpegExe


def _ffmpegOptsToArgs(opts):
    """Convert a mapping of FFMPEG options to a list of command line arguments.

    Keys are option names without the leading dash (e.g. ``'c:v'``, ``'b:a'``).
    String and numeric values are passed through as the argument following the
    option. A value of `True` gives a bare flag (e.g. ``{'shortest': True}``
    becomes ``['-shortest']``) while `False` or `None` drops the option
    entirely, which allows a caller to switch off one of the defaults.

    Parameters
    ----------
    opts : dict
        Mapping of FFMPEG option names to values.

    Returns
    -------
    list
        Command line arguments to splice into an FFMPEG command.

    """
    toReturn = []
    for key, value in opts.items():
        if value is None or value is False:  # option disabled, skip it
            continue

        toReturn.append('-' + str(key))

        if value is True:  # bare flag, no value follows it
            continue

        toReturn.append(str(value))

    return toReturn


def addAudioToMovie(outputFile, videoFile, audioFile, useThreads=True, 
                    removeFiles=False, writerOpts=None):
    """Add an audio track to a video file.

    This function will add an audio track to a video file. If the video file
    already has an audio track, it will be replaced with the audio file
    provided. If no audio file is provided, the audio track will be removed
    from the video file.

    The audio track should be exactly the same length as the video track.

    Muxing is done by FFMPEG, which is called as a shell command. The video
    stream is copied across untouched by default (no re-encode, so no
    generational quality loss) and only the audio is transcoded.

    Parameters
    ----------
    outputFile : str
        Path to the output video file where audio and video will be merged. Any
        existing file at this location will be overwritten.
    videoFile : str
        Path to the input video file.
    audioFile : str or None
        Path to the audio file to add to the video file. If `None`, the output
        file will have no audio track at all.
    useThreads : bool
        If `True`, the audio will be added in a separate thread. This allows the
        audio to be added in the background while the program continues to run.
        If `False`, the audio will be added in the main thread and the program
        will block until the audio is added. Defaults to `True`. Note that the
        thread is not returned and never joined, so there is presently no way
        for the caller to tell when the merge has finished or whether it
        succeeded, failures are logged as errors instead of raised. Pass
        `useThreads=False` if you need to handle those cases.
    removeFiles : bool
        If `True`, the input video (`videoFile`) and audio (`audioFile`) files 
        will be removed (i.e. deleted from disk) after the audio has been added 
        to the video. Defaults to `False`. The input files are left alone if the
        merge fails.
    writerOpts : dict or None
        Additional options to pass to FFMPEG as a mapping of option names
        (without the leading dash) to values, for instance
        ``{'c:a': 'libmp3lame', 'b:a': '192k'}``. These are merged over the
        defaults (``{'c:v': 'copy', 'c:a': 'aac', 'shortest': True}``) so a key
        given here overrides the default of the same name, and a value of
        `False` or `None` drops that option. A value of `True` gives a bare
        flag. Defaults to `None`.

    Raises
    ------
    FileNotFoundError
        If `videoFile` or `audioFile` does not exist, or if the FFMPEG
        executable cannot be found on this system.
    RuntimeError
        If FFMPEG failed to merge the tracks. Only raised when
        `useThreads=False`, see above.

    Examples
    --------
    Combine a video file and an audio file into a single video file::

        from psychopy.tools.movietools import addAudioToMovie
        addAudioToMovie('output.mp4', 'video.mp4', 'audio.mp3')

    Transcode the audio to MP3 instead of the default AAC::

        addAudioToMovie('output.mp4', 'video.mp4', 'audio.wav',
                        writerOpts={'c:a': 'libmp3lame', 'b:a': '192k'})

    """
    import subprocess as sp

    if not os.path.exists(videoFile):
        raise FileNotFoundError(
            "Video file `{}` does not exist.".format(videoFile))

    if audioFile is not None and not os.path.exists(audioFile):
        raise FileNotFoundError(
            "Audio file `{}` does not exist.".format(audioFile))

    # resolve FFMPEG up-front so a missing binary is reported to the caller
    # rather than buried in a worker thread
    ffmpegExe = _getFFMPEGExe()

    if audioFile is None:  # no audio given, strip any audio the video has
        ffmpegOpts = {'c:v': 'copy', 'an': True}
    else:
        ffmpegOpts = {
            'c:v': 'copy',  # pass the video stream through unchanged
            'c:a': 'aac',  # transcode the audio track
            'shortest': True  # stop when the shortest input stream ends
        }

    if writerOpts is not None:  # let the user override any of the defaults
        ffmpegOpts.update(writerOpts)

    cmd = [
        ffmpegExe,
        '-loglevel', 'error',  # suppress output except errors
        '-nostdin',  # do not read from stdin
        '-y',  # overwrite output file if it exists
        '-i', videoFile  # input video track
    ]

    if audioFile is not None:
        cmd.extend(['-i', audioFile])  # input audio track

    cmd.extend(_ffmpegOptsToArgs(ffmpegOpts))
    cmd.append(outputFile)  # output file goes last

    def _renderVideo(cmd, outputFile, videoFile, audioFile, removeFiles):
        """Run the FFMPEG command which merges the audio and video tracks.
        """
        logging.debug(
            "Merging audio and video tracks with command: {}".format(
                ' '.join(cmd)))

        proc = sp.run(
            cmd,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            stdin=sp.DEVNULL,
            universal_newlines=True)

        if proc.returncode != 0:
            raise RuntimeError(
                "FFMPEG returned non-zero exit code {} while merging audio and "
                "video tracks into `{}`:\n{}".format(
                    proc.returncode, outputFile, proc.stderr))

        logging.info(
            "Merged audio and video tracks into `{}`".format(outputFile))

        if removeFiles:
            # remove the input files
            os.remove(videoFile)
            if audioFile is not None:
                os.remove(audioFile)

    # run the audio/video merge in the main thread
    if not useThreads:
        logging.debug('Adding audio to video file in main thread')
        _renderVideo(cmd, outputFile, videoFile, audioFile, removeFiles)
        return

    def _renderVideoThreaded(*args):
        """Wrapper which logs errors, nothing can catch them out here.
        """
        try:
            _renderVideo(*args)
        except Exception as e:
            logging.error(
                "Failed to add audio to video file: {}".format(e))

    # run the audio/video merge in a separate thread
    logging.debug('Adding audio to video file in separate thread')
    compositorThread = threading.Thread(
        target=_renderVideoThreaded, 
        args=(cmd,
              outputFile, 
              videoFile, 
              audioFile, 
              removeFiles))
    compositorThread.start()


def extractAudioFromMovie(videoFile, audioFile, removeFiles=False):
    """Extract the audio track from a video file.

    This function will extract the audio track from a video file and save it to
    a separate audio file. The audio stream is transcoded by FFMPEG using the
    encoder associated with the extension of `audioFile` (e.g. ``.wav`` gives
    PCM audio, ``.mp3`` gives MPEG layer 3 audio, etc.)

    Parameters
    ----------
    videoFile : str
        Path to the input video file.
    audioFile : str
        Path to the output audio file where the audio track will be saved. Any
        existing file at this location will be overwritten.
    removeFiles : bool
        If `True`, the input video file (`videoFile`) will be removed (i.e.
        deleted from disk) after the audio has been extracted. Defaults to
        `False`. The video file is left alone if the extraction fails.

    Raises
    ------
    FileNotFoundError
        If `videoFile` does not exist, or if the FFMPEG executable cannot be
        found on this system.
    RuntimeError
        If FFMPEG failed to extract the audio track, for instance if the video
        file has no audio track at all.

    Examples
    --------
    Extract the audio track from a video file::

        from psychopy.tools.movietools import extractAudioFromMovie
        extractAudioFromMovie('video.mp4', 'audio.mp3')

    """
    import subprocess as sp

    if not os.path.exists(videoFile):
        raise FileNotFoundError(
            "Video file `{}` does not exist.".format(videoFile))

    ffmpegExe = _getFFMPEGExe()  # raises if FFMPEG is unavailable

    # build the command to demux the audio track out of the video file, the
    # encoder used is inferred by FFMPEG from the output file extension
    cmd = [
        ffmpegExe,
        '-loglevel', 'error',  # suppress output except errors
        '-nostdin',  # do not read from stdin
        '-y',  # overwrite output file if it exists
        '-i', videoFile,  # input video file
        '-vn',  # drop the video stream
        audioFile  # output audio file
    ]

    logging.debug(
        "Extracting audio track with command: {}".format(' '.join(cmd)))

    proc = sp.run(
        cmd,
        stdout=sp.PIPE,
        stderr=sp.PIPE,
        stdin=sp.DEVNULL,
        universal_newlines=True)

    if proc.returncode != 0:
        raise RuntimeError(
            "FFMPEG returned non-zero exit code {} while extracting the audio "
            "track from `{}`:\n{}".format(
                proc.returncode, videoFile, proc.stderr))

    logging.info(
        "Extracted audio track from `{}` to `{}`".format(videoFile, audioFile))

    if removeFiles:
        # remove the input video file
        os.remove(videoFile)


if __name__ == "__main__":
    pass
