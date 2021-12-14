#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of using Cedrus RB730 hardware
"""

from psychopy.hardware import cedrus
from psychopy import core
import sys

rb730 = cedrus.RB730(7, baudrate=115200)

# Get RB info
print(rb730.getInfo())
# this is the time taken to send a signal to the unit and back via USB:
print(('roundTrip:', rb730.measureRoundTrip()))

core.wait(0.1)  # give chance to clear prev commands
rb730.resetBaseTimer()
rb730.resetTrialTimer()

# Test keys
print('push some keys (1 exits)')
sys.stdout.flush()
notAbort = True
while notAbort:
    keyEvents = rb730.waitKeyEvents(downOnly=False)
    for evt in keyEvents:
        print("key=%s, rt=%.4f, up/down=%i" % (evt.key, evt.rt, evt.direction))
        if evt.key == 1:
            notAbort = False

print('done')
print(('baseTime:', rb730.getBaseTimer()))
core.quit()

# The contents of this file are in the public domain.
