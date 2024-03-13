#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import glob
import json
import errno

from .. import ribbon
from ..stdout.stdOutRich import ScriptOutputPanel
from ..themes import handlers, colors, icons
from ..themes.ui import ThemeSwitcher

import wx
import wx.lib.agw.aui as aui
import os
import sys
import time
import requests
import traceback
import webbrowser
from pathlib import Path
from subprocess import Popen, PIPE

from psychopy import experiment, logging
from psychopy.app.utils import FrameSwitcher, FileDropTarget
from psychopy.localization import _translate
from psychopy.projects.pavlovia import getProject
from psychopy.scripts.psyexpCompile import generateScript
from psychopy.app.runner.scriptProcess import ScriptProcess
import psychopy.tools.versionchooser as versions


folderColumn = 2
runModeColumn = 1
filenameColumn = 0


class RunnerFrame(wx.Frame, handlers.ThemeMixin):
    """Construct the Psychopy Runner Frame."""

    def __init__(self, parent=None, id=wx.ID_ANY, title='', app=None):
        super(RunnerFrame, self).__init__(parent=parent,
                                          id=id,
                                          title=title,
                                          pos=wx.DefaultPosition,
                                          size=wx.DefaultSize,
                                          style=wx.DEFAULT_FRAME_STYLE,
                                          name=title,
                                          )

        self.app = app
        self.paths = self.app.prefs.paths
        self.frameType = 'runner'
        self.app.trackFrame(self)

        self.panel = RunnerPanel(self, id, title, app)
        self.panel.SetDoubleBuffered(True)

        # detect retina displays (then don't use double-buffering)
        self.isRetina = self.GetContentScaleFactor() != 1
        self.SetDoubleBuffered(not self.isRetina)
        self.SetMinSize(wx.Size(640, 480))
        # double buffered better rendering except if retina
        self.panel.SetDoubleBuffered(not self.isRetina)

        # Create menu
        self.runnerMenu = wx.MenuBar()
        self.makeMenu()
        self.SetMenuBar(self.runnerMenu)
        # Link to file drop function
        self.SetDropTarget(FileDropTarget(targetFrame=self))

        # create icon
        if sys.platform != 'darwin':
            # doesn't work on darwin and not necessary: handled by app bundle
            iconFile = os.path.join(self.paths['resources'], 'runner.ico')
            if os.path.isfile(iconFile):
                self.SetIcon(wx.Icon(iconFile, wx.BITMAP_TYPE_ICO))

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.panel, 1, wx.EXPAND | wx.ALL)
        self.SetSizerAndFit(self.mainSizer)
        self.appData = self.app.prefs.appData['runner']
        # Load previous tasks
        for filePath in self.appData['taskList']:
            if os.path.exists(filePath):
                self.addTask(fileName=filePath)
        self.Bind(wx.EVT_CLOSE, self.onClose)

        # hide alerts to begin with, more room for std while also making alerts more noticeable
        self.Layout()
        if self.isRetina:
            self.SetSize(wx.Size(920, 640))
        else:
            self.SetSize(wx.Size(1080, 920))

        self.theme = app.theme

    @property
    def filename(self):
        """Presently selected file name in Runner (`str` or `None`). If `None`,
        not file is presently selected or the task list is empty.
        """
        if not self.panel.currentSelection:  # no selection or empty list
            return

        if self.panel.currentSelection >= 0:  # has valid item selected
            return self.panel.expCtrl.GetItem(self.panel.currentSelection).Text

    def addTask(self, evt=None, fileName=None, runMode="run"):
        self.panel.addTask(fileName=fileName, runMode=runMode)

    def removeTask(self, evt=None):
        self.panel.removeTask(evt)

    def getOutputPanel(self, name):
        """
        Get output panel which matches the given name.

        Parameters
        ----------
        name : str
            Key by which the output panel was stored on creation

        Returns
        -------
        ScriptOutputPanel
            Handle of the output panel
        """
        return self.panel.outputNotebook.panels[name]

    @property
    def stdOut(self):
        return self.panel.stdoutPnl.ctrl

    @property
    def alerts(self):
        return self.panel.alertsPnl.ctrl

    def makeMenu(self):
        """Create Runner menubar."""
        keys = self.app.prefs.keys
        # Menus
        fileMenu = wx.Menu()
        viewMenu = wx.Menu()
        runMenu = wx.Menu()
        demosMenu = wx.Menu()

        # Menu items
        fileMenuItems = [
            {'id': wx.ID_ADD, 'label': _translate('Add task'),
             'status': _translate('Adding task'),
             'func': self.addTask},
            {'id': wx.ID_REMOVE, 'label': _translate('Remove task'),
             'status': 'Removing task',
             'func': self.removeTask},
            {'id': wx.ID_CLEAR, 'label': _translate('Clear all'),
             'status': _translate('Clearing tasks'),
             'func': self.clearTasks},
            {'id': wx.ID_SAVE,
             'label': _translate('&Save list')+'\t%s'%keys['save'],
             'status': _translate('Saving task'),
             'func': self.saveTaskList},
            {'id': wx.ID_OPEN, 'label': _translate('&Open list')+'\tCtrl-O',
             'status': _translate('Loading task'),
             'func': self.loadTaskList},
            {'id': wx.ID_CLOSE_FRAME, 'label': _translate('Close')+'\tCtrl-W',
             'status': _translate('Closing Runner'),
             'func': self.onClose},
            {'id': wx.ID_EXIT, 'label': _translate("&Quit\t%s") % keys['quit'],
             'status': _translate('Quitting PsychoPy'),
             'func': self.onQuit},
        ]

        viewMenuItems = [
        ]

        runMenuItems = [
            {'id': wx.ID_ANY,
             'label': _translate("&Run/pilot\t%s") % keys['runScript'],
             'status': _translate('Running experiment'),
             'func': self.panel.onRunShortcut},
            {'id': wx.ID_ANY,
             'label': _translate('Run &JS for local debug'),
             'status': _translate('Launching local debug of online study'),
             'func': self.panel.runOnlineDebug},
            {'id': wx.ID_ANY,
             'label': _translate('Run JS on &Pavlovia'),
             'status': _translate('Launching online study at Pavlovia'),
             'func': self.panel.runOnline},
            ]

        demosMenuItems = [
            {'id': wx.ID_ANY,
             'label': _translate("&Builder Demos"),
             'status': _translate("Loading builder demos"),
             'func': self.loadBuilderDemos},
            {'id': wx.ID_ANY,
             'label': _translate("&Coder Demos"),
             'status': _translate("Loading coder demos"),
             'func': self.loadCoderDemos},
        ]

        menus = [
            {'menu': fileMenu, 'menuItems': fileMenuItems, 'separators': ['clear all', 'load list']},
            {'menu': viewMenu, 'menuItems': viewMenuItems, 'separators': []},
            {'menu': runMenu, 'menuItems': runMenuItems, 'separators': []},
            {'menu': demosMenu, 'menuItems': demosMenuItems, 'separators': []},
        ]

        # Add items to menus
        for eachMenu in menus:
            for item in eachMenu['menuItems']:
                fileItem = eachMenu['menu'].Append(item['id'], item['label'], item['status'])
                self.Bind(wx.EVT_MENU, item['func'], fileItem)
                if item['label'].lower() in eachMenu['separators']:
                    eachMenu['menu'].AppendSeparator()

        # Theme switcher
        self.themesMenu = ThemeSwitcher(app=self.app)
        viewMenu.AppendSubMenu(self.themesMenu, _translate("&Themes"))

        # Frame switcher
        FrameSwitcher.makeViewSwitcherButtons(viewMenu, frame=self, app=self.app)

        # Create menus
        self.runnerMenu.Append(fileMenu, _translate('&File'))
        self.runnerMenu.Append(viewMenu, _translate('&View'))
        self.runnerMenu.Append(runMenu, _translate('&Run'))
        self.runnerMenu.Append(demosMenu, _translate('&Demos'))

        # Add frame switcher
        self.windowMenu = FrameSwitcher(self)
        self.runnerMenu.Append(self.windowMenu, _translate('&Window'))

    def saveTaskList(self, evt=None):
        """Save task list as psyrun file."""
        if hasattr(self, 'listname'):
            filename = self.listname
        else:
            filename = "untitled.psyrun"
        initPath, filename = os.path.split(filename)

        _w = "PsychoPy task lists (*.psyrun)|*.psyrun|Any file (*.*)|*"
        if sys.platform != 'darwin':
            _w += '.*'
        wildcard = _translate(_w)
        dlg = wx.FileDialog(
            self, message=_translate("Save task list as ..."), defaultDir=initPath,
            defaultFile=filename, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            wildcard=wildcard)

        if dlg.ShowModal() == wx.ID_OK:
            newPath = dlg.GetPath()
            # actually save
            experiments = []
            for i in range(self.panel.expCtrl.GetItemCount()):
                experiments.append(
                    {
                        'path': self.panel.expCtrl.GetItem(i, folderColumn).Text,
                        'file': self.panel.expCtrl.GetItem(i, filenameColumn).Text,
                        'runMode': self.panel.expCtrl.GetItem(i, runModeColumn).Text,
                    },
                )
            with open(newPath, 'w') as file:
                json.dump(experiments, file)
            self.listname = newPath

        dlg.Destroy()

    def loadTaskList(self, evt=None):
        """Load saved task list from appData."""
        if hasattr(self, 'listname'):
            filename = self.listname
        else:
            filename = "untitled.psyrun"
        initPath, filename = os.path.split(filename)

        _w = "PsychoPy task lists (*.psyrun)|*.psyrun|Any file (*.*)|*"
        if sys.platform != 'darwin':
            _w += '.*'
        wildcard = _translate(_w)
        dlg = wx.FileDialog(
            self, message=_translate("Open task list ..."), defaultDir=initPath,
            defaultFile=filename, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            wildcard=wildcard)

        fileOk = True
        newPath = None
        if dlg.ShowModal() == wx.ID_OK:  # file was selected
            newPath = dlg.GetPath()
            with open(newPath, 'r') as file:
                try:
                    experiments = json.load(file)
                except Exception:  # broad catch, but lots of stuff can go wrong
                    fileOk = False

                if fileOk:
                    self.panel.entries = {}
                    self.panel.expCtrl.DeleteAllItems()
                    for exp in experiments:
                        self.panel.addTask(
                            fileName=os.path.join(exp['path'], exp['file']),
                            runMode=exp.get('runMode', "run")
                        )
                    self.listname = newPath

        dlg.Destroy()  # close the file browser

        if newPath is None:  # user cancelled
            if evt is not None:
                evt.Skip()
            return

        if not fileOk:  # file failed to load, show an error dialog
            errMsg = (
                u"Failed to open file '{}', check if the file has the "
                u"correct UTF-8 encoding and is the correct format."
            )
            errMsg = errMsg.format(str(newPath))
            errDlg = wx.MessageDialog(
                None, errMsg, 'Error',
                wx.OK | wx.ICON_ERROR)
            errDlg.ShowModal()
            errDlg.Destroy()

    def clearTasks(self, evt=None):
        """Clear all items from the panels expCtrl ListCtrl."""
        self.panel.expCtrl.DeleteAllItems()
        self.panel.currentSelection = None
        self.panel.currentProject = None
        self.panel.currentFile = None

    def onClose(self, event=None):
        """Define Frame closing behavior."""
        self.app.runner = None
        allFrames = self.app.getAllFrames()
        lastFrame = len(allFrames) == 1
        if lastFrame:
            self.onQuit()
        else:
            self.Hide()
        self.app.forgetFrame(self)
        self.app.updateWindowMenu()

    def onQuit(self, evt=None):
        sys.stderr = sys.stdout = sys.__stdout__
        self.panel.stopTask()
        self.app.quit(evt)

    def checkSave(self):
        return True

    def viewBuilder(self, evt):
        if self.panel.currentFile is None:
            self.app.showBuilder()
            return

        for frame in self.app.getAllFrames("builder"):
            if frame.filename == 'untitled.psyexp' and frame.lastSavedCopy is None:
                frame.fileOpen(filename=str(self.panel.currentFile))
                return

        self.app.showBuilder(fileList=[str(self.panel.currentFile)])

    def viewCoder(self, evt):
        if self.panel.currentFile is None:
            self.app.showCoder()
            return

        self.app.showCoder()  # ensures that a coder window exists
        self.app.coder.setCurrentDoc(str(self.panel.currentFile))
        self.app.coder.setFileModified(False)

    def showRunner(self):
        self.app.showRunner()

    def loadBuilderDemos(self, event):
        """Load Builder demos"""
        self.panel.expCtrl.DeleteAllItems()
        unpacked = self.app.prefs.builder['unpackedDemosDir']
        if not unpacked:
            return
        # list available demos
        demoList = sorted(glob.glob(os.path.join(unpacked, '*')))
        demos = {wx.NewIdRef(): demoList[n]
                 for n in range(len(demoList))}
        for thisID in demos:
            junk, shortname = os.path.split(demos[thisID])
            if (shortname.startswith('_') or
                    shortname.lower().startswith('readme.')):
                continue  # ignore 'private' or README files
            for file in os.listdir(demos[thisID]):
                if file.endswith('.psyexp'):
                    self.addTask(fileName=os.path.join(demos[thisID], file))

    def loadCoderDemos(self, event):
        """Load Coder demos"""
        self.panel.expCtrl.DeleteAllItems()
        _localized = {'basic': _translate('basic'),
                      'input': _translate('input'),
                      'stimuli': _translate('stimuli'),
                      'experiment control': _translate('exp control'),
                      'iohub': 'ioHub',  # no translation
                      'hardware': _translate('hardware'),
                      'timing': _translate('timing'),
                      'misc': _translate('misc')}
        folders = glob.glob(os.path.join(self.paths['demos'], 'coder', '*'))
        for folder in folders:
            # if it isn't a folder then skip it
            if (not os.path.isdir(folder)):
                continue
            # otherwise create a submenu
            folderDisplayName = os.path.split(folder)[-1]
            if folderDisplayName.startswith('_'):
                continue  # don't include private folders
            if folderDisplayName in _localized:
                folderDisplayName = _localized[folderDisplayName]

            # find the files in the folder (search two levels deep)
            demoList = glob.glob(os.path.join(folder, '*.py'))
            demoList += glob.glob(os.path.join(folder, '*', '*.py'))
            demoList += glob.glob(os.path.join(folder, '*', '*', '*.py'))

            demoList.sort()

            for thisFile in demoList:
                shortname = thisFile.split(os.path.sep)[-1]
                if shortname == "run.py":
                    # file is just "run" so get shortname from directory name
                    # instead
                    shortname = thisFile.split(os.path.sep)[-2]
                elif shortname.startswith('_'):
                    continue  # remove any 'private' files
                self.addTask(fileName=thisFile)

    @property
    def taskList(self):
        """
        Retrieve item paths from expCtrl.

        Returns
        -------
        taskList : list of filepaths
        """
        temp = []
        for idx in range(self.panel.expCtrl.GetItemCount()):
            filename = self.panel.expCtrl.GetItem(idx, filenameColumn).Text
            folder = self.panel.expCtrl.GetItem(idx, folderColumn).Text
            temp.append(str(Path(folder) / filename))
        return temp


