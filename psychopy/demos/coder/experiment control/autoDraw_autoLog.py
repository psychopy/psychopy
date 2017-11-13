#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
One easy way to handle stimuli that are drawn repeatedly is to
setAutoDraw(True) for that stimulus. It will continue to be drawn until
stim.setAutoDraw(False) is called. By default a logging message of
level EXP will be created when the setAutoDraw is called.

This can be turned off for each call with stim.setAutoDraw(True, autoLog=False)
"""

from __future__ import absolute_import, division, print_function

from builtins import range
from psychopy import visual, core

win = visual.Window([800, 800])

# a stim's name is used in log entries
stim1 = visual.GratingStim(win, pos=[-0.5, -0.5], name='stim1')
stim2 = visual.TextStim(win, pos=[0.5, 0.5], text='stim2', name='textStim')

# no need to log the fixation point info, use autoLog=False
fixation = visual.GratingStim(win, mask='gauss', tex=None, size=0.02,
    name='fixation', autoLog=False)

fixation.setAutoDraw(True)
stim1.setAutoDraw(True)
stim2.setAutoDraw(True)
# both on
for frameN in range(20):  # run 20 frames like this
    win.flip()

stim2.setAutoDraw(False)
# will draw only stim1 (and fixation)
for frameN in range(20):  # run 20 frames like this
    win.flip()

stim1.setAutoDraw(False)
stim2.setAutoDraw(True)
# will draw only stim2 (and fixation)
for frameN in range(20):  # run 20 frames like this
    win.flip()

for stim in [stim1, stim2, fixation]:
    stim.setAutoDraw(False)
win.flip()  # will cause the 'off' log messages to be sent

win.close()
core.quit()

# The contents of this file are in the public domain.
