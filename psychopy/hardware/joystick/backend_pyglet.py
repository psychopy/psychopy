#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Pyglet backend for joystick support.

Note that this backend requires an open pyglet `Window` which is being flipped,
since joystick state is updated by pyglet's event dispatch loop. Use the GLFW
backend if you need joystick input without a window, or with a window created by
another library.

"""

__all__ = ['JoystickDevicePyglet', 'JoystickInterfacePyglet',
           'getPygletJoysticks']

try:
    from pyglet import input as pyglet_input  # pyglet 1.2+
    from pyglet import app as pyglet_app
    havePyglet = True
except Exception:
    havePyglet = False

from psychopy import logging
from psychopy.hardware.joystick._base import JoystickDevice


# pyglet `Joystick` objects handed out so far, see `getPygletJoysticks`
_pygletJoysticks = []


def getPygletJoysticks():
    """All joysticks pyglet can see, reusing the objects handed out before.

    `pyglet.input.get_joysticks()` builds a brand new `Joystick` on every call,
    over device objects it caches. Building one rebinds the `on_change` handler
    of every control on that device to the new `Joystick`, which orphans any
    `Joystick` handed out earlier -- it keeps its last values and never updates
    again. Anything which enumerated the hardware while a device was open would
    therefore freeze that device, and since `getDeviceProfile` enumerates the
    first time a response is timestamped, one button press was enough to do it.

    Re-enumerating is only safe while nothing is open, so that is the only time
    we do it. Joysticks plugged in after one has been opened aren't picked up
    until the open ones are closed.

    Returns
    -------
    list
        pyglet `Joystick` objects, in the order pyglet reports them.

    """
    global _pygletJoysticks
    if not havePyglet:
        return []

    if not any(joy.device.is_open for joy in _pygletJoysticks):
        _pygletJoysticks = pyglet_input.get_joysticks()

    return _pygletJoysticks


if havePyglet:
    class PygletDispatcher:
        """Steps pyglet's platform event loop.

        Retained for backwards compatibility; `JoystickDevicePyglet` now
        registers itself with open windows and steps the loop from `update()`.

        """
        def dispatch_events(self):
            pyglet_app.platform_event_loop.step(timeout=0.001)

    pyglet_dispatcher = PygletDispatcher()


class JoystickDevicePyglet(JoystickDevice):
    """Joystick or gamepad accessed through the pyglet library.

    Requires an open pyglet `Window` which is being flipped.

    Parameters
    ----------
    device : int, str or None
        Index or name of the joystick to open.

    """
    _inputLib = 'pyglet'

    @staticmethod
    def getAvailableDevices():
        """Return a list of available joystick devices.

        Returns
        -------
        list of dict
            Device profiles, whose keys other than `deviceName` and
            `deviceClass` are valid `__init__` keyword arguments.

        """
        if not havePyglet:
            return []

        profiles = []
        for i, joy in enumerate(getPygletJoysticks()):
            profiles.append({
                'deviceName': "{} (pyglet)".format(joy.device.name),
                'deviceClass':
                    "psychopy.hardware.joystick.backend_pyglet."
                    "JoystickDevicePyglet",
                'device': i,
                'backend': 'pyglet',
            })

        return profiles

    # --------------------------------------------------------------------------
    # Lifecycle
    #

    def _openDevice(self):
        """Acquire the pyglet joystick object and open it."""
        joys = getPygletJoysticks()
        # the index was validated by `_resolveDeviceIndex`
        self._device = joys[self._deviceIndex]

        try:
            self._device.open()
        except pyglet_input.DeviceOpenException:
            # the device may already be open, which is not an error
            pass

        # imported here rather than at module scope -- `psychopy.visual` imports
        # `psychopy.hardware`, so a top-level import risks a cycle and drags the
        # whole visual stack into any joystick import
        from psychopy import visual
        if len(visual.openWindows) == 0:
            logging.warning(
                "The 'pyglet' joystick backend needs an open pyglet window "
                "which is being flipped in order to update. Open a window "
                "before polling this joystick, or use the 'glfw' backend.")

    def _closeDevice(self):
        """Release the pyglet joystick object."""
        if self._device is not None and hasattr(self._device, 'close'):
            try:
                self._device.close()
            except Exception:
                pass

    def update(self):
        """Step pyglet's platform event loop so joystick state refreshes."""
        if havePyglet:
            pyglet_app.platform_event_loop.step(timeout=0.001)

    # --------------------------------------------------------------------------
    # Raw state
    #

    def getName(self):
        """The manufacturer-defined name describing the device (`str`)."""
        return self._device.device.name

    def _getRawAxes(self):
        """Raw axis values, in the conventional x/y/z/rx/ry/rz order."""
        names = ['x', 'y', 'z', 'rx', 'ry', 'rz']
        axes = []
        for axName in names:
            if hasattr(self._device, axName):
                val = getattr(self._device, axName)
                axes.append(0.0 if val is None else val)
        return axes

    def _getRawButtons(self):
        """Raw button states."""
        return list(self._device.buttons)

    def _getRawHats(self):
        """Raw hat positions.

        pyglet exposes a hat as a pair of controls named `hat_x` and `hat_y`.
        Counting those controls individually reports twice as many hats as the
        device actually has, so a device with any hat control has exactly one
        hat.

        """
        for ctrl in self._device.device.get_controls():
            if ctrl.name is not None and 'hat' in ctrl.name:
                return [(self._device.hat_x, self._device.hat_y)]
        return []

    # --------------------------------------------------------------------------
    # Events
    #

    def setEventCallback(self, evt, callback):
        """Set a callback to be invoked when a joystick event occurs.

        Parameters
        ----------
        evt : str
            Name of the pyglet event to listen for, e.g.
            `'on_joybutton_press'`, `'on_joybutton_release'`,
            `'on_joyaxis_motion'`.
        callback : callable
            Function called when the event occurs.

        """
        self._device.push_handlers(**{evt: callback})


# legacy alias, this class was named for an interface before the DeviceManager
# migration made it a device in its own right
JoystickInterfacePyglet = JoystickDevicePyglet


if __name__ == "__main__":
    pass
