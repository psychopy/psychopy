#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Deprecated location for the emulated joystick buttons.

The virtual joystick is now a proper joystick backend and lives at
`psychopy.hardware.joystick.backend_virtual`, where one implementation covers
both this and `virtualJoystick`. See that module for details.

"""

__all__ = ['VirtualJoyButtons']

from psychopy.hardware.joystick.backend_virtual import (
    JoystickDeviceVirtual as VirtualJoyButtons)
