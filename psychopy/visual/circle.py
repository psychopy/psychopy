#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a Circle with a given radius
as a special case of a :class:`~psychopy.visual.Polygon`
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import psychopy  # so we can get the __path__

from psychopy.visual.polygon import Polygon
import numpy as np


class Circle(Polygon):
    """Creates a Circle with a given radius as a special case of a
    :class:`~psychopy.visual.ShapeStim`

    Parameters
    ----------
    win : :class:`~psychopy.visual.Window`
        Window this shape is being drawn to. The stimulus instance will
        allocate its required resources using that Windows context. In many
        cases, a stimulus instance cannot be drawn on different windows
        unless those windows share the same OpenGL context, which permits
        resources to be shared between them.
    edges : int
        Number of edges to use to define the outline of the circle. The
        greater the number of edges, the 'rounder' the circle will appear.
    radius : float
        Initial radius of the circle in `units`.
    units : str
        Units to use when drawing. This will affect how parameters and
        attributes `pos`, `size` and `radius` are interpreted.
    lineWidth : float
        Width of the circle's outline.
    lineColor, fillColor : array_like, str, :class:`~psychopy.colors.Color` or None
        Color of the circle's outline and fill. If `None`, a fully
        transparent color is used which makes the fill or outline invisible.
    lineColorSpace, fillColorSpace : str
        Colorspace to use for the outline and fill. These change how the
        values passed to `lineColor` and `fillColor` are interpreted.
        *Deprecated*. Please use `colorSpace` to set both outline and fill
        colorspace. These arguments may be removed in a future version.
    pos : array_like
        Initial position (`x`, `y`) of the circle on-screen relative to the
        origin located at the center of the window or buffer in `units`
        (unless changed by specifying `viewPos`). This can be updated after
        initialization by setting the `pos` property. The default value is
        `(0.0, 0.0)` which results in no translation.
    size : float or array_like
        Initial scale factor for adjusting the size of the circle. A single
        value (`float`) will apply uniform scaling, while an array (`sx`,
        `sy`) will result in anisotropic scaling in the horizontal (`sx`)
        and vertical (`sy`) direction. Providing negative values to `size`
        will cause the shape being mirrored. Scaling can be changed by
        setting the `size` property after initialization. The default value
        is `1.0` which results in no scaling.
    ori : float
        Initial orientation of the circle in degrees about its origin.
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
        Depth layer to draw the stimulus when `autoDraw` is enabled.
    interpolate : bool
        Enable smoothing (anti-aliasing) when drawing shape outlines. This
        produces a smoother (less-pixelated) outline of the shape.
    lineRGB, fillRGB: array_like, :class:`~psychopy.colors.Color` or None
        *Deprecated*. Please use `lineColor` and `fillColor`. These
        arguments may be removed in a future version.
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
    color : array_like, str, :class:`~psychopy.colors.Color` or `None`
        Sets both the initial `lineColor` and `fillColor` of the shape.
    colorSpace : str
        Sets the colorspace, changing how values passed to `lineColor` and
        `fillColor` are interpreted.

    Attributes
    ----------
    radius : float or int
        Radius of the shape. Avoid using `size` for adjusting figure dimensions
        if radius != 0.5 which will result in undefined behavior.

    """
    def __init__(self,
                 win,
                 radius=.5,
                 edges=32,
                 units='',
                 lineWidth=1.5,
                 lineColor=None,
                 lineColorSpace=None,
                 fillColor='white',
                 fillColorSpace=None,
                 pos=(0, 0),
                 size=1.0,
                 anchor=None,
                 ori=0.0,
                 opacity=None,
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
            anchor=anchor,
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

    def getSector(self, theta, useCache=True):
        """
        Return a copy of this Circle, whose vertices are reduced such that only a sector of angle theta is visible.
        """
        def _newSector(parent):
            """
            Copy this circle, but with 360 edges
            """
            return Polygon(
                parent.win,
                radius=parent.radius,
                edges=360,
                units=parent.units,
                lineWidth=parent.lineWidth,
                lineColor=parent._borderColor,
                fillColor=parent._fillColor,
                pos=parent.pos,
                size=parent.size,
                anchor=parent.anchor,
                ori=parent.ori,
                contrast=parent.contrast or 1,
                depth=parent.depth,
                interpolate=parent.interpolate,
                autoLog=parent.autoLog,
                autoDraw=parent.autoDraw,
            )

        assert theta <= 360, "When retrieving a sector of a circle, its angle cannot exceed 360."

        if useCache:
            # If useCache, use last cached sector object
            if hasattr(self, "_lastSector"):
                sector = self._lastSector
            else:
                sector = self._lastSector = _newSector(self)
        else:
            # Otherwise, make a new one
            sector = _newSector(self)

        # Get 360 point circular vertices
        sector.edges = 360
        sector._calcVertices()
        # Get vertices of arc
        arc = sector.vertices[:int(theta)]
        # Add midpoint to start and end of vertices and apply
        sector.vertices = np.vstack([
            (0, 0),
            arc,
            (0, 0)]
        )
        sector._updateVertices()

        return sector
