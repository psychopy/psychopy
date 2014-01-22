#!/usr/bin/env python2
#this is win32 only - I have no idea how to use parallel ports on a Mac! jwp
from psychopy import visual, core, logging
from psychopy import parallel 

nFramesOn = 5
nFramesOff = 30
nCycles = 2
parallel.setPortAddress(0x378)#address for parallel port on many machines
pinNumber = 2#choose a pin to write to (2-9). 

#setup the stimuli and other objects we need
myWin = visual.Window([1280, 1024],allowGUI=False)#make a window
myWin.flip()#present it
myStim = visual.PatchStim(myWin, tex=None, mask=None, color='white', size=2)   
myClock = core.Clock() #just to keep track of time

#present a stimulus for EXACTLY 20 frames and exactly 5 cycles
for cycleN in range(nCycles):
    for frameN in range(nFramesOff):
        #don't draw, just refresh the window
        myWin.flip()
        parallel.setData(0)#sets all pins low
        
    for frameN in range(nFramesOn):
        myStim.draw()
        myWin.flip()
        #immediately *after* screen refresh set pins as desired
        parallel.setPin(2,1)#sets just this pin to be high        
        
#report the mean time afterwards
print 'total time=', myClock.getTime()
print 'avg frame rate=', myWin.fps()
#set pins back to low
myWin.flip()
parallel.setData(0)#sets all pins low again
