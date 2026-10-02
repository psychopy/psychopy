#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Base class for reading frames from movie files.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'MovieFileReader',
    'PREFERRED_VIDEO_LIB',
    'SUPPORTED_VIDEO_LIBS',
]

import os.path
import math
import threading
import time
from collections import deque

from psychopy import logging
from psychopy.constants import NOT_STARTED
from ..frame import FRAME_PIXEL_FORMAT, FRAME_BYTES_PER_PIXEL
from ..metadata import MovieMetadata, NULL_MOVIE_METADATA

# time to wait for the movie decoder to respond
defaultTimeout = 5.0  # seconds

# Memory the `pyav` and `opencv` backends may use for frames decoded ahead of
# playback, and the bounds on how many frames that comes to. Decoding ahead on
# a background thread absorbs frames which take longer than usual to decode,
# such as the first after a seek while the decoder's own threads refill, rather
# than stalling the drawing loop. A 4K frame is ~33 MB as RGBA, so this is 8
# frames at 4K and the maximum at 1080p and below.
DECODE_AHEAD_BYTES = 256 * 1024 ** 2
DECODE_AHEAD_MIN_FRAMES = 2
DECODE_AHEAD_MAX_FRAMES = 16

# How far back the decode thread first goes when a seek lands on a frame past
# the position asked for, doubling each time it still does. This happens with
# `pyav`, see `_runDecoder`.
DECODE_SEEK_BACKOFF = 0.5  # seconds

# Placed in the decode-ahead queue where the movie ends. When looping,
# frames from the start of the next pass are queued after it.
_END_OF_STREAM = object()

# recommended library for video decoding
PREFERRED_VIDEO_LIB = 'pyav'

# Movie decoder libraries which are recognized/supported by `MovieFileReader`
# and `MovieStim`.
SUPPORTED_VIDEO_LIBS = ('ffpyplayer', 'pyav', 'opencv', 'vlc')

# Keep track of movie readers here. This is used to close all movie readers
# when the main thread exits. We identify movie readers by hashing the filename
# they are presently reading from.

_openMovieReaders = set()

# Reader class for each of `SUPPORTED_VIDEO_LIBS`, by name, filled in as each
# is defined, see `MovieFileReader.__init_subclass__`
_MOVIE_READER_CLASSES = {}

