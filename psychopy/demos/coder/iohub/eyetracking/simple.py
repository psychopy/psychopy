#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simple iohub eye tracker device demo. Shows how monitoring for central
fixation monitoring could be done.
No iohub config .yaml files are needed for this demo.
Demo config is setup for an EyeLink(C) 1000 Desktop System. 
To to use a different eye tracker implementation, change the 
iohub_tracker_class_path and eyetracker_config dict script variables.
"""
from __future__ import absolute_import, division, print_function

from psychopy import core, visual
from psychopy.iohub.client import launchHubServer
import time

# Number if 'trials' to run in demo
TRIAL_COUNT = 2
# Maximum trial time / time timeout
T_MAX = 10.0

iohub_tracker_class_path = 'eyetracker.hw.sr_research.eyelink.EyeTracker'
eyetracker_config = dict()
eyetracker_config['name'] = 'tracker'
eyetracker_config['model_name'] = 'EYELINK 1000 DESKTOP'
eyetracker_config['simulation_mode'] = True
eyetracker_config['runtime_settings'] = dict(sampling_rate=1000,
                                             track_eyes='RIGHT')

# Since no experiment or session code is given, no iohub hdf5 file
# will be saved, but device events are still available at runtime.
io = launchHubServer(**{iohub_tracker_class_path: eyetracker_config})

# Get some iohub devices for future access.
keyboard = io.getDevice('keyboard')
display = io.getDevice('display')
tracker = io.getDevice('tracker')

# run eyetracker calibration
tracker.runSetupProcedure()

win = visual.Window(display.getPixelResolution(),
                    units='pix',
                    fullscr=True,
                    allowGUI=False
                    )

gaze_ok_region = visual.Circle(win, radius=200, units='pix')

gaze_dot = visual.GratingStim(win, tex=None, mask='gauss', pos=(0, 0),
                              size=(66, 66), color='green', units='pix')

text_stim_str = 'Eye Position: %.2f, %.2f. In Region: %s\n'
text_stim_str += 'Press space key to start next trial.'
missing_gpos_str = 'Eye Position: MISSING. In Region: No\n'
missing_gpos_str += 'Press space key to start next trial.'
text_stim = visual.TextStim(win, text=text_stim_str,
                            pos=[0, int((-win.size[1]/2)*0.8)], height=24,
                                 color='black',
                                 alignHoriz='center',
                                 alignVert='center', 
                                 wrapWidth=win.size[0] * .9)

# Run Trials.....
t = 0
while t < TRIAL_COUNT:
    io.clearEvents()
    tracker.setRecordingState(True)
    run_trial = True
    tstart_time = core.getTime()
    while run_trial is True:
        # Get the latest gaze position in dispolay coord space..
        gpos = tracker.getLastGazePosition()
        #print("gpos:",gpos)
        # Update stim based on gaze position
        valid_gaze_pos = isinstance(gpos, (tuple, list))
        gaze_in_region = valid_gaze_pos and gaze_ok_region.contains(gpos)
        if valid_gaze_pos:
            # If we have a gaze position from the tracker, update gc stim
            # and text stim.
            if gaze_in_region:
                gaze_in_region = 'Yes'
            else:
                gaze_in_region = 'No'
            text_stim.text = text_stim_str % (gpos[0], gpos[1], gaze_in_region)

            gaze_dot.setPos(gpos)
        else:
            # Otherwise just update text stim
            text_stim.text = missing_gpos_str

        # Redraw stim
        gaze_ok_region.draw()
        text_stim.draw()
        if valid_gaze_pos:
            gaze_dot.draw()

        # Display updated stim on screen.
        flip_time = win.flip()

        # Check any new keyboard char events for a space key.
        # If one is found, set the trial end variable.
        #
        #if keyboard.getEvents():
        if core.getTime()-tstart_time > T_MAX:
            run_trial = False

    # Current Trial is Done
    # Stop eye data recording
    tracker.setRecordingState(False)
    t += 1

# All Trials are done
# End experiment
tracker.setConnectionState(False)

io.quit()
#core.quit()
