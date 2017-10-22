#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo for iohub keyboard

Displays information from ioHub Keyboard Events vs. psychopy.event.geKeys().
"""

from __future__ import absolute_import, division, print_function

from builtins import str
from psychopy import core, visual, event
from psychopy.iohub import launchHubServer

WINDOW_SIZE = 1024, 768

# Start iohub process. The iohub process can be accessed using `io`.
io = launchHubServer()

# A `keyboard` variable is used to access the iohub Keyboard device.
keyboard = io.devices.keyboard

dw = WINDOW_SIZE[0] / 2
dh = WINDOW_SIZE[1] / 2
unit_type = 'pix'
win = visual.Window(WINDOW_SIZE, units=unit_type,
    color=[128, 128, 128], colorSpace='rgb255')

# constants for text element spacing:
ROW_COUNT = 10
TEXT_ROW_HEIGHT = (dh * 2) / ROW_COUNT
TEXT_STIM_HEIGHT = int(TEXT_ROW_HEIGHT / 2)
MARGIN = 25
LABEL_COLUMN_X = -dw + MARGIN
VALUE_COLUMN_X = MARGIN
LABEL_WRAP_LENGTH = dw - MARGIN / 2
VALUE_WRAP_LENGTH = dw - MARGIN / 2
TEXT_ROWS_START_Y = dh - MARGIN

# Create some psychoPy stim to display the keyboard events received...

# field labels:
title_label = visual.TextStim(win, units=unit_type,
    text=u'Press and Releases Keys for ioHub KB Event Details',
    pos=[0, TEXT_ROWS_START_Y],
    height=TEXT_STIM_HEIGHT,
    color='black', wrapWidth=dw * 2)
title2_label = visual.TextStim(win, units=unit_type,
    text=u'Press "Q" Key to Exit Demo',
    pos=[0, TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT],
    height=TEXT_STIM_HEIGHT,
    color=[0.25, 0.2, 1],
    alignHoriz='center',
    alignVert='top',
    wrapWidth=dw * 2)
key_text_label = visual.TextStim(win, units=unit_type, text=u'event.key:',
    pos=[LABEL_COLUMN_X, TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 2],
    color='black', alignHoriz='left',
    height=TEXT_STIM_HEIGHT, wrapWidth=LABEL_WRAP_LENGTH)
char_label = visual.TextStim(win, units=unit_type, text=u'event.char:',
    pos=[LABEL_COLUMN_X, TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 3],
    color='black', alignHoriz='left',
    height=TEXT_STIM_HEIGHT, wrapWidth=LABEL_WRAP_LENGTH)
modifiers_label = visual.TextStim(win, units=unit_type,
    text=u'event.modifiers',
    pos=[LABEL_COLUMN_X, TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 4],
    color='black', alignHoriz='left',
    height=TEXT_STIM_HEIGHT, wrapWidth=LABEL_WRAP_LENGTH)
keypress_duration_label = visual.TextStim(win, units=unit_type,
    text=u'Last Pressed Duration:',
    pos=[LABEL_COLUMN_X, TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 5],
    color='black', alignHoriz='left',
    height=TEXT_STIM_HEIGHT, wrapWidth=LABEL_WRAP_LENGTH)
all_pressed__label = visual.TextStim(win, units=unit_type,
    text=u'All Pressed Keys:',
    pos=[LABEL_COLUMN_X, TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 6],
    color='black', alignHoriz='left',
    height=TEXT_STIM_HEIGHT, wrapWidth=LABEL_WRAP_LENGTH)
event_type_label = visual.TextStim(win, units=unit_type,
    text=u'Last Event Type:',
    pos=[LABEL_COLUMN_X, TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 7],
    color='black', alignHoriz='left',
    height=TEXT_STIM_HEIGHT, wrapWidth=LABEL_WRAP_LENGTH)
psychopy_key_label = visual.TextStim(win, units=unit_type,
    text=u'event.getKeys():',
    pos=[LABEL_COLUMN_X, TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 8],
    color='black', alignHoriz='left',
    height=TEXT_STIM_HEIGHT, wrapWidth=LABEL_WRAP_LENGTH)

# Dynamic stim:
key_text_stim = visual.TextStim(win, units=unit_type, text=u'',
    pos=[VALUE_COLUMN_X, TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 2],
    color='black', alignHoriz='left',
    height=TEXT_STIM_HEIGHT, wrapWidth=LABEL_WRAP_LENGTH)
char_stim = visual.TextStim(win, units=unit_type, text=u'',
    pos=[VALUE_COLUMN_X, TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 3],
    color='black', alignHoriz='left',
    height=TEXT_STIM_HEIGHT, wrapWidth=LABEL_WRAP_LENGTH)
modifiers_stim = visual.TextStim(win, units=unit_type, text=u'',
    pos=[VALUE_COLUMN_X, TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 4],
    color='black', alignHoriz='left',
    height=TEXT_STIM_HEIGHT, wrapWidth=LABEL_WRAP_LENGTH)
keypress_duration_stim = visual.TextStim(win, units=unit_type, text=u'',
    pos=[VALUE_COLUMN_X, TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 5],
    color='black', alignHoriz='left',
    height=TEXT_STIM_HEIGHT, wrapWidth=LABEL_WRAP_LENGTH)
all_pressed_stim = visual.TextStim(win, units=unit_type, text=u'',
    pos=[VALUE_COLUMN_X, TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 6],
    color='black', alignHoriz='left',
    height=TEXT_STIM_HEIGHT, wrapWidth=LABEL_WRAP_LENGTH)
event_type_stim = visual.TextStim(win, units=unit_type, text=u'',
    pos=[VALUE_COLUMN_X, TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 7],
    color='black', alignHoriz='left',
    height=TEXT_STIM_HEIGHT, wrapWidth=LABEL_WRAP_LENGTH)
psychopy_key_stim = visual.TextStim(win, units=unit_type, text=u'',
    pos=[VALUE_COLUMN_X, TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 8],
    color='black', alignHoriz='left',
    height=TEXT_STIM_HEIGHT,  wrapWidth=dw * 2)

# Having all the stim to update / draw in a list makes drawing code
# more compact and reusable
STIM_LIST = [title_label, title2_label, key_text_label, char_label,
    modifiers_label, keypress_duration_label, all_pressed__label,
    event_type_label, psychopy_key_label,
    key_text_stim, char_stim, modifiers_stim, keypress_duration_stim,
    all_pressed_stim, event_type_stim, psychopy_key_stim]

# Clear all events from the global and device level ioHub Event Buffers.

io.clearEvents('all')

QUIT_EXP = False
demo_timeout_start = core.getTime()

# Loop until we get a 'escape' key is pressed,
# or until 15 seconds passed since last keyboard event.

# Note that keyboard events can be compared to a string, matching when
# the event.key or .char == basestring value.
events = []
flip_time = demo_timeout_start = 0
while not 'q' in events and flip_time - demo_timeout_start < 15.0:
    for s in STIM_LIST:
        s.draw()
    flip_time = win.flip()

    events = keyboard.getKeys()

    for kbe in events:
        key_text_stim.text = kbe.key
        char_stim.text = kbe.char

        psychopy_keys = event.getKeys()
        if psychopy_keys:
            psychopy_key_stim.text = psychopy_keys[0]
        elif kbe.type == "KEYBOARD_PRESS":
            psychopy_key_stim.text = ''

        modifiers_stim.text = str(kbe.modifiers)
        all_pressed_stim.text = str(list(keyboard.state.keys()))

        if kbe.type == "KEYBOARD_PRESS":
            keypress_duration_stim.text = ''
        else:
            keypress_duration_stim.text = "%.6f" % kbe.duration

        event_type_stim.text = kbe.type
        demo_timeout_start = kbe.time

win.close()
core.quit()

# The contents of this file are in the public domain.
