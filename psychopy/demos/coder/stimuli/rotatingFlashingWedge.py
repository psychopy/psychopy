#!/usr/bin/env python2
#rotate flashing wedge
from psychopy import visual, event, core

globalClock = core.Clock()
win = visual.Window([800,800])
#make two wedges (in opposite contrast) and alternate them for flashing
wedge1 = visual.RadialStim(win, tex='sqrXsqr', color=1,size=1,
    visibleWedge=[0, 45], radialCycles=4, angularCycles=8, interpolate=False,
    autoLog=False)#this stim changes too much for autologging to be useful
wedge2 = visual.RadialStim(win, tex='sqrXsqr', color=-1,size=1,
    visibleWedge=[0, 45], radialCycles=4, angularCycles=8, interpolate=False,
    autoLog=False)#this stim changes too much for autologging to be useful
t=0
rotationRate = 0.01 #revs per sec
flashPeriod = 0.1 #seconds for one B-W cycle (ie 1/Hz)
while t<5:#for 5 secs
    t=globalClock.getTime()
    if (t%flashPeriod) < (flashPeriod/2.0):# (NB more accurate to use number of frames)
        stim = wedge1
    else:
        stim=wedge2
        
    stim.setOri(t*rotationRate*360.0)
    stim.draw()
    win.flip()
    
win.close()
