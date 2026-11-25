#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Calling functions when a frame is presented on screen, rather than when
the flip which submits it returns, see :meth:`Window.callOnPresent`.

The calls are made on a thread of their own, which waits for the predicted
presentation time with the operating system's absolute-deadline sleep. That
releases the GIL and uses no CPU while waiting, so other threads (drawing, or
audio callbacks) aren't held up by it. The thread raises its own priority so
it's woken on time (on macOS, it would otherwise be woken ~1 ms late), and
the interval at which CPython hands the GIL between threads is lowered while
it runs, so it isn't held up once woken.
"""

__all__ = [
    'PresentCall',
    'PresentCallScheduler',
]

import collections
import ctypes
import ctypes.util
import sys
import threading
import time
import traceback

from psychopy import logging
from psychopy import clock as _clock

# Interval (s) at which CPython hands the GIL between threads which want it,
# while a scheduler is running. With the default (5 ms), a call due while the
# main thread is running Python is made up to 5 ms late. At 0.1 ms, measured
# on macOS, calls were ~0.12 ms late with the main thread busy, and it lost
# no measurable throughput, as the scheduler only wants the GIL once a frame.
SWITCH_INTERVAL = 0.0001


def _makeWaiterDarwin():
    libc = ctypes.CDLL(ctypes.util.find_library('c') or '/usr/lib/libc.dylib')
    machAbsoluteTime = libc.mach_absolute_time
    machAbsoluteTime.restype = ctypes.c_uint64
    machWaitUntil = libc.mach_wait_until
    machWaitUntil.restype = ctypes.c_int
    machWaitUntil.argtypes = [ctypes.c_uint64]

    class _TimebaseInfo(ctypes.Structure):
        _fields_ = [('numer', ctypes.c_uint32), ('denom', ctypes.c_uint32)]

    info = _TimebaseInfo()
    libc.mach_timebase_info(ctypes.byref(info))
    secsPerTick = info.numer / info.denom / 1e9

    def machSeconds():
        return machAbsoluteTime() * secsPerTick

    def waitUntil(t):
        deadline = t - _clock.measureClockOffset(machSeconds, nSamples=11)
        machWaitUntil(int(deadline / secsPerTick))

    return waitUntil


def _makeWaiterLinux():
    libc = ctypes.CDLL(ctypes.util.find_library('c') or 'libc.so.6',
                       use_errno=True)

    class _Timespec(ctypes.Structure):
        _fields_ = [('tv_sec', ctypes.c_long), ('tv_nsec', ctypes.c_long)]

    clockNanosleep = libc.clock_nanosleep
    clockNanosleep.restype = ctypes.c_int
    clockNanosleep.argtypes = [
        ctypes.c_int, ctypes.c_int, ctypes.POINTER(_Timespec), ctypes.c_void_p]
    CLOCK_MONOTONIC, TIMER_ABSTIME, EINTR = 1, 1, 4

    def monotonicSeconds():
        return time.clock_gettime(time.CLOCK_MONOTONIC)

    def waitUntil(t):
        deadline = t - _clock.measureClockOffset(monotonicSeconds, nSamples=11)
        secs = int(deadline)
        spec = _Timespec(secs, int((deadline - secs) * 1e9))
        # an absolute deadline can just be waited for again if interrupted
        while clockNanosleep(
                CLOCK_MONOTONIC, TIMER_ABSTIME, ctypes.byref(spec), None) == EINTR:
            pass

    return waitUntil


def _makeWaiterWin32():
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateWaitableTimerExW.restype = ctypes.c_void_p
    kernel32.CreateWaitableTimerExW.argtypes = [
        ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32]
    kernel32.SetWaitableTimer.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(ctypes.c_int64), ctypes.c_long,
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
    kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    CREATE_WAITABLE_TIMER_HIGH_RESOLUTION = 0x2
    TIMER_ALL_ACCESS = 0x1F0003
    INFINITE = 0xFFFFFFFF

    # high resolution timers need Windows 10 1803 or later
    timer = kernel32.CreateWaitableTimerExW(
        None, None, CREATE_WAITABLE_TIMER_HIGH_RESOLUTION, TIMER_ALL_ACCESS)
    if not timer:
        timer = kernel32.CreateWaitableTimerExW(None, None, 0, TIMER_ALL_ACCESS)
    if not timer:
        raise OSError("Unable to create a waitable timer")

    def waitUntil(t):
        remaining = t - _clock.getTime()
        if remaining <= 0:
            return
        # a negative due time is relative, in 100 ns units
        dueTime = ctypes.c_int64(-int(remaining * 1e7))
        kernel32.SetWaitableTimer(
            timer, ctypes.byref(dueTime), 0, None, None, 0)
        kernel32.WaitForSingleObject(timer, INFINITE)

    return waitUntil


def _raisePriorityDarwin():
    # Without this, macOS coalesces the thread's timer wake-ups, so it wakes
    # around a millisecond late. Real-time threads are woken on time. The
    # thread computes little each time it wakes, as the constraint says, or
    # macOS would demote it.
    libc = ctypes.CDLL(ctypes.util.find_library('c') or '/usr/lib/libc.dylib')

    class _TimebaseInfo(ctypes.Structure):
        _fields_ = [('numer', ctypes.c_uint32), ('denom', ctypes.c_uint32)]

    class _TimeConstraintPolicy(ctypes.Structure):
        _fields_ = [
            ('period', ctypes.c_uint32), ('computation', ctypes.c_uint32),
            ('constraint', ctypes.c_uint32), ('preemptible', ctypes.c_int)]

    info = _TimebaseInfo()
    libc.mach_timebase_info(ctypes.byref(info))
    ticksPerMs = 1e6 * info.denom / info.numer
    policy = _TimeConstraintPolicy(
        int(10 * ticksPerMs), int(0.5 * ticksPerMs), int(1 * ticksPerMs), 1)

    libc.pthread_self.restype = ctypes.c_void_p
    libc.pthread_mach_thread_np.restype = ctypes.c_uint
    libc.pthread_mach_thread_np.argtypes = [ctypes.c_void_p]
    THREAD_TIME_CONSTRAINT_POLICY, POLICY_COUNT = 2, 4
    if libc.thread_policy_set(
            libc.pthread_mach_thread_np(libc.pthread_self()),
            THREAD_TIME_CONSTRAINT_POLICY, ctypes.byref(policy), POLICY_COUNT):
        raise OSError("thread_policy_set failed")


def _raisePriorityLinux():
    # wake as close to the deadline as the kernel can (the default slack is
    # 50 us), which needs no privileges, unlike real-time scheduling
    libc = ctypes.CDLL(ctypes.util.find_library('c') or 'libc.so.6')
    PR_SET_TIMERSLACK = 29
    if libc.prctl(PR_SET_TIMERSLACK, ctypes.c_ulong(1), 0, 0, 0):
        raise OSError("prctl(PR_SET_TIMERSLACK) failed")


def _raisePriorityWin32():
    kernel32 = ctypes.windll.kernel32
    kernel32.GetCurrentThread.restype = ctypes.c_void_p
    THREAD_PRIORITY_TIME_CRITICAL = 15
    if not kernel32.SetThreadPriority(
            ctypes.c_void_p(kernel32.GetCurrentThread()),
            THREAD_PRIORITY_TIME_CRITICAL):
        raise OSError("SetThreadPriority failed")


def raiseThreadPriority():
    """Have the calling thread woken as close as possible to the deadlines it
    waits for, as far as the operating system allows without privileges."""
    if sys.platform == 'darwin':
        raiser = _raisePriorityDarwin
    elif sys.platform == 'win32':
        raiser = _raisePriorityWin32
    elif sys.platform.startswith('linux'):
        raiser = _raisePriorityLinux
    else:
        return
    try:
        raiser()
    except Exception as err:
        logging.debug(
            "Unable to raise the priority of the thread making calls on "
            "presentation, so they may be late: {}".format(err))


def _waitUntilSleeping(t):
    """Fallback for waiting until a raw time, with `time.sleep`."""
    remaining = t - _clock.getTime()
    if remaining > 0:
        time.sleep(remaining)


def makeWaiter():
    """A function which waits until a time on the raw timebase (as returned
    by :func:`psychopy.clock.getTime`) without holding the GIL or spinning,
    using the operating system's absolute-deadline sleep where possible.
    """
    makers = {
        'darwin': _makeWaiterDarwin,
        'win32': _makeWaiterWin32,
    }
    maker = makers.get(sys.platform)
    if maker is None and sys.platform.startswith('linux'):
        maker = _makeWaiterLinux
    if maker is not None:
        try:
            return maker()
        except Exception as err:
            logging.debug(
                "Unable to use the OS's deadline sleep for calls on "
                "presentation, using time.sleep: {}".format(err))

    return _waitUntilSleeping


class PresentCall:
    """A function to call when a frame is presented on screen, as returned
    by :meth:`Window.callOnPresent`, which records when it was called.

    Times are on the clock used for logging, as `Timestamp`s.

    Attributes
    ----------
    tTarget : Timestamp or None
        When the call was due: the predicted presentation time of its frame.
        `None` until the frame is flipped.
    tCalled : Timestamp or None
        When the function was called. `None` until it has been.
    tOnset : Timestamp or None
        Recorded presentation time of the frame (see
        `Window.lastFlipTimeSource`). `None` until the frame is flipped.

    """
    def __init__(self, function, args, kwargs):
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self._tTargetRaw = None
        self._tCalledRaw = None
        self.tOnset = None
        self.called = threading.Event()

    @property
    def tTarget(self):
        if self._tTargetRaw is None:
            return None
        return logging.defaultClock.timestampFromRaw(self._tTargetRaw)

    @property
    def tCalled(self):
        if self._tCalledRaw is None:
            return None
        return logging.defaultClock.timestampFromRaw(self._tCalledRaw)

    @property
    def lateBy(self):
        """How long after it was due the function was called, in seconds
        (`None` if it hasn't been yet)."""
        if self._tCalledRaw is None or self._tTargetRaw is None:
            return None
        return self._tCalledRaw - self._tTargetRaw

    @property
    def error(self):
        """How long after the recorded presentation time of its frame the
        function was called, in seconds: negative if before (`None` if
        either isn't known yet)."""
        tCalled = self.tCalled
        if tCalled is None or self.tOnset is None:
            return None
        return float(tCalled) - float(self.tOnset)

    def _call(self):
        self._tCalledRaw = _clock.getTime()
        try:
            self.function(*self.args, **self.kwargs)
        except Exception:
            logging.error(
                "Error in function called on presentation:\n{}".format(
                    traceback.format_exc()))
        finally:
            self.called.set()

    def __repr__(self):
        return "<PresentCall {} tCalled={}>".format(
            getattr(self.function, '__name__', self.function), self.tCalled)


class PresentCallScheduler:
    """Calls functions at the predicted presentation times of their frames,
    on a thread of its own, which is started by :meth:`start`, or when first
    needed.

    Once it has been given calls to make, the interval at which CPython hands
    the GIL between threads is lowered to `SWITCH_INTERVAL`, so a call isn't
    held up waiting for the main thread to let go of it.
    """
    # number of schedulers which have lowered the switch interval, and what it
    # was before the first did
    _nRunning = 0
    _savedSwitchInterval = None
    _runningLock = threading.Lock()

    def __init__(self):
        self._queue = collections.deque()
        self._condition = threading.Condition()
        self._thread = None
        self._stopped = False
        self._switchIntervalLowered = False
        self._waitUntil = None

    def start(self):
        """Start the thread which makes the calls, if it isn't running yet.

        Starting a thread can hold up the next buffer swap (by a couple of
        refreshes, measured on Windows with NVIDIA graphics, the first time a
        thread is started), so `Window` starts it when it's created rather
        than on the frame of the first call.
        """
        with self._condition:
            if self._thread is None and not self._stopped:
                self._start()

    def schedule(self, calls, tTarget):
        """Call functions at a time.

        Parameters
        ----------
        calls : list[PresentCall]
            Calls to make, in order.
        tTarget : float
            Raw time (on the clock :func:`psychopy.clock.getTime` reads) to
            call them at. If it has passed, they're called straight away.

        """
        with self._condition:
            if self._stopped:
                return
            if calls and not self._switchIntervalLowered:
                self._lowerSwitchInterval()
            for call in calls:
                call._tTargetRaw = tTarget
                self._queue.append(call)
            if self._thread is None:
                self._start()
            self._condition.notify()

    def _lowerSwitchInterval(self):
        with PresentCallScheduler._runningLock:
            if PresentCallScheduler._nRunning == 0:
                PresentCallScheduler._savedSwitchInterval = sys.getswitchinterval()
                sys.setswitchinterval(
                    min(SWITCH_INTERVAL, PresentCallScheduler._savedSwitchInterval))
            PresentCallScheduler._nRunning += 1
        self._switchIntervalLowered = True

    def _start(self):
        self._thread = threading.Thread(
            target=self._run, name="PresentCallScheduler", daemon=True)
        self._thread.start()

    def _run(self):
        raiseThreadPriority()
        self._waitUntil = makeWaiter()
        while True:
            with self._condition:
                while not self._queue and not self._stopped:
                    self._condition.wait()
                if self._stopped:
                    return
                call = self._queue.popleft()
            self._waitUntil(call._tTargetRaw)
            call._call()

    def stop(self, timeout=1.0):
        """Stop calling functions, dropping any not yet called, and restore
        the switch interval if no other scheduler is running."""
        with self._condition:
            if self._stopped:
                return
            self._stopped = True
            self._queue.clear()
            self._condition.notify()
            thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout)
        if not self._switchIntervalLowered:
            return
        self._switchIntervalLowered = False
        with PresentCallScheduler._runningLock:
            PresentCallScheduler._nRunning -= 1
            if PresentCallScheduler._nRunning == 0:
                sys.setswitchinterval(PresentCallScheduler._savedSwitchInterval)
