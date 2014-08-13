# -*- coding: utf-8 -*-
"""Fetching data about the system"""
# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys, os, time, platform

from psychopy import visual, logging, core, data, web
from psychopy.core import shellCall
from psychopy.platform_specific import rush
from psychopy import __version__ as psychopyVersion
from pyglet.gl import *
import numpy, scipy, matplotlib, pyglet
try:
    import ctypes
    haveCtypes = True
    DWORD = ctypes.c_ulong  # for getRAM() on win
    DWORDLONG = ctypes.c_ulonglong
except ImportError:
    haveCtypes = False
import hashlib
import random
import wx
import locale


class RunTimeInfo(dict):
    """Returns a snapshot of your configuration at run-time, for immediate or archival use.
    
    Returns a dict-like object with info about PsychoPy, your experiment script, the system & OS,
    your window and monitor settings (if any), python & packages, and openGL.
    
    If you want to skip testing the refresh rate, use 'refreshTest=None'
    
    Example usage: see runtimeInfo.py in coder demos.
    
    :Author:
        - 2010 written by Jeremy Gray, with input from Jon Peirce and Alex Holcombe
    """
    def __init__(self, author=None, version=None, win=None, refreshTest='grating',
                 userProcsDetailed=False, verbose=False, randomSeed=None ):
        """
        :Parameters:
            
            win : *None*, False, :class:`~psychopy.visual.Window` instance
                what window to use for refresh rate testing (if any) and settings. None -> temporary window using
                defaults; False -> no window created, used, nor profiled; a Window() instance you have already created
            
            author : *None*, string
                None = try to autodetect first __author__ in sys.argv[0]; string = user-supplied author info (of an experiment)
            
            version : *None*, string
                None = try to autodetect first __version__ in sys.argv[0]; string = user-supplied version info (of an experiment)
            
            verbose : *False*, True; how much detail to assess
            
            refreshTest : None, False, True, *'grating'*
                True or 'grating' = assess refresh average, median, and SD of 60 win.flip()s, using visual.getMsPerFrame()
                'grating' = show a visual during the assessment; True = assess without a visual
                
            userProcsDetailed: *False*, True
                get details about concurrent user's processses (command, process-ID)
                
            randomSeed: *None*
                a way for the user to record, and optionally set, a random seed for making reproducible random sequences
                'set:XYZ' will both record the seed, 'XYZ', and set it: random.seed('XYZ'); numpy.random.seed() is NOT set
                None defaults to python default;
                'time' = use time.time() as the seed, as obtained during RunTimeInfo()
                randomSeed='set:time' will give a new random seq every time the script is run, with the seed recorded.
                
        :Returns: 
            a flat dict (but with several groups based on key names):
            
            psychopy : version, rush() availability
                psychopyVersion, psychopyHaveExtRush, git branch and current commit hash if available
                
            experiment : author, version, directory, name, current time-stamp, 
                SHA1 digest, VCS info (if any, svn or hg only),
                experimentAuthor, experimentVersion, ...
                
            system : hostname, platform, user login, count of users, user process info (count, cmd + pid), flagged processes
                systemHostname, systemPlatform, ...
                
            window : (see output; many details about the refresh rate, window, and monitor; units are noted)
                windowWinType, windowWaitBlanking, ...windowRefreshTimeSD_ms, ... windowMonitor.<details>, ...
                
            python : version of python, versions of key packages (wx, numpy, scipy, matplotlib, pyglet, pygame)
                pythonVersion, pythonScipyVersion, ...
                
            openGL : version, vendor, rendering engine, plus info on whether several extensions are present
                openGLVersion, ..., openGLextGL_EXT_framebuffer_object, ...
        """
        
        dict.__init__(self)  # this will cause an object to be created with all the same methods as a dict
        
        self['psychopyVersion'] = psychopyVersion
        self['psychopyHaveExtRush'] = rush(False) # NB: this looks weird, but avoids setting high-priority incidentally
        d = os.path.abspath(os.path.dirname(__file__))
        githash = _getHashGitHead(dir=d) # should be .../psychopy/psychopy/
        if githash: 
            self['psychopyGitHead'] = githash
        
        self._setExperimentInfo(author, version, verbose, randomSeed)
        self._setSystemInfo() # current user, locale, other software
        self._setCurrentProcessInfo(verbose, userProcsDetailed)
        
        # need a window for frame-timing, and some openGL drivers want a window open
        if win == None: # make a temporary window, later close it
            win = visual.Window(fullscr=True, monitor="testMonitor")
            refreshTest = 'grating'
            usingTempWin = True
        else: # either False, or we were passed a window instance, use it for timing and profile it:
            usingTempWin = False
        if win: 
            self._setWindowInfo(win, verbose, refreshTest, usingTempWin)
       
        self['pythonVersion'] = sys.version.split()[0]
        if verbose:
            self._setPythonInfo()
            if win: self._setOpenGLInfo()
        if usingTempWin:
            win.close() # close after doing openGL
            
    def _setExperimentInfo(self, author, version, verbose, randomSeedFlag=None):
        # try to auto-detect __author__ and __version__ in sys.argv[0] (= the users's script)
        if not author or not version:
            f = open(sys.argv[0],'r')
            lines = f.read()
            f.close()
        if not author and lines.find('__author__')>-1:
            linespl = lines.splitlines()
            while linespl[0].find('__author__') == -1:
                linespl.pop(0)
            auth = linespl[0]
            if len(auth) and auth.find('=') > 0:
                try:
                    author = str(eval(auth[auth.find('=')+1 :]))
                except:
                    pass
        if not version and lines.find('__version__')>-1:
            linespl = lines.splitlines()
            while linespl[0].find('__version__') == -1:
                linespl.pop(0)
            ver = linespl[0]
            if len(ver) and ver.find('=') > 0:
                try:
                    version = str(eval(ver[ver.find('=')+1 :]))
                except:
                    pass
        
        if author or verbose:  
            self['experimentAuthor'] = author
        if version or verbose: 
            self['experimentAuthVersion'] = version
        
        # script identity & integrity information:
        self['experimentScript'] = os.path.basename(sys.argv[0])  # file name
        scriptDir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self['experimentScript.directory'] = scriptDir
        # sha1 digest, text-format compatibility
        self['experimentScript.digestSHA1'] = _getSha1hexDigest(os.path.abspath(sys.argv[0]), file=True)
        # subversion revision?
        try:
            svnrev, last, url = _getSvnVersion(os.path.abspath(sys.argv[0])) # svn revision
            if svnrev: # or verbose:
                self['experimentScript.svnRevision'] = svnrev
                self['experimentScript.svnRevLast'] = last
                self['experimentScript.svnRevURL'] = url
        except:
            pass
        # mercurical revision?
        try:
            hgChangeSet = _getHgVersion(os.path.abspath(sys.argv[0])) 
            if hgChangeSet: # or verbose:
                self['experimentScript.hgChangeSet'] = hgChangeSet
        except:
            pass
        
        # when was this run?
        self['experimentRunTime.epoch'] = core.getAbsTime()  # basis for default random.seed()
        self['experimentRunTime'] = data.getDateStr(format="%Y_%m_%d %H:%M (Year_Month_Day Hour:Min)")
        
        # random.seed -- record the value, and initialize random.seed() if 'set:'
        if randomSeedFlag: 
            randomSeedFlag = str(randomSeedFlag)
            while randomSeedFlag.find('set: ') == 0:
                randomSeedFlag = randomSeedFlag.replace('set: ','set:',1) # spaces between set: and value could be confusing after deleting 'set:'
            randomSeed = randomSeedFlag.replace('set:','',1).strip()
            if randomSeed in ['time']:
                randomSeed = self['experimentRunTime.epoch']
            self['experimentRandomSeed.string'] = randomSeed
            if randomSeedFlag.find('set:') == 0:
                random.seed(self['experimentRandomSeed.string']) # seed it
                self['experimentRandomSeed.isSet'] = True
            else:
                self['experimentRandomSeed.isSet'] = False
        else:
            self['experimentRandomSeed.string'] = None
            self['experimentRandomSeed.isSet'] = False
            
    def _setSystemInfo(self):
        # machine name
        self['systemHostName'] = platform.node()
        
        self['systemMemTotalRAM'], self['systemMemFreeRAM'] = getRAM()
        
        # locale information:
        import locale
        loc = '.'.join(map(str,locale.getlocale()))  # (None, None) -> str
        if loc == 'None.None':
            loc = locale.setlocale(locale.LC_ALL,'')
        self['systemLocale'] = loc  # == the locale in use, from OS or user-pref
        
        # platform name, etc
        if sys.platform in ['darwin']:
            OSXver, junk, architecture = platform.mac_ver()
            platInfo = 'darwin '+OSXver+' '+architecture
            # powerSource = ...
        elif sys.platform.startswith('linux'):
            platInfo = 'linux '+platform.release()
            # powerSource = ...
        elif sys.platform in ['win32']:
            platInfo = 'windowsversion='+repr(sys.getwindowsversion())
            # powerSource = ...
        else:
            platInfo = ' [?]'
            # powerSource = ...
        self['systemPlatform'] = platInfo
        #self['systemPowerSource'] = powerSource
        
        # count all unique people (user IDs logged in), and find current user name & UID
        self['systemUser'],self['systemUserID'] = _getUserNameUID()
        try:
            users = shellCall("who -q").splitlines()[0].split()
            self['systemUsersCount'] = len(set(users))
        except:
            self['systemUsersCount'] = False
        
        # when last rebooted?
        try:
            lastboot = shellCall("who -b").split()
            self['systemRebooted'] = ' '.join(lastboot[2:])
        except: # windows
            sysInfo = shellCall('systeminfo').splitlines()
            lastboot = [line for line in sysInfo if line.find("System Up Time") == 0 or line.find("System Boot Time") == 0]
            lastboot += ['[?]'] # put something in the list just in case
            self['systemRebooted'] = lastboot[0].strip()
        
        # R (and r2py) for stats:
        try:
            Rver,err = shellCall("R --version",stderr=True)
            Rversion = Rver.splitlines()[0]
            if Rversion.startswith('R version'):
                self['systemRavailable'] = Rversion.strip()
            try:
                import rpy2
                self['systemRpy2'] = rpy2.__version__
            except:
                pass
        except:
            pass
        
        # encryption / security tools:
        try:
            vers, se = shellCall('openssl version', stderr=True)
            if se:
                vers = str(vers) + se.replace('\n',' ')[:80]
            if vers.strip():
                self['systemSec.OpenSSLVersion'] = vers
        except:
            pass
        try:
            so, se = shellCall('gpg --version', stderr=True)
            if so.find('GnuPG') > -1:
                self['systemSec.GPGVersion'] = so.splitlines()[0]
                self['systemSec.GPGHome'] = ''.join([line.replace('Home:','').lstrip()
                                                    for line in so.splitlines()
                                                    if line.startswith('Home:')])
        except:
            pass
        try:
            import ssl
            self['systemSec.pythonSSL'] = True
        except ImportError:
            self['systemSec.pythonSSL'] = False
        
        # pyo for sound:
        try:
            import pyo
            self['systemPyoVersion'] = '%i.%i.%i' % pyo.getVersion()
            try:
                # requires pyo svn r1024 or higher:
                inp, out = pyo.pa_get_devices_infos()
                self['systemPyo.InputDevices'] = inp
                self['systemPyo.OutputDevices'] = out
            except AttributeError:
                pass
        except ImportError:
            pass
        
        # flac (free lossless audio codec) for google-speech:
        flacv = ''
        if sys.platform == 'win32':
            flacexe = 'C:\\Program Files\\FLAC\\flac.exe'
            if os.path.exists(flacexe):
                flacv = core.shellCall(flacexe + ' --version')
        else:
            flac, se = core.shellCall('which flac', stderr=True)
            if not se and flac and not flac.find('Command not found') > -1:
                flacv = core.shellCall('flac --version')
        if flacv:
            self['systemFlacVersion'] = flacv
        
        # detect internet access or fail quickly:
        #web.setupProxy() & web.testProxy(web.proxies)  # can take a long time to fail if there's no connection
        self['systemHaveInternetAccess'] = web.haveInternetAccess()
        if not self['systemHaveInternetAccess']:
            self['systemHaveInternetAccess'] = 'False (proxies not attempted)'

    def _setCurrentProcessInfo(self, verbose=False, userProcsDetailed=False):
        # what other processes are currently active for this user?
        profileInfo = ''
        appFlagList = [# flag these apps if active, case-insensitive match:
            'Firefox','Safari','Explorer','Netscape', 'Opera', 'Google Chrome', # web browsers can burn CPU cycles
            'Dropbox', 'BitTorrent', 'iTunes', # but also matches iTunesHelper (add to ignore-list)
            'mdimport', 'mdworker', 'mds', # can have high CPU
            'Office', 'KeyNote', 'Pages', 'LaunchCFMApp', # productivity; on mac, MS Office (Word etc) can be launched by 'LaunchCFMApp'
            'Skype',
            'VirtualBox','VBoxClient', # virtual machine as host or client
            'Parallels', 'Coherence', 'prl_client_app','prl_tools_service',
            'VMware'] # just a guess
        appIgnoreList = [# always ignore these, exact match:
            'ps','login','-tcsh','bash', 'iTunesHelper']
        
        # assess concurrently active processes owner by the current user:
        try:
            # ps = process status, -c to avoid full path (potentially having spaces) & args, -U for user
            if sys.platform not in ['win32']:
                proc = shellCall("ps -c -U "+os.environ['USER'])
            else:
                proc, err = shellCall("tasklist", stderr=True) # "tasklist /m" gives modules as well
                if err:
                    logging.error('tasklist error:', err)
                    #raise
            systemProcPsu = []
            systemProcPsuFlagged = [] 
            systemUserProcFlaggedPID = []
            procLines = proc.splitlines() 
            headerLine = procLines.pop(0) # column labels
            if sys.platform not in ['win32']:
                try:
                    cmd = headerLine.upper().split().index('CMD') # columns and column labels can vary across platforms
                except ValueError:
                    cmd = headerLine.upper().split().index('COMMAND') 
                pid = headerLine.upper().split().index('PID')  # process id's extracted in case you want to os.kill() them from psychopy
            else: # this works for win XP, for output from 'tasklist'
                procLines.pop(0) # blank
                procLines.pop(0) # =====
                pid = -5 # pid next after command, which can have
                cmd = 0  # command is first, but can have white space, so end up taking line[0:pid]
            for p in procLines:
                pr = p.split() # info fields for this process
                if pr[cmd] in appIgnoreList:
                    continue
                if sys.platform in ['win32']:  #allow for spaces in app names
                    systemProcPsu.append([' '.join(pr[cmd:pid]),pr[pid]]) # later just count these unless want details
                else:
                    systemProcPsu.append([' '.join(pr[cmd:]),pr[pid]]) #
                matchingApp = [a for a in appFlagList if p.lower().find(a.lower())>-1]
                for app in matchingApp:
                    systemProcPsuFlagged.append([app, pr[pid]])
                    systemUserProcFlaggedPID.append(pr[pid])
            self['systemUserProcCount'] = len(systemProcPsu)
            self['systemUserProcFlagged'] = systemProcPsuFlagged
            
            if verbose and userProcsDetailed:
                self['systemUserProcCmdPid'] = systemProcPsu
                self['systemUserProcFlaggedPID'] = systemUserProcFlaggedPID
        except:
            if verbose:
                self['systemUserProcCmdPid'] = None
                self['systemUserProcFlagged'] = None
        
        # CPU speed (will depend on system busy-ness)
        d = numpy.array(numpy.linspace(0., 1., 1000000))
        t0 = core.getTime()
        numpy.std(d)
        t = core.getTime() - t0
        del d
        self['systemTimeNumpySD1000000_sec'] = t
    
    def _setWindowInfo(self, win, verbose=False, refreshTest='grating', usingTempWin=True):
        """find and store info about the window: refresh rate, configuration info
        """

        if refreshTest in ['grating', True]:
            msPFavg, msPFstd, msPFmd6 = visual.getMsPerFrame(win, nFrames=120, showVisual=bool(refreshTest=='grating'))
            self['windowRefreshTimeAvg_ms'] = msPFavg
            self['windowRefreshTimeMedian_ms'] = msPFmd6
            self['windowRefreshTimeSD_ms'] = msPFstd
        if usingTempWin:
            return
        
        # These 'configuration lists' control what attributes are reported.
        # All desired attributes/properties need a legal internal name, e.g., win.winType.
        # If an attr is callable, its gets called with no arguments, e.g., win.monitor.getWidth()
        winAttrList = ['winType', '_isFullScr', 'units', 'monitor', 'pos', 'screen', 'rgb', 'size']
        winAttrListVerbose = ['allowGUI', 'useNativeGamma', 'recordFrameIntervals','waitBlanking', '_haveShaders', '_refreshThreshold']
        if verbose: winAttrList += winAttrListVerbose
        
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
                log.warning('AttributeError in RuntimeInfo._setWindowInfo(): Window instance has no attribute', winAttr)
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
            if winAttr in ['Pos','Size']:
                winAttr += '_pix'
            if winAttr in ['Monitor.getWidth','Monitor.getDistance']:
                winAttr += '_cm'
            if winAttr in ['RefreshThreshold']:
                winAttr += '_sec'
            self['window'+winAttr] = attrValue
        
    def _setPythonInfo(self):
        # External python packages:
        self['pythonNumpyVersion'] = numpy.__version__
        self['pythonScipyVersion'] = scipy.__version__
        self['pythonWxVersion'] = wx.version()
        self['pythonMatplotlibVersion'] = matplotlib.__version__
        self['pythonPygletVersion'] = pyglet.version
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
        GLextensionsOfInterest=['GL_ARB_multitexture', 'GL_EXT_framebuffer_object',
             'GL_ARB_fragment_program', 'GL_ARB_shader_objects','GL_ARB_vertex_shader',
             'GL_ARB_texture_non_power_of_two','GL_ARB_texture_float', 'GL_STEREO']
    
        for ext in GLextensionsOfInterest:
            self['openGLext.'+ext] = bool(gl_info.have_extension(ext))
        
        maxVerts = GLint()
        glGetIntegerv(GL_MAX_ELEMENTS_VERTICES, maxVerts)
        self['openGLmaxVerticesInVertexArray'] = maxVerts.value
        
    def __repr__(self):
        """ Return a string that is a legal python (dict), and close to YAML, .ini, and configObj syntax
        """
        info = '{\n#[ PsychoPy2 RuntimeInfoStart ]\n'
        sections = ['PsychoPy', 'Experiment', 'System', 'Window', 'Python', 'OpenGL']
        for sect in sections:
            info += '  #[[ %s ]] #---------\n' % (sect)
            sectKeys = [k for k in self.keys() if k.lower().find(sect.lower()) == 0]
            # get keys for items matching this section label; use reverse-alpha order if easier to read:
            sectKeys.sort(key=str.lower, reverse=bool(sect in ['PsychoPy', 'Window', 'Python', 'OpenGL']))
            for k in sectKeys:
                selfk = self[k] # alter a copy for display purposes
                try:
                    if type(selfk) == type('abc'):
                        selfk = selfk.replace('"','').replace('\n',' ')
                    elif k.find('_ms')> -1: #type(selfk) == type(0.123):
                        selfk = "%.3f" % selfk
                    elif k.find('_sec')> -1:
                        selfk = "%.4f" % selfk
                    elif k.find('_cm')>-1:
                        selfk = "%.1f" % selfk
                except:
                    pass
                if k in ['systemUserProcFlagged','systemUserProcCmdPid'] and selfk is not None and len(selfk): # then strcat unique proc names
                    prSet = []
                    for pr in self[k]: # str -> list of lists
                        if pr[0].find(' ')>-1: # add single quotes around file names that contain spaces
                            pr[0] = "'"+pr[0]+"'"
                        prSet += [pr[0]] # first item in sublist is proc name (CMD)
                    selfk = ' '.join(list(set(prSet)))
                if k not in ['systemUserProcFlaggedPID']: # suppress display PID info -- useful at run-time, never useful in an archive
                    #if type(selfk) == type('abc'): 
                        info += '    "%s": "%s",\n' % (k, selfk) 
                    #else:
                    #    info += '    "%s": %s,\n' % (k, selfk)
        info += '#[ PsychoPy2 RuntimeInfoEnd ]\n}\n'
        return info
    
    def __str__(self):
        """ Return a string intended for printing to a log file
        """
        infoLines = self.__repr__()
        info = infoLines.splitlines()[1:-1] # remove enclosing braces from repr
        for i,line in enumerate(info):
            if line.find('openGLext')>-1: # swap order for OpenGL extensions -- much easier to read
                tmp = line.split(':')
                info[i] = ': '.join(['   '+tmp[1].replace(',',''),tmp[0].replace('    ','')+','])
            info[i] = info[i].rstrip(',')
        info = '\n'.join(info).replace('"','')+'\n'
        return info
    
    def _type(self):
        # for debugging
        sk = self.keys()
        sk.sort()
        for k in sk:
            print k,type(self[k]),self[k]
            
