"""Platform specific extensions (using ctypes)"""
# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys

def rush():#dummy method. will be overridden by imports below
    pass

if sys.platform=='win32':
    from win32 import *
elif sys.platform=='darwin':
    from darwin import *
elif sys.platform.startswith('linux'):#normally 'linux2'
    from linux import *
elif sys.platform=='posix':#ever?!
    from posix import *

