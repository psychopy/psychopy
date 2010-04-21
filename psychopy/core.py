"""Basic functions, including timing and run-time configuration profile
"""
# Part of the PsychoPy library
# Copyright (C) 2010 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys, platform, os, time, threading
import subprocess, shlex, numpy

# these are for RuntimeInfo():
from psychopy import __version__
from pyglet.gl import gl_info
import scipy, matplotlib, pyglet
try: from pygame import __version__ as pygameVersion
except: pygameVersion = ''

#  
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

def msPerFrame(myWin, frames=60):
    """estimates the monitor refresh rate
    
    times at least 40 frames, returns the average of the six times nearest the median (in ms)
    """
    frames = max(40, frames)  # lower bound of 40 frames to sample
    num2avg = 6  # how many to average from the middle
    
    t  = [] # clock times
    ft = [] # frame-times
    for i in range(5): # wake everybody up
        myWin.flip()
    t.append(getTime())
    # accumulate secs per frame for a bunch of frames:
    for i in range(frames):
        myWin.flip()
        t.append(getTime()) # this is core.getTime()
    ft = [t[i] - t[i-1] for i in range(1,len(t))] 
    ft.sort() # sort in order to get a slice around the median, and average it:
    secPerFrame = numpy.average(ft[ (frames-num2avg)/2 : (frames+num2avg)/2 ])
    
    return secPerFrame * 1000.  # return ms
    

