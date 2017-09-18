#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of an efficient visual mask, by modulating its opacity.

When you want to reveal an image gradually from behind a mask,
the tempting thing to do is to alter a stimulus mask using .setMask()

That will actually be very slow because of the overhead in sending
textures to the graphics card on each change. Instead, the more
efficient way of doing this is to create an element array and alter the
opacity of each element of the array to reveal what's behind it.
"""

from __future__ import division

from psychopy import core, visual, event
from psychopy.tools.arraytools import createXYs
import numpy

win = visual.Window((600, 600), allowGUI=False, color=0,
        monitor='testMonitor', winType='pyglet', units='norm')

# Initialize some stimuli
gabor = visual.GratingStim(win, tex='sin', mask='gauss', size=1, sf=5)

# create a grid of xy vals
xys = createXYs(numpy.linspace(-0.5, 0.5, 11))  # 11 entries from -0.5 to 0.5

# create opacity for each square in mask
opacs = numpy.ones(len(xys))  # all opaque to start

# create mask
elSize = xys[1, 0] - xys[0, 0]
mask = visual.ElementArrayStim(win, elementTex=None, elementMask=None,
    nElements=len(xys),
    colors=win.color,  # i.e., same as background
    xys=xys, opacities=opacs,
    sizes=elSize)

trialClock = core.Clock()
t = 0
maskIndices = numpy.arange(len(xys))
numpy.random.shuffle(maskIndices)

frameN = 0
while not event.getKeys():
    t = trialClock.getTime()
    gabor.ori += 1  # advance ori by 1 degree
    gabor.draw()

    # update mask by making one element transparent, selected by index
    if frameN < len(maskIndices):
        ii = maskIndices[frameN]
        opacs[ii] = 0
        mask.opacities = opacs
    mask.draw()

    win.flip()
    frameN += 1

win.close()
core.quit()

# The contents of this file are in the public domain.
