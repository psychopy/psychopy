# -*- coding: utf-8 -*-
"""
Script can be used to test the error in the base analog input device delay
calculated for multi channel analog input events.  It seems that default
delay error is quite constant for a specific computer and analog input device.
Therefore, running this script and recording the calculated delay adjustment
that should be applied should result in analog input event times that are 
within 1 msec of accuracy.

Description of Test
````````````````````

An iohub script is run using a LabJack AnalogInput device (any supported
AnalogInput device can be used though), as well as a mcu.ioSync device,
which uses a Teensy 3 MCU running the ioSync Sketch.

The script srarts recording data from the Analog Input Device and then 
repeatedly alternates between setting ioSync DOUT_0 and DOUT_1 high, 
noting the iohub PC time that each TTL state change occurred. Multi Channel
Analog Input events are monitored after each TTL state change until the
associated AIN channel reflects the change made. The iohub time of the first
event that contains the changed AIN value is also noted.

By knowing the actual time each ioSync DOU change occurred, as well as the 
time given to the AIN event that reflected that change, the error in the base 
AnalogInput device delay can be calculated. This error can then be used to 
correct the delays and times of multichannel analog input events so that they
are within 1 msec of the actual event time.
   
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
analog_input_channels=[0,1]
repetitions=20

import numpy as np    
import time
from psychopy import core
from psychopy.iohub import launchHubServer,Computer
getTime=core.getTime

ttl_bytes=[]
for r in range(repetitions):
    ttl_bytes.extend(analog_input_channels)

psychopy_mon_name='testMonitor'
exp_code='events'
sess_code='S_{0}'.format(long(time.mktime(time.localtime())))

iohub_config={
"psychopy_monitor_name":psychopy_mon_name,
"mcu.iosync.MCU":dict(serial_port='COM8',monitor_event_types=['DigitalInputEvent']),

"daq.hw.labjack.AnalogInput": dict(name='ain',
                                   channel_sampling_rate=1000,
                                   resolution_index=1,
                                   settling_factor=1,
                                   model_name='U6'),
"experiment_code":exp_code, 
"session_code":sess_code
}

io=launchHubServer(**iohub_config)

Computer.enableHighPriority()
io.enableHighPriority()

display=io.devices.display
mcu=io.devices.mcu
kb=io.devices.keyboard
ain=io.devices.ain
experiment=io.devices.experiment

ai_event_results=np.zeros((len(ttl_bytes),6),dtype=np.float32)
#print 'analog_inputs shape:',ai_event_results.shape
        
mcu.setDigitalOutputByte(0)
mcu.enableEventReporting(True)
ain.enableEventReporting(True)

print 'Running Test. Please wait.',    
time.sleep(1.0) 
for i,c in enumerate(ttl_bytes):
    io.clearEvents("all")             
    ain_channel_name='AI_%d'%c
    v=np.power(2,c)
    stime=getTime()
    r=mcu.setDigitalOutputByte(v)
    etime=getTime()
    io.sendMessageEvent("%d %d %.6f"%(i,v,etime-stime),"DOUT",0.0,etime)
    #reply=mcu.getDigitalInputs()
    #rid=reply['id']
    # TODO: Fix getRequestResponse; sometimes it hangs right now.     
    #response=None
    #while response is None:
    #    response=mcu.getRequestResponse(rid)
    #print response#'.',
    found_analog_trigger=False
    while found_analog_trigger is False:
        for din in mcu.getEvents():
            print 'DIN:',din
        for ai in ain.getEvents(asType='dict'):
            if ai[ain_channel_name] > 3.0:
                #print "Hit: ",etime,ain_channel_name,ai
                ai_event_results[i,0]=v
                ai_event_results[i,1]=(etime+stime)/2.0
                ai_event_results[i,2]=ai['device_time']
                ai_event_results[i,3]=ai['logged_time']
                ai_event_results[i,4]=ai['time']
                ai_event_results[i,5]=ai['delay']
                found_analog_trigger=True
                break
        time.sleep(0.01)
io.clearEvents('all')
mcu.setDigitalOutputByte(0)
mcu.enableEventReporting(False)  
ain.enableEventReporting(False)  


analog_timing_errors=ai_event_results[:,1]-ai_event_results[:,4]
avg_timing_error=analog_timing_errors.mean()  
ai_event_results[:,5]=ai_event_results[:,5]-avg_timing_error  
ai_event_results[:,4]=ai_event_results[:,3]-ai_event_results[:,5]
coorrected_timing_errors=ai_event_results[:,1]-ai_event_results[:,4]

print
print
print '--------------------'
print 'Calculated Delay error (in msec):\n\tMin: %.6f\n\tMax: %.6f\n\tMean: %.6f'%(analog_timing_errors.min()*1000.0,
                                                                            analog_timing_errors.max()*1000.0,
                                                                            avg_timing_error*1000.0)
print
print 'To correct for AnalogInput Delay Error:'
print '\tSubtract %.3f msec from AIN event delays.'%(avg_timing_error*1000.0)
print '\tAdd %.3f msec to analog input event times.'%(avg_timing_error*1000.0)
print 
print 'Corrected delay error (in msec):\n\tMin: %.6f\n\tMax: %.6f\n\tMean: %.6f'%(coorrected_timing_errors.min()*1000.0,
                                                                            coorrected_timing_errors.max()*1000.0,
                                                                            coorrected_timing_errors.mean()*1000.0)
print '--------------------'

Computer.disableHighPriority()
io.disableHighPriority()

io.quit() 
