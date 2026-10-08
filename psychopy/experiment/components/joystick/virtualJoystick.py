#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Deprecated location for the emulated joystick.

The virtual joystick is now a proper joystick backend and lives at
`psychopy.hardware.joystick.backend_virtual`. It used to live here, under the
Builder package, and be imported by generated experiment scripts -- which meant
a runtime script depended on the Builder package.

This shim is kept so hand-edited scripts written against the old location keep
working. Builder regenerates scripts on every run, so new scripts never use it.

"""

__all__ = ['VirtualJoystick']

from psychopy.hardware.joystick.backend_virtual import (
    JoystickDeviceVirtual as VirtualJoystick)
