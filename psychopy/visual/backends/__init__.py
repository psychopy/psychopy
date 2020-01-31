#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Backends provide the window creation and flipping commands. To create a new
backend subclass the
"""

from __future__ import absolute_import, print_function

from psychopy import logging
import psychopy.plugins as plugins
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
    """Retrieve the apprpriate backend

    :param winType:
    :return:
    """
    try:
        useBackend = winTypes[win.winType]
    except KeyError:
        raise KeyError(
            "User requested Window with winType='{}' but there is no backend "
            "definition to match that `winType`.".format(win.winType))

    if useBackend.startswith('.'):  # relative to this module
        useBackend = 'psychopy.visual.backends' + useBackend

    # resolve the backend object
    Backend = plugins.resolveObjectFromName(useBackend)

    # check if valid subclass of `BaseBackend`
    if not issubclass(Backend, BaseBackend):
        raise TypeError("Requested backend is not subclass of `BaseBackend`.")

    return Backend(win, *args, **kwargs)

