#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a Line between two points as a special case of a
:class:`~psychopy.visual.ShapeStim`
"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, division, print_function

import psychopy  # so we can get the __path__
from psychopy import logging
import numpy

from psychopy.visual.shape import ShapeStim
from psychopy.tools.attributetools import attributeSetter, setAttribute


class Line(ShapeStim):
    """Creates a Line between two points.

    (New in version 1.72.00)
    """

    def __init__(self, win, start=(-.5, -.5), end=(.5, .5), **kwargs):
        """Line accepts all input parameters, that
        :class:`~psychopy.visual.ShapeStim` accepts, except
        for vertices, closeShape and fillColor.

        :Notes:

        The `contains` method always return False because a line is not a
        proper (2D) polygon.
        """
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')
        # kwargs isn't a parameter, but a list of params
        self._initParams.remove('kwargs')
        self._initParams.extend(kwargs)

        self.__dict__['start'] = numpy.array(start)
        self.__dict__['end'] = numpy.array(end)
        self.__dict__['vertices'] = [start, end]
        kwargs['closeShape'] = False  # Make sure nobody messes around here
        kwargs['vertices'] = self.vertices
        kwargs['fillColor'] = None
        super(Line, self).__init__(win, **kwargs)

    @attributeSetter
    def start(self, start):
        """tuple, list or 2x1 array.

        Specifies the position of the start of the line.
        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['start'] = numpy.array(start)
        self.setVertices([self.start, self.end], log=False)

    def setStart(self, start, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'start', start, log)

    @attributeSetter
    def end(self, end):
        """tuple, list or 2x1 array

        Specifies the position of the end of the line.
        :ref:`Operations <attrib-operations>` supported."""
        self.__dict__['end'] = numpy.array(end)
        self.setVertices([self.start, self.end], log=False)

    def setEnd(self, end, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'end', end, log)

    def contains(self, *args, **kwargs):
        return False
