#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, division, print_function

from builtins import str
from builtins import object

profiling = False  # turning on will save profile files in currDir

import sys
import argparse
import platform
import psychopy
from psychopy import prefs
from pkg_resources import parse_version
from psychopy.constants import PY3
from . import urls
from . import frametracker
from . import themes
from . import icons

import io
import json

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

if not PY3 and sys.platform == 'darwin':
    blockTips = True
else:
    blockTips = False

travisCI = bool(str(os.environ.get('TRAVIS')).lower() == 'true')

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
                    "High DPI support is not appear to be supported by this version"
                    " of Windows. Disabling in preferences.")

                psychopy.prefs.app['highDPI'] = False
                psychopy.prefs.saveUserPrefs()


class MenuFrame(wx.Frame, themes.ThemeMixin):
    """A simple empty frame with a menubar, should be last frame closed on mac
    """

    def __init__(self, parent=None, ID=-1, app=None, title="PsychoPy3"):

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


class _Showgui_Hack(object):
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


class PsychoPyApp(wx.App, themes.ThemeMixin):

    def __init__(self, arg=0, testMode=False, **kwargs):
        """With a wx.App some things get done here, before App.__init__
        then some further code is launched in OnInit() which occurs after
        """
        if profiling:
            import cProfile, time
            profile = cProfile.Profile()
            profile.enable()
            t0 = time.time()

        self._appLoaded = False  # set to true when all frames are created
        self.coder = None
        self.runner = None
        self.version = psychopy.__version__
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
        self.iconCache = themes.IconCache()

        if not self.testMode:
            self._lastRunLog = open(os.path.join(
                    self.prefs.paths['userPrefsDir'], 'last_app_load.log'),
                    'w')
            sys.stderr = sys.stdout = lastLoadErrs = self._lastRunLog
            logging.console.setLevel(logging.DEBUG)

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

        # set the exception hook to present unhandled errors in a dialog
        if not travisCI:
            from psychopy.app.errorDlg import exceptionCallback
            sys.excepthook = exceptionCallback

        self.onInit(testMode=testMode, **kwargs)
        if profiling:
            profile.disable()
            print("time to load app = {:.2f}".format(time.time()-t0))
            profile.dump_stats('profileLaunchApp.profile')


    def onInit(self, showSplash=True, testMode=False):
        """This is launched immediately *after* the app initialises with wx
        :Parameters:

          testMode: bool
        """
        self.SetAppName('PsychoPy3')

        if showSplash: #showSplash:
            # show splash screen
            splashFile = os.path.join(
                self.prefs.paths['resources'], 'psychopySplash.png')
            splashImage = wx.Image(name=splashFile)
            splashImage.ConvertAlphaToMask()
            splash = AS.AdvancedSplash(None, bitmap=splashImage.ConvertToBitmap(),
                                       timeout=3000,
                                       agwStyle=AS.AS_TIMEOUT | AS.AS_CENTER_ON_SCREEN,
                                       )  # transparency?
            w, h = splashImage.GetSize()
            splash.SetTextPosition((int(340), h-30))
            splash.SetText(_translate("Copyright (C) 2020 OpenScienceTools.org"))
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
        if not (50 < self.dpi < 120):
            self.dpi = 80  # dpi was unreasonable, make one up

        if sys.platform == 'win32':
            # wx.SYS_DEFAULT_GUI_FONT is default GUI font in Win32
            self._mainFont = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        else:
            self._mainFont = wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT)

        try:
            self._codeFont = wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT)
        except wx._core.wxAssertionError:
            # if no SYS_ANSI_FIXED_FONT then try generic FONTFAMILY_MODERN
            self._codeFont = wx.Font(self._mainFont.GetPointSize(),
                                     wx.FONTFAMILY_MODERN,
                                     wx.FONTSTYLE_NORMAL,
                                     wx.FONTWEIGHT_NORMAL)
        # that gets most of the properties of _codeFont but the FaceName
        # FaceName is set in the setting of the theme:
        self.theme = self.prefs.app['theme']

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
        view, args = parser.parse_known_args(sys.argv)
        print(args)
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

        # Create windows
        if view.runner:
            self.showRunner(fileList=runlist)
        if view.coder:
            self.showCoder(fileList=scripts)
        if view.builder:
            self.showBuilder(fileList=exps)

        # send anonymous info to www.psychopy.org/usage.php
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

        if (self.prefs.app['showStartupTips']
                and not self.testMode and not blockTips):
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
            if v('3.0') <= v(wx.version()) <v('4.0'):
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

        # flush any errors to the last run log file
        logging.flush()
        sys.stdout.flush()
        # we wanted debug mode while loading but safe to go back to info mode
        if not self.prefs.app['debugMode']:
            logging.console.setLevel(logging.INFO)
        # Runner captures standard streams until program closed
        if self.runner and not self.testMode:
            sys.stdout = self.runner.stdOut
            sys.stderr = self.runner.stdOut

        return True

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
            title = "PsychoPy3 Coder (IDE) (v%s)"
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
        # have to reimport because it is ony local to __init__ so far
        wx.BeginBusyCursor()
        from .builder.builder import BuilderFrame
        title = "PsychoPy3 Experiment Builder (v%s)"
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

    def newRunnerFrame(self, event=None):
        # have to reimport because it is only local to __init__ so far
        from .runner.runner import RunnerFrame
        title = "PsychoPy3 Experiment Runner (v{})".format(self.version)
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
        class ColorPicker(wx.Panel):

            def __init__(self, parent):
                wx.Panel.__init__(self, parent, wx.ID_ANY)
                rgb = 'None'
                dlg = wx.ColourDialog(self)
                dlg.GetColourData().SetChooseFull(True)
                if dlg.ShowModal() == wx.ID_OK:
                    data = dlg.GetColourData()
                    rgb = data.GetColour().Get(includeAlpha=False)
                    rgb = map(lambda x: "%.3f" %
                              ((x - 127.5) / 127.5), list(rgb))
                    rgb = '[' + ','.join(rgb) + ']'
                    # http://wiki.wxpython.org/AnotherTutorial#wx.TheClipboard
                    if wx.TheClipboard.Open():
                        wx.TheClipboard.Clear()
                        wx.TheClipboard.SetData(wx.TextDataObject(str(rgb)))
                        wx.TheClipboard.Close()
                dlg.Destroy()
                parent.newRBG = rgb
        frame = wx.Frame(None, wx.ID_ANY, "Color picker",
                         size=(0, 0))  # not shown
        ColorPicker(frame)
        newRBG = frame.newRBG
        frame.Destroy()
        return newRBG  # string

    def openMonitorCenter(self, event):
        from psychopy.monitors import MonitorCenter
        self.monCenter = MonitorCenter.MainFrame(
            None, 'PsychoPy3 Monitor Center')
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
                # must do this before destroying the frame?
                self.prefs.saveAppData()
            except Exception:
                pass  # we don't care if this fails - we're quitting anyway
        self.Destroy()

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

        with io.open(os.path.join(self.prefs.paths['psychopy'],'LICENSE.txt'),
                     'r', encoding='utf-8-sig') as f:
            license = f.read()

        msg = _translate(
            "For stimulus generation and experimental control in python.\n"
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

        info.SetCopyright('(C) 2002-2018 Jonathan Peirce')
        info.SetWebSite('http://www.psychopy.org')
        info.SetLicence(license)
        info.AddDeveloper('Jonathan Peirce')
        info.AddDeveloper('Jeremy Gray')
        info.AddDeveloper('Sol Simpson')
        info.AddDeveloper(u'Jonas Lindel\xF8v')
        info.AddDeveloper('Yaroslav Halchenko')
        info.AddDeveloper('Erik Kastman')
        info.AddDeveloper('Michael MacAskill')
        info.AddDeveloper('Hiroyuki Sogo')
        info.AddDeveloper('David Bridges')
        info.AddDocWriter('Jonathan Peirce')
        info.AddDocWriter('Jeremy Gray')
        info.AddDocWriter('Rebecca Sharman')
        info.AddTranslator('Hiroyuki Sogo')

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

    def onThemeChange(self, event):
        """Handles a theme change event (from a window with a themesMenu)"""
        win = event.EventObject.Window
        newTheme = win.themesMenu.FindItemById(event.GetId()).ItemLabel
        prefs.app['theme'] = newTheme
        prefs.saveUserPrefs()
        self.theme = newTheme

    @property
    def theme(self):
        """The theme to be used through the application"""
        return prefs.app['theme']

    @theme.setter
    def theme(self, value):
        """The theme to be used through the application"""
        themes.ThemeMixin.loadThemeSpec(self, themeName=value)
        prefs.app['theme'] = value
        self._currentThemeSpec = themes.ThemeMixin.spec
        codeFont = themes.ThemeMixin.codeColors['base']['font']

        # On OSX 10.15 Catalina at least calling SetFaceName with 'AppleSystemUIFont' fails.
        # So this fix checks to see if changing the font name invalidates the font.
        # if so rollback to the font before attempted change.
        # Note that wx.Font uses referencing and copy-on-write so we need to force creation of a copy
        # witht he wx.Font() call. Otherwise you just get reference to the font that gets borked by SetFaceName()
        # -Justin Ales
        beforesetface = wx.Font(self._codeFont)
        success = self._codeFont.SetFaceName(codeFont)
        if not (success):
            self._codeFont = beforesetface
        # Apply theme
        self._applyAppTheme()

    def _applyAppTheme(self):
        """Overrides ThemeMixin for this class"""
        self.iconCache.setTheme(themes.ThemeMixin)

        for frameRef in self._allFrames:
            frame = frameRef()
            if hasattr(frame, '_applyAppTheme'):
                frame._applyAppTheme()


if __name__ == '__main__':
    # never run; stopped earlier at cannot do relative import in a non-package
    sys.exit("Do not launch the app from this script -"
             "use python psychopyApp.py instead")
