import wx
from psychopy.alerts._alerts import AlertEntry
from psychopy.alerts._alerts import alertLog


class AlertPanel(wx.Panel):
    """
    Alerts panel for presenting alerts stored in _alerts.alertLog
    """
    def __init__(self, parent=None, id=wx.ID_ANY, size=[300,300]):
        wx.Panel.__init__(self, parent, id, size=size)

        self.lblDetails = wx.StaticText(self, -1, "Alerts")
        self.listCtrl = wx.ListCtrl(self, -1, style=wx.LC_REPORT)
        self.ConfigureListCtrl()

        for alert in alertLog:
            if isinstance(alert, AlertEntry):
                temp = [alert.code, alert.cat, alert.name, alert.msg, alert.url]
                self.listCtrl.Append(temp)

        # self.listCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.getListItem)
        # self.details = wx.TextCtrl(panel, -1, value='', style=wx.TE_MULTILINE)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.lblDetails, 0, wx.LEFT, 10)
        mainSizer.Add(self.listCtrl, 1, wx.EXPAND | wx.ALL, 10)
        self.SetSizerAndFit(mainSizer)

        self.SetSizerAndFit(mainSizer)
        self.SetMinSize(size)

    # def getListItem(self, evt):
    #     itemSelected = evt.GetEventObject().GetFirstSelected()
    #     helpText = self.listCtrl.GetItem(itemIdx=itemSelected, col=3).Text
    #     self.details.SetLabel(helpText)

    def ConfigureListCtrl(self):
        self.listCtrl.InsertColumn(0, "Code")
        self.listCtrl.InsertColumn(1, "Category")
        self.listCtrl.InsertColumn(2, "Component")
        self.listCtrl.InsertColumn(3, "Message")
        self.listCtrl.InsertColumn(4, "URL")

        self.listCtrl.SetColumnWidth(0, 50)
        self.listCtrl.SetColumnWidth(1, 100)
        self.listCtrl.SetColumnWidth(2, 150)
        self.listCtrl.SetColumnWidth(3, 500)
        self.listCtrl.SetColumnWidth(4, 250)
