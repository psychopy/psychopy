#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for using photometers.

This module serves as the entry point for plugin classes implementing
third-party photometer interfaces. All installed interfaces are discoverable
by calling the :func:`getAllPhotometers()` function.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'addPhotometer',
    'getAllPhotometers',
    'getAllPhotometerClasses'
]

from psychopy.tools.pkgtools import PluginStub

# Special handling for legacy classes which have been offloaded to optional
# packages. This will change to allow more flexibility in the future to avoid
# updating this package for additions to these sub-packages. We'll need a
# photometer type to do that, but for now we're doing it like this.
from psychopy.hardware.crs.colorcal import ColorCAL
from psychopy.hardware.crs.optical import OptiCAL

# Photo Resaerch Inc. spectroradiometers
from psychopy.hardware.pr import PR655, PR650

# Konica Minolta light-measuring devices
from psychopy.hardware.minolta import LS100, CS100A

# Gamma scientific devices
from psychopy.hardware.gammasci import S470

# photometer interfaces will be stored here after being registered
photometerInterfaces = {}


def addPhotometer(cls):
    """Register a photometer interface class.

    Once a photometer class is registered, it will be discoverable when
    :func:`getAllPhotometers()` is called. This function is also used by the
    plugin interface to add new interfaces at runtime.

    This function will overwrite interface with the same `driverFor` name
    automatically.

    Parameters
    ----------
    cls : Any
        Class specifying a photometer interface.

    """
    global photometerInterfaces

    # photometers interfaces are IDed by the model they interface with
    if not hasattr(cls, 'driverFor') or cls.driverFor is None:
        raise AttributeError(
            "Photometer interface class does not define member `driverFor` and "
            "cannot be added.")

    # add interface references to dictionary
    if isinstance(cls.driverFor, (list, tuple)):
        # multiple devices sharing the same interface
        for devModel in cls.driverFor:
            if not isinstance(devModel, str):  # items must be all strings
                raise TypeError(
                    "Invalid item type for array `driverFor`. Items must all "
                    "have type `str`.")
            photometerInterfaces[devModel] = cls
    elif isinstance(cls.driverFor, str):
        devModel = cls.driverFor
        photometerInterfaces[devModel] = cls
    else:
        raise TypeError(
            "Invalid type for `driverFor` member specified. Must be either "
            "`str`, `tuple` or `list`.")


def getAllPhotometers():
    """Gets all available photometers.

    The returned photometers may vary depending on which drivers are installed.
    Standalone PsychoPy ships with libraries for all supported photometers.

    Returns
    -------
    dict
        A mapping of all photometer classes. Where the keys (`str`) are model
        names the interface works with and the values are references to the
        unbound interface class associated with it. Keys can have the same value
        the interface is common to multiple devices.

    """
    # Given that we need to preserve legacy namespaces for the time being, we
    # need to import supported photometer classes from their extant namespaces.
    # In the future, all photometer classes will be identified by possessing a
    # common base class and being a member of this module. This is much like
    # how Builder components are discovered.

    # build a dictionary with names
    foundPhotometers = {}

    # Classes from extant namespaces. Even though these are optional, we need
    # to respect the namespaces for now.
    optionalPhotometers = (
        'ColorCAL', 'OptiCAL', 'S470', 'PR650', 'PR655', 'LS100', 'CS100A')
    incPhotomList = []
    for photName in optionalPhotometers:
        try:
            photClass = globals()[photName]
        except (ImportError, AttributeError):
            continue
        if issubclass(photClass, PluginStub):
            continue
        incPhotomList.append(photClass)

    # iterate over all classes and register them as if they were plugins
    for photom in incPhotomList:
        addPhotometer(photom)

    # Merge with classes from plugins. Duplicate names will be overwritten by
    # the plugins.
    foundPhotometers.update(photometerInterfaces)

    return foundPhotometers.copy()


def getAllPhotometerClasses():
    """Get unique photometer interface classes presently available.

    This is used to preserve compatibility with the legacy
    :func:`~psychopy.hardware.getAllPhotometers()` function call.

    Returns
    -------
    list
        Discovered unique photometer classes.

    """
    # iterate over known photometers
    photometers = getAllPhotometers()

    if not photometers:  # do nothing if no photometers found
        return []

    interfaceIDs = []  # a store unique IDs for interfaces
    # Remove items the are duplicated, i.e. multiple IDs that have a common
    # interface.
    knownInterfaces = []
    for cls in photometers.values():
        clsID = id(cls)
        if clsID in interfaceIDs:  # already added
            continue

        interfaceIDs.append(clsID)
        knownInterfaces.append(cls)

    return knownInterfaces


if __name__ == "__main__":
    pass
