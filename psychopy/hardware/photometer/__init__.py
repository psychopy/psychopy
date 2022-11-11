#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for using photometers.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['getAllPhotometers']

# mapping of known photometer classes to names
availablePhotometers = {}


def getAllPhotometers():
    """Gets all available photometers.

    The returned photometers may vary depending on which drivers are
    installed. Standalone PsychoPy ships with libraries for all supported
    photometers.

    Returns
    -------
    dict
        A list of all photometer classes.

    """
    # remove import eventually
    from . import minolta, pr, gammasci
    from .. import crs

    global availablePhotometers

    # classes we ship with, we can remove these as we offload them to plugins
    builtinPhotometers = {
        'PR650': pr.PR650,
        'PR655': pr.PR655,
        'CS100A': minolta.CS100A,
        'LS100': minolta.LS100,
        'S470': gammasci.S470
    }

    if hasattr(crs, "ColorCAL"):
        builtinPhotometers['ColorCAL'] = crs.ColorCAL

    # Merge with classes from plugins. Duplicate names will be overwritten by
    # the plugins.
    availablePhotometers.update(builtinPhotometers)

    return availablePhotometers.copy()


if __name__ == "__main__":
    pass
