#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy using a
local installation of VLC media player (https://www.videolan.org/).
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
#
# VlcMovieStim contributed by Dan Fitch, April 2019.
# The MovieStim2 class was taken and rewritten to use only vlc

from __future__ import absolute_import, division, print_function

import os
import sys
import threading
import weakref
import ctypes

from psychopy import core, logging
from psychopy.tools.attributetools import logAttrib, setAttribute
from psychopy.tools.filetools import pathToString
from psychopy.visual.basevisual import BaseVisualStim, ContainerMixin
from psychopy.clock import Clock
from psychopy.constants import FINISHED, NOT_STARTED, PAUSED, PLAYING, STOPPED

import numpy
import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl

try:
    # check if the lib can be loaded
    import vlc
except Exception as err:
    if "wrong architecture" in err:
        msg = ("Failed to import `vlc` module required by `vlcmoviestim`.\n"
               "You're using %i-bit python. Is your VLC install the same?"
               % 64 if sys.maxsize == 2 ** 64 else 32)
        raise OSError(msg)
    else:
        raise err

# flip time, and time since last movie frame flip will be printed
reportNDroppedFrames = 10


class VlcMovieStim(BaseVisualStim, ContainerMixin):
    """A stimulus class for playing movies in various formats (mpeg, avi,
    etc...) in PsychoPy using the VLC media player as a decoder (`libvlc`).

    The VLC media player (https://www.videolan.org/) must be installed on the
    machine running PsychoPy to use this class. Make certain that the version
    of VLC installed matches the architecture of the Python version is use by
    PsychoPy.

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
    loop : bool, optional
        Whether to start the movie over from the beginning if draw is called and
        the movie is done.
    autoStart : bool
        Automatically begin playback of the video when `flip()` is called.

    """
    def __init__(self, win,
                 filename="",
                 units='pix',
                 size=None,
                 pos=(0.0, 0.0),
                 ori=0.0,
                 flipVert=False,
                 flipHoriz=False,
                 color=(1.0, 1.0, 1.0),
                 colorSpace='rgb',
                 opacity=1.0,
                 volume=1.0,
                 name='',
                 loop=False,
                 autoLog=True,
                 depth=0.0,
                 noAudio=False,
                 vframe_callback=None,
                 fps=None,
                 interpolate=True,
                 autoStart=True):
        # what local vars are defined (these are the init params) for use
        # by __repr__
        self._initParams = dir()
        self._initParams.remove('self')
        super(VlcMovieStim, self).__init__(win, units=units, name=name,
                                         autoLog=False)
        # check for pyglet
        if win.winType != 'pyglet':
            logging.error('Movie stimuli can only be used with a pyglet window')
            core.quit()
        self._retracerate = win._monitorFrameRate
        if self._retracerate is None:
            self._retracerate = win.getActualFrameRate()
        if self._retracerate is None:
            logging.warning("FrameRate could not be supplied by psychopy; "
                            "defaulting to 60.0")
            self._retracerate = 60.0
        self.filename = pathToString(filename)
        self.loop = loop
        self.flipVert = flipVert
        self.flipHoriz = flipHoriz
        self.pos = numpy.asarray(pos, float)
        self.size = numpy.asarray(size, float)
        self.depth = depth
        self.opacity = float(opacity)
        self._volume = volume
        self.no_audio = noAudio
        self.current_frame = -1
        self._loopCount = 0
        self._frameNeedsUpdate = True

        # video pixel and texture buffer variables, setup later
        self.interpolate = interpolate
        self._texture_id = GL.GLuint()
        self._pixbuff_id = GL.GLuint()

        self._pause_time = 0
        self._vlc_clock = Clock()
        self._vlc_initialized = False
        self._reset()
        self.loadMovie(self.filename)
        self.setVolume(volume)
        self.nDroppedFrames = 0
        self._autoStart = autoStart
        self._glReady = False  # OpenGL surfaces are ready

        self.ori = ori
        # set autoLog (now that params have been initialised)
        self.autoLog = autoLog
        if autoLog:
            logging.exp("Created {} = {}".format(self.name, self))

    @property
    def interpolate(self):
        """Enable linear interpolation (`bool').

        If `True` linear filtering will be applied to the video making the image
        less pixelated if scaled. You may leave this off if the native size of
        the video is used.

        """
        return self._interpolate

    @interpolate.setter
    def interpolate(self, value):
        self._interpolate = value
        self._texFilterNeedsUpdate = True

    def _reset(self):
        """Internal method to reset video playback system. Frees any OpenGL
        textures and pixel buffers, releases the VLC stream. This puts the
        system into the original state, ready to play a movie.

        """
        self.status = NOT_STARTED
        self.frame_counter = self.current_frame = self._loopCount = 0
        self.width = self.height = self.duration = self.frame_rate = None

        # free pixel and texture buffers
        if self._pixbuff_id.value > 0:
            GL.glDeleteBuffers(1, self._pixbuff_id)
            self._pixbuff_id = GL.GLuint()

        if self._texture_id.value > 0:
            GL.glDeleteTextures(1, self._texture_id)
            self._texture_id = GL.GLuint()

        self._glReady = False

        if self._vlc_initialized:
            self._release_vlc()

    def setMovie(self, filename, log=True):
        """See `~MovieStim.loadMovie` (the functions are identical).

        This form is provided for syntactic consistency with other
        visual stimuli.
        """
        self.loadMovie(filename, log=log)

    def loadMovie(self, filename, log=True):
        """Load a movie from file

        Parameters
        ----------
        filename : str
            The name of the file or URL, including path if necessary.

        Notes
        -----
        * Due to VLC oddness, .duration is not correct until the movie starts
        playing.

        """
        self._reset()
        self.filename = pathToString(filename)

        # Initialize VLC
        self._vlc_start()

        self.status = NOT_STARTED
        logAttrib(self, log, 'movie', filename)

    def _vlc_start(self):
        """Create the vlc stream player for the video using python-vlc.
        """
        if not os.access(self.filename, os.R_OK):
            raise RuntimeError('Error: %s file not readable' % self.filename)
        if self.no_audio:
            instance = vlc.Instance("--no-audio")
        else:
            instance = vlc.Instance()
        try:
            stream = instance.media_new(self.filename)
        except NameError:
            msg = 'NameError: %s vs LibVLC %s'
            raise ImportError(msg % (vlc.__version__,
                                     vlc.libvlc_get_version()))

        # used to capture log messages from VLC
        instance.log_set(vlcLogCallback, None)

        player = instance.media_player_new()
        player.set_media(stream)

        # Load up the file
        stream.parse()
        size = player.video_get_size()
        self.video_width = size[0]
        self.video_height = size[1]
        self.frame_rate = player.get_fps()
        self.frame_counter = 0

        # TODO: Why is duration -1 still even after parsing? Newer vlc docs seem
        # to hint this won't work until playback starts.
        duration = player.get_length()
        logging.info("Video is %ix%i, duration %s, fps %s" % (
            self.video_width, self.video_height, duration, self.frame_rate))
        logging.flush()

        # We assume we can use the RGBA format here
        player.video_set_format(
            "RGBA", self.video_width, self.video_height, self.video_width << 2)

        # Configure a lock and a buffer for the pixels coming from VLC
        self.pixel_lock = threading.Lock()
        self.pixel_buffer = \
            (ctypes.c_ubyte * self.video_width * self.video_height * 4)()

        # Once you set these callbacks, you are in complete control of what to
        # do with the video buffer.
        selfref = ctypes.cast(
            ctypes.pointer(ctypes.py_object(self)), ctypes.c_void_p)
        player.video_set_callbacks(
            vlcLockCallback, vlcUnlockCallback, vlcDisplayCallback, selfref)

        manager = player.event_manager()

        # bind media event callbacks
        for evt in (vlc.EventType.MediaPlayerTimeChanged,
                    vlc.EventType.MediaPlayerEndReached):
            manager.event_attach(evt, vlcMediaEventCallback,
                weakref.ref(self), player)

        # Keep references
        self._self_ref = selfref
        self._instance = instance
        self._player = player
        self._stream = stream
        self._manager = manager

        logging.info("Initialized VLC...")
        self._vlc_initialized = True

        # setup texture buffers
        self._setupTextureBuffers()

    def _release_vlc(self):
        logging.info("Releasing VLC...")

        if self._player:
            self._player.stop()

        if self._manager:
            for evt in (vlc.EventType.MediaPlayerTimeChanged,
                        vlc.EventType.MediaPlayerEndReached):
                self._manager.event_detach(evt)

        if self._stream:
            self._stream.release()

        if self._instance:
            self._instance.release()

        self._stream = None
        self._stream_event_manager = None
        self._player = None
        self._instance = None
        self._vlc_initialized = False

    def _setupTextureBuffers(self):
        """Setup texture buffers which hold frame data. This creates a 2D
        RGB texture and pixel buffer. The pixel buffer serves as the store for
        texture color data. Each frame, the pixel buffer memory is mapped and
        frame data is copied over to the GPU from the decoder.

        This is called everytime a video file is loaded, destroying any pixel
        buffers or textures previously in use.

        """
        # delete buffers and textures if previously created
        if self._pixbuff_id.value > 0:
            GL.glDeleteBuffers(1, self._pixbuff_id)
            self._pixbuff_id = GL.GLuint()

        # Calculate the total size of the pixel store in bytes needed to hold a
        # single video frame. This value is reused during the pixel upload
        # process. Assumes RGBA color format.
        self._videoFrameBufferSize = \
            self.video_width * self.video_height * 4 * ctypes.sizeof(GL.GLubyte)

        # Create the pixel buffer object which will serve as the texture memory
        # store. Pixel data will be copied to this buffer each frame.
        GL.glGenBuffers(1, ctypes.byref(self._pixbuff_id))
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, self._pixbuff_id)
        GL.glBufferData(
            GL.GL_PIXEL_UNPACK_BUFFER,
            self._videoFrameBufferSize,
            None,
            GL.GL_STREAM_DRAW)  # one-way app -> GL
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)

        # delete the old texture if present
        if self._texture_id.value > 0:
            GL.glDeleteTextures(1, self._texture_id)
            self._texture_id = GL.GLuint()

        # Create a texture which will hold the data streamed to the pixel
        # buffer. Only one texture needs to be allocated.
        GL.glGenTextures(1, ctypes.byref(self._texture_id))
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texture_id)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGB8,
            self.video_width, self.video_height,  # frame width and height in pixels
            0,
            GL.GL_RGB,
            GL.GL_UNSIGNED_BYTE,
            None)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)  # needs to be 1

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

    def _update_texture(self):
        """Take the pixel buffer (assumed to be RGBA) and cram it into the GL
        texture.

        """
        with self.pixel_lock:
            # bind pixel unpack buffer
            GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, self._pixbuff_id)

            # Free last storage buffer before mapping and writing new frame
            # data. This allows the GPU to process the extant buffer in VRAM
            # uploaded last cycle without being stalled by the CPU accessing it.
            # Also allows VLC to access the buffer while the previous one is
            # still in use.
            GL.glBufferData(
                GL.GL_PIXEL_UNPACK_BUFFER,
                self._videoFrameBufferSize,
                None,
                GL.GL_STREAM_DRAW)

            # Map the buffer to client memory, `GL_WRITE_ONLY` to tell the
            # driver to optimize for a one-way copy operation.
            bufferPtr = GL.glMapBuffer(
                GL.GL_PIXEL_UNPACK_BUFFER,
                GL.GL_WRITE_ONLY)

            # This gets passed to the callback, VLC will draw the frame directly
            # to this buffer. Since buffer mapping only happens when VLC has a
            # pixel lock, it should be safe to do this.
            self.pixel_buffer = bufferPtr

            # vlcFrameAsNDArray = numpy.ctypeslib.as_array(
            #     ctypes.cast(self.pixel_buffer, ctypes.POINTER(GL.GLubyte)),
            #     shape=(self.video_width, self.video_height, 4))
            #
            # # upload pixel data by copying
            # numpy.copyto(
            #     numpy.ctypeslib.as_array(
            #         ctypes.cast(bufferPtr, ctypes.POINTER(GL.GLubyte)),
            #         shape=vlcFrameAsNDArray.shape),
            #     vlcFrameAsNDArray,
            #     casting='no')

            # Very important that we unmap the buffer data after copying, but
            # keep the buffer bound for setting the texture.
            GL.glUnmapBuffer(GL.GL_PIXEL_UNPACK_BUFFER)

            # bind the texture in OpenGL
            GL.glEnable(GL.GL_TEXTURE_2D)

            # copy the PBO to the texture
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texture_id)
            GL.glTexSubImage2D(
                GL.GL_TEXTURE_2D, 0, 0, 0,
                self.video_width,
                self.video_height,
                GL.GL_RGBA,
                GL.GL_UNSIGNED_BYTE,
                0)  # point to the presently bound buffer

            # update texture filtering if needed
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

    @property
    def isPlaying(self):
        """`True` if the video is presently playing."""
        return self.status == PLAYING

    @property
    def isNotStarted(self):
        """`True` if the video has not be started yet. This status is given
        after a video is loaded and play has yet to be called."""
        return self.status == NOT_STARTED

    def play(self, log=True):
        """Start or continue a paused movie from current position.

        Returns
        -------
        int
            Frame index playback started at. Should always be `0` if starting at
            the beginning of the video.

        """
        if not self._player:
            return  # nop if there is no player open

        if self.isNotStarted:  # video has not been played yet
            self.status = PLAYING
            self._player.play()

            if log and self.autoLog:
                self.win.logOnFlip(
                    "Set %s playing" % self.name,
                    level=logging.EXP, obj=self)

            self._update_texture()

            return self.current_frame
        elif self.isPaused:  # video is presently paused
            pass

    @property
    def isPaused(self):
        """`True` if the video is presently paused."""
        return self.status == PAUSED

    def pause(self, log=True):
        """Pause the current point in the movie.
        """
        if self.status == PLAYING:
            self.status = PAUSED
            player = self._player
            if player and player.can_pause():
                player.pause()
            if log and self.autoLog:
                self.win.logOnFlip("Set %s paused" % self.name,
                                   level=logging.EXP, obj=self)
            self._pause_time = self._vlc_clock.getTime()
            return True
        if log and self.autoLog:
            self.win.logOnFlip("Failed Set %s paused" % self.name,
                               level=logging.EXP, obj=self)
        return False

    @property
    def isStopped(self):
        """`True` if the video is stopped."""
        return self.status == STOPPED

    def stop(self, log=True):
        """Stop the current point in the movie (sound will stop, current frame
        will not advance). Once stopped the movie cannot be restarted - it must
        be loaded again.

        Use `pause()` instead if you may need to restart the movie.

        """
        if self.isPlaying or self.isPaused:
            self.status = STOPPED

            if log and self.autoLog:
                self.win.logOnFlip(
                    "Set %s stopped" % self.name, level=logging.EXP, obj=self)

            self._reset()

    def seek(self, timestamp, log=True):
        """Seek to a particular timestamp in the movie.

        Parameters
        ----------
        timestamp : float
            Time in seconds.
        log : bool
            Log this change.

        """
        if self.isPlaying or self.isPaused:
            player = self._player
            if player and player.is_seekable():
                player.set_time(int(timestamp * 1000.0))
                self._vlc_clock.reset(timestamp)

                if self.status == PAUSED:
                    self._pause_time = timestamp

            if log:
                logAttrib(self, log, 'seek', timestamp)

    def setFlipHoriz(self, newVal=True, log=True):
        """If set to True then the movie will be flipped horizontally
        (left-to-right). Note that this is relative to the original, not
        relative to the current state.
        """
        self.flipHoriz = newVal
        logAttrib(self, log, 'flipHoriz')

    def setFlipVert(self, newVal=True, log=True):
        """If set to True then the movie will be flipped vertically
        (top-to-bottom). Note that this is relative to the original, not
        relative to the current state.
        """
        self.flipVert = not newVal
        logAttrib(self, log, 'flipVert')

    @property
    def volume(self):
        """Audio track volume (`int` or `float`). See `setVolume for more
        information about valid values.

        """
        return self.getVolume()

    @volume.setter
    def volume(self, value):
        self.setVolume(value)

    def setVolume(self, v):
        """Set the audio track volume.

        0 = mute, 100 = 0 dB. float values between 0.0 and 1.0 are also
        accepted, and scaled to an int between 0 and 100.

        """
        if self._player:
            if 0.0 <= v <= 1.0 and isinstance(v, float):
                v = int(v * 100)
            else:
                v = int(v)
            self._volume = v
            if self._player:
                self._player.audio_set_volume(v)

    def getVolume(self):
        """Returns the current movie audio volume.

        0 is no audio, 100 is max audio volume.
        """
        if self._player:
            self._volume = self._player.audio_get_volume()
        return self._volume

    def increaseVolume(self, amount=5):
        """Increase the volume.

        Parameters
        ----------
        amount : int
            Increase the volume by this amount. This gets added to the preset
            volume level.

        Returns
        -------
        int
            Volume after being changed.

        """
        if not self._player:
            return 0

        currentVolume = self.getVolume()
        newVolume = int(amount) + currentVolume

        # clip the volume in range
        if newVolume > 100:
            newVolume = 100
        elif newVolume < 0:
            newVolume = 0
        else:
            newVolume = newVolume

        self.setVolume(newVolume)

        return self._volume

    def decreaseVolume(self, amount=5):
        """Decrease the volume.

        Parameters
        ----------
        amount : int
            Decrease the volume by this amount. This gets subtracted from the
            preset volume level.

        Returns
        -------
        int
            Volume after being changed.

        """
        if not self._player:
            return 0

        currentVolume = self.getVolume()
        newVolume = currentVolume - int(amount)

        # clip the volume in range
        if newVolume > 100:
            newVolume = 100
        elif newVolume < 0:
            newVolume = 0
        else:
            newVolume = newVolume

        self.setVolume(newVolume)

        return self._volume

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
        return self.frame_rate

    def getCurrentFrameNumber(self):
        """Get the current movie frame number (`int`), same as `frameIndex`.
        """
        return self.frame_counter

    @property
    def percentageComplete(self):
        """Percentage of the video completed (`float`)."""
        return self.getPercentageComplete()

    def getCurrentFrameTime(self):
        """Get the time that the movie file specified the current video frame as
        having.
        """
        return self._vlc_clock.getTime()

    @property
    def percentageComplete(self):
        """Percentage of the video completed (`float`)."""
        return self.getPercentageComplete()

    def getPercentageComplete(self):
        """Provides a value between 0.0 and 100.0, indicating the amount of the
        movie that has been already played.
        """
        return self._player.get_position() * 100.0

    def _draw_rectangle(self, win):
        # make sure that textures are on and GL_TEXTURE0 is active
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        # sets opacity (1,1,1 = RGB placeholder)
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
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texture_id)
        GL.glPushClientAttrib(GL.GL_CLIENT_VERTEX_ARRAY_BIT)
        # 2D texture array, 3D vertex array
        GL.glInterleavedArrays(GL.GL_T2F_V3F, 0, array)
        GL.glDrawArrays(GL.GL_QUADS, 0, 4)
        GL.glPopClientAttrib()
        GL.glPopAttrib()
        GL.glPopMatrix()

    @property
    def frameIndex(self):
        """Current frame index being displayed (`int`)."""
        return self.current_frame

    @property
    def loopCount(self):
        """Number of loops completed since playback started (`int`). This value
        is reset when either `stop` or `loadMovie` is called.
        """
        return self._loopCount

    def draw(self, win=None):
        """Draw the current frame to a particular visual.Window (or to the
        default win for this object if not specified).

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

        # check if we need to pull a new frame this round
        if self.current_frame == self.frame_counter:

            # update the texture, getting the most recent frame
            self._update_texture()

            # draw the frame to the window
            self._draw_rectangle(win)

            return False  # frame does not need an update this round

        # update the current frame
        self.current_frame = self.frame_counter

        if self.status == NOT_STARTED or (self.status == FINISHED and self.loop):
            self._loopCount += 1
            self.play()
        elif self.status == FINISHED and not self.loop:
            return False

        # select the window to output to
        self._selectWindow(self.win if win is None else win)

        # update the texture, getting the most recent frame
        self._update_texture()

        # draw the frame to the window
        self._draw_rectangle(win)

        # token gesture for existing code, we handle this logic internally now
        return True

    def _unload(self):
        """Internal method called when the video stream is closed or stopped.
        Unloads any OpenGL resources associated with the last video.
        """
        if self._vlc_initialized:
            self._release_vlc()

        self._glReady = False

        if self._pixbuff_id.value > 0:
            GL.glDeleteBuffers(1, self._pixbuff_id)
            self._pixbuff_id.value = 0

        if self._texture_id.value > 0:
            GL.glDeleteTextures(1, self._texture_id)
            self._texture_id.value = 0

        self.status = FINISHED

    def _onEos(self):
        """Internal method called when the decoder encounters the end of the
        stream.
        """
        if self.loop:
            self.seek(0.0)
        else:
            self.status = FINISHED
            self.stop()

        if self.autoLog:
            self.win.logOnFlip(
                "Set %s finished" % self.name, level=logging.EXP, obj=self)

    def __del__(self):
        try:
            self._unload()
        except (ImportError, ModuleNotFoundError, TypeError):
            pass  # has probably been garbage-collected already

    def setAutoDraw(self, val, log=None):
        """Add or remove a stimulus from the list of stimuli that will be
        automatically drawn on each flip

        :parameters:
            - val: True/False
                True to add the stimulus to the draw list, False to remove it
        """
        if val:
            self.play(log=False)  # set to play in case stopped
        else:
            self.pause(log=False)
        # add to drawing list and update status
        setAttribute(self, 'autoDraw', val, log)


# ------------------------------------------------------------------------------
# Callback functions for `libvlc`
#

@vlc.CallbackDecorators.VideoLockCb
def vlcLockCallback(user_data, planes):
    """Callback invoked when VLC has new texture data."""
    cls = ctypes.cast(
        user_data, ctypes.POINTER(ctypes.py_object)).contents.value
    cls.pixel_lock.acquire()

    # tell VLC to take the data and stuff it into the buffer
    planes[0] = ctypes.cast(cls.pixel_buffer, ctypes.c_void_p)


@vlc.CallbackDecorators.VideoUnlockCb
def vlcUnlockCallback(user_data, picture, planes):
    """Called when VLC releases the frame draw buffer."""
    cls = ctypes.cast(
        user_data, ctypes.POINTER(ctypes.py_object)).contents.value
    cls.pixel_lock.release()


@vlc.CallbackDecorators.VideoDisplayCb
def vlcDisplayCallback(user_data, picture):
    """Callback used by VLC when its ready to display a new frame.
    """
    cls = ctypes.cast(
        user_data, ctypes.POINTER(ctypes.py_object)).contents.value
    cls.frame_counter += 1


@vlc.CallbackDecorators.LogCb
def vlcLogCallback(user_data, level, ctx, fmt, args):
    """Callback for logging messages emitted by VLC. Processed here and
    converted to PsychoPy logging format.
    """
    # if level == vlc.DEBUG:
    #     logging.debug()

    pass  # suppress messages from VLC, look scary but can be mostly ignored


def vlcMediaEventCallback(event, user_data, player):
    """Callback used by VLC for handling media player events.
    """
    if not user_data():
        return

    cls = user_data()  # ref to movie class
    event = event.type

    if event == vlc.EventType.MediaPlayerTimeChanged:  # needed for pause
        tm = -player.get_time() / 1000.0
        cls._vlc_clock.reset(tm)
    elif event == vlc.EventType.MediaPlayerEndReached:
        cls._onEos()


if __name__ == "__main__":
    pass
