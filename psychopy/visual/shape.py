#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Create geometric (vector) shapes by defining vertex locations."""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL)

from __future__ import absolute_import, print_function

from builtins import str
from past.builtins import basestring

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
from psychopy.tools.attributetools import (attributeSetter, logAttrib,
                                           setAttribute)
from psychopy.tools.arraytools import val2array
from psychopy.visual.basevisual import (BaseVisualStim, ColorMixin,
                                        ContainerMixin)
from psychopy.visual.helpers import setColor

from psychopy.contrib import tesselate
import copy
import numpy


knownShapes = {
    "cross" :  [
        (-0.1, +0.5), # up
        (+0.1, +0.5),
        (+0.1, +0.1),
        (+0.5, +0.1),  # right
        (+0.5, -0.1),
        (+0.1, -0.1),
        (+0.1, -0.5),  # down
        (-0.1, -0.5),
        (-0.1, -0.1),
        (-0.5, -0.1),  # left
        (-0.5, +0.1),
        (-0.1, +0.1),
    ],
    "star7" : [(0.0,0.5),(0.09,0.18),(0.39,0.31),(0.19,0.04),
             (0.49,-0.11),(0.16,-0.12),(0.22,-0.45),(0.0,-0.2),
             (-0.22,-0.45),(-0.16,-0.12),(-0.49,-0.11),(-0.19,0.04),
             (-0.39,0.31),(-0.09,0.18)]
}

