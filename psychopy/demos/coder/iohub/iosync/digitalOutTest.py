#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This demo requires that an ioSync device is correctly connected to the computer
running this script.

This demo illustrates how to use the digital output and input functionality
of the ioSync device, testing the time difference between when a dout pin is
changed to when that change is detected by a connected din pin and a
DigitalInput event received.

Wiring:

DOUT_0 to DIN_8
"""
from __future__ import absolute_import, division, print_function

from builtins import range
repetitions=10

import time
from psychopy import core
from psychopy.iohub import launchHubServer
getTime=core.getTime

io = None
mcu = None
ain = None

dout_times = []
din_times=[]

try:
    psychopy_mon_name='testMonitor'
    exp_code='events'
    sess_code='S_{0}'.format(int(time.mktime(time.localtime())))
    iohub_config={
    "psychopy_monitor_name":psychopy_mon_name,
    "mcu.iosync.MCU":dict(serial_port='auto',monitor_event_types=['DigitalInputEvent']),
    "experiment_code":exp_code, 
    "session_code":sess_code
    }
    io=launchHubServer(**iohub_config)
    mcu=io.devices.mcu
    kb=io.devices.keyboard
    experiment=io.devices.experiment
    core.wait(0.5)
    mcu.enableEventReporting(True)
    
    print('Running Test. Please wait.')
    print()

    mcu.setDigitalOutputByte(0)
    old_stuff=mcu.getRequestResponse()
    io.clearEvents("all")      
    for i in range(repetitions): 
        for dl in [0, 1, 0, 1, 0, 1, 0, 1]:
            mcu.setDigitalOutputByte(dl)
            core.wait(0.25)
            resp_hit=False
            stime=getTime()
            while getTime()-stime < 0.5 and resp_hit is False:
                responses = mcu.getRequestResponse()
                for r in responses:
                    dout_times.append(r['iohub_time'])
                    resp_hit = True
                    break

            resp_hit=False
            stime=getTime()
            while getTime()-stime < 0.5 and resp_hit is False:
                for dine in mcu.getEvents():
                    din_times.append(dine.time)
                    resp_hit = True
                    break

    core.wait(0.25, 0)
    responses = mcu.getRequestResponse()            
except Exception:
    import traceback
    traceback.print_exc()    
finally:
    if mcu:    
        mcu.setDigitalOutputByte(0)
        mcu.enableEventReporting(False)  
    if io:
        io.quit()

import numpy as np
import matplotlib.pyplot as plt
din_array = np.asarray(din_times)
dout_array = np.asarray(dout_times)

# diff between psychopy.iohub time digital out was sent by ioSync and
# psychopy.iohub time digital input was received by ioSync.
# This will give a sense of the accuracy of the calculated cmd exec and
# event iohub times. Ideally there should be no difference between the two times
# in this test.
#
diff = (din_array-dout_array)*1000.0

diff_min=diff.min()
diff_max=diff.max()
diff_mean=diff.mean()
diff_std=diff.std()

plt.hist(diff,bins=50)
plt.title("Min: %.3f, Max: %.3f, Mean: %.3f, Stdev: %.3f"%(diff_min,diff_max,diff_mean,diff_std))
plt.show()