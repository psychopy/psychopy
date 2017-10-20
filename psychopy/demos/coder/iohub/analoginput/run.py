#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Displays values from 8 channels ( 0 - 7 ) from the AnalogInput Device as
configured in the iohub.config.yaml file in this directory.

@author: Sol
"""

from __future__ import absolute_import, division, print_function

from builtins import range
from psychopy import visual
from collections import OrderedDict
from psychopy.iohub import ioHubExperimentRuntime, EventConstants, module_directory


class ExperimentRuntime(ioHubExperimentRuntime):
    """
    Create an experiment using psychopy and the ioHub framework by extending
    the ioHubExperimentRuntime class. At minimum all that is needed is to override
    the run() method with the main experiment script logic.

    By the time run() is called, the experiment_config.yaml and iohub_config.yaml
    files have been read and used to initialize the ioHub Server. The ioHubConnection
    instance that has been created to interact the ioHub Process can be accessed using
    `self.hub`.

    To change the analog input device being used, or any configuration parameters
    for that device hardware, edit the iohub_config.yaml. The demo is currently
    set to use the LabJack U6 USB DAQ.
    """
    def run(self,*args):
        """
        The run method contains your experiment logic.
        It is equal to what would be in your main psychopy experiment
        script .py file in a standard psychopy experiment setup.
        """
        display=self.devices.display
        kb=self.devices.kb
        ain=self.devices.ain

        display_resolution=display.getPixelResolution()
        psychopy_monitor=display.getPsychopyMonitorName()
        unit_type=display.getCoordinateType()
        screen_index=display.getIndex()

        # Create a psychopy window, full screen resolution, full screen mode.
        window=visual.Window(display_resolution, monitor=psychopy_monitor,
                            units=unit_type, color=[128,128,128], colorSpace='rgb255',
                            fullscr=True, allowGUI=False, screen=screen_index)

        # Get the number of trials selected in the session dialog.
        #
        user_params=self.getUserDefinedParameters()
        print('user_params: ', user_params)
        trial_count=int(user_params.get('trial_count',5))


        # Create an ordered dictionary of psychopy stimuli.
        #   An ordered dictionary is one that returns keys in the order
        #   they are added, so you can use it to reference stim by a name
        #   or by 'zorder'.
        #
        psychoStim=OrderedDict()
        psychoStim['grating'] = visual.PatchStim(window, mask="circle",
                                size=150,pos=[0,0], sf=.075)

        psychoStim['title'] = visual.TextStim(window,
                              text="Analog Input Test. Trial 1 of %d"%(trial_count),
                              pos = [0,200], height=36, color=[1,.5,0],
                              colorSpace='rgb',
                              alignHoriz='center',alignVert='center',
                              wrapWidth=800.0)

        ai_values_string_proto="AI_0: %.3f\tAI_1: %.3f\tAI_2: %.3f\tAI_3: %.3f\t\nAI_4: %.3f\tAI_5: %.3f\tAI_6: %.3f\tAI_7: %.3f"
        ai_values=(0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0)
        psychoStim['analog_input_values'] = visual.TextStim(window,
                              text=ai_values_string_proto%ai_values,
                              pos = [0,-200], height=24, color=[1,1,0],
                              colorSpace='rgb',
                              alignHoriz='center',alignVert='center',
                              wrapWidth=800.0)

        psychoStim['instruction'] = visual.TextStim(window,
                              text="Press SPACE Key for Next Trial",
                              pos = [0,-300], height=36, color=[1,1,0.5],
                              colorSpace='rgb',
                              alignHoriz='center',alignVert='center',
                              wrapWidth=800.0)

        # Clear all events from the global and device level event buffers.
        self.hub.clearEvents('all')

        # Run a number of analog input recording /trials/
        #
        for i in range(trial_count):
            # Clear all events from the global and device level event buffers.
            psychoStim['title'].setText("Analog Input Test. Trial %d of %d"%(i+1,trial_count))
            self.hub.clearEvents('all')

            # Start streaming AnalogInput data.
            #
            ain.enableEventReporting(True)

            # Loop until we get a keyboard event where the
            #   SPACE key was pressed.
            #
            while 1:

                # For each retrace, update the grating phase
                #
                psychoStim['grating'].setPhase(0.05, '+')

                # Update analog input values to display
                #
                analog_input_events=ain.getEvents()
                if analog_input_events:
                    event_count=len(analog_input_events)
                    event=analog_input_events[-1]
                    ai_values=(event.AI_0,event.AI_1,event.AI_2,event.AI_3,
                               event.AI_4,event.AI_5,event.AI_6,event.AI_7)
                    psychoStim['analog_input_values'].setText(ai_values_string_proto%ai_values)

                # redraw the stim
                [psychoStim[stimName].draw() for stimName in psychoStim]

                # Flip, storing the time of the start of display update retrace.
                #
                flip_time=window.flip()


                # Send a message to the ioHub Process with indicating
                #   that a flip occurred and at what time.
                #
                self.hub.sendMessageEvent("Flip", sec_time=flip_time)

                # Get any new key values from keyboard *Char* Events.
                #
                key_values=[k.key for k in kb.getEvents(EventConstants.KEYBOARD_RELEASE)]

                if u' ' in key_values:
                    break

            # Clear the screen
            #
            window.flip()

            # Stop analog input recording
            #
            ain.enableEventReporting(False)

            # Delay 1/4 second before next trial
            #
            actualDelay=self.hub.wait(0.250)

        # All trials have been run. End demo....
        #   Wait 250 msec before ending the experiment
        actualDelay=self.hub.wait(0.250)

        print("Delay requested %.6f, actual delay %.6f, Diff: %.6f"%(0.250,actualDelay,actualDelay-0.250))

        ### End of experiment logic

###############################################################################


if __name__ == "__main__":
    import sys

    def main(configurationDirectory):
        """
        Creates an instance of the ExperimentRuntime class,
        and launches the experiment logic in run().
        """
        runtime=ExperimentRuntime(configurationDirectory, "experiment_config.yaml")
        runtime.start(sys.argv)

    # run the main function, which starts the experiment runtime
    main(module_directory(main))
