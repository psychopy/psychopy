#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a Circle with a given radius
as a special case of a :class:`~psychopy.visual.Polygon`
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

import psychopy  # so we can get the __path__

from psychopy.visual.polygon import Polygon


class Circle(Polygon):
    """Creates a Circle with a given radius as a special case of a
    :class:`~psychopy.visual.ShapeStim`

    (New in version 1.72.00)

    """
    def __init__(self,
                 win,
                 radius=.5,
                 edges=32,
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
                 lineRGB=None,
                 fillRGB=None,
                 name=None,
                 autoLog=None,
                 autoDraw=False,
                 color=None,
                 colorSpace='rgb'):
        """
        Circle accepts all input parameters that
        `~psychopy.visual.ShapeStim` accept, except for `vertices` and
        `closeShape`.

        Parameters
        ----------
        win : ~`psychopy.visual.Window`
            Window this circle is being drawn to.
        radius : float
            Radius of the circle.
        units : str
            Units to use when drawing.
        lineWidth : float
            Width of the circle's outline.
        lineColor, fillColor : `array_like`, ~`psychopy.visual.Color` or `None`
            Color of the circle's outline and fill. If `None`, a fully
            transparent color is used which makes the fill or outline invisible.
        lineColorSpace, fillColorSpace : str
            Colorspace to use for the outline and fill. This changes how the
            values passed to `lineColor` and `fillColor` are interpreted.
        pos : array_like
            Initial position (X, Y) of the circle on-screen in `units`.
        size : float
            Scaling factor for te size of the circle in window units.
        ori : float
            Initial rotation of the circle in degrees.
        opacity : float
            Opacity of the circle. A value of 1.0 indicates fully opaque and 0.0
            is fully transparent (therefore invisible). Values between 1.0 and
            0.0 will result in colors being blended with objects in the
            background. This value affects the fill and outline of the shape.
        contrast : float
            Contrast level on the circle (0.0 - 1.0).
        depth : int
            Depth layer to draw the circle.
        interpolate : bool

        """
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')

        # initialise parent class
        super(Circle, self).__init__(
            win,
            radius=radius,
            edges=edges,
            units=units,
            lineWidth=lineWidth,
            lineColor=lineColor,
            lineColorSpace=lineColorSpace,
            fillColor=fillColor,
            fillColorSpace=fillColorSpace,
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
