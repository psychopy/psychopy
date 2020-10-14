#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
In PsychoPy 1.81.00 the support for Bits++ has been substantially rewritten and will
require a few changes to your code. It will allow a greater range of devices to be used
in future (including BitsSharp).

From now on, rather than the device/mode being a setting of the window you now
create the bitsBox object yourself, providing it with a reference to the window
and then interact with the box directly. So instead of
   win = visual.Window([1024, 768], bitsmode='fast')
   win.bits.setContrast(0.5)

you would now use:
   win = visual.Window([1024, 768])
   bitsBox = crs.BitsSharp(win, mode='bits++')
   bitsBox.setContrast(0.5)

Check your experiment still works as expected!
"""

from __future__ import absolute_import, division, print_function

from psychopy import visual, core, event, logging
from psychopy.hardware import crs
import numpy

# This is the new way to use the Bits++ box (or a Bits# device) with PsychoPy.
# The BitsSharp device under PsychoPy has some issues right now:
#    - the shaders aren't working for mono++and color++modes
#    - for BitsSharp, the device will try to deduce the identity LUT of the screen
#    but to do that it needs to be in fullscreen mode
# logging.console.setLevel(logging.INFO)
win = visual.Window([1024, 768], useFBO=True, fullscr=True, screen = 0)
bitsBox = crs.BitsPlusPlus(win, mode='bits++',
        rampType='configFile')  # change this to an integer to use a specific identityLUT

# BitsSharp can check identity LUT automatically:
# bitsBox = crs.BitsSharp(win, mode='bits++', checkConfigLevel=1)
# if not bitsBox.OK:
#    print('failed to connect to Bits box')
# else:
#    print('found %s on %s' %(bitsBox.type, bitsBox.com.port))

grating = visual.GratingStim(win, mask = 'gauss', ori=45, sf=2)

# Using bits++ with one stimulus
globalClock = core.Clock()
while True:
    # get new contrast
    t = globalClock.getTime()
    newContr = numpy.sin(t * numpy.pi * 2)  # sinusoidally modulate contrast

    # set whole screen to this contrast
    bitsBox.setContrast(newContr)

    # draw gratings and update screen
    grating.draw()
    win.flip()

    # check for a keypress
    if event.getKeys():
        break
    event.clearEvents('mouse')  # only really needed for pygame windows

# reset the bits++(and update the window so that this is done properly)
bitsBox.setContrast(1)
win.flip()

win.close()
core.quit()

# The contents of this file are in the public domain.
