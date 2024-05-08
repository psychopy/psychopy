#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
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
_psychopyAppInstance = None


def startApp(showSplash=True, testMode=False, safeMode=False, startView=None):
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
    startView : str, None
        Name of the view to start the app with. Valid values are 'coder',
        'builder' or 'runner'. If `None`, the app will start with the default
        view.

    """
    global _psychopyAppInstance

    if isAppStarted():  # do nothing it the app is already loaded
        return  # NOP
    
    # set the session lock
    setSessionLock(True)

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
    _psychopyAppInstance = PsychoPyApp(
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

    stdDisp = StdStreamDispatcher(_psychopyAppInstance, prefLogFilePath)
    stdDisp.redirect()

    if not testMode:
        # Setup redirection of errors to the error reporting dialog box. We
        # don't want this in the test environment since the box will cause the
        # app to stall on error.
        from psychopy.app.errorDlg import exceptionCallback

        # After this point, errors will appear in a dialog box. Messages will
        # continue to be written to the dialog.
        sys.excepthook = exceptionCallback

        # open the frames if requested
        if startView is not None:
            frame = getAppFrame(startView)  # opens if not yet loaded

            # raise frames to the top
            if frame is not None:
                if hasattr(frame, 'Raise'):
                    frame.Raise()
                else:
                    logging.warning(
                        'Frame has no `Raise()` method. Cannot raise it.')
            else:
                logging.error('Frame cannot be opened.')

        # Allow the UI to refresh itself. Don't do this during testing where the
        # UI is exercised programmatically.
        _psychopyAppInstance.MainLoop()


def quitApp():
    """Quit the running PsychoPy application instance.

    Will have no effect if `startApp()` has not been called previously.

    """
    if not isAppStarted():
        return

    global _psychopyAppInstance
    if hasattr(_psychopyAppInstance, 'quit'):  # type check
        _psychopyAppInstance.quit()
        # PsychoPyApp._called_from_test = False  # reset
        _psychopyAppInstance = None
    else:
        raise AttributeError('Object `_psychopyApp` has no attribute `quit`.')

    # remove the session lock
    setSessionLock(False)


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
    return _psychopyAppInstance  # use a function here to protect the reference


def setAppInstance(obj):
    """
    Define a reference to the current PsychoPyApp object.

    Parameters
    ----------
    obj : psychopy.app._psychopyApp.PsychoPyApp
        Current instance of the PsychoPy app
    """
    global _psychopyAppInstance
    _psychopyAppInstance = obj


def isAppStarted():
    """Check if the GUI portion of PsychoPy is running.

    Returns
    -------
    bool
        `True` if the GUI is started else `False`.

    """
    return _psychopyAppInstance is not None


def getSessionLock():
    """Check if the session is locked.

    Returns
    -------
    bool
        `True` if the session is locked, `False` otherwise.

    """
    from psychopy.preferences import prefs
    lockFilePath = os.path.join(prefs.paths['userPrefsDir'], 'session.lock')
    return os.path.exists(lockFilePath)


def setSessionLock(state):
    """Set the session lock state.

    This writes a session lock file to the user preferences directory. The
    presence of this file will indicate that an active PsychoPy session is
    running. This is used to prevent multiple instances of PsychoPy from running
    simultaneously, but also to detect if the app was closed unexpectedly.

    Setting the state will either create or remove the lock file. If the file
    is deleted during a session, the app will restart automatically when the 
    user quits PsychoPy.

    Parameters
    ----------
    state : bool
        `True` to lock the session, `False` to unlock.

    """
    from psychopy.preferences import prefs
    lockFilePath = os.path.join(prefs.paths['userPrefsDir'], 'session.lock')

    if state:
        if not os.path.exists(lockFilePath):
            with open(lockFilePath, 'w') as lockFile:
                lockFile.write('')  # empty file
    else:
        if os.path.exists(lockFilePath):
            os.remove(lockFilePath)


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
    frameRef = getattr(_psychopyAppInstance, frameName, None)
    if frameRef is None:
        if frameName == 'builder' and hasattr(_psychopyAppInstance, 'showBuilder'):
            _psychopyAppInstance.showBuilder()
        elif frameName == 'coder' and hasattr(_psychopyAppInstance, 'showCoder'):
            _psychopyAppInstance.showCoder()
        elif frameName == 'runner' and hasattr(_psychopyAppInstance, 'showRunner'):
            _psychopyAppInstance.showRunner()
        else:
            raise AttributeError('Cannot load frame. Method not available.')
        
        frameRef = getattr(_psychopyAppInstance, frameName, None)

    return frameRef


if __name__ == "__main__":
    pass
