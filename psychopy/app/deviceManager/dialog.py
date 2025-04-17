import json
import wx
from psychopy.localization import _translate
from psychopy.preferences import prefs
from psychopy.hardware.manager import DeviceManager


class DeviceManagerDlg(wx.Dialog):
    """
    GUI for managing named devices, allows user to map device names specified in an experiment to 
    physical devices on this machine.
    """
    def __init__(self, parent):
        wx.Dialog.__init__(
            self, parent, title="Device manager",
            size=(540, 360),
            style=wx.RESIZE_BORDER | wx.CAPTION | wx.CLOSE_BOX
        )
        self.devices = prefs.devices.copy()
        # setup sizers
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        # setup splitter
        self.splitter = wx.SplitterWindow(self)
        self.border.Add(
            self.splitter, border=12, proportion=1, flag=wx.EXPAND | wx.ALL
        )
        # setup panels
        self.namesPnl = wx.Panel(self.splitter)
        self.namesPnl.sizer = wx.BoxSizer(wx.VERTICAL)
        self.namesPnl.SetSizer(self.namesPnl.sizer)
        self.devicePnl = wx.Panel(self.splitter)
        self.devicePnl.sizer = wx.BoxSizer(wx.VERTICAL)
        self.devicePnl.SetSizer(self.devicePnl.sizer)
        self.splitter.SplitVertically(self.namesPnl, self.devicePnl, sashPosition=100)

        # names list
        self.namesCtrl = wx.ListBox(
            self.namesPnl, choices=[]
        )
        self.namesCtrl.Bind(wx.EVT_LISTBOX, self.onNameSelected)
        self.namesPnl.sizer.Add(
            self.namesCtrl, border=6, proportion=1, flag=wx.EXPAND | wx.ALL
        )
        # add device button
        self.addDeviceBtn = wx.Button(
            self.namesPnl, label="Add device"
        )
        self.addDeviceBtn.Bind(wx.EVT_BUTTON, self.onAddDeviceBtn)
        self.namesPnl.sizer.Add(
            self.addDeviceBtn, border=6, flag=wx.ALIGN_RIGHT | wx.ALL
        )

        # profile ctrl
        self.profileCtrl = wx.TextCtrl(
            self.devicePnl, style=wx.TE_MULTILINE | wx.TE_READONLY
        )
        self.devicePnl.sizer.Add(
            self.profileCtrl, border=6, proportion=1, flag=wx.EXPAND | wx.ALL
        )
        self.populate()

        # add ctrls
        self.ctrls = self.CreateStdDialogButtonSizer(
            flags=wx.OK | wx.CANCEL
        )
        self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)
        self.border.Add(self.ctrls, border=12, flag=wx.EXPAND | wx.ALL)

        self.Layout()
    
    def populate(self):
        """
        Populate the device names ctrl from saved devices.
        """
        self.namesCtrl.Clear()
        self.namesCtrl.SetItems(list(self.devices))

    def onNameSelected(self, evt=None):
        # start off with no profile
        self.profileCtrl.SetValue("")
        # get name
        name = self.getCurrentName()
        # disable whole panel if nothing is selected
        self.devicePnl.Enable(name is not None)
        # show/hide profile according to whether device is mapped
        self.profileCtrl.Show(name in self.devices)
        # if mapped, show mapping
        if name in self.devices:
            self.profileCtrl.SetValue(
                json.dumps(self.devices[name], indent=True)
            )
        
        self.Layout()
        self.Refresh()

    def onAddDeviceBtn(self, evt=None):
        dlg = AddDeviceDlg(self)

        if dlg.ShowModal() == wx.ID_OK:
            name, profile = dlg.getDevice()
            self.devices[name] = profile

        self.populate()
    
    def onOK(self, evt):
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


class AddDeviceDlg(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(
            self, parent, title="Add device",
            size=(540, 360),
            style=wx.RESIZE_BORDER | wx.CAPTION | wx.CLOSE_BOX
        )
        # get array of available devices
        self.availableDevices = DeviceManager.getAvailableDevices()
        # setup sizers
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(
            self.sizer, proportion=1, border=12, flag=wx.EXPAND | wx.ALL
        )
        
        # name ctrl
        self.nameLbl = wx.StaticText(self, label=_translate("Device label"))
        self.sizer.Add(
            self.nameLbl, border=6, flag=wx.EXPAND | wx.ALL
        )
        self.nameCtrl = wx.TextCtrl(self)
        self.sizer.Add(
            self.nameCtrl, border=6, flag=wx.EXPAND | wx.ALL
        )

        # devices ctrl
        self.devicesLbl = wx.StaticText(self, label=_translate("Available devices"))
        self.sizer.Add(
            self.devicesLbl, border=6, flag=wx.EXPAND | wx.ALL
        )
        self.devicesCtrl = wx.TreeCtrl(self)
        self.sizer.Add(
            self.devicesCtrl, proportion=1, border=6, flag=wx.EXPAND | wx.ALL
        )
        self.populate()

        # add ctrls
        self.ctrls = self.CreateStdDialogButtonSizer(
            flags=wx.OK | wx.CANCEL
        )
        self.border.Add(self.ctrls, border=12, flag=wx.EXPAND | wx.ALL)

        self.Layout()
    
    def populate(self):
        """
        Populate the devices tree control from DeviceManager
        """
        # clear ctrl
        self.devicesCtrl.DeleteAllItems()
        # add a root
        root = self.devicesCtrl.AddRoot("Available devices")
        # iterate through classes...
        for cls, profiles in self.availableDevices.items():
            # add a child for each class
            branch = self.devicesCtrl.AppendItem(root, cls)
            # iterate through profiles...
            for profile in profiles:
                self.devicesCtrl.AppendItem(branch, profile.get("deviceName", "unnamed"))
        # expand
        self.devicesCtrl.ExpandAll()
    
    def getDevice(self):
        return self.nameCtrl.GetValue(), self.getSelectedProfile()

    def getSelectedProfile(self):
        # get id of selected profile and its parent
        item = self.devicesCtrl.GetSelection()
        branch = self.devicesCtrl.GetItemParent(item)
        # get class and device name
        cls = self.devicesCtrl.GetItemText(branch)
        name = self.devicesCtrl.GetItemText(item)
        # find profile with matching name
        profile = None
        for thisProfile in self.availableDevices[cls]:
            if thisProfile.get("deviceName", "unnamed") == name:
                profile = thisProfile
                break
        print(profile)

        return profile
