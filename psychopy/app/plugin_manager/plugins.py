import wx
import webbrowser
from PIL import Image as pil

from psychopy.app.themes import theme, handlers, colors, icons
from psychopy.app import utils
from psychopy.localization import _translate
from psychopy import plugins


class PluginManagerPanel(wx.Panel, handlers.ThemeMixin):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        # Setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # Make list
        self.pluginList = PluginBrowserList(self)
        self.sizer.Add(self.pluginList, flag=wx.EXPAND | wx.ALL)
        # Seperator
        self.sizer.Add(wx.StaticLine(self, style=wx.LI_VERTICAL), border=6, flag=wx.EXPAND | wx.ALL)
        # Make viewer
        self.pluginViewer = PluginDetailsPanel(self)
        self.sizer.Add(self.pluginViewer, proportion=1, flag=wx.EXPAND | wx.ALL)
        # Cross-reference viewer & list
        self.pluginViewer.list = self.pluginList
        self.pluginList.viewer = self.pluginViewer
        # Mark installed on items now that we have necessary references
        for item in self.pluginList.allItems:
            item.markInstalled(item.info.installed)
        # Start of with nothing selected
        self.pluginList.onClick()

        self.Layout()
        self.theme = theme.app

    def _applyAppTheme(self):
        # Set colors
        self.SetBackgroundColour(colors.app['tab_bg'])


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
            self.installBtn = PluginInstallBtn(self)
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
            self.markInstalled(info.installed)
            self.activeBtn.SetValue(info.active)

            # Bind navigation
            self.Bind(wx.EVT_NAVIGATION_KEY, self.onNavigation)

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
            from psychopy.app.themes import fonts
            self.nameLbl.SetFont(fonts.appTheme['h3'].obj)
            self.pipNameLbl.SetFont(fonts.coderTheme.base.obj)
            # Set text colors
            self.nameLbl.SetForegroundColour(fg)
            self.pipNameLbl.SetForegroundColour(fg)

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
            # Mark pending
            self.markInstalled(None)
            # Install
            self.info.install()
            # Mark installed
            self.markInstalled(self.info.installed)

        def onActive(self, evt=None):
            # Activate/deactivate
            self.info.active = evt.IsChecked()

            # Continue with normal checkbox behaviour
            evt.Skip()

        def markInstalled(self, installed=True):
            """
            Shorthand to call markInstalled with self and corresponding item

            Parameters
            ----------
            installed : bool or None
                True if installed, False if not installed, None if pending/unclear
            """
            markInstalled(
                pluginItem=self,
                pluginPanel=self.parent.viewer,
                installed=installed
            )

        def onNavigation(self, evt=None):
            """
            Use the tab key to progress to the next panel, or the arrow keys to change selection in this panel.

            This is the same functionality as in a wx.ListCtrl
            """
            if evt.IsFromTab() and self.GetPrevSibling().HasFocus():
                # If navigating via tab, move on to next object
                if evt.GetDirection():
                    next = self.parent.GetNextSibling()
                else:
                    next = self.parent.GetPrevSibling()
                if hasattr(next, "SetFocus"):
                    next.SetFocus()
            else:
                # Do usual behaviour
                evt.Skip()

    def __init__(self, parent, viewer=None):
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent
        self.viewer = viewer
        # Setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # Define categories
        self.categories = {
            "curated": _translate("Curated Plugins"),
            "community": _translate("Community Plugins"),
            "unknown": _translate("Unknown Source")
        }
        # Setup items sizers & labels
        self.itemSizers = {}
        self.itemLabels = {}
        for category, label in self.categories.items():
            # Create label
            self.itemLabels[category] = wx.StaticText(self, label=label)
            self.sizer.Add(self.itemLabels[category], border=3, flag=wx.ALL | wx.EXPAND)
            # Create sizer
            self.itemSizers[category] = wx.BoxSizer(wx.VERTICAL)
            self.sizer.Add(self.itemSizers[category], border=3, flag=wx.ALL | wx.EXPAND)

        # Bind deselect
        self.Bind(wx.EVT_LEFT_DOWN, self.onClick)

        # Setup items
        self.populate()

    def populate(self):
        self.items = {category: [] for category in self.categories}
        # Get all plugin details
        items = plugins.getAllPluginDetails()
        # Put installed packages at top of list
        items.sort(key=lambda obj: obj.installed, reverse=True)
        for item in items:
            self.appendItem(item)
        # Hide any empty categories
        for category in self.items:
            shown = bool(self.items[category])
            self.itemLabels[category].Show(shown)
            self.itemSizers[category].ShowItems(shown)

    def onClick(self, evt=None):
        self.SetFocusIgnoringChildren()
        self.viewer.info = None

    def _applyAppTheme(self):
        # Set colors
        self.SetBackgroundColour(colors.app['tab_bg'])
        # Set fonts
        for lbl in self.itemLabels.values():
            from psychopy.app.themes import fonts
            lbl.SetFont(fonts.appTheme['h2'].obj)
            lbl.SetForegroundColour(colors.app['text'])

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

    @property
    def allItems(self):
        """
        Get all items as a flat list
        """
        items = []
        for val in self.items.values():
            items += val
        return items


