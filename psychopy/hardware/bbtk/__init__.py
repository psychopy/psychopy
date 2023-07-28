#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for Black Box Toolkit Ltd. devices.

These are optional components that can be obtained by installing the
`psychopy-bbtk` extension into the current environment.

"""

import psychopy.logging as logging

try:
    from psychopy_bbtk import BlackBoxToolkit
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for Black Box Toolkit hardware is not available this session. "
        "Please install `psychopy-bbtk` and restart the session to enable "
        "support.")
except Exception as e:  # misc errors during module loading
    logging.error(
        "Error encountered while loading `psychopy-bbtk`. Check logs for more "
        "information.")

if __name__ == "__main__":
    pass