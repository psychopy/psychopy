#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ElementArray demo.

This demo requires a graphics card that supports OpenGL2 extensions.

It shows how to manipulate an arbitrary set of elements using numpy arrays
and avoiding for loops in your code for optimised performance.

See also the elementArrayStim demo.
"""

from __future__ import division

from psychopy import visual, event, core
from psychopy.tools.coordinatetools import pol2cart
import numpy

nDots = 500
maxSpeed = 0.02
dotSize = .0075

dotsTheta = numpy.random.rand(nDots) * 360
dotsRadius = (numpy.random.rand(nDots) ** 0.5) * 2
speed = numpy.random.rand(nDots) * maxSpeed

win = visual.Window([800, 600], color=[-1, -1, -1])
dots = visual.ElementArrayStim(win, elementTex=None, elementMask='circle',
    nElements=nDots, sizes=dotSize)

while not event.getKeys():
    # update radius
    dotsRadius = (dotsRadius + speed)
    # random radius where radius too large
    outFieldDots = (dotsRadius >= 2.0)
    dotsRadius[outFieldDots] = numpy.random.rand(sum(outFieldDots)) * 2.0

    dotsX, dotsY = pol2cart(dotsTheta, dotsRadius)
    dotsX *=  0.75  # to account for wider aspect ratio
    dots.xys = numpy.array([dotsX, dotsY]).transpose()
    dots.draw()

    win.flip()

win.close()
core.quit()

# The contents of this file are in the public domain.
