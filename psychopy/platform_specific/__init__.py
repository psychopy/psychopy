"""Platform specific extensions (using ctypes)"""
# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys, platform

def rush(value=False): 
    #dummy method. Should be overridden by imports below if they exist and work
    #if we return something it means rush doesn't work on this platform
    return False
def waitForVBL():
    pass
    
if sys.platform=='win32':#NB includes vista and 7 (but not sure about vista64)
    from win32 import *
elif sys.platform=='darwin':
    from darwin import *
elif sys.platform.startswith('linux'):#normally 'linux2'
    from linux import *
elif sys.platform=='posix':#ever?!
    from posix import *

