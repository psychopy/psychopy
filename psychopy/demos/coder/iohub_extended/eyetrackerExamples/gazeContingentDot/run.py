"""
ioHub
.. file: ioHub/examples/simple/simpleTrackerTest.py
"""

from psychopy import visual

from psychopy.iohub import Computer, ioHubExperimentRuntime, FullScreenWindow, OrderedDict

class ExperimentRuntime(ioHubExperimentRuntime):
    """
    Create an experiment using psychopy and the ioHub framework by extending the ioHubExperimentRuntime class. At minimum
    all that is needed in the __init__ for the new class, here called ExperimentRuntime, is the a call to the
    ioHubExperimentRuntime __init__ itself.
    """
    def __init__(self,configFileDirectory, configFile):
        ioHubExperimentRuntime.__init__(self,configFileDirectory,configFile)

    def run(self,*args):
        """
        The run method contains your experiment logic. It is equal to what would be in your main psychopy experiment
        script.py file in a standard psychopy experiment setup. That is all there is too it really.
        """

        # PLEASE REMEMBER , THE SCREEN ORIGIN IS ALWAYS IN THE CENTER OF THE SCREEN,
        # REGARDLESS OF THE COORDINATE SPACE YOU ARE RUNNING IN. THIS MEANS 0,0 IS SCREEN CENTER,
        # -x_min, -y_min is the screen bottom left
        # +x_max, +y_max is the screen top right
        #
        # RIGHT NOW, ONLY PIXEL COORD SPACE IS SUPPORTED. THIS WILL BE FIXED SOON.

        # Let's make some short-cuts to the devices we will be using in this 'experiment'.


        tracker=self.hub.devices.tracker
        display=self.hub.devices.display
        kb=self.hub.devices.kb
        mouse=self.hub.devices.mouse
        
        tracker.runSetupProcedure()
        self.hub.clearEvents('all')
        self.hub.wait(0.050)

        current_gaze=[0,0]

        # Create a psychopy window, full screen resolution, full screen mode, pix units, with no boarder, using the monitor
        # profile name 'test monitor, which is created on the fly right now by the script
        window = FullScreenWindow(display)
        
        # Hide the 'system mouse cursor' so we can display a cool gaussian mask for a mouse cursor.
        mouse.setSystemCursorVisibility(False)

        # Create an ordered dictionary of psychopy stimuli. An ordered dictionary is one that returns keys in the order
        # they are added, you you can use it to reference stim by a name or by 'zorder'
        psychoStim=OrderedDict()
        psychoStim['grating'] = visual.PatchStim(window, mask="circle", size=75,pos=[-100,0], sf=.075)
        psychoStim['fixation'] =visual.PatchStim(window, size=25, pos=[0,0], sf=0,  color=[-1,-1,-1], colorSpace='rgb')
        psychoStim['gazePosText'] =visual.TextStim(window, text=str(current_gaze), pos = [100,0], height=48, color=[-1,-1,-1], colorSpace='rgb',alignHoriz='left',wrapWidth=300)
        psychoStim['gazePos'] =visual.GratingStim(window,tex=None, mask="gauss", pos=current_gaze,size=(50,50),color='purple')

        [psychoStim[stimName].draw() for stimName in psychoStim]

        Computer.enableHighPriority(True)
        #self.setProcessAffinities([0,1],[2,3])

        tracker.setRecordingState(True)
        self.hub.wait(0.050)

        # Clear all events from the ioHub event buffers.
        self.hub.clearEvents('all')


        # Loop until we get a keyboard event
        while len(kb.getEvents())==0:

            # for each loop, update the grating phase
            psychoStim['grating'].setPhase(0.05, '+')#advance phase by 0.05 of a cycle

            # and update the gaze contingent gaussian based on the current gaze location

            current_gaze=tracker.getLastGazePosition()
            current_gaze=int(current_gaze[0]),int(current_gaze[1])
               
            psychoStim['gazePos'].setPos(current_gaze)
            psychoStim['gazePosText'].setText(str(current_gaze))

            # this is short hand for looping through the psychopy stim list and redrawing each one
            # it is also efficient, may not be as user friendly as:
            # for stimName, stim in psychoStim.itervalues():
            #    stim.draw()
            # which does the same thing if you like and is probably just as efficent.
            [psychoStim[stimName].draw() for stimName in psychoStim]

            # flip the psychopy window buffers, so the stim changes you just made get displayed.
            flip_time=window.flip()

            # send a message to the iohub with the message text that a flip occurred and what the mouse position was.
            # since we know the ioHub server time the flip occurred on, we can set that directly in the event.
            self.hub.sendMessageEvent("Flip %s"%(str(current_gaze),),sec_time=flip_time)

        # a key was pressed so the loop was exited. We are clearing the event buffers to avoid an event overflow ( currently known issue)
        self.hub.clearEvents('all')

        tracker.setRecordingState(False)

        # wait 250 msec before ending the experiment (makes it feel less abrupt after you press the key)
        self.hub.wait(0.250)
        tracker.setConnectionState(False)

        # _close neccessary files / objects, 'disable high priority.
        window.close()

        ### End of experiment logic

##################################################################
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