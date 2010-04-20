"""Basic functions, including timing and run-time configuration profile
"""
# Part of the PsychoPy library
# Copyright (C) 2010 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys, platform, os, time, threading
import subprocess, shlex
#from numpy import *

try: from ext import rush
except: pass

runningThreads=[]
try:
    import pyglet.media
except:
    pass
    
def quit():
    """Close everything and exit nicely (ending the experiment)
    """
    #pygame.quit() #safe even if pygame was never initialised
    for thisThread in threading.enumerate():
        if hasattr(thisThread,'stop') and hasattr(thisThread,'running'):
            #this is one of our event threads - kill it and wait for success
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

def wait(secs, hogCPUperiod=0.2):
    """Wait for a given time period. 
    
    If secs=10 and hogCPU=0.2 then for 9.8s python's time.sleep function will be used,
    which is not especially precise, but allows the cpu to perform housekeeping. In
    the final hogCPUperiod the more precise method of constantly polling the clock 
    is used for greater precision.
    """
    #initial relaxed period, using sleep (better for system resources etc)
    if secs>hogCPUperiod:
        time.sleep(secs-hogCPUperiod)
        secs=hogCPUperiod#only this much is now left
        
    #hog the cpu, checking time
    t0=getTime()
    while (getTime()-t0)<secs:
        pass
    
    #we're done, let's see if pyglet collected any event in meantime
    try:
        pyglet.media.dispatch_events()
    except:
        pass #maybe pyglet 


def shellCall(shellCmd, stderr=False):
    """Calls a system command via subprocess, returns the stdout from the command.
    
    returns (stdout,stderr) if kwarg stderr==True
    """
    
    shellCmdList = shlex.split(shellCmd) # safely split into command + list-of-args
    stdoutData, stderrData = subprocess.Popen(shellCmdList,stdout=subprocess.PIPE).communicate()
    if stderr:
        return stdoutData, stderrData
    else:
        return stdoutData

def svnVersion(dir='.'):
    """Tries to discover the svn version (revision #) for a directory.
    
    Not thoroughly tested; completely untested on Windows Vista, Win 7, FreeBSD
    """
    if sys.platform in ['darwin', 'linux2', 'freebsd']:
        svnrev,stderr = shellCall('svnversion -n "'+dir+'"',stderr=True) 
        if stderr:
            svnrev = None
    else: # this hack worked for me on Win XP sp2 with TortoiseSVN (SubWCRev.exe)
        tmpin = os.path.join(dir,'tmp.in')
        f = open(tmpin,'w')
        f.write('$WCREV$')
        f.close()
        tmph = os.path.join(dir,'tmp.h')
        stdout,stderr = shellCall('subwcrev "'+dir+'" "'+tmpin+'" "'+tmph+'"',stderr=True)
        os.unlink(tmpin)
        if stderr == None:
            f = open(tmph,'r')
            svnrev = f.readline() # likely contained in stdout as well
            f.close()
            os.unlink(tmph)
        else:
            svnrev = None
    
    return svnrev

def msPerFrame(myWin, frames=120, avg=12):
    """estimates the monitor refresh rate
    record a bunch of frame-times, return an average value that 
    """
    frames = max(40, frames) # lower bound of 40
    avg = max(4,avg)
    avg = min(frames/2,avg)
    
    t = [0 for i in range(frames)]
    ftdiff = [0 for i in range(frames)]
    for i in range(20): # just to warm things up
        myWin.flip()
    
    c = Clock()
    t[0] = c.getTime()
    # accumulate secs per frame for a bunch of frames:
    t[0] = time.time()
    for i in range(1,frames):
        myWin.flip()
        t[i] = c.getTime()
        ftdiff[i] = t[i] - t[i-1]

    ftdiff.sort() # sort the frame times
    secPerFrame = sum(ftdiff[ (frames-avg)/2 : (frames+avg)/2 ]) / avg # average a slice from the middle
    
    return secPerFrame * 1000.  # return ms
    

