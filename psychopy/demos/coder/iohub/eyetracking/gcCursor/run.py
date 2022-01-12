#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gc_cursor_demo/run.py

Demonstrates the ioHub Common EyeTracking Interface by displaying a gaze cursor
at the currently reported gaze position on an image background.

Select which tracker to use by setting the TRACKER variable below. Edit the associated
configuration dict for the eye tracker being used to modify it's settings.
"""
from psychopy import core, visual
from psychopy.data import TrialHandler, importConditions
from psychopy.iohub import launchHubServer
from psychopy.iohub.util import getCurrentDateTimeString, hideWindow, showWindow
import os

# Eye tracker to use ('mouse', 'eyelink', 'gazepoint', or 'tobii')
TRACKER = 'mouse'

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

if __name__ == "__main__":
    window = visual.Window((1920, 1080),
                        units='height',
                        fullscr=True,
                        allowGUI=False,
                        colorSpace='rgb',
                        color=[0, 0, 0]
                        )

    window.setMouseVisible(False)

    # Create a dict of image stim for trials and a gaze blob to show the
    # reported gaze position with.
    #
    image_cache = dict()
    image_names = ['canal.jpg', 'fall.jpg', 'party.jpg', 'swimming.jpg', 'lake.jpg']
    for iname in image_names:
        image_cache[iname] = visual.ImageStim(window, image=os.path.join('./images/', iname), name=iname)

    # Create a circle to use for the Gaze Cursor. Current units assume pix.
    #
    gaze_dot = visual.GratingStim(window, tex=None, mask="gauss", pos=(0, 0),
                                  size=(0.1, 0.1), color='green')

    # Create a Text Stim for use on /instruction/ type screens.
    # Current units assume pix.
    instructions_text_stim = visual.TextStim(window, text='', pos=[0, 0], units='pix', height=24, color=[-1, -1, -1],
                                             wrapWidth=window.size[0]*.9)


    exp_conditions = importConditions('trial_conditions.xlsx')
    trials = TrialHandler(exp_conditions, 1)

    io_hub = launchHubServer(window=window, experiment_code='gc_cursor', **devices_config)
    # Inform the ioDataStore that the experiment is using a TrialHandler. The ioDataStore will create a table
    # which can be used to record the actual trial variable values (DV or IV) in the order run / collected.
    #
    io_hub.createTrialHandlerRecordTable(trials)

    # Let's make some short-cuts to the devices we will be using in this demo.
    tracker = None
    try:
        tracker = io_hub.devices.tracker
    except Exception:
        print(" No eye tracker config found in iohub_config.yaml")
        io_hub.quit()
        core.quit()

    display = io_hub.devices.display
    kb = io_hub.devices.keyboard

    # Minimize the PsychoPy window if needed
    hideWindow(window)
    # Display calibration gfx window and run calibration.
    result = tracker.runSetupProcedure()
    print("Calibration returned: ", result)
    # Maximize the PsychoPy window if needed
    showWindow(window)

    flip_time = window.flip()
    io_hub.sendMessageEvent(text="EXPERIMENT_START", sec_time=flip_time)

    # Send some information to the ioDataStore as experiment messages,
    # including the experiment and session id's, the calculated pixels per
    # degree, display resolution, etc.
    #
    io_hub.sendMessageEvent(text="IO_HUB EXPERIMENT_INFO START")
    io_hub.sendMessageEvent(text="ioHub Experiment started {0}".format(getCurrentDateTimeString()))
    io_hub.sendMessageEvent(text="Experiment ID: {0}, Session ID: {1}".format(io_hub.experimentID,
                                                                              io_hub.experimentSessionID))
    io_hub.sendMessageEvent(text="Stimulus Screen ID: {0}, "
                            "Size (pixels): {1}, CoordType: {2}".format(display.getIndex(),
                                                                        display.getPixelResolution(),
                                                                        display.getCoordinateType()))
    io_hub.sendMessageEvent(text="Calculated Pixels Per Degree: {0} x, {1} y".format(*display.getPixelsPerDegree()))
    io_hub.sendMessageEvent(text="IO_HUB EXPERIMENT_INFO END")

    io_hub.clearEvents('all')

    # For each trial in the set of trials within the current block.
    #
    t = 0
    for trial in trials:
        # Update the instruction screen text to indicate
        # a trial is about to start.
        #
        instuction_text = "Press Space Key To Start Trial %d" % t
        instructions_text_stim.setText(instuction_text)
        instructions_text_stim.draw()
        window.flip()

        # Wait until a space key press event occurs after the
        # start trial instuctions have been displayed.
        #
        io_hub.clearEvents('all')
        kb.waitForPresses(keys=[' ', ])

        # Space Key has been pressed, start the trial.
        # Set the current session and trial id values to be saved
        # in the ioDataStore for the upcoming trial.
        #

        trial['session_id'] = io_hub.getSessionID()
        trial['trial_id'] = t+1

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
        io_hub.clearEvents('all')
        # Send a msg to the ioHub indicating that the trial started,
        # and the time of the first retrace displaying the trial stim.
        #
        io_hub.sendMessageEvent(text="TRIAL_START", sec_time=flip_time)
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
            if type(gpos) in [tuple, list]:
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
            if type(gpos) in [tuple, list]:
                io_hub.sendMessageEvent("IMAGE_UPDATE %s %.3f %.3f" % (trial['IMAGE_NAME'], gpos[0], gpos[1]),
                                        sec_time=flip_time)
            else:
                io_hub.sendMessageEvent("IMAGE_UPDATE %s [NO GAZE]" % (trial['IMAGE_NAME']),
                                        sec_time=flip_time)

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
        io_hub.sendMessageEvent(text="TRIAL_END", sec_time=flip_time)

        # Stop recording eye data.
        # In this example, we have no use for any eye data
        # between trials, so why save it.
        #
        tracker.setRecordingState(False)

        # Save the experiment condition variable values for this
        # trial to the ioDataStore.
        #
        io_hub.addTrialHandlerRecord(trial)

        # Clear all event buffers
        #
        io_hub.clearEvents('all')
        t += 1

    # All trials have been run, so end the experiment.
    #

    flip_time = window.flip()
    io_hub.sendMessageEvent(text='EXPERIMENT_COMPLETE', sec_time=flip_time)

    # Disconnect the eye tracking device.
    #
    tracker.setConnectionState(False)

    # The experiment is done, all trials have been run.
    # Clear the screen and show an 'experiment  done' message using the
    # instructionScreen text.
    #
    instuction_text = "Press Any Key to Exit Demo"
    instructions_text_stim.setText(instuction_text)
    instructions_text_stim.draw()
    flip_time = window.flip()
    io_hub.sendMessageEvent(text="SHOW_DONE_TEXT", sec_time=flip_time)
    io_hub.clearEvents('all')
    # wait until any key is pressed
    kb.waitForPresses()
