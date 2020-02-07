"""Plugin manger for PsychoPy GUI apps (Builder and Coder)."""

from __future__ import absolute_import, division, print_function

from pkg_resources import parse_version
import wx

try:
    from wx import aui
except ImportError:
    import wx.lib.agw.aui as aui  # some versions of phoenix
try:
    from wx.adv import PseudoDC
except ImportError:
    from wx import PseudoDC

if parse_version(wx.__version__) < parse_version('4.0.3'):
    wx.NewIdRef = wx.NewId

from psychopy import logging, plugins
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

from psychopy.preferences import prefs


class CustomListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
    """Custom ListCtrl that allows for automatic resizing of columns."""
    def __init__(self, parent, id):
        wx.ListCtrl.__init__(self,
                             parent,
                             id,
                             style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        ListCtrlAutoWidthMixin.__init__(self)


class EntryPointViewer(wx.Dialog):
    """Dialog that displays a plugin's entry points.
    """
    def __init__(self, parent, pluginName):
        """A dialog for loading and managing plugins.
        """
        self.parent = parent
        self.pluginName = pluginName
        title = "Plugin Entry Points"
        pos = wx.Point(parent.Position[0] + 80, parent.Position[1] + 80)
        wx.Dialog.__init__(self, parent, title=title,
                           size=(640, 480), pos=pos,
                           style=wx.DEFAULT_DIALOG_STYLE |
                                 wx.FRAME_FLOAT_ON_PARENT |
                                 wx.RESIZE_BORDER)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.initCtrls()

    def onClose(self, evt=None):
        """
        Defines behavior on close of the Readme Frame
        """
        self.Destroy()

    def initCtrls(self):
        """Create window controls."""
        frameSizer = wx.BoxSizer(wx.VERTICAL)
        framePanel = wx.Panel(self)
        framePanelSizer = wx.BoxSizer(wx.VERTICAL)

        # add the box
        fraEntryPoints = wx.StaticBox(
            framePanel, wx.ID_ANY,
            "Entry points for plugin `{}`".format(self.pluginName))
        fraSizer = wx.StaticBoxSizer(fraEntryPoints, wx.HORIZONTAL)

        epTree = wx.TreeCtrl(fraEntryPoints, id=wx.ID_ANY,
                             style=wx.TR_HAS_BUTTONS)
        root = epTree.AddRoot(self.pluginName)

        # populate the tree control
        entryPointMap = plugins.pluginEntryPoints(self.pluginName)
        for group, entryPoints in entryPointMap.items():
            groupNode = epTree.AppendItem(root, group)
            for _, val in entryPoints.items():
                epTree.AppendItem(groupNode, str(val))

        epTree.ExpandAll()
        fraSizer.Add(epTree, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP |
                                  wx.BOTTOM, border=5, proportion=1)

        # panel for dialog buttons
        pnlDialogCtrls = wx.Panel(framePanel)
        pnlDialogCtrlsSizer = wx.FlexGridSizer(1, 1, 10, 10)
        pnlDialogCtrls.SetSizer(pnlDialogCtrlsSizer)

        # load selected plugin button
        self.cmdClose = wx.Button(pnlDialogCtrls, id=wx.ID_ANY, label='Close')
        self.cmdClose.Bind(wx.EVT_BUTTON, self.onClose)
        pnlDialogCtrlsSizer.Add(self.cmdClose, 0, 0)

        # add the panel to the frame sizer
        framePanelSizer.Add(fraSizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT |
                                           wx.TOP | wx.BOTTOM, border=10,
                            proportion=1)
        framePanelSizer.Add(pnlDialogCtrls, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM
                                                 | wx.ALIGN_RIGHT, border=10)

        # add the panel to the frame sizer

        framePanel.SetSizer(framePanelSizer)
        frameSizer.Add(framePanel, flag=wx.EXPAND | wx.ALL, proportion=1)
        self.SetSizer(frameSizer)


class PluginManagerFrame(wx.Dialog):
    """Defines the construction of the plugin manager frame.

    This provides a graphical interface for getting information about installed
    plugins and loading them into the current session. This UI is accessed
    through the "File" > "Plugin Manager" menu item in Builder and Coder.

    """
    def __init__(self, parent):
        """A frame for loading and managing plugins.
        """
        self.parent = parent
        title = "Plugin Manager"
        pos = wx.Point(parent.Position[0] + 80, parent.Position[1] + 80)
        _style = wx.DEFAULT_DIALOG_STYLE | wx.FRAME_FLOAT_ON_PARENT | wx.RESIZE_BORDER
        wx.Dialog.__init__(self, parent, title=title,
                           size=(800, 600), pos=pos, style=_style)
        self.Bind(wx.EVT_CLOSE, self.onClose)

        self.selectedItem = -1

        self.initCtrls()
        self.refreshList()

    def refreshList(self):
        """Refresh the plugin list.
        """
        self.lstPlugins.DeleteAllItems()  # clear existing items

        # get current state
        self.startupPlugins = plugins.listPlugins('startup')

        # populate the list with installed plugins
        for pName in plugins._installed_plugins_:
            metadata = plugins.pluginMetadata(pName)
            index = self.lstPlugins.InsertItem(0, pName)
            self.lstPlugins.SetItem(
                index, 1,
                u'\u2713' if pName in plugins._loaded_plugins_.keys() else u'')
            self.lstPlugins.SetItem(
                index, 2,
                u'\u2713' if pName in self.startupPlugins else u'')
            self.lstPlugins.SetItem(
                index, 3,
                metadata['Version'] if 'Version' in metadata.keys() else 'N/A')
            self.lstPlugins.SetItem(
                index, 4,
                metadata['Author'] if 'Author' in metadata.keys() else 'N/A')
            self.lstPlugins.SetItem(
                index, 5,
                metadata['Summary'] if 'Summary' in metadata.keys() else 'N/A')

        self.cmdLoadPlugin.Disable()
        self.cmdEntryPoints.Disable()
        self.chkStartup.SetValue(False)
        self.chkStartup.Disable()

    def initCtrls(self):
        """Create window controls."""
        frameSizer = wx.BoxSizer(wx.VERTICAL)
        framePanel = wx.Panel(self)
        panelSizer = wx.BoxSizer(wx.VERTICAL)

        # add the box
        fraPlugins = wx.StaticBox(framePanel, wx.ID_ANY, "Installed Plugins")
        fraSizer = wx.StaticBoxSizer(fraPlugins, wx.HORIZONTAL)
        pnlPlugins = wx.Panel(fraPlugins)
        bsizer = wx.BoxSizer(wx.HORIZONTAL)

        # plugin list
        self.lstPlugins = CustomListCtrl(pnlPlugins, id=wx.ID_ANY)
        self.lstPlugins.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.lstPlugins.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onItemSelected)
        self.lstPlugins.InsertColumn(0, 'Name', width=120)
        self.lstPlugins.InsertColumn(1, 'Loaded', wx.LIST_FORMAT_CENTER, width=60)
        self.lstPlugins.InsertColumn(2, 'Startup', wx.LIST_FORMAT_CENTER, width=60)
        self.lstPlugins.InsertColumn(3, 'Version', width=100)
        self.lstPlugins.InsertColumn(4, 'Author', width=150)
        self.lstPlugins.InsertColumn(5, 'Description', width=250)

        bsizer.Add(self.lstPlugins, flag=wx.EXPAND | wx.ALL, proportion=1)
        fraSizer.Add(pnlPlugins, flag=wx.EXPAND | wx.ALL, proportion=1, border=5)

        # plugin buttons
        buttonSizer = wx.BoxSizer(wx.VERTICAL)

        # rescan plugins button
        self.cmdScanPlugin = wx.Button(pnlPlugins, id=wx.ID_ANY, label='Rescan')
        self.cmdScanPlugin.Bind(wx.EVT_BUTTON, self.onRescanPlugins)
        self.cmdScanPlugin.SetToolTip(wx.ToolTip(
            "Rescan installed packages for PsychoPy plugins."))
        buttonSizer.Add(self.cmdScanPlugin, flag=wx.EXPAND | wx.BOTTOM, border=5)

        # load selected plugin button
        self.cmdLoadPlugin = wx.Button(pnlPlugins, id=wx.ID_ANY, label='Load')
        self.cmdLoadPlugin.Bind(wx.EVT_BUTTON, self.onLoadPlugin)
        self.cmdLoadPlugin.SetToolTip(wx.ToolTip("Load the selected plugin."))
        buttonSizer.Add(self.cmdLoadPlugin, flag=wx.EXPAND | wx.BOTTOM, border=5)

        # display entry points button
        self.cmdEntryPoints = wx.Button(pnlPlugins, id=wx.ID_ANY,
                                        label='Entry Points ...')
        self.cmdEntryPoints.Bind(wx.EVT_BUTTON, self.onShowEntryPoints)
        self.cmdEntryPoints.SetToolTip(wx.ToolTip(
            "Display the entry points for the selected plugin."))
        buttonSizer.Add(self.cmdEntryPoints, flag=wx.EXPAND | wx.BOTTOM, border=5)

        # load on startup check box
        self.chkStartup = wx.CheckBox(pnlPlugins, id=wx.ID_ANY, label='Load on startup?')
        self.chkStartup.Bind(wx.EVT_CHECKBOX, self.onStartupChecked)
        self.chkStartup.SetToolTip(wx.ToolTip(
            "Load the selected plugin automatically when a PsychoPy session "
            "starts."))
        buttonSizer.Add(self.chkStartup, flag=wx.EXPAND | wx.BOTTOM, border=5)
        bsizer.Add(buttonSizer, flag=wx.EXPAND | wx.BOTTOM | wx.LEFT, border=5)
        pnlPlugins.SetSizer(bsizer)

        # panel for dialog buttons
        pnlDialogCtrls = wx.Panel(framePanel)
        pnlDialogCtrlsSizer = wx.FlexGridSizer(1, 2, 10, 10)
        pnlDialogCtrls.SetSizer(pnlDialogCtrlsSizer)

        # disable all startup plugins button
        self.cmdDisableAll = wx.Button(pnlDialogCtrls, id=wx.ID_ANY, label='Clear startup plugins')
        self.cmdDisableAll.Bind(wx.EVT_BUTTON, self.onClearStartupPlugins)
        self.cmdDisableAll.SetToolTip(wx.ToolTip(
            "Clear all plugins registered to load on startup."))
        pnlDialogCtrlsSizer.Add(self.cmdDisableAll, 0, 0)

        # load selected plugin button
        self.cmdClose = wx.Button(pnlDialogCtrls, id=wx.ID_ANY, label='Close')
        self.cmdClose.Bind(wx.EVT_BUTTON, self.onClose)
        pnlDialogCtrlsSizer.Add(self.cmdClose, 0, 0)

        # add the panel to the frame sizer
        panelSizer.Add(fraSizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, border=10, proportion=1)
        panelSizer.Add(pnlDialogCtrls, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT, border=10)
        framePanel.SetSizer(panelSizer)
        frameSizer.Add(framePanel, flag=wx.EXPAND | wx.ALL, proportion=1)
        self.SetSizer(frameSizer)

    def onStartupChecked(self, evt=None):
        """Called when the checkbox for specifying if a plugin should be loaded
        on startup is clicked."""
        self.selectedItem = self.lstPlugins.GetFirstSelected()
        if self.selectedItem != -1:
            pluginName = self.lstPlugins.GetItem(
                self.selectedItem, col=0).GetText()

            checked = self.chkStartup.GetValue()

            # check if in startup
            if not checked:
                try:
                    prefs.general['startUpPlugins'].remove(pluginName)
                except ValueError:
                    pass
                prefs.saveUserPrefs()
            else:
                plugins.startUpPlugins(pluginName, add=True)

            self.startupPlugins = plugins.listPlugins('startup')
            self.refreshList()

    def onItemSelected(self, evt=None):
        """Get the selected item."""
        self.selectedItem = self.lstPlugins.GetFirstSelected()
        if self.selectedItem != -1:
            pluginName = self.lstPlugins.GetItem(
                self.selectedItem, col=0).GetText()
            self.cmdEntryPoints.Enable()
            self.chkStartup.Enable()
            if pluginName not in plugins._loaded_plugins_.keys():
                self.cmdLoadPlugin.Enable()
            else:
                self.cmdLoadPlugin.Disable()

            self.chkStartup.SetValue(pluginName in self.startupPlugins)
        else:
            self.cmdLoadPlugin.Disable()
            self.cmdEntryPoints.Disable()
            self.chkStartup.SetValue(False)
            self.chkStartup.Disable()

    def onLoadPlugin(self, evt=None):
        """Pressed the load button."""
        if self.selectedItem == -1:
            return

        pluginName = self.lstPlugins.GetItem(
            self.selectedItem, col=0).GetText()
        plugins.loadPlugin(pluginName)

        self.refreshList()

    def onRescanPlugins(self, evt=None):
        """Pressed the rescan button."""
        plugins.scanPlugins()

        self.refreshList()

    def onShowEntryPoints(self, evt=None):
        """Pressed the show entry points button."""
        if self.selectedItem == -1:
            return

        epView = EntryPointViewer(self, self.lstPlugins.GetItem(
            self.selectedItem, col=0).GetText())
        epView.ShowModal()

    def onClearStartupPlugins(self, evt=None):
        """Clear all startup plugins."""
        plugins.startUpPlugins([], add=False)
        self.startupPlugins = plugins.listPlugins('startup')
        self.refreshList()

    def onClose(self, evt=None):
        """
        Defines behavior on close of the Readme Frame
        """
        self.parent.pluginManager = None
        self.Destroy()
