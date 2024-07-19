#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['MovieStim']


import ctypes
import os.path
from pathlib import Path

from psychopy import prefs
from psychopy.tools.filetools import pathToString, defaultStim
from psychopy.visual.basevisual import (
    BaseVisualStim, DraggingMixin, ContainerMixin, ColorMixin
)
from psychopy.constants import FINISHED, NOT_STARTED, PAUSED, PLAYING, STOPPED

from .players import getMoviePlayer
from .metadata import MovieMetadata, NULL_MOVIE_METADATA
from .frame import MovieFrame, NULL_MOVIE_FRAME_INFO

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


class MovieStim(BaseVisualStim, DraggingMixin, ColorMixin, ContainerMixin):
    """Class for presenting movie clips as stimuli.

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
        self._filename = pathToString(filename)
        self._volume = volume
        self._noAudio = noAudio  # cannot be changed
        self.loop = loop
        self._recentFrame = None
        self._autoStart = autoStart
        self._isLoaded = False

        # OpenGL data
        self.interpolate = interpolate
        self._texFilterNeedsUpdate = True
        self._metadata = NULL_MOVIE_METADATA
        self._pixbuffId = GL.GLuint(0)
        self._textureId = GL.GLuint(0)

        # get the player interface for the desired `movieLib` and instance it
        self._player = getMoviePlayer(movieLib)(self)

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

    def loadMovie(self, filename):
        """Load a movie file from disk.

        Parameters
        ----------
        filename : str
            Path to movie file. Must be a format that FFMPEG supports.

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

        self._filename = filename
        self._player.load(self._filename)

        self._freeBuffers()  # free buffers (if any) before creating a new one
        self._setupTextureBuffers()

        self._isLoaded = True

    def load(self, filename):
        """Load a movie file from disk (alias of `loadMovie`).

        Parameters
        ----------
        filename : str
            Path to movie file. Must be a format that FFMPEG supports.

        """
        self.loadMovie(filename=filename)

    def unload(self, log=True):
        """Stop and unload the movie.

        Parameters
        ----------
        log : bool
            Log this event.

        """
        self._player.stop(log=log)
        self._player.unload()
        self._freeBuffers()  # free buffer before creating a new one
        self._isLoaded = False

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
        # get the current movie frame for the video time
        newFrameFromPlayer = self._player.getMovieFrame()
        if newFrameFromPlayer is not None:
            self._recentFrame = newFrameFromPlayer

        # only do a pixel transfer on valid frames
        if self._recentFrame is not None:
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

        # handle autoplay
        if self._autoStart and self.isNotStarted:
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
        if self._player is not None:
            return self._player.isFinished

        return False

    def play(self, log=True):
        """Start or continue a paused movie from current position.

        Parameters
        ----------
        log : bool
            Log the play event.

        """
        # get the absolute experiment time the first frame is to be presented
        # if self.status == NOT_STARTED:
        #     self._player.volume = self._volume

        self._player.play(log=log)

    def pause(self, log=True):
        """Pause the current point in the movie. The image of the last frame
        will persist on-screen until `play()` or `stop()` are called.

        Parameters
        ----------
        log : bool
            Log this event.

        """
        self._player.pause(log=log)

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
            self._player.stop()

    def seek(self, timestamp, log=True):
        """Seek to a particular timestamp in the movie.

        Parameters
        ----------
        timestamp : float
            Time in seconds.
        log : bool
            Log this event.

        """
        self._player.seek(timestamp, log=log)

    def rewind(self, seconds=5, log=True):
        """Rewind the video.

        Parameters
        ----------
        seconds : float
            Time in seconds to rewind from the current position. Default is 5
            seconds.
        log : bool
            Log this event.

        """
        self._player.rewind(seconds, log=log)

    def fastForward(self, seconds=5, log=True):
        """Fast-forward the video.

        Parameters
        ----------
        seconds : float
            Time in seconds to fast forward from the current position. Default
            is 5 seconds.
        log : bool
            Log this event.

        """
        self._player.fastForward(seconds, log=log)

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
        self._player.replay(log=log)

    # --------------------------------------------------------------------------
    # Audio stream control methods
    #

    @property
    def muted(self):
        """`True` if the stream audio is muted (`bool`).
        """
        return self._player.muted

    @muted.setter
    def muted(self, value):
        self._player.muted = value

    def volumeUp(self, amount=0.05):
        """Increase the volume by a fixed amount.

        Parameters
        ----------
        amount : float or int
            Amount to increase the volume relative to the current volume.

        """
        self._player.volumeUp(amount)

    def volumeDown(self, amount=0.05):
        """Decrease the volume by a fixed amount.

        Parameters
        ----------
        amount : float or int
            Amount to decrease the volume relative to the current volume.

        """
        self._player.volumeDown(amount)

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
        return self._player.frameIndex

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

        return self._player.metadata.duration

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

        return self._player.loopCount

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

        return self._player.metadata.frameRate

    @property
    def videoSize(self):
        """Size of the video `(w, h)` in pixels (`tuple`). Returns `(0, 0)` if
        no video is loaded.
        """
        if not self._player:
            return 0, 0

        return self._player.metadata.size

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

        return self._player.metadata.size

    @property
    def pts(self):
        """Presentation timestamp of the most recent frame (`float`).

        This value corresponds to the time in movie/stream time the frame is
        scheduled to be presented.

        """
        if not self._player:
            return -1.0

        return self._player.pts

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
        nBufferBytes = vidWidth * vidHeight * 4

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
            GL.GL_RGBA8,
            vidWidth, vidHeight,  # frame dims in pixels
            0,
            GL.GL_BGRA,
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

        nBufferBytes = vidWidth * vidHeight * 4

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
        bufferArray[:] = self._recentFrame.colorData[:]

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
            GL.GL_BGRA,
            GL.GL_UNSIGNED_INT_8_8_8_8_REV,
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
