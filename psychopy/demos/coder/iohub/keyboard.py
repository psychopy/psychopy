# -*- coding: utf-8 -*-
"""
iohub_keyboard.py

Displays event information from ioHub Keyboard Events. 

Inital Version: May 6th, 2013, Sol Simpson
Updated June 22nd: Added demo timeout. SS
"""

MAX_KEY_EVENT_COUNT = 500
WINDOW_SIZE = 1024,768

from psychopy import core, visual, event
from psychopy.iohub import launchHubServer

io = launchHubServer()
display = io.devices.display
keyboard = io.devices.keyboard
mouse = io.devices.mouse

dw, dh = WINDOW_SIZE
dw = dw / 2
dh = dh / 2
unit_type = 'pix'
window = visual.Window((dw*2, dh*2), units=unit_type, color=[128, 128, 128],
                       colorSpace='rgb255')

# constants for text element spacing:
ROW_COUNT = 10
TEXT_ROW_HEIGHT = (dh*2)/(ROW_COUNT)
TEXT_STIM_HEIGHT = int(TEXT_ROW_HEIGHT/2)
MARGIN=25
LABEL_COLUMN_X = -dw+MARGIN
VALUE_COLUMN_X = MARGIN
LABEL_WRAP_LENGTH = dw-MARGIN/2
VALUE_WRAP_LENGTH = dw-MARGIN/2
TEXT_ROWS_START_Y = dh - MARGIN

# Create some psychoPy stim to display the keyboard events received...
#
# field labels:
title_label = visual.TextStim(window, units=unit_type,
                               text=u'Press and Releases Keys for ioHub KB Event Details',

                               pos=[0, TEXT_ROWS_START_Y],
                               height=TEXT_STIM_HEIGHT,
                               color=[-1, 1, 0.5], colorSpace='rgb',
                               alignHoriz='center',
                               alignVert='top', wrapWidth=dw * 2)
title2_label = visual.TextStim(window, units=unit_type,
                              text=u'Press CTRL + Q to Exit Demo',
                              pos=[0, TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT],
                              height=TEXT_STIM_HEIGHT,
                              color=[0.25, 0.2, 1], colorSpace='rgb',
                              alignHoriz='center',
                              alignVert='top', wrapWidth=dw * 2)
key_text_label = visual.TextStim(window, units=unit_type, text=u'event.key:',
                                 pos=[LABEL_COLUMN_X,
                                      TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 2],
                                 height=TEXT_STIM_HEIGHT,
                                 color=[-1, -1, -1], colorSpace='rgb',
                                 alignHoriz='left',
                                 alignVert='top', wrapWidth=LABEL_WRAP_LENGTH)
char_label = visual.TextStim(window, units=unit_type, text=u'event.char:',
                             pos=[LABEL_COLUMN_X,
                                  TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 3],
                             height=TEXT_STIM_HEIGHT,
                             color=[-1, -1, -1], colorSpace='rgb',
                             alignHoriz='left',
                             alignVert='top', wrapWidth=LABEL_WRAP_LENGTH)
modifiers_label = visual.TextStim(window, units=unit_type,
                                  text=u'event.modifiers',
                                  pos=[LABEL_COLUMN_X,
                                       TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 4],
                                  height=TEXT_STIM_HEIGHT, color=[-1, -1, -1],
                                  colorSpace='rgb',
                                  alignHoriz='left', alignVert='top',
                                  wrapWidth=LABEL_WRAP_LENGTH)
keypress_duration_label = visual.TextStim(window, units=unit_type,
                                          text=u'Last Pressed Duration:',
                                          pos=[LABEL_COLUMN_X,
                                               TEXT_ROWS_START_Y -
                                               TEXT_ROW_HEIGHT * 5],
                                          height=TEXT_STIM_HEIGHT,
                                          color=[-1, -1, -1],
                                          colorSpace='rgb', alignHoriz='left',
                                          alignVert='top',
                                          wrapWidth=LABEL_WRAP_LENGTH)
