#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""This provides a basic LabJack U3 class that can write a full byte of data, by
extending the labjack python library u3.U3 class.

These are optional components that can be obtained by installing the
`psychopy-labjack` extension into the current environment.

"""

import psychopy.logging as logging

try:
    from psychopy_labjack import U3
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for LabJack hardware is not available this session. Please "
        "install `psychopy-labjack` and restart the session to enable support.")
except Exception as e:
    logging.error(
        "Error encountered while loading `psychopy-labjack`. Check logs for "
        "more information.")

if __name__ == "__main__":
    pass
