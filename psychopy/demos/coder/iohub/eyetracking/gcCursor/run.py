#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Demonstrates use of ioHub and the ioHub Common EyeTracking Interface within a
very simple psychopy exeriment script:
    1) Load an xlsx file containing the trial conditions for use
       during the experiment. All DV's and IV's to be used or updated
       for each trial must be specified as columns in the xlsx file.
    2) Start the ioHub Server and inform it of the trial conditions to be used.
       The ioHub Server will create an experiment specific results table in
       the ioHub HDF5 file, with a column for each DV and IV defined in the
       xls file.
    3) Calibrate the eye tracker.
    4) Create the experiment runtime graphics, including creating a cache of
       images to be displayed for each trial of the experiment.
    5) Run a set of trials. Each trial sequence consists of:
           a) The participant pressing the SPACE key to start the trial.
           b) Randomly displaying one of the background images for a trial.
           c) Starting recording of data from the eye tracker.
           d) Displaying a gaze contingent dot located at the gaze position
              reported by the eye tracker for each display frame.
           e) Ending each trial by pressing the SPACE key.
           f) Sending the condition variable values for that trial
              to the ioHub Server, which will be saved in the trial condition
              variables table of the ioHub hdf5 file.
           g) Stopping of event recording on the eye tracker device.

ioHub Device configuration is read from the iohub_config.yaml file, which
contains commented out settings for each of the different iohub eye tracker
interfaces. Before using the demo this file must be edited:
    - uncomment the settings for the eye tracker that will be used
    - change any settings for the specific model being used.
