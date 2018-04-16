#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of basic mouse handling from the ioHub (a separate asynchronous process for
fetching and processing events from hardware; mice, keyboards, eyetrackers).

Initial Version: May 6th, 2013, Sol Simpson
Abbrieviated: May 2013, Jon Peirce
Updated July, 2013, Sol, Added timeouts
"""

from __future__ import absolute_import, division, print_function

import sys

from psychopy import visual, core
from psychopy.iohub import launchHubServer

# create the process that will run in the background polling devices
io = launchHubServer()

# some default devices have been created that can now be used
display = io.devices.display
keyboard = io.devices.keyboard
mouse = io.devices.mouse

# We can use display to find info for the Window creation, like the resolution
# (which means PsychoPy won't warn you that the fullscreen does not match your requested size)
display_resolution = display.getPixelResolution()

# ioHub currently supports the use of a single full-screen PsychoPy Window
win = visual.Window(display_resolution,
                    units='pix', fullscr=True, allowGUI=False, screen=0)

# Create some psychopy visual stim (same as how you would do so normally):
fixSpot = visual.GratingStim(win, tex="none", mask="gauss",
    pos=(0, 0), size=(30, 30), color='black', autoLog=False)
grating = visual.GratingStim(win, pos=(300, 0),
    tex="sin", mask="gauss",
    color=[1.0, 0.5, -1.0],
    size=(150.0, 150.0), sf=(0.01, 0.0),
    autoLog=False)
message = visual.TextStim(win, pos=(0.0, -(display_resolution[1]/3)),
    alignHoriz='center', alignVert='center', height=40,
    text='move=mv-spot, left-drag=SF, right-drag=mv-grating, scroll=ori',
    autoLog=False, wrapWidth=display_resolution[0] * .9)
message2 = visual.TextStim(win, pos=(0.0, -(display_resolution[1]/4)),
    alignHoriz='center', alignVert='center', height=40,
    text='Press Any Key to Quit.',
    autoLog=False, wrapWidth=display_resolution[0] * .9)

last_wheelPosY = 0

io.clearEvents('all')

demo_timeout_start = core.getTime()
# Run the example until a keyboard event is received.

kb_events = None
while not kb_events:
    # Get the current mouse position
    # posDelta is the change in position * since the last call *
    position, posDelta = mouse.getPositionAndDelta()
    mouse_dX, mouse_dY = posDelta

    # Get the current state of each of the Mouse Buttons
    left_button, middle_button, right_button = mouse.getCurrentButtonStates()

    # If the left button is pressed, change the grating's spatial frequency
    if left_button:
        grating.setSF(mouse_dX / 5000.0, '+')
    elif right_button:
        grating.setPos(position)

    # If no buttons are pressed on the Mouse, move the position of the mouse cursor.
    if True not in (left_button, middle_button, right_button):
        fixSpot.setPos(position)

    if sys.platform == 'darwin':
        # On macOS, both x and y mouse wheel events can be detected, assuming the mouse being used
        # supported 2D mouse wheel motion.
        wheelPosX, wheelPosY = mouse.getScroll()
    else:
        # On Windows and Linux, only vertical (Y) wheel position is supported.
        wheelPosY = mouse.getScroll()

    # keep track of the wheel position 'delta' since the last frame.
    wheel_dY = wheelPosY - last_wheelPosY
    last_wheelPosY = wheelPosY

    # Change the orientation of the visual grating based on any vertical mouse wheel movement.
    grating.setOri(wheel_dY * 5, '+')

    # Advance 0.05 cycles per frame.
    grating.setPhase(0.05, '+')

    # Redraw the stim for this frame.
    fixSpot.draw()
    grating.draw()
    message.draw()
    message2.draw()
    flip_time = win.flip()  # redraw the buffer

    # Check for keyboard orand mouse events.
    # If 15 seconds passes without receiving any kb or mouse event,
    # then exit the demo
    kb_events = keyboard.getEvents()
    mouse_events = mouse.getEvents()
    if mouse_events:
        demo_timeout_start = mouse_events[-1].time

    if flip_time - demo_timeout_start > 15.0:
        print("Ending Demo Due to 15 Seconds of Inactivity.")
        break

    # Clear out events that were not accessed this frame.
    io.clearEvents()

# End of Example

win.close()
core.quit()

# The contents of this file are in the public domain.
