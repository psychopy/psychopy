
#!/usr/bin/env python2

'''Creates a regular polygon (triangles, pentagrams, ...)
as a special case of a :class:`~psychopy.visual.ShapeStim`'''

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import psychopy  # so we can get the __path__
from psychopy import logging

from psychopy.visual.shape import ShapeStim
from psychopy.tools.attributetools import logAttrib

import numpy


class Polygon(ShapeStim):
    """Creates a regular polygon (triangles, pentagrams, ...) as a special case of a :class:`~psychopy.visual.ShapeStim`

    (New in version 1.72.00)
    """
    def __init__(self, win, edges=3, radius=.5, **kwargs):
        """
        Polygon accepts all input parameters that :class:`~psychopy.visual.ShapeStim` accepts, except for vertices and closeShape.

        :Parameters:

            edges : int
                Number of edges of the polygon

            radius : float, int, tuple, list or 2x1 array
                Radius of the Polygon (distance from the center to the corners).
                May be a -2tuple or list to stretch the polygon asymmetrically
        """
        #what local vars are defined (these are the init params) for use by __repr__
        self._initParams = dir()
        self._initParams.remove('self')
        #kwargs isn't a parameter, but a list of params
        self._initParams.remove('kwargs')
        self._initParams.extend(kwargs)
        self.autoLog = False #but will be changed if needed at end of init
        self.edges = edges
        self.radius = numpy.asarray(radius)
        self._calcVertices()
        kwargs['closeShape'] = True # Make sure nobody messes around here
        kwargs['vertices'] = self.vertices
        super(Polygon, self).__init__(win, **kwargs)

    def _calcVertices(self):
        d = numpy.pi*2/ self.edges
        self.vertices = numpy.asarray([
            numpy.asarray(
                (numpy.sin(e*d), numpy.cos(e*d))
            ) * self.radius
            for e in xrange(self.edges)
        ])
    def setEdges(self,edges, log=True):
        "Set the number of edges to a new value"
        self.edges=edges
        self._calcVertices()
        logAttrib(self, log, 'edges')
    def setRadius(self, radius, log=True):
        """Changes the radius of the Polygon. Parameter should be

            - float, int, tuple, list or 2x1 array"""
        self.radius = numpy.asarray(radius)
        self._calcVertices()
        self.setVertices(self.vertices, log=False)
        logAttrib(self, log, 'radius')
