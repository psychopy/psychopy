#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy.
"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, division, print_function

from builtins import next
from builtins import str
import sys
import os

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl

# on windows try to load avbin now (other libs can interfere)
if sys.platform == 'win32':
    # make sure we also check in SysWOW64 if on 64-bit windows
    if 'C:\\Windows\\SysWOW64' not in os.environ['PATH']:
        os.environ['PATH'] += ';C:\\Windows\\SysWOW64'

    try:
        from pyglet.media import avbin
        haveAvbin = True
    except ImportError:
        # either avbin isn't installed or scipy.stats has been imported
        # (prevents avbin loading)
        haveAvbin = False
    except Exception as e:
        # WindowsError on some systems
        # AttributeError if using avbin5 from pyglet 1.2?
        haveAvbin = False


import psychopy  # so we can get the __path__
from psychopy import core, logging, event
import psychopy.event

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import logAttrib, setAttribute
from psychopy.visual.basevisual import BaseVisualStim, ContainerMixin
from psychopy.tools.filetools import pathToString

if sys.platform == 'win32' and not haveAvbin:
    logging.warning("avbin.dll failed to load. "
                    "Try importing psychopy.visual as the first library "
                    "(before anything that uses scipy) or use a different"
                    "movie backend (e.g. moviepy).")

import numpy
try:
    from pyglet import media
    havePygletMedia = True
except Exception:
    havePygletMedia = False

from psychopy.constants import FINISHED, NOT_STARTED, PAUSED, PLAYING, STOPPED


