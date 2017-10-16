#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Basic functions, including timing, rush (imported), quit
"""
# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function
from __future__ import division

from builtins import object
import sys
import threading
import subprocess
import shlex

# some things are imported just to be accessible within core's namespace
from psychopy.clock import (MonotonicClock, Clock, CountdownTimer,
                            wait, monotonicClock, getAbsTime,
                            StaticPeriod)  # pylint: disable=W0611

# always safe to call rush, even if its not going to do anything for a
# particular OS
from psychopy.platform_specific import rush  # pylint: disable=W0611
from psychopy import logging
from psychopy.constants import STARTED, NOT_STARTED, FINISHED, PY3

try:
    import pyglet
    havePyglet = True
    # may not want to check, to preserve terminal window focus
    checkPygletDuringWait = True
except ImportError:
    havePyglet = False
    checkPygletDuringWait = False


runningThreads = []  # just for backwards compatibility?
openWindows = []  # visual.Window updates this, event.py and clock.py use it

# Set getTime in core to == the monotonicClock instance created in the
# clockModule.
# The logging module sets the defaultClock to == clock.monotonicClock,
# so by default the core.getTime() and logging.defaultClock.getTime()
# functions return the 'same' timebase.
#
# This way 'all' OSs have a core.getTime() timebase that starts at 0.0 when
# the experiment is launched, instead of it being this way on Windows only
# (which was also a descripancy between OS's when win32 was using time.clock).


def getTime():
    """Get the current time since psychopy.core was loaded.

    Version Notes: Note that prior to PsychoPy 1.77.00 the behaviour of
    getTime() was platform dependent (on OSX and linux it was equivalent to
    :func:`psychopy.core.getAbsTime`
    whereas on windows it returned time since loading of the module, as now)
    """
    return monotonicClock.getTime()


def quit():
    """Close everything and exit nicely (ending the experiment)
    """
    # pygame.quit()  # safe even if pygame was never initialised
    logging.flush()
    
    for thisThread in threading.enumerate():
        if hasattr(thisThread, 'stop') and hasattr(thisThread, 'running'):
            # this is one of our event threads - kill it and wait for success
            thisThread.stop()
            while thisThread.running == 0:
                pass  # wait until it has properly finished polling

    sys.exit(0)  # quits the python session entirely


def shellCall(shellCmd, stdin='', stderr=False):
    """Call a single system command with arguments, return its stdout.
    Returns stdout, stderr if stderr is True.
    Handles simple pipes, passing stdin to shellCmd (pipes are untested
    on windows) can accept string or list as the first argument
    """
    if type(shellCmd) == str:
        # safely split into cmd+list-of-args, no pipes here
        shellCmdList = shlex.split(shellCmd)
    elif type(shellCmd) == bytes:
        # safely split into cmd+list-of-args, no pipes here
        shellCmdList = shlex.split(shellCmd.decode('utf-8'))
    elif type(shellCmd) in (list, tuple):  # handles whitespace in filenames
        shellCmdList = shellCmd
    else:
        return None, 'shellCmd requires a list or string'
    bytesObjects = []
    for obj in shellCmdList:
        if type(obj) != bytes:
            bytesObjects.append(obj.encode('utf-8'))
        else:
            bytesObjects.append(obj)
    proc = subprocess.Popen(bytesObjects, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdoutData, stderrData = proc.communicate(stdin)
    del proc
    if stderr:
        return stdoutData.strip(), stderrData.strip()
    else:
        return stdoutData.strip()
