#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function

from psychopy import iohub
from psychopy.core import wait
from psychopy.visual import Window
from psychopy.visual.ratingscale import SimpleRatingScale

io = iohub.launchHubServer()
win = Window()
rs = SimpleRatingScale(
    win, ori='vert', limits=(0, 100), ticks=(0, 50, 100),
    tickLabels=('small', 'medium', 'large'), maxTime=5, mousePos=(-0.5, 0),
    labelLoc='right', iohub=True)

rs.draw()
win.flip()
rs.waitForResponse()

# Display marker, then clear the screen.
rs.draw()
win.flip()
wait(0.2)
win.flip()

if rs.response is not None:
    print('Got response %.2f after %.3f sec.' %( rs.response, rs.rt))
else:
    print('Did not get a response within %.3f sec.' % rs.maxTime)