class RunnerPanel(wx.Panel, ScriptProcess, handlers.ThemeMixin):
    def __init__(self, parent=None, id=wx.ID_ANY, title='', app=None):
        super(RunnerPanel, self).__init__(parent=parent,
                                          id=id,
                                          pos=wx.DefaultPosition,
                                          size=[1080, 720],
                                          style=wx.DEFAULT_FRAME_STYLE,
                                          name=title,
                                          )
        ScriptProcess.__init__(self, app)
        #self.Bind(wx.EVT_END_PROCESS, self.onProcessEnded)

        # double buffered better rendering except if retina
        self.SetDoubleBuffered(parent.IsDoubleBuffered())
        self.SetMinSize(wx.Size(640, 480))

        self.app = app
        self.prefs = self.app.prefs.coder
        self.paths = self.app.prefs.paths
        self.parent = parent
        # start values for server stuff
        self.serverProcess = None
        self.serverPort = None

        # self.entries is dict of dicts: {filepath: {'index': listCtrlInd}} and may store more info later
        self.entries = {}
        self.currentFile = None
        self.currentProject = None  # access from self.currentProject property
        self.currentSelection = None
        self.currentExperiment = None

        # setup sizer
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)

        # setup ribbon
        self.ribbon = RunnerRibbon(self)
        self.mainSizer.Add(self.ribbon, border=0, flag=wx.EXPAND | wx.ALL)

        # Setup splitter
        self.splitter = wx.SplitterWindow(self, style=wx.SP_NOBORDER)
        self.mainSizer.Add(self.splitter, proportion=1, border=0, flag=wx.EXPAND | wx.ALL)

        # Setup panel for top half (experiment control and toolbar)
        self.topPanel = wx.Panel(self.splitter)
        self.topPanel.border = wx.BoxSizer()
        self.topPanel.SetSizer(self.topPanel.border)
        self.topPanel.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.topPanel.border.Add(self.topPanel.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)

        # ListCtrl for list of tasks
        self.expCtrl = wx.ListCtrl(self.topPanel,
                                   id=wx.ID_ANY,
                                   style=wx.LC_REPORT | wx.BORDER_NONE | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL)
        self.expCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED,
                          self.onItemSelected, self.expCtrl)
        self.expCtrl.Bind(wx.EVT_LIST_ITEM_DESELECTED,
                          self.onItemDeselected, self.expCtrl)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onDoubleClick, self.expCtrl)
        self.expCtrl.InsertColumn(filenameColumn, _translate('File'))
        self.expCtrl.InsertColumn(folderColumn, _translate('Path'))
        self.expCtrl.InsertColumn(folderColumn, _translate('Run mode'))
        self.topPanel.sizer.Add(self.expCtrl, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)

        # Setup panel for bottom half (alerts and stdout)
        self.bottomPanel = wx.Panel(self.splitter, style=wx.BORDER_NONE)
        self.bottomPanel.border = wx.BoxSizer()
        self.bottomPanel.SetSizer(self.bottomPanel.border)
        self.bottomPanel.sizer = wx.BoxSizer(wx.VERTICAL)
        self.bottomPanel.border.Add(self.bottomPanel.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)

        # Setup notebook for output
        self.outputNotebook = RunnerOutputNotebook(self.bottomPanel)
        self.stdoutPnl = self.outputNotebook.stdoutPnl
        self.stdoutCtrl = self.outputNotebook.stdoutPnl.ctrl
        self.alertsPnl = self.outputNotebook.alertsPnl
        self.alertsCtrl = self.outputNotebook.alertsPnl.ctrl
        self.bottomPanel.sizer.Add(
            self.outputNotebook, proportion=1, border=6, flag=wx.ALL | wx.EXPAND
        )

        # Assign to splitter
        self.splitter.SplitVertically(
            window1=self.topPanel,
            window2=self.bottomPanel,
            sashPosition=480
        )
        self.splitter.SetMinimumPaneSize(360)

        self.SetSizerAndFit(self.mainSizer)

        # Set starting states on buttons
        self.ribbon.buttons['pystop'].Disable()
        self.ribbon.buttons['remove'].Disable()

        self.theme = parent.theme

    def __del__(self):
        if self.serverProcess is not None:
            self.killServer()

    def _applyAppTheme(self):
        # Srt own background
        self.SetBackgroundColour(colors.app['panel_bg'])
        self.topPanel.SetBackgroundColour(colors.app['panel_bg'])
        self.bottomPanel.SetBackgroundColour(colors.app['panel_bg'])
        # Theme buttons
        self.ribbon.theme = self.theme
        # Theme notebook
        self.outputNotebook.theme = self.theme
        bmps = {
            self.alertsPnl: icons.ButtonIcon("alerts", size=16).bitmap,
            self.stdoutPnl: icons.ButtonIcon("stdout", size=16).bitmap,
            self.outputNotebook.gitPnl: icons.ButtonIcon("pavlovia", size=16).bitmap,
        }
        for i in range(self.outputNotebook.GetPageCount()):
            pg = self.outputNotebook.GetPage(i)
            if pg in bmps:
                self.outputNotebook.SetPageBitmap(i, bmps[pg])
        # Apply app theme on objects in non-theme-mixin panels
        for obj in (
                self.expCtrl, self.ribbon
        ):
            obj.theme = self.theme
            if hasattr(obj, "_applyAppTheme"):
                obj._applyAppTheme()
            else:
                handlers.ThemeMixin._applyAppTheme(obj)

        self.Refresh()

    def setAlertsVisible(self, new=True):
        if new:
            self.outputNotebook.SetSelectionToPage(
                self.outputNotebook.GetPageIndex(self.alertsPnl)
            )

    def setStdoutVisible(self, new=True):
        if new:
            self.outputNotebook.SetSelectionToPage(
                self.outputNotebook.GetPageIndex(self.stdoutPnl)
            )

    def stopTask(self, event=None):
        """Kill script processes currently running."""
        # Stop subprocess script running local server
        if self.serverProcess is not None:
            self.serverProcess.kill()
            self.serverProcess = None

        # Stop local Runner processes
        if self.scriptProcess is not None:
            self.stopFile(event)

        self.ribbon.buttons['pystop'].Disable()
        if self.currentSelection:
            self.ribbon.buttons['pyrun'].Enable()
            self.ribbon.buttons['pypilot'].Enable()

    def onRunShortcut(self, evt=None):
        """
        Callback for when the run shortcut is pressed - will either run or pilot depending on run mode
        """
        # do nothing if we have no experiment
        if self.currentExperiment is None:
            return
        # run/pilot according to mode
        if self.currentExperiment.runMode:
            self.runLocal(evt)
        else:
            self.pilotLocal(evt)

    def runLocal(self, evt=None, focusOnExit='runner', args=None):
        """Run experiment from new process using inherited ScriptProcess class methods."""
        if self.currentSelection is None:
            return

        # substitute args
        if args is None:
            args = []
        # start off looking at stdout (will switch to Alerts if there are any)
        self.outputNotebook.SetSelectionToWindow(self.stdoutPnl)

        currentFile = str(self.currentFile)
        if self.currentFile.suffix == '.psyexp':
            generateScript(
                exp=self.loadExperiment(),
                outfile=currentFile.replace('.psyexp', '_lastrun.py')
            )
        procStarted = self.runFile(
            fileName=currentFile,
            focusOnExit=focusOnExit,
            args=args
        )

        # Enable/Disable btns
        if procStarted:
            self.ribbon.buttons['pyrun'].Disable()
            self.ribbon.buttons['pypilot'].Disable()
            self.ribbon.buttons['pystop'].Enable()

    def pilotLocal(self, evt=None, focusOnExit='runner', args=None):
        # run in pilot mode
        self.runLocal(evt, args=["--pilot"], focusOnExit=focusOnExit)

    def runOnline(self, evt=None):
        """Run PsychoJS task from https://pavlovia.org."""
        if self.currentProject not in [None, "None", ''] and self.currentFile.suffix == '.psyexp':
            webbrowser.open(
                "https://pavlovia.org/run/{}/{}"
                    .format(self.currentProject,
                            self.outputPath))

    def runOnlineDebug(self, evt, port=12002):
        """
        Open PsychoJS task on local server running from localhost.

        Local debugging is useful before pushing up to Pavlovia.

        Parameters
        ----------
        port: int
            The port number used for the localhost server
        """
        if self.currentSelection is None:
            return

        # get relevant paths
        htmlPath = str(self.currentFile.parent / self.outputPath)
        jsFile = self.currentFile.parent / (self.currentFile.stem + ".js")
        # make sure JS file exists
        if not os.path.exists(jsFile):
            generateScript(outfile=str(jsFile),
                           exp=self.loadExperiment(),
                           target="PsychoJS")
        # start server
        self.startServer(htmlPath, port=port)
        # open experiment
        webbrowser.open("http://localhost:{}".format(port))
        # log experiment open
        print(
            f"##### Running PsychoJS task from {htmlPath} on port {port} #####\n"
        )

    def startServer(self, htmlPath, port=12002):
        # we only want one server process open
        if self.serverProcess is not None:
            self.killServer()
        # get PsychoJS libs
        self.getPsychoJS()
        # construct command
        command = [sys.executable, "-m", "http.server", str(port)]
        # open server
        self.serverPort = port
        self.serverProcess = Popen(
            command,
            bufsize=1,
            cwd=htmlPath,
            stdout=PIPE,
            stderr=PIPE,
            shell=False,
            universal_newlines=True,
        )
        time.sleep(.1)
        # log server start
        logging.info(f"Local server started on port {port} in directory {htmlPath}")

    def killServer(self):
        # we can only close if there is a process
        if self.serverProcess is None:
            return
        # kill subprocess
        self.serverProcess.terminate()
        time.sleep(.1)
        # log server stopped
        logging.info(f"Local server on port {self.serverPort} stopped")
        # reset references to server stuff
        self.serverProcess = None
        self.serverPort = None

    def onURL(self, evt):
        self.parent.onURL(evt)

    def getPsychoJS(self, useVersion=''):
        """
        Download and save the current version of the PsychoJS library.

        Useful for debugging, amending scripts.
        """
        libPath = self.currentFile.parent / self.outputPath / 'lib'
        ver = versions.getPsychoJSVersionStr(self.app.version, useVersion)
        libFileExtensions = ['css', 'iife.js', 'iife.js.map', 'js', 'js.LEGAL.txt', 'js.map']

        try:  # ask-for-forgiveness rather than query-then-make
            os.makedirs(libPath)
        except OSError as e:
            if e.errno != errno.EEXIST:  # we only want to ignore "exists", not others like permissions
                raise  # raises the error again

        for ext in libFileExtensions:
            finalPath = libPath / ("psychojs-{}.{}".format(ver, ext))
            if finalPath.exists():
                continue
            url = "https://lib.pavlovia.org/psychojs-{}.{}".format(ver, ext)
            req = requests.get(url)
            with open(finalPath, 'wb') as f:
                f.write(req.content)

        print("##### PsychoJS libs downloaded to {} #####\n".format(libPath))

    def addTask(self, evt=None, fileName=None, runMode="run"):
        """
        Add task to the expList listctrl.

        Only adds entry if current entry does not exist in list.
        Can be passed a filename to add to the list.

        Parameters
        ----------
        evt: wx.Event
        fileName: str
            Filename of task to add to list
        """
        if fileName:  # Filename passed from outside runner
            if Path(fileName).suffix not in ['.py', '.psyexp']:
                print("##### You can only add Python files or psyexp files to the Runner. #####\n")
                return
            filePaths = [fileName]
        else:
            with wx.FileDialog(self, "Open task...", wildcard="Tasks (*.py;*.psyexp)|*.py;*.psyexp",
                               style=wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST) as fileDialog:

                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return  # the user changed their mind

                filePaths = fileDialog.GetPaths()

        for thisFile in filePaths:
            thisFile = Path(thisFile)
            if thisFile.absolute() in self.entries:
                thisIndex = self.entries[thisFile.absolute()]['index']
            else:
                # Set new item in listCtrl
                thisIndex = self.expCtrl.InsertItem(self.expCtrl.GetItemCount(),
                                                str(thisFile.name))  # implicitly filenameColumn
                self.expCtrl.SetItem(thisIndex, folderColumn, str(thisFile.parent))  # add the folder name
                # add the new item to our list of files
                self.entries[thisFile.absolute()] = {'index': thisIndex}
            # load psyexp
            if thisFile.suffix == ".psyexp":
                # get run mode from file
                if experiment.Experiment.getRunModeFromFile(thisFile):
                    runMode = "run"
                else:
                    runMode = "pilot"
            # set run mode for item
            self.expCtrl.SetItem(thisIndex, runModeColumn, runMode)

        if filePaths:  # set selection to the final item to be added
            # Set item selection
            # de-select previous
            self.expCtrl.SetItemState(self.currentSelection or 0, 0, wx.LIST_STATE_SELECTED)
            # select new
            self.setSelection(thisIndex)  # calls onSelectItem which updates other info

        # Set column width
        self.expCtrl.SetColumnWidth(filenameColumn, wx.LIST_AUTOSIZE)
        self.expCtrl.SetColumnWidth(folderColumn, wx.LIST_AUTOSIZE)
        self.expCtrl.SetColumnWidth(runModeColumn, wx.LIST_AUTOSIZE)

        self.expCtrl.Refresh()

    def removeTask(self, evt):
        """Remove experiment entry from the expList listctrl."""
        if self.currentSelection is None:
            self.currentProject = None
            return

        if self.expCtrl.GetItemCount() == 0:
            self.currentSelection = None
            self.currentFile = None
            self.currentExperiment = None
            self.currentProject = None

        del self.entries[self.currentFile]  # remove from our tracking dictionary
        self.expCtrl.DeleteItem(self.currentSelection) # from wx control
        self.app.updateWindowMenu()

    def onRunModeToggle(self, evt):
        """
        Function to execute when switching between pilot and run modes
        """
        mode = evt.GetInt()
        # update buttons
        # show/hide run buttons
        for key in ("pyrun", "jsrun"):
            self.ribbon.buttons[key].Show(mode)
        # hide/show pilot buttons
        for key in ("pypilot", "jspilot"):
            self.ribbon.buttons[key].Show(not mode)
        # update experiment mode
        if self.currentExperiment is not None:
            # find any Builder windows with this experiment open
            for frame in self.app.getAllFrames(frameType='builder'):
                if frame.exp == self.currentExperiment:
                    frame.ribbon.buttons['pyswitch'].setMode(mode)
            # update current selection
            runMode = "pilot"
            if mode:
                runMode = "run"
            self.expCtrl.SetItem(self.currentSelection, runModeColumn, runMode)
        # update
        self.ribbon.Update()
        self.ribbon.Refresh()
        self.ribbon.Layout()

    def setSelection(self, index):
        self.expCtrl.Select(index)
        self.onItemSelected(index)

    def onItemSelected(self, evt):
        """Set currentSelection to index of currently selected list item."""
        if not isinstance(evt, int):
            evt = evt.Index
        self.currentSelection = evt
        filename = self.expCtrl.GetItemText(self.currentSelection, filenameColumn)
        folder = self.expCtrl.GetItemText(self.currentSelection, folderColumn)
        runMode = self.expCtrl.GetItemText(self.currentSelection, runModeColumn)
        self.currentFile = Path(folder, filename)
        self.currentExperiment = self.loadExperiment()
        self.currentProject = None  # until it's needed (slow to update)
        # thisItem = self.entries[self.currentFile]

        self.ribbon.buttons['remove'].Enable()
        # enable run/pilot ctrls
        self.ribbon.buttons['pyswitch'].Enable()
        self.ribbon.buttons['pyrun'].Enable()
        self.ribbon.buttons['pypilot'].Enable()
        # enable JS run
        if self.currentFile.suffix == '.psyexp':
            self.ribbon.buttons['jsrun'].Enable()
            self.ribbon.buttons['jspilot'].Enable()
        else:
            self.ribbon.buttons['jsrun'].Disable()
            self.ribbon.buttons['jspilot'].Disable()
        # disable stop
        self.ribbon.buttons['pystop'].Disable()
        # switch mode
        self.ribbon.buttons['pyswitch'].setMode(runMode == "run")
        # update
        self.updateAlerts()
        self.app.updateWindowMenu()
        self.ribbon.Update()
        self.ribbon.Refresh()
        self.ribbon.Layout()

    def onItemDeselected(self, evt):
        """Set currentSelection, currentFile, currentExperiment and currentProject to None."""
        self.expCtrl.SetItemState(self.currentSelection, 0, wx.LIST_STATE_SELECTED)
        self.currentSelection = None
        self.currentFile = None
        self.currentExperiment = None
        self.currentProject = None
        self.ribbon.buttons['pyswitch'].Disable()
        self.ribbon.buttons['pyrun'].Disable()
        self.ribbon.buttons['pypilot'].Disable()
        self.ribbon.buttons['jsrun'].Disable()
        self.ribbon.buttons['jspilot'].Disable()
        self.ribbon.buttons['remove'].Disable()
        self.app.updateWindowMenu()

    def updateAlerts(self):
        prev = sys.stdout
        # check for alerts
        sys.stdout = sys.stderr = self.alertsCtrl
        self.alertsCtrl.Clear()
        if hasattr(self.currentExperiment, 'integrityCheck'):
            self.currentExperiment.integrityCheck()
            nAlerts = len(self.alertsCtrl.alerts)
        else:
            nAlerts = 0
        # update labels and text accordingly
        sys.stdout.flush()
        sys.stdout = sys.stderr = prev
        if nAlerts == 0:
            self.setAlertsVisible(False)

    def onDoubleClick(self, evt):
        self.currentSelection = evt.Index
        filename = self.expCtrl.GetItem(self.currentSelection, filenameColumn).Text
        folder = self.expCtrl.GetItem(self.currentSelection, folderColumn).Text
        filepath = os.path.join(folder, filename)
        if filename.endswith('psyexp'):
            # do we have that file already in a frame?
            builderFrames = self.app.getAllFrames("builder")
            for frame in builderFrames:
                if filepath == frame.filename:
                    frame.Show(True)
                    frame.Raise()
                    self.app.SetTopWindow(frame)
                    return  # we're done
            # that file isn't open so look for a blank frame to reuse
            for frame in builderFrames:
                if frame.filename == 'untitled.psyexp' and frame.lastSavedCopy is None:
                    frame.fileOpen(filename=filepath)
                    frame.Show(True)
                    frame.Raise()
                    self.app.SetTopWindow(frame)
            # no reusable frame so make one
            self.app.showBuilder(fileList=[filepath])
        else:
            self.app.showCoder()  # ensures that a coder window exists
            self.app.coder.setCurrentDoc(filepath)

    def onHover(self, evt):
        btn = evt.GetEventObject()
        btn.SetBackgroundColour(colors.app['bmpbutton_bg_hover'])
        btn.SetForegroundColour(colors.app['bmpbutton_fg_hover'])

    def offHover(self, evt):
        btn = evt.GetEventObject()
        btn.SetBackgroundColour(colors.app['panel_bg'])
        btn.SetForegroundColour(colors.app['text'])

    @property
    def outputPath(self):
        """
        Access and return html output path saved in Experiment Settings from the current experiment.

        Returns
        -------
        output path: str
            The output path, relative to parent folder.
        """
        return self.currentExperiment.settings.params['HTML path'].val

    def loadExperiment(self):
        """
        Load the experiment object for the current psyexp file.

        Returns
        -------
        PsychoPy Experiment object
        """
        fileName = str(self.currentFile)
        if not os.path.exists(fileName):
            raise FileNotFoundError("File not found: {}".format(fileName))

        # If not a Builder file, return
        if not fileName.endswith('.psyexp'):
            return None

        # Load experiment file
        exp = experiment.Experiment(prefs=self.app.prefs)
        try:
            exp.loadFromXML(fileName)
        except Exception:
            print(u"Failed to load {}. Please send the following to"
                  u" the PsychoPy user list".format(fileName))
            traceback.print_exc()

        return exp

    @property
    def currentProject(self):
        """Returns the current project, updating from the git repo if no
        project currently found"""
        if not self._currentProject:
            # Check for project
            try:
                project = getProject(str(self.currentFile))
                if hasattr(project, 'id'):
                    self._currentProject = project.id
            except NotADirectoryError as err:
                self.stdoutCtrl.write(err)
        return self._currentProject

    @currentProject.setter
    def currentProject(self, project):
        self._currentProject = None


