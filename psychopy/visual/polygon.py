#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Creates a regular polygon (triangles, pentagrams, ...)
as a special case of a :class:`~psychopy.visual.ShapeStim`'''

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from builtins import range
import psychopy  # so we can get the __path__

from psychopy.visual.shape import BaseShapeStim
from psychopy.tools.attributetools import attributeSetter, setAttribute

import numpy


class Polygon(BaseShapeStim):
    """Creates a regular polygon (triangles, pentagrams, ...).
     A special case of a :class:`~psychopy.visual.ShapeStim`.

    (New in version 1.72.00)
    """

    def __init__(self, win, edges=3, radius=.5, **kwargs):
        """Polygon accepts all input parameters that
        :class:`~psychopy.visual.ShapeStim` accepts, except for
        vertices and closeShape.
        """
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')
        # kwargs isn't a parameter, but a list of params
        self._initParams.remove('kwargs')
        self._initParams.extend(kwargs)
        self.autoLog = False  # but will be changed if needed at end of init
        self.__dict__['edges'] = edges
        self.radius = numpy.asarray(radius)
        self._calcVertices()
        kwargs['closeShape'] = True  # Make sure nobody messes around here
        kwargs['vertices'] = self.vertices
        super(Polygon, self).__init__(win, **kwargs)

    def _calcVertices(self):
        d = numpy.pi * 2 / self.edges
        self.vertices = numpy.asarray(
            [numpy.asarray((numpy.sin(e * d), numpy.cos(e * d))) * self.radius
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
        self.__dict__['radius'] = numpy.array(radius)
        self._calcVertices()
        self.setVertices(self.vertices, log=False)

    def setRadius(self, radius, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'radius', radius, log, operation)
