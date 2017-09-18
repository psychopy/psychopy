#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This demo shows you how to schedule a call to an arbitrary function immediately
using win.callOnFlip()

This is especially useful in scheduling a call to a trigger (eg. parallel port) when
your frame flip occurs. Avoid do anything time-consuming in these function calls.

The first argument to callOnFlip() is the function you want to call, the other
arguments are the arguments exactly as you would normally use them
(and can used ordered arguments or named, keyword args as usual).
"""

from __future__ import division
from __future__ import print_function

from builtins import range
from psychopy import visual, core
import numpy

win = visual.Window([400, 400])
# insert a pause to allow the window and python (avoid initial frame drops)
core.wait(2)
clock = core.Clock()  # a clock to check times from

# a function to be called on selected frames
def printFrame(frameN, tReceived):
    tPrinted = clock.getTime()
    print(frameN, tReceived, tPrinted)

for frame in range(100):
    core.wait(numpy.random.random()/200)  # wait 0-5ms
    if frame in [2, 4, 6, 20, 30, 40]:
        win.callOnFlip(printFrame, frame, tReceived=clock.getTime())
    core.wait(numpy.random.random() / 200)  # wait 0-5ms
    win.flip()

win.close()
core.quit()

# The contents of this file are in the public domain.
