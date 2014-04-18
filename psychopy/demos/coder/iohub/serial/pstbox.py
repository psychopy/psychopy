"""
Demo using the ioHub Serial device, a generic interface to a serial port.

This demo is setup to read the serial output from the PST button box. Changes
in the byte value of the serial stream generate iohub events.

** Important: Change the 'port' and 'baud' values in line 27 of this file to
              whatever serial port you are using and the correct baudrate for
              the PST box.

If only one serial port is available on the computer being used, the 'port'
value can be set to 'auto' (without the '') and iohub will automatically
detect the serial port to use. If port is set to auto and there are > 1
ports available, the first port found is used.
"""
import time
from psychopy import core
from psychopy.iohub import launchHubServer

# configure iohub
psychopy_mon_name = 'testMonitor'
exp_code = 'pstbox'
sess_code = 'S_{0}'.format(long(time.mktime(time.localtime())))
iohubkwargs = {'psychopy_monitor_name':psychopy_mon_name,
                'experiment_code': exp_code,
                'session_code': sess_code,
                'serial.Serial': dict(name='serial', port='COM6', baud=115200,
                                   event_parser = dict(byte_diff=True))
               }

# start the iohub server and get the keyboard and PST box devices
io = launchHubServer(**iohubkwargs)
kb = io.devices.keyboard
pstbox = io.devices.serial

# Not sure if this is needed, but one psychopy-user forum post suggested it
# is required to enable serial streaming on the PST box.
pstbox.write(chr(128)+chr(32))

# Clear out any device events collected so far
io.clearEvents('all')
print "Reporting any Serial byte value changes. Press any key to exit."

# Start collecting data from the PST box.
pstbox.enableEventReporting(True)
# Report info on each PST button event until a keyboard button is pressed.
while not kb.getEvents():
    pstevents=pstbox.getEvents()
    for e in pstevents:
        print e.time, e.prev_byte, e.current_byte
    if pstevents:
        print '---'
    core.wait(0.01, 0.0)
# Stop recording events from the PST box and quit the iohub server.
pstbox.enableEventReporting(False)
io.quit()

## EOD