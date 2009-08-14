# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""
There are no c extensions for windows at the moment - everything is done
from the pywin32 extensions.
"""
import win32process, win32api#comes from pywin32 libraries
def rush(value=True):    
    """Raise the priority of the current thread/process 
    Win32 and OS X only so far - on linux use os.nice(niceIncrement)
    
    Set with rush(True) or rush(False)
    
    Beware and don't take priority until after debugging your code
    and ensuring you have a way out (e.g. an escape sequence of
    keys within the display loop). Otherwise you could end up locked
    out and having to reboot!
    """
    thr=win32api.GetCurrentThread()
    pr =win32api.GetCurrentProcess()
    if value:
            win32process.SetPriorityClass(pr, win32process.REALTIME_PRIORITY_CLASS)
            win32process.SetThreadPriority(thr, win32process.THREAD_PRIORITY_TIME_CRITICAL)
    else:
            win32process.SetPriorityClass(pr, win32process.NORMAL_PRIORITY_CLASS)
            win32process.SetThreadPriority(thr, win32process.THREAD_PRIORITY_NORMAL)
