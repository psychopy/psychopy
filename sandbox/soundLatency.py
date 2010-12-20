
from sys import platform
from psychopy import sound,core,visual,event
if platform=="win32": from psychopy import _parallel
import pyglet.media
#sound.setEventPollingPeriod(0.0001) #this gives priority to sound over drawing but isn't necessary

winType = 'pyglet'
LPT1 = 0x378#address for parallel port on many machines
pinNumber = 2#choose a pin to write to (2-9).  

#black window
win = visual.Window([800,800], rgb=-1, winType=winType)
win.update()#draw black screen
white = visual.PatchStim(win, tex=None, rgb=1)#and create white patch to detect with diode

#if pygame has been initialised this will be a pygame sound, otherwise pyglet    
A = sound.Sound(400,secs=0.08,bits=16,sampleRate=44100)  
A.setVolume(0.6)
#make screen white then play sound and set parallel high
white.draw(); win.update()
A.play()
if platform=="win32": _parallel.out(LPT1, 2**(pinNumber-2))#sets just this pin to be high (pin2 represent databit 0, pin3=bit1...)    

win.update()#draw black screen and set parallel low
if platform=="win32": _parallel.out(LPT1, 0)#sets all pins low
core.wait(2)#wait for sound to finish

core.quit()