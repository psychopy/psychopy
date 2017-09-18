#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo creating a drifting visual plaid stimulus.

For combining stimuli (e.g. to create a plaid) it's best to use blendMode='add'
rather than blendMode='avg'. In this blendMode the background is not overwritten
but added to, which is ideal in this instance.
On the other hand, in this mode the opacity attribute is a slight
misnomer; setting a high 'opacity' doesn't cause the background to be
obscured; it just acts as a multiplier for the contrast of the stimulus being drawn.
"""

from __future__ import division

from psychopy import visual, logging, event, core

# create a window to draw in
win = visual.Window((600, 600), allowGUI=False, blendMode='avg', useFBO=True)
logging.console.setLevel(logging.DEBUG)

# Initialize some stimuli, note contrast, opacity, ori
grating1 = visual.GratingStim(win, mask="circle", color='white', contrast=0.5,
    size=(1.0, 1.0), sf=(4, 0), ori = 45, autoLog=False)
grating2 = visual.GratingStim(win, mask="circle", color='white', opacity=0.5,
    size=(1.0, 1.0), sf=(4, 0), ori = -45, autoLog=False,
    pos=(0.1,0.1))

trialClock = core.Clock()
t = 0
while not event.getKeys() and t < 20:
    t = trialClock.getTime()

    grating1.phase = 1 * t  # drift at 1Hz
    grating1.draw()  # redraw it
    grating2.phase = 2 * t    # drift at 2Hz
    grating2.draw()  # redraw it

    win.flip()

win.close()
core.quit()

# The contents of this file are in the public domain.
