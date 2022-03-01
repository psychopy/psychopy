#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy using a
FFMPEG through ffpyplayer.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
#
# VlcMovieStim originally contributed by Dan Fitch, April 2019. The `MovieStim2`
# class was taken and rewritten to use only VLC.
#

import os
import sys
import threading
import ctypes

from psychopy import core, logging
from psychopy.clock import Clock
from psychopy.tools.attributetools import logAttrib, setAttribute
from psychopy.tools.filetools import pathToString
from psychopy.visual.basevisual import BaseVisualStim, ContainerMixin
from psychopy.constants import FINISHED, NOT_STARTED, PAUSED, PLAYING, STOPPED

import numpy as np
import pyglet
GL = pyglet.gl

haveFFPyPlayer = True
try:
    from ffpyplayer.player import MediaPlayer
except ImportError:
    haveFFPyPlayer = False
    logging.warning(
        'Cannot import package `ffpyplayer`, therefore `FFMovieStim` cannot '
        'be used this session. To get it use command `python -m pip install '
        'ffpyplayer`.')


# threshold to stop reporting dropped frames
reportNDroppedFrames = 10

# constants for use with ffpyplayer
FFPYPLAYER_STATUS_EOF = 'eof'
FFPYPLAYER_STATUS_PAUSED = 'paused'


class MovieFrameInfo:
    """Class containing data of a single movie frame.

    Parameters
    ----------
    frameIdx : int
        Frame index.
    video : ArrayLike or None
    audio : ArrayLike or None
    absTime : float

    """
    __slots__ = [
        "_frameIdx",
        "_video",
        "_audio",
        "_absTime"
    ]

    def __init__(self, frameIdx=-1, video=None, audio=None, absTime=0.0):
        self._frameIdx = int(frameIdx)
        self._video = video
        self._audio = audio
        self._absTime = float(absTime)

    @property
    def absTime(self):
        return self._absTime

    @absTime.setter
    def absTime(self, val):
        self._absTime = float(val)

    @property
    def video(self):
        return self._video

    @video.setter
    def video(self, val):
        self._video = val


# used to represent an empty frame
NULL_MOVIE_FRAME_INFO = MovieFrameInfo()


