#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
eye_tracker/run.py

Demonstrates the ioHub Common EyeTracking Interface by displaying a gaze cursor
at the currently reported gaze position on an image background. 
All currently supported Eye Tracker Implementations are supported,  
with the Eye Tracker Technology chosen at the start of the demo via a
drop down list. Exact same demo script is used regardless of the 
Eye Tracker hardware used.

Initial Version: May 6th, 2013, Sol Simpson
"""

from __future__ import absolute_import, division, print_function

from psychopy import visual
from psychopy.data import TrialHandler,importConditions
from psychopy.iohub import ioHubExperimentRuntime
from psychopy.iohub.util import getCurrentDateTimeString

import os

class ExperimentRuntime(ioHubExperimentRuntime):
    """
    Create an experiment using psychopy and the ioHub framework by extending the ioHubExperimentRuntime class. At minimum
    all that is needed in the __init__ for the new class, here called ExperimentRuntime, is the a call to the
    ioHubExperimentRuntime __init__ itself.
    """
    def run(self,*args):
        """
        The run method contains your experiment logic. It is equal to what would be in your main psychopy experiment
        script.py file in a standard psychopy experiment setup. That is all there is too it really.
        """

        exp_conditions=importConditions('trial_conditions.xlsx')
        trials = TrialHandler(exp_conditions,1)

        # Inform the ioDataStore that the experiment is using ac
        # TrialHandler. The ioDataStore will create a table 
        # which can be used to record the actual trial variable values (DV or IV)
        # in the order run / collected.
        #
        self.hub.createTrialHandlerRecordTable(trials) 
                                 
        selected_eyetracker_name=args[0]
        # Let's make some short-cuts to the devices we will be using in this 'experiment'.
        tracker=self.hub.devices.tracker
        display=self.hub.devices.display
        kb=self.hub.devices.keyboard
                    
        # Start by running the eye tracker default setup procedure.
        tracker.runSetupProcedure()

        # Create a psychopy window, full screen resolution, full screen mode...
        #
        res=display.getPixelResolution()
        window=visual.Window(res,monitor=display.getPsychopyMonitorName(),
                                    units=display.getCoordinateType(),
                                    fullscr=True,
                                    allowGUI=False,
                                    screen= display.getIndex()
                                    )

        # Create a dict of image stim for trials and a gaze blob to show gaze position.
        #
        display_coord_type=display.getCoordinateType()
        image_cache=dict()
        image_names=['canal.jpg','fall.jpg','party.jpg','swimming.jpg','lake.jpg']

        for iname in image_names:
            image_cache[iname]=visual.ImageStim(window, image=os.path.join('./images/',iname), 
                        name=iname,units=display_coord_type)
                        
        gaze_dot =visual.GratingStim(window,tex=None, mask="gauss", 
                                     pos=(0,0 ),size=(66,66),color='green', 
                                                        units=display_coord_type)
        instructions_text_stim = visual.TextStim(window, text='', pos = [0,0], height=24, 
                       color=[-1,-1,-1], colorSpace='rgb',alignHoriz='center', alignVert='center',wrapWidth=window.size[0]*.9)


        # Update Instruction Text and display on screen.
        # Send Message to ioHub DataStore with Exp. Start Screen display time.
        #
        instuction_text="Press Any Key to Start Experiment."
        instructions_text_stim.setText(instuction_text)        
        instructions_text_stim.draw()
        flip_time=window.flip()
        self.hub.sendMessageEvent(text="EXPERIMENT_START",sec_time=flip_time)
        
        # wait until a key event occurs after the instructions are displayed
        self.hub.clearEvents('all')
        kb.waitForPresses()
            
        
        # Send some information to the ioHub DataStore as experiment messages
        # including the eye tracker being used for this session.
        #
        self.hub.sendMessageEvent(text="IO_HUB EXPERIMENT_INFO START")
        self.hub.sendMessageEvent(text="ioHub Experiment started {0}".format(getCurrentDateTimeString()))
        self.hub.sendMessageEvent(text="Experiment ID: {0}, Session ID: {1}".format(self.hub.experimentID,self.hub.experimentSessionID))
        self.hub.sendMessageEvent(text="Stimulus Screen ID: {0}, Size (pixels): {1}, CoordType: {2}".format(display.getIndex(),display.getPixelResolution(),display.getCoordinateType()))
        self.hub.sendMessageEvent(text="Calculated Pixels Per Degree: {0} x, {1} y".format(*display.getPixelsPerDegree()))        
        self.hub.sendMessageEvent(text="Eye Tracker being Used: {0}".format(selected_eyetracker_name))
        self.hub.sendMessageEvent(text="IO_HUB EXPERIMENT_INFO END")

        self.hub.clearEvents('all')
        t=0
        for trial in trials:    
            # Update the instruction screen text...
            #            
            instuction_text="Press Space Key To Start Trial %d"%t
            instructions_text_stim.setText(instuction_text)        
            instructions_text_stim.draw()
            flip_time=window.flip()
            self.hub.sendMessageEvent(text="EXPERIMENT_START",sec_time=flip_time)
            

            # wait until a space key event occurs after the instructions are displayed
            kb.waitForPresses(keys=' ')

            # So request to start trial has occurred...
            # Clear the screen, start recording eye data, and clear all events
            # received to far.
            #
            flip_time=window.flip()
            trial['session_id']=self.hub.getSessionID()
            trial['trial_id']=t+1 
            trial['TRIAL_START']=flip_time
            self.hub.sendMessageEvent(text="TRIAL_START",sec_time=flip_time)
            self.hub.clearEvents('all')
            tracker.setRecordingState(True)


            
            # Get the image name for this trial
            #
            imageStim=image_cache[trial['IMAGE_NAME']]

            # Loop until we get a keyboard event
            #
            run_trial=True
            while run_trial is True:
                # Get the latest gaze position in dispolay coord space..
                #
                gpos=tracker.getLastGazePosition()
                if isinstance(gpos,(tuple,list)):
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
                flip_time=window.flip()   
                
                # Send a message to the ioHub Process / DataStore indicating 
                # the time the image was drawn and current position of gaze spot.
                #
                if isinstance(gpos,(tuple,list)):
                    self.hub.sendMessageEvent("IMAGE_UPDATE %s %.3f %.3f"%(iname,gpos[0],gpos[1]),sec_time=flip_time)
                else:
                    self.hub.sendMessageEvent("IMAGE_UPDATE %s [NO GAZE]"%(iname),sec_time=flip_time)
 
                # Check any new keyboard char events for a space key.
                # If one is found, set the trial end variable.
                #
                if ' ' in kb.getPresses():
                    run_trial = False
        
            # So the trial has ended, send a message to the DataStore
            # with the trial end time and stop recording eye data.
            # In this example, we have no use for any eye data between trials, so why save it.
            #
            flip_time=window.flip()
            trial['TRIAL_END']=flip_time
            self.hub.sendMessageEvent(text="TRIAL_END %d"%t,sec_time=flip_time)
            tracker.setRecordingState(False)
            # Save the Experiment Condition Variable Data for this trial to the
            # ioDataStore.
            #
            self.hub.addTrialHandlerRecord(trial)          
            self.hub.clearEvents('all')
            t+=1

        # Disconnect the eye tracking device.
        #
        tracker.setConnectionState(False)

        # Update the instruction screen text...
        #            
        instuction_text="Press Any Key to Exit Demo"
        instructions_text_stim.setText(instuction_text)        
        instructions_text_stim.draw()
        flip_time=window.flip()
        self.hub.sendMessageEvent(text="SHOW_DONE_TEXT",sec_time=flip_time)
     
        # wait until any key is pressed
        kb.waitForPresses()
            
        # So the experiment is done, all trials have been run.
        # Clear the screen and show an 'experiment  done' message using the 
        # instructionScreen state. What for the trigger to exit that state.
        # (i.e. the space key was pressed)
        #
        self.hub.sendMessageEvent(text='EXPERIMENT_COMPLETE')
        ### End of experiment logic


####### Main Script Launching Code Below #######

if __name__ == "__main__":
    from psychopy import gui
    from psychopy.iohub import module_directory
        
    def main(configurationDirectory):
        """
        Creates an instance of the ExperimentRuntime class, gets the eye tracker
        the user wants to use for the demo, and launches the experiment logic.
        """
        # The following code merges a iohub_config file called iohub_config.yaml.part,
        # that has all the iohub_config settings, other than those for the eye tracker.
        # the eye tracker configs are in the yaml files in the eyetracker_configs dir.
        # 
        # This code lets a person select an eye tracker, and then merges the main iohub_config.yaml.part
        # with the contents of the eyetracker config yaml in eyetracker_configs
        # associated with the selected tracker.
        #
        # The merged result is saved as iohub_config.yaml so it can be picked up
        # by the Experiment _runtime
        # as normal.
        eye_tracker_config_files={
                                  'GazePoint':'eyetracker_configs/gazepoint_config.yaml',
                                  'SMI':'eyetracker_configs/iviewx_config.yaml',
                                  'SR Research':'eyetracker_configs/eyelink_config.yaml',
                                  'Tobii':'eyetracker_configs/tobii_config.yaml',
                                  }
        
        info = {'Eye Tracker Type': ['Select', 'GazePoint', 
                                     'SMI', 'SR Research', 'Tobii']}
        
        dlg_info=dict(info)
        infoDlg = gui.DlgFromDict(dictionary=dlg_info, title='Select Eye Tracker')
        if not infoDlg.OK:
            return -1 

        while list(dlg_info.values())[0] == u'Select' and infoDlg.OK:
                dlg_info=dict(info)
                infoDlg = gui.DlgFromDict(dictionary=dlg_info, title='SELECT Eye Tracker To Continue...')
   
        if not infoDlg.OK:
            return -1 

        base_config_file=os.path.normcase(os.path.join(configurationDirectory,
                                                       'iohub_config.yaml.part'))
                                                       
        eyetrack_config_file=os.path.normcase(os.path.join(configurationDirectory,
                                eye_tracker_config_files[list(dlg_info.values())[0]]))

        combined_config_file_name=os.path.normcase(os.path.join(configurationDirectory,
                                                                'iohub_config.yaml'))
        
        ExperimentRuntime.mergeConfigurationFiles(base_config_file,
                                eyetrack_config_file,combined_config_file_name)

        
        runtime=ExperimentRuntime(configurationDirectory, "experiment_config.yaml")    
        runtime.start((list(dlg_info.values())[0],))


    # Get the current directory, using a method that does not rely on __FILE__
    # or the accuracy of the value of __FILE__.
    #
    configurationDirectory=module_directory(main)

    # Run the main function, which starts the experiment runtime
    #
    main(configurationDirectory)
