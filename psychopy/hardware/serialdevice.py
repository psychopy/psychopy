#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Generic interface for serial ports (i.e. RS-232).

These are optional components that can be obtained by installing the
`psychopy-connect` extension into the current environment.

"""

import psychopy.logging as logging

try:
    from psychopy_connect import SerialDevice
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support serial ports is not available this session. Please install "
        "`psychopy-connect` and restart the session to enable support.")

if __name__ == "__main__":
    pass