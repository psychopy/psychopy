#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for button boxes.

This module serves as the entry point for plugin classes implementing
third-party button box interfaces. All installed interfaces are discoverable
by calling the :func:`getAllButtonBoxes()` function.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'getAllButtonBoxes'
]

import sys
import psychopy.logging as logging

# Interfaces for button boxes will be registered here until we get a proper
# base class to identify them by type within this module's scope.
bboxInterfaces = {}

# Import from legacy namespaces to maintain compatibility. These are loaded if
# optional components are installed.

# Cedrus
try:
    from ..cedrus import RB730
except Exception:
    RB730 = None

# ioLabs
try:
    from ..iolab import ButtonBox as ioLabsButtonBox
except Exception:  # NameError from dud pkg
    ioLabsButtonBox = None

# Current Designs
try:
    from ..forp import ButtonBox as curdesButtonBox
except Exception:
    curdesButtonBox = None


def getAllButtonBoxes():
    """Get all button box interface classes.

    Returns
    -------
    dict
        Mapping of button box classes.

    """
    # build a dictionary with names
    foundBBoxes = {}

    # classes from extant namespaces
    optionalBBoxes = ('RB730', 'ioLabsButtonBox', 'curdesButtonBox')

    for bboxName in optionalBBoxes:
        bboxClass = getattr(sys.modules[__name__], bboxName)
        if bboxClass is None:  # not loaded if `None`
            continue

        logging.debug('Found button box class `{}`'.format(bboxName))
        foundBBoxes[bboxName] = bboxClass

    # Merge with classes from plugins. Duplicate names will be overwritten by
    # the plugins.
    foundBBoxes.update(bboxInterfaces)

    return foundBBoxes.copy()


if __name__ == "__main__":
    pass
