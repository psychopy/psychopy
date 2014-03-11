#!/usr/bin/env python
from psychopy import visual, core, event, logging
import numpy
from pycrsltd import bits

logging.console.setLevel(logging.INFO)
bitsBox = bits.BitsSharp(None)

#create a window with bitsMode='fast' (why would you ever use 'slow'!?)
win = visual.Window([1280, 1024], screen=1, bitsMode='fast', fullscr = False)
currGamma = 1.0
win.winHandle.setGamma(win.winHandle, newGamma=currGamma, rampType=0)
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
    
    vidLine = bitsBox.getVideoLine(1,20)
    if len(vidLine):
        if vidLine[0,0]==36:
            print vidLine
            break
        elif vidLine[0,0]>36:
            currGamma -= 0.01
            win.winHandle.setGamma(win.winHandle, newGamma=currGamma, rampType=0)
            print 'gamma now:', currGamma
        else:
            currGamma += 0.01
            win.winHandle.setGamma(win.winHandle, newGamma=currGamma, rampType=0)
            print 'gamma now:', currGamma
    #check for a keypress
    if event.getKeys():
        break
    event.clearEvents('mouse')#only really needed for pygame windows


#reset the bits++ (and update the window so that this is done properly)
bitsBox.startBitsPlusPlusMode()
win.bits.setContrast(1)

win.flip()

core.quit()
