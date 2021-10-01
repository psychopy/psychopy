#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Utilities for running scripts from the PsychoPy application suite.
"""

__all__ = ['ScriptProcess']

import wx
import sys
import psychopy.app.jobs as jobs


class ScriptProcess:
    """Class to run script through subprocess.

    Parameters
    ----------
    app : object
        Handle for the application. Used to update UI elements to reflect the
        current state of the script.

    """
    def __init__(self, app):
        self.app = app
        self.scriptProcess = None

    @property
    def running(self):
        """Is there a script running (`bool`)?
        """
        # This is an alias for the old `runner` attribute.
        if self.scriptProcess is None:
            return False

        return self.scriptProcess.isRunning

    def runFile(self, event=None, fileName=None):
        """Begin new process to run experiment.

        Parameters
        ----------
        event : wx.Event or None
            Parameter for event information if this function is bound as a
            callback. Set as `None` if calling directly.
        fileName : str
            Path to the file to run.

        """
        # full path to the script
        fullPath = fileName.replace('.psyexp', '_lastrun.py')

        # provide a message that the script is running
        # format the output message
        runMsg = u"## Running: {} ##".format(fullPath)
        runMsg = runMsg.center(80, "#") + "\n"

        # if we have a runner frame, write to the output text box
        if hasattr(self.app, 'runner'):
            stdOut = self.app.runner.stdOut
            stdOut.write(runMsg)
            stdOut.lenLastRun = len(self.app.runner.stdOut.getText())
        else:
            # if not, just write to the output pipe
            sys.stdout.write(runMsg)

        # build the shell command to run the script
        command = [sys.executable, '-u', fullPath]

        # option flags for the subprocess
        execFlags = jobs.EXEC_ASYNC  # all use `EXEC_ASYNC`
        if sys.platform == 'win32':
            execFlags |= jobs.EXEC_HIDE_CONSOLE
        else:
            execFlags |= jobs.EXEC_MAKE_GROUP_LEADER

        # time the process ends
        self._processEndTime = None

        # create a new job with the user script
        self.scriptProcess = jobs.Job(
            command=command,
            flags=execFlags,
            inputCallback=self._onInputCallback,  # both treated the same
            errorCallback=self._onInputCallback,
            terminateCallback=self._onTerminateCallback,
            pollMillis=120  # check input every 120 ms
        )

        # start the subprocess
        self.scriptProcess.start()

    def stopFile(self, event=None):
        """Stop the script process.
        """
        if hasattr(self.app, 'terminateHubProcess'):
            self.app.terminateHubProcess()

        if self.scriptProcess is not None:
            self.scriptProcess.terminate()

        # Used to call `_onTerminateCallback` here, but that is now called by
        # the `Job` instance when it exits.

    def _onInputCallback(self, data):
        """Callback to process data from the input stream from the subprocess.
        This is called everytime `poll` is called.

        The default behavior here is to convert the data to a UTF-8 string and
        write it to the Runner output window.

        Parameters
        ----------
        data : bytes or str
            Data from the 'stdin' or 'sderr' streams connected to the
            subprocess.

        """
        if hasattr(self.app, 'runner'):
            self.app.runner.stdOut.write(data.decode('utf-8'))
            self.app.runner.stdOut.flush()

    def _onTerminateCallback(self):
        """Callback invoked when the subprocess exits.

        Default behavior is to push remaining data to the Runner output window
        and show it by raising the Runner window.

        """
        self.scriptProcess = None
        if hasattr(self.app, 'runner'):
            self.app.runner.stdOut.flush()
            self.app.runner.Show()

        # write a close message
        closeMsg = "##### Experiment ended. #####\n"
        sys.stdout.write(closeMsg)


if __name__ == "__main__":
    pass

