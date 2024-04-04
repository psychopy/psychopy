#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

# Acknowledgements:
#    This code was initially written by Jon Peirce.
#    with substantial additions by Andrew Schofield
#    CRS Ltd provided support as needed.
#    Shader code for mono++ and color++ modes was based on code in Psychtoolbox
#    (Kleiner) but does not actually use that code directly

import psychopy.logging as logging

try:
    from psychopy_crs.bits import (
        BitsSharp,
        BitsPlusPlus,
        DisplayPlusPlus,
        DisplayPlusPlusTouch)
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for Cambridge Research Systems Bits#, Bits++, Display++ and "
        "Display++ Touch hardware is not available this session. Please "
        "install `psychopy-crs` and restart the session to enable support.")
except Exception as e:
    logging.error(
        "Error encountered while loading `psychopy-crs`. Check logs for more "
        "information.")

if __name__ == "__main__":
    pass
