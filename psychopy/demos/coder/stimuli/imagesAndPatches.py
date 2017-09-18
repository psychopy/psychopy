#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of ImageStim and GratingStim with image contents.
"""

from __future__ import division
from __future__ import print_function

from psychopy import core, visual, event

# Create a window to draw in
win = visual.Window((800, 800), monitor='testMonitor', allowGUI=False, color='black')

# Initialize some stimuli
beach = visual.ImageStim(win, image='beach.jpg', flipHoriz=True, pos=(0, 4.50), units='deg')
faceRGB = visual.ImageStim(win, image='face.jpg', mask=None,
    pos=(50, -50), size=None,  # will be the size of the original image in pixels
    units='pix', interpolate=True, autoLog=False)
print("original image size:", faceRGB.size)
faceALPHA = visual.GratingStim(win, pos=(-0.7, -0.2),
    tex="sin", mask="face.jpg", color=[1.0, 1.0, -1.0],
    size=(0.5, 0.5), units="norm", autoLog=False)
message = visual.TextStim(win, pos=(-0.95, -0.95),
    text='[Esc] to quit', color='white', alignHoriz='left', alignVert='bottom')

trialClock = core.Clock()
t = lastFPSupdate = 0
win.recordFrameIntervals = True
while not event.getKeys():
    t = trialClock.getTime()
    # Images can be manipulated on the fly
    faceRGB.ori += 1  # advance ori by 1 degree
    faceRGB.draw()
    faceALPHA.phase += 0.01  # advance phase by 1/100th of a cycle
    faceALPHA.draw()
    beach.draw()

    # update fps once per second
    if t - lastFPSupdate > 1.0:
        lastFPS = win.fps()
        lastFPSupdate = t
        message.text = "%ifps, [Esc] to quit" % lastFPS
    message.draw()

    win.flip()
    event.clearEvents('mouse')  # only really needed for pygame windows

win.close()
core.quit()

# The contents of this file are in the public domain.
