"""
ioHub
.. file: ioHub/examples/headless/run.py
"""

from psychopy.iohub import Computer, ioHubExperimentRuntime, EventConstants

import time

class ExperimentRuntime(ioHubExperimentRuntime):
    """
    """    
    def run(self,*args):
        """
        """
        self.keyboard=self.devices.kb
        self.display=self.devices.display
        self.mouse=self.devices.mouse
        
        self.eyetracker=self.devices.tracker
        
            
        self.print_eye_event_stream=False
        self.print_current_gaze_pos=False
        self.print_keyboard_event_stream=False
        self.print_mouse_event_stream=False
        
        self.app_start_time=Computer.getTime()
        # Loop until we get a keyboard event with the space, Enter (Return), 
        # or Escape key is pressed.
        
        self.printCommandOptions()
        self.printApplicationStatus()
        
        while 1:
            
             # if 'an event handler returns True, quit the program         
            if self.handleEyeTrackerEvents():
                break
            if self.handleKeyboardEvents():
                break
            if self.handleMouseEvents():
                break

            if self.eyetracker:
                self.printGazePosition()
                
            # discard any event we do not need from the online event queues            
            self.hub.clearEvents('all')
            
            # since realtime access to events on this process does not matter in 
            # this demo, elt's sleep for 20 msec every loop
            time.sleep(0.02)
        
        self.eyetracker.setConnectionState(False)
        self.hub.clearEvents('all')
        # END OF PROGRAM

    def handleKeyboardEvents(self):
        event_list=self.keyboard.getEvents(EventConstants.KEYBOARD_CHAR)        
        
        for k in event_list:
            if  k.modifiers is not None and 'CONTROL_LEFT' in k.modifiers:            
                if k.key in ['ESCAPE', ]:
                    print '\n>> Quit key pressed: ',k.key,' for ',k.duration,' sec.'
                    return True        
                elif k.key == 'E':
                    self.toggleEyeEventPrinting()
                elif k.key == 'G':
                    self.toggleGazePositionPrinting()
                elif k.key == 'M':
                    self.toggleMouseEventPrinting()
                elif k.key == 'K':
                    self.toggleKeyboardEventPrinting()
                elif k.key == 'C':
                    return self.runEyeTrackerCalibration()
                elif k.key == 'R':
                    self.toggleEyeEventRecording()
                elif k.key == 'H':
                    self.printCommandOptions()
                elif k.key == 'S':
                    self.printApplicationStatus()
            
            elif self.print_keyboard_event_stream is True:
                self.printKeyEvent(k)
            
        return False

    def handleMouseEvents(self):
        if self.print_mouse_event_stream is True:
            event_list=self.mouse.getEvents()
            for m in event_list:
                self.printMouseEvent(m)
                
        return False

    def handleEyeTrackerEvents(self):
        event_list=self.eyetracker.getEvents()
        if self.print_eye_event_stream is True:
            for t in event_list:
                self.printEyeEvent(t)
        return False

    def toggleGazePositionPrinting(self):
        print ''
        self.print_current_gaze_pos=not self.print_current_gaze_pos
        if self.print_current_gaze_pos is True:
            print '\n>> Disabled ALL Event Printing.'
            self.print_eye_event_stream=False    
            self.print_mouse_event_stream=False                        
            self.print_keyboard_event_stream=False    
        print '>> Gaze Pos Print Status: ',self.print_current_gaze_pos
        print '>> Eye Event Print Status: ',self.print_eye_event_stream
        print ''

    def printEyeEvent(self,e):
        if e.type == EventConstants.BINOCULAR_EYE_SAMPLE:
            print 'BINOC SAMPLE:\n\tLEFT:\n\t\tSTATUS: %d\n\t\tPOS: (%.3f,%.3f)\n\t\tPUPIL_SIZE: %.3f\n\tRIGHT:\n\t\tSTATUS: %d\n\t\tPOS: (%.3f,%.3f)\n\t\t PUPIL_SIZE: %.3f\n'%(
                     int(e.status/10.0),                    
                     e.left_gaze_x,e.left_gaze_y,
                     e.left_pupil_measure1,
                     e.status%10,
                     e.right_gaze_x,e.right_gaze_y,
                     e.right_pupil_measure1)
        elif e.type == EventConstants.MONOCULAR_EYE_SAMPLE:
            print 'MONOC SAMPLE: mot handled yet'
        else:
            print 'Unhandled eye event:\n{0}\n'.format(e)

    def printGazePosition(self):
        if self.print_current_gaze_pos is True and self.eyetracker.isRecordingEnabled():
            
            gp=self.eyetracker.getLastGazePosition()
            if gp is None:
                print 'GAZE POS: TRACK LOSS\r',            
            else:
                gx,gy=gp
                print 'GAZE POS: ( %.3f, %.3f )\r'%(gx,gy),

    def toggleEyeEventPrinting(self):
        print ''
        self.print_eye_event_stream=not self.print_eye_event_stream
        if self.print_eye_event_stream is True:
            print '\n>> Disabled Gaze Pos Printing.'                    
            self.print_current_gaze_pos=False    
        print '>> Eye Event Print Status: ',self.print_eye_event_stream
        print '>> Gaze Pos Print Status: ',self.print_current_gaze_pos
        print ''

    def toggleMouseEventPrinting(self):
        print ''
        self.print_mouse_event_stream=not self.print_mouse_event_stream
        if self.print_current_gaze_pos is True:
            print '\n>> Disabled Gaze Pos Printing.'
            self.print_current_gaze_pos=False
        print '>> Mouse Event Print Status: ',self.print_mouse_event_stream
        print ''

    def printMouseEvent(self,m):          
        print 'Mouse Event: ', m.time, (m.x_position,m.y_position), m.button_id, m.scroll_y, m.window_id 

    def toggleKeyboardEventPrinting(self):
        print ''
        self.print_keyboard_event_stream=not self.print_keyboard_event_stream
        if self.print_current_gaze_pos is True:
            print '\n>> Disabled Gaze Pos Printing.' 
            self.print_current_gaze_pos=False
        print '\n>> Keyboard Event Print Status: ',self.print_keyboard_event_stream
        print ''

    def printKeyEvent(self,k):
        print 'Keyboard Event: ', k.time, k.key, k.modifiers 

    def toggleEyeEventRecording(self):
        # Toggle eye tracker recording.
        is_recording=self.eyetracker.setRecordingState(not self.eyetracker.isRecordingEnabled())
        print "\n>> NOTE: Tracker Recording State change: ",is_recording
        
    def runEyeTrackerCalibration(self):
        # start calibration if not recording data
        if self.eyetracker:
            if self.eyetracker.isRecordingEnabled() is True:
                print '\n>> ERROR: Can not calibrate when recording. Stop recording first, then calibrate'
                return False
                
            calibrationOK=self.eyetracker.runSetupProcedure()
            if calibrationOK is False:
                print "\n>> ERROR: Exiting application due to failed calibration."
                return True
                
        print "\n>> NOTE: Tracker Calibration Done."
    
    def printCommandOptions(self):
        print ''
        print '######################################'
        print '# >> Headless ioHub Controls:        #'
        print '#                                    #'
        print '# The following key combinations     #'
        print '# are available:                     #'
        print '#                                    #'
        print '# L_CTRL+ESCAPE: End Program         #'
        print '# L_CTRL+C:      Start ET Calibr.    #'
        print '# L_CTRL+R:      Toggle Eye Rec.     #'
        print '#                                    #'
        print '# L_CTRL+E:      Toggle Eye Events   #'
        print '# L_CTRL+G:      Toggle Gaze Pos.    #'
        print '# L_CTRL+M:      Toggle Mouse Events #'
        print '# L_CTRL+K:      Toggle KB Events    #'
        print '#                                    #'
        print '# L_CTRL+H:      Print Controls      #'
        print '# L_CTRL+S:      Print Status        #'
        print '#                                    #'
        print '######################################'
        print ''
        
    def printApplicationStatus(self):
        print ''
        print 'Headless ioHub Status:'
        if self.eyetracker:
            print '\tRunning Time: %.3f seconds.'%(Computer.getTime()-self.app_start_time)
            print '\tRecording Eye Data: ',self.eyetracker.isRecordingEnabled()
            print '\tPrinting Eye Events: ',self.print_eye_event_stream
            print '\tPrinting Mouse Events: ',self.print_mouse_event_stream
            print '\tPrinting Keyboard Events: ',self.print_keyboard_event_stream
            print '\tPrinting Gaze Position: ',self.print_current_gaze_pos
        print ''

    def prePostSessionVariableCallback(self,sessionVarDict):
        sess_code=sessionVarDict['code']
        scount=1
        while self.isSessionCodeInUse(sess_code) is True:
            sess_code='%s-%d'%(sessionVarDict['code'],scount)
            scount+=1
        sessionVarDict['code']=sess_code
        return sessionVarDict

################################################################################
# The below code should never need to be changed, unless you want to get command
# line arguements or something. 
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