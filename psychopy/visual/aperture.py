#!/usr/bin/env python2

'''Restrict a stimulus visibility area to a basic shape or list of vertices'''

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl

import psychopy  # so we can get the __path__
from psychopy import logging, core
import psychopy.event

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.monitorunittools import cm2pix, deg2pix, convertToPix
from psychopy.tools.attributetools import attributeSetter, setAttribute
from psychopy.visual.shape import ShapeStim
from psychopy.visual.basevisual import MinimalStim, ContainerMixin

import numpy
from numpy import cos, sin, radians

from psychopy.constants import STARTED, STOPPED


class Aperture(MinimalStim, ContainerMixin):
    """Restrict a stimulus visibility area to a basic shape or list of vertices.

    When enabled, any drawing commands will only operate on pixels within the
    Aperture. Once disabled, subsequent draw operations affect the whole screen
    as usual.

    If shape is 'square' or 'triangle' then that is what will be used (obviously)
    If shape is 'circle' or `None` then a polygon with nVerts will be used (120 for a rough circle)
    If shape is a list or numpy array (Nx2) then it will be used directly as the vertices to a :class:`~psychopy.visual.ShapeStim`

    See demos/stimuli/aperture.py for example usage

    :Author:
        2011, Yuri Spitsyn
        2011, Jon Peirce added units options, Jeremy Gray added shape & orientation
        2014, Jeremy Gray added .contains() option
    """
    def __init__(self, win, size=1, pos=(0,0), ori=0, nVert=120, shape='circle', units=None,
            name=None, autoLog=None):
        #what local vars are defined (these are the init params) for use by __repr__
        self._initParams = dir()
        self._initParams.remove('self')
        super(Aperture, self).__init__(name=name, autoLog=False)

        #set self params
        self.autoLog=False #set this False first and change after attribs are set
        self.win=win
        if not win.allowStencil:
            logging.error('Aperture has no effect in a window created without allowStencil=True')
            core.quit()
        self.__dict__['size'] = size
        self.__dict__['pos'] = pos
        self.__dict__['ori'] = ori
        
        #unit conversions
        if units!=None and len(units):
            self.units = units
        else:
            self.units = win.units

        # set vertices using shape, or default to a circle with nVerts edges
        if hasattr(shape, 'lower'):
            shape = shape.lower()
        if shape is None or shape == 'circle':
            # NB: pentagon etc point upwards by setting x,y to be y,x (sin,cos):
            vertices = [(0.5*sin(radians(theta)), 0.5*cos(radians(theta)))
                        for theta in numpy.linspace(0, 360, nVert, False)]
        elif shape == 'square':
            vertices = [[0.5,-0.5],[-0.5,-0.5],[-0.5,0.5],[0.5,0.5]]
        elif shape == 'triangle':
            vertices = [[0.5,-0.5],[0,0.5],[-0.5,-0.5]]
        elif type(shape) in [tuple, list, numpy.ndarray] and len(shape) > 2:
            vertices = shape
        else:
            logging.error("Unrecognized shape for aperture. Expected 'circle', 'square', 'triangle', vertices, or None; got %s" %(repr(shape)))
        self._shape = ShapeStim(win=self.win, vertices=vertices,
                                fillColor=1, lineColor=None,
                                interpolate=False, pos=pos, size=size,
                                autoLog=False)

        self.vertices = self._shape.vertices
        self._needVertexUpdate = True
        self._needReset = True  # Default when setting attributes
        self._reset()  #implicitly runs a self.enabled = True. Also sets self._needReset = True on every call
        
        # set autoLog now that params have been initialised
        self.__dict__['autoLog'] = autoLog or autoLog is None and self.win.autoLog
        if self.autoLog:
            logging.exp("Created %s = %s" %(self.name, str(self)))
    def _reset(self):
        """Internal method to rebuild the shape - shouldn't be called by the user.
        You have to explicitly turn resetting off by setting self._needReset = False"""
        if not self._needReset:
            self._needReset = True
        else:
            self.enabled = True  # attributeSetter, turns on.
            GL.glClearStencil(0)
            GL.glClear(GL.GL_STENCIL_BUFFER_BIT)
    
            GL.glPushMatrix()
            self.win.setScale('pix')
    
            GL.glDisable(GL.GL_LIGHTING)
            GL.glDisable(GL.GL_DEPTH_TEST)
            GL.glDepthMask(GL.GL_FALSE)
            GL.glStencilFunc(GL.GL_NEVER, 0, 0)
            GL.glStencilOp(GL.GL_INCR, GL.GL_INCR, GL.GL_INCR)
            self._shape.draw(keepMatrix=True) #draw without push/pop matrix
            GL.glStencilFunc(GL.GL_EQUAL, 1, 1)
            GL.glStencilOp(GL.GL_KEEP, GL.GL_KEEP, GL.GL_KEEP)
    
            GL.glPopMatrix()
    
    @attributeSetter
    def size(self, size):
        """Set the size (diameter) of the Aperture. 
        
        This essentially controls a :class:`.ShapeStim` so see documentation for ShapeStim.size.
        
        :ref:`Operations <attrib-operations>` supported here as well as ShapeStim.
        
        Use setSize() if you want to control 0logging and resetting."""
        self.__dict__['size'] = size
        self._shape.size = size  # a ShapeStim
        self._reset()
    def setSize(self, size, needReset=True, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        self._needReset = needReset
        setAttribute(self, 'size', size, log)
    @attributeSetter
    def ori(self, ori):
        """Set the orientation of the Aperture.
        
        This essentially controls a :class:`.ShapeStim` so see documentation for ShapeStim.ori.
        
        :ref:`Operations <attrib-operations>` supported here as well as ShapeStim.
        
        Use setOri() if you want to control logging and resetting."""
        self.__dict__['ori'] = ori
        self._shape.ori = ori  # a ShapeStim
        self._reset()
    def setOri(self, ori, needReset=True, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        self._needReset = needReset
        setAttribute(self, 'ori', ori, log)
    @attributeSetter
    def pos(self, pos):
        """Set the pos (centre) of the Aperture. :ref:`Operations <attrib-operations>` supported.
                
        This essentially controls a :class:`.ShapeStim` so see documentation for ShapeStim.pos.
        
        :ref:`Operations <attrib-operations>` supported here as well as ShapeStim.

        Use setPos() if you want to control logging and resetting.
        """
        self.__dict__['pos'] = numpy.array(pos)
        self._shape.pos = self.pos  # a ShapeStim
        self._reset()
    def setPos(self, pos, needReset=True, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        self._needReset = needReset
        setAttribute(self, 'pos', pos, log)
    @property
    def posPix(self):
        """The position of the aperture in pixels
        """
        return self._shape.posPix
    @property
    def sizePix(self):
        """The size of the aperture in pixels
        """
        return self._shape.sizePix
    @attributeSetter
    def enabled(self, value):
        """True / False. Enable or disable the aperture. 
        Determines whether it is used in future drawing operations.

        NB. The Aperture is enabled by default, when created.
        """
        if value:
            if self._shape._needVertexUpdate:
                self._shape._updateVertices()
            GL.glEnable(GL.GL_STENCIL_TEST)
            self.status = STARTED
        else:
            GL.glDisable(GL.GL_STENCIL_TEST)
            self.status = STOPPED
        
        self.__dict__['enabled'] = value
    def enable(self):
        """Use Aperture.enabled = True instead."""
        self.enabled = True
    def disable(self):
        """Use Aperture.enabled = False instead."""
        self.enabled = False
    def __del__(self):
        self.enabled = False
