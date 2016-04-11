#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Demo for iohub keyboard.
Displays information from ioHub Keyboard Events and psychopy.event.geKeys().
"""
from __future__ import division, print_function

from psychopy import core, visual, event
#pylint: disable=no-name-in-module
from psychopy.iohub.client import launchHubServer

def createPsychopyGraphicsWindow():
    """
    Lots of text stim used in this demo, so create everything in a function.
    The code in this function is not relevant to the demo's purpose.

    :return: psychopy.visual.Window, dict of visual.TextStim
    """
    WINDOW_SIZE = 1024, 768
    dw = WINDOW_SIZE[0] / 2
    dh = WINDOW_SIZE[1] / 2
    unit_type = 'pix'
    win_ = visual.Window(WINDOW_SIZE, units=unit_type,
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
    # static label stim:
    text_stims = dict()

    ltxt = u'Press and Releases Keys for ioHub KB Event Details'
    txt_stim_kwargs = dict(text=ltxt,
                           units=unit_type,
                           pos=[0, TEXT_ROWS_START_Y],
                           height=TEXT_STIM_HEIGHT,
                           color='black',
                           wrapWidth=dw * 2)
    text_stims['title_label'] = visual.TextStim(win_, **txt_stim_kwargs)

    txt_stim_kwargs['text'] = u'Press "Q" Key to Exit Demo'
    txt_stim_kwargs['pos'] = [0, TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT]
    txt_stim_kwargs['color'] = [0.25, 0.2, 1]
    txt_stim_kwargs['alignHoriz'] = 'center'
    txt_stim_kwargs['alignVert'] = 'top'
    text_stims['title2_label'] = visual.TextStim(win_, **txt_stim_kwargs)

    txt_stim_kwargs['text'] = u'event.key:'
    txt_stim_kwargs['pos'][0] = LABEL_COLUMN_X
    txt_stim_kwargs['pos'][1] -= TEXT_ROW_HEIGHT
    txt_stim_kwargs['color'] = 'black'
    txt_stim_kwargs['alignHoriz'] = 'left'
    txt_stim_kwargs['height'] = TEXT_STIM_HEIGHT
    txt_stim_kwargs['wrapWidth'] = LABEL_WRAP_LENGTH
    del txt_stim_kwargs['alignVert']
    text_stims['key_text_label'] = visual.TextStim(win_, **txt_stim_kwargs)

    txt_stim_kwargs['text'] = u'event.char:'
    txt_stim_kwargs['pos'][1] -= TEXT_ROW_HEIGHT
    text_stims['char_label'] = visual.TextStim(win_, **txt_stim_kwargs)

    txt_stim_kwargs['text'] = u'event.modifiers'
    txt_stim_kwargs['pos'][1] -= TEXT_ROW_HEIGHT
    text_stims['modifiers_label'] = visual.TextStim(win_, **txt_stim_kwargs)

    txt_stim_kwargs['text'] = u'Last Pressed Duration:'
    txt_stim_kwargs['pos'][1] -= TEXT_ROW_HEIGHT
    text_stims['duration_label'] = visual.TextStim(win_, **txt_stim_kwargs)

    txt_stim_kwargs['text'] = u'All Pressed Keys:'
    txt_stim_kwargs['pos'][1] -= TEXT_ROW_HEIGHT
    text_stims['all_pressed_label'] = visual.TextStim(win_, **txt_stim_kwargs)

    txt_stim_kwargs['text'] = u'Last Event Type:'
    txt_stim_kwargs['pos'][1] -= TEXT_ROW_HEIGHT
    text_stims['event_type_label'] = visual.TextStim(win_, **txt_stim_kwargs)

    txt_stim_kwargs['text'] = u'event.getKeys():'
    txt_stim_kwargs['pos'][1] -= TEXT_ROW_HEIGHT
    text_stims['event_key_label'] = visual.TextStim(win_, **txt_stim_kwargs)

    # Dynamic stim:
    txt_stim_kwargs['text'] = u''
    txt_stim_kwargs['pos'][0] = VALUE_COLUMN_X
    txt_stim_kwargs['wrapWidth'] = VALUE_WRAP_LENGTH
    txt_stim_kwargs['pos'][1] = TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 2
    text_stims['key_text'] = visual.TextStim(win_, **txt_stim_kwargs)

    txt_stim_kwargs['pos'][1] -= TEXT_ROW_HEIGHT
    text_stims['key_char'] = visual.TextStim(win_, **txt_stim_kwargs)

    txt_stim_kwargs['pos'][1] -= TEXT_ROW_HEIGHT
    text_stims['modifiers'] = visual.TextStim(win_, **txt_stim_kwargs)

    txt_stim_kwargs['pos'][1] -= TEXT_ROW_HEIGHT
    text_stims['duration'] = visual.TextStim(win_, **txt_stim_kwargs)

    txt_stim_kwargs['pos'][1] -= TEXT_ROW_HEIGHT
    text_stims['all_pressed'] = visual.TextStim(win_, **txt_stim_kwargs)

    txt_stim_kwargs['pos'][1] -= TEXT_ROW_HEIGHT
    text_stims['event_type'] = visual.TextStim(win_, **txt_stim_kwargs)

    txt_stim_kwargs['pos'][1] -= TEXT_ROW_HEIGHT
    text_stims['event_key'] = visual.TextStim(win_, **txt_stim_kwargs)

    return win_, text_stims
    # end of createPsychopyGraphicsWindow function

# Demo code ...

# Start iohub process. The iohub process can be accessed using `io`.
io = launchHubServer()
keyboard = io.devices.keyboard

# create the psychopy window and text stim's
win, text_stim = createPsychopyGraphicsWindow()

# Clear keyboard events since script started...
keyboard.clearEvents()

events = []
flip_time = last_kb_evt_time = 0
# Loop until we get a 'q' key is pressed, or until 15 seconds passed
# since last keyboard event.
#
# Note that keyboard events can be compared to a str/unicode, matching when
# the event.key or event.char == str/unicode value.
while 'q' not in events and flip_time - last_kb_evt_time < 15.0:
    # Redraw stim and update display
    for s in text_stim.values():
        s.draw()
    flip_time = win.flip()

    # Get the key events using psychopy.event.getKeys()
    psychopy_keys = event.getKeys()

    # and get any new iohub keyboard events
    events = keyboard.getKeys()
    for kbe in events:
        # Update text stim's 'text' as needed......
        text_stim['key_text'].text = kbe.key
        text_stim['key_char'].text = kbe.char

        if psychopy_keys:
            text_stim['event_key'].text = psychopy_keys[0]
        elif kbe.type == 'KEYBOARD_PRESS':
            text_stim['event_key'].text = ''

        text_stim['modifiers'].text = str(kbe.modifiers)
        text_stim['all_pressed'].text = str(keyboard.state.keys())

        if kbe.type == 'KEYBOARD_PRESS':
            text_stim['duration'].text = ''
        else:
            text_stim['duration'].text = '%.6f' % kbe.duration

        text_stim['event_type'].text = kbe.type
        last_kb_evt_time = kbe.time

win.close()
io.quit()
core.quit()

# The contents of this file are in the public domain.
