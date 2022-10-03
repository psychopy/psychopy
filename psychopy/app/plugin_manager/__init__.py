"""Plugin manager for PsychoPy GUI apps (Builder and Coder)."""

from pkg_resources import parse_version
import wx

from psychopy.app import utils
from psychopy.app.themes import handlers, colors, icons, fonts, theme

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

from psychopy import plugins
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin, CheckListCtrlMixin

from psychopy.preferences import prefs
from psychopy.localization import _translate

import os
from PIL import Image as pil


# Get a copy of startup plugins, we want to defer changes made to preferences to
# take effect after PsychoPy is shutdown. This prevents any sub-processed
# spawned by the GUI from using the plugins until a full restart.
if 'startUpPlugins' in prefs.general.keys():
    _startup_plugins_ = list(prefs.general['startUpPlugins'])
else:
    _startup_plugins_ = []

_startUpPluginsUpdated = False  # flag if plugins have been changed


class PluginManagerDlg(wx.Dialog, handlers.ThemeMixin):
    def __init__(self, parent):
        wx.Dialog.__init__(
            self, parent=parent,
            size=(1080, 720),
            style=wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE | wx.CENTER | wx.TAB_TRAVERSAL | wx.NO_BORDER
        )
        self.SetMinSize((980, 520))
        # Setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # Make list
        self.pluginList = PluginBrowserList(self)
        self.sizer.Add(self.pluginList, border=6, flag=wx.ALL | wx.EXPAND)
        # Make viewer
        self.pluginViewer = PluginDetailsPanel(self)
        self.sizer.Add(self.pluginViewer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # Start of with nothing selected
        self.pluginList.onClick()
        # Setup panel traversal
        self.focusIndex = 0
        self.Bind(wx.EVT_NAVIGATION_KEY, self.onCtrlTab)

        self.Layout()
        self.theme = theme.app

    def _applyAppTheme(self):
        # Set colors
        self.SetBackgroundColour(colors.app['frame_bg'])

    def onCtrlTab(self, evt=None):
        if not evt.IsWindowChange():
            # At dialog level, we only care about window change events
            return
        # Iterate focus index
        self.focusIndex += 1
        if self.focusIndex >= len(self.GetChildren()):
            self.focusIndex = 0
        # Get next child
        target = self.GetChildren()[self.focusIndex]
        # Focus target
        target.SetFocus()


class PluginBrowserList(wx.Panel, handlers.ThemeMixin):
    class PluginListItem(wx.Window, handlers.ThemeMixin):
        """
        Individual item pointing to a plugin
        """
        def __init__(self, parent, info):
            wx.Window.__init__(self, parent=parent, style=wx.SIMPLE_BORDER)
            self.parent = parent
            # Link info object
            self.info = info
            # Setup sizer
            self.border = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.border)
            self.sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
            # Add active checkbox
            self.activeBtn = wx.CheckBox(self)
            self.activeBtn.Bind(wx.EVT_CHECKBOX, self.onActive)
            self.sizer.Add(self.activeBtn, border=3, flag=wx.ALL | wx.EXPAND)
            # Add label
            self.label = wx.BoxSizer(wx.VERTICAL)
            self.nameLbl = wx.StaticText(self, label=info.name)
            self.label.Add(self.nameLbl, flag=wx.ALIGN_LEFT)
            self.pipNameLbl = wx.StaticText(self, label=info.pipname)
            self.label.Add(self.pipNameLbl, flag=wx.ALIGN_LEFT)
            self.sizer.Add(self.label, proportion=1, border=3, flag=wx.ALL | wx.EXPAND)
            # Add install button
            self.installBtn = utils.HoverButton(self,
                                                label=_translate("Install"),
                                                style=wx.BORDER_NONE | wx.BU_LEFT)
            self.installBtn.Bind(wx.EVT_BUTTON, self.onInstall)
            self.sizer.AddSpacer(24)
            self.sizer.Add(self.installBtn, border=3, flag=wx.ALL | wx.ALIGN_BOTTOM)

            # Map to onclick function
            self.Bind(wx.EVT_LEFT_DOWN, self.onClick)
            self.nameLbl.Bind(wx.EVT_LEFT_DOWN, self.onClick)
            self.pipNameLbl.Bind(wx.EVT_LEFT_DOWN, self.onClick)
            self.Bind(wx.EVT_SET_FOCUS, self.onFocus)
            self.Bind(wx.EVT_KILL_FOCUS, self.onFocus)

            # Set initial value
            self.installed = info.installed
            self.markInstalled(info.installed)
            self.activeBtn.SetValue(info.active)

        def _applyAppTheme(self):
            # Set colors
            if self.HasFocus():
                bg = colors.app['panel_bg']
                fg = colors.app['text']
            else:
                bg = colors.app['tab_bg']
                fg = colors.app['text']
            self.SetBackgroundColour(bg)
            self.SetForegroundColour(fg)
            # Set label fonts
            self.nameLbl.SetFont(fonts.appTheme['h3'].obj)
            self.pipNameLbl.SetFont(fonts.coderTheme.base.obj)
            # Set text colors
            self.nameLbl.SetForegroundColour(fg)
            self.pipNameLbl.SetForegroundColour(fg)
            # Style button
            self.installBtn.SetBitmap(icons.ButtonIcon("download", 16).bitmap)
            self.installBtn.SetBitmapDisabled(icons.ButtonIcon("greytick", 16).bitmap)
            self.installBtn.SetBitmapMargins(6, 3)
            self.installBtn._applyAppTheme()

            self.Update()
            self.Refresh()

        def onClick(self, evt=None):
            self.SetFocus()

        def onFocus(self, evt=None):
            if evt.GetEventType() == wx.EVT_SET_FOCUS.typeId:
                # Display info in viewer
                self.parent.viewer.info = self.info
            # Update appearance
            self._applyAppTheme()

        def onInstall(self, evt=None):
            # Mark installed
            self.installed = self.info.installed = True
            self.markInstalled(True)
            # If currently on this item's page, mark as installed there too
            if self.parent.viewer.info == self.info:
                self.parent.viewer.markInstalled(True)

        def onActive(self, evt=None):
            return

        def markInstalled(self, installed=True):
            if installed:
                # Install button disabled, active box enabled
                self.installBtn.Disable()
                self.activeBtn.Enable()
                # Update label
                self.installBtn.SetLabelText(_translate("Installed"))
            else:
                # Install button enabled, active box disabled
                self.installBtn.Enable()
                self.activeBtn.Disable()
                # Update label
                self.installBtn.SetLabelText(_translate("Install"))

    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent
        # Setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # Setup items sizers
        self.itemSizers = {
            'curated': wx.BoxSizer(wx.VERTICAL),
            'community': wx.BoxSizer(wx.VERTICAL)
        }
        self.curatedLbl = wx.StaticText(self, label=_translate("Curated Plugins"))
        self.sizer.Add(self.curatedLbl, border=3, flag=wx.ALL | wx.EXPAND)
        self.sizer.Add(self.itemSizers['curated'], border=3, flag=wx.ALL | wx.EXPAND)
        self.communityLbl = wx.StaticText(self, label=_translate("Community Plugins"))
        self.sizer.Add(self.communityLbl, border=3, flag=wx.ALL | wx.EXPAND)
        self.sizer.Add(self.itemSizers['community'], border=3, flag=wx.ALL | wx.EXPAND)
        # Bind deselect
        self.Bind(wx.EVT_LEFT_DOWN, self.onClick)

        # Setup items
        self.items = {'curated': [], 'community': []}
        self.populate()

    @property
    def viewer(self):
        # The list associated with this info panel
        return self.parent.pluginViewer

    def populate(self):
        # Get all plugin details
        items = plugins.getAllPluginDetails()
        # Put installed packages at top of list
        items.sort(key=lambda obj: obj.installed, reverse=True)
        for item in items:
            self.appendItem(item)

    def onClick(self, evt=None):
        self.SetFocusIgnoringChildren()
        self.viewer.info = None

    def _applyAppTheme(self):
        # Set colors
        self.SetBackgroundColour(colors.app['tab_bg'])
        # Set fonts
        self.curatedLbl.SetFont(fonts.appTheme['h2'].obj)
        self.curatedLbl.SetForegroundColour(colors.app['text'])
        self.communityLbl.SetFont(fonts.appTheme['h2'].obj)
        self.communityLbl.SetForegroundColour(colors.app['text'])

    def appendItem(self, info):
        item = self.PluginListItem(self, info)
        self.items[info.source].append(item)
        self.itemSizers[info.source].Add(item, border=6, flag=wx.ALL | wx.EXPAND)

    def getItem(self, info):
        """
        Get the PluginListItem object associated with a PluginInfo object
        """
        for item in self.items['curated'] + self.items['community']:
            if item.info == info:
                return item


