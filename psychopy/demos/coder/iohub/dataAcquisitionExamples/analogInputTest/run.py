"""
ioHub
.. file: ioHub/examples/analogInputTest/run.py
"""

from psychopy import visual

from psychopy.iohub import OrderedDict,Computer,ioHubExperimentRuntime, EventConstants, FullScreenWindow

class ExperimentRuntime(ioHubExperimentRuntime):
    """
    Create an experiment using psychopy and the ioHub framework by extending the ioHubExperimentRuntime class. At minimum
    all that is needed in the __init__ for the new class, here called ExperimentRuntime, is the a call to the
    ioHubExperimentRuntime __init__ itself.
    """
    def run(self,*sys_args):
        """
        The run method contains your experiment logic. It is equal to what would be in your main psychopy experiment
        script.py file in a standard psychopy experiment setup. That is all there is too it really.
        """

        # PLEASE REMEMBER , THE SCREEN ORIGIN IS ALWAYS IN THE CENTER OF THE SCREEN,
        # REGARDLESS OF THE COORDINATE SPACE YOU ARE RUNNING IN. THIS MEANS 0,0 IS SCREEN CENTER,
        # -x_min, -y_min is the screen bottom left
        # +x_max, +y_max is the screen top right
        #
        # *** RIGHT NOW, ONLY PIXEL COORD SPACE IS SUPPORTED. THIS WILL BE FIXED SOON. ***

        # Let's make some short-cuts to the devices we will be using in this 'experiment'.
        mouse=self.devices.mouse
        display=self.devices.display
        kb=self.devices.kb
        ain=self.devices.ain
        
        # get the number of trials entered in the session dialog
        user_params=self.getSavedUserDefinedParameters()
        print 'user_params: ', user_params
        trial_count=int(user_params.get('trial_count',5))
           
        #Computer.enableHighPriority()

        # Set the mouse position to 0,0, which means the 'center' of the screen.
        mouse.setPosition((0.0,0.0))

        # Read the current mouse position (should be 0,0)  ;)
        currentPosition=mouse.getPosition()

        # Create a psychopy window, full screen resolution, full screen mode
        psychoWindow = FullScreenWindow(display)
        
        # Hide the 'system mouse cursor' so we can display a cool gaussian mask for a mouse cursor.
        mouse.setSystemCursorVisibility(False)

        # Create an ordered dictionary of psychopy stimuli. An ordered dictionary is one that returns keys in the order
        # they are added, you you can use it to reference stim by a name or by 'zorder'
        psychoStim=OrderedDict()
        psychoStim['grating'] = visual.PatchStim(psychoWindow, mask="circle", size=150,pos=[0,0], sf=.075)

        psychoStim['title'] = visual.TextStim(win=psychoWindow, 
                              text="Analog Input Test. Trial 1 of %d"%(trial_count),
                              pos = [0,200], height=36, color=[1,.5,0], 
                              colorSpace='rgb',
                              alignHoriz='center',alignVert='center',
                              wrapWidth=800.0)

        ai_values_string_proto="AI_0: %.3f\tAI_1: %.3f\tAI_2: %.3f\tAI_3: %.3f\t\nAI_4: %.3f\tAI_5: %.3f\tAI_6: %.3f\tAI_7: %.3f"
        ai_values=(0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0)
        psychoStim['analog_input_values'] = visual.TextStim(win=psychoWindow, 
                              text=ai_values_string_proto%ai_values,
                              pos = [0,-200], height=24, color=[1,1,0], 
                              colorSpace='rgb',
                              alignHoriz='center',alignVert='center',
                              wrapWidth=800.0)

        psychoStim['instruction'] = visual.TextStim(win=psychoWindow, 
                              text="Press ESCAPE Key for Next Trial",
                              pos = [0,-300], height=36, color=[1,1,0.5], 
                              colorSpace='rgb',
                              alignHoriz='center',alignVert='center',
                              wrapWidth=800.0)

        # Clear all events from the global and device level event buffers.
        self.hub.clearEvents('all')

        
        # Loop until we get a keyboard event with the space, Enter (Return), or Escape key is pressed.
        for i in range(trial_count):        
            # Clear all events from the global and device level event buffers.
            psychoStim['title'].setText("Analog Input Test. Trial %d of %d"%(i+1,trial_count))
            self.hub.clearEvents('all')
            
            #start streamin AnalogInput data        
            ain.enableEventReporting(True)
            
            QUIT_TRIAL=False
            
            while QUIT_TRIAL is False:
    
                # for each loop, update the grating phase
                psychoStim['grating'].setPhase(0.05, '+')#advance phase by 0.05 of a cycle
    
                # update analog input values to display
                analog_input_events=ain.getEvents()
                if analog_input_events:
                    event_count=len(analog_input_events)
                    event=analog_input_events[-1]
                    ai_values=(event.AI_0,event.AI_1,event.AI_2,event.AI_3,
                               event.AI_4,event.AI_5,event.AI_6,event.AI_7)
                    psychoStim['analog_input_values'].setText(ai_values_string_proto%ai_values)
    
                # redraw the stim
                [psychoStim[stimName].draw() for stimName in psychoStim]
    
                # flip the psychopy window buffers, so the stim changes you just made get displayed.
                psychoWindow.flip()
                # it is on this side of the call that you know the changes have been displayed, so you can
                # make a call to the ioHub time method and get the time of the flip, as the built in
                # time methods represent both experiment process and ioHub server process time.
                # Most times in ioHub are represented sec.msec format to match that of Psychopy.
                flip_time=Computer.currentSec()
    
                # send a message to the iohub with the message text that a flip occurred and what the mouse position was.
                # since we know the ioHub server time the flip occurred on, we can set that directly in the event.
                self.hub.sendMessageEvent("Flip %s"%(str(currentPosition),), sec_time=flip_time)
        
                # for each new keyboard char event, check if it matches one of the end example keys.
                for k in kb.getEvents(EventConstants.KEYBOARD_CHAR):
                    if k.key in ['ESCAPE', ]:
                        print 'Trial Quit key pressed: ',k.key,' for ',k.duration,' sec.'
                        QUIT_TRIAL=True

            
            # clear the screen
            psychoWindow.flip()
 
            # stop analog input recording
            ain.enableEventReporting(False)
                    
            # delay 1/4 second before next trial
            actualDelay=self.hub.delay(0.250)
    
        # wait 250 msec before ending the experiment
        actualDelay=self.hub.wait(0.250)
        print "Delay requested %.6f, actual delay %.6f, Diff: %.6f"%(0.250,actualDelay,actualDelay-0.250)

        # for fun, test getting a bunch of events at once, likely causing a mutlipacket getEvents()
        stime = Computer.currentSec()
        events=self.hub.getEvents()
        etime=Computer.currentSec()
        print 'event count: ', len(events),' delay (msec): ',(etime-stime)*1000.0

        # _close neccessary files / objects, 'disable high priority.
        psychoWindow.close()

        ### End of experiment logic

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