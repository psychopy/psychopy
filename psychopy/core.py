"""Basic functions, including timing and run-time configuration profile
"""
# Part of the PsychoPy library
# Copyright (C) 2010 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys, platform, os, time, threading
import subprocess, shlex, numpy

# these are for RuntimeInfo():
from psychopy import __version__ as psychopyVersion
from pyglet.gl import gl_info
import scipy, matplotlib, pyglet

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

def msPerFrame(myWin, frames=60, progressBar=True):
    """assesses the monitor refresh rate, and SD of refresh rate under current conditions
    
    times at least 60 frames, returns the average of all, the avg of the six at the median (in ms),
    and the standard deviation of all frames
    """
    # extend: 1. allow display of a specific stim during refresh testing?
    # 2. allow other than norm units for progress bars
    # 3. allow clearBuff = False, so user can display something and then test refresh during that static display
    #    e.g., perhaps have an "any-key to end" option
    
    from psychopy import visual # which imports core, so currently need to do here in core.msPerFrame()
    
    frames = max(60, frames)  # lower bound of 60 samples--need enough to estimate the SD
    num2avg = 6  # how many to average from the middle
    if myWin.units != 'norm': # so far things are hard coded in norm units, bad
        progressBar = False
    if progressBar:
        vAdj = -0.35
        pbar = visual.ShapeStim(myWin, lineWidth=1, lineColor=(0,0,1), lineColorSpace='rgb',
                    fillColor=(0,0,1),fillColorSpace='rgb', vertices=[[-.5,vAdj-.05],[-.5,vAdj+.05],[-.5,vAdj+.05],[-.5,vAdj-.05]])
        
    t  = [] # clock times
    ft = [] # frame-times
    for i in range(5): # wake everybody up
        myWin.flip()
    
    # accumulate secs per frame for a bunch of frames:
    t.append(getTime()) # core.getTime()
    for i in range(frames):
        if progressBar:
            f = -.5 + float(i)/frames # right end of progress bar
            pbar.setVertices([[-.5,vAdj-.05], [-.5,vAdj+.05], [f,vAdj+.05], [f+.04,vAdj], [f,vAdj-.05]])
            pbar.draw()
        myWin.flip()
        t.append(getTime()) # this is core.getTime()
    myWin.flip()
    ft = [t[i] - t[i-1] for i in range(1,len(t))] 
    ft.sort() # sort in order to get a slice around the median, and average it:
    secPerFrame = numpy.average(ft[ (frames-num2avg)/2 : (frames+num2avg)/2 ])
    msPFmd6 = 1000 * secPerFrame
    msPFavg = 1000 * numpy.average(ft)
    msPFstd = 1000 * numpy.std(ft)
    
    return msPFavg, msPFstd, msPFmd6
    

