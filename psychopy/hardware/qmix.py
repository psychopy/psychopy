#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for Cetoni neMESYS syringe pump systems.

These are optional components that can be obtained by installing the
`psychopy-qmix` extension into the current environment.

"""

import psychopy.logging as logging

try:
    from psychopy_qmix import (
        Pump,
        _init_all_pumps,
        _init_bus,
        _checkSyringeTypes,
        _PumpWrapperForBuilderComponent,
        volumeUnits,  # don't use module level constants in plugins
        flowRateUnits,
        configName,
        bus,
        pumps,
        syringeTypes)
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for the Cetoni neMESYS syringe pump system is not available "
        "this session. Please install `psychopy-qmix` and restart the session "
        "to enable support.")
except Exception as e:
    logging.error(
        "Error encountered while loading `psychopy-qmix`. Check logs for more "
        "information.")

if __name__ == "__main__":
    pass
