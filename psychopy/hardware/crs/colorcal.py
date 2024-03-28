#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import psychopy.logging as logging

try:
    from psychopy_crs.colorcal import ColorCAL
except (ModuleNotFoundError, ImportError, NameError):
    logging.error(
        "Support for Cambridge Research Systems ColorCAL is not available this "
        "session. Please install `psychopy-crs` and restart the session to "
        "enable support.")
except Exception as e:
    logging.error(
        "Error encountered while loading `psychopy-crs`. Check logs for more "
        "information.")
else:
    # Monkey-patch our metadata into CRS class if missing required attributes
    if not hasattr(ColorCAL, "longName"):
        setattr(ColorCAL, "longName", "CRS ColorCAL")

    if not hasattr(ColorCAL, "driverFor"):
        setattr(ColorCAL, "driverFor", ["colorcal"])

if __name__ == "__main__":
    pass
