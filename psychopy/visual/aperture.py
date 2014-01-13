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
from psychopy.tools.monitorunittools import cm2pix, deg2pix, convertToPix

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
        #what local vars are defined (these are the init params) for use by __repr__
        self._initParams = dir()
        self._initParams.remove('self')
        #set self params
        self.autoLog=False #set this False first and change after attribs are set
        self.win=win
        self.name = name

        #unit conversions
        if units!=None and len(units):
            self.units = units
        else:
            self.units = win.units

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
        self.autoLog= autoLog
        if autoLog:
            logging.exp("Created %s = %s" %(self.name, repr(self)))
    def _reset(self):
        self.enable()
        GL.glClearStencil(0)
        GL.glClear(GL.GL_STENCIL_BUFFER_BIT)

        GL.glPushMatrix()
        self.win.setScale('pix')
        GL.glTranslatef(self.posPix[0], self.posPix[1], 0)
        GL.glRotatef(-self.ori, 0.0, 0.0, 1.0)

        GL.glDisable(GL.GL_LIGHTING)
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDepthMask(GL.GL_FALSE)
        GL.glStencilFunc(GL.GL_NEVER, 0, 0)
        GL.glStencilOp(GL.GL_INCR, GL.GL_INCR, GL.GL_INCR)
        GL.glColor3f(0,0,0)
        GL.gluDisk(self.quad, 0, self.sizePix/2.0, self.nVert, 2)
        GL.glStencilFunc(GL.GL_EQUAL, 1, 1)
        GL.glStencilOp(GL.GL_KEEP, GL.GL_KEEP, GL.GL_KEEP)

        GL.glPopMatrix()

    def setSize(self, size, needReset=True, log=True):
        """Set the size (diameter) of the Aperture
        """
        self.size = size
        self._needVertexUpdate=True
        if needReset:
            self._reset()
        if log and self.autoLog:
             self.win.logOnFlip("Set %s size=%s" %(self.name, size),
                 level=logging.EXP,obj=self)
    def setOri(self, ori, needReset=True, log=True):
        """Set the orientation of the Aperture
        """
        self.ori = ori
        if needReset:
            self._reset()
        if log and self.autoLog:
             self.win.logOnFlip("Set %s ori=%s" %(self.name, ori),
                 level=logging.EXP,obj=self)
    def setPos(self, pos, needReset=True, log=True):
        """Set the pos (centre) of the Aperture
        """
        self.pos = numpy.array(pos)
        self._needVertexUpdate=True
        if needReset:
            self._reset()
        if log and self.autoLog:
             self.win.logOnFlip("Set %s pos=%s" %(self.name, pos),
                 level=logging.EXP,obj=self)
    def _updateVertices(self):
        """
        """
        #then combine with position and convert to pix
        pos = convertToPix(stim=self, vertices = [0,0], pos = self.pos)
        size = convertToPix(stim=self, vertices = self.size, pos = 0)
        try:
            size=size[0]
        except:
            pass
        #assign to self attrbute
        self.__dict__['posPix'] = pos
        self.__dict__['sizePix'] = size
        self._needVertexUpdate = False
    @property
    def posPix(self):
        """This determines the centre of the aperture in in pixels using pos and units
        """
        #because this is a property getter we can check /on-access/ if it needs updating :-)
        if self._needVertexUpdate:
            self._updateVertices()
        return self.__dict__['posPix']
    @property
    def sizePix(self):
        """This determines the size of the aperture in in pixels using size and units
        """
        #because this is a property getter we can check /on-access/ if it needs updating :-)
        if self._needVertexUpdate:
            self._updateVertices()
        return self.__dict__['sizePix']
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
