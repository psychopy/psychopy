#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Various string functions for working with strings.
#

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import re

__all__ = ["prettyname"]


def prettyname(name):
    """Convert a camelCase, TitleCase or underscore_delineated title to Full Title Case"""
    # Replace _ with space
    name = name.replace("_", " ")
    # Put a space before any capital letter, apart from at the beginning, or already after a space
    name = name[0] + re.sub('(?<![ -.])([A-Z])', r' \1', name[1:])
    # Capitalise first letter of each word
    name = name.title()
    # Treat the word "PsychoPy" as a special case
    name = name.replace("Psycho Py", "PsychoPy")

    return name