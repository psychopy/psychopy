#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a regular polygon (triangles, pentagons, ...) as a special case of a
:class:`~psychopy.visual.ShapeStim`"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from builtins import range
import psychopy  # so we can get the __path__
from psychopy.visual.shape import BaseShapeStim
from psychopy.tools.attributetools import attributeSetter, setAttribute

import numpy as np


class Polygon(BaseShapeStim):
    """Creates a regular polygon (triangles, pentagons, ...).

     this class is a special case of a :class:`~psychopy.visual.ShapeStim`.

    (New in version 1.72.00)

    """
    def __init__(self,
                 win,
                 edges=3,
                 radius=.5,
                 units='',
                 lineWidth=1.5,
                 lineColor=None,
                 lineColorSpace=None,
                 fillColor=None,
                 fillColorSpace=None,
                 pos=(0, 0),
                 size=1.0,
                 ori=0.0,
                 opacity=1.0,
                 contrast=1.0,
                 depth=0,
                 interpolate=True,
                 lineRGB=False,
                 fillRGB=False,
                 name=None,
                 autoLog=None,
                 autoDraw=False,
                 color=None,
                 colorSpace='rgb'):
        """
        Polygon accepts all input parameters that
        :class:`~psychopy.visual.ShapeStim` accepts, except for `vertices` and
        `closeShape`.

        Parameters
        ----------
        win : ~`psychopy.visual.Window`
            Window this polygon is being drawn to.
        radius : float
            Maximum radius of the polygon.
        units : str
            Units to use when drawing.
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
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')

        self.autoLog = False  # but will be changed if needed at end of init
        self.__dict__['edges'] = edges
        self.radius = np.asarray(radius)
        self._calcVertices()

        super(Polygon, self).__init__(
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
        d = np.pi * 2 / self.edges
        self.vertices = np.asarray(
            [np.asarray((np.sin(e * d), np.cos(e * d))) * self.radius
             for e in range(int(round(self.edges)))])

    @attributeSetter
    def edges(self, edges):
        """Number of edges of the polygon. Floats are rounded to int.

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['edges'] = edges
        self._calcVertices()
        self.setVertices(self.vertices, log=False)

    def setEdges(self, edges, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message"""
        setAttribute(self, 'edges', edges, log, operation)

    @attributeSetter
    def radius(self, radius):
        """float, int, tuple, list or 2x1 array
        Radius of the Polygon (distance from the center to the corners).
        May be a -2tuple or list to stretch the polygon asymmetrically.

        :ref:`Operations <attrib-operations>` supported.

        Usually there's a setAttribute(value, log=False) method for each
        attribute. Use this if you want to disable logging.
        """
        self.__dict__['radius'] = np.array(radius)
        self._calcVertices()
        self.setVertices(self.vertices, log=False)

    def setRadius(self, radius, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'radius', radius, log, operation)
