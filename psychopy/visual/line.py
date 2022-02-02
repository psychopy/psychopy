#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a Line between two points as a special case of a
:class:`~psychopy.visual.ShapeStim`
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).




import psychopy  # so we can get the __path__
from psychopy import logging
import numpy

from psychopy.visual.shape import ShapeStim
from psychopy.tools.attributetools import attributeSetter, setAttribute


class Line(ShapeStim):
    """Creates a Line between two points.

    `Line` accepts all input parameters, that :class:`~psychopy.visual.ShapeStim`
    accepts, except for `vertices`, `closeShape` and `fillColor`.

    (New in version 1.72.00)

    Parameters
    ----------
    win : :class:`~psychopy.visual.Window`
        Window this line is being drawn to. The stimulus instance will
        allocate its required resources using that Windows context. In many
        cases, a stimulus instance cannot be drawn on different windows
        unless those windows share the same OpenGL context, which permits
        resources to be shared between them.
    start : array_like
        Coordinate `(x, y)` of the starting point of the line.
    end : array_like
        Coordinate `(x, y)` of the end-point of the line.
    units : str
        Units to use when drawing. This will affect how parameters and
        attributes `pos`, `size` and `radius` are interpreted.
    lineWidth : float
        Width of the line.
    lineColor : array_like, str, :class:`~psychopy.colors.Color` or None
        Color of the line. If `None`, a fully transparent color is used which
        makes the line invisible. *Deprecated* use `color` instead.
    lineColorSpace : str or None
        Colorspace to use for the line. These change how the values passed to
        `lineColor` are interpreted. *Deprecated*. Please use `colorSpace` to
        set the line colorspace. This arguments may be removed in a future
        version.
    pos : array_like
        Initial translation (`x`, `y`) of the line on-screen relative to the
        origin located at the center of the window or buffer in `units`.
        This can be updated after initialization by setting the `pos`
        property. The default value is `(0.0, 0.0)` which results in no
        translation.
    size : float or array_like
        Initial scale factor for adjusting the size of the line. A single
        value (`float`) will apply uniform scaling, while an array (`sx`,
        `sy`) will result in anisotropic scaling in the horizontal (`sx`)
        and vertical (`sy`) direction. Providing negative values to `size`
        will cause the line to be mirrored. Scaling can be changed by
        setting the `size` property after initialization. The default value
        is `1.0` which results in no scaling.
    ori : float
        Initial orientation of the line in degrees about its origin.
        Positive values will rotate the line clockwise, while negative
        values will rotate counterclockwise. The default value for `ori` is
        0.0 degrees.
    opacity : float
        Opacity of the line. A value of 1.0 indicates fully opaque and 0.0
        is fully transparent (therefore invisible). Values between 1.0 and
        0.0 will result in colors being blended with objects in the
        background. This value affects the fill (`fillColor`) and outline
        (`lineColor`) colors of the shape.
    contrast : float
        Contrast level of the line (0.0 to 1.0). This value is used to
        modulate the contrast of colors passed to `lineColor` and
        `fillColor`.
    depth : int
        Depth layer to draw the stimulus when `autoDraw` is enabled.
    interpolate : bool
        Enable smoothing (anti-aliasing) when drawing lines. This produces a
        smoother (less-pixelated) line.
    lineRGB: array_like, :class:`~psychopy.colors.Color` or None
        *Deprecated*. Please use `color` instead. This argument may be removed
        in a future version.
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

    Notes
    -----
    The `contains` method always return `False` because a line is not a proper
    (2D) polygon.

    Attributes
    ----------
    start, end : array_like
        Coordinates `(x, y)` for the start- and end-point of the line.

    """
    def __init__(self,
                 win,
                 start=(-.5, -.5),
                 end=(.5, .5),
                 units=None,
                 lineWidth=1.5,
                 lineColor='white',
                 fillColor=None, # Not used, but is supplied by Builder via Polygon
                 lineColorSpace=None,
                 pos=(0, 0),
                 size=1.0,
                 anchor="center",
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

        """

        """
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')

        self.__dict__['start'] = numpy.array(start)
        self.__dict__['end'] = numpy.array(end)

        super(Line, self).__init__(
            win,
            units=units,
            lineWidth=lineWidth,
            lineColor=lineColor,
            lineColorSpace=None,
            fillColor=None,
            fillColorSpace=lineColorSpace,  # have these set to the same
            vertices=None,
            anchor=anchor,
            closeShape=False,
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

        self._vertices.setas([start, end], self.units)
        del self._tesselVertices

    @property
    def color(self):
        return self.lineColor

    @color.setter
    def color(self, value):
        self.lineColor = value

    @attributeSetter
    def start(self, start):
        """tuple, list or 2x1 array.

        Specifies the position of the start of the line.
        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['start'] = numpy.array(start)
        self.setVertices([self.start, self.end], log=False)

    def setStart(self, start, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'start', start, log)

    @attributeSetter
    def end(self, end):
        """tuple, list or 2x1 array

        Specifies the position of the end of the line.
        :ref:`Operations <attrib-operations>` supported."""
        self.__dict__['end'] = numpy.array(end)
        self.setVertices([self.start, self.end], log=False)

    def setEnd(self, end, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'end', end, log)

    def contains(self, *args, **kwargs):
        return False
