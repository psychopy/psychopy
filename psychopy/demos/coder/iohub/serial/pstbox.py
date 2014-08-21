from __future__ import print_function
import time
import numpy as np
from psychopy import core, visual
from psychopy.iohub import launchHubServer

#####################################################################

#
# Device setup
#

# Settings for serial port (PST response box) communication.
SERIAL_PORT = 'COM5'
BAUDRATE = 19200

# configure iohub
psychopy_mon_name = 'Monitor_01'
exp_code = 'pstbox'
sess_code = 'S_{0}'.format(long(time.mktime(time.localtime())))
iohubkwargs = {'psychopy_monitor_name': psychopy_mon_name,
               'experiment_code': exp_code,
               'session_code': sess_code,
               'serial.Serial': dict(name='serial', port=SERIAL_PORT, baud=BAUDRATE,
                                     event_parser=dict(byte_diff=True))}

# start the iohub server and set up display and PST box devices
io = launchHubServer(**iohubkwargs)
display = io.devices.display
pstbox = io.devices.serial

# Prepare the PST box.
#
# Bit 7 = 128 -> Enable/Disable streaming.
# Bit 6 =  64 -> Lower bits control lamp state.
# Bit 5 =  32 -> Enable/Disable button queries.
# Bit 0-4 = 1-16 -> Enable/Disable Lamp 0-4.
#
# Source: https://psychtoolbox-3.googlecode.com/svn/beta/Psychtoolbox/PsychHardware/CMUBox.m
print('Switching response box to streaming mode and switching on lamp #3...')
pstbox.write(chr(np.uint8(128+32+64+4)))
core.wait(0.25)
print('...done.')

# Start collecting data from the PST box in the background.
pstbox.enableEventReporting(True)

# Create a window.
win = visual.Window(display.getPixelResolution(),
                    units='pix',
                    fullscr=True, allowGUI=False,
                    screen=0)

#####################################################################

#
# Set up fixation and stimulus.
#

# Instruction text.
instruction = visual.TextStim(win, text='Push a button as soon as the colored figure appears.\n\nPush any button to start.')

# Fixation spot.
fixSpot = visual.PatchStim(win, tex='none', mask='gauss',
                           pos=(0, 0), size=(30, 30), color='black', autoLog=False)

# Visual stimulus.
grating = visual.PatchStim(win, pos=(0, 0),
                           tex='sin', mask='gauss',
                           color=[1.0, 0.5, -1.0],
                           size=(300.0, 300.0), sf=(0.01, 0.0),
                           autoLog=False)

#####################################################################

#
# Start the experiment.
#

# Display instruction.
instruction.draw()
win.flip()
io.clearEvents('serial')
# Check if we collected any button events.
# If we did, use the first one to determine response time.
while not pstbox.getEvents():
    continue

win.flip()

nreps = 10
RT = np.array([])
core.wait(2)

for i in range(nreps):
    print('Trial #', i)

    # Draw the fixation.
    fixSpot.draw()
    win.flip()

    # Clear the PST box event buffers immediately after the fixation is displayed.
    io.clearEvents('serial')

    # Wait a variable time until the stimulus is being presented.
    core.wait(1+np.random.rand())

    # Draw the stimulus.
    grating.draw()
    t0 = win.flip()
    core.wait(0.5)

    # Clear the screen and wait a little while for possible late responses.
    win.flip()
    core.wait(0.25)

    # Check if we collected any button events.
    # If we did, use the first one to determine response time.
    pstevents = pstbox.getEvents()
    if pstevents:
        RT = np.append(RT, pstevents[0].time - t0)
        print('RT:', RT[-1])
    else:
        RT = np.append(RT, np.nan)
        print('No response.')

    print('---')

    # ITI
    core.wait(2)

#####################################################################

#
# All data collected; print some results.
#

print('Collected', np.count_nonzero(~np.isnan(RT)), 'responses.')
print('Mean RT:', np.nanmean(RT), 's')
print('---')

#####################################################################

#
# Shut down.
#

# Stop recording events from the PST box and switch off all lamps.
pstbox.enableEventReporting(False)
pstbox.write(chr(np.uint8(64)))

# Close the window and quit the program.
io.quit()
core.quit()
