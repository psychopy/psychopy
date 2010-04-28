# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).
"""
placeholder for adding c (or ctypes) extensions to the linux PsychoPy
"""
from psychopy import log
try:
    import ctypes, ctypes.util
    c = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))
    importCtypesFailed = False
except:
    importCtypesFailed = True
    log.debug("rush() not available because import ctypes, ctypes.util failed in ext/linux.py")
    
#FIFO and RR(round-robin) allow highest priority for realtime
SCHED_NORMAL=0
SCHED_FIFO  =1
SCHED_RR    =2
SCHED_BATCH =3

if not importCtypesFailed:
    class _SchedParams(ctypes.Structure):
        _fields_ = [('sched_priority', ctypes.c_int)]#

def rush(value=True):    
    """Raise the priority of the current thread/process using 
        - sched_setscheduler
    
    NB for rush() to work on linux requires that the script is run as sudo
    """
    if importCtypesFailed: return False
    
    if value:#set to RR with max priority
        schedParams = _SchedParams()
        schedParams.sched_priority = c.sched_get_priority_max(SCHED_RR)
        err = c.sched_setscheduler(0,SCHED_RR, ctypes.byref(schedParams))
        if err==-1:#returns 0 if OK
            log.warning("Failed to raise thread priority with sched_setscheduler. You need to run as sudo in order for PsychoPy to rush()")
    else:#set to RR with max priority
        schedParams = _SchedParams()
        schedParams.sched_priority = c.sched_get_priority_min(SCHED_NORMAL)
        err = c.sched_setscheduler(0,SCHED_NORMAL, ctypes.byref(schedParams))
        if err==-1:#returns 0 if OK
            log.warning("Failed to set thread priority back to normal level with sched_setscheduler.")
    
    return True
        
  
  
