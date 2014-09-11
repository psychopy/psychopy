__author__ = 'Sol'

import psutil
from psychopy.iohub import launchHubServer, Computer

from psychopy.tests.utils import skip_under_travis

@skip_under_travis
def startHubProcess():
    io = launchHubServer()
    assert io != None

    io_proc = Computer.getIoHubProcess()
    io_proc_pid = io_proc.pid
    assert io_proc != None and io_proc_pid > 0

    return io

@skip_under_travis
def stopHubProcess():
    from psychopy.iohub.client import ioHubConnection

    io = ioHubConnection.getActiveConnection()
    assert io != None

    io_proc = Computer.getIoHubProcess()
    io_proc_pid = io_proc.pid
    assert io_proc != None and psutil.pid_exists(io_proc_pid)

    # Stop iohub server, ending process.
    io.quit()

    # Enure iohub proc has terminated.
    assert not psutil.pid_exists(io_proc_pid)

    assert ioHubConnection.getActiveConnection() is None
