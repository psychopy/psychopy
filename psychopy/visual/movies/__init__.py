#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'MovieStim',
    'backend',   # allow the user to get the current backend and set it
    'setBackend',
    'getBackend']


import ctypes
import functools
import math
import os.path
import sys
import threading
import weakref
from collections import deque
from fractions import Fraction
from pathlib import Path

import time

from psychopy import layout, prefs
from psychopy.tools.filetools import pathToString, defaultStim
from psychopy.visual.basevisual import (
    BaseVisualStim, DraggingMixin, ContainerMixin, ColorMixin
)
from psychopy.constants import (
    FINISHED, NOT_STARTED, PAUSED, PLAYING, STOPPED, SEEKING)
from psychopy import core
from psychopy.hardware import speaker, DeviceManager

from psychopy import logging
import numpy as np
import pyglet
pyglet.options['debug_gl'] = False
import psychopy.tools.pygletgl as GL

# threshold to stop reporting dropped frames
reportNDroppedFrames = 10

# time to wait for the movie decoder to respond
defaultTimeout = 5.0  # seconds

# Pixel format every decoder backend delivers frames in, and the number of bytes
# per pixel it uses. Frames are packed RGBA rather than RGB even though the
# movie has no use for the alpha channel, since many drivers have no native
# three-byte texture format and convert RGB uploads on the way to the GPU.
FRAME_PIXEL_FORMAT = 'rgba'
FRAME_BYTES_PER_PIXEL = 4

# Memory the `pyav` backend may use for frames decoded ahead of playback, and
# the bounds on how many frames that comes to. Decoding ahead on a background
# thread absorbs frames which take longer than usual to decode, such as the
# first after a seek while the decoder's own threads refill, rather than
# stalling the drawing loop. A 4K frame is ~33 MB, so this is 8 frames at 4K
# and the maximum at 1080p and below.
PYAV_DECODE_AHEAD_BYTES = 256 * 1024 ** 2
PYAV_DECODE_AHEAD_MIN_FRAMES = 2
PYAV_DECODE_AHEAD_MAX_FRAMES = 16

# How far back the `pyav` backend first goes when a seek lands on a frame past
# the position asked for, doubling each time it still does.
PYAV_SEEK_BACKOFF = 0.5  # seconds

# Placed in the `pyav` decode-ahead queue where the movie ends. When looping,
# frames from the start of the next pass are queued after it.
_PYAV_END_OF_STREAM = object()

# Samples (per channel) of a movie's audio track resampled at a time as it is
# decoded into memory. Resampling each decoded frame on its own is slower, a
# long track having tens of thousands of them, and resampling the whole track
# at once is slower still, besides needing a second copy of it in memory.
AUDIO_DECODE_BLOCK = 1 << 20

# Length in samples of the silence a movie's audio track starts out as, which
# opens the speaker so that the track can be decoded at the rate it plays at.
AUDIO_TRACK_PLACEHOLDER_SAMPLES = 128

# How much longer than the movie file says its audio track is to make room for,
# since it can come out a little longer once decoded. See `_AudioTrackLoader`.
AUDIO_TRACK_DURATION_MARGIN = 0.5  # seconds

# Largest denominator considered when working out how display refreshes line
# up with movie frames, see `_frameSampleOffset`. Large enough for the common
# pairings (e.g. 25 FPS at 60 Hz is 5/12, 30 FPS at 144 Hz is 5/24), and small
# enough that a refresh rate measured as 59.96 Hz still counts as 60.
FRAME_CADENCE_MAX_DENOMINATOR = 24

# constants for use with ffpyplayer
FFPYPLAYER_STATUS_EOF = 'eof'
FFPYPLAYER_STATUS_PAUSED = 'paused'

# How far the frame-counted playback position may differ from the position VLC
# reports before it is re-anchored to VLC's own clock. VLC reports its position
# in coarse steps (a quarter of a second or so), so this has to be well clear
# of that to be measuring drift rather than the size of those steps.
VLC_PTS_RESYNC_THRESHOLD = 1.0  # seconds

# How long to wait for VLC to present the frame at a position just seeked to.
# Seeking has to decode forward from the nearest keyframe before it can render
# anything, so it takes appreciably longer than a frame arriving during
# ordinary playback.
VLC_SEEK_TIMEOUT = 0.5  # seconds

# How many frames VLC must present after a seek before one of them is taken as
# the frame at the new position. The picture from the old position can still be
# presented once after the seek is issued, so more than one is needed.
VLC_SEEK_SETTLE_FRAMES = 2

# Longest to wait for a pause to work its way through VLC. Seeking before it
# has lands the player somewhere unrelated to the position asked for, so this
# is a correctness matter rather than a tidiness one.
VLC_PAUSE_SETTLE_TIMEOUT = 0.25  # seconds

# Shortest a pause is given to take hold, whatever the movie's frame rate.
# Waiting for VLC to present a frame is the signal that it has noticed the
# pause, but on its own that proved to come too early to seek on.
VLC_PAUSE_SETTLE_MIN = 0.05  # seconds

# recommended library for video decoding
PREFERRED_VIDEO_LIB = 'pyav'

# Movie decoder libraries which are recognized/supported by `MovieFileReader`
# and `MovieStim`.
SUPPORTED_VIDEO_LIBS = ('ffpyplayer', 'pyav', 'opencv', 'vlc')

# Keep track of movie readers here. This is used to close all movie readers
# when the main thread exits. We identify movie readers by hashing the filename
# they are presently reading from.

_openMovieReaders = set()

# Set the backend to use for movie decoding
backend = PREFERRED_VIDEO_LIB  # initial value 


def setBackend(movielib):
    """Set the backend to use for video decoding.

    This cannot be changed if there are open movie players.
    
    Parameters
    ----------
    movielib : str or None
        Backend to use for video decoding.

    """
    global backend

    if _openMovieReaders:
        raise RuntimeError(
            "Cannot change the movie backend while there are open movie readers."
        )

    # check if member of supported video libraries
    if movielib is None:
        backend = PREFERRED_VIDEO_LIB
    elif movielib in SUPPORTED_VIDEO_LIBS:
        backend = movielib
    else:
        raise RuntimeError(
            "Unknown movie library specified: {}. "
            "Supported libraries are: {}".format(
                movielib, ', '.join(SUPPORTED_VIDEO_LIBS))
        )


def getBackend():
    """Get the current backend used for video decoding.
    
    Returns
    -------
    str
        The current backend used for video decoding.

    """
    return backend


@functools.lru_cache(maxsize=16)
def _frameSampleOffset(framePeriod, frameInterval):
    """How far past the movie clock to look for the frame to show.

    The movie clock is read at each flip, and when playback starts it is on a
    flip too. Unless the display refresh period and the movie frame interval
    are unrelated, the clock then keeps landing on the same few positions
    within a frame, and when playback starts at the start of a frame, one of
    those is the very start of a frame. The slightest jitter then decides
    between that frame and the one before it, and the movie judders, repeating
    one frame and skipping the next. A 60 FPS movie on a 60 Hz display does
    this on every flip.

    Where the refresh period is `p / q` frame intervals in lowest terms, the
    clock lands on positions `frameInterval / q` apart. Looking half that far
    ahead keeps all of them as far from the start of a frame as they can be.

    Parameters
    ----------
    framePeriod : float
        Display refresh period in seconds.
    frameInterval : float
        Movie frame interval in seconds.

    Returns
    -------
    float
        Offset in seconds to add to the movie clock when choosing the frame to
        show, or `0.0` if either period is unknown.

    """
    if not (framePeriod and frameInterval) or \
            framePeriod < 0.0 or frameInterval < 0.0:
        return 0.0

    cadence = Fraction(framePeriod / frameInterval).limit_denominator(
        FRAME_CADENCE_MAX_DENOMINATOR)

    # Where the true denominator is larger than allowed above, positions are
    # closer together than the approximation suggests, so never look further
    # ahead than half a refresh. This only changes the result in that case.
    return min(frameInterval / (2 * cadence.denominator), framePeriod / 2.0)


# ------------------------------------------------------------------------------
# Classes
#

class MoviePlaybackError(Exception):
    """Exception raised when there is an error during movie playback."""
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"MoviePlaybackError: {self.message}"
    

class MovieFileNotFoundError(MoviePlaybackError):
    """Exception raised when a movie file is not found."""
    def __init__(self, filename):
        super().__init__(f"Movie file not found: {filename}")
        self.filename = filename

    def __str__(self):
        return f"MovieFileNotFoundError: {self.filename} does not exist."
    

class MovieFileFormatError(MoviePlaybackError):
    """Exception raised when a movie file format is not supported."""
    def __init__(self, filename):
        super().__init__(f"Movie file format not supported: {filename}")
        self.filename = filename

    def __str__(self):
        return f"MovieFileFormatError: {self.filename} is not a supported movie format."


class MovieAudioError(MoviePlaybackError):
    """Exception raised when there is an error with movie audio playback."""
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"MovieAudioError: {self.message}"

# ------------------------------------------------------------------------------

class MovieMetadata:
    """Class for storing metadata about a movie file.

    This class is used to store metadata about a movie file. This includes
    information about the video and audio tracks in the movie. Metadata is
    extracted from the movie file when the movie reader is opened.

    This class is not intended to be used directly by users. It is used
    internally by the `MovieFileReader` class to store metadata about the movie
    file being read.

    Parameters
    ----------
    filename : str
        The name (or path) of the movie file to extract metadata from.
    size : tuple
        The size of the movie in pixels (width, height).
    frameRate : float
        The frame rate of the movie in frames per second.
    duration : float
        The duration of the movie in seconds.
    colorFormat : str
        The color format of the movie (e.g. 'rgba', etc.).
    audioTrack : AudioMetadata or None
        The audio track metadata.
    
    """
    __slots__ = (
        '_filename', '_size', '_frameRate', '_duration', '_frameInterval',
        '_colorFormat', '_audioTrack')
    
    def __init__(self, filename, size, frameRate, duration, colorFormat, 
                 audioTrack=None):
        self._filename = filename
        self._size = size
        self._frameRate = frameRate
        self._duration = duration
        self._frameInterval = 1.0 / self._frameRate

        if isinstance(colorFormat, bytes):
            colorFormat = colorFormat.decode('utf-8')
        self._colorFormat = colorFormat

        # audio track metadata
        self._audioTrack = audioTrack

    def __repr__(self):
        return (
            f"MovieMetadata(filename={self.filename}, "
            f"size={self.size}, "
            f"frameRate={self.frameRate}, "
            f"duration={self.duration})")
        
    def __str__(self):
        return (
            f"MovieMetadata(filename={self.filename}, "
            f"size={self.size}, "
            f"frameRate={self.frameRate}, "
            f"duration={self.duration})")

    @property
    def filename(self):
        """The name (path) of the movie file (`str`).

        """
        return self._filename

    @property
    def size(self):
        """The size of the movie in pixels (`tuple`).

        """
        return self._size

    @property
    def frameRate(self):
        """The frame rate of the movie in frames per second (`float`).

        """
        return self._frameRate
    
    @property
    def frameInterval(self):
        """The interval between frames in the movie in seconds (`float`).

        """
        return self._frameInterval
    
    @property
    def duration(self):
        """The duration of the movie in seconds (`float`).

        """
        return self._duration

    @property
    def colorFormat(self):
        """The color format of the movie (`str`).

        """
        return self._colorFormat
    
    @property
    def audioTrack(self):
        """The audio track metadata (`AudioMetadata` or `None`).

        """
        return self._audioTrack


# Null movie metadata object, return a reference to this object instead of
# `None` when no metadata is present.
NULL_MOVIE_METADATA = MovieMetadata(
    filename=u'', 
    size=(-1, -1),
    frameRate=-1,
    duration=-1.0, 
    colorFormat=u'unknown', 
    audioTrack=None
)


class _RGBFrameAdapter:
    """Lightweight adapter exposing an `ffpyplayer`-like interface around raw
    RGBA frame bytes obtained from other decoder backends (currently
    `PyAV`, `OpenCV` and `VLC`).

    Higher level code (`MovieFileReader`, `MovieStim`) was originally written
    around `ffpyplayer`'s `Image` objects, which expose `.to_memoryview()`
    (returning a list whose first element has a `.memview` attribute) and
    `.get_pixel_format()`. Wrapping decoded frames from other backends in
    this adapter lets that code stay backend-agnostic instead of branching
    on `decoderLib` throughout.

    Parameters
    ----------
    rgbData : bytes or numpy.ndarray
        Raw RGBA pixel data, row-major, 4 bytes per pixel (see
        `FRAME_PIXEL_FORMAT`). An array is kept
        as-is (made contiguous first if needed) rather than converted to
        `bytes`, which would cost a whole-frame copy per decoded frame for no
        benefit; everything downstream reads this through the buffer protocol.

    """
    __slots__ = ['_data']

    def __init__(self, rgbData):
        if isinstance(rgbData, np.ndarray):
            rgbData = np.ascontiguousarray(rgbData)

        self._data = rgbData

    def to_memoryview(self):
        return [self]

    @property
    def memview(self):
        return self._data

    def get_pixel_format(self):
        return FRAME_PIXEL_FORMAT

    @property
    def size(self):
        """Size `(w, h)` of the frame in pixels (`tuple`), or `None` if the
        frame is raw bytes, which are always the movie's own size."""
        if isinstance(self._data, np.ndarray) and self._data.ndim == 3:
            return self._data.shape[1], self._data.shape[0]

        return None


class _ScheduledTime:
    """A fixed absolute time, to pass as `when` to `Sound.play()`.

    The `Sound` backends accept a window as `when`, and ask it for the time of
    its next flip in whichever clock they schedule playback with. This answers
    the same question for a fixed time, so that each backend converts it to its
    own clock the same way it would a flip time.

    Parameters
    ----------
    t : float
        Absolute time in seconds, on the clock `psychopy.clock.getTime()`
        reads.

    """
    __slots__ = ['_t']

    def __init__(self, t):
        self._t = t

    def getFutureFlipTime(self, targetTime=0, clock=None):
        # mirrors the clock conversion in `Window.getFutureFlipTime`, where
        # every clock's last reset time is an absolute time like `_t`
        if clock == 'ptb':
            return self._t
        elif clock == 'now':
            return self._t - core.monotonicClock.getLastResetTime() - \
                core.getTime()
        elif clock:
            return self._t - clock.getLastResetTime()

        return self._t - logging.defaultClock.getLastResetTime()


# Audio tracks being decoded in the background, which are stopped on exit so
# that PyAV isn't left decoding while the interpreter shuts down
_audioTrackLoaders = set()


class _AudioTrackLoader:
    """Decodes a movie's audio track into a `Sound` on a background thread.

    The `Sound` is given its full length of silence up front (see
    `Sound._allocateSamples`) and the track is written into it a block at a
    time as it decodes, which doesn't hold up drawing on the main thread.
    Samples past the end of that are kept here instead, as is the whole track
    if `nAllocated` is zero, for `MovieStim._finishAudioLoad` to hand over in
    one go.

    Parameters
    ----------
    container : av.container.InputContainer
        Movie file to decode from, which this takes over and closes once done.
    audioStream : av.audio.stream.AudioStream
        Track to decode.
    track : psychopy.sound.Sound
        Sound to decode into.
    sampleRate : int
        Sample rate in Hz to decode to.
    layout : str
        Channel layout to decode to.
    nAllocated : int
        Number of samples `track` was given by `_allocateSamples`, or zero if
        it wasn't.

    """
    def __init__(self, container, audioStream, track, sampleRate, layout,
                 nAllocated):
        self.track = track
        self.sampleRate = sampleRate
        self.nAllocated = nAllocated
        self.nSamples = 0  # decoded so far
        self.overflow = []  # samples decoded past `nAllocated`
        self.error = None  # raised while decoding, to be raised again later
        self.tStart = time.time()

        self._cancel = threading.Event()
        self._thread = threading.Thread(
            target=self._run, args=(container, audioStream, layout),
            name='AudioTrackLoader', daemon=True)
        _audioTrackLoaders.add(self)
        self._thread.start()

    @property
    def isDone(self):
        """`True` once decoding has finished, failed or been cancelled."""
        return not self._thread.is_alive()

    def wait(self, timeout=None):
        """Wait for decoding to finish. Returns `isDone`."""
        self._thread.join(timeout)

        return self.isDone

    def cancel(self):
        """Stop decoding, waiting for it to stop (within a frame or so)."""
        self._cancel.set()
        if not self.wait(defaultTimeout):
            logging.warning(
                "Audio track decoding did not stop within {} seconds.".format(
                    defaultTimeout))

    def _run(self, container, audioStream, layout):
        try:
            with container:
                MovieStim._decodeAudioTrack(
                    container, audioStream, self.sampleRate, layout=layout,
                    onBlock=self._onBlock, cancel=self._cancel)
        except BaseException as err:
            self.error = err  # for the thread waiting on this
        finally:
            _audioTrackLoaders.discard(self)

    def _onBlock(self, start, samples):
        nWritten = 0
        if start < self.nAllocated:
            nWritten = self.track._writeSamples(start, samples)
        if nWritten < len(samples):
            self.overflow.append(samples[nWritten:].copy())
        self.nSamples = start + len(samples)


