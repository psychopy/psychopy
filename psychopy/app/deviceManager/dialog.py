import importlib
import json
import wx, wx.propgrid
from psychopy.localization import _translate
from psychopy.preferences import prefs
from psychopy.hardware.manager import DeviceManager
from psychopy.experiment.devices import DeviceBackend
from psychopy.app.themes import icons, fonts


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
        self.profilesListCtrl.Refresh()
        # set a sizer on the list control so we can add controls
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

        self.Layout()
    
    def populate(self):
        """
        Populate the device names ctrl from saved devices.
        """
        # add pages
        for name, device in self.devices.items():
            if name not in self.pages:
                self.pages[name] = DevicePanel(
                    parent=self.profilesNotebook, 
                    dlg=self, 
                    device=device
                )
                self.profilesNotebook.AddPage(
                    text=name, page=self.pages[name]
                )
        # delete pages from extinct devices
        for name in self.pages:
            if name not in self.devices:
                self.profilesNotebook.DeletePage(
                    self.profilesNotebook.FindPage(self.pages[name])
                )
    
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
            name, cls, profile = dlg.getDevice()
            # create Device object
            self.devices[name] = cls(profile)
            self.devices[name].params['deviceLabel'].val = name

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


class DevicePanel(wx.Panel):
    def __init__(self, parent, dlg, device):
        wx.Panel.__init__(self, parent)
        # store parentage
        self.parent = parent
        self.dlg = dlg
        # store device
        self.device = device
        # setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(
            self.sizer, proportion=1, border=0, flag=wx.EXPAND | wx.ALL
        )
        # sort params by order
        sortedParams = {}
        for key in device.order:
            if key in device.params:
                sortedParams[key] = device.params[key]
        for key in device.params:
            if key not in sortedParams:
                sortedParams[key] = device.params[key]
        # param ctrls
        self.paramCtrls = {}
        for name, param in sortedParams.items():
            # make label
            lbl = wx.StaticText(
                self, label=param.label
            )
            self.sizer.Add(
                lbl, border=6, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP
            )
            # make param ctrl
            self.paramCtrls[name] = wx.TextCtrl(self)
            self.paramCtrls[name].param = param
            self.paramCtrls[name].Bind(wx.EVT_TEXT, self.onParamEdit)
            self.sizer.Add(
                self.paramCtrls[name], border=6, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM
            )
            # store name param ctrl
            if name == "deviceLabel":
                self.nameCtrl = self.paramCtrls[name]
                # style name ctrl
                self.nameCtrl.SetFont(
                    fonts.AppFont(pointSize=int(fonts.AppFont.pointSize*1.2), bold=True).obj
                )
                # hide label
                lbl.Hide()
        # profile label
        self.profileLbl = wx.StaticText(self, label="Device information")
        self.sizer.Add(
            self.profileLbl, border=6, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP
        )
        # profile ctrl
        self.profileCtrl = wx.propgrid.PropertyGrid(self)
        for key, val in device.profile.items():
            prop = wx.propgrid.StringProperty(key, key, str(val))
            self.profileCtrl.Append(prop)
            prop.ChangeFlag(wx.propgrid.PG_PROP_READONLY, True)  
        self.profileCtrl.FitColumns()
        self.sizer.Add(
            self.profileCtrl, border=6, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM
        )
        # delete button
        self.deleteBtn = wx.Button(self, label="Remove device")
        self.deleteBtn.Bind(wx.EVT_BUTTON, self.onDelete)
        self.sizer.Add(
            self.deleteBtn, border=6, flag=wx.ALIGN_RIGHT | wx.ALL
        )
        
        # populate from device
        self.populate()
    
    def onDelete(self, evt=None):
        # remove from devices
        del self.dlg.devices[self.device.name]
        # repopulate without this page
        self.dlg.populate()

    def onParamEdit(self, evt):
        # get calling ctrl and param
        ctrl = evt.GetEventObject()
        param = ctrl.param
        # if renaming, pass it to the dialog so the control updates
        if ctrl is self.nameCtrl:
            self.dlg.renameDevice(
                oldname=self.device.name,
                newname=self.nameCtrl.GetValue()
            )
            return
        # set value from ctrl
        param.val = ctrl.GetValue()  

    def populate(self):
        # update params
        for name, ctrl in self.paramCtrls.items():
            ctrl.ChangeValue(str(self.device.params[name].val))
        
        self.Layout()


class AddDeviceDlg(wx.Dialog):

    availableDevices = None

    def __init__(self, parent):
        wx.Dialog.__init__(
            self, parent, title="Add device",
            size=(540, 360),
            style=wx.RESIZE_BORDER | wx.CAPTION | wx.CLOSE_BOX
        )
        # get array of available devices by backend
        if AddDeviceDlg.availableDevices is None:
            AddDeviceDlg.availableDevices = {}
            for backend in DeviceBackend.getAllBackends():
                AddDeviceDlg.availableDevices[backend] = DeviceManager.getAvailableDevices(backend.deviceClass)
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
        self.branchClasses = {}
        # add a root
        root = self.devicesCtrl.AddRoot("Available devices")
        # iterate through classes...
        for cls, profiles in self.availableDevices.items():
            # add a child for each class
            branch = self.devicesCtrl.AppendItem(root, cls.backendName)
            # store ref to branch class
            self.branchClasses[branch] = cls
            # iterate through profiles...
            for profile in profiles:
                self.devicesCtrl.AppendItem(branch, profile.get("deviceName", "unnamed"))
        # expand
        self.devicesCtrl.ExpandAll()
    
    def getDevice(self):
        return self.nameCtrl.GetValue(), *self.getSelectedProfile()

    def getSelectedProfile(self):
        # get id of selected profile and its parent
        item = self.devicesCtrl.GetSelection()
        branch = self.devicesCtrl.GetItemParent(item)
        # get class and device name
        cls = self.branchClasses[branch]
        name = self.devicesCtrl.GetItemText(item)
        # find profile with matching name
        profile = None
        for thisProfile in self.availableDevices[cls]:
            if thisProfile.get("deviceName", "unnamed") == name:
                profile = thisProfile
                break

        return cls, profile
