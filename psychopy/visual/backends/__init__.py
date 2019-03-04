#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Backends provide the window creation and flipping commands. To create a new
backend subclass the
"""

from __future__ import absolute_import, print_function

from psychopy import logging

def getBackend(win, *args, **kwargs):
    """Retrieve the apprpriate backend

    :param winType:
    :return:
    """
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
    return Backend(win, *args, **kwargs)

