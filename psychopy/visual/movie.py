#!/usr/bin/env python

'''A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy.'''

# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys
import os

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl

#on windows try to load avbin now (other libs can interfere)
if sys.platform == 'win32':
    #make sure we also check in SysWOW64 if on 64-bit windows
    if 'C:\\Windows\\SysWOW64' not in os.environ['PATH']:
        os.environ['PATH'] += ';C:\\Windows\\SysWOW64'
    try:
        from pyglet.media import avbin
        haveAvbin = True
    except ImportError:
        # either avbin isn't installed or scipy.stats has been imported
        # (prevents avbin loading)
        haveAvbin = False

import psychopy  # so we can get the __path__
from psychopy import core, logging, event
import psychopy.event

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.arraytools import val2array
from psychopy import makeMovies
from psychopy.visual.basevisual import BaseVisualStim

if sys.platform == 'win32' and not haveAvbin:
    logging.error("""avbin.dll failed to load.
                     Try importing psychopy.visual as the first library
                     (before anything that uses scipy)
                     and make sure that avbin is installed.""")

import numpy

try:
    from pyglet import media
    havePygletMedia = True
except:
    havePygletMedia = False

from psychopy.constants import FINISHED, NOT_STARTED, PAUSED, PLAYING, STOPPED


class MovieStim(BaseVisualStim):
    """A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy.

    **Example**::

        mov = visual.MovieStim(myWin, 'testMovie.mp4', flipVert=False)
        print mov.duration
        print mov.format.width, mov.format.height #give the original size of the movie in pixels

        mov.draw() #draw the current frame (automagically determined)

    See MovieStim.py for demo.

    mov.contains() and mov.overlaps() will work only if the containing
    visual.Window() has units='pix'.
    """
    def __init__(self, win,
                 filename = "",
                 units   = 'pix',
                 size    = None,
                 pos      =(0.0,0.0),
                 ori     =0.0,
                 flipVert = False,
                 flipHoriz = False,
                 color=(1.0,1.0,1.0),
                 colorSpace='rgb',
                 opacity=1.0,
                 name='',
                 loop=False,
                 autoLog=True,
                 depth=0.0,):
        """
        :Parameters:

            filename :
                a string giving the relative or absolute path to the movie. Can be any movie that
                AVbin can read (e.g. mpeg, DivX)
            flipVert : True or *False*
                If True then the movie will be top-bottom flipped
            flipHoriz : True or *False*
                If True then the movie will be right-left flipped
            loop : bool, optional
                Whether to start the movie over from the beginning if draw is
                called and the movie is done.

        """
        BaseVisualStim.__init__(self, win, units=units, name=name, autoLog=autoLog)

        if not havePygletMedia:
            raise ImportError, """pyglet.media is needed for MovieStim and could not be imported.
                This can occur for various reasons;
                    - psychopy.visual was imported too late (after a lib that uses scipy)
                    - no audio output is enabled (no audio card or no speakers attached)
                    - avbin is not installed
            """
        self._movie=None # the actual pyglet media object
        self._player=pyglet.media.ManagedSoundPlayer()
        self._player._on_eos=self._onEos
        self.filename=filename
        self.duration=None
        self.loop = loop
        if loop and pyglet.version>='1.2':
            logging.error("looping of movies is not currently supported for pyglet>=1.2 only for version 1.1.4")
        self.loadMovie( self.filename )
        self.format=self._movie.video_format
        self.pos = numpy.asarray(pos, float)
        self.depth=depth
        self.flipVert = flipVert
        self.flipHoriz = flipHoriz
        self.colorSpace=colorSpace
        self.setColor(color, colorSpace=colorSpace, log=False)
        self.opacity = float(opacity)
        self.status=NOT_STARTED

        #size
        if size == None: self.size= numpy.array([self.format.width,
                                                 self.format.height] , float)
        else:
            self.size = val2array(size)

        self.ori = ori
        self._calcPosRendered()
        self._calcSizeRendered()

        # enable self.contains(), overlaps(); currently win must have pix units:
        self._calcVertices()

        #check for pyglet
        if win.winType!='pyglet':
            logging.Error('Movie stimuli can only be used with a pyglet window')
            core.quit()
    def _calcVertices(self):
        R, T = self._sizeRendered / 2  # pix
        L, B = -R, -T
        self._vertices = numpy.array([[L, T], [R, T], [R, B], [L, B]])
        self.needVertexUpdate = True
    def _calcVerticesRendered(self):
        self.needVertexUpdate = False
        self._verticesRendered = self._vertices
        self._posRendered = self.pos
    def setMovie(self, filename, log=True):
        """See `~MovieStim.loadMovie` (the functions are identical).
        This form is provided for syntactic consistency with other visual stimuli.
        """
        self.loadMovie(filename, log=log)

    def loadMovie(self, filename, log=True):
        """Load a movie from file

        :Parameters:

            filename: string
                The name of the file, including path if necessary

        Brings up a warning if avbin is not found on the computer.
        After the file is loaded MovieStim.duration is updated with the movie
        duration (in seconds).
        """
        try:
            self._movie = pyglet.media.load(filename, streaming=True)
        except Exception, e:
            # pyglet.media.riff is N/A if avbin is available, and then
            # actual exception would get masked with a new one for unknown
            # (sub)module riff, thus catching any exception and tuning msg
            # up if it has to do anything with avbin
            estr = str(e)
            msg = ''
            if "avbin" in estr.lower():
                msg = "\n         It seems that avbin was not installed correctly." \
                      "\n         Please fetch/install it from http://code.google.com/p/avbin/."
            raise IOError("Caught exception '%s' while loading file '%s'.%s"
                          % (estr, filename, msg))
        self._player.queue(self._movie)
        self.duration = self._movie.duration
        while self._player.source!=self._movie:
            self._player.next()
        self.status=NOT_STARTED
        self._player.pause()#start 'playing' on the next draw command
        self.filename=filename
        if log and self.autoLog:
            self.win.logOnFlip("Set %s movie=%s" %(self.name, filename),
                level=logging.EXP,obj=self)

    def pause(self, log=True):
        """Pause the current point in the movie (sound will stop, current frame
        will not advance).  If play() is called again both will restart.
        """
        self._player.pause()
        self.status=PAUSED
        if log and self.autoLog:
            self.win.logOnFlip("Set %s paused" %(self.name),
                level=logging.EXP,obj=self)
    def stop(self, log=True):
        """Stop the current point in the movie (sound will stop, current frame
        will not advance). Once stopped the movie cannot be restarted - it must
        be loaded again. Use pause() if you may need to restart the movie.
        """
        self._player.stop()
        self.status=STOPPED
        if log and self.autoLog:
            self.win.logOnFlip("Set %s stopped" %(self.name),
                level=logging.EXP,obj=self)
    def play(self, log=True):
        """Continue a paused movie from current position
        """
        self._player.play()
        self.status=PLAYING
        if log and self.autoLog:
            self.win.logOnFlip("Set %s playing" %(self.name),
                level=logging.EXP,obj=self)
    def seek(self,timestamp, log=True):
        """ Seek to a particular timestamp in the movie.
        NB this does not seem very robust as at version 1.62 and may cause crashes!
        """
        self._player.seek(float(timestamp))
        if log and self.autoLog:
            self.win.logOnFlip("Set %s seek=%f" %(self.name,timestamp),
                level=logging.EXP,obj=self)
    def setFlipHoriz(self, newVal=True, log=True):
        """If set to True then the movie will be flipped horiztonally (left-to-right).
        Note that this is relative to the original, not relative to the current state.
        """
        self.flipHoriz = newVal
        if log and self.autoLog:
            self.win.logOnFlip("Set %s flipHoriz=%s" % (self.name, newVal),
                level=logging.EXP, obj=self)
    def setFlipVert(self, newVal=True, log=True):
        """If set to True then the movie will be flipped vertically (top-to-bottom).
        Note that this is relative to the original, not relative to the current state.
        """
        self.flipVert = newVal
        if log and self.autoLog:
            self.win.logOnFlip("Set %s flipVert=%s" % (self.name, newVal),
                level=logging.EXP, obj=self)

    def draw(self, win=None):
        """Draw the current frame to a particular visual.Window (or to the
        default win for this object if not specified). The current position in
        the movie will be determined automatically.

        This method should be called on every frame that the movie is meant to
        appear"""

        if self.status == PLAYING and not self._player.playing:
            self.status = FINISHED
        if self.status==NOT_STARTED or (self.status==FINISHED and self.loop):
            self.play()
        elif self.status == FINISHED and not self.loop:
            return

        if win==None: win=self.win
        self._selectWindow(win)

        #make sure that textures are on and GL_TEXTURE0 is active
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        if pyglet.version>='1.2': #for pyglet 1.1.4 this was done via media.dispatch_events
            self._player.update_texture()
        frameTexture = self._player.get_texture()
        if frameTexture==None:
            return

        desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace, 1)  #Contrast=1
        GL.glColor4f(desiredRGB[0],desiredRGB[1],desiredRGB[2],self.opacity)
        GL.glPushMatrix()
        #do scaling
        #scale the viewport to the appropriate size
        self.win.setScale(self._winScale)
        #move to centre of stimulus and rotate
        GL.glTranslatef(self._posRendered[0],self._posRendered[1],0)
        GL.glRotatef(-self.ori,0.0,0.0,1.0)
        flipBitX = 1-self.flipHoriz*2
        flipBitY = 1-self.flipVert*2
        frameTexture.blit(
                -self._sizeRendered[0]/2.0*flipBitX,
                -self._sizeRendered[1]/2.0*flipBitY,
                width=self._sizeRendered[0]*flipBitX,
                height=self._sizeRendered[1]*flipBitY,
                z=0)
        GL.glPopMatrix()

    def setContrast(self):
        """"Not yet implemented for MovieStim"""
        pass

    def _onEos(self):
        if self.loop:
            self.loadMovie(self.filename)
            self.play()
            self.status=PLAYING
        else:
            self.status=FINISHED
        if self.autoLog:
            self.win.logOnFlip("Set %s finished" %(self.name),
                level=logging.EXP,obj=self)
    def setAutoDraw(self, val, log=True):
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
        #add to drawing list and update status
        BaseVisualStim.autoDraw = val
    def __del__(self):
        self._clearTextures()
