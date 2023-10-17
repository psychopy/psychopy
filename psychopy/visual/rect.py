#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a rectangle of given width and height as a special case of a
:class:`~psychopy.visual.ShapeStim`"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import numpy as np

import psychopy  # so we can get the __path__
from psychopy.visual.shape import BaseShapeStim
from psychopy.tools.attributetools import attributeSetter, setAttribute


class Rect(BaseShapeStim):
    """Creates a rectangle of given width and height as a special case of a
    :class:`~psychopy.visual.ShapeStim`. This is a lazy-imported class,
    therefore import using full path `from psychopy.visual.rect import Rect`
    when inheriting from it.

    Parameters
    ----------
    win : :class:`~psychopy.visual.Window`
        Window this shape is being drawn to. The stimulus instance will
        allocate its required resources using that Windows context. In many
        cases, a stimulus instance cannot be drawn on different windows
        unless those windows share the same OpenGL context, which permits
        resources to be shared between them.
    width, height : float or int
        The width or height of the shape. *DEPRECATED* use `size` to define
        the dimensions of the shape on initialization. If `size` is
        specified the values of `width` and `height` are ignored. This is to
        provide legacy compatibility for existing applications.
    units : str
        Units to use when drawing. This will affect how parameters and
        attributes `pos`, `size` and `radius` are interpreted.
    lineWidth : float
        Width of the shape's outline.
    lineColor, fillColor : array_like, str, :class:`~psychopy.colors.Color` or None
        Color of the shape outline and fill. If `None`, a fully transparent
        color is used which makes the fill or outline invisible.
    lineColorSpace, fillColorSpace : str
        Colorspace to use for the outline and fill. These change how the
        values passed to `lineColor` and `fillColor` are interpreted.
        *Deprecated*. Please use `colorSpace` to set both outline and fill
        colorspace. These arguments may be removed in a future version.
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
    color : array_like, str, :class:`~psychopy.colors.Color` or None
        Sets both the initial `lineColor` and `fillColor` of the shape.
    colorSpace : str
        Sets the colorspace, changing how values passed to `lineColor` and
        `fillColor` are interpreted.
    draggable : bool
        Can this stimulus be dragged by a mouse click?

    Attributes
    ----------
    width, height : float or int
        The width and height of the rectangle. Values are aliased with fields
        in the `size` attribute. Use these values to adjust the size of the
        rectangle in a single dimension after initialization.

    """

    _defaultFillColor = 'white'
    _defaultLineColor = None

    def __init__(self,
                 win,
                 width=.5,
                 height=.5,
                 units='',
                 lineWidth=1.5,
                 lineColor=False,
                 fillColor=False,
                 colorSpace='rgb',
                 pos=(0, 0),
                 size=None,
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
                 color=None,
                 lineColorSpace=None,
                 fillColorSpace=None,
                 lineRGB=False,
                 fillRGB=False,
                 ):
        # width and height attributes, these are later aliased with `size`
        self.__dict__['width'] = float(width)
        self.__dict__['height'] = float(height)

        # If the size argument was specified, override values of width and
        # height, this is to maintain legacy compatibility. Args width and
        # height should be deprecated in later releases.
        if size is None:
            size = (self.__dict__['width'],
                    self.__dict__['height'])

        # vertices for rectangle, CCW winding order
        vertices = np.array([[-.5,  .5],
                             [ .5,  .5],
                             [ .5, -.5],
                             [-.5, -.5]])
        super(Rect, self).__init__(
            win,
            units=units,
            lineWidth=lineWidth,
            lineColor=lineColor,
            lineColorSpace=lineColorSpace,
            fillColor=fillColor,
            fillColorSpace=fillColorSpace,
            vertices=vertices,
            closeShape=True,
            pos=pos,
            size=size,
            anchor=anchor,
            ori=ori,
            opacity=opacity,
            contrast=contrast,
            depth=depth,
            interpolate=interpolate,
            draggable=draggable,
            lineRGB=lineRGB,
            fillRGB=fillRGB,
            name=name,
            autoLog=autoLog,
            autoDraw=autoDraw,
            color=color,
            colorSpace=colorSpace)

    def setSize(self, size, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message

        :ref:`Operations <attrib-operations>` supported.
        """
        setAttribute(self, 'size', size, log, operation)

    def setWidth(self, width, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'width', width, log, operation)

    def setHeight(self, height, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'height', height, log, operation)
