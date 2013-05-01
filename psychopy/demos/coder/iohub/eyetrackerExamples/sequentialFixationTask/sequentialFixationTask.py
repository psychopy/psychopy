"""
ioHub
.. file: ioHub/examples/sequentialFixationTask/sequentialFixationTask.py

"""

from psychopy.iohub import (ExperimentVariableProvider, getCurrentDateTimeString,
                              DeviceEventTrigger, ClearScreen, generatedPointGrid,
                              InstructionScreen, FileDialog, FullScreenWindow,
                              Computer,ioHubExperimentRuntime, EventConstants,
                              )

from  experimentResources import TargetScreen


import numpy as np

try:
    from shapely.geometry import Point
except:
    import sys
    print "This example uses the python package called 'shapely'. Please install and run again."
    sys.exit(1)
    
class ExperimentRuntime(ioHubExperimentRuntime):
    HORZ_SCALING=0.9
    VERT_SCALING=0.9
    HORZ_POS_COUNT=7
    VERT_POS_COUNT=7
    RANDOMIZE_TRIALS=True

    def __init__(self,configFileDirectory, configFile):
        ioHubExperimentRuntime.__init__(self,configFileDirectory,configFile)

    def run(self,*args):
        # PLEASE REMEMBER , THE SCREEN ORIGIN IS ALWAYS IN THE CENTER OF THE SCREEN,
        # REGARDLESS OF THE COORDINATE SPACE YOU ARE RUNNING IN. THIS MEANS 0,0 IS SCREEN CENTER,
        # -x_min, -y_min is the screen bottom left
        # +x_max, +y_max is the screen top right
        #
        # RIGHT NOW, ONLY PIXEL COORD SPACE IS SUPPORTED. THIS WILL BE FIXED.

        # Let's make some short-cuts to the devices we will be using in this 'experiment'.
        # using getDevice() returns None if the device is not found, 
        tracker=self.hub.getDevice('tracker')
        
        display=self.devices.display
        kb=self.devices.kb
        mouse=self.devices.mouse

        if tracker is None:
            print "EyeTracker Device cdid not load."
            #return 0
        
        # get the experiment condition variable excel file to use.
        fdialog=FileDialog(message="Select a Condition Variable File",
                           defaultDir=self.paths.CONDITION_FILES.getPath(),
                           defaultFile="", openFile=True,
                           allowMultipleSelections= False,
                           allowChangingDirectories = True,
                           fileTypes=(FileDialog.EXCEL_FILES,FileDialog.ALL_FILES),
                           display_index=display.getIndex())

        result,conditionVariablesFile=fdialog.show()
        fdialog.Destroy()

        if result != FileDialog.OK_RESULT:
            print "User cancelled Condition Variable Selection... Exiting Experiment."
            return

        if conditionVariablesFile:
            conditionVariablesFile=conditionVariablesFile[0]

        #create a condition set provider
        self.conditionVariablesProvider=ExperimentVariableProvider(
                                        conditionVariablesFile,'BLOCK_LABEL',
                                        practiceBlockValues='PRACTICE',
                                        randomizeBlocks=False,
                                        randomizeTrials=True)

        # initialize (or create) a table in the ioDataStore to hold the condition variable data
        self.hub.initializeConditionVariableTable(self.conditionVariablesProvider)
        
        # Hide the 'system mouse cursor' so it does not bother us.
        mouse.setSystemCursorVisibility(False)
        
        # Create a psychopy window, full screen resolution, full screen mode, pix units, with no border, using the monitor
        # profile name 'test monitor', which is created on the fly right now by the script
        self.window = FullScreenWindow(display)

        # create screen states

        # screen state that can be used to just clear the screen to blank.
        self.clearScreen=ClearScreen(self)
        self.clearScreen.flip(text='EXPERIMENT_INIT')

        self.clearScreen.sendMessage("IO_HUB EXPERIMENT_INFO START")
        self.clearScreen.sendMessage("ioHub Experiment started {0}".format(getCurrentDateTimeString()))
        self.clearScreen.sendMessage("Experiment ID: {0}, Session ID: {1}".format(self.hub.experimentID,self.hub.experimentSessionID))
        self.clearScreen.sendMessage("Stimulus Screen ID: {0}, Size (pixels): {1}, CoordType: {2}".format(display.getIndex(),display.getPixelResolution(),display.getCoordinateType()))
        self.clearScreen.sendMessage("Calculated Pixels Per Degree: {0} x, {1} y".format(*display.getPixelsPerDegree()))        
        self.clearScreen.sendMessage("IO_HUB EXPERIMENT_INFO END")

        # screen for showing text and waiting for a keyboard response or something
        dtrigger=DeviceEventTrigger(kb,EventConstants.KEYBOARD_PRESS,{'key':' '})
        self.instructionScreen=InstructionScreen(self,"Press Space Key when Ready to Start Experiment.",dtrigger,5*60)

        # screen state used during the data collection / runtime of the experiment to move the
        # target from one point to another.
        self.targetScreen=TargetScreen(self)

        xyEventTrigs=[DeviceEventTrigger(kb,EventConstants.KEYBOARD_PRESS,{'key':'F1'},self.targetScreen.toggleDynamicStimVisibility),]
        if tracker:
            self.targetScreen.dynamicStimPositionFuncPtr=tracker.getLastGazePosition
            msampleTrig=DeviceEventTrigger(tracker,EventConstants.MONOCULAR_EYE_SAMPLE,{},self.targetScreen.setDynamicStimPosition)
            bsampleTrig=DeviceEventTrigger(tracker,EventConstants.BINOCULAR_EYE_SAMPLE,{},self.targetScreen.setDynamicStimPosition)
            xyEventTrigs.extend([msampleTrig,bsampleTrig])
        else:
            self.targetScreen.dynamicStimPositionFuncPtr=mouse.getPosition
            msampleTrig=DeviceEventTrigger(mouse,EventConstants.MOUSE_MOVE,{},self.targetScreen.setDynamicStimPosition)
            xyEventTrigs.append(msampleTrig)

        # setup keyboard event hook on target screen state 
        # to catch any press space bar events for responses to color changes.

        dtrigger=DeviceEventTrigger(kb,EventConstants.KEYBOARD_PRESS,{'key':' '},self._spaceKeyPressedDuringTargetState)
        xyEventTrigs.append(dtrigger)
        self.targetScreen.setEventTriggers(xyEventTrigs)

        # set all screen states background color to the first screen background color in the Excel file
        # i.e. the SCREEN_COLOR column
        displayColor=tuple(self.conditionVariablesProvider.getData()[0]['SCREEN_COLOR'])
        self.clearScreen.setScreenColor(displayColor)
        self.instructionScreen.setScreenColor(displayColor)
        self.targetScreen.setScreenColor(displayColor)

        # clear the display a few times to be sure front and back buffers are clean.
        self.clearScreen.flip()
        
        self.hub.clearEvents('all')

        # show the opening instruction screen, clearing events so events pre display of the
        # screen state change are not picked up by the event monitoring. This is the default,
        # so you can just call .switchTo() if you want all events cleared right after the flip
        # returns. If you 'do not' want events cleared, use .switchTo(False)
        #
        flip_time,time_since_flip,event=self.instructionScreen.switchTo(clearEvents=True,msg='EXPERIMENT_START')

        self.clearScreen.flip(text='PRACTICE_BLOCKS_START')
        # Run Practice Blocks
        self.runBlockSet(self.conditionVariablesProvider.getPracticeBlocks())
        self.clearScreen.flip(text='PRACTICE_BLOCKS_END')

        # Run Experiment Blocks
        self.clearScreen.flip(text='EXPERIMENT_BLOCKS_START')
        self.runBlockSet(self.conditionVariablesProvider.getExperimentBlocks())
        self.clearScreen.flip(text='EXPERIMENT_BLOCKS_END')

        # show the 'thanks for participating screen'
        self.instructionScreen.setText("Experiment Complete. Thank you for Participating.")
        self.instructionScreen.setTimeout(10*60) # 10 minute timeout
        dtrigger=DeviceEventTrigger(kb,EventConstants.KEYBOARD_PRESS,{'key':' '})
        self.instructionScreen.setEventTriggers(dtrigger)
        flip_time,time_since_flip,event=self.instructionScreen.switchTo(msg='EXPERIMENT_END')

        # close the psychopy window
        self.window.close()

        # Done Experiment close the tracker connection if it is open.

        if tracker:
            tracker.setConnectionState(False)

        ### End of experiment logic


    # Called by the run() method to perform a sequence of blocks in the experiment.
    # So this method has the guts of the experiment logic.
    # This method is called once to run any practice blocks, and once to run the experimental blocks.
    #
    def runBlockSet(self, blockSet):
        # using getDevice() returns None if the device is not found, 
        tracker=self.hub.getDevice('tracker')
        
        daq=self.hub.getDevice('daq')
        
        # using self.devices.xxxxx raises an exception if the
        # device is not present
        kb=self.devices.kb
        display=self.devices.display
        
        # for each block in the group of blocks.....
        for trialSet in blockSet.getNextConditionSet():
            # if an eye tracker is connected,
            if tracker:
                self.instructionScreen.setTimeout(30*60.0) # 30 minute timeout, long enough for a break if needed.
                dtrigger=DeviceEventTrigger(kb,EventConstants.KEYBOARD_PRESS,{'key':['RETURN','ESCAPE']})
                self.instructionScreen.setEventTriggers(dtrigger)
                self.instructionScreen.setText("Press 'Enter' to go to eye tracker Calibration mode.\n\nTo skip calibration and start Data Recording press 'Escape'")
                flip_time,time_since_flip,event=self.instructionScreen.switchTo(msg='CALIBRATION_SELECT')
                if event and event.key == 'RETURN':
                    runEyeTrackerSetupAndCalibration(tracker,self.window)
                elif event and event.key == 'ESCAPE':
                    print '** Calibration stage skipped for block ',blockSet.getCurrentConditionSetIteration()
                else:
                    print '** Time out occurred. Entering calibration mode to play it safe. ;)'
                    runEyeTrackerSetupAndCalibration(tracker,self.window)

            dres=display.getPixelResolution()
            # right now, target positions are automatically generated based on point grid size, screen size, and a scaling factor (a gain).
            TARGET_POSITIONS=generatedPointGrid(dres[0],dres[1],self.HORZ_SCALING,self.VERT_SCALING,self.HORZ_POS_COUNT,self.VERT_POS_COUNT)

            # indexes to display the condition variable order in start out 'non' randomized.
            RAND_INDEXES=np.arange(TARGET_POSITIONS.shape[0])

            # if conditionVariablesProvider was told to randomize trials, then randomize trial index access list.
            if self.conditionVariablesProvider.randomizeTrials is True:
                self.hub.sendMessageEvent("RAND SEED = {0}".format(ExperimentVariableProvider._randomGeneratorSeed),sec_time=ExperimentVariableProvider._randomGeneratorSeed/1000.0)
                np.random.shuffle(RAND_INDEXES)

            dtrigger=DeviceEventTrigger(kb,EventConstants.KEYBOARD_PRESS,{'key':' '})
            self.instructionScreen.setEventTriggers(dtrigger)
            self.instructionScreen.setText("Press 'Space' key when Ready to Start Block %d"%(blockSet.getCurrentConditionSetIteration()))
            flip_time,time_since_flip,event=self.instructionScreen.switchTo(msg='BLOCK_START')

            # enable high priority for the experiment process only. Not sure this is necessary, or a good idea,
            # based on tests so far frankly. Running at std priority seems to usually be just fine.
            Computer.enableRealTimePriority(True)

            # if we have a tracker, start recording.......
            if tracker:
                tracker.setRecordingState(True)

            # delay a short time to let " the data start flow'in "
            self.hub.wait(.050)

            # In this paradigm, each 'trial' is the movement from one target location to another.
            # Recording of eye data is on for the whole block of XxY target positions within the block.
            # A rough outline of the runtime / data collection portion of a block is as follows:
            #      a) Start each block with the target at screen center.
            #      b) Wait sec.msec duration after showing the target [ column PRE_POS_CHANGE_INTERVAL ] in excel file
            #      c) Then schedule move of target to next target position at the time of the next retrace.
            #      d) Once the Target has moved to the 2nd position for the trial, wait PRE_COLOR_CHANGE_INTERVAL
            #         sec.msec before 'possibly changing the color of the center of the target. The new color is
            #         determined by the FP_INNER_COLOR2 column. If no color change is wanted, simply make this color
            #         equal to the color of the target center in column FP_INNER_COLOR for that row of the spreadsheet.
            #      e) Once the target has been redrawn (either with or without a color change, it stays in position for
            #         another POST_COLOR_CHANGE_INTERVAL sec.msec. Since ioHub is being used, all keyboard activity
            #         is being recorded to the ioDataStore file, so there is no need really to 'monitor' for
            #         the participants key presses, since we do not use it for feedback. It can be retrieved from the
            #         data file for analysis post hoc.
            #      f) After the POST_COLOR_CHANGE_INTERVAL, the current 'trial' officially ends, and the next trial
            #         starts, with the target remaining in the position it was at in the end of the last trial, but
            #         with the target center color switching to FP_INNER_COLOR.
            #      g) Then the sequence from b) starts again for the number of target positions in the block
            #        (49 currently).
            #
            
            self.hub.clearEvents('all') 
            
            self._TRIAL_STATE=None
            self.targetScreen.nextAreaOfInterest=None
            
            for trial in trialSet.getNextConditionSet():
                try:
                        
                    currentTrialIndex=trialSet.getCurrentConditionSetIndex()
                    
                    nextTargetPosition=TARGET_POSITIONS[currentTrialIndex]                
                    trial['FP_X']=nextTargetPosition[0]
                    trial['FP_Y']=nextTargetPosition[1]
                    
                    ppd_x,ppd_y=self.devices.display.getPixelsPerDegree()
                                    
                    fp_outer_radius=int(trial['FP_OUTER_RADIUS']*ppd_x),int(trial['FP_OUTER_RADIUS']*ppd_y)
                    fp_inner_radius=int(trial['FP_INNER_RADIUS']*ppd_x),int(trial['FP_INNER_RADIUS']*ppd_y)
    
                    self.targetScreen.setScreenColor(tuple(trial['SCREEN_COLOR']))
                    self.targetScreen.setTargetOuterColor(tuple(trial['FP_OUTER_COLOR']))
                    self.targetScreen.setTargetInnerColor(tuple(trial['FP_INNER_COLOR']))
                    self.targetScreen.setTargetOuterSize(fp_outer_radius)
                    self.targetScreen.setTargetInnerSize(fp_inner_radius)
                    
                    self.hub.clearEvents('kb') 
                    
                    self.targetScreen.setTimeout(trial['PRE_POS_CHANGE_INTERVAL'])
                    self._TRIAL_STATE=trial,'FIRST_PRE_POS_CHANGE_KEY'                
                    target_pos1_color1_time,time_since_flip,event=self.targetScreen.switchTo(msg='TRIAL_TARGET_INITIAL_COLOR')
                    print 'TRIAL_TARGET_INITIAL_COLOR: ',  target_pos1_color1_time,time_since_flip,event
                    
                    self.targetScreen.setTargetPosition(nextTargetPosition)
                    self.targetScreen.setTimeout(trial['PRE_COLOR_CHANGE_INTERVAL'])
                    self._TRIAL_STATE=trial,'FIRST_POST_POS_CHANGE_KEY'                
    
                    # create a 3 degree circular region (1.5 degree radius) around the next target position
                    # for use as out invisible boundary                 
                    self.targetScreen.nextAreaOfInterest=Point(*nextTargetPosition).buffer(((ppd_x+ppd_y)/2.0)*1.5)
    
                    target_pos2_color1_time,time_since_flip,event=self.targetScreen.switchTo(msg='TRIAL_TARGET_MOVE')
                    print 'TRIAL_TARGET_MOVE: ',  target_pos1_color1_time,time_since_flip,event
                    
                    
                    self.targetScreen.setTargetInnerColor(tuple(trial['FP_INNER_COLOR2']))
                    self.targetScreen.setTimeout(trial['POST_COLOR_CHANGE_INTERVAL'])
                    self._TRIAL_STATE=trial,'FIRST_POST_COLOR_CHANGE_KEY'                
                    target_pos2_color2_time,time_since_flip,event=self.targetScreen.switchTo(msg='TRIAL_TARGET_COLOR_TWO')
                    print 'TRIAL_TARGET_COLOR_TWO: ',  target_pos1_color1_time,time_since_flip,event
                   
                    # end of 'trial sequence'
                    # send condition variables used / populated to ioDataStore
                    toSend=[self.hub.experimentSessionID,trialSet.getCurrentConditionSetIteration()]
                    trial['TSTART_TIME']=target_pos1_color1_time
                    trial['APPROX_TEND_TIME']=target_pos2_color2_time+time_since_flip
                    trial['target_pos1_color1_time']=target_pos1_color1_time
                    trial['target_pos2_color1_time']=target_pos2_color1_time
                    trial['target_pos2_color2_time']=target_pos2_color2_time
                    
                    if self.targetScreen.aoiTriggeredID:
                        trial['VOG_SAMPLE_ID_AOI_TRIGGER']=self.targetScreen.aoiTriggeredID
                        trial['VOG_SAMPLE_TIME_AOI_TRIGGER']=self.targetScreen.aoiTriggeredTime
                    if self.targetScreen.aoiBestGaze:
                        trial['BEST_GAZE_X']=self.targetScreen.aoiBestGaze[0]
                        trial['BEST_GAZE_Y']=self.targetScreen.aoiBestGaze[1]
                        
                    self._TRIAL_STATE=None
                    if self.targetScreen.nextAreaOfInterest:
                        del self.targetScreen.nextAreaOfInterest
                        self.targetScreen.nextAreaOfInterest=None
                        
                    toSend.extend(trial.tolist())
                    self.hub.addRowToConditionVariableTable(toSend)
                    print 'Trial end'
                    print '------------'
                except:
                    print 'Error During Trial'
                    self.printExceptionDetails()
            # end of block of trials, clear screen
            self.clearScreen.flip(text='BLOCK_END')

            self._TRIAL_STATE=None
            
            # if tracking eye position, turn off eye tracking.
            if tracker:
                tracker.setRecordingState(False)
            if daq:
                daq.enableEventReporting(False)

            # turn off high priority so python GC can clean up if it needs to.
            Computer.disableHighPriority()

            # give a 100 msec delay before starting next block
            self.hub.wait(.100)

        # end of block set, return from method.
        self.clearScreen.flip(text='BLOCK_SET_END')
        return True

    def _spaceKeyPressedDuringTargetState(self,flipTime, stateDuration, event):
        if self._TRIAL_STATE:
            trial,column_name=self._TRIAL_STATE
            if trial[column_name]<=-100: # no RT has been registered yet
                trial[column_name]=event.time-flipTime
        return False
        