class MovieFileReader:
    """Read movie frames from file.

    This class manages reading movie frames from a file or stream. The method
    used to read the movie frames is determined by the `decoderLib` parameter.

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
    * If `decoderLib='pyav'`, frames are decoded ahead of playback on a
      background thread, up to `PYAV_DECODE_AHEAD_BYTES` worth of them.
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
    def __init__(self, 
                 filename,
                 decoderLib=None,
                 decoderOpts=None):

        if decoderLib is None:
            decoderLib = PREFERRED_VIDEO_LIB

        self._filename = filename
        self._decoderLib = decoderLib
        self._decoderOpts = {} if decoderOpts is None else decoderOpts

        # thread for the reader
        self._player = None  # player interface object (ffpyplayer)

        # FFPyPlayer specific state
        # PTS of an in-flight seek, used to discard frames still arriving from
        # the pre-seek position (`None` when no seek is pending)
        self._pendingSeekPTS = None
        # cached `SWScale` instance, rebuilt only when the source pixel format
        # or frame size changes
        self._swsContext = None
        self._swsContextKey = None

        # PyAV specific state
        self._container = None  # av.container.InputContainer
        self._videoStream = None  # av video stream being decoded
        self._packetIterator = None  # generator yielding decoded video frames
        # Frames are decoded ahead of playback on a background thread, which
        # has sole use of the container and stream above from when it starts
        # until it is stopped (see `_runPyAVDecoder`). The state shared with
        # it below is guarded by `_pyavCondition`.
        self._pyavThread = None
        self._pyavCondition = threading.Condition()
        # decoded frames as `(frame, pts)` waiting to be shown, oldest first,
        # with `_PYAV_END_OF_STREAM` where the movie ends
        self._pyavQueue = deque()
        self._pyavQueueDepth = PYAV_DECODE_AHEAD_MIN_FRAMES  # set on open
        self._pyavSeekTarget = None  # position the thread is to seek to
        # Bumped on every seek, so the thread can tell that a frame it has
        # just decoded is from before the seek and drop it
        self._pyavGeneration = 0
        self._pyavAtEnd = False  # thread is idle at the end of the movie
        self._pyavStopping = False  # thread has been asked to exit
        # Frames this reader is finished with, which the decode thread drops so
        # that freeing them (~2 ms each at 4K) doesn't hold up drawing. They
        # are collected by the thread calling `getFrame()` in
        # `_pyavReleasePending`, which only it uses, and handed over to
        # `_pyavReleased` (guarded by `_pyavCondition`) by `decodeAhead()`.
        self._pyavReleasePending = []
        self._pyavReleased = []
        # `getFrame()` has taken frames from the queue without letting the
        # decode thread know yet, see `decodeAhead()`
        self._pyavRefillPending = False
        # Used only by the thread calling `getFrame()`. The first frame after
        # a seek or a loop wrapping round is shown even if it is a little
        # ahead of the time asked for, as when a stream starts a frame or two
        # in. `_pyavLastPTS` is the time the last frame was shown for, to
        # recognise the movie clock wrapping back round to the start.
        self._pyavLanding = False
        self._pyavLastPTS = None

        # OpenCV specific state
        self._capture = None  # cv2.VideoCapture object

        # VLC specific state
        self._vlcInstance = None  # vlc.Instance
        self._vlcPlayer = None  # vlc.MediaPlayer
        self._vlcMedia = None  # vlc.Media being played
        self._vlcEventManager = None  # vlc.EventManager for the player
        # Guards the frame buffers below, which VLC's decoding thread writes
        # into through the video callbacks while this thread reads them out.
        self._vlcFrameLock = threading.RLock()
        # `True` between the lock and unlock callbacks, so that an unlock
        # arriving for a lock which bailed out cannot release a lock it never
        # took
        self._vlcLockHeld = False
        # VLC decodes into one buffer while the other is read from, the two
        # being swapped once a frame is complete (see `_makeVLCCallbacks`)
        self._vlcWriteBuffer = None
        self._vlcReadBuffer = None
        self._vlcFrameNBytes = 0  # bytes of a buffer a frame occupies
        self._vlcFrameReady = False  # a frame is waiting to be picked up
        # Counts every frame VLC presents, including the repeats of the current
        # picture it keeps sending while paused. Used to tell that VLC has
        # moved on rather than to time anything.
        self._vlcDisplayCount = 0
        # display count a seek has to reach before the picture is taken to be
        # the one at the new position (`None` when no seek is outstanding)
        self._vlcSeekSettleAt = None
        self._vlcStreamEnded = False  # set by the end-of-stream event callback
        self._vlcPaused = True  # whether VLC is presently producing frames
        # when the current pause was asked for, and the frame count at that
        # point, so that `_vlcPauseHasSettled` can tell whether it has had time
        # to take hold (`_vlcPausedAt` is `None` while playing)
        self._vlcPausedAt = None
        self._vlcPausedAtCount = 0
        # position a seek is waiting to be applied at, see `_seekVLC`
        self._vlcPendingSeekPTS = None
        # Playback position is counted in frames from a known point in the
        # movie rather than read from VLC every frame, see `_ptsForNextVLCFrame`
        self._vlcPTSAnchor = 0.0  # movie time the count below starts from
        self._vlcFramesSinceAnchor = 0
        # the video callbacks, which must stay referenced while VLC holds them
        self._vlcLockCb = self._vlcUnlockCb = self._vlcDisplayCb = None

        # last requested mute state, used by backends which have no mute state
        # of their own to report
        self._muted = False

        # Size frames are scaled down to as they're decoded, or `None` for their
        # own, and the `swscale` filter to do it with. Kept as one tuple so
        # that the decode thread reads a consistent pair. See
        # `setOutputFrameSize`.
        self._outputFrameFormat = (None, 'AREA')

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
        were decoded at. Only `pyav` scales frames, the other backends always
        give them at their own size.

        Parameters
        ----------
        size : ArrayLike or None
            Largest size `(w, h)` in pixels to give frames at, or `None` to
            keep their own size.
        interpolation : str
            `swscale` filter to scale frames with, such as `'AREA'` (box
            filter, the default) or `'POINT'` (nearest neighbour).

        """
        if size is not None:
            size = tuple(max(1, int(math.ceil(abs(val)))) for val in size)

        self._outputFrameFormat = (size, interpolation)

        if self._decoderLib == 'pyav' and self._srcFrameSize[0] > 0:
            # as many frames as fit in the budget at the new size
            with self._pyavCondition:
                self._pyavQueueDepth = self._getPyAVQueueDepth()
                self._pyavCondition.notify_all()

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
        if self._decoderLib == 'ffpyplayer':
            return self._getVolumeFFPyPlayer()
        elif self._decoderLib == 'vlc':
            return self._getVolumeVLC()
        elif self._decoderLib in ('pyav', 'opencv'):
            # neither backend performs audio playback of its own; volume is
            # managed externally by `MovieStim` via its extracted audio track.
            return self._decoderOpts.get('volume', 0.0)
        else:
            raise NotImplementedError(
                'Volume control is not implemented for this decoder library.')

    @volume.setter
    def volume(self, value):
        """Set the volume level of the movie player (`float`).

        This is only valid after calling `open()`. If not, the value is `0.0`.

        """
        if self._decoderLib == 'ffpyplayer':
            self._setVolumeFFPyPlayer(value)
        elif self._decoderLib == 'vlc':
            self._setVolumeVLC(value)
        elif self._decoderLib in ('pyav', 'opencv'):
            # no-op; audio volume for these backends is controlled through the
            # separate `Sound` object managing the extracted audio track
            self._decoderOpts['volume'] = value
        else:
            raise NotImplementedError(
                'Volume control is not implemented for this decoder library.')

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
    # Backend-specific reader interface methods
    # 
    # These methods are used to interface with the backend specified by the
    # `decoderLib` parameter. The methods are not intended to be used directly
    # by users. In the future, these will likely be moved into separate classes
    # for each backend. Methods are suffixed with the backend name and are 
    # selected based on the `decoderLib` parameter inside public methods which 
    # relate to them (e.g. `open()` will call `_openFFPyPlayer()` if the backend
    # is `ffpyplayer`).
    #
    
    # --------------------------------------------------------------------------
    # FFPyPlayer specific methods
    # 

    def _openFFPyPlayer(self):
        """Open a movie reader using FFPyPlayer.

        This function opens the movie file and extracts metadata about the movie
        file. Metadata will be accessible via the `getMetadata()` method.

        """
        # import in the class too avoid hard dependency on ffpyplayer
        try:
            from ffpyplayer.player import MediaPlayer
        except ImportError:
            raise ImportError(
                'The `ffpyplayer` library is required to read movie files with '
                '`decoderLib=ffpyplayer`. Note that `ffpyplayer` is not '
                'available on Python 3.14 and later; use `decoderLib=pyav` '
                'instead (this is the default on those Python versions).')

        logging.info("Opening movie file: {}".format(self._filename))

        # Using sync to audio since it allows us to poll the player for frames
        # any number of frames and allows the audio to be played at the correct 
        # rate if using the SDL2 interface
        syncMode = 'audio' 

        # default options
        defaultFFOpts = {
            'paused': True,
            'sync': syncMode,  # always use audio sync
            'an': False,
            'volume': 0.0,  # mute
            'loop': 1,  # number of replays (0=infinite, 1=once, 2=twice, etc.)
            'infbuf': True,
            'out_fmt': FRAME_PIXEL_FORMAT  # so frames need no conversion here
        }

        # merge user settings with defaults, user settings take precedence
        defaultFFOpts.update(self._decoderOpts)
        self._decoderOpts = defaultFFOpts

        # create media player interface
        self._player = MediaPlayer(
            self._filename,
            ff_opts=self._decoderOpts)

        self._player.set_mute(True)  # mute the player first
        self._player.set_pause(False)

        # Get metadata and 'warm-up' the player to ensure it is responsive 
        # before we start decoding frames.

        # wait for valid metadata to be available
        logging.debug("Waiting for movie metadata...")
        startTime = time.time()
        while time.time() - startTime < defaultTimeout:  # 5 second timeout
            movieMetadata = self._player.get_metadata()
            # keep calling until we get a valid frame size
            if movieMetadata['src_vid_size'] != (0, 0):
                break
            time.sleep(0.001)  # yield, don't spin the CPU while waiting
        else:
            raise RuntimeError(
                'FFPyPlayer failed to extract metadata from the movie. Check '
                'the movie file and decoder options.')

        # warmup, takes a while before the video starts playing
        startTime = time.time()
        while time.time() - startTime < defaultTimeout:  # 5 second timeout
            frame, _ = self._player.get_frame()
            if frame is not None:
                break
            time.sleep(0.001)  # yield, don't spin the CPU while waiting
        else:
            raise RuntimeError(
                'FFPyPlayer failed to start decoding the movie. Check the '
                'movie file and decoder options.')
        
        # go back to first frame
        self._player.set_pause(True)  # pause the player again
        self._player.set_mute(False)  # unmute the player

        # seek to the beginning of the movie
        self._player.seek(0.0, relative=False, accurate=False)
        
        # wait until the player actually seeks to zero, this gets its own
        # timeout budget since the warm-up above may have consumed most of it
        startTime = time.time()
        while time.time() - startTime < defaultTimeout:
            curPts = self._player.get_pts()
            if abs(curPts) < 1e-6:
                break
            time.sleep(0.001)  # wait a bit before checking again
        else:
            logging.warning(
                "FFPyPlayer did not report seeking back to the start of the "
                "movie within {} seconds; the first frame presented may not "
                "be the first frame of the movie.".format(defaultTimeout))

        # compute frame rate and interval
        numer, denom = movieMetadata['frame_rate']
        if not denom or not numer:
            raise RuntimeError(
                'FFPyPlayer could not determine the frame rate of the movie '
                'file (reported {}/{}).'.format(numer, denom))
        frameRate = numer / denom

        duration = movieMetadata['duration']
        if not duration > 0.0:
            raise RuntimeError(
                'FFPyPlayer could not determine the duration of the movie '
                'file (reported {}).'.format(duration))

        self._frameInterval = 1.0 / frameRate
        # always allow at least one retry, `int()` alone truncates to zero for
        # movies faster than 1000 fps
        self._maxGetFrameAttempts = max(1, int(self._frameInterval / 0.001))
        self._frameRate = frameRate
        self._srcFrameSize = movieMetadata['src_vid_size']
        self._duration = duration

        # Report the pixel format frames are actually delivered in rather
        # than `src_pix_fmt` (the format of the *source* stream). Frames are
        # always converted to `FRAME_PIXEL_FORMAT`, whatever `out_fmt` the user
        # passed, so reporting the source format here would disagree with
        # what `getFrame()` returns and with the other decoder backends.
        img, curPts = frame
        initialFrameRGB = self._convertFrameToRGBFFPyPlayer(img)
        deliveredPixFmt = initialFrameRGB.get_pixel_format()

        # populate the metadata object with the movie metadata we got
        self._metadata = MovieMetadata(
            self._filename,
            movieMetadata['src_vid_size'],
            frameRate,
            duration,
            deliveredPixFmt)

        logging.debug("Movie metadata: {}".format(movieMetadata))

        # store the frame we got during warmup so it shows when the movie is
        # stopped+idle but not paused
        self._frameStore.append(
            (initialFrameRGB, curPts, FFPYPLAYER_STATUS_PAUSED))
    
    def _seekFFPyPlayer(self, reqPTS):
        """FFPyPlayer specific seek routine.

        This is called by `seek()` when the `ffpyplayer` backend is in use. 
        Video decoding will be paused after calling this function.

        Parameters
        ----------
        reqPTS : float
            The presentation timestamp (PTS) to seek to in seconds.

        Returns
        -------
        float
            The presentation timestamp (PTS) requested in seconds. FFPyPlayer
            seeks asynchronously, so the decoder may still be delivering frames
            from the previous position when this returns; `_getFrameFFPyPlayer`
            discards those before returning a frame.

        """
        reqPTS = min(max(0.0, reqPTS), self._metadata.duration)

        if self._player is None:
            return
        
        # clear the frame store
        self._cleanUpFrameStore()

        # seek to the desired PTS
        self._player.seek(
            reqPTS, 
            relative=False, 
            seek_by_bytes=False, 
            accurate=True)

        # Mark the seek as in-flight. `get_pts()` reports the *requested*
        # position as soon as the seek is issued, so it cannot tell us when the
        # decoder has caught up; instead `_getFrameFFPyPlayer` drops frames
        # that arrive from ahead of this target until the seek lands.
        self._pendingSeekPTS = reqPTS

        return reqPTS
    
    def _convertFrameToRGBFFPyPlayer(self, frame):
        """Convert a frame to RGBA format.

        This function converts a frame to `FRAME_PIXEL_FORMAT`. The player is
        asked for frames in that format already (see `out_fmt` in
        `_openFFPyPlayer`), so this only converts if a user-supplied `out_fmt`
        overrode it. The result will be in the correct format to upload to
        OpenGL as a texture.

        Parameters
        ----------
        frame : FFPyPlayer frame
            The frame to convert.

        Returns
        -------
        ffpyplayer.pic.Image
            The converted frame in RGBA format.

        """
        srcPixFmt = frame.get_pixel_format()

        if srcPixFmt == FRAME_PIXEL_FORMAT:  # already converted
            return frame

        from ffpyplayer.pic import SWScale

        # Use the frame's own dimensions rather than the metadata size, which
        # can disagree with what the decoder actually emits.
        width, height = frame.get_size()

        # Building an `SWScale` allocates a colour conversion context, so reuse
        # it across frames and only rebuild when the format or size changes.
        contextKey = (srcPixFmt, width, height)
        if self._swsContext is None or self._swsContextKey != contextKey:
            self._swsContext = SWScale(
                width, height, srcPixFmt, ofmt=FRAME_PIXEL_FORMAT)
            self._swsContextKey = contextKey

        return self._swsContext.scale(frame)

    # --------------------------------------------------------------------------
    # PyAV specific methods
    #

    def _openPyAV(self):
        """Open a movie reader using PyAV.

        This function opens the movie file using the `av` package and extracts
        metadata about the movie file. Metadata will be accessible via the
        `getMetadata()` method.

        Once the first frame has been read, frames are decoded ahead of
        playback on a background thread (see `_runPyAVDecoder`), so that a
        frame which is slow to decode does not hold up drawing.

        """
        logging.info("Using PyAV for reading movie frames.")
        try:
            import av
        except ImportError:
            raise ImportError(
                'The `av` (PyAV) library is required to read movie files with '
                '`decoderLib=pyav`. Install it with `pip install av`.')

        logging.info("Opening movie file: {}".format(self._filename))

        openOpts = self._decoderOpts.get('options', {})
        self._container = av.open(self._filename, options=openOpts)

        videoStream = next(
            (s for s in self._container.streams if s.type == 'video'), None)
        
        if videoStream is None:
            self._container.close()
            self._container = None
            raise MovieFileFormatError(self._filename)

        # use multi-threaded decoding where available for faster frame access
        try:
            videoStream.thread_type = 'AUTO'
        except Exception:
            pass  # not fatal if the codec doesn't support threaded decoding

        self._videoStream = videoStream

        # determine the frame rate; prefer the averaged rate reported by the
        # stream, falling back to the guessed rate if unavailable
        rateFraction = videoStream.average_rate or videoStream.guessed_rate
        if not rateFraction:
            raise RuntimeError(
                'PyAV could not determine the frame rate of the movie file.')
        frameRate = float(rateFraction)

        self._frameInterval = 1.0 / frameRate
        self._maxGetFrameAttempts = max(1, int(self._frameInterval / 0.001))
        self._frameRate = frameRate

        width = videoStream.codec_context.width
        height = videoStream.codec_context.height
        self._srcFrameSize = (width, height)

        # determine duration in seconds, preferring the stream's own duration
        if videoStream.duration is not None and videoStream.time_base is not None:
            duration = float(videoStream.duration * videoStream.time_base)
        elif self._container.duration is not None:
            duration = float(self._container.duration / av.time_base)
        else:
            raise RuntimeError(
                'PyAV could not determine the duration of the movie file.')
        self._duration = duration

        self._metadata = MovieMetadata(
            self._filename,
            (width, height),
            frameRate,
            duration,
            FRAME_PIXEL_FORMAT)

        logging.debug("Movie metadata: {}".format(repr(self._metadata)))

        # start the decode generator and warm up by grabbing the first frame
        self._packetIterator = self._container.decode(video=0)

        startTime = time.time()
        firstFrame = None
        while time.time() - startTime < defaultTimeout:
            try:
                firstFrame = next(self._packetIterator)
                break
            except StopIteration:
                break
        if firstFrame is None:
            raise RuntimeError(
                'PyAV failed to decode the first frame of the movie. Check '
                'the movie file.')

        # Show the first frame from the very start of the movie. Streams often
        # start a frame or two in (when B-frames delay the first one), which
        # would otherwise leave nothing to show before it.
        initialFrameRGB = self._convertFrameToRGBPyAV(firstFrame)
        self._frameStore.append((initialFrameRGB, 0.0, 'paused'))
        self._pyavLastPTS = 0.0

        # Carry on decoding from here in the background. Seeking back to the
        # start instead would empty the decoder, which with frame threading
        # then takes several frames' worth of decoding to produce one again
        # (~50 ms at 4K), and playback would start by waiting on that.
        self._pyavQueueDepth = self._getPyAVQueueDepth()
        self._startPyAVDecoder()

    def _getPyAVQueueDepth(self):
        """Number of frames for the `pyav` decode thread to decode ahead
        (`int`), as many as fit in `PYAV_DECODE_AHEAD_BYTES` at the size they
        are decoded at."""
        width, height = self._srcFrameSize
        outputSize = self._outputFrameFormat[0]
        if outputSize is not None:
            width, height = min(width, outputSize[0]), min(height, outputSize[1])
        frameBytes = max(1, width * height * FRAME_BYTES_PER_PIXEL)

        return min(
            max(PYAV_DECODE_AHEAD_BYTES // frameBytes,
                PYAV_DECODE_AHEAD_MIN_FRAMES),
            PYAV_DECODE_AHEAD_MAX_FRAMES)

    def _seekPyAV(self, reqPTS):
        """PyAV specific seek routine.

        The seek is handed to the decode thread, which seeks the container and
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

        if self._container is None or self._videoStream is None:
            return

        self._cleanUpFrameStore()

        with self._pyavCondition:
            self._pyavGeneration += 1
            # all from before the seek, freed by the decode thread on its way
            # to the new position
            self._pyavReleased.extend(self._pyavQueue)
            self._pyavQueue.clear()
            self._pyavSeekTarget = reqPTS
            self._pyavAtEnd = False
            self._pyavCondition.notify_all()

        self._pyavLanding = True
        self._pyavLastPTS = None

        return reqPTS

    def _startPyAVDecoder(self):
        """Start the thread which decodes frames ahead of playback.

        From here until `_stopPyAVDecoder()` the container and video stream
        belong to that thread, and must not be used from any other.

        """
        with self._pyavCondition:
            self._pyavQueue.clear()
            self._pyavReleased.clear()
            self._pyavSeekTarget = None
            self._pyavAtEnd = False
            self._pyavStopping = False

        self._pyavReleasePending.clear()
        self._pyavRefillPending = False

        self._pyavThread = threading.Thread(
            target=self._runPyAVDecoder,
            name='PyAVDecoder({})'.format(os.path.basename(self._filename)),
            daemon=True)
        self._pyavThread.start()

    def _stopPyAVDecoder(self):
        """Stop the decode thread and drop any frames it decoded.

        Returns
        -------
        bool
            `True` if the thread has stopped (or was never started), after
            which the container is free to be closed.

        """
        if self._pyavThread is None:
            return True

        with self._pyavCondition:
            self._pyavStopping = True
            self._pyavCondition.notify_all()

        # it only checks between frames, so this waits out at most one decode
        self._pyavThread.join(timeout=defaultTimeout)
        if self._pyavThread.is_alive():
            logging.warning(
                "PyAV decode thread for {} did not stop within {} seconds."
                .format(self._filename, defaultTimeout))
            return False

        self._pyavThread = None
        with self._pyavCondition:
            self._pyavQueue.clear()
            self._pyavReleased.clear()

        self._pyavReleasePending.clear()
        self._pyavRefillPending = False

        return True

    def _queuedPyAVFrameCount(self):
        """Number of decoded frames waiting in the queue (`int`). Must be
        called holding `_pyavCondition`."""
        return sum(
            1 for item in self._pyavQueue if item is not _PYAV_END_OF_STREAM)

    def _runPyAVDecoder(self):
        """Decode frames ahead of playback. This runs on the decode thread.

        Frames are decoded and converted until `_pyavQueueDepth` of them are
        waiting, then this waits for `getFrame()` to take some. Seeks are
        carried out here too, since only this thread may use the container.
        At the end of the movie `_PYAV_END_OF_STREAM` is queued, and when
        looping, decoding carries on from the start straight away so that the
        next pass is ready by the time playback wraps round to it.

        """
        cond = self._pyavCondition
        timeBase = self._videoStream.time_base
        frameInterval = self._frameInterval
        seekTarget = None  # frames from before this are skipped after a seek
        # Where the container was last seeked to, and how much further back to
        # go if the first frame from there turns out to be past `seekTarget`
        # (`None` once a frame from at or before it has been reached).
        seekFrom = 0.0
        seekBackoff = None

        with cond:
            generation = self._pyavGeneration

        while True:
            with cond:
                while not self._pyavStopping and \
                        self._pyavSeekTarget is None and \
                        not self._pyavReleased and \
                        (self._pyavAtEnd or self._queuedPyAVFrameCount() >=
                            self._pyavQueueDepth):
                    cond.wait()

                if self._pyavStopping:
                    return

                released = self._pyavReleased  # dropped below
                self._pyavReleased = []

                seekNow = self._pyavSeekTarget is not None
                if seekNow:
                    seekTarget = seekFrom = self._pyavSeekTarget
                    seekBackoff = PYAV_SEEK_BACKOFF
                    self._pyavSeekTarget = None
                    generation = self._pyavGeneration

                # woken only to free frames, with nowhere to put another
                noRoom = not seekNow and (
                    self._pyavAtEnd or self._queuedPyAVFrameCount() >=
                    self._pyavQueueDepth)

            # Free the frames handed over here, outside the lock, rather than
            # on the thread drawing them where it would hold up a frame.
            del released
            if noRoom:
                continue

            failed = False
            try:
                if seekNow:
                    self._seekContainerPyAV(seekFrom)

                avFrame = next(self._packetIterator, None)
            except Exception as err:
                # Treat a corrupt or truncated file as the end of the movie,
                # rather than leave playback waiting on frames that will never
                # come.
                logging.error(
                    "PyAV failed to decode {}: {}".format(self._filename, err))
                avFrame = None
                failed = True

            if avFrame is None:  # reached the end of the movie
                # infinite looping is requested when `loop` is explicitly `0`,
                # mirroring the `ffpyplayer` convention used elsewhere
                loopInfinitely = \
                    self._decoderOpts.get('loop', 1) == 0 and not failed
                with cond:
                    if generation != self._pyavGeneration:
                        continue  # seeked since, so this is not the end now
                    self._pyavQueue.append(_PYAV_END_OF_STREAM)
                    self._pyavAtEnd = not loopInfinitely
                    cond.notify_all()

                if loopInfinitely:
                    seekTarget = None
                    try:
                        self._seekContainerPyAV(0.0)
                    except Exception as err:
                        logging.error(
                            "PyAV failed to rewind {} to loop it: {}".format(
                                self._filename, err))
                        with cond:
                            self._pyavAtEnd = True
                continue

            pts = float(avFrame.pts * timeBase) \
                if avFrame.pts is not None else 0.0

            if seekTarget is not None:
                if seekBackoff is not None:
                    if pts > seekTarget and seekFrom > 0.0:
                        # The container seeks to keyframes by decode time, and
                        # with B-frames the one it lands on can be shown after
                        # the position asked for, leaving the frames up to it
                        # unreachable from there. Go back further and decode
                        # forward instead.
                        seekFrom = max(0.0, seekFrom - seekBackoff)
                        seekBackoff *= 2
                        try:
                            self._seekContainerPyAV(seekFrom)
                        except Exception as err:
                            logging.error("PyAV failed to seek {}: {}".format(
                                self._filename, err))
                            seekBackoff = None
                        continue
                    seekBackoff = None  # reached a frame from before it

                if pts + frameInterval <= seekTarget:
                    continue  # from before the position seeked to
                seekTarget = None

            frame = self._convertFrameToRGBPyAV(avFrame)

            with cond:
                if generation == self._pyavGeneration:  # else seeked since
                    self._pyavQueue.append((frame, pts))
                    cond.notify_all()

    def _seekContainerPyAV(self, pts):
        """Seek the container to the keyframe at or before `pts` (seconds).
        Only the decode thread may call this once it has been started."""
        self._container.seek(
            int(pts / self._videoStream.time_base), stream=self._videoStream,
            any_frame=False, backward=True)
        # decoding must restart after a container-level seek
        self._packetIterator = self._container.decode(video=0)

    def _skipToNextPassPyAV(self):
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

        with self._pyavCondition:
            if not any(item is _PYAV_END_OF_STREAM for item in self._pyavQueue):
                return False

            while True:
                item = self._pyavQueue.popleft()
                if item is _PYAV_END_OF_STREAM:
                    break
                # the rest of the pass being left, for the decode thread to free
                self._pyavReleased.append(item)
            self._pyavCondition.notify_all()

        self._cleanUpFrameStore()
        self._pyavLanding = True
        self._pyavLastPTS = None

        return True

    def _convertFrameToRGBPyAV(self, frame):
        """Convert a PyAV frame to RGBA format.

        Parameters
        ----------
        frame : av.VideoFrame or `_RGBFrameAdapter`
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

        # Scaled down in the same `swscale` pass as the conversion, which costs
        # little more than the conversion alone, see `setOutputFrameSize`
        outputSize, interpolation = self._outputFrameFormat
        if outputSize is not None:
            width = min(outputSize[0], frame.width)
            height = min(outputSize[1], frame.height)
            if (width, height) != (frame.width, frame.height):
                return _RGBFrameAdapter(frame.to_ndarray(
                    format=FRAME_PIXEL_FORMAT, width=width, height=height,
                    interpolation=interpolation))

        return _RGBFrameAdapter(frame.to_ndarray(format=FRAME_PIXEL_FORMAT))

    def _getFramePyAV(self, reqPTS=0.0, blocking=True, deferDecoding=False):
        """Get a frame from the movie file using PyAV.

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
            Video data (`_RGBFrameAdapter`), presentation timestamp (PTS), and
            status.

        """
        if self._container is None:
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
        if self._pyavLastPTS is not None and reqPTS < self._pyavLastPTS:
            if not self._skipToNextPassPyAV():
                self._seekPyAV(reqPTS)

        frameInterval = self._metadata.frameInterval
        deadline = time.time() + defaultTimeout
        cond = self._pyavCondition
        found = None  # most recent decoded frame due by `reqPTS`
        reachedEnd = False

        with cond:
            while True:
                if self._pyavQueue:
                    head = self._pyavQueue[0]

                    if head is _PYAV_END_OF_STREAM:
                        # The end only counts once no frame from before it is
                        # still to be shown. A seek landing here has gone past
                        # the end, and otherwise it's the end unless the movie
                        # is looping, which waits here for the movie clock to
                        # wrap round to the next pass.
                        if found is None and \
                                (self._pyavLanding or self._pyavAtEnd):
                            self._pyavQueue.popleft()
                            reachedEnd = True
                        break

                    img, pts = head
                    if pts <= reqPTS or (self._pyavLanding and found is None):
                        # The decode thread is not told there is room for
                        # another until `decodeAhead()`. Waking it here would
                        # have it decoding and converting a frame just as this
                        # one is copied to the GPU, and they compete for memory
                        # bandwidth, which roughly doubles the time taken by
                        # that copy for 4K frames.
                        self._pyavQueue.popleft()
                        self._pyavRefillPending = True
                        if found is not None:
                            # gone by already, so not shown after all
                            self._pyavReleasePending.append(found)
                        found = head
                        if reqPTS < pts + frameInterval:
                            break  # the frame for `reqPTS`
                        # This one has gone by already, but is the one to show
                        # unless one after it is due too.
                        continue

                    break  # the next frame is not due yet

                # The decode thread has yet to get this far. Without waiting,
                # the most recent frame found (if any) is the best there is.
                if self._pyavAtEnd or not blocking:
                    break

                remaining = deadline - time.time()
                if remaining <= 0:
                    logging.warning(
                        "PyAV did not decode a frame within {} seconds."
                        .format(defaultTimeout))
                    break

                # the decode thread may be waiting on room made above
                cond.notify_all()
                cond.wait(remaining)

        if reachedEnd:
            if self._streamEOFCallback is not None:
                self._streamEOFCallback()
            self._cleanUpFrameStore()
            self._seeking = False  # nothing left to seek to
            self._pyavLanding = False
            frameData = None
        elif found is None:
            frameData = None
        else:
            img, pts = found
            self._frameStore.append((img, pts, 'playing'))
            self._cleanUpFrameStore(reqPTS)
            self._pyavLanding = False
            # a landing frame can be a little ahead of the time asked for, and
            # that's not the movie clock going backwards when the next is
            # asked for
            self._pyavLastPTS = min(pts, reqPTS)
            frameData = (img, pts, 'playing')

        if not deferDecoding:
            self.decodeAhead()

        return frameData

    # --------------------------------------------------------------------------
    # OpenCV specific methods
    #

    def _openOpenCV(self):
        """Open a movie reader using OpenCV.

        This function opens the movie file using the `cv2` package and extracts
        metadata about the movie file. Metadata will be accessible via the
        `getMetadata()` method.

        Like `PyAV`, OpenCV pulls frames on demand (there is no background
        decode thread as with `ffpyplayer`) and provides no audio playback of
        its own. OpenCV reports frame positions as indices rather than
        timestamps, so presentation timestamps are derived from the frame index
        and the frame rate. This assumes a constant frame rate; use `pyav` or
        `ffpyplayer` for variable frame rate movies.

        """
        logging.info("Using OpenCV for reading movie frames.")
        try:
            import cv2
        except ImportError:
            raise ImportError(
                'The `opencv-python` (cv2) library is required to read movie '
                'files with `decoderLib=opencv`. Install it with '
                '`pip install opencv-python`.')

        logging.info("Opening movie file: {}".format(self._filename))

        capture = cv2.VideoCapture(self._filename)
        if not capture.isOpened():
            capture.release()
            raise MovieFileFormatError(self._filename)

        self._capture = capture

        # determine the frame rate, OpenCV reports `0` if it cannot work it out
        frameRate = float(capture.get(cv2.CAP_PROP_FPS))
        if not frameRate > 0.0:
            self._freePlayer()
            raise RuntimeError(
                'OpenCV could not determine the frame rate of the movie file. '
                'Try `movieLib="pyav"` instead for this file.')

        self._frameInterval = 1.0 / frameRate
        self._maxGetFrameAttempts = max(1, int(self._frameInterval / 0.001))
        self._frameRate = frameRate

        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width <= 0 or height <= 0:
            self._freePlayer()
            raise RuntimeError(
                'OpenCV could not determine the frame size of the movie file.')
        self._srcFrameSize = (width, height)

        # OpenCV has no direct notion of duration, so it is computed from the
        # frame count and the frame rate
        frameCount = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if frameCount <= 0:
            self._freePlayer()
            raise RuntimeError(
                'OpenCV could not determine the duration of the movie file. '
                'Try `movieLib="pyav"` instead for this file.')
        duration = frameCount / frameRate
        self._duration = duration

        self._metadata = MovieMetadata(
            self._filename,
            (width, height),
            frameRate,
            duration,
            FRAME_PIXEL_FORMAT)

        logging.debug("Movie metadata: {}".format(repr(self._metadata)))

        # warm up the decoder by grabbing the first frame
        success, firstFrame = capture.read()
        if not success:
            self._freePlayer()
            raise RuntimeError(
                'OpenCV failed to decode the first frame of the movie. Check '
                'the movie file.')

        initialFrameRGB = self._convertFrameToRGBOpenCV(firstFrame)
        self._frameStore.append((initialFrameRGB, 0.0, 'paused'))

        # reset back to the start of the stream so playback begins at frame 0
        self._seekOpenCV(0.0)
        # re-add the first frame to the store since seeking clears it
        self._frameStore.append((initialFrameRGB, 0.0, 'paused'))

    def _seekOpenCV(self, reqPTS):
        """OpenCV specific seek routine.

        Parameters
        ----------
        reqPTS : float
            The presentation timestamp (PTS) to seek to in seconds.

        Returns
        -------
        float
            The presentation timestamp (PTS) requested. OpenCV seeks to the
            nearest preceding keyframe and decodes forward internally, so the
            next frame read may be slightly before the requested position.

        """
        if self._capture is None:
            return

        reqPTS = min(max(0.0, reqPTS), self._metadata.duration)

        self._cleanUpFrameStore()

        import cv2

        # prefer frame-index seeking since presentation timestamps for this
        # backend are derived from frame indices
        targetFrame = self._timestampToFrameIndex(reqPTS)
        if not self._capture.set(cv2.CAP_PROP_POS_FRAMES, targetFrame):
            # fall back to millisecond seeking if the backend in use doesn't
            # support seeking by frame index
            self._capture.set(cv2.CAP_PROP_POS_MSEC, reqPTS * 1000.0)

        return reqPTS

    def _convertFrameToRGBOpenCV(self, frame):
        """Convert an OpenCV frame to RGB format.

        OpenCV decodes frames as BGR arrays, which must be converted to RGB
        before being uploaded as a texture.

        Parameters
        ----------
        frame : numpy.ndarray or `_RGBFrameAdapter`
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

        # OpenCV decodes to BGR; this also fills in an opaque alpha channel
        return _RGBFrameAdapter(cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA))

    def _getFrameOpenCV(self, reqPTS=0.0):
        """Get a frame from the movie file using OpenCV.

        Parameters
        ----------
        reqPTS : float
            The presentation timestamp (PTS) of the frame to get in seconds.

        Returns
        -------
        tuple or None
            Video data (`_RGBFrameAdapter`), presentation timestamp (PTS), and
            status.

        """
        if self._capture is None:
            return None

        import cv2

        reqPTS = min(
            max(0.0, reqPTS),
            self._metadata.duration + self._metadata.frameInterval)

        frame = self._getFrameFromStore(reqPTS)
        if frame is not None:
            return frame

        # infinite looping is requested when `loop` is explicitly `0`,
        # mirroring the `ffpyplayer` convention used elsewhere in this file
        loopInfinitely = self._decoderOpts.get('loop', 1) == 0

        # only one rewind is ever needed to satisfy a request, so this also
        # guards against spinning forever should the capture stop yielding
        # frames entirely
        restartsRemaining = 1 if loopInfinitely else 0

        while True:
            # the frame index reported before reading is that of the frame
            # about to be decoded, which gives us its PTS
            frameIndex = int(self._capture.get(cv2.CAP_PROP_POS_FRAMES))
            success, bgrFrame = self._capture.read()

            if not success:  # end of stream
                if restartsRemaining > 0:
                    # restart decoding from the beginning of the stream and
                    # keep looking for the requested frame (used when the
                    # caller wraps `reqPTS` back around to 0 for looping
                    # playback)
                    restartsRemaining -= 1
                    self._seekOpenCV(0.0)
                    continue

                if self._streamEOFCallback is not None:
                    self._streamEOFCallback()
                self._cleanUpFrameStore()
                self._seeking = False  # nothing left to seek to
                break

            curPts = self._frameIndexToTimestamp(frameIndex)

            if curPts + self._metadata.frameInterval >= reqPTS:
                self._frameStore.append(
                    (self._convertFrameToRGBOpenCV(bgrFrame), curPts,
                     'playing'))
                break

        toReturn = self._getFrameFromStore(reqPTS)
        self._cleanUpFrameStore(reqPTS)

        return toReturn

    # --------------------------------------------------------------------------
    # VLC specific methods
    #
    # WARNING: `libvlc` is not thread-safe and the video callbacks below are
    # invoked from VLC's own decoding thread. Calling into the `libvlc` API
    # from any of them deadlocks the player, so they only ever touch plain
    # Python state guarded by `_vlcFrameLock`. Everything which does call
    # `libvlc` (seeking, pausing, reading the clock) runs on the thread which
    # owns this reader, never inside a callback.
    #

    def _makeVLCCallbacks(self):
        """Build the video callbacks VLC writes frames through.

        The callbacks are created per reader instance and close over a weak
        reference to it, which keeps the reader collectable (a strong
        reference would be kept alive by the callback objects it stores) and
        lets a callback firing during teardown bail out instead of touching a
        half-freed reader.

        Returns
        -------
        tuple
            The lock, unlock and display callbacks, as `ctypes` function
            objects. These must be kept referenced for as long as VLC holds
            them, otherwise they are garbage collected and VLC calls into
            freed memory.

        """
        import vlc

        selfRef = weakref.ref(self)

        @vlc.CallbackDecorators.VideoLockCb
        def lockCallback(userData, planes):
            """Hand VLC the buffer to decode the next frame into."""
            reader = selfRef()
            if reader is None or reader._vlcWriteBuffer is None:
                # Nothing to decode into. Returning without taking the lock
                # is safe because `unlockCallback` only releases it when this
                # callback recorded that it took it.
                return None

            reader._vlcFrameLock.acquire()
            reader._vlcLockHeld = True
            planes[0] = ctypes.cast(reader._vlcWriteBuffer, ctypes.c_void_p)

            return None

        @vlc.CallbackDecorators.VideoUnlockCb
        def unlockCallback(userData, picture, planes):
            """Called once VLC has finished writing the frame."""
            reader = selfRef()
            if reader is None or not reader._vlcLockHeld:
                return

            reader._vlcLockHeld = False
            reader._vlcFrameLock.release()

        @vlc.CallbackDecorators.VideoDisplayCb
        def displayCallback(userData, picture):
            """Called when the frame just written is due to be shown.

            VLC has released the frame buffer by this point, so the buffers can
            be swapped: the frame which was just written becomes the one
            `_pullFrameVLC` reads, and VLC decodes the next frame into the one
            it had been reading.

            """
            reader = selfRef()
            if reader is None:
                return

            with reader._vlcFrameLock:
                reader._vlcWriteBuffer, reader._vlcReadBuffer = (
                    reader._vlcReadBuffer, reader._vlcWriteBuffer)
                reader._vlcFrameReady = True
                reader._vlcDisplayCount += 1

        return lockCallback, unlockCallback, displayCallback

    def _onVLCEndReached(self, event):
        """Handle VLC reaching the end of the stream.

        This runs on a VLC thread, so it only raises a flag which
        `_serviceVLCStreamEnd` acts on from the reader's own thread. Calling
        the `libvlc` API here would deadlock the player.

        """
        self._vlcStreamEnded = True

    def _openVLC(self):
        """Open a movie reader using VLC.

        This function opens the movie file using the `python-vlc` bindings to a
        local `libvlc` installation and extracts metadata about the movie file.
        Metadata will be accessible via the `getMetadata()` method.

        Like `ffpyplayer`, VLC decodes in the background on its own clock and
        plays the movie's audio track itself, rather than handing frames over
        on demand the way `pyav` and `opencv` do. Frames arrive by way of the
        video callbacks set up here, which write into buffers owned by this
        reader.

        """
        logging.info("Using VLC for reading movie frames.")
        try:
            import vlc
        except Exception as err:
            # `python-vlc` raises rather than failing to import when it cannot
            # find a `libvlc` of a matching architecture, so the error is
            # reported here alongside the usual missing-package case.
            raise ImportError(
                'The `python-vlc` library and a local VLC installation are '
                'required to read movie files with `decoderLib=vlc`. Make '
                'sure the VLC install matches the architecture of the Python '
                'interpreter running PsychoPy. Original error: {}'.format(err))

        logging.info("Opening movie file: {}".format(self._filename))

        # `an` is set by `MovieStim` when the audio track is being played back
        # by something other than the decoder, or not at all
        noAudio = bool(self._decoderOpts.get('an', False))
        # infinite looping is requested when `loop` is explicitly `0`,
        # mirroring the `ffpyplayer` convention used elsewhere in this file
        loopInfinitely = self._decoderOpts.get('loop', 1) == 0

        instanceArgs = ['--quiet', '--no-video-title-show']
        if noAudio:
            instanceArgs.append('--no-audio')
        if sys.platform.startswith('linux'):
            # nothing is drawn through X here (frames come back through the
            # callbacks below), so keep VLC from initialising Xlib alongside
            # the window backend PsychoPy is already using
            instanceArgs.append('--no-xlib')
        instanceArgs.extend(self._decoderOpts.get('options', []))

        self._vlcInstance = vlc.Instance(instanceArgs)
        if self._vlcInstance is None:
            raise RuntimeError(
                'Failed to create a VLC instance. Check that VLC is installed '
                'and that its architecture matches the Python interpreter.')

        self._vlcPlayer = self._vlcInstance.media_player_new()
        self._vlcMedia = self._vlcInstance.media_new(self._filename)

        if loopInfinitely:
            # Let VLC do the looping. It wraps the stream itself without ever
            # reporting the end of it, which keeps its clock in step with the
            # caller's, and keeps the audio track looping along with the video.
            self._vlcMedia.add_option(':input-repeat=65535')

        self._vlcPlayer.set_media(self._vlcMedia)

        # Read the movie's properties. Parsing is what populates them, and it
        # has to happen before playback starts since the frame size is needed
        # to set the output format up.
        self._vlcMedia.parse()

        width, height = self._vlcPlayer.video_get_size(0)
        if not width or not height:
            self._freePlayer()
            raise MovieFileFormatError(self._filename)
        self._srcFrameSize = (width, height)

        frameRate = float(self._vlcPlayer.get_fps())
        if not frameRate > 0.0:
            self._freePlayer()
            raise RuntimeError(
                'VLC could not determine the frame rate of the movie file. '
                'Try `movieLib="pyav"` instead for this file.')

        self._frameInterval = 1.0 / frameRate
        self._maxGetFrameAttempts = max(1, int(self._frameInterval / 0.001))
        self._frameRate = frameRate

        # VLC reports the duration in milliseconds
        duration = self._vlcMedia.get_duration() / 1000.0
        if not duration > 0.0:
            self._freePlayer()
            raise RuntimeError(
                'VLC could not determine the duration of the movie file. '
                'Try `movieLib="pyav"` instead for this file.')
        self._duration = duration

        self._metadata = MovieMetadata(
            self._filename,
            (width, height),
            frameRate,
            duration,
            FRAME_PIXEL_FORMAT)

        logging.debug("Movie metadata: {}".format(repr(self._metadata)))

        # Ask VLC for packed RGBA so frames arrive in the format the rest of
        # this class works in and no colour conversion is needed per frame.
        # `RGBA` is VLC's name for it and is laid out R, G, B, A in memory.
        pitch = width * FRAME_BYTES_PER_PIXEL
        self._vlcPlayer.video_set_format('RGBA', width, height, pitch)

        # Two buffers so VLC can decode the next frame while the last one is
        # being read, see `displayCallback` above. The spare bytes guard
        # against a decoder writing past the end of the last row.
        bufferSize = pitch * height + pitch
        self._vlcWriteBuffer = (ctypes.c_ubyte * bufferSize)()
        self._vlcReadBuffer = (ctypes.c_ubyte * bufferSize)()
        self._vlcFrameNBytes = pitch * height

        # these have to stay referenced for as long as VLC holds them
        (self._vlcLockCb,
         self._vlcUnlockCb,
         self._vlcDisplayCb) = self._makeVLCCallbacks()

        self._vlcPlayer.video_set_callbacks(
            self._vlcLockCb, self._vlcUnlockCb, self._vlcDisplayCb, None)

        self._vlcEventManager = self._vlcPlayer.event_manager()
        self._vlcEventManager.event_attach(
            vlc.EventType.MediaPlayerEndReached, self._onVLCEndReached)

        # Warm the decoder up. VLC does not produce frames until playback
        # starts, so it is started muted, run until the first frame lands, then
        # paused and rewound so the movie is sitting on frame 0 ready to play.
        self._vlcPlayer.audio_set_mute(True)
        if self._vlcPlayer.play() == -1:
            self._freePlayer()
            raise MovieFileFormatError(self._filename)

        startTime = time.time()
        while time.time() - startTime < defaultTimeout:
            if self._vlcFrameReady:
                break
            time.sleep(0.001)  # yield, don't spin the CPU while waiting
        else:
            self._freePlayer()
            raise RuntimeError(
                'VLC failed to decode the first frame of the movie within {} '
                'seconds. Check the movie file.'.format(defaultTimeout))

        firstFrameBytes = self._takeVLCFrameBytes()

        self._setVLCPaused(True)
        self._waitForVLCPauseToSettle()  # rewinding before this lands nowhere
        self._discardPendingVLCFrame()
        self._vlcPlayer.set_time(0)
        self._vlcStreamEnded = False
        self._anchorVLCPTS(0.0)
        self._vlcPlayer.audio_set_mute(self._muted or noAudio)

        # Hold the first frame at a PTS of exactly zero so that it is the frame
        # found for the start of the movie, as with the other backends.
        self._frameStore.append(
            (_RGBFrameAdapter(firstFrameBytes), 0.0, 'paused'))

    def _takeVLCFrameBytes(self):
        """Copy the most recently decoded frame out of the read buffer.

        The copy is made while holding `_vlcFrameLock` so that a buffer swap
        cannot hand this buffer back to VLC part way through it. VLC's decoding
        thread only blocks on that lock if it happens to be starting the next
        frame, and only for as long as the copy takes.

        Returns
        -------
        bytes or None
            Raw RGB24 pixel data for the frame, or `None` if VLC has not
            delivered a new one since the last call.

        """
        with self._vlcFrameLock:
            if not self._vlcFrameReady or self._vlcReadBuffer is None:
                return None

            self._vlcFrameReady = False

            return bytes(memoryview(self._vlcReadBuffer)[:self._vlcFrameNBytes])

    def _discardPendingVLCFrame(self):
        """Drop the frame VLC has waiting to be picked up, if there is one.

        Used when moving to a new position in the movie, where whatever has
        already been decoded belongs to where playback used to be.

        """
        with self._vlcFrameLock:
            self._vlcFrameReady = False

    def _setVLCPaused(self, state):
        """Pause or resume VLC, noting when a pause was asked for.

        `_waitForVLCPauseToSettle` needs to know how long ago playback was
        paused, since seeking before a pause has taken hold lands the player
        somewhere unrelated to the position asked for.

        Parameters
        ----------
        state : bool
            `True` to pause playback, `False` to resume it.

        """
        state = bool(state)

        self._vlcPlayer.set_pause(int(state))
        self._vlcPaused = state
        self._vlcPausedAt = time.time() if state else None
        self._vlcPausedAtCount = self._vlcDisplayCount

    def _vlcPauseHasSettled(self):
        """Whether a pause has had time to work its way through VLC (`bool`).

        A seek issued while a pause is still in progress is mishandled by VLC:
        rather than landing late, or not at all, the player ends up at a
        position unrelated to the one asked for. Nothing reports the pause as
        complete (`get_state()` says `Paused` straight away, well before it is
        safe to seek), but VLC presents a frame once it has noticed, so that
        is taken as the signal along with a short floor, neither being enough
        on its own.

        """
        if self._vlcPausedAt is None:
            return True  # playing, so there is no pause to wait on

        elapsed = time.time() - self._vlcPausedAt

        if elapsed >= VLC_PAUSE_SETTLE_TIMEOUT:
            return True  # asked for long enough ago to have certainly landed

        # `_vlcDisplayCount` is only ever read for progress, so it is read
        # without taking the lock rather than contending with the decoding
        # thread over it
        framesSince = self._vlcDisplayCount - self._vlcPausedAtCount

        return framesSince >= 1 and \
            elapsed >= max(self._frameInterval, VLC_PAUSE_SETTLE_MIN)

    def _waitForVLCPauseToSettle(self):
        """Wait for a pause to work its way through VLC before seeking.

        See `_vlcPauseHasSettled` for why this is needed.

        """
        deadline = time.time() + VLC_PAUSE_SETTLE_TIMEOUT

        while not self._vlcPauseHasSettled():
            if time.time() > deadline:
                logging.debug(
                    "VLC did not settle within {} seconds of being paused; a "
                    "seek made now may not land where asked.".format(
                        VLC_PAUSE_SETTLE_TIMEOUT))
                return

            time.sleep(0.001)  # yield, don't spin the CPU while waiting

    def _pullFrameVLC(self):
        """Take the frame VLC has most recently decoded, if there is a new one.

        The frame store for this backend only ever holds the newest frame.
        Unlike the on-demand backends there is no way to ask VLC for a frame at
        a particular position, so there is nothing to be gained from keeping
        the ones which have already gone past.

        Returns
        -------
        bool
            `True` if a new frame was taken and stored.

        """
        if self._vlcSeekSettleAt is not None:
            if self._vlcDisplayCount < self._vlcSeekSettleAt:
                # still being shown the position which was seeked away from
                return False

            self._vlcSeekSettleAt = None

        frameBytes = self._takeVLCFrameBytes()
        if frameBytes is None:
            return False

        self._frameStore[:] = [
            (_RGBFrameAdapter(frameBytes), self._ptsForNextVLCFrame(),
             'playing')]

        return True

    def _anchorVLCPTS(self, pts):
        """Peg the frame-counted playback position to a known movie time.

        Parameters
        ----------
        pts : float
            The movie time, in seconds, the next frame VLC delivers will be at.

        """
        self._vlcPTSAnchor = pts
        self._vlcFramesSinceAnchor = 0

    def _ptsForNextVLCFrame(self):
        """Work out the movie time of the frame just delivered by VLC.

        VLC reports its position in coarse steps, roughly a quarter of a second
        at a time, which is far too blunt to timestamp individual frames with.
        Since VLC hands frames over as it reaches them, counting them from a
        known position gives a much better estimate. The count is re-pegged to
        VLC's own clock whenever the two drift apart, which also picks up the
        wrap-around when VLC loops the movie.

        Returns
        -------
        float
            The presentation timestamp (PTS) of the frame, in seconds.

        """
        curPts = self._vlcPTSAnchor + \
            self._vlcFramesSinceAnchor * self._frameInterval

        if not self._vlcPaused:
            # While paused VLC keeps presenting the picture it is sitting on,
            # and those repeats are the same frame over again rather than the
            # movie moving on.
            self._vlcFramesSinceAnchor += 1

        # `get_time()` is a `libvlc` call, so it happens here on the reader's
        # own thread rather than in the display callback. It reports where
        # playback has reached, in milliseconds.
        reportedPts = self._vlcPlayer.get_time() / 1000.0

        if reportedPts >= 0.0 and \
                abs(curPts - reportedPts) > VLC_PTS_RESYNC_THRESHOLD:
            # The count has come adrift of where VLC actually is, either
            # because frames were dropped or because VLC has looped back to the
            # start of the movie. Believe VLC.
            self._anchorVLCPTS(reportedPts)
            self._vlcFramesSinceAnchor = 1
            curPts = reportedPts

        return curPts

    def _serviceVLCStreamEnd(self):
        """Act on VLC having reached the end of the stream.

        The event callback cannot do this itself, since notifying the caller
        may lead back into the `libvlc` API which must not be called from a VLC
        thread.

        """
        if not self._vlcStreamEnded:
            return

        self._vlcStreamEnded = False
        self._vlcPaused = True  # a finished player is not going to produce more

        # nothing further will arrive, so a seek waiting on a frame never lands
        self._seeking = False

        if self._streamEOFCallback is not None:
            self._streamEOFCallback()

    def _seekVLC(self, reqPTS):
        """VLC specific seek routine.

        Parameters
        ----------
        reqPTS : float
            The presentation timestamp (PTS) to seek to in seconds.

        Returns
        -------
        float
            The presentation timestamp (PTS) requested in seconds. The player
            is not moved here, only marked as needing to be; see
            `_applyPendingVLCSeek`. Once it is, VLC renders the frame for the
            new position through the usual callbacks, so `_getFrameVLC` may
            need to be called a few times before it arrives.

        """
        if self._vlcPlayer is None:
            return

        import vlc

        reqPTS = min(max(0.0, reqPTS), self._metadata.duration)

        # A player which has run off the end of the stream ignores any new
        # position until it has been restarted; `play()` on its own is not
        # enough to revive it.
        if self._vlcPlayer.get_state() == vlc.State.Ended:
            self._vlcPlayer.stop()
            self._vlcPlayer.play()
            self._vlcStreamEnded = False

            # the new position cannot be set until playback is running again
            startTime = time.time()
            while time.time() - startTime < defaultTimeout:
                if self._vlcPlayer.get_state() == vlc.State.Playing:
                    break
                time.sleep(0.001)
            else:
                logging.warning(
                    "VLC did not restart within {} seconds after reaching the "
                    "end of the movie; the seek to {:.3f} seconds may not have "
                    "taken effect.".format(defaultTimeout, reqPTS))

            self._vlcPaused = False
            self._vlcPausedAt = None

        # Let go of what has already been decoded at the old position.
        self._discardPendingVLCFrame()
        self._cleanUpFrameStore()
        self._anchorVLCPTS(reqPTS)

        # Moving the player is left to `_applyPendingVLCSeek`, which runs when
        # a frame is next asked for. It may have to wait for a pause to take
        # hold first, and doing that waiting here would charge it to the
        # caller's movie clock, leaving the movie that much past the position
        # it asked for.
        self._vlcPendingSeekPTS = reqPTS

        return reqPTS

    def _applyPendingVLCSeek(self, blocking=True):
        """Move the player to the position a seek has asked for.

        Parameters
        ----------
        blocking : bool
            Whether to wait for a pause which has yet to take hold, since the
            position cannot be set until it has. Pass `False` to return
            without moving in that case, leaving the seek to be applied on a
            later call rather than holding the caller up.

        Returns
        -------
        bool
            `True` if the player was moved.

        """
        if self._vlcPendingSeekPTS is None:
            return False

        # Playback being under way is itself enough for a seek to be handled
        # properly, so this only bites when the caller paused a moment ago.
        if not self._vlcPauseHasSettled():
            if not blocking:
                return False  # try again when next asked for a frame

            self._waitForVLCPauseToSettle()

        reqPTS = self._vlcPendingSeekPTS
        self._vlcPendingSeekPTS = None

        # anything presented up to now belongs to the position being left
        self._discardPendingVLCFrame()

        self._vlcPlayer.set_time(int(round(reqPTS * 1000.0)))
        self._anchorVLCPTS(reqPTS)

        # VLC presents the picture from the old position once more before
        # putting up the one at the new position, so skip that first one and
        # take the next, which is the frame seeked to.
        self._vlcSeekSettleAt = self._vlcDisplayCount + VLC_SEEK_SETTLE_FRAMES

        return True

    def _convertFrameToRGBVLC(self, frame):
        """Convert a VLC frame to RGB format.

        VLC is asked for `RGBA` frames in `_openVLC`, which is already the
        packed RGBA layout used throughout this class, so frames are wrapped
        as they are taken from the buffer and nothing is left to do here.

        Parameters
        ----------
        frame : `_RGBFrameAdapter`
            The frame to convert.

        Returns
        -------
        _RGBFrameAdapter
            The frame, unchanged.

        """
        return frame

    def _getFrameVLC(self, reqPTS=0.0, blocking=True):
        """Get a frame from the movie file using VLC.

        Parameters
        ----------
        reqPTS : float
            The presentation timestamp (PTS) of the frame to get in seconds.
        blocking : bool
            Whether to wait for VLC to deliver a frame if none has arrived
            since the last call. Pass `False` to return `None` straight away
            and leave the caller showing the previous frame.

        Returns
        -------
        tuple or None
            Video data (`_RGBFrameAdapter`), presentation timestamp (PTS), and
            status.

        """
        if self._vlcPlayer is None:
            return None

        reqPTS = min(
            max(0.0, reqPTS),
            self._metadata.duration + self._metadata.frameInterval)

        self._serviceVLCStreamEnd()
        self._applyPendingVLCSeek(blocking=blocking)

        gotNewFrame = self._pullFrameVLC()

        # VLC decodes to its own clock, so there is nothing to prod along by
        # asking again; either a frame has arrived or one has not. Waiting is
        # only worth it while frames are still coming, otherwise a paused movie
        # would stall the caller for a frame interval on every draw. A seek is
        # the exception: the player may be paused and still owe a frame for the
        # position just moved to.
        waited = False
        if blocking and not gotNewFrame and (not self._vlcPaused or
                                             self._seeking):
            waited = True
            # a seek has to decode forward from a keyframe before it can render
            # anything, which takes longer than a frame is due within during
            # ordinary playback
            deadline = time.time() + (
                VLC_SEEK_TIMEOUT if self._seeking else self._frameInterval)
            while time.time() < deadline:
                time.sleep(0.001)  # yield, don't spin the CPU while waiting
                if self._pullFrameVLC():
                    gotNewFrame = True
                    break

        if self._seeking and waited and not gotNewFrame:
            # VLC has had long enough to render the frame for the new position
            # and has not produced one, which is what happens when the seek ran
            # to the end of the movie and there is no further frame to render.
            # Leaving the seek marked as outstanding would have the caller
            # waiting on a frame which is never going to arrive.
            self._seeking = False
            self._vlcSeekSettleAt = None
            self._vlcPendingSeekPTS = None

        toReturn = self._getFrameFromStore(reqPTS)

        if toReturn is None and gotNewFrame and self._frameStore:
            # VLC runs the movie on its own clock, so the position it reports
            # can differ from the caller's by more than a frame interval,
            # leaving the lookup above with nothing. The frame just decoded is
            # still the one which should be on-screen, so hand that back rather
            # than freezing the video until the two clocks happen to agree.
            img, pts, status = self._frameStore[-1]
            toReturn = (self._convertFrameToRGB(img), pts, status)

        return toReturn

    def _freeVLCPlayer(self):
        """Tear down the VLC player and release everything it holds.

        Ordering matters here. The video callbacks run on VLC's decoding
        thread and write into buffers owned by this reader, so the player is
        stopped first (which waits for that thread), then the callbacks are
        unbound, and only then are the buffers dropped.

        Never call this while holding `_vlcFrameLock`: stopping the player
        waits on the decoding thread, which may be waiting for that very lock.

        """
        if self._vlcPlayer is not None:
            import vlc

            if self._vlcEventManager is not None:
                self._vlcEventManager.event_detach(
                    vlc.EventType.MediaPlayerEndReached)
                self._vlcEventManager = None

            self._vlcPlayer.stop()

            # Unbind before the buffers the callbacks write into are dropped.
            # Leaving them bound also keeps the interpreter from shutting down
            # cleanly.
            self._vlcPlayer.video_set_callbacks(None, None, None, None)
            self._vlcPlayer.set_media(None)
            self._vlcPlayer.release()
            self._vlcPlayer = None

        if self._vlcMedia is not None:
            self._vlcMedia.release()
            self._vlcMedia = None

        if self._vlcInstance is not None:
            self._vlcInstance.release()
            self._vlcInstance = None

        # safe now that the player has stopped and the callbacks are unbound
        self._vlcLockCb = self._vlcUnlockCb = self._vlcDisplayCb = None
        self._vlcWriteBuffer = self._vlcReadBuffer = None
        self._vlcFrameNBytes = 0
        self._vlcFrameReady = False
        self._vlcLockHeld = False
        self._vlcSeekSettleAt = None
        self._vlcStreamEnded = False
        self._vlcPaused = True
        self._vlcPausedAt = None
        self._vlcPendingSeekPTS = None

    def _getVolumeVLC(self):
        """Get the volume of the movie player using VLC.

        Returns
        -------
        float
            The volume level of the movie player, between 0.0 (mute) and 1.0
            (full volume).

        """
        if self._vlcPlayer is None:
            return 0.0

        # VLC reports the volume as a percentage, and `-1` if it cannot
        volume = self._vlcPlayer.audio_get_volume()
        if volume < 0:
            return self._decoderOpts.get('volume', 0.0)

        return volume / 100.0

    def _setVolumeVLC(self, volume):
        """Set the volume of the movie player using VLC.

        Parameters
        ----------
        volume : float
            The volume level to set, between 0.0 (mute) and 1.0 (full volume).

        """
        if self._vlcPlayer is None:
            return

        self._vlcPlayer.audio_set_volume(int(round(volume * 100.0)))

    # --------------------------------------------------------------------------
    # Backend-agnostic frame conversion dispatcher
    #

    def _convertFrameToRGB(self, frame):
        """Convert a frame to RGB format.

        This function converts a frame to RGB format. The frame is returned as
        a Numpy array. The resulting array will be in the correct format to
        upload to OpenGL as a texture.

        Parameters
        ----------
        frame : FFPyPlayer frame, av.VideoFrame, BGR `ndarray`, or \
                `_RGBFrameAdapter`
            The frame to convert.

        Returns
        -------
        numpy.ndarray
            The converted frame in RGB format.

        """
        # convert the frame to RGB format
        if self._decoderLib == 'ffpyplayer':
            return self._convertFrameToRGBFFPyPlayer(frame)
        elif self._decoderLib == 'pyav':
            return self._convertFrameToRGBPyAV(frame)
        elif self._decoderLib == 'opencv':
            return self._convertFrameToRGBOpenCV(frame)
        elif self._decoderLib == 'vlc':
            return self._convertFrameToRGBVLC(frame)
        else:
            raise NotImplementedError(
                'Frame conversion is not implemented for this decoder library.')
    
    def _bufferFramesFFPyPlayer(self, start=0.0, end=None, units='seconds',
                                maxFrames=1024):
        """Buffer frames from the movie file using FFPyPlayer.
        
        Parameters
        ----------
        start : float or int
            The start position to buffer frames from, interpreted according to
            `units`.
        end : float or int or None
            The end position to buffer frames to, interpreted according to
            `units`. If `None`, the end of the movie is used.
        units : str
            The units `start` and `end` are given in, either `'seconds'`
            (default) or `'frames'`. If `'frames'`, they are interpreted as
            frame indices.
        maxFrames : int
            Maximum number of frames to buffer. Decoded frames are held in
            memory as RGB24, so an unbounded range can exhaust memory on long
            or high resolution movies (a minute of 1080p is roughly 11 GB).
            Buffering stops once this many frames have been collected.

        """
        if self._player is None:
            return

        if units not in ('seconds', 'frames'):
            raise ValueError(
                "`units` must be either 'seconds' or 'frames', got "
                "'{}'.".format(units))

        # check if we have a valid start time
        if start < 0.0:
            raise ValueError('Start time must be greater than or equal to 0.0.')

        # check if we have a valid end time
        if end is None:
            end = self._metadata.duration if units == 'seconds' else \
                self._timestampToFrameIndex(self._metadata.duration)
        elif end < 0.0:
            raise ValueError('End time must be greater than or equal to 0.0.')

        # convert the start and end frame indices to timestamps
        if units == 'frames':
            start = self._frameIndexToTimestamp(start)
            end = self._frameIndexToTimestamp(end)

        if end < start:
            raise ValueError(
                'End time must be greater than or equal to the start time.')

        # seek to the start time
        self._seekFFPyPlayer(start)

        # buffer frames from the movie file
        buffered = 0
        getFrameAttempts = 0
        staleDrops = 0
        maxStaleDrops = 240
        # FFPyPlayer paces delivery to the playback clock, so `get_frame()`
        # returns `None` on most polls; retry rather than stopping at the first
        # one. The budget is per-frame (reset below on each frame received) and
        # generous since buffering is a bulk operation with no timing demands.
        maxBufferAttempts = self._maxGetFrameAttempts * 3

        while buffered < maxFrames:
            frame, status = self._player.get_frame()

            if status == FFPYPLAYER_STATUS_EOF:
                break

            if frame is None:
                if getFrameAttempts < maxBufferAttempts:
                    time.sleep(0.001)
                    getFrameAttempts += 1
                    continue
                logging.warning(
                    "FFPyPlayer stopped delivering frames while buffering; "
                    "buffered {} frame(s).".format(buffered))
                break

            getFrameAttempts = 0  # frame received, reset the retry budget

            img, curPts = frame

            # drop frames still arriving from before the seek above
            if self._pendingSeekPTS is not None:
                if curPts > self._pendingSeekPTS + self._metadata.frameInterval:
                    staleDrops += 1
                    if staleDrops < maxStaleDrops:
                        continue
                self._pendingSeekPTS = None

            if curPts >= end:
                break
            if curPts >= start:
                # convert the frame to RGB format
                rgbImg = self._convertFrameToRGBFFPyPlayer(img)
                self._frameStore.append((rgbImg, curPts, 'playing'))
                buffered += 1
        else:
            logging.warning(
                "Stopped buffering after reaching the {} frame limit; request "
                "a narrower range or raise `maxFrames`.".format(maxFrames))

    def _getFrameFFPyPlayer(self, reqPTS=0.0, blocking=True):
        """Get a frame from the movie file using FFPyPlayer.

        This method gets the desired frame from the movie file. If it has not
        been decoded yet, this function will ensure the frame is decoded and 
        made available.

        Parameters
        ----------
        reqPTS : float
            The presentation timestamp (PTS) of the frame to get in seconds.
            This hints the reader to which frame to decode and return.
        blocking : bool
            Whether to wait for the decoder to catch up. FFPyPlayer hands over
            frames on its own schedule, so by default this waits up to a frame
            interval for one. Pass `False` to give up immediately instead and
            leave the caller showing the previous frame, which keeps a drawing
            loop responsive while a seek is still resolving.

        Returns
        -------
        tuple
            Video data (`ndarray`), presentation timestamp (PTS), and status.
            The status value may be backend specific.

        """        
        # check if we have a player object, return None if not
        if self._player is None:
            return None
            # raise ValueError('Movie reader is not open. Cannot grab frame.')
        
        # normalzie the PTS to be between 0 and the duration of the movie
        reqPTS = min(max(0.0, reqPTS), 
                     self._metadata.duration + self._metadata.frameInterval)
        
        # check if we have the frame in the store
        frame = self._getFrameFromStore(reqPTS)
        if frame is not None:
            return frame
        
        getFrameAttempts = 0
        # bound on frames discarded while waiting for a seek to land, so a
        # seek that never takes effect cannot hang the caller
        staleDrops = 0
        maxStaleDrops = 240
        while 1:  # keep getting frames until we reach the desired PTS           
            frame, status = self._player.get_frame()

            if status == FFPYPLAYER_STATUS_EOF:
                if self._streamEOFCallback is not None:
                    self._streamEOFCallback()
                self._cleanUpFrameStore()
                self._pendingSeekPTS = None
                self._seeking = False  # nothing left to seek to
                break
            elif status == FFPYPLAYER_STATUS_PAUSED:
                # A paused decoder will not deliver the frame a seek is waiting
                # on, so stop reporting the seek as outstanding. This is what
                # happens when a movie is seeked past its own end, since
                # reaching the end pauses playback.
                self._seeking = False
                break
            
            # If we get `None` for the frame, the player isn't ready to give us
            # one yet, so wait a moment and try again. Give up after
            # `_maxGetFrameAttempts` *consecutive* misses and let the caller
            # show the previous frame; `MovieStim.updateVideoFrame` already
            # treats `None` as 'keep the last frame on screen'. Raising here
            # would abort the experiment over a transient decoder stall.
            if frame is None:
                maxAttempts = self._maxGetFrameAttempts
                if not blocking:
                    maxAttempts = max(1, maxAttempts // 8)

                if getFrameAttempts < maxAttempts:
                    time.sleep(0.001)  # wait a bit before trying again
                    getFrameAttempts += 1
                    continue   # keep retrying
                
                if blocking:
                    logging.warning(
                        "FFPyPlayer failed to return a frame after {} "
                        "attempts, keeping the previous frame.".format(
                            getFrameAttempts))
                break
            
            # the decoder gave us a frame, so reset the retry budget; it counts
            # consecutive misses, not misses accumulated over a long decode
            getFrameAttempts = 0
            
            img, curPts = frame  # extract frame information

            # Discard frames still in flight from before a seek. An accurate
            # seek never lands ahead of its target, so anything ahead of it is
            # left over from the previous position and would otherwise be
            # stored against the wrong PTS (breaking backward seeks).
            if self._pendingSeekPTS is not None:
                if curPts > self._pendingSeekPTS + self._metadata.frameInterval:
                    staleDrops += 1
                    if staleDrops < maxStaleDrops:
                        continue  # stale, keep draining
                    logging.warning(
                        "FFPyPlayer did not settle at the requested seek "
                        "position after discarding {} frames; using the "
                        "current position instead.".format(staleDrops))
                self._pendingSeekPTS = None  # seek has landed (or gave up)

            # if we have gotten the frame we are looking for, return it
            if curPts + self._metadata.frameInterval >= reqPTS:
                self._frameStore.append(
                    (self._convertFrameToRGBFFPyPlayer(img), curPts,
                     'playing'))
                break
        
        toReturn = self._getFrameFromStore(reqPTS)

        self._cleanUpFrameStore(reqPTS)  # clean up the frame store

        return toReturn
    
    # --------------------------------------------------------------------------
    # File I/O methods
    #

    def open(self):
        """Open the movie file for reading.

        Calling this will open the movie file and extract metadata to determine
        the frame rate, size, and duration of the movie.

        """
        logging.debug("Using decoder library: {}".format(self._decoderLib))
        if self._decoderLib == 'ffpyplayer':
            self._openFFPyPlayer()
        elif self._decoderLib == 'pyav':
            self._openPyAV()
        elif self._decoderLib == 'opencv':
            self._openOpenCV()
        elif self._decoderLib == 'vlc':
            self._openVLC()
        else:
            raise ValueError(
                'Unknown decoder library: {}'.format(self._decoderLib))
        
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

    def _freePlayer(self):
        """Clean up the player.
        
        This function closes the player and clears the player object. Do not 
        call this method directly while the player is still in use.

        """
        if self._decoderLib == 'ffpyplayer':
            if self._player is None:
                return

            self._player.set_mute(True)  # mute the player
            self._player.set_pause(True)  # pause the player
            self._player.close_player()

            self._player = None
            self._pendingSeekPTS = None
            self._swsContext = None
            self._swsContextKey = None
        elif self._decoderLib == 'pyav':
            # the decode thread must be done with the container before it can
            # be closed
            if not self._stopPyAVDecoder():
                return
            if self._container is not None:
                self._container.close()
                self._container = None
            self._videoStream = None
            self._packetIterator = None
            self._pyavLanding = False
            self._pyavLastPTS = None
        elif self._decoderLib == 'opencv':
            if self._capture is not None:
                self._capture.release()
                self._capture = None
        elif self._decoderLib == 'vlc':
            self._freeVLCPlayer()

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

        if self._pyavThread is not None:
            # freed by the decode thread, see `decodeAhead()`
            self._pyavReleasePending.extend(self._frameStore[:keepFrom])

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
        if self._decoderLib == 'ffpyplayer':
            if self._player is None:
                return

            self._player.set_pause(bool(state))
        elif self._decoderLib == 'vlc':
            if self._vlcPlayer is None:
                return

            self._setVLCPaused(state)
        elif self._decoderLib in ('pyav', 'opencv'):
            # These backends have no playback clock of their own to pause.
            # `opencv` decodes on demand, and `pyav` decodes ahead only as far
            # as its queue allows, then waits. `MovieStim` already stops
            # requesting new frames when paused, so there is nothing to do.
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

        if self._decoderLib == 'ffpyplayer':
            self._seekFFPyPlayer(pts)
        elif self._decoderLib == 'pyav':
            self._seekPyAV(pts)
        elif self._decoderLib == 'opencv':
            self._seekOpenCV(pts)
        elif self._decoderLib == 'vlc':
            self._seekVLC(pts)
        else:
            raise ValueError(
                'Unknown decoder library: {}'.format(self._decoderLib))
        
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
        self._muted = bool(state)

        if self._decoderLib == 'ffpyplayer':
            if self._player is None:
                return

            self._player.set_mute(self._muted)
        elif self._decoderLib == 'vlc':
            if self._vlcPlayer is None:
                return

            self._vlcPlayer.audio_set_mute(self._muted)
        elif self._decoderLib in ('pyav', 'opencv'):
            # audio for `pyav` and `opencv` movies is handled by a separate
            # `Sound` object owned by `MovieStim`; nothing to mute on the
            # reader itself
            pass

    @property
    def muted(self):
        """Whether the movie reader is muted (`bool`).

        For `ffpyplayer` and `vlc` this reflects the state of the underlying
        player. The `pyav` and `opencv` backends do not play audio themselves,
        so this reports the last state passed to `mute()`.

        """
        if self._decoderLib == 'ffpyplayer' and self._player is not None:
            return bool(self._player.get_mute())

        if self._decoderLib == 'vlc' and self._vlcPlayer is not None:
            # VLC reports `-1` when it cannot say, in which case fall back to
            # the last state asked for
            isMuted = self._vlcPlayer.audio_get_mute()
            if isMuted >= 0:
                return bool(isMuted)

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
        if self._decoderLib == 'pyav':
            with self._pyavCondition:
                totalFramesDecoded += self._queuedPyAVFrameCount()
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
            This only affects `ffpyplayer`, `pyav` and `vlc`, the backends
            which decode ahead on their own schedule; `opencv` decodes on
            demand when asked.
        deferDecoding : bool
            If `True`, the decoder is left to replace the frames this takes
            when `decodeAhead()` is next called, rather than straight away.
            Call that once done with the frame, such as once it has been
            copied to the GPU, so that the decoder isn't competing with that
            for the CPU and memory bandwidth. Failing that, it happens at the
            start of the next call to this. Only affects `pyav`.

        Returns
        -------
        tuple or None
            Video data, or `None` if no frame is available.

        """
        if self._decoderLib == 'ffpyplayer':
            frameData = self._getFrameFFPyPlayer(pts, blocking=blocking)
        elif self._decoderLib == 'pyav':
            frameData = self._getFramePyAV(
                pts, blocking=blocking, deferDecoding=deferDecoding)
        elif self._decoderLib == 'opencv':
            frameData = self._getFrameOpenCV(pts)
        elif self._decoderLib == 'vlc':
            frameData = self._getFrameVLC(pts, blocking=blocking)
        else:
            raise ValueError(
                'Unknown decoder library: {}'.format(self._decoderLib))

        if frameData is not None:
            # the decoder has caught up with the position asked for
            self._seeking = False

        return frameData

    def decodeAhead(self):
        """Let the decoder replace the frames `getFrame()` has taken.

        This goes with `getFrame(deferDecoding=True)`, and does nothing
        otherwise. The decoder also frees the frames this reader is finished
        with, so that doing so doesn't hold up the caller either.

        """
        if self._pyavThread is None:
            return

        if not (self._pyavRefillPending or self._pyavReleasePending):
            return

        with self._pyavCondition:
            # Handed over and dropped here together while holding the lock,
            # which the decode thread needs to take them. Otherwise it could
            # drop its references first, leaving the last to go here.
            self._pyavReleased.extend(self._pyavReleasePending)
            self._pyavReleasePending.clear()
            self._pyavCondition.notify_all()

        self._pyavRefillPending = False

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
        if self._decoderLib == 'ffpyplayer' and self._player is None:
            return ''
        if self._decoderLib == 'pyav' and self._container is None:
            return ''
        if self._decoderLib == 'opencv' and self._capture is None:
            return ''
        if self._decoderLib == 'vlc' and self._vlcPlayer is None:
            return ''

        return ''

    def _getVolumeFFPyPlayer(self):
        """Get the volume of the movie player using the ffpyplayer library.

        Returns
        -------
        float
            The volume level of the movie player, between 0.0 (mute) and 1.0 (full volume).
        """
        if self._player is None:
            return 0.0

        return self._player.get_volume()

    def _setVolumeFFPyPlayer(self, volume):
        """Set the volume of the movie player using the ffpyplayer library.

        Parameters
        ----------
        volume : float
            The volume level to set, between 0.0 (mute) and 1.0 (full volume).

        """
        if self._player is None:
            return

        self._player.set_volume(volume)

    def setVolume(self, volume):
        """Set the volume of the movie player.

        Parameters
        ----------
        volume : float
            The volume level to set, between 0.0 (mute) and 1.0 (full volume).

        """
        volume = min(1.0, max(0.0, float(volume)))
        
        logging.debug("Setting movie volume to: {}".format(volume))

        if self._decoderLib == 'ffpyplayer':
            if self._player is None:
                return
            self._setVolumeFFPyPlayer(volume)
        elif self._decoderLib == 'vlc':
            self._setVolumeVLC(volume)
        elif self._decoderLib in ('pyav', 'opencv'):
            # stored for reference; actual playback volume for these backends
            # is controlled through `MovieStim`'s extracted-audio `Sound`
            # object
            self._decoderOpts['volume'] = volume
        else:
            raise NotImplementedError(
                'Volume control is not implemented for this decoder library.')

    def __del__(self):
        """Close the movie file when the object is deleted.
        """
        self.close()


