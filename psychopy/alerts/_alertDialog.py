import wx
import wx.lib.sized_controls as sc


class AlertDlg(sc.SizedDialog):
    """
    Alerts docstring

    See wx Sized Control Error Dlg
    """
    def __init__(self, parent=None, id=wx.ID_ANY, size=[200,200], alerts=None):
        sc.SizedDialog.__init__(self, parent, id, "Alerts log viewer",
                                style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        # Always use self.GetContentsPane() - this ensures that your dialog
        # automatically adheres to HIG spacing requirements on all platforms.
        # pane here is a sc.SizedPanel with a vertical sizer layout. All children
        # should be added to this pane, NOT to self.
        panel = self.GetContentsPane()
        # wx.Panel.__init__(self, parent, wx.ID_ANY, size=size)

        self.alerts = alerts

        # first row
        self.listCtrl = wx.ListCtrl(panel, -1, size=(300, -1), style=wx.LC_REPORT)
        self.listCtrl.SetSizerProps(expand=True, proportion=1)
        self.ConfigureListCtrl()

        for alert in self.alerts:
            temp = [alert.code, alert.cat, alert.name, alert.msg, alert.url]
            self.listCtrl.Append(temp)
        self.listCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.getListItem)

        # second row
        self.lblDetails = wx.StaticText(panel, -1, "Alerts")

        # third row
        self.details = wx.TextCtrl(panel, -1, value='', style=wx.TE_MULTILINE)
        self.details.SetSizerProps(expand=True, proportion=1)

        self.Fit()
        self.SetMinSize(self.GetSize())
        self.Center()
        self.Show()

    def getListItem(self, evt):

        itemSelected = evt.GetEventObject().GetFirstSelected()
        helpText = self.listCtrl.GetItem(itemIdx=itemSelected, col=3).Text
        self.details.SetLabel(helpText)

    def ConfigureListCtrl(self):
        self.listCtrl.InsertColumn(0, "Code")
        self.listCtrl.InsertColumn(1, "Category")
        self.listCtrl.InsertColumn(2, "Component")
        self.listCtrl.InsertColumn(3, "Message")
        self.listCtrl.InsertColumn(4, "URL")

        self.listCtrl.SetColumnWidth(0, 50)
        self.listCtrl.SetColumnWidth(1, 100)
        self.listCtrl.SetColumnWidth(2, 150)
        self.listCtrl.SetColumnWidth(3, 200)
        self.listCtrl.SetColumnWidth(4, 250)