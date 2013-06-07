"""Basic functions, including timing, rush (imported), quit
"""
# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys, threading
from clock import MonotonicClock, Clock, CountdownTimer, wait, monotonicClock, getAbsTime
# always safe to call rush, even if its not going to do anything for a particular OS
from psychopy.platform_specific import rush
from psychopy import logging
import subprocess, shlex

runningThreads=[] # just for backwards compatibility?

# Set getTime in core to == the monolithicClock instance created in the clockModule.
# The logging module sets the defaultClock to == clock.monolithicClock,
# so by default the core.getTime() and logging.defaultClock.getTime()
# functions return the 'same' timebase.
#
# This way 'all' OSs have a core.getTime() timebase that starts at 0.0 when the experiment 
# is launched, instead of it being this way on Windows only (which was also a 
# descripancy between OS's when win32 was using time.clock).
global getTime
getTime=monotonicClock.getTime
#getAbsTime=clock.getAbsTime  # imported

try:
    import pyglet
    havePyglet = True
    checkPygletDuringWait = True # may not want to check, to preserve terminal window focus
except:
    havePyglet = False
    checkPygletDuringWait = False

def quit():
    """Close everything and exit nicely (ending the experiment)
    """
    #pygame.quit() #safe even if pygame was never initialised
    logging.flush()
    for thisThread in threading.enumerate():
        if hasattr(thisThread,'stop') and hasattr(thisThread,'running'):
            #this is one of our event threads - kill it and wait for success
            thisThread.stop()
            while thisThread.running==0:
                pass#wait until it has properly finished polling
    sys.exit(0)#quits the python session entirely

def shellCall(shellCmd, stdin='', stderr=False):
    """Call a single system command with arguments, return its stdout.
    Returns stdout,stderr if stderr is True.
    Handles simple pipes, passing stdin to shellCmd (pipes are untested on windows)
    can accept string or list as the first argument
    """
    if type(shellCmd) == str:
        shellCmdList = shlex.split(shellCmd) # safely split into cmd+list-of-args, no pipes here
    elif type(shellCmd) == list: # handles whitespace in filenames
        shellCmdList = shellCmd
    else:
        return None, 'shellCmd requires a list or string'
    proc = subprocess.Popen(shellCmdList, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdoutData, stderrData = proc.communicate(stdin)
    del proc
    if stderr:
        return stdoutData.strip(), stderrData.strip()
    else:
        return stdoutData.strip()

