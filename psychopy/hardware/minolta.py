#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for Minolta light-measuring devices.

These are optional components that can be obtained by installing the
`psychopy-minolta` extension into the current environment.

"""

import psychopy.logging as logging

try:
    from psychopy_minolta import CS100A, LS100
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for Konica Minolta hardware is not available this session. "
        "Please install `psychopy-minolta` and restart the session to enable "
        "support.")
except Exception as e:
    logging.error(
        "Error encountered while loading `psychopy-minolta`. Check logs for "
        "more information.")

if __name__ == "__main__":
    pass
