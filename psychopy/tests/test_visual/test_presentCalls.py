"""Tests for calling functions on presentation of a frame
(`Window.callOnPresent`) and resetting clocks at the recorded time of a flip
(`Window.resetClockOnFlip`), without a window.
"""
import sys
import threading
import types

import pytest

from psychopy import clock, logging
from psychopy.visual import _presentcalls
from psychopy.visual._presentcalls import PresentCall, PresentCallScheduler
from psychopy.visual.window import Window


@pytest.fixture
def scheduler():
    scheduler = PresentCallScheduler()
    yield scheduler
    scheduler.stop()


def _call(function=lambda: None, *args):
    return PresentCall(function, args, {})


# --------------------------------------------------------------------------
# Waiting and calling
#

@pytest.mark.parametrize("wait", [0.005, 0.02])
def test_waiter_wakes_at_deadline(wait):
    """The OS deadline sleep wakes at the deadline, not early, and soon after
    (generously, for loaded test machines).

    It waits on a thread of its own with its priority raised, as the
    scheduler's is: without that, macOS coalesces the thread's timer wake-ups,
    so it wakes late (by tens of milliseconds on CI virtual machines). The
    test's own thread isn't raised, as that would last for the rest of the
    test session.
    """
    times = {}

    def waitForDeadline():
        _presentcalls.raiseThreadPriority()
        waitUntil = _presentcalls.makeWaiter()
        times['deadline'] = deadline = clock.getTime() + wait
        waitUntil(deadline)
        times['woke'] = clock.getTime()

    thread = threading.Thread(target=waitForDeadline, daemon=True)
    thread.start()
    thread.join(5.0)
    assert 'woke' in times, "the waiter didn't wake"
    deadline, woke = times['deadline'], times['woke']
    assert woke >= deadline - 0.0002
    assert woke - deadline < 0.005


def test_call_made_at_target(scheduler):
    call = _call()
    scheduler.schedule([call], clock.getTime() + 0.02)
    assert call.called.wait(1.0)
    assert -0.0002 <= call.lateBy < 0.005


def test_past_target_called_straight_away_in_order(scheduler):
    order = []
    calls = [_call(order.append, i) for i in range(3)]
    scheduler.schedule(calls, clock.getTime() - 1.0)
    assert calls[-1].called.wait(1.0)
    assert order == [0, 1, 2]
    assert all(call.lateBy >= 1.0 for call in calls)


def test_error_in_call_logged_and_next_still_made(scheduler, monkeypatch):
    errors = []
    monkeypatch.setattr(logging, "error", lambda msg, *a, **k: errors.append(msg))

    def fails():
        raise RuntimeError("trigger failed")

    bad, good = _call(fails), _call()
    scheduler.schedule([bad, good], clock.getTime())
    assert good.called.wait(1.0)
    assert bad.tCalled is not None
    assert len(errors) == 1 and "trigger failed" in errors[0]


def test_stop_drops_calls_and_restores_switch_interval():
    before = sys.getswitchinterval()
    scheduler = PresentCallScheduler()
    scheduler.schedule([_call()], clock.getTime())
    assert sys.getswitchinterval() <= _presentcalls.SWITCH_INTERVAL
    late = _call()
    scheduler.schedule([late], clock.getTime() + 0.05)
    scheduler.stop()
    assert sys.getswitchinterval() == before
    scheduler.schedule([_call()], clock.getTime())  # ignored once stopped
    assert not late.called.wait(0.1)


def test_started_ahead_without_lowering_switch_interval():
    """`Window` starts the thread when it's created, as starting a thread can
    hold up a flip, but the switch interval is left alone until there are
    calls to make."""
    before = sys.getswitchinterval()
    scheduler = PresentCallScheduler()
    try:
        scheduler.start()
        assert scheduler._thread.is_alive()
        assert sys.getswitchinterval() == before
        thread = scheduler._thread
        call = _call()
        scheduler.schedule([call], clock.getTime())
        assert call.called.wait(1.0)
        assert scheduler._thread is thread  # not started again
        assert sys.getswitchinterval() <= _presentcalls.SWITCH_INTERVAL
    finally:
        scheduler.stop()
    assert sys.getswitchinterval() == before
    assert not thread.is_alive()


# --------------------------------------------------------------------------
# Window: when calls are due, and checking them afterwards
#

def _fakeWin(tNextRaw=None, framePeriod=1 / 60):
    """Just enough of a Window for the methods tested."""
    def getFutureFlipTime(targetTime=0, clock=None):
        if tNextRaw is None:
            raise IndexError("no flip yet")
        return tNextRaw

    return types.SimpleNamespace(
        getFutureFlipTime=getFutureFlipTime,
        monitorFramePeriod=framePeriod,
        _presentCalls=[], _presentCallsFlipped=[], _presentScheduler=None,
        nEarlyPresentCalls=0, presentationLatency=0.0)


def test_calls_scheduled_for_predicted_presentation():
    tNext = clock.getTime() + 10.0
    win = _fakeWin(tNextRaw=tNext)
    win._presentCalls = [_call(), _call()]
    calls = Window._schedulePresentCalls(win)
    try:
        assert win._presentCalls == []
        assert [call._tTargetRaw for call in calls] == [tNext, tNext]
    finally:
        win._presentScheduler.stop()


def test_calls_made_straight_away_without_a_prediction():
    win = _fakeWin(tNextRaw=None)
    win._presentCalls = [_call()]
    calls = Window._schedulePresentCalls(win)
    try:
        assert calls[0].called.wait(1.0)
    finally:
        win._presentScheduler.stop()


def _madeCall(tCalled, tOnset):
    call = _call()
    call._tCalledRaw = tCalled + logging.defaultClock.getLastResetTime()
    call.tOnset = tOnset
    return call


@pytest.mark.parametrize("tCalled, early", [
    (10.0, False),       # at the presentation time
    (9.998, False),      # a little before it
    (10.0 - 1 / 60, True),  # a refresh before it: the frame was dropped
])
def test_early_calls_counted(tCalled, early, monkeypatch):
    warnings = []
    monkeypatch.setattr(logging, "warning", lambda msg, *a, **k: warnings.append(msg))
    win = _fakeWin()
    win._presentCallsFlipped = [_madeCall(tCalled, tOnset=10.0)]
    Window._checkPresentCalls(win)
    assert win.nEarlyPresentCalls == int(early)
    assert len(warnings) == int(early)
    assert win._presentCallsFlipped == []


def test_calls_not_yet_made_checked_later():
    win = _fakeWin()
    waiting = _call()
    waiting.tOnset = 10.0
    win._presentCallsFlipped = [waiting]
    Window._checkPresentCalls(win)
    assert win._presentCallsFlipped == [waiting]


# --------------------------------------------------------------------------
# Resetting clocks at the time of a flip
#

def test_clock_reset_at_raw_time():
    c = clock.Clock()
    c.resetAt(clock.getTime() - 0.5)
    assert float(c.getTime()) == pytest.approx(0.5, abs=0.01)
    c.resetAt(clock.getTime(), newT=-2.0)  # as for reset(-2)
    assert float(c.getTime()) == pytest.approx(2.0, abs=0.01)


def test_clock_reset_at_recorded_flip_time():
    """The clock is reset to the recorded flip time, not to when the reset
    is made."""
    flipTime = logging.defaultClock.getTime() - 0.25  # flipped 250 ms ago
    win = types.SimpleNamespace(_frameTime=flipTime)
    c = clock.Clock()
    Window._resetClockAtFlip(win, c, 0.0)
    assert float(c.getTime()) == pytest.approx(0.25, abs=0.01)
