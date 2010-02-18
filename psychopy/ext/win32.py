# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""
There are no c extensions for windows at the moment - everything is done
from the pywin32 extensions.
"""
#these are correct for win32, not sure about 64bit versions
   #DEFINE NORMAL_PRIORITY_CLASS 32
   #DEFINE IDLE_PRIORITY_CLASS 64
   #DEFINE HIGH_PRIORITY_CLASS 128
   #DEFINE REALTIME_PRIORITY_CLASS 1600
    #define THREAD_PRIORITY_IDLE            -15
    #define THREAD_PRIORITY_LOWEST          -2
    #define THREAD_PRIORITY_BELOW_NORMAL    -1
    #define THREAD_PRIORITY_NORMAL          0
    #define THREAD_PRIORITY_ABOVE_NORMAL    1
    #define THREAD_PRIORITY_HIGHEST         2
    #define THREAD_PRIORITY_TIME_CRITICAL   15
    
from ctypes import windll
windll=windll.kernel32

NORMAL_PRIORITY_CLASS    =32
IDLE_PRIORITY_CLASS      =64
HIGH_PRIORITY_CLASS      =128
REALTIME_PRIORITY_CLASS  =1600
THREAD_PRIORITY_IDLE         =   -15
THREAD_PRIORITY_LOWEST       =   -2
THREAD_PRIORITY_BELOW_NORMAL =   -1
THREAD_PRIORITY_NORMAL       =   0
THREAD_PRIORITY_ABOVE_NORMAL =   1
THREAD_PRIORITY_HIGHEST      =   2
THREAD_PRIORITY_TIME_CRITICAL=   15

def rush(value=True):    
    """Raise the priority of the current thread/process 
    Win32 and OS X only so far - on linux use os.nice(niceIncrement)
    
    Set with rush(True) or rush(False)
    
    Beware and don't take priority until after debugging your code
    and ensuring you have a way out (e.g. an escape sequence of
    keys within the display loop). Otherwise you could end up locked
    out and having to reboot!
    """
    thr=windll.GetCurrentThread()
    pr =windll.GetCurrentProcess()
    if value:
            windll.SetPriorityClass(pr, REALTIME_PRIORITY_CLASS)
            windll.SetThreadPriority(thr, THREAD_PRIORITY_TIME_CRITICAL)
    else:
            windll.SetPriorityClass(pr, NORMAL_PRIORITY_CLASS)
            windll.SetThreadPriority(thr, THREAD_PRIORITY_NORMAL)

def waitForVBL():
    """Not implemented on win32 yet
    """
    pass