def _getHashGitHead(dir=''):
    origDir = os.getcwd()
    os.chdir(dir)
    try:
        git_hash = shellCall("git rev-parse --verify HEAD")
    except OSError:
        os.chdir(origDir)
        return None
    except WindowsError: # not defined on mac; OSError should catch lack of git
        os.chdir(origDir)
        return None
    os.chdir(origDir)
    git_branches = shellCall("git branch")
    git_branch = [line.split()[1] for line in git_branches.splitlines() if line.startswith('*')]
    if len(git_branch):
        return git_branch[0] + ' ' + git_hash.strip()
    else: # dir is not a git repo
        return None
    
def _getSvnVersion(file):
    """Tries to discover the svn version (revision #) for a file.
    
    Not thoroughly tested; completely untested on Windows Vista, Win 7, FreeBSD
    
    :Author:
        - 2010 written by Jeremy Gray
    """
    if not (os.path.exists(file) and os.path.isdir(os.path.join(os.path.dirname(file),'.svn'))):
        return None, None, None
    svnRev, svnLastChangedRev, svnUrl = None, None, None
    if sys.platform in ['darwin', 'freebsd'] or sys.platform.startswith('linux'):
        try:
            svninfo,stderr = shellCall('svn info "'+file+'"', stderr=True) # expects a filename, not dir
        except:
            svninfo = ''
        for line in svninfo.splitlines():
            if line.find('URL:') == 0:
                svnUrl = line.split()[1]
            elif line.find('Revision: ') == 0:
                svnRev = line.split()[1]
            elif line.find('Last Changed Rev') == 0:
                svnLastChangedRev = line.split()[3]
    else: # worked for me on Win XP sp2 with TortoiseSVN (SubWCRev.exe)
        try:
            stdout,stderr = shellCall('subwcrev "'+file+'"', stderr=True)
        except:
            stdout = ''
        for line in stdout.splitlines():
            if line.find('Last committed at revision') == 0:
                svnRev = line.split()[4]
            elif line.find('Updated to revision') == 0:
                svnLastChangedRev = line.split()[3]
    return svnRev, svnLastChangedRev, svnUrl

