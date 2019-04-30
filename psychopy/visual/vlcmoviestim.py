#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy
using VLC.  movie4 does /not/ require avbin to be installed.

Testing has only been done on Windows.

VlcMovieStim requires:
~~~~~~~~~~~~~~~~~~~~~

1. VLC. Just install the standard VLC of the same bitness as python
    for your OS.

    http://www.videolan.org/vlc/index.html

2. pip install python-vlc

To play a video:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a new instance, `mov = visual.VlcMovieStim(..)`

    shouldflip = mov.play()
    continueRoutine = True
    while continueRoutine:
        if shouldflip:
            # Draw other stimuli here
            win.flip()
        else:
            time.sleep(0.001)
        shouldflip = mov.draw()


To fix "stale cache" VLC errors on Windows...
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Libvlc has a bug related to changing from daylight standard time to daylight 
saving time. After the time change libvlc complains that the plugin cache is 
stale. The error message begins with "main libvlc error: stale plugins cache: 
...". VLC provides an executable to update the plugin cache timestamps. To run 
it, execute this as Administrator:

    cd "C:\Program Files\VideoLAN\VLC"
    vlc-cache-gen.exe "C:\Program Files\VideoLAN\VLC\plugins"


Not implemented:
~~~~~~~~~~~~~~~~

* Horizontal/vertical flipping
* getCurrentFrameTime
* getPercentageComplete

"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).
#
# VlcMovieStim contributed by Dan Fitch, April 2019.
# The MovieStim2 class was taken and rewritten to use only vlc

from __future__ import absolute_import, division, print_function

# If True then, on each flip a new movie frame is displayed, the frame index,
# flip time, and time since last movie frame flip will be printed
reportNDroppedFrames = 10

import os
import sys
import threading
import weakref

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl


import psychopy
from psychopy import core, logging

from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import logAttrib, setAttribute
from psychopy.tools.filetools import pathToString
from psychopy.visual.basevisual import BaseVisualStim, ContainerMixin
from psychopy.clock import Clock
from psychopy.constants import FINISHED, NOT_STARTED, PAUSED, PLAYING, STOPPED
from psychopy.tools.monitorunittools import convertToPix

import ctypes
import numpy

try:
    import vlc
except Exception as err:
    if sys.maxsize == 9223372036854775807:
        bits = 64
    else:
        bits = 32
    if "wrong architecture" in err:
        msg = ("Failed to import vlc module for MovieStim2.\n"
               "You're using %i-bit python. Is your VLC install the same?"
               % bits)
        raise OSError(msg)
    else:
        raise err



class TexturedRect:
    def __init__(self, texture_id):
        self.texture_id = texture_id
        self.pos = (0.0, 0.0)
        self.size = (1.0, 1.0)
        self.angle = 0
        self.init_vertexes()

    def init_vertexes(self):
        x = 0.5
        y = 0.5
        self.vertex_list = pyglet.graphics.vertex_list(4, ('v2f', [-x,y, x,y, -x,-y, x,-y]), ('t2f', [0,0, 1,0, 0,1, 1,1]))

    def set_position_and_size(self, pos, size):
        self.pos = pos
        self.size = size

    def draw(self):
        GL.glPushMatrix()
        GL.glTranslatef(self.pos[0], self.pos[1], 0)
        GL.glRotatef(self.angle, 0, 0, 1)
        GL.glScalef(self.size[0], self.size[1], 1)
        GL.glColor4f(1,1,1,1)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture_id)
        self.vertex_list.draw(GL.GL_TRIANGLE_STRIP)
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glPopMatrix()

# vlc.CallbackDecorators in python-vlc lib are incorrect and don't match VLC docs
CorrectVideoLockCb = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))
CorrectVideoUnlockCb = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))

@CorrectVideoLockCb
def vlcLockCallback(user_data, planes):
    self = ctypes.cast(user_data, ctypes.POINTER(ctypes.py_object)).contents.value
    self.pixel_lock.acquire()
    # Tell VLC to take the data and stuff it into the buffer
    planes[0] = ctypes.cast(self.pixel_buffer, ctypes.c_void_p)

@CorrectVideoUnlockCb
def vlcUnlockCallback(user_data, picture, planes):
    self = ctypes.cast(user_data, ctypes.POINTER(ctypes.py_object)).contents.value
    self.pixel_lock.release()

