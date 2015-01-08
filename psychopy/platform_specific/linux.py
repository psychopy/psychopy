# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).
"""
placeholder for adding c (or ctypes) extensions to the linux PsychoPy
"""
from psychopy import logging
import sys
try:
    import ctypes, ctypes.util
    c = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))
    importCtypesFailed = False
except:
    importCtypesFailed = True
    logging.debug("rush() not available because import ctypes, ctypes.util failed in ext/linux.py")

#FIFO and RR(round-robin) allow highest priority for realtime
SCHED_NORMAL=0
SCHED_FIFO  =1
SCHED_RR    =2
SCHED_BATCH =3

if not importCtypesFailed:
    class _SchedParams(ctypes.Structure):
        _fields_ = [('sched_priority', ctypes.c_int)]#

def rush(value=True, realtime=False):
    """Raise the priority of the current thread/process using
        - sched_setscheduler

    realtime arg is not used in linux implementation.

    NB for rush() to work on (debian-based?) linux requires that the script is run using a copy of python that
    is allowed to change priority, eg: sudo setcap cap_sys_nice=eip <sys.executable>, and maybe restart PsychoPy.
    If <sys.executable> is the system python, its important to restore it back to normal to avoid possible
    side-effects. Alternatively, use a different python executable, and change its cap_sys_nice.

    For RedHat-based systems, 'sudo chrt ...' at run-time might be needed instead, not sure.
    see http://rt.et.redhat.com/wiki/images/8/8e/Rtprio.pdf
    """
    if importCtypesFailed: return False

    if value:#set to RR with max priority
        schedParams = _SchedParams()
        schedParams.sched_priority = c.sched_get_priority_max(SCHED_RR)
        err = c.sched_setscheduler(0,SCHED_RR, ctypes.byref(schedParams))
        if err==-1:#returns 0 if OK
            logging.warning("""Could not raise thread priority with sched_setscheduler.
To enable rush(), if you are using a debian-based linux, try this in a terminal window:
  'sudo setcap cap_sys_nice=eip %s'  [NB: You may need to install 'setcap' first.]
If you are using the system's python (eg /usr/bin/python2.x), its highly recommended
to change cap_sys_nice back to normal afterwards:
  'sudo setcap cap_sys_nice= %s'""" % (sys.executable,sys.executable))
    else:#set to RR with normal priority
        schedParams = _SchedParams()
        schedParams.sched_priority = c.sched_get_priority_min(SCHED_NORMAL)
        err = c.sched_setscheduler(0,SCHED_NORMAL, ctypes.byref(schedParams))
        if err==-1:#returns 0 if OK
            logging.warning("""Failed to set thread priority back to normal level with sched_setscheduler.
Try:  'sudo setcap cap_sys_nice= %s'""" % (sys.executable))

    return True



