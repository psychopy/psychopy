#!/usr/bin/env python2

'''Creates a rectangle of given width and height
as a special case of a :class:`~psychopy.visual.ShapeStim`'''

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import psychopy  # so we can get the __path__
from psychopy import logging

from psychopy.visual.shape import ShapeStim
from psychopy.tools.attributetools import logAttrib

import numpy


class Rect(ShapeStim):
    """Creates a rectangle of given width and height as a special case of a :class:`~psychopy.visual.ShapeStim`

    (New in version 1.72.00)
    """
    def __init__(self, win, width=.5, height=.5, **kwargs):
        """
        Rect accepts all input parameters, that `~psychopy.visual.ShapeStim` accept, except for vertices and closeShape.

        :Parameters:

            width : int or float
                Width of the Rectangle (in its respective units, if specified)

            height : int or float
                Height of the Rectangle (in its respective units, if specified)

        """
        #what local vars are defined (these are the init params) for use by __repr__
        self._initParams = dir()
        self._initParams.remove('self')
        #kwargs isn't a parameter, but a list of params
        self._initParams.remove('kwargs')
        self._initParams.extend(kwargs)

        self.width = width
        self.height = height
        self._calcVertices()
        kwargs['closeShape'] = True # Make sure nobody messes around here
        kwargs['vertices'] = self.vertices

        super(Rect, self).__init__(win, **kwargs)

    def _calcVertices(self):
        self.vertices = numpy.array([
            (-self.width*.5,  self.height*.5),
            ( self.width*.5,  self.height*.5),
            ( self.width*.5, -self.height*.5),
            (-self.width*.5, -self.height*.5)
        ])

    def setWidth(self, width, log=True):
        """Changes the width of the Rectangle"""
        self.width = width
        self._calcVertices()
        self.setVertices(self.vertices, log=False)
        logAttrib(self, log, 'width')

    def setHeight(self, height, log=True):
        """Changes the height of the Rectangle """
        self.height = height
        self._calcVertices()
        self.setVertices(self.vertices, log=False)
        logAttrib(self, log, 'height')
