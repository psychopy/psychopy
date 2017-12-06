#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo using a custom serial rx parser to generate ioHub Serial Device events.

The parseserial.py file is also required for this demo, as it contains the
custom parser function that the ioHub Serial device uses during runtime.

** This demo assumes that whatever is written out to the serial port is what the
serial device receives back as rx data. **

"""
from __future__ import absolute_import, division, print_function

import time
from psychopy import core, visual
from psychopy.iohub import launchHubServer

# Settings for serial port communication.
SERIAL_PORT = 'COM16'
BAUDRATE = 19200

# event_parser_info dict:
#
# parser_function key value can be a str giving the module.function path,
# or it can be the actual function object to be run by the iohub process.
#
# *Important:* The function provided should be in a file that can be imported
# as a module without causing unwanted behavior on the iohub process.
# Some options:
#     1) Put the function in a file that contains only the function,
#        as is done in this example.
#     2) Ensure any script logic that will be run when the file is called by
#        a user ( i.e. python.exe filewithfunc.py ) is inside a:
#            if __name__ == '__main__':
#        condition so it is not run when the file is only imported.

event_parser_info = dict(parser_function="parseserial.checkForSerialEvents",
                         parser_kwargs=dict(var1='not used', var2=1234))
# configure iohub
exp_code = 'serial_demo'
sess_code = 'S_{0}'.format(int(time.mktime(time.localtime())))
iohubkwargs = {'experiment_code': exp_code,
               'session_code': sess_code,
               'serial.Serial': dict(name='serial',
                                     port=SERIAL_PORT,
                                     baud=BAUDRATE,
                                     parity='NONE',
                                     bytesize=8,
                                     event_parser=event_parser_info)}

# start the iohub server and set up display and PST box devices
io = launchHubServer(**iohubkwargs)
serial_device = io.devices.serial
keyboard = io.devices.keyboard

# Start collecting data from the PST box in the background.
serial_device.enableEventReporting(True)

# Create a window.
win = visual.Window((1024, 768), units='pix')

# Instruction text.
instruction = visual.TextStim(win, text='Monitoring for serial input events....\n\nPress any key to exit.')
# Display instruction.
instruction.draw()
win.flip()
io.clearEvents('all')

# Check for keyboard and serial events.
# Exit on keyboard press event.
# Print any serial events.
#
while not keyboard.getPresses():
    serial_device.write("TEST")
    for serevt in serial_device.getEvents():
        print(serevt)
    io.wait(.500)

# Stop recording events from the PST box and switch off all lamps.
serial_device.enableEventReporting(False)

# Close the window and quit the program.
io.quit()
core.quit()
