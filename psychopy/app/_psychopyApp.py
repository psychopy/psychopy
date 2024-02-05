#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import traceback
from pathlib import Path

from psychopy.app.colorpicker import PsychoColorPicker

import sys
import pickle
import tempfile
import mmap
import time
import io
import argparse

from psychopy.app.themes import icons, colors, handlers

profiling = False  # turning on will save profile files in currDir

import psychopy
from psychopy import prefs
from pkg_resources import parse_version
from . import urls
from . import frametracker
from . import themes
from . import console


if not hasattr(sys, 'frozen'):
    try:
        import wxversion
        haveWxVersion = True
    except ImportError:
        haveWxVersion = False  # if wxversion doesn't exist hope for the best
    if haveWxVersion:
        wxversion.ensureMinimal('2.8')  # because this version has agw
import wx
try:
    from agw import advancedsplash as AS
except ImportError:  # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.advancedsplash as AS

# from .plugin_manager import saveStartUpPluginsConfig

from psychopy.localization import _translate
# NB keep imports to a minimum here because splash screen has not yet shown
# e.g. coder and builder are imported during app.__init__ because they
# take a while

# needed by splash screen for the path to resources/psychopySplash.png
import ctypes
from psychopy import logging, __version__
from psychopy import projects
from . import connections
from .utils import FileDropTarget
import os
import weakref

# knowing if the user has admin priv is generally a good idea for security.
# not actually needed; psychopy should never need anything except normal user
# see older versions for code to detect admin (e.g., v 1.80.00)

# Enable high-dpi support if on Windows. This fixes blurry text rendering.
if sys.platform == 'win32':
    # get the preference for high DPI
    if 'highDPI' in psychopy.prefs.app.keys():  # check if we have the option
        enableHighDPI = psychopy.prefs.app['highDPI']

        # check if we have OS support for it
        if enableHighDPI:
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(enableHighDPI)
            except OSError:
                logging.warn(
                    "High DPI support is not appear to be supported by this "
                    "version of Windows. Disabling in preferences.")

                psychopy.prefs.app['highDPI'] = False
                psychopy.prefs.saveUserPrefs()


class MenuFrame(wx.Frame, themes.handlers.ThemeMixin):
    """A simple empty frame with a menubar, should be last frame closed on mac
    """

    def __init__(self, parent=None, ID=-1, app=None, title="PsychoPy"):

        wx.Frame.__init__(self, parent, ID, title, size=(1, 1))
        self.app = app

        self.menuBar = wx.MenuBar()

        self.viewMenu = wx.Menu()
        self.menuBar.Append(self.viewMenu, _translate('&View'))
        mtxt = _translate("&Open Builder view\t%s")
        self.app.IDs.openBuilderView = self.viewMenu.Append(wx.ID_ANY,
                             mtxt,
                             _translate("Open a new Builder view")).GetId()
        self.Bind(wx.EVT_MENU, self.app.showBuilder,
                  id=self.app.IDs.openBuilderView)
        mtxt = _translate("&Open Coder view\t%s")
        self.app.IDs.openCoderView = self.viewMenu.Append(wx.ID_ANY,
                             mtxt,
                             _translate("Open a new Coder view")).GetId()
        self.Bind(wx.EVT_MENU, self.app.showCoder,
                  id=self.app.IDs.openCoderView)
        mtxt = _translate("&Quit\t%s")
        item = self.viewMenu.Append(wx.ID_EXIT, mtxt % self.app.keys['quit'],
                                    _translate("Terminate the program"))
        self.Bind(wx.EVT_MENU, self.app.quit, id=item.GetId())
        self.SetMenuBar(self.menuBar)
        self.Show()


class IDStore(dict):
    """A simpe class that works like a dict but you can access attributes
    like standard python attrs. Useful to replace the previous pre-made
    app.IDs (wx.NewID() is no longer recommended or safe)
    """
    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value


class _Showgui_Hack():
    """Class with side-effect of restoring wx window switching under wx-3.0

    - might only be needed on some platforms (Mac 10.9.4 needs it for me);
    - needs to be launched as an external script
    - needs to be separate: seg-faults as method of PsychoPyApp or in-lined
    - unlear why it works or what the deeper issue is, blah
    - called at end of PsychoPyApp.onInit()
    """

    def __init__(self):
        super(_Showgui_Hack, self).__init__()
        from psychopy import core
        import os
        # should be writable:
        noopPath = os.path.join(psychopy.prefs.paths['userPrefsDir'],
                                'showgui_hack.py')
        # code to open & immediately close a gui (= invisibly):
        if not os.path.isfile(noopPath):
            code = """from psychopy import gui
                dlg = gui.Dlg().Show()  # non-blocking
                try: 
                    dlg.Destroy()  # might as well
                except Exception: 
                    pass"""
            with open(noopPath, 'wb') as fd:
                fd.write(bytes(code))
        # append 'w' for pythonw seems not needed
        core.shellCall([sys.executable, noopPath])


