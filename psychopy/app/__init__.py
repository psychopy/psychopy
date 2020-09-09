#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Module for the PsychoPy GUI application."""

from __future__ import absolute_import, print_function

__all__ = ['startApp', 'getApp', 'getAppFrame']

from psychopy.app._psychopyApp import PsychoPyApp
from .frametracker import openFrames

# Handle to the PsychoPy GUI application instance. We need to have this mainly
# to allow the plugin system to access GUI to allow for changes after startup.
_psychopyApp = None


def startApp(safeMode=False, showSplash=True):
    """Start the PsychoPy GUI. This can be called only once per session.
    Additional calls after the app starts will have no effect.

    After calling this function, you can get the handle to the created app's
    `PsychoPyApp` instance by calling :func:`getApp`.

    Parameters
    ----------
    safeMode : bool
        Start PsychoPy in safe-mode. If `True`, the GUI application will launch
        with without plugins and will use a default a configuration (planned
        feature, not implemented yet).
    showSplash : bool
        Show the splash screen on start.

    """
    global _psychopyApp
    if _psychopyApp is None:
        _psychopyApp = PsychoPyApp(0, showSplash=showSplash)
        _psychopyApp.MainLoop()


def getApp():
    """Get a reference to the `PsychoPyApp` object. This function will return
    `None` if PsychoPy has been imported as a library or the app has not been
    fully realized.

    Returns
    -------
    PsychoPyApp or None
        Handle to the application instance. Returns `None` if the app has not
        been started yet or the PsychoPy is being used without a GUI.

    """
    return _psychopyApp  # use a function here to protect the reference


def getAppFrame(frameName):
    """Get the reference to one of PsychoPy's application frames. Returns `None`
    if the coder frame has not been realized or PsychoPy is not in GUI mode.

    Parameters
    ----------
    frameName : str
        Identifier for the frame to get a reference to. Valid names are
        'coder', 'builder' or 'runner'.

    Returns
    -------
    object or None
        Reference to the frame (i.e. `CoderFrame`, `BuilderFrame` or
        `RunnerFrame`). `None` is returned if the frame has not been created or
        the app is not running.

    """
    if _psychopyApp is None:  # PsychoPy is not in GUI mode
        return False

    if frameName not in ('builder', 'coder', 'runner'):
        raise ValueError('Invalid identifier specified as `frameName`.')

    return getattr(_psychopyApp, frameName, None)

