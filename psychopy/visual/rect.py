#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a rectangle of given width and height as a special case of a
:class:`~psychopy.visual.ShapeStim`"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
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
    def __init__(self, win, width=.5, height=.5, autoLog=None, **kwargs):
        """Rect accepts all input parameters, that
        `~psychopy.visual.ShapeStim` accept, except vertices and closeShape.

        Parameters
        ----------
        win : psychopy.visual.Window
            Window object to be associated with this stimuli.
        width, height : float or int
            The width and height of the rectangle. *DEPRECATED* use `size`
            to define the dimensions of the rectangle on initialization. If
            `size` is specified the values of `width` and `height` are
            ignored.

        """
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')
        # kwargs isn't a parameter, but a list of params
        self._initParams.remove('kwargs')
        self._initParams.extend(kwargs)

        self.__dict__['width'] = width
        self.__dict__['height'] = height
        self.__dict__['autoLog'] = autoLog

        # vertices for rectangle, CCW winding order
        self.vertices = np.array([[-1.,  1.],
                                  [ 1.,  1.],
                                  [ 1., -1.],
                                  [-1., -1.]])

        self.setVertices(self.vertices, log=False)

        kwargs['closeShape'] = True  # Make sure nobody messes around here
        kwargs['vertices'] = self.vertices

        super(Rect, self).__init__(win, **kwargs)

        # Get the value of `size` if specified and use it instead of `width`
        # and `height`.
        argSize = kwargs.get('size', None)

        # If the size argument was specified, override values of width and
        # height, this is too maintain legacy compatibility. Args width and
        # height should be deprecated in later releases.
        if argSize is None:
            self.size = (width, height)
        else:
            self.size = argSize

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
