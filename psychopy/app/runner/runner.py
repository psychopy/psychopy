import wx
import os
import sys
import time
from pathlib import Path
import requests
import webbrowser
import xml.etree.ElementTree as xml
from subprocess import Popen, PIPE

from psychopy.app import icons
from psychopy.constants import PY3
from psychopy.app.stdOutRich import StdOutRich
from psychopy.app.coder.coder import CoderFrame
from psychopy.app.builder.builder import BuilderFrame
from psychopy.projects.pavlovia import getProject


class RunnerFrame(wx.Frame):
    """Defines construction of the Psychopy Runner Frame"""
    def __init__(self, parent=None, id=wx.ID_ANY, title='', app=None):
        super(RunnerFrame, self).__init__(parent=parent,
                                          id=id,
                                          title=title,
                                          pos=wx.DefaultPosition,
                                          size=wx.DefaultSize,
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

        self.panel = RunnerPanel(self, id, title, app)

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.panel, 1, wx.EXPAND | wx.ALL)
        self.SetSizerAndFit(self.mainSizer)
        self.prefs = self.app.prefs.runner
        self.loadTasks()

        self.Bind(wx.EVT_CLOSE, self.onClose)

    def addTask(self, evt=None, fileName=None):
        self.panel.addExperiment(fileName=fileName)

    def removeTask(self, evt=None):
        self.panel.removeTask(evt)

    @property
    def stdOut(self):
        return self.panel.stdoutCtrl

    def makeMenu(self):
        """
        Create Runner menu.
        """
        # Menus
        fileMenu = wx.Menu()
        viewMenu = wx.Menu()

        # Menu items
        fileMenuItems = [
            {'id': wx.ID_ADD, 'label': 'Add task', 'status': 'Adding task...', 'func': self.addTask},
            {'id': wx.ID_REMOVE, 'label': 'Remove task', 'status': 'Removing task...', 'func': self.removeTask},
            {'id': wx.ID_CLEAR, 'label': 'Clear all', 'status': 'Clearing tasks...', 'func': self.clearTasks},
            {'id': wx.ID_SAVE, 'label': 'Save task', 'status': 'Saving task...', 'func': self.saveTasks},
            {'id': wx.ID_COPY, 'label': 'Load task', 'status': 'Loading task...', 'func': self.loadTasks},
            {'id': wx.ID_CLOSE_FRAME, 'label': 'Close', 'status': 'Closing Runner...', 'func': self.onClose},
            {'id': wx.ID_EXIT, 'label': 'Quit', 'status': 'Quitting PsychoPy...', 'func': self.onQuit},
        ]

        viewMenuItems = [
            {'id': wx.ID_ANY, 'label': 'View Builder', 'status': 'Opening Builder...', 'func': self.viewBuilder},
            {'id': wx.ID_ANY, 'label': 'View Coder', 'status': 'Opening Coder...', 'func': self.viewCoder},
        ]

        menus = [
            {'menu': fileMenu, 'menuItems': fileMenuItems, 'separators': ['clear all', 'load task']},
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
        """
        Open link in default browser.
        """
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

    def saveTasks(self, evt=None):
        self.prefs['taskList'] = self.taskList
        self.app.prefs.saveUserPrefs()

    def loadTasks(self, evt=None):
        for filePath in self.prefs['taskList']:
            self.addTask(fileName=filePath)

    def clearTasks(self, evt=None):
        self.panel.expCtrl.DeleteAllItems()

    def onClose(self, evt):
        """
        Defines Frame closing behavior.
        Frame only gets destroyed if no other frames exist.
        """
        lastFrame = len(self.app.getAllFrames()) == 1
        if lastFrame:
            self.onQuit()
        else:
            self.Hide()

    def onQuit(self, evt=None):
        self.Destroy()  # required
        self.app.forgetFrame(self)
        self.app.quit(evt)

    def checkSave(self):
        try:
            self.saveTasks()
        except Exception:
            print("##### Task List not saved correctly. #####\n")
        return True

    def viewBuilder(self, evt):
        for frame in self.app.getAllFrames("builder"):
            if frame.filename == 'untitled.psyexp' and frame.lastSavedCopy is None:
                frame.fileOpen(filename=str(self.panel.currentFile))
                return
        self.app.showBuilder(fileList=[str(self.panel.currentFile)])

    def viewCoder(self, evt):
        self.app.showCoder()  # ensures that a coder window exists
        self.app.coder.setCurrentDoc(str(self.panel.currentFile))
        self.app.coder.setFileModified(False)

    def showRunner(self):
        self.app.showRunner()

    @property
    def taskList(self):
        temp = []
        for idx in range(self.panel.expCtrl.GetItemCount()):
            temp.append(self.panel.expCtrl.GetItem(idx, 1).Text)
        return temp


class RunnerPanel(wx.Panel):
    def __init__(self, parent=None, id=wx.ID_ANY, title='', app=None):
        super(RunnerPanel, self).__init__(parent=parent,
                                          id=id,
                                          pos=wx.DefaultPosition,
                                          size=[400,700],
                                          style=wx.DEFAULT_FRAME_STYLE,
                                          name=title,
                                          )

        expCtrlSize = [400, 150]
        ctrlSize = [400, 150]

        self.app = app
        self.parent = parent
        self.localProcess = None
        self.serverProcess = None

        self.currentFile = None
        self.currentProject = None
        self.currentSelection = None

        # Set ListCtrl for list of tasks
        self.expCtrl = wx.ListCtrl(self,
                                   id=wx.ID_ANY,
                                   size=expCtrlSize,
                                   style=wx.LC_REPORT | wx.BORDER_SUNKEN)

        # Set stdout
        self.stdoutCtrl = StdOutText(parent=self,
                                     size=ctrlSize,
                                     style=wx.TE_READONLY | wx.TE_MULTILINE)

        self.expCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected, self.expCtrl)
        self.expCtrl.InsertColumn(0, 'File')
        self.expCtrl.InsertColumn(1, 'Path')

        # Set buttons
        plusBtn = self.makeBmpButton(main='addExp32.png')
        negBtn = self.makeBmpButton(main='removeExp32.png')
        runLocalBtn = self.makeBmpButton(main='run32.png')
        self.stopBtn = stopTaskBtn = self.makeBmpButton(main='stop32.png')
        onlineBtn = self.makeBmpButton(main='globe32.png', emblem='run16.png')
        onlineDebugBtn = self.makeBmpButton(main='globe32.png', emblem='bug16.png')

        plusBtn.SetToolTip(wx.ToolTip("Add experiment to list"))
        negBtn.SetToolTip(wx.ToolTip("Remove experiment from list"))
        runLocalBtn.SetToolTip(wx.ToolTip("Run PsychoPy task (Python)"))
        stopTaskBtn.SetToolTip(wx.ToolTip("Stop Task"))
        onlineBtn.SetToolTip(wx.ToolTip("Run PsychoJS task from Pavlovia"))
        onlineDebugBtn.SetToolTip(wx.ToolTip("Run PsychoJS task in local debug mode"))

        # Bind events to buttons
        self.Bind(wx.EVT_BUTTON, self.addExperiment, plusBtn)
        self.Bind(wx.EVT_BUTTON, self.removeTask, negBtn)
        self.Bind(wx.EVT_BUTTON, self.runLocal, runLocalBtn)
        self.Bind(wx.EVT_BUTTON, self.stopTask, stopTaskBtn)
        self.Bind(wx.EVT_BUTTON, self.runOnline, onlineBtn)
        self.Bind(wx.EVT_BUTTON, self.runOnlineDebug, onlineDebugBtn)

        # GridBagSizer
        gridRow, gridCol = (4,2)
        self.expBtnSizer = wx.GridBagSizer(vgap=0, hgap=0)

        # Add ListCtrl
        self.expBtnSizer.Add(self.expCtrl, (0, 0), (gridRow, gridCol), wx.EXPAND)

        # Add buttons
        self.expBtnSizer.Add(plusBtn, (0,2), (1,1), wx.ALL, 5)
        self.expBtnSizer.Add(negBtn, (1,2), (1,1), wx.ALL, 5)
        self.expBtnSizer.Add(runLocalBtn, (3,2),(1,1), wx.ALL | wx.EXPAND, 5)
        self.expBtnSizer.Add(stopTaskBtn, (3, 3), (1, 1), wx.ALL | wx.EXPAND, 5)
        self.expBtnSizer.Add(onlineBtn, (3,4),(1,1), wx.ALL | wx.EXPAND, 5)
        self.expBtnSizer.Add(onlineDebugBtn, (3,5),(1,1), wx.ALL | wx.EXPAND, 5)

        for idx in range(gridRow):
            self.expBtnSizer.AddGrowableRow(idx)
            if idx < 2:
                self.expBtnSizer.AddGrowableCol(idx)

        # Set main sizer
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.expBtnSizer, 1, wx.EXPAND | wx.ALL, 10)
        self.mainSizer.Add(self.stdoutCtrl, 1, wx.EXPAND | wx.ALL, 10)

        self.SetSizerAndFit(self.mainSizer)
        self.SetMinSize(self.Size)

    def makeBmpButton(self, main=None, emblem=None):
        """
        Produces buttons for the Runner.

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

    def stopTask(self, evt):
        """
        Kills script processes currently running.
        """
        # Check whether script ended automatically
        if self.processExists and not (evt.EventObject.ClassName == 'wxBitmapButton'):
            return

        # Stop Runner script local process
        if self.localProcess is not None:
            self.Bind(wx.EVT_IDLE, None)
            try:
                self.localProcess.stopFile(evt)
            except TypeError:
                pass  # coder Process already dead
            self.localProcess = None
            print("##### Experiment finished. #####\n")

        # Stop subprocess script running local server
        if self.serverProcess is not None:
            self.serverProcess.kill()
            self.serverProcess = None
            print("##### Local server shut down. #####\n")

        # Stop Builder or Coder scripts
        for thisFrame in self.app.getAllFrames():
            if hasattr(thisFrame, 'scriptProcess') and thisFrame.scriptProcess is not None:
                thisFrame.stopFile()
                print("##### Experiment finished. #####\n")

    def runLocal(self, evt):
        """
        Run experiment from Builder - Builder can run both .py and .psyexp filetypes,
        if builderFrame.filename is set after frame creation.
        """
        if self.currentSelection is None or self.localProcess is not None:
            return

        if self.currentFile.suffix == '.psyexp':
            title = "PsychoPy3 Experiment Builder (v{})".format(self.app.version)
            self.localProcess = BuilderFrame(None, -1,
                                             title=title,
                                             fileName=str(self.currentFile),
                                             app=self.app)
        else:
            title = "PsychoPy3 Experiment Builder (v{})".format(self.app.version)
            self.localProcess = CoderFrame(None, -1,
                                           title=title,
                                           files=[str(self.currentFile)],
                                           app=self.app)
        self.localProcess.runFile()
        time.sleep(.5)  # Give processes a moment to start up
        self.Bind(wx.EVT_IDLE, self.stopTask)

    @property
    def processExists(self):
        if not hasattr(self.localProcess, 'scriptProcess'):
            return
        if self.localProcess.scriptProcess is not None:
            time.sleep(.1)
            return True

    def runOnline(self, evt):
        """
        Runs PsychoJS task from https://pavlovia.org
        """
        if self.currentSelection is None:
            return

        if self.currentProject not in [None, "None", ''] and self.currentFile.suffix == '.psyexp':
            webbrowser.open(
                "https://pavlovia.org/run/{}/{}"
                    .format(self.currentProject,
                            self.outputPath(
                                self.currentFile)))

    def runOnlineDebug(self, evt, port=12002):
        """
        Opens PsychoJS task on local server running from localhost, useful for debugging
        before pushing up to Pavlovia.

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

        outputPath = self.outputPath(self.currentFile)
        htmlPath = self.currentFile.parent / outputPath
        server = ["SimpleHTTPServer", "http.server"][PY3]
        pythonExec = Path(sys.executable)
        command = [str(pythonExec), "-m", server, str(port)]

        if not os.path.exists(htmlPath):
            print('##### HTML output path: "{}" does not exist. '
                  'Try exporting your HTML, and try again #####\n'.format(outputPath))
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
        libPath = self.currentFile.parent / 'lib'
        if not os.path.exists(libPath):
            os.makedirs(libPath)

        ver = '.'.join(self.app.version.split('.')[:2])
        psychoJSLibs = ['core', 'data', 'util', 'visual', 'sound']
        for lib in psychoJSLibs:
            url = "https://lib.pavlovia.org/{}-{}.js".format(lib, ver)
            req = requests.get(url)
            with open(libPath / "{}-{}.js".format(lib, ver), 'wb') as f:
                f.write(req.content)

        print("##### PsychoJS libs downloaded to {} #####\n".format(libPath))

    def addExperiment(self, evt=None, fileName=None):
        """
        Adds experiment entry to the expList listctrl.
        Only adds entry if current entry does not exist in list.
        Can be passed a filename to add to the list.

        Parameters
        ----------
        evt: wx.Event
        fileName: str
            Filename of task to add to list
        """
        if fileName:  # Filename passed from Builder
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
        """
        Removes experiment entry from the expList listctrl.
        """
        if self.currentSelection is None:
            return

        self.expCtrl.DeleteItem(self.currentSelection)
        if self.expCtrl.GetItemCount() == 0:
            self.currentSelection = None
            self.currentProject = None
            self.currentFile = None

    def onItemSelected(self, evt):
        """
        Sets currentSelection to index of currently selected list item.
        """
        self.currentSelection = evt.Index
        self.currentFile = Path(self.expCtrl.GetItem(self.currentSelection, 1).Text)
        self.currentProject = None

        # Check for project
        project = getProject(str(self.currentFile))
        if hasattr(project, 'id'):
            self.currentProject = project.id

    def outputPath(self, filePath):
        """
        Returns html output path saved in Experiment Settings.

        Parameters
        ----------
        filePath: str
            The file path of the currently selected list item

        Returns
        -------
        output path: str
            The output path, relative to parent folder.

        """
        doc = xml.ElementTree()
        doc.parse(filePath)
        settings = doc.getroot().find('Settings')
        for param in settings:
            if param.attrib['name'] == "HTML path":
                return param.attrib['val']


class StdOutText(StdOutRich):
    """
    StdOutRich which also handles Git messages from Pavlovia projects.
    """
    def __init__(self, parent=None, style=wx.TE_READONLY | wx.TE_MULTILINE, size=wx.DefaultSize):
        StdOutRich.__init__(self, parent=parent, style=style, size=size)

    def getText(self):
        """
        Return the text of the current buffer
        """
        return self.GetValue()

    def setStatus(self, status):
        self.SetValue(status)
        self.Refresh()
        self.Layout()
        wx.Yield()

    def statusAppend(self, newText):
        text = self.GetValue() + newText
        self.setStatus(text)





