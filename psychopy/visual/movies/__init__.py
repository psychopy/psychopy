#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['MovieStim']


import ctypes
import os.path
from pathlib import Path

import tempfile
import time

from psychopy import prefs
from psychopy.tools.filetools import pathToString, defaultStim
from psychopy.visual.basevisual import (
    BaseVisualStim, DraggingMixin, ContainerMixin, ColorMixin
)
from psychopy.constants import FINISHED, NOT_STARTED, PAUSED, PLAYING, STOPPED
from psychopy import core

from .players import getMoviePlayer
from .metadata import MovieMetadata, NULL_MOVIE_METADATA
from .frame import MovieFrame, NULL_MOVIE_FRAME_INFO

from psychopy import logging
import numpy as np
import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl

# threshold to stop reporting dropped frames
reportNDroppedFrames = 10

# constants for use with ffpyplayer
FFPYPLAYER_STATUS_EOF = 'eof'
FFPYPLAYER_STATUS_PAUSED = 'paused'

PREFERRED_VIDEO_LIB = 'ffpyplayer'


# ------------------------------------------------------------------------------
# Classes
#

# Keep track of movie readers here. This is used to close all movie readers
# when the main thread exits. We identify movie readers by hashing the filename
# they are presently reading from.
_openMovieReaders = set()


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
    
    """
    def __init__(self, filename, size, frameRate, duration, colorFormat):
        self._filename = filename
        self._size = size
        self._frameRate = frameRate
        self._duration = duration
        self._colorFormat = colorFormat

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
    def duration(self):
        """The duration of the movie in seconds (`float`).

        """
        return self._duration

    @property
    def colorFormat(self):
        """The color format of the movie (`str`).

        """
        return self._colorFormat
    

class MovieFileReader:
    """Read movie frames from file.

    This class allows for the reading of movie frames from a file for playback
    or analysis.

    This class does not expose playback controls, simply provide a presentation
    timestamp and the reader will return the frame data at that time. The reader
    will automatically seek to the correct frame in the movie file and return
    the frame data. The reader is optimized to read frames in sequence, so 
    specifying monotonic timestamps will yield the best performance. The reader will
    
    If the movie file contains an audio track, the audio track will be extracted
    when the movie is opened and written to disk. This is required to allow for 
    PyshcoPy to play the audio track in sync with the video frames.

    Parameters
    ----------
    filename : str
        The name (or path) of the file to read the movie from.
    decoderLib : str
        The library to use to handle decoding the movie. The default is
        'ffpyplayer'.
    decoderOpts : dict or None
        A dictionary of options to pass to the decoder. These option can be used
        to control the quality of the movie, for example. The options depend on
        the `decoderLib` in use. If `None`, the reader will use the default
        options for the backend.

    Notes
    -----
    * If `decoderLib='ffpyplayer'`, audio playback is handled externally by 
      SDL2. This means that audio playback is not synchronized with frame 
      presentation in PsychoPy. However, playback will not begin until the audio 
      track starts playing.
    * Do not access private attributes or methods of this class directly since 
      doing so is not thread-safe. Use the public methods provided by this class
      to interact with the movie reader.

    """
    def __init__(self, 
                 filename,
                 decoderLib='ffpyplayer', 
                 decoderOpts=None):
        
        self._filename = filename
        self._decoderLib = decoderLib
        self._decoderOpts = {} if decoderOpts is None else decoderOpts

        # thread for the reader
        self._player = None  # player interface object

        # movie information
        self._frameInterval = 0.0  # seconds
        self._srcFrameSize = (-1, -1)  # w, h pixels
        self._frameRate = -1.0  # Hz
        self._duration = -1.0  # seconds
        self._srcPixelFormat = None  

        self._metadata = None  # metadata object
        
        # store decoded video segmenets in memory
        self._videoSegments = []

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
            raise ValueError('Movie metadata not available. Movie not open.')

        return self._metadata

    def _openFFPyPlayer(self):
        """Open a movie reader using FFPyPlayer.

        This function opens the movie file and extracts metadata about the movie
        file. Call `startDecoding()` to begin decoding frames in a background 
        thread.

        """
        # import in the class too avoid hard dependency on ffpyplayer
        try:
            from ffpyplayer.player import MediaPlayer
        except ImportError:
            raise ImportError(
                'The `ffpyplayer` library is required to read movie files with '
                '`decoderLib=ffpyplayer`.')

        logging.info("Opening movie file: {}".format(self._filename))

        # default options
        defaultFFOpts = {
            'paused': True,
            'sync': 'audio',
            'an': False,
            'volume': 1.0,
            'loop': 1,
            'infbuf': True
        }

        # merge user settings with defaults, user settings take precedence
        defaultFFOpts.update(self._decoderOpts)
        self._decoderOpts = defaultFFOpts

        # create media player
        self._player = MediaPlayer(
            self._filename,
            ff_opts=self._decoderOpts)

        self._player.set_pause(False)

        # wait for valid metadata to be available
        logging.debug("Waiting for movie metadata...")
        while 1:
            movieMetadata = self._player.get_metadata()
            if movieMetadata['src_vid_size'] != (0, 0):
                break

        # # warmup, takes a while before the video starts playing
        # while 1:
        #     frame, _ = self._player.get_frame()
        #     if frame != None:
        #         break

        self._player.seek(0.0, relative=False, accurate=True)
        self._player.set_pause(True)  # pause the player again
        # self._player.set_pause(False)  # pause the player again

        # movie metadata
        numer, denom = movieMetadata['frame_rate']
        self._srcFrameSize = movieMetadata['src_vid_size']
        self._frameRate = numer / denom
        self._frameInterval = 1.0 / self._frameRate
        self._duration = movieMetadata['duration']
        self._srcPixelFormat = movieMetadata['src_pix_fmt']

        self._metadata = MovieMetadata(
            self._filename,
            self._srcFrameSize,
            self._frameRate,
            self._duration,
            self._srcPixelFormat)

        if isinstance(self._srcPixelFormat, bytes):
            self._srcPixelFormat = self._srcPixelFormat.decode('utf-8')

        logging.debug("Movie metadata: {}".format(movieMetadata))

    def open(self):
        """Open the movie file for reading.

        """
        logging.debug("Using decoder library: {}".format(self._decoderLib))
        if self._decoderLib == 'ffpyplayer':
            self._openFFPyPlayer()
        elif self._decoderLib == 'opencv':
            self._openOpenCV()
        else:
            raise ValueError(
                'Unknown decoder library: {}'.format(self._decoderLib))
        
        # register the reader with the global list of open movie readers
        if self in _openMovieReaders:
            raise RuntimeError(
                'Movie reader already open for file: {}'.format(self._filename))
        
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
        """
        self._player.close_player()  # close the player
        self._player = None  # clear the player

        # clear frames from store
        self._cleanUpFrameStore()

        self._metadata = None  # clear metadata

        # remove the reader from the global list of open movie readers
        if self in _openMovieReaders:
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
            self._videoSegments.clear()
            return

        # remove all frames we have already presented
        for i in range(len(self._videoSegments) - 1, -1, -1):
            _, pts, _ = self._videoSegments[i]
            if pts < keepAfterPTS:
                del self._videoSegments[i]
            else:
                break
        
    # --------------------------------------------------------------------------
    # Backend-specific decoding routines
    #

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

    def _startFFPyPlayer(self):
        """Start decoding video frames using FFPyPlayer.

        This function spawns the background thread to begin reading frames from
        the movie file. If the thread is already running, this function will
        do nothing.

        """
        if not self.isOpen:
            raise ValueError('Movie reader is not open. Cannot start decoding.')

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
        return frameIndex * self._frameInterval

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
        return int(pts / self._frameInterval)

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
            The presentation timestamp (PTS) of the frame in seconds after 
            seeking.

        """
        reqPTS = min(max(0.0, reqPTS), self._duration)
        print('Seeking to PTS: {}'.format(reqPTS))

        if self._player is None:
            raise ValueError('Movie reader is not open. Cannot seek.')
        
        # check if the provided PTS is valid
        if reqPTS < 0.0 or reqPTS > self._duration:
            raise ValueError('Invalid PTS: {}'.format(reqPTS))
        
        # clear the frame store
        self._cleanUpFrameStore()

        # seek to the desired PTS
        # self._player.set_pause(True)
        self._player.seek(
            reqPTS, 
            relative=False, 
            seek_by_bytes=False, 
            accurate=True)
            # thisPTS = self._player.get_pts()
            # if abs(thisPTS - reqPTS) < 0.001:
            #     break
        
        return self._player.get_pts()
    
    def _restartFFPyPlayer(self):
        """Restart the FFPyPlayer decoder.

        This function restarts the FFPyPlayer decoder. This is useful if the
        decoder has stopped working or if the movie file has changed.

        """
        self._seekFFPyPlayer(0.0)  # seek to the beginning of the movie

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
        if self._player is None:
            raise ValueError('Movie reader is not open. Cannot pause.')

        self._player.set_pause(bool(state))

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
        if self._decoderLib == 'ffpyplayer':
            self._seekFFPyPlayer(pts)
        elif self._decoderLib == 'opencv':  # rough in support for opencv
            raise NotImplementedError(
                'The `opencv` library is not supported for movie reading.')
        else:
            raise ValueError(
                'Unknown decoder library: {}'.format(self._decoderLib))

    @property
    def memoryUsed(self):
        """Get the amount of memory used for cache.

        Returns
        -------
        int
            The amount of memory used by the movie reader in bytes.

        """
        # sum of bytes used by video segments
        totalFramesDecoded = len(self._videoSegments)
        pixelSize = 3 if 'rgb' in self._srcPixelFormat else 4
        pixelCount = self._srcFrameSize[0] * self._srcFrameSize[1]

        return totalFramesDecoded * pixelCount * pixelSize

    def clearSegments(self):
        """Clear all buffered video segments.

        This function clears all buffered video segments from memory. This is
        useful if you want to free up memory used by the video segment buffer.

        """
        self._videoSegments.clear()
    
    def _getFrameFFPyPlayer(self, reqPTS=0.0):
        """Get a frame from the movie file using FFPyPlayer.

        This method gets the desired frame from the movie file. If it has not
        been decoded yet, this function will ensure the frame is decoded and 
        made available.

        Parameters
        ----------
        reqPTS : float
            The presentation timestamp (PTS) of the frame to get in seconds.
        dropFrame : bool
            If `True`, the frame is dropped if it is not available, and the 
            most recent frame will be returned immediately. If `False`, the 
            function will block until the desired frame is returned.

        Returns
        -------
        tuple
            Video data.

        """
        def _convertFrameToRGB(frame):
            """Convert a frame to RGB format.

            This function converts a frame to RGB format. The frame is returned
            as a Numpy array. The resulting array will be in the correct format
            to upload to OpenGL as a texture.

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

            rgbImg = SWScale(
                self._metadata.size[0], 
                self._metadata.size[1], 
                frame.get_pixel_format(), 
                ofmt='rgb24').scale(frame)
            
            return rgbImg
        
        def _getFrameFromStore(reqPTS):
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
            numpy.ndarray
                The converted frame in RGB format.

            """
            for img, pts, status in self._videoSegments:
                if pts <= reqPTS < pts + self._frameInterval:
                    return (img, pts, status)

        # check if we have a player object, return None if not
        if self._player is None:
            return None
            # raise ValueError('Movie reader is not open. Cannot grab frame.')
        
        # normalzie the PTS to be between 0 and the duration of the movie
        reqPTS = min(max(0.0, reqPTS), self._duration + self._frameInterval)

        # check if we have the frame in the store
        frame = _getFrameFromStore(reqPTS)
        if frame is not None:
            return frame
        
        while 1:  # keep getting frames until we reach the desired PTS
            # get the next frame                    
            frame, status = self._player.get_frame()

            if status == 'eof':
                # self._player.seek(0.0, relative=False, accurate=True)
                # print('EOF reached, seeking to beginning')
                # self._player.set_pause(False)  # pause the player again
                if self._streamEOFCallback is not None:
                    self._streamEOFCallback()
                self._cleanUpFrameStore()
                break
            elif status == 'paused':
                break

            if frame is None:
                break 
            
            img, curPts = frame  # extract frame information

            # if we have gotten the frame we are looking for, return it
            if curPts + self._frameInterval >= reqPTS:
                self._videoSegments.append(
                    (_convertFrameToRGB(img), curPts, status))

        return _getFrameFromStore(reqPTS)
    
    def getFrame(self, pts=0.0):
        """Get a frame from the movie file at the specified presentation 
        timestamp.

        Parameters
        ----------
        pts : float or None
            The presentation timestamp (PTS) of the frame to get in seconds.
            Timestamps can be as precise as six decimal places.
        dropFrame : bool
            If `True`, the frame is dropped if it is not available, and the 
            most recent frame will be returned immediately. If `False`, the 
            function will block until the desired frame is returned.

        Returns
        -------
        tuple
            Video data.

        """
        if self._decoderLib == 'ffpyplayer':
            return self._getFrameFFPyPlayer(pts)

    def __del__(self):
        """Close the movie file when the object is deleted.
        """
        self.close()


class MovieStim(BaseVisualStim, DraggingMixin, ColorMixin, ContainerMixin):
    """Class for presenting movie clips as stimuli.

    This class is used to present movie clips loaded from file as stimuli in 
    PsychoPy.

    Parameters
    ----------
    win : :class:`~psychopy.visual.Window`
        Window the video is being drawn to.
    filename : str
        Name of the file or stream URL to play. If an empty string, no file will
        be loaded on initialization but can be set later.
    movieLib : str or None
        Library to use for video decoding. By default, the 'preferred' library
        by PsychoPy developers is used. Default is `'ffpyplayer'`. An alert is
        raised if you are not using the preferred player.
    audioLib : str or None
        Library to use for audio decoding. By default, 'soundfile' is used.
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

    """
    def __init__(self,
                 win,
                 filename="",
                 movieLib=u'ffpyplayer',
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
                 autoStart=True):

        # # check if we have the VLC lib
        # if not haveFFPyPlayer:
        #     raise ImportError(
        #         'Cannot import package `ffpyplayer`, therefore `FFMovieStim` '
        #         'cannot be used this session.')

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
        self._movieLib = movieLib
        self._decoderOpts = {}
        self._player = None  # player interface object
        self._filename = pathToString(filename)
        self._volume = volume
        self._noAudio = noAudio  # cannot be changed
        self.loop = loop
        self._recentFrame = None
        self._autoStart = autoStart
        self._isLoaded = False
        self._pts = 0.0
        self._movieTime = 0.0   # current movie position in seconds
        self._lastFrameAbsTime = -1.0  # absolute time of the last frame

        # audio stuff
        if audioLib is None and self._movieLib == 'ffpyplayer':
            self._audioLib = 'sdl2'
        else:
            self._audioLib = audioLib

        self._audioTempFile = None  # audio extracted from the movie
        self._audioSamples = []  # audio samples from the movie 
        self._audioReader = None  # audio reader object
        self._audioSampleRate = 44100  # audio sample rate
        self._audioChannels = 2  # number of audio channels

        # OpenGL data
        self.interpolate = interpolate
        self._texFilterNeedsUpdate = True
        self._metadata = NULL_MOVIE_METADATA
        self._pixbuffId = GL.GLuint(0)
        self._textureId = GL.GLuint(0)

        # load a file if provided, otherwise the user must call `setMovie()`
        self._filename = pathToString(filename)
        if self._filename:  # load a movie if provided
            self.loadMovie(self._filename)

        self.autoLog = autoLog

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
        return self._player.metadata.frameRate

    @property
    def _hasPlayer(self):
        """`True` if a media player instance is started.
        """
        # use this property to check if the player instance is started in
        # methods which require it
        return self._player is not None
    
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
                raise FileNotFoundError("Cannot open movie file `{}`".format(
                    filename))
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

        # Extact the audio track so we can read samples from it. This needs to
        # be done before the movie is opened by the player to avoid file access
        # issues. The audio track is extracted to a temporary file which is
        # deleted when the movie is closed.

        disableAudio = False
        if not self._noAudio and self._audioLib not in ('sdl', 'sdl2'):
            # if using SDL, playback is handled by the ffpyplayer library so we
            # don't need to extract the audio track or setup the audio stream
            self._extractAudioTrack()
            disableAudio = True

        self._decoderOpts['an'] = disableAudio  

        # Create the movie player interface, this is what decodes movie frames
        # in the background. We disable audio playback since we are using the
        # our own audio library for playback.

        self._player = MovieFileReader(
            filename=self._filename,
            decoderLib=self._movieLib,
            decoderOpts=self._decoderOpts)
        
        # Open the player, this will get metadata about the movie and start
        # decoding frames in the background.
        
        self._player.open()
        
        logging.debug(
            "Movie file opened in {:.2f} seconds".format(
                time.time() - t0))

        # Setup the OpenGL buffers for the movie frames. The sizes of the 
        # buffers are determined by the size of the movie frames obtained from
        # the player.

        self._freeBuffers()  # free buffers (if any) before creating a new one
        self._setupTextureBuffers()

        self._isLoaded = True

    def _setupAudioStream(self):
        """Setup the audio stream for the movie.
        """
        pass

    def _pushAudioSamples(self):
        """Push audio samples to the audio buffer.

        """
        if self._noAudio:
            return

    def _extractAudioTrack(self):
        """Extract the audio track from the movie file.

        This function extracts the audio track from the movie file and writes
        it to a temporary file. The temporary file is used to play the audio
        track in sync with the video frames.

        """
        t0 = time.time()
        logging.debug("Extracting audio track from movie file: {}".format(
            self._filename))

        # Create a temporary file where the audio track will be written to. The 
        # file will be deleted when the movie is closed.
        self._audioTempFile = tempfile.NamedTemporaryFile(
            suffix='.wav',
            delete=False)
        
        # use moviepy to extract the audio track
        import moviepy as mp

        videoClip = mp.VideoFileClip(
            self._filename)
        audioTrackData = videoClip.audio

        audioTrackData.write_audiofile(
            self._audioTempFile.name,
            codec='pcm_s16le',
            fps=44100,
            nbytes=2,
            logger=None)
        
        videoClip.close()
        self._audioTempFile.close()

        logging.warning(
            "Audio track written to temporary file: {} ({} bytes)".format(
                self._audioTempFile.name, 
                os.path.getsize(self._audioTempFile.name)))

        logging.warning(
            "Audio track extraction completed in {:.2f} seconds".format(
                time.time() - t0))
        
        # use soundfile to read the audio samples from the temporary file
        import soundfile as sf
        samples, sr = sf.read(
            self._audioTempFile.name,
            dtype='float32',
            always_2d=True)
        self._audioSampleRate = sr
        self._audioSamples = samples

        # compute the size of the audio samples in bytes
        audioSize = self._audioSamples.nbytes

        logging.debug(
            "Audio track size: {} bytes".format(audioSize))

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
        self._player.close()
        self._freeBuffers()  # free buffer before creating a new one
        self._isLoaded = False

    @property
    def frameTexture(self):
        """Texture ID for the current video frame (`GLuint`). You can use this
        as a video texture. However, you must periodically call
        `updateVideoFrame` to keep this up to date.

        """
        return self._textureId

    def _updateMoviePos(self):
        """Update the movie position.

        This function updates the movie position. The movie position is the
        presentation timestamp (PTS) of the current frame. The PTS is updated
        when the movie is played or paused.

        """
        now = core.getTime()

        if self.status == PLAYING:
            # determine the current movie time
            incr = now - self._lastFrameAbsTime
            self._movieTime += now - self._lastFrameAbsTime
        elif self.status == STOPPED:
            self._movieTime = 0.0

        # if paused, the movie time does not advance but we still need to
        # update the last frame time
        self._lastFrameAbsTime = now  # always updates 

    def updateVideoFrame(self):
        """Update the present video frame. The next call to `draw()` will make
        the retrieved frame appear.

        Returns
        -------
        bool
            If `True`, the video texture has been updated and the frame index is
            advanced by one. If `False`, the last frame should be kept
            on-screen.

        """
        # get the current movie frame for the video time
        self._updateMoviePos()  # update the movie position

        frameData = self._player.getFrame(self._movieTime)
        
        if frameData is None:
            return self._recentFrame
        
        frameImage, pts, _ = frameData

        if frameImage is not None:
            videoBuffer = frameImage.to_memoryview()[0].memview
            videoFrameArray = np.frombuffer(videoBuffer, dtype=np.uint8)
            self._recentFrame = videoFrameArray # most recent frame
        else:
            self._recentFrame = None

        # only do a pixel transfer on valid frames
        if self._recentFrame is not None:
            self._pts = pts  # store the current PTS
            self._pixelTransfer()

        return self._recentFrame
            
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

        # self._movieTime = self._pts  # get the current movie time
        # self._lastFrameTime = core.getTime()  # get the current time

        # handle autoplay
        # if self._autoStart and self.isNotStarted:
        #    self.play()

        # update the video frame and draw it to a quad
        _ = self.updateVideoFrame()
        self._drawRectangle()  # draw the texture to the target window

        return True

    # --------------------------------------------------------------------------
    # Video playback controls and status
    #

    @property
    def isPlaying(self):
        """`True` if the video is presently playing (`bool`).
        """
        # Status flags as properties are pretty useful for users since they are
        # self documenting and prevent the user from touching the status flag
        # attribute directly.
        #
        if self._player is not None:
            return self._player.isPlaying

        return False

    @property
    def isNotStarted(self):
        """`True` if the video may not have started yet (`bool`). This status is
        given after a video is loaded and play has yet to be called.
        """
        if self._player is not None:
            return self._player.isNotStarted

        return True

    @property
    def isStopped(self):
        """`True` if the video is stopped (`bool`). It will resume from the
        beginning if `play()` is called.
        """
        if self._player is not None:
            return self._player.isStopped

        return False

    @property
    def isPaused(self):
        """`True` if the video is presently paused (`bool`).
        """
        if self._player is not None:
            return self._player.isPaused

        return False

    @property
    def isFinished(self):
        """`True` if the video is finished (`bool`).
        """
        return False
    
    @property
    def movieTime(self):
        """Current movie time in seconds (`float`). This is the time since the
        movie started playing. If the movie is paused, this time will not
        advance.
        """
        return self._movieTime

    def play(self, log=True):
        """Start or continue a paused movie from current position.

        Parameters
        ----------
        log : bool
            Log the play event.

        """
        if self.status == PLAYING:
            return  # nop
        
        # get the absolute experiment time the first frame is to be presented
        # if self.status == NOT_STARTED:
        #     self._player.volume = self._volume
        # self._player.pause(True)
        # self.seek(0.0)  # seek to the current PTS
        # self._absStartTime = core.getTime()
        self._player.pause(False)  # start the player
        self.status = PLAYING
        # self._movieTime = 0.0
        self._lastFrameAbsTime = core.getTime()  # get the current time

    def pause(self, log=True):
        """Pause the current point in the movie. The image of the last frame
        will persist on-screen until `play()` or `stop()` are called.

        Parameters
        ----------
        log : bool
            Log this event.

        """
        self._player.pause()
        self.status = PAUSED

    def toggle(self, log=True):
        """Switch between playing and pausing the movie. If the movie is playing,
        this function will pause it. If the movie is paused, this function will
        play it.

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

        Parameters
        ----------
        log : bool
            Log this event.

        """
        # stop should reset the video to the start and pause
        if self._player is not None:
            self._player.close()

        self.status = STOPPED

    def seek(self, timestamp, log=True):
        """Seek to a particular timestamp in the movie.

        Parameters
        ----------
        timestamp : float
            Time in seconds.
        log : bool
            Log this event.

        """
        self._movieTime = timestamp
        # self._player.pause(True)  # pause the player
        self._player.seek(self._movieTime)

        if self.status == PLAYING: 
            self._player.pause(False)
        elif self.status == PAUSED:
            self._player.pause(True)
        else:
            self.updateVideoFrame()

        self._pts = self._movieTime  # store the current PTS

    def rewind(self, seconds=1, log=True):
        """Rewind the video.

        Parameters
        ----------
        seconds : float
            Time in seconds to rewind from the current position. Default is 5
            seconds.
        log : bool
            Log this event.

        """
        newPts = self._movieTime - seconds
        self._movieTime = min(max(0.0, newPts), self.duration)
        self.seek(self._movieTime)  # seek to the new position

    def fastForward(self, seconds=1, log=True):
        """Fast-forward the video.

        Parameters
        ----------
        seconds : float
            Time in seconds to fast forward from the current position. Default
            is 5 seconds.
        log : bool
            Log this event.

        """
        newPts = self._movieTime + seconds
        self._movieTime = min(max(0.0, newPts), self.duration)
        self.seek(self._movieTime)  # seek to the new position

    def replay(self, log=True):
        """Replay the movie from the beginning.

        Parameters
        ----------
        log : bool
            Log this event.

        Notes
        -----
        * This tears down the current media player instance and creates a new
          one. Similar to calling `stop()` and `loadMovie()`. Use `seek(0.0)` if
          you would like to restart the movie without reloading.

        """
        self.seek(0.0)
        self._movieTime = 0.0
        self.play()

    # --------------------------------------------------------------------------
    # Audio stream control methods
    #

    @property
    def muted(self):
        """`True` if the stream audio is muted (`bool`).
        """
        return self._player.mute

    @muted.setter
    def muted(self, value):
        self._player.mute = value

    def volumeUp(self, amount=0.05):
        """Increase the volume by a fixed amount.

        Parameters
        ----------
        amount : float or int
            Amount to increase the volume relative to the current volume.

        """
        currentVolume = self._player.volume 
        self._player.setVolume(currentVolume + amount)

    def volumeDown(self, amount=0.05):
        """Decrease the volume by a fixed amount.

        Parameters
        ----------
        amount : float or int
            Amount to decrease the volume relative to the current volume.

        """
        currentVolume = self._player.volume 
        self._player.setVolume(currentVolume - amount)

    @property
    def volume(self):
        """Volume for the audio track for this movie (`int` or `float`).
        """
        return self._player.volume

    @volume.setter
    def volume(self, value):
        self._player.volume = value

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

        return 0

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

        return self._player.getFrameRate()

    @property
    def videoSize(self):
        """Size of the video `(w, h)` in pixels (`tuple`). Returns `(0, 0)` if
        no video is loaded.
        """
        if not self._player:
            return 0, 0

        return self._player.getSize()

    @property
    def origSize(self):
        """
        Alias of videoSize
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
        return (self.pts / self.duration) * 100.0

    # --------------------------------------------------------------------------
    # OpenGL and rendering
    #

    def _freeBuffers(self):
        """Free texture and pixel buffers. Call this when tearing down this
        class or if a movie is stopped.
        """
        try:
            # delete buffers and textures if previously created
            if self._pixbuffId.value > 0:
                GL.glDeleteBuffers(1, self._pixbuffId)
                self._pixbuffId = GL.GLuint()

            # delete the old texture if present
            if self._textureId.value > 0:
                GL.glDeleteTextures(1, self._textureId)
                self._textureId = GL.GLuint()

        except TypeError:  # can happen when unloading or shutting down
            pass

    def _setupTextureBuffers(self):
        """Setup texture buffers which hold frame data. This creates a 2D
        RGB texture and pixel buffer. The pixel buffer serves as the store for
        texture color data. Each frame, the pixel buffer memory is mapped and
        frame data is copied over to the GPU from the decoder.

        This is called every time a video file is loaded. The `_freeBuffers`
        method is called in this routine prior to creating new buffers, so it's
        safe to call this right after loading a new movie without having to
        `_freeBuffers` first.

        """
        # get the size of the movie frame and compute the buffer size
        vidWidth, vidHeight = self._player.getMetadata().size
        nBufferBytes = vidWidth * vidHeight * 3

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
        if self.interpolate:
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
        """Copy pixel data from video frame to texture.
        """
        # get the size of the movie frame and compute the buffer size
        vidWidth, vidHeight = self._player.getMetadata().size

        nBufferBytes = vidWidth * vidHeight * 3

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
            self._recentFrame.ctypes.data,
            nBufferBytes)

        # copy data
        # bufferArray[:] = self._recentFrame[:]

        # Very important that we unmap the buffer data after copying, but
        # keep the buffer bound for setting the texture.
        GL.glUnmapBuffer(GL.GL_PIXEL_UNPACK_BUFFER)

        # bind the texture in OpenGL
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._textureId)

        # copy the PBO to the texture
        GL.glTexSubImage2D(
            GL.GL_TEXTURE_2D, 0, 0, 0,
            vidWidth, vidHeight,
            GL.GL_RGB,
            GL.GL_UNSIGNED_BYTE,
            0)  # point to the presently bound buffer

        # update texture filtering only if needed
        if self._texFilterNeedsUpdate:
            if self.interpolate:
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

    def _drawRectangle(self):
        """Draw the video frame to the window.

        This is called by the `draw()` method to blit the video to the display
        window.

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
        GL.glPushClientAttrib(GL.GL_CLIENT_VERTEX_ARRAY_BIT)

        # 2D texture array, 3D vertex array
        GL.glInterleavedArrays(GL.GL_T2F_V3F, 0, array)
        GL.glDrawArrays(GL.GL_QUADS, 0, 4)
        GL.glPopClientAttrib()
        GL.glPopAttrib()
        GL.glPopMatrix()

        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)


if __name__ == "__main__":
    pass
