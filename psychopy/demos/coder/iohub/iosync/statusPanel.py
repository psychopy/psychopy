#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This demo requires that an ioSync device is correctly connected to the computer
running this script.

This demo displays the ioSync digital and analog input values in real time.
The GUI can also be used to toggle the state of any of the digital output lines.
"""
from __future__ import absolute_import, division, print_function

from builtins import range
LUX_AIN = 0

import sys
from psychopy import core, visual, event
from _statusPanelStim import AnalogMeter, DigitalLineStateButton
from psychopy.iohub import EventConstants, launchHubServer, MouseConstants
getTime = core.getTime

def main():
    """
    Main demo logic. Called at the end of the script so locally defined
    functions and globals are loaded prior to demo starting.
    """
    mcu = None
    io = None
    kb = None
    iomouse=None
    digital_input_state=0
    digital_output_state=0
    last_analog_in_event=None
    try:
        # create display graphics
        #
        w, h = 800, 600
        win = visual.Window((w, h), units='pix', color=[0, 0, 0],
                            fullscr=False, allowGUI=True, screen=0)

        # Various text stim used on the status panel.
        #
        demo_title = visual.TextStim(win, color='#FFFFFF',height=24, wrapWidth=w,
                            text = u"ioSync Demo Initializing, Please Wait.",
                            pos=[0, 300], alignHoriz='center',alignVert='top')
        analog_in_txt = visual.TextStim(win, color='#FFFFFF',height=18,
                            text = u"Analog Input Levels", wrapWidth=w,
                            pos=[-375, 230], alignHoriz='left',alignVert='center')
        digital_in_txt = visual.TextStim(win, color='#FFFFFF',height=18,
                            text = u"Digital Input States", wrapWidth=w,
                            pos=[-375, -50], alignHoriz='left',alignVert='center')
        digital_out_txt = visual.TextStim(win, color='#FFFFFF',height=18, wrapWidth=w,
                            text = u"Digital Output States (Click button to toggle state)",
                            pos=[-375, -175], alignHoriz='left',alignVert='center')
        static_text_stim=[demo_title,analog_in_txt,digital_in_txt,digital_out_txt]

        # Draw some text indicating the demo is loading. It can take a couple
        # seconds to initialize and fire everything up. ;)
        #
        demo_title.draw()
        win.flip()
        demo_title.setText('ioSync MCU Demo. Press ESC to Exit.')

        # Create the 8 analog input gauges.
        ain_gauges = []
        for i in range(8):
            ain_name = "AI_%d" % (i)
            meter = AnalogMeter(win, dial_color=[1, 1, 1],
                                arrow_color=[-0.8, -0.8, -0.8],
                                size=0.2, pos=(
                    -0.75 + (i % 4) * .5, 0.025 + .4 * (1 - int(i/4))),
                                title=ain_name)
            meter.ain_name = ain_name
            ain_gauges.append(meter)

        # forces pyglet to get events from the windows event queue so window
        # does not report being non responsive.
        core.wait(0.05)

        # Create digital input state buttons and digital output control buttons
        digital_in_lines=[]
        digital_out_lines=[]
        for i in range(8):
            din_name = "DI_%d" % (i)
            # digital inputs are set to use pull ups by default,
            # so 'off' is high and 'on' is when the line goes low.
            din_state_button = DigitalLineStateButton(win, i, './off.png', './on.png',
                     pos=(-350+i*100,-100),size=(50,50), title=din_name, initial_state = True)
            digital_in_lines.append(din_state_button)

            dout_name = "DO_%d" % (i)

            dout_state_button = DigitalLineStateButton(win, i, './on.png', './off.png',
                     pos=(-350+i*100,-225),size=(50,50), title=dout_name)
            digital_out_lines.append(dout_state_button)

        # forces pyglet to get events from the windows event queue
        core.wait(0.05)

        pymouse=event.Mouse()

        # Try to start up the ioHub and connect to an ioSync device.
        # If something goes wrong (like an ioSync is not present), give an error
        try:
            io = startIOHub()
            mcu = io.devices.mcu
            kb = io.devices.keyboard
            iomouse = io.devices.mouse
            mcu.setDigitalOutputByte(0)
            # forces pyglet to get events from the windows event queue
            core.wait(0.05)
            mcu.enableEventReporting(True)
            io.clearEvents('all')
        except Exception:
            import traceback
            traceback.print_exc()
            demo_title.setText('Error Starting ioHub.\n1) Is ioSync connected to the PC\n2) Has the correct serial port been provided?\n\nExiting in 5 seconds.')
            demo_title.pos=0,0
            demo_title.draw()
            win.flip()
            core.wait(5.0)
            win.close()
            sys.exit(0)

        # Main demo loop, reads ioSync digital and analog inputs,
        # displays current input values, and provides buttons to control
        # the iosync digital output lines.
        #
        # Exit when ESC is pressed.
        run_demo = True
        while run_demo:
            if 'escape' in [e.key for e in kb.getEvents()]:
                run_demo = False
                break

            mcu_events = mcu.getEvents()
            for mcue in mcu_events:
                if mcue.type == EventConstants.DIGITAL_INPUT:
                    digital_input_state = mcue.state
                elif mcue.type ==  EventConstants.ANALOG_INPUT:
                    last_analog_in_event = mcue

            if last_analog_in_event:
                for c, m in enumerate(ain_gauges):
                    vraw = getattr(last_analog_in_event, m.ain_name)
                    raw_ratio = vraw//MAX_RAW
                    vstr = '%.3fV' % (toVolts(vraw))
                    if LUX_AIN == c:
                        vstr = '%d Lux' % (int(tolux(vraw)))
                    m.update_gauge(raw_ratio, vstr)
                last_analog_in_event = None
            else:
                [m.draw() for m in ain_gauges]

            mouse_clicked = False
            if [me.button_id for me in iomouse.getEvents(
                            event_type_id = EventConstants.MOUSE_BUTTON_RELEASE)
                            if me.button_id == MouseConstants.MOUSE_BUTTON_LEFT]:
                mouse_clicked = True

            for dpin in range(8):
                digital_in_lines[dpin].enable(digital_input_state)

                if mouse_clicked and digital_out_lines[dpin].contains(pymouse):
                    mouse_clicked=False
                    if digital_out_lines[dpin].state:
                        digital_output_state -= 2**dpin
                        mcu.setDigitalOutputPin(dpin, False)
                    else:
                        digital_output_state += 2**dpin
                        mcu.setDigitalOutputPin(dpin, True)
                digital_out_lines[dpin].enable(digital_output_state)

            [ts.draw() for ts in static_text_stim]
            win.flip()
            core.wait(0.033, 0.0)

        # turn off ioSync Recording
        # and do misc. cleanup
        mcu.setDigitalOutputByte(0)
        mcu.enableEventReporting(False)
        win.close()

    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        if mcu:
            mcu.enableEventReporting(False)
        if io:
            io.clearEvents('all')
            io.quit()

# Misc. constraints for ioSync
MAX_RAW = 2.0 ** 16
MAX_LUX = 15.0 # in k lux
MAX_AIN_V = 3.3
LOG_LUX_RANGE = MAX_AIN_V
LOG_LUX_RATIO = LOG_LUX_RANGE/MAX_RAW
DIGITAL_ANALOG_16_STEP = MAX_AIN_V/MAX_RAW

def toVolts(raw):
    """
    Convert raw ioSync analog input value to voltage value.
    """
    return DIGITAL_ANALOG_16_STEP * raw

def tolux(raw):
    """
    Used if LUX_AIN is set to between 0 and 7; indicating that the ioSync
    light meter peripheral is attached to that analog input line.

    Convert raw ioSync analog input value to lux value.
    """
    return pow(10, raw * LOG_LUX_RATIO)

def startIOHub():
    """
    Starts the ioHub process, saving events to events.hdf5, recording data from
    all standard devices as well as the ioSync MCU device.
    """
    global io
    import time
    psychopy_mon_name = 'testMonitor'
    exp_code = 'events'
    sess_code = 'S_{0}'.format(int(time.mktime(time.localtime())))
    iohub_config = {
        "psychopy_monitor_name": psychopy_mon_name,
        "mcu.iosync.MCU": dict(serial_port='auto',
                               monitor_event_types=['AnalogInputEvent',
                                                    'DigitalInputEvent']),
        "experiment_code": exp_code,
        "session_code": sess_code
    }
    return launchHubServer(**iohub_config)

#
## Start main demo logic
#
main()