class PluginDetailsPanel(wx.Panel, handlers.ThemeMixin):
    iconSize = (128, 128)

    def __init__(self, parent, info=None, list=None):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.list = list
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
        self.installBtn = PluginInstallBtn(self)
        self.installBtn.Bind(wx.EVT_BUTTON, self.onInstall)
        self.buttonSizer.Add(self.installBtn, border=3, flag=wx.ALL | wx.ALIGN_BOTTOM)
        self.activeBtn = wx.CheckBox(self, label=_translate("Activated"))
        self.buttonSizer.Add(self.activeBtn, border=3, flag=wx.ALL | wx.ALIGN_BOTTOM)
        # Description
        self.description = wx.TextCtrl(self, value="",
                                       style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE | wx.TE_NO_VSCROLL)
        self.sizer.Add(self.description, border=12, proportion=1, flag=wx.ALL | wx.EXPAND)

        self.sizer.Add(wx.StaticLine(self), border=6, flag=wx.EXPAND | wx.ALL)

        # Add author panel
        self.author = AuthorDetailsPanel(self, info=None)
        self.sizer.Add(self.author, border=6, flag=wx.EXPAND | wx.ALL)

        self.info = info
        self.Layout()

    def _applyAppTheme(self):
        # Set background
        self.SetBackgroundColour(colors.app['tab_bg'])
        # Set fonts
        from psychopy.app.themes import fonts
        self.title.SetFont(fonts.appTheme['h1'].obj)
        self.title.SetForegroundColour(colors.app['text'])
        self.pipName.SetFont(fonts.coderTheme.base.obj)
        self.pipName.SetForegroundColour(colors.app['text'])
        # Style description
        self.description.SetForegroundColour(colors.app['text'])
        self.description.SetBackgroundColour(colors.app['tab_bg'])

    def markInstalled(self, installed=True):
        """
        Shorthand to call markInstalled with self and corresponding item

        Parameters
        ----------
        installed : bool or None
            True if installed, False if not installed, None if pending/unclear
        """
        if self.list:
            item = self.list.getItem(self.info)
        else:
            item = None
        markInstalled(
            pluginItem=item,
            pluginPanel=self,
            installed=installed
        )

    def onInstall(self, evt=None):
        # Mark as pending
        self.markInstalled(installed=None)
        # Do install
        self.info.installed = True
        # Mark according to install success
        self.markInstalled(self.info.installed)

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
            # Resize to fit ctrl
            icon = icon.resize(size=self.iconSize)
            # Supply an alpha channel if there is one
            if "A" in icon.getbands():
                alpha = icon.tobytes("raw", "A")
            else:
                alpha = None
            icon = wx.BitmapFromBuffer(
                width=icon.size[0],
                height=icon.size[1],
                dataBuffer=icon.tobytes("raw", "RGB"),
                alphaBuffer=alpha
            )
        if not isinstance(icon, wx.Bitmap):
            icon = wx.Bitmap(icon)
        self.icon.SetBitmap(icon)
        # Set names
        self.title.SetLabelText(value.name)
        self.pipName.SetLabelText(value.pipname)
        # Set installed
        self.markInstalled(value.installed)
        # Set activated
        self.activeBtn.SetValue(value.active)
        # Set description
        self.description.SetValue(value.description)

        # Set author info
        self.author.info = value.author

        self.Layout()


