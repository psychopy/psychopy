#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for routines in Builder.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import importlib, importlib.metadata
import inspect
from ._base import BaseStandaloneRoutine, BaseDeviceRoutine, BaseValidatorRoutine, Routine
from .unknown import UnknownRoutine
from pathlib import Path
from psychopy import logging

# Standalone components loaded from plugins are stored in this dictionary. These
# are added by calling `addStandaloneRoutine`. Plugins will always override
# builtin components with the same name.
pluginRoutines = {} 


def filterRoutine(rt):
    """
    Function for filtering Routines to remove e.g. base classes.

    Parameters
    ----------
    rt : BaseStandaloneRoutine
        Class of the Routine to check
    
    Returns
    -------
    bool
        True if Routine is fine to include
    """
    # filter non-classes
    if not inspect.isclass(rt):
        return False
    # filter non-Routines
    if not issubclass(rt, BaseStandaloneRoutine):
        return False
    # filter protected classes
    if rt.__name__.startswith("_"):
        return False
    # filter base Routines
    if rt.__name__.lower().startswith("base"):
        return False
    # filter unknown Routines
    if rt.__name__.lower().startswith("unknown"):
        return False

    return True


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


def getAllStandaloneRoutines(fetchIcons=False):
    """
    Get a mapping of all standalone routines.

    This function will return a dictionary of all standalone routines
    available in Builder. The dictionary is indexed by the class name of the
    routine. The values are the routine classes themselves.

    Returns
    -------
    dict
        Dictionary of all standalone routines available in Builder, including
        those added by plugins.

    """
    # start with blank dict
    routines = {}
    # search folder for modules which look like they contain a Routine...
    for subfolder in Path(__file__).parent.glob("*/__init__.py"):
        # import each submodule
        mod = importlib.import_module(
            f"psychopy.experiment.routines.{subfolder.parent.stem}"
        )
        # go through members in module
        for attrib in dir(mod):
            # get member
            member = getattr(mod, attrib)
            # if member is a Routine, add it
            if filterRoutine(member):
                routines[member.__name__] = member
    
    # find plugin Routines...
    for point in importlib.metadata.entry_points(group="psychopy.experiment.routines"):
        # load entry point
        member = point.load()
        # if it's a Component, add it
        if filterRoutine(member):
            routines[member.__name__] = member
    
    return routines


if __name__ == "__main__":
    pass
