#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Module for the PsychoPy GUI application.
"""

__all__ = [
    'startApp',
    'quitApp',
    'getAppInstance',
    'getAppFrame',
    'isAppStarted']

import sys
import os
from .frametracker import openFrames

# Handle to the PsychoPy GUI application instance. We need to have this mainly
# to allow the plugin system to access GUI to allow for changes after startup.
_psychopyApp = None


def startApp(showSplash=True, testMode=False, safeMode=False):
    """Start the PsychoPy GUI. This can be called only once per session.
    Additional calls after the app starts will have no effect.

    After calling this function, you can get the handle to the created app's
    `PsychoPyApp` instance by calling :func:`getAppInstance`.

    Parameters
    ----------
    showSplash : bool
        Show the splash screen on start.
    testMode : bool
        Must be `True` if creating an instance for unit testing.
    safeMode : bool
        Start PsychoPy in safe-mode. If `True`, the GUI application will launch
        with without plugins and will use a default a configuration (planned
        feature, not implemented yet).

    """
    global _psychopyApp
    if _psychopyApp is None:
        # Make sure logging is started before loading the bulk of the main
        # application UI to catch as many errors as possible.
        if not testMode:
            from psychopy.preferences import prefs
            from psychopy.logging import console, DEBUG

            # construct path the preferences
            userPrefsDir = prefs.paths['userPrefsDir']
            prefPath = os.path.join(userPrefsDir, 'last_app_load.log')
            lastRunLog = open(prefPath, 'w')  # open the file for writing
            sys.stderr = sys.stdout = lastRunLog  # redirect output to file
            console.setLevel(DEBUG)

        # PsychoPyApp._called_from_test = testMode
        # create the application instance which starts loading it
        from psychopy.app._psychopyApp import PsychoPyApp
        _psychopyApp = PsychoPyApp(
            0, testMode=testMode, showSplash=showSplash)

        if not testMode:
            _psychopyApp.MainLoop()  # allow the UI to refresh itself


def quitApp():
    """Quit the running PsychoPy application instance.

    Will have no effect if `startApp()` has not been called previously.

    """
    if not isAppStarted():
        return

    global _psychopyApp
    if hasattr(_psychopyApp, 'quit'):  # type check
        _psychopyApp.quit()
        # PsychoPyApp._called_from_test = False  # reset
        _psychopyApp = None
    else:
        raise AttributeError(
            'Object for `_psychopyApp` does not have attribute `quit`.')


def getAppInstance():
    """Get a reference to the `PsychoPyApp` object. This function will return
    `None` if PsychoPy has been imported as a library or the app has not been
    fully realized.

    Returns
    -------
    PsychoPyApp or None
        Handle to the application instance. Returns `None` if the app has not
        been started yet or the PsychoPy is being used without a GUI.

    Examples
    --------
    Get the coder frame (if any)::

        import psychopy.app as app
        coder = app.getAppInstance().coder

    """
    return _psychopyApp  # use a function here to protect the reference


def isAppStarted():
    """Check if the GUI portion of PsychoPy is running.

    Returns
    -------
    bool
        `True` if the GUI is started else `False`.

    """
    return _psychopyApp is not None


def getAppFrame(frameName):
    """Get the reference to one of PsychoPy's application frames. Returns `None`
    if the specified frame has not been fully realized yet or PsychoPy is not in
    GUI mode.

    Parameters
    ----------
    frameName : str
        Identifier for the frame to get a reference to. Valid names are
        'coder', 'builder' or 'runner'.

    Returns
    -------
    object or None
        Reference to the frame instance (i.e. `CoderFrame`, `BuilderFrame` or
        `RunnerFrame`). `None` is returned if the frame has not been created or
        the app is not running.

    """
    if not isAppStarted():  # PsychoPy is not in GUI mode
        return None

    if frameName not in ('builder', 'coder', 'runner'):
        raise ValueError('Invalid identifier specified as `frameName`.')

    return getattr(_psychopyApp, frameName, None)
