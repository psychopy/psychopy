#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Using multiple screens and windows with PsychoPy
"""

from psychopy import visual, event
from numpy import sin, pi  # numeric python

if True:  # use two positions on one screen
    winL = visual.Window(size=[400, 300], pos=[100, 200], screen=0,
                         allowGUI=False)  # , fullscr=True)
    winR = visual.Window(size=[400, 300], pos=[400, 200], screen=0,
                         allowGUI=False)  # , fullscr=True)  # same screen diff place
else:
    winL = visual.Window(size=[400, 300], pos=[100, 200], screen=0,
                         allowGUI=False, fullscr=False)
    winR = visual.Window(size=[400, 300], pos=[100, 200], screen=1,
                         allowGUI=False, fullscr=False)  # same place diff screen

# create some stimuli
# NB. if the windows have the same characteristics then

# left screen
contextPatchL = visual.GratingStim(winL, tex='sin', mask='circle',
    size=1.0, sf=3.0, texRes=512)
targetStimL = visual.GratingStim(winL, ori=20, tex='sin', mask='circle',
    size=0.4, sf=3.0, texRes=512, autoLog=False)

# right screen
contextPatchR = visual.GratingStim(winR, tex='sin', mask='circle',
    size=1.0, sf=3.0, texRes=512)
targetStimR =visual.GratingStim(winR, ori=20, tex='sin', mask='circle',
    size=0.4, sf=3.0, texRes=512, autoLog=False)

t = 0.0
while not event.getKeys():
    t = t + 0.01
    # don't let it go behind the context (looks weird if it switches):
    newX = sin(t * pi * 2) * 0.05 + 0.05

    contextPatchR.draw()
    targetStimR.pos = [newX, 0]  # make this patch move the opposite way
    targetStimR.draw()

    contextPatchL.draw()
    targetStimL.pos = [-newX, 0]
    targetStimL.draw()

    winL.flip()
    winR.flip()

# Close windows
winR.close()
winL.close()

# The contents of this file are in the public domain.
