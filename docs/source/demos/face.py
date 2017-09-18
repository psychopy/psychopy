#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from psychopy import core, visual, event

#create a window to draw in
myWin = visual.Window((600, 600), allowGUI=False, color=(-1, -1, -1))

#INITIALISE SOME STIMULI
faceRGB = visual.GratingStim(myWin, tex='face.jpg',
                             mask=None,
                             pos=(0.0, 0.0),
                             size=(1.0, 1.0),
                             sf=(1.0, 1.0))

faceALPHA = visual.GratingStim(myWin, pos=(-0.5, 0),
                               tex="sin", mask="face.jpg",
                               color=[1.0, 1.0, -1.0],
                               size=(0.5, 0.5), sf=1.0,
                               units="norm")

message = visual.TextStim(myWin, pos=(-0.95, -0.95),
                          text='[Esc] to quit', color=1,
                          alignHoriz='left', alignVert='bottom')

trialClock = core.Clock()
t = lastFPSupdate = 0
while True:
    t = trialClock.getTime()
    faceRGB.setOri(1, '+')#advance ori by 1 degree
    faceRGB.draw()

    faceALPHA.setPhase(0.01, "+")#advance phase by 1/100th of a cycle
    faceALPHA.draw()

    #update fps every second
    if t-lastFPSupdate > 1.0:
        lastFPS = myWin.fps()
        lastFPSupdate = t
        message.setText("%ifps, [Esc] to quit" %lastFPS)
    message.draw()

    myWin.flip()

    #handle key presses each frame
    for keys in event.getKeys():
        if keys in ['escape', 'q']:
            print(myWin.fps())
            myWin.close()
            core.quit()
    event.clearEvents()
