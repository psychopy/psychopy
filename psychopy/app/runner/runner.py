#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
from wx.lib import platebtn
import os
import sys
import time
import requests
import traceback
import webbrowser
from pathlib import Path
from subprocess import Popen, PIPE

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
                                          size=wx.DefaultSize,
                                          style=wx.DEFAULT_FRAME_STYLE,
                                          name=title,
                                          )

        self.app = app
        self.frameType = 'runner'
        self.app.trackFrame(self)

        self.panel = RunnerPanel(self, id, title, app)

        # Create menu
        self.runnerMenu = wx.MenuBar()
        self.makeMenu()
        self.SetMenuBar(self.runnerMenu)

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.panel, 1, wx.EXPAND | wx.ALL)
        self.SetSizerAndFit(self.mainSizer)
        self.appData = self.app.prefs.appData['runner']
        self.loadTaskList()

        self.Bind(wx.EVT_CLOSE, self.onClose)

    def addTask(self, evt=None, fileName=None):
        self.panel.addTask(fileName=fileName)

    def removeTask(self, evt=None):
        self.panel.removeTask(evt)

    @property
    def stdOut(self):
        return self.panel.stdoutCtrl

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

        self.runnerMenu.Append(fileMenu, 'File')
        self.runnerMenu.Append(viewMenu, 'View')
        self.runnerMenu.Append(runMenu, 'Run')

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
        self.panel.expCtrl.DeleteAllItems()
        self.panel.currentSelection = None
        self.panel.currentProject = None
        self.panel.currentFile = None

    def onClose(self, event=None):
        """Define Frame closing behavior."""
        allFrames = self.app.getAllFrames()
        lastFrame = len(allFrames) == 1

        if lastFrame:
            self.onQuit()
        else:
            self.Hide()

    def onQuit(self, evt=None):
        sys.stderr = sys.stdout = sys.__stdout__
        self.panel.stopTask()
        self.app.quit(evt)

    def checkSave(self):
        try:
            self.saveTaskList()
        except Exception as e:
            print("##### Task List not saved correctly. #####\n")
            print(e)
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


class RunnerPanel(wx.Panel, ScriptProcess):
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

        expCtrlSize = [500, 150]
        ctrlSize = [500, 150]

        self.app = app
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
                                   style=wx.LC_REPORT | wx.BORDER_SUNKEN)

        self.expCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED,
                          self.onItemSelected, self.expCtrl)
        self.expCtrl.Bind(wx.EVT_LIST_ITEM_DESELECTED,
                          self.onItemDeselected, self.expCtrl)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onDoubleClick, self.expCtrl)
        self.expCtrl.InsertColumn(0, 'File')
        self.expCtrl.InsertColumn(1, 'Path')

        _style = platebtn.PB_STYLE_DROPARROW
        # Alerts
        self._selectedHiddenAlerts = False  # has user manually hidden alerts?
        self.alertsToggleBtn = platebtn.PlateButton(self, -1, 'Alerts',
                                          style=_style, name='Alerts')
        # mouse event must be bound like this
        self.alertsToggleBtn.Bind(wx.EVT_LEFT_DOWN, self.setAlertsVisible)
        # mouse event must be bound like this
        self.alertsToggleBtn.Bind(wx.EVT_RIGHT_DOWN, self.setAlertsVisible)
        self.alertsCtrl = StdOutText(parent=self,
                                     size=ctrlSize,
                                     style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.setAlertsVisible(True)

        # StdOut
        self.stdoutToggleBtn = platebtn.PlateButton(self, -1, 'Stdout',
                                          style=_style, name='Stdout')
        # mouse event must be bound like this
        self.stdoutToggleBtn.Bind(wx.EVT_LEFT_DOWN, self.setStdoutVisible)
        # mouse event must be bound like this
        self.stdoutToggleBtn.Bind(wx.EVT_RIGHT_DOWN, self.setStdoutVisible)
        self.stdoutCtrl = StdOutText(parent=self,
                                     size=ctrlSize,
                                     style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.setStdoutVisible(True)

        # Set buttons
        plusBtn = self.makeBmpButton(main='addExp32.png')
        negBtn = self.makeBmpButton(main='removeExp32.png')
        self.runBtn = runLocalBtn = self.makeBmpButton(main='run32.png')
        self.stopBtn = stopTaskBtn = self.makeBmpButton(main='stop32.png')
        self.onlineBtn = self.makeBmpButton(main='globe32.png', emblem='run16.png')
        self.onlineDebugBtn = self.makeBmpButton(main='globe32.png',
                                            emblem='bug16.png')

        plusBtn.SetToolTip(wx.ToolTip(
            _translate("Add experiment to list")))
        negBtn.SetToolTip(wx.ToolTip(
            _translate("Remove experiment from list")))
        runLocalBtn.SetToolTip(wx.ToolTip(
            _translate("Run the current script in Python")))
        stopTaskBtn.SetToolTip(wx.ToolTip(
            _translate("Stop Task")))
        self.onlineBtn.SetToolTip(wx.ToolTip(
            _translate("Run PsychoJS task from Pavlovia")))
        self.onlineDebugBtn.SetToolTip(wx.ToolTip(
            _translate("Run PsychoJS task in local debug mode")))

        # Bind events to buttons
        self.Bind(wx.EVT_BUTTON, self.addTask, plusBtn)
        self.Bind(wx.EVT_BUTTON, self.removeTask, negBtn)
        self.Bind(wx.EVT_BUTTON, self.runLocal, runLocalBtn)
        self.Bind(wx.EVT_BUTTON, self.stopTask, stopTaskBtn)
        self.Bind(wx.EVT_BUTTON, self.runOnline, self.onlineBtn)
        self.Bind(wx.EVT_BUTTON, self.runOnlineDebug, self.onlineDebugBtn)

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
                                   (self.onlineBtn, 0, wx.ALL, 5),
                                   (self.onlineDebugBtn, 0, wx.ALL, 5),
                                   ])

        # Set main sizer
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.upperSizer, 0, wx.EXPAND | wx.ALL, 10)

        self.mainSizer.Add(self.alertsToggleBtn, 0, wx.TOP, 10)
        self.mainSizer.Add(self.alertsCtrl, 1, wx.EXPAND | wx.ALL, 10)
        self.mainSizer.Add(self.stdoutToggleBtn, 0, wx.TOP, 10)
        self.mainSizer.Add(self.stdoutCtrl, 1, wx.EXPAND | wx.ALL, 10)

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

        if self.currentProject not in [None, "None", '']:
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
            filePaths = [fileName]
        else:
            with wx.FileDialog(self, "Open task...", wildcard="*.py; *.psyexp | *.py; *.psyexp",
                               style=wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST) as fileDialog:

                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return  # the user changed their mind

                filePaths = fileDialog.GetPaths()

        for file in filePaths:
            temp = Path(file)

            # Check list for item
            index = self.expCtrl.FindItem(-1, temp.name)
            if index > -1:
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
        self.alertsToggleBtn.SetLabelText("Alerts ({})".format(nAlerts))
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
