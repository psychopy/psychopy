#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Backends provide the window creation and flipping commands.
"""

from psychopy import logging
# import psychopy.plugins as plugins
from ._base import BaseBackend

# Keep track of currently installed window backends. When a window is loaded,
# its `winType` is looked up here and the matching backend is loaded. Plugins
# which define entry points into this module will update `winTypes` if they
# define subclasses of `BaseBackend` that have valid names.
winTypes = {
    'pyglet': '.pygletbackend.PygletBackend',
    'glfw': '.glfwbackend.GLFWBackend',
    'pygame': '.pygamebackend.PygameBackend'
}


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
    # when the plugin system goes live. For now we're leaving it here.
    # try:
    #     useBackend = winTypes[win.winType]
    # except KeyError:
    #     raise KeyError(
    #         "User requested Window with winType='{}' but there is no backend "
    #         "definition to match that `winType`.".format(win.winType))

    # This loads the backend dynamically, will be enabled when the plugin system
    # goes live.
    # Backend = plugins.resolveObjectFromName(useBackend, __name__)

    if win.winType == 'pyglet':
        from .pygletbackend import PygletBackend as Backend
    elif win.winType == 'glfw':
        from .glfwbackend import GLFWBackend as Backend
    elif win.winType == 'pygame':
        from .pygamebackend import PygameBackend as Backend
    else:
        raise AttributeError("User requested Window with winType='{}' but "
                             "there is no backend definition to match that "
                             "winType.".format(win.winType))

    # Check if Backend is valid subclass of `BaseBackend`. If not, it should not
    # be used as a backend.
    if not issubclass(Backend, BaseBackend):
        raise TypeError("Requested backend is not subclass of `BaseBackend`.")

    return Backend(win, *args, **kwargs)
