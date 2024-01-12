#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).


"""Classes and functions for broadcasting standard streams from external
consoles/terminals within the PsychoPy GUI suite.
"""

# This module can be expanded to centralize management for all console related
# actions in the future.
#
import os.path
import sys
import io


class StdStreamDispatcher:
    """Class for broadcasting standard output to text boxes.

    This class serves to redirect and log standard streams within the PsychoPy
    GUI suite, usually from sub-processes (e.g., a running script) to display
    somewhere. An instance of this class is created on-startup and referenced by
    the main application instance. Only one instance of this class can be
    created per-session (singleton).

    Parameters
    ----------
    app : :class:`~psychopy.app._psychopyApp.PsychoPyApp`
        Reference to the application instance.

    """
    # Developer note: In the future we should be able to attach other listeners
    # dynamically. Right now they are hard-coded, being the runner output box
    # and coder output panel. This will allow changes being made on those
    # objects not requiring any changes here.
    #
    _instance = None
    _initialized = False
    _app = None  # reference to parent app
    _logFile = None

    def __init__(self, app, logFile=None):
        # only setup if previously not instanced
        if not self._initialized:
            self._app = app
            self._logFile = logFile
            self._initialized = True

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(StdStreamDispatcher, cls).__new__(cls)

        return cls._instance

    @classmethod
    def getInstance(cls):
        """Get the (singleton) instance of the `StdStreamDispatcher` class.

        Getting a reference to the `StdOutManager` class outside of the scope of
        the user's scripts should be done through this class method.

        Returns
        -------
        StdStreamDispatcher or None
            Instance of the `Mouse` class created by the user.

        """
        return cls._instance

    @classmethod
    def initialized(cls):
        """Check if this class has been initialized.

        Returns
        -------
        bool
            `True` if the `StdStreamDispatcher` class has been already
            instanced.

        """
        return cls._initialized

    @property
    def app(self):
        """Handle to the app (`PsychopyApp` or `None`).
        """
        return self._app

    @app.setter
    def app(self, val):
        self._app = val

    @property
    def logFile(self):
        """Log file for standard streams (`str` or `None`).
        """
        return self._logFile

    @logFile.setter
    def logFile(self, val):
        self._logFile = val

    def redirect(self):
        """Redirect `stdout` and `stderr` to listeners.
        """
        sys.stdout = sys.stderr = self

    def write(self, text):
        """Send text standard output to all listeners (legacy). This method is
        used for compatibility for older code. This makes it so an instance of
        this object looks like a file object.

        Parameters
        ----------
        text : str
            Text to broadcast to all standard output windows.

        """
        self.broadcast(text=text)

    def broadcast(self, text):
        """Send text standard output to all listeners.

        Parameters
        ----------
        text : str
            Text to broadcast to all standard output windows.

        """
        # write to log file
        if self._logFile is not None:
            # with open(self._logFile, 'a') as lf:
            with io.open(self._logFile, 'a', encoding="utf-8") as lf:
                lf.write(text)
                lf.flush()

        # print text to stdout
        with io.open(sys.__stdout__.fileno(), 'w', encoding="utf-8") as sdto:
            sdto.write(text)
            sdto.flush()

        # do nothing is the app isn't fully realized
        if self.app is None or not self.app.appLoaded:
            return 

        coder = self._app.coder
        if coder is not None:
            if hasattr(coder, 'consoleOutput'):
                coder.consoleOutput.write(text)

        runner = self._app.runner
        if runner is not None:
            runner.stdOut.write(text)

    def flush(self):
        pass

    def __enter__(self):
        """Context manager entry point.
        """
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def open(self):
        """Open the log writer.
        
        This redirects stdout and stderr. Same as calling `redirect()` but
        included for compatibility with context managers.
        
        """
        sys.stdout = self
        sys.stderr = self

    def close(self):
        """Close sthe log writer.
        
        This unredirects stdout and stderr.
        
        """
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def clear(self):
        """Clear all output windows."""
        # do nothing is the app isn't fully realized
        if not self._app.appLoaded:
            return

        coder = self._app.coder
        if coder is not None:
            if hasattr(coder, 'consoleOutput'):
                coder.consoleOutput.Clear()

        runner = self._app.runner
        if runner is not None:
            runner.stdOut.Clear()

    def __del__(self):
        # restore stdout and stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


if __name__ == "__main__":
    pass
