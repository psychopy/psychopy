#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Web browser server process for `WebBrowserStim`.

Started by the stimulus (see `_host`) as a script, so it doesn't import
PsychoPy (which is slow and opens things a helper process shouldn't). It
connects back, sets up Qt for rendering pages off screen, then runs the pages
until told to shut down, the connection closes, or the process that started it
goes.

Usage::

    python _server.py --address ADDRESS --parent-pid PID [--platform PLATFORM]
                      [--gpu {auto,off}]

The connection's authentication key is passed (as hex) in the environment
variable named by `_protocol.ENV_AUTHKEY`.
"""

import argparse
import os
import queue
import signal
import sys
import threading

# siblings, importable as this directory is first on `sys.path`
import _gpushare
import _protocol
import _shm
import _watchdog

# Chromium throttles pages it thinks aren't visible, which unshown ones are
_CHROMIUM_FLAGS_ = [
    '--disable-background-timer-throttling',
    '--disable-renderer-backgrounding',
    '--disable-backgrounding-occluded-windows',
    '--disable-features=CalculateNativeWinOcclusion'
]


class Connection:
    """Sends messages to the stimulus' process from a thread of its own, so
    sending never blocks the Qt event loop.

    Parameters
    ----------
    conn : multiprocessing.connection.Connection
        Connection to the stimulus' process.
    pid : int or None
        ID of the stimulus' process, which handles are copied into on Windows.

    """
    def __init__(self, conn, pid=None):
        self.conn = conn
        self.pid = pid
        self._queue = queue.SimpleQueue()
        self._thread = threading.Thread(
            target=self._write, name='webServerWriter', daemon=True)
        self._thread.start()

    def send(self, fds=None, **msg):
        """Queue a message to send.

        Parameters
        ----------
        fds : list of int or None
            OS handles to pass with the message, which are closed once sent:
            file descriptors sent after it (see `_protocol.sendFds`), giving
            it an `nfds` field saying how many there are; or on Windows,
            handles copied into the stimulus' process, giving it a `handles`
            field with their values there.
        **msg
            The message.

        Raises
        ------
        OSError
            If handles can't be copied into the stimulus' process.

        """
        if fds and os.name == 'nt':
            try:
                msg['handles'] = _protocol.duplicateHandles(fds, self.pid)
            finally:
                _gpushare.closeHandles(fds)
            fds = None
        if fds:
            msg['nfds'] = len(fds)
        self._queue.put((_protocol.pack(msg), fds or ()))

    def _write(self):
        while True:
            item = self._queue.get()
            if item is None:
                return
            data, fds = item
            try:
                self.conn.send_bytes(data)
                if fds:
                    _protocol.sendFds(self.conn, fds)
            except (OSError, ValueError):  # the other end has gone
                return
            finally:
                _gpushare.closeHandles(fds)

    def close(self, timeout=2.0):
        """Send what is queued, then close the connection."""
        self._queue.put(None)
        self._thread.join(timeout)
        try:
            self.conn.close()
        except OSError:
            pass


def choosePlatform(requested):
    """Choose how Qt renders pages.

    Parameters
    ----------
    requested : str
        `'native'` uses the window system (fastest, needs a display),
        `'offscreen'` renders without one, in software. `'auto'` uses the window
        system if there is one.

    Returns
    -------
    str
        `'native'` or `'offscreen'`.

    """
    if requested in ('native', 'offscreen'):
        return requested
    if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
        return 'offscreen'
    return 'native'


def configureEnvironment(platform, environ=None, gpu='off'):
    """Set the environment variables Qt and Chromium read on starting.

    Parameters
    ----------
    platform : str
        `'native'` or `'offscreen'`, see `choosePlatform`.
    environ : dict or None
        Environment to change, defaults to `os.environ`.
    gpu : str
        `'auto'` if frames may be shared on the GPU, `'off'` if not.

    """
    env = os.environ if environ is None else environ
    # one frame pixel per page pixel (macOS Retina displays still double it,
    # which the stimulus allows for)
    env['QT_ENABLE_HIGHDPI_SCALING'] = '0'
    flags = env.get('QTWEBENGINE_CHROMIUM_FLAGS', '').split()
    flags += [f for f in _CHROMIUM_FLAGS_ if f not in flags]
    if platform == 'offscreen':
        env['QT_QPA_PLATFORM'] = 'offscreen'
        env['QT_QUICK_BACKEND'] = 'software'
        flags.append('--disable-gpu')
    elif sys.platform.startswith('linux'):
        # Qt grabs stale frames of unshown pages under Wayland, and PsychoPy's
        # windows use X11 (XWayland) anyway
        env['QT_QPA_PLATFORM'] = 'xcb'
    if gpu == 'auto' and sys.platform == 'win32':
        # frames are shared on the GPU with OpenGL (see `_qtgpu`), which Qt
        # Quick only renders with on Windows when asked (else Direct3D 11)
        env.setdefault('QSG_RHI_BACKEND', 'opengl')
    if sys.platform == 'darwin':
        # don't become a foreground app, with a Dock icon and focus
        env['QT_MAC_DISABLE_FOREGROUND_APPLICATION_TRANSFORM'] = '1'
    if sys.platform.startswith('linux') and os.geteuid() == 0:
        # Chromium's sandbox doesn't run as root (e.g. in Docker)
        env['QTWEBENGINE_DISABLE_SANDBOX'] = '1'
    env['QTWEBENGINE_CHROMIUM_FLAGS'] = ' '.join(flags)


def parseArgs(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--address', required=True,
                        help="Address of the stimulus' process to connect to")
    parser.add_argument('--parent-pid', type=int, required=True,
                        help="Process ID of the stimulus' process")
    parser.add_argument('--platform', default='auto',
                        choices=['auto', 'native', 'offscreen'],
                        help="How Qt renders pages")
    parser.add_argument('--gpu', default='auto', choices=['auto', 'off'],
                        help="Whether frames may be shared on the GPU")
    return parser.parse_args(argv)


def main(argv=None):
    args = parseArgs(argv)

    # the stimulus' process decides when to stop, Ctrl+C in a terminal goes to
    # it too, and it closes the connection
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # take the key out of the environment, so page processes don't get it
    authkey = bytes.fromhex(os.environ.pop(_protocol.ENV_AUTHKEY, ''))
    from multiprocessing.connection import Client
    conn = Connection(Client(args.address, authkey=authkey), args.parent_pid)

    _watchdog.startParentWatchdog(args.parent_pid, _shm.closeOwnedRings)

    platform = choosePlatform(args.platform)
    # sharing frames on the GPU needs a GPU to render with
    gpu = args.gpu
    if platform != 'native' or not _protocol.GPU_SHARING_PLATFORM:
        gpu = 'off'
    configureEnvironment(platform, gpu=gpu)
    try:
        import _qtbrowser
    except Exception as err:
        conn.send(op='fatal', error=(
            "Can't load the web browser ({}: {}). Install it with "
            "`pip install psychopy[web]`.".format(type(err).__name__, err)))
        conn.close()
        return 1

    try:
        return _qtbrowser.run(conn, platform, gpu)
    finally:
        _shm.closeOwnedRings()


if __name__ == "__main__":
    sys.exit(main())
