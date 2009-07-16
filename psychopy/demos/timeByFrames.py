#!/usr/bin/env python
from psychopy import visual, core, log, ext
import pylab

#often you should synchronise your stimulus to the frame

nFrames = 200
core.rush()
#setup the stimuli and other objects we need
myWin = visual.Window([800,600],allowGUI=False)#make a window
myWin.setRecordFrameIntervals(True)

myStim = visual.PatchStim(myWin, tex='sin', mask='gauss', sf=3.0)
log.console.setLevel(log.DEBUG)#this will cause skipped frames to be reported
myClock = core.Clock() #just to keep track of time

#present a stimulus for EXACTLY 20 frames and exactly one cycle
for frameN in range(nFrames):
    myStim.setPhase(1.0/nFrames, '+') #advance the phase (add 1/nFrames to prev value)
    myStim.draw()
    myWin.flip()
    ext.waitForVBL()
    
#report the mean time afterwards
print 'total time=', myClock.getTime()
print 'avg frame time=', myClock.getTime()/nFrames
pylab.plot(myWin.frameIntervals, '-o')
pylab.show()