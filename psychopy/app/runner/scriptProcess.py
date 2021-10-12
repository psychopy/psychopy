#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Utilities for running scripts from the PsychoPy application suite.

Usually these are Python scripts, either written by the user in Coder or
compiled from Builder.

"""

__all__ = ['ScriptProcess']

import sys
import psychopy.app.jobs as jobs
from wx import BeginBusyCursor, EndBusyCursor


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
        pyExec = '"' + pyExec + '"'  # use quotes, needed for Windows
        command = [pyExec, '-u', fullPath]

        # create a new job with the user script
        self.scriptProcess = jobs.Job(
            command=command,
            flags=execFlags,
            inputCallback=self._onInputCallback,  # both treated the same
            errorCallback=self._onErrorCallback,
            terminateCallback=self._onTerminateCallback,
            pollMillis=120  # check input/error pipes every 120 ms
        )

        BeginBusyCursor()  # visual feedback

        # start the subprocess
        self.scriptProcess.start()

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
        if hasattr(self.app, 'runner'):
            # get any remaining data on the pipes
            stdOut = self.app.runner.stdOut
            self.app.runner.Show()
        else:
            stdOut = sys.stdout

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
            "##### Experiment ended with exit code {} [pid:{}] #####\n".format(
                exitCode, pid)
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

        EndBusyCursor()


if __name__ == "__main__":
    pass
