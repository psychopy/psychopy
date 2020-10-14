#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a rectangle of given width and height as a special case of a
:class:`~psychopy.visual.ShapeStim`"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

import numpy as np

import psychopy  # so we can get the __path__
from psychopy.visual.shape import BaseShapeStim
from psychopy.tools.attributetools import attributeSetter, setAttribute


class Rect(BaseShapeStim):
    """Creates a rectangle of given width and height as a special case of a
    :class:`~psychopy.visual.ShapeStim`

    (New in version 1.72.00)

    Attributes
    ----------
    width, height : float or int
        The width and height of the rectangle. Values are aliased with fields
        in the `size` attribute. Use these values to adjust the size of the
        rectangle in a single dimension after initialization.

    """
    def __init__(self,
                 win,
                 width=.5,
                 height=.5,
                 autoLog=None,
                 units='',
                 lineWidth=1.5,
                 lineColor='white',
                 lineColorSpace='rgb',
                 fillColor=None,
                 fillColorSpace='rgb',
                 pos=(0, 0),
                 size=None,
                 ori=0.0,
                 opacity=1.0,
                 contrast=1.0,
                 depth=0,
                 interpolate=True,
                 name=None,
                 autoDraw=False):
        """
        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window object to be associated with this stimuli.
        width, height : float or int
            The width and height of the rectangle. *DEPRECATED* use `size`
            to define the dimensions of the rectangle on initialization. If
            `size` is specified the values of `width` and `height` are
            ignored. This is to provide legacy compatibility for existing
            applications.
        size : array_like, float or int
            Width and height of the rectangle as (w, h) or [w, h]. If a single
            value is provided, the width and height will be set to the same
            specified value. If `None` is specified, the `size` will be set
            with values passed to `width` and `height`.

        """
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
            ori=ori,
            opacity=opacity,
            contrast=contrast,
            depth=depth,
            interpolate=interpolate,
            name=name,
            autoLog=autoLog,
            autoDraw=autoDraw)

    @attributeSetter
    def size(self, value):
        """array-like.
        Size of the rectangle (`width` and `height`).
        """
        # Needed to override `size` to ensure `width` and `height` attrs
        # are updated when it changes.
        self.__dict__['size'] = np.array(value, float)

        width, height = self.__dict__['size']
        self.__dict__['width'] = width
        self.__dict__['height'] = height

        self._needVertexUpdate = True

    def setSize(self, size, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message

        :ref:`Operations <attrib-operations>` supported.
        """
        setAttribute(self, 'size', size, log, operation)

    @attributeSetter
    def width(self, value):
        """int or float.
        Width of the Rectangle (in its respective units, if specified).

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['width'] = float(value)
        self.size = (self.__dict__['width'], self.size[1])

    def setWidth(self, width, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'width', width, log, operation)

    @attributeSetter
    def height(self, value):
        """int or float.
        Height of the Rectangle (in its respective units, if specified).

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['height'] = float(value)
        self.size = (self.size[0], self.__dict__['height'])

    def setHeight(self, height, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'height', height, log, operation)