def _getHgVersion(file):
    """Tries to discover the mercurial (hg) parent and id of a file.
    
    Not thoroughly tested; completely untested on Windows Vista, Win 7, FreeBSD
    
    :Author:
        - 2010 written by Jeremy Gray
    """
    if not os.path.exists(file) or not os.path.isdir(os.path.join(os.path.dirname(file),'.hg')):
        return None
    try:
        hgParentLines,err = shellCall('hg parents "'+file+'"', stderr=True)
        changeset = hgParentLines.splitlines()[0].split()[-1]
    except:
        changeset = ''
    try:
        hgID,err = shellCall('hg id -nibt "'+os.path.dirname(file)+'"', stderr=True)
    except:
        if err: hgID = ''
    
    if len(hgID) or len(changeset):
        return hgID.strip()+' | parent: '+changeset.strip()
    else:
        return None

def _getUserNameUID():
    """Return user name, UID.
    
    UID values can be used to infer admin-level:
    -1=undefined, 0=full admin/root, >499=assume non-admin/root (>999 on debian-based)
    
    :Author:
        - 2010 written by Jeremy Gray
    """
    try:
        user = os.environ['USER']
    except KeyError:
        user = os.environ['USERNAME']
    uid = '-1' 
    if sys.platform not in ['win32']:
        uid = shellCall('id -u')
    else:
        uid = '1000'
        if haveCtypes and ctypes.windll.shell32.IsUserAnAdmin():
            uid = '0'
    return str(user), int(uid)

