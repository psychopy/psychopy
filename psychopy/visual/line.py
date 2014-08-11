#!/usr/bin/env python

'''Creates a Line between two points
as a special case of a :class:`~psychopy.visual.ShapeStim`'''

# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import psychopy  # so we can get the __path__
from psychopy import logging

from psychopy.visual.shape import ShapeStim


class Line(ShapeStim):
    """Creates a Line between two points.

    (New in version 1.72.00)
    """
    def __init__(self, win, start=(-.5, -.5), end=(.5, .5), **kwargs):
        """
        Line accepts all input parameters, that :class:`~psychopy.visual.ShapeStim` accepts, except
        for vertices, closeShape and fillColor.

        The methods `contains` and `overlaps` are inherited from `~psychopy.visual.ShapeStim`,
        but always return False (because a line is not a proper (2D) polygon).

        :Parameters:

            start : tuple, list or 2x1 array
                Specifies the position of the start of the line

            end : tuple, list or 2x1 array
                Specifies the position of the end of the line

        """
        self.start = start
        self.end = end
        self.vertices = [start, end]
        kwargs['closeShape'] = False # Make sure nobody messes around here
        kwargs['vertices'] = self.vertices
        kwargs['fillColor'] = None
        ShapeStim.__init__(self, win, **kwargs)

    def setStart(self, start, log=True):
        """Changes the start point of the line. Argument should be

            - tuple, list or 2x1 array specifying the coordinates of the start point"""
        self.start = start
        self.setVertices([self.start, self.end], log=False)
        if log and self.autoLog:
            self.win.logOnFlip("Set %s start=%s" %(self.name, start),
                level=logging.EXP,obj=self)

    def setEnd(self, end, log=True):
        """Changes the end point of the line. Argument should be a tuple, list
        or 2x1 array specifying the coordinates of the end point"""
        self.end = end
        self.setVertices([self.start, self.end], log=False)
        if log and self.autoLog:
            self.win.logOnFlip("Set %s end=%s" %(self.name, end),
                level=logging.EXP,obj=self)

    def contains(self):
        pass
    def overlaps(self):
        pass
