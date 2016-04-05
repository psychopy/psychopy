#!/usr/bin/env python2

'''Create geometric (vector) shapes by defining vertex locations.'''

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL)

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl

import psychopy  # so we can get the __path__
from psychopy import logging

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.monitorunittools import cm2pix, deg2pix
from psychopy.tools.attributetools import attributeSetter, setWithOperation, logAttrib
from psychopy.visual.basevisual import BaseVisualStim
from psychopy.visual.basevisual import ColorMixin, ContainerMixin
from psychopy.visual.helpers import setColor

import numpy


class ShapeStim(BaseVisualStim, ColorMixin, ContainerMixin):
    """Create geometric (vector) shapes by defining vertex locations.

    Shapes can be outlines or filled, by setting lineRGB and fillRGB to
    rgb triplets, or None. They can also be rotated (stim.setOri(__)) and
    translated (stim.setPos(__)) like any other stimulus.

    NB for now the fill of objects is performed using glBegin(GL_POLYGON)
    and that is limited to convex shapes. With concavities you get unpredictable
    results (e.g. add a fill color to the arrow stim below). To create concavities,
    you can combine multiple shapes, or stick to just outlines. (If anyone wants
    to rewrite ShapeStim to use glu tesselators that would be great!)
    """
    def __init__(self,
                 win,
                 units  ='',
                 lineWidth=1.0,
                 lineColor=(1.0,1.0,1.0),
                 lineColorSpace='rgb',
                 fillColor=None,
                 fillColorSpace='rgb',
                 vertices=((-0.5,0),(0,+0.5),(+0.5,0)),
                 closeShape=True,
                 pos= (0,0),
                 size=1,
                 ori=0.0,
                 opacity=1.0,
                 contrast=1.0,
                 depth  =0,
                 interpolate=True,
                 lineRGB=None,
                 fillRGB=None,
                 name='', autoLog=True):
        """
        :Parameters:

            lineWidth : int (or float?)
                specifying the line width in **pixels**

            vertices : a list of lists or a numpy array (Nx2)
                specifying xy positions of each vertex

            closeShape : True or False
                Do you want the last vertex to be automatically connected to the first?

            interpolate : True or False
                If True the edge of the line will be antialiased.
                """
        #what local vars are defined (these are the init params) for use by __repr__
        self._initParams = dir()
        self._initParams.remove('self')

        # Initialize inheritance and remove unwanted methods
        super(ShapeStim, self).__init__(win, units=units, name=name, autoLog=False) #autoLog is set later
        self.__dict__['setColor'] = None
        self.__dict__['color'] = None
        self.__dict__['colorSpace'] = None

        self.contrast = float(contrast)
        self.opacity = float(opacity)
        self.pos = numpy.array(pos, float)
        self.closeShape=closeShape
        self.lineWidth=lineWidth
        self.interpolate=interpolate

        # Color stuff
        self.useShaders=False#since we don't ned to combine textures with colors
        self.__dict__['lineColorSpace'] = lineColorSpace
        self.__dict__['fillColorSpace'] = fillColorSpace

        if lineRGB!=None:
            logging.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setLineColor(lineRGB, colorSpace='rgb')
        else:
            self.setLineColor(lineColor, colorSpace=lineColorSpace)

        if fillRGB!=None:
            logging.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setFillColor(fillRGB, colorSpace='rgb')
        else:
            self.setFillColor(fillColor, colorSpace=fillColorSpace)

        # Other stuff
        self.depth=depth
        self.ori = numpy.array(ori,float)
        self.size = numpy.array([0.0,0.0])
        self.setSize(size, log=False)
        self.setVertices(vertices, log=False)

        #set autoLog (now that params have been initialised)
        self.autoLog= autoLog
        if autoLog:
            logging.exp("Created %s = %s" %(self.name, str(self)))

    @attributeSetter
    def fillColor(self, color):
        """
        Sets the color of the shape fill. See :meth:`psychopy.visual.GratingStim.color`
        for further details of how to use colors.

        Note that shapes where some vertices point inwards will usually not
        'fill' correctly.
        """
        setColor(self, color, rgbAttrib='fillRGB', colorAttrib='fillColor')

    @attributeSetter
    def lineColor(self, color):
        """
        Sets the color of the shape lines. See :meth:`psychopy.visual.GratingStim.color`
        for further details of how to use colors.
        """
        setColor(self, color, rgbAttrib='lineRGB', colorAttrib='lineColor')

    @attributeSetter
    def fillColorSpace(self, value):
        """
        Sets color space for fill color. See documentation for fillColorSpace
        """
        self.__dict__['fillColorSpace'] = value

    @attributeSetter
    def lineColorSpace(self, value):
        """
        Sets color space for line color. See documentation for lineColorSpace
        """
        self.__dict__['lineColorSpace'] = value

    def setColor(self, color, colorSpace=None, operation=''):
        """For ShapeStim use :meth:`~ShapeStim.lineColor` or
        :meth:`~ShapeStim.fillColor`
        """
        raise AttributeError, 'ShapeStim does not support setColor method. Please use setFillColor or setLineColor instead'
    def setLineRGB(self, value, operation=''):
        """DEPRECATED since v1.60.05: Please use :meth:`~ShapeStim.setLineColor`
        """
        self._set('lineRGB', value, operation)
    def setFillRGB(self, value, operation=''):
        """DEPRECATED since v1.60.05: Please use :meth:`~ShapeStim.setFillColor`
        """
        self._set('fillRGB', value, operation)
    def setLineColor(self, color, colorSpace=None, operation='', log=True):
        """Sets the color of the shape edge. See :meth:`psychopy.visual.GratingStim.color`
        for further details of how to use this function.
        """
        setColor(self,color, colorSpace=colorSpace, operation=operation,
                    rgbAttrib='lineRGB',#the name for this rgb value
                    colorAttrib='lineColor',#the name for this color
                    log=log)
    def setFillColor(self, color, colorSpace=None, operation='', log=True):
        """Sets the color of the shape fill. See :meth:`psychopy.visual.GratingStim.color`
        for further details of how to use this function.

        Note that shapes where some vertices point inwards will usually not
        'fill' correctly.
        """
        #run the original setColor, which creates color and
        setColor(self,color, colorSpace=colorSpace, operation=operation,
                    rgbAttrib='fillRGB',#the name for this rgb value
                    colorAttrib='fillColor',#the name for this color
                    log=log)
    def setSize(self, value, operation='', log=True):
        """ Sets the size of the shape.
        Size is independent of the units of shape and will simply scale the shape's vertices by the factor given.
        Use a tuple or list of two values to scale asymmetrically.
        """
        self._set('size', numpy.asarray(value), operation, log=log)
        self._needVertexUpdate=True

    def setVertices(self,value=None, operation='', log=True):
        """Set the xy values of the vertices (relative to the centre of the field).
        Values should be:

            - an array/list of Nx2 coordinates.

        """
        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)
        #check shape
        if not (value.shape==(2,) \
            or (len(value.shape)==2 and value.shape[1]==2)
            ):
                raise ValueError("New value for setXYs should be 2x1 or Nx2")
        #set value and log
        setWithOperation(self, 'vertices', value, operation)
        logAttrib(self, log, 'vertices', value)
        self._needVertexUpdate=True

    def draw(self, win=None, keepMatrix=False): #keepMatrix option is needed by Aperture
        """
        Draw the stimulus in its relevant window. You must call
        this method after every MyWin.flip() if you want the
        stimulus to appear on that frame and then update the screen
        again.
        """
        if win==None: win=self.win
        self._selectWindow(win)

        vertsPix = self.verticesPix #will check if it needs updating (check just once)
        nVerts = vertsPix.shape[0]
        #scale the drawing frame etc...
        if not keepMatrix:
            GL.glPushMatrix()#push before drawing, pop after
            win.setScale('pix')
        #load Null textures into multitexteureARB - or they modulate glColor
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        if self.interpolate:
            GL.glEnable(GL.GL_LINE_SMOOTH)
            GL.glEnable(GL.GL_MULTISAMPLE)
        else:
            GL.glDisable(GL.GL_LINE_SMOOTH)
            GL.glDisable(GL.GL_MULTISAMPLE)
        GL.glVertexPointer(2, GL.GL_DOUBLE, 0, vertsPix.ctypes)#.data_as(ctypes.POINTER(ctypes.c_float)))

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        if nVerts>2: #draw a filled polygon first
            if self.fillRGB!=None:
                #convert according to colorSpace
                fillRGB = self._getDesiredRGB(self.fillRGB, self.fillColorSpace, self.contrast)
                #then draw
                GL.glColor4f(fillRGB[0], fillRGB[1], fillRGB[2], self.opacity)
                GL.glDrawArrays(GL.GL_POLYGON, 0, nVerts)
        if self.lineRGB!=None:
            lineRGB = self._getDesiredRGB(self.lineRGB, self.lineColorSpace, self.contrast)
            #then draw
            GL.glLineWidth(self.lineWidth)
            GL.glColor4f(lineRGB[0], lineRGB[1], lineRGB[2], self.opacity)
            if self.closeShape: GL.glDrawArrays(GL.GL_LINE_LOOP, 0, nVerts)
            else: GL.glDrawArrays(GL.GL_LINE_STRIP, 0, nVerts)
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        if not keepMatrix:
            GL.glPopMatrix()
