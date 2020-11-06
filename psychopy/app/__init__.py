#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Module for the PsychoPy GUI application."""

from __future__ import absolute_import, print_function

__all__ = ['startApp', 'getApp', 'getAppFrame', 'isSafeMode']

from psychopy.app._psychopyApp import PsychoPyApp
from .frametracker import openFrames

# Handle to the PsychoPy GUI application instance. We need to have this mainly
# to allow the plugin system to access GUI to allow for changes after startup.
# In addition, one can use this reference to automate GUI tasks from scripts.
_psychopyApp = None

# Safe mode flag. If `True` plugins should not be loaded and a default
# configuration should be used.
_safeMode = False


def startApp(safeMode=False, showSplash=True):
    """Start the PsychoPy GUI. This can be called only once per session.
    Additional calls after the app starts will have no effect.

    After calling this function, you can get the handle to the created app's
    `PsychoPyApp` instance by calling :func:`getApp`. Calling this function from
    a script can be used to invoke the GUI.

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
    global _safeMode
    if _psychopyApp is None:
        _safeMode = safeMode
        _psychopyApp = PsychoPyApp(0, showSplash=showSplash)
        _psychopyApp.MainLoop()


def getApp():
    """Get a reference to the `PsychoPyApp` object. This function will return
    `None` if PsychoPy has been imported as a library or the app has not been
    fully realized.

    One can use this function to determine whether the PsychoPy was loaded as
    a library or started in GUI mode. Plugins can check this to determine
    whether or not to load Builder components.

    Returns
    -------
    PsychoPyApp or None
        Handle to the application instance. Returns `None` if the app has not
        been started yet or the PsychoPy is being used without a GUI.

    Examples
    --------
    Check if PsychoPy was started with a GUI::

        hasGUI = getApp() is not None

    """
    return _psychopyApp  # use a function here to protect the reference


def getAppFrame(frameName):
    """Get the reference to one of PsychoPy's application frames. Returns `None`
    if a frame has not been realized or PsychoPy is not in GUI mode.

    The returned object can be used to manipulate GUI elements (invoke events,
    add/update widgets, etc.) while the application is running.

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

    Examples
    --------
    Get the reference to the Coder frame then set the current document::

        import psychopy.app as app

        coderFrame = app.getAppFrame('coder')
        coderFrame.setCurrentDoc('path/to/my/doc.py')

    """
    if _psychopyApp is None:  # PsychoPy is not in GUI mode
        return False

    if frameName not in ('builder', 'coder', 'runner'):
        raise ValueError('Invalid identifier specified as `frameName`.')

    return getattr(_psychopyApp, frameName, None)


def isSafeMode():
    """Check if PsychoPy's GUI was started in 'safe-mode'.

    If so, plugins should not be loaded and a default configuration should be
    used. Safe-mode is needed to recover from errors which prevent PsychoPy from
    loading. Giving the user an opportunity to disable plugins or fix
    configurations which caused the problem. Third-party software can check if
    the user has specified safe-mode and disable features accordingly.

    Returns
    -------
    bool
        `True` is PsychoPy was started in safe mode.

    """
    global _safeMode
    return _safeMode

