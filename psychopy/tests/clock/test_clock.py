#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import pytest

from psychopy.clock import wait, StaticPeriod, CountdownTimer
from psychopy.visual import Window


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

    assert np.allclose(timer.getTime(),
                       1.0/refresh_rate,
                       atol=0.001)
    win.close()


if __name__ == '__main__':
    test_StaticPeriod()
