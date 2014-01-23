#!/usr/bin/env python2
"""
There are many ways to generate counter-phase e.g. 
vary the contrast of a grating sinusoidally between 1 and -1, 
take 2 gratings in opposite phase overlaid and vary the 
opacity of the upper one between 1:0, or take 2 gratings
overlaid with the upper one of 0.5 opacity and drift them
in opposite directions.
This script takes the first approach as a test of how fast 
contrast textures are being rewritten to the graphics card
"""
from psychopy import core, visual, event
from numpy import sin, pi

#create a window to draw in
myWin = visual.Window((600,600.0), allowGUI=False, monitor='testMonitor', units='deg')

#INITIALISE SOME STIMULI
grating1 = visual.GratingStim(myWin,tex="sin",mask="circle",texRes=128,
            color=[1.0,1.0,1.0],colorSpace='rgb', opacity=1.0,
            size=(5.0,5.0), sf=(2.0,2.0),
            ori = 45, depth=0.5,
            autoLog=False)#this stim changes too much for autologging to be useful
message = visual.TextStim(myWin,text='Hit Q to quit',
    pos=(-0.95,-0.95),units='norm',
    alignVert='bottom',alignHoriz='left')
    
trialClock = core.Clock()
t = lastFPSupdate = 0
while t<20:#quits after 20 secs
    t=trialClock.getTime()
    
    grating1.setContrast(sin(t*pi*2))
    grating1.draw()  #redraw it
    
    message.draw()
    
    myWin.flip()          #update the screen

    #handle key presses each frame
    for key in event.getKeys():
        if key in ['escape','q']:
            myWin.close()
            core.quit()
