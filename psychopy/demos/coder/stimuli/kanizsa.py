#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Demo for the class psychopy.visual.Pie().

Use the `Pie` class to create a Kanizsa figure which produces illusory
contours.

"""
from psychopy import core
import psychopy.visual as visual
from psychopy.visual import Pie
from psychopy import event

# open a window to render the shape
win = visual.Window((600, 600), allowGUI=False, monitor='testMonitor')

# create the stimulus object
pieStim = Pie(
    win, radius=50, start=0., end=270., fillColor=(-1., -1., -1.), units='pix')

message = visual.TextStim(
    win, text='Any key to quit', pos=(0, -0.8), units='norm')

# positions of the corners of the shapes
pos = [(-100, 100), (100, 100), (-100, -100), (100, -100)]

# orientations of the shapes
ori = [180., 270., 90., 0.]

while not event.getKeys():

    for i in range(4):
        pieStim.pos = pos[i]
        pieStim.ori = ori[i]
        pieStim.draw()

    message.draw()
    win.flip()

win.close()
core.quit()
