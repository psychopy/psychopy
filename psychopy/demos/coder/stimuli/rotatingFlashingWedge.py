#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo: Rotate flashing wedge
"""

from __future__ import division

from psychopy import visual, event, core

win = visual.Window([800, 800])
globalClock = core.Clock()

# Make two wedges (in opposite contrast) and alternate them for flashing
wedge1 = visual.RadialStim(win, tex='sqrXsqr', color=1, size=1,
    visibleWedge=[0, 45], radialCycles=4, angularCycles=8, interpolate=False,
    autoLog=False)  # this stim changes too much for autologging to be useful
wedge2 = visual.RadialStim(win, tex='sqrXsqr', color=-1, size=1,
    visibleWedge=[0, 45], radialCycles=4, angularCycles=8, interpolate=False,
    autoLog=False)  # this stim changes too much for autologging to be useful

t = 0
rotationRate = 0.1  # revs per sec
flashPeriod = 0.1  # seconds for one B-W cycle (ie 1/Hz)
while not event.getKeys():
    t = globalClock.getTime()
    if t % flashPeriod < flashPeriod / 2.0:  # more accurate to count frames
        stim = wedge1
    else:
        stim = wedge2
    stim.ori = t * rotationRate * 360.0  # set new rotation
    stim.draw()
    win.flip()

win.close()
core.quit()

# The contents of this file are in the public domain.
