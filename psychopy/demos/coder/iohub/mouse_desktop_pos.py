#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test for using iohub mouse with event positions reported in desktop coord's.
To start iohub with mouse reporting in desktop coord's, use:

launchHubServer(window=win, Mouse=dict(use_desktop_position=True))
"""
from psychopy import visual, core
from psychopy.iohub import launchHubServer

def isMouseOnPsychWin(mouse_event):
    for w in visual.window.openWindows:
        if w()._hw_handle == mouse_event.window_id:
            return mouse_event.window_id
    return 0

def mouseWindowPos(mouse_event):
    for w in visual.window.openWindows:
        if w()._hw_handle == mouse_event.window_id:
            return mouse_event.x_position-w().pos[0], mouse_event.y_position-w().pos[1]
    return 'na', 'na'

win = visual.Window((400, 400), pos=(0,30), units='height', fullscr=False, allowGUI=True, screen=0)
win2 = visual.Window((600, 600), pos=(500,30), units='height', fullscr=False, allowGUI=True, screen=0)
print('win handle: ',win._hw_handle, "pos:", win.pos)
print('win2 handle: ',win2._hw_handle, "pos:", win2.pos)
# create the process that will run in the background polling devices
io = launchHubServer(window=win, Mouse=dict(use_desktop_position=True))

# some default devices have been created that can now be used
keyboard = io.devices.keyboard
mouse = io.devices.mouse

# TODO: How to handle setPos when mouse use_desktop_position=True
#mouse.setPosition((0.0, .250))
#win.setMouseVisible(False)
quit_msg = visual.TextStim(win, pos=(0.0, -0.4), alignText='center', anchorHoriz='center', anchorVert='center',
                           height=.05, text='win._hw_handle: %d\nPress Any Key to Quit.' % win._hw_handle,
                           autoLog=False, wrapWidth=0.7)
quit_msg2 = visual.TextStim(win2, pos=(0.0, -0.4), alignText='center', anchorHoriz='center', anchorVert='center',
                           height=.05, text='win2._hw_handle: %d\nPress Any Key to Quit.' % win2._hw_handle,
                            autoLog=False, wrapWidth=0.7)
last_wheelPosY = 0

io.clearEvents('all')

demo_timeout_start = core.getTime()
# Run the example until a keyboard event is received.

kb_events = None
while not kb_events:
    quit_msg.draw()
    quit_msg2.draw()
    win.flip()  # redraw the buffer
    flip_time = win2.flip()  # redraw the buffer

    # Check for Mouse events
    mouse_events = mouse.getEvents()
    if mouse_events:
        for me in mouse_events:
            if isMouseOnPsychWin(me):
                print("Desktop: ", me.x_position, ",", me.y_position, " -> Win(%d):" % me.window_id, " ",
                      mouseWindowPos(me))
            else:
                print("Desktop: ", me.x_position, ",", me.y_position)

        demo_timeout_start = mouse_events[-1].time
    # If 15 seconds passes without receiving any kb or mouse event,
    # then exit the demo
    if flip_time - demo_timeout_start > 15.0:
        print("Ending Demo Due to 15 Seconds of Inactivity.")
        break

    # Check for keyboard events.
    kb_events = keyboard.getEvents()

# End of Example

core.quit()

# The contents of this file are in the public domain.
