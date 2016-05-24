#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Demonstrates the ioHub Common EyeTracking Interface by displaying a gaze cursor
at the currently reported gaze position on an image background.
Any currently supported Eye Tracker can be used during the demo by selecting
the eye tracker name the start of the demo. The demo script is used regardless
of the Eye Tracker hardware selected.
"""
from __future__ import division, print_function, absolute_import

import os

from psychopy import core, visual
from psychopy.data import TrialHandler, importConditions
from psychopy.iohub.util import readConfig, saveConfig, module_directory
from psychopy.iohub.client import launchHubServer

eye_tracker_config_files = {
    'LC Technologies EyeGaze': 'eyetracker_configs/eyegaze_config.yaml',
    'SMI iViewX': 'eyetracker_configs/iviewx_config.yaml',
    'SR Research EyeLink': 'eyetracker_configs/eyelink_config.yaml',
    'Tobii Technologies Eye Trackers': 'eyetracker_configs/tobii_config.yaml',
    }

def selectTrackerConfig():
    from psychopy import gui

    info = {
        'Eye Tracker Type': [
            'Select',
            'LC Technologies EyeGaze',
            'SMI iViewX',
            'SR Research EyeLink',
            'Tobii Technologies Eye Trackers']}

    dlg_info = dict(info)
    infoDlg = gui.DlgFromDict(
        dictionary=dlg_info,
        title='Select Eye Tracker')
    if not infoDlg.OK:
        return None

    while dlg_info.values()[0] == u'Select' and infoDlg.OK:
        dlg_info = dict(info)
        infoDlg = gui.DlgFromDict(
            dictionary=dlg_info,
            title='SELECT Eye Tracker To Continue...')

    if not infoDlg.OK:
        return None

    current_path = module_directory(selectTrackerConfig)
    return os.path.join(current_path,
                        eye_tracker_config_files[dlg_info.values()[0]])

if __name__ == '__main__':
    et_config_path = selectTrackerConfig()
    if et_config_path is None:
        print("Tracker Selection Cancelled. Exiting Demo...")
        core.quit()
    et_config = readConfig(et_config_path)
    selected_eyetracker_name = et_config.keys()[0]
    iohub_config = dict(iohub_config_name='iohub_config.yaml.part')
    iohub_config[et_config.keys()[0]] = et_config.values()[0]
    iohub_config['experiment_code'] = 'select_tracker'

    io = launchHubServer(**iohub_config)

    exp_conditions = importConditions('trial_conditions.xlsx')
    trials = TrialHandler(exp_conditions, 1)

    # Inform the ioDataStore that the experiment is using ac
    # TrialHandler. The ioDataStore will create a table
    # which can be used to record the actual trial variable values (DV or IV)
    # in the order run / collected.
    #
    io.createTrialHandlerRecordTable(trials)

    # Let's make some short-cuts to the devices we will be using in this
    # 'experiment'.
    tracker = io.devices.tracker
    display = io.devices.display
    kb = io.devices.keyboard
    mouse = io.devices.mouse

    # Start by running the eye tracker default setup procedure.
    tracker.runSetupProcedure()

    # Create a psychopy window, full screen resolution, full screen mode...
    #
    res = display.getPixelResolution()
    window = visual.Window(res, monitor=display.getPsychopyMonitorName(),
                           units=display.getCoordinateType(),
                           fullscr=True,
                           allowGUI=False,
                           screen=display.getIndex()
                           )

    # Create a dict of image stim for trials and a gaze blob to show
    # gaze position.
    display_coord_type = display.getCoordinateType()
    image_cache = dict()
    image_names = [
        'canal.jpg',
        'fall.jpg',
        'party.jpg',
        'swimming.jpg',
        'lake.jpg']

    for iname in image_names:
        image_cache[iname] = visual.ImageStim(window, image=os.path.join(
            './images/', iname), name=iname, units=display_coord_type)

    gaze_dot = visual.GratingStim(window, tex=None, mask='gauss',
                                  pos=(0, 0), size=(66, 66), color='green',
                                  units=display_coord_type)
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

    # wait until a key event occurs after the instructions are displayed
    io.clearEvents()
    kb.waitForPresses()

    # Send some information to the ioHub DataStore as experiment messages
    # including the eye tracker being used for this session.
    #
    io.sendMessageEvent(text='IO_HUB EXPERIMENT_INFO START')
    io.sendMessageEvent(text='Experiment ID: {0}, Session ID: {1}'.format(io.experimentID, io.experimentSessionID))
    io.sendMessageEvent(
        text='Stimulus Screen ID: {0}, Size (pixels): {1}, CoordType: {2}'.format(
            display.getIndex(),
            display.getPixelResolution(),
            display.getCoordinateType()))
    io.sendMessageEvent(
        text='Calculated Pixels Per Degree: {0} x, {1} y'.format(
            *display.getPixelsPerDegree()))
    io.sendMessageEvent(
        text='Eye Tracker being Used: {0}'.format(selected_eyetracker_name))
    io.sendMessageEvent(text='IO_HUB EXPERIMENT_INFO END')

    io.clearEvents()
    t = 0
    for trial in trials:
        # Update the instuction screen text...
        #
        instuction_text = 'Press Space Key To Start Trial %d' % t
        instructions_text_stim.setText(instuction_text)
        instructions_text_stim.draw()
        flip_time = window.flip()
        io.sendMessageEvent(
            text='EXPERIMENT_START', sec_time=flip_time)

        start_trial = False

        # wait until a space key event occurs after the instructions are
        # displayed
        kb.waitForPresses(keys=' ')

        # So request to start trial has occurred...
        # Clear the screen, start recording eye data, and clear all events
        # received to far.
        #
        flip_time = window.flip()
        trial['session_id'] = io.getSessionID()
        trial['trial_id'] = t + 1
        trial['TRIAL_START'] = flip_time
        io.sendMessageEvent(text='TRIAL_START', sec_time=flip_time)
        io.clearEvents()
        tracker.setRecordingState(True)

        # Get the image name for this trial
        #
        imageStim = image_cache[trial['IMAGE_NAME']]

        # Loop until we get a keyboard event
        #
        run_trial = True
        while run_trial is True:
            # Get the latest gaze position in dispolay coord space..
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
                io.sendMessageEvent(
                    'IMAGE_UPDATE %s %.3f %.3f' %
                    (iname, gpos[0], gpos[1]), sec_time=flip_time)
            else:
                io.sendMessageEvent(
                    'IMAGE_UPDATE %s [NO GAZE]' %
                    (iname), sec_time=flip_time)

            # Check any new keyboard char events for a space key.
            # If one is found, set the trial end variable.
            #
            if ' ' in kb.getPresses():
                run_trial = False

        # So the trial has ended, send a message to the DataStore
        # with the trial end time and stop recording eye data.
        # In this example, we have no use for any eye data between trials,
        # so why save it?
        flip_time = window.flip()
        trial['TRIAL_END'] = flip_time
        io.sendMessageEvent(
            text='TRIAL_END %d' %
            t, sec_time=flip_time)
        tracker.setRecordingState(False)
        # Save the Experiment Condition Variable Data for this trial to the
        # ioDataStore.
        #
        io.addTrialHandlerRecord(trial.values())
        io.clearEvents()
        t += 1

    # Disconnect the eye tracking device.
    #
    tracker.setConnectionState(False)

    # Update the instuction screen text...
    #
    instuction_text = 'Press Any Key to Exit Demo'
    instructions_text_stim.setText(instuction_text)
    instructions_text_stim.draw()
    flip_time = window.flip()
    io.sendMessageEvent(text='SHOW_DONE_TEXT', sec_time=flip_time)

    # wait until any key is pressed
    kb.waitForPresses()

    # So the experiment is done, all trials have been run.
    # Clear the screen and show an 'experiment  done' message using the
    # instructionScreen state. What for the trigger to exit that state.
    # (i.e. the space key was pressed)
    #
    io.sendMessageEvent(text='EXPERIMENT_COMPLETE')
    # End of experiment logic