@vlc.CallbackDecorators.VideoDisplayCb
def vlcDisplayCallback(user_data, picture):
    self = ctypes.cast(user_data, ctypes.POINTER(ctypes.py_object)).contents.value
    self.frame_counter += 1


class VlcMovieStim(BaseVisualStim, ContainerMixin):
    """A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy
    that uses VLC and does not require avbin. The VLC media player must be 
    installed on the psychopy computer.
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
                 interpolate=True):
        """
        :Parameters:

            filename :
                a string giving the relative or absolute path to the movie.
            flipVert : True or *False*
                If True then the movie will be top-bottom flipped
            flipHoriz : True or *False*
                If True then the movie will be right-left flipped
            volume :
                The nominal level is 100, and 0 is silence.
            loop : bool, optional
                Whether to start the movie over from the beginning if draw is
                called and the movie is done.

        """
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
        self.depth = depth
        self.opacity = float(opacity)
        self.volume = volume
        self.no_audio = noAudio

        self.interpolate = interpolate
        self._texture_id = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._texture_id))

        self._vlc_initialized = False
        self._reset()
        self.loadMovie(self.filename)
        self.setVolume(volume)
        self.nDroppedFrames = 0

        self.ori = ori
        # set autoLog (now that params have been initialised)
        self.autoLog = autoLog
        if autoLog:
            logging.exp("Created {} = {}".format(self.name, self))

    def _reset(self):
        self.frame_counter = 0
        self.current_frame = 0
        self.duration = None
        self.status = NOT_STARTED
        self.width = None
        self.height = None
        self.frame_rate = None

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

        :Parameters:

            filename: string
                The name of the file, including path if necessary

        Due to VLC oddness, .duration is not correct until the movie starts playing.
        """
        self._reset()
        self.filename = pathToString(filename)

        # Initialize VLC
        self._vlc_start()

        self.status = NOT_STARTED
        logAttrib(self, log, 'movie', filename)

    def _vlc_start(self):
        """
        Create the vlc stream player for the video using python-vlc.
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

        player = instance.media_player_new()
        player.set_media(stream)

        # Load up the file
        stream.parse()
        size = player.video_get_size()
        self.video_width = size[0]
        self.video_height = size[1]
        self.frame_rate = player.get_fps()
        self.frame_counter = 0

        # TODO: Why is duration -1 still even after parsing? Newer vlc docs seem to hint this won't work until playback starts
        duration = player.get_length()
        logging.warning("Video is %ix%i, duration %s, fps %s" % (self.video_width, self.video_height, duration, self.frame_rate))
        logging.flush()

        # We assume we can use the RGBA format here
        player.video_set_format("RGBA", self.video_width, self.video_height, self.video_width << 2)

        # Configure a lock and a buffer for the pixels coming from VLC
        self.pixel_lock = threading.Lock()
        self.pixel_buffer = (ctypes.c_ubyte * self.video_width * self.video_height * 4)()

        # Configure a helper for drawing the texture
        self._video_rect = TexturedRect(self._texture_id)

        # Once you set these callbacks, you are in complete control of what to do with the video buffer
        selfref = ctypes.cast(ctypes.pointer(ctypes.py_object(self)), ctypes.c_void_p)

        player.video_set_callbacks(vlcLockCallback, vlcUnlockCallback, vlcDisplayCallback, selfref)

        # Keep references
        self._instance = instance
        self._player = player
        self._stream = stream

        self._vlc_initialized = True

    def _release_vlc(self):
        logging.info("Releasing VLC...")

        if self._player: self._player.stop()
        if self._stream: self._stream.release()
        if self._instance: self._instance.release()

        self._stream = None
        self._stream_event_manager = None
        self._player = None
        self._instance = None
        self._vlc_initialized = False

    def _update_texture(self):
        """
        Take the pixel buffer (assumed to be RGBA)
        and cram it into the GL texture
        """
        with self.pixel_lock:
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texture_id)
            GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
            if self.interpolate:
                interpolation = GL.GL_LINEAR
            else:
                interpolation = GL.GL_NEAREST
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, interpolation)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, interpolation)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB,
                            self.video_width,
                            self.video_height,
                            0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE,
                            self.pixel_buffer)
            GL.glDisable(GL.GL_TEXTURE_2D)


    def play(self, log=True):
        """Start or continue a paused movie from current position.
        """
        cstat = self.status
        if cstat != PLAYING:
            self.status = PLAYING

            if self._player:
                if cstat == PAUSED:
                    self._player.pause()
                else:
                    self._player.play()

            if log and self.autoLog:
                self.win.logOnFlip("Set %s playing" % (self.name),
                                   level=logging.EXP, obj=self)

            self._update_texture()
            return self.current_frame

    def pause(self, log=True):
        """Pause the current point in the movie (sound will stop, current
        frame will not advance). If play() is called again both will restart.
        """
        if self.status == PLAYING:
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
        """Stop the current point in the movie (sound will stop,
        current frame will not advance). Once stopped the movie cannot
        be restarted - it must be loaded again.

        Use pause() if you may need to restart the movie.
        """
        if self.status != STOPPED:
            self.status = STOPPED
            self._reset()
            if log and self.autoLog:
                self.win.logOnFlip("Set %s stopped" % (self.name),
                                   level=logging.EXP, obj=self)

    def seek(self, timestamp, log=True):
        """Seek to a particular timestamp in the movie.
        """
        if self.status in [PLAYING, PAUSED]:
            if self.status == PLAYING:
                self.pause()
            player = self._player
            if player and player.is_seekable():
                player.set_time(int(timestamp * 1000.0))

            if log:
                logAttrib(self, log, 'seek', timestamp)

            self.play()

    def setFlipHoriz(self, newVal=True, log=True):
        """If set to True then the movie will be flipped horizontally
        (left-to-right). Note that this is relative to the original,
        not relative to the current state.
        """
        self.flipHoriz = newVal
        logAttrib(self, log, 'flipHoriz')

    def setFlipVert(self, newVal=True, log=True):
        """If set to True then the movie will be flipped vertically
        (top-to-bottom). Note that this is relative to the original,
        not relative to the current state.
        """
        self.flipVert = not newVal
        logAttrib(self, log, 'flipVert')

    def setVolume(self, v):
        """Set the audio track volume. 0 = mute, 100 = 0 dB. float values
        between 0.0 and 1.0 are also accepted, and scaled to an int
        between 0 and 100.
        """
        if self._player:
            if 0.0 <= v <= 1.0 and isinstance(v, float):
                v = int(v * 100)
            else:
                v = int(v)
            self.volume = v
            if self._player:
                self._player.audio_set_volume(v)

    def getVolume(self):
        """Returns the current movie audio volume.

        0 is no audio, 100 is max audio volume.
        """
        if self._player:
            self.volume = self._player.audio_get_volume()
        return self.volume

    def getFPS(self):
        """
        Returns the movie frames per second playback speed.
        """
        return self.frame_rate

    def getCurrentFrameNumber(self):
        """Get the current movie frame number.
        The first frame number in a file is 1.
        """
        return self.frame_counter

    def getCurrentFrameTime(self):
        """Get the time that the movie file specified the current
        video frame as having.
        """
        # TODO
        return 0

    def getPercentageComplete(self):
        """Provides a value between 0.0 and 100.0, indicating the
        amount of the movie that has been already played.
        """
        # TODO
        return 0

    def draw(self, win=None):
        """Draw the current frame to a particular visual.Window (or to the
        default win for this object if not specified).
        The current position in the movie will be determined automatically.

        This method should be called on every frame that the movie is meant
        to appear.
        """
        if self.status == NOT_STARTED or (self.status == FINISHED and self.loop):
            self.play()
        elif self.status == FINISHED and not self.loop:
            return
        if win is None:
            win = self.win
        self._selectWindow(win)

        self._update_texture()

        win.setScale('pix')
        posPix = convertToPix([0, 0], self.pos, win.units, win)
        sizePix = convertToPix([0, 0], self.size, win.units, win)

        self._video_rect.angle = self.ori
        self._video_rect.set_position_and_size(posPix, sizePix)
        self._video_rect.draw()

        if self.current_frame != self.frame_counter:
            self.current_frame = self.frame_counter
            return True

    def setContrast(self):
        """Not yet implemented
        """
        pass

    def _unload(self):
        if self._vlc_initialized:
            self._release_vlc()
        if self._texture_id is not None:
            GL.glDeleteTextures(1, self._texture_id)
            self._texture_id = None
        self.status = FINISHED

    def _onEos(self):
        if self.loop:
            self.seek(0.0)
        else:
            self.status = FINISHED
            self.stop()
        if self.autoLog:
            self.win.logOnFlip("Set %s finished" % self.name,
                               level=logging.EXP, obj=self)

    def __del__(self):
        self._unload()

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
