#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'MovieStim',
    'MovieFileReader',
    'MovieMetadata',
    'MoviePlaybackError',
    'MovieFileNotFoundError',
    'MovieFileFormatError',
    'MovieAudioError',
    'backend',   # allow the user to get the current backend and set it
    'setBackend',
    'getBackend']


import ctypes
import functools
import math
import os.path
import sys
import threading
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


from .exceptions import (
    MoviePlaybackError, MovieFileNotFoundError, MovieFileFormatError,
    MovieAudioError)
from .metadata import MovieMetadata, NULL_MOVIE_METADATA
from .frame import (
    FRAME_BYTES_PER_PIXEL, _YUVFrameAdapter, _COLOR_MATRIX_KR_KB)
from .readers import (
    MovieFileReader, PREFERRED_VIDEO_LIB, SUPPORTED_VIDEO_LIBS)
from .readers._base import defaultTimeout, _openMovieReaders

# threshold to stop reporting dropped frames
reportNDroppedFrames = 10

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


@functools.lru_cache(maxsize=16)
def _yuvToRGBUniforms(colorMatrix, fullRange):
    """Matrix and offset converting YUV to RGB, for the shader frames are drawn
    with (see `psychopy.visual.shaders.fragYUVToRGB`).

    These match what `swscale` does. Sampling an 8-bit plane gives its code
    value over 255 (`t`), and the RGB is `matrix @ (t - offset)`.

    Parameters
    ----------
    colorMatrix : str
        `swscale` name of the colour matrix, see `_frameColorMatrix`.
    fullRange : bool
        Whether the samples are full range (0 to 255) rather than limited
        (16 to 235 for luma, 16 to 240 for chroma).

    Returns
    -------
    tuple
        The matrix as 9 floats in row order, and the offset as 3 floats.

    """
    kr, kb = _COLOR_MATRIX_KR_KB[colorMatrix]
    kg = 1.0 - kr - kb
    matrix = np.array([
        [1.0, 0.0, 2.0 * (1.0 - kr)],
        [1.0, -2.0 * kb * (1.0 - kb) / kg, -2.0 * kr * (1.0 - kr) / kg],
        [1.0, 2.0 * (1.0 - kb), 0.0]])

    if fullRange:
        scale = np.array([1.0, 1.0, 1.0])
        offset = np.array([0.0, 128.0, 128.0]) / 255.0
    else:
        scale = np.array([255.0 / 219.0, 255.0 / 224.0, 255.0 / 224.0])
        offset = np.array([16.0, 128.0, 128.0]) / 255.0

    return tuple((matrix * scale).ravel()), tuple(offset)


