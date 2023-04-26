# -*- coding: utf-8 -*-
"""
Created on Tue Apr 23 11:18:47 2013

Tests the psychopy.core.getTime Function:
  On Windows:
    1) Checks that the currently used core.getTime() implementation gives duration results
       consistent with directly using the Python high resolution timer.
    2) Checks that the time between core.getTime calls is never negative.
    3) Tests the overhead in the core.getTime function call
    4) Tries to assess the resolution of the underlying core.getTime() time base and the Python high resolution timer.
    5) Tests MonotonicClock, Clock, CountdownTimer, wait
@author: Sol

-----
Jan 2014, Jeremy Gray:
- Coverage of .quit, .shellCall, and increased coverage of StaticPeriod()
"""

import time
import sys
import numpy as np
import gc
import pytest

import psychopy
import psychopy.logging as logging
from psychopy.visual import Window
from psychopy.core import (getTime, MonotonicClock, Clock, CountdownTimer, wait,
                           StaticPeriod, shellCall)
from psychopy.clock import monotonicClock
from psychopy.tools import systemtools


def test_EmptyFunction():
    pass

PRINT_TEST_RESULTS = False


def printf(*args):
    if PRINT_TEST_RESULTS:
        for a in args:
            sys.stdout(a)
        print('')


py_time = None
py_timer_name = None

py_time=time.time
py_timer_name = 'time.time'


def printExceptionDetails():
    import traceback,pprint
    exc_type, exc_value, exc_traceback = sys.exc_info()
    pprint.pprint(exc_type, indent=1, width=80, depth=None)
    pprint.pprint(exc_value, indent=1, width=80, depth=None)
    pprint.pprint(traceback.format_tb(exc_traceback), indent=1, width=80, depth=None)


@pytest.mark.slow
def test_DelayDurationAccuracy(sample_size=100):
    # test with sample_size randomly selected durations between 0.05 and 1.0 msec
    durations=np.zeros((3,sample_size))
    durations[0,:] = (np.random.randint(50, 1001, sample_size) * 0.001)

    for t in range(sample_size):
        cdur=durations[0][t]
        start_times=py_time(),getTime()
        stime=start_times[0]
        while py_time()-stime<cdur-0.02:
            end_times=py_time(),getTime()
        while py_time()-stime<cdur:
            end_times=py_time(),getTime()
        durations[1][t]=end_times[0]-start_times[0]
        durations[2][t]=end_times[1]-start_times[1]

    clockDurVsExpected=durations[1]-durations[0]
    clockDurVsQpc=durations[1]-durations[2]

    printf("## %s vs. psychopy getTime() Duration Difference Test:\n"%(py_timer_name))
    printf(">> Actual Vs. Expected %s Duration Diffs (msec.usec):"%(py_timer_name))
    printf("\tmin:\t\t%.3f"%(clockDurVsExpected.min()*1000.0))
    printf("\tmax:\t\t%.3f"%(clockDurVsExpected.max()*1000.0))
    printf("\tmean:\t\t%.3f"%(clockDurVsExpected.mean()*1000.0))
    printf("\tstd:\t\t%.3f"%(clockDurVsExpected.std()*1000.0))
    printf(">> %s vs getTime Duration Diffs (msec.usec):"%(py_timer_name))
    printf("\tmin:\t\t%.3f"%(clockDurVsQpc.min()*1000.0))
    printf("\tmax:\t\t%.3f"%(clockDurVsQpc.max()*1000.0))
    printf("\tmean:\t\t%.3f"%(clockDurVsQpc.mean()*1000.0))
    printf("\tstd:\t\t%.3f"%(clockDurVsQpc.std()*1000.0))

    # check that the differences between time.clock and psychopy.getTime
    # (which is using Win QPC) are within these limits:
    #
    # fabs(min) or max diff:    < 50 usec
    # mean diff:                < 10 usec
    # std of diff:              < 5 usec
    try:
        assert np.fabs(clockDurVsQpc.min())<0.00005
        assert clockDurVsQpc.max()<0.00005
        assert np.fabs(clockDurVsQpc.mean())<0.00001
        assert clockDurVsQpc.std()<0.000005
        printf("\nDuration Difference Test: PASSED")
    except Exception:
        printf("\nDuration Difference Test: FAILED")
    printf("-------------------------------------\n")