class RuntimeInfo(dict):
    """Returns a snapshot of your configuration at run-time, intended to be useful for immediate or archival use.
    
    Finds and returns a dict-like object with info about PsychoPy, your experiment script, your window and monitor
    settings (if any), the system & OS, python & packages, and openGL.
    
    The value in sys.argv[0] is assumed to be your "experiment script". You have to explicitly provide
    any desired author and version info. Your information (such as author) cannot contain double-quote characters
    (they are removed). Setting verbose=True reports more detail, including OpenGL info.
    The screen refresh rate is estimated in ms-per-frame by returning the median of 60 samples.
    If the directory containing your script is under version control using svn, the revision number is discovered.
    """
    def __init__(self, author=None, version=None, verbose=False, win=None):
        """This is where most of the work gets done: saving various settings and so on into a data structure.
        To control item order and appearance in __str__ and __repr__, init first creates a string with all the 
        info and is formatted nicely (e.g., includes comments). At the end of __init__, the string gets converted
        to a dict.
        NB: Adding code to this section is like writing in php: you have to think in terms of creating strings
        that will evaluate to legal syntax, requiring some care to sanitize values that might cause eval() to
        break. So its good to do .replace('"','') a fair amount if a string could have double-quotes
        Aim to generate lines that are legal dict key:val pair:  '   "uniqueTag": "value_as_string",\n'
        """
        dict.__init__(self)  # this will cause an object to be created with all the same methods as a dict
        
        from psychopy import visual # have to do this here
        
        # These 'configuration lists' control what attributes are reported.
        # All desired attributes/properties need a legal internal name, e.g., win.winType.
        # If an attr is callable, its gets called with no arguments, e.g., win.monitor.getWidth()
        winAttrList = ['winType', '_isFullScr', 'units', 'monitor', 'pos', 'screen', 'rgb', 'size']
        winAttrListVerbose = ['allowGUI', 'useNativeGamma', 'recordFrameIntervals',
                              'waitBlanking', '_haveShaders', '_refreshThreshold']
        if verbose: winAttrList += winAttrListVerbose            
                
        # if 'monitor' is in winAttrList, then these items are reported, as win.monitor.X:
        monAttrList = ['name', 'getDistance', 'getWidth', 'currentCalibName']
        monAttrListVerbose = ['_gammaInterpolator', '_gammaInterpolator2']
        if verbose: monAttrList += monAttrListVerbose
                    
        GLextensionsOfInterest=['GL_ARB_multitexture', 'GL_EXT_framebuffer_object','GL_ARB_fragment_program',
            'GL_ARB_shader_objects','GL_ARB_vertex_shader', 'GL_ARB_texture_non_power_of_two','GL_ARB_texture_float']
            
        profileInfo = '  #PsychoPy: --- http://www.psychopy.org ---\n'
        profileInfo += '    "psychopy_version": "'+__version__+'",\n'
        
        profileInfo += '  #Experiment script: ---------\n'
        profileInfo += '    "experiment_scriptName": "'+os.path.basename(sys.argv[0]).replace('"','')+'",\n'
        if author:  profileInfo += '    "experiment_scriptAuthor": "'+author.replace('"','')+'",\n'
        if version: profileInfo += '    "experiment_scriptVersion": "'+version.replace('"','')+'",\n'
        profileInfo += '    "experiment_runDate": "'+time.ctime()+'",\n'
        scriptDir = os.path.dirname(os.path.abspath(sys.argv[0]))
        profileInfo += '    "experiment_fullPath": "'+scriptDir+'",\n'
        svnrev = svnVersion(dir=scriptDir)
        if svnrev: 
            profileInfo += '    "experiment_svnRev": "'+svnrev+'",\n'
        
        profileInfo += '  #System: ---------\n'
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
        
        # need a window for frames-per-second, and some drivers want a window open
        if win == None:
            win = visual.Window([100,100],monitor="testMonitor") # the temp window
            usingTempWin = True  
        else:  # we were passed a window instance, use it for timing and profile it here:
            usingTempWin = False  # later avoid closing user's window
            profileInfo += '  # Window: ---------\n'
            if 'monitor' in winAttrList: # replace 'monitor' with all desired monitor.<attribute>
                i = winAttrList.index('monitor') # retain list-position info, put monitor stuff there
                del(winAttrList[i])
                for monAttr in monAttrList:
                    winAttrList.insert(i, 'monitor.' + monAttr)
                    i += 1
            for winAttr in winAttrList: 
                try:
                    thing = eval('win.'+winAttr) 
                except AttributeError:
                    print 'Warning (AttributeError): Window instance has no attribute', winAttr
                    continue
                if hasattr(thing, '__call__'):
                    try: thing = thing()
                    except:
                        print 'Warning: could not get a value from', thing+'()  (expects arguments?)'
                        continue
                strthing = str(thing).replace('"','').replace('\n','')
                if winAttr in ['monitor.getDistance','monitor.getWidth']:
                    strthing += ' cm'
                profileInfo += '    "win_'+winAttr+'": "'+strthing+'",\n'
                
        if not verbose:
            msPF = msPerFrame(win,frames=60)
            profileInfo += '    "secPerRefresh": "%.5f",\n' % (msPF/1000.)
            profileInfo += '    "msPerFrame": "%.2f",\n' % (msPF)
        else:
            msPFmoreFrames = msPerFrame(win,frames=120)
            profileInfo += '    "secPerRefresh": "%.5f",\n' % (msPFmoreFrames/1000)
            profileInfo += '    "msPerFrame": "%.2f",\n' % (msPFmoreFrames)
            profileInfo += '    "framesPerSecond": "%.2f",\n' % (1000. / msPFmoreFrames)
        
        profileInfo += '  #Python: ---------\n'
        profileInfo += '    "python_version": "'+sys.version.split()[0]+'",\n'
        
        if verbose:
            # External python packages:
            profileInfo += '    "numpy_version": "'+numpy.__version__.replace('"','')+'",\n'
            profileInfo += '    "scipy_version": "'+scipy.__version__.replace('"','')+'",\n'
            profileInfo += '    "matplotlib_version": "'+matplotlib.__version__.replace('"','')+'",\n'
            profileInfo += '    "pyglet_version": "'+pyglet.__version__.replace('"','')+'",\n'
            profileInfo += '    "pygame_version": "'+pygameVersion.replace('"','')+'",\n'
            
            # Python gory details:
            profileInfo += '    "python_fullVersion": "'+sys.version.replace('\n',' ').replace('"','')+'",\n'
            profileInfo += '    "python_executable": "'+sys.executable.replace('"','')+'",\n'
            
            # OpenGL info:
            profileInfo += '  #OpenGL: ---------\n'
            #from pyglet.gl import gl_info
            profileInfo += '    "openGL_vendor": "'+gl_info.get_vendor().replace('"','')+'",\n'
            profileInfo += '    "openGL_renderingEngine": "'+gl_info.get_renderer().replace('"','')+'",\n'
            profileInfo += '    "openGL_version": "'+gl_info.get_version().replace('"','')+'",\n'
            for ext in GLextensionsOfInterest:
                profileInfo += '    "'+ext+'": '+str(bool(gl_info.have_extension(ext)))+',\n'
        if usingTempWin:
            win.close()
        
        # cache the string version for use in __repr__() and __str__()
        self.stringRepr = profileInfo
        
        # convert string to dict
        tmpDict = eval('{'+profileInfo+'}')
        for k in tmpDict.keys():
            self[k] = tmpDict[k]
        
    def __repr__(self):
        # returns string that is quite readable, and also legal python dict syntax
        return '{\n'+self.stringRepr+'}'
    
    def __str__(self):
        # cleaned-up for easiest human-reading (e.g., in a log file), no longer legal python syntax
        return self.stringRepr.replace('"','').replace(',\n','\n')