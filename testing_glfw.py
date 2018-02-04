#!/usr/bin/env python
# -*- coding: utf-8 -*-

from psychopy import visual, core, event
from psychopy.hardware import joystick
"""
Text rendering has changed a lot (for the better) under pyglet. This
script shows you the new way to specify fonts.
"""
#create a window to draw in
myWin = visual.Window(size=(800, 600), allowGUI=True, fullscr=False, winType='glfw', screen=0, useFBO=True, bpc=(8, 8, 8))
print(myWin.getActualFrameRate())
trialClock = core.Clock()
t=lastFPSupdate=0

while 1:

    if event.getKeys(['s']):
        break

    myWin.flip()

