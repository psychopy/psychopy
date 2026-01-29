from psychopy.app.deviceManager.addDialog import AddDeviceDlg
from psychopy.app.deviceManager.panel import DevicePanel
from psychopy.app.deviceManager.utils import DeviceImageList
from psychopy.preferences import prefs


import wx


class DeviceManagerDlg(wx.Dialog):
    """
    GUI for managing named devices, allows user to map device names specified in an experiment to 
    physical devices on this machine.
    """
    def __init__(self, parent):
        wx.Dialog.__init__(
            self, parent, title="Device manager",
            size=(720, 540),
            style=wx.RESIZE_BORDER | wx.CAPTION | wx.CLOSE_BOX
        )
        self.SetMinSize((540, 256))
        self.devices = prefs.devices.copy()
        # setup sizers
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(
            self.sizer, border=12, proportion=1, flag=wx.EXPAND | wx.ALL
        )

        # profiles notebook
        self.profilesNotebook = wx.Listbook(self, style=wx.LB_LEFT)
        self.sizer.Add(
            self.profilesNotebook, border=0, proportion=1, flag=wx.EXPAND | wx.ALL
        )
        self.pages = {}
        # resize the list ctrl
        self.profilesListCtrl = self.profilesNotebook.GetListView()
        self.profilesListCtrl.SetWindowStyleFlag(wx.LC_LIST)

        if wx.Platform == "__WXMSW__":
            self.profilesListCtrl.SetColumnWidth(-1, 128)
            
        self.profilesListCtrl.SetMinSize((128, 128))
        self.profilesListCtrl.Refresh()
        # apply cached devices image list
        self.imageList = DeviceImageList(width=24, height=24)
        self.profilesListCtrl.SetImageList(self.imageList, which=wx.IMAGE_LIST_SMALL)
        # self.profilesListCtrl.SetWindowStyle(wx.LC_ICON)
        # get list ctrl sizer so we can add ctrls
        self.profilesListCtrl.sizer = self.profilesListCtrl.GetSizer()
        if self.profilesListCtrl.sizer is None:
            # on windows, ListCtrl doesn't have a sizer, so make one
            self.profilesListCtrl.sizer = wx.BoxSizer(wx.VERTICAL)
            self.profilesListCtrl.sizer.AddStretchSpacer(1)
            self.profilesListCtrl.SetSizer(self.profilesListCtrl.sizer)
        # add device button
        self.addDeviceBtn = wx.Button(
            self.profilesListCtrl, label="Add device"
        )
        self.addDeviceBtn.Bind(wx.EVT_BUTTON, self.onAddDeviceBtn)
        self.profilesListCtrl.sizer.Add(
            self.addDeviceBtn, border=6, flag=wx.EXPAND | wx.ALL
        )

        self.populate()

        # add ctrls
        self.ctrls = self.CreateStdDialogButtonSizer(
            flags=wx.OK | wx.CANCEL
        )
        self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)
        self.border.Add(self.ctrls, border=12, flag=wx.EXPAND | wx.ALL)
        # get handle of OK button
        for item in self.ctrls.GetChildren():
            if item.Window is not None and item.Window.GetId() == wx.ID_OK:
                self.okBtn = item.Window

        self.Layout()
    
    def populate(self):
        """
        Populate the device names ctrl from saved devices.
        """
        # add pages
        for name, device in self.devices.items():
            if name not in self.pages:
                # create page
                self.pages[name] = DevicePanel(
                    parent=self.profilesNotebook, 
                    dlg=self, 
                    device=device
                )
                # add page
                self.profilesNotebook.AddPage(
                    text=name, page=self.pages[name], imageId=self.imageList.getIcon(device)
                )
        # add/remove a placeholder depending on whether there's no pages
        if not len(self.pages):
            self.pages[None] = wx.Panel(self.profilesNotebook)
            self.profilesNotebook.AddPage(text="", page=self.pages[None])
        elif None in self.pages:
            self.profilesNotebook.RemovePage(
                self.profilesNotebook.FindPage(self.pages[None])
            )
            del self.pages[None]
    
    def renameDevice(self, oldname, newname):
        # set name param
        self.devices[oldname].name = newname
        # rename tab
        self.profilesNotebook.SetPageText(
            self.profilesNotebook.FindPage(self.pages[oldname]),
            newname
        )
        # relocate in devices array
        self.devices[newname] = self.devices.pop(oldname)
        # relocate in pages array
        self.pages[newname] = self.pages.pop(oldname)
        # validate ok button
        self.validate()

    def onNameSelected(self, evt=None):
        # get name
        name = self.getCurrentName()
        # disable whole panel if nothing is selected
        self.devicePnl.Enable(name is not None)
        # if mapped, show mapping
        if name in self.pages:
            self.profilesNotebook.ChangeSelection(
                self.profilesNotebook.FindPage(self.pages[name])
            )
        
        self.Layout()
        self.Refresh()

    def onAddDeviceBtn(self, evt=None):
        dlg = AddDeviceDlg(self)

        if dlg.ShowModal() == wx.ID_OK:
            # get selected device
            device = dlg.getDevice()
            # create Device object
            self.devices[device.name] = device

        self.populate()
    
    def validate(self):
        # enable/disable OK button if every page is okay
        self.okBtn.Enable(all([
            self.profilesNotebook.GetPage(i).warnings.OK 
            for i in range(self.profilesNotebook.GetPageCount())
        ]))
    
    def onOK(self, evt):
        # run on OK methods from all params
        for i in range(self.profilesNotebook.GetPageCount()):
            page = self.profilesNotebook.GetPage(i)
            if hasattr(page, "onElementOk"):
                page.onElementOk(evt)
        # save config
        self.devices.save()
        # reload in prefs so changes are applied this session
        prefs.devices.reload()

        evt.Skip()
    
    def getCurrentName(self):
        """
        Get the currently selected name.

        Returns
        -------
        str
            Current name
        """
        # get index of selection
        i = self.namesCtrl.GetSelection()
        # return None if none found
        if i == wx.NOT_FOUND:
            return None
        # get name
        name = self.namesCtrl.GetString(i)

        return name
