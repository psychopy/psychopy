#!/usr/bin/env python
# -*- coding: utf-8 -*-

from psychopy import visual, core, event
from psychopy.hardware import joystick
import numpy as np

"""
Text rendering has changed a lot (for the better) under pyglet. This
script shows you the new way to specify fonts.
"""
#create a window to draw in
myWin = visual.Window(size=(800, 600), allowGUI=True, fullscr=False, screen=0, units='pix', winType='glfw')
print(myWin.getActualFrameRate())
myWin.recordFrameIntervals = True
gr = visual.GratingStim(myWin, size=(265, 256), sf=0.03)

myWin.gamma = np.asarray((1.0, 1.0, 1.0))

while 1:
    gr.draw()
    if event.getKeys(['s']):
        break

    myWin.flip()
