#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for routines in Builder.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from importlib import import_module
from ._base import BaseStandaloneRoutine, BaseValidatorRoutine, Routine
from .unknown import UnknownRoutine
from pathlib import Path
from psychopy import logging

# Standalone components loaded from plugins are stored in this dictionary. These
# are added by calling `addStandaloneRoutine`. Plugins will always override
# builtin components with the same name.
pluginRoutines = {} 


def addStandaloneRoutine(routineClass):
    """Add a standalone routine to Builder.

    This function will override any routine already loaded with the same
    class name. Usually, this function is called by the plugin system. The user
    typically does not need to call this directly.

    Parameters
    ----------
    routineClass : object
        Standalone routine class. Should be a subclass of 
        `BaseStandaloneRoutine`.

    """
    global pluginRoutines  # components loaded at runtime

    routineName = routineClass.__name__
    logging.debug("Registering Builder routine class `{}`.".format(routineName))

    # check type and attributes of the class
    if not issubclass(routineClass, BaseStandaloneRoutine):
        logging.warning(
            "Component `{}` does not appear to be a subclass of "
            "`psychopy.experiment.routines._base.BaseStandaloneRoutine`. This "
            " may not work correcty.".format(routineName))
    elif not hasattr(routineClass, 'categories'):
        logging.warning(
            "Routine `{}` does not define a `.categories` attribute.".format(
                routineName))

    pluginRoutines[routineName] = routineClass


def getAllStandaloneRoutines(fetchIcons=True):
    """Get a mapping of all standalone routines.

    This function will return a dictionary of all standalone routines
    available in Builder. The dictionary is indexed by the class name of the
    routine. The values are the routine classes themselves.

    Parameters
    ----------
    fetchIcons : bool
        If `True`, the routine classes will be asked to fetch their icons.

    Returns
    -------
    dict
        Dictionary of all standalone routines available in Builder, including
        those added by plugins.

    """
    # Safe import all modules within this folder (apart from protected ones with a _)
    for loc in Path(__file__).parent.glob("*"):
        if loc.is_dir() and not loc.name.startswith("_"):
            import_module("." + loc.name, package="psychopy.experiment.routines")

    # Get list of subclasses of BaseStandalone
    def getSubclasses(cls, classList=None):
        # create list if needed
        if classList is None:
            classList = []
        # add to class list
        classList.append(cls)
        # recur for subclasses
        for subcls in cls.__subclasses__():
            getSubclasses(subcls, classList)

        return classList
    classList = getSubclasses(BaseStandaloneRoutine)
    # Remove unknown
    #if UnknownRoutine in classList:
    #    classList.remove(UnknownRoutine)
    # Get list indexed by class name with Routine removed
    classDict = {c.__name__: c for c in classList}

    # merge with plugin components
    global pluginRoutines
    if pluginRoutines:
        logging.debug("Merging plugin routines with builtin Builder routines.")
        classDict.update(pluginRoutines)

    return classDict


if __name__ == "__main__":
    pass