class BaseShapeStim(BaseVisualStim, ColorMixin, ContainerMixin):
    """Create geometric (vector) shapes by defining vertex locations.

    Shapes can be outlines or filled, set lineColor and fillColor to
    a color name, or None. They can also be rotated (stim.setOri(__)),
    translated (stim.setPos(__)), and scaled (stim.setSize(__)) like
    any other stimulus.

    BaseShapeStim is currently used by ShapeStim and Aperture (for
    basic shapes). It is also retained in case backwards compatibility
    is needed.

    v1.84.00: ShapeStim became BaseShapeStim.
    """

    def __init__(self,
                 win,
                 units='',
                 lineWidth=1.5,
                 lineColor=(1.0, 1.0, 1.0),
                 lineColorSpace='rgb',
                 fillColor=None,
                 fillColorSpace='rgb',
                 vertices=((-0.5, 0), (0, +0.5), (+0.5, 0)),
                 closeShape=True,
                 pos=(0, 0),
                 size=1,
                 ori=0.0,
                 opacity=1.0,
                 contrast=1.0,
                 depth=0,
                 interpolate=True,
                 lineRGB=None,
                 fillRGB=None,
                 name=None,
                 autoLog=None,
                 autoDraw=False,
                 color=None,
                 colorSpace=None):
        """ """  # all doc is in the attributes
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')

        # Initialize inheritance and remove unwanted methods; autoLog is set
        # later
        super(BaseShapeStim, self).__init__(win, units=units,
                                            name=name, autoLog=False)

        self.contrast = float(contrast)
        self.opacity = float(opacity)
        self.pos = numpy.array(pos, float)
        self.closeShape = closeShape
        self.lineWidth = lineWidth
        self.interpolate = interpolate

        # Color stuff
        self.useShaders = False  # don't need to combine textures with colors
        # set color first but then potentially override
        self.__dict__['colorSpace'] = colorSpace
        self.__dict__['lineColorSpace'] = lineColorSpace
        self.__dict__['fillColorSpace'] = fillColorSpace

        if lineRGB is not None:
            logging.warning("Use of rgb arguments to stimuli are deprecated."
                            " Please use color and colorSpace args instead")
            self.setLineColor(lineRGB, colorSpace='rgb', log=None)
        elif color is not None and lineColor is None:
            pass  # user has set color but not lineColor. Don't override that
        else:
            self.setLineColor(lineColor, colorSpace=lineColorSpace, log=None)

        if fillRGB is not None:
            logging.warning("Use of rgb arguments to stimuli are deprecated."
                            " Please use color and colorSpace args instead")
            self.setFillColor(fillRGB, colorSpace='rgb', log=None)
        elif color is not None and fillColor is None:
            pass  # user has set color but not fillColor. Don't override that
        else:
            self.setFillColor(fillColor, colorSpace=fillColorSpace, log=None)

        # if the fillColor and lineColor are not set but color is
        # then the user probably wants color applied to both
        if (lineColor==(1.0, 1.0, 1.0) and fillColor is None
                and color is not None):
            self.color = color

        # Other stuff
        self.depth = depth
        self.ori = numpy.array(ori, float)
        self.size = numpy.array([0.0, 0.0]) + size  # make sure that it's 2D
        if vertices is not ():  # flag for when super-init'ing a ShapeStim
            self.vertices = vertices  # call attributeSetter
        self.autoDraw = autoDraw  # call attributeSetter

        # set autoLog now that params have been initialised
        wantLog = autoLog is None and self.win.autoLog
        self.__dict__['autoLog'] = autoLog or wantLog
        if self.autoLog:
            logging.exp("Created %s = %s" % (self.name, str(self)))

    @attributeSetter
    def lineWidth(self, value):
        """int or float
        specifying the line width in **pixels**

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['lineWidth'] = value

    def setLineWidth(self, value, operation='', log=None):
        setAttribute(self, 'lineWidth', value, log, operation)

    @attributeSetter
    def closeShape(self, value):
        """True or False
        Should the last vertex be automatically connected to the first?

        If you're using `Polygon`, `Circle` or `Rect`, closeShape=True is
        assumed and shouldn't be changed.
        """
        self.__dict__['closeShape'] = value

    @attributeSetter
    def interpolate(self, value):
        """True or False
        If True the edge of the line will be antialiased.
        """
        self.__dict__['interpolate'] = value

    @attributeSetter
    def color(self, color):
        self.fillColor = color
        self.lineColor = color

    @attributeSetter
    def fillColor(self, color):
        """Sets the color of the shape fill.

        See :meth:`psychopy.visual.GratingStim.color` for further details
        of how to use colors.

        Note that shapes where some vertices point inwards will usually not
        'fill' correctly.
        """
        setColor(self, color, rgbAttrib='fillRGB', colorAttrib='fillColor')

    @attributeSetter
    def lineColor(self, color):
        """Sets the color of the shape lines.

        See :meth:`psychopy.visual.GratingStim.color` for further details
        of how to use colors.
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

    def setColor(self, color, colorSpace=None, operation='', log=None):
        """Sets both the line and fill to be the same color
        """
        self.setLineColor(color, colorSpace, operation, log)
        self.setFillColor(color, colorSpace, operation, log)

    def setLineRGB(self, value, operation=''):
        """DEPRECATED since v1.60.05: Please use :meth:`~ShapeStim.lineColor`
        """
        self._set('lineRGB', value, operation)

    def setFillRGB(self, value, operation=''):
        """DEPRECATED since v1.60.05: Please use :meth:`~ShapeStim.fillColor`
        """
        self._set('fillRGB', value, operation)

    def setLineColor(self, color, colorSpace=None, operation='', log=None):
        """Sets the color of the shape edge.

        See :meth:`psychopy.visual.GratingStim.color` for further details.
        """
        setColor(self, color, colorSpace=colorSpace, operation=operation,
                 rgbAttrib='lineRGB',  # the name for this rgb value
                 colorAttrib='lineColor')  # the name for this color
        logAttrib(self, log, 'lineColor', value='%s (%s)' %
                  (self.lineColor, self.lineColorSpace))

    def setFillColor(self, color, colorSpace=None, operation='', log=None):
        """Sets the color of the shape fill.

        See :meth:`psychopy.visual.GratingStim.color` for further details.

        Note that shapes where some vertices point inwards will usually not
        'fill' correctly.
        """
        # run the original setColor, which creates color and
        setColor(self, color, colorSpace=colorSpace, operation=operation,
                 rgbAttrib='fillRGB',  # the name for this rgb value
                 colorAttrib='fillColor')  # the name for this color
        logAttrib(self, log, 'fillColor', value='%s (%s)' %
                  (self.fillColor, self.fillColorSpace))

    @attributeSetter
    def size(self, value):
        """Int/Float or :ref:`x,y-pair <attrib-xy>`.
        Sets the size of the shape.
        Size is independent of the units of shape and will simply scale
        the shape's vertices by the factor given.
        Use a tuple or list of two values to scale asymmetrically.

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['size'] = numpy.array(value, float)
        self._needVertexUpdate = True

    def setSize(self, value, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'size', value, log,
                     operation)  # calls attributeSetter

    @attributeSetter
    def vertices(self, value):
        """A list of lists or a numpy array (Nx2) specifying xy positions of
        each vertex, relative to the center of the field.

        If you're using `Polygon`, `Circle` or `Rect`, this shouldn't be used.

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['vertices'] = numpy.array(value, float)

        # Check shape
        if not (self.vertices.shape == (2,) or
                (len(self.vertices.shape) == 2 and
                 self.vertices.shape[1] == 2)):
            raise ValueError("New value for setXYs should be 2x1 or Nx2")
        self._needVertexUpdate = True

    def setVertices(self, value=None, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'vertices', value, log, operation)

    def draw(self, win=None, keepMatrix=False):
        """Draw the stimulus in its relevant window.

        You must call this method after every MyWin.flip() if you want the
        stimulus to appear on that frame and then update the screen again.
        """
        # The keepMatrix option is needed by Aperture
        if win is None:
            win = self.win
        self._selectWindow(win)

        if win._haveShaders:
            _prog = self.win._progSignedFrag
            GL.glUseProgram(_prog)
        # will check if it needs updating (check just once)
        vertsPix = self.verticesPix
        nVerts = vertsPix.shape[0]
        # scale the drawing frame etc...
        if not keepMatrix:
            GL.glPushMatrix()  # push before drawing, pop after
            win.setScale('pix')
        # load Null textures into multitexteureARB - or they modulate glColor
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
        # .data_as(ctypes.POINTER(ctypes.c_float)))
        GL.glVertexPointer(2, GL.GL_DOUBLE, 0, vertsPix.ctypes)

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        if nVerts > 2:  # draw a filled polygon first
            if self.fillRGB is not None:
                # convert according to colorSpace
                fillRGB = self._getDesiredRGB(
                    self.fillRGB, self.fillColorSpace, self.contrast)
                # then draw
                GL.glColor4f(fillRGB[0], fillRGB[1], fillRGB[2], self.opacity)
                GL.glDrawArrays(GL.GL_POLYGON, 0, nVerts)
        if self.lineRGB is not None and self.lineWidth != 0.0:
            lineRGB = self._getDesiredRGB(
                self.lineRGB, self.lineColorSpace, self.contrast)
            # then draw
            GL.glLineWidth(self.lineWidth)
            GL.glColor4f(lineRGB[0], lineRGB[1], lineRGB[2], self.opacity)
            if self.closeShape:
                GL.glDrawArrays(GL.GL_LINE_LOOP, 0, nVerts)
            else:
                GL.glDrawArrays(GL.GL_LINE_STRIP, 0, nVerts)
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        if win._haveShaders:
            GL.glUseProgram(0)
        if not keepMatrix:
            GL.glPopMatrix()