@pytest.mark.slow
def test_TimebaseQuality(sample_size=1000):
    gc.disable()

    callTimes=np.zeros((5,sample_size))

    timer_clock_jumpbacks=0
    core_getTime_jumpbacks=0

    for t in range(sample_size):
       s=py_time()
       e=py_time()
       callTimes[0][t]=e-s
       if e<s:
           timer_clock_jumpbacks+=1

       s=getTime()
       e=getTime()
       callTimes[1][t]=e-s
       if e<s:
           core_getTime_jumpbacks+=1

       s=py_time()
       x=test_EmptyFunction()
       e=py_time()
       callTimes[2][t]=e-s

       s=py_time()
       x=py_time()
       e=py_time()
       callTimes[3][t]=e-s

       s=py_time()
       x=getTime()
       e=py_time()
       callTimes[4][t]=e-s


    gc.enable()

    printf("## Timebase 'Quality' Tests :\n")
    test_headers=(">> %s Resolution (msec.usec):"%(py_timer_name),
                  ">> core.getTime() Resolution (msec.usec):",
                  ">> Empty function (msec.usec):",
                  ">> %s (msec.usec):"%(py_timer_name),
                  ">> core.getTime() (msec.usec):")
    for i,header in enumerate(test_headers):
        printf(header)
        printf("\tmin:\t\t%.9f"%(callTimes[i].min()*1000.0))
        printf("\tmax:\t\t%.6f"%(callTimes[i].max()*1000.0))
        printf("\tmean:\t\t%.6f"%(callTimes[i].mean()*1000.0))
        printf("\tstd:\t\t%.6f"%(callTimes[i].std()*1000.0))

    printf(">> %s jumpbacks: "%(py_timer_name),timer_clock_jumpbacks)
    printf(">> core.getTime() jumpbacks: ",core_getTime_jumpbacks)

    # Test that these conditions are true:
    #   - Effective Resolution (mean inter timer call duration) of timer is < 10 usec
    #   - Maximum inter timer call duration is < 100 usec
    #   - no negative durations in timer call durations
    try:
        assert (callTimes[0].mean()*1000.0)<0.01
        assert (callTimes[0].max()*1000.0)<0.1
        assert timer_clock_jumpbacks==0
        printf("\n%s Call Time / Resolution Test: PASSED"%(py_timer_name))
    except Exception:
        printf("\n%s Call Time / Resolution Test: FAILED"%(py_timer_name))

    try:
        assert (callTimes[1].mean()*1000.0)<0.01
        assert (callTimes[1].max()*1000.0)<0.1
        assert core_getTime_jumpbacks==0
        printf("\ncore.getTime() Call Time / Resolution Test: PASSED")
    except Exception:
        printf("\ncore.getTime() Call Time / Resolution Test: FAILED")

    printf("-------------------------------------\n")


def test_MonotonicClock():
    try:
        mc = MonotonicClock()

        t1=mc.getTime()
        time.sleep(1.0)
        t2=mc.getTime()

        startTime=mc.getLastResetTime()

        assert t2>t1
        assert t2-t1 > 0.95
        assert t2-t1 < 1.05
        assert startTime > 0

        # Test things that 'should fail':
        try:
            x=mc.timeAtLastReset
            assert 1=="MonotonicClock should not have an attribute called 'timeAtLastReset'."
        except Exception:
            pass

        try:
            x=mc.reset()
            assert 1=="MonotonicClock should not have a method 'reset()'."
        except Exception:
            pass

        try:
            x=mc.add()
            assert 1=="MonotonicClock should not have a method 'add()'."
        except Exception:
            pass

        printf(">> MonotonicClock Test: PASSED")

    except Exception:
        printf(">> MonotonicClock Test: FAILED")
        printExceptionDetails()

    printf("-------------------------------------\n")


def test_Clock():
    try:
        c = Clock()

        t1=c.getTime()
        time.sleep(1.0)
        t2=c.getTime()

        startTime=c.getLastResetTime()

        assert t2>t1
        assert t2-t1 > 0.95
        assert t2-t1 < 1.05
        assert startTime > 0

        c.reset()
        t=c.getTime()
        assert t < 0.01

        c.reset(10)
        t=c.getTime()
        assert t > -10.0
        assert t < -9.9

        t1=c.getTime()
        c.add(50)
        t2=c.getTime()
        assert t2-t1 > -50.0
        assert t2-t1 < -49.9

        printf(">> Clock Test: PASSED")

    except Exception:
        printf(">> Clock Test: FAILED")
        printExceptionDetails()

    printf("-------------------------------------\n")


def test_CountdownTimer():
    try:
        cdt = CountdownTimer(5.0)

        assert cdt.getTime() <= 5.0
        assert cdt.getTime() >= 4.75

        time.sleep(cdt.getTime())

        assert np.fabs(cdt.getTime()) < 0.1

        printf(">> CountdownTimer Test: PASSED")

    except Exception:
        printf(">> CountdownTimer Test: FAILED")
        printExceptionDetails()

    printf("-------------------------------------\n")


