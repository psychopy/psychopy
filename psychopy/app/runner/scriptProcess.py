import wx
import sys
import time
from queue import Queue
from subprocess import Popen, PIPE
from threading import Thread
from pathlib import Path

try:
    FileNotFoundError
except NameError:
    # Py2 has no FileNotFoundError
    FileNotFoundError = IOError


class OutputThread(Thread):
    """Thread class for collecting standard stream data."""

    def __init__(self, proc):
        Thread.__init__(self)
        self.proc = proc
        self.queue = Queue()
        self.daemon = True
        self.exit = False

    def run(self):
        """Start the thread."""
        running = self.doCheck()  # block until process ends

    def doCheck(self):
        # will do the next line repeatedly until finds EOL
        # after checking each line check if we should quit
        try:
            for line in iter(self.proc.stdout.readline, b''):
                # this runs repeatedly
                self.queue.put(line)
                if not line:
                    break
        except ValueError:
            return False
            # then check if the process ended
            # self.exit
        for line in self.proc.stderr.readlines():
            self.queue.put(line)
            if not line:
                break
        return True

    def getBuffer(self):
        """Retrieve all lines currently in buffer."""
        lines = ''
        while not self.queue.empty():
            lines += self.queue.get_nowait()
        return lines


class ScriptProcess(object):
    """Class to run script through subprocess."""

    def __init__(self, app):
        self.app = app
        self.scriptProcess = None
        self._stdoutThread = None
        self.Bind(wx.EVT_END_PROCESS, self.onProcessEnded)

    def runFile(self, event=None, fileName=None):
        """Begin new process to run experiment."""
        fullPath = fileName.replace('.psyexp', '_lastrun.py')
        wx.BeginBusyCursor()

        # provide a running... message
        self.app.runner.stdOut.write((u"## Running: {} ##".format(fullPath)).center(80, "#")+"\n")
        self.app.runner.stdOut.lenLastRun = len(self.app.runner.stdOut.getText())

        if sys.platform == 'win32':
            # the quotes allow file paths with spaces
            command = [sys.executable, '-u', fullPath]
            if hasattr(wx, "EXEC_NOHIDE"):
                _opts = wx.EXEC_ASYNC | wx.EXEC_NOHIDE  # that hid console!
            else:
                _opts = wx.EXEC_ASYNC | wx.EXEC_SHOW_CONSOLE
        else:
            command = [sys.executable, '-u', fullPath]
            _opts = wx.EXEC_ASYNC | wx.EXEC_MAKE_GROUP_LEADER

        fullPathDir = str(Path(fullPath).parent)  # for cwd the file path - JK
        # the whileRunning method will check on stdout from the script
        self._processEndTime = None
        self.scriptProcess = Popen(
            args=command,
            bufsize=1, executable=None, stdin=None,
            stdout=PIPE, stderr=PIPE, preexec_fn=None,
            shell=False, cwd=fullPathDir, env=None,
            universal_newlines=True,  # gives us back a string instead of bytes
            creationflags=0,
        )
        # this part creates a non-blocking thread to check the stdout/err
        self._stdoutThread = OutputThread(self.scriptProcess)
        self._stdoutThread.start()
        self.Bind(wx.EVT_IDLE, self.whileRunningFile)

    def stopFile(self, event=None):
        """Kill script processes"""
        self.app.terminateHubProcess()
        if self.scriptProcess:
            self.scriptProcess.kill()
        self.onProcessEnded()

    def whileRunningFile(self, event=None):
        """
        This is an Idle function while study is running.

        Check on process and handle stdout.
        """
        newOutput = self._stdoutThread.getBuffer()
        if newOutput:
            sys.stdout.write(newOutput)
        returnVal = self.scriptProcess.poll()
        if returnVal is not None:
            self.onProcessEnded()
        else:
            time.sleep(0.1)  # let's not check too often

    def onProcessEnded(self, event=None):
        """Perform when script has finished running."""
        try:
            wx.EndBusyCursor()
        except wx._core.wxAssertionError:
            pass
        self._stdoutThread.exit = True
        time.sleep(0.1)  # give time for the buffers to finish writing?
        buff = self._stdoutThread.getBuffer()
        self.app.runner.stdOut.write(buff)
        self.app.runner.stdOut.flush()
        self.app.runner.Show()

        self.scriptProcess = None
        self.Bind(wx.EVT_IDLE, None)
        print("##### Experiment ended. #####\n")
