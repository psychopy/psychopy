#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of psychopy.visual.Pie: a Kanizsa figure

Four "Pac-Man" shapes with their wedges facing inward produce the illusory
contours of a square that is not actually drawn.
"""

from psychopy import visual, event, core

win = visual.Window(size=(600, 600), monitor='testMonitor', units='height')

# centre of each inducer, at the corners of the illusory square
offset = 0.16
positions = [(-offset, offset), (offset, offset), (-offset, -offset), (offset, -offset)]

# orientation of each inducer, so that its missing wedge points at the centre
orientations = [180, 270, 90, 0]

# each Pie is filled from `start` to `end` degrees, leaving a 90 degree wedge
inducers = [
    visual.Pie(win, radius=0.08, start=0, end=270, pos=pos, ori=ori,
               fillColor='black', lineColor=None)
    for pos, ori in zip(positions, orientations)
]

msg = visual.TextStim(win, text='Press any key to quit', pos=(0, -0.4), height=0.03)

while not event.getKeys():
    for inducer in inducers:
        inducer.draw()
    msg.draw()

    win.flip()

win.close()
core.quit()

# The contents of this file are in the public domain.
