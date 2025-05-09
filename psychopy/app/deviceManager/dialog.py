import importlib
import json
import wx, wx.propgrid
from psychopy.app.builder.dialogs.paramCtrls import ParamCtrl, EVT_PARAM_CHANGED
from psychopy.app.builder.validators import WarningManager
from psychopy.experiment.params import Param
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
        self.profilesListCtrl.SetColumnWidth(-1, 128)
        self.profilesListCtrl.SetMinSize((128, 128))
        self.profilesListCtrl.Refresh()
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
                self.pages[name] = DevicePanel(
                    parent=self.profilesNotebook, 
                    dlg=self, 
                    device=device
                )
                self.profilesNotebook.AddPage(
                    text=name, page=self.pages[name]
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
            self.profilesNotebook.GetPage(i).onElementOk(evt)
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
        # setup warnings
        self.warnings = WarningManager(self)
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
            self.paramCtrls[name] = ParamCtrl(
                self, 
                field=name, 
                param=param, 
                element=None, 
                warnings=self.warnings
            )
            self.paramCtrls[name].Bind(EVT_PARAM_CHANGED, self.onParamEdit)
            self.sizer.Add(
                self.paramCtrls[name], border=6, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM
            )
            # store name param ctrl
            if name == "deviceLabel":
                self.nameCtrl = self.paramCtrls[name]
                # bump up the font size
                self.nameCtrl.ctrl.SetFont(fonts.AppFont(
                    pointSize=int(fonts.AppFont.pointSize*1.5),
                    bold=True
                ).obj)
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
        # warnings panel
        self.sizer.Add(
            self.warnings.output, border=6, flag=wx.EXPAND | wx.ALL
        )
        
        # populate from device
        self.populate()
    
    def onDelete(self, evt=None):
        # remove from devices
        del self.dlg.devices[self.device.name]
        # remove page
        self.dlg.profilesNotebook.DeletePage(
            self.dlg.profilesNotebook.FindPage(self)
        )
        del self.dlg.pages[self.device.name]                
        # repopulate without this page
        self.dlg.populate()

    def onParamEdit(self, evt=None):
        # get calling ctrl and param
        ctrl = evt.GetEventObject()
        param = ctrl.param
        # if renaming, pass it to the dialog so the control updates
        if ctrl is self.nameCtrl:
            self.dlg.renameDevice(
                oldname=self.device.name,
                newname=self.nameCtrl.getValue()
            )
            return
        # set value from ctrl
        param.val = ctrl.getValue()
        # validate dlg
        self.dlg.validate()
    
    def onElementOk(self, evt=None):
        for name, ctrl in self.paramCtrls.items():
            ctrl.onElementOk(evt)

    def populate(self):
        # update params
        for name, ctrl in self.paramCtrls.items():
            ctrl.setValue(str(self.device.params[name].val))
        
        self.Layout()


class AddDeviceDlg(wx.Dialog):

    availableDevices = None

    def __init__(self, parent):
        wx.Dialog.__init__(
            self, parent, title="Add device",
            size=(540, 540),
            style=wx.RESIZE_BORDER | wx.CAPTION | wx.CLOSE_BOX
        )
        # attributes to store selection
        self.selectedCls = None
        self.selectedProfile = None
        # setup warnings
        self.warnings = WarningManager(self)
        # setup sizers
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(
            self.sizer, proportion=1, border=12, flag=wx.EXPAND | wx.ALL
        )
        # name ctrl
        self.name = Param(
            "device", valType="str", inputType="name",
            label=_translate("Device label"),
            hint=_translate(
                "A name to refer to this device by in Device Manager."
            )
        )
        self.nameCtrl = ParamCtrl(
            self,
            field="name",
            param=self.name,
            element=None,
            warnings=self.warnings
        )
        # bump up the font size
        self.nameCtrl.ctrl.SetFont(fonts.AppFont(
            pointSize=int(fonts.AppFont.pointSize*1.5),
            bold=True
        ).obj)
        self.sizer.Add(
            self.nameCtrl, border=6, flag=wx.EXPAND | wx.BOTTOM
        )
        self.nameCtrl.Bind(EVT_PARAM_CHANGED, self.validate)

        # devices ctrl
        self.devicesLbl = wx.StaticText(self, label=_translate("Available devices"))
        self.sizer.Add(
            self.devicesLbl, border=6, flag=wx.EXPAND | wx.TOP
        )
        self.devicesCtrl = wx.TreeCtrl(
            self,
            style=wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_NO_LINES
        )
        self.sizer.Add(
            self.devicesCtrl, proportion=1, border=6, flag=wx.EXPAND | wx.BOTTOM
        )
        self.devicesCtrl.Bind(wx.EVT_TREE_SEL_CHANGED, self.onSelectItem)
        self.devicesLoadingLbl = wx.StaticText(
            self, 
            label=_translate("Scanning...")
        )
        self.sizer.Add(
            self.devicesLoadingLbl, border=6, flag=wx.EXPAND | wx.ALL
        )
        # warnings panel
        self.sizer.Add(
            self.warnings.output, border=6, flag=wx.EXPAND | wx.TOP
        )
        # add ctrls
        self.ctrls = self.CreateStdDialogButtonSizer(
            flags=wx.OK | wx.CANCEL
        )
        self.border.Add(
            self.ctrls, border=12, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM
        )
        # get handle of OK button
        for item in self.ctrls.GetChildren():
            if item.Window is not None and item.Window.GetId() == wx.ID_OK:
                self.okBtn = item.Window
        self.Layout()

        # queue populate command
        self.Bind(wx.EVT_IDLE, self.populateAsync)
    
    def validate(self, evt=None):
        self.okBtn.Enable(
            self.warnings.OK 
            and self.selectedCls is not None
            and self.selectedProfile is not None
        )
    
    def populate(self):
        """
        Populate the devices tree control from DeviceManager
        """
        # start off with "loading devices" message
        self.devicesLoadingLbl.Show()
        self.devicesCtrl.Hide()
        self.Layout()
        # get array of available devices by backend
        if AddDeviceDlg.availableDevices is None:
            AddDeviceDlg.availableDevices = {}
            for backend in DeviceBackend.getAllBackends():
                AddDeviceDlg.availableDevices[backend] = DeviceManager.getAvailableDevices(backend.deviceClass)
        # clear ctrl
        self.devicesCtrl.DeleteAllItems()
        self.branchClasses = {}
        self.imageList = wx.ImageList(width=16, height=16)
        self.devicesCtrl.SetImageList(self.imageList)
        # add a root
        root = self.devicesCtrl.AddRoot("Available devices")
        # iterate through classes...
        for cls, profiles in self.availableDevices.items():
            # add icon if possible
            if cls.icon is not None:
                bmp = icons.BaseIcon.resizeBitmap(
                    wx.Bitmap(str(cls.getIconFile())), 
                    size=16
                )
                img = self.imageList.Add(bmp)
            else:
                img = -1
            # add a child for each class
            branch = self.devicesCtrl.AppendItem(root, cls.backendLabel, image=img)
            # store ref to branch class
            self.branchClasses[branch] = cls
            # iterate through profiles...
            for profile in profiles:
                self.devicesCtrl.AppendItem(branch, profile.get("deviceName", "unnamed"))
        # expand and show
        self.devicesCtrl.ExpandAll()
        self.devicesLoadingLbl.Hide()
        self.devicesCtrl.Show()
        self.Layout()
    
    def populateAsync(self, evt):
        """
        Call `.populate` from an asynchronous event handler, the unbind it.

        Parameters
        ----------
        evt : wx.IdleEvent
            wx event triggering this call
        """
        # populate
        self.populate()
        # unbind
        if evt.EventType == wx.EVT_IDLE.typeId:
            self.Unbind(wx.EVT_IDLE)
    
    def getDevice(self):
        """
        Get the Device object from the choice made in this ctrl.

        Returns
        -------
        psychopy.experiment.devices.DeviceBackend
            Backend object for the chosen device
        """
        # create device object
        device = self.selectedCls(self.selectedProfile)
        # store name
        device.params['deviceLabel'].val = self.nameCtrl.getValue()
        
        return device

    def onSelectItem(self, evt):
        evt.Skip()
        # get id of selected profile and its parent
        item = self.devicesCtrl.GetSelection()
        branch = self.devicesCtrl.GetItemParent(item)
        # update profile
        if branch != self.devicesCtrl.GetRootItem():
            # get class and device name
            cls = self.branchClasses[branch]
            name = self.devicesCtrl.GetItemText(item)
            # find profile with matching name
            profile = None
            for thisProfile in self.availableDevices[cls]:
                if thisProfile.get("deviceName", "unnamed") == name:
                    profile = thisProfile
                    break
        else:
            # if parent is the root node, selection isn't a profile
            cls = profile = None
        # store selected values
        self.selectedCls = cls
        self.selectedProfile = profile
        # enable OK based on selection
        self.validate()
