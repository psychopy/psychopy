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
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin, CheckListCtrlMixin

from psychopy.preferences import prefs


class CustomListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin, CheckListCtrlMixin):
    """Custom ListCtrl that allows for automatic resizing of columns."""
    def __init__(self, parent, id):
        wx.ListCtrl.__init__(self,
                             parent,
                             id,
                             style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        ListCtrlAutoWidthMixin.__init__(self)
        CheckListCtrlMixin.__init__(self)


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
                           size=(1024, 460), pos=pos, style=_style)
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
        for pluginName in plugins._installed_plugins_:
            metadata = plugins.pluginMetadata(pluginName)

            # check if a plugin is enabled, but needs the session restarted
            index = self.lstPlugins.InsertItem(0, pluginName)

            if pluginName in plugins.listPlugins('startup'):
                if pluginName not in plugins._loaded_plugins_.keys():
                    self.lstPlugins.SetItemBackgroundColour(index, self.attnListCol)
                    status = 'Needs Restart'
                else:
                    self.lstPlugins.SetItemBackgroundColour(index, self.defaultListCol)
                    status = 'Ready'
            else:

                if pluginName in plugins._loaded_plugins_.keys():
                    self.lstPlugins.SetItemBackgroundColour(index, self.attnListCol)
                    status = 'Needs Restart'
                else:
                    self.lstPlugins.SetItemBackgroundColour(index, self.defaultListCol)
                    status = ''

            self.lstPlugins.CheckItem(index, pluginName in self.startupPlugins)
            self.lstPlugins.SetItem(index, 1, status)
            self.lstPlugins.SetItem(
                index, 2,
                metadata['Version'] if 'Version' in metadata.keys() else 'N/A')
            self.lstPlugins.SetItem(
                index, 3,
                metadata['Author'] if 'Author' in metadata.keys() else 'N/A')
            self.lstPlugins.SetItem(
                index, 4,
                metadata['Summary'] if 'Summary' in metadata.keys() else 'N/A')

        self.cmdEntryPoints.Disable()

    def initCtrls(self):
        """Create window controls."""
        frameSizer = wx.BoxSizer(wx.VERTICAL)
        framePanel = wx.Panel(self)
        panelSizer = wx.BoxSizer(wx.VERTICAL)

        # add some text
        lblInfo = wx.StaticText(
            framePanel,
            id=wx.ID_ANY,
            label="Mark the desired plugins to load when a PsychoPy session is "
                  "started. Highlighted items indicate that PsychoPy needs to "
                  "be restarted before the plugin can take full effect.")

        panelSizer.Add(lblInfo, flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=10)

        # add the box
        fraPlugins = wx.StaticBox(framePanel, wx.ID_ANY, "Installed Plugins")
        fraSizer = wx.StaticBoxSizer(fraPlugins, wx.HORIZONTAL)
        pnlPlugins = wx.Panel(fraPlugins)
        bsizer = wx.BoxSizer(wx.HORIZONTAL)

        # plugin list
        self.lstPlugins = CustomListCtrl(pnlPlugins, id=wx.ID_ANY)
        self.lstPlugins.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.lstPlugins.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onItemSelected)
        self.lstPlugins.OnCheckItem = self.callbackItemChecked
        self.lstPlugins.InsertColumn(0, 'Name', width=180)
        self.lstPlugins.InsertColumn(1, 'Status', wx.LIST_FORMAT_CENTER, width=100)
        self.lstPlugins.InsertColumn(2, 'Version', width=60)
        self.lstPlugins.InsertColumn(3, 'Author', width=150)
        self.lstPlugins.InsertColumn(4, 'Description', width=250)

        self.defaultListCol = self.lstPlugins.GetBackgroundColour()
        colordb = wx.ColourDatabase()
        self.attnListCol = colordb.Find('MEDIUM GOLDENROD')

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

        # display entry points button
        self.cmdEntryPoints = wx.Button(pnlPlugins, id=wx.ID_ANY,
                                        label='Entry Points ...')
        self.cmdEntryPoints.Bind(wx.EVT_BUTTON, self.onShowEntryPoints)
        self.cmdEntryPoints.SetToolTip(wx.ToolTip(
            "Display the entry points for the selected plugin."))
        buttonSizer.Add(self.cmdEntryPoints, flag=wx.EXPAND | wx.BOTTOM, border=5)

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

    def onItemSelected(self, evt=None):
        """Get the selected item."""
        self.selectedItem = self.lstPlugins.GetFirstSelected()
        if self.selectedItem != -1:
            pluginName = self.lstPlugins.GetItem(
                self.selectedItem, col=0).GetText()
            self.cmdEntryPoints.Enable()
        else:
            self.cmdEntryPoints.Disable()

    def callbackItemChecked(self, index, flag):
        """Do something when an item is checked."""
        item = self.lstPlugins.GetItem(index, col=0)
        pluginName = item.GetText()

        # check if in startup
        if not flag:
            try:
                prefs.general['startUpPlugins'].remove(pluginName)
            except ValueError:
                pass
            prefs.saveUserPrefs()
        else:
            plugins.startUpPlugins(pluginName, add=True)

        if pluginName in plugins.listPlugins('startup'):
            if pluginName not in plugins._loaded_plugins_.keys():
                self.lstPlugins.SetItemBackgroundColour(index, self.attnListCol)
                status = 'Needs Restart'
            else:
                self.lstPlugins.SetItemBackgroundColour(index, self.defaultListCol)
                status = 'Ready'
        else:

            if pluginName in plugins._loaded_plugins_.keys():
                self.lstPlugins.SetItemBackgroundColour(index, self.attnListCol)
                status = 'Needs Restart'
            else:
                self.lstPlugins.SetItemBackgroundColour(index, self.defaultListCol)
                status = ''

        self.lstPlugins.SetItem(index, 1, status)

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
        Defines behavior on close of the plugin manager
        """
        # if any items indicate a restart is needed, give a message
        for itemIdx in range(0, self.lstPlugins.GetItemCount()):
            if self.lstPlugins.GetItem(itemIdx, col=1).GetText() == "Needs Restart":
                dlg = wx.MessageDialog(
                    self, "PsychoPy must be restarted for plugin changes to take effect.",
                    caption="Information", style=wx.OK | wx.CENTRE | wx.ICON_INFORMATION)
                dlg.ShowModal()
                break

        self.parent.pluginManager = None
        self.Destroy()
