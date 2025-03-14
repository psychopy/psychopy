#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Classes and functions for creating and managing subprocesses spawned by the
GUI application. These subprocesses are mainly used to perform 'jobs'
asynchronously without blocking the main application loop which would otherwise
render the UI unresponsive.
"""

__all__ = [
    'EXEC_SYNC',
    'EXEC_ASYNC',
    'EXEC_SHOW_CONSOLE',
    'EXEC_HIDE_CONSOLE',
    'EXEC_MAKE_GROUP_LEADER',
    'EXEC_NODISABLE',
    'EXEC_NOEVENTS',
    'EXEC_BLOCK',
    'SIGTERM',
    'SIGKILL',
    'SIGINT',
    'KILL_NOCHILDREN',
    'KILL_CHILDREN',
    'KILL_OK',
    'KILL_BAD_SIGNAL',
    'KILL_ACCESS_DENIED',
    'KILL_NO_PROCESS',
    'KILL_ERROR',
    'Job'
]

import os.path

import wx
import os
import sys
from subprocess import Popen, PIPE
from threading import Thread, Event
from queue import Queue, Empty
import time

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

# PIPE_READER_POLL_INTERVAL = 0.025  # seconds


class PipeReader(Thread):
    """Thread for reading standard stream pipes. This is used by the `Job` class
    to provide non-blocking reads of pipes.

    Parameters
    ----------
    fdpipe : Any
        File descriptor for the pipe, either `Popen.stdout` or `Popen.stderr`.

    """
    def __init__(self, fdpipe):
        # setup the `Thread` stuff
        super(PipeReader, self).__init__()
        self.daemon = True

        self._fdpipe = fdpipe  # pipe file descriptor
        # queue objects for passing bytes to the main thread
        self._queue = Queue(maxsize=1)
        # Overflow buffer if the queue is full, prevents data loss if the
        # application isn't reading the pipe quick enough.
        self._overflowBuffer = []
        # used to signal to the thread that it's time to stop
        self._stopSignal = Event()
        self._closedSignal = Event()

    @property
    def isAvailable(self):
        """Are there bytes available to be read (`bool`)?"""
        if self._queue.full():
            return True
        elif self._overflowBuffer:  # have leftover bytes
            self._queue.put("".join(self._overflowBuffer))
            self._overflowBuffer = []  # clear the overflow buffer
            return True
        else:
            return False

    def read(self):
        """Read all bytes enqueued by the thread coming off the pipe. This is
        a non-blocking operation. The value `''` is returned if there is no
        new data on the pipe since the last `read()` call.

        Returns
        -------
        bytes
            Most recent data passed from the subprocess since the last `read()`
            call.

        """
        try:
            return self._queue.get_nowait()
        except Empty:
            return ''

    def run(self):
        """Payload routine for the thread. This reads bytes from the pipe and
        enqueues them.
        """
        # read bytes in chunks until EOF
        for pipeBytes in iter(self._fdpipe.readline, b''):
            # put bytes into the queue, handle overflows if the queue is full
            if not self._queue.full():
                # we have room, check if we have a backlog of bytes to send
                if self._overflowBuffer:
                    pipeBytes = "".join(self._overflowBuffer) + pipeBytes
                    self._overflowBuffer = []  # clear the overflow buffer

                # write bytes to the queue
                self._queue.put(pipeBytes)
            else:
                # Put bytes into buffer if the queue hasn't been emptied quick
                # enough. These bytes will be passed along once the queue has
                # space.
                self._overflowBuffer.append(pipeBytes)

            if self._stopSignal.is_set():
                break

        self._closedSignal.set()

    def stop(self):
        """Call this to signal the thread to stop reading bytes."""
        self._stopSignal.set()
        while not self._closedSignal.is_set():
            time.sleep(0.01)

        return self._fdpipe


class Job:
    """General purpose class for running subprocesses using wxPython's
    subprocess framework. This class should only be instanced and used if the
    GUI is present.

    Parameters
    ----------
    command : list or tuple
        Command to execute when the job is started. Similar to who you would
        specify the command to `Popen`.
    terminateCallback : callable
        Callback function to call when the process exits. This can be used to
        inform the application that the subprocess is done.
    inputCallback : callable
        Callback function called when `poll` is invoked and the input pipe has
        data. Data is passed to the first argument of the callable object.
    errorCallback : callable
        Callback function called when `poll` is invoked and the error pipe has
        data. Data is passed to the first argument of the callable object. You
        may set `inputCallback` and `errorCallback` using the same function.
    extra : dict or None
        Dict of extra variables to be accessed by callback functions, use None
        for a blank dict.

    Examples
    --------
    Spawn a new subprocess::

        # command to execute
        command = 'python3 myScript.py'
        # create a new job object
        job = Job(command, flags=EXEC_ASYNC)
        # start it
        pid = job.start()  # returns a PID for the sub process

    """
    def __init__(self, parent, command='', terminateCallback=None,
                 inputCallback=None, errorCallback=None, extra=None):
        # use the app instance if parent isn't given
        if parent is None:
            from psychopy.app import getAppInstance
            parent = getAppInstance()
        # command to be called, cannot be changed after spawning the process
        self.parent = parent
        self._command = command
        self._pid = None
        # self._flags = flags  # unused right now
        self._process = None
        # self._pollMillis = None
        # self._pollTimer = wx.Timer()

        # user defined callbacks
        self._inputCallback = None
        self._errorCallback = None
        self._terminateCallback = None
        self.inputCallback = inputCallback
        self.errorCallback = errorCallback
        self.terminateCallback = terminateCallback
        # user defined additional info
        if extra is None:
            extra = {}
        self.extra = extra

        # non-blocking pipe reading threads and FIFOs
        self._stdoutReader = None
        self._stderrReader = None

    def start(self, cwd=None, env=None):
        """Start the subprocess.

        Parameters
        ----------
        cwd : str or None
            Working directory for the subprocess. Leave `None` to use the same
            as the application.
        env : dict or None
            Environment variables to pass to the subprocess. Leave `None` to
            use the same as the application.

        Returns
        -------
        int
            Process ID assigned by the operating system.

        """
        # NB - keep these lines since we will use them once the bug in
        # `wx.Execute` is fixed.
        #
        # create a new process object, this handles streams and stuff
        # self._process = wx.Process(None, -1)
        # self._process.Redirect()  # redirect streams from subprocess

        # start the sub-process
        command = self._command

        # # subprocess inherits the environment of the parent process
        if env is None:  
            scriptEnv = os.environ.copy()
        else:
            scriptEnv = env

        # remove some environment variables that can cause issues
        if 'PYTHONSTARTUP' in scriptEnv:
            del scriptEnv['PYTHONSTARTUP']

        # Set encoding for text mode pipes, needs to be explicitly set or we 
        # crash on windows
        scriptEnv['PYTHONIOENCODING'] = 'utf-8'
        if sys.platform == 'win32':
            scriptEnv['PYTHONLEGACYWINDOWSSTDIO'] = 'utf-8'

        try:
            self._process = Popen(
                args=command,
                bufsize=1,
                executable=None,
                stdin=None,
                stdout=PIPE,
                stderr=PIPE,
                preexec_fn=None,
                shell=False,
                cwd=cwd,
                env=scriptEnv,
                # universal_newlines=True,  # gives us back a string instead of bytes
                creationflags=0,
                text=False,
                encoding='utf-8'
            )
        except FileNotFoundError:
            return -1  # negative PID means failure

        # get the PID
        self._pid = self._process.pid

        # setup asynchronous readers of the subprocess pipes
        self._stdoutReader = PipeReader(self._process.stdout)
        self._stderrReader = PipeReader(self._process.stderr)
        self._stdoutReader.start()
        self._stderrReader.start()

        # bind the event called when the process ends
        # self._process.Bind(wx.EVT_END_PROCESS, self.onTerminate)
        self.parent.Bind(wx.EVT_IDLE, self.poll)

        return self._pid

    def terminate(self):
        """Terminate the subprocess associated with this object.

        Return
        ------
        bool
            `True` if the terminate call was successful in ending the
            subprocess. If `False`, something went wrong and you should try and
            figure it out.

        """
        if not self.isRunning:
            return False  # nop

        self.parent.Unbind(wx.EVT_IDLE)

        # isOk = wx.Process.Kill(self._pid, signal, flags) is wx.KILL_OK
        self._process.kill()  # kill the process
        #self._pollTimer.Stop()

        # Wait for the process to exit completely, return code will be incorrect
        # if we don't.
        if self._process is not None:
            processStillRunning = True
            while processStillRunning:
                wx.Yield()  # yield to the GUI main loop
                if self._process is None:
                    processStillRunning = False
                    continue

                processStillRunning = self._process.poll() is None
                time.sleep(0.1)  # sleep a bit to avoid CPU over-utilization

            # get the return code of the subprocess
            retcode = self._process.returncode
        else:
            retcode = 0

        self.onTerminate(retcode)

        return retcode is None

    @property
    def command(self):
        """Shell command to execute (`list`). Same as the `command` argument.
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
        """Subprocess execution option flags (`int`).
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

    # def setPriority(self, priority):
    #     """Set the subprocess priority. Has no effect if the process has not
    #     been started.
    #
    #     Parameters
    #     ----------
    #     priority : int
    #         Process priority from 0 to 100, where 100 is the highest. Values
    #         will be clipped between 0 and 100.
    #
    #     """
    #     if self._process is None:
    #         return
    #
    #     priority = max(min(int(priority), 100), 0)  # clip range
    #     self._process.SetPriority(priority)  # set it

    @property
    def inputCallback(self):
        """Callback function called when data is available on the input stream
        pipe (`callable` or `None`).
        """
        return self._inputCallback

    @inputCallback.setter
    def inputCallback(self, val):
        self._inputCallback = val

    @property
    def errorCallback(self):
        """Callback function called when data is available on the error stream
        pipe (`callable` or `None`).
        """
        return self._errorCallback

    @errorCallback.setter
    def errorCallback(self, val):
        self._errorCallback = val

    @property
    def terminateCallback(self):
        """Callback function called when the subprocess is terminated
        (`callable` or `None`).
        """
        return self._terminateCallback

    @terminateCallback.setter
    def terminateCallback(self, val):
        self._terminateCallback = val

    # @property
    # def pollMillis(self):
    #     """Polling interval for input and error pipes (`int` or `None`).
    #     """
    #     return self._pollMillis

    # @pollMillis.setter
    # def pollMillis(self, val):
    #     if isinstance(val, (int, float)):
    #         self._pollMillis = int(val)
    #     elif val is None:
    #         self._pollMillis = None
    #     else:
    #         raise TypeError("Value must be must be `int` or `None`.")
    #
    #     if not self._pollTimer.IsRunning():
    #         return
    #
    #     if self._pollMillis is None:  # if `None`, stop the timer
    #         self._pollTimer.Stop()
    #     else:
    #         self._pollTimer.Start(self._pollMillis, oneShot=wx.TIMER_CONTINUOUS)

    #   ~~~
    #   NB - Keep these here commented until wxPython fixes the `env` bug with
    #   `wx.Execute`. Hopefully someday we can use that again and remove all
    #   this stuff with threads which greatly simplifies this class.
    #   ~~~
    #
    # @property
    # def isOutputAvailable(self):
    #     """`True` if the output pipe to the subprocess is opened (therefore
    #     writeable). If not, you cannot write any bytes to 'outputStream'. Some
    #     subprocesses may signal to the parent process that its done processing
    #     data by closing its input.
    #     """
    #     if self._process is None:
    #         return False
    #
    #     return self._process.IsInputOpened()
    #
    # @property
    # def outputStream(self):
    #     """Handle to the file-like object handling the standard output stream
    #     (`ww.OutputStream`). This is used to write bytes which will show up in
    #     the 'stdin' pipe of the subprocess.
    #     """
    #     if not self.isRunning:
    #         return None
    #
    #     return self._process.OutputStream

    @property
    def isInputAvailable(self):
        """Check if there are bytes available to be read from the input stream
        (`bool`).
        """
        if self._process is None:
            return False

        return self._stdoutReader.isAvailable

    def getInputData(self):
        """Get any new data which has shown up on the input pipe (stdout of the
        subprocess).

        Returns
        -------
        str
            Data as a string. Returns and empty string if there is no new data.

        """
        if self._process is None:
            return

        if self._stdoutReader.isAvailable:
            return self._stdoutReader.read()

        return ''

    # @property
    # def inputStream(self):
    #     """Handle to the file-like object handling the standard input stream
    #     (`wx.InputStream`). This is used to read bytes which the subprocess is
    #     writing to 'stdout'.
    #     """
    #     if not self.isRunning:
    #         return None
    #
    #     return self._process.InputStream

    @property
    def isErrorAvailable(self):
        """Check if there are bytes available to be read from the error stream
        (`bool`).
        """
        if self._process is None:
            return False

        return self._stderrReader.isAvailable

    def getErrorData(self):
        """Get any new data which has shown up on the error pipe (stderr of the
        subprocess).

        Returns
        -------
        str
            Data as a string. Returns and empty string if there is no new data.

        """
        if self._process is None:
            return

        if self._stderrReader.isAvailable:
            return self._stderrReader.read()

        return ''

    # @property
    # def errorStream(self):
    #     """Handle to the file-like object handling the standard error stream
    #     (`wx.InputStream`). This is used to read bytes which the subprocess is
    #     writing to 'stderr'.
    #     """
    #     if not self.isRunning:
    #         return None
    #
    #     return self._process.ErrorStream

    def _readPipes(self):
        """Read data available on the pipes."""
        # get data from pipes
        if self.isInputAvailable:
            stdinText = self.getInputData()
            if self._inputCallback is not None:
                wx.CallAfter(self._inputCallback, stdinText)

        if self.isErrorAvailable:
            stderrText = self.getErrorData()
            if self._errorCallback is not None:
                wx.CallAfter(self._errorCallback, stderrText)

    def poll(self, evt=None):
        """Poll input and error streams for data, pass them to callbacks if
        specified. Input stream data is processed before error.
        """
        if self._process is None:  # do nothing if there is no process
            return

        # poll the subprocess
        retCode = self._process.poll()
        if retCode is not None:  # process has exited?
            # unbind the idle loop used to poll the subprocess
            self.parent.Bind(wx.EVT_IDLE, None)
            time.sleep(0.1)  # give time for pipes to flush
            wx.CallAfter(self.onTerminate, retCode)

        # get data from pipes
        self._readPipes()

    def onTerminate(self, exitCode):
        """Called when the process exits.

        Override for custom functionality. Right now we're just stopping the
        polling timer, doing a final `poll` to empty out the remaining data from
        the pipes and calling the user specified `terminateCallback`.

        If there is any data left in the pipes, it will be passed to the
        `_inputCallback` and `_errorCallback` before `_terminateCallback` is
        called.

        """
        # if self._pollTimer.IsRunning():
        #     self._pollTimer.Stop()

        self._readPipes()  # read remaining data

        # catch remaining data
        for i, p in enumerate((self._stdoutReader, self._stderrReader)):
            subprocPipeFd = p.stop()
            subprocPipeFd.flush()
            pipeBytes = subprocPipeFd.read()
            wx.CallAfter(
                self._inputCallback if i == 0 else self._errorCallback,
                pipeBytes)

        # flush remaining bytes, write out
        self._stdoutReader.join(timeout=1)
        self._stderrReader.join(timeout=1)

        # if callback is provided, else nop
        if self._terminateCallback is not None:
            wx.CallAfter(self._terminateCallback, self._pid, exitCode)

        self._process = self._pid = None  # reset
        # self._flags = 0

    # def onNotify(self):
    #     """Called when the polling timer elapses.
    #
    #     Default action is to read input and error streams and broadcast any data
    #     to user defined callbacks (if `poll()` has not been overwritten).
    #     """
    #     self.poll()

    def __del__(self):
        """Called when the object is garbage collected or deleted."""
        try:
            if hasattr(self, '_process'):
                if self._process is not None:
                    self._process.kill()
        except (ValueError, AttributeError):
            pass


if __name__ == "__main__":
    pass
