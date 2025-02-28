import json
import wx
from psychopy.preferences import prefs
from psychopy.hardware.manager import DeviceManager


class DeviceManagerDlg(wx.Dialog):
    """
    GUI for managing named devices, allows user to map device names specified in an experiment to 
    physical devices on this machine.
    """
    def __init__(self, parent, exp):
        wx.Dialog.__init__(
            self, parent, title="Device manager",
            size=(540, 360),
            style=wx.RESIZE_BORDER | wx.CAPTION | wx.CLOSE_BOX
        )
        self.exp = exp
        self.devices = prefs.devices.copy()
        self.deviceTypes = self.exp.getRequiredDeviceNames()
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
            self.namesPnl, choices=list(self.deviceTypes)
        )
        self.namesCtrl.Bind(wx.EVT_LISTBOX, self.onNameSelected)
        self.namesPnl.sizer.Add(
            self.namesCtrl, border=6, proportion=1, flag=wx.EXPAND | wx.ALL
        )

        # profile ctrl
        self.profileCtrl = wx.TextCtrl(
            self.devicePnl, style=wx.TE_MULTILINE | wx.TE_READONLY
        )
        self.devicePnl.sizer.Add(
            self.profileCtrl, border=6, proportion=1, flag=wx.EXPAND | wx.ALL
        )
        # map device button
        self.mapDeviceBtn = wx.Button(
            self.devicePnl, label="Map device"
        )
        self.mapDeviceBtn.Bind(wx.EVT_BUTTON, self.onMapDeviceBtn)
        self.devicePnl.sizer.Add(
            self.mapDeviceBtn, border=6, flag=wx.ALIGN_RIGHT | wx.ALL
        )

        # add ctrls
        self.ctrls = self.CreateStdDialogButtonSizer(
            flags=wx.OK | wx.CANCEL
        )
        self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)
        self.border.Add(self.ctrls, border=12, flag=wx.EXPAND | wx.ALL)

        self.Layout()

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

    def onMapDeviceBtn(self, evt=None):
        # get selected name
        name = self.getCurrentName()
        # open interface for mapping name to a device profile
        if name in self.deviceTypes:
            self.mapDevice(name, self.deviceTypes[name])
    
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
    
    def mapDevice(self, name, types):
        """
        Open an interface to map a given name to a device profile

        Parameters
        ----------
        name : str
            Name to map to
        types : list[str or type]
            List of possible types which the device profile could be
        """
        # make sure types is iterable
        if not isinstance(types, (list, tuple)):
            types = [types]
        # create dialog for mapping a device
        dlg = MapDeviceDlg(self, types)
        # show dialog and update profile if OK
        if dlg.ShowModal() == wx.ID_OK:
            self.devices[name] = dlg.getSelectedProfile()
        # update selection
        self.onNameSelected()


class MapDeviceDlg(wx.Dialog):
    """
    Interface for choosing a device profile from a list of possible types.

    Parameters
    ----------
    parent : wx.Window
        Parent window for this dialog
    types : list[str or type]
        List of possible types which the device profile could be
    """
    def __init__(self, parent, types):
        wx.Dialog.__init__(
            self, parent, title="Map device...",
            style=wx.RESIZE_BORDER | wx.CAPTION | wx.CLOSE_BOX
        )
        # setup sizers
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(
            self.sizer, proportion=1, border=12, flag=wx.EXPAND | wx.ALL
        )
        # setup device ctrl
        self.profilesCtrl = wx.ListCtrl(
            self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL
        )
        self.sizer.Add(
            self.profilesCtrl, proportion=1, border=6, flag=wx.EXPAND | wx.ALL
        )
        # populate
        for cls in types:
            for profile in DeviceManager.getAvailableDevices(cls):
                # make sure required columns exist
                for key in profile:
                    if key not in self.getColumnNames():
                        self.profilesCtrl.AppendColumn(key)
                # format entry
                entry = []
                for key in self.getColumnNames():
                    entry.append(profile.get(key, ""))
                # add entry
                self.profilesCtrl.Append(entry)
        # add ctrls
        self.ctrls = self.CreateStdDialogButtonSizer(
            flags=wx.OK | wx.CANCEL
        )
        self.border.Add(self.ctrls, border=12, flag=wx.EXPAND | wx.ALL)
    
    def getColumnNames(self):
        colNames = []
        for col in range(self.profilesCtrl.GetColumnCount()):
            colNames.append(self.profilesCtrl.GetColumn(col).GetText())
        
        return colNames
    
    def getSelectedProfile(self):
        i = self.profilesCtrl.GetFirstSelected()
        profile = {}
        for col in range(self.profilesCtrl.GetColumnCount()):
            key = self.profilesCtrl.GetColumn(col).GetText()
            profile[key] = self.profilesCtrl.GetItem(i, col=col).GetText()
        
        return profile
