#! /usr/local/bin/python2.5
from psychopy import visual, core, log
#often you should synchronise your stimulus to the frame

nFrames = 20

#setup the stimuli and other objects we need
myWin = visual.Window([800,600],allowGUI=False)#make a window
myWin.update()#present it
myStim = visual.AlphaStim(myWin, tex='sin', mask='gauss', sf=3.0)
log.console.setLevel(log.DEBUG)#this will cause skipped frames to be reported
myClock = core.Clock() #just to keep track of time

#present a stimulus for EXACTLY 20 frames and exactly one cycle
for frameN in range(nFrames):
    myStim.setPhase(1.0/nFrames, '+') #advance the phase (add 1/nFrames to prev value)
    myStim.draw()
    myWin.update()
    
#report the mean time afterwards
print 'total time=', myClock.getTime()
print 'avg frame time=', myClock.getTime()/nFrames