def _getSha1hexDigest(thing, file=False):
    """Returns base64 / hex encoded sha1 digest of str(thing), or of a file contents
    return None if a file is requested but no such file exists
    
    :Author:
        - 2010 Jeremy Gray; updated 2011 to be more explicit, 2012 to remove sha.new()

    >>> _getSha1hexDigest('1')
    '356a192b7913b04c54574d18c28d46e6395428ab'
    >>> _getSha1hexDigest(1)
    '356a192b7913b04c54574d18c28d46e6395428ab'
    """
    digester = hashlib.sha1()
    if file:
        filename = thing
        if os.path.isfile(filename):
            f = open(filename,'rb')
            digester.update(f.read()) # check file size < available RAM first? or update in chunks?
            f.close()
        else:
            return None
    else:
        digester.update(str(thing))
    return digester.hexdigest()


def getRAM():
    """Return system's physical RAM & available RAM, in M.
    
    Slow on Mac and Linux; fast on Windows. psutils is good but another dep."""
    freeRAM = 'unknown'
    totalRAM = 'unknown'
    
    if sys.platform == 'darwin':
        so,se = core.shellCall('vm_stat', stderr=True)
        lines = so.splitlines()
        pageIndex = lines[0].find('page size of ')
        if  pageIndex > -1:
            pagesize = int(lines[0][pageIndex + len('page size of '):].split()[0])
            free = float(lines[1].split()[-1])
            freeRAM = int(free * pagesize / 1048576.)  # M
            pieces = [lines[i].split()[-1] for i in range(1,6)]
            total = sum(map(float, pieces))
            totalRAM = int(total * pagesize / 1048576.)  # M
    elif sys.platform == 'win32':
        if not haveCtypes:
            return 'unknown', 'unknown'
        try:
            # http://code.activestate.com/recipes/511491/
            # modified by Sol Simpson for 64-bit systems (also ok for 32-bit)
            kernel32 = ctypes.windll.kernel32
            class MEMORYSTATUS(ctypes.Structure):
                _fields_ = [
                ('dwLength', DWORD),
                ('dwMemoryLoad', DWORD),
                ('dwTotalPhys', DWORDLONG), # ctypes.c_ulonglong for 64-bit
                ('dwAvailPhys', DWORDLONG),
                ('dwTotalPageFile', DWORDLONG),
                ('dwAvailPageFile', DWORDLONG),
                ('dwTotalVirtual', DWORDLONG),
                ('dwAvailVirtual', DWORDLONG),
                ('ullAvailExtendedVirtual', DWORDLONG),
                ]
            memoryStatus = MEMORYSTATUS()
            memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUS)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(memoryStatus))

            totalRAM = int(memoryStatus.dwTotalPhys / 1048576.) # M
            freeRAM = int(memoryStatus.dwAvailPhys / 1048576.) # M
        except:
            pass
    elif sys.platform.startswith('linux'):
        try:
            so,se = core.shellCall('free', stderr=True)
            lines = so.splitlines()
            freeRAM = int(int(lines[1].split()[3]) / 1024.)  # M
            totalRAM = int(int(lines[1].split()[1]) / 1024.)
        except:
            pass
    else: # bsd, works on mac too
        try:
            total = core.shellCall('sysctl -n hw.memsize')
            totalRAM = int(int(total) / 1048576.)
            # not sure how to get available phys mem
        except:
            pass
    return totalRAM, freeRAM
