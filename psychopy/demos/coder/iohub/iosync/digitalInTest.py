#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This demo requires that an ioSync device is correctly connected to the computer
running this script. Some switches or buttons also need to be connected to
at least one of the digital input lines of the ioSync so they can be used
to generate the digital input events.

This is a simple example of how to enable ioSync digital input events.
The demo starts the iosync with digital input events enabled. An ioSync
DigitalInputEvent is created each time one of the eight digital input lines
changes state. The event returns a 'state' byte, giving the value of all input
lines when the event occurred, as well as the time the event was detected by
the ioSync hardware.

ioSync supports 8 digital inputs. Digital inputs are sampled at 1000 Hz.
 
A state of 0 indicates no input lines are high. If DI_0
is high, state will equal 1, DI_1 = 2,  DI_2 = 4 etc. 

So digital input state = sum(2**di), where di is the index of an input that
is high, bound by 0 <= di <= 7.

If the ioSync program (iosync.ino) running on the teensy 3 shuld be compiled
with the following define setting:

#define DIGITAL_INPUT_TYPE INPUT_PULLUP

This turns on the internal pullup resistors on the T3. If the define is set
to INPUT, then you will need to provide a resistor between the ground pin and
the digital input ground wire.

IMPORTANT: Input voltage to a digital input pin must be between 0.0 V and 3.3 V 
or you may damage the Teensy 3. The Teensy 3.1 supports digital inputs up to
5 V.
"""
from __future__ import absolute_import, division, print_function

import time
from psychopy import core
from psychopy.iohub import launchHubServer
getTime=core.getTime

try:
    psychopy_mon_name='testMonitor'
    exp_code='events'
    sess_code='S_{0}'.format(int(time.mktime(time.localtime())))
    iohub_config={
    "psychopy_monitor_name":psychopy_mon_name,
    "mcu.iosync.MCU":dict(serial_port='auto',monitor_event_types=['DigitalInputEvent',]),
    "experiment_code":exp_code, 
    "session_code":sess_code
    }
    io=launchHubServer(**iohub_config)
    mcu=io.devices.mcu
    kb=io.devices.keyboard
        
    core.wait(0.5)
    mcu.enableEventReporting(True)
    io.clearEvents("all")
    while not kb.getEvents():   
        mcu_events=  mcu.getEvents()
        for mcu_evt in mcu_events:
            print('{0}\t{1}'.format(mcu_evt.time,mcu_evt.state))
        core.wait(0.002,0)
    io.clearEvents('all')
except Exception:
    import traceback
    traceback.print_exc()    
finally:
    if mcu:    
        mcu.enableEventReporting(False)   
    if io:
        io.quit() 
