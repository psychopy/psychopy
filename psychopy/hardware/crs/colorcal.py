#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).


from psychopy.tools.pkgtools import PluginStub


class ColorCAL(PluginStub, plugin="psychopy-crs", doclink="https://psychopy.github.io/psychopy-crs/coder/ColorCAL"):
    pass


# Monkey-patch our metadata into CRS class if missing required attributes
if not hasattr(ColorCAL, "longName"):
    setattr(ColorCAL, "longName", "CRS ColorCAL")

if not hasattr(ColorCAL, "driverFor"):
    setattr(ColorCAL, "driverFor", ["colorcal"])
