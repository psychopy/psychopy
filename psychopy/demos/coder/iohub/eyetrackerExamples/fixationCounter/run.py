"""
ioHub
.. file: ioHub/examples/eyeTrackerFixationCounter/run.py
"""

from psychopy import visual
from psychopy.iohub import ioHubExperimentRuntime, EventConstants, FullScreenWindow, win32MessagePump

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

        # Create a psychopy window, full screen resolution, full screen mode, pix units, with no boarder, using the monitor
        # profile name 'test monitor, which is created on the fly right now by the script
        window = FullScreenWindow(display)

        # Hide the 'system mouse cursor' so we can display a cool gaussian mask for a mouse cursor.
        mouse.setSystemCursorVisibility(False)

        # Create an ordered dictionary of psychopy stimuli. An ordered dictionary is one that returns keys in the order
        # they are added, you you can use it to reference stim by a name or by 'zorder'
        image_name='./images/party.png'
        imageStim = visual.ImageStim(window, image=image_name, name='image_stim')

        imageStim.draw()

        print "Detected Fixation Message Format:"
        print "FIX_DETECTED fix_end_time fix_x fix_y fdur fix_rt"

        tracker.setRecordingState(True)
        self.hub.wait(0.050)

        flip_time=window.flip()
        self.hub.clearEvents('all')
        self.hub.sendMessageEvent("SYNCTIME %s"%(image_name,),sec_time=flip_time)
        # Clear all events from the global event buffer, and from the keyboard and eyetracker event buffer.
        # This 'mess' of calls is needed right now because clearing the global event buffer does not
        # clear device level event buffers, and each device buffer is independent. Not sure this is a 'good'
        # thing as it stands, but until there is feedback, it will stay as is.

        fixationCount=0
        dwellTime=0.0
        # Loop until we get a keyboard event
        while len(kb.getEvents())==0:
            for ee in tracker.getEvents(EventConstants.FIXATION_END):
                if EventConstants.FIXATION_END == ee.type:
                    etime=ee.time
                    eeye=ee.eye
                    ex=ee.average_gaze_x
                    ey=ee.average_gaze_y
                    edur=ee.duration
                    ert=etime-flip_time
                    print 'FIX %.3f\t%d\t%.3f\t%.3f\t%.3f\t%.3f'%(etime,eeye,ex,ey,edur,ert)
                    fixationCount+=1
                    dwellTime+=edur
                    self.hub.sendMessageEvent("FIX_DETECTED %.6f %.3f %.3f %.6f %.6f"%(etime,ex,ey,edur,ert))

            imageStim.draw()
            window.flip()

        print "-------------"
        print " Number Fixations Made: ",fixationCount
        print " Total Dwell Time: ",dwellTime
        if fixationCount:
            print " Average Dwell Time / Fixation: ",dwellTime/fixationCount

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