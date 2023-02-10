#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for `Brain Products GMBH <https://www.brainproducts.com>`_
hardware.

Here we have implemented support for the Remote Control Server application,
which allows you to control recordings, send annotations etc. all from Python.

"""

import psychopy.logging as logging

try:
    from psychopy_brainproducts import RemoteControlServer
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for Brain Products GMBH hardware is not available this "
        "session. Please install `psychopy-brainproducts` and restart the "
        "session to enable support.")
except Exception as e:
    logging.error(
        "Error encountered while loading `psychopy-brainproducts`. Check logs "
        "for more information.")

if __name__ == "__main__":
    pass
