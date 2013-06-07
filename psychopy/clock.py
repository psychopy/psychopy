# -*- coding: utf-8 -*-
"""
Created on Tue Apr 23 11:28:32 2013

Provides the high resolution timebase used by psychopy, and defines some
time related utility Classes. 

Moved functionality from core.py so a common code
base could be used in core.py and logging.py; vs. duplicating the getTime and
Clock logic.

@author: Sol
"""
from __future__ import division
import time
import sys

try:
    import pyglet
except:
    pass # pyglet is not installed
    
    
#set the default timing mechanism
getTime=None

# Select the timer to use as the psychopy high resolution time base. Selection
# is based on OS and Python version. 
# 
# Three requirements exist for the psychopy time base implementation:
#     A) The Python interpreter does not apply an offset to the times returned
#        based on when the timer module being used was loaded or when the timer 
#        fucntion first called was first called. 
#     B) The timer implementation used must be monotonic and report elapsed time
#        between calls, 'not' system or CPU usage time. 
#     C) The timer implementation must provide a resolution of 50 usec or better.
#
# Given the above requirements, psychopy selects a timer implementation as follows:
#     1) On Windows, the Windows Query Performance Counter API is used using ctypes access.
#     2) On other OS's, if the Python version being used is 2.6 or lower,
#        time.time is used. For Python 2.7 and above, the timeit.default_timer
#        function is used.
if sys.platform == 'win32':
    global _fcounter, _qpfreq, _winQPC
    from ctypes import byref, c_int64, windll
    _fcounter = c_int64()
    _qpfreq = c_int64()
    windll.Kernel32.QueryPerformanceFrequency(byref(_qpfreq))
    _qpfreq=float(_qpfreq.value)
    _winQPC=windll.Kernel32.QueryPerformanceCounter

    def getTime():
        _winQPC(byref(_fcounter))
        return  _fcounter.value/_qpfreq
else:
    cur_pyver = sys.version_info
    if cur_pyver[0]==2 and cur_pyver[1]<=6: 
        getTime = time.time
    else:
        import timeit
        getTime = timeit.default_timer

class MonotonicClock:
    """
    A convenient class to keep track of time in your experiments.
    When a MonotonicClock is created, it stores the current time
    from getTime and uses this as an offset for psychopy times returned.
    """
    def __init__(self,start_time=None):
        if start_time is None:
            self._timeAtLastReset=getTime()#this is sub-millisec timer in python
        else:
            self._timeAtLastReset=start_time

    def getTime(self):
        """Returns the current time on this clock in secs (sub-ms precision)
        """
        return getTime()-self._timeAtLastReset
        
    def getLastResetTime(self):
        """ 
        Returns the current offset being applied to the high resolution 
        timebase used by Clock.
        """
        return self._timeAtLastReset

monotonicClock=MonotonicClock()

class Clock(MonotonicClock):
    """A convenient class to keep track of time in your experiments.
    You can have as many independent clocks as you like (e.g. one
    to time responses, one to keep track of stimuli...)
    The clock uses a a sub-millisec timer selected based on OS and Python version
    being used. i.e. the times reported will be more accurate than you need!
    """
    def __init__(self):
        MonotonicClock.__init__(self)
                        
    def reset(self, newT=0.0):
        """Reset the time on the clock. With no args time will be
        set to zero. If a float is received this will be the new
        time on the clock
        """
        self._timeAtLastReset=getTime()+newT

    def add(self,t):
        """Add more time to the clock's 'start' time (t0).

        Note that, by adding time to t0, you make the current time appear less.
        Can have the effect that getTime() returns a negative number that will
        gradually count back up to zero.

        e.g.::

            timer = core.Clock()
            timer.add(5)
            while timer.getTime()<0:
                #do something
        """
        self._timeAtLastReset += t

class CountdownTimer(Clock):
    """Similar to a Clock except that time counts down from the time of last reset

    Typical usage::

        timer = core.CountdownTimer(5)
        while timer.getTime() > 0:  # after 5s will become negative
            #do stuff
    """
    def __init__(self, start=0):
        Clock.__init__(self)
        if start:
            self.add(start)

    def getTime(self):
        """Returns the current time left on this timer in secs (sub-ms precision)
        """
        return self._timeAtLastReset-getTime()

def wait(secs, hogCPUperiod=0.2):
    """Wait for a given time period.

    If secs=10 and hogCPU=0.2 then for 9.8s python's time.sleep function will be used,
    which is not especially precise, but allows the cpu to perform housekeeping. In
    the final hogCPUperiod the more precise method of constantly polling the clock
    is used for greater precision.

    If you want to obtain key-presses during the wait, be sure to use pyglet and
    to hogCPU for the entire time, and then call :func:`psychopy.event.getKeys()` after calling :func:`~.psychopy.core.wait()`

    If you want to suppress checking for pyglet events during the wait, do this once::
        core.checkPygletDuringWait = False

    and from then on you can do::
        core.wait(sec)

    This will preserve terminal-window focus during command line usage.
    """
    import core
    
    #initial relaxed period, using sleep (better for system resources etc)
    if secs>hogCPUperiod:
        time.sleep(secs-hogCPUperiod)
        secs=hogCPUperiod#only this much is now left

    #hog the cpu, checking time
    t0=getTime()
    while (getTime()-t0)<secs:
        if not (core.havePyglet and core.checkPygletDuringWait):
            continue
        #let's see if pyglet collected any event in meantime
        try:
            # this takes focus away from command line terminal window:
            pyglet.media.dispatch_events()#events for sounds/video should run independently of wait()
            wins = pyglet.window.get_platform().get_default_display().get_windows()
            for win in wins: win.dispatch_events()#pump events on pyglet windows
        except:
            pass #presumably not pyglet

def getAbsTime():
    """Return unix time (i.e., whole seconds elapsed since Jan 1, 1970).

    This uses the same clock-base as the other timing features, like `getTime()`.
    The time (in seconds) ignores the time-zone (like `time.time()` on linux).
    To take the timezone into account, use `int(time.mktime(time.gmtime()))`.

    Absolute times in seconds are especially useful to add to generated file
    names for being unique, informative (= a meaningful time stamp), and because
    the resulting files will always sort as expected when sorted in chronological,
    alphabetical, or numerical order, regardless of locale and so on.
    """
    return int(time.mktime(time.localtime()))