class PluginDetailsPanel(wx.Panel, handlers.ThemeMixin):
    iconSize = (128, 128)
    def __init__(self, parent, info=None):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        # Setup sizers
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        self.headSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.headSizer, flag=wx.EXPAND)
        # Icon ctrl
        self.icon = wx.StaticBitmap(self, bitmap=wx.Bitmap(), size=self.iconSize, style=wx.SIMPLE_BORDER)
        self.headSizer.Add(self.icon, border=6, flag=wx.ALL | wx.EXPAND)
        # Title
        self.titleSizer = wx.BoxSizer(wx.VERTICAL)
        self.headSizer.Add(self.titleSizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        self.title = wx.StaticText(self, label="...")
        self.titleSizer.Add(self.title, flag=wx.EXPAND)
        # Pip name
        self.pipName = wx.StaticText(self, label="psychopy-...")
        self.titleSizer.Add(self.pipName, flag=wx.EXPAND)
        # Buttons
        self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.titleSizer.AddStretchSpacer()
        self.titleSizer.Add(self.buttonSizer, flag=wx.EXPAND)
        self.installBtn = utils.HoverButton(self,
                                            label=_translate("Install"),
                                            style=wx.BORDER_NONE | wx.BU_LEFT)
        self.installBtn.Bind(wx.EVT_BUTTON, self.onInstall)
        self.buttonSizer.Add(self.installBtn, border=3, flag=wx.ALL | wx.ALIGN_BOTTOM)
        self.activeBtn = wx.CheckBox(self, label=_translate("Activated"))
        self.buttonSizer.Add(self.activeBtn, border=3, flag=wx.ALL | wx.ALIGN_BOTTOM)
        # Description
        self.description = wx.TextCtrl(self, value="",
                                       style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE | wx.TE_NO_VSCROLL)
        self.sizer.Add(self.description, border=12, proportion=1, flag=wx.ALL | wx.EXPAND)

        self.info = info
        self.Layout()

    def _applyAppTheme(self):
        # Set background
        self.SetBackgroundColour(colors.app['tab_bg'])
        # Set fonts
        self.title.SetFont(fonts.appTheme['h1'].obj)
        self.title.SetForegroundColour(colors.app['text'])
        self.pipName.SetFont(fonts.coderTheme.base.obj)
        self.pipName.SetForegroundColour(colors.app['text'])
        # Style install button
        self.installBtn.SetBitmap(icons.ButtonIcon("download", 16).bitmap)
        self.installBtn.SetBitmapDisabled(icons.ButtonIcon("greytick", 16).bitmap)
        self.installBtn.SetBitmapMargins(6, 3)
        self.installBtn._applyAppTheme()
        # Style description
        self.description.SetForegroundColour(colors.app['text'])
        self.description.SetBackgroundColour(colors.app['tab_bg'])

    def onInstall(self, evt=None):
        # Mark installed here
        self.info.installed = True
        self.markInstalled()
        # Mark installed in list
        item = self.list.getItem(self.info)
        if item is not None:
            item.markInstalled()

    @property
    def list(self):
        # The list associated with this info panel
        return self.parent.pluginList

    @property
    def info(self):
        """
        Information about this plugin
        """
        return self._info

    @info.setter
    def info(self, value):
        self.Enable(value is not None)
        # Handle None
        if value is None:
            value = plugins.PluginInfo(
                "community", "psychopy-...",
                name="..."
            )
        self._info = value
        # Set icon
        icon = value.icon
        if icon is None:
            icon = wx.Bitmap()
        if isinstance(icon, pil.Image):
            icon = icon.resize(size=self.iconSize)
            icon = wx.BitmapFromBuffer(
                width=icon.size[0],
                height=icon.size[1],
                dataBuffer=icon.tobytes()
            )
        if not isinstance(icon, wx.Bitmap):
            icon = wx.Bitmap(icon)
        self.icon.SetBitmap(icon)
        # Set names
        self.title.SetLabelText(value.name)
        self.pipName.SetLabelText(value.pipname)
        # Set description
        self.description.SetValue(value.description)
        # Set installed
        self.markInstalled(value.installed)
        # Set activated
        self.activeBtn.SetValue(value.active)

        self.Layout()

    def markInstalled(self, installed=True):
        if installed:
            # Install button disabled, active box enabled
            self.installBtn.Disable()
            self.activeBtn.Enable()
            # Update label
            self.installBtn.SetLabelText(_translate("Installed"))
        else:
            # Install button enabled, active box disabled
            self.installBtn.Enable()
            self.activeBtn.Disable()
            # Update label
            self.installBtn.SetLabelText(_translate("Install"))

# ---

class PluginBrowserListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin, CheckListCtrlMixin):
    """Custom ListCtrl that allows for automatic resizing of columns and
    checkboxes."""
    def __init__(self, parent, id):
        wx.ListCtrl.__init__(self,
                             parent,
                             id,
                             style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        ListCtrlAutoWidthMixin.__init__(self)
        CheckListCtrlMixin.__init__(self)

        # colors for rows
        colordb = wx.ColourDatabase()
        self.defaultRowColor = self.GetBackgroundColour()
        self.attnRowColor = colordb.Find('MEDIUM GOLDENROD')
        self.failedRowColor = colordb.Find('PLUM')

        self.pluginRemovedFlag = False

        self.createColumns()

    @property
    def selectedItem(self):
        return self.GetFirstSelected()

    def updatePluginStatus(self):
        """Update the plugin status column text and set the row color if a
        restart is needed.
        """
        for itemIdx in range(0, self.GetItemCount()):
            pluginName = self.GetItem(itemIdx, col=0).GetText()

            # deal with failed plugins
            if pluginName in plugins._failed_plugins_:
                if pluginName in _startup_plugins_:
                    self.SetItemBackgroundColour(
                        itemIdx, self.failedRowColor)
                    self.SetItem(itemIdx, 1, 'Failed')
                else:
                    self.SetItemBackgroundColour(
                        itemIdx, self.attnRowColor)
                    self.SetItem(itemIdx, 1, 'Needs Restart')

                continue

            if pluginName in _startup_plugins_:
                if not plugins.isPluginLoaded(pluginName):
                    self.SetItemBackgroundColour(
                        itemIdx, self.attnRowColor)
                    status = 'Needs Restart'
                else:
                    self.SetItemBackgroundColour(
                        itemIdx, self.defaultRowColor)
                    status = 'Ready'
            else:
                if plugins.isPluginLoaded(pluginName):
                    self.SetItemBackgroundColour(
                        itemIdx, self.attnRowColor)
                    status = 'Needs Restart'
                else:
                    self.SetItemBackgroundColour(
                        itemIdx, self.defaultRowColor)
                    status = ''

            self.SetItem(itemIdx, 1, status)


    def createColumns(self):
        """Create columns for this widget."""
        self.InsertColumn(0, 'Name', width=180)
        self.InsertColumn(1, 'Status', wx.LIST_FORMAT_CENTER, width=100)
        self.InsertColumn(2, 'Version', width=60)
        self.InsertColumn(3, 'Author', width=150)
        self.InsertColumn(4, 'Description', width=250)

    def refreshList(self):
        """Refresh the plugin list.
        """
        global _startup_plugins_
        self.DeleteAllItems()  # clear existing items

        # populate the list with installed plugins
        plugins.scanPlugins()
        allPlugins = plugins.listPlugins(which='all')

        # check if there are startup plugins that have been uninstalled during
        # the session
        for pluginName in _startup_plugins_:
            if pluginName not in allPlugins:
                # show the warning
                dlg = wx.MessageDialog(
                    self,
                    "Startup plugin `{}` cannot be found on the system! It "
                    "will be removed from startup plugins.".format(pluginName),
                    caption="Warning",
                    style=wx.OK | wx.CENTRE | wx.ICON_WARNING)
                dlg.ShowModal()

                # remove the startup plugin entry
                try:
                    _startup_plugins_.remove(pluginName)
                except KeyError:
                    pass

                self.pluginRemovedFlag = True

        # populate the list with installed plugins
        for pluginName in allPlugins:
            # get the metadata from the plugin to display
            metadata = plugins.pluginMetadata(pluginName)
            index = self.InsertItem(0, pluginName)

            # put a checkmark on the plugin if loaded
            self.CheckItem(index, pluginName in _startup_plugins_)
            self.SetItem(
                index, 2,
                metadata['Version'] if 'Version' in metadata.keys() else 'N/A')
            self.SetItem(
                index, 3,
                metadata['Author'] if 'Author' in metadata.keys() else 'N/A')
            self.SetItem(
                index, 4,
                metadata['Summary'] if 'Summary' in metadata.keys() else 'N/A')

        self.updatePluginStatus()

    def OnCheckItem(self, index, flag):
        """Do something when an item is checked."""
        item = self.GetItem(index, col=0)
        pluginName = item.GetText()
        global _startup_plugins_
        # check if in startup
        if not flag:
            try:
                _startup_plugins_.remove(pluginName)
            except ValueError:
                pass
        else:
            if pluginName not in _startup_plugins_:
                _startup_plugins_.append(pluginName)

        self.updatePluginStatus()

    def needsRestart(self):
        """Check if there are any items with status indicating a restart is
        needed."""
        self.refreshList()
        if self.pluginRemovedFlag:
            return True

        # if any items indicate a restart is needed, give a message
        for itemIdx in range(0, self.GetItemCount()):
            if self.GetItem(itemIdx, col=1).GetText() == "Needs Restart":
                return True

        return False

    def updateStartUpPluginsList(self):
        """Update the list of startup plugins based on what has been checked
        off in the list."""
        global _startup_plugins_

        # clear the startup plugins, only use the one from the manager
        _startup_plugins_ = []

        for itemIdx in range(0, self.GetItemCount()):
            if self.IsChecked(itemIdx):
                pluginName = self.GetItem(itemIdx, col=0).GetText()
                _startup_plugins_.append(pluginName)


class EntryPointListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
    """Custom ListCtrl that allows for automatic resizing of columns and
    checkboxes."""
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
                           size=(640, 380), pos=pos,
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
            "Entry points advertised by plugin `{}`".format(self.pluginName))
        fraSizer = wx.StaticBoxSizer(fraEntryPoints, wx.HORIZONTAL)

        lstEntryPoints = EntryPointListCtrl(fraEntryPoints, id=wx.ID_ANY)
        lstEntryPoints.InsertColumn(0, 'Group', width=200)
        lstEntryPoints.InsertColumn(1, 'Attribute', width=100)
        lstEntryPoints.InsertColumn(2, 'Entry Point', width=200)

        # populate the tree control
        entryPointMap = plugins.pluginEntryPoints(self.pluginName, parse=True)
        for group, entryPoints in entryPointMap.items():
            for attr, val in entryPoints.items():
                index = lstEntryPoints.InsertItem(0, group)
                lstEntryPoints.SetItem(index, 0, group)
                lstEntryPoints.SetItem(index, 1, attr)
                lstEntryPoints.SetItem(index, 2, val)

        fraSizer.Add(
            lstEntryPoints,
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM,
            border=5,
            proportion=1)

        # panel for dialog buttons
        pnlDialogCtrls = wx.Panel(framePanel)
        pnlDialogCtrlsSizer = wx.FlexGridSizer(1, 1, 10, 10)
        pnlDialogCtrls.SetSizer(pnlDialogCtrlsSizer)

        # load selected plugin button
        self.cmdClose = wx.Button(pnlDialogCtrls, id=wx.ID_ANY, label='Close')
        self.cmdClose.Bind(wx.EVT_BUTTON, self.onClose)
        pnlDialogCtrlsSizer.Add(self.cmdClose, 0, 0)

        # add the panel to the frame sizer
        framePanelSizer.Add(
            fraSizer,
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM,
            border=10,
            proportion=1)

        framePanelSizer.Add(
            pnlDialogCtrls,
            flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT,
            border=10)

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
        title = "Plugins"
        pos = wx.Point(parent.Position[0] + 80, parent.Position[1] + 80)
        _style = wx.DEFAULT_DIALOG_STYLE | wx.FRAME_FLOAT_ON_PARENT | wx.RESIZE_BORDER
        wx.Dialog.__init__(self, parent, title=title,
                           size=(1024, 480), pos=pos, style=_style)
        self.Bind(wx.EVT_CLOSE, self.onClose)

        self.initCtrls()
        self.lstPlugins.refreshList()
        self.cmdEntryPoints.Disable()

    def initCtrls(self):
        """Create window controls."""
        frameSizer = wx.BoxSizer(wx.VERTICAL)
        framePanel = wx.Panel(self)
        panelSizer = wx.BoxSizer(wx.VERTICAL)

        pnlDialogHeader = wx.Panel(framePanel)
        pnlDialogHeaderSizer = wx.BoxSizer(wx.HORIZONTAL)

        # this should be cached ...
        PNG = wx.BITMAP_TYPE_PNG
        rc = prefs.paths['resources']
        pluginBMP = wx.Bitmap(os.path.join(rc, 'plugins32.png'), PNG)
        pluginGraphic = wx.StaticBitmap(
            pnlDialogHeader, wx.ID_ANY, pluginBMP, (0, 0), (32, 32))

        # add some text
        lblInfo = wx.StaticText(
            pnlDialogHeader,
            id=wx.ID_ANY,
            label="Plugins are third-party packages used to extend PsychoPy. "
                  "Indicate below which plugins should be loaded when a "
                  "PsychoPy session starts.")

        pnlDialogHeaderSizer.Add(pluginGraphic, flag=wx.ALIGN_CENTRE_VERTICAL)
        pnlDialogHeaderSizer.Add(
            lblInfo, flag=wx.ALIGN_CENTRE_VERTICAL | wx.LEFT, border=10)

        pnlDialogHeader.SetSizer(pnlDialogHeaderSizer)
        panelSizer.Add(
            pnlDialogHeader,
            flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT,
            border=10)

        # add the box
        fraPlugins = wx.StaticBox(framePanel, wx.ID_ANY, "Available Plugins")
        fraSizer = wx.StaticBoxSizer(fraPlugins, wx.HORIZONTAL)
        pnlPlugins = wx.Panel(fraPlugins)
        bsizer = wx.BoxSizer(wx.HORIZONTAL)

        # plugin list
        self.lstPlugins = PluginBrowserListCtrl(pnlPlugins, id=wx.ID_ANY)
        self.lstPlugins.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.lstPlugins.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onItemSelected)

        bsizer.Add(self.lstPlugins, flag=wx.EXPAND | wx.ALL, proportion=1)
        fraSizer.Add(pnlPlugins, flag=wx.EXPAND | wx.ALL, proportion=1, border=5)

        # plugin buttons
        buttonSizer = wx.BoxSizer(wx.VERTICAL)

        # rescan plugins button
        self.cmdScanPlugin = wx.Button(pnlPlugins, id=wx.ID_ANY, label='Rescan')
        self.cmdScanPlugin.Bind(wx.EVT_BUTTON, self.onRescanPlugins)
        self.cmdScanPlugin.SetToolTip(wx.ToolTip(
            "Rescan installed packages for PsychoPy plugins."))
        buttonSizer.Add(
            self.cmdScanPlugin,
            flag=wx.EXPAND | wx.BOTTOM,
            border=5)

        # display entry points button
        self.cmdEntryPoints = wx.Button(pnlPlugins, id=wx.ID_ANY,
                                        label='Entry Points ...')
        self.cmdEntryPoints.Bind(wx.EVT_BUTTON, self.onShowEntryPoints)
        self.cmdEntryPoints.SetToolTip(wx.ToolTip(
            "Display the entry points for the selected plugin."))
        buttonSizer.Add(
            self.cmdEntryPoints,
            flag=wx.EXPAND | wx.BOTTOM,
            border=5)

        bsizer.Add(buttonSizer, flag=wx.EXPAND | wx.BOTTOM | wx.LEFT, border=5)
        pnlPlugins.SetSizer(bsizer)

        # panel for dialog buttons
        pnlDialogCtrls = wx.Panel(framePanel)
        pnlDialogCtrlsSizer = wx.FlexGridSizer(1, 2, 10, 10)
        pnlDialogCtrls.SetSizer(pnlDialogCtrlsSizer)

        # disable all startup plugins button
        self.cmdDisableAll = wx.Button(
            pnlDialogCtrls,
            id=wx.ID_ANY,
            label='Clear startup plugins')
        self.cmdDisableAll.Bind(wx.EVT_BUTTON, self.onClearStartupPlugins)
        self.cmdDisableAll.SetToolTip(wx.ToolTip(
            "Clear all plugins registered to load on startup."))
        pnlDialogCtrlsSizer.Add(self.cmdDisableAll, 0, 0)

        # load selected plugin button
        self.cmdClose = wx.Button(pnlDialogCtrls, id=wx.ID_ANY, label='Close')
        self.cmdClose.Bind(wx.EVT_BUTTON, self.onClose)
        pnlDialogCtrlsSizer.Add(self.cmdClose, 0, 0)

        # add the panel to the frame sizer
        panelSizer.Add(
            fraSizer,
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM,
            border=10,
            proportion=1)
        panelSizer.Add(
            pnlDialogCtrls,
            flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT,
            border=10)
        framePanel.SetSizer(panelSizer)
        frameSizer.Add(framePanel, flag=wx.EXPAND | wx.ALL, proportion=1)
        self.SetSizer(frameSizer)

    def onRescanPlugins(self, evt=None):
        """Event handler for when the rescan button is pressed."""
        self.cmdEntryPoints.Disable()
        self.lstPlugins.refreshList()

    def onShowEntryPoints(self, evt=None):
        """Event for when the entry points of a selected plugin are
        requested."""
        selectedItem = self.lstPlugins.selectedItem
        if selectedItem == -1:
            return

        # show the entry point dialog
        epView = EntryPointViewer(self, self.lstPlugins.GetItem(
            selectedItem, col=0).GetText())
        epView.ShowModal()

    def onClearStartupPlugins(self, evt=None):
        """Clear all startup plugins."""
        global _startup_plugins_
        _startup_plugins_ = []
        self.lstPlugins.refreshList()

    def onItemSelected(self, evt=None):
        """Event handler for when an item is selected."""
        self.selectedItem = self.lstPlugins.GetFirstSelected()
        if self.lstPlugins.selectedItem != -1:
            self.cmdEntryPoints.Enable()
        else:
            self.cmdEntryPoints.Disable()

    def onClose(self, evt=None):
        """Called when the plugin manager is closed.
        """
        global _startUpPluginsUpdated
        _startUpPluginsUpdated = self.lstPlugins.needsRestart()

        # warn if there are any plugins that need a restart
        if _startUpPluginsUpdated:
            dlg = wx.MessageDialog(
                self,
                "PsychoPy must be restarted for plugin changes to take effect.",
                caption="Information",
                style=wx.OK | wx.CENTRE | wx.ICON_INFORMATION)
            dlg.ShowModal()

            # Update the startup plugins based off what has been given in the
            # list. Only do this if the user made any changes.
            self.lstPlugins.updateStartUpPluginsList()

        self.parent.pluginManager = None
        self.Destroy()


def saveStartUpPluginsConfig():
    """Write startup plugins to the user config. This will only write to the
    config file if there have been changes to the plugin configuration over the
    course of the current session.

    """
    if _startUpPluginsUpdated:
        prefs.general['startUpPlugins'] = _startup_plugins_
        prefs.saveUserPrefs()
