#this is win32 only - I have no idea how to use parallel ports on a Mac! jwp
from psychopy import visual, core, log
from psychopy import _parallel 
# i plan to make parallel a bit more user-friendly, in which case 
#_parallel will become simply parallel. Right now it's based on 
# winioport.py  Author: Dincer Aydin dinceraydin@gmx.net www.dinceraydin.com

nFramesOn = 5
nFramesOff = 30
nCycles = 2
LPT1 = 0x378#address for parallel port on many machines
pinNumber = 2#choose a pin to write to (2-9). 

#setup the stimuli and other objects we need
myWin = visual.Window([1280, 1024],allowGUI=False)#make a window
myWin.update()#present it
myStim = visual.AlphaStim(myWin, tex=None, mask=None, rgb=1, size=2)   
myClock = core.Clock() #just to keep track of time

#present a stimulus for EXACTLY 20 frames and exactly 5 cycles
for cycleN in range(nCycles):
    for frameN in range(nFramesOff):
        #don't draw, just refresh the window
        myWin.update()
        _parallel.out(LPT1, 0)#sets all pins low
        
    for frameN in range(nFramesOn):
        myStim.draw()
        myWin.update()
        #immediately *after* screen refresh set pins as desired
        _parallel.out(LPT1, 2**(pinNumber-2))#sets just this pin to be high (pin2 represent databit 0, pin3=bit1...)
        
    
#report the mean time afterwards
print 'total time=', myClock.getTime()
print 'avg frame rate=', myWin.fps()
#set pins back to low
myWin.update()
_parallel.out(LPT1, 0)#sets all pins low