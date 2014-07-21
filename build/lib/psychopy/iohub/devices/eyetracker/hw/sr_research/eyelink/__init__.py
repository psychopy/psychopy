"""
ioHub
Common Eye Tracker Interface
.. file: ioHub/devices/eyeTracker/hw/sr_research/eyelink/__init__.py

Copyright (C) 2012-2013 iSolver Software Solutions

Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

from psychopy.iohub.util import addDirectoryToPythonPath

addDirectoryToPythonPath('devices/eyetracker/hw/sr_research/eyelink')

from eyetracker import (EyeTracker, MonocularEyeSampleEvent, BinocularEyeSampleEvent,
                        FixationStartEvent,FixationEndEvent,SaccadeStartEvent,
                        SaccadeEndEvent,BlinkStartEvent,BlinkEndEvent)
