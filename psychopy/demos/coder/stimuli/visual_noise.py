#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo: Using an arbitrary numpy array as a visual stimulus.

Also illustrates logging DEBUG level details to the console.
"""

from psychopy import visual, event, core, logging
import numpy

logging.console.setLevel(logging.DEBUG)

win = visual.Window([600, 600], allowGUI=False)

noiseTexture = numpy.random.rand(128, 128) * 2.0 - 1
patch = visual.GratingStim(win, tex=noiseTexture,
    size=(128, 128), units='pix',
    interpolate=False, autoLog=False)

while not event.getKeys():
    # increment by (1, 0.5) pixels per frame:
    patch.phase += (1 / 128.0, 0.5 / 128.0)
    patch.draw()
    win.flip()

win.close()
core.quit()

# The contents of this file are in the public domain.
