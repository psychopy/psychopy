#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for EMOTIV devices such as button boxes.

These are optional components that can be obtained by installing the
`psychopy-emotiv` extension into the current environment.

"""

import psychopy.logging as logging

try:
    from psychopy_emotiv import (
        Cortex,
        CortexApiException,
        CortexNoHeadsetException,
        CortexTimingException)
except (ModuleNotFoundError, ImportError, NameError):
    logging.error(
        "Support for Emotiv hardware is not available this session. Please "
        "install `psychopy-emotiv` and restart the session to enable support.")
except Exception as e:
    logging.error(
        "Error encountered while loading `psychopy-emotiv`. Check logs for "
        "more information.")

if __name__ == "__main__":
    pass