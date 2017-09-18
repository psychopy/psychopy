#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Textures (e.g. for a GratingStim) can be created from custom numpy arrays.

For this they should be square arrays, with size in powers of two (e.g. 64, 128, 256, 512)
A 256x256 array can then be given color efficiently using the normal stimulus methods.
A 256x256x3 array has its color defined by the array (obviously).

This demo creates a radial array as a patch stimulus, using helper functions from
psychopy.filters and then creates a second sub-stimulus created from a section of
the original. Both are masked simply by circles.
"""

from __future__ import division

from psychopy import visual, event, core
from psychopy.visual import filters
import numpy as np

win = visual.Window([800, 600], units='pix')

# Generate the radial textures
cycles = 6
res = 512
radius = filters.makeRadialMatrix(res)
radialTexture = np.sin(radius * 2 * np.pi * cycles)
mainMask = filters.makeMask(res)

# Select the upper left quadrant of our radial stimulus
radialTexture_sub = radialTexture[256:, 0:256]
# and create an appropriate mask for it
subMask = filters.makeMask(res, radius=0.5, center=[-0, 0])

bigStim = visual.GratingStim(win, tex=radialTexture, mask=mainMask,
   color='white', size=512, sf=1.0 / 512, interpolate=True)
# draw the quadrant stimulus centered in the top left quadrant of the 'base' stimulus (so they're aligned)
subStim = visual.GratingStim(win, tex=radialTexture_sub, pos=(-128, 128), mask=subMask,
   color=[1, 1, 1], size=256, sf=1.0 / 256, interpolate=True, autoLog=False)

bigStim.draw()
subStim.draw()
globalClock =core.Clock()

while not event.getKeys():
    # clockwise rotation of sub-patch
    t = globalClock.getTime()

    bigStim.draw()
    subStim.ori = np.sin(t * 2 * np.pi) * 20  # control speed
    subStim.draw()
    win.flip()

    event.clearEvents('mouse')  # only really needed for pygame windows

win.close()
core.quit()

# The contents of this file are in the public domain.
