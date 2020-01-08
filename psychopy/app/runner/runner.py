import wx
import os
from pathlib import Path
import webbrowser
import xml.etree.ElementTree as xml
from psychopy.app.stdOutRich import StdOutRich
from psychopy.app.builder.builder import BuilderFrame
from psychopy.app.coder.coder import CoderFrame
from psychopy.projects.pavlovia import getProject

from threading import Thread
import time
import http.server
import socketserver

class TestThread(Thread):
    """Test Worker Thread Class."""

    # ----------------------------------------------------------------------
    def __init__(self, ref, path):
        """Init Worker Thread Class."""
        Thread.__init__(self)


        self.ref = ref
        self.start()  # start the thread
        # if path is not None:
        #     os.chdir(path)

    # ----------------------------------------------------------------------
    def run(self):
        """Run Worker Thread."""
        PORT = 7800
        handler = http.server.SimpleHTTPRequestHandler
        handler.extensions_map.update({'.js': 'text/javascript'})
        with socketserver.TCPServer(('', PORT), handler) as httpd:
            try:
                print("Serving at port: ", PORT)
                time.sleep(.5)
                httpd.serve_forever()
            except KeyboardInterrupt:
                httpd.server_close()
            except Exception as err:
                httpd.server_close()
                print(err)
            finally:
                httpd.server_close()
                self.ref.serverThread = None


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
        # Add and remove experiments
        btnFont = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
        plusBtn = wx.Button(self, -1, '+', size=[30, 30])
        negBtn = wx.Button(self, -1, '-', size=[30, 30])

        plusBtn.SetFont(btnFont)
        negBtn.SetFont(btnFont)

        # Run study buttons
        localBtn = wx.Button(self, -1, 'Local')
        onlineBtn = wx.Button(self, -1, 'Online')
        onlineDebugBtn = wx.Button(self, -1, 'Online Debug')

        # Bind events to buttons
        self.Bind(wx.EVT_BUTTON, self.addExperiment, plusBtn)
        self.Bind(wx.EVT_BUTTON, self.removeExperiment, negBtn)
        self.Bind(wx.EVT_BUTTON, self.runLocal, localBtn)
        self.Bind(wx.EVT_BUTTON, self.runOnlineDebug, onlineDebugBtn)
        self.Bind(wx.EVT_BUTTON, self.runOnline, onlineBtn)

        # Button sizers
        self.expBtnSizer = wx.BoxSizer(wx.VERTICAL)
        self.expBtnSizer.Add(plusBtn, 1)
        self.expBtnSizer.Add(negBtn, 1)

        self.runBtnSizer = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, "Run"), wx.HORIZONTAL)
        self.runBtnSizer.Add(localBtn, 1)
        self.runBtnSizer.Add(onlineBtn, 1)
        self.runBtnSizer.Add(onlineDebugBtn, 1)
        self.expBtnSizer.Add(self.runBtnSizer, 1)

        # ListCtrl sizer
        self.expListSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.expListSizer.Add(self.expCtrl, 1)
        self.expListSizer.Add(self.expBtnSizer, 1)

        # Set main sizer
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.expListSizer, 1, wx.ALL, 10)
        self.mainSizer.Add(self.stdoutCtrl, 1, wx.EXPAND | wx.ALL, 10)

        self.SetSizerAndFit(self.mainSizer)
        self.SetMinSize(self.Size)


    def runLocal(self, evt):
        """
        Run experiment from Builder or Coder Frames, depending on file type.
        """
        if self.currentSelection is not None:

            fileType = self.expCtrl.GetItem(self.currentSelection, 1).Text
            fileName = self.expCtrl.GetItem(self.currentSelection, 2).Text

            if fileType == '.py':
                title = "PsychoPy3 Coder (IDE) (v{})".format(self.app.version)
                thisFrame = CoderFrame(None, -1,
                                       title=title,
                                       files=[fileName], app=self.app)
            else:
                title = "PsychoPy3 Experiment Builder (v{})".format(self.app.version)
                thisFrame = BuilderFrame(None, -1,
                                         title=title,
                                         fileName=fileName, app=self.app)
            thisFrame.runFile()

    def canRunOnline(self, fileName):
        if not Path(fileName).suffix == '.psyexp':
            return False
        return True

    def runOnline(self, evt):
        currentProj = self.expCtrl.GetItem(self.currentSelection, 3).Text
        currentFile = self.expCtrl.GetItem(self.currentSelection, 2).Text

        if currentProj not in [None, "None", ''] and self.canRunOnline(currentFile):
            wx.LaunchDefaultBrowser(
                "https://pavlovia.org/run/{}/{}"
                    .format(currentProj,
                            self.outputPath(
                                currentFile)))

    def runOnlineDebug(self, evt, port=7800):
        currentProj = self.expCtrl.GetItem(self.currentSelection, 3).Text
        currentFile = self.expCtrl.GetItem(self.currentSelection, 2).Text

        if currentProj not in [None, "None", ''] and self.canRunOnline(currentFile):
            if self.serverThread is None:
                self.serverThread = TestThread(self, currentFile)
                time.sleep(.5)
                print(os.getcwd())
                print("Local server thread started!\n")

            webbrowser.open("http://localhost:{}".format(port))


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





