#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This demo requires that an ioSync and LabJack U6 device are correctly connected
to the computer running this script.

This script can be used to test the error in the base analog input device delay
calculated for multi channel analog input events.  It seems that default
delay error is quite constant for a specific computer and analog input device.
Therefore, running this script and recording the calculated delay adjustment
that should be applied should result in analog input event times that are 
within +/- 1 msec of accuracy.

Description of Test
````````````````````

An iohub script is run using a LabJack AnalogInput device (any supported
AnalogInput device can be used though), as well as a mcu.ioSync device,
which uses a Teensy 3 MCU running the ioSync Sketch.

The script starts recording data from the Analog Input Device and then
repeatedly alternates between setting ioSync DOUT_0 and DOUT_1 high, 
noting the iohub PC time that each TTL state change occurred. Multi Channel
Analog Input events are monitored after each TTL state change until the
associated AIN channel reflects the change made. The iohub time of the first
event that contains the changed AIN value is also noted.

By knowing the actual time each ioSync DOUT change occurred, as well as the 
time given to the AIN event that reflected that change, the error in the base 
AnalogInput device delay can be calculated. This error can then be used to 
correct the delays and times of multichannel analog input events so that they
are within 1 msec of the actual event time.

The delay offset can be set by adding the following setting to the analog
input device's configuration:

delay_offset: <calculated_mean_delay_error>
   
Hardware Setup Needed
``````````````````````

To Use this script, the following devices need to be available on the iohub
computer and connected in the fashion described.

1) mcu.ioSync device connected to the iohub PC with the USB interface
    provided by the Teensy 3 MCU used by ioSync. 

2) A Labjack U6 Analog Input device connected to the iohub PC with the U6 
    USB connection.

3) Drivers required for both the ioSync and LabJack U6 devices must be 
    installed.
    
2) ioSync Digital Output Lines 0 and 1 must be connected to Analog Input
channels AIN0 and AIN1 of the Labjack. So:

Teensy3 Pin         LabJack Terminal

2                   AIN_0
3                   AIN_1

 
Test Parameters
````````````````

The analog_input_channels variable declared below indicates the ioSync
DOUT pin and AnalogInput channel numbers to use for the test. It is suggested 
to leave these at [0,1]

The repetitions variable specifies how many times the line defined by 
analog_input_channels should be toggled through. For example, assuming 
analog_input_channels = [0.1] and repetitions = 10, then 2x10 = 20 state
changes will occur and will be used for the delay error correction calculation.
  
"""
from __future__ import absolute_import, division, print_function

from builtins import range
analog_input_channels=[0,1]
repetitions=5

import numpy as np
from psychopy import core
import time
from psychopy.iohub import launchHubServer
getTime=core.getTime

try:
    ttl_bytes=[]
    for r in range(repetitions):
        ttl_bytes.extend(analog_input_channels)
    ai_event_results=np.zeros((len(ttl_bytes),6),dtype=np.float64)

    psychopy_mon_name='testMonitor'
    exp_code='events'
    sess_code='S_{0}'.format(int(time.mktime(time.localtime())))
    iohub_config={
    "psychopy_monitor_name":psychopy_mon_name,
    "mcu.iosync.MCU":dict(serial_port='auto',monitor_event_types=[]),
    "daq.hw.labjack.AnalogInput": dict(name='ain',
                                       #delay_offset=0.0159915408328,
                                       channel_sampling_rate=1000,
                                       resolution_index=1,
                                       settling_factor=1,
                                       model_name='U6'),
    "experiment_code":exp_code, 
    "session_code":sess_code
    }
    io=launchHubServer(**iohub_config)
    mcu=io.devices.mcu
    kb=io.devices.keyboard
    ain=io.devices.ain
    experiment=io.devices.experiment
    mcu.setDigitalOutputByte(0)
    mcu.enableEventReporting(True)
    ain.enableEventReporting(True)
    delay_offset=ain.getDelayOffset()
    
    print()
    print('>> Running test using a delay_offset of',delay_offset)
    print('>> Please wait.')    
    print()
    core.wait(1.0)
    mcu.getRequestResponse()
    io.clearEvents("all")   
    response_times=[]
    for i,c in enumerate(ttl_bytes):      
        ain_channel_name='AI_%d'%c
        v=np.power(2,c)
        r=mcu.setDigitalOutputByte(v)
        dout_id=r['id']
        found_analog_trigger=False
        found_dout_response=False
        stime=getTime()
        ai_event_results[i,:]=0.0
        while getTime()-stime < 2.0:
            if found_analog_trigger is False:        
                ai_events=ain.getEvents(asType='dict')        
                for ai in ai_events:
                    if ai[ain_channel_name] > 3.0:
                        ai_event_results[i,0]=v
                        ai_event_results[i,2]=ai['device_time']
                        ai_event_results[i,3]=ai['logged_time']
                        ai_event_results[i,4]=ai['time']
                        ai_event_results[i,5]=ai['delay']
                        found_analog_trigger=True
                        break
    
            if found_dout_response is False:
                responses = mcu.getRequestResponse()
                for resp in responses:
                    if resp['id'] == dout_id:
                        ai_event_results[i,1]=resp['iohub_time']
                        found_dout_response=True
                        break
    
            if found_analog_trigger and found_dout_response:
                dtime=ai_event_results[i,1]
                atime=ai_event_results[i,4]
                print('Hit:',i,v,dtime,atime,atime-dtime)
                io.sendMessageEvent("%d %d %.6f %.6f %.6f"%(i,v,dtime,atime,atime-dtime),"DOUT")
                break
                
        if found_analog_trigger is False or found_dout_response is False:
            print('*******\nTIMEOUT WAITING FOR REQUIRED INPUTS\n**********')
            io.sendMessageEvent("%d %d NO_RESPONSE"%(i,v),"DOUT")
    
        core.wait(0.2,.1)
        mcu.getRequestResponse()  
        io.clearEvents('all')
        
        
    mcu.setDigitalOutputByte(0)
    core.wait(0.2,.1)
    mcu.getRequestResponse()  
    mcu.enableEventReporting(False)  
    ain.enableEventReporting(False)  
    io.clearEvents('all')
    
    analog_timing_errors=ai_event_results[:,1]-ai_event_results[:,4]
    avg_timing_error=analog_timing_errors.mean()  
    ai_event_results[:,5]=ai_event_results[:,5]-avg_timing_error  
    ai_event_results[:,4]=ai_event_results[:,4]+avg_timing_error
    coorrected_timing_errors=ai_event_results[:,1]-ai_event_results[:,4]
    
    print('--------------------\n')
    print('Calculated Delay error (in msec):\n\tMin: %.6f\n\tMax: %.6f\n\tMean: %.6f'%(analog_timing_errors.min()*1000.0,
                                                                                analog_timing_errors.max()*1000.0,
                                                                                avg_timing_error*1000.0))
    if delay_offset == 0.0:
        print()
        print('To correct for this AnalogInput Delay Error,\nset the "delay_offset" device configuration setting to',avg_timing_error)
        print() 
        print('Corrected delay error (in msec):\n\tMin: %.6f\n\tMax: %.6f\n\tMean: %.6f'%(coorrected_timing_errors.min()*1000.0,
                                                                                    coorrected_timing_errors.max()*1000.0,
                                                                                    coorrected_timing_errors.mean()*1000.0))
    print()
    print('--------------------')
except Exception:
    import traceback
    traceback.print_exc()    
finally:
    if mcu:    
        mcu.enableEventReporting(False)  
    if ain:
        ain.enableEventReporting(False)  
    if io:
        io.quit() 
