""" Test starting and stopping iohub server
"""

#from psychopy.visual import Window, ShapeStim
#from psychopy import event, core
#from psychopy.constants import NOT_STARTED

import pytest
import os

imports_ok = False
launchHubServer = None

travis = bool(str(os.environ.get('TRAVIS')).lower() == 'true')

try:
    from psychopy.iohub import launchHubServer, Computer
    imports_ok = True
except:
    print "psychopy.iohub could not be imported:"
    import traceback
    traceback.print_exc()
    
def testDefaultServerLaunch():
    """
    """
    io = launchHubServer()

    io_proc = Computer.getIoHubProcess()
    io_proc_pid = io_proc.pid
    assert io != None and io_proc_pid > 0

    # check that a kb and mouse have been created
    keyboard=io.devices.keyboard
    mouse=io.devices.mouse

    assert keyboard != None
    assert mouse != None

    # Check that iohub pid is valid and alive
    import psutil
    assert psutil.pid_exists(io_proc_pid)

    # Stop iohub server, ending process.    
    io.quit()
    
    # Enure iohub proc has terminated.
    assert not psutil.pid_exists(io_proc_pid)
    

if __name__ == '__main__':
    if imports_ok is True:
        testDefaultServerLaunch()