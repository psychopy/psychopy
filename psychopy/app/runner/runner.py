#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
import os
import sys
import time
import requests
import traceback
import webbrowser
from pathlib import Path
from subprocess import Popen, PIPE
import wx.lib.agw.aui as aui

from psychopy.app import icons
from psychopy import experiment
from psychopy.constants import PY3
from psychopy.localization import _translate
from psychopy.app.stdOutRich import StdOutRich
from psychopy.projects.pavlovia import getProject
from psychopy.scripts.psyexpCompile import generateScript
from psychopy.app.runner.scriptProcess import ScriptProcess


class RunnerFrame(wx.Frame):
    """Construct the Psychopy Runner Frame."""

    def __init__(self, parent=None, id=wx.ID_ANY, title='', app=None):
        super(RunnerFrame, self).__init__(parent=parent,
                                          id=id,
                                          title=title,
                                          pos=wx.DefaultPosition,
                                          size=[800, 600],
                                          style=wx.DEFAULT_FRAME_STYLE,
                                          name=title,
                                          )

        # Create menu
        self.runnerMenu = wx.MenuBar()
        self.makeMenu()
        self.SetMenuBar(self.runnerMenu)

        self.app = app
        self.frameType = 'runner'
        self.app.trackFrame(self)

        self.ctrlPanel = RunnerPanel(self, id, title, app)
        self.stdoutPanel = StdoutPanel(self, id, title, app)
        self.appData = self.app.prefs.appData['runner']
        self.loadTaskList()

        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.CreateStatusBar()

        self._mgr = aui.AuiManager()

        # notify AUI which frame to use
        self._mgr.SetManagedWindow(self)

        # add the panes to the manager
        self._mgr.AddPane(self.ctrlPanel, aui.AuiPaneInfo()
                          .Direction(aui.AUI_DOCK_CENTER)
                          .CloseButton(visible=False)
                          .MinSize((400,300)))
        self._mgr.AddPane(self.stdoutPanel, aui.AuiPaneInfo()
                          .Direction(aui.AUI_DOCK_CENTER)
                          .CloseButton(visible=False)
                          .MinSize((400, 200)))

        # tell the manager to "commit" all the changes just made
        self._mgr.Update()
        self.SetMinSize((300,600))

    def addTask(self, evt=None, fileName=None):
        self.ctrlPanel.addTask(fileName=fileName)

    def removeTask(self, evt=None):
        self.ctrlPanel.removeTask(evt)

    @property
    def stdOut(self):
        return self.stdoutPanel.stdoutCtrl

    def makeMenu(self):
        """Create Runner menubar."""
        # Menus
        fileMenu = wx.Menu()
        viewMenu = wx.Menu()

        # Menu items
        fileMenuItems = [
            {'id': wx.ID_ADD, 'label': 'Add task', 'status': 'Adding task...', 'func': self.addTask},
            {'id': wx.ID_REMOVE, 'label': 'Remove task', 'status': 'Removing task...', 'func': self.removeTask},
            {'id': wx.ID_CLEAR, 'label': 'Clear all', 'status': 'Clearing tasks...', 'func': self.clearTasks},
            {'id': wx.ID_SAVE, 'label': 'Save list', 'status': 'Saving task...', 'func': self.saveTaskList},
            {'id': wx.ID_COPY, 'label': 'Load list', 'status': 'Loading task...', 'func': self.loadTaskList},
            {'id': wx.ID_CLOSE_FRAME, 'label': 'Close', 'status': 'Closing Runner...', 'func': self.onClose},
            {'id': wx.ID_EXIT, 'label': 'Quit', 'status': 'Quitting PsychoPy...', 'func': self.onQuit},
        ]

        viewMenuItems = [
            {'id': wx.ID_ANY, 'label': 'View Builder', 'status': 'Opening Builder...', 'func': self.viewBuilder},
            {'id': wx.ID_ANY, 'label': 'View Coder', 'status': 'Opening Coder...', 'func': self.viewCoder},
        ]

        menus = [
            {'menu': fileMenu, 'menuItems': fileMenuItems, 'separators': ['clear all', 'load list']},
            {'menu': viewMenu, 'menuItems': viewMenuItems, 'separators': []},
        ]

        # Add items to menus
        for eachMenu in menus:
            for item in eachMenu['menuItems']:
                fileItem = eachMenu['menu'].Append(item['id'], item['label'], item['status'])
                self.Bind(wx.EVT_MENU, item['func'], fileItem)
                if item['label'].lower() in eachMenu['separators']:
                    eachMenu['menu'].AppendSeparator()

        self.runnerMenu.Append(fileMenu, 'File')
        self.runnerMenu.Append(viewMenu, 'View')

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
        except Exception:
            print("##### Could not open URL: {} #####\n".format(evt.String))
        wx.EndBusyCursor()

    def saveTaskList(self, evt=None):
        """Save task list to appData."""
        self.appData['taskList'] = self.taskList
        self.app.prefs.saveAppData()

    def loadTaskList(self, evt=None):
        """Load saved task list from appData."""
        for filePath in self.appData['taskList']:
            if os.path.exists(filePath):
                self.addTask(fileName=filePath)

    def clearTasks(self, evt=None):
        """Clear all items from the panels expCtrl ListCtrl."""
        self.ctrlPanel.expCtrl.DeleteAllItems()
        self.ctrlPanel.currentSelection = None
        self.ctrlPanel.currentProject = None
        self.ctrlPanel.currentFile = None

    def onClose(self, event=None):
        """Define Frame closing behavior."""
        allFrames = self.app.getAllFrames()
        lastFrame = len(allFrames) == 1

        if lastFrame:
            self.onQuit()
        else:
            self.Hide()

    def onQuit(self, evt=None):
        self.ctrlPanel.stopTask()
        self.app.quit(evt)

    def checkSave(self):
        try:
            self.saveTaskList()
        except Exception:
            print("##### Task List not saved correctly. #####\n")
        return True

    def viewBuilder(self, evt):
        if self.ctrlPanel.currentFile is None:
            self.app.showBuilder()
            return

        for frame in self.app.getAllFrames("builder"):
            if frame.filename == 'untitled.psyexp' and frame.lastSavedCopy is None:
                frame.fileOpen(filename=str(self.ctrlPanel.currentFile))
                return

        self.app.showBuilder(fileList=[str(self.ctrlPanel.currentFile)])

    def viewCoder(self, evt):
        if self.ctrlPanel.currentFile is None:
            self.app.showCoder()
            return

        self.app.showCoder()  # ensures that a coder window exists
        self.app.coder.setCurrentDoc(str(self.ctrlPanel.currentFile))
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
        for idx in range(self.ctrlPanel.expCtrl.GetItemCount()):
            temp.append(self.ctrlPanel.expCtrl.GetItem(idx, 1).Text)
        return temp