class ShapeStim(BaseShapeStim):
    """A class for arbitrary shapes defined as lists of vertices (x,y).

    Shapes can be lines, polygons (concave, convex, self-crossing), or have
    holes or multiple regions.

    `vertices` is typically a list of points (x,y). By default, these are
    assumed to define a closed figure (polygon); set `closeShape=False` for
    a line. `closeShape` cannot be changed dynamically, but individual
    vertices can be changed on a frame-by-frame basis. The stimulus as a
    whole can be rotated, translated, or scaled dynamically
    (using .ori, .pos, .size).

    Vertices can be a string, giving the name of a known set of vertices,
    although "cross" is the only named shape available at present.

    Advanced shapes: `vertices` can also be a list of loops, where each loop
    is a list of points (x,y), e.g., to define a shape with a hole. Borders
    and contains() are not supported for multi-loop stimuli.

    `windingRule` is an advanced feature to allow control over the GLU
    tessellator winding rule (default: GLU_TESS_WINDING_ODD). This is relevant
    only for self-crossing or multi-loop shapes. Cannot be set dynamically.

    See Coder demo > stimuli > shapes.py

    Changed Nov 2015: v1.84.00. Now allows filling of complex shapes. This
    is almost completely backwards compatible (see changelog). The
    old version is accessible as `psychopy.visual.BaseShapeStim`.
    """

    # Author: Jeremy Gray, November 2015, using psychopy.contrib.tesselate

    def __init__(self,
                 win,
                 units='',
                 lineWidth=1.5,
                 lineColor='white',
                 lineColorSpace='rgb',
                 fillColor=None,
                 fillColorSpace='rgb',
                 vertices=((-0.5, 0), (0, +0.5), (+0.5, 0)),
                 windingRule=None,  # default GL.GLU_TESS_WINDING_ODD
                 closeShape=True,  # False for a line
                 pos=(0, 0),
                 size=1,
                 ori=0.0,
                 opacity=1.0,
                 contrast=1.0,
                 depth=0,
                 interpolate=True,
                 name=None,
                 autoLog=None,
                 autoDraw=False):
        """
        """
        # what local vars are defined (init params, for use by __repr__)
        self._initParamsOrig = dir()
        self._initParamsOrig.remove('self')

        super(ShapeStim, self).__init__(win,
                                        units=units,
                                        lineWidth=lineWidth,
                                        lineColor=lineColor,
                                        lineColorSpace=lineColorSpace,
                                        fillColor=fillColor,
                                        fillColorSpace=fillColorSpace,
                                        vertices=(),  # dummy verts
                                        closeShape=self.closeShape,
                                        pos=pos,
                                        size=size,
                                        ori=ori,
                                        opacity=opacity,
                                        contrast=contrast,
                                        depth=depth,
                                        interpolate=interpolate,
                                        name=name,
                                        autoLog=False,
                                        autoDraw=autoDraw)

        self.closeShape = closeShape
        self.windingRule = windingRule
        self.vertices = vertices

        # remove deprecated params (from ShapeStim.__init__):
        self._initParams = self._initParamsOrig

        # set autoLog now that params have been initialised
        wantLog = autoLog or autoLog is None and self.win.autoLog
        self.__dict__['autoLog'] = wantLog
        if self.autoLog:
            logging.exp("Created %s = %s" % (self.name, str(self)))

    def _tesselate(self, newVertices):
        """Set the .vertices and .border to new values, invoking tessellation.
        """
        # TO-DO: handle borders properly for multiloop stim like holes
        # likely requires changes in ContainerMixin to iterate over each
        # border loop

        self.border = copy.deepcopy(newVertices)
        if self.closeShape:
            # convert original vertices to triangles (= tesselation) if
            # possible. (not possible if closeShape is False, don't even try)
            GL.glPushMatrix()  # seemed to help at one point, superfluous?
            if self.windingRule:
                GL.gluTessProperty(tesselate.tess, GL.GLU_TESS_WINDING_RULE,
                                   self.windingRule)
            if hasattr(newVertices[0][0], '__iter__'):
                loops = newVertices
            else:
                loops = [newVertices]
            tessVertices = tesselate.tesselate(loops)
            GL.glPopMatrix()
            if self.windingRule:
                GL.gluTessProperty(tesselate.tess, GL.GLU_TESS_WINDING_RULE,
                                   tesselate.default_winding_rule)

        if not self.closeShape or tessVertices == []:
            # probably got a line if tesselate returned []
            initVertices = newVertices
            self.closeShape = False
        elif len(tessVertices) % 3:
            raise tesselate.TesselateError("Could not properly tesselate")
        else:
            initVertices = tessVertices
        self.__dict__['_tesselVertices'] = numpy.array(initVertices, float)

    @attributeSetter
    def vertices(self, newVerts):
        """A list of lists or a numpy array (Nx2) specifying xy positions of
        each vertex, relative to the center of the field.

        Assigning to vertices can be slow if there are many vertices.

        :ref:`Operations <attrib-operations>` supported with `.setVertices()`.
        """
        # check if this is a name of one of our known shapes
        if isinstance(newVerts, basestring) and newVerts in knownShapes:
            newVerts = knownShapes[newVerts]

        # Check shape
        self.__dict__['vertices'] = val2array(newVerts, withNone=True,
                                              withScalar=True, length=2)
        self._needVertexUpdate = True
        self._tesselate(self.vertices)

    @property
    def verticesPix(self):
        """This determines the coordinates of the vertices for the
        current stimulus in pixels, accounting for size, ori, pos and units
        """
        # because this is a property getter we can check /on-access/ if it
        # needs updating :-)
        if self._needVertexUpdate:
            self._updateVertices()
        return self.__dict__['verticesPix']

    def draw(self, win=None, keepMatrix=False):
        """Draw the stimulus in the relevant window. You must call this method
        after every win.flip() if you want the stimulus to appear on that
        frame and then update the screen again.
        """
        # mostly copied from BaseShapeStim. Uses GL_TRIANGLES and depends on
        # two arrays of vertices: tesselated (for fill) & original (for
        # border) keepMatrix is needed by Aperture, although Aperture
        # currently relies on BaseShapeStim instead

        if win is None:
            win = self.win
        self._selectWindow(win)

        # scale the drawing frame etc...
        if not keepMatrix:
            GL.glPushMatrix()
            win.setScale('pix')

        # setup the shaderprogram
        if win._haveShaders:
            _prog = self.win._progSignedFrag
            GL.glUseProgram(_prog)

        # load Null textures into multitexteureARB - or they modulate glColor
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
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)

        # fill interior triangles if there are any
        if (self.closeShape and
                self.verticesPix.shape[0] > 2 and
                self.fillRGB is not None):
            GL.glVertexPointer(2, GL.GL_DOUBLE, 0, self.verticesPix.ctypes)
            fillRGB = self._getDesiredRGB(self.fillRGB, self.fillColorSpace,
                                          self.contrast)
            GL.glColor4f(fillRGB[0], fillRGB[1], fillRGB[2], self.opacity)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, self.verticesPix.shape[0])

        # draw the border (= a line connecting the non-tesselated vertices)
        if self.lineRGB is not None and self.lineWidth:
            GL.glVertexPointer(2, GL.GL_DOUBLE, 0, self._borderPix.ctypes)
            lineRGB = self._getDesiredRGB(self.lineRGB, self.lineColorSpace,
                                          self.contrast)
            GL.glLineWidth(self.lineWidth)
            GL.glColor4f(lineRGB[0], lineRGB[1], lineRGB[2], self.opacity)
            if self.closeShape:
                gl_line = GL.GL_LINE_LOOP
            else:
                gl_line = GL.GL_LINE_STRIP
            GL.glDrawArrays(gl_line, 0, self._borderPix.shape[0])

        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        if win._haveShaders:
            GL.glUseProgram(0)
        if not keepMatrix:
            GL.glPopMatrix()
