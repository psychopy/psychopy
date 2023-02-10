#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Software fMRI machine emulator.

Idea: Run or debug an experiment script using exactly the same code, i.e., for
both testing and online data acquisition. To debug timing, you can emulate sync
pulses and user responses.

Limitations: pyglet only; keyboard events only.

These are optional components that can be obtained by installing the
`psychopy-mri-emulator` extension into the current environment.

"""

import psychopy.logging as logging

try:
    from psychopy_mri_emulator import (
        SyncGenerator, ResponseEmulator, launchScan)
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for software fMRI emulation is not available this session. "
        "Please install `psychopy-mri-emulator` and restart the session to "
        "enable support.")
except Exception as e:
    logging.error(
        "Error encountered while loading `psychopy-mri-emulator`. Check logs "
        "for more information.")

if __name__ == "__main__":
    pass
