try: #this fails on a first new build
    import _win32 #the .pyd file (a dll)
except:
    pass

#Should fetch these properly from winbase.h 
#- must learn how to fetch constants from headers :)
NORMAL_PRIORITY_CLASS	=32
IDLE_PRIORITY_CLASS	=64
HIGH_PRIORITY_CLASS	=128
REALTIME_PRIORITY_CLASS	=256

THREAD_PRIORITY_ABOVE_NORMAL =1
THREAD_PRIORITY_BELOW_NORMAL =(-1)
THREAD_PRIORITY_HIGHEST =2
THREAD_PRIORITY_IDLE =(-15)
THREAD_PRIORITY_LOWEST =(-2)
THREAD_PRIORITY_NORMAL =0
THREAD_PRIORITY_TIME_CRITICAL =15

#from msvc winbase.h
"""
#define NORMAL_PRIORITY_CLASS       0x00000020
#define IDLE_PRIORITY_CLASS         0x00000040
#define HIGH_PRIORITY_CLASS         0x00000080
#define REALTIME_PRIORITY_CLASS     0x00000100

#define THREAD_PRIORITY_LOWEST          THREAD_BASE_PRIORITY_MIN
#define THREAD_PRIORITY_BELOW_NORMAL    (THREAD_PRIORITY_LOWEST+1)
#define THREAD_PRIORITY_NORMAL          0
#define THREAD_PRIORITY_HIGHEST         THREAD_BASE_PRIORITY_MAX
#define THREAD_PRIORITY_ABOVE_NORMAL    (THREAD_PRIORITY_HIGHEST-1)
#define THREAD_PRIORITY_ERROR_RETURN    (MAXLONG)

#define THREAD_PRIORITY_TIME_CRITICAL   THREAD_BASE_PRIORITY_LOWRT
#define THREAD_PRIORITY_IDLE            THREAD_BASE_PRIORITY_IDLE
"""
#from mingw winbase.h
"""
#define NORMAL_PRIORITY_CLASS	32
#define IDLE_PRIORITY_CLASS	64
#define HIGH_PRIORITY_CLASS	128
#define REALTIME_PRIORITY_CLASS	256

#define THREAD_PRIORITY_ABOVE_NORMAL 1
#define THREAD_PRIORITY_BELOW_NORMAL (-1)
#define THREAD_PRIORITY_HIGHEST 2
#define THREAD_PRIORITY_IDLE (-15)
#define THREAD_PRIORITY_LOWEST (-2)
#define THREAD_PRIORITY_NORMAL 0
#define THREAD_PRIORITY_TIME_CRITICAL 15
"""
def rush(rushLevel):
    """rushLevel varies from 0(don't rush) to 3(absolute priority)
    Beware and don't take priority until after debugging your code
    and ensuring you have a way out (e.g. an escape sequence of
    keys within the display loop). Otherwise you could end up locked
    out and having to reboot!
    """
    if rushLevel==0:
        _win32.setProcessPriority(IDLE_PRIORITY_CLASS)
        _win32.setThreadPriority(THREAD_PRIORITY_IDLE)
    elif rushLevel==1:
        _win32.setProcessPriority(NORMAL_PRIORITY_CLASS)
        _win32.setThreadPriority(THREAD_PRIORITY_NORMAL)
    elif rushLevel==2:
        _win32.setProcessPriority(HIGH_PRIORITY_CLASS)
        _win32.setThreadPriority(THREAD_PRIORITY_HIGHEST)
    elif rushLevel==3:
        _win32.setProcessPriority(REALTIME_PRIORITY_CLASS)
        _win32.setThreadPriority(THREAD_PRIORITY_TIME_CRITICAL)
    else: raise RuntimeError, 'Rush raised to unknown priority'
        
