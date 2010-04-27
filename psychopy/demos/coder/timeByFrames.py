#!/usr/bin/env python
from psychopy import visual, core, log, ext
import pylab

#often you should synchronise your stimulus to the frame

nFrames = 200
#setup the stimuli and other objects we need
myWin = visual.Window([1024,768],screen=0, fullscr=True, waitBlanking=True)#make a window
myWin.setRecordFrameIntervals(True)

myStim = visual.PatchStim(myWin, tex='sin', mask='gauss', sf=3.0)
log.console.setLevel(log.DEBUG)#this will cause skipped frames to be reported
myClock = core.Clock() #just to keep track of time

#present a stimulus for EXACTLY nFrames and exactly one cycle
for frameN in range(nFrames):
    myStim.setPhase(1.0/nFrames, '+') #advance the phase (add 1.0/nFrames to prev value)
    myStim.draw()
    myWin.flip()

#report the mean time afterwards
print 'total time=', myClock.getTime()
print 'avg frame time=', myClock.getTime()/nFrames
myWin.close() # this takes a while--do it after getting time from the clock
frameTimes=pylab.array(myWin.frameIntervals[5:])*1000 #convert to ms, ignore the first 5 (likely to be noisy)
pylab.plot(frameTimes, '-o')
frameTimes.sort() # can be interesting
pylab.plot(frameTimes, '-o')
pylab.ylabel('frame times (ms)')
pylab.show()