class RunnerOutputNotebook(aui.AuiNotebook, handlers.ThemeMixin):
    def __init__(self, parent):
        aui.AuiNotebook.__init__(self, parent, style=wx.BORDER_NONE)

        # store pages by non-translated names for easy access (see RunnerFrame.getOutputPanel)
        self.panels = {}

        # Alerts
        self.alertsPnl = ScriptOutputPanel(
            parent=parent,
            style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE
        )
        self.alertsPnl.ctrl.Bind(wx.EVT_TEXT, self.onWrite)
        self.AddPage(
            self.alertsPnl, caption=_translate("Alerts")
        )
        self.panels['alerts'] = self.alertsPnl

        # StdOut
        self.stdoutPnl = ScriptOutputPanel(
            parent=parent,
            style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE
        )
        self.stdoutPnl.ctrl.Bind(wx.EVT_TEXT, self.onWrite)
        self.AddPage(
            self.stdoutPnl, caption=_translate("Stdout")
        )
        self.panels['stdout'] = self.stdoutPnl

        # Git (Pavlovia) output
        self.gitPnl = ScriptOutputPanel(
            parent=parent,
            style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE
        )
        self.gitPnl.ctrl.Bind(wx.EVT_TEXT, self.onWrite)
        self.AddPage(
            self.gitPnl, caption=_translate("Pavlovia")
        )
        self.panels['git'] = self.gitPnl

        # bind function when page receives focus
        self._readCache = {}
        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.onFocus)

        self.SetMinSize(wx.Size(100, 100))  # smaller than window min size

    def setRead(self, i, state):
        """
        Mark a tab (by index) as read/unread (determines whether the page gets a little blue dot)

        Parameters
        ----------
        i : int
            Index of the page to set
        state : bool
            True for read (i.e. no dot), False for unread (i.e. dot)
        """
        # if state matches cached state, don't bother updating again
        if self._readCache.get(i, None) == state:
            return
        # cache read value
        self._readCache[i] = state
        # get tab label without asterisk
        label = self.GetPageText(i).replace(" *", "")
        # add/remove asterisk
        if state:
            self.SetPageText(i, label)
        else:
            self.SetPageText(i, label + " *")
        # update
        self.Update()
        self.Refresh()

    def onWrite(self, evt):
        # get ctrl
        ctrl = evt.GetEventObject()
        # iterate through pages
        for i in range(self.GetPageCount()):
            # get page window
            page = self.GetPage(i)
            # is the ctrl a child of that window, and is it deselected?
            if page.IsDescendant(ctrl) and self.GetSelection() != i:
                # mark unread
                self.setRead(i, False)
                # alerts and pavlovia get focus too when written to
                if page in (self.panels['git'], self.panels['alerts']):
                    self.SetSelection(i)

    def onFocus(self, evt):
        # get index of new selection
        i = evt.GetSelection()
        # set read status
        self.setRead(i, True)


