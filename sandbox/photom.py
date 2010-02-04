from psychopy import hardware, log
from psychopy import monitors
from psychopy.hardware import pr

log.console.setLevel(log.DEBUG)
#phot = pr.PR650('/dev/tty.USA19H1d1P1.1')
phot = hardware.findPhotometer(['/dev/tty.KeySerial1.'])
if phot!=None:
    print phot.getLum()