#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

# Acknowledgements:
#    This code was mostly written by Jon Peirce.
#    CRS Ltd provided support as needed.
#    Shader code for mono++ and color++ modes was based on code in
#    Psychtoolbox (Kleiner) but does not actually use that code directly

"""Interfaces for Cambridge Research Systems hardware.

These are optional components that can be obtained by installing the
`psychopy-crs` extension into the current environment.

"""

import psychopy.logging as logging

try:
    from psychopy_crs.bits import (
        BitsSharp,
        BitsPlusPlus,
        DisplayPlusPlus,
        DisplayPlusPlusTouch)
    from psychopy_crs.optical import OptiCAL
    from psychopy_crs.colorcal import ColorCAL
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for Cambridge Research Systems hardware is not available this "
        "session. Please install `psychopy-crs` and restart the session to "
        "enable support.")
else:
    # Monkey-patch our metadata into CRS class if missing required attributes
    setattr(OptiCAL, "longName", "CRS OptiCal")
    setattr(OptiCAL, "driverFor", ["optical"])
    setattr(ColorCAL, "longName", "CRS ColorCAL")
    setattr(ColorCAL, "driverFor", ["colorcal"])

if __name__ == "__main__":
    pass
