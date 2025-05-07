#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Pyglet backend for joystick support.

"""

__all__ = ['JoystickInterfacePyglet']

try:
    from pyglet import input as pyglet_input  # pyglet 1.2+
    from pyglet import app as pyglet_app
    havePyglet = True
except Exception:
    havePyglet = False

from psychopy import logging, visual
from psychopy.hardware.joystick._base import BaseJoystickInterface

if havePyglet:
    class PygletDispatcher:
        def dispatch_events(self):
            pyglet_app.platform_event_loop.step(timeout=0.001)

    pyglet_dispatcher = PygletDispatcher()


class JoystickInterfacePyglet(BaseJoystickInterface):
    """Class for defining an interface for joystick and gamepad devices using
    the Pyglet library.

    Parameters
    ----------
    device : str or int
        The name or index of the joystick to control.

    """
    _inputLib = 'pyglet'
    def __init__(self, device, **kwargs):
        super(JoystickInterfacePyglet, self).__init__(device, **kwargs)

        joys = pyglet_input.get_joysticks()  # enum all joysticks

        if isinstance(device, str):   # get index by string name
            if device in ('None', 'default'):
                self._device = 0  # use first device
            else:
                # find the device by name
                for i, joy in enumerate(joys):
                    if joy.device.name == device:
                        self._device = i
                        break
                else:
                    logging.error(
                        "No joystick found with the name '%s'" % device)
        elif isinstance(device, int):  # get by index
            if device >= len(joys):
                logging.error(
                    "You don't have that many joysticks attached (remember "
                    "that the first joystick has deviceIndex=0 etc...)")

            self._device = joys[device]

        self._isOpen = False

        try:
            self.open()  # open the device
        except pyglet_input.DeviceOpenException as e:
            pass

        if len(visual.openWindows) == 0:
            logging.error(
                "You need to open a window before creating your joystick")
        else:
           for win in visual.openWindows:
               win()._eventDispatchers.append(pyglet_dispatcher)

    @staticmethod
    def getAvailableDevices():
        """Return a list of available joystick devices.

        This method is used by `DeviceManager` to get a list of available
        devices.

        Returns
        -------
        list
            A list of available joystick devices.

        """
        joys = pyglet_input.get_joysticks()

        if not joys:
            return []

        deviceList = []
        for i, joy in enumerate(joys):
            config = {}
            config['index'] = i
            config['name'] = joy.device.name
            deviceList.append(config)

        return deviceList

    @property
    def hasTracking(self):
        """Check if the joystick has tracking capabilities.

        Returns
        -------
        bool
            True if the joystick has tracking capabilities, False otherwise.

        """
        return False
    
    def open(self):
        """Open the joystick device.

        """
        self._device.open()
        self._isOpen = True

    @property
    def isOpen(self):
        """Check if the joystick device is open.

        Returns
        -------
        bool
            True if the joystick device is open, False otherwise.

        """
        # return self._device.device.is_open
        return self._isOpen

    def close(self):
        """Close the joystick device.

        """
        if hasattr(self._device, 'close'):
            self._device.close()

        self._isOpen = False

    def __del__(self):
        """Close the joystick device when the object is deleted.

        """
        if hasattr(self, '_device'):
            self.close()

    def getName(self):
        """Get the manufacturer-defined name describing the device.

        Returns
        -------
        str
            The name of the joystick.

        """
        return self._device.device.name

    def getNumButtons(self):
        """Number of digital buttons on the device.

        Returns
        -------
        int
            The number of buttons on the joystick.

        """
        return len(self._device.buttons)

    def getButton(self, buttonId):
        """Get the state of a given button.

        buttonId should be a value from 0 to the number of buttons-1

        Parameters
        ----------
        buttonId : int
            The button ID to get the state of.

        Returns
        -------
        bool
            True if the button is pressed, False otherwise.

        """
        return self._device.buttons[buttonId]

    def getAllButtons(self):
        """Get the state of all buttons.

        Returns
        -------
        list
            A list of button states.

        """
        return self._device.buttons

    def getAllHats(self):
        """Get the current values of all available hats as a list of tuples.

        Returns
        -------
        list
            A list of tuples representing the state of each hat. Each value is
            a tuple (x, y) where x and y can be -1, 0, +1.

        """
        hats = []
        for ctrl in self._device.device.get_controls():
            if ctrl.name != None and 'hat' in ctrl.name:
                hats.append((self._device.hat_x, self._device.hat_y))
        return hats

    def getNumHats(self):
        """Get the number of hats on this joystick.

        Returns
        -------
        int
            The number of hats on the joystick.

        """
        return len(self.getAllHats())

    def getHat(self, hatId=0):
        """Get the position of a particular hat.

        Returns
        -------
        tuple
            The position of the hat as an (x, y) tuple where x and y can be -1,
            0, or +1.

        """
        if hatId == 0:
            return self._device.hat_x, self._device.hat_y
        else:
            return self.getAllHats()[hatId]
    
    def getX(self):
        """Return the X axis value (equivalent to joystick.getAxis(0))."""
        return self._device.x

    def getY(self):
        """Return the Y axis value (equivalent to joystick.getAxis(1))."""
        return self._device.y

    def getZ(self):
        """Return the Z axis value (equivalent to joystick.getAxis(2))."""
        return self._device.z

    def getAllAxes(self):
        """Get a list of all current axis values."""
        names = ['x', 'y', 'z', 'rx', 'ry', 'rz', ]
        axes = []
        for axName in names:
            if hasattr(self._device, axName):
                axes.append(getattr(self._device, axName))
        return axes
    
    def getNumAxes(self):
        """Number of joystick axes found.

        Returns
        -------
        int
            The number of axes found on the joystick.

        """
        return len(self.getAllAxes())

    def getAxis(self, axisId):
        """Get the value of an axis by an integer id.

        (from 0 to number of axes - 1)
        """
        val = self.getAllAxes()[axisId]
        return 0 if val is None else val

    def poll(self):
        """Check for new joystick events.

        Returns
        -------
        bool
            True if there are new joystick events, False otherwise.

        """
        return self._device.poll()

    def update(self):
        """Update the joystick state.

        """
        pass  # NOP, automatically done by pyglet event dispatching loop


if __name__ == "__main__":
    pass
