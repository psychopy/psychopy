#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This demo requires that an ioSync device is correctly connected to the computer
running this script.

Script used to test retrace onset timing accuracy of the psychopy win.flip()
method.

The script is written expecting that a specific light sensor is being used
and is connected to the ioSync. The test also allows using an LED to drive the
light sensor as a base line test to confirm the accuracy of the ioSync and this
test program.

The light sensor with breakout board used when writing this test can be found
at:

http://www.adafruit.com/products/1384
"""
from __future__ import absolute_import, division, print_function

from builtins import range
import time
from psychopy import visual, core,event
from psychopy.iohub import launchHubServer, EventConstants
import numpy as np

getTime=core.getTime

color_phase_flip_count = 10
iterations = 30

w, h = 1680, 1050
win = visual.Window((w, h), units='pix', color=[0, 0, 0],
                    fullscr=True, allowGUI=False, screen=0)
sqrVertices = [ [w/2, -h/2], [-w/2, -h/2], [-w/2, h/2], [w/2, h/2] ]

MAX_RAW = 2.0 ** 16 # 3.3v
MAX_LUX = 5.0 # 3.3v = 10^5 lux
MAX_AIN_V = 3.3
MAX_NORM = 1.0 # psychopy norm greyscale -1 to 1
LOG_LUX_RANGE = MAX_LUX
NORM_RANGE = 2.0
LOG_LUX_RATIO = LOG_LUX_RANGE/MAX_RAW
NORM_RATIO = NORM_RANGE/MAX_NORM
DIGITAL_ANALOG_16_STEP = MAX_AIN_V/MAX_RAW

def toLux(raw):
    """
    Used if LUX_AIN is set to between 0 and 7; indicating that the ioSync
    light meter peripheral is attached to that analog input line.

    Convert raw ioSync analog input value to lux value.
    """
    return np.power(10, raw * LOG_LUX_RATIO)

def toNorm(raw):
    """
    Convert raw ioSync analog input from lux meter to psychopy norm grayscale (-1 t0 1.0)
    value.
    """
    return np.power(MAX_NORM, raw * NORM_RATIO)


blackstim = visual.ShapeStim(win,
                 lineColor='grey',
                 lineWidth=0, #in pixels
                 fillColor=[-.25,-.25,-.25], #beware, with convex shapes this won't work
                 vertices=sqrVertices,#choose something from the above or make your own
                 closeShape=True,#do you want the final vertex to complete a loop with 1st?
                 pos= [-400,300], #the anchor (rotaion and vertices are position with respect to this)
                 interpolate=True,
                 opacity=1,
                 autoLog=False)#this stim changes too much for autologging to be useful

whitestim = visual.ShapeStim(win,
                 lineColor='white',
                 lineWidth=0, #in pixels
                 fillColor=[.25,.25,.25], #beware, with convex shapes this won't work
                 vertices=sqrVertices,#choose something from the above or make your own
                 closeShape=True,#do you want the final vertex to complete a loop with 1st?
                 #pos= [0.5,0.5], #the anchor (rotaion and vertices are position with respect to this)
                 interpolate=True,
                 opacity=1,
                 autoLog=False)#this stim changes too much for autologging to be useful


def showblack():
    fdraw_time=getTime()
    blackstim.draw()
    fcall_time=getTime()
    return fdraw_time, fcall_time, win.flip()

def showwhite():
    fdraw_time=getTime()
    whitestim.draw()
    fcall_time=getTime()
    return fdraw_time, fcall_time, win.flip()

def setLED(mcu, on):
    rid=mcu.setDigitalOutputByte(on)['id']
    rv=None
    while rv is None:
        r = mcu.getRequestResponse(rid)
        if r:
            rv = r['iohub_time']
            break
        time.sleep(0.0005)
    return rv

io=None
mcu=None
start_draw_times=[]
flip_called_times=[]
white_ftimes=[]
black_ftimes=[]
ai0_vals=[]
ai0_times=[]

try:
    psychopy_mon_name='testMonitor'
    exp_code='events'
    sess_code='S_{0}'.format(int(time.mktime(time.localtime())))
    iohub_config={
    "psychopy_monitor_name":psychopy_mon_name,
    "mcu.iosync.MCU":dict(serial_port='auto',monitor_event_types=['AnalogInputEvent']),#['DigitalInputEvent']),
    "experiment_code":exp_code,
    "session_code":sess_code
    }
    io=launchHubServer(**iohub_config)
    mcu=io.devices.mcu
    kb=io.devices.keyboard

    showblack()
    core.wait(.1)
    mcu.enableEventReporting(True)

    event.getKeys()
    io.clearEvents("all")
    mcu.getRequestResponse()

    i=0
    t=0
    ai0_vals=[]
    ai0_times=[]
    led_off_times=[]
    led_on_times=[]
    thresh_times=[]
    while not kb.getEvents() and t < iterations:
        ain_time=0
        for c in range(color_phase_flip_count):
            draw_start_time, flip_called_time, retrace_time = showwhite()
            ledtime=setLED(mcu,True)
            if c == 0:
                white_ftimes.append(retrace_time)
                led_on_times.append(ledtime)
            mcu_events = mcu.getEvents()
            for mcu_evt in mcu_events:
                if mcu_evt.type == EventConstants.ANALOG_INPUT:
                    ai0_times.append(mcu_evt.time)
                    ai0_vals.append(mcu_evt.AI_0)
                else:
                    thresh_times.append(mcu_evt.time)

        for c in range(color_phase_flip_count):
            draw_start_time, flip_called_time, retrace_time = showblack()
            ledtime=setLED(mcu,False)
            if c == 0:
                black_ftimes.append(retrace_time)
                led_off_times.append(ledtime)
            mcu_events = mcu.getEvents()
            for mcu_evt in mcu_events:
                if mcu_evt.type == EventConstants.ANALOG_INPUT:
                    ai0_times.append(mcu_evt.time)
                    ai0_vals.append(mcu_evt.AI_0)
                else:
                    thresh_times.append(mcu_evt.time)
        t+=1
except Exception:
    import traceback
    traceback.print_exc()
finally:
    if mcu:
        mcu.enableEventReporting(False)
    if io:
        io.quit()
    win.close()

# Save and Plot results
from matplotlib import pyplot as plt
ai0_times = np.asarray(ai0_times,dtype=np.float64)*1000.0
ai0_vals = np.asarray(ai0_vals,dtype=np.float64)
ai0_vals = toLux(ai0_vals)
led_off_times = np.asarray(led_off_times, dtype=np.float64)*1000.0
led_on_times = np.asarray(led_on_times, dtype=np.float64)*1000.0
white_ftimes = np.asarray(white_ftimes, dtype=np.float64)*1000.0
black_ftimes = np.asarray(black_ftimes,  dtype=np.float64)*1000.0
np.savez('retracetimingdata.npz', ain_times=ai0_times, ain_vals=ai0_vals,
         led_on_times=led_on_times, led_off_times=led_off_times,
         white_ftimes=white_ftimes, black_ftimes=black_ftimes)
plt.plot(ai0_times, ai0_vals)
mixx, maxx = min(ai0_times)-100,max(ai0_times)+100
miny, maxy = min(ai0_vals)-0.1, max(ai0_vals)+0.1
plt.xlim([mixx, maxx])
plt.ylim([miny, maxy])

for v in led_off_times:
    plt.plot((v, v), (miny, maxy), 'k-')#, label='LED_OFF')
#for v in thresh_times:
#    plt.plot((v, v), (miny, maxy), 'm-')
for v in led_on_times:
    plt.plot((v, v), (miny, maxy), 'c-')#, label='LED_ON')
for v in white_ftimes:
    plt.plot((v, v), (miny, maxy), 'g-')#, label='FLIP_LIGHT')
for v in black_ftimes:
    plt.plot((v, v), (miny, maxy), 'r-')#, label='FLIP_DARK')

plt.ylabel('Light Level ( Lux )')
plt.xlabel('Time ( msec )')
plt.title("LED Traces Synced to Retrace Timing Results")

plt.show()



