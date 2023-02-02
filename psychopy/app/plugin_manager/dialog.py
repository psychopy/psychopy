import wx

from psychopy.app import getAppInstance
from psychopy.app.plugin_manager import PluginManagerPanel, PackageManagerPanel
from psychopy.localization import _translate
import psychopy.tools.pkgtools as pkgtools

pkgtools.refreshPackages()  # build initial package cache


class EnvironmentManagerDlg(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(
            self, parent=parent,
            title=_translate("Plugins & Packages"),
            size=(1080, 720),
            style=wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE | wx.CENTER | wx.TAB_TRAVERSAL | wx.NO_BORDER
        )
        self.SetMinSize((980, 520))
        self.app = getAppInstance()
        # Setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.EXPAND | wx.ALL)
        # Create notebook
        self.notebook = wx.Notebook(self)
        self.sizer.Add(self.notebook, border=6, proportion=1, flag=wx.EXPAND | wx.ALL)
        # Plugin manager
        self.pluginMgr = PluginManagerPanel(self.notebook)
        self.notebook.AddPage(self.pluginMgr, text=_translate("Plugins"))
        # Package manager
        self.packageMgr = PackageManagerPanel(self.notebook)
        self.notebook.AddPage(self.packageMgr, text=_translate("Packages"))

        # Buttons
        self.btns = self.CreateStdDialogButtonSizer(flags=wx.HELP | wx.CLOSE)
        self.sizer.Add(self.btns, border=6, flag=wx.EXPAND | wx.ALL)

    def onClose(self, evt=None):
        # Get changes to plugin states
        pluginChanges = self.pluginMgr.pluginList.getChanges()

        # If any plugins have been uninstalled, prompt user to restart
        if any(["uninstalled" in changes for changes in pluginChanges.values()]):
            msg = _translate(
                "It looks like you've uninstalled some plugins. In order for this to take effect, you will need to "
                "restart the PsychoPy app.\n"
            )
            dlg = wx.MessageDialog(
                None, msg,
                style=wx.ICON_WARNING | wx.OK
            )
            dlg.ShowModal()

        # Repopulate component panels
        for frame in self.app.getAllFrames():
            if hasattr(frame, "componentButtons") and hasattr(frame.componentButtons, "populate"):
                frame.componentButtons.populate()