class RuntimeInfo(dict):
    """Returns a snapshot of your configuration at run-time, intended to be useful for immediate or archival use.
    
    Finds and returns a dict-like object with info about PsychoPy, your experiment script, the system & OS,
    your window and monitor settings (if any), python & packages, and openGL.
    
    The value in sys.argv[0] is assumed to be your "experiment script". You have to explicitly provide
    any desired author and version info. Your information (such as author) cannot contain double-quote characters
    (they are removed), but single-quotes are fine. Setting verbose=True reports more detail, including python
    package versions and OpenGL info.
    The screen refresh rate is estimated in ms-per-frame by msPerFrame(), which is passed progressBar as an arg.
    If the directory containing your script is under version control using svn, the revision number is discovered.
    if verbose and getUserProcs='detailed', then return names and PID's of the user's other concurrent processes.
    """
    
    def __init__(self, author=None, version=None, win=None, verbose=False, progressBar=False, userProcsDetailed=False):
        """This is where most of the work gets done: build up self[key]
        """
        from psychopy import visual # have to do this in __init__ (visual imports core)
        
        dict.__init__(self)  # this will cause an object to be created with all the same methods as a dict
        
        self['psychopyVersion'] = psychopyVersion
        self['experimentName'] = os.path.basename(sys.argv[0])
        if author:  
            self['experimentAuthor'] = author
        if version: 
            self['experimentVersion'] = version
        self['experimentRunDateTime'] = time.ctime()
        scriptDir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self['experimentDirectory'] = scriptDir
        svnrev = svnVersion(dir=scriptDir)
        if svnrev: 
            self['experimentDirctorySVNRevision'] = svnrev
        self._setSystemUserInfo()
        self._setCurrentProcessInfo(verbose, userProcsDetailed)
        
        # need a window for frames-per-second, and some drivers want a window open
        if win == None: # make a temporary window, later close it
            win = visual.Window(fullscr=True, monitor="testMonitor", allowGUI=False, units='norm')
            usingTempWin = True
        else: # we were passed a window instance, use it for timing and profile it:
            usingTempWin = False
            self._setWindowInfo(win, verbose, progressBar)
       
        self['pythonVersion'] = sys.version.split()[0] # always do this
        if verbose:
            self._setPythonInfo()
            self._setOpenGLInfo()
        if usingTempWin:
            win.close() # close after doing openGL
        
    def _setSystemUserInfo(self):
        # machine name and platform:
        self['systemHostName'] = platform.node()
        if sys.platform in ['darwin']:
            OSXver, junk, architecture = platform.mac_ver()
            pInfo = ' '+OSXver+' '+architecture
        elif sys.platform in ['linux2']:
            pInfo = ' '+platform.release()
        elif sys.platform in ['win32']:
            pInfo = ' windowsversion='+repr(sys.getwindowsversion())
        else:
            pInfo = ' [?]'
        self['systemPlatform'] = pInfo
        
        # count all unique people (user IDs logged in), and find current user name
        try:
            users = shellCall("who -q").splitlines()[0].split()
            self['systemUserCount'] = len(set(users))
        except:
            self['systemUserCount'] = "[?]"
        try:
            self['systemUser'] = os.environ['USER']
        except:
            try: self['systemUser'] = os.environ['USERNAME']
            except: self['systemUser'] = "[?]"
        
    def _setCurrentProcessInfo(self, verbose=False, userProcsDetailed=False):
        # what other processes are currently active for this user?
        profileInfo = ''
        appFlagList = [# flag these apps if active, case-insensitive match:
            'Firefox','Safari','Explorer','Netscape', 'Opera', # web browsers can burn CPU cycles
            'BitTorrent', 'iTunes', # but also matches iTunesHelper (add to ignore-list)
            'mdimport', # can have high CPU
            'Office', 'KeyNote', 'Pages', 'LaunchCFMApp', # productivity; on mac, MS Word etc is launched by 'LaunchCFMApp'
            'VirtualBox','VBoxClient', # virtual machine as host or client
            'Parallels', 'Coherence',
            'VMware',
            #'update-notifier'
            ]
        appIgnoreList = [# always ignore these, exact match:
            'ps','login','-tcsh','bash',
            'iTunesHelper',
            ]
        
        # assess concurrently active processes owner by the current user:
        try:
            # ps = process status, -c to avoid full path (potentially having spaces) & args, -U for user
            if sys.platform in ['darwin']:
                proc = shellCall("ps -c -U "+os.environ['USER'])
                cmdStr = 'COMMAND'
            elif sys.platform in ['linux2']:
                proc = shellCall("ps -c -U "+os.environ['USER'])
                cmdStr = 'CMD'
            elif sys.platform in ['win32']: 
                proc, err = shellCall("tasklist", stderr=True) # "tasklist /m" gives modules as well
                if err:
                    print 'tasklist error:', err
                    raise
            else: # guess about freebsd based on darwin... 
                proc,err = shellCall("ps -U "+os.environ['USER'],stderr=True)
                if err: raise
                cmdStr = 'COMMAND' # or 'CMD'?
            systemProcPsu = []
            systemProcPsuFlagged = []
            procLines = proc.splitlines() 
            headerLine = procLines.pop(0) # column labels
            if sys.platform not in ['win32']:
                cmd = headerLine.split().index(cmdStr) # columns and column labels vary across platforms
                pid = headerLine.split().index('PID')  # process id's extracted in case you want to os.kill() them from psychopy
            else: # this works for win XP, for output from 'tasklist'
                procLines.pop(0)
                cmd = 0
                pid = 1
            for p in procLines:
                pr = p.split() # info fields for this process
                if pr[cmd] not in appIgnoreList:
                    systemProcPsu.append([pr[cmd],pr[pid]]) # later just count these unless want details
                    for app in appFlagList:
                        if p.lower().find(app.lower())>-1: # match anywhere in the process line
                            systemProcPsuFlagged.append([app, pr[pid]])
            if verbose and userProcsDetailed:
                self['systemUserProcesses'] = repr(systemProcPsu)
            else:
                self['systemUserProcesses'] = repr(systemProcPsu)
            self['systemUserProcessesFlagged'] = repr(systemProcPsuFlagged)
        except:
            self['systemUserProcesses'] = "[?]"
            self['systemUserProcessesFlagged'] = "[?]"
    
    def _setWindowInfo(self,win=None,verbose=False, progressBar=False):
        # These 'configuration lists' control what attributes are reported.
        # All desired attributes/properties need a legal internal name, e.g., win.winType.
        # If an attr is callable, its gets called with no arguments, e.g., win.monitor.getWidth()
        winAttrList = ['winType', '_isFullScr', 'units', 'monitor', 'pos', 'screen', 'rgb', 'size']
        winAttrListVerbose = ['allowGUI', 'useNativeGamma', 'recordFrameIntervals','waitBlanking', '_haveShaders', '_refreshThreshold']
        if verbose: winAttrList += winAttrListVerbose
        # if 'monitor' is in winAttrList, then these items are reported, as win.monitor.X:
        monAttrList = ['name', 'getDistance', 'getWidth', 'currentCalibName']
        monAttrListVerbose = ['_gammaInterpolator', '_gammaInterpolator2']
        if verbose: monAttrList += monAttrListVerbose
        
        if 'monitor' in winAttrList: # replace 'monitor' with all desired monitor.<attribute>
            i = winAttrList.index('monitor') # retain list-position info, put monitor stuff there
            del(winAttrList[i])
            for monAttr in monAttrList:
                winAttrList.insert(i, 'monitor.' + monAttr)
                i += 1
        for winAttr in winAttrList: 
            try:
                attrValue = eval('win.'+winAttr)
            except AttributeError:
                print 'Warning (AttributeError): Window instance has no attribute', winAttr
                continue
            if hasattr(attrValue, '__call__'):
                try:
                    a = attrValue()
                    attrValue = a
                except:
                    print 'Warning: could not get a value from win.'+winAttr+'()  (expects arguments?)'
                    continue
            while winAttr[0]=='_':
                winAttr = winAttr[1:]
            winAttr = winAttr[0].capitalize()+winAttr[1:]
            winAttr = winAttr.replace('Monitor._','Monitor.')
            self['window'+winAttr] = attrValue
        
        msPFavg, msPFstd, msPF6md = msPerFrame(win, frames=60, progressBar=progressBar)
        self['windowSecPerRefresh'] = "%.5f" % (msPFavg/1000.)
        self['windowMsPerFrameAvg'] = "%.2f" %(msPFavg)
        self['windowMsPerFrameMed6'] = "%.2f" %(msPF6md)
        self['windowMsPerFrameSD'] = "%.2f" %(msPFstd)
        
    def _setPythonInfo(self):
        # External python packages:
        self['pythonNumpyVersion'] = numpy.__version__
        self['pythonScipyVersion'] = scipy.__version__
        self['pythonMatplotlibVersion'] = matplotlib.__version__
        self['pythonPygletVersion'] = pyglet.__version__
        try: from pygame import __version__ as pygameVersion
        except: pygameVersion = '(no pygame)'
        self['pythonPygameVersion'] = pygameVersion
        
        # Python gory details:
        self['pythonFullVersion'] = sys.version.replace('\n',' ')
        self['pythonExecutable'] = sys.executable
        
    def _setOpenGLInfo(self):
        # OpenGL info:
        self['openGLVendor'] = gl_info.get_vendor()
        self['openGLRenderingEngine'] = gl_info.get_renderer()
        self['openGLVersion'] = gl_info.get_version()
        
        GLextensionsOfInterest=['GL_ARB_multitexture', 'GL_EXT_framebuffer_object','GL_ARB_fragment_program',
            'GL_ARB_shader_objects','GL_ARB_vertex_shader', 'GL_ARB_texture_non_power_of_two','GL_ARB_texture_float']
        for ext in GLextensionsOfInterest:
            self['openGLext'+ext] = bool(gl_info.have_extension(ext))
        
    def __repr__(self):
        # returns string that is quite readable, and also legal python dict (and close to configObj syntax)
        info = '{\n#[ PsychoPy2 RuntimeInfo ]\n'
        sections = ['PsychoPy', 'Experiment', 'System', 'Window', 'Python', 'OpenGL']
        for sect in sections:
            info += '  #[[ %s ]] #---------\n' % (sect)
            sectKeys = [k for k in self.keys() if k.lower().find(sect.lower()) == 0]
            sectKeys.sort(key=str.lower)
            for k in sectKeys:
                info += '    "%s": %s,\n' % (k, self[k]) #.replace('"','').replace('\n',' '))
        info += '}'
        return info
    
    def __str__(self):
        # cleaned-up for human reading (e.g., in a log file), no longer legal python syntax
        # add anything needed, like units
        addUnitsCM = ['windowMonitor.getDistance','windowMonitor.getWidth']
        for k in addUnitsCM:
            self[k] = str(self[k])+' cm'
        info = self.__repr__()
        info.replace('"','').replace(',\n','\n')
        
        return info
        
    def config(self):
        # return a ConfigObj?
        return None