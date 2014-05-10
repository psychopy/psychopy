#!/usr/bin/env python
#coding=utf-8

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""This demo shows you how to use a CRS BitsSharp device with PsychoPy

As of version 1.81.00 PsychoPy can make use of the Bits# in any of its rendering
modes provided that your graphics card supports OpenGL framebuffer objects.

You don't need to worry about setting the high- and low-bit pixels. Just draw as
normal and PsychoPy will do the conversions for you
"""

from psychopy import visual, core, event
from psychopy.hardware import crs

win = visual.Window(screen=1, fullscr=True, useFBO=True)
win.setGamma(1.0) #make sure gfx card LUT is identity

#initialise BitsSharp
#you need to give this the psychopy Window so that it can override various
#window functions (e.g. to override gamma settings etc)
bits = crs.BitsSharp(win=win, mode='mono++')
print bits.info

bits.sendMessage('$FirmwareDate\r')
core.wait(0.1)
print bits.read()
# now, you can change modes using
bits.mode = 'mono++' # 'mono++', 'bits++', 'auto++' or 'status'

#create a  stimulus and draw as normal
stim = visual.GratingStim(win,tex='sin', size=2, sf=2)
globalClock = core.Clock()
while len(event.getKeys())<1:
    t = globalClock.getTime()
    stim.phase = t*3 #drift at 3Hz
    stim.draw()
    win.flip()

#You can test pixel values (going to the box) using getVideoLine()
#this requires 'status' mode and that takes a few moments to set up
bits.mode = 'status'
core.wait(3)
pixels = bits.getVideoLine(lineN=1, nPixels=5)
print pixels

#make BitsSharp go beep
#bits.beep()

#you probably don't need to but you can send BitsSharp your own messages using
bits.sendMessage('$FirmwareDate\r')
print bits.read(timeout=0.1)

bits.mode = "bits++" #get out of status screen