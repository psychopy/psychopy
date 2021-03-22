#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
eye_tracker/run.py

Demonstrates the ioHub Common EyeTracking Interface by displaying a gaze cursor
at the currently reported gaze position on an image background. This demo also
illustrates how the same experiment script / logic can be used with any of the
supported eye trackers.

If needed, eye tracker settings can be adjusted by editing the eye tracker's
.yaml file file the ./eyetracker_configs/ folder in this demo.
"""
from __future__ import absolute_import, division, print_function
import os
from psychopy import visual, gui
from psychopy.data import TrialHandler, importConditions
from psychopy.iohub import launchHubServer
from psychopy.iohub.util import mergeConfigurationFiles, getCurrentDateTimeString
from psychopy.iohub import module_directory


def run(selected_eyetracker_name):
    """

    :param selected_eyetracker_name:
    :return:
    """
    io_hub = launchHubServer(experiment_code='select_tracker', iohub_config_name="iohub_config.yaml")

    exp_conditions = importConditions('trial_conditions.xlsx')
    trials = TrialHandler(exp_conditions, 1)

    # Inform the ioDataStore that the experiment is using ac
    # TrialHandler. The ioDataStore will create a table
    # which can be used to record the actual trial variable values (DV or IV)
    # in the order run / collected.
    #
    io_hub.createTrialHandlerRecordTable(trials)

    # Let's make some short-cuts to the devices we will be using in this 'experiment'.
    tracker = io_hub.devices.tracker
    display = io_hub.devices.display
    kb = io_hub.devices.keyboard

    # Start by running the eye tracker default setup procedure.
    tracker.runSetupProcedure()

    # Create a psychopy window, full screen resolution, full screen mode...
    #
    res = display.getPixelResolution()
    window = visual.Window(res, monitor=display.getPsychopyMonitorName(), units=display.getCoordinateType(),
                           fullscr=True, allowGUI=False, screen=0)
    window.setMouseVisible(False)

    # Create a dict of image stim for trials and a gaze blob to show gaze position.
    #
    display_coord_type = display.getCoordinateType()
    image_cache = dict()
    image_names = ['canal.jpg', 'fall.jpg', 'party.jpg', 'swimming.jpg', 'lake.jpg']

    for iname in image_names:
        image_cache[iname] = visual.ImageStim(
            window, image=os.path.join('./images/', iname),
            name=iname, units=display_coord_type
        )
    gaze_dot = visual.GratingStim(
        window, tex=None, mask="gauss",
        pos=(0, 0), size=(66, 66), color='green',
        units=display_coord_type
    )
    instructions_text_stim = visual.TextStim(
        window, text='', pos=[0, 0], height=24,
        color=[-1, -1, -1], colorSpace='rgb',
        wrapWidth=window.size[0] * .9, units='pix'
    )

    # Update Instruction Text and display on screen.
    # Send Message to ioHub DataStore with Exp. Start Screen display time.
    #
    instuction_text = "Press Any Key to Start Experiment."
    instructions_text_stim.setText(instuction_text)
    instructions_text_stim.draw()
    flip_time = window.flip()
    io_hub.sendMessageEvent(text="EXPERIMENT_START", sec_time=flip_time)

    # wait until a key event occurs after the instructions are displayed
    io_hub.clearEvents('all')
    kb.waitForPresses()

    # Send some information to the ioHub DataStore as experiment messages
    # including the eye tracker being used for this session.
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
    io_hub.sendMessageEvent(text="Eye Tracker being Used: {0}".format(selected_eyetracker_name))
    io_hub.sendMessageEvent(text="IO_HUB EXPERIMENT_INFO END")

    io_hub.clearEvents('all')
    t = 0
    for trial in trials:
        # Update the instruction screen text...
        #
        instuction_text = "Press Space Key To Start Trial %d" % t
        instructions_text_stim.setText(instuction_text)
        instructions_text_stim.draw()
        flip_time = window.flip()
        io_hub.sendMessageEvent(text="EXPERIMENT_START", sec_time=flip_time)

        # wait until a space key event occurs after the instructions are displayed
        kb.waitForPresses(keys=' ')

        # So request to start trial has occurred...
        # Clear the screen, start recording eye data, and clear all events
        # received to far.
        #
        flip_time = window.flip()
        trial['session_id'] = io_hub.getSessionID()
        trial['trial_id'] = t+1
        trial['TRIAL_START'] = flip_time
        io_hub.sendMessageEvent(text="TRIAL_START", sec_time=flip_time)
        io_hub.clearEvents('all')
        tracker.setRecordingState(True)

        # Get the image name for this trial
        #
        imageStim = image_cache[trial['IMAGE_NAME']]

        # Loop until we get a keyboard event
        #
        run_trial = True
        while run_trial is True:
            # Get the latest gaze position in display coord space..
            #
            gpos = tracker.getLastGazePosition()
            if isinstance(gpos, (tuple, list)):
                # If we have a gaze position from the tracker, draw the
                # background image and then the gaze_cursor.
                #
                gaze_dot.setPos(gpos)
                imageStim.draw()
                gaze_dot.draw()
            else:
                # Otherwise just draw the background image.
                #
                imageStim.draw()

            # flip video buffers, updating the display with the stim we just
            # updated.
            #
            flip_time = window.flip()

            # Send a message to the ioHub Process / DataStore indicating
            # the time the image was drawn and current position of gaze spot.
            #
            if isinstance(gpos, (tuple, list)):
                io_hub.sendMessageEvent("IMAGE_UPDATE %s %.3f %.3f" % (trial['IMAGE_NAME'], gpos[0], gpos[1]),
                                        sec_time=flip_time)
            else:
                io_hub.sendMessageEvent("IMAGE_UPDATE %s [NO GAZE]" % trial['IMAGE_NAME'], sec_time=flip_time)

            # Check any new keyboard char events for a space key.
            # If one is found, set the trial end variable.
            #
            if ' ' in kb.getPresses():
                run_trial = False

        # So the trial has ended, send a message to the DataStore
        # with the trial end time and stop recording eye data.
        # In this example, we have no use for any eye data between trials, so why save it.
        #
        flip_time = window.flip()
        trial['TRIAL_END'] = flip_time
        io_hub.sendMessageEvent(text="TRIAL_END %d" % t, sec_time=flip_time)
        tracker.setRecordingState(False)
        # Save the Experiment Condition Variable Data for this trial to the
        # ioDataStore.
        #
        io_hub.addTrialHandlerRecord(trial)
        io_hub.clearEvents('all')
        t += 1

    # Disconnect the eye tracking device.
    #
    tracker.setConnectionState(False)

    # Update the instruction screen text...
    #
    instuction_text = "Press Any Key to Exit Demo"
    instructions_text_stim.setText(instuction_text)
    instructions_text_stim.draw()
    flip_time = window.flip()
    io_hub.sendMessageEvent(text="SHOW_DONE_TEXT", sec_time=flip_time)

    # wait until any key is pressed
    kb.waitForPresses()

    # So the experiment is done, all trials have been run.
    # Clear the screen and show an 'experiment  done' message using the
    # instructionScreen state. What for the trigger to exit that state.
    # (i.e. the space key was pressed)
    #
    io_hub.sendMessageEvent(text='EXPERIMENT_COMPLETE')
    # End of experiment logic


def select_eye_tracker():
    eye_tracker_config_files = {
        'GazePoint': 'eyetracker_configs/gazepoint_config.yaml',
        'SR Research': 'eyetracker_configs/eyelink_config.yaml',
        'Tobii': 'eyetracker_configs/tobii_config.yaml',
    }

    info = {'Eye Tracker Type': ['Select', 'GazePoint', 'SR Research', 'Tobii']}

    dlg_info = dict(info)
    infoDlg = gui.DlgFromDict(dictionary=dlg_info, title='Select Eye Tracker')
    if not infoDlg.OK:
        return False

    while list(dlg_info.values())[0] == u'Select' and infoDlg.OK:
        dlg_info = dict(info)
        infoDlg = gui.DlgFromDict(dictionary=dlg_info, title='SELECT Eye Tracker To Continue...')

    if not infoDlg.OK:
        return False

    configurationDirectory = module_directory(run)
    base_config_file = os.path.normcase(os.path.join(configurationDirectory, 'base_iohub_config.yaml'))

    eyetrack_config_file = os.path.normcase(os.path.join(configurationDirectory,
                                                         eye_tracker_config_files[list(dlg_info.values())[0]]))

    combined_config_file_name = os.path.normcase(os.path.join(configurationDirectory, 'iohub_config.yaml'))

    mergeConfigurationFiles(base_config_file, eyetrack_config_file, combined_config_file_name)
    return list(dlg_info.values())[0]


if __name__ == "__main__":
    selected_tracker = select_eye_tracker()
    if selected_tracker:
        run(selected_tracker)