def _getYUVToRGBProgram(win):
    """The shader program frames uploaded as YUV are converted with on a window,
    made the first time it's needed (`tuple`).

    Returns
    -------
    tuple or None
        The program handle and a mapping of its uniform locations by name, or
        `None` if the program couldn't be made, in which case frames are
        converted to RGBA as they're decoded instead.

    """
    if not hasattr(win, '_movieYUVToRGBProgram'):
        from psychopy.visual import shaders

        try:
            # only defined for the legacy (fixed-function) pipeline, which
            # `MovieStim` draws with
            program = shaders.compileProgram(
                fragmentSource=shaders.fragYUVToRGB)
        except Exception as err:
            logging.warning(
                "Couldn't make the shader movies are converted to RGB with as "
                "they're drawn, so they'll be converted as they're decoded "
                "instead: {}".format(err))
            win._movieYUVToRGBProgram = None
        else:
            uniforms = {
                name: GL.glGetUniformLocation(program, name.encode())
                for name in ('uPlaneY', 'uPlaneU', 'uPlaneV', 'uYUVToRGB',
                             'uYUVOffset')}
            win._movieYUVToRGBProgram = (program, uniforms)

    return win._movieYUVToRGBProgram


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
        `False`. Only the `pyav` and `opencv` backends scale frames. Default
        is `True`.
    gpuColorConversion : bool
        Upload frames in the YUV they're decoded in, and convert them to RGB in
        a shader on the GPU, rather than converting them as they're decoded. That 
        saves the conversion, and leaves less than half as much to copy to the GPU 
        for each frame. Either way, colours are converted with the colour matrix 
        the movie is encoded with. Only the `pyav` backend does this, and only for
        movies in 8-bit planar YUV (as most are), others being converted as they're 
        decoded. `frameTexture` holds the frame as RGBA either way. Default is `True`.

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
                 gpuColorConversion=True,
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
        # size `(w, h)` of `_recentFrame` in pixels, and how it's laid out to
        # upload (see `_setRecentFrame`)
        self._recentFrameSize = None
        self._recentFrameLayout = None
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

        # whether frames are uploaded as YUV for a shader to convert, see
        # `_useGPUColorConversion`
        self._gpuColorConversion = bool(gpuColorConversion)
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
        # textures for the Y, U and V planes of frames uploaded as YUV, and the
        # framebuffer they're converted into `_textureId` through, see
        # `_setupPlaneTextures`
        self._planeTextureIds = None
        self._frameBufferId = GL.GLuint(0)
        self._vidWidth = self._vidHeight = 0  # set by `_setupTextureBuffers`
        self._nBufferBytes = 0
        # What the textures are for, as `_recentFrameLayout` describes frames,
        # and the colour matrix and range of the YUV last uploaded to them
        self._textureLayout = None
        self._textureColor = None

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

        # and in YUV, if they're to be converted to RGB on the GPU
        self._player.setOutputPixelFormat(
            'yuv' if self._useGPUColorConversion() else 'rgba')

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

        # Let the decoder fill its queue now, at the size and in the format the
        # frames are now to be decoded in, rather than as fast as it can while
        # the movie starts playing
        self._player.waitForDecodedFrames()

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

    def _useGPUColorConversion(self):
        """Whether frames are to be uploaded as YUV and converted to RGB by a
        shader as they're uploaded (`bool`), see `gpuColorConversion`."""
        if not self._gpuColorConversion:
            return False

        # the shader is made for the window's context
        self._selectWindow(self.win)

        return _getYUVToRGBProgram(self.win) is not None

    def _setRecentFrame(self, frameImage):
        """Make `frameImage` the frame to upload, and show from now on."""
        self._recentFrameImage = frameImage
        # frames scaled down as they're decoded give their size, and any others
        # are the movie's own size
        self._recentFrameSize = getattr(frameImage, 'size', None) or \
            tuple(self._player.getMetadata().size)

        if isinstance(frameImage, _YUVFrameAdapter):
            # uploaded as its planes, see `_uploadPlanes`
            self._recentFrame = frameImage.planes[0][0]  # the luma, to look at
            self._recentFrameAddr = None
            self._recentFrameLayout = ('yuv', tuple(
                (width, height, rowLength)
                for _, width, height, rowLength in frameImage.planes))
        else:
            # suggested by Alex Forrence (aforren1) originally in PR #6439 to use memoryview
            videoBuffer = frameImage.to_memoryview()[0].memview
            videoFrameArray = np.frombuffer(videoBuffer, dtype=np.uint8)
            self._recentFrame = videoFrameArray # most recent frame
            # cached here since `ndarray.ctypes` builds a new helper object
            # on every access, and the pixel transfer runs every draw
            self._recentFrameAddr = videoFrameArray.ctypes.data
            self._recentFrameLayout = ('rgba',) + tuple(self._recentFrameSize)

        self._frameNeedsUpload = True

    @property
    def frameTexture(self):
        """Texture ID for the current video frame (`GLuint`). You can use this
        as a video texture. However, you must periodically call
        `updateVideoFrame` to keep this up to date.

        The texture is the size of the frames given to it, which with
        `downscaleFrames` is the size the movie is drawn at (if smaller than
        its own), and is replaced with a new one if that changes.

        It holds the frame as RGBA either way frames are converted to RGB. With
        `gpuColorConversion`, frames are uploaded as YUV and converted into it
        on the GPU as they are.

        """
        return self._textureId
    
    def updateVideoFrame(self, blocking=None):
        """Get the frame for the movie's present position, and upload it to
        `frameTexture` if it's a new one.

        `draw()` does this itself, so this is only needed to keep
        `frameTexture` up to date without drawing the movie.

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
            If `True`, there is a frame for the present position, now in
            `frameTexture`. If `False`, there isn't one yet, and the last frame
            should be kept on-screen.

        """
        # the textures belong to the movie's window
        self._selectWindow(self.win)

        return self._updateVideoFrame(blocking)

    def _updateVideoFrame(self, blocking=None):
        """`updateVideoFrame()`, with the window already chosen by the caller
        (which `draw()` does, being able to draw to any window)."""
        # get the current movie frame for the video time
        self._updateMoviePos()  # update the movie position

        if blocking is None:
            # Waiting is worthwhile when the decoder is merely a little behind
            # during playback, but not while catching up from a seek the caller
            # asked not to block on; there the previous frame is shown and this
            # is retried on the next draw.
            blocking = not self._player.isSeeking

        # Decoding is deferred until the frame has been copied to the GPU
        # below, see `MovieFileReader.decodeAhead()`
        frameData = self._player.getFrame(
            self._movieTime + _frameSampleOffset(
                self.win.monitorFramePeriod, self._player.frameInterval),
            blocking=blocking,
            deferDecoding=True)
        
        if frameData is None:  # handle frame not available by showing last frame
            # if self._playbackStatus == PLAYING:  # something went wrong
            #     self._playbackStatus = SEEKING
            self._player.decodeAhead()

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

        # into `frameTexture` if it's new, after which the decoder can carry on
        self._pixelTransfer()
        self._player.decodeAhead()

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
        self._recentFrameLayout = None
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

            if self._planeTextureIds is not None:
                GL.glDeleteTextures(
                    len(self._planeTextureIds), self._planeTextureIds)

            if self._frameBufferId.value > 0:
                GL.glDeleteFramebuffers(1, self._frameBufferId)
                self._frameBufferId = GL.GLuint()

        except Exception:  # can happen when unloading or shutting down
            pass

        self._planeTextureIds = None
        self._vidWidth = self._vidHeight = 0
        self._nBufferBytes = 0
        self._textureLayout = None

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
        self._createFrameTexture(vidWidth, vidHeight)

        GL.glFlush()  # make sure all buffers are ready

        self._textureLayout = ('rgba', vidWidth, vidHeight)

    def _createFrameTexture(self, width, height):
        """Make the RGBA texture frames are drawn from, `_textureId`, which is
        what `frameTexture` gives.
        
        Parameters
        ----------
        width, height : int
            The size of the texture in pixels.
        
        """
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glGenTextures(1, ctypes.byref(self._textureId))
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._textureId)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGBA8,
            width, height,  # frame dims in pixels
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

    def _setupPlaneTextures(self, planes):
        """Make the textures and pixel buffer for frames uploaded as YUV, one
        single channel texture for each plane, along with the RGBA texture a
        shader converts them into (see `_convertPlanesToRGBA`) and the
        framebuffer it does so through. Any made before are deleted first.

        Parameters
        ----------
        planes : tuple
            The size `(width, height, rowLength)` of each plane in pixels, as
            `_recentFrameLayout` gives them.

        Returns
        -------
        bool
            `True` if the framebuffer could be made, which it should always
            be. If not, frames are decoded as RGBA from then on instead.

        """
        self._deleteTextureObjects()

        # one pixel buffer for all the planes, each row as long as decoded
        nBufferBytes = sum(rowLength * height for _, height, rowLength in planes)
        GL.glGenBuffers(1, ctypes.byref(self._pixbuffId))
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, self._pixbuffId)
        GL.glBufferData(
            GL.GL_PIXEL_UNPACK_BUFFER, nBufferBytes, None, GL.GL_STREAM_DRAW)
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)

        # Converted at their own size, so this only comes into it for chroma
        # subsampled planes, which are interpolated up to the luma's size
        # whether or not the movie is interpolated as it's drawn
        textureIds = (GL.GLuint * len(planes))()
        GL.glGenTextures(len(planes), textureIds)
        for textureId, (width, height, _) in zip(textureIds, planes):
            GL.glBindTexture(GL.GL_TEXTURE_2D, textureId)
            GL.glTexImage2D(
                GL.GL_TEXTURE_2D, 0, GL.GL_LUMINANCE8, width, height, 0,
                GL.GL_LUMINANCE, GL.GL_UNSIGNED_BYTE, None)
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
            # to the edge rather than the border colour, which would otherwise
            # tint the edges of the picture through the chroma
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        self._planeTextureIds = textureIds
        self._vidWidth, self._vidHeight = planes[0][0], planes[0][1]
        self._nBufferBytes = nBufferBytes

        # the RGBA texture the planes are converted into, and the framebuffer
        # they're drawn into it through
        self._createFrameTexture(self._vidWidth, self._vidHeight)
        prevFrameBuffer = GL.GLint()
        GL.glGetIntegerv(GL.GL_FRAMEBUFFER_BINDING, ctypes.byref(prevFrameBuffer))
        GL.glGenFramebuffers(1, ctypes.byref(self._frameBufferId))
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self._frameBufferId)
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D,
            self._textureId, 0)
        status = GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, prevFrameBuffer.value)

        if status != GL.GL_FRAMEBUFFER_COMPLETE:
            logging.error(
                "Couldn't make the framebuffer movie frames are converted to "
                "RGB through (status {:#x}), so they'll be converted as they're "
                "decoded instead.".format(status))
            self._deleteTextureObjects()
            self._player.setOutputPixelFormat('rgba')
            return False

        self._textureLayout = ('yuv', tuple(planes))

        return True

    def _pixelTransfer(self, forceRefresh=False):
        """Copy pixel data from video frame to texture.

        This is called when a new frame is available. The pixel data is copied
        from the video frame to the texture store on the GPU.

        This happens whether or not the movie is playing, so that a frame
        sought to while it's paused (or before it starts) shows, and is in
        `frameTexture`. While paused the frame doesn't otherwise change, so
        there's nothing new to copy.

        Parameters
        ----------
        forceRefresh : bool
            If `True`, the pixel data will be copied to the texture even if it
            already holds this frame.

        """
        if self._recentFrame is None:
            return  # no frame to copy

        if not (forceRefresh or self._frameNeedsUpload):
            # The frame already on the GPU is the one to show. This is the
            # common case whenever the display refresh rate is higher than the
            # movie frame rate (e.g. a 30 FPS movie on a 60 Hz window), where
            # re-uploading would burn a whole-frame copy and a texture transfer
            # per draw to no effect.
            return

        # The textures follow the size and format of the frames, which change
        # when the movie comes to be drawn at another size (see
        # `downscaleFrames`), or decoded in another format
        if self._recentFrameLayout != self._textureLayout:
            if self._recentFrameLayout[0] == 'yuv':
                if not self._setupPlaneTextures(self._recentFrameLayout[1]):
                    self._frameNeedsUpload = False  # shown once RGBA ones come
                    return
            else:
                self._setupTextureBuffers(*self._recentFrameLayout[1:])

        if self._recentFrameLayout[0] == 'yuv':
            self._uploadPlanes()
            return

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

    def _uploadPlanes(self):
        """Copy the planes of a frame decoded as YUV to their textures, see
        `_setupPlaneTextures`."""
        frameImage = self._recentFrameImage
        planes = frameImage.planes

        for samples, _, height, rowLength in planes:
            if samples.nbytes < rowLength * height:
                logging.error(
                    "Movie frame plane is smaller than its size says, "
                    "skipping the pixel transfer.")
                self._frameNeedsUpload = False
                return

        # all the planes into the pixel buffer in one go, as with RGBA frames
        # (see `_pixelTransfer`), their rows as long as they were decoded
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, self._pixbuffId)
        GL.glBufferData(
            GL.GL_PIXEL_UNPACK_BUFFER, self._nBufferBytes, None,
            GL.GL_STREAM_DRAW)
        bufferAddr = ctypes.cast(
            GL.glMapBuffer(GL.GL_PIXEL_UNPACK_BUFFER, GL.GL_WRITE_ONLY),
            ctypes.c_void_p).value

        offsets = []
        offset = 0
        for samples, _, height, rowLength in planes:
            nBytes = rowLength * height
            ctypes.memmove(bufferAddr + offset, samples.ctypes.data, nBytes)
            offsets.append(offset)
            offset += nBytes

        GL.glUnmapBuffer(GL.GL_PIXEL_UNPACK_BUFFER)

        # and from there to each plane's texture, the row length telling GL to
        # skip any padding at the end of each row
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        for textureId, offset, (_, width, height, rowLength) in zip(
                self._planeTextureIds, offsets, planes):
            GL.glPixelStorei(GL.GL_UNPACK_ROW_LENGTH, rowLength)
            GL.glBindTexture(GL.GL_TEXTURE_2D, textureId)
            GL.glTexSubImage2D(
                GL.GL_TEXTURE_2D, 0, 0, 0, width, height,
                GL.GL_LUMINANCE, GL.GL_UNSIGNED_BYTE, ctypes.c_void_p(offset))

        # back to the defaults, which other stimuli upload with
        GL.glPixelStorei(GL.GL_UNPACK_ROW_LENGTH, 0)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 4)
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        self._textureColor = (frameImage.colorMatrix, frameImage.fullRange)
        self._convertPlanesToRGBA()
        self._frameNeedsUpload = False  # textures now match `_recentFrame`

    def _convertPlanesToRGBA(self):
        """Convert the planes of the frame just uploaded (see `_uploadPlanes`)
        to RGB, into the RGBA texture the movie is drawn from and
        `frameTexture` gives.

        The planes are drawn through the shader into that texture at its own
        size, which leaves it just as if the frame had been converted to RGBA
        as it was decoded, the picture's top row first. Everything this changes
        is put back afterwards, including the framebuffer bound (which may be
        the window's own).

        """
        program, uniforms = _getYUVToRGBProgram(self.win)

        prevFrameBuffer = GL.GLint()
        GL.glGetIntegerv(GL.GL_FRAMEBUFFER_BINDING, ctypes.byref(prevFrameBuffer))
        GL.glPushAttrib(
            GL.GL_ENABLE_BIT | GL.GL_VIEWPORT_BIT | GL.GL_COLOR_BUFFER_BIT |
            GL.GL_CURRENT_BIT | GL.GL_TRANSFORM_BIT)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self._frameBufferId)
        GL.glViewport(0, 0, self._vidWidth, self._vidHeight)
        # written as is, whatever the window is set to do with what's drawn
        for capability in (GL.GL_BLEND, GL.GL_SCISSOR_TEST, GL.GL_DEPTH_TEST,
                           GL.GL_STENCIL_TEST, GL.GL_ALPHA_TEST,
                           GL.GL_CULL_FACE):
            GL.glDisable(capability)
        GL.glColorMask(GL.GL_TRUE, GL.GL_TRUE, GL.GL_TRUE, GL.GL_TRUE)
        GL.glColor4f(1.0, 1.0, 1.0, 1.0)

        for unit, textureId in enumerate(self._planeTextureIds):
            GL.glActiveTexture(GL.GL_TEXTURE0 + unit)
            GL.glBindTexture(GL.GL_TEXTURE_2D, textureId)

        GL.glUseProgram(program)
        for unit, name in enumerate(('uPlaneY', 'uPlaneU', 'uPlaneV')):
            GL.glUniform1i(uniforms[name], unit)
        matrix, offset = _yuvToRGBUniforms(*self._textureColor)
        GL.glUniformMatrix3fv(
            uniforms['uYUVToRGB'], 1, GL.GL_TRUE, (GL.GLfloat * 9)(*matrix))
        GL.glUniform3f(uniforms['uYUVOffset'], *offset)

        # A quad over the whole texture. The planes' rows go top down, as they
        # were decoded, and so do the texture's, as frames decoded as RGBA are
        # uploaded to it.
        quad = (GL.GLfloat * 20)(
            0, 0, -1, -1, 0,  # texture coords, vertex
            1, 0, 1, -1, 0,
            1, 1, 1, 1, 0,
            0, 1, -1, 1, 0)
        GL.glClientActiveTexture(GL.GL_TEXTURE0)
        GL.glPushClientAttrib(GL.GL_CLIENT_VERTEX_ARRAY_BIT)
        GL.glInterleavedArrays(GL.GL_T2F_V3F, 0, quad)
        GL.glDrawArrays(GL.GL_QUADS, 0, 4)
        GL.glPopClientAttrib()

        GL.glUseProgram(0)
        for unit in reversed(range(len(self._planeTextureIds))):
            GL.glActiveTexture(GL.GL_TEXTURE0 + unit)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, prevFrameBuffer.value)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPopMatrix()
        GL.glPopAttrib()

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

        # Frames uploaded as YUV have been converted into the same texture by
        # now, see `_convertPlanesToRGBA`
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

        # update the video frame (uploading it if it's new) and draw it
        self._updateVideoFrame()
        self._drawRectangle()  # draw the texture to the target window

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