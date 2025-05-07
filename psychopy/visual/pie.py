#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Create a pie shape."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy.visual.shape import BaseShapeStim
from psychopy.tools.attributetools import attributeSetter, setAttribute
import numpy as np


class Pie(BaseShapeStim):
    """Creates a pie shape which is a circle with a wedge cut-out. This is a 
    lazy-imported class, therefore import using full path 
    `from psychopy.visual.pie import Pie` when inheriting from it.

    This shape is sometimes referred to as a Pac-Man shape which is often
    used for creating Kanizsa figures. However, the shape can be adapted for
    other uses.

    Parameters
    ----------
    win : :class:`~psychopy.visual.Window`
        Window this shape is being drawn to. The stimulus instance will
        allocate its required resources using that Windows context. In many
        cases, a stimulus instance cannot be drawn on different windows
        unless those windows share the same OpenGL context, which permits
        resources to be shared between them.
    radius : float or int
        Radius of the shape. Avoid using `size` for adjusting figure
        dimensions if radius != 0.5 which will result in undefined behavior.
    start, end : float or int
        Start and end angles of the filled region of the shape in
        degrees. Shapes are filled counter clockwise between the specified
        angles.
    edges : int
        Number of edges to use when drawing the figure. A greater number of
        edges will result in smoother curves, but will require more time
        to compute.
    units : str
        Units to use when drawing. This will affect how parameters and
        attributes `pos`, `size` and `radius` are interpreted.
    lineWidth : float
        Width of the shape's outline.
    lineColor, fillColor : array_like, str, :class:`~psychopy.colors.Color` or None
        Color of the shape outline and fill. If `None`, a fully transparent
        color is used which makes the fill or outline invisible.
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
    name : str
        Optional name of the stimuli for logging.
    autoLog : bool
        Enable auto-logging of events associated with this stimuli. Useful
        for debugging and to track timing when used in conjunction with
        `autoDraw`.
    autoDraw : bool
        Enable auto drawing. When `True`, the stimulus will be drawn every
        frame without the need to explicitly call the
        :py:meth:`~psychopy.visual.shape.ShapeStim.draw()` method.
    color : array_like, str, :class:`~psychopy.colors.Color` or None
        Sets both the initial `lineColor` and `fillColor` of the shape.
    colorSpace : str
        Sets the colorspace, changing how values passed to `lineColor` and
        `fillColor` are interpreted.

    Attributes
    ----------
    start, end : float or int
        Start and end angles of the filled region of the shape in
        degrees. Shapes are filled counter clockwise between the specified
        angles.
    radius : float or int
        Radius of the shape. Avoid using `size` for adjusting figure dimensions
        if radius != 0.5 which will result in undefined behavior.

    """

    def __init__(self,
                 win,
                 radius=.5,
                 start=0.0,
                 end=90.0,
                 edges=32,
                 units='',
                 lineWidth=1.5,
                 lineColor=None,
                 fillColor=None,
                 pos=(0, 0),
                 size=1.0,
                 ori=0.0,
                 opacity=1.0,
                 contrast=1.0,
                 depth=0,
                 interpolate=True,
                 name=None,
                 autoLog=None,
                 autoDraw=False,
                 colorSpace=None,
                 # legacy
                 color=False,
                 fillColorSpace='rgb',
                 lineColorSpace='rgb',
                 lineRGB=False,
                 fillRGB=False,
                 ):

        self.__dict__['radius'] = radius
        self.__dict__['edges'] = edges
        self.__dict__['start'] = start
        self.__dict__['end'] = end

        self.vertices = self._calcVertices()

        super(Pie, self).__init__(
             win,
             units=units,
             lineWidth=lineWidth,
             lineColor=lineColor,
             lineColorSpace=lineColorSpace,
             fillColor=fillColor,
             fillColorSpace=fillColorSpace,
             vertices=self.vertices,
             closeShape=True,
             pos=pos,
             size=size,
             ori=ori,
             opacity=opacity,
             contrast=contrast,
             depth=depth,
             interpolate=interpolate,
             lineRGB=lineRGB,
             fillRGB=fillRGB,
             name=name,
             autoLog=autoLog,
             autoDraw=autoDraw,
             color=color,
             colorSpace=colorSpace)

    def _calcVertices(self):
        """Calculate the required vertices for the figure.
        """
        startRadians = np.radians(self.start)
        endRadians = np.radians(self.end)

        # get number of steps for vertices
        edges = self.__dict__['edges']
        steps = np.linspace(startRadians, endRadians, num=edges)

        # offset by 1 since the first vertex needs to be at centre
        verts = np.zeros((edges + 2, 2), float)
        verts[1:-1, 0] = np.sin(steps)
        verts[1:-1, 1] = np.cos(steps)

        verts *= self.radius

        return verts

    @attributeSetter
    def start(self, value):
        """Start angle of the slice/wedge in degrees (`float` or `int`).

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['start'] = value
        self.vertices = self._calcVertices()
        self.setVertices(self.vertices, log=False)

    def setStart(self, start, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'start', start, log, operation)

    @attributeSetter
    def end(self, value):
        """End angle of the slice/wedge in degrees (`float` or `int`).

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['end'] = value
        self.vertices = self._calcVertices()
        self.setVertices(self.vertices, log=False)

    def setEnd(self, end, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'end', end, log, operation)

    @attributeSetter
    def radius(self, value):
        """Radius of the shape in `units` (`float` or `int`).

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['radius'] = value
        self.vertices = self._calcVertices()
        self.setVertices(self.vertices, log=False)

    def setRadius(self, end, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'radius', end, log, operation)
