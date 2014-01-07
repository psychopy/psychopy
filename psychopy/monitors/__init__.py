# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import os, sys
import calibTools
from calibTools import *

#create a test monitor if there isn't one already
if 'testMonitor' not in calibTools.getAllMonitors():
    defMon = Monitor('testMonitor',
        width=30,
        distance=57,
        gamma=1.0,
        notes='default (not very useful) monitor')
    defMon.setSizePix([1024,768])
    defMon.saveMon()
