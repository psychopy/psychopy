#!/usr/bin/env python

"""Demo program to illustrate using ioLabs button box.

To run this test the ioLab library needs to be installed (it is included with
the Standalone distributions of PsychoPy; otherwise try "pip install ioLabs").
"""

__author__ = 'Jonathan Roberts'
# refactored by Jeremy Gray 2013

import random
from psychopy import core, visual, event
from psychopy.hardware import iolabs

myWin = visual.Window()
instructions = visual.TextStim(myWin,
    text = '6 trials:\nhit the left lighted button when you see the word "left".\nhit the right lighted button when you see the word "right".\nhit space to start... <escape> to quit',
    wrapWidth = 1.8, height =.08)
fixation = visual.TextStim(myWin,text = '+')
target = visual.TextStim(myWin,text = 'to be filled it during trial loop')
trialClock = core.Clock()

# set up the button box
myBBox = iolabs.BBox()

buttons = [1, 6]
labeledResponse = {1:'left', 6:'right'}
stims = ['left', 'right'] * 3  # make a list of stims with 3 'lefts' and 3 'rights'
random.shuffle(stims)

# turn on the lights above the buttons we will be using and enable them
myBBox.lightButtons(buttons)
myBBox.enableButtons(buttons)

# show instructions, wait for spacebar
instructions.draw()
myWin.flip()
if 'escape' in event.waitKeys(['space', 'escape']):
    core.quit()
myWin.flip()

# trial loop
for stim in stims:
    # unpredictable-duration fixation point
    fixation.draw()
    myWin.flip()
    core.wait(0.5 + random.random())
    target.setText(stim)
    target.draw()
    myWin.flip()
    trialClock.reset()  # reset the trial clock immediately after the screen flip

    myBBox.clearEvents()  # clear any events that have already happened
    if event.getKeys(['q', 'escape']):
        break
    btn = myBBox.waitButtons()

    rt = trialClock.getTime()  # get the time as soon as we detect a keyevent
    rt = round(rt * 1000, 2)  # convert to msec with 2 decimal places
    if  labeledResponse[btn] == stim:
        print 'correct', btn, rt
    else:
        print 'wrong', btn, rt

myBBox.lightButtons(None)  # turn out all the lights

