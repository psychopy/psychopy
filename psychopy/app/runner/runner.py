import wx
from ._runnerDlgs import RunnerPanel
import webbrowser
from psychopy.alerts._alerts import AlertEntry


class RunnerFrame(wx.Frame):
    """Defines construction of the Psychopy Runner Frame"""
    def __init__(self, parent=None, id=wx.ID_ANY, title='', app=None):
        super(RunnerFrame, self).__init__(parent=parent,
                                          id=id,
                                          title=title,
                                          pos=wx.DefaultPosition,
                                          size=wx.DefaultSize,
                                          style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP,
                                          name=title,
                                          )
        self.app = app
        self.panel = RunnerPanel(self, id, title, app)

        self.Bind(wx.EVT_CLOSE, self.onClose)

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.panel, 1, wx.EXPAND | wx.ALL)
        self.SetSizerAndFit(self.mainSizer)

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
                webbrowser.open(evt.String)
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