class StdoutPanel(wx.Panel):
    def __init__(self, parent=None, id=wx.ID_ANY, title='', app=None):
        super(StdoutPanel, self).__init__(parent=parent,
                                           id=id,
                                           pos=wx.DefaultPosition,
                                           size=wx.DefaultSize,
                                           style=wx.DEFAULT_FRAME_STYLE,
                                           name=title,
                                          )

        ctrlSize = [500, 200]
        self.stdoutCtrl = StdOutText(parent=self,
                                     size=ctrlSize,
                                     style=wx.TE_READONLY | wx.TE_MULTILINE)

        # Set main sizer
        self.parent = parent
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.stdoutCtrl, 1, wx.EXPAND | wx.ALL, 10)

        self.SetSizerAndFit(self.mainSizer)
        self.SetMinSize(self.Size)

    def onURL(self, val):
        self.parent.onURL(val)

class RunnerPanel(wx.Panel, ScriptProcess):
    def __init__(self, parent=None, id=wx.ID_ANY, title='', app=None):
        super(RunnerPanel, self).__init__(parent=parent,
                                          id=id,
                                          pos=wx.DefaultPosition,
                                          size=wx.DefaultSize,
                                          style=wx.DEFAULT_FRAME_STYLE,
                                          name=title,
                                          )
        ScriptProcess.__init__(self, app)
        self.Bind(wx.EVT_END_PROCESS, self.onProcessEnded)

        expCtrlSize = [500, 150]

        self.app = app
        self.parent = parent
        self.serverProcess = None

        self.currentFile = None
        self.currentProject = None
        self.currentSelection = None
        self.currentExperiment = None

        # Set ListCtrl for list of tasks
        self.expCtrl = wx.ListCtrl(self,
                                   id=wx.ID_ANY,
                                   size=expCtrlSize,
                                   style=wx.LC_REPORT | wx.BORDER_SUNKEN)

        self.expCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED,
                          self.onItemSelected, self.expCtrl)
        self.expCtrl.Bind(wx.EVT_LIST_ITEM_DESELECTED,
                          self.onItemDeselected, self.expCtrl)
        self.expCtrl.InsertColumn(0, 'File')
        self.expCtrl.InsertColumn(1, 'Path')

        # Set buttons
        plusBtn = self.makeBmpButton(main='addExp32.png')
        negBtn = self.makeBmpButton(main='removeExp32.png')
        self.runBtn = runLocalBtn = self.makeBmpButton(main='run32.png')
        self.stopBtn = stopTaskBtn = self.makeBmpButton(main='stop32.png')
        onlineBtn = self.makeBmpButton(main='globe32.png', emblem='run16.png')
        onlineDebugBtn = self.makeBmpButton(main='globe32.png',
                                            emblem='bug16.png')

        plusBtn.SetToolTip(wx.ToolTip(
            _translate("Add experiment to list")))
        negBtn.SetToolTip(wx.ToolTip(
            _translate("Remove experiment from list")))
        runLocalBtn.SetToolTip(wx.ToolTip(
            _translate("Run PsychoPy task (Python)")))
        stopTaskBtn.SetToolTip(wx.ToolTip(
            _translate("Stop Task")))
        onlineBtn.SetToolTip(wx.ToolTip(
            _translate("Run PsychoJS task from Pavlovia")))
        onlineDebugBtn.SetToolTip(wx.ToolTip(
            _translate("Run PsychoJS task in local debug mode")))

        # Bind events to buttons
        self.Bind(wx.EVT_BUTTON, self.addTask, plusBtn)
        self.Bind(wx.EVT_BUTTON, self.removeTask, negBtn)
        self.Bind(wx.EVT_BUTTON, self.runLocal, runLocalBtn)
        self.Bind(wx.EVT_BUTTON, self.stopTask, stopTaskBtn)
        self.Bind(wx.EVT_BUTTON, self.runOnline, onlineBtn)
        self.Bind(wx.EVT_BUTTON, self.runOnlineDebug, onlineDebugBtn)

        # Box sizers
        self.upperSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.buttonSizer = wx.BoxSizer(wx.VERTICAL)

        self.upperSizer.Add(self.expCtrl, 1, wx.ALL | wx.EXPAND, 5)
        self.upperSizer.Add(self.buttonSizer, 0, wx.ALL | wx.EXPAND, 5)
        self.buttonSizer.Add(plusBtn, 0, wx.ALL | wx.ALIGN_TOP, 5)
        self.buttonSizer.Add(negBtn, 0, wx.ALL | wx.ALIGN_TOP, 5)
        self.buttonSizer.AddStretchSpacer()
        self.buttonSizer.AddMany([(runLocalBtn, 0, wx.ALL, 5),
                                   (stopTaskBtn, 0, wx.ALL, 5),
                                   (onlineBtn, 0, wx.ALL, 5),
                                   (onlineDebugBtn, 0, wx.ALL, 5),
                                   ])

        # Set main sizer
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.upperSizer, 1, wx.EXPAND | wx.ALL, 10)

        self.stopBtn.Disable()

        self.SetSizerAndFit(self.mainSizer)
        self.SetMinSize(self.Size)

    def onProcessEnded(self):
        ScriptProcess.onProcessEnded(self)
        self.stopTask()

    def makeBmpButton(self, main=None, emblem=None):
        """
        Produce buttons for the Runner.

        Parameters
        ----------
        main: str
            Name of main icon from Resources
        emblem: str
            Name of emblem icon from Resources
        Returns
        -------
        wx.BitmapButton
        """
        buttonSize = 32
        rc = self.app.prefs.paths['resources']
        join = os.path.join
        PNG = wx.BITMAP_TYPE_PNG

        if main and emblem:
            bmp = icons.combineImageEmblem(
                main=join(rc, main),
                emblem=join(rc, emblem), pos='bottom_right')
        else:
            bmp = wx.Bitmap(join(rc, main), PNG)
        return wx.BitmapButton(self, -1, bmp, size=[buttonSize, buttonSize], style=wx.NO_BORDER )

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
                           exp=self.currentExperiment)
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
        if self.currentSelection is None or self.currentFile.suffix == '.py':
            return

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

        if self.currentProject not in [None, "None", ''] and self.currentFile.suffix == '.psyexp':
            if self.serverProcess is None:
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
            filePath = [fileName]
        else:
            with wx.FileDialog(self, "Open task...", wildcard="*.py; *.psyexp | *.py; *.psyexp",
                               style=wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST) as fileDialog:

                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return  # the user changed their mind

                filePath = fileDialog.GetPaths()

        for file in filePath:
            temp = Path(file)

            # Check list for item
            if self.expCtrl.FindItem(-1, temp.name) > -1:
                continue

            # Set new item in listCtrl
            index = self.expCtrl.InsertItem(self.expCtrl.GetItemCount(), str(temp.name))
            self.expCtrl.SetItem(index, 1, str(temp))

            # Set item selection
            self.expCtrl.SetItemState(self.currentSelection or 0, 0, wx.LIST_STATE_SELECTED)
            self.expCtrl.Select(self.expCtrl.GetItemCount() - 1)

        # Set column width
        self.expCtrl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.expCtrl.SetColumnWidth(1, wx.LIST_AUTOSIZE)

    def removeTask(self, evt):
        """Remove experiment entry from the expList listctrl."""
        if self.currentSelection is None:
            return

        self.expCtrl.DeleteItem(self.currentSelection)
        if self.expCtrl.GetItemCount() == 0:
            self.currentSelection = None
            self.currentFile = None
            self.currentExperiment = None
            self.currentProject = None

    def onItemSelected(self, evt):
        """Set currentSelection to index of currently selected list item."""
        self.currentSelection = evt.Index
        self.currentFile = Path(self.expCtrl.GetItem(self.currentSelection, 1).Text)
        self.currentExperiment = self.experiment()
        self.currentProject = None

        # Check for project
        try:
            project = getProject(str(self.currentFile))
            if hasattr(project, 'id'):
                self.currentProject = project.id
        except NotADirectoryError as err:
            self.stdoutCtrl.write(err)

    def onItemDeselected(self, evt):
        """Set currentSelection, currentFile, currentExperiment and currentProject to None."""
        self.expCtrl.SetItemState(self.currentSelection, 0, wx.LIST_STATE_SELECTED)
        self.currentSelection = None
        self.currentFile = None
        self.currentExperiment = None
        self.currentProject = None

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

    def experiment(self):
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


class StdOutText(StdOutRich):
    """StdOutRich subclass which also handles Git messages from Pavlovia projects."""

    def __init__(self, parent=None, style=wx.TE_READONLY | wx.TE_MULTILINE, size=wx.DefaultSize):
        StdOutRich.__init__(self, parent=parent, style=style, size=size)

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


