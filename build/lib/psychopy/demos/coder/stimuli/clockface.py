#!/usr/bin/env python2
from psychopy import visual, core, event
import numpy, time    
win = visual.Window([800,800], monitor='testMonitor')

handVerts = numpy.array([ [0,0.8],[-0.05,0],[0,-0.05],[0.05,0] ])#vertices (using numpy means we can scale them easily)

second = visual.ShapeStim(win, vertices= [[0,-0.1], [0.1,0.8]],
    lineColor=[1,-1,-1],fillColor=None, lineWidth=2, autoLog=False)
minute = visual.ShapeStim(win, vertices=handVerts,
    lineColor=[1,1,1],fillColor=[0.8,0.8,0.8], autoLog=False)
hour = visual.ShapeStim(win, vertices=handVerts/2.0,
    lineColor=[-1,-1,-1],fillColor=[-0.8,-0.8,-0.8], autoLog=False)
clock = core.Clock()

while True: #ie forever
    t = time.localtime()
    
    minPos = numpy.floor(t[4])*360/60 #NB floor will round down to previous minute
    minute.ori = minPos
    minute.draw()
    
    hourPos = (t[3])*360/12#this one can be smooth
    hour.ori = hourPos
    hour.draw()
    
    secPos = numpy.floor(t[5])*360/60#NB floor will round down to previous second
    second.ori = secPos
    second.draw()
    
    win.flip()
    if 'q' in event.getKeys():
        break
    event.clearEvents('mouse')#only really needed for pygame windows
    
