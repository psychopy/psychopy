#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import json

from psychopy.app.themes._themes import ThemeSwitcher

from ..themes import ThemeMixin

import wx
from wx.lib import platebtn
import wx.lib.agw.aui as aui  # some versions of phoenix
import os
import sys
import time
import requests
import traceback
import webbrowser
from pathlib import Path
from subprocess import Popen, PIPE

from psychopy import experiment
from psychopy.app.utils import PsychopyPlateBtn, PsychopyToolbar, FrameSwitcher
from psychopy.constants import PY3
from psychopy.localization import _translate
from psychopy.app.stdOutRich import StdOutRich
from psychopy.projects.pavlovia import getProject
from psychopy.scripts.psyexpCompile import generateScript
from psychopy.app.runner.scriptProcess import ScriptProcess


class RunnerFrame(wx.Frame, ThemeMixin):
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
        # double buffered better rendering except if retina
        self.panel.SetDoubleBuffered(not self.isRetina)

        # Create menu
        self.runnerMenu = wx.MenuBar()
        self.makeMenu()
        self.SetMenuBar(self.runnerMenu)

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
        self.theme = app.theme

    @property
    def filename(self):
        if self.panel.currentSelection or self.panel.currentSelection == 0:
            return self.panel.expCtrl.GetItem(self.panel.currentSelection).Text

    def addTask(self, evt=None, fileName=None):
        self.panel.addTask(fileName=fileName)

    def removeTask(self, evt=None):
        self.panel.removeTask(evt)

    @property
    def stdOut(self):
        return self.panel.stdoutCtrl

    @property
    def alerts(self):
        return self.panel.alertsCtrl

    def makeMenu(self):
        """Create Runner menubar."""
        keys = self.app.prefs.keys
        # Menus
        fileMenu = wx.Menu()
        viewMenu = wx.Menu()
        runMenu = wx.Menu()

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
             'label': _translate('Save list')+'\t%s'%keys['save'],
             'status': _translate('Saving task'),
             'func': self.saveTaskList},
            {'id': wx.ID_COPY, 'label': _translate('Open list')+'\tCtrl-O',
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
            {'id': wx.ID_ANY, 'label': _translate("Open &Builder view"),
             'status': _translate("Opening Builder"), 'func': self.viewBuilder},
            {'id': wx.ID_ANY, 'label': _translate("Open &Coder view"),
             'status': _translate('Opening Coder'), 'func': self.viewCoder},
        ]

        runMenuItems = [
            {'id': wx.ID_ANY,
             'label': _translate("Run\t%s") % keys['runScript'],
             'status': _translate('Running experiment'),
             'func': self.panel.runLocal},
            {'id': wx.ID_ANY,
             'label': _translate('Run JS for local debug'),
             'status': _translate('Launching local debug of online study'),
             'func': self.panel.runOnlineDebug},
            {'id': wx.ID_ANY,
             'label': _translate('Run JS on Pavlovia'),
             'status': _translate('Launching online study at Pavlovia'),
             'func': self.panel.runOnline},
            ]

        menus = [
            {'menu': fileMenu, 'menuItems': fileMenuItems, 'separators': ['clear all', 'load list']},
            {'menu': viewMenu, 'menuItems': viewMenuItems, 'separators': []},
            {'menu': runMenu, 'menuItems': runMenuItems, 'separators': []},
        ]

        # Add items to menus
        for eachMenu in menus:
            for item in eachMenu['menuItems']:
                fileItem = eachMenu['menu'].Append(item['id'], item['label'], item['status'])
                self.Bind(wx.EVT_MENU, item['func'], fileItem)
                if item['label'].lower() in eachMenu['separators']:
                    eachMenu['menu'].AppendSeparator()
        # Add Theme Switcher
        self.themesMenu = ThemeSwitcher(self)
        viewMenu.AppendSubMenu(self.themesMenu,
                           _translate("Themes"))
        # Add frame switcher
        self.windowMenu = FrameSwitcher(self)

        # Create menus
        self.runnerMenu.Append(fileMenu, _translate('File'))
        self.runnerMenu.Append(viewMenu, _translate('View'))
        self.runnerMenu.Append(runMenu, _translate('Run'))
        self.runnerMenu.Append(self.windowMenu, _translate('Window'))

    def onURL(self, evt):
        """Open link in default browser."""
        wx.BeginBusyCursor()
        try:
            if evt.String.startswith("http"):
                webbrowser.open(evt.String)
            else:
                # decompose the URL of a file and line number"""
                # "C:\Program Files\wxPython...\samples\hangman\hangman.py"
                filename = evt.GetString().split('"')[1]
                lineNumber = int(evt.GetString().split(',')[1][5:])
                self.app.showCoder()
                self.app.coder.gotoLine(filename, lineNumber)
        except Exception as e:
            print("##### Could not open URL: {} #####\n".format(evt.String))
            print(e)
        wx.EndBusyCursor()

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
                    {'path': self.panel.expCtrl.GetItem(i,1).Text,
                     'file': self.panel.expCtrl.GetItem(i,0).Text}
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
        if dlg.ShowModal() == wx.ID_OK:
            newPath = dlg.GetPath()
            with open(newPath, 'r') as file:
                experiments = json.load(file)
            self.panel.expCtrl.DeleteAllItems()
            for exp in experiments:
                self.panel.addTask(fileName=os.path.join(exp['path'], exp['file']))
            self.listname = newPath

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
            filename = self.panel.expCtrl.GetItem(idx, 0).Text
            folder = self.panel.expCtrl.GetItem(idx, 1).Text
            temp.append(str(Path(folder) / filename))
        return temp


