#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of mouse handling.

As of version 1.51 the mouse coordinates for
    myMouse.getPos()
    myMouse.setPos()
    myMouse.getRel()
are in the same units as the window.

You can also check the motion of the wheel with myMouse.getWheelRel()
(in two directions for the mac mighty mouse or equivalent!)
"""

from psychopy import visual, core, event

# Create a window to draw in
win = visual.Window((600.0, 600.0), allowGUI=True)

# Initialize some stimuli
fixSpot = visual.GratingStim(win, tex="none", mask="gauss",
    pos=(0, 0), size=(0.05, 0.05), color='black', autoLog=False)
grating = visual.GratingStim(win, pos=(0.5, 0),
    tex="sin", mask="gauss",
    color=[1.0, 0.5, -1.0],
    size=(1.0, 1.0), sf=(3, 0),
    autoLog=False)  # autologging not useful for dynamic stimuli
myMouse = event.Mouse()  #  will use win by default
message = visual.TextStim(win, pos=(-0.95, -0.9), height=0.08,
    alignText='left', anchorHoriz='left',
    text='left-drag=SF, right-drag=pos, scroll=ori',
    autoLog=False)

# Continue until keypress
while not event.getKeys():
    # get mouse events
    mouse_dX, mouse_dY = myMouse.getRel()
    mouse1, mouse2, mouse3 = myMouse.getPressed()
    if (mouse1):
        grating.setSF(mouse_dX, '+')
    elif (mouse3):
        grating.setPos([mouse_dX, mouse_dY], '+')
    else:
        fixSpot.setPos(myMouse.getPos())

    # Handle the wheel(s):
    # dY is the normal mouse wheel, but some have a dX as well
    wheel_dX, wheel_dY = myMouse.getWheelRel()
    grating.setOri(wheel_dY * 5, '+')

    # get rid of other, unprocessed events
    event.clearEvents()

    # Do the drawing
    fixSpot.draw()
    grating.setPhase(0.05, '+')  # advance 0.05 cycles per frame
    grating.draw()
    message.draw()
    win.flip()

win.close()
core.quit()

# The contents of this file are in the public domain.
