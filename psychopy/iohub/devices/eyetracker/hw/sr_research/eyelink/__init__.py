"""ioHub Common Eye Tracker Interface for EyeLink(C) Systems"""
 # Part of the psychopy.iohub library.
 # Copyright (C) 2012-2016 iSolver Software Solutions
 # Distributed under the terms of the GNU General Public License (GPL).
from ......util import addDirectoryToPythonPath
from ..... import Computer

if Computer.system == 'win32' and Computer.sysbits == 32:
    addDirectoryToPythonPath('devices/eyetracker/hw/sr_research/eyelink')

from .eyetracker import (EyeTracker, MonocularEyeSampleEvent,
                        BinocularEyeSampleEvent, FixationStartEvent,
                        FixationEndEvent, SaccadeStartEvent,
                        SaccadeEndEvent, BlinkStartEvent,BlinkEndEvent)
