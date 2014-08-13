"""Platform specific extensions (using ctypes)"""
# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys, platform

#dummy methods Should be overridden by imports below if they exist
def rush(value=False):
    """
    """
    #dummy method.
    return False
def waitForVBL():
    """DEPRECATED: waiting for a VBL is handled by the screen flip
    """
    return False
def sendStayAwake():
    """Sends a signal to your system to indicate that the computer is in use and
    should not sleep. This should be sent periodically, but PsychoPy will send
    the signal by default on each screen refresh.
    Added: v1.79.00

    Currently supported on: windows, OS X
    """
    return False

if sys.platform=='win32':#NB includes vista and 7 (but not sure about vista64)
    from win32 import *
elif sys.platform=='darwin':
    from darwin import *
elif sys.platform.startswith('linux'):#normally 'linux2'
    from linux import *
elif sys.platform=='posix':#ever?!
    from posix import *

