#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Create geometric (vector) shapes by defining vertex locations."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL)

import copy
import numpy

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet

import psychopy  # so we can get the __path__
from psychopy import logging
from psychopy.colors import Color

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
# from psychopy.tools.monitorunittools import cm2pix, deg2pix
from psychopy.tools.attributetools import (attributeSetter,  # logAttrib,
                                           setAttribute)
from psychopy.tools.arraytools import val2array
from psychopy.visual.basevisual import (
    BaseVisualStim, DraggingMixin, ColorMixin, ContainerMixin, WindowMixin
)
# from psychopy.visual.helpers import setColor
import psychopy.visual
from psychopy.contrib import tesselate

pyglet.options['debug_gl'] = False
GL = pyglet.gl


knownShapes = {
    "triangle": [
        (+0.0, 0.5),  # Point
        (-0.5, -0.5),  # Bottom left
        (+0.5, -0.5),  # Bottom right
    ],
    "rectangle": [
        [-.5,  .5],  # Top left
        [ .5,  .5],  # Top right
        [ .5, -.5],  # Bottom left
        [-.5, -.5],  # Bottom right
    ],
    "circle": "circle",  # Placeholder, value calculated on set based on line width
    "cross": [
        (-0.1, +0.5),  # up
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
    "star7": [
        (0.0, 0.5),
        (0.09, 0.18),
        (0.39, 0.31),
        (0.19, 0.04),
        (0.49, -0.11),
        (0.16, -0.12),
        (0.22, -0.45),
        (0.0, -0.2),
        (-0.22, -0.45),
        (-0.16, -0.12),
        (-0.49, -0.11),
        (-0.19, 0.04),
        (-0.39, 0.31),
        (-0.09, 0.18)
    ],
    "arrow": [
        (0.0, 0.5),
        (-0.5, 0.0),
        (-1/6, 0.0),
        (-1/6, -0.5),
        (1/6, -0.5),
        (1/6, 0.0),
        (0.5, 0.0)
    ],
}
knownShapes['square'] = knownShapes['rectangle']
knownShapes['star'] = knownShapes['star7']


class BaseShapeStim(BaseVisualStim, DraggingMixin, ColorMixin, ContainerMixin):
    """Create geometric (vector) shapes by defining vertex locations.
    This is a lazy-imported class, therefore import using full path 
    `from psychopy.visual.shape import BaseShapeStim` when inheriting
    from it.
    

    Shapes can be outlines or filled, set lineColor and fillColor to
    a color name, or None. They can also be rotated (stim.setOri(__)),
    translated (stim.setPos(__)), and scaled (stim.setSize(__)) like
    any other stimulus.

    BaseShapeStim is currently used by ShapeStim and Aperture (for
    basic shapes). It is also retained in case backwards compatibility
    is needed.

    v1.84.00: ShapeStim became BaseShapeStim.

    """

    _defaultFillColor = None
    _defaultLineColor = "black"

    def __init__(self,
                 win,
                 units='',
                 lineWidth=1.5,
                 lineColor=False, # uses False in place of None to distinguish between "not set" and "transparent"
                 fillColor=False, # uses False in place of None to distinguish between "not set" and "transparent"
                 colorSpace='rgb',
                 vertices=((-0.5, 0), (0, +0.5), (+0.5, 0)),
                 closeShape=True,
                 pos=(0, 0),
                 size=1,
                 anchor=None,
                 ori=0.0,
                 opacity=None,
                 contrast=1.0,
                 depth=0,
                 interpolate=True,
                 draggable=False,
                 name=None,
                 autoLog=None,
                 autoDraw=False,
                 # legacy
                 color=False,
                 lineRGB=False,
                 fillRGB=False,
                 fillColorSpace=None,
                 lineColorSpace=None
                 ):
        """ """  # all doc is in the attributes
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')

        # Initialize inheritance and remove unwanted methods; autoLog is set
        # later
        super(BaseShapeStim, self).__init__(win, units=units, name=name,
                                            autoLog=False)
        self.draggable = draggable

        self.pos = pos
        self.closeShape = closeShape
        self.lineWidth = lineWidth
        self.interpolate = interpolate

        # Appearance
        self.colorSpace = colorSpace
        if fillColor is not False:
            self.fillColor = fillColor
        elif color is not False:
            # Override fillColor with color if not set
            self.fillColor = color
        else:
            # Default to None if neither are set
            self.fillColor = self._defaultFillColor
        if lineColor is not False:
            self.lineColor = lineColor
        elif color is not False:
            # Override lineColor with color if not set
            self.lineColor = color
        else:
            # Default to black if neither are set
            self.lineColor = self._defaultLineColor
        if lineRGB is not False:
            # Override with RGB if set
            logging.warning("Use of rgb arguments to stimuli are deprecated."
                            " Please use color and colorSpace args instead")
            self.setLineColor(lineRGB, colorSpace='rgb', log=None)
        if fillRGB is not False:
            # Override with RGB if set
            logging.warning("Use of rgb arguments to stimuli are deprecated."
                            " Please use color and colorSpace args instead")
            self.setFillColor(fillRGB, colorSpace='rgb', log=None)
        self.contrast = contrast
        if opacity is not None:
            self.opacity = opacity

        # Other stuff
        self.depth = depth
        self.ori = numpy.array(ori, float)
        self.size = size  # make sure that it's 2D
        self.vertices = vertices  # call attributeSetter
        self.anchor = anchor
        self.autoDraw = autoDraw  # call attributeSetter

        # set autoLog now that params have been initialised
        wantLog = autoLog is None and self.win.autoLog
        self.__dict__['autoLog'] = autoLog or wantLog
        if self.autoLog:
            logging.exp("Created %s = %s" % (self.name, str(self)))

    @attributeSetter
    def lineWidth(self, value):
        """Width of the line in **pixels**.

        :ref:`Operations <attrib-operations>` supported.
        """
        # Enforce float
        if not isinstance(value, (float, int)):
            value = float(value)

        if isinstance(self, psychopy.visual.Line):
            if value > 127:
                logging.warning("lineWidth is greater than max width supported by OpenGL. For lines thicker than 127px, please use a filled Rect instead.")
        self.__dict__['lineWidth'] = value

    def setLineWidth(self, value, operation='', log=None):
        setAttribute(self, 'lineWidth', value, log, operation)

    @attributeSetter
    def closeShape(self, value):
        """Should the last vertex be automatically connected to the first?

        If you're using `Polygon`, `Circle` or `Rect`, `closeShape=True` is
        assumed and shouldn't be changed.
        """
        self.__dict__['closeShape'] = value

    @attributeSetter
    def interpolate(self, value):
        """If `True` the edge of the line will be anti-aliased.
        """
        self.__dict__['interpolate'] = value

    @attributeSetter
    def color(self, color):
        """Set the color of the shape. Sets both `fillColor` and `lineColor`
        simultaneously if applicable.
        """
        ColorMixin.foreColor.fset(self, color)
        self.fillColor = color
        self.lineColor = color
        return ColorMixin.foreColor.fget(self)

    #---legacy functions---

    def setColor(self, color, colorSpace=None, operation='', log=None):
        """Sets both the line and fill to be the same color.
        """
        ColorMixin.setForeColor(self, color, colorSpace, operation, log)
        self.setLineColor(color, colorSpace, operation, log)
        self.setFillColor(color, colorSpace, operation, log)

    @property
    def vertices(self):
        return BaseVisualStim.vertices.fget(self)

    @vertices.setter
    def vertices(self, value):
        if value is None:
            value = "rectangle"
        # check if this is a name of one of our known shapes
        if isinstance(value, str) and value in knownShapes:
            value = knownShapes[value]
            if value == "circle":
                # If circle is requested, calculate how many points are needed for the gap between line rects to be < 1px
                value = self._calculateMinEdges(self.lineWidth, threshold=5)
        if isinstance(value, int):
            value = self._calcEquilateralVertices(value)
        # Check shape
        WindowMixin.vertices.fset(self, value)
        self._needVertexUpdate = True

    def setVertices(self, value=None, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'vertices', value, log, operation)

    @staticmethod
    def _calcEquilateralVertices(edges, radius=0.5):
        """
        Get vertices for an equilateral shape with a given number of sides, will assume radius is 0.5 (relative) but
        can be manually specified
        """
        d = numpy.pi * 2 / edges
        vertices = numpy.asarray(
            [numpy.asarray((numpy.sin(e * d), numpy.cos(e * d))) * radius
             for e in range(int(round(edges)))])
        return vertices

    @staticmethod
    def _calculateMinEdges(lineWidth, threshold=180):
        """
        Calculate how many points are needed in an equilateral polygon for the gap between line rects to be < 1px and
        for corner angles to exceed a threshold.

        In other words, how many edges does a polygon need to have to appear smooth?

        lineWidth : int, float, np.ndarray
            Width of the line in pixels

        threshold : int
            Maximum angle (degrees) for corners of the polygon, useful for drawing a circle. Supply 180 for no maximum
            angle.
        """
        # sin(theta) = opp / hyp, we want opp to be 1/8 (meaning gap between rects is 1/4px, 1/2px in retina)
        opp = 1/8
        hyp = lineWidth / 2
        thetaR = numpy.arcsin(opp / hyp)
        theta = numpy.degrees(thetaR)
        # If theta is below threshold, use threshold instead
        theta = min(theta, threshold / 2)
        # Angles in a shape add up to 360, so theta is 360/2n, solve for n
        return int((360 / theta) / 2)

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
            if self._fillColor != None:
                # then draw
                GL.glColor4f(*self._fillColor.render('rgba1'))
                GL.glDrawArrays(GL.GL_POLYGON, 0, nVerts)
        if self._borderColor != None and self.lineWidth != 0.0:
            # then draw
            GL.glLineWidth(self.lineWidth)
            GL.glColor4f(*self._borderColor.render('rgba1'))
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
    This is a lazy-imported class, therefore import using full path 
    `from psychopy.visual.shape import ShapeStim` when inheriting
    from it.

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

    Parameters
    ----------
    win : :class:`~psychopy.visual.Window`
        Window this shape is being drawn to. The stimulus instance will
        allocate its required resources using that Windows context. In many
        cases, a stimulus instance cannot be drawn on different windows
        unless those windows share the same OpenGL context, which permits
        resources to be shared between them.
    units : str
        Units to use when drawing. This will affect how parameters and
        attributes `pos`, `size` and `radius` are interpreted.
    colorSpace : str
        Sets the colorspace, changing how values passed to `lineColor` and
        `fillColor` are interpreted.
    lineWidth : float
        Width of the shape outline.
    lineColor, fillColor : array_like, str, :class:`~psychopy.colors.Color` or None
        Color of the shape outline and fill. If `None`, a fully
        transparent color is used which makes the fill or outline invisible.
    vertices : array_like
        Nx2 array of points (eg., `[[-0.5, 0], [0, 0.5], [0.5, 0]`).
    windingRule : :class:`~pyglet.gl.GLenum` or None
        Winding rule to use for tesselation, default is
        `GLU_TESS_WINDING_ODD` if `None` is specified.
    closeShape : bool
        Close the shape's outline. If `True` the first and last vertex will
        be joined by an edge. Must be `True` to use tesselation. Default is
        `True`.
    pos : array_like
        Initial position (`x`, `y`) of the shape on-screen relative to
        the origin located at the center of the window or buffer in `units`.
        This can be updated after initialization by setting the `pos`
        property. The default value is `(0.0, 0.0)` which results in no
        translation.
    size : array_like, float, int or None
        Width and height of the shape as `(w, h)` or `[w, h]`. If a single
        value is provided, the width and height will be set to the same
        specified value. If `None` is specified, the `size` will be set
        with values passed to `width` and `height`.
    ori : float
        Initial orientation of the shape in degrees about its origin.
        Positive values will rotate the shape clockwise, while negative
        values will rotate counterclockwise. The default value for `ori` is
        0.0 degrees.
    opacity : float
        Opacity of the shape. A value of 1.0 indicates fully opaque and 0.0
        is fully transparent (therefore invisible). Values between 1.0 and
        0.0 will result in colors being blended with objects in the
        background. This value affects the fill (`fillColor`) and outline
        (`lineColor`) colors of the shape.
    contrast : float
        Contrast level of the shape (0.0 to 1.0). This value is used to
        modulate the contrast of colors passed to `lineColor` and
        `fillColor`.
    depth : int
        Depth layer to draw the shape when `autoDraw` is enabled.
        *DEPRECATED*
    interpolate : bool
        Enable smoothing (anti-aliasing) when drawing shape outlines. This
        produces a smoother (less-pixelated) outline of the shape.
    draggable : bool
        Can this stimulus be dragged by a mouse click?
    name : str
        Optional name of the stimuli for logging.
    autoLog : bool
        Enable auto-logging of events associated with this stimuli. Useful
        for debugging and to track timing when used in conjunction with
        `autoDraw`.
    autoDraw : bool
        Enable auto drawing. When `True`, the stimulus will be drawn every
        frame without the need to explicitly call the
        :py:meth:`~psychopy.visual.ShapeStim.draw` method.
    color : array_like, str, :class:`~psychopy.colors.Color` or None
        Sets both the initial `lineColor` and `fillColor` of the shape.
    lineRGB, fillRGB: array_like, :class:`~psychopy.colors.Color` or None
        *Deprecated*. Please use `lineColor` and `fillColor`. These
        arguments may be removed in a future version.
    lineColorSpace, fillColorSpace : str
        Colorspace to use for the outline and fill. These change how the
        values passed to `lineColor` and `fillColor` are interpreted.
        *Deprecated*. Please use `colorSpace` to set both outline and fill
        colorspace. These arguments may be removed in a future version.

    """
    # Author: Jeremy Gray, November 2015, using psychopy.contrib.tesselate

    def __init__(self,
                 win,
                 units='',
                 colorSpace='rgb',
                 fillColor=False,
                 lineColor=False,
                 lineWidth=1.5,
                 vertices=((-0.5, 0), (0, +0.5), (+0.5, 0)),
                 windingRule=None,  # default GL.GLU_TESS_WINDING_ODD
                 closeShape=True,  # False for a line
                 pos=(0, 0),
                 size=1,
                 anchor=None,
                 ori=0.0,
                 opacity=1.0,
                 contrast=1.0,
                 depth=0,
                 interpolate=True,
                 draggable=False,
                 name=None,
                 autoLog=None,
                 autoDraw=False,
                 # legacy
                 color=False,
                 lineRGB=False,
                 fillRGB=False,
                 fillColorSpace=None,
                 lineColorSpace=None
                 ):

        # what local vars are defined (init params, for use by __repr__)
        self._initParamsOrig = dir()
        self._initParamsOrig.remove('self')

        super(ShapeStim, self).__init__(win,
                                        units=units,
                                        lineWidth=lineWidth,
                                        colorSpace=colorSpace,
                                        lineColor=lineColor,
                                        lineColorSpace=lineColorSpace,
                                        fillColor=fillColor,
                                        fillColorSpace=fillColorSpace,
                                        vertices=None,  # dummy verts
                                        closeShape=self.closeShape,
                                        pos=pos,
                                        size=size,
                                        anchor=anchor,
                                        ori=ori,
                                        opacity=opacity,
                                        contrast=contrast,
                                        depth=depth,
                                        interpolate=interpolate,
                                        draggable=draggable,
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
        """Set the `.vertices` and `.border` to new values, invoking
        tessellation.
        """
        # TO-DO: handle borders properly for multiloop stim like holes
        # likely requires changes in ContainerMixin to iterate over each
        # border loop

        self.border = copy.deepcopy(newVertices)
        tessVertices = []  # define to keep the linter happy
        if self.closeShape:
            # convert original vertices to triangles (= tesselation) if
            # possible. (not possible if closeShape is False, don't even try)
            GL.glPushMatrix()  # seemed to help at one point, superfluous?
            if getattr(self, "windingRule", False):
                GL.gluTessProperty(tesselate.tess, GL.GLU_TESS_WINDING_RULE,
                                   self.windingRule)
            if hasattr(newVertices[0][0], '__iter__'):
                loops = newVertices
            else:
                loops = [newVertices]
            tessVertices = tesselate.tesselate(loops)
            GL.glPopMatrix()
            if getattr(self, "windingRule", False):
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

    @property
    def vertices(self):
        """A list of lists or a numpy array (Nx2) specifying xy positions of
        each vertex, relative to the center of the field.

        Assigning to vertices can be slow if there are many vertices.

        :ref:`Operations <attrib-operations>` supported with `.setVertices()`.
        """
        return WindowMixin.vertices.fget(self)

    @vertices.setter
    def vertices(self, value):
        # check if this is a name of one of our known shapes
        if isinstance(value, str) and value in knownShapes:
            value = knownShapes[value]
        if isinstance(value, str) and value == "circle":
            # If circle is requested, calculate how many points are needed for the gap between line rects to be < 1px
            value = self._calculateMinEdges(self.lineWidth, threshold=5)
        if isinstance(value, int):
            value = self._calcEquilateralVertices(value)
        # Check shape
        WindowMixin.vertices.fset(self, value)
        self._needVertexUpdate = True
        self._tesselate(self.vertices)

    def draw(self, win=None, keepMatrix=False):
        """Draw the stimulus in the relevant window.

        You must call this method after every `win.flip()` if you want the
        stimulus to appear on that frame and then update the screen again.
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
                self._fillColor != None):
            GL.glVertexPointer(2, GL.GL_DOUBLE, 0, self.verticesPix.ctypes)
            GL.glColor4f(*self._fillColor.render('rgba1'))
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, self.verticesPix.shape[0])

        # draw the border (= a line connecting the non-tesselated vertices)
        if self._borderColor != None and self.lineWidth:
            GL.glVertexPointer(2, GL.GL_DOUBLE, 0, self._borderPix.ctypes)
            GL.glLineWidth(self.lineWidth)
            GL.glColor4f(*self._borderColor.render('rgba1'))
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