class FFMovieStim(BaseVisualStim, ContainerMixin):
    """Class for loading an presenting movies using FFMPEG.

    Support for FFMPEG is provided by the `ffpyplayer` library which allows for
    playback of streams (e.g., URLs, webcams, etc.) and video files.

    Parameters
    ----------
    win : :class:`~psychopy.visual.Window`
        Window the video is being drawn to.
    filename : str
        Name of the file or stream URL to play. If an empty string, no file will
        be loaded on initialization but can be set later.
    units : str
        Units to use when sizing the video frame on the window, affects how
        `size` is interpreted.
    size : ArrayLike or None
        Size of the video frame on the window in `units`. If `None`, the native
        size of the video will be used.
    flipVert : bool
        If `True` then the movie will be top-bottom flipped.
    flipHoriz : bool
        If `True` then the movie will be right-left flipped.
    volume : int or float
        If specifying an `int` the nominal level is 100, and 0 is silence. If a
        `float`, values between 0 and 1 may be used.
    loop : bool
        Whether to start the movie over from the beginning if draw is called and
        the movie is done. Default is `False.
    autoStart : bool
        Automatically begin playback of the video when `flip()` is called.

    """
    def __init__(self,
                 win,
                 filename="",
                 units='pix',
                 size=None,
                 pos=(0.0, 0.0),
                 ori=0.0,
                 flipVert=False,
                 flipHoriz=False,
                 color=(1.0, 1.0, 1.0),  # remove?
                 colorSpace='rgb',
                 opacity=1.0,
                 volume=1.0,
                 name='',
                 loop=False,
                 autoLog=True,
                 depth=0.0,
                 noAudio=False,
                 interpolate=True,
                 autoStart=True):

        # check if we have the VLC lib
        if not haveFFPyPlayer:
            raise ImportError(
                'Cannot import package `ffpyplayer`, therefore `FFMovieStim` '
                'cannot be used this session.')

        # what local vars are defined (these are the init params) for use
        self._initParams = dir()
        self._initParams.remove('self')

        super(FFMovieStim, self).__init__(
            win, units=units, name=name, autoLog=False)

        # drawing stuff
        self.flipVert = flipVert
        self.flipHoriz = flipHoriz
        self.pos = np.asarray(pos, float)
        self.ori = ori
        self.size = np.asarray(size, float)
        self.depth = depth
        self.opacity = float(opacity)

        # playback stuff
        self._filename = pathToString(filename)
        self._volume = volume
        self._noAudio = noAudio  # cannot be changed
        self._currentFrame = -1
        self._loopCount = 0
        self._player = None
        self._metadata = {}  # video metadata
        self._frameTime = 0.0
        self._lastFrameOnsetTime = 0.0
        self.loop = loop

        # descriptor with data from the last frame
        self._lastFrameInfo = NULL_MOVIE_FRAME_INFO
        self._lastFrameTime = 0.0
        self._videoClock = Clock()  # keep track of current video time

        # original size to keep BaseVisualStim happy
        self._origSize = np.asarray((128, 128,), float)

        # video pixel and texture buffer variables, setup later
        self.interpolate = interpolate  # use setter
        self._textureId = GL.GLuint(0)
        self._pixbuffId = GL.GLuint(0)
        self._texFilterNeedsUpdate = True  # only set on user change

        self.nDroppedFrames = 0
        self._autoStart = autoStart

        self._filename = pathToString(filename)
        if self._filename:  # load a movie if provided
            self.loadMovie(self._filename)

    @property
    def filename(self):
        """File name for the loaded video (`str`)."""
        return self._filename

    @filename.setter
    def filename(self, value):
        self.loadMovie(value)

    @property
    def autoStart(self):
        """Start playback when `.draw()` is called (`bool`)."""
        return self._autoStart

    @autoStart.setter
    def autoStart(self, value):
        self._autoStart = bool(value)

    @property
    def _hasPlayer(self):
        """`True` if a media player instance is started.
        """
        # use this property to check if the player instance is started in
        # methods which require it
        return self._player is not None

    def _assertMediaPlayer(self):
        """Ensure the media player instance is available. Raises a
        `RuntimeError` if no movie is loaded.
        """
        if self._hasPlayer and isinstance(self._player, MediaPlayer):
            return  # nop if we're good

        raise RuntimeError(
            "Calling this class method requires a successful call to "
            "`loadMovie` first.")

    def loadMovie(self, filename):
        """Load a movie file from disk.

        Parameters
        ----------
        filename : str
            Path to movie file. Must be a format that FFMPEG supports.

        """
        # set the file path
        self._filename = pathToString(filename)

        # Check if the player is already started. Close it and load a new
        # instance if so.
        if self._player is not None:  # player already started
            # make sure it's the correct type
            if not isinstance(self._player, MediaPlayer):
                raise TypeError(
                    'Incorrect type for `FFMovieStim._player`, expected '
                    '`ffpyplayer.player.MediaPlayer`. Got type `{}` '
                    'instead.'.format(type(self._player).__name__))

            # close the player and reset
            self._player.close_player()
            self._player = None

            self._selectWindow(self.win)
            self._freeBuffers()  # clean up any buffers previously allocated

        # reset flags
        self._metadata = {}
        self._frameTime = 0.0
        self._currentFrame = -1  # increment frame index
        self._lastFrameInfo = NULL_MOVIE_FRAME_INFO

        # create a new media player instance
        self._player = MediaPlayer(self._filename)
        # pause the video and seek to the start
        self._player.set_pause(True)
        # self._player.seek(0.0)

        self.updateVideoFrame()  # get the first frame queued up

        # get metadata
        self._metadata = self._player.get_metadata()

        # video loaded and waiting
        self.status = NOT_STARTED

    @property
    def frameTexture(self):
        """Texture ID for the current video frame (`GLuint`). You can use this
        as a video texture. However, you must periodically call
        `updateVideoFrame` to keep this up to date.

        """
        return self._textureId

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
        self._assertMediaPlayer()  # make sure we have a media playback object

        # create a video texture after starting playback
        if self._currentFrame < 0:  # movie is starting
            self._videoClock.reset()
            needsVideoTexture = True
        else:
            needsVideoTexture = False

        # Don't get a new frame if we haven't reached its presentation
        # timestamp yet. Just use the last frame again.
        if self._videoClock.getTime() < self._lastFrameInfo.absTime:
            return False

        # get the frame an playback status
        frame, playbackStatus = self._player.get_frame()

        # NB - We could potentially buffer a bunch of frames in another thread
        # and pull them in here. Right now we're pulling one frame at a time.

        # set status flags accordingly
        if playbackStatus == FFPYPLAYER_STATUS_EOF:
            self.status = FINISHED
            return False
        elif playbackStatus == FFPYPLAYER_STATUS_PAUSED:
            self.status = PAUSED
            return False
        elif frame is None:
            return False  # NOT_STARTED?
        else:
            self.status = PLAYING

        # process the new frame
        colorData, pts = frame

        # if we have a new frame, update the frame information
        videoBuffer = colorData.to_bytearray()[0]
        videoFrameArray = np.frombuffer(videoBuffer, dtype=np.uint8)

        self._lastFrameInfo = MovieFrameInfo(
            frameIdx=self._currentFrame,
            video=videoFrameArray,
            audio=None,  # played via SDL, not audio data yet from player
            absTime=playbackStatus
        )
        self._currentFrame += 1  # increment frame index

        # we need to play at least one frame to get metadata
        if needsVideoTexture:
            self._setupTextureBuffers()

        # update the texture now
        self._pixelTransfer()

        return True

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
        self._assertMediaPlayer()

        self._freeBuffers()  # free buffer before creating a new one

        # get the size of the movie frame and compute the buffer size
        vidWidth, vidHeight = self.videoSize
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

        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)

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
        """Copy pixel data from video frame to texture."""
        self._assertMediaPlayer()

        # get the size of the movie frame and compute the buffer size
        vidWidth, vidHeight = self.videoSize
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

        bufferArray = np.ctypeslib.as_array(
            ctypes.cast(bufferPtr, ctypes.POINTER(GL.GLubyte)),
            shape=(nBufferBytes,))

        # copy data
        bufferArray[:] = self._lastFrameInfo.video[:]

        # Very important that we unmap the buffer data after copying, but
        # keep the buffer bound for setting the texture.
        GL.glUnmapBuffer(GL.GL_PIXEL_UNPACK_BUFFER)

        if self._lastFrameInfo.video is None:
            pass

        # bind the texture in OpenGL
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._textureId)

        # copy the PBO to the texture
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
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
        """Draw the frame to the window. This is called by the `draw()` method.
        """
        # make sure that textures are on and GL_TEXTURE0 is activ
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

    def draw(self, win=None):
        """Draw the current frame to a particular
        :class:`~psychopy.visual.Window` (or to the default win for this object
        if not specified).

        The current position in the movie will be determined automatically. This
        method should be called on every frame that the movie is meant to
        appear.

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

        if not self._hasPlayer:  # do nothing if a video is not loaded
            return True

        # video is not started yet
        if self._autoStart and self._hasPlayer:
            self.play()

        # update the video frame and draw it to a quad
        _ = self.updateVideoFrame()
        self._drawRectangle()  # draw the texture to the target window

        return True

    # --------------------------------------------------------------------------
    # Video playback controls and status
    #
    @property
    def isPlaying(self):
        """`True` if the video is presently playing (`bool`)."""
        # Status flags as properties are pretty useful for users since they are
        # self documenting and prevent the user from touching the status flag
        # attribute directly.
        #
        return self.status == PLAYING

    @property
    def isNotStarted(self):
        """`True` if the video has not be started yet (`bool`). This status is
        given after a video is loaded and play has yet to be called."""
        return self.status == NOT_STARTED

    @property
    def isStopped(self):
        """`True` if the video is stopped (`bool`)."""
        return self.status == STOPPED

    @property
    def isPaused(self):
        """`True` if the video is presently paused (`bool`)."""
        return self.status == PAUSED

    @property
    def isFinished(self):
        """`True` if the video is finished (`bool`)."""
        # why is this the same as STOPPED?
        return self.status == FINISHED

    def play(self, log=True):
        """Start or continue a paused movie from current position.

        Parameters
        ----------
        log : bool
            Log the play event.

        Returns
        -------
        int or None
            Frame index playback started at. Should always be `0` if starting at
            the beginning of the video. Returns `None` if the player has not
            been initialized.

        """
        self._assertMediaPlayer()

        # if not started, reset the clock
        if self.status == NOT_STARTED:
            self._videoClock.reset(0.0)

        if self._player.get_pause():  # if paused, unpause to start playback
            self._player.set_pause(False)

        self.status = PLAYING

        if log and self.autoLog:
            self.win.logOnFlip(
                "Set %s playing" % self.name, level=logging.EXP, obj=self)

        return self._currentFrame

    def pause(self, log=True):
        """Pause the current point in the movie. The image of the last frame
        will persist on-screen until `play()` or `stop()` are called.

        Parameters
        ----------
        log : bool
            Log the pause event.

        """
        self._assertMediaPlayer()

        if not self._player.get_pause():
            self._player.set_pause(True)

        self.status = PAUSED  # could be set at next call to `_getMovieFrame`

        if log and self.autoLog:
            self.win.logOnFlip(
                "Set %s paused" % self.name, level=logging.EXP, obj=self)

        return False

    def stop(self, log=True):
        """Stop the current point in the movie (sound will stop, current frame
        will not advance). Once stopped the movie cannot be restarted - it must
        be loaded again.

        Use `pause()` instead if you may need to restart the movie.

        Parameters
        ----------
        log : bool
            Log the stop event.

        """
        self._assertMediaPlayer()

        self._player.close_player()
        self.status = STOPPED

        if log and self.autoLog:
            self.win.logOnFlip(
                "Set %s stopped" % self.name, level=logging.EXP, obj=self)

    # def seek(self, timestamp, log=True):
    #     """Seek to a particular timestamp in the movie.
    #
    #     Parameters
    #     ----------
    #     timestamp : float
    #         Time in seconds.
    #     log : bool
    #         Log the seek event.
    #
    #     """
    #     if self.isPlaying or self.isPaused:
    #         player = self._player
    #         if player and player.is_seekable():
    #             # pause while seeking
    #             player.set_time(int(timestamp * 1000.0))
    #
    #         if log:
    #             logAttrib(self, log, 'seek', timestamp)

    def rewind(self, seconds=5):
        """Rewind the video.

        Parameters
        ----------
        seconds : float
            Time in seconds to rewind from the current position. Default is 5
            seconds.

        Returns
        -------
        float
            Timestamp after rewinding the video.

        """
        self._assertMediaPlayer()

        self._player.seek(-seconds, relative=True)
        _ = self.updateVideoFrame()

        # after seeking
        return self.getCurrentFrameTime()

    def fastForward(self, seconds=5):
        """Fast-forward the video.

        Parameters
        ----------
        seconds : float
            Time in seconds to fast forward from the current position. Default
            is 5 seconds.

        Returns
        -------
        float
            Timestamp at new position after fast forwarding the video.

        """
        self._assertMediaPlayer()

        self._player.seek(seconds, relative=True)
        _ = self.updateVideoFrame()

        return self.getCurrentFrameTime()

    def replay(self, autoStart=True):
        """Replay the movie from the beginning.

        Parameters
        ----------
        autoStart : bool
            Start playback immediately. If `False`, you must call `play()`
            afterwards to initiate playback.

        Notes
        -----
        * This tears down the current media player instance and creates a new
          one. Similar to calling `stop()` and `loadMovie()`. Use `seek(0.0)` if
          you would like to restart the movie without reloading.

        """
        self.stop()  # stop the movie
        lastMovieFile = self._filename

        self._autoStart = autoStart
        self.loadMovie(lastMovieFile)  # will play if auto start

    # --------------------------------------------------------------------------
    # Video and playback information
    #

    @property
    def frameIndex(self):
        """Current frame index being displayed (`int`)."""
        return 0  # for now

    def getCurrentFrameNumber(self):
        """Get the current movie frame number (`int`), same as `frameIndex`.
        """
        pass

    @property
    def duration(self):
        """Duration of the loaded video in seconds (`float`). Not valid unless
        the video has been started.
        """
        duration = self._metadata.get('duration', 0.0)
        return float(duration) if isinstance(duration, str) else duration

    @property
    def loopCount(self):
        """Number of loops completed since playback started (`int`). This value
        is reset when either `stop` or `loadMovie` is called.
        """
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
        pass

    @property
    def frameTime(self):
        """Current frame time in seconds (`float`)."""
        return self._frameTime

    def getCurrentFrameTime(self):
        """Get the time that the movie file specified the current video frame as
        having.

        Returns
        -------
        float
            Current video time in seconds.

        """
        pass

    def getPercentageComplete(self):
        """Provides a value between 0.0 and 100.0, indicating the amount of the
        movie that has been already played.
        """
        pass

    @property
    def videoSize(self):
        """Size of the video `(w, h)` in pixels (`tuple`). Returns `(0, 0)` if
        no video is loaded."""
        return self._metadata.get('src_vid_size', (0, 0))


if __name__ == "__main__":
    pass