#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This demo requires that an ioSync device is correctly connected to the computer
running this script.

Script can be used to test the accuracy of the conversion from ioSync time
stamps to iohub the time base.
"""
from __future__ import absolute_import, division, print_function

from builtins import range
repetitions = 1000

import numpy as np
import time
from psychopy import core
from psychopy.iohub import launchHubServer
getTime = core.getTime

results = np.zeros((repetitions,3),dtype=np.float64)

iohub_config = {
"mcu.iosync.MCU": dict(serial_port='auto', monitor_event_types=[]),
}
io = launchHubServer(**iohub_config)
mcu = io.devices.mcu
mcu.enableEventReporting(True)

old_stuff = mcu.getRequestResponse()
io.clearEvents("all")

for i in range(repetitions):      
    request = mcu.requestTime()
    response = None
    while response is None:
        response = mcu.getRequestResponse(request['id'])
        if response:
            if response['id'] != request['id']:
                print("ERROR: Got REsponse %d; looking for %d"%(response['id'] ,request['id'] ))
                response = None
            results[i][0] = response['tx_time']*1000.0
            results[i][1] = response.get('iohub_time', (response['rx_time']*1000.0+response['tx_time']*1000.0)/2.0)
            results[i][2] = response['rx_time']*1000.0


    time.sleep(0.00075)
mcu.enableEventReporting(False)
io.quit()

txtimes = results[:, 0]
iotimes = results[:, 1]
rxtimes = results[:, 2]

e2edelays = rxtimes - txtimes
msgintervals = txtimes[1:]-txtimes[:-1]
mintime = min(txtimes.min(), iotimes.min(), rxtimes.min())
maxtime = max(txtimes.max(), iotimes.max(), rxtimes.max())

from matplotlib import pylab as pl
pl.xlim(mintime-1.0, maxtime+1.0)
pl.plot(txtimes, e2edelays, label="Round Trip Delay")
pl.plot(txtimes[1:], msgintervals, label="Msg Tx Intervals")
pl.xlabel("Time (msec)")
pl.ylabel("Duration (msec)")
pl.legend()

statstr = "Min: %.3f, Max: %.3f, Mean: %.3f, Std: %.3f"
rtdstats = statstr%(e2edelays.min(), e2edelays.max(), e2edelays.mean(),
                    e2edelays.std())
mtistats = statstr%(msgintervals.min(), msgintervals.max(), msgintervals.mean(),
                    msgintervals.std())
pl.title("Round Trip Delay:: %s\nMsg Tx Interval:: %s"%(rtdstats, mtistats))
pl.show()
