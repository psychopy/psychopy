#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Class for loading / saving prefs
"""

from pathlib import Path

from . import preferences as prefsLib
from .generateSpec import generateSpec

Preferences = prefsLib.Preferences
prefs = prefsLib.prefs

# Take note of the folder this module is in
__folder__ = Path(__file__).parent