class RunnerRibbon(ribbon.FrameRibbon):
    def __init__(self, parent):
        # initialize
        ribbon.FrameRibbon.__init__(self, parent)

        # --- File ---
        self.addSection(
            "list", label=_translate("Manage list"), icon="file"
        )
        # add experiment
        self.addButton(
            section="list", name="add", label=_translate("Add"), icon="addExp",
            tooltip=_translate("Add experiment to list"),
            callback=parent.addTask
        )
        # remove experiment
        self.addButton(
            section="list", name="remove", label=_translate("Remove"), icon="removeExp",
            tooltip=_translate("Remove experiment from list"),
            callback=parent.removeTask
        )
        # save
        self.addButton(
            section="list", name="save", label=_translate("Save"), icon="filesaveas",
            tooltip=_translate("Save task list to a file"),
            callback=parent.parent.saveTaskList
        )
        # load
        self.addButton(
            section="list", name="open", label=_translate("Open"), icon="fileopen",
            tooltip=_translate("Load tasks from a file"),
            callback=parent.parent.loadTaskList
        )

        self.addSeparator()

        # --- Tools ---
        self.addSection(
            "experiment", label=_translate("Experiment"), icon="experiment"
        )
        # switch run/pilot
        runPilotSwitch = self.addSwitchCtrl(
            section="experiment", name="pyswitch",
            labels=(_translate("Pilot"), _translate("Run")),
            callback=parent.onRunModeToggle,
            style=wx.HORIZONTAL
        )

        self.addSeparator()

        # --- Python ---
        self.addSection(
            "py", label=_translate("Desktop"), icon="desktop"
        )
        # pilot Py
        btn = self.addButton(
            section="py", name="pypilot", label=_translate("Pilot"), icon='pyPilot',
            tooltip=_translate("Run the current script in Python with piloting features on"),
            callback=parent.pilotLocal
        )
        btn.Hide()
        # run Py
        btn = self.addButton(
            section="py", name="pyrun", label=_translate("Run"), icon='pyRun',
            tooltip=_translate("Run the current script in Python"),
            callback=parent.runLocal
        )
        btn.Hide()
        # stop
        self.addButton(
            section="py", name="pystop", label=_translate("Stop"), icon='stop',
            tooltip=_translate("Stop the current (Python) script"),
            callback=parent.stopTask
        )

        self.addSeparator()

        # --- JS ---
        self.addSection(
            "browser", label=_translate("Browser"), icon="browser"
        )
        # pilot JS
        btn = self.addButton(
            section="browser", name="jspilot", label=_translate("Pilot in browser"),
            icon='jsPilot',
            tooltip=_translate("Pilot experiment locally in your browser"),
            callback=parent.runOnlineDebug
        )
        btn.Hide()
        # run JS
        btn = self.addButton(
            section="browser", name="jsrun", label=_translate("Run on Pavlovia"), icon='jsRun',
            tooltip=_translate("Run experiment on Pavlovia"),
            callback=parent.runOnline
        )
        btn.Hide()

        self.addSeparator()

        # --- Pavlovia ---
        self.addSection(
            name="pavlovia", label=_translate("Pavlovia"), icon="pavlovia"
        )
        # pavlovia user
        self.addPavloviaUserCtrl(
            section="pavlovia", name="pavuser", frame=parent
        )

        # --- Views ---
        self.addStretchSpacer()
        self.addSeparator()

        self.addSection(
            "views", label=_translate("Views"), icon="windows"
        )
        # show Builder
        self.addButton(
            section="views", name="builder", label=_translate("Show Builder"), icon="showBuilder",
            tooltip=_translate("Switch to Builder view"),
            callback=parent.app.showBuilder
        )
        # show Coder
        self.addButton(
            section="views", name="coder", label=_translate("Show Coder"), icon="showCoder",
            tooltip=_translate("Switch to Coder view"),
            callback=parent.app.showCoder
        )
        # show Runner
        self.addButton(
            section="views", name="runner", label=_translate("Show Runner"), icon="showRunner",
            tooltip=_translate("Switch to Runner view"),
            callback=parent.app.showRunner
        ).Disable()
