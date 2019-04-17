#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import

from psychopy import core, visual
from psychopy.gui.qtgui import infoDlg
from psychopy.iohub.client import launchHubServer

TRIAL_COUNT = 1

# Start ioHub event monitoring process, in this demo using the
# eyelink eyetracker.
# Note: No iohub config .yaml files are needed in this demo
# Since no experiment or session code is given, no iohub hdf5 file
# will be saved, but device events are still available at runtime.
#runtime_settings = dict()
#runtime_settings['sampling_rate'] = 500
#runtime_settings['track_eyes'] = 'RIGHT'
#iohub_config = {'eyetracker.hw.sr_research.eyelink.EyeTracker':
#                {'name': 'tracker',
#                 #'simulation_mode': True,
#                 'model_name': 'EYELINK 1000 DESKTOP',
#                 'runtime_settings': runtime_settings
#                 },
#
#                }

# Config the GazePoint 3 tracker for use.
iohub_config = {'eyetracker.hw.gazepoint.gp3.EyeTracker':
                {'name': 'tracker', 'device_timer': {'interval': 0.005}}}
                
# Uncomment experiment_code setting to enable saving data to hdf5 file.
iohub_config['experiment_code'] = 'et_simple'

io = launchHubServer(**iohub_config)

# Get some iohub devices for future access.
keyboard = io.devices.keyboard
display = io.devices.display
tracker = io.devices.tracker

infoDlg("Eye Tracker Setup", "Press OK to start\neye tracker setup / calibration procedure.")
    
# run eyetracker calibration
r = tracker.runSetupProcedure()
if isinstance(r,dict):
    # iohub-GP3 interface setup call returns the GP3 calibration results.
    # Ex: {u'LX5': 0.0, u'LX4': 0.0, u'LX3': 0.0, u'LX2': 0.0, u'LX1': 0.0,
    #      u'CALX1': 0.5, u'CALX3': 0.85, u'CALX2': 0.85, u'CALX5': 0.15,
    #      u'CALX4': 0.15, u'LV5': 0, u'LV4': 0, u'LV1': 0, u'LV3': 0,
    #      u'LV2': 0, u'RX1': 0.0, u'RX3': 0.0, u'RX2': 0.0,
    #       'type': u'CAL', u'RX4': 0.0, 
    #      u'LY4': 0.0, u'LY5': 0.0, u'LY1': 0.0, u'LY2': 0.0, u'LY3': 0.0,
    #      'SUMMARY': {u'AVE_ERROR': 1051.16, u'VALID_POINTS': 2, 
    #                  'type': u'ACK', u'ID': u'CALIBRATE_RESULT_SUMMARY'},
    #      u'RV3': 0, u'RV2': 0, u'RV1': 0, u'RV5': 0, u'RV4': 0, 
    #      u'CALY2': 0.15, u'CALY3': 0.85, u'CALY1': 0.5,
    #      u'ID': u'CALIB_RESULT', u'CALY4': 0.85, u'CALY5': 0.15, u'RX5': 0.0,
    #      u'RY4': 0.0, u'RY5': 0.0, u'RY2': 0.0, u'RY3': 0.0, u'RY1': 0.0}    
    
    # parse GP3 calibration results dict
    
    cal_avg_err = r.get('SUMMARY',{}).get('AVE_ERROR')
    num_val_calpt = r.get('SUMMARY',{}).get('VALID_POINTS')
    num_calpt = len([k for k in r.keys() if k.startswith('RV')])

    print("cal_avg_err /  num_calpt / num_val_calpt: {} / {} / {}".format(cal_avg_err, 
                                                                          num_val_calpt,
                                                                          num_calpt))
    
# Create a default PsychoPy Window and stim to use in trials
win = visual.Window(display.getPixelResolution(),
                    units='pix',
                    fullscr=True,
                    allowGUI=False
                    )

gaze_ok_region = visual.Circle(win, radius=200, units='pix')
gaze_dot = visual.GratingStim(win, tex=None, mask='gauss', pos=(0, 0),
                              size=(66, 66), color='green', units='pix')
text_stim_str = 'Eye Position: %.2f, %.2f. In Region: %s\nPress space key to start next trial.'
text_stim = visual.TextStim(win, text=text_stim_str,
                            pos=[0, int((-win.size[1]/2)*0.8)], height=24,
                            color='black', alignHoriz='center',
                            alignVert='center', wrapWidth=win.size[0] * .9)

# Run Trials.....
t = 0
while t < TRIAL_COUNT:
    io.clearEvents()
    tracker.setRecordingState(True)
    run_trial = True
    while run_trial is True:
        # Get the latest gaze position in display coord space..
        gpos = tracker.getLastGazePosition()

        # Update stim based on gaze position
        valid_gaze_pos = isinstance(gpos, (tuple, list))
        gaze_in_region = valid_gaze_pos and gaze_ok_region.contains(gpos)
        if valid_gaze_pos:
             #
            if gaze_in_region:
                gaze_in_region = 'Yes'
            else:
                gaze_in_region = 'No'
            text_stim.text = text_stim_str % (gpos[0], gpos[1], gaze_in_region)

           # If we have a gaze position from the tracker, update gc stim
            gaze_dot.setPos(gpos)
        else:
            # Otherwise just draw the background image.
            #
            ttxt_ = 'Eye Position: MISSING. In Region: No\n'
            ttxt_ += 'Press space key to start next trial.'
            text_stim.text = ttxt_
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
        if " " in keyboard.getPresses():
            run_trial = False

    # Current Trial is Done
    # Stop eye data recording
    tracker.setRecordingState(False)
    t += 1

# All Trials are done
# End experiment
win.close()
tracker.setConnectionState(False)
#io.quit()
#core.quit()