class MovieStim(BaseVisualStim, ContainerMixin):
    """A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy.

    **Example**::

        mov = visual.MovieStim(myWin, 'testMovie.mp4', flipVert=False)
        print(mov.duration)
        # give the original size of the movie in pixels:
        print(mov.format.width, mov.format.height)

        mov.draw()  # draw the current frame (automagically determined)

    See MovieStim.py for demo.
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
                 name=None,
                 loop=False,
                 autoLog=None,
                 depth=0.0,):
        """
        :Parameters:

            filename :
                a string giving the relative or absolute path to the movie.
                Can be any movie that AVbin can read (e.g. mpeg, DivX)
            flipVert : True or *False*
                If True then the movie will be top-bottom flipped
            flipHoriz : True or *False*
                If True then the movie will be right-left flipped
            volume :
                The nominal level is 1.0, and 0.0 is silence,
                see pyglet.media.Player
            loop : bool, optional
                Whether to start the movie over from the beginning
                if draw is called and the movie is done.

        """
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')

        super(MovieStim, self).__init__(
            win, units=units, name=name, autoLog=False)
        self._verticesBase *= numpy.array([[-1, 1]])  # unflip

        if not havePygletMedia:
            msg = ("pyglet.media is needed for MovieStim and could not be"
                   " imported.\nThis can occur for various reasons;"
                   "    - psychopy.visual was imported too late (after a lib"
                   " that uses scipy)"
                   "    - no audio output is enabled (no audio card or no "
                   "speakers attached)"
                   "    - avbin is not installed")
            raise ImportError(msg)
        self._movie = None  # the actual pyglet media object
        self._player = pyglet.media.ManagedSoundPlayer()
        self._player.volume = volume
        try:
            self._player_default_on_eos = self._player.on_eos
        except Exception:
            # pyglet 1.1.4?
            self._player_default_on_eos = self._player._on_eos

        self.filename = pathToString(filename)
        self.duration = None
        self.loop = loop
        if loop and pyglet.version >= '1.2':
            logging.error("looping of movies is not currently supported "
                          "for pyglet >= 1.2 (only for version 1.1.4)")
        self.loadMovie(self.filename)
        self.format = self._movie.video_format
        self.pos = numpy.asarray(pos, float)
        self.depth = depth
        self.flipVert = flipVert
        self.flipHoriz = flipHoriz
        self.opacity = float(opacity)
        self.status = NOT_STARTED

        # size
        if size is None:
            self.size = numpy.array([self.format.width, self.format.height],
                                    float)
        else:
            self.size = val2array(size)

        self.ori = ori
        self._updateVertices()

        if win.winType != 'pyglet':
            logging.error('Movie stimuli can only be used with a '
                          'pyglet window')
            core.quit()

        # set autoLog now that params have been initialised
        wantLog = autoLog is None and self.win.autoLog
        self.__dict__['autoLog'] = autoLog or wantLog
        if self.autoLog:
            logging.exp("Created %s = %s" % (self.name, str(self)))

    def setMovie(self, filename, log=None):
        """See `~MovieStim.loadMovie` (the functions are identical).
        This form is provided for syntactic consistency with other visual
        stimuli.
        """
        self.loadMovie(filename, log=log)

    def loadMovie(self, filename, log=None):
        """Load a movie from file

        :Parameters:

            filename: string
                The name of the file, including path if necessary

        Brings up a warning if avbin is not found on the computer.
        After the file is loaded MovieStim.duration is updated with the movie
        duration (in seconds).
        """
        filename = pathToString(filename)
        try:
            self._movie = pyglet.media.load(filename, streaming=True)
        except Exception as e:
            # pyglet.media.riff is N/A if avbin is available, and then
            # actual exception would get masked with a new one for unknown
            # (sub)module riff, thus catching any exception and tuning msg
            # up if it has to do anything with avbin
            estr = str(e)
            msg = ''
            if "avbin" in estr.lower():
                msg = ("\nIt seems that avbin was not installed correctly."
                       "\nPlease fetch/install it from "
                       "http://code.google.com/p/avbin/.")
            emsg = "Caught exception '%s' while loading file '%s'.%s"
            raise IOError(emsg % (estr, filename, msg))
        self._player.queue(self._movie)
        self.duration = self._movie.duration
        while self._player.source != self._movie:
            next(self._player)
        self.status = NOT_STARTED
        self._player.pause()  # start 'playing' on the next draw command
        self.filename = filename
        logAttrib(self, log, 'movie', filename)

    def pause(self, log=None):
        """Pause the current point in the movie (sound will stop, current
        frame will not advance). If play() is called again both will restart.
        """
        self._player.pause()
        self._player._on_eos = self._player_default_on_eos
        self.status = PAUSED
        if log or log is None and self.autoLog:
            self.win.logOnFlip("Set %s paused" % self.name,
                               level=logging.EXP, obj=self)

    def stop(self, log=None):
        """Stop the current point in the movie.

        The sound will stop, current frame will not advance. Once stopped
        the movie cannot be restarted - it must be loaded again.
        Use pause() if you may need to restart the movie.
        """
        self._player.stop()
        self._player._on_eos = self._player_default_on_eos
        self.status = STOPPED
        if log or log is None and self.autoLog:
            self.win.logOnFlip("Set %s stopped" % self.name,
                               level=logging.EXP, obj=self)

    def play(self, log=None):
        """Continue a paused movie from current position.
        """
        self._player.play()
        self._player._on_eos = self._onEos
        self.status = PLAYING
        if log or log is None and self.autoLog:
            self.win.logOnFlip("Set %s playing" % self.name,
                               level=logging.EXP, obj=self)

    def seek(self, timestamp, log=None):
        """Seek to a particular timestamp in the movie.

        NB this does not seem very robust as at version 1.62, may crash!
        """
        self._player.seek(float(timestamp))
        logAttrib(self, log, 'seek', timestamp)

    def setFlipHoriz(self, newVal=True, log=None):
        """If set to True then the movie will be flipped horizontally
        (left-to-right). Note that this is relative to the original,
        not relative to the current state.
        """
        self.flipHoriz = newVal
        logAttrib(self, log, 'flipHoriz')
        self._needVertexUpdate = True

    def setFlipVert(self, newVal=True, log=None):
        """If set to True then the movie will be flipped vertically
        (top-to-bottom). Note that this is relative to the original,
        not relative to the current state.
        """
        self.flipVert = newVal
        logAttrib(self, log, 'flipVert')
        self._needVertexUpdate = True

    def draw(self, win=None):
        """Draw the current frame to a particular visual.Window.

        Draw to the default win for this object if not specified.
        The current position in the movie will be determined automatically.

        This method should be called on every frame that the movie is
        meant to appear.
        """

        if self.status == PLAYING and not self._player.playing:
            self.status = FINISHED
        _done = bool(self.status == FINISHED)
        if self.status == NOT_STARTED or (_done and self.loop):
            self.play()
        elif _done and not self.loop:
            return

        if win is None:
            win = self.win
        self._selectWindow(win)

        # make sure that textures are on and GL_TEXTURE0 is active
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        if pyglet.version >= '1.2':
            # for pyglet 1.1.4 this was done via media.dispatch_events
            self._player.update_texture()
        frameTexture = self._player.get_texture()
        if frameTexture is None:
            return

        # sets opacity (1,1,1 = RGB placeholder)
        GL.glColor4f(1, 1, 1, self.opacity)
        GL.glPushMatrix()
        self.win.setScale('pix')
        # move to centre of stimulus and rotate
        vertsPix = self.verticesPix
        t = frameTexture.tex_coords
        array = (GL.GLfloat * 32)(
            t[0], t[1],
            vertsPix[0, 0], vertsPix[0, 1], 0.,  # vertex
            t[3], t[4],
            vertsPix[1, 0], vertsPix[1, 1], 0.,
            t[6], t[7],
            vertsPix[2, 0], vertsPix[2, 1], 0.,
            t[9], t[10],
            vertsPix[3, 0], vertsPix[3, 1], 0.,
        )

        GL.glPushAttrib(GL.GL_ENABLE_BIT)
        GL.glEnable(frameTexture.target)
        GL.glBindTexture(frameTexture.target, frameTexture.id)
        GL.glPushClientAttrib(GL.GL_CLIENT_VERTEX_ARRAY_BIT)
        # 2D texture array, 3D vertex array
        GL.glInterleavedArrays(GL.GL_T2F_V3F, 0, array)
        GL.glDrawArrays(GL.GL_QUADS, 0, 4)
        GL.glPopClientAttrib()
        GL.glPopAttrib()
        GL.glPopMatrix()

    def setContrast(self):
        """Not yet implemented for MovieStim.
        """
        pass

    def _onEos(self):
        if self.loop:
            self.loadMovie(self.filename)
            self.play()
            self.status = PLAYING
        else:
            self.status = FINISHED
            self._player._on_eos = self._player_default_on_eos
        if self.autoLog:
            self.win.logOnFlip("Set %s finished" % self.name,
                               level=logging.EXP, obj=self)

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
            next(self._player)
        except Exception:
            pass
