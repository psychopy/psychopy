#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""GLFW backend for joystick support.

"""

__all__ = ['JoystickInterfaceGLFW']

from psychopy import logging
from psychopy.hardware.joystick._base import BaseJoystickInterface


class JoystickInterfaceGLFW(BaseJoystickInterface):
    """Class for defining an interface for joystick and gamepad devices using
    the GLFW library.

    Once can use GLFW for joystick support in PsychoPy even if the window is
    created with another library (e.g., Pyglet).

    Parameters
    ----------
    device : str or int
        The name or index of the joystick to control.

    """
    _inputLib = 'glfw'
    def __init__(self, device, **kwargs):
        super(JoystickInterfaceGLFW, self).__init__(device, **kwargs)

        # We can create a joystick anytime after glfwInit() is called, but
        # there should be a window open first.
        # Joystick events are processed when flipping the associated window.
        import glfw
        self._glfwLib = glfw  # keep a reference to the GLFW library

        if not glfw.init():
            logging.error("GLFW could not be initialized. Exiting.")

        # get all available joysticks, GLFW supports up to 16.
        joys = []
        for joy in range(glfw.JOYSTICK_1, glfw.JOYSTICK_LAST):
            if glfw.joystick_present(joy):
                joys.append(joy)

        if isinstance(device, str):   # get index by string name
            if device in ('None', 'default'):
                self._device = 0  # use first device
            else:
                # find the device by name
                for joy in joys:
                    if glfw.get_joystick_name(joy) == device:
                        self._device = joy
                        break
                else:
                    logging.error(
                        "No joystick found with the name '%s'" % device)
        elif isinstance(device, int):  # get by index
            if device >= len(joys):
                logging.error(
                    "You don't have that many joysticks attached (remember "
                    "that the first joystick has device=0 etc...)")
                raise ValueError("Invalid joystick index")

            self._device = joys[device]

        # if len(visual.openWindows) == 0:
        #     logging.error(
        #         "You need to open a window before creating your joystick")
        # else:
        #     for win in visual.openWindows:
        #         # sending the raw ID to the window.
        #         win()._eventDispatchers.append(self._device)

        self._isOpen = True   # GLFW joysticks don't need to be opened

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
        import glfw

        deviceList = []
        for joy in range(glfw.JOYSTICK_1, glfw.JOYSTICK_LAST):
            if not glfw.joystick_present(joy):
                continue

            config = {}
            config['index'] = joy
            config['name'] = glfw.get_joystick_name(joy).decode("utf-8")

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
        # self._device.open()
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
        # self._device.close()
        self._isOpen = False

    def __del__(self):
        """Close the joystick device when the object is deleted.

        """
        if hasattr(self, '_isOpen'):
            self.close()

    def getName(self):
        """Get the manufacturer-defined name describing the device.

        Returns
        -------
        str
            The name of the joystick.

        """
        return self._glfwLib.get_joystick_name(self._device).decode("utf-8")

    def getNumButtons(self):
        """Number of digital buttons on the device.

        Returns
        -------
        int
            The number of buttons on the joystick.

        """
        _, count = self._glfwLib.get_joystick_buttons(self._device)
        return count

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
        bs, _ = self._glfwLib.get_joystick_buttons(self._device)
        return bs[buttonId]

    def getAllButtons(self):
        """Get the state of all buttons.

        Returns
        -------
        list
            A list of button states.

        """
        bs, count = self._glfwLib.get_joystick_buttons(self._device)
        return [bs[i] for i in range(count)]

    def getAllHats(self):
        """Get the current values of all available hats as a list of tuples.

        Returns
        -------
        list
            A list of tuples representing the state of each hat. Each value is
            a tuple (x, y) where x and y can be -1, 0, +1.

        """
        return []

    def getNumHats(self):
        """Get the number of hats on this joystick.

        Returns
        -------
        int
            The number of hats on the joystick.

        """
        return 0

    def getHat(self, hatId=0):
        """Get the position of a particular hat.

        Returns
        -------
        tuple
            The position of the hat as an (x, y) tuple where x and y can be -1,
            0, or +1.

        """
        return []
    
    def getX(self):
        """Return the X axis value (equivalent to joystick.getAxis(0))."""
        return self.getAxis(0)

    def getY(self):
        """Return the Y axis value (equivalent to joystick.getAxis(1))."""
        return self.getAxis(1)

    def getZ(self):
        """Return the Z axis value (equivalent to joystick.getAxis(2))."""
        return self.getAxis(2)
    
    def getRX(self):
        """Return the RX axis value (equivalent to joystick.getAxis(3))."""
        return self.getAxis(3)

    def getRY(self):
        """Return the RY axis value (equivalent to joystick.getAxis(4))."""
        return self.getAxis(4)

    def getRZ(self):
        """Return the RZ axis value (equivalent to joystick.getAxis(5))."""
        return self.getAxis(5)

    def getXY(self):
        """Return the XY axis value (equivalent to joystick.getAxis(6))."""
        return [self.getAxis(0), self.getAxis(1)]

    def getAllAxes(self):
        """Get a list of all current axis values.
        """
        axes, count = self._glfwLib.get_joystick_axes(self._device)
        return [axes[i] for i in range(count)]
    
    def getNumAxes(self):
        """Number of joystick axes found.

        Returns
        -------
        int
            The number of axes found on the joystick.

        """
        _, count = self._glfwLib.get_joystick_axes(self._device)
        return count

    def getAxis(self, axisId):
        """Get the value of an axis by an integer id.

        (from 0 to number of axes - 1)
        """
        val, _ = self._glfwLib.get_joystick_axes(self._device)
        return val[axisId]

    def update(self):
        """Update the joystick state.

        """
        self._glfwLib.poll_events()


if __name__ == "__main__":
    pass
