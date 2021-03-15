# -*- coding: utf-8 -*-
import psychopy
MonotonicClock = psychopy.clock.MonotonicClock
monotonicClock = psychopy.clock.monotonicClock
_getTime = monotonicClock.getTime


def getTime():
    return monotonicClock.getTime()
