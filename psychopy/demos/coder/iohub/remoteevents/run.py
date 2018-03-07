#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
pub_sub_device/run.py

EventPublisher / RemoteEventSubscriber Devices usage Demo. 

For simplicity, both the EventPublisher and RemoteEventSubscriber run on the
local computer. The EventPublisher publishes all keyboard event types, and the 
RemoteEventSubscriber subscribes to only KeyboardPressEvents, and KeyboardCharEvents.

** IMPORTANT: The Python package 'pyzmq' must be available in your python
    environment to be able to use the EventPublisher and / or RemoteEventSubscriber
    devices. The pyzmq website is https://github.com/zeromq/pyzmq
    
Initial Version: July 17th, 2013, Sol Simpson
"""
from __future__ import absolute_import, division, print_function

from psychopy.iohub import (ioHubExperimentRuntime, MessageDialog,
                            module_directory,Computer)

class ExperimentRuntime(ioHubExperimentRuntime):
    """
    Create an experiment using psychopy and the ioHub framework by extending the 
    ioHubExperimentRuntime class.
    """
    def run(self,*args):
        """
        The run method contains your experiment logic. It is equal to what 
        would be in your main psychopy experiment script.py file in a standard 
        psychopy experiment setup. That is all there is too it really.
        """
        run_demo=True
     
        kb=self.hub.devices.kb
        evt_sub=self.hub.devices.evt_sub
            
        # This demo does not display a PsychoPy window, instead it just prints
        # keyboard event info. received from the local keyboard device and keyboard
        # events received from the RemoteEventSubscriber device. Inform the user of this...
        # 
        msg_dialog=MessageDialog("This demo does not create a PsychoPy window.\nInstead local and subscribed keyboard event info is simply printed to stdout.\n\nOnce the demo has started, press 'ESCAPE' to quit.\n\nPress OK to continue or Cancel to abort the demo.",
                     title="PsychoPy.ioHub PUB - SUB Event Demo", 
                     dialogType=MessageDialog.IMPORTANT_DIALOG,display_index=0)

        if msg_dialog.show() == MessageDialog.OK_RESULT:
            # wait until 'ESCAPE' is pressed, or quit after 15 seconds of no kb events.
            self.hub.clearEvents('all')
            last_event_time=Computer.getTime()
            while run_demo is True and Computer.getTime()-last_event_time<15.0:
                local_kb_events=kb.getEvents()
                for event in local_kb_events:
                    print('* Local KB Event: {etime}\t{ekey}\t{edelay}'.format(
                        etime=event.time,ekey=event.key,edelay=event.delay))
                    last_event_time=event.time
                    if event.key == u'ESCAPE':
                        run_demo=False
                        break
                subscribed_kb_events=evt_sub.getEvents()
                for event in subscribed_kb_events:
                    print('# Subscribed KB Event: {etime}\t{ekey}\t{edelay}'.format(
                        etime=event.time, ekey=event.key,edelay=event.delay))
                self.hub.wait(0.1)

        ### End of experiment logic

####### Main Script Launching Code Below #######

if __name__ == "__main__":
    def main(configurationDirectory):
        """
        Creates an instance of the ExperimentRuntime class, launches the experiment logic.
        """        
        runtime=ExperimentRuntime(configurationDirectory, "experiment_config.yaml")    
        runtime.start(configurationDirectory)

    # Get the current directory, using a method that does not rely on __FILE__
    # or the accuracy of the value of __FILE__.
    #
    configurationDirectory=module_directory(main)

    # Run the main function, which starts the experiment runtime
    #
    main(configurationDirectory)
