# -*- coding: utf-8 -*-
"""
iohub_keyboard.py

Displays information from ioHub Keyboard Events
vs. psychopy.event.geKeys().
"""
WINDOW_SIZE = 1024,768

from psychopy import core, visual, event
from psychopy.iohub import launchHubServer

# Start iohub process. The iohub process can be accessed using the 'io' variable.
io = launchHubServer()

# Creating a 'keyboard' variable that is used to access the iohub Keyboard device.
keyboard = io.devices.keyboard

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
                              text=u'Press "Q" Key to Exit Demo',
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
             all_pressed_stim, event_type_stim,psychopy_key_stim]


# Clear all events from the global and device level ioHub Event Buffers.
#
io.clearEvents('all')

QUIT_EXP = False
demo_timeout_start = core.getTime()

# Loop until we get a 'escape' key is pressed,
# or until 15 seconds passed since last keyboard event.
#
while QUIT_EXP is False:
    # Redraw stim and window flip...
    [s.draw() for s in STIM_LIST]
    flip_time = window.flip()

    events = keyboard.getKeys()

    for kbe in events:
        key_text_stim.setText(kbe.key)
        char_stim.setText(kbe.char)

        psychopy_keys = event.getKeys()
        if psychopy_keys:
            psychopy_key_stim.setText(psychopy_keys[0])
        elif kbe.type == "KEYBOARD_PRESS":
            psychopy_key_stim.setText('')

        modifiers_stim.setText(str(kbe.modifiers))
        all_pressed_stim.setText(str(keyboard.state.keys()))

        if kbe.type == "KEYBOARD_PRESS":
            keypress_duration_stim.setText("")
        else:
            keypress_duration_stim.setText("%.6f" % (kbe.duration))

        event_type_stim.setText(kbe.type)

        demo_timeout_start = kbe.time

        # Note that keyboard events can be compared to a string, matching when
        # the event.key or .char == basestring value.
        if kbe == 'q':
            QUIT_EXP = True
            break

    if flip_time - demo_timeout_start > 15.0:
        print "Ending Demo Due to 15 Seconds of Inactivity."
        break

core.quit()