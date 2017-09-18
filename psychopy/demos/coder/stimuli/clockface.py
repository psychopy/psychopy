#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of using ShapeStim to make a functioning visual clock.
"""

from __future__ import division

from psychopy import visual, core, event
import numpy, time
win = visual.Window([800, 800], monitor='testMonitor')

# vertices (using numpy means we can scale them easily)
handVerts = numpy.array([ [0, 0.8], [-0.05, 0], [0, -0.05], [0.05, 0] ])

second = visual.ShapeStim(win, vertices=[[0, -0.1], [0.1, 0.8]],
    lineColor=[1, -1, -1], fillColor=None, lineWidth=2, autoLog=False)
minute = visual.ShapeStim(win, vertices=handVerts,
    lineColor='white', fillColor=[0.8, 0.8, 0.8], autoLog=False)
hour = visual.ShapeStim(win, vertices=handVerts/2.0,
    lineColor='black', fillColor=[-0.8, -0.8, -0.8], autoLog=False)
clock = core.Clock()

while not event.getKeys():
    t = time.localtime()

    minPos = numpy.floor(t[4]) * 360 / 60  # NB floor will round down
    minute.ori = minPos
    minute.draw()

    hourPos = (t[3]) * 360 / 12  # this one can be smooth
    hour.ori = hourPos
    hour.draw()

    secPos = numpy.floor(t[5]) * 360 / 60  # NB floor will round down
    second.ori = secPos
    second.draw()

    win.flip()
    event.clearEvents('mouse')  # only really needed for pygame windows

win.close()
core.quit()

# The contents of this file are in the public domain.