class MovieStim(BaseVisualStim, DraggingMixin, ColorMixin, ContainerMixin):
    """Class for presenting movie clips as stimuli.

    This class is used to present movie clips loaded from file as stimuli in 
    PsychoPy. Movies will play at the their native frame rate regardless of the
    refresh rate of the display.

    Parameters
    ----------
    win : :class:`~psychopy.visual.Window`
        Window the video is being drawn to.
    filename : str
        Name of the file or stream URL to play. If an empty string, no file will
        be loaded on initialization but can be set later.
    movieLib : str or None
        Library to use for video decoding. One of `'ffpyplayer'`, `'pyav'`,
        `'opencv'` or `'vlc'`. If `None` (the default), the library set
        globally with `setBackend()` is used. That in turn defaults to the library
        appropriate for the running Python version: `'pyav'` on Python 3.14+
        (where `ffpyplayer` is not available), and `'ffpyplayer'` otherwise.
        An alert is raised if you explicitly request a library that isn't the
        'preferred' one for your Python version.
    audioLib : str or None
        Library to use for audio decoding. If `movieLib` is `'ffpyplayer'`
        then this must be `'sdl2'` for audio playback, and if `movieLib` is
        `'vlc'` it must be `'vlc'`. If `None`, the default audio library for
        the `movieLib` will be used (this will be `'sdl2'` for
        `movieLib='ffpyplayer'`, `'vlc'` for `movieLib='vlc'`, and
        extracted-track playback via `psychopy.sound.Sound` for
        `movieLib='pyav'` and `movieLib='opencv'`, since neither library
        provides its own audio playback).
    units : str
        Units to use when sizing the video frame on the window, affects how
        `size` is interpreted.
    size : ArrayLike or None
        Size of the video frame on the window in `units`. If `None`, the native
        size of the video will be used.
    draggable : bool
        Can this stimulus be dragged by a mouse click?
    flipVert : bool
        If `True` then the movie will be top-bottom flipped.
    flipHoriz : bool
        If `True` then the movie will be right-left flipped.
    volume : int or float
        If specifying an `int` the nominal level is 100, and 0 is silence. If a
        `float`, values between 0 and 1 may be used.
    loop : bool
        Whether to start the movie over from the beginning if draw is called and
        the movie is done. Default is `False`.
    autoStart : bool
        Automatically begin playback of the video when `flip()` is called.
    loadAudioInBackground : bool
        Decode the movie's audio track in the background, rather than waiting
        for it to load along with the movie. For a long movie that takes a
        second or so, which loading the movie then doesn't wait for. If `play()`
        is called before the track has loaded, it waits for it, so leave time
        between loading and playing the movie (check `isAudioReady`), or the
        wait lands in the drawing loop instead. Default is `False`.
    downscaleFrames : bool
        Scale frames down to the size the movie is drawn at as they are
        decoded, if smaller than the movie's own. This is much less to copy to
        the GPU for each frame (a 4K frame drawn at 800x600 goes from ~33 MB to
        ~2 MB), and looks better than leaving the GPU to shrink it. Frames are
        scaled with a box filter, or nearest neighbour if `interpolate` is
        `False`. Only the `pyav` backend scales frames. Default is `True`.

    Notes
    -----
    * Precise audio and visual syncronization is not guaranteed when using 
      the `ffpyplayer` library for video playback. If you require precise
      synchronization, consider extracting the audio from the movie file and
      playing it separately using the `sound.Sound` class instead.
    * `ffpyplayer` is not available on Python 3.14 and later. On those
      versions, `PyAV` (`movieLib='pyav'`) is used automatically.
    * `OpenCV` (`movieLib='opencv'`) derives frame timestamps from frame
      indices and the reported frame rate, so it should only be used with
      constant frame rate movies.
    * `VLC` (`movieLib='vlc'`) requires VLC itself to be installed, of an
      architecture matching the Python interpreter running PsychoPy. Like
      `ffpyplayer` it plays the movie's audio itself, on the default output
      device, and so does not give precise audio-visual synchronization.

    """
    def __init__(self,
                 win,
                 filename="",
                 movieLib=None,
                 audioLib=None,
                 units='pix',
                 size=None,
                 pos=(0.0, 0.0),
                 ori=0.0,
                 anchor="center",
                 draggable=False,
                 flipVert=False,
                 flipHoriz=False,
                 color=(1.0, 1.0, 1.0),  # remove?
                 colorSpace='rgb',
                 opacity=1.0,
                 contrast=1,
                 volume=1.0,
                 name='',
                 loop=False,
                 autoLog=True,
                 depth=0.0,
                 noAudio=False,
                 interpolate=True,
                 autoStart=True,
                 audioDevice=None,
                 audioConfig=None,
                 loadAudioInBackground=False,
                 downscaleFrames=True,
                 **kwargs):

        # what local vars are defined (these are the init params) for use
        self._initParams = dir()
        self._initParams.remove('self')

        super(MovieStim, self).__init__(
            win, units=units, name=name, autoLog=False)

        # drawing stuff
        self.draggable = draggable
        self.flipVert = flipVert
        self.flipHoriz = flipHoriz
        self.pos = pos
        self.ori = ori
        self.size = size
        self.depth = depth
        self.anchor = anchor
        self.colorSpace = colorSpace
        self.color = color
        self.opacity = opacity

        # playback stuff
        # Resolve the decoder library to use if the user has not explicitly
        # requested one. This defers to the module-level backend, which starts
        # out as the library appropriate for this Python version (`ffpyplayer`
        # is unavailable on Python 3.14+, so `pyav` is used there instead) and
        # can be changed globally with `setBackend()`.
        if movieLib is None:
            movieLib = getBackend()
        elif movieLib != PREFERRED_VIDEO_LIB:
            logging.warning(
                "Requested `movieLib='{}'` but the preferred (and only "
                "guaranteed to be installed) movie library for this Python "
                "version ({}.{}) is '{}'. If movie loading fails, try "
                "`movieLib='{}'` instead.".format(
                    movieLib, sys.version_info.major, sys.version_info.minor,
                    PREFERRED_VIDEO_LIB, PREFERRED_VIDEO_LIB))

        self._movieLib = movieLib
        self._decoderOpts = {}
        self._player = None  # player interface object
        self._filename = pathToString(filename)
        self._volume = volume
        self._noAudio = noAudio  # cannot be changed
        self._loop = loop
        self._loopCount = 0  # number of times the movie has looped
        self._recentFrame = None
        # Frame object `_recentFrame` was built from, and the address of its
        # pixel data. The decoder hands back the same frame object each time it
        # is asked for a position within the same frame interval, so its
        # identity is what tells us whether there is anything new to upload.
        self._recentFrameImage = None
        self._recentFrameAddr = None
        # size `(w, h)` of `_recentFrame` in pixels, see `_setRecentFrame`
        self._recentFrameSize = None
        self._frameNeedsUpload = False
        self._autoStart = autoStart
        self._isLoaded = False
        self._pts = 0.0
        self._movieTime = 0.0   # current movie position in seconds
        self._lastFrameAbsTime = -1.0  # absolute time of the last frame

        # internal status flags for keeping track of the playback state
        self._playbackStatus = NOT_STARTED
        self._wasPaused = False  # was the movie paused?
        # time playback was scheduled to start by `play(when=...)`, until the
        # decoder has been started then (`None` when there's nothing pending)
        self._startPlayerAt = None

        # audio stuff
        if audioDevice is not None:
            logging.debug(
                "Audio device specified for movie playback. Ignoring "
                "`audioLib` parameter."
            )
            if isinstance(audioDevice, str) and DeviceManager.getDevice(audioDevice):
                audioDevice = DeviceManager.getDevice(audioDevice)
            # make sure speaker is a SpeakerDevice
            if not isinstance(audioDevice, speaker.SpeakerDevice.resolveBackend()):
                audioDevice = speaker.SpeakerDevice(audioDevice)

            self._audioDevice = audioDevice
            self._audioLib = None  # override
        else:
            self._audioDevice = None
            if audioLib is not None:
                self._audioLib = audioLib
            elif self._movieLib == 'ffpyplayer':
                # ffpyplayer plays audio itself via SDL2
                self._audioLib = 'sdl2'
                self._noAudio = False  # use SDL2 for audio playback
            elif self._movieLib == 'vlc':
                # VLC plays audio itself, on the default output device
                self._audioLib = 'vlc'
            else:
                # other decoder backends (`pyav`, `opencv`) do not provide
                # their own audio playback, so the audio track is extracted and
                # played back separately via `psychopy.sound.Sound`
                # (see `_loadAudioTrack`/`_extractAudioTrack`)
                self._audioLib = None

        # warn the user if the decoder is playing the audio itself, since 
        # precise A/V sync is not supported in that case
        if self._audioLib == 'sdl2':
            logging.warning(
                'Using `sdl2` for audio playback via `ffpyplayer`. This is not '
                'recommended for applications requiring precise audio-visual '
                'synchronization.')
        elif self._audioLib == 'vlc':
            logging.warning(
                'Using VLC for audio playback. This is not recommended for '
                'applications requiring precise audio-visual '
                'synchronization.')
        # else:
        #     raise MovieAudioError(
        #         "Movie audio playback is only supported with the 'sdl2' library "
        #         "at this time.")

        # audio playback configuration
        self._audioConfig = audioConfig if audioConfig is not None else {}
        # what `_audioTrack` was loaded from, see `_getAudioSource`
        self._audioTrackSource = None
        # decodes `_audioTrack` in the background, until it's done
        self._audioLoader = None
        # whether loading the movie leaves `_audioLoader` decoding the track
        # rather than waiting for it, see `_loadAudioTrack`
        self._loadAudioInBackground = bool(loadAudioInBackground)

        # Whether frames are scaled down to the size they're drawn at as they
        # are decoded, and the size and filter the decoder was last given for
        # it, see `_updateOutputFrameSize`
        self._downscaleFrames = bool(downscaleFrames)
        self._outputFrameFormat = None
        self._audioSamples = []  # audio samples from the movie 
        self._audioTrack = None  # audio track information from the movie metadata
        self._audioReader = None  # audio reader object
        self._audioSampleRate = 44100  # audio sample rate
        self._audioChannels = 2  # number of audio channels

        # OpenGL data
        self._interpolate = interpolate
        self._texFilterNeedsUpdate = True
        self._metadata = NULL_MOVIE_METADATA
        self._pixbuffId = GL.GLuint(0)
        self._textureId = GL.GLuint(0)
        self._vidWidth = self._vidHeight = 0  # set by `_setupTextureBuffers`
        self._nBufferBytes = 0

        # load a file if provided, otherwise the user must call `setMovie()`
        self._filename = pathToString(filename)
        if self._filename:  # load a movie if provided
            self.loadMovie(self._filename)

        self.autoLog = autoLog
    
    @property
    def size(self):
        return BaseVisualStim.size.fget(self)
    
    @size.setter
    def size(self, value):
        # store requested size
        self._requestedSize = value
        # if player isn't initialsied yet, do no more
        if not self._hasPlayer:
            return
        # duplicate if necessary
        if isinstance(value, (float, int)) or value is None:
            value = [value, value]
        # make sure value is a list so we can assign indices
        if isinstance(value, tuple):
            value = [val for val in value]
        # handle aspect ratio
        if value[0] is None and value[1] is None:
            # if both values are none, use original size
            value = layout.Size(self.frameSize, units="pix", win=self.win)
        elif value[0] is None:
            # if width is None, use height and maintain aspect ratio
            value[0] = (self.frameSize[0] / self.frameSize[1]) * value[1]
        elif value[1] is None:
            # if height is None, use width and maintain aspect ratio
            value[1] = (self.frameSize[1] / self.frameSize[0]) * value[0]
        # set as normal
        BaseVisualStim.size.fset(self, value)
        # frames are decoded at the size they're drawn at
        self._updateOutputFrameSize()
            
    @property
    def filename(self):
        """File name for the loaded video (`str`)."""
        return self._filename

    @filename.setter
    def filename(self, value):
        self.loadMovie(value)

    def setMovie(self, value):
        if self._isLoaded:
            self.unload()
        self.loadMovie(value)

    @property
    def autoStart(self):
        """Start playback when `.draw()` is called (`bool`)."""
        return self._autoStart

    @autoStart.setter
    def autoStart(self, value):
        self._autoStart = bool(value)

    @property
    def frameRate(self):
        """Frame rate of the movie in Hertz (`float`).
        """
        if self._player is None or self._player._metadata is None:
            return 0.0
        
        return self._player._metadata.frameRate
    
    @property
    def loop(self):
        """Whether the movie will loop when it reaches the end (`bool`).
        
        If `True`, the movie will start over from the beginning when it reaches
        the end. If `False`, the movie will stop at the end.
        
        """
        return self._loop
    
    @loop.setter
    def loop(self, value):
        """Set whether the movie will loop when it reaches the end.
        
        Parameters
        ----------
        value : bool
            If `True`, the movie will loop when it reaches the end. If `False`,
            the movie will stop at the end.
        
        """
        self._loop = bool(value)

    @property
    def _decoderPlaysAudio(self):
        """Whether the decoder plays the movie's audio track itself (`bool`).

        `ffpyplayer` (through SDL2) and VLC play the audio themselves, so
        volume and muting are controlled on the movie reader. The other
        backends decode video only, and their audio is played back by a
        separate `Sound` object holding the track extracted by
        `_extractAudioTrack`.

        """
        return self._audioLib in ('sdl', 'sdl2', 'vlc')

    @property
    def _hasPlayer(self):
        """`True` if a media player instance is started.
        """
        # use this property to check if the player instance is started in
        # methods which require it
        return hasattr(self, "_player") and self._player is not None

    @property
    def interpolate(self):
        """Whether to use linear interpolation when scaling the video frame 
        (`bool`).
        """
        return self._interpolate
    
    @interpolate.setter
    def interpolate(self, value):
        self._interpolate = bool(value)
        self._texFilterNeedsUpdate = True  # update the texture filter on the next draw call
        # and frames scaled down as they're decoded use the matching filter
        self._updateOutputFrameSize()

    @staticmethod
    def getBackend():
        """Get the current movie decoder backend (`str`)."""
        return getBackend()

    @staticmethod
    def setBackend(movieLib):
        """Set the movie decoder backend to use (`str`)."""
        setBackend(movieLib)

    # --------------------------------------------------------------------------
    # Movie file handlers
    #
    
    def _setFileName(self, filename):
        """Set the file name of the movie.

        This function sets the file name of the movie. The file name is used
        to load the movie from disk. If the file name is not set, the movie
        will not be loaded.

        Parameters
        ----------
        filename : str
            The file name of the movie.

        """
        # If given `default.mp4`, sub in full path
        if isinstance(filename, str):
            # alias default names (so it always points to default.png)
            if filename in defaultStim:
                filename = Path(prefs.paths['assets']) / defaultStim[filename]

            # check if the file has can be loaded
            if not os.path.isfile(filename):
                raise MovieFileNotFoundError(
                    "Cannot open movie file `{}`".format(filename))
        else:
            # If given a recording component, use its last clip
            if hasattr(filename, "lastClip"):
                filename = filename.lastClip

        self._filename = os.path.abspath(str(filename))

    def loadMovie(self, filename):
        """Load a movie file from disk.

        Parameters
        ----------
        filename : str
            Path to movie file. Must be a format that FFMPEG supports.

        """
        # Set the movie file name, this handles normalizing the path and
        # checking if the file exists.

        self._setFileName(filename)

        # Time opening the movie file

        t0 = time.time()  # time it
        logging.debug(
            "Opening movie file: {}".format(self._filename))

        # Load the audio track to play alongside the video. This needs to be
        # done before the movie is opened by the player to avoid file access
        # issues. The track is decoded into memory (in the background if
        # `loadAudioInBackground`), or kept from before if this is the same
        # movie being reloaded, as by `stop()`.
        disableAudio = False
        if not self._noAudio and not self._decoderPlaysAudio:
            self._loadAudioTrack()  # decode and load the audio track
            disableAudio = True  # playing through our libs, so disable in ffpyplayer

        if self._noAudio and self._movieLib == 'vlc':
            # VLC opens the audio output device itself as soon as it starts
            # playing, so `noAudio` has to be passed down to it. The other
            # backends are kept as they are: theirs is either muted (SDL2) or
            # never played in the first place.
            disableAudio = True

        self._decoderOpts['an'] = disableAudio

        # Setup looping if the user has requested it. This is done by setting the
        # `loop` option in the decoder options so FFMPEG will loop the movie 
        # automatically when it reaches the end. The loop count is reset to 0.

        self._decoderOpts['loop'] = 0 if self._loop else 1
        self._loopCount = 0  # reset loop count

        # Create the movie player interface, this is what decodes movie frames
        # in the background. We disable audio playback since we are using the
        # our own audio library for playback.

        self._player = MovieFileReader(
            filename=self._filename,
            decoderLib=self._movieLib,
            decoderOpts=self._decoderOpts)
        
        # Frames are decoded at the size they're drawn at. Where that doesn't
        # depend on the movie's own size, the decoder is told before it starts,
        # so that even the first frames come out at it.
        self._outputFrameFormat = None
        requestedSizePix = self._getRequestedSizePix()
        if requestedSizePix is not None:
            self._updateOutputFrameSize(requestedSizePix)

        # Open the player, this will get metadata about the movie and start
        # decoding frames in the background.
        
        self._player.open()
        
        logging.debug(
            "Movie file opened in {:.2f} seconds".format(
                time.time() - t0))

        # Free the OpenGL buffers for the last movie's frames, if any. Those for
        # this one are made at the size of its frames as they're uploaded, see
        # `_pixelTransfer`.
        self._freeTextureBuffers()

        # update size in case frame size has changed
        self.size = self._requestedSize

        # reset movie state and timekeeping variables
        self._playbackStatus = NOT_STARTED  # reset playback status
        self._pts = 0.0  # reset presentation timestamp
        self._movieTime = 0.0  # reset movie time
        self._startPlayerAt = None
        self._isLoaded = True

        # set the volume to previous 
        self.volume = self._volume

        # display first frame of video
        frameData = self._player._getFrameFromStore(0.0)
        if frameData is not None:
            self._setRecentFrame(frameData[0])
            self._pixelTransfer(forceRefresh=True)  # copy the first frame to the texture
        else:
            # at the movie's own size until it has a frame to show
            self._setupTextureBuffers()

    def _setupAudioStream(self):
        """Setup the audio stream for the movie.
        """
        # todo - handle setting up the audio library stream
        if self._noAudio or self._decoderPlaysAudio:
            return

    def _pushAudioSamples(self):
        """Push audio samples to the audio buffer.
        """
        # todo - implement this
        if self._noAudio or self._decoderPlaysAudio:
            return

    def _getAudioSource(self):
        """Identify the audio track loading this movie would give (`tuple`).

        This goes by the movie file as it is on disk now, and the settings the
        track is loaded with. See `_loadAudioTrack`, which uses a track already
        loaded with the same identity rather than loading it again.

        """
        try:
            fileStat = os.stat(self._filename)
            fileState = (fileStat.st_mtime_ns, fileStat.st_size)
        except OSError:
            fileState = None

        return (os.path.abspath(self._filename), fileState,
                self._audioConfig.get('fps'), self._audioDevice)

    @staticmethod
    def _getTrackSampleRate(track):
        """Sample rate in Hz that a `Sound` plays at, and that sounds at any
        other rate are resampled to when loaded (`int`).

        """
        # `sounddevice` plays sounds through streams of its own...
        rate = getattr(getattr(track, 'stream', None), 'sampleRate', None)
        if not rate:
            # ...where `ptb` plays them through the speaker's, opened by now
            rate = getattr(getattr(track, 'speaker', None), 'sampleRateHz', None)

        return int(rate or track.sampleRate)

    @staticmethod
    def _getTrackChannels(track):
        """Number of channels a movie's audio track is decoded to for a `Sound`
        to play (`int`), which is stereo unless its speaker is mono. A track
        with more channels is mixed down to these."""
        channels = getattr(getattr(track, 'speaker', None), 'channels', None)

        return 1 if channels == 1 else 2

    @staticmethod
    def _getAudioDuration(container, audioStream):
        """Duration in seconds of an audio track going by the movie file's
        metadata (`float`), or `None` if it doesn't say."""
        if audioStream.duration is not None and \
                audioStream.time_base is not None:
            return float(audioStream.duration * audioStream.time_base)

        if container.duration is not None:
            import av
            return container.duration / av.time_base

        return None

    @staticmethod
    def _decodeAudioTrack(container, audioStream, sampleRate, layout=None,
                          onBlock=None, cancel=None):
        """Decode an audio track.

        Parameters
        ----------
        container : av.container.InputContainer
            Movie file the track is in.
        audioStream : av.audio.stream.AudioStream
            Track to decode.
        sampleRate : int
            Sample rate in Hz to resample the track to.
        layout : str or None
            Channel layout to mix the track to (e.g. `'stereo'`), or `None` to
            keep its own.
        onBlock : callable or None
            Called as `onBlock(start, samples)` with each block of samples as
            it is decoded, `start` being the index in the track of the first
            of them. `samples` is only valid for the duration of the call. If
            `None`, the whole track is returned as one array instead.
        cancel : threading.Event or None
            Decoding stops once this is set, returning `None`.

        Returns
        -------
        ndarray, int or None
            Without `onBlock`, the samples as 32-bit floats shaped
            `(samples, channels)`. With it, the number of samples decoded.
            `None` if cancelled.

        """
        import av
        from av.audio.layout import AudioLayout
        from av.audio.resampler import AudioResampler

        # not fatal if the codec doesn't support decoding with threads
        try:
            audioStream.thread_type = 'AUTO'
        except Exception:
            pass

        trackLayout = audioStream.layout.name
        trackChannels = len(audioStream.layout.channels)
        if layout is None:
            layout = trackLayout
        nChannels = len(AudioLayout(layout).channels)

        returnSamples = onBlock is None
        if returnSamples:
            # Room for the whole track going by its duration, with a little to
            # spare in case that's out. It's grown if it turns out to need more.
            duration = MovieStim._getAudioDuration(container, audioStream)
            out = np.empty(
                int(((duration or 60.0) + 1.0) * sampleRate) * nChannels,
                dtype=np.float32)

            def onBlock(start, samples):
                nonlocal out
                begin, end = start * nChannels, (start + len(samples)) * nChannels
                if end > len(out):
                    grown = np.empty(max(end, 2 * len(out)), np.float32)
                    grown[:begin] = out[:begin]
                    out = grown
                out[begin:end] = samples.reshape(-1)

        nOut = 0

        def emit(frames):
            """Hand on resampled frames (packed 32-bit float)."""
            nonlocal nOut
            for resampled in frames:
                n = resampled.samples
                onBlock(nOut, np.frombuffer(
                    resampled.planes[0], np.float32, n * nChannels).reshape(
                        n, nChannels))
                nOut += n

        # Decoded samples are gathered into blocks of 32-bit float planar
        # samples, which most decoders produce anyway, and each block is
        # resampled as it fills. See `AUDIO_DECODE_BLOCK`.
        resampler = AudioResampler(format='flt', layout=layout, rate=sampleRate)
        block = np.empty((trackChannels, AUDIO_DECODE_BLOCK), np.float32)
        nBlock = 0
        blockRate = None  # rate decoded at, taken from the first frame
        toPlanar = None  # for frames in any other form

        def resampleBlock():
            nonlocal nBlock
            if not nBlock:
                return
            blockFrame = av.AudioFrame.from_ndarray(
                block[:, :nBlock], format='fltp', layout=trackLayout)
            blockFrame.sample_rate = blockRate
            emit(resampler.resample(blockFrame))
            nBlock = 0

        def addToBlock(frames):
            nonlocal block, nBlock
            for frame in frames:
                n = frame.samples
                if nBlock + n > block.shape[1]:
                    resampleBlock()
                    if n > block.shape[1]:
                        block = np.empty((trackChannels, n), np.float32)
                for channel, plane in enumerate(frame.planes):
                    block[channel, nBlock:nBlock + n] = np.frombuffer(
                        plane, np.float32, n)
                nBlock += n

        for frame in container.decode(audioStream):
            if cancel is not None and cancel.is_set():
                return None

            if blockRate is None:
                blockRate = frame.sample_rate

            if frame.format.name == 'fltp' and frame.layout.name == trackLayout \
                    and frame.sample_rate == blockRate:
                addToBlock((frame,))
                continue

            if toPlanar is None:
                toPlanar = AudioResampler(
                    format='fltp', layout=trackLayout, rate=blockRate)
            addToBlock(toPlanar.resample(frame))

        if toPlanar is not None:
            addToBlock(toPlanar.resample(None))  # flush
        resampleBlock()
        emit(resampler.resample(None))  # flush

        if returnSamples:
            return out[:nOut * nChannels].reshape(-1, nChannels)

        return nOut

    def _loadAudioTrack(self):
        """Load the movie's audio track into a `Sound` for playback.

        The `Sound` is made here, which opens the speaker, and the track is
        decoded into it on a background thread (see `_AudioTrackLoader`). This
        waits for it to finish unless `loadAudioInBackground` was set, in which
        case `play()` waits for it if it hasn't finished by then, see
        `_finishAudioLoad`.

        The track is decoded at the sample rate of the speaker it plays on (or
        `audioConfig['fps']`, if given), and in stereo unless the speaker is
        mono, so that it needn't be converted again to be played. The
        `'codec'` and `'nbytes'` that `audioConfig` used to take no longer
        apply, since the track is no longer written to a file on the way.

        A track already loaded (or loading) from the same file is used again
        as it is, rather than being decoded again, as when `stop()` reloads the
        movie.

        """
        source = self._getAudioSource()

        if self._audioTrack is not None:
            if hasattr(self._audioTrack, 'stop'):
                self._audioTrack.stop()

            if source == self._audioTrackSource:
                logging.debug(
                    "Using the audio track already loaded from: {}".format(
                        self._filename))
                if hasattr(self._audioTrack, 'seek'):
                    self._audioTrack.seek(0.0)
                return

            self._cleanupAudioTrack()

        logging.debug("Loading audio track from movie file: {}".format(
            self._filename))

        import av
        import psychopy.sound as _sound

        container = av.open(self._filename)
        try:
            audioStream = next(
                (s for s in container.streams if s.type == 'audio'), None)

            if audioStream is None:
                logging.warning(
                    "Movie file has no audio track, no audio will be played "
                    "for: {}".format(self._filename))
                container.close()
                return

            # Open the speaker with a moment of silence first, to find out the
            # rate it plays at. A sound at any other rate is resampled to fit
            # as it is loaded, which takes seconds for a long track, where
            # decoding to the right rate in the first place costs next to
            # nothing extra.
            speakerKwargs = {}
            if self._audioDevice is not None:
                speakerKwargs['speaker'] = self._audioDevice
            track = _sound.Sound(
                np.zeros((AUDIO_TRACK_PLACEHOLDER_SAMPLES, 2), dtype=np.float32),
                **speakerKwargs)
            track.volume = self._volume  # set the volume to the current level

            playbackRate = self._getTrackSampleRate(track)
            sampleRate = int(self._audioConfig.get('fps') or playbackRate)
            nChannels = self._getTrackChannels(track)

            # Give the sound its full length of silence now, which the track is
            # written into a block at a time as it decodes. That needs to know
            # how long the track is, and for it to be at the rate the sound
            # plays at. Otherwise it's handed over in one go once decoded.
            nAllocated = 0
            duration = self._getAudioDuration(container, audioStream)
            if duration is not None and sampleRate == playbackRate:
                nAllocated = int(
                    (duration + AUDIO_TRACK_DURATION_MARGIN) * sampleRate)
                track.sampleRate = sampleRate
                track._allocateSamples(nAllocated, nChannels)

            loader = _AudioTrackLoader(
                container, audioStream, track, sampleRate,
                'mono' if nChannels == 1 else 'stereo', nAllocated)
        except BaseException:
            container.close()
            raise

        self._audioTrack = track
        self._audioTrackSource = source
        self._audioLoader = loader

        if not self._loadAudioInBackground:
            # wait for it here, raising any error decoding it ran into
            loader.wait()
            self._finishAudioLoad()

    def _finishAudioLoad(self, wait=True):
        """Finish loading the audio track once it has decoded, see
        `_loadAudioTrack`.

        Parameters
        ----------
        wait : bool
            Wait for the track to decode if it hasn't yet.

        Returns
        -------
        bool
            `True` if the track has loaded (or there is none), or `False` if it
            is still decoding and `wait` is `False`.

        """
        loader = self._audioLoader
        if loader is None:
            return True

        if not loader.isDone:
            if not wait:
                return False

            t0 = time.time()
            loader.wait()
            waited = time.time() - t0
            # only worth a warning if it held playback up by a refresh or more
            logFunc = logging.warning \
                if waited > (self.win.monitorFramePeriod or 1 / 60.) \
                else logging.debug
            logFunc(
                "Movie {} was played before its audio track had loaded, so "
                "waited {:.3f} seconds for it. Leave more time between loading "
                "a movie and playing it to avoid this, or check "
                "`isAudioReady`.".format(self._filename, waited))

        self._audioLoader = None
        track = loader.track

        if loader.error is not None:
            self._cleanupAudioTrack()
            raise loader.error

        if not loader.nSamples:
            logging.warning(
                "No audio could be decoded from the audio track of: {}".format(
                    self._filename))
            self._cleanupAudioTrack()
        elif loader.overflow:
            # The track turned out longer than the movie file said, or couldn't
            # be written a block at a time, so is handed over in one go. This
            # holds up drawing for a moment if the track is long.
            samples = np.concatenate(
                [track.sndArr[:loader.nAllocated]] + loader.overflow)
            track.sampleRate = loader.sampleRate
            track.setSound(samples, log=False)
        elif loader.nAllocated:
            track._trimSamples(loader.nSamples)

        logging.debug(
            "Audio track loaded at {} Hz in {:.2f} seconds".format(
                loader.sampleRate, time.time() - loader.tStart))

        return True

    def _restartAudioTrack(self):
        """Play the extracted audio track again from the start, as when the
        movie loops.

        Decoders which play the audio themselves loop it along with the video,
        so this only applies to the track played back separately.

        """
        track = self._audioTrack
        if self._noAudio or self._decoderPlaysAudio or track is None:
            return
        if not (hasattr(track, 'seek') and hasattr(track, 'play')):
            return

        # The track may still be playing out its last moments, or have
        # finished already if it is a little shorter than the video. Seeking
        # restarts one which is playing, and the other needs playing again.
        wasPlaying = getattr(track, 'isPlaying', False)
        track.seek(0.0)
        if not wasPlaying:
            track.play()

    def _cleanupAudioTrack(self):
        """Clean up the audio track.

        This function stops the audio track if it is playing and releases it,
        stopping it decoding first if it still is.

        """
        if self._audioLoader is not None:
            self._audioLoader.cancel()
            self._audioLoader = None

        if self._audioTrack is not None:
            if hasattr(self._audioTrack, 'stop'):
                self._audioTrack.stop()
            self._audioTrack = None

        self._audioTrackSource = None

    def load(self, filename):
        """Load a movie file from disk (alias of `setMovie`).

        Parameters
        ----------
        filename : str
            Path to movie file. Must be a format that FFMPEG supports.

        """
        self.setMovie(filename=filename)

    def unload(self, log=True):
        """Stop and unload the movie.

        Parameters
        ----------
        log : bool
            Log this event.

        """
        if self._isLoaded:
            self._player.close()
            self._freeTextureBuffers()  # free buffer before creating a new one
            self._cleanupAudioTrack()
            self._isLoaded = False

    # --------------------------------------------------------------------------
    # Time and frame management
    #

    def _nextFlipTime(self):
        """Time of the next flip of the window, in seconds on the clock
        `core.getTime()` reads (`float`).

        This is the time the movie clock is read at, being when the frame drawn
        now will appear. Reading it at the time of drawing instead would let
        that jitter by however long the rest of the drawing loop varies by,
        and put the movie a refresh behind its own clock. Before the window has
        flipped at all, this is the present time.

        """
        try:
            return self.win.getFutureFlipTime(clock=core.monotonicClock)
        except (AttributeError, IndexError):
            # the refresh rate is unknown, or there is no flip to go from yet
            return core.getTime()

    def _updateMoviePos(self):
        """Update the movie position.

        This function updates the movie position. The movie position is the
        presentation timestamp (PTS) of the current frame. The PTS is updated
        when the movie is played or paused.

        """
        # the movie clock, as of the flip the frame drawn now will appear on
        now = self._nextFlipTime()
        # if self._playbackStatus == SEEKING:
        #     self._lastFrameAbsTime = now
        #     # if we are seeking, the movie time is not updated until done
        #     return

        if self._playbackStatus == PLAYING:
            if now < self._lastFrameAbsTime:
                # Playback is scheduled to start later, see `play(when=...)`.
                # Hold the current position until then, leaving the start time
                # where the movie clock will run from.
                return

            if self._startPlayerAt is not None:
                self._startPlayer()

            # check if were at the end of the movie
            if self._movieTime < self.duration:
                # determine the current movie time
                self._movieTime = min(
                    self._movieTime + (now - self._lastFrameAbsTime), 
                    self.duration)
            else:
                if self._loop:
                    # if looping, reset the movie time to 0
                    self._loopCount += 1  # increment loop count
                    self._movieTime = 0.0
                    self._restartAudioTrack()
                else:
                    # if not looping, stop playback
                    self._player.pause(True)
                    self._movieTime = self.duration  # set to end of movie
                    self._playbackStatus = FINISHED  # indicate movie is done

        # A movie which hasn't started stays where it is, which is the start
        # unless it has been seeked (loading, `stop()` and `reset()` all put
        # it back there themselves).

        # if paused, the movie time does not advance but we still need to
        # update the last frame time
        self._lastFrameAbsTime = now  # always updates 

    # --------------------------------------------------------------------------
    # Drawing and rendering
    #

    def _getRequestedSizePix(self):
        """Size `(w, h)` in pixels the movie was asked to be drawn at, or
        `None` if that depends on the movie's own size (`ndarray` or `None`).
        """
        value = self._requestedSize
        if isinstance(value, (int, float)):
            value = (value, value)
        if value is None or any(val is None for val in value):
            return None

        return layout.Size(value, units=self.units, win=self.win).pix

    def _updateOutputFrameSize(self, sizePix=None):
        """Tell the decoder the size the movie is drawn at, for it to scale
        frames down to as it decodes them, if that has changed. See
        `downscaleFrames` and `MovieFileReader.setOutputFrameSize`.

        Parameters
        ----------
        sizePix : ArrayLike or None
            Size `(w, h)` in pixels the movie is drawn at, or `None` to go by
            `size`.

        """
        player = getattr(self, '_player', None)
        if player is None:
            return

        outputSize = None
        if self._downscaleFrames:
            if sizePix is None:
                sizePix = self._size.pix
            outputSize = tuple(
                max(1, int(math.ceil(abs(val)))) for val in sizePix)

        # nearest neighbour when not interpolating, as the GPU does
        outputFormat = (outputSize, 'AREA' if self._interpolate else 'POINT')
        if outputFormat != self._outputFrameFormat:
            self._outputFrameFormat = outputFormat
            player.setOutputFrameSize(*outputFormat)

    def _setRecentFrame(self, frameImage):
        """Make `frameImage` the frame to upload, and show from now on."""
        # suggested by Alex Forrence (aforren1) originally in PR #6439 to use memoryview
        videoBuffer = frameImage.to_memoryview()[0].memview
        videoFrameArray = np.frombuffer(videoBuffer, dtype=np.uint8)
        self._recentFrame = videoFrameArray # most recent frame
        # cached here since `ndarray.ctypes` builds a new helper object
        # on every access, and the pixel transfer runs every draw
        self._recentFrameAddr = videoFrameArray.ctypes.data
        self._recentFrameImage = frameImage
        # frames scaled down as they're decoded give their size, and any others
        # are the movie's own size
        self._recentFrameSize = getattr(frameImage, 'size', None) or \
            tuple(self._player.getMetadata().size)
        self._frameNeedsUpload = True

    @property
    def frameTexture(self):
        """Texture ID for the current video frame (`GLuint`). You can use this
        as a video texture. However, you must periodically call
        `updateVideoFrame` to keep this up to date.

        The texture is the size of the frames given to it, which with
        `downscaleFrames` is the size the movie is drawn at (if smaller than
        its own), and is replaced with a new one if that changes.

        """
        return self._textureId
    
    def updateVideoFrame(self, blocking=None):
        """Update the present video frame. The next call to `draw()` will make
        the retrieved frame appear.

        Parameters
        ----------
        blocking : bool or None
            Whether to wait for the decoder if the frame is not ready yet. If
            `None` (default), this waits during ordinary playback but not while
            a seek is outstanding, so that a seek started with
            `seek(blocking=False)` cannot stall the drawing loop. Pass `True`
            or `False` to decide explicitly.

        Returns
        -------
        bool
            If `True`, the video texture has been updated and the frame index is
            advanced by one. If `False`, the last frame should be kept
            on-screen.

        """
        # get the current movie frame for the video time
        self._updateMoviePos()  # update the movie position

        if blocking is None:
            # Waiting is worthwhile when the decoder is merely a little behind
            # during playback, but not while catching up from a seek the caller
            # asked not to block on; there the previous frame is shown and this
            # is retried on the next draw.
            blocking = not self._player.isSeeking

        # Decoding is deferred until `draw()` has copied the frame to the GPU,
        # see `MovieFileReader.decodeAhead()`. Called on its own, this leaves
        # it to the next call instead.
        frameData = self._player.getFrame(
            self._movieTime + _frameSampleOffset(
                self.win.monitorFramePeriod, self._player.frameInterval),
            blocking=blocking,
            deferDecoding=True)
        
        if frameData is None:  # handle frame not available by showing last frame
            # if self._playbackStatus == PLAYING:  # something went wrong
            #     self._playbackStatus = SEEKING
            
            return False
        
        frameImage, pts, _ = frameData

        # check if we are seeking
        # if self._playbackStatus == SEEKING:
        #     if self._wasPaused:
        #         self._playbackStatus = PAUSED
        #     else:
        #         self._playbackStatus = PLAYING

        if frameImage is not None:
            # The decoder serves the same frame object for any position within
            # a frame interval, so while the display refresh outruns the movie
            # frame rate most calls land on the frame already on the GPU. Only
            # rewrap and flag for upload when the frame really has changed.
            if frameImage is not self._recentFrameImage or pts != self._pts:
                self._setRecentFrame(frameImage)
        else:
            self._recentFrame = None
            self._recentFrameAddr = None
            self._recentFrameImage = None

        self._pts = pts  # store the current PTS of the frame we got

        return True

    def _freeTextureBuffers(self):
        """Free texture and pixel buffers. Call this when tearing down this
        class or if a movie is stopped.

        """
        # Drop the frame held for the buffers being freed. Without this a frame
        # from a previously loaded movie could be uploaded into the buffers
        # made for the next one, which may not be the same size.
        self._recentFrame = None
        self._recentFrameImage = None
        self._recentFrameAddr = None
        self._recentFrameSize = None
        self._frameNeedsUpload = False

        self._deleteTextureObjects()

    def _deleteTextureObjects(self):
        """Delete the texture and pixel buffer, if made."""
        try:
            # delete buffers and textures if previously created
            if self._pixbuffId.value > 0:
                GL.glDeleteBuffers(1, self._pixbuffId)
                self._pixbuffId = GL.GLuint()

            # delete the old texture if present
            if self._textureId.value > 0:
                GL.glDeleteTextures(1, self._textureId)
                self._textureId = GL.GLuint()
            
        except Exception:  # can happen when unloading or shutting down
            pass

        self._vidWidth = self._vidHeight = 0
        self._nBufferBytes = 0

    def _setupTextureBuffers(self, width=None, height=None):
        """Setup texture buffers which hold frame data. This creates a 2D
        RGBA texture and pixel buffer. The pixel buffer serves as the store for
        texture color data. Each frame, the pixel buffer memory is mapped and
        frame data is copied over to the GPU from the decoder.

        This is called with the size of the frames being uploaded whenever it
        changes, see `_pixelTransfer`. Any texture and pixel buffer made before
        are deleted first.

        Parameters
        ----------
        width, height : int or None
            Size of the frames in pixels, or `None` for the movie's own size.

        """
        if width is None or height is None:
            width, height = self._player.getMetadata().size

        self._deleteTextureObjects()

        # Compute the buffer size. These are fixed for the life of the
        # buffers, so they are cached here rather than recomputed on every
        # pixel transfer.
        vidWidth, vidHeight = int(width), int(height)
        nBufferBytes = vidWidth * vidHeight * FRAME_BYTES_PER_PIXEL
        self._vidWidth = vidWidth
        self._vidHeight = vidHeight
        self._nBufferBytes = nBufferBytes

        # Create the pixel buffer object which will serve as the texture memory
        # store. Pixel data will be copied to this buffer each frame.
        GL.glGenBuffers(1, ctypes.byref(self._pixbuffId))
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, self._pixbuffId)
        GL.glBufferData(
            GL.GL_PIXEL_UNPACK_BUFFER,
            nBufferBytes,
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
            GL.GL_RGBA8,
            vidWidth, vidHeight,  # frame dims in pixels
            0,
            GL.GL_RGBA,
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

    def _pixelTransfer(self, forceRefresh=False):
        """Copy pixel data from video frame to texture.

        This is called when a new frame is available. The pixel data is copied
        from the video frame to the texture store on the GPU.

        Parameters
        ----------
        forceRefresh : bool
            If `True`, the pixel data will be copied to the texture even if the
            playback state indicates that the movie is paused or seeking.

        """
        if self._recentFrame is None:
            return  # no frame to copy
        
        if not forceRefresh and self._playbackStatus != PLAYING:
            return  # don't update the texture if paused or seeking unless forced

        if not (forceRefresh or self._frameNeedsUpload):
            # The frame already on the GPU is the one to show. This is the
            # common case whenever the display refresh rate is higher than the
            # movie frame rate (e.g. a 30 FPS movie on a 60 Hz window), where
            # re-uploading would burn a whole-frame copy and a texture transfer
            # per draw to no effect.
            return

        # The texture follows the size of the frames, which changes when the
        # movie comes to be drawn at another size, see `downscaleFrames`
        if tuple(self._recentFrameSize) != (self._vidWidth, self._vidHeight):
            self._setupTextureBuffers(*self._recentFrameSize)

        # frame size and buffer size are cached by `_setupTextureBuffers`
        vidWidth, vidHeight = self._vidWidth, self._vidHeight
        nBufferBytes = self._nBufferBytes

        if self._recentFrame.nbytes < nBufferBytes:
            # guards against uploading a frame which does not match the buffers
            # it would be read into, which would read past the end of it
            logging.error(
                "Movie frame is smaller than the texture buffer allocated for "
                "it, skipping the pixel transfer.")
            self._frameNeedsUpload = False
            return

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

        # copy the frame data to the buffer
        ctypes.memmove(bufferPtr,
            self._recentFrameAddr,
            nBufferBytes)

        # Very important that we unmap the buffer data after copying, but
        # keep the buffer bound for setting the texture.
        GL.glUnmapBuffer(GL.GL_PIXEL_UNPACK_BUFFER)

        # Bind the texture in OpenGL. Note that `GL_TEXTURE_2D` does not need
        # enabling for this; the enable bit only gates fixed-function drawing,
        # which `_drawRectangle` sets up for itself.
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._textureId)
        # rows of 4-byte pixels are always 4-byte aligned
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 4)

        # copy the PBO to the texture, the format matching the texture's own
        # so that the driver can copy it as-is rather than convert it
        GL.glTexSubImage2D(
            GL.GL_TEXTURE_2D, 0, 0, 0,
            vidWidth, vidHeight,
            GL.GL_RGBA,
            GL.GL_UNSIGNED_BYTE,
            0)  # point to the presently bound buffer

        # important to unbind the PBO
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        self._frameNeedsUpload = False  # texture now matches `_recentFrame`

    def _updateTexFilter(self):
        """Apply the texture filtering mode for the `interpolate` setting.

        The texture must be bound before calling this. This is done as part of
        drawing rather than of the pixel transfer so that a change to
        `interpolate` takes effect on the next draw, whether or not a new frame
        has been uploaded since.

        """
        if self._interpolate:
            texFilter = GL.GL_LINEAR
        else:
            texFilter = GL.GL_NEAREST

        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, texFilter)
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, texFilter)

        self._texFilterNeedsUpdate = False

    def _drawRectangle(self):
        """Draw the video frame to the window.

        This is called by the `draw()` method to blit the video to the display
        window. The dimensions of the video are set by the `size` parameter.

        """
        # make sure that textures are on and GL_TEXTURE0 is active
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture(GL.GL_TEXTURE0)

        # sets opacity (1, 1, 1 = RGB placeholder)
        GL.glColor4f(1, 1, 1, self.opacity)
        GL.glPushMatrix()
        self.win.setScale('pix')

        # move to centre of stimulus and rotate
        vertsPix = self.verticesPix

        array = (GL.GLfloat * 32)(
            1, 1,  # texture coords
            vertsPix[0, 0], vertsPix[0, 1], 0.,  # vertex
            0, 1,
            vertsPix[1, 0], vertsPix[1, 1], 0.,
            0, 0,
            vertsPix[2, 0], vertsPix[2, 1], 0.,
            1, 0,
            vertsPix[3, 0], vertsPix[3, 1], 0.,
        )
        GL.glPushAttrib(GL.GL_ENABLE_BIT)

        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._textureId)

        if self._texFilterNeedsUpdate:
            self._updateTexFilter()

        GL.glPushClientAttrib(GL.GL_CLIENT_VERTEX_ARRAY_BIT)

        # 2D texture array, 3D vertex array
        GL.glInterleavedArrays(GL.GL_T2F_V3F, 0, array)
        GL.glDrawArrays(GL.GL_QUADS, 0, 4)
        GL.glPopClientAttrib()
        GL.glPopAttrib()
        GL.glPopMatrix()

        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)

    def _drawThrobber(self):
        """Draw a throbber to indicate that the movie is loading or seeking.
        """
        # todo - implement this
        pass

    def draw(self, win=None):
        """Draw the current frame to a particular window.

        The current position in the movie will be determined automatically. This
        method should be called on every frame that the movie is meant to
        appear. If `.autoStart==True` the video will begin playing when this is
        called.

        Parameters
        ----------
        win : :class:`~psychopy.visual.Window` or `None`
            Window the video is being drawn to. If `None`, the window specified
            at initialization will be used instead.

        Returns
        -------
        bool
            `True` if the frame was updated this draw call.

        """
        self._selectWindow(self.win if win is None else win)

        # handle autoplay
        if self._autoStart and self.isNotStarted:
           self.play()

        # update the video frame and draw it to a quad
        if self.updateVideoFrame():
            self._pixelTransfer()

        self._drawRectangle()  # draw the texture to the target window

        # the frame is on its way to the GPU, so the decoder can carry on
        self._player.decodeAhead()

        # if self._playbackStatus == SEEKING:
        #     self._drawThrobber()

        return True

    # --------------------------------------------------------------------------
    # Video playback controls and status
    #

    @property
    def isPlaying(self):
        """`True` if the video is presently playing (`bool`).
        """
        return self._playbackStatus == PLAYING

    @property
    def isNotStarted(self):
        """`True` if the video may not have started yet (`bool`). This status is
        given after a video is loaded and play has yet to be called.
        """
        return self._playbackStatus == NOT_STARTED

    @property
    def isStopped(self):
        """`True` if the video is stopped (`bool`). It will resume from the
        beginning if `play()` is called.
        """
        return self._playbackStatus == STOPPED

    @property
    def isPaused(self):
        """`True` if the video is presently paused (`bool`).
        """
        return self._playbackStatus == PAUSED

    @property
    def isFinished(self):
        """`True` if the video is finished (`bool`). Reports the same status as
        `isStopped` if the video is stopped.
        """
        return self._playbackStatus == FINISHED

    @property
    def isSeeking(self):
        """`True` while a seek has yet to produce a frame (`bool`).

        This is set between a call to `seek()` (or `rewind()`, `fastForward()`
        and `replay()`, which use it) and the decoder delivering a frame for
        the new position, and is cleared once that frame arrives or the movie
        ends before it can.

        It is independent of the playback status, so a movie which was playing
        before the seek still reports `isPlaying` while this is `True`.

        Seeks normally complete within the `seek()` call itself, so this is
        only observable when the decoder cannot keep up, such as with large
        frames or slow media. It is useful for showing a loading indicator
        while waiting on the movie to catch up.

        """
        if self._player is None:
            return False

        return self._player.isSeeking

    @property
    def isAudioReady(self):
        """`True` once the movie's audio track has loaded (`bool`).

        With `loadAudioInBackground=True`, the audio track is decoded in the
        background after the movie loads, so that loading doesn't wait for it,
        and `play()` waits for it if it hasn't finished. For a long movie this
        can take a second or so, so check this to leave time for it before
        playing. Always `True` otherwise, as it is for a movie without an
        audio track, or with audio disabled.

        Raises any error decoding the audio track ran into.

        """
        return self._finishAudioLoad(wait=False)

    @property
    def movieTime(self):
        """Current movie time in seconds (`float`). This is the time since the
        movie started playing, as of the flip the most recently drawn frame
        appears on. If the movie is paused, this time will not advance.
        """
        return self._movieTime

    def play(self, when=None, log=True):
        """Start or continue a paused movie from current position.

        Parameters
        ----------
        when : float, :class:`~psychopy.visual.Window` or None
            When to start playback. Either an absolute time in seconds on the
            clock `psychopy.clock.getTime()` reads, the same as `when` for
            `Sound.play()`, or a window to start on its next flip. The audio track is scheduled to start at the same time.
            If `None` (default), or a time which has already passed, playback
            starts straight away, the video from the next flip of the window.
            Until playback starts, the frame at the current position stays
            on-screen.
        log : bool
            Log the play event.

        Notes
        -----
        * With `loadAudioInBackground=True`, the audio track is decoded in the
          background after the movie loads. If it hasn't finished, this waits
          for it first, delaying playback. Check `isAudioReady` to leave time
          for it.
        * When the decoder plays the audio itself (`ffpyplayer` and `vlc`), it
          is started on the first `draw()` at or after `when`, so the audio
          onset is only as precise as the drawing loop.

        """
        if self._player is None:
            return
        
        if self._playbackStatus == PLAYING:
           return  # nop

        # With `loadAudioInBackground`, the audio track may still be decoding,
        # so wait for it if it hasn't finished. This comes before working out
        # when to start, so that playback still starts on the next flip after.
        self._finishAudioLoad()

        # The movie clock runs on `core.getTime()`, which is
        # `psychopy.clock.getTime()` less `monotonicClock`'s last reset time.
        now = core.getTime()
        if when is None:
            tStart = now
        elif hasattr(when, 'getFutureFlipTime'):
            tStart = when.getFutureFlipTime(clock=core.monotonicClock)
        else:
            tStart = float(when) - core.monotonicClock.getLastResetTime()

        scheduled = tStart > now
        if not scheduled:
            # Straight away, which for the video means from the next flip, the
            # first it can be shown on. The movie clock is read at the flip
            # each frame appears on (see `_updateMoviePos`), so starting it
            # there puts the first frame on that flip.
            tStart = max(self._nextFlipTime(), now)

        if not self._noAudio and not self._decoderPlaysAudio:
            if self._audioTrack is not None and hasattr(self._audioTrack, 'play'):
                # Start the audio from wherever the video is. A paused track
                # can't be relied on to carry on from the right place itself:
                # the `sounddevice` backend reads blocks ahead of playback, so
                # it would resume ~20 ms past where it was paused.
                if hasattr(self._audioTrack, 'seek'):
                    self._audioTrack.seek(self._movieTime)

                if when is None:
                    self._audioTrack.play()
                else:
                    self._audioTrack.play(when=_ScheduledTime(
                        tStart + core.monotonicClock.getLastResetTime()))

        self._playbackStatus = PLAYING
        self._wasPaused = False  # reset the paused flag
        # the movie clock runs from `tStart`, see `_updateMoviePos`
        self._lastFrameAbsTime = tStart

        if scheduled:
            # Decoders with a clock of their own (and which may be playing the
            # audio too) are started once the time comes round, see
            # `_updateMoviePos`.
            self._startPlayerAt = tStart
        else:
            self._startPlayer()

        if log:
            if scheduled:
                logging.info(
                    "Movie playback {} scheduled to start at {:.2f} seconds "
                    "in, at t={:.4f}".format(
                        self._filename, self._movieTime, tStart))
            else:
                logging.info(
                    "Movie playback {} started at {:.2f} seconds".format(
                        self._filename, self._movieTime))

    def _startPlayer(self):
        """Start the decoder, and its audio if it plays the audio itself."""
        self._startPlayerAt = None

        if not self._noAudio and self._decoderPlaysAudio:
            self._player.mute(False)
            self._player.setVolume(self._volume)

        self._player.pause(False)  # start the player

    def pause(self, log=True):
        """Pause the current point in the movie. The image of the last frame
        will persist on-screen until `play()` or `stop()` are called.

        Parameters
        ----------
        log : bool
            Log this event.

        """
        if not self._noAudio:
            if self._decoderPlaysAudio:
                self._player.mute(True)
            else:
                if self._audioTrack is not None and hasattr(self._audioTrack, 'pause'):
                    self._audioTrack.pause()

        self._player.pause()
        self._startPlayerAt = None  # cancel a start still to come, if any
        self._wasPaused = True  # set the paused flag
        self._playbackStatus = PAUSED

        if log:
            logging.info("Movie {} paused at position {:.2f} seconds".format(
                self._filename, self._movieTime))

    def toggle(self, log=True):
        """Switch between playing and pausing the movie. If the movie is playing,
        this function will pause it. If the movie is paused, this function will
        begin playback from the current position.

        Parameters
        ----------
        log : bool
            Log this event.

        """
        if self.isPlaying:
            self.pause()
        else:
            self.play()

    def stop(self, log=True):
        """Stop the current point in the movie (sound will stop, current frame
        will not advance and remain on-screen). Once stopped the movie can be
        restarted from the beginning by calling `play()`.

        Note that this method will fully unload the movie and reset the
        player instance. If you want to reset the movie without unloading it,
        use `seek(0.0)` instead.

        Parameters
        ----------
        log : bool
            Log this event.

        """
        # stop should reset the video to the start and pause
        if self._player is None:
            return  # nothing to stop

        if log:
            logging.debug("Stopping movie: {}".format(self._filename))

        self._player.close()  # close the player

        # Stop the audio but keep the track, which reloading the movie below
        # uses again rather than decoding it from the file all over again
        if self._audioTrack is not None and hasattr(self._audioTrack, 'stop'):
            self._audioTrack.stop()

        self.loadMovie(self._filename)  # reload the movie
        
        self._playbackStatus = NOT_STARTED

        if log:
            logging.info("Movie stopped: {}".format(self._filename))

    def seek(self, timestamp, blocking=True, log=True):
        """Seek to a particular timestamp in the movie.

        Parameters
        ----------
        timestamp : float
            Time in seconds.
        blocking : bool
            Whether to wait for the frame at `timestamp` before returning. If
            `True` (default), the new frame is fetched here and is on-screen at
            the next `draw()`. If `False`, this returns as soon as the seek has
            been requested and the frame is picked up by the next `draw()`
            instead, leaving `isSeeking` set until it arrives.
        log : bool
            Log this event.

        Notes
        -----
        * The decoders themselves seek asynchronously, so the cost of a
          blocking seek is waiting on the frame rather than on the seek. Use
          `blocking=False` to keep a drawing loop responsive, and `isSeeking`
          to show a loading indicator until the movie catches up.

        """
        if self._playbackStatus == PLAYING: 
            self._wasPaused = False
        elif self._playbackStatus == PAUSED:
            self._wasPaused = True

        self._movieTime = timestamp
        self._player.seek(self._movieTime)

        # seek the audio track if we have one
        if self._audioTrack is not None and hasattr(self._audioTrack, 'seek'):
            self._audioTrack.seek(self._movieTime)

        if blocking:
            # Fetch the frame for the new position now, rather than leaving it
            # to the next `draw()`. This has to wait explicitly: the seek is
            # outstanding at this point, which is exactly when
            # `updateVideoFrame` would otherwise choose not to.
            self._lastFrameAbsTime = self._nextFlipTime()
            _ = self.updateVideoFrame(blocking=True)

            # Moving the decoder and waiting on the frame for the new position
            # is not time the movie spent playing, so don't let the next
            # update charge it to the movie clock. Left in, it would push the
            # movie past the position asked for, and compound over a run of
            # seeks since `rewind`/`fastForward` work from where the last one
            # left off.
            self._lastFrameAbsTime = self._nextFlipTime()

    def rewind(self, seconds=1, blocking=True, log=True):
        """Rewind the video.

        Parameters
        ----------
        seconds : float
            Time in seconds to rewind from the current position. Default is 5
            seconds.
        blocking : bool
            Whether to wait for the frame at the new position before returning.
            If `False`, the frame is picked up by the next `draw()` instead and
            `isSeeking` stays set until it arrives. See `seek()`.
        log : bool
            Log this event.

        """
        newPts = self._movieTime - seconds
        self._movieTime = min(max(0.0, newPts), self.duration)
        # seek to the new position
        self.seek(self._movieTime, blocking=blocking)

    def fastForward(self, seconds=1, blocking=True, log=True):
        """Fast-forward the video.

        Parameters
        ----------
        seconds : float
            Time in seconds to fast forward from the current position. Default
            is 5 seconds.
        blocking : bool
            Whether to wait for the frame at the new position before returning.
            If `False`, the frame is picked up by the next `draw()` instead and
            `isSeeking` stays set until it arrives. See `seek()`.
        log : bool
            Log this event.

        """
        newPts = self._movieTime + seconds
        self._movieTime = min(max(0.0, newPts), self.duration)
        # seek to the new position
        self.seek(self._movieTime, blocking=blocking)

    def replay(self, blocking=True, log=True):
        """Replay the movie from the beginning.

        Parameters
        ----------
        blocking : bool
            Whether to wait for the frame at the new position before returning.
            If `False`, the frame is picked up by the next `draw()` instead and
            `isSeeking` stays set until it arrives. See `seek()`.
        log : bool
            Log this event.

        """
        self._movieTime = 0.0  # reset movie time
        self.seek(self._movieTime, blocking=blocking)
        self.play()

    def reset(self, blocking=True):
        """Reset the movie to its initial state.

        Parameters
        ----------
        blocking : bool
            Whether to wait for the frame at the new position before returning.
            If `False`, the frame is picked up by the next `draw()` instead and
            `isSeeking` stays set until it arrives. See `seek()`.

        """
        self._movieTime = 0.0  # reset movie time
        self.seek(self._movieTime, blocking=blocking)
        self._playbackStatus = NOT_STARTED  # reset playback status
        
    # --------------------------------------------------------------------------
    # Audio stream control methods
    #

    @property
    def muted(self):
        """`True` if the stream audio is muted (`bool`).
        """
        if self._decoderPlaysAudio:
            return self._player.muted
        else:
            if self._audioTrack is not None and hasattr(self._audioTrack, 'volume'):
                return self._audioTrack.volume == 0.0
            else:
                return False

    @muted.setter
    def muted(self, value):
        if self._decoderPlaysAudio:
            self._player.mute(value)
        else:
            if self._audioTrack is not None and hasattr(self._audioTrack, 'volume'):
                self._audioTrack.volume = 0.0 if value else self._volume

    def volumeUp(self, amount=0.05):
        """Increase the volume by a fixed amount.

        Parameters
        ----------
        amount : float or int
            Amount to increase the volume relative to the current volume.

        """
        if self._decoderPlaysAudio:
            currentVolume = self._player.volume
            self._player.setVolume(currentVolume + amount)
        else:
            if self._audioTrack is not None and hasattr(self._audioTrack, 'volume'):
                self._audioTrack.volume = min(self._audioTrack.volume + amount, 1.0)

    def volumeDown(self, amount=0.05):
        """Decrease the volume by a fixed amount.

        Parameters
        ----------
        amount : float or int
            Amount to decrease the volume relative to the current volume.

        """
        if self._decoderPlaysAudio:
            currentVolume = self._player.volume
            self._player.setVolume(currentVolume - amount)
        else:
            if self._audioTrack is not None and hasattr(self._audioTrack, 'volume'):
                self._audioTrack.volume = max(self._audioTrack.volume - amount, 0.0)

    @property
    def volume(self):
        """Volume for the audio track for this movie (`int` or `float`).
        """
        if self._decoderPlaysAudio:
            return self._player.volume
        else:
            if self._audioTrack is not None and hasattr(self._audioTrack, 'volume'):
                return self._audioTrack.volume
            else:
                return 0.0

    @volume.setter
    def volume(self, value):
        if self._decoderPlaysAudio:
            self._player.setVolume(value)
        else:
            if self._audioTrack is not None and hasattr(self._audioTrack, 'volume'):
                self._audioTrack.volume = value
            self._volume = value  # store the volume for later use when loading new movies

    # --------------------------------------------------------------------------
    # Video and playback information
    #

    @property
    def frameIndex(self):
        """Current frame index being displayed (`int`)."""
        return 0

    def getCurrentFrameNumber(self):
        """Get the current movie frame number (`int`), same as `frameIndex`.
        """
        return self.frameIndex

    @property
    def duration(self):
        """Duration of the loaded video in seconds (`float`). Not valid unless
        the video has been started.
        """
        if not self._player:
            return -1.0

        return self._player.getMetadata().duration

    @property
    def loopCount(self):
        """Number of loops completed since playback started (`int`). Incremented
        each time the movie begins another loop.

        Examples
        --------
        Compute how long a looping video has been playing until now::

            totalMovieTime = (mov.loopCount + 1) * mov.pts

        """
        if not self._player:
            return -1

        return self._loopCount

    @property
    def fps(self):
        """Movie frames per second (`float`)."""
        return self.getFPS()

    def getFPS(self):
        """Movie frames per second.

        Returns
        -------
        float
            Nominal number of frames to be displayed per second.

        """
        if not self._player:
            return 1.0

        return self._player.frameRate

    @property
    def videoSize(self):
        """Size of the video `(w, h)` in pixels (`tuple`). Returns `(0, 0)` if
        no video is loaded.
        """
        return self.frameSize

    @property
    def origSize(self):
        """Alias of `videoSize`
        """
        return self.videoSize

    @property
    def frameSize(self):
        """Size of the video `(w, h)` in pixels (`tuple`). Alias of `videoSize`.
        """
        if not self._player:
            return 0, 0

        return self._player.getMetadata().size

    @property
    def pts(self):
        """Presentation timestamp of the most recent frame (`float`).

        This value corresponds to the time in movie/stream time the frame is
        scheduled to be presented.

        """
        if not self._player:
            return -1.0

        return self._pts

    def getPercentageComplete(self):
        """Provides a value between 0.0 and 100.0, indicating the amount of the
        movie that has been already played (`float`).
        """
        return (self._movieTime / self.duration) * 100.0
    
    # --------------------------------------------------------------------------
    # Miscellaneous methods
    #

    def getSubtitleText(self):
        """Get the subtitle for the current frame.

        Returns
        -------
        str
            Subtitle for the current frame.

        """
        if not self._player:
            return ""

        return self._player.getSubtitle()
    
    def __del__(self):
        """Destructor for the MovieStim class.

        This function is called when the object is deleted. It closes the movie
        player and frees any resources used by the object.

        """
        self.unload()
    

def _closeAllMovieReaders():
    """Close all movie readers.

    This function explicitly closes movie reader interfaces that are presently 
    open, to free resources when the interpreter exits to reduce the chances of
    any subprocesses spawned by the interface being orphaned. 
    
    Do not call this directly, it is called automatically when the interpreter 
    exits (via `atexit`). If you do, all sorts of bad things will happen if
    there are any open movie readers still in use.

    """
    global _openMovieReaders

    for movieReader in _openMovieReaders:
        logging.debug(
            "Closing movie reader interface for file: {}".format(
                movieReader.filename))
        movieReader._freePlayer()


def _cancelAudioTrackLoaders():
    """Stop any audio tracks still decoding in the background, so that PyAV
    isn't left decoding while the interpreter shuts down."""
    for loader in list(_audioTrackLoaders):
        loader.cancel()


# try an close any players on exit
import atexit
atexit.register(_closeAllMovieReaders)   # call this when the program exits
atexit.register(_cancelAudioTrackLoaders)
    
    
if __name__ == "__main__":
    pass