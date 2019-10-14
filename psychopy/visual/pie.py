#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a pie shape."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function
from psychopy.visual.shape import BaseShapeStim
from psychopy.tools.attributetools import attributeSetter, setAttribute
import numpy as np


class Pie(BaseShapeStim):
    """Creates a pie shape which is a circle with a wedge cut-out. This
    shape is frequently used for creating Kanizsa figures. However, it
    can be adapted for other uses.

    Attributes
    ----------
    start, end : float or int
        Start and end angles of the filled region of the shape in
        degrees. Shapes are filled counter clockwise between the
        specified angles.
    radius : float or int
        Radius of the shape.

    """
    def __init__(self, win, radius=.5, edges=64, start=0.0, end=90.0, **kwargs):
        self.radius = radius
        self.edges = edges
        self.__dict__['start'] = start
        self.__dict__['end'] = end

        self._initParams = dir()
        self._initParams.remove('self')
        # kwargs isn't a parameter, but a list of params
        self._initParams.remove('kwargs')
        self._initParams.extend(kwargs)

        self.vertices = self._calcVertices()
        kwargs['closeShape'] = True
        kwargs['vertices'] = self.vertices

        super(Pie, self).__init__(win, **kwargs)

    def _calcVertices(self):
        """Calculate the required vertices for the figure.
        """
        startRadians = np.radians(self.start)
        endRadians = np.radians(self.end)

        # get number of steps for vertices
        steps = np.linspace(startRadians, endRadians, num=self.edges)

        # offset by 1 since the first vertex needs to be at centre
        verts = np.zeros((self.edges + 1, 2), float)
        verts[1:, 0] = np.sin(steps)
        verts[1:, 1] = np.cos(steps)

        verts *= self.radius

        return verts

    @attributeSetter
    def start(self, value):
        """int or float.
        Height of the Rectangle (in its respective units, if specified).

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['start'] = value
        self._calcVertices()
        self.setVertices(self.vertices, log=False)

    def setStart(self, start, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'start', start, log, operation)

    @attributeSetter
    def end(self, value):
        """int or float.
        Height of the Rectangle (in its respective units, if specified).

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['end'] = value
        self._calcVertices()
        self.setVertices(self.vertices, log=False)

    def setEnd(self, end, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'end', end, log, operation)

    @attributeSetter
    def radius(self, value):
        """int or float.
        Height of the Rectangle (in its respective units, if specified).

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['radius'] = value
        self._calcVertices()
        self.setVertices(self.vertices, log=False)

    def setRadius(self, end, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'radius', end, log, operation)
