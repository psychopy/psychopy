from psychopy.app import utils
from psychopy.app.builder.dialogs.paramCtrls import EVT_PARAM_CHANGED, ParamCtrl
from psychopy.app.builder.validators import WarningManager
from psychopy.app.themes import fonts


import wx
from wx.lib.scrolledpanel import ScrolledPanel
import wx.propgrid


class DevicePanel(ScrolledPanel):
    def __init__(self, parent, dlg, device):
        ScrolledPanel.__init__(self, parent, style=wx.DEFAULT | wx.VSCROLL)
        self.SetMinSize((512, -1))
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
        # sort params by categ then order
        sortedParams = {}
        for key in device.order:
            if key in device.params:
                # make sure there's a page for this category
                categ = device.params[key].categ
                if categ not in sortedParams:
                    sortedParams[categ] = {}
                # add param to categ
                sortedParams[categ][key] = device.params[key]
        for key in device.params:
            # make sure there's a page for this category
            categ = device.params[key].categ
            if categ not in sortedParams:
                sortedParams[categ] = {}
            # add param to categ
            if key not in sortedParams[categ]:
                sortedParams[categ][key] = device.params[key]
        # param ctrls
        self.paramCtrls = {}
        for categ in sortedParams:
            # if categ if Basic, add to root sizer
            toggle = None
            if categ == "Basic":
                categSizer = self.sizer
            else:
                # otherwise, make a show/hider
                categSizer = wx.BoxSizer(wx.VERTICAL)
                toggle = utils.ShowHideBtn(
                    self, target=categSizer, label=categ
                )
                self.sizer.Add(
                    toggle, border=6, flag=wx.EXPAND | wx.ALL
                )
                self.sizer.Add(
                    categSizer, border=0, flag=wx.EXPAND | wx.ALL
                )
            for name, param in sortedParams[categ].items():
                # make param ctrl
                self.paramCtrls[name] = ctrl = ParamCtrl(
                    self,
                    field=name,
                    param=param,
                    element=device,
                    warnings=self.warnings
                )
                ctrl.Bind(EVT_PARAM_CHANGED, self.onParamEdit)
                # make label
                lbl = wx.StaticText(
                    self, label=param.label
                )
                # make sizer for this ctrl
                if type(ctrl).__name__ in ("BoolCtrl"):
                    sizer = wx.BoxSizer(wx.HORIZONTAL)
                    # add crl
                    sizer.Add(
                        ctrl, border=6, flag=wx.EXPAND | wx.RIGHT
                    )
                    # add label
                    sizer.Add(
                        lbl, flag=wx.ALIGN_CENTER
                    )
                else:
                    sizer = wx.BoxSizer(wx.VERTICAL)
                    # add label
                    sizer.Add(
                        lbl, border=3, flag=wx.EXPAND | wx.BOTTOM
                    )
                    sizer.Add(
                        ctrl, flag=wx.EXPAND
                    )
                    # add ctrl
                # add sizer to panel
                categSizer.Add(
                    sizer, border=6, flag=wx.EXPAND | wx.ALL
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
            # start other categories off hidden
            if toggle:
                toggle.setValue(False)
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
        self.profileCtrl.SetMinSize((-1, 128))
        self.sizer.Add(
            self.profileCtrl, border=6, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM
        )
        # delete button
        self.deleteBtn = wx.Button(self, label="Remove device")
        self.deleteBtn.SetMinSize((-1, 24))
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
        self.SetupScrolling()

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
            # do ctrl's usual ok function
            ctrl.onElementOk(evt)
            # update param
            self.device.params[name] = ctrl.param
            self.device.params[name].val = ctrl.getValue()

    def populate(self):
        # update params
        for name, ctrl in self.paramCtrls.items():
            ctrl.setValue(self.device.params[name].val)

        self.Layout()
