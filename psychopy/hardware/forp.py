#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for Current Designs Inc. devices such as button boxes.

This class is only useful when the fORP is connected via the serial port. If
you're connecting via USB, just treat it like a standard keyboard. E.g., use a
Keyboard component, and typically listen for Allowed keys ``'1', '2', '3', '4',
'5'``. Or use ``event.getKeys()``.

These are optional components that can be obtained by installing the
`psychopy-curdes` extension into the current environment.

"""


from psychopy.plugins import PluginStub


class ButtonBox(
    PluginStub,
    plugin="psychopy-curdes",
    docsHome="https://github.com/psychopy/psychopy-curdes"
):
    pass


BUTTON_RED: int
BUTTON_BLUE: int
BUTTON_GREEN: int
BUTTON_YELLOW: int
BUTTON_TRIGGER: int
BUTTON_MAP: dict
