#!/usr/bin/env python2
from psychopy import visual, core, event
import numpy

#create a window with bitsMode='fast' (why would you ever use 'slow'!?)
win = visual.Window([800,800], bitsMode='fast')

grating = visual.PatchStim(win,mask = 'gauss',sf=2)

#---using bits++ with one stimulus
globalClock = core.Clock()
while True:
    #get new contrast
    t=globalClock.getTime()
    newContr = numpy.sin(t*numpy.pi*2)#sinusoidally modulate contrast
    
    #set whole screen to this contrast
    win.bits.setContrast(newContr)# see http://www.psychopy.org/reference/
    #draw gratings and update screen
    grating.draw()
    win.flip()
    
    #check for a keypress
    if event.getKeys():
        break
    event.clearEvents('mouse')#only really needed for pygame windows


#reset the bits++ (and update the window so that this is done properly)

win.bits.setContrast(1)

win.flip()

core.quit()
