#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
parallel ports demo

This is for win32 only.
"""

from psychopy import visual, core
from psychopy import parallel

nFramesOn = 5
nFramesOff = 30
nCycles = 2
parallel.setPortAddress(0x378)  # address for parallel port on many machines
pinNumber = 2  # choose a pin to write to (2-9).

# setup the stimuli and other objects we need
win = visual.Window([1280, 1024], allowGUI=False)  # make a window
win.flip()  # present it
myStim = visual.GratingStim(win, tex=None, mask=None, color='white', size=2)
myClock = core.Clock()  # just to keep track of time

# present a stimulus for EXACTLY 20 frames and exactly 5 cycles
for cycleN in range(nCycles):
    for frameN in range(nFramesOff):
        # don't draw, just refresh the window
        win.flip()
        parallel.setData(0)  # sets all pins low

    for frameN in range(nFramesOn):
        myStim.draw()
        win.flip()
        # immediately *after* screen refresh set pins as desired
        parallel.setPin(2, 1)  # sets just this pin to be high

# report the mean time afterwards
print('total time=%0.6f' % myClock.getTime())
print('avg frame rate=%0.3f' % win.fps())

# set pins back to low
win.flip()
parallel.setData(0)  # sets all pins low again

win.close()
core.quit()

# The contents of this file are in the public domain.
