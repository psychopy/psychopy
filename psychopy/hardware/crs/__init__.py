#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for Cambridge Research Systems hardware.

These are optional components that can be obtained by installing the
`psychopy-crs` extension into the current environment.

"""

import psychopy.logging as logging

try:
    from .bits import (
        BitsSharp,
        BitsPlusPlus,
        DisplayPlusPlus,
        DisplayPlusPlusTouch)
    from .optical import OptiCAL
    from .colorcal import ColorCAL
except (ModuleNotFoundError, ImportError, NameError):
    logging.error(
        "Support for Cambridge Research Systems hardware is not available this "
        "session. Please install `psychopy-crs` and restart the session to "
        "enable support.")
else:
    # Monkey-patch our metadata into CRS class if missing required attributes
    if not hasattr(OptiCAL, "longName"):
        setattr(OptiCAL, "longName", "CRS OptiCal")

    if not hasattr(OptiCAL, "driverFor"):
        setattr(OptiCAL, "driverFor", ["optical"])

    if not hasattr(ColorCAL, "longName"):
        setattr(ColorCAL, "longName", "CRS ColorCAL")

    if not hasattr(ColorCAL, "driverFor"):
        setattr(ColorCAL, "driverFor", ["colorcal"])


if __name__ == "__main__":
    pass
