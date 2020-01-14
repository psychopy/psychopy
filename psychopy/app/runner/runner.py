import wx
import os
import sys
import time
from pathlib import Path
import webbrowser
import xml.etree.ElementTree as xml
from subprocess import Popen, PIPE

from psychopy.app import icons
from psychopy.constants import PY3
from psychopy.app.stdOutRich import StdOutRich
from psychopy.app.builder.builder import BuilderFrame
from psychopy.app.coder.coder import CoderFrame
from psychopy.projects.pavlovia import getProject


# todo: Make print statements ALERTS
# todo: Set menu to allow app quit, view of Builder, Coder, and allow opening of listed tasks in those frames.

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
        self.app = app
        self.frameType = 'runner'
        self.app.trackFrame(self)
        self.panel = RunnerPanel(self, id, title, app)

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.panel, 1, wx.EXPAND | wx.ALL)
        self.SetSizerAndFit(self.mainSizer)

        self.Bind(wx.EVT_CLOSE, self.onClose)

    def addExperiment(self, fileName=None):
        self.panel.addExperiment(fileName=fileName)

    @property
    def stdOut(self):
        return self.panel.stdoutCtrl

    def onURL(self, evt):
        """
        Open link in default browser.
        """
        wx.BeginBusyCursor()
        try:
            if evt.String.startswith("http"):
                wx.LaunchDefaultBrowser(evt.String)
            else:
                # decompose the URL of a file and line number"""
                # "C:\Program Files\wxPython...\samples\hangman\hangman.py"
                filename = evt.GetString().split('"')[1]
                lineNumber = int(evt.GetString().split(',')[1][5:])
                self.app.showCoder()
                self.app.coder.gotoLine(filename, lineNumber)
        except Exception:
            print("Could not open URL: {}".format(evt.String))
        wx.EndBusyCursor()

    def onClose(self, evt):
        """
        Defines Frame closing behavior.
        Frame only closes if no other frames exist.
        """
        lastFrame = len(self.app.getAllFrames()) == 1
        if lastFrame:
            self.Destroy()  # required
            self.app.forgetFrame(self)
            self.app.quit(evt)


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
        self.taskList = {}
        self.localProcess = None
        self.serverProcess = None
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
        self.expCtrl.InsertColumn(1, 'Type')
        self.expCtrl.InsertColumn(2, 'Path')
        self.expCtrl.InsertColumn(3, 'Project')
        self.expCtrl.SetColumnWidth(1, 75)

        # Set buttons
        plusBtn = self.makeBmpButton(main='addExp32.png')
        negBtn = self.makeBmpButton(main='removeExp32.png')
        runLocalBtn = self.makeBmpButton(main='run32.png')
        stopTaskBtn = self.makeBmpButton(main='stop32.png')
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
        self.Bind(wx.EVT_BUTTON, self.removeExperiment, negBtn)
        self.Bind(wx.EVT_BUTTON, self.runLocal, runLocalBtn)
        self.Bind(wx.EVT_BUTTON, self.stopTask, stopTaskBtn)
        self.Bind(wx.EVT_BUTTON, self.runOnline, onlineBtn)
        self.Bind(wx.EVT_BUTTON, self.runOnlineDebug, onlineDebugBtn)

        # GridBagSizer
        gridSize = 4
        self.expBtnSizer = wx.GridBagSizer(vgap=0, hgap=0)

        # Add ListCtrl
        self.expBtnSizer.Add(self.expCtrl, (0, 0), (gridSize, gridSize), wx.EXPAND)

        # Add buttons
        self.expBtnSizer.Add(plusBtn, (0,4), (1,1), wx.ALL, 5)
        self.expBtnSizer.Add(negBtn, (1,4), (1,1), wx.ALL, 5)
        self.expBtnSizer.Add(runLocalBtn, (3,4),(1,1), wx.ALL | wx.EXPAND, 5)
        self.expBtnSizer.Add(stopTaskBtn, (3, 5), (1, 1), wx.ALL | wx.EXPAND, 5)
        self.expBtnSizer.Add(onlineBtn, (3,6),(1,1), wx.ALL | wx.EXPAND, 5)
        self.expBtnSizer.Add(onlineDebugBtn, (3,7),(1,1), wx.ALL | wx.EXPAND, 5)

        for idx in range(gridSize):
            self.expBtnSizer.AddGrowableRow(idx)
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
        # Local script
        if self.localProcess is not None:
            self.localProcess.stopFile(evt)
            self.localProcess = None
            print("***** Experiment quit. *****")

        # Subprocess script running local server
        if self.serverProcess is not None:
            self.serverProcess.kill()
            self.serverProcess = None
            print("***** Local server shut down. *****")

    def runLocal(self, evt):
        """
        Run experiment from Builder or Coder Frames, depending on file type.
        """
        if self.currentSelection is None:
            return

        fileType = self.expCtrl.GetItem(self.currentSelection, 1).Text
        fileName = self.expCtrl.GetItem(self.currentSelection, 2).Text

        if fileType == '.py':
            title = "PsychoPy3 Coder (IDE) (v{})".format(self.app.version)
            self.localProcess = CoderFrame(None, -1,
                                   title=title,
                                   files=[fileName], app=self.app)
        else:
            title = "PsychoPy3 Experiment Builder (v{})".format(self.app.version)
            self.localProcess = BuilderFrame(None, -1,
                                     title=title,
                                     fileName=fileName, app=self.app)
        self.localProcess.runFile()

    def runOnline(self, evt):
        """
        Runs PsychoJS task from https://pavlovia.org
        """
        if self.currentSelection is None:
            return

        currentFile = self.expCtrl.GetItem(self.currentSelection, 2).Text
        currentProj = self.expCtrl.GetItem(self.currentSelection, 3).Text

        if currentProj not in [None, "None", ''] and Path(currentFile).suffix == '.psyexp':
            webbrowser.open(
                "https://pavlovia.org/run/{}/{}"
                    .format(currentProj,
                            self.outputPath(
                                currentFile)))

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

        currentFile = self.expCtrl.GetItem(self.currentSelection, 2).Text
        currentProj = self.expCtrl.GetItem(self.currentSelection, 3).Text
        htmlPath = Path(currentFile).parent / self.outputPath(Path(currentFile))
        server = ["SimpleHTTPServer", "http.server"][PY3]
        pythonExec = Path(sys.executable)
        cmd = [pythonExec, "-m", server, str(port)]

        if currentProj not in [None, "None", ''] and Path(currentFile).suffix == '.psyexp':
            if self.serverProcess is None:
                self.serverProcess = Popen(cmd,
                                           bufsize=1,
                                           cwd=htmlPath,
                                           stdout=PIPE,
                                           stderr=PIPE,
                                           shell=False,
                                           universal_newlines=True,
                                           )

            time.sleep(.1)  # Wait for subprocess to start server
            webbrowser.open("http://localhost:{}".format(port))
            print("***** Local server started! *****")
            print("***** Running PsychoJS task from {} *****".format(htmlPath))

    def onURL(self, evt):
        self.parent.onURL(evt)

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
                print("You can only add Python files or psyexp files to the Runner.")
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

            # Check for project
            project = getProject(str(temp))
            if hasattr(project, 'id'):
                project = project.id

            # Set new item in listCtrl
            index = self.expCtrl.InsertItem(self.expCtrl.GetItemCount(), str(temp.name))
            self.expCtrl.SetItem(index, 1, str(temp.suffix))
            self.expCtrl.SetItem(index, 2, str(temp))
            self.expCtrl.SetItem(index, 3, str(project))

        # Set column width
        self.expCtrl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.expCtrl.SetColumnWidth(2, wx.LIST_AUTOSIZE)
        self.expCtrl.SetColumnWidth(3, wx.LIST_AUTOSIZE)

        # Set item selection
        self.expCtrl.SetItemState(self.currentSelection or 0, 0, wx.LIST_STATE_SELECTED)
        self.expCtrl.Select(self.expCtrl.GetItemCount() - 1)

    def removeExperiment(self, evt):
        """
        Removes experiment entry from the expList listctrl.
        """
        self.expCtrl.DeleteItem(self.currentSelection)
        if self.expCtrl.GetItemCount() == 0:
            self.currentSelection = None

    def onItemSelected(self, evt):
        """
        Sets currentSelection to index of currently selected list item.
        """
        self.currentSelection = evt.Index

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





