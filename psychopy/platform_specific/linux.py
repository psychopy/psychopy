#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Placeholder for adding c (or ctypes) extensions to PsychoPy on linux.
"""
from psychopy import logging
import sys
try:
    import ctypes
    import ctypes.util
    c = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))
    importCtypesFailed = False
except Exception:
    importCtypesFailed = True
    logging.debug("rush() not available because import ctypes, ctypes.util "
                  "failed in psychopy/platform_specific/linux.py")

# FIFO and RR(round-robin) allow highest priority for realtime
SCHED_NORMAL = 0
SCHED_FIFO = 1
SCHED_RR = 2
SCHED_BATCH = 3

if not importCtypesFailed:
    class _SchedParams(ctypes.Structure):
        _fields_ = [('sched_priority', ctypes.c_int)]

# Text that appears at the top of the dialog with provides instructions to the
# user.
_introStr = (
    u"Could not set the thread priority with sched_setscheduler.\n"
    u"For optimal performance on Linux, Psychtoolbox requires additional\n"
    u"configuration changes to be made to this system by entering the\n"
    u"following commands into your terminal:\n\n{cmdstr}"
)

# config file path
_confPath = u"/etc/security/limits.d/99-psychopylimits.conf"

# these are the commands we want the user to run in their terminal
_cmdStr = (
    u"sudo groupadd --force psychopy\n\n"
    u"sudo usermod -a -G psychopy $USER\n\n"
    u"sudo gedit {fpath}\n"
    u"@psychopy - nice -20\n"
    u"@psychopy - rtprio 50\n"
    u"@psychopy - memlock unlimited")
warnMax = _introStr.format(cmdstr=_cmdStr.format(fpath=_confPath))

def rush(value=True, realtime=False):
    """Raise the priority of the current thread/process using
        - sched_setscheduler

    realtime arg is not used in Linux implementation.

    NB for rush() to work on Linux requires that the script is run by
    a user with sufficient permissions to raise the priority of a process.
    In PsychoPy, we suggest adding the user to a group with these permissions.

    If this function returns `False`, see the log for instructions on how
    to set up such a group.
    """
    if importCtypesFailed:
        return False

    schedParams = _SchedParams()
    sched = SCHED_RR if value else SCHED_NORMAL
    schedParams.sched_priority = c.sched_get_priority_min(sched)
    err = c.sched_setscheduler(0, sched, ctypes.byref(schedParams))
    if err == -1:
        logging.warning(warnMax)

    return not err
