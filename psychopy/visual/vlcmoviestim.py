#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy using a
local installation of VLC media player (https://www.videolan.org/).
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
import weakref

from psychopy import core, logging
from psychopy.tools.attributetools import logAttrib, setAttribute
from psychopy.tools.filetools import pathToString
from psychopy.visual.basevisual import BaseVisualStim, ContainerMixin
from psychopy.constants import FINISHED, NOT_STARTED, PAUSED, PLAYING, STOPPED

import numpy
import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl

try:
    # check if the lib can be loaded
    import vlc
    haveVLC = True
except Exception as err:
    haveVLC = False
    # store the error but only raise it if the
    if "wrong architecture" in str(err):
        msg = ("Failed to import `vlc` module required by `vlcmoviestim`.\n"
               "You're using %i-bit python. Is your VLC install the same?"
               % 64 if sys.maxsize == 2 ** 64 else 32)
        _vlcImportErr = OSError(msg)
    else:
        _vlcImportErr = err

# flip time, and time since last movie frame flip will be printed
reportNDroppedFrames = 10


class VlcMovieStim(BaseVisualStim, ContainerMixin):
    """A stimulus class for playing movies in various formats (mpeg, avi,
    etc...) in PsychoPy using the VLC media player as a decoder.

    This movie class is very efficient and better suited for playing
    high-resolution videos (720p+) than the other movie classes. However, audio
    is only played using the default output device. This may be adequate for
    most applications where the user is not concerned about precision audio
    onset times.

    The VLC media player (https://www.videolan.org/) must be installed on the
    machine running PsychoPy to use this class. Make certain that the version
    of VLC installed matches the architecture of the Python interpreter hosting
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
    loop : bool
        Whether to start the movie over from the beginning if draw is called and
        the movie is done. Default is `False.
    autoStart : bool
        Automatically begin playback of the video when `flip()` is called.

    Notes
    -----
    * You may see error messages in your log output from VLC (e.g.,
      `get_buffer() failed`, `no frame!`, etc.) after shutting down. These
      errors originate from the decoder and can be safely ignored.

    """
    def __init__(self, win,
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
        if not haveVLC:
            raise _vlcImportErr
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

        # drawing stuff
        self.flipVert = flipVert
        self.flipHoriz = flipHoriz
        self.pos = numpy.asarray(pos, float)

        # original size to keep BaseVisualStim happy
        self._origSize = numpy.asarray((128, 128,), float)

        # Defer setting size until after the video is loaded to use it's native
        # size instead of the one set by the user.
        self._useFrameSizeFromVideo = size is None
        if not self._useFrameSizeFromVideo:
            self.size = numpy.asarray(size, float)

        self.depth = depth
        self.opacity = float(opacity)

        # playback stuff
        self._filename = pathToString(filename)
        self._volume = volume
        self._noAudio = noAudio  # cannot be changed
        self._currentFrame = -1
        self._loopCount = 0
        self.loop = loop

        # video pixel and texture buffer variables, setup later
        self.interpolate = interpolate  # use setter
        self._textureId = GL.GLuint()
        self._pixbuffId = GL.GLuint()

        # VLC related attributes
        self._instance = None
        self._player = None
        self._manager = None
        self._stream = None
        self._videoWidth = 0
        self._videoHeight = 0
        self._frameRate = 0.0
        self._vlcInitialized = False
        self._pixelLock = threading.Lock()  # semaphore for VLC pixel transfer
        self._framePixelBuffer = None  # buffer pointer to draw to
        self._videoFrameBufferSize = None
        self._streamEnded = False

        # spawn a VLC instance for this class instance
        # self._createVLCInstance()

        # load a movie if provided
        if self._filename:
            self.loadMovie(self._filename)

        self.setVolume(volume)
        self.nDroppedFrames = 0
        self._autoStart = autoStart

        self.ori = ori
        # set autoLog (now that params have been initialised)
        self.autoLog = autoLog
        if autoLog:
            logging.exp("Created {} = {}".format(self.name, self))

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

    def setMovie(self, filename, log=True):
        """See `~MovieStim.loadMovie` (the functions are identical).

        This form is provided for syntactic consistency with other visual
        stimuli.
        """
        self.loadMovie(filename, log=log)

    def loadMovie(self, filename, log=True):
        """Load a movie from file

        Parameters
        ----------
        filename : str
            The name of the file or URL, including path if necessary.
        log : bool
            Log this event.

        Notes
        -----
        * Due to VLC oddness, `.duration` is not correct until the movie starts
          playing.

        """
        self._filename = pathToString(filename)

        # open the media using a new player
        self._openMedia()

        self.status = NOT_STARTED
        logAttrib(self, log, 'movie', filename)

    def _createVLCInstance(self):
        """Internal method to create a new VLC instance.

        Raises an error if an instance is already spawned and hasn't been
        released.
        """
        logging.debug("Spawning new VLC instance ...")

        # Creating VLC instances is slow, so we want to create once per class
        # instantiation and reuse it as much as possible. Stopping and starting
        # instances too frequently can result in an errors and affect the
        # stability of the system.

        if self._instance is not None:
            self._releaseVLCInstance()
            # errmsg = ("Attempted to create another VLC instance without "
            #           "releasing the previous one first!")
            # logging.fatal(errmsg, obj=self)
            # logging.flush()
            # raise RuntimeError(errmsg)

        # Using "--quiet" here is just sweeping anything VLC pukes out under the
        # rug. Most of the time the errors only look scary but can be ignored.
        params = " ".join(
            ["--no-audio" if self._noAudio else "", "--sout-keep", "--quiet"])
        self._instance = vlc.Instance(params)

        # used to capture log messages from VLC
        self._instance.log_set(vlcLogCallback, None)

        # create a new player object, reusable by by just changing the stream
        self._player = self._instance.media_player_new()

        # setup the event manager
        self._manager = self._player.event_manager()
        # self._manager.event_attach(
        #     vlc.EventType.MediaPlayerTimeChanged, vlcMediaEventCallback,
        #     weakref.ref(self), self._player)
        self._manager.event_attach(
            vlc.EventType.MediaPlayerEndReached, vlcMediaEventCallback,
            weakref.ref(self), self._player)

        self._vlcInitialized = True

        logging.debug("VLC instance created.")

    def _releaseVLCInstance(self):
        """Internal method to release a VLC instance. Calling this implicitly
        stops and releases any stream presently loaded and playing.
        """
        self._vlcInitialized = False

        if self._player is not None:
            self._player.stop()

            # shutdown the manager
            self._manager.event_detach(vlc.EventType.MediaPlayerEndReached)
            self._manager = None

            # Doing this here since I figured Python wasn't shutting down due to
            # callbacks remaining bound. Seems to actually fix the problem.
            self._player.video_set_callbacks(None, None, None, None)
            self._player.set_media(None)
            self._player.release()
            self._player = None

            # reset video information
            self._filename = None
            self._videoWidth = self._videoHeight = 0
            self._frameCounter = self._loopCount = 0
            self._frameRate = 0.0
            self._framePixelBuffer = None

        if self._stream is not None:
            self._stream.release()
            self._streamEnded = False
            self._stream = None

        if self._instance is not None:
            self._instance.release()
            self._instance = None

        self.status = STOPPED

    def _openMedia(self, uri=None):
        """Internal method that opens a new stream using `filename`. This will
        close the previous stream. Raises an error if a VLC instance is not
        available.
        """
        # if None, use `filename`
        uri = self.filename if uri is None else uri

        # create a fresh VLC instance
        self._createVLCInstance()

        # raise error if there is no VLC instance
        if self._instance is None:
            errmsg = "Cannot open a stream without a VLC instance started."
            logging.fatal(errmsg, obj=self)
            logging.flush()

        # check if we have a player, stop it if so
        if self._player is None:
            errmsg = "Cannot open a stream without a VLC media player."
            logging.fatal(errmsg, obj=self)
            logging.flush()
        else:
            self._player.stop()  # stop any playback

        # check if the file is valid and readable
        if not os.access(uri, os.R_OK):
            raise RuntimeError('Error: %s file not readable' % uri)

        # close the previous VLC resources if needed
        if self._stream is not None:
            self._stream.release()

        # open the file and create a new stream
        try:
            self._stream = self._instance.media_new(uri)
        except NameError:
            raise ImportError('NameError: %s vs LibVLC %s' % (
                vlc.__version__, vlc.libvlc_get_version()))

        # player object
        self._player.set_media(self._stream)

        # set media related attributes
        self._stream.parse()
        videoWidth, videoHeight = self._player.video_get_size()
        self._videoWidth = videoWidth
        self._videoHeight = videoHeight

        # set the video size
        if self._useFrameSizeFromVideo:
            self.size = self._origSize = numpy.array(
                (self._videoWidth, self._videoHeight), float)

        self._frameRate = self._player.get_fps()
        self._frameCounter = self._loopCount = 0
        self._streamEnded = False

        # uncomment if not using direct GPU write, might be more thread-safe
        self._framePixelBuffer = (
                ctypes.c_ubyte * self._videoWidth * self._videoHeight * 4)()

        # duration unavailable until started
        duration = self._player.get_length()
        logging.info("Video is %ix%i, duration %s, fps %s" % (
            self._videoWidth, self._videoHeight, duration, self._frameRate))
        logging.flush()

        # We assume we can use the RGBA format here
        self._player.video_set_format(
            "RGBA", self._videoWidth, self._videoHeight, self._videoWidth << 2)

        # setup texture buffers before binding the callbacks
        self._setupTextureBuffers()

        # Set callbacks since we have the resources to write to.
        thisInstance = ctypes.cast(
            ctypes.pointer(ctypes.py_object(self)), ctypes.c_void_p)
        
        # we need to increment the ref count
        ctypes.pythonapi.Py_IncRef(ctypes.py_object(thisInstance))
        

        self._player.video_set_callbacks(
            vlcLockCallback, vlcUnlockCallback, vlcDisplayCallback,
            thisInstance)

    def _closeMedia(self):
        """Internal method to release the presently loaded stream (if any).
        """
        self._vlcInitialized = False

        if self._player is not None:  # stop any playback
            self._player.stop()
            self._player.set_media(None)

        if self._stream is None:
            return  # nop

        self._stream.release()
        self._stream = self._player = None
        self._useFrameSizeFromVideo = True

        self._releaseVLCInstance()

        # unregister callbacks before freeing buffers
        self._freeBuffers()
        GL.glFlush()

    def _onEos(self):
        """Internal method called when the decoder encounters the end of the
        stream.
        """
        # Do not call the libvlc API in this method, causes a deadlock which
        # freezes PsychoPy. Just set the flag below and the stream will restart
        # on the next `.draw()` call.
        self._streamEnded = True

        if not self.loop:
            self.status = FINISHED

        if self.autoLog:
            self.win.logOnFlip(
                "Set %s finished" % self.name, level=logging.EXP, obj=self)

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
        self._freeBuffers()  # clean up any buffers previously allocated

        # Calculate the total size of the pixel store in bytes needed to hold a
        # single video frame. This value is reused during the pixel upload
        # process. Assumes RGBA color format.
        self._videoFrameBufferSize = \
            self._videoWidth * self._videoHeight * 4 * ctypes.sizeof(GL.GLubyte)

        # Create the pixel buffer object which will serve as the texture memory
        # store. Pixel data will be copied to this buffer each frame.
        GL.glGenBuffers(1, ctypes.byref(self._pixbuffId))
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, self._pixbuffId)
        GL.glBufferData(
            GL.GL_PIXEL_UNPACK_BUFFER,
            self._videoFrameBufferSize,
            None,
            GL.GL_STREAM_DRAW)  # one-way app -> GL
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)

        # Create a texture which will hold the data streamed to the pixel
        # buffer. Only one texture needs to be allocated.
        GL.glGenTextures(1, ctypes.byref(self._textureId))
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._textureId)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGBA8,
            self._videoWidth, self._videoHeight,  # frame dims in pixels
            0,
            GL.GL_RGBA,
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

        GL.glFlush()  # make sure all buffers are ready

    @property
    def frameTexture(self):
        """Texture ID for the current video frame (`GLuint`). You can use this
        as a video texture. However, you must periodically call `updateTexture`
        to keep this up to date.

        """
        return self._textureId

    def _pixelTransfer(self):
        """Internal method which maps the pixel buffer for the video texture
        to client memory, allowing for VLC to directly draw a video frame to it.

        This method is not thread-safe and should never be called without the
        pixel lock semaphore being first set by VLC.

        """
        # bind pixel unpack buffer
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, self._pixbuffId)

        # Free last storage buffer before mapping and writing new frame data.
        # This allows the GPU to process the extant buffer in VRAM uploaded last
        # cycle without being stalled by the CPU accessing it. Also allows VLC
        # to access the buffer while the previous one is still in use.
        GL.glBufferData(
            GL.GL_PIXEL_UNPACK_BUFFER,
            self._videoFrameBufferSize,
            None,
            GL.GL_STREAM_DRAW)

        # Map the buffer to client memory, `GL_WRITE_ONLY` to tell the driver to
        # optimize for a one-way write operation if it can.
        bufferPtr = GL.glMapBuffer(
            GL.GL_PIXEL_UNPACK_BUFFER,
            GL.GL_WRITE_ONLY)

        # comment to disable direct VLC -> GPU frame write
        # self._framePixelBuffer = bufferPtr

        # uncomment if not using direct GPU write, might provide better thread
        # safety ...
        ctypes.memmove(
            bufferPtr,
            ctypes.byref(self._framePixelBuffer),
            ctypes.sizeof(self._framePixelBuffer))

        # Very important that we unmap the buffer data after copying, but
        # keep the buffer bound for setting the texture.
        GL.glUnmapBuffer(GL.GL_PIXEL_UNPACK_BUFFER)

        # bind the texture in OpenGL
        GL.glEnable(GL.GL_TEXTURE_2D)

        # copy the PBO to the texture
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._textureId)
        GL.glTexSubImage2D(
            GL.GL_TEXTURE_2D, 0, 0, 0,
            self._videoWidth,
            self._videoHeight,
            GL.GL_RGBA,
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

    def updateTexture(self):
        """Update the video texture buffer to the most recent video frame.
        """
        with self._pixelLock:
            self._pixelTransfer()

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
        if self.isNotStarted:  # video has not been played yet
            if log and self.autoLog:
                self.win.logOnFlip(
                    "Set %s playing" % self.name,
                    level=logging.EXP,
                    obj=self)

            self._player.play()

        elif self.isPaused:
            self.win.logOnFlip(
                "Resuming playback at position {:.4f}".format(
                    self._player.get_time() / 1000.0),
                level=logging.EXP,
                obj=self)

            if self._player.will_play():
                self._player.play()

        self.status = PLAYING

        return self._currentFrame

    def pause(self, log=True):
        """Pause the current point in the movie.

        Parameters
        ----------
        log : bool
            Log the pause event.

        """
        if self.isPlaying:
            self.status = PAUSED
            player = self._player
            if player and player.can_pause():
                player.pause()
            if log and self.autoLog:
                self.win.logOnFlip("Set %s paused" % self.name,
                                   level=logging.EXP, obj=self)
            return True
        if log and self.autoLog:
            self.win.logOnFlip("Failed Set %s paused" % self.name,
                               level=logging.EXP, obj=self)
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

        if self._player is None:
            return

        self.status = STOPPED

        if log and self.autoLog:
            self.win.logOnFlip(
                "Set %s stopped" % self.name, level=logging.EXP, obj=self)

        self._releaseVLCInstance()

    def seek(self, timestamp, log=True):
        """Seek to a particular timestamp in the movie.

        Parameters
        ----------
        timestamp : float
            Time in seconds.
        log : bool
            Log the seek event.

        """
        if self.isPlaying or self.isPaused:
            player = self._player
            if player and player.is_seekable():
                # pause while seeking
                player.set_time(int(timestamp * 1000.0))

            if log:
                logAttrib(self, log, 'seek', timestamp)

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
        self.seek(max(self.getCurrentFrameTime() - float(seconds), 0.0))

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
        self.seek(
            min(self.getCurrentFrameTime() + float(seconds), self.duration))

        return self.getCurrentFrameTime()

    def replay(self, autoPlay=True):
        """Replay the movie from the beginning.

        Parameters
        ----------
        autoPlay : bool
            Start playback immediately. If `False`, you must call `play()`
            afterwards to initiate playback.

        Notes
        -----
        * This tears down the current VLC instance and creates a new one.
          Similar to calling `stop()` and `loadMovie()`. Use `seek(0.0)` if you
          would like to restart the movie without reloading.

        """
        lastMovieFile = self._filename
        self.stop()
        self.loadMovie(lastMovieFile)

        if autoPlay:
            self.play()

    # --------------------------------------------------------------------------
    # Volume controls
    #
    @property
    def volume(self):
        """Audio track volume (`int` or `float`). See `setVolume` for more
        information about valid values.

        """
        return self.getVolume()

    @volume.setter
    def volume(self, value):
        self.setVolume(value)

    def setVolume(self, volume):
        """Set the audio track volume.

        Parameters
        ----------
        volume : int or float
            Volume level to set. 0 = mute, 100 = 0 dB. float values between 0.0
            and 1.0 are also accepted, and scaled to an int between 0 and 100.

        """
        if self._player:
            if 0.0 <= volume <= 1.0 and isinstance(volume, float):
                v = int(volume * 100)
            else:
                v = int(volume)
            self._volume = v

            if self._player:
                self._player.audio_set_volume(v)

    def getVolume(self):
        """Returns the current movie audio volume.

        Returns
        -------
        int
            Volume level, 0 is no audio, 100 is max audio volume.

        """
        if self._player:
            self._volume = self._player.audio_get_volume()

        return self._volume

    def increaseVolume(self, amount=10):
        """Increase the volume.

        Parameters
        ----------
        amount : int
            Increase the volume by this amount (percent). This gets added to the
            present volume level. If the value of `amount` and the current
            volume is outside the valid range of 0 to 100, the value will be
            clipped. The default value is 10 (or 10% increase).

        Returns
        -------
        int
            Volume after changed.

        See also
        --------
        getVolume
        setVolume
        decreaseVolume

        Examples
        --------
        Adjust the volume of the current video using key presses::

            # assume `mov` is an instance of this class defined previously
            for key in event.getKeys():
                if key == 'minus':
                    mov.decreaseVolume()
                elif key == 'equals':
                    mov.increaseVolume()

        """
        if not self._player:
            return 0

        self.setVolume(min(max(self.getVolume() + int(amount), 0), 100))

        return self._volume

    def decreaseVolume(self, amount=10):
        """Decrease the volume.

        Parameters
        ----------
        amount : int
            Decrease the volume by this amount (percent). This gets subtracted
            from the present volume level. If the value of `amount` and the
            current volume is outside the valid range of 0 to 100, the value
            will be clipped. The default value is 10 (or 10% decrease).

        Returns
        -------
        int
            Volume after changed.

        See also
        --------
        getVolume
        setVolume
        increaseVolume

        Examples
        --------
        Adjust the volume of the current video using key presses::

            # assume `mov` is an instance of this class defined previously
            for key in event.getKeys():
                if key == 'minus':
                    mov.decreaseVolume()
                elif key == 'equals':
                    mov.increaseVolume()

        """
        if not self._player:
            return 0

        self.setVolume(min(max(self.getVolume() - int(amount), 0), 100))

        return self._volume

    # --------------------------------------------------------------------------
    # Video and playback information
    #
    @property
    def frameIndex(self):
        """Current frame index being displayed (`int`)."""
        return self._currentFrame

    def getCurrentFrameNumber(self):
        """Get the current movie frame number (`int`), same as `frameIndex`.
        """
        return self._frameCounter

    @property
    def percentageComplete(self):
        """Percentage of the video completed (`float`)."""
        return self.getPercentageComplete()

    @property
    def duration(self):
        """Duration of the loaded video in seconds (`float`). Not valid unless
        the video has been started.
        """
        if not self.isNotStarted:
            return self._player.get_length()

        return 0.0

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
        return self._frameRate

    @property
    def frameTime(self):
        """Current frame time in seconds (`float`)."""
        return self.getCurrentFrameTime()

    def getCurrentFrameTime(self):
        """Get the time that the movie file specified the current video frame as
        having.

        Returns
        -------
        float
            Current video time in seconds.

        """
        if not self._player:
            return 0.0

        return self._player.get_time() / 1000.0

    def getPercentageComplete(self):
        """Provides a value between 0.0 and 100.0, indicating the amount of the
        movie that has been already played.
        """
        return self._player.get_position() * 100.0

    @property
    def videoSize(self):
        """Size of the video `(w, h)` in pixels (`tuple`). Returns `(0, 0)` if
        no video is loaded."""
        if self._stream is not None:
            return self._videoWidth, self._videoHeight

        return 0, 0

    # --------------------------------------------------------------------------
    # Drawing methods and properties
    #
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
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._textureId)
        GL.glPushClientAttrib(GL.GL_CLIENT_VERTEX_ARRAY_BIT)

        # 2D texture array, 3D vertex array
        GL.glInterleavedArrays(GL.GL_T2F_V3F, 0, array)
        GL.glDrawArrays(GL.GL_QUADS, 0, 4)
        GL.glPopClientAttrib()
        GL.glPopAttrib()
        GL.glPopMatrix()

        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glEnable(GL.GL_TEXTURE_2D)

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
        if self.isNotStarted and self._autoStart:
            self.play()
        elif self._streamEnded and self.loop:
            self._loopCount += 1
            self._streamEnded = False
            self.replay()
        elif self.isFinished:
            self.stop()
            return False

        self._selectWindow(self.win if win is None else win)

        # check if we need to pull a new frame this round
        if self._currentFrame == self._frameCounter:

            # update the texture, getting the most recent frame
            self.updateTexture()

            # draw the frame to the window
            self._drawRectangle()

            return False  # frame does not need an update this round

        # Below not called if the frame hasn't advanced yet ------

        # update the current frame
        self._currentFrame = self._frameCounter

        # update the texture, getting the most recent frame
        self.updateTexture()

        # draw the frame to the window
        self._drawRectangle()

        # token gesture for existing code, we handle this logic internally now
        return True

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

    def __del__(self):
        try:
            if hasattr(self, '_player'):
                # false if crashed before creating instance
                self._releaseVLCInstance()
        except (ImportError, ModuleNotFoundError, TypeError):
            pass  # has probably been garbage-collected already


