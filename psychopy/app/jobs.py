#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Classes and functions for creating and managing subprocesses spawned by the
GUI application. These subprocesses are mainly used to perform 'jobs'
asynchronously without blocking the main application loop which would otherwise
render the UI unresponsive.
"""

import wx

# Aliases so we don't need to explicitly import `wx`.
EXEC_ASYNC = wx.EXEC_ASYNC
EXEC_SYNC = wx.EXEC_SYNC
EXEC_SHOW_CONSOLE = wx.EXEC_SHOW_CONSOLE
EXEC_HIDE_CONSOLE = wx.EXEC_HIDE_CONSOLE
EXEC_MAKE_GROUP_LEADER = wx.EXEC_MAKE_GROUP_LEADER
EXEC_NODISABLE = wx.EXEC_NODISABLE
EXEC_NOEVENTS = wx.EXEC_NOEVENTS
EXEC_BLOCK = wx.EXEC_BLOCK

# Signal enumerations for `wx.Process.Kill`, only use the one here that work on
# all platforms.
SIGTERM = wx.SIGTERM
SIGKILL = wx.SIGKILL
SIGINT = wx.SIGINT

# Flags for wx.Process.Kill`.
KILL_NOCHILDREN = wx.KILL_NOCHILDREN
KILL_CHILDREN = wx.KILL_CHILDREN  # yeesh ...

# Error values for `wx.Process.Kill`
KILL_OK = wx.KILL_OK
KILL_BAD_SIGNAL = wx.KILL_BAD_SIGNAL
KILL_ACCESS_DENIED = wx.KILL_ACCESS_DENIED
KILL_NO_PROCESS = wx.KILL_NO_PROCESS
KILL_ERROR = wx.KILL_ERROR


class Job:
    """General purpose class for running subprocesses using wxPython's
    subprocess framework. This class should only be instanced and used if the
    GUI is present.

    Parameters
    ----------
    command : str
    pollMillis : int or None
        Time in milliseconds between polling intervals. When interval specified
        by `pollMillis` elapses, the input and error streams will be read and
        callback functions will be called. If `None`, then the timer will be
        disabled and the `poll()` method will need to be invoked.

    Examples
    --------
    Spawn a new subprocess::

        # command to execute
        command = 'python3 myScript.py'
        # create a new job object
        job = Job(command, flags=EXEC_ASYNC)
        # start it
        pid = job.start()  # returns a PID for the sub process
        # read data from the subprocess

    """
    def __init__(self, command='', flags=EXEC_ASYNC, terminateCallback=None,
                 inputCallback=None, errorCallback=None, pollMillis=None):

        # command to be called, cannot be changed after spawning the process
        self._command = command
        self._pid = None
        self._flags = flags
        self._process = None
        self._pollMillis = pollMillis
        self._pollTimer = wx.Timer()

        # user defined callbacks
        self._inputCallback = inputCallback
        self._errorCallback = errorCallback
        self._terminateCallback = terminateCallback

    def start(self):
        """Start the subprocess.

        Returns
        -------
        int
            Process ID assigned by the operating system.

        """
        wx.BeginBusyCursor()  # visual feedback

        # create a new process object, this handles streams and stuff
        self._process = wx.Process(None, -1)
        self._process.Redirect()  # redirect streams from subprocess

        # start the sub-process
        self._pid = wx.Execute(self._command, self._flags, self._process)

        # bind the event called when the process ends
        self._process.Bind(wx.EVT_END_PROCESS, self.onTerminate)

        # start polling for data from the subprocesses
        if self._pollMillis is not None:
            self._pollTimer.Notify = self.onNotify  # override
            self._pollTimer.Start(self._pollMillis, oneShot=wx.TIMER_CONTINUOUS)

        wx.EndBusyCursor()

        return self._pid

    def terminate(self, signal=SIGTERM, flags=KILL_NOCHILDREN):
        """Stop/kill the subprocess associated with this object.

        Parameters
        ----------
        signal : int
            Signal to use (eg. `SIGTERM`, `SIGINT`, `SIGKILL`, etc.) These are
            available as module level constants.
        flags : int
            Additional option flags, by default `KILL_NOCHILDREN` is specified
            which prevents child processes of the active subprocess from being
            signaled to terminate. Using `KILL_CHILDREN` will signal child
            processes to terminate. Note that on UNIX, `KILL_CHILDREN` will only
            have an effect if `EXEC_MAKE_GROUP_LEADER` was specified when the
            process was spawned. These values are available as module level
            constants.

        Return
        ------
        bool
            `True` if the terminate call was successful in ending the
            subprocess. If `False`, something went wrong and you should try and
            figure it out.

        """
        if not self.isRunning:
            return  # nop

        wx.BeginBusyCursor()  # visual feedback

        # kill the process, check if itm was successful
        isOk = wx.Process.Kill(self._pid, signal, flags) != wx.KILL_OK
        self._pollTimer.Stop()

        if isOk:
            self._process = self._pid = None

        wx.EndBusyCursor()

        return isOk

    @property
    def command(self):
        """Shell command to execute (`str`). Same as the `command` argument.
        Raises an error if this value is changed after `start()` was called.
        """
        return self._command

    @command.setter
    def command(self, val):
        if self.isRunning:
            raise AttributeError(
                'Cannot set property `command` if the subprocess is running!')

        self._command = val

    @property
    def flags(self):
        """Shell command to execute (`str`). Same as the `command` argument.
        Raises an error if this value is changed after `start()` was called.
        """
        return self._flags

    @flags.setter
    def flags(self, val):
        if self.isRunning:
            raise AttributeError(
                'Cannot set property `flags` if the subprocess is running!')

        self._flags = val

    @property
    def isRunning(self):
        """Is the subprocess running (`bool`)? If `True` the value of the
        `command` property cannot be changed.
        """
        return self._pid != 0 and self._process is not None

    @property
    def pid(self):
        """Process ID for the active subprocess (`int`). Only valid after the
        process has been started.
        """
        return self._pid

    def getPid(self):
        """Process ID for the active subprocess. Only valid after the process
        has been started.

        Returns
        -------
        int or None
            Process ID assigned to the subprocess by the system. Returns `None`
            if the process has not been started.

        """
        return self._pid

    @property
    def isOutputAvailable(self):
        """`True` if the output pipe to the subprocess is opened (therefore
        writeable). If not, you cannot write any bytes to 'outputStream'. Some
        subprocesses may signal to the parent process that its done processing
        data by closing its input.
        """
        if self._process is None:
            return False

        return self._process.IsInputOpened()

    @property
    def outputStream(self):
        """Handle to the file-like object handling the standard output stream
        (`ww.OutputStream`). This is used to write bytes which will show up in
        the 'stdin' pipe of the subprocess.
        """
        if not self.isRunning():
            return None

        return self._process.OutputStream

    @property
    def isInputAvailable(self):
        """Check if there are bytes available to be read from the input stream
        (`bool`).
        """
        if self._process is None:
            return False

        return self._process.IsInputAvailable()

    @property
    def inputStream(self):
        """Handle to the file-like object handling the standard input stream
        (`wx.InputStream`). This is used to read bytes which the subprocess is
        writing to 'stdout'.
        """
        if not self.isRunning():
            return None

        return self._process.InputStream

    @property
    def isErrorAvailable(self):
        """Check if there are bytes available to be read from the error stream
        (`bool`).
        """
        if self._process is None:
            return False

        return self._process.IsErrorAvailable()

    @property
    def errorStream(self):
        """Handle to the file-like object handling the standard error stream
        (`wx.InputStream`). This is used to read bytes which the subprocess is
        writing to 'stderr'.
        """
        if not self.isRunning():
            return None

        return self._process.ErrorStream

    def poll(self):
        """Poll input and error streams for data, pass them to callbacks if
        specified.
        """
        if self._process is None:  # do nothing if there is no process
            return

        # is there data in the input pipe?
        if self._process.IsInputAvailable() and self._inputCallback is not None:
            stdinText = self._process.InputStream.read()
            wx.CallAfter(self._inputCallback, args=(stdinText,))

        # same as above but with the error stream
        if self._process.IsErrorAvailable() and self._errorCallback is not None:
            stderrText = self._process.ErrorStream.read()
            wx.CallAfter(self._errorCallback, args=(stderrText,))

    def onTerminate(self, evt=None):
        """Called when the process exits. Override for custom functionality."""
        wx.CallAfter(self._terminateCallback)

    def onNotify(self):
        """Called when the polling timer elapses.

        Default action is to read input and error streams and broadcast any data
        to user defined callbacks (if `poll()` has not been overwritten).
        """
        self.poll()


if __name__ == "__main__":
    pass