def test_Wait(duration=1.55):
    try:
        t1=getTime()
        wait(duration)
        t2=getTime()

        # Check that the actual duration of the wait was close to the requested delay.
        #
        # Note that I have had to set this to a relatively high value of
        # 50 msec because on my Win7, i7, 16GB machine I would get delta's of up to
        # 35 msec when I was testing this.
        #
        # This is 'way high', and I think is because the current wait()
        # implementation polls pyglet for events during the CPUhog period.
        # IMO, during the hog period, which should only need to be only 1 - 2 msec
        # , not the 200 msec default now, nothing should be done but tight looping
        # waiting for the wait() to expire. This is what I do in ioHub and on this same
        # PC I get actual vs. requested duration delta's of < 100 usec consistently.
        #
        # I have not changed the wait in psychopy until feedback is given, as I
        # may be missing a reason why the current wait() implementation is required.
        #
        assert np.fabs((t2-t1)-duration) < 0.05

        printf(">> core.wait(%.2f) Test: PASSED"%(duration))

    except Exception:
        printf(">> core.wait(%.2f) Test: FAILED. Actual Duration was %.3f"%(duration,(t2-t1)))
        printExceptionDetails()

    printf("-------------------------------------\n")


def test_LoggingDefaultClock():
    try:
        t1 = logging.defaultClock.getTime()
        t2 = getTime()
        t3 = monotonicClock.getTime()

        assert np.fabs(t1-t2) < 0.02
        assert np.fabs(t1-t3) < 0.02
        assert np.fabs(t3-t2) < 0.02

        assert logging.defaultClock.getLastResetTime() == monotonicClock.getLastResetTime()

        printf(">> logging.defaultClock Test: PASSED")

    except Exception:
        printf(">> logging.defaultClock Test: FAILED. ")
        printExceptionDetails()

    printf("-------------------------------------\n")


@pytest.mark.staticperiod
def test_StaticPeriod():
    static = StaticPeriod()
    static.start(0.1)
    wait(0.05)
    assert static.complete()==1
    static.start(0.1)
    wait(0.11)
    assert static.complete()==0

    win = Window(autoLog=False)
    static = StaticPeriod(screenHz=60, win=win)
    static.start(.002)
    assert win.recordFrameIntervals is False
    static.complete()
    assert static._winWasRecordingIntervals == win.recordFrameIntervals
    win.close()

    # Test if screenHz parameter is respected, i.e., if after completion of the
    # StaticPeriod, 1/screenHz seconds are still remaining, so the period will
    # complete after the next flip.
    refresh_rate = 100.0
    period_duration = 0.1
    timer = CountdownTimer()
    win = Window(autoLog=False)

    static = StaticPeriod(screenHz=refresh_rate, win=win)
    static.start(period_duration)
    timer.reset(period_duration )
    static.complete()

    if systemtools.isVM_CI():
        tolerance = 0.01  # without a proper screen timing might not eb sub-ms
    else:
        tolerance = 0.001
    assert np.allclose(timer.getTime(),
                       1.0/refresh_rate,
                       atol=tolerance)
    win.close()


@pytest.mark.quit
def test_quit():
    # to-do: make some active threads
    with pytest.raises(SystemExit):
        psychopy.core.quit()


@pytest.mark.shellCall
class Test_shellCall():
    def setup_class(self):
        if sys.platform == 'win32':
            self.cmd = 'findstr'
        else:
            self.cmd = 'grep'

        self.msg = 'echo'

    def test_invalid_argument(self):
        with pytest.raises(TypeError):
            shellCall(12345)

    def test_stdin(self):
        echo = shellCall([self.cmd, self.msg], stdin=self.msg)
        assert echo == self.msg

        echo = shellCall(self.cmd + ' ' + self.msg, stdin=self.msg)
        assert echo == self.msg

    def test_stderr(self):
        _, se = shellCall([self.cmd, self.msg], stderr=True)
        assert se == ''

        _, se = shellCall(self.cmd + ' ' + self.msg, stderr=True)
        assert se == ''

    def test_stdin_and_stderr(self):
        echo, se = shellCall([self.cmd, self.msg], stdin='echo', stderr=True)
        assert echo == self.msg
        assert se == ''

        echo, se = shellCall(self.cmd + ' ' + self.msg, stdin='echo',
                             stderr=True)
        assert echo == self.msg
        assert se == ''

    def test_encoding(self):
        shellCall([self.cmd, self.msg], stdin=self.msg, encoding='utf-8')


if __name__ == '__main__':
    test_MonotonicClock()
    test_Clock()
    test_CountdownTimer()
    test_Wait()
    test_LoggingDefaultClock()
    test_TimebaseQuality()
    test_StaticPeriod()
    printf("\n** Next Test will Take ~ 1 minute...**\n")
    test_DelayDurationAccuracy()
