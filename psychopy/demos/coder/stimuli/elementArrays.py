#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of the ElementArrayStim, a highly optimised stimulus for generating
arrays of similar (but not identical) elements, such as in global form
arrays or random dot stimuli.

Elements must have the same basic texture and mask, but can differ in any
other way (ori, sf, rgb...).

This demo relies on numpy arrays to manipulate stimulus characteristics.
Working with array vectors is fast, much faster than python for-loops, which
would be too slow for a large array of stimuli like this.

See also the starField demo.
"""

from __future__ import division

from builtins import range
from psychopy import visual, core, event
from psychopy.tools.coordinatetools import cart2pol

# We only need these two commands from numpy.random:
from numpy.random import random, shuffle

win = visual.Window([1024, 768], units='pix', monitor='testMonitor')

N = 500
fieldSize = 500
elemSize = 40
coherence = 0.5

# build a standard (but dynamic!) global form stimulus
xys = random([N, 2]) * fieldSize - fieldSize / 2.0  # numpy vector
globForm = visual.ElementArrayStim(win,
    nElements=N, sizes=elemSize, sfs=3,
    xys=xys, colors=[180, 1, 1], colorSpace='hsv')

# calculate the orientations for global form stimulus
def makeCoherentOris(XYs, coherence, formAngle):
    # length along the first dimension:
    nNew = XYs.shape[0]

    # random orientations:
    newOris = random(nNew) * 180

    # select some elements to be coherent
    possibleIndices = list(range(nNew))  # create an array of indices
    shuffle(possibleIndices)  # shuffle it 'in-place' (no new array)
    coherentIndices = possibleIndices[0: int(nNew * coherence)]

    # use polar coordinates; set the ori of the coherent elements
    theta, radius = cart2pol(XYs[: , 0], XYs[: , 1])
    newOris[coherentIndices] = formAngle - theta[coherentIndices]

    return newOris

globForm.oris = makeCoherentOris(globForm.xys, coherence, 45)

# Give each element a life of 10 frames, and give it a new position after that
lives = random(N) * 10  # this will be the current life of each element
while not event.getKeys():
    # take a copy of the current xy and ori values
    newXYs = globForm.xys
    newOris = globForm.oris

    # find the dead elemnts and reset their life
    deadElements = (lives > 10)  # numpy vector, not standard python
    lives[deadElements] = 0

    # for the dead elements update the xy and ori
    # random array same shape as dead elements
    newXYs[deadElements, : ] = random(newXYs[deadElements, : ].shape) * fieldSize - fieldSize/2.0

    # for new elements we still want same % coherent:
    new = makeCoherentOris(newXYs[deadElements, : ], coherence, 45)
    newOris[deadElements] = new

    # update the oris and xys of the new elements
    globForm.xys = newXYs
    globForm.pris = newOris

    globForm.draw()

    win.flip()
    lives = lives + 1

    event.clearEvents('mouse')  # only really needed for pygame windows

win.close()
core.quit()

# The contents of this file are in the public domain.
