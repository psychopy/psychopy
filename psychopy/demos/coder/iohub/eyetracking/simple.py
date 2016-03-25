from psychopy import core, visual
from psychopy.iohub.client import launchHubServer

TRIAL_COUNT = 2

# Start ioHub event monitoring process, using the eyelink eyetracker
# Note: No iohub config .yaml files are needed in this demo
# Since no experiment or session code is given, no iohub hdf5 file 
# will be saved, but device events are still available at runtime.
runtime_settings = dict()
runtime_settings['sampling_rate'] = 500
runtime_settings['track_eyes'] = 'RIGHT'
iohub_config = {'eyetracker.hw.sr_research.eyelink.EyeTracker': 
                    {'name': 'tracker', 
                     #'simulation_mode': True,
                     'model_name': 'EYELINK 1000 DESKTOP',
                     'runtime_settings': runtime_settings
                     },
}

io = launchHubServer(**iohub_config)

# Get some iohub devices for future access.
keyboard = io.devices.keyboard
display = io.devices.display
tracker = io.devices.tracker

# run eyetracker calibration
r = tracker.runSetupProcedure()

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
        # Get the latest gaze position in dispolay coord space..
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
            text_stim.text = text_stim_str%(gpos[0],gpos[1],gaze_in_region)

           # If we have a gaze position from the tracker, update gc stim
            gaze_dot.setPos(gpos)
        else:
            # Otherwise just draw the background image.
            #
            text_stim.text = 'Eye Position: MISSING. In Region: No\nPress space key to start next trial.'

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
        if ' ' in keyboard.getPresses():
            run_trial = False

    # Current Trial is Done
    # Stop eye data recording
    tracker.setRecordingState(False)
    t += 1

# All Trials are done
# End experiment
win.close()
tracker.setConnectionState(False)
io.quit()
core.quit()
