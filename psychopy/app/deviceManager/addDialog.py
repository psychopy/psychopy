from psychopy.app.deviceManager.utils import DeviceImageList
from psychopy.app.builder.dialogs.paramCtrls import EVT_PARAM_CHANGED, ParamCtrl
from psychopy.app.builder.validators import WarningManager
from psychopy.app.themes import fonts, icons
from psychopy.experiment.devices import DeviceBackend
from psychopy.experiment.params import Param
from psychopy.hardware.manager import DeviceManager
from psychopy import logging
from psychopy.localization import _translate


import wx


class AddDeviceDlg(wx.Dialog):

    availableDevices = None

    def __init__(self, parent, deviceName=""):
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
        self.nameLbl = wx.StaticText(self, label=_translate("Device name"))
        self.sizer.Add(
            self.nameLbl, border=6, flag=wx.EXPAND | wx.TOP
        )
        self.name = Param(
            deviceName, valType="str", inputType="name",
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
        self.imageList = DeviceImageList(width=24, height=24)
        self.devicesCtrl.SetImageList(self.imageList)
        self.devicesCtrl.SetIndent(6)
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
        # start off with focus on name field
        self.nameCtrl.SetFocus()

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
                try:
                    AddDeviceDlg.availableDevices[backend] = DeviceManager.getAvailableDevices(backend.deviceClass)
                except Exception as err:
                    logging.warn(f"Failed to scan for {backend.deviceClass} devices, reason: {err}")
        # clear ctrl
        self.devicesCtrl.DeleteAllItems()
        self.branchClasses = {}
        # add a root
        root = self.devicesCtrl.AddRoot("Available devices")
        # iterate through classes...
        for cls, profiles in self.availableDevices.items():
            # don't add label if there's no profiles
            if len(profiles) == 0:
                continue
            # add a child for each class
            branch = self.devicesCtrl.AppendItem(
                root, 
                cls.backendLabel or cls.__name__, 
                image=self.imageList.getIcon(cls) or -1
            )
            self.devicesCtrl.SetItemBold(branch)
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
        device.params['name'].val = self.nameCtrl.getValue()

        return device

    def onSelectItem(self, evt):
        evt.Skip()
        # this event is triggered on deletion due to a bug in wx.TreeCtrl, so catch it
        if not self.devicesCtrl:
            return
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