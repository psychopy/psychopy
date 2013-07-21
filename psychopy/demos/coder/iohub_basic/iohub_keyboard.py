# -*- coding: utf-8 -*-
"""
iohub_keyboard.py

Displays event information from ioHub Keyboard Events. 

Inital Version: May 6th, 2013, Sol Simpson
Updated June 22nd: Added demo timeout. SS
"""
from psychopy import core, visual
from psychopy.iohub import launchHubServer,EventConstants 


# launchHubServer is a fucntion that can be used to create an instance of the 
#   ioHub Process within a procedural PsychoPy Script and without the need for
#   external configuration files. It is useful when devices like the Keyboard,
#   Mouse, Display, and Experiment are all that is needed. By default the
#   Display device will use pixel units and display index 0 of a multimonitor setup.
#   The returned 'io' variable gives access to the ioHub Process.
#
io=launchHubServer(experiment_code='key_evts',psychopy_monitor_name='default')

# Devices that have been created on the ioHub Process and will be monitored
# for events during the experiment can be accessed via the io.devices.* attribute.
#
# save some 'dots' during the trial loop
#
display = io.devices.display
keyboard = io.devices.keyboard
mouse=io.devices.mouse

# Hide the 'system mouse cursor'.
mouse.setSystemCursorVisibility(False)

# Get settings needed to create the PsychoPy full screen window.
#   - display_resolution: the current resolution of diplsay specified by the screen_index.
#       Using this to create your full screen window stops the warniong about the
#       resolution entered does not match the full screen size that PsychoPy will generate.
#   - unit_type: same as PsychoPy units.
#   - screen_index: specifies what Display to use in a multi monitor setup. Default is 0. 
#
display_resolution=display.getPixelResolution()
unit_type=display.getCoordinateType()
screen_index=display.getIndex()

# ioHub currently supports the use of 'one', 'full screen' PsychoPy Window
# for stimulus presentation. Let's create one....
#
window=visual.Window(display_resolution, 
                        units=unit_type,
                        color=[128,128,128], colorSpace='rgb255',
                        fullscr=True, allowGUI=False,
                        screen=screen_index
                        )                 

# constants for text element spacing:
TEXT_STIM_HEIGHT=38
TEXT_ROW_HEIGHT=60   
LABEL_COLUMN_X=-300
VALUE_COLUMN_X=100
LABEL_WRAP_LENGTH=(VALUE_COLUMN_X-LABEL_COLUMN_X)*.9             
VALUE_WRAP_LENGTH=(display_resolution[0]/2-VALUE_COLUMN_X)*.9             
ROW_COUNT=5
TEXT_ROWS_START_Y=(ROW_COUNT*TEXT_ROW_HEIGHT)/2

# Create some psychoPy stim to display the keyboard events received...
#
# field labels:
title_label = visual.TextStim(window, units=unit_type, text=u'Press CTRL + Q to Exit Demo', 
                         pos = [0,display_resolution[1]/4], height=TEXT_STIM_HEIGHT, 
                         color=[0.5,0.2,0.5], colorSpace='rgb',alignHoriz='center',
                         alignVert='center',wrapWidth=display_resolution[0])
title2_label = visual.TextStim(window, units=unit_type, text=u'Press and Releases Keys for ioHub KB Event Details', 
                         pos = [0,display_resolution[1]/3], height=TEXT_STIM_HEIGHT+1.5, 
                         color=[-0.5,0.5,0.5], colorSpace='rgb',alignHoriz='center',
                         alignVert='center',wrapWidth=display_resolution[0])
key_text_label = visual.TextStim(window, units=unit_type, text=u'event.key:', 
                         pos = [LABEL_COLUMN_X,TEXT_ROWS_START_Y-TEXT_ROW_HEIGHT*0], height=TEXT_STIM_HEIGHT, 
                         color=[-1,-1,-1], colorSpace='rgb',alignHoriz='left',
                         alignVert='top',wrapWidth=LABEL_WRAP_LENGTH)
ucode_label = visual.TextStim(window, units=unit_type, text=u'event.ucode:', 
                         pos = [LABEL_COLUMN_X,TEXT_ROWS_START_Y-TEXT_ROW_HEIGHT*1], height=TEXT_STIM_HEIGHT, 
                         color=[-1,-1,-1], colorSpace='rgb',alignHoriz='left',
                         alignVert='top',wrapWidth=LABEL_WRAP_LENGTH)
modifiers_label = visual.TextStim(window, units=unit_type, text=u'event.modifiers', 
                         pos = [LABEL_COLUMN_X,TEXT_ROWS_START_Y-TEXT_ROW_HEIGHT*2], height=32, color=[-1,-1,-1], colorSpace='rgb', 
                         alignHoriz='left',alignVert='top', wrapWidth=LABEL_WRAP_LENGTH)
