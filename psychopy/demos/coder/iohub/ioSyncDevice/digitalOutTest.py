# -*- coding: utf-8 -*-
"""
This demo requires that an ioSync device is correctly connected to the computer
running this script.

This demo illustrates how to use the digital output functionality of the ioSync
device, allowing control of 8 digital output lines.
"""

repetitions=10

import time
from psychopy import core
from psychopy.iohub import launchHubServer
getTime=core.getTime

io=None
mcu=None
ain=None

try:
    psychopy_mon_name='testMonitor'
    exp_code='events'
    sess_code='S_{0}'.format(long(time.mktime(time.localtime())))
    iohub_config={
    "psychopy_monitor_name":psychopy_mon_name,
    "mcu.iosync.MCU":dict(serial_port='auto',monitor_event_types=[]),
    "experiment_code":exp_code, 
    "session_code":sess_code
    }
    io=launchHubServer(**iohub_config)
    mcu=io.devices.mcu
    kb=io.devices.keyboard
    experiment=io.devices.experiment
    core.wait(0.5)
    mcu.enableEventReporting(True)
    
    print 'Running Test. Please wait.'
    print   
    labels=(
             'tx_time',
             'iohub_time',
             'iohub_time - tx_time' ,
             )       
    print '\t'.join(labels)
    print

    mcu.setDigitalOutputByte(0)
    old_stuff=mcu.getRequestResponse()
    io.clearEvents("all")      
    for i in range(repetitions): 
        for dl in [16,32,64,128,16,48,112,242]:        
            mcu.setDigitalOutputByte(dl)
            core.wait(0.25)
            resp_hit=False
            stime=getTime()
            while getTime()-stime < 0.5 and resp_hit is False:
                responses = mcu.getRequestResponse()
                for r in responses:
                    if r['iohub_time']:
                        vals=(
                            (r['tx_time'])*1000.0,
                            (r['iohub_time'])*1000.0,
                            (r['iohub_time']-r['tx_time'])*1000.0
                            )
                        valstr=['%.3f'%(v) for v in vals]
                        print '\t'.join(valstr)            
                        resp_hit=True
                        break
    core.wait(0.25,0)
    responses = mcu.getRequestResponse()            
except:
    import traceback
    traceback.print_exc()    
finally:
    if mcu:    
        mcu.setDigitalOutputByte(0)
        mcu.enableEventReporting(False)  
    if io:
        io.quit()