# ------------------------------------------------------------------------------
# Callback functions for `libvlc`
#
# WARNING: Due to a limitation of libvlc, you cannot call the API from within
# the callbacks below. Doing so will result in a deadlock that stalls the
# application. This applies to any method in the `VloMovieStim` class being
# called within a callback too. They cannot have any libvlc calls anywhere in
# the call stack.
#

@vlc.CallbackDecorators.VideoLockCb
def vlcLockCallback(user_data, planes):
    """Callback invoked when VLC has new texture data.
    """
    # Need to catch errors caused if a NULL object is passed. Not sure why this
    # happens but it might be due to the callback being invoked before the
    # movie stim class is fully realized. This may happen since the VLC library
    # operates in its own thread and may be processing frames before we are
    # ready to use them. This `try-except` structure is present in all callback
    # functions here that pass `user_data` which is a C pointer to the stim
    # object. Right now, these functions just return when we get a NULL object.
    #
    try:
        cls = ctypes.cast(
            user_data, ctypes.POINTER(ctypes.py_object)).contents.value
    except (ValueError, TypeError):
        return

    cls._pixelLock.acquire()

    # tell VLC to take the data and stuff it into the buffer
    planes[0] = ctypes.cast(cls._framePixelBuffer, ctypes.c_void_p)


@vlc.CallbackDecorators.VideoUnlockCb
def vlcUnlockCallback(user_data, picture, planes):
    """Called when VLC releases the frame draw buffer.
    """
    try:
        cls = ctypes.cast(
            user_data, ctypes.POINTER(ctypes.py_object)).contents.value
    except (ValueError, TypeError):
        return

    cls._pixelLock.release()


@vlc.CallbackDecorators.VideoDisplayCb
def vlcDisplayCallback(user_data, picture):
    """Callback used by VLC when its ready to display a new frame.
    """
    try:
        cls = ctypes.cast(
            user_data, ctypes.POINTER(ctypes.py_object)).contents.value
    except (ValueError, TypeError):
        return

    cls._frameCounter += 1


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

    if event == vlc.EventType.MediaPlayerEndReached:
        cls._onEos()


if __name__ == "__main__":
    pass
