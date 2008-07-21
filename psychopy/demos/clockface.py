#! /usr/local/bin/python2.5
from psychopy import visual, core, event
import numpy 
minHand = numpy.array([#
    [0,0,0,0],
    [0,0,0,0],
    [1,1,1,1],
    [1,1,1,1]])

win = visual.Window([800,800])

second = visual.PatchStim(win, rgb=[1.0,0.5,0.5], size=[0.01,1], 
    tex=None, mask=minHand,interpolate=False)
minute = visual.PatchStim(win, rgb=1, size=[0.05,1],  tex=None, mask=minHand,interpolate=False)
hour = visual.PatchStim(win, rgb=-1, size=[0.05,0.5],  tex=None, mask=minHand,interpolate=False)
clock = core.Clock()
 
while True: #ie forever
    t = clock.getTime()*60 #speed up time with multipliers :-)
    
    minPos = numpy.floor((t/60.0)%60.0)*360/60 #NB floor will round down to previous minute
    minute.setOri(minPos)
    minute.draw()
    
    hourPos = ((t/3600))*360/12#this one can be smooth
    hour.setOri(hourPos)
    hour.draw()
    
    secPos = numpy.floor(t%60.0)*360/60#NB floor will round down to previous second
    second.setOri(secPos)
    second.draw()
    
    win.flip()
    if 'q' in event.getKeys():
        break
    event.clearEvents()
    
