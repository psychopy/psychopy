#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a Circle with a given radius
as a special case of a :class:`~psychopy.visual.Polygon`
"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

import psychopy  # so we can get the __path__

from psychopy.visual.polygon import Polygon


class Circle(Polygon):
    """Creates a Circle with a given radius as a special case of a
    :class:`~psychopy.visual.ShapeStim`

    (New in version 1.72.00)
    """

    def __init__(self, win, radius=.5, edges=32, **kwargs):
        """
        Circle accepts all input parameters that
        `~psychopy.visual.ShapeStim` accept,
        except for vertices and closeShape.
        """
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')
        # kwargs isn't a parameter, but a list of params
        self._initParams.remove('kwargs')
        self._initParams.extend(kwargs)

        # initialise parent class
        kwargs['edges'] = edges
        kwargs['radius'] = radius
        super(Circle, self).__init__(win, **kwargs)
