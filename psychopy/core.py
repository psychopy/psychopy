"""Basic functions, including timing, rush (imported), quit
"""
# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys, threading
from clock import MonotonicClock, Clock, CountdownTimer, wait, monotonicClock, getAbsTime
# always safe to call rush, even if its not going to do anything for a particular OS
from psychopy.platform_specific import rush
from . import logging
from constants import STARTED, NOT_STARTED, FINISHED
import subprocess, shlex

runningThreads=[] # just for backwards compatibility?

# Set getTime in core to == the monotonicClock instance created in the clockModule.
# The logging module sets the defaultClock to == clock.monotonicClock,
# so by default the core.getTime() and logging.defaultClock.getTime()
# functions return the 'same' timebase.
#
# This way 'all' OSs have a core.getTime() timebase that starts at 0.0 when the experiment
# is launched, instead of it being this way on Windows only (which was also a
# descripancy between OS's when win32 was using time.clock).
def getTime():
    """Get the current time since psychopy.core was loaded.

    Version Notes: Note that prior to PsychoPy 1.77.00 the behaviour of getTime()
    was platform dependent (on OSX and linux it was equivalent to :func:`psychopy.core.getAbsTime`
    whereas on windows it returned time since loading of the module, as now)"""
    return monotonicClock.getTime()

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

class StaticPeriod(object):
    """A class to help insert a timing period that includes code to be run.

    Typical usage::

        fixation.draw()
        win.flip()
        ISI = StaticPeriod(screenHz=60)
        ISI.start(0.5) #start a period of 0.5s
        stim.image = 'largeFile.bmp' #could take some time
        ISI.complete() #finish the 0.5s, taking into account one 60Hz frame

        stim.draw()
        win.flip() #the period takes into account the next frame flip
        #time should now be at exactly 0.5s later than when ISI.start() was called

    """

    #NB - this might seem to be more sensible in the clock.py module, but that creates a circular reference
    # with the logging module.

    def __init__(self, screenHz=None, win=None, name='StaticPeriod'):
        """
        :param screenHz: the frame rate of the monitor (leave as None if you don't want this accounted for)
        :param name: if a visual.Window is given then StaticPeriod will also pause/restart frame interval recording
        :param name: give this StaticPeriod a name for more informative logging messages
        """
        self.status=NOT_STARTED
        self.countdown = CountdownTimer()
        self.name = name
        self.win = win
        if screenHz is None:
            self.frameTime = 0
        else:
            self.frameTime = 1.0/screenHz
    def start(self, duration):
        """Start the period. If this is called a second time, the timer will be reset and starts again
        """
        self.status = STARTED
        self.countdown.reset(duration)
        #turn off recording of frame intervals throughout static period
        if self.win:
            self.win.recordFrameIntervals = False
            self._winWasRecordingIntervals = self.win.recordFrameIntervals
    def complete(self):
        """Completes the period, using up whatever time is remaining with a call to wait()

        :return: 1 for success, 0 for fail (the period overran)
        """
        self.status=FINISHED
        timeRemaining = self.countdown.getTime()
        if self.win:
            self.win.recordFrameIntervals = self._winWasRecordingIntervals
        if timeRemaining<0:
            import logging#we only do this if we need it - circular import
            logging.warn('We overshot the intended duration of %s by %.4fs. The intervening code took too long to execute.' %(self.name, abs(timeRemaining)))
            return 0
        else:
            wait(timeRemaining)
            return 1
