#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demo of using the iohub mouse.
"""

import sys

from psychopy import visual, core
from psychopy.iohub import launchHubServer


win = visual.Window((1920, 1080), units='height', fullscr=True, allowGUI=False, screen=0)

# create the process that will run in the background polling devices
io = launchHubServer(window=win)

# some default devices have been created that can now be used
keyboard = io.devices.keyboard
mouse = io.devices.mouse
mouse.setPosition((0.0, .250))
#win.setMouseVisible(False)

# Create some psychopy visual stim
fixSpot = visual.GratingStim(win, tex="none", mask="gauss", pos=(0, 0), size=(.03, .03), color='black', autoLog=False)
grating = visual.GratingStim(win, pos=(.3, 0), tex="sin", mask="gauss", color=[1.0, .5, -1.0], size=(.15, .15),
                             sf=(.01, 0), autoLog=False)
message = visual.TextStim(win, pos=(0, -.2), height=.03, alignText='center', anchorHoriz='center', anchorVert='center',
                          wrapWidth=.7, text='move=mv-spot, left-drag=SF, right-drag=mv-grating, scroll=ori',
                          autoLog=False)
displayIdMsg = visual.TextStim(win, pos=(0.0, -0.3), alignText='center', anchorHoriz='center', anchorVert='center',
                               height=.03, text='Display X', autoLog=False, wrapWidth=0.7)
message3 = visual.TextStim(win, pos=(0.0, -0.4), alignText='center', anchorHoriz='center', anchorVert='center',
                           height=.03, text='Press Any Key to Quit.', autoLog=False, wrapWidth=0.7)
last_wheelPosY = 0

io.clearEvents('all')

demo_timeout_start = core.getTime()
# Run the example until a keyboard event is received.

kb_events = None
last_display_ix = -1
while not kb_events:
    # Get the current mouse position
    # posDelta is the change in position * since the last call *
    position, posDelta, display_ix = mouse.getPositionAndDelta(return_display_index=True)
    mouse_dX, mouse_dY = posDelta

    if display_ix is not None and display_ix != last_display_ix:
        displayIdMsg.setText("Display %d" % display_ix)
        last_display_ix = display_ix

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
    message3.draw()
    displayIdMsg.draw()
    flip_time = win.flip()  # redraw the buffer

    # Check for keyboard and mouse events.
    # If 15 seconds passes without receiving any mouse events, then exit the demo
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
