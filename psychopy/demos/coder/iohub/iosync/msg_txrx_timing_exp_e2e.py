#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This demo requires that an ioSync device is correctly connected to the computer
running this script.

Script can be used to test the round trip time from when an a psychopy experiment
issues an ioSync message request to when the psychopy script receives a reply.
In this test the 'GET_TIME' request type is sent, which causes ioSync to
return the current ioSync MCU 48 bit usec time.

Each test iteration does the following(in sudo code):

    request = iosync.requestTime()

    reply_id = None
    while reply_id is None:
        reply = iosync.getReplies()
        if reply.id == request.id:
            reply_id = reply.id
            tx_time = request.tx_time
            rx_time = response.rx_time
            round_trip_delay = rx_time - tx_time

    sleep(0.00075) # sleep 750 usec before running next iteration

Both the round trip time of iohub sending and receiving the request, and the
full round trip time from experiment script send to receive, are recorded
and plotted separately for comparison purposes.
"""
from __future__ import absolute_import, division, print_function

# How many request - reply iterations should be run.
from builtins import range
repetitions = 10000

import numpy as np
import time
from psychopy import core
from psychopy.iohub import launchHubServer
getTime = core.getTime

# Array for storing all timing results
results = np.zeros((repetitions,3),dtype=np.float64)

# Start iohub with the ioSync enabled.
iohub_config = {
"mcu.iosync.MCU": dict(serial_port='auto', monitor_event_types=[]),
}
io = launchHubServer(**iohub_config)
mcu = io.devices.mcu

# Tell ioSync to start collecting data
mcu.enableEventReporting(True)

# clear out any old events before starting test
old_stuff = mcu.getRequestResponse()
io.clearEvents("all")

# Run test
for i in range(repetitions):
    # ASk ioSync MCU for it's current time.
    exp_start_time=getTime()
    request = mcu.requestTime()
    response = None
    # Loop until the response maatching the request ID is found
    while response is None:
        response = mcu.getRequestResponse(request['id'])
        exp_end_time=getTime()
        if response:
            if response['id'] != request['id']:
                # This should never happen. ;)
                print("ERROR: Got Response %d; looking for %d"%(response['id'],
                                                                request['id']))
                response = None

            # Collect time request was sent (tx_time) and time response was
            # received (rx_time).
            results[i][0] = response['tx_time']*1000.0
            results[i][1] = (exp_end_time - exp_start_time)*1000.0#response.get('iohub_time', ((response['rx_time']*1000.0+response['tx_time']*1000.0)/2.0))
            results[i][2] = response['rx_time']*1000.0

    # Give a quick (750 usec) break so the process does not hog 100% of the CPU.
    time.sleep(0.00075)

# Test Done. Stop recording from ioiSync and close ioHub Process
mcu.enableEventReporting(False)
io.quit()

# Calculate measures of interest from collected data
txtimes = results[:, 0]
expe2edelay = results[:, 1]
rxtimes = results[:, 2]

e2edelays = rxtimes - txtimes
msgintervals = txtimes[1:]-txtimes[:-1]

mintime = min(txtimes.min(),  rxtimes.min())
maxtime = max(txtimes.max(),  rxtimes.max())

statstr = "Min: %.3f, Max: %.3f, Mean: %.3f, Std: %.3f"
rtdstats = statstr%(e2edelays.min(), e2edelays.max(), e2edelays.mean(),
                    e2edelays.std())
expstats = statstr%(expe2edelay.min(), expe2edelay.max(), expe2edelay.mean(),
                    expe2edelay.std())

# Plot the results.
from matplotlib import pylab as pl
pl.xlim(mintime-1.0, maxtime+1.0)
pl.plot(txtimes, e2edelays, label="ioHub")
pl.plot(txtimes, expe2edelay, label="Experiment")
pl.xlabel("Time (msec)")
pl.ylabel("Round Trip Delay (msec)")
pl.legend()
pl.title("ioHub-ioSync Delay:: %s\nPsychoPy-ioSync Delay:: %s"%(rtdstats, expstats))
pl.show()
