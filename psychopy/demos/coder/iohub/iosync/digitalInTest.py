# -*- coding: utf-8 -*-
"""This demo requires that an ioSync device is correctly connected to the
computer running this script. Some switches or buttons also need to be
connected to at least one of the digital input lines of the ioSync so they can
be used to generate the digital input events.

This is a simple example of how to enable ioSync digital input events.
The demo starts the iosync with digital input events enabled. An ioSync
DigitalInputEvent is created each time one of the eight digital input lines
changes state. The event returns a 'state' byte, giving the value of all input
lines when the event occurred, as well as the time the event was detected by
the ioSync hardware.

ioSync supports 8 digital inputs. Digital inputs are sampled at 1000 Hz.

By default all DINs use pullup resistors, so if a DIN line is high then the
line is open; when the DIN line is connected to ground then the line becomes
low and is closed. This is ideal when using digital inputs to detect button
press and releases. A state byte of 255 therefore indicates that all DIN lines
are open. A state byte of 0 indicates that all DIN lines are closed
(all buttons are pressed).

DIN_0 = LSB of the state Byte (dec 1)
....
DIN_7 = MSB  of the state byte (dec 128)

Pullup Resesistors are enabled in the ioSync Teensy 3 program (iosync.ino)
with the following define setting:

#define DIGITAL_INPUT_TYPE INPUT_PULLUP


If the define is set to INPUT, then a DIN line is high when the line is closed.
In this case, you will need to provide a resistor between the ground pin 
and the digital input ground wire, otherwise when a DIN line is open it is 
floating and will randomly change state causing false events.

IMPORTANT: Input voltage to a digital input pin must be between 0.0 V and 3.3 V
or you may damage the Teensy 3. The Teensy 3.1 supports digital inputs up to
5 V.
"""
import time
import sys
from psychopy import core
from psychopy.iohub.client import launchHubServer
getTime = core.getTime


def getDigitalInPins(din_byte):
    din_byte = 255 - din_byte
    return [(din_byte >> b) & 0x01 for b in xrange(0, 8)]
try:
    mcu = None
    io = None
    iohub_config = {'mcu.iosync.MCU': dict(serial_port='auto',
                                           monitor_event_types=[
                                               'DigitalInputEvent',
                                               ]
                                           )
                    }
    io = launchHubServer(**iohub_config)
    mcu = io.devices.mcu
    kb = io.devices.keyboard
    if mcu.isConnected():
        mcuport = mcu.getSerialPort()
        print("Connected to ioSync on Serial Port {}".format(mcuport))
    else:
        print("Could not connect to ioSync Device...\n"
              "Ensure USB and power cables are plugged in")
        io.quit()
        core.wait(0.25)
        sys.exit()

    core.wait(0.25)
    mcu.enableEventReporting(True)
    io.clearEvents()
    print("Short ioSync Digital Inputs to Generate Events.")
    print("Press any Keyboard key to exit....")

    while not kb.getEvents():
        mcu_events = mcu.getEvents()
        for mcu_evt in mcu_events:
            print'{:.3f}\t{}'.format(mcu_evt.time,
                                     getDigitalInPins(mcu_evt.state))
        core.wait(0.002, 0)
    io.clearEvents()
except Exception:
    import traceback
    traceback.print_exc()
finally:
    if mcu:
        mcu.enableEventReporting(False)
    if io:
        io.quit()
