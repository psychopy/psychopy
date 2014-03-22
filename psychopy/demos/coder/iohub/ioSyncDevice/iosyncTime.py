# -*- coding: utf-8 -*-
"""
This demo requires that an ioSync device is correctly connected to the computer
running this script.

Script can be used to test the accuracy of the conversion from ioSync time
stamps to iohub the time base.
"""

repetitions = 100

import numpy as np    
import time
from psychopy import core
from psychopy.iohub import launchHubServer
getTime = core.getTime

results=np.zeros((repetitions,5),dtype=np.float64)

psychopy_mon_name = 'testMonitor'
exp_code = 'events'
sess_code = 'S_{0}'.format(long(time.mktime(time.localtime())))

iohub_config = {
"psychopy_monitor_name": psychopy_mon_name,
"mcu.iosync.MCU": dict(serial_port='auto', monitor_event_types=[]),
"experiment_code": exp_code,
"session_code": sess_code
}

io=launchHubServer(**iohub_config)
display=io.devices.display
mcu=io.devices.mcu
kb=io.devices.keyboard
experiment=io.devices.experiment

core.wait(0.5)

mcu.enableEventReporting(True)

print 'Running Test. Please wait.'
print   
old_stuff=mcu.getRequestResponse()
io.clearEvents("all")  

labels=('tx_time',
         'iohub_time',
         'rx_time',
         'rx_time - tx_time' ,
         'iohub_time - tx_time' ,
         'rx_time - iohub_time'
         )
print '\t'.join(labels)
print

for i in range(repetitions):      
    r=mcu.requestTime()
    stime=getTime()
    core.wait(0.1)
    hitFound=False
    while getTime()-stime < 0.5 and hitFound is False:
        responses = mcu.getRequestResponse()
        for r in responses:
            if r['iohub_time']:
                vals=(
                    (r['tx_time'])*1000.0,
                    (r['iohub_time'])*1000.0,
                    (r['rx_time'])*1000.0,
                    (r['rx_time']-r['tx_time'])*1000.0,
                    (r['iohub_time']-r['tx_time'])*1000.0,
                    (r['rx_time']-r['iohub_time'])*1000.0
                    )
                valstr=['%.3f'%(v) for v in vals]
                print '\t'.join(valstr)
            hitFound=True
            break

mcu.enableEventReporting(False)
io.quit()