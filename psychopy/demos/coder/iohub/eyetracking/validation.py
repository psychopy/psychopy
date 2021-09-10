#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Calibrate, validate, run with GC cursor demo / test.
Select which tracker to use by setting the TRACKER variable below.
"""

from psychopy import core, visual
from psychopy import iohub
from psychopy.iohub.client.eyetracker.validation import TargetStim
from psychopy.iohub.util import hideWindow, showWindow

# Eye tracker to use ('mouse', 'eyelink', 'gazepoint', or 'tobii')
TRACKER = 'mouse'

use_unit_type = 'height'
use_color_type = 'rgb'

eyetracker_config = dict(name='tracker')
devices_config = {}
if TRACKER == 'mouse':
    devices_config['eyetracker.hw.mouse.EyeTracker'] = eyetracker_config
    eyetracker_config['calibration'] = dict(auto_pace=True,
                                            target_duration=1.5,
                                            target_delay=1.0,
                                            screen_background_color=(0, 0, 0),
                                            type='NINE_POINTS',
                                            unit_type=None,
                                            color_type=None,
                                            target_attributes=dict(outer_diameter=0.05,
                                                                   inner_diameter=0.025,
                                                                   outer_fill_color=[-0.5, -0.5, -0.5],
                                                                   inner_fill_color=[-1, 1, -1],
                                                                   outer_line_color=[1, 1, 1],
                                                                   inner_line_color=[-1, -1, -1],
                                                                   animate=dict(enable=True,
                                                                                expansion_ratio=1.5,
                                                                                contract_only=False)
                                                                   )
                                            )
elif TRACKER == 'eyelink':
    eyetracker_config['model_name'] = 'EYELINK 1000 DESKTOP'
    eyetracker_config['simulation_mode'] = False
    eyetracker_config['runtime_settings'] = dict(sampling_rate=1000, track_eyes='RIGHT')
    eyetracker_config['calibration'] = dict(auto_pace=True,
                                            target_duration=1.5,
                                            target_delay=1.0,
                                            screen_background_color=(0, 0, 0),
                                            type='NINE_POINTS',
                                            unit_type=None,
                                            color_type=None,
                                            target_attributes=dict(outer_diameter=0.05,
                                                                   inner_diameter=0.025,
                                                                   outer_fill_color=[-0.5, -0.5, -0.5],
                                                                   inner_fill_color=[-1, 1, -1],
                                                                   outer_line_color=[1, 1, 1],
                                                                   inner_line_color=[-1, -1, -1]
                                                                   )
                                            )
    devices_config['eyetracker.hw.sr_research.eyelink.EyeTracker'] = eyetracker_config
elif TRACKER == 'gazepoint':
    eyetracker_config['device_timer'] = {'interval': 0.005}
    eyetracker_config['calibration'] = dict(use_builtin=False,
                                            target_duration=1.5,
                                            target_delay=1.0,
                                            screen_background_color=(0,0,0),
                                            type='NINE_POINTS',
                                            unit_type=None,
                                            color_type=None,
                                            target_attributes=dict(outer_diameter=0.05,
                                                                   inner_diameter=0.025,
                                                                   outer_fill_color=[-0.5, -0.5, -0.5],
                                                                   inner_fill_color=[-1, 1, -1],
                                                                   outer_line_color=[1, 1, 1],
                                                                   inner_line_color=[-1, -1, -1],
                                                                   animate=dict(enable=True,
                                                                                expansion_ratio=1.5,
                                                                                contract_only=False)
                                                                   )
                                            )
    devices_config['eyetracker.hw.gazepoint.gp3.EyeTracker'] = eyetracker_config
elif TRACKER == 'tobii':
    eyetracker_config['calibration'] = dict(auto_pace=True,
                                            target_duration=1.5,
                                            target_delay=1.0,
                                            screen_background_color=(0, 0, 0),
                                            type='NINE_POINTS',
                                            unit_type=None,
                                            color_type=None,
                                            target_attributes=dict(outer_diameter=0.05,
                                                                   inner_diameter=0.025,
                                                                   outer_fill_color=[-0.5, -0.5, -0.5],
                                                                   inner_fill_color=[-1, 1, -1],
                                                                   outer_line_color=[1, 1, 1],
                                                                   inner_line_color=[-1, -1, -1],
                                                                   animate=dict(enable=True,
                                                                                expansion_ratio=1.5,
                                                                                contract_only=False)
                                                                   )
                                            )
    devices_config['eyetracker.hw.tobii.EyeTracker'] = eyetracker_config
else:
    print("{} is not a valid TRACKER name; please use 'mouse', 'eyelink', 'gazepoint', or 'tobii'.".format(TRACKER))
    core.quit()

# Number if 'trials' to run in demo
TRIAL_COUNT = 2
# Maximum trial time / time timeout
T_MAX = 60.0
win = visual.Window((1920, 1080),
                    units=use_unit_type,
                    fullscr=True,
                    allowGUI=False,
                    colorSpace=use_color_type,
                    monitor='55w_60dist',
                    color=[0, 0, 0]
                    )

win.setMouseVisible(False)
text_stim = visual.TextStim(win, text="Start of Experiment",
                            pos=[0, 0], height=24,
                            color='black', units='pix', colorSpace='named',
                            wrapWidth=win.size[0] * .9)

text_stim.draw()
win.flip()

# Since no experiment_code or session_code is given, no iohub hdf5 file
# will be saved, but device events are still available at runtime.
io = iohub.launchHubServer(window=win, **devices_config)

# Get some iohub devices for future access.
keyboard = io.getDevice('keyboard')
tracker = io.getDevice('tracker')

# Minimize the PsychoPy window if needed
hideWindow(win)
# Display calibration gfx window and run calibration.
result = tracker.runSetupProcedure()
print("Calibration returned: ", result)
# Maximize the PsychoPy window if needed
showWindow(win)

# Validation

# Create a target stim. iohub.client.eyetracker.validation.TargetStim provides a standard doughnut style
# target. Or use any stim that has `.setPos()`, `.radius`, `.innerRadius`, and `.draw()`.
target_stim = TargetStim(win, radius=0.025, fillcolor=[.5, .5, .5], edgecolor=[-1, -1, -1], edgewidth=2,
                         dotcolor=[1, -1, -1], dotradius=0.005, units=use_unit_type, colorspace=use_color_type)

# target_positions: Provide your own list of validation positions,
# target_positions = [(0.0, 0.0), (0.85, 0.85), (-0.85, 0.0), (0.85, 0.0), (0.85, -0.85), (-0.85, 0.85),
#                    (-0.85, -0.85), (0.0, 0.85), (0.0, -0.85)]
target_positions = 'FIVE_POINTS'

# Create a validation procedure, iohub must already be running with an
# eye tracker device, or errors will occur.
validation_proc = iohub.ValidationProcedure(win,
                                            target=target_stim,  # target stim
                                            positions=target_positions,  # string constant or list of points
                                            randomize_positions=True,  # boolean
                                            expand_scale=1.5,  # float
                                            target_duration=1.5,  # float
                                            target_delay=1.0,  # float
                                            enable_position_animation=True,
                                            color_space=use_color_type,
                                            unit_type=use_unit_type,
                                            progress_on_key="",  # str or None
                                            gaze_cursor=(-1.0, 1.0, -1.0),  # None or color value
                                            show_results_screen=True,  # bool
                                            save_results_screen=False,  # bool, only used if show_results_screen == True
                                            )

# Run the validation procedure. run() does not return until the validation is complete.
validation_proc.run()
if validation_proc.results:
    results = validation_proc.results
    print("++++ Validation Results ++++")
    print("Passed:", results['passed'])
    print("failed_pos_count:", results['positions_failed_processing'])
    print("Units:", results['reporting_unit_type'])
    print("min_error:", results['min_error'])
    print("max_error:", results['max_error'])
    print("mean_error:", results['mean_error'])
else:
    print("Validation Aborted by User.")

# Run Trials.....

gaze_ok_region = visual.Circle(win, lineColor='black', radius=0.33, units=use_unit_type, colorSpace='named')

gaze_dot = visual.GratingStim(win, tex=None, mask='gauss', pos=(0, 0),
                              size=(0.02, 0.02), color='green', colorSpace='named', units=use_unit_type)

text_stim_str = 'Eye Position: %.2f, %.2f. In Region: %s\n'
text_stim_str += 'Press space key to start next trial.'
missing_gpos_str = 'Eye Position: MISSING. In Region: No\n'
missing_gpos_str += 'Press space key to start next trial.'
text_stim.setText(text_stim_str)

t = 0
while t < TRIAL_COUNT:
    io.clearEvents()
    tracker.setRecordingState(True)
    run_trial = True
    tstart_time = core.getTime()
    while run_trial is True:
        # Get the latest gaze position in display coord space.
        gpos = tracker.getLastGazePosition()
        # Update stim based on gaze position
        valid_gaze_pos = isinstance(gpos, (tuple, list))
        gaze_in_region = valid_gaze_pos and gaze_ok_region.contains(gpos)
        if valid_gaze_pos:
            # If we have a gaze position from the tracker, update gc stim and text stim.
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
        if keyboard.getPresses(keys=' '):
            run_trial = False
        elif core.getTime()-tstart_time > T_MAX:
            run_trial = False
    win.flip()
    # Current Trial is Done
    # Stop eye data recording
    tracker.setRecordingState(False)
    t += 1

# All Trials are done
# End experiment
tracker.setConnectionState(False)
core.quit()
