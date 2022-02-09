#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""This module has tools for fetching data about the system or the current
Python process. Such info can be useful for understanding the context in which
an experiment was run.
"""

__all__ = [
    'RunTimeInfo',
    'getMemoryUsage',
    'getRAM',
    'APP_FLAG_LIST',  # user might want to see these
    'APP_IGNORE_LIST',
    # These should be hidden, but I'm unsure if somewhere `import *` is being
    # used so I'm adding them for now to prevent breakage. - mdc
    '_getUserNameUID',
    '_getHashGitHead',
    '_getSha1hexDigest',
    '_getHgVersion',
    '_getSvnVersion',
    '_thisProcess'
]

import sys
import os
import platform
import io

from pyglet.gl import gl_info, GLint, glGetIntegerv, GL_MAX_ELEMENTS_VERTICES
import numpy
import scipy
import matplotlib
import pyglet
try:
    import ctypes
    haveCtypes = True
except ImportError:
    haveCtypes = False
import hashlib
import wx
import locale
import subprocess
import psutil

from psychopy import visual, logging, core, data, web
from psychopy.core import shellCall
from psychopy.platform_specific import rush
from psychopy import __version__ as psychopyVersion

# List of applications to flag as problematic while running an experiment. These
# apps running in the background consume resources (CPU, GPU and memory) which
# may interfere with a PsychoPy experiment. If these apps are allowed to run, it
# may result in poor timing, glitches, dropped frames, etc.
#
# Names that appear here are historically known to affect performance. The user
# can check if these processes are running using `RunTimeInfo()` and shut them
# down. App names are matched in a case insensitive way from the start of the
# name string obtained from `psutils`.
APP_FLAG_LIST = [
    # web browsers can burn CPU cycles
    'Firefox',
    'Safari',
    'Explorer',
    'Netscape',
    'Opera',
    'Google Chrome',
    'Dropbox',
    'BitTorrent',
    'iTunes',  # but also matches iTunesHelper (add to ignore-list)
    'mdimport',
    'mdworker',
    'mds',  # can have high CPU
    # productivity
    'Office',
    'KeyNote',
    'Pages',
    'LaunchCFMApp',  # on mac, MS Office (Word etc) can be launched by this
    'Skype',
    'VirtualBox',
    'VBoxClient',  # virtual machine as host or client
    'Parallels',
    'Coherence',
    'prl_client_app',
    'prl_tools_service',
    'VMware'  # just a guess
    # gaming, may need to be started for VR support
    'Steam'
    'Oculus'
]

# Apps listed here will not be flagged if a partial match exist in
# `APP_FLAG_LIST`. This list is checked first before `RunTimeInfo()` looks for a
# name in `APP_FLAG_LIST`. You can also add names here to eliminate ambiguity,
# for instance if 'Dropbox' is in `APP_FLAG_LIST`, then `DropboxUpdate` will
# also be flagged. You can prevent this by adding 'DropboxUpdate' to
# `APP_IGNORE_LIST`.
APP_IGNORE_LIST = [
    # shells
    'ps',
    'login',
    '-tcsh',
    'bash',
    # helpers and updaters
    'iTunesHelper',
    'DropboxUpdate',
    'OfficeClickToRun'
]


class RunTimeInfo(dict):
    """Returns a snapshot of your configuration at run-time, for immediate or
    archival use.

    Returns a dict-like object with info about PsychoPy, your experiment script,
    the system & OS, your window and monitor settings (if any), python &
    packages, and openGL.

    If you want to skip testing the refresh rate, use 'refreshTest=None'

    Example usage: see runtimeInfo.py in coder demos.

    Parameters
    ----------
    win : :class:`~psychopy.visual.Window`, False or None
        What window to use for refresh rate testing (if any) and settings.
        `None` -> temporary window using defaults; `False` -> no window created,
        used, nor profiled; a `Window()` instance you have already created one.
    author : str or None
        `None` will try to autodetect first __author__ in sys.argv[0], whereas
        a `str` being user-supplied author info (of an experiment).
    version : str or None
        `None` try to autodetect first __version__ in sys.argv[0] or `str` being
        the user-supplied version info (of an experiment).
    verbose : bool
        Show additional information. Default is `False`.
    refreshTest : str, bool or None
        True or 'grating' = assess refresh average, median, and SD of 60
        win.flip()s, using visual.getMsPerFrame() 'grating' = show a visual
        during the assessment; `True` = assess without a visual. Default is
        `'grating'`.
    userProcsDetailed: bool
        Get details about concurrent user's processes (command, process-ID).
        Default is `False`.

    Returns
    -------
    A flat dict (but with several groups based on key names):

    psychopy : version, rush() availability
        psychopyVersion, psychopyHaveExtRush, git branch and current commit hash
        if available

    experiment : author, version, directory, name, current time-stamp, SHA1
        digest, VCS info (if any, svn or hg only),
        experimentAuthor, experimentVersion, ...

    system : hostname, platform, user login, count of users,
        user process info (count, cmd + pid), flagged processes
        systemHostname, systemPlatform, ...

    window : (see output; many details about the refresh rate, window,
        and monitor; units are noted)
        windowWinType, windowWaitBlanking, ...windowRefreshTimeSD_ms,
        ... windowMonitor.<details>, ...

    python : version of python, versions of key packages
        (wx, numpy, scipy, matplotlib, pyglet, pygame)
        pythonVersion, pythonScipyVersion, ...

    openGL : version, vendor, rendering engine, plus info on whether
        several extensions are present
        openGLVersion, ..., openGLextGL_EXT_framebuffer_object, ...

    """
    # Author: 2010 written by Jeremy Gray, input from Jon Peirce and
    # Alex Holcombe
    def __init__(self, author=None, version=None, win=None,
                 refreshTest='grating', userProcsDetailed=False,
                 verbose=False):
        # this will cause an object to be created with all the same methods as
        # a dict
        dict.__init__(self)

        self['psychopyVersion'] = psychopyVersion
        # NB: this looks weird, but avoids setting high-priority incidentally
        self['psychopyHaveExtRush'] = rush(False)
        d = os.path.abspath(os.path.dirname(__file__))
        githash = _getHashGitHead(d)  # should be .../psychopy/psychopy/
        if githash:
            self['psychopyGitHead'] = githash

        self._setExperimentInfo(author, version, verbose)
        self._setSystemInfo()  # current user, locale, other software
        self._setCurrentProcessInfo(verbose, userProcsDetailed)

        # need a window for frame-timing, and some openGL drivers want
        # a window open
        if win is None:  # make a temporary window, later close it
            win = visual.Window(
                fullscr=True, monitor="testMonitor", autoLog=False)
            refreshTest = 'grating'
            usingTempWin = True
        elif win != False:
            # we were passed a window instance, use it:
            usingTempWin = False
            self.winautoLog = win.autoLog
            win.autoLog = False
        else:  # don't want any window
            usingTempWin = False

        if win:
            self._setWindowInfo(win, verbose, refreshTest, usingTempWin)

        self['pythonVersion'] = sys.version.split()[0]
        if verbose:
            self._setPythonInfo()
            if win:
                self._setOpenGLInfo()
        if usingTempWin:
            win.close()  # close after doing openGL
        elif win != False:
            win.autoLog = self.winautoLog  # restore

    def _setExperimentInfo(self, author, version, verbose):
        """Auto-detect __author__ and __version__ in sys.argv[0] (= the
        # users's script)
        """
        if not author or not version:
            lines = ''
            if os.path.isfile(sys.argv[0]):
                with io.open(sys.argv[0], 'r', encoding='utf-8-sig') as f:
                    lines = f.read()
            if not author and '__author__' in lines:
                linespl = lines.splitlines()
                while linespl[0].find('__author__') == -1:
                    linespl.pop(0)
                auth = linespl[0]
                if len(auth) and '=' in auth:
                    try:
                        author = str(eval(auth[auth.find('=') + 1:]))
                    except Exception:
                        pass
            if not version and '__version__' in lines:
                linespl = lines.splitlines()
                while linespl[0].find('__version__') == -1:
                    linespl.pop(0)
                ver = linespl[0]
                if len(ver) and ver.find('=') > 0:
                    try:
                        version = str(eval(ver[ver.find('=') + 1:]))
                    except Exception:
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
        scriptPath = os.path.abspath(sys.argv[0])
        key = 'experimentScript.digestSHA1'
        self[key] = _getSha1hexDigest(scriptPath, isfile=True)
        # subversion revision?
        try:
            svnrev, last, url = _getSvnVersion(scriptPath)  # svn revision
            if svnrev:  # or verbose:
                self['experimentScript.svnRevision'] = svnrev
                self['experimentScript.svnRevLast'] = last
                self['experimentScript.svnRevURL'] = url
        except Exception:
            pass
        # mercurical revision?
        try:
            hgChangeSet = _getHgVersion(scriptPath)
            if hgChangeSet:  # or verbose:
                self['experimentScript.hgChangeSet'] = hgChangeSet
        except Exception:
            pass

        # when was this run?
        self['experimentRunTime.epoch'] = core.getAbsTime()
        fmt = "%Y_%m_%d %H:%M (Year_Month_Day Hour:Min)"
        self['experimentRunTime'] = data.getDateStr(format=fmt)

    def _setSystemInfo(self):
        """System info
        """
        # machine name
        self['systemHostName'] = platform.node()

        self['systemMemTotalRAM'], self['systemMemFreeRAM'] = getRAM()

        # locale information:
        # (None, None) -> str
        loc = '.'.join([str(x) for x in locale.getlocale()])
        if loc == 'None.None':
            loc = locale.setlocale(locale.LC_ALL, '')
        # == the locale in use, from OS or user-pref
        self['systemLocale'] = loc

        # platform name, etc
        if sys.platform in ['darwin']:
            OSXver, _junk, architecture = platform.mac_ver()
            platInfo = 'darwin ' + OSXver + ' ' + architecture
            # powerSource = ...
        elif sys.platform.startswith('linux'):
            platInfo = 'linux ' + platform.release()
            # powerSource = ...
        elif sys.platform in ['win32']:
            platInfo = 'windowsversion=' + repr(sys.getwindowsversion())
            # powerSource = ...
        else:
            platInfo = ' [?]'
            # powerSource = ...
        self['systemPlatform'] = platInfo
        # self['systemPowerSource'] = powerSource

        # count all unique people (user IDs logged in), and find current user
        # name & UID
        self['systemUser'], self['systemUserID'] = _getUserNameUID()
        try:
            users = shellCall("who -q").splitlines()[0].split()
            self['systemUsersCount'] = len(set(users))
        except Exception:
            self['systemUsersCount'] = False

        # when last rebooted?
        try:
            lastboot = shellCall("who -b").split()
            self['systemRebooted'] = ' '.join(lastboot[2:])
        except Exception:  # windows
            sysInfo = shellCall('systeminfo').splitlines()
            lastboot = [line for line in sysInfo if line.startswith(
                "System Up Time") or line.startswith("System Boot Time")]
            lastboot += ['[?]']  # put something in the list just in case
            self['systemRebooted'] = lastboot[0].strip()

        # R (and r2py) for stats:
        try:
            Rver = shellCall(["R", "--version"])
            Rversion = Rver.splitlines()[0]
            if Rversion.startswith('R version'):
                self['systemRavailable'] = Rversion.strip()
            try:
                import rpy2
                self['systemRpy2'] = rpy2.__version__
            except ImportError:
                pass
        except Exception:
            pass

        # encryption / security tools:
        try:
            vers, se = shellCall('openssl version', stderr=True)
            if se:
                vers = str(vers) + se.replace('\n', ' ')[:80]
            if vers.strip():
                self['systemSec.OpenSSLVersion'] = vers
        except Exception:
            pass
        try:
            so = shellCall(['gpg', '--version'])
            if so.find('GnuPG') > -1:
                self['systemSec.GPGVersion'] = so.splitlines()[0]
                _home = [line.replace('Home:', '').lstrip()
                         for line in so.splitlines()
                         if line.startswith('Home:')]
                self['systemSec.GPGHome'] = ''.join(_home)
        except Exception:
            pass
        try:
            import ssl
            self['systemSec.pythonSSL'] = True
        except ImportError:
            self['systemSec.pythonSSL'] = False

        # pyo for sound:
            import importlib.util
            if importlib.util.find_spec('pyo') is not None:
                self['systemPyoVersion'] = '-'

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
        # web.setupProxy() & web.testProxy(web.proxies)  # can be slow
        # to fail if there's no connection
        self['systemHaveInternetAccess'] = web.haveInternetAccess()
        if not self['systemHaveInternetAccess']:
            self['systemHaveInternetAccess'] = 'False (proxies not attempted)'

    def _setCurrentProcessInfo(self, verbose=False, userProcsDetailed=False):
        """What other processes are currently active for this user?
        """
        systemProcPsu = []             # found processes
        systemProcPsuFlagged = []      # processes which are flagged
        systemUserProcFlaggedPID = []  # PIDs of those processes
        # lower case these names for matching
        appFlagListLowerCase = [pn.lower() for pn in APP_FLAG_LIST]
        appIgnoreListLowerCase = [pn.lower() for pn in APP_IGNORE_LIST]

        # iterate over processes retrieved by psutil
        for proc in psutil.process_iter(attrs=None, ad_value=None):
            try:
                processFullName = proc.name()  # get process name
                processPid = proc.pid
                processName = processFullName.lower()  # use for matching only
            except (psutil.AccessDenied, psutil.NoSuchProcess,
                    psutil.ZombieProcess):
                continue  # skip iteration on exception

            # check if process is in ignore list, skip if so
            for appIgnore in appIgnoreListLowerCase:
                # case-insensitive match from the start of string
                if processName.startswith(appIgnore):
                    break
            else:
                # if we get here, the name isn't in the ignore list
                for appFlag in appFlagListLowerCase:
                    if processName.startswith(appFlag):
                        # append actual name and PID to output lists
                        systemProcPsuFlagged.append(processFullName)
                        systemUserProcFlaggedPID.append(processPid)
                        break

            systemProcPsu.append(processName)

        # add items to dictionary
        self['systemUserProcCount'] = len(systemProcPsu)
        self['systemUserProcFlagged'] = systemProcPsuFlagged

        # if the user wants more ...
        if verbose and userProcsDetailed:
            self['systemUserProcCmdPid'] = systemProcPsu  # is this right?
            self['systemUserProcFlaggedPID'] = systemUserProcFlaggedPID

        # CPU speed (will depend on system busy-ness)
        d = numpy.array(numpy.linspace(0., 1., 1000000))
        t0 = core.getTime()
        numpy.std(d)
        t = core.getTime() - t0
        del d
        self['systemTimeNumpySD1000000_sec'] = t

    def _setWindowInfo(self, win, verbose=False, refreshTest='grating',
                       usingTempWin=True):
        """Find and store info about the window: refresh rate,
        configuration info.
        """

        if refreshTest in ['grating', True]:
            wantVisual = bool(refreshTest == 'grating')
            a, s, m = visual.getMsPerFrame(win, nFrames=120,
                                           showVisual=wantVisual)
            self['windowRefreshTimeAvg_ms'] = a
            self['windowRefreshTimeMedian_ms'] = m
            self['windowRefreshTimeSD_ms'] = s
        if usingTempWin:
            return

        # These 'configuration lists' control what attributes are reported.
        # All desired attributes/properties need a legal internal name,
        # e.g., win.winType. If an attr is callable, its gets called with
        # no arguments, e.g., win.monitor.getWidth()
        winAttrList = ['winType', '_isFullScr', 'units',
                       'monitor', 'pos', 'screen', 'rgb', 'size']
        winAttrListVerbose = ['allowGUI', 'useNativeGamma',
                              'recordFrameIntervals', 'waitBlanking',
                              '_haveShaders', 'refreshThreshold']
        if verbose:
            winAttrList += winAttrListVerbose

        monAttrList = ['name', 'getDistance', 'getWidth', 'currentCalibName']
        monAttrListVerbose = ['getGammaGrid', 'getLinearizeMethod',
                              '_gammaInterpolator', '_gammaInterpolator2']
        if verbose:
            monAttrList += monAttrListVerbose
        if 'monitor' in winAttrList:
            # replace 'monitor' with all desired monitor.<attribute>
            # retain list-position info, put monitor stuff there
            i = winAttrList.index('monitor')
            del winAttrList[i]
            for monAttr in monAttrList:
                winAttrList.insert(i, 'monitor.' + monAttr)
                i += 1
        for winAttr in winAttrList:
            try:
                attrValue = eval('win.' + winAttr)
            except AttributeError:
                msg = ('AttributeError in RuntimeInfo._setWindowInfo(): '
                       'Window instance has no attribute')
                logging.warning(0, msg, winAttr)
                continue
            if hasattr(attrValue, '__call__'):
                try:
                    a = attrValue()
                    attrValue = a
                except Exception:
                    msg = ('Warning: could not get a value from win. '
                           '%s()  (expects arguments?)' % winAttr)
                    print(msg)
                    continue
            while winAttr[0] == '_':
                winAttr = winAttr[1:]
            winAttr = winAttr[0].capitalize() + winAttr[1:]
            winAttr = winAttr.replace('Monitor._', 'Monitor.')
            if winAttr in ('Pos', 'Size'):
                winAttr += '_pix'
            if winAttr in ('Monitor.getWidth', 'Monitor.getDistance'):
                winAttr += '_cm'
            if winAttr in ('RefreshThreshold'):
                winAttr += '_sec'
            self['window' + winAttr] = attrValue

    def _setPythonInfo(self):
        """External python packages, python details
        """
        self['pythonNumpyVersion'] = numpy.__version__
        self['pythonScipyVersion'] = scipy.__version__
        self['pythonWxVersion'] = wx.version()
        self['pythonMatplotlibVersion'] = matplotlib.__version__
        self['pythonPygletVersion'] = pyglet.version
        try:
            from pygame import __version__ as pygameVersion
        except ImportError:
            pygameVersion = '(no pygame)'
        self['pythonPygameVersion'] = pygameVersion

        # Python gory details:
        self['pythonFullVersion'] = sys.version.replace('\n', ' ')
        self['pythonExecutable'] = sys.executable

    def _setOpenGLInfo(self):
        # OpenGL info:
        self['openGLVendor'] = gl_info.get_vendor()
        self['openGLRenderingEngine'] = gl_info.get_renderer()
        self['openGLVersion'] = gl_info.get_version()
        GLextensionsOfInterest = ('GL_ARB_multitexture',
                                  'GL_EXT_framebuffer_object',
                                  'GL_ARB_fragment_program',
                                  'GL_ARB_shader_objects',
                                  'GL_ARB_vertex_shader',
                                  'GL_ARB_texture_non_power_of_two',
                                  'GL_ARB_texture_float', 'GL_STEREO')

        for ext in GLextensionsOfInterest:
            self['openGLext.' + ext] = bool(gl_info.have_extension(ext))

        maxVerts = GLint()
        glGetIntegerv(GL_MAX_ELEMENTS_VERTICES, maxVerts)
        self['openGLmaxVerticesInVertexArray'] = maxVerts.value

    def __repr__(self):
        """Return a string that is a legal python (dict), and close
        to YAML, .ini, and configObj syntax
        """
        info = '{\n#[ PsychoPy3 RuntimeInfoStart ]\n'
        sections = ['PsychoPy', 'Experiment',
                    'System', 'Window', 'Python', 'OpenGL']
        for sect in sections:
            info += '  #[[ %s ]] #---------\n' % (sect)
            sectKeys = [k for k in list(self.keys(
            )) if k.lower().find(sect.lower()) == 0]
            # get keys for items matching this section label;
            #  use reverse-alpha order if easier to read:
            revSet = ('PsychoPy', 'Window', 'Python', 'OpenGL')
            sectKeys.sort(reverse=bool(sect in revSet))
            for k in sectKeys:
                selfk = self[k]  # alter a copy for display purposes
                try:
                    if type(selfk) == type('abc'):
                        selfk = selfk.replace('"', '').replace('\n', ' ')
                    elif '_ms' in k:  # type(selfk) == type(0.123):
                        selfk = "%.3f" % selfk
                    elif '_sec' in k:
                        selfk = "%.4f" % selfk
                    elif '_cm' in k:
                        selfk = "%.1f" % selfk
                except Exception:
                    pass
                # then strcat unique proc names
                if (k in ('systemUserProcFlagged', 'systemUserProcCmdPid') and
                        selfk is not None and
                        len(selfk)):
                    prSet = []
                    for pr in self[k]:  # str -> list of lists
                        if ' ' in pr:  # add single quotes if file has spaces
                            pr = "'" + pr + "'"
                        # first item in sublist is proc name (CMD)
                        prSet += [pr]
                    selfk = ' '.join(list(set(prSet)))
                # suppress display PID info -- useful at run-time, never useful
                # in an archive
                if k != 'systemUserProcFlaggedPID':
                    info += '    "%s": "%s",\n' % (k, selfk)
        info += '#[ PsychoPy3 RuntimeInfoEnd ]\n}\n'
        return info

    def __str__(self):
        """Return a string intended for printing to a log file
        """
        infoLines = self.__repr__()
        # remove enclosing braces from repr
        info = infoLines.splitlines()[1:-1]
        for i, line in enumerate(info):
            if 'openGLext' in line:
                # swap order for OpenGL extensions -- much easier to read
                tmp = line.split(':')
                info[i] = ': '.join(['   ' + tmp[1].replace(',', ''),
                                     tmp[0].replace('    ', '') + ','])
            info[i] = info[i].rstrip(',')
        info = '\n'.join(info).replace('"', '') + '\n'
        return info


def _getHashGitHead(gdir='.'):
    if not os.path.isdir(gdir):
        raise OSError('not a directory')
    try:
        git_hash = subprocess.check_output('git rev-parse --verify HEAD',
                                           cwd=gdir,
                                           shell=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        return None  # no git
    git_branches = subprocess.check_output('git branch', cwd=gdir, shell=True)
    git_branch = [line.split()[1] for line in git_branches.splitlines()
                  if line.startswith(b'*')]
    if len(git_branch):
        return "{} {}".format(git_branch[0], git_hash.strip())
    else:
        return '(unknown branch)'


def _getSvnVersion(filename):
    """Tries to discover the svn version (revision #) for a file.

    Not thoroughly tested; untested on Windows Vista, Win 7, FreeBSD

    :Author:
        - 2010 written by Jeremy Gray
    """
    if not (os.path.exists(filename) and
            os.path.isdir(os.path.join(os.path.dirname(filename), '.svn'))):
        return None, None, None
    svnRev, svnLastChangedRev, svnUrl = None, None, None
    if (sys.platform in ('darwin', 'freebsd') or
            sys.platform.startswith('linux')):
        try:
            # expects a filename, not dir
            svninfo = shellCall(['svn', 'info', filename])
        except Exception:
            svninfo = ''
        for line in svninfo.splitlines():
            if line.startswith('URL:'):
                svnUrl = line.split()[1]
            elif line.startswith('Revision: '):
                svnRev = line.split()[1]
            elif line.startswith('Last Changed Rev'):
                svnLastChangedRev = line.split()[3]
    else:
        # worked for me on Win XP sp2 with TortoiseSVN (SubWCRev.exe)
        try:
            stdout = shellCall(['subwcrev', filename])
        except Exception:
            stdout = ''
        for line in stdout.splitlines():
            if line.startswith('Last committed at revision'):
                svnRev = line.split()[4]
            elif line.startswith('Updated to revision'):
                svnLastChangedRev = line.split()[3]
    return svnRev, svnLastChangedRev, svnUrl


def _getHgVersion(filename):
    """Tries to discover the mercurial (hg) parent and id of a file.

    Not thoroughly tested; untested on Windows Vista, Win 7, FreeBSD

    :Author:
        - 2010 written by Jeremy Gray
    """
    dirname = os.path.dirname
    if (not os.path.exists(filename) or
            not os.path.isdir(os.path.join(dirname(filename), '.hg'))):
        return None
    try:
        hgParentLines, err = shellCall(['hg', 'parents', filename],
                                       stderr=True)
        changeset = hgParentLines.splitlines()[0].split()[-1]
    except Exception:
        changeset = ''
    try:
        hgID, err = shellCall(['hg', 'id', '-nibt', dirname(filename)],
                              stderr=True)
    except Exception:
        if err:
            hgID = ''

    if len(hgID) or len(changeset):
        return hgID.strip() + ' | parent: ' + changeset.strip()
    else:
        return None


def _getUserNameUID():
    """Return user name, UID.

    UID values can be used to infer admin-level:
    -1=undefined, 0=full admin/root,
    >499=assume non-admin/root (>999 on debian-based)

    :Author:
        - 2010 written by Jeremy Gray
    """
    user = os.environ.get('USER', None) or os.environ.get('USERNAME', None)
    if not user:
        return 'undefined', '-1'

    if sys.platform not in ['win32']:
        uid = shellCall('id -u')
    else:
        uid = '1000'
        if haveCtypes and ctypes.windll.shell32.IsUserAnAdmin():
            uid = '0'
    return str(user), int(uid)


def _getSha1hexDigest(thing, isfile=False):
    """Returns base64 / hex encoded sha1 digest of str(thing), or
    of a file contents. Return None if a file is requested but no such
    file exists

    :Author:
        - 2010 Jeremy Gray; updated 2011 to be more explicit,
        - 2012 to remove sha.new()

    >>> _getSha1hexDigest('1')
    '356a192b7913b04c54574d18c28d46e6395428ab'
    >>> _getSha1hexDigest(1)
    '356a192b7913b04c54574d18c28d46e6395428ab'
    """
    digester = hashlib.sha1()
    if isfile:
        filename = thing
        if os.path.isfile(filename):
            f = open(filename, 'rb')
            # check file size < available RAM first? or update in chunks?
            digester.update(f.read())
            f.close()
        else:
            return None
    else:
        digester.update(str(thing))
    return digester.hexdigest()


def getRAM():
    """Return system's physical RAM & available RAM, in M.
    """
    totalRAM, available = psutil.virtual_memory()[0:2]
    return totalRAM / 1048576., available / 1048576.


# faster to get the current process only once:
_thisProcess = psutil.Process()


def getMemoryUsage():
    """Get the memory (RAM) currently used by this Python process, in M.
    """
    return _thisProcess.memory_info()[0] / 1048576.
