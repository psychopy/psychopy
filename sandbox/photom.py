from psychopy import hardware, log
from psychopy import monitors
from psychopy.hardware import minolta
import serial
#phot = minolta.LS100('COM3')
#print phot

log.console.setLevel(log.DEBUG)
#phot = pr.PR650('/dev/tty.USA19H1d1P1.1')
phot = hardware.findPhotometer(ports=[3])
if phot!=None:
    print phot.getLum()
print 'done' 