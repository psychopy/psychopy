#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example of performing eye tracker validation using the ioHub Common Eye Tracker interface
and the psychopy.iohub.client.eyetracker.validation.ValidationProcedure class.
"""
import time
from psychopy import visual
from psychopy.iohub import launchHubServer
from psychopy.iohub.client.eyetracker.validation import TargetStim, ValidationProcedure

if __name__ == "__main__":
    # Create a default PsychoPy Window
    # monitor *must* be the name of a valid PsychoPy Monitor config file.
    win = visual.Window((1920, 1080), fullscr=True, allowGUI=False, monitor='55w_60dist')

    # Create ioHub Server config ....
    sess_code = 'S_{0}'.format(int(time.mktime(time.localtime())))
    iohub_config = dict(experiment_code='validation_demo', session_code=sess_code)
    # Add an eye tracker device
    iohub_config['eyetracker.hw.mouse.EyeTracker'] = dict(name='tracker')

    # Start the ioHub process.
    io = launchHubServer(window=win, **iohub_config)

    # Get the eye tracker device.
    tracker = io.devices.tracker

    # Run eyetracker calibration
    r = tracker.runSetupProcedure()

    # ValidationProcedure setup

    # Create a target stim. iohub.client.eyetracker.validation.TargetStim provides a standard doughnut style
    # target. Or use any stim that has `.setPos()`, `.setRadius()`, and `.draw()` methods.
    target_stim = TargetStim(win, radius=0.025, fillcolor=[.5, .5, .5], edgecolor=[-1, -1, -1], edgewidth=2,
                             dotcolor=[1, -1, -1], dotradius=0.005, units='norm', colorspace='rgb')

    # target_positions: Provide your own list of validation positions,
    # or use the PositionGrid class to generate a set.
    target_positions = [(0.0, 0.0), (0.85, 0.85), (-0.85, 0.0), (0.85, 0.0), (0.85, -0.85), (-0.85, 0.85),
                        (-0.85, -0.85), (0.0, 0.85), (0.0, -0.85)]

    # Create a validation procedure, iohub must already be running with an
    # eye tracker device, or errors will occur.
    validation_proc = ValidationProcedure(win,
                                          target=target_stim,
                                          positions=target_positions,
                                          randomize_positions=False,
                                          target_animation=dict(velocity=1.0,
                                                                expandedscale=3.0,
                                                                expansionduration=0.2,
                                                                contractionduration=0.4),
                                          accuracy_period_start=0.550,
                                          accuracy_period_stop=.150,
                                          show_intro_screen=True,
                                          intro_text='Eye Tracker Validation Procedure.',
                                          show_results_screen=True,
                                          results_in_degrees=True,
                                          save_results_screen=True,
                                          toggle_gaze_cursor_key='g',
                                          terminate_key='escape')

    # Run the validation procedure. run() does not return until the validation is complete.
    validation_results = validation_proc.run()
    if validation_results:
        print("++++ Validation Results ++++")
        print("Passed:", validation_results['passed'])
        print("failed_pos_count:", validation_results['positions_failed_processing'])
        print("Units:", validation_results['reporting_unit_type'])
        print("min_error:", validation_results['min_error'])
        print("max_error:", validation_results['max_error'])
        print("mean_error:", validation_results['mean_error'])
    else:
        print("Validation Aborted by User.")
    io.quit()
