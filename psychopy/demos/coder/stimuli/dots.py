#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of dot kinematogram
"""

from psychopy import visual, event, core

win = visual.Window((600, 600), allowGUI=False, winType='pyglet')

# Initialize some stimuli
dotPatch = visual.DotStim(win, color=(1.0, 1.0, 1.0), dir=270,
    nDots=500, fieldShape='circle', fieldPos=(0.0, 0.0), fieldSize=1,
    dotLife=5,  # number of frames for each dot to be drawn
    signalDots='same',  # are signal dots 'same' on each frame? (see Scase et al)
    noiseDots='direction',  # do the noise dots follow random- 'walk', 'direction', or 'position'
    speed=0.01, coherence=0.9)

print(dotPatch)

message = visual.TextStim(win, text='Any key to quit', pos=(0, -0.5))
trialClock =core.Clock()
while not event.getKeys():
    dotPatch.draw()
    message.draw()
    win.flip()  # make the drawn things visible

    event.clearEvents('mouse')  # only really needed for pygame windows

print(win.fps())
win.close()
core.quit()

# The contents of this file are in the public domain.
