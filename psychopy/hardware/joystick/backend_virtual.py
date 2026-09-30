#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Virtual joystick backend, emulating a gamepad with the keyboard and mouse.

Useful for developing an experiment on a machine with no joystick attached. The
mouse position drives the X and Y axes, and `ctrl` + `alt` + a number key (or a
mouse button) presses a joystick button.

"""

__all__ = ['JoystickDeviceVirtual', 'VirtualJoystick', 'VirtualJoyButtons']

from psychopy.hardware.joystick._base import JoystickDevice


class JoystickDeviceVirtual(JoystickDevice):
    """A joystick emulated with the keyboard and mouse.

    Buttons are pressed with `ctrl` + `alt` + a number key, or with the mouse
    buttons. The X and Y axes follow the mouse position.

    Parameters
    ----------
    device : int, str or None
        Ignored; there is only ever one virtual joystick.

    """
    _inputLib = 'virtual'

    #: keys which act as buttons when combined with the modifiers
    numberKeys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    #: modifiers which must be held for a number key to count as a button
    modifierKeys = ['ctrl', 'alt']

    @staticmethod
    def getAvailableDevices():
        """The virtual joystick is always available."""
        return [{
            'deviceName': "Virtual joystick (keyboard + mouse)",
            'deviceClass':
                "psychopy.hardware.joystick.backend_virtual."
                "JoystickDeviceVirtual",
            'device': 0,
            'backend': 'virtual',
        }]

    # --------------------------------------------------------------------------
    # Lifecycle
    #

    def _openDevice(self):
        """Grab a mouse to read positions and buttons from."""
        from psychopy import event
        self._event = event
        self._mouse = event.Mouse()
        # hide the cursor through the mouse we already have; building a second
        # one just to set its visibility leaves a throwaway object behind, and
        # logs a second time when there's no window to attach to yet
        self._mouse.setVisible(False)
        self._state = [False] * len(self.numberKeys)
        self._device = self._deviceIndex

    def _closeDevice(self):
        """Nothing to release."""
        pass

    def getName(self):
        """The name of the device (`str`)."""
        return "Virtual joystick (keyboard + mouse)"

    # --------------------------------------------------------------------------
    # Raw state
    #

    def _getRawButtons(self):
        """Button states, from the modified number keys and mouse buttons."""
        keys = self._event.getKeys(keyList=self.numberKeys, modifiers=True)
        pressed = [
            key for key, modifiers in keys
            if all(modifiers[modKey] for modKey in self.modifierKeys)]

        state = [key in pressed for key in self.numberKeys]

        # mouse buttons press the first few joystick buttons too. The mouse
        # needs a window to read from, so fall back to the keys alone when
        # there isn't one yet.
        try:
            mouseButtons = self._mouse.getPressed() or []
        except Exception:
            mouseButtons = []
        state[:len(mouseButtons)] = [
            a or b != 0 for a, b in zip(state, mouseButtons)]

        self._state = state
        return state

    def _getRawAxes(self):
        """X and Y follow the mouse; the remaining axes read zero.

        The mouse position is relative to a window, so the axes read zero until
        one is open.
        """
        try:
            pos = self._mouse.getPos()
            x, y = (0.0, 0.0) if pos is None else pos
        except Exception:
            x = y = 0.0
        return [x, y, 0.0, 0.0, 0.0, 0.0]

    def _getRawHats(self):
        """The virtual joystick has no hats."""
        return []


# Legacy names. These classes used to live under `psychopy.experiment` and be
# imported by generated experiment scripts, which is a layering violation -- a
# runtime script should not depend on the Builder package. They are kept as
# aliases so hand-edited scripts keep working.
VirtualJoystick = JoystickDeviceVirtual
VirtualJoyButtons = JoystickDeviceVirtual


if __name__ == "__main__":
    pass
