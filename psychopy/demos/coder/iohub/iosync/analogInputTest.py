#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
"""This demo requires that an ioSync device is correctly connected to the
computer running this script.

Simple example of how to enable ioSync analog input reading. The demo starts
the iosync with analog input events enabled. Analog input events are saved to
a text file and saved to the ioHub Data Store file.

ioSync supports 8 single ended analog inputs. All channels are sampled at
1000 Hz Analog inputs are 16 bit at a HW level, but realistically only 
expect ~ 12 - 13 bit effective resolution. More testing is needed to really 
quantify this.

Data is currently output in raw form for each channel, with a value range
of 0 (0.0 V) to 2**16 (3.3 V).

IMPORTANT: Input voltage to an analog input pin must be between AGND (0.0 V)
and AREF (3.3 V) Volts. Providing a voltage outside this range can damage the
AIN line or the Teensy 3 itself.

Connect analog input sources to ioSync inputs AI_0 to AI_7; connect grounds to
the AGND pin.

Analog input channels which are not connected to anything 'float'. If you want
unused channels to be fixed at ground, connect each unused channel to the AGND
pin.
"""


import time
import sys
import codecs
from psychopy import core
from psychopy.iohub.client import launchHubServer
getTime = core.getTime

class EncodedOut:
    def __init__(self, enc='utf-8'):
        self.enc = enc
        self.stdout = sys.stdout
    def __enter__(self):
        if sys.stdout.encoding is None:
            w = codecs.getwriter(self.enc)
            sys.stdout = w(sys.stdout)
    def __exit__(self, exc_ty, exc_val, tb):
        sys.stdout = self.stdout    

io = None
mcu = None

try:
    psychopy_mon_name = 'testMonitor'
    exp_code = 'iosync_ain'
    sess_code = 'S_{0}'.format(long(time.mktime(time.localtime())))
    iohub_config = {
        'mcu.iosync.MCU': dict(serial_port='auto', 
                               monitor_event_types=['AnalogInputEvent', ]),
        'experiment_code': exp_code,
        'session_code': sess_code
    }
    io = launchHubServer(**iohub_config)
    mcu = io.devices.mcu
    kb = io.devices.keyboard

    mcu.enableEventReporting(True)
    io.clearEvents()
    i = 0
    print("Saving Analog Data to File. Press 'escape' Key to Quit...")
    start_time = end_time = None
    ain_sample_count = 0
    aout = file('%s.txt'%(exp_code), 'w')
    while 'escape' not in kb.getKeys():
        mcu_events = mcu.getEvents()
        if mcu_events:
            if start_time is None:
                start_time = mcu_events[0].time
            end_time = mcu_events[-1].time
            ain_sample_count = ain_sample_count + len(mcu_events)
            for mcu_evt in mcu_events:
                aout.write(
                    '{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\n'.format(
                        mcu_evt.time,
                        mcu_evt.AI_0,
                        mcu_evt.AI_1,
                        mcu_evt.AI_2,
                        mcu_evt.AI_3,
                        mcu_evt.AI_4,
                        mcu_evt.AI_5,
                        mcu_evt.AI_6,
                        mcu_evt.AI_7,
                    ))
            if ain_sample_count%1000 < 10:
                print("Samples Read: {}".format(ain_sample_count), end = '\r')
        core.wait(0.002, 0)
    aout.flush()
    aout.close()
    print("")
    print("Analog recording complete.")
    io.clearEvents()
except Exception:
    import traceback
    traceback.print_exc()
finally:
    if mcu:
        mcu.enableEventReporting(False)
    if io:
        io.quit()