"""
from __future__ import division, print_function, absolute_import

import os

from psychopy import core, visual
from psychopy.data import TrialHandler, importConditions
from psychopy.iohub.client import launchHubServer

# Start ioHub
io = launchHubServer(experiment_code='gccursor_demo',
                     iohub_config_name='iohub_config.yaml')

# Read trial conditions file
exp_conditions = importConditions('trial_conditions.xlsx')
trials = TrialHandler(exp_conditions, 1)

# Inform the ioDataStore that the experiment is using a
# TrialHandler. The ioDataStore will create a table
# which can be used to record the actual trial variable values (DV or IV)
# in the order run / collected.
#
io.createTrialHandlerRecordTable(trials)

# Let's make some short-cuts to the devices we will be using
# in this demo.
display = io.devices.display
kb = io.devices.keyboard
mouse = io.devices.mouse
try:
    tracker = io.devices.tracker
except Exception:
    # No eye tracker config found in iohub_config.yaml
    from psychopy.gui.qtgui import criticalDlg
    md = criticalDlg('No Eye Tracker Configuration Found',
                     'Update the iohub_config.yaml file by '
                     'uncommenting\nthe appropriate eye tracker '
                     'config lines.\n\nPress OK to exit demo.')
    io.quit()
    core.quit()

# Start the eye tracker setup / calibration procedure.
tracker.runSetupProcedure()

# Create a psychopy window for the experiment graphics,
# ioHub supports the use of one full screen window during
# the experiment runtime. (If you are using a window at all).
#
# Current pixel resolution of the Display to be used
res = display.getPixelResolution()
coord_type = display.getCoordinateType()
# name of the PsychoPy Monitor Config file if used.
psychopy_mon_conf_file = display.getPsychopyMonitorName()
window = visual.Window(res,
                       monitor=psychopy_mon_conf_file,
                       units=coord_type,  # coordinate space to use.
                       fullscr=True,  # We need full screen mode.
                       allowGUI=False,  # We want it to be borderless
                       # The display index to use for fullscreen window.
                       screen=display.getIndex()
                       )

# Create a dict of image stim for trials and a gaze blob to show the
# reported gaze position with.
#
image_cache = dict()
image_names = [
    'canal.jpg',
    'fall.jpg',
    'party.jpg',
    'swimming.jpg',
    'lake.jpg']
for iname in image_names:
    img_path = os.path.join('./images/', iname)
    image_cache[iname] = visual.ImageStim(window, image=img_path, name=iname,
                                          units=coord_type)

# Create a circle to use for the Gaze Cursor. Current units assume pix.
#
gaze_dot = visual.GratingStim(window, tex=None, mask='gauss', pos=(0, 0),
                              size=(66, 66), color='green', units=coord_type)

# Create a Text Stim for use on /instuction/ type screens.
# Current units assume pix.
instructions_text_stim = visual.TextStim(window, text='', pos=[0, 0],
                                         height=24, color=[-1, -1, -1],
                                         colorSpace='rgb',
                                         alignHoriz='center',
                                         alignVert='center',
                                         wrapWidth=window.size[0] * .9)

# Update Instruction Text and display on screen.
# Send Message to ioHub DataStore with Exp. Start Screen display time.
#
instuction_text = 'Press Any Key to Start Experiment.'
instructions_text_stim.setText(instuction_text)
instructions_text_stim.draw()
flip_time = window.flip()
io.sendMessageEvent(text='EXPERIMENT_START', sec_time=flip_time)

# Wait until a key event occurs after the instructions are displayed
io.clearEvents()
kb.waitForPresses()

# Send some information to the ioHub hdf5 file as experiment messages,
# including the window's calculated pixels per degree, display resolution, etc.
#
io.sendMessageEvent(text='IO_HUB EXPERIMENT_INFO START')

msg_proto_ = 'Stimulus Screen ID: {0}, Size (pixels): {1}, CoordType: {2}'
msg_txt_ = msg_proto_.format(display.getIndex(), display.getPixelResolution(),
                             display.getCoordinateType())
io.sendMessageEvent(text=msg_txt_)

msg_proto_ = 'Calculated Pixels Per Degree: {0} x, {1} y'
msg_txt_ = msg_proto_.format(*display.getPixelsPerDegree())
io.sendMessageEvent(text=msg_txt_)

io.sendMessageEvent(text='IO_HUB EXPERIMENT_INFO END')

io.clearEvents()

# For each trial in the set of trials within the current block
# (there is only 1 in the demo).
#
t = 0
for trial in trials:
    # Update the instruction screen text to indicate
    # a trial is about to start.
    #
    instuction_text = 'Press Space Key To Start Trial %d' % t
    instructions_text_stim.setText(instuction_text)
    instructions_text_stim.draw()
    flip_time = window.flip()

    # Send an experiment msg with the display time for the trial's instruction
    # screen.
    io.sendMessageEvent(text='INSTRUCTIONS_START', sec_time=flip_time)

    # Wait until a space key press event occurs after the
    # start trial instuctions have been displayed.
    #
    io.clearEvents()
    kb.waitForPresses(keys=' ')

    # Space Key has been pressed, start the trial.
    # Set the current session and trial id values to be saved
    # in the ioDataStore for the upcoming trial.
    #
    trial['trial_id'] = t + 1

    io.sendMessageEvent(text='RECORDING_START')

    # Start Recording Eye Data
    #
    tracker.setRecordingState(True)

    # Get the image stim for this trial.
    #
    imageStim = image_cache[trial['IMAGE_NAME']]
    imageStim.draw()
    flip_time = window.flip()
    # Clear all the events received prior to the trial start.
    #
    io.clearEvents()

    # Send a msg to the ioHub indicating that the trial started,
    # and the time of the first retrace displaying the trial stim.
    #
    io.sendMessageEvent(text='TRIAL_START: %s' % trial['IMAGE_NAME'],
                        sec_time=flip_time)

    # Set the value of the trial start variable for this trial
    #
    trial['TRIAL_START'] = flip_time

    # Loop until we get a keyboard event
    #
    run_trial = True
    while run_trial is True:
        # Get the latest gaze position in display coord space..
        #
        gpos = tracker.getPosition()
        if gpos:
            # If we have a gaze position from the tracker,
            # redraw the background image and then the
            # gaze_cursor at the current eye position.
            #
            gaze_dot.setPos([gpos[0], gpos[1]])
            imageStim.draw()
            gaze_dot.draw()
        else:
            # Otherwise just draw the background image.
            # This will remove the gaze cursor from the screen
            # when the eye tracker is not successfully
            # tracking eye position.
            #
            imageStim.draw()

        # Flip video buffers, displaying the stim we just
        # updated.
        #
        flip_time = window.flip()

        # Send an experiment message to the ioDataStore
        # indicating the time the image was drawn and
        # current position of gaze spot.
        #
        if gpos:
            io.sendMessageEvent('GAZE_UPDATE: %.3f %.3f' % (gpos[0], gpos[1]),
                                sec_time=flip_time)
        else:
            io.sendMessageEvent('IMAGE_UPDATE: NO GAZE', sec_time=flip_time)

        # Check any new keyboard press events by a space key.
        # If one is found, set the trial end variable and break.
        # from the loop
        if kb.getPresses(keys=[' ', ]):
            run_trial = False
            break

    # The trial has ended, so update the trial end time condition value,
    # and send a message to the ioDataStore with the trial end time.
    #
    flip_time = window.flip()
    trial['TRIAL_END'] = flip_time
    io.sendMessageEvent(text='TRIAL_END %d' % t, sec_time=flip_time)

    # Stop recording eye data.
    # In this example, we have no use for any eye data
    # between trials, so why save it.
    #
    tracker.setRecordingState(False)

    # Save the experiment condition variable values for this
    # trial to the ioHub hdf5 file.
    #
    io.addTrialHandlerRecord(trial.values())

    # Clear all event buffers
    #
    io.clearEvents()
    t += 1

# All trials have been run, so end the experiment.
#
window.flip()
io.sendMessageEvent(text='EXPERIMENT_COMPLETE')

# Disconnect the eye tracking device.
#
tracker.setConnectionState(False)

# The experiment is done, all trials have been run.
# Clear the screen and show an 'experiment  done' message using the
# instructionScreen text.
#
instuction_text = 'Press Any Key to Exit Demo'
instructions_text_stim.setText(instuction_text)
instructions_text_stim.draw()
flip_time = window.flip()
io.sendMessageEvent(text='SHOW_DONE_TEXT', sec_time=flip_time)
io.clearEvents()
# wait until any key is pressed
kb.waitForPresses()

io.quit()
core.quit()

