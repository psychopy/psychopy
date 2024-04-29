#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
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

warnMax = """Could not raise thread priority with sched_setscheduler.

To enable rush(), if you are using a debian-based Linux, try this:
  'sudo setcap cap_sys_nice=eip %s'  [NB: install 'setcap' first.]
If you are using the system's python (eg /usr/bin/python2.x), its highly
recommended to change cap_sys_nice back to normal afterwards:
  'sudo setcap cap_sys_nice= %s'"""

warnNormal = ("Failed to set thread priority to normal with "
              "sched_setscheduler.\n"
              "Try:  'sudo setcap cap_sys_nice= %s'")


def rush(value=True, realtime=False):
    """Raise the priority of the current thread/process using
        - sched_setscheduler

    realtime arg is not used in Linux implementation.

    NB for rush() to work on (debian-based?) Linux requires that the
    script is run using a copy of python that is allowed to change
    priority, eg: sudo setcap cap_sys_nice=eip <sys.executable>,
    and maybe restart PsychoPy. If <sys.executable> is the system python,
    it's important to restore it back to normal to avoid possible
    side-effects. Alternatively, use a different python executable,
    and change its cap_sys_nice.

    For RedHat-based systems, 'sudo chrt ...' at run-time might be
    needed instead, not sure.
    see http://rt.et.redhat.com/wiki/images/8/8e/Rtprio.pdf
    """
    if importCtypesFailed:
        return False

    if value:  # set to RR with max priority
        schedParams = _SchedParams()
        schedParams.sched_priority = c.sched_get_priority_max(SCHED_RR)
        err = c.sched_setscheduler(0, SCHED_RR, ctypes.byref(schedParams))
        if err == -1:  # returns 0 if OK
            logging.warning(warnMax % (sys.executable, sys.executable))
    else:  # set to RR with normal priority
        schedParams = _SchedParams()
        schedParams.sched_priority = c.sched_get_priority_min(SCHED_NORMAL)
        err = c.sched_setscheduler(0, SCHED_NORMAL, ctypes.byref(schedParams))
        if err == -1:  # returns 0 if OK
            logging.warning(warnNormal % sys.executable)

    return True