class MovieFileReader:
    """Read movie frames from file.

    This class manages reading movie frames from a file or stream. The method
    used to read the movie frames is determined by the `decoderLib` parameter.
    Each backend has a subclass of its own (`FFPyPlayerMovieFileReader`,
    `PyAVMovieFileReader`, `OpenCVMovieFileReader` and `VLCMovieFileReader`),
    and creating a `MovieFileReader` gives an instance of the one `decoderLib`
    names. Machinery common to the backends lives in this class.

    Parameters
    ----------
    filename : str
        The name (or path) of the file to read the movie from.
    decoderLib : str or None
        The library to use to handle decoding the movie. One of `'ffpyplayer'`,
        `'pyav'`, `'opencv'` or `'vlc'`. If `None` (default), the library is
        chosen automatically based on the running Python version: `'pyav'` on
        Python 3.14+ (where `ffpyplayer` is not available), and `'ffpyplayer'`
        otherwise.
    decoderOpts : dict or None
        A dictionary of options to pass to the decoder. These option can be used
        to control the quality of the movie, for example. The options depend on
        the `decoderLib` in use. If `None`, the reader will use the default
        options for the backend.

    Notes
    -----
    * If `decoderLib='ffpyplayer'` or `decoderLib='vlc'`, the decoder is left
      paused after `open()`, so `getFrame()` returns `None` until
      `pause(False)` is called. The `pyav` and `opencv` backends return a
      frame immediately. `MovieStim` handles this for you via `play()`.
    * If `decoderLib='pyav'` or `decoderLib='opencv'`, frames are decoded
      ahead of playback on a background thread, up to `DECODE_AHEAD_BYTES`
      worth of them.
    * If `decoderLib='ffpyplayer'`, audio playback is handled externally by 
      SDL2. This means that audio playback is not synchronized with frame 
      presentation in PsychoPy. However, playback will not begin until the audio 
      track starts playing.
    * If `decoderLib='vlc'`, audio playback is handled by VLC itself, on the
      default output device. As with `ffpyplayer`, audio is not synchronized
      with frame presentation in PsychoPy.
    * If `decoderLib='pyav'` or `decoderLib='opencv'`, no audio playback is
      provided by the decoder itself; audio must be extracted and played back
      separately (this is handled automatically by `MovieStim`).
    * If `decoderLib='opencv'`, presentation timestamps are derived from frame
      indices and the reported frame rate, so movies with a variable frame rate
      will not be timed correctly. Use `'pyav'` or `'ffpyplayer'` for those.
    * If `decoderLib='vlc'`, VLC decodes to its own clock and hands frames over
      as it reaches them, so `getFrame()` returns whichever frame VLC has most
      recently decoded rather than the one at exactly the requested timestamp.
      This also requires VLC itself to be installed, of an architecture
      matching the Python interpreter running PsychoPy.
    * Do not access private attributes or methods of this class directly since 
      doing so is not thread-safe. Use the public methods provided by this class
      to interact with the movie reader.

    """
    # Name of the decoder library the subclass reads movies with, one of
    # `SUPPORTED_VIDEO_LIBS`
    _decoderLib = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls._decoderLib is not None:
            _MOVIE_READER_CLASSES[cls._decoderLib] = cls

    def __new__(cls, filename, decoderLib=None, decoderOpts=None):
        # `MovieFileReader` itself stands for the reader of whichever backend
        # `decoderLib` names
        if cls is MovieFileReader:
            if decoderLib is None:
                decoderLib = PREFERRED_VIDEO_LIB
            try:
                cls = _MOVIE_READER_CLASSES[decoderLib]
            except KeyError:
                raise ValueError(
                    'Unknown decoder library: {}'.format(decoderLib))
        elif decoderLib is not None and decoderLib != cls._decoderLib:
            raise ValueError(
                '`{}` reads movies with `decoderLib={!r}`, not {!r}.'.format(
                    cls.__name__, cls._decoderLib, decoderLib))

        return super().__new__(cls)

    def __init__(self,
                 filename,
                 decoderLib=None,
                 decoderOpts=None):

        # `decoderLib` has already picked the class, see `__new__`
        self._filename = filename
        self._decoderOpts = {} if decoderOpts is None else decoderOpts

        # Decode-ahead state, for the backends which decode frames as they are
        # asked for (`pyav` and `opencv`). Frames are decoded ahead of playback
        # on a background thread, which has sole use of the decoder from when
        # it starts until it is stopped (see `_runDecoder`). The state shared
        # with it below is guarded by `_decoderCondition`.
        self._decoderThread = None
        self._decoderCondition = threading.Condition()
        # decoded frames as `(frame, pts)` waiting to be shown, oldest first,
        # with `_END_OF_STREAM` where the movie ends
        self._decodeQueue = deque()
        self._decodeQueueDepth = DECODE_AHEAD_MIN_FRAMES  # set on open
        self._decodeSeekTarget = None  # position the thread is to seek to
        # Bumped on every seek, so the thread can tell that a frame it has
        # just decoded is from before the seek and drop it
        self._decodeGeneration = 0
        self._decodeAtEnd = False  # thread is idle at the end of the movie
        self._decoderStopping = False  # thread has been asked to exit
        # Frames this reader is finished with, which the decode thread drops so
        # that freeing them (~2 ms each at 4K) doesn't hold up drawing. They
        # are collected by the thread calling `getFrame()` in
        # `_releasePending`, which only it uses, and handed over to
        # `_releasedFrames` (guarded by `_decoderCondition`) by `decodeAhead()`.
        self._releasePending = []
        self._releasedFrames = []
        # `getFrame()` has taken frames from the queue without letting the
        # decode thread know yet, see `decodeAhead()`
        self._refillPending = False
        # Used only by the thread calling `getFrame()`. The first frame after
        # a seek or a loop wrapping round is shown even if it is a little
        # ahead of the time asked for, as when a stream starts a frame or two
        # in. `_lastFramePTS` is the time the last frame was shown for, to
        # recognise the movie clock wrapping back round to the start.
        self._decodeLanding = False
        self._lastFramePTS = None

        # last requested mute state, used by backends which have no mute state
        # of their own to report
        self._muted = False

        # Size frames are scaled down to as they're decoded, or `None` for their
        # own, the `swscale` filter to do it with, and whether to keep frames
        # which are planar YUV as such. Kept as one tuple so that the decode
        # thread reads a consistent set. See `setOutputFrameSize` and
        # `setOutputPixelFormat`.
        self._outputFrameFormat = (None, 'AREA', False)

        # set by `seek()` and cleared once the decoder delivers a frame for the
        # new position, see the `isSeeking` property
        self._seeking = False

        # movie information
        self._metadata = None  # metadata object

        # movie attributes
        self._frameInterval = -1.0
        self._srcFrameSize = (-1, -1)
        self._frameRate = -1.0
        self._duration = -1.0
        
        # store decoded video segments in memory
        self._frameStore = []

        # maximum number of attempts to get a frame from the decoder before giving up
        self._maxGetFrameAttempts = -1  # set later based on the frame interval

        # callbacks for video events
        self._streamEOFCallback = None

        # video segment format
        # [{'video': videoFrame, 'audio': audioFrame, 'pts': pts}, ...]

    def __hash__(self):
        """Use the absolute file path as the hash value since we only allow one
        instance per file.
        """
        return hash(os.path.abspath(self._filename))
    
    def _clearFrameQueue(self):
        """Clear the frame queue in a thread-safe way.
        """
        with self._frameQueue.mutex:
            self._frameQueue.queue.clear()

    @property
    def decoderLib(self):
        """The library used to decode the movie (`str`).

        """
        return self._decoderLib

    @property
    def frameSize(self):
        """The frame size of the movie in pixels (`tuple`).

        This is only valid after calling `open()`. If not, the value is 
        `(-1, -1)`.

        """
        return self._srcFrameSize

    @property
    def outputFrameSize(self):
        """Size `(w, h)` in pixels that frames are scaled down to as they are
        decoded, or `None` to keep their own size (`tuple` or `None`). See
        `setOutputFrameSize`."""
        return self._outputFrameFormat[0]

    def setOutputFrameSize(self, size, interpolation='AREA'):
        """Set the size frames are scaled down to as they are decoded.

        Scaling a frame down to the size it will be drawn at, as part of
        converting it to RGBA, costs little more than the conversion alone,
        and makes the frame that much less to copy to the GPU: ~2 MB rather
        than ~33 MB for a 4K movie drawn at 800x600. The result looks better
        too, since the GPU's bilinear filtering samples only a few of the
        source pixels when shrinking a texture by much.

        Frames are never scaled up, nor is their own size changed in either
        dimension beyond `size`. Frames already decoded keep the size they
        were decoded at. Only `pyav` and `opencv` scale frames, the other
        backends always give them at their own size.

        Parameters
        ----------
        size : ArrayLike or None
            Largest size `(w, h)` in pixels to give frames at, or `None` to
            keep their own size.
        interpolation : str
            `swscale` filter to scale frames with, such as `'AREA'` (box
            filter, the default) or `'POINT'` (nearest neighbour). For
            `opencv`, the nearest equivalent of OpenCV's is used, see
            `_resizeFrameOpenCV`.

        """
        if size is not None:
            size = tuple(max(1, int(math.ceil(abs(val)))) for val in size)

        self._outputFrameFormat = (
            size, interpolation, self._outputFrameFormat[2])

        if self._decoderThread is not None:
            # as many frames as fit in the budget at the new size
            with self._decoderCondition:
                self._decodeQueueDepth = self._getDecodeQueueDepth()
                self._decoderCondition.notify_all()

    @property
    def outputPixelFormat(self):
        """Pixel format frames are given in, `'rgba'` or `'yuv'` (`str`). See
        `setOutputPixelFormat`."""
        return 'yuv' if self._outputFrameFormat[2] else 'rgba'

    def setOutputPixelFormat(self, pixelFormat):
        """Set the pixel format frames are given in.

        With `'yuv'`, frames decoded as planar YUV (as most are) are kept as
        such, as `_YUVFrameAdapter`, for the caller to convert to RGB itself
        (`MovieStim` does so in a shader as it uploads them). That saves
        converting them as they're decoded, and leaves less than half as much
        to copy to the GPU. Frames in any other format are given as RGBA
        regardless, as they are with `'rgba'` (the default). Frames already
        decoded keep the format they were decoded in. Only `pyav` gives frames
        as YUV.

        Parameters
        ----------
        pixelFormat : str
            `'rgba'` or `'yuv'`.

        """
        if pixelFormat not in ('rgba', 'yuv'):
            raise ValueError(
                "Invalid pixel format {!r}, expected 'rgba' or 'yuv'.".format(
                    pixelFormat))

        size, interpolation, _ = self._outputFrameFormat
        self._outputFrameFormat = (size, interpolation, pixelFormat == 'yuv')

    @property
    def frameInterval(self):
        """The interval between frames in the movie in seconds (`float`).

        This is only valid after calling `open()`. If not, the value is `-1`.

        """
        return self._frameInterval

    @property
    def frameRate(self):
        """The frame rate of the movie in frames per second (`float`).

        This is only valid after calling `open()`. If not, the value is `-1`.

        """
        return self._frameRate

    @property
    def duration(self):
        """The duration of the movie in seconds (`float`).

        This is only valid after calling `open()`. If not, the value is `-1`.

        """
        return self._duration
    
    @property
    def volume(self):
        """The volume level of the movie player (`float`).

        This is only valid after calling `open()`. If not, the value is `0.0`.

        """
        return self._getVolume()

    @volume.setter
    def volume(self, value):
        """Set the volume level of the movie player (`float`).

        This is only valid after calling `open()`. If not, the value is `0.0`.

        """
        self._setVolume(value)

    @property
    def filename(self):
        """The name (path) of the movie file (`str`).

        This cannot be changed after the reader has been opened.

        """
        return self._filename
    
    def load(self, filename):
        """Load a movie file.

        This is an alias for `setMovie()` to synchronize naming with other video
        classes around PsychoPy.

        Parameters
        ----------
        filename : str
            The name (path) of the file to read the movie from.

        """
        self.setMovie(filename)

    def setMovie(self, filename):
        """Set the movie file to read from and open it.

        If there is a movie file currently open, it will be closed before
        opening the new movie file. Playback will be reset to the beginning of
        the movie.
        
        Parameters
        ----------
        filename : str
            The name (path) of the file to read the movie from.
        
        """
        if self.isOpen:
            self.close()

        # check if the file exists and is readable
        if not os.path.isfile(filename):
            raise IOError('Movie file does not exist: {}'.format(filename))

        self._filename = filename

        self.open()

    def getMetadata(self):
        """Get metadata about the movie file.

        This function returns a `MovieMetadata` object containing metadata
        about the movie file. This includes information about the video and audio
        tracks in the movie. Metadata is extracted from the movie file when the
        movie reader is opened.

        Returns
        -------
        MovieMetadata
            Movie metadata object. If no movie is loaded, return a
            `NULL_MOVIE_METADATA` object instead of `None`. At a minimum,
            ensure that fields `duration`, `size`, and `frameRate` are
            populated if a valid movie is loaded.

        """
        if self._metadata is None:
            return NULL_MOVIE_METADATA
            # raise ValueError('Movie metadata not available. Movie not open.')

        return self._metadata
    
    # --------------------------------------------------------------------------
    # Backend interface
    #
    # Each backend's subclass overrides the methods here to interface with its
    # decoder library. They are not intended to be used directly by users. By
    # default, frames are decoded ahead of playback on a background thread,
    # for which a backend provides `_decodeNextFrame()` and `_seekDecoder()`,
    # and calls `_startDecoder()` once open. Backends which decode to a
    # playback clock of their own override `_getFrame()` and `_seek()`
    # instead, and `pause()`, `mute()`, `muted`, `_getVolume()` and
    # `_setVolume()` too if they play the audio track themselves.
    #

    def _open(self):
        """Open the movie file with the backend's decoder.

        This opens the movie file and extracts metadata about it (see
        `_setMovieProperties`), which will be accessible via the
        `getMetadata()` method. The frame at the start of the movie is put in
        the frame store, so that it shows before playback starts.

        """
        raise NotImplementedError

    def _freePlayer(self):
        """Clean up the player.

        This function closes the player and clears the player object. Do not
        call this method directly while the player is still in use.

        """
        raise NotImplementedError

    def _convertFrameToRGB(self, frame):
        """Convert a frame to RGB format.

        This function converts a frame as the decoder gives it to the format
        frames are given in, see `setOutputPixelFormat`. The result will be in
        the correct format to upload to OpenGL as a texture. Frames which have
        been converted already are returned unchanged.

        Parameters
        ----------
        frame : object
            The frame to convert.

        Returns
        -------
        _RGBFrameAdapter, _YUVFrameAdapter or ffpyplayer.pic.Image
            The converted frame.

        """
        raise NotImplementedError

    def _getVolume(self):
        """Get the volume of the movie player.

        Backends which do not play the audio track themselves report the
        volume last set, since it is managed externally by `MovieStim` via its
        extracted audio track.

        Returns
        -------
        float
            The volume level of the movie player, between 0.0 (mute) and 1.0
            (full volume).

        """
        return self._decoderOpts.get('volume', 0.0)

    def _setVolume(self, volume):
        """Set the volume of the movie player.

        Backends which do not play the audio track themselves only store it
        for reference, since actual playback volume is controlled through
        `MovieStim`'s extracted-audio `Sound` object.

        Parameters
        ----------
        volume : float
            The volume level to set, between 0.0 (mute) and 1.0 (full volume).

        """
        self._decoderOpts['volume'] = volume

    def _setMovieProperties(self, size, frameRate, duration,
                            colorFormat=FRAME_PIXEL_FORMAT):
        """Set the properties of the movie just opened, and the metadata
        `getMetadata()` gives.

        Parameters
        ----------
        size : tuple
            Size `(w, h)` of the movie's frames in pixels.
        frameRate : float
            Frame rate of the movie in frames per second.
        duration : float
            Duration of the movie in seconds.
        colorFormat : str
            Pixel format frames are given in.

        """
        self._frameInterval = 1.0 / frameRate
        # always allow at least one retry, `int()` alone truncates to zero for
        # movies faster than 1000 fps
        self._maxGetFrameAttempts = max(1, int(self._frameInterval / 0.001))
        self._frameRate = frameRate
        self._srcFrameSize = size
        self._duration = duration

        self._metadata = MovieMetadata(
            self._filename,
            size,
            frameRate,
            duration,
            colorFormat)

        logging.debug("Movie metadata: {}".format(repr(self._metadata)))

    # --------------------------------------------------------------------------
    # Decoding ahead
    #
    # Used by the backends which decode frames as they are asked for (`pyav`
    # and `opencv`), see the backend interface above.
    #

    def _decodeNextFrame(self):
        """Decode the next frame of the movie. Only the decode thread may call
        this once it has been started.

        Returns
        -------
        tuple or None
            The frame as the decoder gives it, and its presentation timestamp
            in seconds, or `None` at the end of the movie.

        """
        raise NotImplementedError

    def _seekDecoder(self, pts):
        """Seek the decoder so that it decodes from the frame at or before
        `pts` (seconds) next. Only the decode thread may call this once it has
        been started."""
        raise NotImplementedError

    def _getDecodeQueueDepth(self):
        """Number of frames for the decode thread to decode ahead
        (`int`), as many as fit in `DECODE_AHEAD_BYTES` at the size they
        are decoded at."""
        width, height = self._srcFrameSize
        outputSize = self._outputFrameFormat[0]
        if outputSize is not None:
            width, height = min(width, outputSize[0]), min(height, outputSize[1])
        frameBytes = max(1, width * height * FRAME_BYTES_PER_PIXEL)

        return min(
            max(DECODE_AHEAD_BYTES // frameBytes,
                DECODE_AHEAD_MIN_FRAMES),
            DECODE_AHEAD_MAX_FRAMES)

    def _startDecoder(self, firstFrame):
        """Start the thread which decodes frames ahead of playback.

        Decoding carries on from the first frame of the movie, which has been
        decoded already. Seeking back to the start instead would empty the
        decoder, which with frame threading then takes several frames' worth of
        decoding to produce one again (~50 ms at 4K), and playback would start
        by waiting on that.

        From here until `_stopDecoder()` the decoder (whatever
        `_decodeNextFrame` and `_seekDecoder` use) belongs to that thread, and
        must not be used from any other.

        Parameters
        ----------
        firstFrame : object
            The first frame of the movie, as the decoder gives it.

        """
        # Show the first frame from the very start of the movie. Streams often
        # start a frame or two in (when B-frames delay the first one), which
        # would otherwise leave nothing to show before it.
        self._frameStore.append(
            (self._convertFrameToRGB(firstFrame), 0.0, 'paused'))
        self._lastFramePTS = 0.0

        self._decodeQueueDepth = self._getDecodeQueueDepth()

        with self._decoderCondition:
            self._decodeQueue.clear()
            self._releasedFrames.clear()
            self._decodeSeekTarget = None
            self._decodeAtEnd = False
            self._decoderStopping = False

        self._releasePending.clear()
        self._refillPending = False

        self._decoderThread = threading.Thread(
            target=self._runDecoder,
            name='MovieDecoder({})'.format(os.path.basename(self._filename)),
            daemon=True)
        self._decoderThread.start()

    def _stopDecoder(self):
        """Stop the decode thread and drop any frames it decoded.

        Returns
        -------
        bool
            `True` if the thread has stopped (or was never started), after
            which the decoder is free to be closed.

        """
        if self._decoderThread is None:
            return True

        with self._decoderCondition:
            self._decoderStopping = True
            self._decoderCondition.notify_all()

        # it only checks between frames, so this waits out at most one decode
        self._decoderThread.join(timeout=defaultTimeout)
        if self._decoderThread.is_alive():
            logging.warning(
                "Decode thread for {} did not stop within {} seconds."
                .format(self._filename, defaultTimeout))
            return False

        self._decoderThread = None
        with self._decoderCondition:
            self._decodeQueue.clear()
            self._releasedFrames.clear()

        self._releasePending.clear()
        self._refillPending = False
        self._decodeLanding = False
        self._lastFramePTS = None

        return True

    def _queuedFrameCount(self):
        """Number of decoded frames waiting in the queue (`int`). Must be
        called holding `_decoderCondition`."""
        return sum(
            1 for item in self._decodeQueue if item is not _END_OF_STREAM)

    def _runDecoder(self):
        """Decode frames ahead of playback. This runs on the decode thread.

        Frames are decoded and converted until `_decodeQueueDepth` of them are
        waiting, then this waits for `getFrame()` to take some. Seeks are
        carried out here too, since only this thread may use the decoder (see
        `_decodeNextFrame` and `_seekDecoder`). At the end of the movie
        `_END_OF_STREAM` is queued, and when looping, decoding carries on from
        the start straight away so that the next pass is ready by the time
        playback wraps round to it.

        """
        cond = self._decoderCondition
        frameInterval = self._frameInterval
        seekTarget = None  # frames from before this are skipped after a seek
        # Where the decoder was last seeked to, and how much further back to
        # go if the first frame from there turns out to be past `seekTarget`
        # (`None` once a frame from at or before it has been reached).
        seekFrom = 0.0
        seekBackoff = None

        with cond:
            generation = self._decodeGeneration

        while True:
            with cond:
                while not self._decoderStopping and \
                        self._decodeSeekTarget is None and \
                        not self._releasedFrames and \
                        (self._decodeAtEnd or self._queuedFrameCount() >=
                            self._decodeQueueDepth):
                    cond.wait()

                if self._decoderStopping:
                    return

                released = self._releasedFrames  # dropped below
                self._releasedFrames = []

                seekNow = self._decodeSeekTarget is not None
                if seekNow:
                    seekTarget = seekFrom = self._decodeSeekTarget
                    seekBackoff = DECODE_SEEK_BACKOFF
                    self._decodeSeekTarget = None
                    generation = self._decodeGeneration

                # woken only to free frames, with nowhere to put another
                noRoom = not seekNow and (
                    self._decodeAtEnd or self._queuedFrameCount() >=
                    self._decodeQueueDepth)

            # Free the frames handed over here, outside the lock, rather than
            # on the thread drawing them where it would hold up a frame.
            del released
            if noRoom:
                continue

            failed = False
            try:
                if seekNow:
                    self._seekDecoder(seekFrom)

                decoded = self._decodeNextFrame()
            except Exception as err:
                # Treat a corrupt or truncated file as the end of the movie,
                # rather than leave playback waiting on frames that will never
                # come.
                logging.error("{} failed to decode {}: {}".format(
                    self._decoderLib, self._filename, err))
                decoded = None
                failed = True

            if decoded is None:  # reached the end of the movie
                # infinite looping is requested when `loop` is explicitly `0`,
                # mirroring the `ffpyplayer` convention used elsewhere
                loopInfinitely = \
                    self._decoderOpts.get('loop', 1) == 0 and not failed
                with cond:
                    if generation != self._decodeGeneration:
                        continue  # seeked since, so this is not the end now
                    self._decodeQueue.append(_END_OF_STREAM)
                    self._decodeAtEnd = not loopInfinitely
                    cond.notify_all()

                if loopInfinitely:
                    seekTarget = None
                    try:
                        self._seekDecoder(0.0)
                    except Exception as err:
                        logging.error(
                            "{} failed to rewind {} to loop it: {}".format(
                                self._decoderLib, self._filename, err))
                        with cond:
                            self._decodeAtEnd = True
                continue

            rawFrame, pts = decoded

            if seekTarget is not None:
                if seekBackoff is not None:
                    if pts > seekTarget and seekFrom > 0.0:
                        # PyAV seeks to keyframes by decode time, and with
                        # B-frames the one it lands on can be shown after the
                        # position asked for, leaving the frames up to it
                        # unreachable from there. Go back further and decode
                        # forward instead.
                        seekFrom = max(0.0, seekFrom - seekBackoff)
                        seekBackoff *= 2
                        try:
                            self._seekDecoder(seekFrom)
                        except Exception as err:
                            logging.error("{} failed to seek {}: {}".format(
                                self._decoderLib, self._filename, err))
                            seekBackoff = None
                        continue
                    seekBackoff = None  # reached a frame from before it

                if pts + frameInterval <= seekTarget:
                    continue  # from before the position seeked to
                seekTarget = None

            frame = self._convertFrameToRGB(rawFrame)

            with cond:
                if generation == self._decodeGeneration:  # else seeked since
                    self._decodeQueue.append((frame, pts))
                    cond.notify_all()

    def _skipToNextPass(self):
        """Skip ahead to the next pass of a looping movie.

        Returns
        -------
        bool
            `True` if the decode thread had already reached the end of the
            movie and the frames after it, from the start of the next pass,
            are now next in line. `False` if it hadn't, or the movie is not
            looping, in which case nothing is changed.

        """
        if self._decoderOpts.get('loop', 1) != 0:
            return False

        with self._decoderCondition:
            if not any(item is _END_OF_STREAM for item in self._decodeQueue):
                return False

            while True:
                item = self._decodeQueue.popleft()
                if item is _END_OF_STREAM:
                    break
                # the rest of the pass being left, for the decode thread to free
                self._releasedFrames.append(item)
            self._decoderCondition.notify_all()

        self._cleanUpFrameStore()
        self._decodeLanding = True
        self._lastFramePTS = None

        return True

    def _seek(self, reqPTS):
        """Seek routine of the backends which decode ahead (`pyav` and
        `opencv`).

        The seek is handed to the decode thread, which seeks the decoder and
        decodes forward to the requested position in the background.

        Parameters
        ----------
        reqPTS : float
            The presentation timestamp (PTS) to seek to in seconds.

        Returns
        -------
        float
            The presentation timestamp (PTS) requested. `getFrame()` returns
            the frame for it once the decode thread has reached it.

        """
        reqPTS = min(max(0.0, reqPTS), self._metadata.duration)

        if self._decoderThread is None:
            return

        self._cleanUpFrameStore()

        with self._decoderCondition:
            self._decodeGeneration += 1
            # all from before the seek, freed by the decode thread on its way
            # to the new position
            self._releasedFrames.extend(self._decodeQueue)
            self._decodeQueue.clear()
            self._decodeSeekTarget = reqPTS
            self._decodeAtEnd = False
            self._decoderCondition.notify_all()

        self._decodeLanding = True
        self._lastFramePTS = None

        return reqPTS

    def _getFrame(self, reqPTS=0.0, blocking=True, deferDecoding=False):
        """Get a frame from the movie file, with the backends which decode
        ahead (`pyav` and `opencv`).

        Frames are taken from those the decode thread has decoded ahead.

        Parameters
        ----------
        reqPTS : float
            The presentation timestamp (PTS) of the frame to get in seconds.
        blocking : bool
            Whether to wait for the decode thread if it has yet to reach
            `reqPTS`. If `False`, returns `None` straight away instead (or the
            most recent frame before `reqPTS`, if one has been decoded).
        deferDecoding : bool
            Leave the decode thread be until `decodeAhead()` is called, rather
            than having it replace the frames taken straight away. See
            `getFrame()`.

        Returns
        -------
        tuple or None
            Video data (`_RGBFrameAdapter` or `_YUVFrameAdapter`), presentation
            timestamp (PTS), and status.

        """
        if self._decoderThread is None:
            return None

        # in case the last call deferred decoding and `decodeAhead()` has not
        # been called since
        self.decodeAhead()

        reqPTS = min(
            max(0.0, reqPTS),
            self._metadata.duration + self._metadata.frameInterval)

        frame = self._getFrameFromStore(reqPTS)
        if frame is not None:
            return frame

        # A time before the frame last shown, without a seek in between, is
        # the movie clock wrapping back round to the start for looping
        # playback. Carry on into the next pass if the decode thread has
        # queued it up already, and seek there if it hasn't.
        if self._lastFramePTS is not None and reqPTS < self._lastFramePTS:
            if not self._skipToNextPass():
                self._seek(reqPTS)

        frameInterval = self._metadata.frameInterval
        deadline = time.time() + defaultTimeout
        cond = self._decoderCondition
        found = None  # most recent decoded frame due by `reqPTS`
        reachedEnd = False

        with cond:
            while True:
                if self._decodeQueue:
                    head = self._decodeQueue[0]

                    if head is _END_OF_STREAM:
                        # The end only counts once no frame from before it is
                        # still to be shown. A seek landing here has gone past
                        # the end, and otherwise it's the end unless the movie
                        # is looping, which waits here for the movie clock to
                        # wrap round to the next pass.
                        if found is None and \
                                (self._decodeLanding or self._decodeAtEnd):
                            self._decodeQueue.popleft()
                            reachedEnd = True
                        break

                    img, pts = head
                    if pts <= reqPTS or (self._decodeLanding and found is None):
                        # The decode thread is not told there is room for
                        # another until `decodeAhead()`. Waking it here would
                        # have it decoding and converting a frame just as this
                        # one is copied to the GPU, and they compete for memory
                        # bandwidth, which roughly doubles the time taken by
                        # that copy for 4K frames.
                        self._decodeQueue.popleft()
                        self._refillPending = True
                        if found is not None:
                            # gone by already, so not shown after all
                            self._releasePending.append(found)
                        found = head
                        if reqPTS < pts + frameInterval:
                            break  # the frame for `reqPTS`
                        # This one has gone by already, but is the one to show
                        # unless one after it is due too.
                        continue

                    break  # the next frame is not due yet

                # The decode thread has yet to get this far. Without waiting,
                # the most recent frame found (if any) is the best there is.
                if self._decodeAtEnd or not blocking:
                    break

                remaining = deadline - time.time()
                if remaining <= 0:
                    logging.warning(
                        "{} did not decode a frame within {} seconds."
                        .format(self._decoderLib, defaultTimeout))
                    break

                # the decode thread may be waiting on room made above
                cond.notify_all()
                cond.wait(remaining)

        if reachedEnd:
            if self._streamEOFCallback is not None:
                self._streamEOFCallback()
            self._cleanUpFrameStore()
            self._seeking = False  # nothing left to seek to
            self._decodeLanding = False
            frameData = None
        elif found is None:
            frameData = None
        else:
            img, pts = found
            self._frameStore.append((img, pts, 'playing'))
            self._cleanUpFrameStore(reqPTS)
            self._decodeLanding = False
            # a landing frame can be a little ahead of the time asked for, and
            # that's not the movie clock going backwards when the next is
            # asked for
            self._lastFramePTS = min(pts, reqPTS)
            frameData = (img, pts, 'playing')

        if not deferDecoding:
            self.decodeAhead()

        return frameData

    # --------------------------------------------------------------------------
    # File I/O methods
    #

    def open(self):
        """Open the movie file for reading.

        Calling this will open the movie file and extract metadata to determine
        the frame rate, size, and duration of the movie.

        """
        logging.debug("Using decoder library: {}".format(self._decoderLib))
        self._open()
        
        # register the reader with the global list of open movie readers
        if self in _openMovieReaders:
            raise RuntimeError(
                'Movie reader already open for file: {}'.format(self._filename))
        
        self._playbackStatus = NOT_STARTED  # reset playback status
        
        _openMovieReaders.add(self)

    @property
    def isOpen(self):
        """Whether the movie file is open (`bool`).

        If `True`, the movie file is open and frames can be read from it. If
        `False`, the movie file is closed and no more frames can be read from
        it.

        """
        return self in _openMovieReaders

    def close(self):
        """Close the movie file or stream.

        This will unload the movie file and free any resources associated with 
        it.

        """
        self._freePlayer()  # free the player

        # clear frames from store
        self._cleanUpFrameStore()

        self._seeking = False

        self._metadata = None  # clear metadata

        # remove the reader from the global list of open movie readers
        if _openMovieReaders and self in _openMovieReaders:
            _openMovieReaders.remove(self)

    def _cleanUpFrameStore(self, keepAfterPTS=None):
        """Clean up the frame store.

        This function is called when the movie reader is closed. It clears the
        frame queue and the video segment buffer.

        Parameters
        ----------
        keepAfterPTS : float
            The presentation timestamp (PTS) to keep in the frame store. All
            frames before this PTS will be removed from the frame store. If
            `None`, all frames will be removed from the frame store.

        """
        if keepAfterPTS is None:
            keepFrom = len(self._frameStore)
        else:
            keepFrom = next(
                (i for i, (_, pts, _) in enumerate(self._frameStore)
                 if pts >= keepAfterPTS - self._metadata.frameInterval),
                0)  # keep them all if none are recent enough

        if self._decoderThread is not None:
            # freed by the decode thread, see `decodeAhead()`
            self._releasePending.extend(self._frameStore[:keepFrom])

        del self._frameStore[:keepFrom]

    def _getFrameFromStore(self, reqPTS):
        """Get a frame from the store.

        This function gets a frame from the store. The frame is returned as
        a Numpy array. The resulting array will be in the correct format to
        upload to OpenGL as a texture.

        Parameters
        ----------
        reqPTS : float
            The presentation timestamp (PTS) of the frame to get in seconds.

        Returns
        -------
        tuple or None
            If a frame is found, return a tuple containing the video data
            (`ndarray`), presentation timestamp (PTS), and status. The status 
            value may be backend specific. If no frame is found, return `None`.

        """
        if self._frameStore is None or not self._frameStore:
            return None
        
        for img, pts, status in self._frameStore:
            if pts <= reqPTS < pts + self._metadata.frameInterval:
                return (self._convertFrameToRGB(img), pts, status)
            
        return None  # no frame found
    
    def setStreamEOFCallback(self, callback):
        """Set a callback function to be called when the end of the movie is
        reached.

        Parameters
        ----------
        callback : callable or None
            The callback function to call when the end of the movie is reached.
            The function should take no arguments. If `None`, no callback
            function will be called.

        """
        if callback is None:
            self._streamEOFCallback = None
            return
        
        if not callable(callback):
            raise ValueError('Callback must be a callable function.')
        
        self._streamEOFCallback = callback

    def _frameIndexToTimestamp(self, frameIndex):
        """Convert a frame index to a presentation timestamp (PTS).

        This function converts a frame index to a presentation timestamp (PTS)
        in seconds. The frame index is the index of the frame in the movie file.

        Parameters
        ----------
        frameIndex : int
            The index of the frame in the movie file.

        Returns
        -------
        float
            The presentation timestamp (PTS) of the frame in seconds.

        """
        return frameIndex * self._metadata.frameInterval

    def _timestampToFrameIndex(self, pts):
        """Convert a presentation timestamp (PTS) to a frame index.

        This function converts a presentation timestamp (PTS) in seconds to a
        frame index. The frame index is the index of the frame in the movie 
        file.

        Parameters
        ----------
        pts : float
            The presentation timestamp (PTS) of the frame in seconds.

        Returns
        -------
        int
            The index of the frame in the movie file.

        """
        return int(pts / self._metadata.frameInterval)

    def pause(self, state=True):
        """Pause the movie reader.

        This function pauses the movie reader. If the movie reader is already
        paused, this function does nothing. If the movie reader is not open,
        this function raises a `ValueError`.

        Parameters
        ----------
        state : bool
            If `True`, the movie reader is paused. If `False`, the movie reader
            is not paused. The default is `True`.

        """
        # Backends which decode frames as they are asked for have no playback
        # clock of their own to pause. They decode ahead only as far as the
        # queue allows, then wait. `MovieStim` already stops requesting new
        # frames when paused, so there is nothing to do.
        pass

    def seek(self, pts):
        """Seek to a specific presentation timestamp (PTS) in the movie.

        This function seeks to a specific presentation timestamp (PTS) in the
        movie file. The decoder will begin decoding frames from the specified
        PTS. If the PTS is outside the range of the movie, the decoder will seek
        to the end of the movie.

        Seeking blocks the main thread until the desired frame is found.

        Parameters
        ----------
        pts : float
            The presentation timestamp (PTS) to seek to in seconds.

        """
        # cleared in `getFrame()` once the decoder produces a frame for the new
        # position, or when the stream ends before it can
        self._seeking = True

        self._seek(pts)

    def mute(self, state=True):
        """Mute the movie reader.

        This function mutes the movie reader. If the movie reader is already
        muted, this function does nothing. If the movie reader is not open,
        this function raises a `ValueError`.

        Parameters
        ----------
        state : bool
            If `True`, the movie reader is muted. If `False`, the movie reader
            is not muted. The default is `True`.

        """
        # Audio for backends which don't play it themselves is handled by a
        # separate `Sound` object owned by `MovieStim`, so there is nothing to
        # mute on the reader itself beyond noting the state asked for.
        self._muted = bool(state)

    @property
    def muted(self):
        """Whether the movie reader is muted (`bool`).

        For `ffpyplayer` and `vlc` this reflects the state of the underlying
        player. The `pyav` and `opencv` backends do not play audio themselves,
        so this reports the last state passed to `mute()`.

        """
        return self._muted

    @property
    def memoryUsed(self):
        """Get the amount of memory used for cache.

        Returns
        -------
        int
            The amount of memory used by the movie reader in bytes.

        """
        # sum of bytes used by video segments, including those decoded ahead
        totalFramesDecoded = len(self._frameStore)
        if self._decoderThread is not None:
            with self._decoderCondition:
                totalFramesDecoded += self._queuedFrameCount()
        # all frames are normalized to `FRAME_PIXEL_FORMAT`
        pixelSize = FRAME_BYTES_PER_PIXEL
        pixelCount = self._srcFrameSize[0] * self._srcFrameSize[1]

        return totalFramesDecoded * pixelCount * pixelSize
    
    def getFrame(self, pts=0.0, blocking=True, deferDecoding=False):
        """Get a frame from the movie file at the specified presentation
        timestamp.

        Parameters
        ----------
        pts : float or None
            The presentation timestamp (PTS) of the frame to get in seconds.
            Timestamps can be as precise as six decimal places.
        blocking : bool
            Whether to wait for the decoder to catch up if the frame is not
            ready yet. Pass `False` to return `None` straight away instead, so
            the caller can keep showing the previous frame and ask again later.
            All the backends decode ahead on their own schedule, so this
            applies to each of them.
        deferDecoding : bool
            If `True`, the decoder is left to replace the frames this takes
            when `decodeAhead()` is next called, rather than straight away.
            Call that once done with the frame, such as once it has been
            copied to the GPU, so that the decoder isn't competing with that
            for the CPU and memory bandwidth. Failing that, it happens at the
            start of the next call to this. Only affects `pyav` and
            `opencv`.

        Returns
        -------
        tuple or None
            Video data, or `None` if no frame is available.

        """
        frameData = self._getFrame(
            pts, blocking=blocking, deferDecoding=deferDecoding)

        if frameData is not None:
            # the decoder has caught up with the position asked for
            self._seeking = False

        return frameData

    def waitForDecodedFrames(self, timeout=defaultTimeout):
        """Wait for the decoder to have decoded as many frames ahead as it
        will, or to reach the end of the movie.

        The decoder fills its queue of frames as fast as it can, using every
        core it can, which is better done before playback starts than while
        it's under way, where it can hold up drawing. Does nothing for
        backends which don't decode ahead (`ffpyplayer` and `vlc`).

        Parameters
        ----------
        timeout : float
            Longest to wait in seconds.

        Returns
        -------
        bool
            `True` if the decoder has filled its queue (or reached the end of
            the movie), `False` if it hadn't by `timeout`.

        """
        if self._decoderThread is None:
            return True

        deadline = time.time() + timeout
        with self._decoderCondition:
            while not self._decodeAtEnd and \
                    self._queuedFrameCount() < self._decodeQueueDepth:
                remaining = deadline - time.time()
                if remaining <= 0 or not self._decoderThread.is_alive():
                    return False
                self._decoderCondition.wait(remaining)

        return True

    def decodeAhead(self):
        """Let the decoder replace the frames `getFrame()` has taken.

        This goes with `getFrame(deferDecoding=True)`, and does nothing
        otherwise. The decoder also frees the frames this reader is finished
        with, so that doing so doesn't hold up the caller either.

        """
        if self._decoderThread is None:
            return

        if not (self._refillPending or self._releasePending):
            return

        with self._decoderCondition:
            # Handed over and dropped here together while holding the lock,
            # which the decode thread needs to take them. Otherwise it could
            # drop its references first, leaving the last to go here.
            self._releasedFrames.extend(self._releasePending)
            self._releasePending.clear()
            self._decoderCondition.notify_all()

        self._refillPending = False

    @property
    def isSeeking(self):
        """Whether a seek has yet to produce a frame (`bool`).

        This is `True` between a call to `seek()` and the decoder delivering a
        frame for the new position. Backends which decode on demand usually
        satisfy a seek within the same call, so this is only observable when
        the decoder cannot keep up, such as with large frames or slow media.

        """
        return self._seeking
        
    def getSubtitle(self):
        """Get the subtitle from the movie file.

        This function returns the subtitle from the movie file. The subtitle is
        returned as a string. If no subtitle is available, this function returns
        `None`.

        Returns
        -------
        str or None
            The subtitle from the movie file. If no subtitle is available, this
            function returns `None`.

        """
        return ''

    def setVolume(self, volume):
        """Set the volume of the movie player.

        Parameters
        ----------
        volume : float
            The volume level to set, between 0.0 (mute) and 1.0 (full volume).

        """
        volume = min(1.0, max(0.0, float(volume)))
        
        logging.debug("Setting movie volume to: {}".format(volume))

        self._setVolume(volume)

    def __del__(self):
        """Close the movie file when the object is deleted.
        """
        self.close()
