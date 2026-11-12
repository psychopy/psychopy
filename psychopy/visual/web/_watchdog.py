#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Detecting that the process that started the web browser server has gone.

The server normally exits when its connection to that process closes, but
processes can be killed without closing anything (e.g. stopping an experiment
from PsychoPy Studio), so the server also checks on it. This mirrors how ioHub
does the same (`psychopy.iohub.devices.Computer.isProcessGone`), without
importing PsychoPy, which the server doesn't.
"""

import os
import threading
import time

import psutil

__all__ = [
    'ORPHAN_EXIT_CODE',
    'SERVER_SCRIPT',
    'isProcessGone',
    'startParentWatchdog',
    'parseServerCmdline'
]

# exit code used when the server exits as the process that started it has gone
ORPHAN_EXIT_CODE = 3

# file name of the server script, which orphaned servers are found by
SERVER_SCRIPT = '_server.py'


def isProcessGone(pid, createdBefore=None):
    """Check whether a process has exited.

    Parameters
    ----------
    pid : int
        Process ID to check.
    createdBefore : float or None
        Time (seconds since the epoch) the process must have been created
        before, so a process created later (allowing a couple of seconds for
        clock adjustments) is taken as a different one given the same ID.

    Returns
    -------
    bool
        `True` if the process doesn't exist, is a zombie or its ID has been
        reused, `False` if it is running or can't be checked.

    """
    try:
        proc = psutil.Process(pid)
        if proc.status() == psutil.STATUS_ZOMBIE:
            return True
        if createdBefore is not None:
            return proc.create_time() > createdBefore + 2.0
        return False
    except psutil.NoSuchProcess:  # includes zombies
        return True
    except psutil.AccessDenied:
        return False


def startParentWatchdog(parentPid, onGone, interval=0.5, grace=None):
    """Start a thread which calls a function once the parent process has gone,
    then exits this process.

    Parameters
    ----------
    parentPid : int
        Process ID of the process that started this one.
    onGone : callable
        Called with no arguments once the parent has gone (e.g. to remove
        shared memory), from the watchdog thread. Exceptions are ignored.
    interval : float
        Seconds between checks.
    grace : float or None
        Seconds to wait after `onGone` returns before exiting, giving the
        normal shutdown (which closing the connection starts) a chance to
        finish. Defaults to the `PSYCHOPY_WEB_ORPHAN_GRACE` environment
        variable, or 3 seconds.

    Returns
    -------
    threading.Thread
        The watchdog thread.

    """
    if grace is None:
        grace = float(os.environ.get('PSYCHOPY_WEB_ORPHAN_GRACE', 3.0))
    ownCreated = psutil.Process().create_time()
    # a direct child is reparented once its parent goes (POSIX only), the
    # parent may not be the direct parent when started through a launcher
    directChild = os.name == 'posix' and os.getppid() == parentPid

    def isParentGone():
        if directChild and os.getppid() != parentPid:
            return True
        return isProcessGone(parentPid, createdBefore=ownCreated)

    def watch():
        while not isParentGone():
            time.sleep(interval)
        try:
            onGone()
        except BaseException:
            pass
        time.sleep(grace)
        # nothing else may be safe to use from here, e.g. stdout may be a pipe
        # with nothing reading it
        try:
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, 1)
            os.dup2(devnull, 2)
        except OSError:
            pass
        os._exit(ORPHAN_EXIT_CODE)

    thread = threading.Thread(target=watch, name='webParentWatchdog',
                              daemon=True)
    thread.start()

    return thread


def parseServerCmdline(cmdline):
    """Get the parent process ID from the command line of a web browser server
    process.

    Parameters
    ----------
    cmdline : list of str or None
        Command line arguments of a process.

    Returns
    -------
    int or None
        The parent process ID passed to the server, or `None` if `cmdline`
        isn't that of a server.

    """
    cmdline = list(cmdline or ())
    if not any(os.path.basename(arg) == SERVER_SCRIPT for arg in cmdline):
        return None
    try:
        pid = int(cmdline[cmdline.index('--parent-pid') + 1])
    except (ValueError, IndexError):
        return None

    return pid if pid > 0 else None
