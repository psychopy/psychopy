#!/usr/bin/env python
from psychopy import *

#create a window to draw in
myWin = visual.Window((600,600.0), allowGUI=False, 
                      monitor='testMonitor')#this contains info about your screen (to calculate angles etc...)

#INITIALISE SOME STIMULI
grating1 = visual.PatchStim(myWin,tex="sin",mask="gauss",
            color=[1.0,1.0,1.0],opacity=1.0,
            size=(5.0,5.0), sf=(2,0),
            ori = 45,
            units='deg')
grating2 = visual.PatchStim(myWin,tex="sin",mask="gauss",
            color=[1.0,1.0,1.0],opacity=0.5,
            size=(5.0,5.0), sf=(1,0),
            ori = 135,
            units='deg')
message = visual.TextStim(myWin,pos=(-0.95,-0.95),text='Hit Q to quit')

trialClock = core.Clock()
t = 0
while t<20:#quits after 20 secs
    t=trialClock.getTime()
    
    grating1.setPhase(2*t)  #drift at 2Hz
    grating1.draw()  #redraw it
    
    grating2.setPhase(t)    #drift at 1Hz
    grating2.draw()  #redraw it
    
    myWin.flip()          #update the screen

    #handle key presses each frame
    for keys in event.getKeys():
        if keys in ['escape','q']:
            core.quit()

    

