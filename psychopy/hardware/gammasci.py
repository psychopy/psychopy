#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for Gamma-Scientific light-measuring devices.

Tested with S470, but should work with S480 and S490, too.

These are optional components that can be obtained by installing the
`psychopy-gammasci` extension into the current environment.

"""

import psychopy.logging as logging

try:
    from psychopy_gammasci import S470
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for Gamma-Scientific Inc. hardware is not available this "
        "session. Please install `psychopy-gammasci` and restart the session "
        "to enable support.")
except Exception as e:
    logging.error(
        "Error encountered while loading `psychopy-gammasci`. Check logs for "
        "more information.")

if __name__ == "__main__":
    pass
