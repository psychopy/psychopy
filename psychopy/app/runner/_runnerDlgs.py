import wx
from psychopy.app.stdOutRich import StdOutRich


class RunnerPanel(wx.Panel, ):

    def __init__(self, parent=None, id=wx.ID_ANY, title='', app=None):
        super(RunnerPanel, self).__init__(parent=parent,
                                          id=id,
                                          pos=wx.DefaultPosition,
                                          size=[400,700],
                                          style=wx.DEFAULT_FRAME_STYLE,
                                          name=title,
                                          )

        expCtrlSize = [200, 150]
        ctrlSize = [400, 150]

        self.app = app
        self.parent = parent

        # Set expCtrl
        self.expCtrl = ExpCtrl(parent, wx.ID_ANY, expCtrlSize)
        btnFont = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
        plusBtn = wx.Button(self, -1, '+', size=[30, 30])
        negBtn = wx.Button(self, -1, '-', size=[30, 30])

        plusBtn.SetFont(btnFont)
        negBtn.SetFont(btnFont)

        self.expListSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.expBtnSizer = wx.BoxSizer(wx.VERTICAL)

        self.expBtnSizer.Add(plusBtn, 1)
        self.expBtnSizer.Add(negBtn, 1)
        self.expListSizer.Add(self.expCtrl, 1)
        self.expListSizer.Add(self.expBtnSizer, 1)

        # Set stdout
        self.stdoutCtrl = StdOutText(parent=self, style=wx.TE_READONLY | wx.TE_MULTILINE, size=ctrlSize)

        # Set sizers
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.expListSizer, 1, wx.ALL, 10)
        self.mainSizer.Add(self.stdoutCtrl, 1, wx.EXPAND | wx.ALL, 10)

        self.SetSizerAndFit(self.mainSizer)
        self.SetMinSize(self.Size)

    def onURL(self, evt):
        self.parent.onURL(evt)


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

class ExpCtrl(wx.ListCtrl):
    """This will be the list of experiments"""
    def __init__(self, parent, ID, size):
        super(ExpCtrl, self).__init__(parent=parent,
                                      id=ID,
                                      size=size,
                                      style=wx.LC_REPORT | wx.BORDER_SUNKEN)

        self.InsertColumn(0, 'File')
        self.InsertColumn(1, 'Type')
