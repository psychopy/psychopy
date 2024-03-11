#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for Current Designs Inc. devices such as button boxes.

This class is only useful when the fORP is connected via the serial port. If
you're connecting via USB, just treat it like a standard keyboard. E.g., use a
Keyboard component, and typically listen for Allowed keys ``'1', '2', '3', '4',
'5'``. Or use ``event.getKeys()``.

These are optional components that can be obtained by installing the
`psychopy-curdes` extension into the current environment.

"""

import psychopy.logging as logging

try:
    from psychopy_curdes import (
        ButtonBox,
        BUTTON_RED,
        BUTTON_BLUE,
        BUTTON_GREEN,
        BUTTON_YELLOW,
        BUTTON_TRIGGER,
        BUTTON_MAP)
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for Current Designs Inc. hardware is not available this "
        "session. Please install `psychopy-curdes` and restart the session "
        "to enable support.")
except Exception as e:
    logging.error(
        "Error encountered while loading `psychopy-curdes`. Check logs for "
        "more information.")

if __name__ == "__main__":
    pass