all_pressed__label = visual.TextStim(window, units=unit_type,
                                          text=u'All Pressed Keys:',
                                          pos=[LABEL_COLUMN_X,
                                               TEXT_ROWS_START_Y -
                                               TEXT_ROW_HEIGHT * 6],
                                          height=TEXT_STIM_HEIGHT,
                                          color=[-1, -1, -1],
                                          colorSpace='rgb', alignHoriz='left',
                                          alignVert='top',
                                          wrapWidth=LABEL_WRAP_LENGTH)

event_type_label = visual.TextStim(window, units=unit_type,
                                   text=u'Last Event Type:',
                                   pos=[LABEL_COLUMN_X,
                                        TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 7],

                                   height=TEXT_STIM_HEIGHT, color=[-1, -1, -1],
                                   colorSpace='rgb', alignHoriz='left',
                                   alignVert='top',
                                   wrapWidth=LABEL_WRAP_LENGTH)

psychopy_key_label = visual.TextStim(window, units=unit_type,
                                   text=u'event.getKeys():',
                                   pos=[LABEL_COLUMN_X,
                                        TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 8],

                                   height=TEXT_STIM_HEIGHT, color=[-1, -1, -1],
                                   colorSpace='rgb', alignHoriz='left',
                                   alignVert='top',
                                   wrapWidth=LABEL_WRAP_LENGTH)
psychopy_iohub_key_mismatch = visual.TextStim(window, units=unit_type,
                                   text=u'',
                                   pos=[0,
                                        TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 9],
                                   height=TEXT_STIM_HEIGHT, color=[1, -1, -1],
                                   colorSpace='rgb', alignHoriz='center',
                                   alignVert='top',
                                   wrapWidth=dw*2)

# dynamic stim
#
key_text_stim = visual.TextStim(window, units=unit_type, text=u'',
                                pos=[VALUE_COLUMN_X,
                                     TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 2],
                                height=TEXT_STIM_HEIGHT, color=[-1, -1, -1],
                                colorSpace='rgb',
                                alignHoriz='left', alignVert='top',
                                wrapWidth=VALUE_WRAP_LENGTH)
char_stim = visual.TextStim(window, units=unit_type, text=u'',
                            pos=[VALUE_COLUMN_X,
                                 TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 3],
                            height=TEXT_STIM_HEIGHT, color=[-1, -1, -1],
                            colorSpace='rgb',
                            alignHoriz='left', alignVert='top',
                            wrapWidth=VALUE_WRAP_LENGTH)
modifiers_stim = visual.TextStim(window, units=unit_type, text=u'',
                                 pos=[VALUE_COLUMN_X,
                                      TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 4],
                                 height=TEXT_STIM_HEIGHT,
                                 color=[-1, -1, -1], colorSpace='rgb',
                                 alignHoriz='left', alignVert='top',
                                 wrapWidth=VALUE_WRAP_LENGTH)
keypress_duration_stim = visual.TextStim(window, units=unit_type, text=u'',
                                         pos=[VALUE_COLUMN_X,
                                              TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 5],
                                         height=TEXT_STIM_HEIGHT,
                                         color=[-1, -1, -1],
                                         colorSpace='rgb', alignHoriz='left',
                                         alignVert='top',
                                         wrapWidth=VALUE_WRAP_LENGTH)
all_pressed_stim = visual.TextStim(window, units=unit_type, text=u'',
                                         pos=[VALUE_COLUMN_X,
                                              TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 6],
                                         height=TEXT_STIM_HEIGHT,
                                         color=[-1, -1, -1],
                                         colorSpace='rgb', alignHoriz='left',
                                         alignVert='top',
                                         wrapWidth=VALUE_WRAP_LENGTH)
event_type_stim = visual.TextStim(window, units=unit_type, text=u'',
                                  pos=[VALUE_COLUMN_X,
                                       TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 7],
                                  height=TEXT_STIM_HEIGHT, color=[-1, -1, -1],
                                  colorSpace='rgb', alignHoriz='left',
                                  alignVert='top',
                                  wrapWidth=VALUE_WRAP_LENGTH)

