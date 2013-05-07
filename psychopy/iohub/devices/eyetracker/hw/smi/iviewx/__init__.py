"""
ioHub
ioHub Common Eye Tracker Interface
.. file: ioHub/devices/eyetracker/hw/smi/iviewx/__init__.py

Copyright (C) 2012-2013 XXXXXXXX, iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson + contributors
"""
#from ioHub import addDirectoryToPythonPath
#addDirectoryToPythonPath('devices/eyetracker/hw/smi/iviewx','bin')

from eyetracker import (EyeTracker, MonocularEyeSampleEvent, BinocularEyeSampleEvent,
                        FixationStartEvent,FixationEndEvent,SaccadeStartEvent,
                        SaccadeEndEvent,BlinkStartEvent,BlinkEndEvent)