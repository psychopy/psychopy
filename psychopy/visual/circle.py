#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a Circle with a given radius
as a special case of a :class:`~psychopy.visual.Polygon`
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

import psychopy  # so we can get the __path__

from psychopy.visual.polygon import Polygon


class Circle(Polygon):
    """Creates a Circle with a given radius as a special case of a
    :class:`~psychopy.visual.ShapeStim`

    (New in version 1.72.00)
    """

    def __init__(self,
                 win,
                 radius=.5,
                 edges=32,
                 units='',
                 lineWidth=1.5,
                 lineColor=None,
                 lineColorSpace=None,
                 fillColor=None,
                 fillColorSpace=None,
                 pos=(0, 0),
                 size=1.0,
                 ori=0.0,
                 opacity=1.0,
                 contrast=1.0,
                 depth=0,
                 interpolate=True,
                 lineRGB=None,
                 fillRGB=None,
                 name=None,
                 autoLog=None,
                 autoDraw=False,
                 color=None,
                 colorSpace='rgb'):
        """
        Circle accepts all input parameters that
        `~psychopy.visual.ShapeStim` accept, except for `vertices` and
        `closeShape`.
        """
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')

        # initialise parent class
        super(Circle, self).__init__(
            win,
            radius=radius,
            edges=edges,
            units=units,
            lineWidth=lineWidth,
            lineColor=lineColor,
            lineColorSpace=lineColorSpace,
            fillColor=fillColor,
            fillColorSpace=fillColorSpace,
            pos=pos,
            size=size,
            ori=ori,
            opacity=opacity,
            contrast=contrast,
            depth=depth,
            interpolate=interpolate,
            lineRGB=lineRGB,
            fillRGB=fillRGB,
            name=name,
            autoLog=autoLog,
            autoDraw=autoDraw,
            color=color,
            colorSpace=colorSpace)