class AuthorDetailsPanel(wx.Panel, handlers.ThemeMixin):
    avatarSize = (64, 64)

    def __init__(self, parent, info):
        wx.Panel.__init__(self, parent)

        # Setup sizers
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)

        # Details sizer
        self.detailsSizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.detailsSizer, proportion=1, border=6, flag=wx.LEFT | wx.EXPAND)
        # Name
        self.name = wx.StaticText(self)
        self.detailsSizer.Add(self.name, border=6, flag=wx.ALIGN_RIGHT | wx.ALL)

        # Button sizer
        self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.detailsSizer.Add(self.buttonSizer, border=3, flag=wx.ALIGN_RIGHT | wx.ALL)
        # Email button
        self.emailBtn = wx.Button(self, size=(24, 24))
        self.emailBtn.Bind(wx.EVT_BUTTON, self.onEmailBtn)
        self.buttonSizer.Add(self.emailBtn, border=3, flag=wx.EXPAND | wx.ALL)
        # GitHub button
        self.githubBtn = wx.Button(self, size=(24, 24))
        self.githubBtn.Bind(wx.EVT_BUTTON, self.onGithubBtn)
        self.buttonSizer.Add(self.githubBtn, border=3, flag=wx.EXPAND | wx.ALL)

        # Avatar
        self.avatar = wx.StaticBitmap(self, bitmap=wx.Bitmap(), size=self.avatarSize, style=wx.BORDER_NONE)
        self.sizer.Add(self.avatar, border=6, flag=wx.ALL | wx.EXPAND)

        # Set initial info
        if info is not None:
            self.info = info

        self.Layout()
        self._applyAppTheme()

    def _applyAppTheme(self):
        # Name font
        from psychopy.app.themes import fonts
        self.name.SetFont(fonts.appTheme['h4'].obj)
        # Email button bitmap
        self.emailBtn.SetBitmap(icons.ButtonIcon("email", 16).bitmap)
        self.emailBtn.SetBitmapDisabled(icons.ButtonIcon("email", 16).bitmap)
        # Github button bitmap
        self.githubBtn.SetBitmap(icons.ButtonIcon("github", 16).bitmap)
        self.githubBtn.SetBitmapDisabled(icons.ButtonIcon("github", 16).bitmap)

    @property
    def info(self):
        if hasattr(self, "_info"):
            return self._info

    @info.setter
    def info(self, value):
        # Alias None
        if value is None:
            value = plugins.AuthorInfo(
                name="..."
            )
        # Store value
        self._info = value
        # Update avatar
        icon = value.avatar
        if icon is None:
            icon = wx.Bitmap()
        if isinstance(icon, pil.Image):
            # Resize to fit ctrl
            icon = icon.resize(size=self.avatarSize)
            # Supply an alpha channel if there is one
            if "A" in icon.getbands():
                alpha = icon.tobytes("raw", "A")
            else:
                alpha = None
            icon = wx.BitmapFromBuffer(
                width=icon.size[0],
                height=icon.size[1],
                dataBuffer=icon.tobytes("raw", "RGB"),
                alphaBuffer=alpha
            )
        if not isinstance(icon, wx.Bitmap):
            icon = wx.Bitmap(icon)
        self.avatar.SetBitmap(icon)
        # Update name
        self.name.SetLabelText(value.name)
        # Show/hide buttons
        self.emailBtn.Show(bool(value.email))
        self.githubBtn.Show(bool(value.github))

    def onEmailBtn(self, evt=None):
        webbrowser.open(f"mailto:{self.info.email}")

    def onGithubBtn(self, evt=None):
        webbrowser.open(f"github.com/{self.info.github}")


class PluginInstallBtn(utils.HoverButton, handlers.ThemeMixin):
    """
    Install button for a plugin, comes with a method to update its appearance according to installation
    status & availability
    """
    def __init__(self, parent):
        # Initialise
        utils.HoverButton.__init__(
            self, parent,
            label="...",
            style=wx.BORDER_NONE | wx.BU_LEFT
        )

    def markInstalled(self, installed=True):
        """
        Mark on this button whether install has completed / is in progress / is available

        Parameters
        ----------
        installed : bool or None
            True if installed, False if not installed, None if pending/unclear
        """
        if installed is None:
            # If pending, disable and set label as ellipsis
            self.Disable()
            self.SetLabelText("...")
        elif installed:
            # If installed, disable and set label as installed
            self.Disable()
            self.SetLabelText(_translate("Installed"))
        else:
            # If not installed, enable and set label as not installed
            self.Enable()
            self.SetLabelText(_translate("Install"))

    def _applyAppTheme(self):
        # Do base method
        utils.HoverButton._applyAppTheme(self)
        # Setup icon
        self.SetBitmap(icons.ButtonIcon("download", 16).bitmap)
        self.SetBitmapDisabled(icons.ButtonIcon("greytick", 16).bitmap)
        self.SetBitmapMargins(6, 3)


def markInstalled(pluginItem, pluginPanel, installed=True):
    """
    Setup installed button according to install state

    Parameters
    ----------
    pluginItem : PluginBrowserList.PluginListItem
        Plugin list item associated with this plugin
    pluginPanel : PluginDetailsPanel
        Plugin viewer panel to update
    installed : bool or None
        True if installed, False if not installed, None if pending/unclear
    """
    # Update plugin item
    if pluginItem:
        pluginItem.installBtn.markInstalled(installed)
        pluginItem.activeBtn.Enable(bool(installed))
    # Update panel (if applicable)
    if pluginPanel and pluginItem and pluginPanel.info == pluginItem.info:
        pluginPanel.installBtn.markInstalled(installed)
        pluginPanel.activeBtn.Enable(bool(installed))


