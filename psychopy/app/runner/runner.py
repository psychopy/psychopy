#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import glob
import json
import errno

from ..themes import handlers, colors, icons
from ..themes.ui import ThemeSwitcher

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
from psychopy.app.utils import PsychopyPlateBtn, BasePsychopyToolbar, FrameSwitcher, FileDropTarget
from psychopy.localization import _translate
from psychopy.app.stdOutRich import StdOutRich
from psychopy.projects.pavlovia import getProject
from psychopy.scripts.psyexpCompile import generateScript
from psychopy.app.runner.scriptProcess import ScriptProcess
import psychopy.tools.versionchooser as versions

folderColumn = 1
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
             'label': _translate('Save list')+'\t%s'%keys['save'],
             'status': _translate('Saving task'),
             'func': self.saveTaskList},
            {'id': wx.ID_OPEN, 'label': _translate('Open list')+'\tCtrl-O',
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

        demosMenuItems = [
            {'id': wx.ID_ANY,
             'label': _translate("Builder Demos"),
             'status': _translate("Loading builder demos"),
             'func': self.loadBuilderDemos},
            {'id': wx.ID_ANY,
             'label': _translate("Coder Demos"),
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
        # Add Theme Switcher
        self.themesMenu = ThemeSwitcher(app=self.app)
        viewMenu.AppendSubMenu(self.themesMenu,
                           _translate("Themes"))
        # Add frame switcher
        self.windowMenu = FrameSwitcher(self)

        # Create menus
        self.runnerMenu.Append(fileMenu, _translate('File'))
        self.runnerMenu.Append(viewMenu, _translate('View'))
        self.runnerMenu.Append(runMenu, _translate('Run'))
        self.runnerMenu.Append(demosMenu, _translate('Demos'))
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
                    {'path': self.panel.expCtrl.GetItem(i, folderColumn).Text,
                     'file': self.panel.expCtrl.GetItem(i, filenameColumn).Text}
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
                    self.panel.expCtrl.DeleteAllItems()
                    for exp in experiments:
                        self.panel.addTask(
                            fileName=os.path.join(exp['path'], exp['file']))
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

    class SizerButton(wx.ToggleButton, handlers.ThemeMixin):
        """Button to show/hide a category of components"""

        def __init__(self, parent, label, sizer):
            # Initialise button
            wx.ToggleButton.__init__(self, parent,
                                     label="   " + label, size=(-1, 24),
                                     style=wx.BORDER_NONE | wx.BU_LEFT)
            self.parent = parent
            # Link to category of buttons
            self.menu = sizer
            # Default states to false
            self.state = False
            self.hover = False
            # Bind toggle function
            self.Bind(wx.EVT_TOGGLEBUTTON, self.ToggleMenu)
            # Bind hover functions
            self.Bind(wx.EVT_ENTER_WINDOW, self.hoverOn)
            self.Bind(wx.EVT_LEAVE_WINDOW, self.hoverOff)

        def ToggleMenu(self, event):
            # If triggered manually with a bool, treat that as a substitute for event selection
            if isinstance(event, bool):
                state = event
            else:
                state = event.GetSelection()
            self.SetValue(state)
            # Show / hide contents according to state
            self.menu.Show(state)
            # Do layout
            self.parent.Layout()
            # Restyle
            self._applyAppTheme()

        def hoverOn(self, event):
            """Apply hover effect"""
            self.hover = True
            self._applyAppTheme()

        def hoverOff(self, event):
            """Unapply hover effect"""
            self.hover = False
            self._applyAppTheme()

        def _applyAppTheme(self):
            """Apply app theme to this button"""
            if self.hover:
                # If hovered over currently, use hover colours
                self.SetForegroundColour(colors.app['txtbutton_fg_hover'])
                # self.icon.SetForegroundColour(ThemeMixin.appColors['txtbutton_fg_hover'])
                self.SetBackgroundColour(colors.app['txtbutton_bg_hover'])
            else:
                # Otherwise, use regular colours
                self.SetForegroundColour(colors.app['text'])
                # self.icon.SetForegroundColour(ThemeMixin.appColors['text'])
                self.SetBackgroundColour(colors.app['panel_bg'])

    class RunnerToolbar(wx.Panel, handlers.ThemeMixin):
        def __init__(self, parent):
            wx.Panel.__init__(self, parent)
            # Setup sizer
            self.sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.sizer)

            # Plus
            btn = parent.plusBtn = wx.Button(self, size=(32, 32), style=wx.BORDER_NONE)
            btn.SetToolTip(
                _translate("Add experiment to list")
            )
            btn.Bind(wx.EVT_BUTTON, parent.addTask)
            btn.stem = "addExp"
            self.sizer.Add(btn, border=5, flag=wx.ALL)
            # Minus
            btn = parent.negBtn = wx.Button(self, size=(32, 32), style=wx.BORDER_NONE)
            btn.SetToolTip(
                _translate("Remove experiment from list")
            )
            btn.Bind(wx.EVT_BUTTON, parent.removeTask)
            btn.stem = "removeExp"
            self.sizer.Add(btn, border=5, flag=wx.ALL)
            # Save
            btn = parent.saveBtn = wx.Button(self, size=(32, 32), style=wx.BORDER_NONE)
            btn.SetToolTip(
                _translate("Save task list to a file")
            )
            btn.Bind(wx.EVT_BUTTON, parent.parent.saveTaskList)
            btn.stem = "filesaveas"
            self.sizer.Add(btn, border=5, flag=wx.ALL)
            # Load
            btn = parent.loadBtn = wx.Button(self, size=(32, 32), style=wx.BORDER_NONE)
            btn.SetToolTip(
                _translate("Load tasks from a file")
            )
            btn.Bind(wx.EVT_BUTTON, parent.parent.loadTaskList)
            btn.stem = "fileopen"
            self.sizer.Add(btn, border=5, flag=wx.ALL)
            # Run
            btn = parent.runBtn = wx.Button(self, size=(32, 32), style=wx.BORDER_NONE)
            btn.SetToolTip(
                _translate("Run the current script in Python")
            )
            btn.Bind(wx.EVT_BUTTON, parent.runLocal)
            btn.stem = "run"
            self.sizer.Add(btn, border=5, flag=wx.ALL)
            # Stop
            btn = parent.stopBtn = wx.Button(self, size=(32, 32), style=wx.BORDER_NONE)
            btn.SetToolTip(
                _translate("Stop task")
            )
            btn.Bind(wx.EVT_BUTTON, parent.stopTask)
            btn.stem = "stop"
            self.sizer.Add(btn, border=5, flag=wx.ALL)
            # Run online
            btn = parent.onlineBtn = wx.Button(self, size=(32, 32), style=wx.BORDER_NONE)
            btn.SetToolTip(
                _translate("Run PsychoJS task from Pavlovia")
            )
            btn.Bind(wx.EVT_BUTTON, parent.runOnline)
            btn.stem = "globe_run"
            self.sizer.Add(btn, border=5, flag=wx.ALL)
            # Debug online
            btn = parent.onlineDebugBtn = wx.Button(self, size=(32, 32), style=wx.BORDER_NONE)
            btn.SetToolTip(
                _translate("Run PsychoJS task in local debug mode")
            )
            btn.Bind(wx.EVT_BUTTON, parent.runOnlineDebug)
            btn.stem = "globe_bug"
            self.sizer.Add(btn, border=5, flag=wx.ALL)

        def _applyAppTheme(self):
            # Iterate through buttons
            for child in self.GetChildren():
                child.SetBackgroundColour(colors.app['panel_bg'])
                if isinstance(child, wx.Button) and hasattr(child, "stem"):
                    # For each button, recreate bitmap from stored stem
                    child.SetBitmap(
                        icons.ButtonIcon(child.stem, size=(32, 32)).bitmap
                    )

    def __init__(self, parent=None, id=wx.ID_ANY, title='', app=None):
        super(RunnerPanel, self).__init__(parent=parent,
                                          id=id,
                                          pos=wx.DefaultPosition,
                                          size=[400,700],
                                          style=wx.DEFAULT_FRAME_STYLE,
                                          name=title,
                                          )
        ScriptProcess.__init__(self, app)
        #self.Bind(wx.EVT_END_PROCESS, self.onProcessEnded)

        # double buffered better rendering except if retina
        self.SetDoubleBuffered(parent.IsDoubleBuffered())

        expCtrlSize = [500, 150]
        ctrlSize = [500, 150]

        self.app = app
        self.prefs = self.app.prefs.coder
        self.paths = self.app.prefs.paths
        self.parent = parent
        self.serverProcess = None

        # self.entries is dict of dicts: {filepath: {'index': listCtrlInd}} and may store more info later
        self.entries = {}
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
        self.expCtrl.InsertColumn(filenameColumn, _translate('File'))
        self.expCtrl.InsertColumn(folderColumn, _translate('Path'))

        _style = platebtn.PB_STYLE_DROPARROW | platebtn.PB_STYLE_SQUARE
        # Alerts
        self._selectedHiddenAlerts = False  # has user manually hidden alerts?

        self.alertsCtrl = StdOutText(parent=self,
                                     size=ctrlSize,
                                     style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE)
        self.alertsToggleBtn = self.SizerButton(self, _translate("Alerts"), self.alertsCtrl)

        self.setAlertsVisible(True)

        # StdOut
        self.stdoutCtrl = StdOutText(parent=self,
                                     size=ctrlSize,
                                     style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE)
        self.stdoutToggleBtn = self.SizerButton(self, _translate("Stdout"), self.stdoutCtrl)
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

        # Make buttons
        self.toolbar = self.RunnerToolbar(self)
        self.upperSizer.Add(self.toolbar, 0, wx.ALL | wx.EXPAND, 15)

        self.SetSizerAndFit(self.mainSizer)
        self.SetMinSize(self.Size)

        # disable the stop button on start
        self.stopBtn.Disable()

        self.theme = parent.theme

    def _applyAppTheme(self):
        # Srt own background
        self.SetBackgroundColour(colors.app['panel_bg'])
        # Theme buttons
        self.toolbar.theme = self.theme
        # Add icons to buttons
        bmp = icons.ButtonIcon("stdout", size=(16, 16)).bitmap
        self.stdoutToggleBtn.SetBitmap(bmp)
        self.stdoutToggleBtn.SetBitmapMargins(x=6, y=0)
        bmp = icons.ButtonIcon("alerts", size=(16, 16)).bitmap
        self.alertsToggleBtn.SetBitmap(bmp)
        self.alertsToggleBtn.SetBitmapMargins(x=6, y=0)

        self.Refresh()

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
        if self.currentSelection:
            self.runBtn.Enable()

    def runLocal(self, evt=None, focusOnExit='runner'):
        """Run experiment from new process using inherited ScriptProcess class methods."""
        if self.currentSelection is None:
            return

        currentFile = str(self.currentFile)
        if self.currentFile.suffix == '.psyexp':
            generateScript(experimentPath=currentFile.replace('.psyexp', '_lastrun.py'),
                           exp=self.loadExperiment())
        procStarted = self.runFile(
            fileName=currentFile,
            focusOnExit=focusOnExit)

        # Enable/Disable btns
        if procStarted:
            self.runBtn.Disable()
            self.stopBtn.Enable()

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

        # we only want one server process open
        if self.serverProcess is not None:
            self.serverProcess.kill()
            self.serverProcess = None

        # Get PsychoJS libs
        self.getPsychoJS()

        htmlPath = str(self.currentFile.parent / self.outputPath)
        pythonExec = Path(sys.executable)
        command = [str(pythonExec), "-m", "http.server", str(port)]

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

        if filePaths:  # set selection to the final item to be added
            # Set item selection
            # de-select previous
            self.expCtrl.SetItemState(self.currentSelection or 0, 0, wx.LIST_STATE_SELECTED)
            # select new
            self.expCtrl.Select(thisIndex)  # calls onSelectItem which updates other info

        # Set column width
        self.expCtrl.SetColumnWidth(filenameColumn, wx.LIST_AUTOSIZE)
        self.expCtrl.SetColumnWidth(folderColumn, wx.LIST_AUTOSIZE)

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

    def onItemSelected(self, evt):
        """Set currentSelection to index of currently selected list item."""
        self.currentSelection = evt.Index
        filename = self.expCtrl.GetItemText(self.currentSelection, filenameColumn)
        folder = self.expCtrl.GetItemText(self.currentSelection, folderColumn)
        self.currentFile = Path(folder, filename)
        self.currentExperiment = self.loadExperiment()
        self.currentProject = None  # until it's needed (slow to update)
        # thisItem = self.entries[self.currentFile]

        if not self.running:  # if we aren't already running we can enable run button
            self.runBtn.Enable()
        if self.currentFile.suffix == '.psyexp':
            self.onlineBtn.Enable()
            self.onlineDebugBtn.Enable()
        else:
            self.onlineBtn.Disable()
            self.onlineDebugBtn.Disable()
        self.updateAlerts()
        self.app.updateWindowMenu()

    def onItemDeselected(self, evt):
        """Set currentSelection, currentFile, currentExperiment and currentProject to None."""
        self.expCtrl.SetItemState(self.currentSelection, 0, wx.LIST_STATE_SELECTED)
        self.currentSelection = None
        self.currentFile = None
        self.currentExperiment = None
        self.currentProject = None
        self.runBtn.Disable()
        self.onlineBtn.Disable()
        self.onlineDebugBtn.Disable()
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
        self.alertsToggleBtn.SetLabelText("   " + _translate("Alerts ({})").format(nAlerts))
        sys.stdout.flush()
        sys.stdout = sys.stderr = prev
        if nAlerts == 0:
            self.setAlertsVisible(False)
        # elif selected hidden then don't touch
        elif not self._selectedHiddenAlerts:
            self.setAlertsVisible(True)

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


class StdOutText(StdOutRich, handlers.ThemeMixin):
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
