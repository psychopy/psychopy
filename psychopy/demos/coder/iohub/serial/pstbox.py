#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from builtins import range
import time
import numpy as np
from psychopy import core, visual
from psychopy.iohub import launchHubServer
from psychopy.iohub.devices import Computer

#####################################################################

#
# Device setup
#

# Settings for serial port (PST response box) communication.
SERIAL_PORT = 'COM5'
BAUDRATE = 19200

# ioHub configuration.
psychopy_mon_name = 'Monitor_01'
exp_code = 'pstbox'
sess_code = 'S_{0}'.format(int(time.mktime(time.localtime())))
iohubkwargs = {
    'psychopy_monitor_name': psychopy_mon_name,
    'experiment_code': exp_code,
    'session_code': sess_code,
    'serial.Pstbox': dict(name='pstbox', port=SERIAL_PORT, baud=BAUDRATE)
}

# Start the iohub server and set up devices.
io = launchHubServer(**iohubkwargs)
computer = Computer
display = io.devices.display
pstbox = io.devices.pstbox

print('Switching on lamp #3...')
pstbox.setLampState([0, 0, 1, 0, 0])
print('...done.')

# Create a window.
win = visual.Window(
    display.getPixelResolution(),
    units='pix', fullscr=True, allowGUI=False,
    screen=0
)

#####################################################################

#
# Set up fixation and stimulus.
#

# Instruction text.
instruction = visual.TextStim(
    win,
    text='Push a button as soon as the colored figure appears.\n\n'
         'Push any button to start.'
)

# Fixation spot.
fixSpot = visual.PatchStim(
    win, tex='none', mask='gauss',
    pos=(0, 0), size=(30, 30), color='black',
    autoLog=False
)

# Visual stimulus.
grating = visual.PatchStim(
    win, pos=(0, 0),
    tex='sin', mask='gauss',
    color=[1.0, 0.5, -1.0],
    size=(300.0, 300.0), sf=(0.01, 0.0),
    autoLog=False
)

#####################################################################

#
# Start the experiment.
#

pstbox.clearEvents()
start_time = computer.getTime()

# Display instruction and check if we collected any button events.
# If there is no button press within a 30 s period, quit.
instruction.draw()
win.flip()
while not pstbox.getEvents():
    if core.getTime() - start_time > 30:
        print('Timeout waiting for button event. Exiting...')
        io.quit()
        core.quit()

# Clear the screen.
win.flip()

nreps = 10
RT = np.array([])
button = np.array([])
io.wait(2)

for i in range(nreps):
    print('Trial #', i)

    # Raise process priorities.
    computer.setPriority('high')
    io.setPriority('high')

    # Draw the fixation.
    fixSpot.draw()
    win.flip()

    # Clear the PST box event buffers immediately after the
    # fixation is displayed.
    pstbox.clearEvents()

    # Wait a variable time until the stimulus is being presented.
    io.wait(1 + np.random.rand())

    # Draw the stimulus and have it displayed for approx. 0.5 s.
    grating.draw()
    t0 = win.flip()
    io.wait(0.5)

    # Clear the screen and wait a little while for possible late responses.
    win.flip()
    io.wait(0.25)

    # Lower process priorities.
    computer.setPriority('normal')
    io.setPriority('normal')

    # Check if we collected any button events.
    # If we did, use the first one to determine response time.
    pstevents = pstbox.getEvents()
    if pstevents:
        RT = np.append(RT, pstevents[0].time - t0)
        button = np.append(button, pstevents[0].button)
        print('RT: %f, Button: %d' % (RT[-1], button[-1]))
    else:
        RT = np.append(RT, np.nan)
        button = np.append(button, np.nan)
        print('No response.')

    print('---')

    # ITI
    io.wait(2)

#####################################################################

#
# All data collected; print some results.
#

print('Collected %d responses.' % np.count_nonzero(~np.isnan(RT)))
print('Mean RT: %f s' % np.nanmean(RT))
print('---')

#####################################################################

#
# Shut down.
#

# Switch off all lamps.
pstbox.setLampState([0, 0, 0, 0, 0])

# Close the window and quit the program.
io.quit()
core.quit()
