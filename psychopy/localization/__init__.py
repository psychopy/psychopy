#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Language localization for PsychoPy.

Sets the locale value as a wx languageID (int) and initializes gettext
translation _translate():
    from psychopy import localization
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from .translation import setLocale, getLocale, _translate

__all__ = [
    "getLocale",
    "setLocale",
    "_translate"
]