class RunnerPanel(wx.Panel, ScriptProcess, ThemeMixin):
    def __init__(self, parent=None, id=wx.ID_ANY, title='', app=None):
        super(RunnerPanel, self).__init__(parent=parent,
                                          id=id,
                                          pos=wx.DefaultPosition,
                                          size=[400,700],
                                          style=wx.DEFAULT_FRAME_STYLE,
                                          name=title,
                                          )
        ScriptProcess.__init__(self, app)
        self.Bind(wx.EVT_END_PROCESS, self.onProcessEnded)
        #self.SetBackgroundColour(ThemeMixin.appColors['frame_bg'])
        #self.SetForegroundColour(ThemeMixin.appColors['txt_default'])

        # double buffered better rendering except if retina
        self.SetDoubleBuffered(parent.IsDoubleBuffered())

        expCtrlSize = [500, 150]
        ctrlSize = [500, 150]

        self.app = app
        self.prefs = self.app.prefs.coder
        self.paths = self.app.prefs.paths
        self.parent = parent
        self.serverProcess = None

        self.currentFile = None
        self.currentProject = None  # access from self.currentProject property
        self.currentSelection = None
        self.currentExperiment = None

        # Set ListCtrl for list of tasks
        self.expCtrl = wx.ListCtrl(self,
                                   id=wx.ID_ANY,
                                   size=expCtrlSize,
                                   style=wx.LC_REPORT | wx.BORDER_NONE |
                                         wx.LC_NO_HEADER | wx.LC_SINGLE_SEL)

        self.expCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED,
                          self.onItemSelected, self.expCtrl)
        self.expCtrl.Bind(wx.EVT_LIST_ITEM_DESELECTED,
                          self.onItemDeselected, self.expCtrl)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onDoubleClick, self.expCtrl)
        self.expCtrl.InsertColumn(0, _translate('File'))
        self.expCtrl.InsertColumn(1, _translate('Path'))

        _style = platebtn.PB_STYLE_DROPARROW | platebtn.PB_STYLE_SQUARE
        # Alerts
        self._selectedHiddenAlerts = False  # has user manually hidden alerts?
        self.alertsToggleBtn = PsychopyPlateBtn(self, -1, _translate('Alerts'),
                                          style=_style, name='Alerts')
        # mouse event must be bound like this
        self.alertsToggleBtn.Bind(wx.EVT_LEFT_DOWN, self.setAlertsVisible)
        # mouse event must be bound like this
        self.alertsToggleBtn.Bind(wx.EVT_RIGHT_DOWN, self.setAlertsVisible)
        self.alertsCtrl = StdOutText(parent=self,
                                     size=ctrlSize,
                                     style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE)

        self.setAlertsVisible(True)

        # StdOut
        self.stdoutToggleBtn = PsychopyPlateBtn(self, -1, _translate('Stdout'),
                                          style=_style, name='Stdout')
        # mouse event must be bound like this
        self.stdoutToggleBtn.Bind(wx.EVT_LEFT_DOWN, self.setStdoutVisible)
        # mouse event must be bound like this
        self.stdoutToggleBtn.Bind(wx.EVT_RIGHT_DOWN, self.setStdoutVisible)
        self.stdoutCtrl = StdOutText(parent=self,
                                     size=ctrlSize,
                                     style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE)
        self.setStdoutVisible(True)

        # Box sizers
        self.upperSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.upperSizer.Add(self.expCtrl, 1, wx.ALL | wx.EXPAND, 5)

        # Set main sizer
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.upperSizer, 0, wx.EXPAND | wx.ALL, 10)
        self.mainSizer.Add(self.alertsToggleBtn, 0, wx.TOP | wx.EXPAND, 10)
        self.mainSizer.Add(self.alertsCtrl, 1, wx.EXPAND | wx.ALL, 10)
        self.mainSizer.Add(self.stdoutToggleBtn, 0, wx.TOP | wx.EXPAND, 10)
        self.mainSizer.Add(self.stdoutCtrl, 1, wx.EXPAND | wx.ALL, 10)

        self.buttonSizer = wx.BoxSizer(wx.VERTICAL)
        self.upperSizer.Add(self.buttonSizer, 0, wx.ALL | wx.EXPAND, 5)
        self.makeButtons()
        self._applyAppTheme()


    def _applyAppTheme(self, target=None):
        if target is None:
            target = self
        ThemeMixin._applyAppTheme(self, self)
        self.alertsCtrl._applyAppTheme()
        self.stdoutCtrl._applyAppTheme()
        ThemeMixin._applyAppTheme(self.expCtrl)
        for btn in self.buttonSizer.GetChildren():
            if btn.Window:
                btn = btn.Window
                btn.SetBackgroundColour(ThemeMixin.appColors['panel_bg'])

    def makeButtons(self):
        # Set buttons
        icons = self.app.iconCache  # type: IconCache
        self.plusBtn = icons.makeBitmapButton(
                parent=self,
                filename='addExp.png',
                name='addExp',
                tip=_translate(
                        "Add experiment to list"),
                size=32)
        self.Bind(wx.EVT_BUTTON, self.addTask, self.plusBtn)
        self.negBtn = icons.makeBitmapButton(
                parent=self,
                filename='removeExp.png',
                name='removeExp',
                tip=_translate(
                        "Remove experiment from list"),
                size=32)
        self.Bind(wx.EVT_BUTTON, self.removeTask, self.negBtn)
        self.saveBtn = icons.makeBitmapButton(
            parent=self,
            filename='filesaveas.png',
            name='saveTasks',
            tip=_translate(
                "Save task list to a file"),
            size=32)
        self.Bind(wx.EVT_BUTTON, self.parent.saveTaskList, self.saveBtn)
        self.loadBtn = icons.makeBitmapButton(
            parent=self,
            filename='fileopen.png',
            name='loadTasks',
            tip=_translate(
                "Load tasks from a file"),
            size=32)
        self.Bind(wx.EVT_BUTTON, self.parent.loadTaskList, self.loadBtn)
        self.runBtn = icons.makeBitmapButton(
                parent=self, filename='run.png',
                name='run',
                tip=_translate(
                        "Run the current script in Python"),
                size=32)
        self.Bind(wx.EVT_BUTTON, self.runLocal, self.runBtn)
        self.stopBtn = icons.makeBitmapButton(
                parent=self, filename='stop.png',
                name='stop',
                tip=_translate("Stop task"),
                size=32)
        self.Bind(wx.EVT_BUTTON, self.stopTask, self.stopBtn)
        self.onlineBtn = icons.makeBitmapButton(
                parent=self,
                filename='globe.png',
                emblem='run', tip=_translate(
                        "Run PsychoJS task from Pavlovia"), size=32)
        self.Bind(wx.EVT_BUTTON, self.runOnline, self.onlineBtn)
        self.onlineDebugBtn = icons.makeBitmapButton(
                parent=self,
                filename='globe.png',
                name='globe',
                emblem='bug',
                tip=_translate(
                        "Run PsychoJS task in local debug mode"),
                size=32)
        self.Bind(wx.EVT_BUTTON, self.runOnlineDebug, self.onlineDebugBtn)
        # Add buttons to sizer
        self.buttonSizer.AddMany([(self.plusBtn, 0, wx.ALL | wx.ALIGN_TOP, 5),
                                      (self.negBtn, 0, wx.ALL | wx.ALIGN_TOP, 5),
                                      (self.saveBtn, 0, wx.ALL, 5),
                                      (self.loadBtn, 0, wx.ALL, 5),
                                      (self.runBtn, 0, wx.ALL, 5),
                                      (self.stopBtn, 0, wx.ALL, 5),
                                      (self.onlineBtn, 0, wx.ALL, 5),
                                      (self.onlineDebugBtn, 0, wx.ALL, 5),
                                      ])
        self.stopBtn.Disable()
        self.SetSizerAndFit(self.mainSizer)
        self.SetMinSize(self.Size)

    def onProcessEnded(self):
        ScriptProcess.onProcessEnded(self)
        self.stopTask()

    def setAlertsVisible(self, new=True):
        if type(new) == bool:
            self.alertsCtrl.Show(new)
        # or could be an event from button click (a toggle)
        else:
            show = (not self.alertsCtrl.IsShown())
            self.alertsCtrl.Show(show)
            self._selectedHiddenAlerts = not show
        self.Layout()

    def setStdoutVisible(self, new=True):
        # could be a boolean from our own code
        if type(new) == bool:
            self.stdoutCtrl.Show(new)
        # or could be an event (so toggle) from button click
        else:
            self.stdoutCtrl.Show(not self.stdoutCtrl.IsShown())
        self.Layout()

    def stopTask(self, event=None):
        """Kill script processes currently running."""
        # Stop subprocess script running local server
        if self.serverProcess is not None:
            self.serverProcess.kill()
            self.serverProcess = None

        # Stop local Runner processes
        if self.scriptProcess is not None:
            self.stopFile(event)

        self.stopBtn.Disable()
        self.runBtn.Enable()

    def runLocal(self, evt):
        """Run experiment from new process using inherited ScriptProcess class methods."""
        if self.currentSelection is None:
            return

        currentFile = str(self.currentFile)
        if self.currentFile.suffix == '.psyexp':
            generateScript(experimentPath=currentFile.replace('.psyexp', '_lastrun.py'),
                           exp=self.loadExperiment())
        self.runFile(fileName=currentFile)

        # Enable/Disable btns
        self.runBtn.Disable()
        self.stopBtn.Enable()

    def runOnline(self, evt):
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

        # we only want one server process open
        if self.serverProcess is not None:
            self.serverProcess.kill()
            self.serverProcess = None

        # Get PsychoJS libs
        self.getPsychoJS()

        htmlPath = str(self.currentFile.parent / self.outputPath)
        server = ["SimpleHTTPServer", "http.server"][PY3]
        pythonExec = Path(sys.executable)
        command = [str(pythonExec), "-m", server, str(port)]

        if not os.path.exists(htmlPath):
            print('##### HTML output path: "{}" does not exist. '
                  'Try exporting your HTML, and try again #####\n'.format(self.outputPath))
            return

        self.serverProcess = Popen(command,
                                   bufsize=1,
                                   cwd=htmlPath,
                                   stdout=PIPE,
                                   stderr=PIPE,
                                   shell=False,
                                   universal_newlines=True,
                                   )

        time.sleep(.1)  # Wait for subprocess to start server
        webbrowser.open("http://localhost:{}".format(port))
        print("##### Local server started! #####\n\n"
              "##### Running PsychoJS task from {} #####\n".format(htmlPath))

    def onURL(self, evt):
        self.parent.onURL(evt)

    def getPsychoJS(self):
        """
        Download and save the current version of the PsychoJS library.

        Useful for debugging, amending scripts.
        """
        libPath = str(self.currentFile.parent / self.outputPath / 'lib')
        ver = '.'.join(self.app.version.split('.')[:2])
        psychoJSLibs = ['core', 'data', 'util', 'visual', 'sound']

        os.path.exists(libPath) or os.makedirs(libPath)

        if len(sorted(Path(libPath).glob('*.js'))) >= len(psychoJSLibs):  # PsychoJS lib files exist
            print("##### PsychoJS lib already exists in {} #####\n".format(libPath))
            return

        for lib in psychoJSLibs:
            url = "https://lib.pavlovia.org/{}-{}.js".format(lib, ver)
            req = requests.get(url)
            with open(libPath + "/{}-{}.js".format(lib, ver), 'wb') as f:
                f.write(req.content)

        print("##### PsychoJS libs downloaded to {} #####\n".format(libPath))

    def addTask(self, evt=None, fileName=None):
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
            with wx.FileDialog(self, "Open task...", wildcard="*.py; *.psyexp | *.py; *.psyexp",
                               style=wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST) as fileDialog:

                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return  # the user changed their mind

                filePaths = fileDialog.GetPaths()

        for file in filePaths:
            temp = Path(file)

            # Check list for items
            start = -1
            fullPaths = []
            while start < self.expCtrl.GetItemCount()-1:
                index = self.expCtrl.FindItem(start, temp.name)
                if index > -1:
                    fullPaths += [Path(self.expCtrl.GetItem(index, 1).Text, self.expCtrl.GetItem(index, 0).Text)]
                    start = index+1
                else:
                    start = self.expCtrl.GetItemCount()
            if temp in fullPaths:
                continue

            # Set new item in listCtrl
            index = self.expCtrl.InsertItem(self.expCtrl.GetItemCount(),
                                            str(temp.name))
            self.expCtrl.SetItem(index, 1, str(temp.parent))  # add the folder name

        if filePaths:  # set selection to the final item to be added
            # Set item selection
            # de-select previous
            self.expCtrl.SetItemState(self.currentSelection or 0, 0, wx.LIST_STATE_SELECTED)
            # select new
            self.expCtrl.Select(index)

        # Set column width
        self.expCtrl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.expCtrl.SetColumnWidth(1, wx.LIST_AUTOSIZE)

    def removeTask(self, evt):
        """Remove experiment entry from the expList listctrl."""
        if self.currentSelection is None:
            self.currentProject = None
            return

        self.expCtrl.DeleteItem(self.currentSelection)
        if self.expCtrl.GetItemCount() == 0:
            self.currentSelection = None
            self.currentFile = None
            self.currentExperiment = None
            self.currentProject = None
        self.app.updateWindowMenu()

    def onItemSelected(self, evt):
        """Set currentSelection to index of currently selected list item."""
        self.currentSelection = evt.Index
        filename = self.expCtrl.GetItem(self.currentSelection, 0).Text
        folder = self.expCtrl.GetItem(self.currentSelection, 1).Text
        self.currentFile = Path(folder, filename)
        self.currentExperiment = self.loadExperiment()
        self.currentProject = None  # until it's needed (slow to update)
        self.runBtn.Enable()
        self.stopBtn.Disable()
        if self.currentFile.suffix == '.psyexp':
            self.onlineBtn.Enable()
            self.onlineDebugBtn.Enable()
        else:
            self.onlineBtn.Disable()
            self.onlineDebugBtn.Disable()
        self.updateAlerts()
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
        self.alertsToggleBtn.SetLabelText(_translate("Alerts ({})").format(nAlerts))
        sys.stdout.flush()
        sys.stdout = sys.stderr = prev
        if nAlerts == 0:
            self.setAlertsVisible(False)
        # elif selected hidden then don't touch
        elif not self._selectedHiddenAlerts:
            self.setAlertsVisible(True)

    def onItemDeselected(self, evt):
        """Set currentSelection, currentFile, currentExperiment and currentProject to None."""
        self.expCtrl.SetItemState(self.currentSelection, 0, wx.LIST_STATE_SELECTED)
        self.currentSelection = None
        self.currentFile = None
        self.currentExperiment = None
        self.currentProject = None
        self.runBtn.Disable()
        self.stopBtn.Disable()
        self.onlineBtn.Disable()
        self.onlineDebugBtn.Disable()
        self.app.updateWindowMenu()

    def onDoubleClick(self, evt):
        self.currentSelection = evt.Index
        filename = self.expCtrl.GetItem(self.currentSelection, 0).Text
        folder = self.expCtrl.GetItem(self.currentSelection, 1).Text
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
        cs = ThemeMixin.appColors
        btn = evt.GetEventObject()
        btn.SetBackgroundColour(cs['bmpbutton_bg_hover'])
        btn.SetForegroundColour(cs['bmpbutton_fg_hover'])

    def offHover(self, evt):
        cs = ThemeMixin.appColors
        btn = evt.GetEventObject()
        btn.SetBackgroundColour(cs['panel_bg'])
        btn.SetForegroundColour(cs['text'])

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


class StdOutText(StdOutRich, ThemeMixin):
    """StdOutRich subclass which also handles Git messages from Pavlovia projects."""

    def __init__(self, parent=None, style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE, size=wx.DefaultSize):
        StdOutRich.__init__(self, parent=parent, style=style, size=size)
        self.prefs = parent.prefs
        self.paths = parent.paths
        self._applyAppTheme()

    def getText(self):
        """Get and return the text of the current buffer."""
        return self.GetValue()

    def setStatus(self, status):
        self.SetValue(status)
        self.Refresh()
        self.Layout()
        wx.Yield()

    def statusAppend(self, newText):
        text = self.GetValue() + newText
        self.setStatus(text)

    def write(self, inStr, evt=False):
        # Override default write behaviour to also update theme on each write
        StdOutRich.write(self, inStr, evt)
        self._applyAppTheme()