psychopy_key_stim = visual.TextStim(window, units=unit_type, text=u'',
                                  pos=[VALUE_COLUMN_X,
                                       TEXT_ROWS_START_Y - TEXT_ROW_HEIGHT * 8],
                                  height=TEXT_STIM_HEIGHT, color=[-1, -1, -1],
                                  colorSpace='rgb', alignHoriz='left',
                                  alignVert='top',
                                  wrapWidth=dw*2)

# Having all the stim to update / draw in a list makes drawing code
# more compact and reusable
STIM_LIST = [title_label, title2_label, key_text_label, char_label,
             modifiers_label, keypress_duration_label, all_pressed__label,
             event_type_label,psychopy_key_label,
             key_text_stim, char_stim, modifiers_stim, keypress_duration_stim,
             all_pressed_stim, event_type_stim,psychopy_key_stim,psychopy_iohub_key_mismatch]


# Clear all events from the global and device level ioHub Event Buffers.
#
io.clearEvents('all')

QUIT_EXP = False
demo_timeout_start = core.getTime()

# Loop until we get a CTRL+q event or until 120 seconds has passed 
#
import numpy as np

data = np.zeros(MAX_KEY_EVENT_COUNT)
i = 0
while QUIT_EXP is False:

    # Keep the ioHub global event buffer cleared since we are not using it.
    #  Not required, but does not hurt.
    #
    io.clearEvents()

    # Redraw stim and window flip...
    #n
    [s.draw() for s in STIM_LIST]
    flip_time = window.flip()
    # Update text fields based on all Keyboard Event types that have occurred
    # since the last call to getEvents of clearEvents(). This means that the most
    # recent event in the list of a given event type is what you will see.
    #
    t1 = core.getTime()
    events = keyboard.getKey()

    if len(events) > 0:
        t2 = core.getTime()
        d = (t2 - t1) * 1000.0
        data[i] = d
        i += 1
    if i == MAX_KEY_EVENT_COUNT:
        QUIT_EXP = True
        break

    for kbe in events:
        key_text_stim.setText(kbe.key)
        char_stim.setText(kbe.char)

        psychopy_keys = event.getKeys()
        psychopy_key=None
        if psychopy_keys:
            psychopy_key = psychopy_keys[0]
            psychopy_key_stim.setText(psychopy_key)
        if psychopy_key and psychopy_key != kbe.key:
            psychopy_iohub_key_mismatch.setText("Key Values !=: [%s] vs [%s]"%(kbe.key, psychopy_key))
        elif psychopy_key:
            psychopy_iohub_key_mismatch.setText("")

        modifiers_stim.setText(str(kbe.modifiers))
        all_pressed_stim.setText(str(keyboard.pressed.keys()))

        if kbe.type == "KEYBOARD_PRESS":
            keypress_duration_stim.setText("")
        else:
            keypress_duration_stim.setText("%.6f" % (kbe.duration))

        event_type_stim.setText(kbe.type)

        demo_timeout_start = kbe.time

        if (kbe.key.lower() == 'q' and (
                        'CONTROL_LEFT' in kbe.modifiers or 'CONTROL_LEFT' in kbe.modifiers)):
            QUIT_EXP = True
            break

    if flip_time - demo_timeout_start > 15.0:
        print "Ending Demo Due to 15 Seconds of Inactivity."
        break

        # Send a message to the iohub with the message text that a flip
        # occurred and what the mouse position was. Since we know the
        # psychopy-iohub time the flip occurred on, we can set that directly
        # in the event.
        #self.hub.sendMessageEvent("Flip %s"%(str(currentPosition),), sec_time=flip_time)

# Done demo loop, cleanup explicitly
#
io.quit()
window.close()


if i:
    from matplotlib import pyplot as plt
    plt.hist(data[:i], 50)
    plt.ylabel("Count")
    plt.xlabel("duration (msec)")
    plt.title("keyboard.getKeys() Execution Duration (msec)")
    plt.show()

