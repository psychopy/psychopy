#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test for using iohub mouse with multiple windows. To enable multi window support
for the iohub Mouse device:

launchHubServer(window=win, Mouse=dict(enable_multi_window=True))

In this mode, if the mouse is over a psychopy window, mouse position is returned
as the pix position within the window, with origin (0,0) at window center. mouse event
window_id will equal a psychopy window handle (pyglet only).

If the mouse is not over a psychopy window, desktop mouse position is returned with
window_id = 0.
"""
import sys

from psychopy import visual, core
from psychopy.iohub import launchHubServer
from psychopy.iohub.constants import EventConstants

# True = print mouse events to stdout, False = do not
PRINT_MOUSE_EVENTS = False

win = visual.Window((400, 400), pos=(0, 30), units='height', fullscr=False, allowGUI=True, screen=0)
print('win handle: ', win._hw_handle, "pos:", win.pos)

# create the process that will run in the background polling devices
io = launchHubServer(window=win, Mouse=dict(enable_multi_window=True))

win2 = visual.Window((600, 600), pos=(500, 30), units='height', fullscr=False, allowGUI=True, screen=1)
print('win2 handle: ', win2._hw_handle, "pos:", win2.pos)

# some default devices have been created that can now be used
keyboard = io.devices.keyboard
mouse = io.devices.mouse

# TODO: How to handle setPos when mouse enable_multi_window=True
# mouse.setPosition((0.0, .250))
# win.setMouseVisible(False)

txt_proto = 'Desktop x,y: {},{}\nWin x,y: {},{}\n\nwin._hw_handle: {}\n\n\nPress Any Key to Quit.'
win_stim={}
for w in visual.window.openWindows:
    win_stim[w()._hw_handle] = visual.TextStim(w(), pos=(-0.5, 0.0), alignText='left', anchorHoriz='left',
                                               anchorVert='center', height=.04, autoLog=False, wrapWidth=0.7,
                                               text=txt_proto.format('?', '?', '?', '?', w()._hw_handle))

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
        if me.window_id > 0:
            for win_handle, stim in win_stim.items():
                if win_handle != me.window_id:
                    stim.text = txt_proto.format('?', '?', '?', '?', win_handle)
                else:
                    stim.text = txt_proto.format('?', '?', me.x_position, me.y_position, win_handle)

        else:
            for win_handle, stim in win_stim.items():
                stim.text = txt_proto.format(me.x_position, me.y_position, '?', '?', win_handle)

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
