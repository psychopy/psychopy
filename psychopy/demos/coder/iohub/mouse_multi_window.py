#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test for using iohub mouse with multiple windows on multiple monitors.

To enable multi window support for the iohub Mouse device:

launchHubServer(window=win, Mouse=dict(enable_multi_window=True))

In this mode, if the mouse is over a psychopy window, mouse position is returned
as the pix position within the window, with origin (0,0) at window center. mouse event
window_id will equal a psychopy window handle (pyglet only).

Note: If testing using 'cm' or 'deg' units, use your actual monitor configurations
or update the `monitors.Monitor` created below to match your setup.

If the mouse is not over a psychopy window, desktop mouse position is returned with
window_id = 0.
"""
import sys

from psychopy import visual, core, monitors
from psychopy.iohub import launchHubServer
from psychopy.iohub.constants import EventConstants

# True = print mouse events to stdout, False = do not
PRINT_MOUSE_EVENTS = False

# Test creating a monitor before starting iohub
mon0 = monitors.Monitor('monitor0')
mon0.setDistance(60.0)
mon0.setWidth(33.0)
mon0.setSizePix((1280, 1024))
win = visual.Window((400, 400), pos=(0, 30), units='norm', fullscr=False, allowGUI=True, screen=0, monitor=mon0,
                    winType='pyglet')

# start the iohub server
io = launchHubServer(window=win, Mouse=dict(enable_multi_window=True))

# Test creating a monitor after starting iohub
mon1 = monitors.Monitor('monitor1')
mon1.setDistance(60.0)
mon1.setWidth(34.5)
mon1.setSizePix((1920, 1080))
win2 = visual.Window((600, 600), pos=(500, 30), units='cm', fullscr=False, allowGUI=True, screen=1, monitor=mon1,
                     winType='pyglet')

# access the iohub keyboard and mouse
keyboard = io.devices.keyboard
mouse = io.devices.mouse

# TODO: How to handle setPos when mouse enable_multi_window=True
# mouse.setPosition((0.0, 0.0))

txt_proto = 'Desktop x,y: {}, {}\nWin x,y: {:.4}, {:.4}\n\nwin.units: {}\n\n\nPress Any Key to Quit.'
win_stim={}
for w in visual.window.openWindows:
    win_stim[w()._hw_handle] = visual.TextStim(w(), pos=(-0.75, 0.0), units='norm', alignText='left', anchorHoriz='left',
                                               anchorVert='center', height=.1, autoLog=False, wrapWidth=1.5,
                                               text=txt_proto.format('?', '?', '?', '?', w().units))

io.clearEvents('all')

demo_timeout_start = core.getTime()

# Run the example until a keyboard event is received.
kb_events = None
while not kb_events:
    for stim in win_stim.values():
        stim.draw()
    win.flip()  # redraw the buffer
    flip_time = win2.flip()  # redraw the buffer

    # Check for Mouse events
    mouse_events = mouse.getEvents()
    if mouse_events:
        # Simple example of handling different mouse event types.
        if PRINT_MOUSE_EVENTS:
            for me in mouse_events:
                if me.type == EventConstants.MOUSE_MOVE:
                    print(me)
                elif me.type == EventConstants.MOUSE_DRAG:
                    print(me)
                elif me.type == EventConstants.MOUSE_BUTTON_PRESS:
                    print(me)
                elif me.type == EventConstants.MOUSE_BUTTON_RELEASE:
                    print(me)
                elif me.type == EventConstants.MOUSE_SCROLL:
                    print(me)
                else:
                    print("Unhandled event type:", me.type, me)
                    sys.exit()

        # Only update display based on last received event
        me = mouse_events[-1]
        #print("display: ", me.display_id)
        if me.window_id > 0:
            for win_handle, stim in win_stim.items():
                if win_handle != me.window_id:
                    stim.text = txt_proto.format('?', '?', '?', '?', stim.win.units)
                else:
                    stim.text = txt_proto.format('?', '?', me.x_position, me.y_position, stim.win.units)

        else:
            for win_handle, stim in win_stim.items():
                stim.text = txt_proto.format(me.x_position, me.y_position, '?', '?', stim.win.units)

        demo_timeout_start = mouse_events[-1].time
    # If 15 seconds passes without receiving any kb or mouse event,
    # then exit the demo
    if flip_time - demo_timeout_start > 15.0:
        print("Ending Demo Due to 15 Seconds of Inactivity.")
        break

    # Check for keyboard events.
    kb_events = keyboard.getEvents()

win.close()
win2.close()

core.quit()
# End of Example

# The contents of this file are in the public domain.
