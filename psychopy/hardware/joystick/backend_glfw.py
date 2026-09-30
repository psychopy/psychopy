#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""GLFW backend for joystick support.

GLFW can be used for joystick support even when the window was created with
another library, and unlike the pyglet backend it does not require a window at
all.

"""

__all__ = ['JoystickDeviceGLFW', 'JoystickInterfaceGLFW']

import threading

from psychopy import logging
from psychopy.hardware.joystick._base import JoystickDevice


def _decodeName(name):
    """GLFW returns joystick names as `bytes` in some builds and `str` in
    others.
    """
    if isinstance(name, bytes):
        return name.decode("utf-8")
    return name


class JoystickDeviceGLFW(JoystickDevice):
    """Joystick or gamepad accessed through the GLFW library.

    Does not require an open window, and may be used alongside a window created
    by another library.

    Note that GLFW makes no distinction between hats and buttons, so this
    backend reports no hats; a hat appears as a group of buttons.

    Parameters
    ----------
    device : int, str or None
        GLFW joystick id, or the name of the joystick to open.

    """
    _inputLib = 'glfw'

    @staticmethod
    def getAvailableDevices():
        """Return a list of available joystick devices.

        Returns
        -------
        list of dict
            Device profiles, whose keys other than `deviceName` and
            `deviceClass` are valid `__init__` keyword arguments.

        """
        try:
            import glfw
        except ImportError:
            return []

        if not glfw.init():
            logging.error("GLFW could not be initialized.")
            return []

        profiles = []
        # NB: `JOYSTICK_LAST` is itself a valid id, so the range is inclusive
        for joy in range(glfw.JOYSTICK_1, glfw.JOYSTICK_LAST + 1):
            if not glfw.joystick_present(joy):
                continue

            profiles.append({
                'deviceName': "{} (glfw)".format(
                    _decodeName(glfw.get_joystick_name(joy))),
                'deviceClass':
                    "psychopy.hardware.joystick.backend_glfw."
                    "JoystickDeviceGLFW",
                'device': joy,
                'backend': 'glfw',
            })

        return profiles

    # --------------------------------------------------------------------------
    # Lifecycle
    #

    def _openDevice(self):
        """Initialise GLFW and keep a reference to it."""
        import glfw
        self._glfwLib = glfw

        if not glfw.init():
            logging.error("GLFW could not be initialized.")

        # GLFW joysticks are addressed by id and need no explicit open
        self._device = self._deviceIndex

    def _closeDevice(self):
        """GLFW joysticks need no explicit close."""
        pass

    def update(self):
        """Pump GLFW's event queue.

        `glfw.poll_events` must be called from the main thread, but listener
        loops dispatch from a background thread, so off the main thread we rely
        on the main thread (usually `win.flip()`) to pump events for us.

        """
        if threading.current_thread() is threading.main_thread():
            self._glfwLib.poll_events()

    def addListener(self, listener, startLoop=False):
        """Add a listener, warning about background dispatch on GLFW."""
        if startLoop:
            logging.warning(
                "The 'glfw' joystick backend cannot pump events from a "
                "background thread, so a listener loop will only see new "
                "input while the main thread is also flipping a window or "
                "polling the joystick.")
        return JoystickDevice.addListener(self, listener, startLoop=startLoop)

    # --------------------------------------------------------------------------
    # Raw state
    #

    def getName(self):
        """The manufacturer-defined name describing the device (`str`)."""
        return _decodeName(self._glfwLib.get_joystick_name(self._device))

    def _getRawAxes(self):
        """Raw axis values."""
        axes, count = self._glfwLib.get_joystick_axes(self._device)
        return [axes[i] for i in range(count)]

    def _getRawButtons(self):
        """Raw button states."""
        buttons, count = self._glfwLib.get_joystick_buttons(self._device)
        return [buttons[i] for i in range(count)]

    def _getRawHats(self):
        """GLFW reports hats as buttons, so there are never any hats."""
        return []


# legacy alias, this class was named for an interface before the DeviceManager
# migration made it a device in its own right
JoystickInterfaceGLFW = JoystickDeviceGLFW


if __name__ == "__main__":
    pass
