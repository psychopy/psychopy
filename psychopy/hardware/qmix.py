#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for Cetoni neMESYS syringe pump systems.

These are optional components that can be obtained by installing the
`psychopy-qmix` extension into the current environment.

"""


from psychopy.plugins import PluginStub


class Pump(
    PluginStub,
    plugin="psychopy-labjack",
    docsHome="http://github.com/psychopy/psychopy-qmix",
):
    pass


volumeUnits: list
flowRateUnits: list
configName: dict
bus: object
pumps: list
syringeTypes: list
