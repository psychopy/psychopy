#!/usr/bin/env python2
from psychopy import visual, logging, event, core

#create a window to draw in
myWin = visual.Window((600,600), allowGUI=False, blendMode='add', useFBO=True)
logging.console.setLevel(logging.DEBUG)

"""For combining stimuli (e.g. to create a plaid) it's best to use blendMode='add'
rather than blendMode='avg'. In this blendMode the background is not overwritten
but added to, which is ideal in this instance.
On the other hand, in this mode the opacity attribute is a slight
misnomer; setting a high 'opacity' doesn't cause the background to be
obscured; it just acts as a multiplier for the contrast of the stimulus being drawn.
"""

#INITIALISE SOME STIMULI
grating1 = visual.GratingStim(myWin,mask="gauss",
    color=[1.0,1.0,1.0],contrast=0.5,
    size=(1.0,1.0), sf=(4,0), ori = 45,
    autoLog=False)#this stim changes too much for autologging to be useful
grating2 = visual.GratingStim(myWin,mask="gauss",
    color=[1.0,1.0,1.0],opacity=0.5,
    size=(1.0,1.0), sf=(4,0), ori = -45,
    autoLog=False)#this stim changes too much for autologging to be useful

trialClock = core.Clock()
t = 0
while t<20:#quits after 20 secs

    t=trialClock.getTime()

    grating1.setPhase(1*t)  #drift at 1Hz
    grating1.draw()  #redraw it

    grating2.setPhase(2*t)    #drift at 2Hz
    grating2.draw()  #redraw it
    
    myWin.flip()          #update the screen

    #handle key presses each frame
    for keys in event.getKeys():
        if keys in ['escape','q']:
            core.quit()


