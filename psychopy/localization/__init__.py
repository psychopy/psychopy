#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Language localization for PsychoPy.

Sets the locale value as a wx languageID (int) and initializes gettext
translation _translate():
    from psychopy.app import localization
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

try:
    from ._localization import (
        _translate, setLocaleWX, locname, available)
except ModuleNotFoundError:
    # if wx doesn't exist we can't translate but most other parts
    # of the _localization lib will not be relevant
    def _translate(val):
        return val