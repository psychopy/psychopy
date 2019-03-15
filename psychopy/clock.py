#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Tue Apr 23 11:28:32 2013

Provides the high resolution timebase used by psychopy, and defines some time
related utility Classes.

Moved functionality from core.py so a common code
base could be used in core.py and logging.py; vs. duplicating the getTime and
Clock logic.

@author: Sol
@author: Jon
"""
from __future__ import absolute_import, division, print_function
from builtins import object
import time
import sys
from pkg_resources import parse_version


try:
    import pyglet
except ImportError:
    pass  # pyglet is not installed

from psychopy.constants import STARTED, NOT_STARTED, FINISHED, PY3
import psychopy.logging  # Absolute import to work around circularity


# set the default timing mechanism
getTime = None


# Select the timer to use as the psychopy high resolution time base. Selection
# is based on OS and Python version.
#
# Three requirements exist for the psychopy time base implementation:
#     A) The Python interpreter does not apply an offset to the times returned
#        based on when the timer module being used was loaded or when the
#        timer function first called was first called.
#     B) The timer implementation used must be monotonic and report elapsed
#        time between calls, 'not' system or CPU usage time.
#     C) The timer implementation must provide a resolution of 50 usec or
#        better.
#
# Given the above requirements, psychopy selects a timer implementation as
# follows:
#     1) On Windows, the Windows Query Performance Counter API is used using
#        ctypes access.
#     2) On other OS's, if the Python version being used is 2.6 or lower,
#        time.time is used. For Python 2.7 and above, the timeit.default_timer
#        function is used.
try:
    import psychtoolbox
    havePTB = True
except ImportError:
    havePTB = False

if havePTB:
    # def getTime():
        # secs, wallTime, error = psychtoolbox.GetSecs('allclocks')
        # return wallTime
    getTime = psychtoolbox.GetSecs
elif sys.platform == 'win32':
    from ctypes import byref, c_int64, windll
    _fcounter = c_int64()
    _qpfreq = c_int64()
    windll.Kernel32.QueryPerformanceFrequency(byref(_qpfreq))
    _qpfreq = float(_qpfreq.value)
    _winQPC = windll.Kernel32.QueryPerformanceCounter
    def getTime():
        _winQPC(byref(_fcounter))
        return _fcounter.value / _qpfreq
elif sys.platform == "darwin":
    # Monotonic getTime with absolute origin. Suggested by @aforren1, and
    # copied from github.com/aforren1/toon/blob/master/toon/input/mac_clock.py 
    import ctypes
    _libc = ctypes.CDLL('/usr/lib/libc.dylib', use_errno=True)
    # create helper class to store data
    class mach_timebase_info_data_t(ctypes.Structure):
        _fields_ = (('numer', ctypes.c_uint32), ('denom', ctypes.c_uint32))
    # get function and set response type
    _mach_absolute_time = _libc.mach_absolute_time
    _mach_absolute_time.restype = ctypes.c_uint64
    # calculate timebase
    _timebase = mach_timebase_info_data_t()
    _libc.mach_timebase_info(ctypes.byref(_timebase))
    _ticks_per_second = _timebase.numer / _timebase.denom * 1.0e9
    #then define getTime func
    def getTime():
        return _mach_absolute_time() / _ticks_per_second
else:
    import timeit
    getTime = timeit.default_timer


class MonotonicClock(object):
    """A convenient class to keep track of time in your experiments using a
    sub-millisecond timer.

    Unlike the :class:`~psychopy.core.Clock` this cannot be reset to
    arbitrary times. For this clock t=0 always represents the time that
    the clock was created.

    Don't confuse this `class` with `core.monotonicClock` which is an
    `instance` of it that got created when PsychoPy.core was imported.
    That clock instance is deliberately designed always to return the
    time since the start of the study.

    Version Notes: This class was added in PsychoPy 1.77.00
    """

    def __init__(self, start_time=None):
        super(MonotonicClock, self).__init__()
        if start_time is None:
            # this is sub-millisec timer in python
            self._timeAtLastReset = getTime()
        else:
            self._timeAtLastReset = start_time

    def getTime(self):
        """Returns the current time on this clock in secs (sub-ms precision)
        """
        return getTime() - self._timeAtLastReset

    def getLastResetTime(self):
        """
        Returns the current offset being applied to the high resolution
        timebase used by Clock.
        """
        return self._timeAtLastReset

monotonicClock = MonotonicClock()


class Clock(MonotonicClock):
    """A convenient class to keep track of time in your experiments.
    You can have as many independent clocks as you like (e.g. one
    to time responses, one to keep track of stimuli...)

    This clock is identical to the :class:`~psychopy.core.MonotonicClock`
    except that it can also be reset to 0 or another value at any point.
    """

    def __init__(self):
        super(Clock, self).__init__()

    def reset(self, newT=0.0):
        """Reset the time on the clock. With no args time will be
        set to zero. If a float is received this will be the new
        time on the clock
        """
        self._timeAtLastReset = getTime() + newT

    def add(self, t):
        """Add more time to the clock's 'start' time (t0).

        Note that, by adding time to t0, you make the current time
        appear less. Can have the effect that getTime() returns a negative
        number that will gradually count back up to zero.

        e.g.::

            timer = core.Clock()
            timer.add(5)
            while timer.getTime()<0:
                # do something
        """
        self._timeAtLastReset += t


class CountdownTimer(Clock):
    """Similar to a :class:`~psychopy.core.Clock` except that time counts down
    from the time of last reset

    Typical usage::

        timer = core.CountdownTimer(5)
        while timer.getTime() > 0:  # after 5s will become negative
            # do stuff
    """

    def __init__(self, start=0):
        super(CountdownTimer, self).__init__()
        self._countdown_duration = start
        if start:
            self.add(start)

    def getTime(self):
        """Returns the current time left on this timer in secs
        (sub-ms precision)
        """
        return self._timeAtLastReset - getTime()

    def reset(self, t=None):
        if t is None:
            Clock.reset(self, self._countdown_duration)
        else:
            self._countdown_duration = t
            Clock.reset(self, t)


class StaticPeriod(object):
    """A class to help insert a timing period that includes code to be run.

    Typical usage::

        fixation.draw()
        win.flip()
        ISI = StaticPeriod(screenHz=60)
        ISI.start(0.5)  # start a period of 0.5s
        stim.image = 'largeFile.bmp'  # could take some time
        ISI.complete()  # finish the 0.5s, taking into account one 60Hz frame

        stim.draw()
        win.flip()  # the period takes into account the next frame flip
        # time should now be at exactly 0.5s later than when ISI.start()
        # was called

    """
    def __init__(self, screenHz=None, win=None, name='StaticPeriod'):
        """
        :param screenHz: the frame rate of the monitor (leave as None if you
            don't want this accounted for)
        :param win: if a visual.Window is given then StaticPeriod will
            also pause/restart frame interval recording
        :param name: give this StaticPeriod a name for more informative
            logging messages
        """
        self.status = NOT_STARTED
        self.countdown = CountdownTimer()
        self.name = name
        self.win = win
        if screenHz is None:
            self.frameTime = 0
        else:
            self.frameTime = 1.0 / screenHz

    def start(self, duration):
        """Start the period. If this is called a second time, the timer will
        be reset and starts again

        :param duration: The duration of the period, in seconds.
        """
        self.status = STARTED
        self.countdown.reset(duration - self.frameTime)
        # turn off recording of frame intervals throughout static period
        if self.win:
            self._winWasRecordingIntervals = self.win.recordFrameIntervals
            self.win.recordFrameIntervals = False

    def complete(self):
        """Completes the period, using up whatever time is remaining with a
        call to wait()

        :return: 1 for success, 0 for fail (the period overran)
        """
        self.status = FINISHED
        timeRemaining = self.countdown.getTime()
        if self.win:
            self.win.recordFrameIntervals = self._winWasRecordingIntervals
        if timeRemaining < 0:
            msg = ('We overshot the intended duration of %s by %.4fs. The '
                   'intervening code took too long to execute.')
            vals = self.name, abs(timeRemaining)
            psychopy.logging.warn(msg % vals)
            return 0
        else:
            wait(timeRemaining)
            return 1


def wait(secs, hogCPUperiod=0.2):
    """Wait for a given time period.

    If secs=10 and hogCPU=0.2 then for 9.8s python's time.sleep function
    will be used, which is not especially precise, but allows the cpu to
    perform housekeeping. In the final hogCPUperiod the more precise
    method of constantly polling the clock is used for greater precision.

    If you want to obtain key-presses during the wait, be sure to use
    pyglet and to hogCPU for the entire time, and then call
    :func:`psychopy.event.getKeys()` after calling
    :func:`~.psychopy.core.wait()`

    If you want to suppress checking for pyglet events during the wait,
    do this once::

        core.checkPygletDuringWait = False

    and from then on you can do::

        core.wait(sec)

    This will preserve terminal-window focus during command line usage.
    """
    from . import core

    # initial relaxed period, using sleep (better for system resources etc)
    if secs > hogCPUperiod:
        time.sleep(secs - hogCPUperiod)
        secs = hogCPUperiod  # only this much is now left

    # hog the cpu, checking time
    t0 = getTime()
    while (getTime() - t0) < secs:
        if not (core.havePyglet and core.checkPygletDuringWait):
            continue
        # let's see if pyglet collected any event in meantime
        try:
            # this takes focus away from command line terminal window:
            if parse_version(pyglet.version) < parse_version('1.2'):
                # events for sounds/video should run independently of wait()
                pyglet.media.dispatch_events()
        except AttributeError:
            # see http://www.pyglet.org/doc/api/pyglet.media-module.html#dispatch_events
            # Deprecated: Since pyglet 1.1, Player objects schedule themselves
            # on the default clock automatically. Applications should not call
            # pyglet.media.dispatch_events().
            pass
        for winWeakRef in core.openWindows:
            win = winWeakRef()
            if (win.winType == "pyglet" and
                    hasattr(win.winHandle, "dispatch_events")):
                win.winHandle.dispatch_events()  # pump events


def getAbsTime():
    """Return unix time (i.e., whole seconds elapsed since Jan 1, 1970).

    This uses the same clock-base as the other timing features,
    like `getTime()`. The time (in seconds) ignores the time-zone
    (like `time.time()` on linux). To take the timezone into account,
    use `int(time.mktime(time.gmtime()))`.

    Absolute times in seconds are especially useful to add to generated
    file names for being unique, informative (= a meaningful time stamp),
    and because the resulting files will always sort as expected when
    sorted in chronological, alphabetical, or numerical order, regardless
    of locale and so on.

    Version Notes: This method was added in PsychoPy 1.77.00
    """
    return int(time.mktime(time.localtime()))
