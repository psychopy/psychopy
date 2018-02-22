#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of using XInput gamepad support from ioHub in PsychoPy.

Important: An XInput compatible gamepad must be connected to the Windows PC
    when this demo is run. As far as I know, macOS and Linux do not support
    XInput. Compatible gamepads include the XBox 360 gamepad for PCs, and the
    Logitech F310 and F710. The XBOX360 and F710 gamepads are wireless and
    also support the * rumble * fucntionality of the XInput API. For wireless
    gamepads, ensure the gamepad is turned on before you try to start the demo.
"""

from __future__ import absolute_import, division, print_function

from builtins import str
from psychopy import visual, core
from psychopy.iohub import launchHubServer, EventConstants


def normalizedValue2Coord(normed_position, normed_magnitude, display_coord_area):
    x = normed_position[0] * normed_magnitude
    y = normed_position[1] * normed_magnitude
    w, h = display_coord_area
    return x * (w / 2.0), y * (h / 2.0)


if __name__ == '__main__':
    # Start the ioHub Event Server, requesting an XInput Gamepad Device to be
    #   created along with the default devices. Since the configuration dict
    #   for the Gamepad is empty, all default values will be used.
    #
    kwargs = {'psychopy_monitor_name':'default', 'xinput.Gamepad':{}}
    io = launchHubServer( ** kwargs)

    display = io.devices.display
    mouse = io.devices.mouse
    display = io.devices.display
    keyboard = io.devices.keyboard
    gamepad = io.devices.gamepad

    display_resolution=display.getPixelResolution()
    psychopy_monitor=display.getPsychopyMonitorName()
    unit_type=display.getCoordinateType()
    screen_index=display.getIndex()
    dl, dt, dr, db=display.getCoordBounds()
    coord_size=dr-dl, dt-db

    win = visual.Window(display_resolution, monitor=psychopy_monitor,
        units=unit_type, color=[128, 128, 128], colorSpace='rgb255',
        fullscr=True, allowGUI=False, screen=screen_index)

    # Hide the 'system mouse cursor'
    mouse.setSystemCursorVisibility(False)

    gamepad.updateBatteryInformation()
    bat = gamepad.getLastReadBatteryInfo()
    print("Battery Info: ")
    print(bat)
    print()

    gamepad.updateCapabilitiesInformation()
    caps = gamepad.getLastReadCapabilitiesInfo()
    print("Capabilities: " + str(caps))

    unit_type = display.getCoordinateType()

    fixSpot = visual.GratingStim(win, tex="none", mask="gauss", pos=(0, 0),
        size=(30, 30), color='black', units=unit_type)

    grating = visual.GratingStim(win, pos=(0, 0), tex="sin", mask="gauss",
        color='white', size=(200, 200), sf=(0.01, 0), units=unit_type)

    msgText = ('Left Stick: Spot Pos; Right Stick: Grating Pos; '
        'Left Trig: SF; Right Trig: Ori; "A" Button: Rumble; "q" key: Quit')
    message = visual.TextStim(win, pos=(0, -200),
        text=msgText, units=unit_type,
        alignHoriz='center', alignVert='center', height=24,
        wrapWidth=display_resolution[0] * .9)
    key_presses = []
    while not u'q' in key_presses:
        # Update stim from gamepad.
        # Sticks are 3 item lists (x, y, magnitude).
        #
        x, y, mag = gamepad.getThumbSticks()['right_stick']
        xx, yy = normalizedValue2Coord((x, y), mag, coord_size)
        grating.setPos((xx, yy))

        x, y, mag=gamepad.getThumbSticks()['left_stick']
        xx, yy=normalizedValue2Coord((x, y), mag, coord_size)
        fixSpot.setPos((xx, yy))

        # Change sf.
        sf = gamepad.getTriggers()['left_trigger']
        grating.setSF((sf / display.getPixelsPerDegree()[0]) * 2 + 0.01)

        # Change ori.
        ori = gamepad.getTriggers()['right_trigger']
        grating.setOri(ori * 360.0)

        # If any button is pressed then make the grating stimulus colored.
        pressed_buttons = gamepad.getPressedButtonList()

        if pressed_buttons:
            grating.setColor('red')
        else:
            grating.setColor('white')

        if 'A' in pressed_buttons:
            # Rumble the pad, 50% low frequency motor, 25% high frequency
            # motor, for 1 second. Method is asynchronous, in that it returns
            # as soon as the ioHub Server has responded that the rumble request
            # was received and started.
            rt, rd = gamepad.setRumble(50.0, 25.0, 1.0)
            rumble_command_time, rumble_command_duration = rt, rd

        # Drift the grating
        t = core.getTime()
        grating.setPhase(t * 2)

        grating.draw()
        fixSpot.draw()
        message.draw()
        flip_time = win.flip()

        _kbe = keyboard.getEvents(EventConstants.KEYBOARD_PRESS)
        key_presses = [event.key for event in _kbe]

        # Do this each frame to avoid keyboard event buffer
        #   filling with non-press event types.
        io.clearEvents('all')

io.quit()
win.close()
core.quit()

# End of run.py Script #

# The contents of this file are in the public domain.
