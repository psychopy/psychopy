#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

# Support for fake joystick/gamepad during development
# if no 'real' joystick/gamepad is available use keyboard emulation
# 'ctrl' + 'alt' + numberKey

from psychopy import event


class VirtualJoystick:
    def __init__(self, device_number):
        self.device_number = device_number
        self.numberKeys = ['0','1','2','3','4','5','6','7','8','9']
        self.modifierKeys = ['ctrl','alt']
        self.mouse = event.Mouse()
        event.Mouse(visible=False)

    def getNumButtons(self):
        return len(self.numberKeys)

    def getAllButtons(self):
        keys = event.getKeys(keyList=self.numberKeys, modifiers=True)
        values = [key for key, modifiers in keys if all([modifiers[modKey] for modKey in self.modifierKeys])]
        self.state = [key in values for key in self.numberKeys]
        mouseButtons = self.mouse.getPressed()
        self.state[:len(mouseButtons)] = [a or b != 0 for (a,b) in zip(self.state, mouseButtons)]
        return self.state

    def getX(self):
        (x, y) = self.mouse.getPos()
        return x

    def getY(self):
        (x, y) = self.mouse.getPos()
        return y
