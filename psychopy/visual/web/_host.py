#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Starting and talking to the web browser server process.

One server runs the pages of all the `WebBrowserStim`s in a process. It is
started when the first is made (or by `psychopy.visual.web.preload`) and kept
until the process exits, as starting it takes a moment.
"""

import atexit
import collections
import itertools
import os
import secrets
import shlex
import subprocess
import sys
import threading
import time
import weakref
from multiprocessing.connection import Listener

import psutil

from psychopy import logging
from . import _gpushare, _protocol, _watchdog

__all__ = [
    'BrowserHost',
    'ViewChannel',
    'killOrphanedWebServers',
    'SERVER_PATH'
]

SERVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           _watchdog.SERVER_SCRIPT)

# seconds to wait for the server to start and connect
START_TIMEOUT = 30.0

# environment variable which turns sharing frames on the GPU off when '0',
# 'off', 'false' or 'no'
ENV_GPU_SHARING = 'PSYCHOPY_WEB_GPU_SHARING'


def gpuSharingAllowed():
    """Whether frames may be shared on the GPU here (`bool`): on Linux and
    Windows (the platforms it is done on), unless the environment turns it
    off."""
    if not _protocol.GPU_SHARING_PLATFORM:
        return False
    value = os.environ.get(ENV_GPU_SHARING, '').strip().lower()
    return value not in ('0', 'off', 'false', 'no')


def _unquote(arg):
    """Remove the quotes around an argument, if it is quoted."""
    if len(arg) >= 2 and arg[0] == arg[-1] and arg[0] in '"\'':
        return arg[1:-1]
    return arg


class WebServerError(RuntimeError):
    """The web browser server couldn't be started, or has stopped."""


def killOrphanedWebServers():
    """Stop web browser servers left running after the process that started
    them exited.

    Servers normally exit by themselves when that happens, this covers those
    that couldn't. Servers of processes still running are left alone.

    Returns
    -------
    list of int
        Process IDs of the servers stopped.

    """
    orphans = []
    ownPid = os.getpid()
    for proc in psutil.process_iter(['cmdline', 'create_time'], ad_value=None):
        if proc.pid == ownPid:
            continue
        parentPid = _watchdog.parseServerCmdline(proc.info['cmdline'])
        if parentPid is None or parentPid == ownPid:
            continue
        if _watchdog.isProcessGone(parentPid,
                                   createdBefore=proc.info['create_time']):
            orphans.append(proc)

    if orphans:
        # they may be exiting already
        _, alive = psutil.wait_procs(orphans, timeout=3)
        for proc in alive:
            try:
                proc.kill()
            except psutil.Error:
                pass
        logging.warning("Stopped orphaned web browser server process(es): "
                        "{}".format([proc.pid for proc in orphans]))

    return [proc.pid for proc in orphans]


class ViewChannel:
    """Messages to and from one page on the server.

    Messages from the server are queued by the host's reader thread and taken
    by the stimulus with `receive`, on its own thread.

    Parameters
    ----------
    host : BrowserHost
        Host of the server the page is on.
    viewId : int
        ID of the page.

    """
    def __init__(self, host, viewId):
        self.host = host
        self.id = viewId
        self.inbox = collections.deque()
        self.closed = False

    def send(self, op, **msg):
        """Send a message about this page to the server.

        Returns
        -------
        bool
            `False` if it couldn't be sent, as the page or server has gone.

        """
        if self.closed:
            return False
        return self.host.send(op=op, view=self.id, **msg)

    def receive(self):
        """Take the messages received since last called.

        Returns
        -------
        list of dict
            Messages, oldest first.

        """
        messages = []
        inbox = self.inbox
        while inbox:
            messages.append(inbox.popleft())
        return messages

    def close(self):
        """Close the page on the server, may be called from any thread."""
        if self.closed:
            return
        self.send('close')
        self.closed = True
        self.host.removeChannel(self)


