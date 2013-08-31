#!/usr/bin/env python

'''Creates a Circle with a given radius
as a special case of a :class:`~psychopy.visual.Polygon`'''

# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import psychopy  # so we can get the __path__
from psychopy import logging

from psychopy.visual.polygon import Polygon

import numpy


class Circle(Polygon):
    """Creates a Circle with a given radius as a special case of a :class:`~psychopy.visual.ShapeStim`

    (New in version 1.72.00)
    """
    def __init__(self, win, radius=.5, edges=32, **kwargs):
        """
        Circle accepts all input parameters that `~psychopy.visual.ShapeStim` accept, except for vertices and closeShape.

        :Parameters:

            edges : float or int (default=32)
                Specifies the resolution of the polygon that is approximating the
                circle.

            radius : float, int, tuple, list or 2x1 array
                Radius of the Circle (distance from the center to the corners).
                If radius is a 2-tuple or list, the values will be interpreted as semi-major and
                semi-minor radii of an ellipse.
        """
        kwargs['edges'] = edges
        kwargs['radius'] = radius
        Polygon.__init__(self, win, **kwargs)


    def setRadius(self, radius, log=True):
        """Changes the radius of the Polygon. If radius is a 2-tuple or list, the values will be
        interpreted as semi-major and semi-minor radii of an ellipse."""
        self.radius = numpy.asarray(radius)
        self._calcVertices()
        self.setVertices(self.vertices, log=False)
        if log and self.autoLog:
            self.win.logOnFlip("Set %s radius=%s" %(self.name, radius),
                level=logging.EXP,obj=self)
