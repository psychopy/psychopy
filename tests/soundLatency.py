
from sys import platform
from psychopy import sound,core,visual
if platform=="win32": from psychopy import _parallel
import numpy
import pyglet.media

winType = 'pyglet'
LPT1 = 0x378#address for parallel port on many machines
pinNumber = 2#choose a pin to write to (2-9).  

#black window
win = visual.Window([800,800], rgb=-1, winType=winType)
win.update()#draw black screen
white = visual.PatchStim(win, tex=None, rgb=1)#and create white patch to detect with diode
     
#if pygame has been initialised this will be a pygame sound, otherwise pyglet    
A = sound.Sound(220, secs=0.2,octave=6, bits=16)  

core.wait(0.5)

#make screen white then play sound and set parallel high
white.draw(); win.update()
A.play()
if platform=="win32": _parallel.out(LPT1, 2**(pinNumber-2))#sets just this pin to be high (pin2 represent databit 0, pin3=bit1...)    

clock = core.Clock()
while clock.getTime()<1.0:
    if winType == 'pyglet': pyglet.media.dispatch_events()

win.update()#draw black screen and set parallel low
if platform=="win32": _parallel.out(LPT1, 0)#sets all pins low
core.wait(0.1)#wait for sound to finish