class BrowserHost:
    """A web browser server process and the connection to it.

    Use `BrowserHost.get()` to get the one for this process.

    """
    _instance = None
    _instanceLock = threading.Lock()

    def __init__(self, platform=None):
        self.platform = platform or os.environ.get(
            'PSYCHOPY_WEB_PLATFORM', 'auto')
        self.proc = None
        self.conn = None
        self.info = {}
        self.alive = False
        self._sendLock = threading.Lock()
        self._channels = {}
        self._channelsLock = threading.Lock()
        self._ids = itertools.count(1)
        self._replies = collections.deque()
        self._replied = threading.Condition()
        self._logFile = None
        self._start()

    @classmethod
    def get(cls):
        """Get the host for this process, starting the server if it isn't
        running.

        Returns
        -------
        BrowserHost

        Raises
        ------
        WebServerError
            If the server can't be started.

        """
        with cls._instanceLock:
            if cls._instance is None or not cls._instance.alive:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def current(cls):
        """Get the host for this process if its server is running, without
        starting one (`BrowserHost` or `None`)."""
        host = cls._instance
        return host if host is not None and host.alive else None

    def _logPath(self):
        try:
            from psychopy.preferences import prefs
            folder = prefs.paths['userPrefsDir']
        except Exception:
            import tempfile
            folder = tempfile.gettempdir()
        return os.path.join(folder, 'web_browser_last_session.log')

    def _command(self):
        cmd = os.environ.get(_protocol.ENV_SERVER_CMD)
        if cmd:
            if os.name == 'posix':
                return shlex.split(cmd)
            # non-POSIX splitting keeps quotes (so backslashes in paths
            # survive), which `Popen` would then pass on as part of them
            return [_unquote(arg) for arg in shlex.split(cmd, posix=False)]
        return [sys.executable, SERVER_PATH, '--platform', self.platform,
                '--gpu', 'auto' if gpuSharingAllowed() else 'off']

    def _start(self):
        killOrphanedWebServers()
        authkey = secrets.token_bytes(32)
        # a private socket on POSIX, a named pipe on Windows
        listener = Listener(authkey=authkey)
        address = listener.address
        cmd = self._command() + [
            '--address', address, '--parent-pid', str(os.getpid())]
        env = dict(os.environ)
        env[_protocol.ENV_AUTHKEY] = authkey.hex()
        logPath = self._logPath()
        self._logFile = open(logPath, 'wb')
        kwargs = {}
        if sys.platform == 'win32':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        t0 = time.perf_counter()
        # output goes to a log file, not a pipe PsychoPy Studio reads, which
        # breaks when the experiment is stopped
        self.proc = subprocess.Popen(
            cmd, env=env, stdin=subprocess.DEVNULL, stdout=self._logFile,
            stderr=subprocess.STDOUT, **kwargs)

        # accept on another thread, so we can give up if the server exits
        accepted = []

        def accept():
            try:
                accepted.append(listener.accept())
            except Exception as err:
                accepted.append(err)

        acceptThread = threading.Thread(target=accept, daemon=True)
        acceptThread.start()
        while not accepted:
            if self.proc.poll() is not None:
                break
            if time.perf_counter() - t0 > START_TIMEOUT:
                break
            acceptThread.join(0.05)
        try:
            if not accepted or isinstance(accepted[0], Exception):
                self._fail("The web browser server didn't connect", logPath)
            self.conn = accepted[0]
            _protocol.makeBlocking(self.conn)  # see `makeBlocking`
            # first message is `hello`, or `fatal` if it can't start
            remaining = START_TIMEOUT - (time.perf_counter() - t0)
            if not self.conn.poll(max(remaining, 1.0)):
                self._fail("The web browser server didn't start", logPath)
            msg = _protocol.unpack(self.conn.recv_bytes())
        except (EOFError, OSError):
            self._fail("The web browser server exited", logPath)
        finally:
            listener.close()

        if msg.get('op') == 'fatal':
            self._fail(msg.get('error', 'unknown error'), logPath)
        if msg.get('op') != 'hello' or \
                msg.get('protocol') != _protocol.PROTOCOL_VERSION:
            self._fail("Unexpected reply from the web browser server: "
                       "{}".format(msg), logPath)
        self.info = msg
        self.alive = True
        logging.info(
            "Started web browser server (pid {}) in {:.2f} s: {}".format(
                msg.get('pid'), time.perf_counter() - t0, msg.get('versions')))
        threading.Thread(target=self._read, name='webHostReader',
                         daemon=True).start()

    def _fail(self, problem, logPath):
        self._kill()
        tail = ''
        try:
            with open(logPath, 'rb') as f:
                lines = f.read().decode('utf-8', 'replace').strip().splitlines()
            if lines:
                tail = '\n' + '\n'.join(lines[-15:])
        except OSError:
            pass
        raise WebServerError("{} (see {}).{}".format(problem, logPath, tail))

    def _read(self):
        """Route messages from the server to their pages (on its own thread).
        """
        try:
            while True:
                msg = _protocol.unpack(self.conn.recv_bytes())
                # handles it passes: file descriptors sent right after it, or
                # Windows handles copied into this process
                if msg.get('nfds'):
                    msg['fds'] = _protocol.recvFds(self.conn, msg['nfds'])
                elif msg.get('handles'):
                    msg['fds'] = msg.pop('handles')
                viewId = msg.get('view')
                if viewId is None:
                    with self._replied:
                        self._replies.append(msg)
                        self._replied.notify_all()
                    continue
                channel = self._channels.get(viewId)
                if channel is not None:
                    channel.inbox.append(msg)
                else:  # its page has closed
                    _gpushare.closeHandles(msg.get('fds', ()))
        except (EOFError, OSError):
            pass
        self.alive = False
        with self._channelsLock:
            channels = list(self._channels.values())
        for channel in channels:
            channel.inbox.append({'op': 'serverGone', 'view': channel.id})
        if self.proc is not None and self.proc.poll() is None:
            # closed the connection without exiting, e.g. stuck
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self._kill()

    def send(self, **msg):
        """Send a message to the server, from any thread.

        Returns
        -------
        bool
            `False` if the server has gone.

        """
        if not self.alive:
            return False
        data = _protocol.pack(msg)
        with self._sendLock:
            try:
                self.conn.send_bytes(data)
            except (OSError, ValueError):
                self.alive = False
                return False
        return True

    def openChannel(self):
        """Make a channel for a new page (see `ViewChannel`)."""
        channel = ViewChannel(self, next(self._ids))
        with self._channelsLock:
            self._channels[channel.id] = channel
        return channel

    def removeChannel(self, channel):
        with self._channelsLock:
            self._channels.pop(channel.id, None)

    def ping(self, timeout=5.0):
        """Check the server is responding.

        Returns
        -------
        bool
            `True` if it replied within `timeout` seconds.

        """
        pingId = secrets.randbits(31)
        if not self.send(op='ping', id=pingId):
            return False
        deadline = time.perf_counter() + timeout
        with self._replied:
            while True:
                for msg in list(self._replies):
                    if msg.get('op') == 'pong' and msg.get('id') == pingId:
                        self._replies.remove(msg)
                        return True
                remaining = deadline - time.perf_counter()
                if remaining <= 0 or not self.alive:
                    return False
                self._replied.wait(remaining)

    def _kill(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.kill()
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                pass

    def shutdown(self, timeout=3.0):
        """Close all pages and stop the server."""
        if self.proc is None:
            return
        self.send(op='shutdown')
        try:
            self.proc.wait(timeout)
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            try:
                self.proc.wait(2)
            except subprocess.TimeoutExpired:
                self._kill()
        self.alive = False
        try:
            self.conn.close()
        except Exception:
            pass
        if self._logFile is not None:
            self._logFile.close()
            self._logFile = None
        if BrowserHost._instance is self:
            BrowserHost._instance = None


@atexit.register
def _shutdownHost():
    host = BrowserHost._instance
    if host is not None:
        try:
            host.shutdown()
        except Exception:
            pass


class WindowPump:
    """Calls each web stimulus drawn in a window once per flip, so they handle
    messages (and pass on input) even when not drawn.

    Registered as one of the window's event dispatchers, which hold strong
    references, so it holds the stimuli weakly and removes itself once they
    have all gone.

    Parameters
    ----------
    win : psychopy.visual.Window
        The window.

    """
    def __init__(self, win):
        self.win = weakref.ref(win)
        self.stims = weakref.WeakSet()

    @classmethod
    def forWindow(cls, win):
        """Get the pump of a window, adding one if it has none."""
        for dispatcher in win._eventDispatchers:
            if isinstance(dispatcher, cls):
                return dispatcher
        pump = cls(win)
        win._eventDispatchers.append(pump)
        return pump

    def add(self, stim):
        self.stims.add(stim)

    def remove(self, stim):
        self.stims.discard(stim)
        if not self.stims:
            self._unregister()

    def _unregister(self):
        win = self.win()
        if win is not None:
            try:
                win._eventDispatchers.remove(self)
            except ValueError:
                pass

    def dispatch_events(self):
        # errors here would be taken by the backend as a sign this has no
        # `dispatch_events`, so stop them here
        try:
            stims = list(self.stims)
            if not stims:
                self._unregister()
                return
            for stim in stims:
                stim._pumpGL()
        except Exception as err:
            logging.error("Error updating web browser stimuli: {}".format(err))