class RuntimeInfo(dict):
    """Return a dict-like object holding run-time details, such as version info.
    
    Returns info about PsychoPy, your experiment script, the system & OS, python & packages, and openGL.
    
    The experiment script is assumed to be sys.argv[0], but you have to feed in your author and version info.
    verbose=True reports more detail, including OpenGL info.
    Estimates the screen refresh rate in frames per second, defaulting to frameSamples=120.
    Quirk: Your information (such as author) cannot contain double-quote characters (they are removed).
    """
    def __init__(self, author='', version='', verbose=False, frameSamples=120):
        dict.__init__(self) #this will cause an object to be created with all the same methods as a dict
        
        # to control item order and appearance in the __str__ method, first build
        # up a string that is formatted nicely for a log file (including comments),
        # then convert to dict (which deletes comments, and is not ordered)
        from psychopy import __version__, visual
        profileInfo = '  #PsychoPy:  see http://www.psychopy.org\n'
        profileInfo += '    "psychopy_version": "'+__version__+'",\n'
        
        profileInfo += '  #Experiment script: ------\n'
        profileInfo += '    "experiment_scriptName": "'+os.path.basename(sys.argv[0]).replace('"','')+'",\n'
        profileInfo += '    "experiment_scriptAuthor": "'+author.replace('"','')+'",\n'
        profileInfo += '    "experiment_scriptVersion": "'+version.replace('"','')+'",\n'
        profileInfo += '    "experiment_runDate": "'+time.ctime()+'",\n'
        scriptDir = os.path.dirname(os.path.abspath(sys.argv[0]))
        profileInfo += '    "experiment_fullPath": "'+scriptDir+'",\n'
        svnrev = svnVersion(dir=scriptDir)
        if svnrev: 
            profileInfo += '    "experiment_svnRev": "'+svnrev+'",\n'
        
        profileInfo += '  #System: ------\n'
        profileInfo += '    "hostname": "'+platform.node().replace('"','')+'",\n'
        profileInfo += '    "platform": "'+sys.platform
        if sys.platform=='darwin':
            OSXver, junk, architecture = platform.mac_ver()
            profileInfo += ' '+OSXver+' '+architecture
        elif sys.platform == 'linux2':
            profileInfo += ' '+platform.release()
        elif sys.platform in ['win32']:
            profileInfo += ' windowsversion='+repr(sys.getwindowsversion())
        else:
            profileInfo += ' [?]'
        profileInfo += '",\n'
        #profileInfo += '    "monitor": "(not implemented)",\n'
        
        # set up a window, for frames-per-second and GL-info; some drivers want a window open first
        tmpwin = visual.Window([10,10])
        msPF = msPerFrame(tmpwin,frames=120,avg=12)
        profileInfo += '    "framesPerSecond": "%.2f",\n' % (1000./msPF)
        profileInfo += '    "msPerFrame": "%.2f",\n' % (msPF)
        
        profileInfo += '  #Python: ------\n'
        profileInfo += '    "python_version": "'+sys.version.split()[0]+'",\n'
        
        if verbose:
            # External python packages:
            import numpy; profileInfo += '    "numpy_version": "'+numpy.__version__.replace('"','')+'",\n'
            import scipy; profileInfo += '    "scipy_version": "'+scipy.__version__.replace('"','')+'",\n'
            import matplotlib; profileInfo += '    "matplotlib_version": "'+matplotlib.__version__.replace('"','')+'",\n'
            import pyglet; profileInfo += '    "pyglet_version": "'+pyglet.__version__.replace('"','')+'",\n'
            try: import pygame; profileInfo += '    "pygame_version": "'+pygame.__version__.replace('"','')+'",\n'
            except: pass
            
            # Python gory details:
            profileInfo += '    "python_fullVersion": "'+sys.version.replace('\n',' ').replace('"','')+'",\n'
            profileInfo += '    "python_executable": "'+sys.executable.replace('"','')+'",\n'
            
            # OpenGL info:
            profileInfo += '  #OpenGL: ------\n'
            from pyglet.gl import gl_info
            profileInfo += '    "openGL_vendor": "'+gl_info.get_vendor().replace('"','')+'",\n'
            profileInfo += '    "openGL_renderingEngine": "'+gl_info.get_renderer().replace('"','')+'",\n'
            profileInfo += '    "openGL_version": "'+gl_info.get_version().replace('"','')+'",\n'
            
            extensionsOfInterest=['GL_ARB_multitexture', 
                'GL_EXT_framebuffer_object','GL_ARB_fragment_program',
                'GL_ARB_shader_objects','GL_ARB_vertex_shader',
                'GL_ARB_texture_non_power_of_two','GL_ARB_texture_float']
            for ext in extensionsOfInterest:
                profileInfo += '    "'+ext+'": '+str(bool(gl_info.have_extension(ext)))+',\n'
        
        tmpwin.close()
        
        # cache the string version for use in __repr__() and __str__()
        self.stringRepr = profileInfo
        
        # convert string to dict
        d = eval('{'+profileInfo+'}')
        for k in d.keys():
            self[k] = d[k]
        
    def __repr__(self):
        # returns nicer format string, still legal python dict
        return '{'+self.stringRepr+'}'
    
    def __str__(self):
        # for easier human reading (e.g., in a log file)
        return self.stringRepr.replace('"','').replace(',\n','\n')