#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of how to copy pixels from the frame buffer
"""

from __future__ import division

from builtins import range
from psychopy import visual, core, logging
logging.console.setLevel(logging.INFO)

win = visual.Window([200, 200])
myStim = visual.GratingStim(win, pos=[-0.5, -0.5],
    size=1, sf=5, color=[0, 1, 1], ori=30, mask='gauss', autoLog=False)

n = 10
for frameN in range(n):
    myStim.setPhase(0.1, '+')
    myStim.draw()
    # you can either read from the back buffer BEFORE win.flip() or
    # from the front buffer just AFTER the flip. The former has the
    # advantage that it won't be affected by other windows whereas
    # latter can be.
    win.getMovieFrame(buffer='back')
    win.flip()

# save the movie in the format of your choice
win.saveMovieFrames('frame.png', clearFrames=False)
win.saveMovieFrames('myMovie.gif', clearFrames=False)
win.saveMovieFrames('myMovie.mp4', clearFrames=False)
win.saveMovieFrames('myMovie.mov', clearFrames=False)

win.close()
core.quit()

# The contents of this file are in the public domain.
