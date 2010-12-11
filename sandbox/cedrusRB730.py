from psychopy.hardware import CedrusPad
from psychopy import core
import sys

rb730 = CedrusPad(7,'RB730',baudrate=115200)
#get RB info
print rb730.getInfo()
print 'roundTrip:', rb730.measureRoundTrip()

core.wait(0.1) #give chance to clear prev commands
rb730.resetBaseTimer()
rb730.resetTrialTimer()

#test keys
print 'push some keys (1 exits)'; sys.stdout.flush()
notAbort=True
while notAbort:
    keyEvents = rb730.waitKeyEvents(downOnly=False)
    for evt in keyEvents:
        print evt.key, evt.rt, evt.direction
        if evt.key==1:notAbort=False
print 'done'
print 'baseTime:',rb730.getBaseTimer()