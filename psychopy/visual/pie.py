#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Create a pie shape."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function
from psychopy.visual.shape import BaseShapeStim
from psychopy.tools.attributetools import attributeSetter, setAttribute
import numpy as np


class Pie(BaseShapeStim):
    """Creates a pie shape which is a circle with a wedge cut-out.

    This shape is sometimes referred to as a Pac-Man shape which is often
    used for creating Kanizsa figures. However, the shape can be adapted for
    other uses.

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
                 lineColorSpace='rgb',
                 fillColor=None,
                 fillColorSpace='rgb',
                 pos=(0, 0),
                 size=1.0,
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

        """
        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window this shape is associated with.
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
        lineWidth : float
            Width of the polygon's outline.
        lineColor, fillColor : `array_like`, ~`psychopy.visual.Color` or `None`
            Color of the shape's outline and fill. If `None`, a fully
            transparent color is used which makes the fill or outline invisible.
        lineColorSpace, fillColorSpace : str
            Colorspace to use for the outline and fill. This changes how the
            values passed to `lineColor` and `fillColor` are interpreted.
        pos : array_like
            Initial position (X, Y) of the polygon on-screen in `units`.
        size : float
            Size of the stimuli in window units.
        ori : float
            Initial rotation of the polygon in degrees.
        opacity : float
            Opacity of the shape. A value of 1.0 indicates fully opaque and 0.0
            is fully transparent (therefore invisible). Values between 1.0 and
            0.0 will result in colors being blended with objects in the
            background. This value affects the fill (`fillColor`) and outline
            (`lineColor`) colors of the shape.
        contrast : float
            Contrast level on the shape (0.0 to 1.0). This value is used to
            modulate the contrast of colors passed to `lineColor` and
            `shapeColor`.
        depth : int
            Depth layer to draw the stimulus.
        interpolate : bool
            Enable smoothing (anti-aliasing) when drawing shape outlines. This
            produces a smoother (less-pixelated) outline of the shape.
        name : str
            Optional name of the stimuli for logging.
        autoLog : bool
            Enable auto-logging of events associated with this stimuli. Useful
            for debugging.
        autoDraw : bool
            Enable auto drawing. When `True`, the stimulus will be drawn every
            frame without the need to explicitly call the `draw()` method.
        """
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