class PsychoPyApp(wx.App, handlers.ThemeMixin):
    _called_from_test = False  # pytest needs to change this

    def __init__(self, arg=0, testMode=False, **kwargs):
        """With a wx.App some things get done here, before App.__init__
        then some further code is launched in OnInit() which occurs after
        """
        if profiling:
            import cProfile
            import time
            profile = cProfile.Profile()
            profile.enable()
            t0 = time.time()

        from . import setAppInstance
        setAppInstance(self)

        self._appLoaded = False  # set to true when all frames are created
        self.builder = None
        self.coder = None
        self.runner = None
        self.version = psychopy.__version__
        # array of handles to extant Pavlovia buttons
        self.pavloviaButtons = {
            'user': [],
            'project': [],
        }
        # set default paths and prefs
        self.prefs = psychopy.prefs
        self._currentThemeSpec = None

        self.keys = self.prefs.keys
        self.prefs.pageCurrent = 0  # track last-viewed page, can return there
        self.IDs = IDStore()
        self.urls = urls.urls
        self.quitting = False
        # check compatibility with last run version (before opening windows)
        self.firstRun = False
        self.testMode = testMode
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        self._stdoutFrame = None

        # set as false to disable loading plugins on startup
        self._safeMode = kwargs.get('safeMode', True)

        # Shared memory used for messaging between app instances, this gets
        # allocated when `OnInit` is called.
        self._sharedMemory = None
        self._singleInstanceChecker = None  # checker for instances
        self._timer = None
        # Size of the memory map buffer, needs to be large enough to hold UTF-8
        # encoded long file paths.
        self.mmap_sz = 2048

        # mdc - removed the following and put it in `app.startApp()` to have
        #       error logging occur sooner.
        #
        # if not self.testMode:
        #     self._lastRunLog = open(os.path.join(
        #             self.prefs.paths['userPrefsDir'], 'last_app_load.log'),
        #             'w')
        #     sys.stderr = sys.stdout = lastLoadErrs = self._lastRunLog
        #     logging.console.setLevel(logging.DEBUG)

        # indicates whether we're running for testing purposes
        self.osfSession = None
        self.pavloviaSession = None

        self.copiedRoutine = None
        self.copiedCompon = None
        self._allFrames = frametracker.openFrames  # ordered; order updated with self.onNewTopWindow

        wx.App.__init__(self, arg)

        # import localization after wx:
        from psychopy import localization  # needed by splash screen
        self.localization = localization
        self.locale = localization.setLocaleWX()
        self.locale.AddCatalog(self.GetAppName())

        logging.flush()
        self.onInit(testMode=testMode, **kwargs)
        if profiling:
            profile.disable()
            print("time to load app = {:.2f}".format(time.time()-t0))
            profile.dump_stats('profileLaunchApp.profile')
        logging.flush()

        # if we're on linux, check if we have the permissions file setup
        from psychopy.app.linuxconfig import (
            LinuxConfigDialog, linuxConfigFileExists)

        if not linuxConfigFileExists():
            linuxConfDlg = LinuxConfigDialog(
                None, timeout=1000 if self.testMode else None)
            linuxConfDlg.ShowModal()
            linuxConfDlg.Destroy()

    def _doSingleInstanceCheck(self):
        """Set up the routines which check for and communicate with other
        PsychoPy GUI processes.

        Single instance check is done here prior to loading any GUI stuff. This
        permits one instance of PsychoPy from running at any time. Clicking on
        files will open them in the extant instance rather than loading up a new
        one.

        Inter-process messaging is done via a memory-mapped file created by the
        first instance. Successive instances will write their args to this file
        and promptly close. The main instance will read this file periodically
        for data and open and file names stored to this buffer.

        This uses similar logic to this example:
        https://github.com/wxWidgets/wxPython-Classic/blob/master/wx/lib/pydocview.py

        """
        # Create the memory-mapped file if not present, this is handled
        # differently between Windows and UNIX-likes.
        if wx.Platform == '__WXMSW__':
            tfile = tempfile.TemporaryFile(prefix="ag", suffix="tmp")
            fno = tfile.fileno()
            self._sharedMemory = mmap.mmap(fno, self.mmap_sz, "shared_memory")
        else:
            tfile = open(
                os.path.join(
                    tempfile.gettempdir(),
                    tempfile.gettempprefix() + self.GetAppName() + '-' +
                    wx.GetUserId() + "AGSharedMemory"),
                'w+b')

            # insert markers into the buffer
            tfile.write(b"*")
            tfile.seek(self.mmap_sz)
            tfile.write(b" ")
            tfile.flush()
            fno = tfile.fileno()
            self._sharedMemory = mmap.mmap(fno, self.mmap_sz)

        # use wx to determine if another instance is running
        self._singleInstanceChecker = wx.SingleInstanceChecker(
            self.GetAppName() + '-' + wx.GetUserId(),
            tempfile.gettempdir())

        # If another instance is running, message our args to it by writing the
        # path the buffer.
        if self._singleInstanceChecker.IsAnotherRunning():
            # Message the extant running instance the arguments we want to
            # process.
            args = sys.argv[1:]

            # if there are no args, tell the user another instance is running
            if not args:
                errMsg = "Another instance of PsychoPy is already running."
                errDlg = wx.MessageDialog(
                    None, errMsg, caption="PsychoPy Error",
                    style=wx.OK | wx.ICON_ERROR, pos=wx.DefaultPosition)
                errDlg.ShowModal()
                errDlg.Destroy()

                self.quit(None)

            # serialize the data
            data = pickle.dumps(args)

            # Keep alive until the buffer is free for writing, this allows
            # multiple files to be opened in succession. Times out after 5
            # seconds.
            attempts = 0
            while attempts < 5:
                # try to write to the buffer
                self._sharedMemory.seek(0)
                marker = self._sharedMemory.read(1)
                if marker == b'\0' or marker == b'*':
                    self._sharedMemory.seek(0)
                    self._sharedMemory.write(b'-')
                    self._sharedMemory.write(data)
                    self._sharedMemory.seek(0)
                    self._sharedMemory.write(b'+')
                    self._sharedMemory.flush()
                    break
                else:
                    # wait a bit for the buffer to become free
                    time.sleep(1)
                    attempts += 1
            else:
                if not self.testMode:
                    # error that we could not access the memory-mapped file
                    errMsg = \
                        "Cannot communicate with running PsychoPy instance!"
                    errDlg = wx.MessageDialog(
                        None, errMsg, caption="PsychoPy Error",
                        style=wx.OK | wx.ICON_ERROR, pos=wx.DefaultPosition)
                    errDlg.ShowModal()
                    errDlg.Destroy()

            # since were not the main instance, exit ...
            self.quit(None)

    def _refreshComponentPanels(self):
        """Refresh Builder component panels.

        Since panels are created before loading plugins, calling this method is
        required after loading plugins which contain components to have them
        appear.

        """
        if not hasattr(self, 'builder') or self.builder is None:
            return  # nop if we haven't realized the builder UI yet

        if not isinstance(self.builder, list):
            self.builder.componentButtons.populate()
        else:
            for builderFrame in self.builder:
                builderFrame.componentButtons.populate()

    def onInit(self, showSplash=True, testMode=False, safeMode=False):
        """This is launched immediately *after* the app initialises with
        wxPython.

        Plugins are loaded at the very end of this routine if `safeMode==False`.

        Parameters
        ----------
        showSplash : bool
            Display the splash screen on init.
        testMode : bool
            Are we running in test mode? If so, disable multi-instance checking
            and other features that depend on the `EVT_IDLE` event.
        safeMode : bool
            Run PsychoPy in safe mode. This temporarily disables plugins and
            resets configurations that may be causing problems running PsychoPy.

        """
        self.SetAppName('PsychoPy3')

        # Check for other running instances and communicate with them. This is
        # done to allow a single instance to accept file open requests without
        # opening it in a seperate process.
        #
        self._doSingleInstanceCheck()

        if showSplash:
            # show splash screen
            splashFile = os.path.join(
                self.prefs.paths['resources'], 'psychopySplash.png')
            splashImage = wx.Image(name=splashFile)
            splashImage.ConvertAlphaToMask()
            splash = AS.AdvancedSplash(
                None, bitmap=splashImage.ConvertToBitmap(),
                timeout=3000, agwStyle=AS.AS_TIMEOUT | AS.AS_CENTER_ON_SCREEN
            )
            w, h = splashImage.GetSize()
            splash.SetTextPosition((340, h - 30))
            splash.SetText(
                _translate("Copyright (C) 2022 OpenScienceTools.org"))
        else:
            splash = None

        # SLOW IMPORTS - these need to be imported after splash screen starts
        # but then that they end up being local so keep track in self

        from psychopy.compatibility import checkCompatibility
        # import coder and builder here but only use them later
        from psychopy.app import coder, builder, runner, dialogs

        if '--firstrun' in sys.argv:
            del sys.argv[sys.argv.index('--firstrun')]
            self.firstRun = True
        if 'lastVersion' not in self.prefs.appData:
            # must be before 1.74.00
            last = self.prefs.appData['lastVersion'] = '1.73.04'
            self.firstRun = True
        else:
            last = self.prefs.appData['lastVersion']

        if self.firstRun and not self.testMode:
            pass

        # setup links for URLs
        # on a mac, don't exit when the last frame is deleted, just show menu
        if sys.platform == 'darwin':
            self.menuFrame = MenuFrame(parent=None, app=self)
        # fetch prev files if that's the preference
        if self.prefs.coder['reloadPrevFiles']:
            scripts = self.prefs.appData['coder']['prevFiles']
        else:
            scripts = []
        appKeys = list(self.prefs.appData['builder'].keys())
        if self.prefs.builder['reloadPrevExp'] and ('prevFiles' in appKeys):
            exps = self.prefs.appData['builder']['prevFiles']
        else:
            exps = []
        runlist = []

        self.dpi = int(wx.GetDisplaySize()[0] /
                       float(wx.GetDisplaySizeMM()[0]) * 25.4)
        # detect retina displays
        self.isRetina = self.dpi>80 and wx.Platform == '__WXMAC__'
        if self.isRetina:
            fontScale = 1.2  # fonts are looking tiny on macos (only retina?) right now
            # mark icons as being retina
            icons.retStr = "@2x"
        else:
            fontScale = 1
        # adjust dpi to something reasonable
        if not (50 < self.dpi < 120):
            self.dpi = 80  # dpi was unreasonable, make one up

        # Manage fonts
        if sys.platform == 'win32':
            # wx.SYS_DEFAULT_GUI_FONT is default GUI font in Win32
            self._mainFont = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        else:
            self._mainFont = wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT)
            # rescale for tiny retina fonts

        if hasattr(wx.Font, "AddPrivateFont") and sys.platform != "darwin":
            # Load packaged fonts if possible
            for fontFile in (Path(__file__).parent / "Resources" / "fonts").glob("*"):
                if fontFile.suffix in ['.ttf', '.truetype']:
                    wx.Font.AddPrivateFont(str(fontFile))
            # Set fonts as those loaded
            self._codeFont = wx.Font(
                wx.FontInfo(self._mainFont.GetPointSize()).FaceName(
                    "JetBrains Mono"))
        else:
            # Get system defaults if can't load fonts
            try:
                self._codeFont = wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT)
            except wx._core.wxAssertionError:
                # if no SYS_ANSI_FIXED_FONT then try generic FONTFAMILY_MODERN
                self._codeFont = wx.Font(self._mainFont.GetPointSize(),
                                         wx.FONTFAMILY_TELETYPE,
                                         wx.FONTSTYLE_NORMAL,
                                         wx.FONTWEIGHT_NORMAL)

        if self.isRetina:
            self._codeFont.SetPointSize(int(self._codeFont.GetPointSize()*fontScale))
            self._mainFont.SetPointSize(int(self._mainFont.GetPointSize()*fontScale))

        # that gets most of the properties of _codeFont but the FaceName
        # FaceName is set in the setting of the theme:
        self.theme = prefs.app['theme']

        # removed Aug 2017: on newer versions of wx (at least on mac)
        # this looks too big
        # if hasattr(self._mainFont, 'Larger'):
        #     # Font.Larger is available since wyPython version 2.9.1
        #     # PsychoPy still supports 2.8 (see ensureMinimal above)
        #     self._mainFont = self._mainFont.Larger()
        #     self._codeFont.SetPointSize(
        #         self._mainFont.GetPointSize())  # unify font size

        # create both frame for coder/builder as necess
        if splash:
            splash.SetText(_translate("  Creating frames..."))

        # Parse incoming call
        parser = argparse.ArgumentParser(prog=self)
        parser.add_argument('--builder', dest='builder', action="store_true")
        parser.add_argument('-b', dest='builder', action="store_true")
        parser.add_argument('--coder', dest='coder', action="store_true")
        parser.add_argument('-c', dest='coder', action="store_true")
        parser.add_argument('--runner', dest='runner', action="store_true")
        parser.add_argument('-r', dest='runner', action="store_true")
        parser.add_argument('-x', dest='direct', action='store_true')
        view, args = parser.parse_known_args(sys.argv)
        # Check from filetype if any windows need to be open
        if any(arg.endswith('.psyexp') for arg in args):
            view.builder = True
            exps = [file for file in args if file.endswith('.psyexp')]
        if any(arg.endswith('.psyrun') for arg in args):
            view.runner = True
            runlist = [file for file in args if file.endswith('.psyrun')]
        # If still no window specified, use default from prefs
        if not any(getattr(view, key) for key in ['builder', 'coder', 'runner']):
            if self.prefs.app['defaultView'] in view:
                setattr(view, self.prefs.app['defaultView'], True)
            elif self.prefs.app['defaultView'] == 'all':
                view.builder = True
                view.coder = True
                view.runner = True

        # set the dispatcher for standard output
        # self.stdStreamDispatcher = console.StdStreamDispatcher(self)
        # self.stdStreamDispatcher.redirect()

        # Create windows
        if view.runner:
            # open Runner is requested
            try:
                self.showRunner(fileList=runlist)
            except Exception as err:
                # if Runner failed with file, try without
                self.showRunner()
                # log error
                logging.error(_translate(
                    "Failed to open Runner with requested file list, opening without file list.\n"
                    "Requested: {}\n"
                    "Err: {}"
                ).format(runlist, traceback.format_exception_only(err)))
                logging.debug(
                    "\n".join(traceback.format_exception(err))
                )

        if view.coder:
            # open Coder if requested
            try:
                self.showCoder(fileList=scripts)
            except Exception as err:
                # if Coder failed with file, try without
                logging.error(_translate(
                    "Failed to open Coder with requested scripts, opening with no scripts open.\n"
                    "Requested: {}\n"
                    "Err: {}"
                ).format(scripts, traceback.format_exception_only(err)))
                logging.debug(
                    "\n".join(traceback.format_exception(err))
                )
                self.showCoder()
        if view.builder:
            # open Builder if requested
            try:
                self.showBuilder(fileList=exps)
            except Exception as err:
                # if Builder failed with file, try without
                self.showBuilder()
                # log error
                logging.error(_translate(
                    "Failed to open Builder with requested experiments, opening with no experiments open.\n"
                    "Requested: {}\n"
                    "Err: {}"
                ).format(exps, traceback.format_exception_only(err)))
                logging.debug(
                    "\n".join(traceback.format_exception(err))
                )

        if view.direct:
            self.showRunner()
            for exp in [file for file in args if file.endswith('.psyexp') or file.endswith('.py')]:
                self.runner.panel.runFile(exp)
        # if we started a busy cursor which never finished, finish it now
        if wx.IsBusy():
            wx.EndBusyCursor()

        # send anonymous info to https://usage.psychopy.org
        # please don't disable this, it's important for PsychoPy's development
        self._latestAvailableVersion = None
        self.updater = None
        self.news = None
        self.tasks = None

        prefsConn = self.prefs.connections

        ok, msg = checkCompatibility(last, self.version, self.prefs, fix=True)
        # tell the user what has changed
        if not ok and not self.firstRun and not self.testMode:
            title = _translate("Compatibility information")
            dlg = dialogs.MessageDialog(parent=None, message=msg, type='Info',
                                        title=title)
            dlg.ShowModal()

        if self.prefs.app['showStartupTips'] and not self.testMode:
            tipFile = os.path.join(
                self.prefs.paths['resources'], _translate("tips.txt"))
            tipIndex = self.prefs.appData['tipIndex']
            if parse_version(wx.__version__) >= parse_version('4.0.0a1'):
                tp = wx.adv.CreateFileTipProvider(tipFile, tipIndex)
                showTip = wx.adv.ShowTip(None, tp)
            else:
                tp = wx.CreateFileTipProvider(tipFile, tipIndex)
                showTip = wx.ShowTip(None, tp)

            self.prefs.appData['tipIndex'] = tp.GetCurrentTip()
            self.prefs.saveAppData()
            self.prefs.app['showStartupTips'] = showTip
            self.prefs.saveUserPrefs()

        self.Bind(wx.EVT_IDLE, self.onIdle)

        # doing this once subsequently enables the app to open & switch among
        # wx-windows on some platforms (Mac 10.9.4) with wx-3.0:
        v = parse_version
        if sys.platform == 'darwin':
            if v('3.0') <= v(wx.__version__) < v('4.0'):
                _Showgui_Hack()  # returns ~immediately, no display
                # focus stays in never-land, so bring back to the app:
                if prefs.app['defaultView'] in ['all', 'builder', 'coder', 'runner']:
                    self.showBuilder()
                else:
                    self.showCoder()
        # after all windows are created (so errors flushed) create output
        self._appLoaded = True
        if self.coder:
            self.coder.setOutputWindow()  # takes control of sys.stdout

        # if the program gets here, there are no other instances running
        self._timer = wx.PyTimer(self._bgCheckAndLoad)
        self._timer.Start(250)

        # load plugins after the app has been mostly realized
        if splash:
            splash.SetText(_translate("  Loading plugins..."))

        # Load plugins here after everything is realized, make sure that we
        # refresh UI elements which are affected by plugins (e.g. the component
        # panel in Builder).
        from psychopy.plugins import activatePlugins
        activatePlugins()
        self._refreshComponentPanels()

        # flush any errors to the last run log file
        logging.flush()
        sys.stdout.flush()
        # we wanted debug mode while loading but safe to go back to info mode
        if not self.prefs.app['debugMode']:
            logging.console.setLevel(logging.INFO)

        return True

    def _bgCheckAndLoad(self):
        """Check shared memory for messages from other instances. This only is
        called periodically in the first and only instance of PsychoPy.

        """
        if not self._appLoaded:  # only open files if we have a UI
            return

        self._timer.Stop()

        self._sharedMemory.seek(0)
        if self._sharedMemory.read(1) == b'+':  # available data
            data = self._sharedMemory.read(self.mmap_sz - 1)
            self._sharedMemory.seek(0)
            self._sharedMemory.write(b"*")
            self._sharedMemory.flush()

            # decode file path from data
            filePaths = pickle.loads(data)
            for fileName in filePaths:
                self.MacOpenFile(fileName)

            # force display of running app
            topWindow = wx.GetApp().GetTopWindow()
            if topWindow.IsIconized():
                topWindow.Iconize(False)
            else:
                topWindow.Raise()

        self._timer.Start(1000)  # 1 second interval

    @property
    def appLoaded(self):
        """`True` if the app has been fully loaded (`bool`)."""
        return self._appLoaded

    def _wizard(self, selector, arg=''):
        from psychopy import core
        wizard = os.path.join(
            self.prefs.paths['psychopy'], 'tools', 'wizard.py')
        so, se = core.shellCall(
            [sys.executable, wizard, selector, arg], stderr=True)
        if se and self.prefs.app['debugMode']:
            print(se)  # stderr contents; sometimes meaningless

    def firstrunWizard(self):
        self._wizard('--config', '--firstrun')
        # wizard typically creates html report file but user can manually skip
        reportPath = os.path.join(
            self.prefs.paths['userPrefsDir'], 'firstrunReport.html')
        if os.path.exists(reportPath):
            with io.open(reportPath, 'r', encoding='utf-8-sig') as f:
                report = f.read()
            if 'Configuration problem' in report:
                # fatal error was encountered (currently only if bad drivers)
                # ensure wizard will be triggered again:
                del self.prefs.appData['lastVersion']
                self.prefs.saveAppData()

    def benchmarkWizard(self, evt=None):
        self._wizard('--benchmark')

    def csvFromPsydat(self, evt=None):
        from psychopy import gui
        from psychopy.tools.filetools import fromFile

        prompt = _translate("Select .psydat file(s) to extract")
        names = gui.fileOpenDlg(allowed='*.psydat', prompt=prompt)
        for name in names or []:
            filePsydat = os.path.abspath(name)
            print("psydat: {0}".format(filePsydat))

            exp = fromFile(filePsydat)
            if filePsydat.endswith('.psydat'):
                fileCsv = filePsydat[:-7]
            else:
                fileCsv = filePsydat
            fileCsv += '.csv'
            exp.saveAsWideText(fileCsv)
            print('   -->: {0}'.format(os.path.abspath(fileCsv)))

    def checkUpdates(self, evt):
        # if we have internet and haven't yet checked for updates then do so
        # we have a network connection but not yet tried an update
        if self._latestAvailableVersion not in [-1, None]:
            # change IDLE routine so we won't come back here
            self.Unbind(wx.EVT_IDLE)  # unbind all EVT_IDLE methods from app
            self.Bind(wx.EVT_IDLE, self.onIdle)
            # create updater (which will create dialogs as needed)
            self.updater = connections.Updater(app=self)
            self.updater.latest = self._latestAvailableVersion
            self.updater.suggestUpdate(confirmationDlg=False)
        evt.Skip()

    def getPrimaryDisplaySize(self):
        """Get the size of the primary display (whose coords start (0,0))
        """
        return list(wx.Display(0).GetGeometry())[2:]

    def makeAccelTable(self):
        """Makes a standard accelorator table and returns it. This then needs
        to be set for the Frame using self.SetAccelerator(table)
        """
        def parseStr(inStr):
            accel = 0
            if 'ctrl' in inStr.lower():
                accel += wx.ACCEL_CTRL
            if 'shift' in inStr.lower():
                accel += wx.ACCEL_SHIFT
            if 'alt' in inStr.lower():
                accel += wx.ACCEL_ALT
            return accel, ord(inStr[-1])
        # create a list to link IDs to key strings
        keyCodesDict = {}
        keyCodesDict[self.keys['copy']] = wx.ID_COPY
        keyCodesDict[self.keys['cut']] = wx.ID_CUT
        keyCodesDict[self.keys['paste']] = wx.ID_PASTE
        keyCodesDict[self.keys['undo']] = wx.ID_UNDO
        keyCodesDict[self.keys['redo']] = wx.ID_REDO
        keyCodesDict[self.keys['save']] = wx.ID_SAVE
        keyCodesDict[self.keys['saveAs']] = wx.ID_SAVEAS
        keyCodesDict[self.keys['close']] = wx.ID_CLOSE
        keyCodesDict[self.keys['redo']] = wx.ID_REDO
        keyCodesDict[self.keys['quit']] = wx.ID_EXIT
        # parse the key strings and convert to accelerator entries
        entries = []
        for keyStr, code in list(keyCodesDict.items()):
            mods, key = parseStr(keyStr)
            entry = wx.AcceleratorEntry(mods, key, code)
            entries.append(entry)
        table = wx.AcceleratorTable(entries)
        return table

    def updateWindowMenu(self):
        """Update items within Window menu to reflect open windows"""
        # Update checks on menus in all frames
        for frame in self.getAllFrames():
            if hasattr(frame, "windowMenu"):
                frame.windowMenu.updateFrames()

    def showCoder(self, event=None, fileList=None):
        # have to reimport because it is only local to __init__ so far
        from . import coder
        if self.coder is None:
            title = "PsychoPy Coder (IDE) (v%s)"
            wx.BeginBusyCursor()
            self.coder = coder.CoderFrame(None, -1,
                                          title=title % self.version,
                                          files=fileList, app=self)
            self.updateWindowMenu()
            wx.EndBusyCursor()
        else:
            # Set output window and standard streams
            self.coder.setOutputWindow(True)
        self.coder.Show(True)
        self.SetTopWindow(self.coder)
        self.coder.Raise()

    def newBuilderFrame(self, event=None, fileName=None):
        # have to reimport because it is only local to __init__ so far
        wx.BeginBusyCursor()
        from .builder.builder import BuilderFrame
        title = "PsychoPy Builder (v%s)"
        self.builder = BuilderFrame(None, -1,
                                 title=title % self.version,
                                 fileName=fileName, app=self)
        self.builder.Show(True)
        self.builder.Raise()
        self.SetTopWindow(self.builder)
        self.updateWindowMenu()
        wx.EndBusyCursor()
        return self.builder

    def showBuilder(self, event=None, fileList=()):
        # have to reimport because it is only local to __init__ so far
        from psychopy.app import builder
        for fileName in fileList:
            if os.path.isfile(fileName):
                self.newBuilderFrame(fileName=fileName)
        # create an empty Builder view if needed
        if len(self.getAllFrames(frameType="builder")) == 0:
            self.newBuilderFrame()
        # loop through all frames, from the back bringing each forward
        for thisFrame in self.getAllFrames(frameType='builder'):
            thisFrame.Show(True)
            thisFrame.Raise()
            self.SetTopWindow(thisFrame)

    def showRunner(self, event=None, fileList=[]):
        if not self.runner:
            self.runner = self.newRunnerFrame()
        if not self.testMode:
            self.runner.Show()
            self.runner.Raise()
            self.SetTopWindow(self.runner)
        # Runner captures standard streams until program closed
        # if self.runner and not self.testMode:
        #     sys.stderr = sys.stdout = self.stdStreamDispatcher

    def newRunnerFrame(self, event=None):
        # have to reimport because it is only local to __init__ so far
        from .runner.runner import RunnerFrame
        title = "PsychoPy Runner (v{})".format(self.version)
        wx.BeginBusyCursor()
        self.runner = RunnerFrame(parent=None,
                             id=-1,
                             title=title,
                             app=self)
        self.updateWindowMenu()
        wx.EndBusyCursor()
        return self.runner

    def OnDrop(self, x, y, files):
        """Not clear this method ever gets called!"""
        logging.info("Got Files")

    def MacOpenFile(self, fileName):
        if fileName.endswith('psychopyApp.py'):
            # in wx4 on mac this is called erroneously by App.__init__
            # if called like `python psychopyApp.py`
            return
        logging.debug('PsychoPyApp: Received Mac file dropped event')
        if fileName.endswith('.py'):
            if self.coder is None:
                self.showCoder()
            self.coder.setCurrentDoc(fileName)
        elif fileName.endswith('.psyexp'):
            self.newBuilderFrame(fileName=fileName)

    def MacReopenApp(self):
        """Called when the doc icon is clicked, and ???"""
        self.GetTopWindow().Raise()

    def openIPythonNotebook(self, event=None):
        """Note that right now this is bad because it ceases all activity in
        the main wx loop and the app has to be quit. We need it to run from
        a separate process? The necessary depends (zmq and tornado) were
        included from v1.78 onwards in the standalone
        """
        import IPython.frontend.html.notebook.notebookapp as nb
        instance = nb.launch_new_instance()

    def openUpdater(self, event=None):
        from psychopy.app import connections
        dlg = connections.InstallUpdateDialog(parent=None, ID=-1, app=self)

    def colorPicker(self, event=None):
        """Open color-picker, sets clip-board to string [r,g,b].

        Note: units are psychopy -1..+1 rgb units to three decimal places,
        preserving 24-bit color.
        """
        if self.coder is None:
            return

        document = self.coder.currentDoc
        dlg = PsychoColorPicker(None, context=document)  # doesn't need a parent
        dlg.ShowModal()
        dlg.Destroy()

        if event is not None:
            event.Skip()

    def openMonitorCenter(self, event):
        from psychopy.monitors import MonitorCenter
        self.monCenter = MonitorCenter.MainFrame(
            None, 'PsychoPy Monitor Center')
        self.monCenter.Show(True)

    def terminateHubProcess(self):
        """
        Send a UDP message to iohub informing it to exit.

        Use this when force quitting the experiment script process so iohub
        knows to exit as well.

        If message is not sent within 1 second, or the iohub server
        address in incorrect,the issue is logged.
        """
        sock = None
        try:
            logging.debug('PsychoPyApp: terminateHubProcess called.')
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            iohubAddress = '127.0.0.1', 9034
            import msgpack
            txData = msgpack.Packer().pack(('STOP_IOHUB_SERVER',))
            return sock.sendto(txData, iohubAddress)
        except socket.error as e:
            msg = 'PsychoPyApp: terminateHubProcess socket.error: %s'
            logging.debug(msg % str(e))
        except socket.herror as e:
            msg = 'PsychoPyApp: terminateHubProcess socket.herror: %s'
            logging.debug(msg % str(e))
        except socket.gaierror as e:
            msg = 'PsychoPyApp: terminateHubProcess socket.gaierror: %s'
            logging.debug(msg % str(e))
        except socket.timeout as e:
            msg = 'PsychoPyApp: terminateHubProcess socket.timeout: %s'
            logging.debug(msg % str(e))
        except Exception as e:
            msg = 'PsychoPyApp: terminateHubProcess exception: %s'
            logging.debug(msg % str(e))
        finally:
            if sock:
                sock.close()
            logging.debug('PsychoPyApp: terminateHubProcess completed.')

    def quit(self, event=None):
        logging.debug('PsychoPyApp: Quitting...')
        self.quitting = True
        # garbage collect the projects before sys.exit
        projects.pavlovia.knownUsers = None
        projects.pavlovia.knownProjects = None
        # see whether any files need saving
        for frame in self.getAllFrames():
            try:  # will fail if the frame has been shut somehow elsewhere
                ok = frame.checkSave()
            except Exception:
                ok = False
                logging.debug("PsychopyApp: exception when saving")
            if not ok:
                logging.debug('PsychoPyApp: User cancelled shutdown')
                return  # user cancelled quit

        # save info about current frames for next run
        if self.coder and len(self.getAllFrames("builder")) == 0:
            self.prefs.appData['lastFrame'] = 'coder'
        elif self.coder is None:
            self.prefs.appData['lastFrame'] = 'builder'
        else:
            self.prefs.appData['lastFrame'] = 'both'

        self.prefs.appData['lastVersion'] = self.version
        # update app data while closing each frame
        # start with an empty list to be appended by each frame
        self.prefs.appData['builder']['prevFiles'] = []
        self.prefs.appData['coder']['prevFiles'] = []

        # write plugins config if changed during the session
        # saveStartUpPluginsConfig()

        for frame in self.getAllFrames():
            try:
                frame.closeFrame(event=event, checkSave=False)
            except Exception:
                pass  # we don't care if this fails - we're quitting anyway
        # must do this before destroying the frame?
        self.prefs.saveAppData()
        #self.Destroy()

        # Reset streams back to default
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        if not self.testMode:
            sys.exit()

    def showPrefs(self, event):
        from psychopy.app.preferencesDlg import PreferencesDlg
        logging.debug('PsychoPyApp: Showing prefs dlg')
        prefsDlg = PreferencesDlg(app=self)
        prefsDlg.ShowModal()
        prefsDlg.Destroy()

    def showAbout(self, event):
        logging.debug('PsychoPyApp: Showing about dlg')

        with io.open(os.path.join(self.prefs.paths['psychopy'], 'LICENSE.txt'),
                     'r', encoding='utf-8-sig') as f:
            license = f.read()

        msg = _translate(
            "For stimulus generation and experimental control in Python.\n"
            "PsychoPy depends on your feedback. If something doesn't work\n"
            "then let us know at psychopy-users@googlegroups.com")
        if parse_version(wx.__version__) >= parse_version('4.0a1'):
            info = wx.adv.AboutDialogInfo()
            showAbout = wx.adv.AboutBox
        else:
            info = wx.AboutDialogInfo()
            showAbout = wx.AboutBox
        if wx.version() >= '3.':
            icon = os.path.join(self.prefs.paths['resources'], 'psychopy.png')
            info.SetIcon(wx.Icon(icon, wx.BITMAP_TYPE_PNG, 128, 128))
        info.SetName('PsychoPy')
        info.SetVersion('v' + psychopy.__version__)
        info.SetDescription(msg)

        info.SetCopyright('(C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.')
        info.SetWebSite('https://www.psychopy.org')
        info.SetLicence(license)
        # developers

        devNames = [
            'Jonathan Peirce',
            'Jeremy Gray',
            'Michael MacAskill',
            'Sol Simpson',
            u'Jonas Lindel\xF8v',
            'Yaroslav Halchenko',
            'Erik Kastman',
            'Hiroyuki Sogo',
            'David Bridges',
            'Matthew Cutone',
            'Philipp Wiesemann',
            u'Richard Höchenberger',
            'Andrew Schofield',
            'Todd Parsons',
            'Dan Fitch',
            'Suddha Sourav',
            'Philipp Wiesemann',
            'Mark Hymers',
            'Benjamin T. Vincent',
            'Yaroslav Halchenko',
            'Jay Borseth',
            'chrisgatwin [@github.com]',
            'toddrjen [@github.com]'
        ]

        docNames = [
            'Jonathan Peirce',
            'Jeremy Gray',
            'Rebecca Hirst',
            'Rebecca Sharman',
            'Matthew Cutone'
        ]
        devNames.sort()

        intNames = [
            'Hiroyuki Sogo (Japanese)'
            'Shun Wang (Chinese)'
        ]
        intNames.sort()

        for name in devNames:
            info.AddDeveloper(name)

        for name in docNames:
            info.AddDocWriter(name)

        for name in intNames:
            info.AddTranslator(name)

        if not self.testMode:
            showAbout(info)

    def showNews(self, event=None):
        connections.showNews(self, checkPrev=False)

    def showSystemInfo(self, event=None):
        """Show system information."""
        from psychopy.app.sysInfoDlg import SystemInfoDialog
        dlg = SystemInfoDialog(None)
        dlg.Show()

    def followLink(self, event=None, url=None):
        """Follow either an event id (= a key to an url defined in urls.py)
        or follow a complete url (a string beginning "http://")
        """
        if event is not None:
            wx.LaunchDefaultBrowser(self.urls[event.GetId()])
        elif url is not None:
            wx.LaunchDefaultBrowser(url)

    def getAllFrames(self, frameType=None):
        """Get a list of frames, optionally filtered by a particular kind
        (which can be "builder", "coder", "project")
        """
        frames = []
        for frameRef in self._allFrames:
            frame = frameRef()
            if (not frame):
                self._allFrames.remove(frameRef)  # has been deleted
                continue
            elif frameType and frame.frameType != frameType:
                continue
            frames.append(frame)
        return frames

    def trackFrame(self, frame):
        """Keep track of an open frame (stores a weak reference to the frame
        which will probably have a regular reference to the app)
        """
        self._allFrames.append(weakref.ref(frame))

    def forgetFrame(self, frame):
        """Keep track of an open frame (stores a weak reference to the frame
        which will probably have a regular reference to the app)
        """
        for entry in self._allFrames:
            if entry() == frame:  # is a weakref
                self._allFrames.remove(entry)

    def onIdle(self, evt):
        from . import idle
        idle.doIdleTasks(app=self)
        evt.Skip()

    @property
    def theme(self):
        """The theme to be used through the application"""
        return themes.theme

    @theme.setter
    def theme(self, value):
        """The theme to be used through the application"""
        # Make sure we just have a name
        if isinstance(value, themes.Theme):
            value = value.code
        # Store new theme
        prefs.app['theme'] = value
        prefs.saveUserPrefs()
        # Reset icon cache
        icons.iconCache.clear()
        # Set theme at module level
        themes.theme.set(value)
        # Apply to frames
        for frameRef in self._allFrames:
            frame = frameRef()
            if isinstance(frame, handlers.ThemeMixin):
                frame.theme = themes.theme

        # On OSX 10.15 Catalina at least calling SetFaceName with 'AppleSystemUIFont' fails.
        # So this fix checks to see if changing the font name invalidates the font.
        # if so rollback to the font before attempted change.
        # Note that wx.Font uses referencing and copy-on-write so we need to force creation of a copy
        # with the wx.Font() call. Otherwise you just get reference to the font that gets borked by SetFaceName()
        # -Justin Ales
        beforesetface = wx.Font(self._codeFont)
        success = self._codeFont.SetFaceName("JetBrains Mono")
        if not (success):
            self._codeFont = beforesetface


if __name__ == '__main__':
    # never run; stopped earlier at cannot do relative import in a non-package
    sys.exit("Do not launch the app from this script -"
             "use python psychopyApp.py instead")
