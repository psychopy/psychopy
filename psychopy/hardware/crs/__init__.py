#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# Acknowledgements:
#    This code was mostly written by Jon Peirce.
#    CRS Ltd provided support as needed.
#    Shader code for mono++ and color++ modes was based on code in
#    Psychtoolbox (Kleiner) but does not actually use that code directly

"""Cambridge Research Systems makes devices to support particularly
vision research.
"""

from __future__ import absolute_import, print_function

from psychopy import logging
from .bits import BitsSharp, BitsPlusPlus, DisplayPlusPlus, DisplayPlusPlusTouch
from .colorcal import ColorCAL
# Monkey-patch our metadata into CRS class.
setattr(ColorCAL, "longName", "CRS ColorCAL")
setattr(ColorCAL, "driverFor", ["colorcal"])
