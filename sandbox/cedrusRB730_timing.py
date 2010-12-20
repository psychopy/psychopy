from psychopy.hardware import CedrusPad
from psychopy import core
import sys
from psychopy import _parallel

#setup parallel port
LPT1 = 0x378#address for parallel port 
_parallel.out(LPT1, 0)#set all pins low

#setup RB730
rb730 = CedrusPad(7,'RB730',baudrate=115200)
#get RB info
print rb730.getInfo()
print 'roundTrip:', rb730.measureRoundTrip()

#core.wait(0.1) #give chance to clear prev commands
#rb730.resetBaseTimer()
#rb730.resetTrialTimer()

c = core.Clock()       
core.wait(0.05)
_parallel.out(LPT1, 1)#set pin 2 high  
#print keys     
c.reset()              
while c.getTime()<0.01:
    pass
_parallel.out(LPT1, 0)#set pin 2 low  
print c.getTime()

#wait for keypresses
notAbort=True
while notAbort:
    keyEvents = rb730.waitKeyEvents(downOnly=True)
    for evt in keyEvents:
        print evt.key, evt.rt, evt.direction
        if evt.key==1:notAbort=False
        
    _parallel.out(LPT1, 1)#set pin 2 high  
    #print keys         
    c.reset()              
    while c.getTime()<0.01:
        pass
    _parallel.out(LPT1, 0)#set pin 2 low  

print 'done'