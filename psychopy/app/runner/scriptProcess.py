#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Utilities for running scripts from the PsychoPy application suite.

Usually these are Python scripts, either written by the user in Coder or
compiled from Builder.

"""

__all__ = ['ScriptProcess']

import os.path
import sys
import psychopy.app.jobs as jobs
from wx import BeginBusyCursor, EndBusyCursor, MessageDialog, ICON_ERROR, OK
from psychopy.app.console import StdStreamDispatcher
import psychopy.logging as logging


class ScriptProcess:
    """Class to run and manage user/compiled scripts from the PsychoPy UI.

    Currently used as a "mixin" class, so don't create instances of this class
    directly for now.

    Parameters
    ----------
    app : object
        Handle for the application. Used to update UI elements to reflect the
        current state of the script.

    """
    def __init__(self, app):
        self.app = app  # reference to the app
        self.scriptProcess = None  # reference to the `Job` object
        self._processEndTime = None  # time the process ends
        self._focusOnExit = 'runner'

    @property
    def focusOnExit(self):
        """Which output to focus on when the script exits (`str`)?
        """
        return self._focusOnExit

    @focusOnExit.setter
    def focusOnExit(self, value):
        if not isinstance(value, str):
            raise TypeError('Property `focusOnExit` must be string.')
        elif value not in ('runner', 'coder'):
            raise ValueError(
                'Property `focusOnExit` must have value either "runner" or '
                '"coder"')

        self._focusOnExit = value

    @property
    def running(self):
        """Is there a script running (`bool`)?
        """
        # This is an alias for the old `runner` attribute.
        if self.scriptProcess is None:
            return False

        return self.scriptProcess.isRunning

    def runFile(self, event=None, fileName=None, focusOnExit='runner'):
        """Begin new process to run experiment.

        Parameters
        ----------
        event : wx.Event or None
            Parameter for event information if this function is bound as a
            callback. Set as `None` if calling directly.
        fileName : str
            Path to the file to run.
        focusOnExit : str
            Which output window to focus on when the application exits. Can be
            either 'coder' or 'runner'. Default is 'runner'.

        Returns
        -------
        bool
            True if the process has been started without error.

        """
        # full path to the script
        fullPath = fileName.replace('.psyexp', '_lastrun.py')

        if not os.path.isfile(fullPath):
            fileNotFoundDlg = MessageDialog(
                None,
                "Cannot run script '{}', file not found!".format(fullPath),
                caption="File Not Found Error",
                style=OK | ICON_ERROR
            )
            fileNotFoundDlg.ShowModal()
            fileNotFoundDlg.Destroy()

            if event is not None:
                event.Skip()

            return False

        # provide a message that the script is running
        # format the output message
        runMsg = u"## Running: {} ##".format(fullPath)
        runMsg = runMsg.center(80, "#") + "\n"

        # if we have a runner frame, write to the output text box
        if hasattr(self.app, 'runner'):
            stdOut = StdStreamDispatcher.getInstance()
            stdOut.lenLastRun = len(self.app.runner.stdOut.getText())
        else:
            # if not, just write to the standard output pipe
            stdOut = sys.stdout

        stdOut.write(runMsg)
        stdOut.flush()

        # interpreter path
        pyExec = sys.executable

        # optional flags for the subprocess
        execFlags = jobs.EXEC_ASYNC  # all use `EXEC_ASYNC`
        if sys.platform == 'win32':
            execFlags |= jobs.EXEC_HIDE_CONSOLE
        else:
            execFlags |= jobs.EXEC_MAKE_GROUP_LEADER

        # build the shell command to run the script
        # pyExec = '"' + pyExec + '"'  # use quotes to prevent issues with spaces
        # fullPath = '"' + fullPath + '"'
        command = [pyExec, '-u', fullPath]  # passed to the Job object

        # create a new job with the user script
        self.scriptProcess = jobs.Job(
            self,
            command=command,
            # flags=execFlags,
            inputCallback=self._onInputCallback,  # both treated the same
            errorCallback=self._onErrorCallback,
            terminateCallback=self._onTerminateCallback
        )

        BeginBusyCursor()  # visual feedback

        # start the subprocess
        workingDir, _ = os.path.split(fullPath)
        workingDir = os.path.abspath(workingDir)  # make absolute
        # move set CWD to Job.__init__ later
        pid = self.scriptProcess.start(cwd=workingDir)

        if pid < 1:  # error starting the process on zero or negative PID
            errMsg = (
                "Failed to run script '{}' in directory '{}'! Check whether "
                "the file or its directory exists and is accessible.".format(
                    fullPath, workingDir)
            )
            fileNotFoundDlg = MessageDialog(
                None,
                errMsg,
                caption="Run Task Error",
                style=OK | ICON_ERROR
            )
            fileNotFoundDlg.ShowModal()
            fileNotFoundDlg.Destroy()

            # also log the error
            logging.error(errMsg)

            if event is not None:
                event.Skip()

            self.scriptProcess = None  # reset
            EndBusyCursor()
            return False

        self.focusOnExit = focusOnExit

        return True

    def stopFile(self, event=None):
        """Stop the script process.

        Parameters
        ----------
        event : wx.Event or None
            Parameter for event information if this function is bound as a
            callback. Set as `None` if calling directly.

        """
        if hasattr(self.app, 'terminateHubProcess'):
            self.app.terminateHubProcess()

        if self.scriptProcess is not None:
            self.scriptProcess.terminate()

        # Used to call `_onTerminateCallback` here, but that is now called by
        # the `Job` instance when it exits.

    def _writeOutput(self, text, flush=True):
        """Write out bytes coming from the current subprocess.

        By default, `text` is written to the Runner window output box. If not
        available for some reason, text is written to `sys.stdout`.

        Parameters
        ----------
        text : str or bytes
            Text to write.
        flush : bool
            Flush text so it shows up immediately on the pipe.

        """
        # Make sure we have a string, data from pipes usually comes out as bytes
        # so we make the conversion if needed.
        if isinstance(text, bytes):
            text = text.decode('utf-8')

        # Where are we outputting to? Usually this is the Runner window, but if
        # not available we just write to `sys.stdout`.
        # if hasattr(self.app, 'runner'):
        #     # get any remaining data on the pipes
        #     stdOut = self.app.runner.stdOut
        # else:
        stdOut = StdStreamDispatcher.getInstance()
        if stdOut is not None:
            # write and flush if needed
            stdOut.write(text)
            if hasattr(stdOut, 'flush') and flush:
                stdOut.flush()

    # --------------------------------------------------------------------------
    # Callbacks for subprocess events
    #

    def _onInputCallback(self, streamBytes):
        """Callback to process data from the input stream of the subprocess.
        This is called when `~psychopy.app.jobs.Jobs.poll` is called and only if
        there is data in the associated pipe.

        The default behavior here is to convert the data to a UTF-8 string and
        write it to the Runner output window.

        Parameters
        ----------
        streamBytes : bytes or str
            Data from the 'stdin' streams connected to the subprocess.

        """
        self._writeOutput(streamBytes)

    def _onErrorCallback(self, streamBytes):
        """Callback to process data from the error stream of the subprocess.
        This is called when `~psychopy.app.jobs.Jobs.poll` is called and only if
        there is data in the associated pipe.

        The default behavior is to call `_onInputCallback`, forwarding argument
        `streamBytes` to it. Override this method if you want data from `stderr`
        to be treated differently.

        Parameters
        ----------
        streamBytes : bytes or str
            Data from the 'sdterr' streams connected to the subprocess.

        """
        self._onInputCallback(streamBytes)

    def _onTerminateCallback(self, pid, exitCode):
        """Callback invoked when the subprocess exits.

        Default behavior is to push remaining data to the Runner output window
        and show it by raising the Runner window. The 'Stop' button will be
        disabled in Runner (if available) since the process has ended and no
        longer can be stopped. Also restores the user's cursor to the default.

        Parameters
        ----------
        pid : int
            Process ID number for the terminated subprocess.
        exitCode : int
            Program exit code.

        """
        # write a close message, shows the exit code
        closeMsg = \
            " Experiment ended with exit code {} [pid:{}] ".format(
                exitCode, pid)
        closeMsg = closeMsg.center(80, '#') + '\n'
        self._writeOutput(closeMsg)

        self.scriptProcess = None  # reset

        # disable the stop button after exiting, no longer needed
        if hasattr(self, 'stopBtn'):  # relies on this being a mixin class
            self.stopBtn.Disable()

        # reactivate the current selection after running
        if hasattr(self, 'expCtrl') and hasattr(self, 'runBtn'):
            itemIdx = self.expCtrl.GetFirstSelected()
            if itemIdx >= 0:
                self.expCtrl.Select(itemIdx)
                self.runBtn.Enable()

        def _focusOnOutput(win):
            """Subroutine to focus on a given output window."""
            win.Show()
            win.Raise()
            win.Iconize(False)

        # set focus to output window
        if self.app is not None:
            if self.focusOnExit == 'coder' and hasattr(self.app, 'coder'):
                if self.app.coder is not None:
                    _focusOnOutput(self.app.coder)
                    self.app.coder.shelf.SetSelection(1)  # page for the console output
                    self.app.coder.shell.SetFocus()
                else:  # coder is closed, open runner and show output instead
                    if hasattr(self.app, 'runner') and \
                            hasattr(self.app, 'showRunner'):
                        # show runner if available
                        if self.app.runner is None:
                            self.app.showRunner()
                        _focusOnOutput(self.app.runner)
                        self.app.runner.stdOut.SetFocus()
            elif self.focusOnExit == 'runner' and hasattr(self.app, 'runner'):
                if self.app.runner is not None:
                    _focusOnOutput(self.app.runner)
                    self.app.runner.stdOut.SetFocus()

        EndBusyCursor()


if __name__ == "__main__":
    pass
