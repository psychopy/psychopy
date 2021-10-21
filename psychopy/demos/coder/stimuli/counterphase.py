#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
There are many ways to generate counter-phase, e.g. vary the contrast of
a grating sinusoidally between 1 and -1, take 2 gratings in opposite phase
overlaid and vary the opacity of the upper one between 1: 0, or take two
gratings overlaid with the upper one of 0.5 opacity and drift them
in opposite directions.

This script takes the first approach as a test of how fast
contrast textures are being rewritten to the graphics card
"""
from psychopy import core, visual, event
from numpy import sin, pi

# Create a window to draw in
win = visual.Window((600, 600), allowGUI=False, monitor='testMonitor', units='deg')

# Initialize some stimuli
grating1 = visual.GratingStim(
    win, tex="sin", mask="circle", texRes=128,
    color='white', size=5, sf=2, ori=45, depth=0.5, autoLog=False)
message = visual.TextStim(
    win, text='Any key to quit',
    pos=(-0.95, -0.95), units='norm',
    anchorVert='bottom', anchorHoriz='left')

trialClock = core.Clock()
t = 0
while not event.getKeys() and t < 20:  # quits after 20 secs
    t = trialClock.getTime()

    grating1.contrast = sin(t * pi * 2)
    grating1.draw()
    message.draw()

    win.flip()

win.close()
core.quit()

# The contents of this file are in the public domain.
