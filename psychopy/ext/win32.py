import win32process#comes from pywin32 libraries

def rush(rushLevel):
    """rushLevel varies from 0(don't rush) to 3(absolute priority)
    Beware and don't take priority until after debugging your code
    and ensuring you have a way out (e.g. an escape sequence of
    keys within the display loop). Otherwise you could end up locked
    out and having to reboot!
    """
    if rushLevel==0:
        #win32process.setProcessPriority(win32process.IDLE_PRIORITY_CLASS)
        win32process.setThreadPriority(win32process.THREAD_PRIORITY_IDLE)
    elif rushLevel==1:
        #win32process.setProcessPriority(NORMAL_PRIORITY_CLASS)
        win32process.setThreadPriority(win32process.THREAD_PRIORITY_NORMAL)
    elif rushLevel==2:
        #win32process.setProcessPriority(win32process.HIGH_PRIORITY_CLASS)
        win32process.setThreadPriority(win32process.THREAD_PRIORITY_HIGHEST)
    elif rushLevel==3:
        #win32process.setProcessPriority(win32process.REALTIME_PRIORITY_CLASS)
        win32process.setThreadPriority(win32process.THREAD_PRIORITY_TIME_CRITICAL)
    else: raise RuntimeError, 'Rush raised to unknown priority'
        
