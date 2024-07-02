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
    'restartApp',
    'setRestartRequired',
    'isRestartRequired',
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

# Flag to indicate if the app requires a restart. This is set by the app when
# it needs to restart after an update or plugin installation. We can check this
# flag to determine if the app is in a state that it is recommended to restart.
REQUIRES_RESTART = False


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
        view or the view specifed with the `PSYCHOPYSTARTVIEW` environment
        variable.

    """
    global _psychopyAppInstance

    if isAppStarted():  # do nothing it the app is already loaded
        return  # NOP

    # process environment variables
    startViewVal = os.environ.get('PSYCHOPYSTARTVIEW', None)
    if startViewVal is not None:
        startView = str(startViewVal).lower()
        if startView not in ('coder', 'builder', 'runner'):
            startView = None  # silently drop invalid values and use default

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


def restartApp():
    """Restart the PsychoPy application instance.

    This will write a file named '.restart' to the user preferences directory
    and quit the application. The presence of this file will indicate to the 
    launcher parent process that the app should restart.

    The app restarts with the same arguments as the original launch. This is
    useful for updating the application or plugins without requiring the user
    to manually restart the app.

    The user will be prompted to save any unsaved work before the app restarts.

    """
    if not isAppStarted():
        return
    
    # write a restart file to the user preferences directory
    from psychopy.preferences import prefs
    restartFilePath = os.path.join(prefs.paths['userPrefsDir'], '.restart')
    
    with open(restartFilePath, 'w') as restartFile:
        restartFile.write('')  # empty file

    quitApp()


def setRestartRequired(state=True):
    """Set the flag to indicate that the app requires a restart.

    This function is used by the app to indicate that a restart is required
    after an update or plugin installation. The flag is checked by the launcher
    parent process to determine if the app should restart.

    Parameters
    ----------
    state : bool
        Set the restart flag. If `True`, the app will restart after quitting.

    """
    global REQUIRES_RESTART
    REQUIRES_RESTART = bool(state)


def isRestartRequired():
    """Check if the app requires a restart.

    Parts of the application may set this flag to indicate that a restart is
    required after an update or plugin installation.

    Returns
    -------
    bool
        `True` if the app requires a restart else `False`.

    """
    return REQUIRES_RESTART


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
