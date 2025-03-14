#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""This provides basic LabHackers (www.labhackers.com) device classes.

These are optional components that can be obtained by installing the
`psychopy-labhackers` extension into the current environment.

"""

import psychopy.logging as logging

try:
    from psychopy_labhackers import (
        getDevices, getSerialPorts, getUSB2TTL8s, USB2TTL8)
except (ModuleNotFoundError, ImportError, NameError):
    logging.error(
        "Support for LabHackers hardware is not available this session. "
        "Please install `psychopy-labhackers` and restart the session to "
        "enable support.")

if __name__ == "__main__":
    pass
