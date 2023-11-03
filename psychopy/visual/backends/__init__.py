#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Backends provide the window creation and flipping commands.
"""

import psychopy.plugins as plugins
from ._base import BaseBackend

# Alias plugins.winTypes here, such that any plugins referencing visual.winTypes
# will also update the matching dict in plugins
winTypes = plugins._winTypes


def getBackend(win, *args, **kwargs):
    """Retrieve the appropriate backend for the window.

    Parameters
    ----------
    win : :class:`psychopy.visual.Window`
        Window requesting the backend. The `winType` attribute of the Window
        is used to determine which one to get.
    *args, **kwargs
        Optional positional and keyword arguments to pass to the backend
        constructor. These arguments are usually those passed to the constructor
        for the Window.

    Returns
    -------
    :class:`~psychopy.visual.backends._base.BaseBackend`
        Backend class (subclass of BaseBackend).

    """
    # Look-up the backend module name for `winType`, this is going to be used
    # when the plugin system goes live. For now, we're leaving it here.
    try:
        useBackend = winTypes[win.winType]
    except KeyError:
        raise KeyError(
            "User requested Window with winType='{}' but there is no backend "
            "definition to match that `winType`.".format(win.winType))

    # this loads the backend dynamically from the FQN stored in `winTypes`
    Backend = plugins.resolveObjectFromName(useBackend, __name__)

    # Check if Backend is valid subclass of `BaseBackend`. If not, it should not
    # be used as a backend.
    if not issubclass(Backend, BaseBackend):
        raise TypeError("Requested backend is not subclass of `BaseBackend`.")

    return Backend(win, *args, **kwargs)


def getAvailableWinTypes():
    """Get a list of available window backends.

    This will also list backends provided by plugins if they have been loaded
    prior to calling this function.

    Returns
    -------
    list
        List of possible values (`str`) to pass to the `winType` argument of
        `~:class:psychopy.visual.Window` .

    """
    global winTypes
    return list(winTypes.keys())  # copy


if __name__ == "__main__":
    pass

