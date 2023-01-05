#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for Photo Research Inc. spectroradiometers.

These are optional components that can be obtained by installing the
`psychopy-photoresearch` extension into the current environment.

"""

import psychopy.logging as logging

try:
    from psychopy_photoresearch import PR650, PR655
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for Photo Research Inc. hardware is not available this "
        "session. Please install `psychopy-photoresearch` and restart the "
        "session to enable support.")
except Exception as e:
    logging.error(
        "Error encountered while loading `psychopy-photoresearch`. Check logs "
        "for more information.")

if __name__ == "__main__":
    pass
