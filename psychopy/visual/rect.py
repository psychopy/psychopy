#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a rectangle of given width and height as a special case of a
:class:`~psychopy.visual.ShapeStim`"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

import numpy

import psychopy  # so we can get the __path__
from psychopy import logging

from psychopy.visual.shape import BaseShapeStim
from psychopy.tools.attributetools import attributeSetter, setAttribute


class Rect(BaseShapeStim):
    """Creates a rectangle of given width and height as a special case of a
    :class:`~psychopy.visual.ShapeStim`

    (New in version 1.72.00)
    """

    def __init__(self, win, width=.5, height=.5, autoLog=None, **kwargs):
        """Rect accepts all input parameters, that
        `~psychopy.visual.ShapeStim` accept, except vertices and closeShape.
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
        self._calcVertices()
        kwargs['closeShape'] = True  # Make sure nobody messes around here
        kwargs['vertices'] = self.vertices

        super(Rect, self).__init__(win, **kwargs)

    def _calcVertices(self):
        self.vertices = numpy.array([(-self.width * .5, self.height * .5),
                                     (self.width * .5, self.height * .5),
                                     (self.width * .5, -self.height * .5),
                                     (-self.width * .5, -self.height * .5)])

    @attributeSetter
    def width(self, value):
        """int or float.
        Width of the Rectangle (in its respective units, if specified).

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['width'] = value
        self._calcVertices()
        self.setVertices(self.vertices, log=False)

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
        self.__dict__['height'] = value
        self._calcVertices()
        self.setVertices(self.vertices, log=False)

    def setHeight(self, height, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'height', height, log, operation)
