# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

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

try:
    from ctypes import windll
    windll=windll.kernel32
    importWindllFailed = False
except:
    importWindllFailed = True
    log.debug("rush() not available because import windll failed in ext/win32.py")

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
#sleep signals
ES_CONTINUOUS = 0x80000000
ES_DISPLAY_REQUIRED = 0x00000002
ES_SYSTEM_REQUIRED = 0x00000001

def rush(value=True):
    """Raise the priority of the current thread/process
    Win32 and OS X only so far - on linux use os.nice(niceIncrement)

    Set with rush(True) or rush(False)

    Beware and don't take priority until after debugging your code
    and ensuring you have a way out (e.g. an escape sequence of
    keys within the display loop). Otherwise you could end up locked
    out and having to reboot!
    """
    if importWindllFailed:
        return False

    thr=windll.GetCurrentThread()
    pr =windll.GetCurrentProcess()
    if value:
            windll.SetPriorityClass(pr, REALTIME_PRIORITY_CLASS)
            windll.SetThreadPriority(thr, THREAD_PRIORITY_TIME_CRITICAL)
    else:
            windll.SetPriorityClass(pr, NORMAL_PRIORITY_CLASS)
            windll.SetThreadPriority(thr, THREAD_PRIORITY_NORMAL)
    return True

def waitForVBL():
    """Not implemented on win32 yet
    """
    pass

def sendStayAwake():
    """Sends a signal to your system to indicate that the computer is in use and
    should not sleep. This should be sent periodically, but PsychoPy will send
    the signal by default on each screen refresh.
    Added: v1.79.00

    Currently supported on: windows, OS X
    """
    success = windll.SetThreadExecutionState( ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED )
    return success #indicates success
