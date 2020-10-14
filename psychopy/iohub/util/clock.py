# -*- coding: utf-8 -*-
from __future__ import division

from builtins import object
import sys
from .. import _ispkg

_getTime = None
MonotonicClock = None
monotonicClock = None

if _ispkg is False:
    import psychopy
    MonotonicClock = psychopy.clock.MonotonicClock
    monotonicClock = psychopy.clock.monotonicClock
    _getTime = monotonicClock.getTime
else:
    if sys.platform == 'win32':
        from ctypes import byref, c_int64, windll
        _fcounter = c_int64()
        _qpfreq = c_int64()
        windll.Kernel32.QueryPerformanceFrequency(byref(_qpfreq))
        _qpfreq = float(_qpfreq.value)
        _winQPC = windll.Kernel32.QueryPerformanceCounter

        def _getTime():
            _winQPC(byref(_fcounter))
            return _fcounter.value / _qpfreq
    elif sys.platform.startswith('linux'):
        from ctypes import byref, c_long, CDLL, Structure
        libc = CDLL('libc.so.6')
        CLOCK_MONOTONIC = 1

        class Timespec(Structure):
            _fields_ = [('tv_sec', c_long),
                        ('tv_nsec', c_long)]
        _ctime = Timespec()

        def _getTime():
            libc.clock_gettime(CLOCK_MONOTONIC, byref(_ctime))
            return _ctime.tv_sec + _ctime.tv_nsec / 1000000000.0
    elif sys.platform == "darwin":
        # Monotonic getTime with absolute origin. Suggested by @aforren1, and
        # copied from github.com/aforren1/toon/blob/master/toon/input/mac_clock.py 
        import ctypes
        _libc = ctypes.CDLL('/usr/lib/libc.dylib', use_errno=True)
        
        class mach_timebase_info_data_t(ctypes.Structure):
            _fields_ = (('numer', ctypes.c_uint32), ('denom', ctypes.c_uint32))
        
        _mach_absolute_time = _libc.mach_absolute_time
        _mach_absolute_time.restype = ctypes.c_uint64
        
        _timebase = mach_timebase_info_data_t()
        _libc.mach_timebase_info(ctypes.byref(_timebase))
        _ticks_per_second = _timebase.numer / _timebase.denom * 1.0e9
        
        def getTime():
            return _mach_absolute_time() / _ticks_per_second

    class MonotonicClock(object):
        """A convenient class to keep track of time in your experiments using a
        sub-millisecond timer.
        """

        def __init__(self, start_time=None):
            super(MonotonicClock, self).__init__()
            if start_time is None:
                # this is sub-millisec timer in python
                self._timeAtLastReset = _getTime()
            else:
                self._timeAtLastReset = start_time

        def getTime(self):
            """Returns the current time on this clock in secs (sub-ms precision)
            """
            return _getTime() - self._timeAtLastReset

        def getLastResetTime(self):
            """Returns the current offset being applied to the high resolution
            timebase used by Clock."""
            return self._timeAtLastReset

    monotonicClock = MonotonicClock()


def getTime():
    return monotonicClock.getTime()