keypress_duration_label = visual.TextStim(window,units=unit_type, text=u'Last Pressed Duration:', 
                         pos = [LABEL_COLUMN_X,TEXT_ROWS_START_Y-TEXT_ROW_HEIGHT*3], height=32, color=[-1,-1,-1], 
                         colorSpace='rgb', alignHoriz='left',alignVert='top',
                         wrapWidth=LABEL_WRAP_LENGTH)
event_type_label = visual.TextStim(window,units=unit_type, text=u'Last Event Type:', 
                         pos = [LABEL_COLUMN_X,TEXT_ROWS_START_Y-TEXT_ROW_HEIGHT*4], height=TEXT_STIM_HEIGHT, color=[-1,-1,-1], 
                         colorSpace='rgb', alignHoriz='left',alignVert='top',
                         wrapWidth=LABEL_WRAP_LENGTH)
# dynamic stim
#
key_text_stim = visual.TextStim(window, units=unit_type, text=u'', 
                         pos = [VALUE_COLUMN_X,TEXT_ROWS_START_Y-TEXT_ROW_HEIGHT*0], 
                         height=TEXT_STIM_HEIGHT, color=[-1,-1,-1], colorSpace='rgb',
                         alignHoriz='left', alignVert='top',wrapWidth=VALUE_WRAP_LENGTH)
ucode_stim = visual.TextStim(window, units=unit_type, text=u'', 
                         pos = [VALUE_COLUMN_X,TEXT_ROWS_START_Y-TEXT_ROW_HEIGHT*1], 
                         height=TEXT_STIM_HEIGHT, color=[-1,-1,-1], colorSpace='rgb',
                         alignHoriz='left', alignVert='top',wrapWidth=VALUE_WRAP_LENGTH)
modifiers_stim = visual.TextStim(window, units=unit_type, text=u'', 
                         pos = [VALUE_COLUMN_X,TEXT_ROWS_START_Y-TEXT_ROW_HEIGHT*2], 
                         height=TEXT_STIM_HEIGHT*.66, color=[-1,-1,-1], colorSpace='rgb',
                         alignHoriz='left',alignVert='top', wrapWidth=VALUE_WRAP_LENGTH)
keypress_duration_stim = visual.TextStim(window,units=unit_type, text=u'', 
                         pos = [VALUE_COLUMN_X,TEXT_ROWS_START_Y-TEXT_ROW_HEIGHT*3], height=TEXT_STIM_HEIGHT, color=[-1,-1,-1],
                         colorSpace='rgb', alignHoriz='left',alignVert='top',
                         wrapWidth=VALUE_WRAP_LENGTH)
event_type_stim = visual.TextStim(window,units=unit_type, text=u'', 
                         pos = [VALUE_COLUMN_X,TEXT_ROWS_START_Y-TEXT_ROW_HEIGHT*4], height=TEXT_STIM_HEIGHT, color=[-1,-1,-1], 
                         colorSpace='rgb', alignHoriz='left',alignVert='top',
                         wrapWidth=VALUE_WRAP_LENGTH)

# Having all the stim to update / draw in a list makes drawing code more compact and reusable
STIM_LIST=[title_label,title2_label,key_text_label,ucode_label,modifiers_label,keypress_duration_label,event_type_label,
           key_text_stim,ucode_stim,modifiers_stim,keypress_duration_stim,event_type_stim]  


# Clear all events from the global and device level ioHub Event Buffers.
#
io.clearEvents('all')
        
QUIT_EXP=False
demo_timeout_start=core.getTime()

# Loop until we get a CTRL+q event or until 120 seconds has passed 
#
while QUIT_EXP is False:
    
    # Keep the ioHub global event buffer cleared since we are not using it.
    #  Not required, but does not hurt.
    #
    io.clearEvents()
    
    # Redraw stim and window flip...
    #
    [s.draw() for s in STIM_LIST]
    flip_time=window.flip()

    # Update text fields based on all Keyboard Event types that have occurred
    # since the last call to getEvents of clearEvents(). This means that the most
    # recent event in the list of a given event type is what you will see.
    #    
    for event in keyboard.getEvents():
        #print 'KB EVT: ',  event, '\n'
        key_text_stim.setText(event.key)
        ucode_stim.setText('{0:#06x} = {1}'.format(event.ucode,unichr(event.ucode)))
        modifiers_stim.setText(str(event.modifiers))
        if event.type == EventConstants.KEYBOARD_CHAR:
            keypress_duration_stim.setText("%.6f"%(event.duration))
        event_type_stim.setText(EventConstants.getName(event.type))

        demo_timeout_start=event.time
    
        if (event.key.lower()=='q' and ('CONTROL_LEFT' in event.modifiers or 'CONTROL_LEFT' in event.modifiers)):
            QUIT_EXP=True
            break
        
    if flip_time-demo_timeout_start>15.0:
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
