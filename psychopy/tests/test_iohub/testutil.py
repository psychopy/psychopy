import pytest

__author__ = 'Sol'

import psutil, sys
from psychopy.iohub import launchHubServer, Computer

getTime = Computer.getTime

from psychopy.tests import skip_under_vm


@skip_under_vm
def startHubProcess():
    io = launchHubServer()
    assert io != None

    io_proc = Computer.getIoHubProcess()
    io_proc_pid = io_proc.pid
    assert io_proc != None and io_proc_pid > 0

    return io


@skip_under_vm
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

skip_not_completed = pytest.mark.skipif("True",
                                       reason="Cannot be tested until the test is completed.")

skip_under_windoz = pytest.mark.skipif("sys.platform == 'win32'",
                                       reason="Cannot be tested under Windoz.")

skip_under_linux = pytest.mark.skipif("sys.platform.startswith('linux')",
                                       reason="Cannot be tested under Linux.")

skip_under_osx = pytest.mark.skipif("sys.platform == 'darwin'",
                                       reason="Cannot be tested under macOS.")