########

def runEyeTrackerSetupAndCalibration(trackerClientView, window):
    # TODO: MOVE EXTRA SURROUNDING CODE TO _preRemoteMethodCallFunctions and _postRemoteMethodCallFunctions
    # TODO: in ioHubDeviceView
    # Instead of calling the eye tracker runSetupProcedure function directly,
    # we wrap it in a local method so that the currently open psychopy window can be
    # hidden prior to, and displayed after, the calibration window is created by the ioHub Process.
    # This seems to keep the psychopy window from staying onto of the calibration graphics window when it opens
    # some of the time

    #psychopyWindow.winHandle.set_visible(False)
    window.winHandle.minimize()

    trackerClientView.runSetupProcedure()

    window.winHandle.maximize()
    #window.winHandle.set_visible(True)
    window.winHandle.activate()

#
####### Main function definition ----------------------------------------------
#
if __name__ == "__main__":
    from psychopy.iohub import module_directory
    def main(configurationDirectory):
        """
        Creates an instance of the ExperimentRuntime class, checks for an
        experiment config file name parameter passed in via
        command line, and launches the experiment logic.
        """
        import sys
        runtime=ExperimentRuntime(configurationDirectory, "experiment_config.yaml")
    
        runtime.start(sys.argv)
        
    configurationDirectory=module_directory(main)

    # run the main function, which starts the experiment runtime
    main(configurationDirectory)