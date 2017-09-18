#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo for the class psychopy.visual.Aperture().

Draw two gabor circles, one with an irregular aperture and one with no aperture.
"""

from __future__ import division

from psychopy import visual, event

# Need to allowStencil=True for a window with an Aperture:
win = visual.Window([400, 400], allowStencil=True, units='norm')

instr = visual.TextStim(win, text="Any key to quit", pos=(0, -.7))
gabor1 = visual.GratingStim(win, mask='circle', sf=4, size=1.2, color=[0.5, -0.5, 1])
gabor2 = visual.GratingStim(win, mask='circle', sf=4, size=1.2, color=[-0.5, -0.5, -1])
vertices = [(-0.02, -0.0), (-.8, .2), (0, .6), (.1, 0.06), (.8, .3), (.6, -.4)]

# `sizes in Aperture refers to the diameter when shape='circle';
# vertices or other shapes are scaled accordingly
aperture = visual.Aperture(win, size=0.9, shape=vertices)  # try shape='square'
aperture.enabled = False  # enabled by default when created

gabor1.draw()
instr.draw()

# drawing will now only be done within the aperture shape:
aperture.enabled = True
gabor2.draw()

win.flip()
event.waitKeys()

win.close()

# The contents of this file are in the public domain.
