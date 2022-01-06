#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo to illustrate using ioLabs button box.
"""

__author__ = 'Jonathan Roberts (orig demo); Jeremy Gray (rewrite 2013)'

from psychopy.hardware import iolab
import random
from psychopy import core, visual, event

# set up the button box
bbox = iolab.ButtonBox()
buttons = [1, 6]
bbox.setLights(buttons)  # turn on those two lights, others off
bbox.setEnabled(buttons)  # ignore other buttons

# show instructions, wait for spacebar
win = visual.Window()
instructions = visual.TextStim(win, wrapWidth = 1.8, height =.08,
    text = '6 trials:\nhit the left lighted button when you see the word "left".\n'
           'hit the right lighted button when you see the word "right".\n'
           'hit space to start... < escape > to quit')
instructions.draw()
win.flip()
if 'escape' in event.waitKeys(['space', 'escape']):
    core.quit()

# loop over fixation + left/right, get response
fixation = visual.TextStim(win, text = '+')
target = visual.TextStim(win, text = 'set during trial loop')
labeledResponse = {1: 'left', 6: 'right'}
stims = list(labeledResponse.values()) * 3  # list of stims: 3 'lefts' and 3 'rights'
random.shuffle(stims)

for stim in stims:
    fixation.draw()
    win.flip()
    core.wait(0.5 + random.random())
    target.setText(stim)
    target.draw()
    win.flip()
    if event.getKeys(['q', 'escape']):
        break

    bbox.resetClock()  # sets RT to 0.000 on bbox internal clock
    evt = bbox.waitEvents()  # clears prior events, wait for response
    if not evt:
        break
    if  labeledResponse[evt.btn] == stim:  # evt.btn is int, evt.key is str
        print('correct', evt.btn, evt.rt)   # evt.rt  is sec, evt.rtc is ms
    else:
        print('wrong', evt.btn, evt.rt)

bbox.standby()  # lights off

win.close()
core.quit()

# The contents of this file are in the public domain.
