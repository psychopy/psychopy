""" Test starting and stopping iohub server
"""

#from psychopy.visual import Window, ShapeStim
#from psychopy import event, core
#from psychopy.constants import NOT_STARTED

import pytest
import os

travis = bool(str(os.environ.get('TRAVIS')).lower() == 'true')

from psychopy.iohub import launchHubServer, Computer, EventConstants
from psychopy.core import getTime
    
def testDefaultServerLaunch():
    """
    """
    io=launchHubServer()
 
    io_proc = Computer.getIoHubProcess()
    io_proc_pid = io_proc.pid
    assert io != None and io_proc_pid > 0
    
    io.clearEvents('all')
    
    # check that a kb and mouse have been created
    keyboard=io.devices.keyboard
    mouse=io.devices.mouse

    assert keyboard != None
    assert mouse != None

    # wait for a kb event for 2.5 seconds; 
    # should timeout if no kb events occur.
    start_time = getTime()
    key_releases = keyboard.waitForRelease(2.5)
    end_time = getTime()
    assert end_time - start_time < 2.75    
    assert end_time - start_time > 2.25    
    assert len(key_releases) == 0


    # Check for no events.
    all_new_evts = io.getEvents()
    assert len(all_new_evts) == 0
    
    ## send 2 experiment msg events, getting current time they were sent    
    #
    io.sendMessageEvent("Test Message")
    io.sendMessageEvent("Test Message2")
    send_msg_time = getTime()   
    
    
    ## Test process priority setting
    #
    io.enableHighPriority()
    
    if Computer.system == 'win32':
        import psutil
        if psutil.version_info[0] >=2:
            assert io_proc.nice() == psutil.HIGH_PRIORITY_CLASS
        else:
            assert io_proc.get_nice() == psutil.HIGH_PRIORITY_CLASS
            
    elif Computer.system == 'linux2':
        import psutil
        if psutil.version_info[0] >=2:
            assert io_proc.nice() == 10
        else:
            assert io_proc.get_nice() == 10
            
    elif Computer.system == 'darwin':
        pass

    # Get the 2 exp. msg events sent before. Check that only 2 events exist, 
    # and that the time diff between the time msg's were sent and each 
    # msg.time iohub time stamp is very small. i.e. delay is low and 2 proc's
    # are using same time base.
    #      
    msg_events = io.getEvents(device_label = 'experiment')
    assert len(msg_events) == 2
    assert msg_events[0].text == "Test Message"
    assert msg_events[1].text == "Test Message2"
    assert send_msg_time - msg_events[0].time > 0 and send_msg_time - msg_events[0].time < 0.003
    assert send_msg_time - msg_events[1].time > 0 and send_msg_time - msg_events[1].time < 0.003
    
    # Check that iohub pid is valid and alive
    import psutil
    assert psutil.pid_exists(io_proc_pid)

    # Stop iohub server, ending process.    
    io.quit()
    
    # Enure iohub proc has terminated.
    assert not psutil.pid_exists(io_proc_pid)
    

if __name__ == '__main__':
    testDefaultLaunch()