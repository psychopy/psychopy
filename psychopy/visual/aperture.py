#!/usr/bin/env python

'''Restrict a stimulus visibility area to a basic shape
(circle, square, triangle)'''

# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl

import psychopy  # so we can get the __path__
from psychopy import logging
import psychopy.event

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.monitorunittools import cm2pix, deg2pix

import numpy

from psychopy.constants import STARTED, STOPPED


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
        elif self.units in ['deg', 'degs']: self._sizeRendered=deg2pix(self.size, self.win.monitor)
        elif self.units=='cm': self._sizeRendered=cm2pix(self.size, self.win.monitor)
        else:
            logging.ERROR("Stimulus units should be 'height', 'norm', 'deg', 'cm' or 'pix', not '%s'" %self.units)
    def _calcPosRendered(self):
        """Calculate the pos of the stimulus in coords of the :class:`~psychopy.visual.Window` (normalised or pixels)"""
        if self.units in ['norm','pix', 'height']: self._posRendered=self.pos
        elif self.units in ['deg', 'degs']: self._posRendered=deg2pix(self.pos, self.win.monitor)
        elif self.units=='cm': self._posRendered=cm2pix(self.pos, self.win.monitor)
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
