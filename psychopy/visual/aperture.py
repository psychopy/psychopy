#!/usr/bin/env python

'''Restrict a stimulus visibility area to a basic shape
(circle, square, triangle)'''

# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys
import os
import glob
import copy

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
import pyglet
pyglet.options['debug_gl'] = False

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
from psychopy import core, platform_specific, logging, prefs, monitors, event
from psychopy import colors
import psychopy.event

# misc must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
import psychopy.misc
from psychopy import makeMovies
from psychopy.misc import (attributeSetter, setWithOperation, isValidColor,
                           makeRadialMatrix)

try:
    from PIL import Image
except ImportError:
    import Image

if sys.platform == 'win32' and not haveAvbin:
    logging.error("""avbin.dll failed to load.
                     Try importing psychopy.visual as the first library
                     (before anything that uses scipy)
                     and make sure that avbin is installed.""")

import numpy
from numpy import sin, cos, pi

from psychopy.core import rush

global currWindow
currWindow = None
reportNDroppedFrames = 5  # stop raising warning after this
reportNImageResizes = 5
global _nImageResizes
_nImageResizes = 0

#shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import ctypes
GL = pyglet.gl

import psychopy.gamma
#import pyglet.gl, pyglet.window, pyglet.image, pyglet.font, pyglet.event
import psychopy._shadersPyglet as _shaders
try:
    from pyglet import media
    havePygletMedia = True
except:
    havePygletMedia = False

try:
    import pygame
    havePygame = True
except:
    havePygame = False

#do we want to use the frameBufferObject (if available an needed)?
global useFBO
useFBO = False

try:
    import matplotlib
    if matplotlib.__version__ > '1.2':
        from matplotlib.path import Path as mpl_Path
    else:
        from matplotlib import nxutils
    haveMatplotlib = True
except:
    haveMatplotlib = False

global DEBUG
DEBUG = False

#symbols for MovieStim: PLAYING, STARTED, PAUSED, NOT_STARTED, FINISHED
from psychopy.constants import *


#keep track of windows that have been opened
openWindows = []

# can provide a default window for mouse
psychopy.event.visualOpenWindows = openWindows


class Aperture:
    """Restrict a stimulus visibility area to a basic shape (circle, square, triangle)

    When enabled, any drawing commands will only operate on pixels within the
    Aperture. Once disabled, subsequent draw operations affect the whole screen
    as usual.

    See demos/stimuli/aperture.py for example usage

    :Author:
        2011, Yuri Spitsyn
        2011, Jon Peirce added units options, Jeremy Gray added shape & orientation
    """
    def __init__(self, win, size, pos=(0,0), ori=0, nVert=120, shape='circle', units=None,
            name='', autoLog=True):
        self.win=win
        self.name = name
        self.autoLog=autoLog

        #unit conversions
        if units!=None and len(units): self.units = units
        else: self.units = win.units
        if self.units in ['norm','height']: self._winScale=self.units
        else: self._winScale='pix' #set the window to have pixels coords

        if shape.lower() == 'square':
            ori += 45
            nVert = 4
        elif shape.lower() == 'triangle':
            nVert = 3
        self.ori = ori
        self.nVert = 120
        if type(nVert) == int:
            self.nVert = nVert
        self.quad=GL.gluNewQuadric() #needed for gluDisk
        self.setSize(size, needReset=False)
        self.setPos(pos, needReset=False)
        self._reset()#implicitly runs an self.enable()
    def _reset(self):
        self.enable()
        GL.glClearStencil(0)
        GL.glClear(GL.GL_STENCIL_BUFFER_BIT)

        GL.glPushMatrix()
        self.win.setScale(self._winScale)
        GL.glTranslatef(self._posRendered[0], self._posRendered[1], 0)
        GL.glRotatef(-self.ori, 0.0, 0.0, 1.0)

        GL.glDisable(GL.GL_LIGHTING)
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDepthMask(GL.GL_FALSE)

        GL.glStencilFunc(GL.GL_NEVER, 0, 0)
        GL.glStencilOp(GL.GL_INCR, GL.GL_INCR, GL.GL_INCR)
        GL.glColor3f(0,0,0)
        GL.gluDisk(self.quad, 0, self._sizeRendered/2.0, self.nVert, 2)
        GL.glStencilFunc(GL.GL_EQUAL, 1, 1)
        GL.glStencilOp(GL.GL_KEEP, GL.GL_KEEP, GL.GL_KEEP)

        GL.glPopMatrix()

    def setSize(self, size, needReset=True, log=True):
        """Set the size (diameter) of the Aperture
        """
        self.size = size
        self._calcSizeRendered()
        if needReset: self._reset()
        if log and self.autoLog:
             self.win.logOnFlip("Set %s size=%s" %(self.name, size),
                 level=logging.EXP,obj=self)
    def setOri(self, ori, needReset=True, log=True):
        """Set the orientation of the Aperture
        """
        self.ori = ori
        if needReset: self._reset()
        if log and self.autoLog:
             self.win.logOnFlip("Set %s ori=%s" %(self.name, ori),
                 level=logging.EXP,obj=self)
    def setPos(self, pos, needReset=True, log=True):
        """Set the pos (centre) of the Aperture
        """
        self.pos = numpy.array(pos)
        self._calcPosRendered()
        if needReset: self._reset()
        if log and self.autoLog:
             self.win.logOnFlip("Set %s pos=%s" %(self.name, pos),
                 level=logging.EXP,obj=self)
    def _calcSizeRendered(self):
        """Calculate the size of the stimulus in coords of the :class:`~psychopy.visual.Window` (normalised or pixels)"""
        if self.units in ['norm','pix', 'height']: self._sizeRendered=self.size
        elif self.units in ['deg', 'degs']: self._sizeRendered=psychopy.misc.deg2pix(self.size, self.win.monitor)
        elif self.units=='cm': self._sizeRendered=psychopy.misc.cm2pix(self.size, self.win.monitor)
        else:
            logging.ERROR("Stimulus units should be 'height', 'norm', 'deg', 'cm' or 'pix', not '%s'" %self.units)
    def _calcPosRendered(self):
        """Calculate the pos of the stimulus in coords of the :class:`~psychopy.visual.Window` (normalised or pixels)"""
        if self.units in ['norm','pix', 'height']: self._posRendered=self.pos
        elif self.units in ['deg', 'degs']: self._posRendered=psychopy.misc.deg2pix(self.pos, self.win.monitor)
        elif self.units=='cm': self._posRendered=psychopy.misc.cm2pix(self.pos, self.win.monitor)
    def enable(self):
        """Enable the aperture so that it is used in future drawing operations

        NB. The Aperture is enabled by default, when created.

        """
        GL.glEnable(GL.GL_STENCIL_TEST)
        self.enabled=True#by default
        self.status=STARTED
    def disable(self):
        """Disable the Aperture. Any subsequent drawing operations will not be
        affected by the aperture until re-enabled.
        """
        GL.glDisable(GL.GL_STENCIL_TEST)
        self.enabled=False
        self.status=STOPPED
    def __del__(self):
        self.disable()
