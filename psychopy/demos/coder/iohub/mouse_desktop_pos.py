#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test for using iohub mouse with event positions reported in desktop coord's.
To start iohub with mouse reporting in desktop coord's, use:

launchHubServer(window=win, Mouse=dict(use_desktop_position=True))
"""
from psychopy import visual, core
from psychopy.iohub import launchHubServer


def mouseWindowPos(mouse_event):
    for w in visual.window.openWindows:
        mx , my = mouse_event.x_position, mouse_event.y_position
        if w().pos[0] <= mx <= w().pos[0]+w().size[0]:
            if w().pos[1] <= my <= w().pos[1] + w().size[1]:
                return w, mx - w().pos[0], my - w().pos[1]
    return None, None, None


win = visual.Window((400, 400), pos=(0, 30), units='height', fullscr=False, allowGUI=True, screen=0)
win2 = visual.Window((600, 600), pos=(500, 30), units='height', fullscr=False, allowGUI=True, screen=0)
print('win handle: ', win._hw_handle, "pos:", win.pos)
print('win2 handle: ', win2._hw_handle, "pos:", win2.pos)
# create the process that will run in the background polling devices
io = launchHubServer(window=win, Mouse=dict(use_desktop_position=True))

# some default devices have been created that can now be used
keyboard = io.devices.keyboard
mouse = io.devices.mouse

# TODO: How to handle setPos when mouse use_desktop_position=True
# mouse.setPosition((0.0, .250))
# win.setMouseVisible(False)

txt_proto = 'Desktop x,y: {},{}\nWin x,y: {},{}\n\nwin._hw_handle: {}\n\n\nPress Any Key to Quit.'
win_stim={}
win_stim[win._hw_handle] = visual.TextStim(win, pos=(0.0, 0.0), alignText='center', anchorHoriz='center',
                                           anchorVert='center', height=.05, autoLog=False, wrapWidth=0.7,
                                           text=txt_proto.format('?', '?', '?', '?', win._hw_handle))

win_stim[win2._hw_handle] = visual.TextStim(win2, pos=(0.0, 0.0), alignText='center', anchorHoriz='center',
                                            anchorVert='center', height=.05, autoLog=False, wrapWidth=0.7,
                                            text=txt_proto.format('?', '?', '?', '?', win._hw_handle))

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
        # Only update display based on last received event
        me = mouse_events[-1]
        psycho_win, x, y = mouseWindowPos(me)
        if psycho_win:
            whndl = psycho_win()._hw_handle
            win_stim[whndl].text = txt_proto.format(me.x_position, me.y_position, x, y, whndl)
            for win_handle, stim in win_stim.items():
                if win_handle != whndl:
                    stim.text = txt_proto.format(me.x_position, me.y_position, '?', '?', win_handle)
                    break

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

# End of Example

core.quit()

# The contents of this file are in the public domain.
