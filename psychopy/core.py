"""Basic timing functions
"""
import sys, os, time
runningThreads=[]
try:
    import pyglet.media
except:
    pass
    
def quit():
    """Close everything and exit nicely (ending the experiment)
    """
    #pygame.quit() #safe even if pygame was never initialised
    for thisThread in runningThreads:
        thisThread.stop()
        while thisThread.running==0:
            pass#wait until it has properly finished polling
    sys.exit(0)#quits the python session entirely

#set the default timing mechanism
"""(The difference in default timer function is because on Windows,
clock() has microsecond granularity but time()'s granularity is 1/60th
of a second; on Unix, clock() has 1/100th of a second granularity and
time() is much more precise.  On Unix, clock() measures CPU time 
rather than wall time.)"""
if sys.platform == 'win32':
    getTime = time.clock
else:
    getTime = time.time

class Clock:
    """A convenient class to keep track of time in your experiments.
    You can have as many independent clocks as you like (e.g. one 
    to time	responses, one to keep track of stimuli...)
    The clock is based on python.time.time() which is a sub-millisec
    timer on most machines. i.e. the times reported will be more
    accurate than you need!
    """
    def __init__(self):
        self.timeAtLastReset=getTime()#this is sub-millisec timer in python
    def getTime(self):
        """Returns the current time on this clock in secs (sub-ms precision)
        """
        return getTime()-self.timeAtLastReset
    def reset(self, newT=0.0):
        """Reset the time on the clock. With no args time will be 
        set to zero. If a float is received this will be the new
        time on the clock
        """
        self.timeAtLastReset=getTime()+newT

def wait(secs):
    """Wait for a given time period (simple wrap of time.sleep()
    which comes with Python)
    """    
    time.sleep(secs)
    try:
        pyglet.media.dispatch_events()
    except:
        pass #maybe pyglet 
    
def rush(rushLevel):
    """Raise the priority of the current thread/process 
    Win32 only - on OSX/linux use os.nice(niceIncrement)
    
    rushLevel varies from 0(don't rush) to 3(absolute priority)
    Beware and don't take priority until after debugging your code
    and ensuring you have a way out (e.g. an escape sequence of
    keys within the display loop). Otherwise you could end up locked
    out and having to reboot!
    """
    
    """for darwin there is an ApplicationServices library with functions
    getpriority
    setpriority
    but I haven't found docs to use them.
    """
    
    if sys.platform=='win32':
        import win32process, win32api#comes from pywin32 libraries
        thr=win32api.GetCurrentThread()
        pr =win32api.GetCurrentProcess()
        if rushLevel==0:
            win32process.SetPriorityClass(pr, win32process.IDLE_PRIORITY_CLASS)
            win32process.SetThreadPriority(thr, win32process.THREAD_PRIORITY_IDLE)
        elif rushLevel==1:
            win32process.SetPriorityClass(pr, win32process.NORMAL_PRIORITY_CLASS)
            win32process.SetThreadPriority(thr, win32process.THREAD_PRIORITY_NORMAL)
        elif rushLevel==2:
            win32process.SetPriorityClass(pr, win32process.HIGH_PRIORITY_CLASS)
            win32process.SetThreadPriority(thr, win32process.THREAD_PRIORITY_HIGHEST)
        elif rushLevel==3:
            win32process.SetPriorityClass(pr, win32process.REALTIME_PRIORITY_CLASS)
            win32process.SetThreadPriority(thr, win32process.THREAD_PRIORITY_TIME_CRITICAL)
        else: raise RuntimeError, 'Rush raised to unknown priority'