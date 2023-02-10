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
from .console import StdStreamDispatcher
from .frametracker import openFrames

# Handle to the PsychoPy GUI application instance. We need to have this mainly
# to allow the plugin system to access GUI to allow for changes after startup.
_psychopyApp = None


def startApp(showSplash=True, testMode=False, safeMode=False):
    """Start the PsychoPy GUI.

    This function is idempotent, where additional calls after the app starts
    will have no effect unless `quitApp()` was previously called. After this
    function returns, you can get the handle to the created `PsychoPyApp`
    instance by calling :func:`getAppInstance` (returns `None` otherwise).

    Errors raised during initialization due to unhandled exceptions with respect
    to the GUI application are usually fatal. You can examine
    'last_app_load.log' inside the 'psychopy3' user directory (specified by
    preference 'userPrefsDir') to see the traceback. After startup, unhandled
    exceptions will appear in a special dialog box that shows the error
    traceback and provides some means to recover their work. Regular logging
    messages will appear in the log file or GUI. We use a separate error dialog
    here is delineate errors occurring in the user's experiment scripts and
    those of the application itself.

    Parameters
    ----------
    showSplash : bool
        Show the splash screen on start.
    testMode : bool
        Must be `True` if creating an instance for unit testing.
    safeMode : bool
        Start PsychoPy in safe-mode. If `True`, the GUI application will launch
        with without loading plugins.

    """
    global _psychopyApp

    if isAppStarted():  # do nothing it the app is already loaded
        return  # NOP

    # Make sure logging is started before loading the bulk of the main
    # application UI to catch as many errors as possible. After the app is
    # loaded, messages are handled by the `StdStreamDispatcher` instance.
    prefLogFilePath = None
    if not testMode:
        from psychopy.preferences import prefs
        from psychopy.logging import console, DEBUG

        # construct path to log file from preferences
        userPrefsDir = prefs.paths['userPrefsDir']
        prefLogFilePath = os.path.join(userPrefsDir, 'last_app_load.log')
        lastRunLog = open(prefLogFilePath, 'w')  # open the file for writing
        console.setLevel(DEBUG)

        # NOTE - messages and errors cropping up before this point will go to
        # console, afterwards to 'last_app_load.log'.
        sys.stderr = sys.stdout = lastRunLog  # redirect output to file

    # Create the application instance which starts loading it.
    # If `testMode==True`, all messages and errors (i.e. exceptions) will log to
    # console.
    from psychopy.app._psychopyApp import PsychoPyApp
    _psychopyApp = PsychoPyApp(
        0, testMode=testMode, showSplash=showSplash, safeMode=safeMode)

    # After the app is loaded, we hand off logging to the stream dispatcher
    # using the provided log file path. The dispatcher will write out any log
    # messages to the extant log file and any GUI windows to show them to the
    # user.

    # ensure no instance was created before this one
    if StdStreamDispatcher.getInstance() is not None:
        raise RuntimeError(
            '`StdStreamDispatcher` instance initialized outside of `startApp`, '
            'this is not permitted.')

    stdDisp = StdStreamDispatcher(_psychopyApp, prefLogFilePath)
    stdDisp.redirect()

    if not testMode:
        # Setup redirection of errors to the error reporting dialog box. We
        # don't want this in the test environment since the box will cause the
        # app to stall on error.
        from psychopy.app.errorDlg import exceptionCallback

        # After this point, errors will appear in a dialog box. Messages will
        # continue to be written to the dialog.
        sys.excepthook = exceptionCallback

        # Allow the UI to refresh itself. Don't do this during testing where the
        # UI is exercised programmatically.
        _psychopyApp.MainLoop()


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
        raise AttributeError('Object `_psychopyApp` has no attribute `quit`.')


def getAppInstance():
    """Get a reference to the `PsychoPyApp` object.

    This function will return `None` if PsychoPy has been imported as a library
    or the app has not been fully realized.

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
        the app is not running. May return a list if more than one window is
        opened.

    """
    if not isAppStarted():  # PsychoPy is not in GUI mode
        return None

    if frameName not in ('builder', 'coder', 'runner'):
        raise ValueError('Invalid identifier specified as `frameName`.')

    # open the requested frame if no yet loaded
    frameRef = getattr(_psychopyApp, frameName, None)
    if frameRef is None:
        if frameName == 'builder' and hasattr(_psychopyApp, 'showBuilder'):
            _psychopyApp.showBuilder()
        elif frameName == 'coder' and hasattr(_psychopyApp, 'showCoder'):
            _psychopyApp.showCoder()
        elif frameName == 'runner' and hasattr(_psychopyApp, 'showRunner'):
            _psychopyApp.showRunner()
        else:
            raise AttributeError('Cannot load frame. Method not available.')

    return frameRef


if __name__ == "__main__":
    pass
