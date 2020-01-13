import wx
import os
import sys
import time
from pathlib import Path
import webbrowser
import xml.etree.ElementTree as xml
from subprocess import Popen, PIPE

from psychopy.app import icons
from psychopy.app.stdOutRich import StdOutRich
from psychopy.app.builder.builder import BuilderFrame, OutputThread
from psychopy.app.coder.coder import CoderFrame
from psychopy.projects.pavlovia import getProject


# todo: Make app stay alive if builder/coder closed and runner still open,
# todo: If Builder closed, show Runner
# todo: Use subprocess or server, and run files from app prefs dir, with psychojs files present


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
        self.panel = RunnerPanel(self, id, title, app)

        self.Bind(wx.EVT_CLOSE, self.onClose)

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.panel, 1, wx.EXPAND | wx.ALL)
        self.SetSizerAndFit(self.mainSizer)

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
        self.Hide()


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

        # Set ListCtrl for list of tasks
        self.expCtrl = wx.ListCtrl(self,
                                   id=wx.ID_ANY,
                                   size=expCtrlSize,
                                   style=wx.LC_REPORT | wx.BORDER_SUNKEN)

        # Set stdout
        self.stdoutCtrl = StdOutText(parent=self, style=wx.TE_READONLY | wx.TE_MULTILINE, size=ctrlSize)

        self.expCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected, self.expCtrl)
        self.expCtrl.InsertColumn(0, 'File')
        self.expCtrl.InsertColumn(1, 'Type')
        self.expCtrl.InsertColumn(2, 'Path')
        self.expCtrl.InsertColumn(3, 'Project')

        self.expCtrl.SetColumnWidth(1, 75)
        self.currentSelection = None
        self.serverThread = None

        # Set buttons
        plusBtn = self.makeBmpButton(main='addExp')
        negBtn = self.makeBmpButton(main='removeExp')
        runLocalBtn = self.makeBmpButton(main='run')
        stopLocalBtn = self.makeBmpButton(main='stop')
        onlineBtn = self.makeBmpButton(main='globe', emblem='run16.png')
        onlineDebugBtn = self.makeBmpButton(main='globe', emblem='bug16.png')

        # Bind events to buttons
        self.Bind(wx.EVT_BUTTON, self.addExperiment, plusBtn)
        self.Bind(wx.EVT_BUTTON, self.removeExperiment, negBtn)
        self.Bind(wx.EVT_BUTTON, self.runLocal, runLocalBtn)
        self.Bind(wx.EVT_BUTTON, self.stopLocal, stopLocalBtn)
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
        self.expBtnSizer.Add(stopLocalBtn, (3, 5), (1, 1), wx.ALL | wx.EXPAND, 5)
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
        """Produces buttons for the Runner"""

        if sys.platform == 'win32' or sys.platform.startswith('linux'):
            if self.app.prefs.app['largeIcons']:
                buttonSize = 32
            else:
                buttonSize = 16
        else:
            buttonSize = 32  # mac: 16 either doesn't work, or looks bad

        rc = self.app.prefs.paths['resources']
        join = os.path.join
        PNG = wx.BITMAP_TYPE_PNG

        if main and emblem:
            bmp = icons.combineImageEmblem(
                main=join(rc, '{}{}.png'.format(main, buttonSize)),
                emblem=join(rc, emblem), pos='bottom_right')
        else:
            bmp = wx.Bitmap(join(rc, '{}{}.png'.format(main, buttonSize)), PNG)
        return wx.BitmapButton(self, -1, bmp, size=[buttonSize, buttonSize], style=wx.NO_BORDER )

    def stopLocal(self, evt):
        """
        Kills script processes.
        """
        if self.localProcess:
            print("Experiment quit")
            self.localProcess.stopFile(evt)
        self.localProcess = None

        if self.serverThread:
            self.serverThread.terminate()
            poll = self.serverThread.poll()
            if poll is not None:
                print("Local server ended.")
                self.Bind(wx.EVT_IDLE, None)
                self.serverThread = None

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

    def runOnlineDebug(self, evt, port=7800):

        if self.currentSelection is None:
            return

        currentFile = self.expCtrl.GetItem(self.currentSelection, 2).Text
        currentProj = self.expCtrl.GetItem(self.currentSelection, 3).Text

        if currentProj not in [None, "None", ''] and Path(currentFile).suffix == '.psyexp':
            if self.serverThread is None:


                self.serverThread = Popen(["python", "-m" ,"http.server", "7800"],
                                          cwd=Path(currentFile).parent,
                                          stdout=PIPE, stderr=PIPE,
                                          universal_newlines=True, shell=False)
                self._stdOut = OutputThread(self.serverThread)
                self._stdOut.start()
                self.Bind(wx.EVT_IDLE, self.whileRunning)
                print("Local server started!\n")

            webbrowser.open("http://localhost:{}".format(port))

    def whileRunning(self, evt):
        """This is an Idle function while study is running. Checks on process
                and handle stdout"""
        newOutput = self._stdOut.getBuffer()

        if newOutput:
            self.stdoutCtrl.write(newOutput)
        time.sleep(0.1)  # let's not check too often

    def onURL(self, evt):
        self.parent.onURL(evt)

    def addExperiment(self, evt=None, fileName=None):

        if fileName:
            filePath = [fileName]
        else:
            with wx.FileDialog(self, "Open task...", wildcard="*.py; *.psyexp | *.py; *.psyexp",
                               style=wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST) as fileDialog:

                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return  # the user changed their mind

                filePath = fileDialog.GetPaths()

        for file in filePath:
            temp = Path(file)

            if self.listContains(temp.name) > -1:
                continue

            # Check for project
            project = getProject(str(temp))
            if hasattr(project, 'id'):
                project = project.id

            index = self.expCtrl.InsertItem(self.expCtrl.GetItemCount(), str(temp.name))
            self.expCtrl.SetItem(index, 1, str(temp.suffix))
            self.expCtrl.SetItem(index, 2, str(temp))
            self.expCtrl.SetItem(index, 3, str(project))

        self.expCtrl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.expCtrl.SetColumnWidth(2, wx.LIST_AUTOSIZE)
        self.expCtrl.SetColumnWidth(3, wx.LIST_AUTOSIZE)

        # Set item selection
        self.expCtrl.SetItemState(self.currentSelection or 0, 0, wx.LIST_STATE_SELECTED)
        self.expCtrl.Select(self.expCtrl.GetItemCount() - 1)

    def removeExperiment(self, evt):
        self.expCtrl.DeleteItem(self.currentSelection)
        if self.expCtrl.GetItemCount() == 0:
            self.currentSelection = None

    def onItemSelected(self, evt):
        self.currentSelection = evt.Index

    def listContains(self, fileName):
        """
        Checks listctrl for existing items.

        Parameters
        ----------
        fileName : str
            The filename of the experiment

        Returns
        -------
        int :
            -1 if item does not exist, else returns item list index

        """
        return self.expCtrl.FindItem(-1, fileName)

    def outputPath(self, fileName):
        doc = xml.ElementTree()
        doc.parse(fileName)
        settings = doc.getroot().find('Settings')
        for param in settings:
            if param.attrib['name'] == "HTML path":
                return param.attrib['val']


class StdOutText(StdOutRich):
    def __init__(self, parent=None, style=wx.TE_READONLY | wx.TE_MULTILINE, size=wx.DefaultSize):
        StdOutRich.__init__(self, parent=parent, style=style, size=size)

    def getText(self):
        """Return the text of the current buffer
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





