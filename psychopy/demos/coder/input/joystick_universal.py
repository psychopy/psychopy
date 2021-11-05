#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
There are two ways to retrieve info from the first 3 joystick axes. You can use:
    joy.getAxis(0)
    joy.getX()
Beyond those 3 axes you need to use the getAxis(id) form.
Although it may be that these don't always align fully. This demo should help
you to find out which physical axis maps to which number for your device.

Known issue: Pygame 1.91 unfortunately spits out a debug message every time the
joystick is accessed and there doesn't seem to be a way to get rid of those
messages.
"""

from psychopy import visual, core, event
from psychopy.hardware import joystick

joystick.backend = 'pyglet'
# As of v1.72.00, you need the winType and joystick.backend to match:
win = visual.Window((800.0, 800.0), allowGUI=False, winType=joystick.backend)

nJoysticks = joystick.getNumJoysticks()

if nJoysticks > 0:
    joy = joystick.Joystick(0)
    print('found ', joy.getName(), ' with:')
    print('...', joy.getNumButtons(), ' buttons')
    print('...', joy.getNumHats(), ' hats')
    print('...', joy.getNumAxes(), ' analogue axes')
else:
    print("You don't have a joystick connected!?")
    win.close()
    core.quit()

nAxes = joy.getNumAxes()

fixSpot = visual.GratingStim(win, pos=(0, 0),
    tex="none", mask="gauss",
    size=(0.05, 0.05), color='black')
grating = visual.GratingStim(win, pos=(0.5, 0),
    tex="sin", mask="gauss",
    color=[1.0, 0.5, -1.0],
    size=(0.2, .2), sf=(2, 0))
message = visual.TextStim(win, pos=(0, -0.95), text='Hit "q" to quit')

trialClock = core.Clock()
t = 0
while not event.getKeys():
    # update stim from joystick
    xx = joy.getX()
    yy = joy.getY()
    grating.setPos((xx, -yy))
    # change SF
    if nAxes > 3:
        sf = (joy.getZ() + 1) * 2.0  # so should be in the range 0: 4?
        grating.setSF(sf)
    # change ori
    if nAxes > 6:
        ori = joy.getAxis(5) * 90
        grating.setOri(ori)
    # if any button is pressed then make the stimulus colored
    if sum(joy.getAllButtons()):
        grating.setColor('red')
    else:
        grating.setColor('white')

    # drift the grating
    t = trialClock.getTime()
    grating.setPhase(t * 2)
    grating.draw()

    fixSpot.draw()
    message.draw()
    print(joy.getAllAxes())  # to see what your axes are doing!

    event.clearEvents()  # do this each frame to avoid a backlog of mouse events
    win.flip()  # redraw the buffer

win.close()
core.quit()

# The contents of this file are in the public domain.
