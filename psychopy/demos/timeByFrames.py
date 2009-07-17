#!/usr/bin/env python
from psychopy import visual, core, log, ext
import pylab

#often you should synchronise your stimulus to the frame

nFrames = 200
core.rush()
#setup the stimuli and other objects we need
myWin = visual.Window([1680,1050],screen=0, fullscr=True, waitBlanking=True)#make a window
myWin.setRecordFrameIntervals(True)

myStim = visual.PatchStim(myWin, tex='sin', mask='gauss', sf=3.0)
log.console.setLevel(log.DEBUG)#this will cause skipped frames to be reported
myClock = core.Clock() #just to keep track of time

#present a stimulus for EXACTLY 20 frames and exactly one cycle
for frameN in range(nFrames):
    myStim.setPhase(1.0/nFrames, '+') #advance the phase (add 1/nFrames to prev value)
    myStim.draw()
    myWin.flip()
myWin.close()    
#report the mean time afterwards
print 'total time=', myClock.getTime()
print 'avg frame time=', myClock.getTime()/nFrames
frameTimes=pylab.array(myWin.frameIntervals[20:])*1000#convert to ms
pylab.plot(frameTimes[20:], '-o')#ignore the first 20 (likely to be noisy)
pylab.ylabel('frame times (ms)')
pylab.show()