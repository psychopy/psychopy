import wx
from wx.lib import scrolledpanel
import webbrowser
from PIL import Image as pil

from psychopy.tools import pkgtools
from psychopy.app.themes import theme, handlers, colors, icons
from psychopy.tools import stringtools as st
from psychopy.tools.versionchooser import VersionRange
from psychopy.app import utils
from psychopy.localization import _translate
from psychopy import plugins, __version__
from psychopy.preferences import prefs
import requests
import os.path
import errno
import sys
import json
import glob


class AuthorInfo:
    """Plugin author information.

    Parameters
    ----------
    name : str
        Author name.
    email : str
        Author email URL.
    github : str
        GitHub repo URL (optional).
    avatar : str
        Avatar image file or URL.

    """
    def __init__(self,
                 name="",
                 email="",
                 github="",
                 avatar=None,
                 **kwargs):
        self.name = name
        self.email = email
        self.github = github
        self.avatar = avatar

    def __eq__(self, other):
        if other == "ost":
            # If author is us, check against our github
            return self.github == "psychopy"
        else:
            # Otherwise check against string attributes
            return other in (self.name, self.email, self.github)

    @property
    def avatar(self):
        if hasattr(self, "_avatar"):
            return self._avatar

    @avatar.setter
    def avatar(self, value):
        self._requestedAvatar = value
        self._avatar = utils.ImageData(value)

    def __repr__(self):
        return (f"<psychopy.app.plugins.AuthorInfo: "
                f"{self.name} (@{self.github}, {self.email})>")


class PluginInfo:
    """Minimal class to store info about a plugin.

    Parameters
    ----------
    pipname : str
        Name of plugin on pip, e.g. "psychopy-legacy".
    name : str
        Plugin name for display, e.g. "Psychopy Legacy".
    icon : wx.Bitmap, path or None
        Icon for the plugin, if any (if None, will use blank bitmap).
    description : str
        Description of the plugin.
    installed : bool or None
        Whether or not the plugin in installed on this system.
    active : bool
        Whether or not the plug is enabled on this system (if not installed,
        will always be False).

    """

    def __init__(self,
                 pipname, name="",
                 author=None, homepage="", docs="", repo="",
                 keywords=None, version=(None, None),
                 icon=None, description="", **kwargs):
        self.pipname = pipname
        self.name = name
        self.author = author
        self.homepage = homepage
        self.docs = docs
        self.repo = repo
        self.icon = icon
        self.description = description
        self.keywords = keywords or []
        self.version = VersionRange(*version)

        self.parent = None   # set after

        # icon graphic
        self._icon = None

    def __repr__(self):
        return (f"<psychopy.plugins.PluginInfo: {self.name} "
                f"[{self.pipname}] by {self.author}>")

    def __eq__(self, other):
        if isinstance(other, PluginInfo):
            return self.pipname == other.pipname
        else:
            return self.pipname == str(other)

    def setParent(self, parent):
        """Set the parent window or panel.

        Need a parent to invoke methods on the top-level window. Might not
        be set.

        Parameters
        ----------
        parent : wx.Window or wx.Panel
            Parent window or panel.

        """
        self.parent = parent

    @property
    def icon(self):
        # check if the directory for the plugin cache exists, create it otherwise
        appPluginCacheDir = os.path.join(
            prefs.paths['userCacheDir'], 'appCache', 'plugins')
        try:
            os.makedirs(appPluginCacheDir, exist_ok=True)
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise

        if isinstance(self._requestedIcon, str):
            if st.is_url(self._requestedIcon):
                # get the file name from the URL in the JSON
                fname = str(self._requestedIcon).split("/")
                if len(fname) > 1:
                    fname = fname[-1]
                else:
                    pass  # not a valid URL, use broken image icon

                # check if the icon is already in the cache, use it if so
                if fname in os.listdir(appPluginCacheDir):
                    self._icon = utils.ImageData(os.path.join(
                        appPluginCacheDir, fname))
                    return self._icon
                
                # if not, download it
                if st.is_url(self._requestedIcon):
                    # download to cache directory
                    ext = "." + str(self._requestedIcon).split(".")[-1]
                    if ext in pil.registered_extensions():
                        content = requests.get(self._requestedIcon).content
                        writeOut = os.path.join(appPluginCacheDir, fname)
                        with open(writeOut, 'wb') as f:
                            f.write(content)
                        self._icon = utils.ImageData(os.path.join(
                            appPluginCacheDir, fname))

            elif st.is_file(self._requestedIcon):
                self._icon = utils.ImageData(self._requestedIcon) 
            else:
                raise ValueError("Invalid icon URL or file path.")
            
            return self._icon
        
        # icon already loaded into memory, just return that
        if hasattr(self, "_icon"):
            return self._icon

    @icon.setter
    def icon(self, value):
        self._requestedIcon = value

    @property
    def active(self):
        """
        Is this plugin active? If so, it is loaded when the app starts.
        Otherwise, it remains installed but is not loaded.
        """
        return plugins.isStartUpPlugin(self.pipname)

    def activate(self, evt=None):
        # If active, add to list of startup plugins
        plugins.startUpPlugins(self.pipname, add=True, verify=False)

    def deactivate(self, evt=None):
        # Remove from list of startup plugins
        current = plugins.listPlugins(which='startup')
        if self.pipname in current:
            current.remove(self.pipname)
        plugins.startUpPlugins(current, add=False, verify=False)

    def install(self):
        if self.parent is None:
            return

        wx.CallAfter(
            self.parent.GetTopLevelParent().installPlugin, self)

    def uninstall(self):
        if self.parent is None:
            return

        wx.CallAfter(
            self.parent.GetTopLevelParent().uninstallPackage, self.pipname)

    @property
    def installed(self):
        return pkgtools.isInstalled(self.pipname)

    @property
    def author(self):
        if hasattr(self, "_author"):
            return self._author

    @author.setter
    def author(self, value):
        if isinstance(value, AuthorInfo):
            # If given an AuthorInfo, use it directly
            self._author = value
        elif isinstance(value, dict):
            # If given a dict, make an AuthorInfo from it
            self._author = AuthorInfo(**value)
        else:
            # Otherwise, assume no author
            self._author = AuthorInfo()


class PluginManagerPanel(wx.Panel, handlers.ThemeMixin):
    def __init__(self, parent, dlg):
        wx.Panel.__init__(self, parent, style=wx.NO_BORDER)
        self.dlg = dlg
        # Setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # Make splitter
        self.splitter = wx.SplitterWindow(self, style=wx.NO_BORDER)
        self.sizer.Add(self.splitter, proportion=1, border=0, flag=wx.EXPAND | wx.ALL)
        # Make list
        self.pluginList = PluginBrowserList(self.splitter, stream=dlg.output)
        # Make viewer
        self.pluginViewer = PluginDetailsPanel(self.splitter, stream=self.dlg.output)
        # Cross-reference viewer & list
        self.pluginViewer.list = self.pluginList
        self.pluginList.viewer = self.pluginViewer
        # Assign to splitter
        self.splitter.SplitVertically(
            window1=self.pluginList,
            window2=self.pluginViewer,
            sashPosition=0
        )
        self.splitter.SetMinimumPaneSize(450)

        # Start of with nothing selected
        self.pluginList.onDeselect()

        self.Layout()
        self.splitter.SetSashPosition(1, True)
        self.theme = theme.app

    def _applyAppTheme(self):
        # Set colors
        self.SetBackgroundColour("white")
        # Manually style children as Splitter interfered with inheritance
        self.pluginList.theme = self.theme
        self.pluginViewer.theme = self.theme


class PluginBrowserList(scrolledpanel.ScrolledPanel, handlers.ThemeMixin):
    class PluginListItem(wx.Window, handlers.ThemeMixin):
        """
        Individual item pointing to a plugin
        """
        def __init__(self, parent, info):
            wx.Window.__init__(self, parent=parent, style=wx.SIMPLE_BORDER)
            self.SetMaxSize((400, -1))
            self.parent = parent
            # Link info object
            self.info = info
            # Setup sizer
            self.border = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.border)
            self.sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
            # Add label
            self.label = wx.BoxSizer(wx.VERTICAL)
            self.nameLbl = wx.StaticText(self, label=info.name)
            self.label.Add(self.nameLbl, flag=wx.ALIGN_LEFT)
            self.pipNameLbl = wx.StaticText(self, label=info.pipname)
            self.label.Add(self.pipNameLbl, flag=wx.ALIGN_LEFT)
            self.sizer.Add(self.label, proportion=1, border=3, flag=wx.ALL | wx.EXPAND)
            # Button sizer
            self.btnSizer = wx.BoxSizer(wx.VERTICAL)
            self.sizer.Add(self.btnSizer, border=3, flag=wx.ALL | wx.ALIGN_BOTTOM)
            self.btnSizer.AddStretchSpacer(1)
            # # Add active button
            # self.activeBtn = wx.Button(self)
            # self.activeBtn.Bind(wx.EVT_BUTTON, self.onToggleActivate)
            # self.btnSizer.Add(self.activeBtn, border=3, flag=wx.ALL | wx.ALIGN_RIGHT)
            # Add install button
            self.installBtn = wx.Button(self)
            self.installBtn.Bind(wx.EVT_BUTTON, self.onInstall)
            self.btnSizer.Add(self.installBtn, border=3, flag=wx.ALL | wx.ALIGN_RIGHT)

            # Map to onclick function
            self.Bind(wx.EVT_LEFT_DOWN, self.onSelect)
            self.nameLbl.Bind(wx.EVT_LEFT_DOWN, self.onSelect)
            self.pipNameLbl.Bind(wx.EVT_LEFT_DOWN, self.onSelect)
            # Bind navigation
            self.Bind(wx.EVT_NAVIGATION_KEY, self.onNavigation)

            # Handle version mismatch
            self.installBtn.Enable(__version__ in self.info.version)

            self._applyAppTheme()

        @property
        def viewer(self):
            """
            Return parent's linked viewer when asked for viewer
            """
            return self.parent.viewer

        def _applyAppTheme(self):
            # Set label fonts
            from psychopy.app.themes import fonts
            self.nameLbl.SetFont(fonts.appTheme['h6'].obj)
            self.pipNameLbl.SetFont(fonts.coderTheme.base.obj)
            # Mark installed/active
            self.markInstalled(self.info.installed)
            #self.markActive(self.info.active)

        def onNavigation(self, evt=None):
            """
            Use the tab key to progress to the next panel, or the arrow keys to
            change selection in this panel.

            This is the same functionality as in a wx.ListCtrl
            """
            # Some shorthands for prev, next and whether each have focus
            prev = self.GetPrevSibling()
            prevFocus = False
            if hasattr(prev, "HasFocus"):
                prevFocus = prev.HasFocus()
            next = self.GetNextSibling()
            nextFocus = False
            if hasattr(next, "HasFocus"):
                nextFocus = next.HasFocus()

            if evt.GetDirection() and prevFocus:
                # If moving forwards from previous sibling, target is self
                target = self
            elif evt.GetDirection() and self.HasFocus():
                # If moving forwards from self, target is next sibling
                target = next
            elif evt.GetDirection():
                # If we're moving forwards from anything else, this event shouldn't have happened. Just deselect.
                target = None
            elif not evt.GetDirection() and nextFocus:
                # If moving backwards from next sibling, target is self
                target = self
            elif not evt.GetDirection() and self.HasFocus():
                # If moving backwards from self, target is prev sibling
                target = prev
            else:
                # If we're moving backwards from anything else, this event shouldn't have happened. Just deselect.
                target = None

            # If target is self or another PluginListItem, select it
            if target in self.parent.items:
                self.parent.setSelection(target)
                target.SetFocus()
            else:
                self.parent.setSelection(None)

            # Do usual behaviour
            evt.Skip()

        def onSelect(self, evt=None):
            self.parent.setSelection(self)

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

        def markActive(self, active=True):
            """
            Shorthand to call markActive with self and corresponding item

            Parameters
            ----------
            active : bool or None
                True if active, False if not active, None if pending/unclear
            """
            markActive(
                pluginItem=self,
                pluginPanel=self.parent.viewer,
                active=active
            )

        def onInstall(self, evt=None):
            # Mark as pending
            self.markInstalled(None)
            # Do install
            self.info.install()
            # Mark according to install success
            self.markInstalled(self.info.installed)

        def onToggleActivate(self, evt=None):
            if self.info.active:
                self.onDeactivate(evt=evt)
            else:
                self.onActivate(evt=evt)

        def onActivate(self, evt=None):
            # Mark as pending
            self.markActive(None)
            # Do activation
            self.info.activate()
            # Mark according to success
            self.markActive(self.info.active)

        def onDeactivate(self, evt=None):
            # Mark as pending
            self.markActive(None)
            # Do deactivation
            self.info.deactivate()
            # Mark according to success
            self.markActive(self.info.active)


    def __init__(self, parent, stream, viewer=None):
        scrolledpanel.ScrolledPanel.__init__(self, parent=parent, style=wx.VSCROLL)
        self.parent = parent
        self.viewer = viewer
        self.stream = stream
        # Setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # Add search box
        self.searchCtrl = wx.SearchCtrl(self)
        self.sizer.Add(self.searchCtrl, border=9, flag=wx.ALL | wx.EXPAND)
        self.searchCtrl.Bind(wx.EVT_SEARCH, self.search)
        # Setup items sizers & labels
        self.itemSizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.itemSizer, proportion=1, border=3, flag=wx.ALL | wx.EXPAND)
        self.badItemLbl = wx.StaticText(self, label=_translate("Not for PsychoPy {}:").format(__version__))
        self.sizer.Add(self.badItemLbl, border=9, flag=wx.ALL | wx.EXPAND)
        self.badItemSizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.badItemSizer, border=3, flag=wx.ALL | wx.EXPAND)

        # Bind deselect
        self.Bind(wx.EVT_LEFT_DOWN, self.onDeselect)

        # Setup items
        self.items = []
        self.populate()
        # Store state of plugins on init so we can detect changes later
        self.initState = {}
        for item in self.items:
            self.initState[item.info.pipname] = {"installed": item.info.installed, "active": item.info.active}

    def populate(self):
        # Get all plugin details
        items = getAllPluginDetails()
        # Start off assuming no headings
        self.badItemLbl.Hide()
        # Put installed packages at top of list
        items.sort(key=lambda obj: obj.installed, reverse=True)
        for item in items:
            item.setParent(self)
            self.appendItem(item)

        # Layout
        self.Layout()
        self.SetupScrolling()

    def search(self, evt=None):
        searchTerm = self.searchCtrl.GetValue().strip()
        for item in self.items:
            # Otherwise show/hide according to search
            match = any((
                searchTerm == "",  # If search is blank, show all
                searchTerm.lower() in item.info.name.lower(),
                searchTerm.lower() in item.info.pipname.lower(),
                searchTerm.lower() in [val.lower() for val in item.info.keywords],
                searchTerm.lower() in item.info.author.name.lower(),
            ))
            item.Show(match)

        self.Layout()

    def getChanges(self):
        """
        Check what plugins have changed state (installed, active) since this dialog was opened
        """
        changes = {}
        for item in self.items:
            info = item.info
            # Skip if its init state wasn't stored
            if info.pipname not in self.initState:
                continue
            # Get inits
            inits = self.initState[info.pipname]

            itemChanges = []
            # Has it been activated?
            if info.active and not inits['active']:
                itemChanges.append("activated")
            # Has it been deactivated?
            if inits['active'] and not info.active:
                itemChanges.append("deactivated")
            # Has it been installed?
            if info.installed and not inits['installed']:
                itemChanges.append("installed")
            # Has it been uninstalled?
            if inits['installed'] and not info.installed:
                itemChanges.append("uninstalled")

            # Add changes if there are any
            if itemChanges:
                changes[info.pipname] = itemChanges

        return changes

    def onClick(self, evt=None):
        self.SetFocusIgnoringChildren()
        self.viewer.info = None

    def setSelection(self, item):
        """
        Set the current selection as either None or the handle of a PluginListItem
        """
        if item is None:
            # If None, set to no selection
            self.selected = None
            self.viewer.info = None
        elif isinstance(item, self.PluginListItem):
            # If given a valid item, select it
            self.selected = item
            self.viewer.info = item.info
        # Style all items
        for obj in self.items:
            if obj == self.selected:
                # Selected colors
                bg = colors.app.light['panel_bg']
            else:
                # Deselected colors
                bg = colors.app.light['tab_bg']
            # Set color
            obj.SetBackgroundColour(bg)
            # Restyle item
            obj._applyAppTheme()
            # Refresh
            obj.Update()
            obj.Refresh()

        # Post CHOICE event
        evt = wx.CommandEvent(wx.EVT_CHOICE.typeId)
        evt.SetEventObject(self)
        evt.SetClientData(item)
        wx.PostEvent(self, evt)

    def onDeselect(self, evt=None):
        """
        If panel itself (not any children) are clicked on, set selection to None
        """
        self.setSelection(None)

    def _applyAppTheme(self):
        # Set colors
        self.SetBackgroundColour("white")
        # Style heading(s)
        from psychopy.app.themes import fonts
        self.badItemLbl.SetFont(fonts.appTheme['h6'].obj)

    def appendItem(self, info):
        item = self.PluginListItem(self, info)
        self.items.append(item)
        if __version__ in item.info.version:
            self.itemSizer.Add(item, border=6, flag=wx.ALL | wx.EXPAND)
        else:
            self.badItemSizer.Add(item, border=6, flag=wx.ALL | wx.EXPAND)
            self.badItemLbl.Show()

    def getItem(self, info):
        """
        Get the PluginListItem object associated with a PluginInfo object
        """
        for item in self.items:
            if item.info == info:
                return item


class PluginDetailsPanel(wx.Panel, handlers.ThemeMixin):
    iconSize = (128, 128)

    def __init__(self, parent, stream, info=None, list=None):
        wx.Panel.__init__(self, parent)
        self.SetMinSize((480, 620))
        self.parent = parent
        self.list = list
        self.stream = stream
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
        # Space
        self.titleSizer.AddStretchSpacer()
        # Versions
        self.versionCtrl = wx.StaticText(self, label=_translate("Version:"))
        self.titleSizer.Add(self.versionCtrl, border=6, flag=wx.TOP | wx.LEFT | wx.RIGHT | wx.EXPAND)
        # Buttons
        self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.titleSizer.Add(self.buttonSizer, flag=wx.EXPAND)
        # Install btn
        self.installBtn = wx.Button(self)
        self.installBtn.Bind(wx.EVT_BUTTON, self.onInstall)
        self.buttonSizer.Add(self.installBtn, border=3, flag=wx.ALL | wx.EXPAND)
        # Active btn
        # self.activeBtn = wx.Button(self)
        # self.activeBtn.Bind(wx.EVT_BUTTON, self.onToggleActivate)
        # self.buttonSizer.Add(self.activeBtn, border=3, flag=wx.ALL | wx.EXPAND)
        # Homepage btn
        self.homepageBtn = wx.Button(self, label=_translate("Homepage"))
        self.homepageBtn.Bind(wx.EVT_BUTTON, self.onHomepage)
        self.buttonSizer.Add(self.homepageBtn, border=3, flag=wx.ALL | wx.EXPAND)
        # Description
        self.description = utils.MarkdownCtrl(
            self, value="",
            style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE | wx.TE_NO_VSCROLL
        )
        self.sizer.Add(self.description, border=0, proportion=1, flag=wx.ALL | wx.EXPAND)
        # Keywords
        self.keywordsLbl = wx.StaticText(self, label=_translate("Keywords:"))
        self.sizer.Add(self.keywordsLbl, border=12, flag=wx.TOP | wx.LEFT | wx.RIGHT | wx.EXPAND)
        self.keywordsCtrl = utils.ButtonArray(
            self,
            orient=wx.HORIZONTAL,
            itemAlias=_translate("keyword"),
            readonly=True
        )
        self.keywordsCtrl.Bind(wx.EVT_BUTTON, self.onKeyword)
        self.sizer.Add(self.keywordsCtrl, border=6, flag=wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.EXPAND)

        self.sizer.Add(wx.StaticLine(self), border=6, flag=wx.EXPAND | wx.ALL)

        # Add author panel
        self.author = AuthorDetailsPanel(self, info=None)
        self.sizer.Add(self.author, border=6, flag=wx.EXPAND | wx.ALL)

        # Add placeholder for when there's no plugin selected
        self.placeholder = utils.MarkdownCtrl(
            self, value=_translate("Select a plugin to view details."),
            style=wx.TE_MULTILINE | wx.BORDER_NONE | wx.TE_NO_VSCROLL
        )
        self.border.Add(
            self.placeholder,
            proportion=1,
            border=12,
            flag=wx.ALL | wx.EXPAND)

        # Set info and installed status
        self.info = info
        self.markInstalled(self.info.installed)
        #self.markActive(self.info.active)
        # Style
        self.Layout()
        self._applyAppTheme()

    def _applyAppTheme(self):
        # Set background
        self.SetBackgroundColour("white")
        self.keywordsCtrl.SetBackgroundColour("white")
        self.versionCtrl.SetForegroundColour("grey")
        # Set fonts
        from psychopy.app.themes import fonts
        self.title.SetFont(fonts.appTheme['h1'].obj)
        self.pipName.SetFont(fonts.coderTheme.base.obj)

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

    def markActive(self, active=True):
        """
        Shorthand to call markActive with self and corresponding item

        Parameters
        ----------
        active : bool or None
            True if active, False if not active, None if pending/unclear
        """
        if self.list:
            item = self.list.getItem(self.info)
        else:
            item = None
        markActive(
            pluginItem=item,
            pluginPanel=self,
            active=active
        )

    def _doInstall(self):
        """Routine to run the installation of a package after the `onInstall`
        event is processed.
        """
        # Mark as pending
        self.markInstalled(None)
        # Do install
        self.info.install()
        # Mark according to install success
        self.markInstalled(self.info.installed)

    def onInstall(self, evt=None):
        """Event called when the install button is clicked.
        """
        wx.CallAfter(self._doInstall)  # call after processing button events
        if evt is not None and hasattr(evt, 'Skip'):
            evt.Skip()

    def _doActivate(self, state=True):
        """Activate a plugin or package after the `onActivate` event.

        Parameters
        ----------
        state : bool
            Active state to set, True for active or False for inactive. Default
            is `True`.

        """
        # Mark as pending
        self.markActive(None)

        if state:  # handle activation
            self.info.activate()
        else:
            self.info.deactivate()

        # Mark according to success
        self.markActive(self.info.active)

    def onToggleActivate(self, evt=None):
        if self.info.active:
            self.onDeactivate(evt=evt)
        else:
            self.onActivate(evt=evt)

    def onActivate(self, evt=None):
        wx.CallAfter(self._doActivate, True)  # call after processing button events
        if evt is not None and hasattr(evt, 'Skip'):
            evt.Skip()

    def onDeactivate(self, evt=None):
        wx.CallAfter(self._doActivate, False)
        if evt is not None and hasattr(evt, 'Skip'):
            evt.Skip()

    def onKeyword(self, evt=None):
        kw = evt.GetString()
        if kw:
            # If we have a keyword, use it in a search
            self.list.searchCtrl.SetValue(kw)
            self.list.search()

    def onHomepage(self, evt=None):
        if self.info.homepage:
            webbrowser.open(self.info.homepage)

    @property
    def info(self):
        """
        Information about this plugin
        """
        return self._info

    @info.setter
    def info(self, value):
        # Hide/show everything according to None
        self.sizer.ShowItems(value is not None)
        # Show/hide placeholder according to None
        self.placeholder.Show(value is None)
        self.placeholder.editBtn.Hide()
        # Handle None
        if value is None:
            value = PluginInfo(
                "psychopy-...",
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
            # Supply an alpha channel
            alpha = icon.tobytes("raw", "A")
            icon = wx.Bitmap.FromBufferAndAlpha(
                width=icon.size[0],
                height=icon.size[1],
                data=icon.tobytes("raw", "RGB"),
                alpha=alpha
            )
        if not isinstance(icon, wx.Bitmap):
            icon = wx.Bitmap(icon)
        self.icon.SetBitmap(icon)
        # Set names
        self.title.SetLabelText(value.name)
        self.pipName.SetLabelText(value.pipname)
        # Set installed
        self.markInstalled(value.installed)
        # Enable/disable homepage
        self.homepageBtn.Enable(bool(self.info.homepage))
        # Set activated
        # self.markActive(value.active)
        # Set description
        self.description.setValue(value.description)
        # Set version text
        self.versionCtrl.SetLabelText(_translate(
            "Works with versions {}."
        ).format(value.version))
        self.versionCtrl.Show(
            value.version.first is not None or value.version.last is not None
        )
        # Set keywords
        self.keywordsCtrl.items = value.keywords

        # Set author info
        self.author.info = value.author

        # Handle version mismatch
        self.installBtn.Enable(__version__ in self.info.version)

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
        # # Email button
        # self.emailBtn = wx.Button(self, style=wx.BU_EXACTFIT)
        # self.emailBtn.SetToolTip(_translate("Email author"))
        # self.emailBtn.Bind(wx.EVT_BUTTON, self.onEmailBtn)
        # self.buttonSizer.Add(self.emailBtn, border=3, flag=wx.EXPAND | wx.ALL)
        # GitHub button
        self.githubBtn = wx.Button(self, style=wx.BU_EXACTFIT)
        self.githubBtn.SetToolTip(_translate("Author's GitHub"))
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
        # # Email button bitmap
        # self.emailBtn.SetBitmap(icons.ButtonIcon("email", 16).bitmap)
        # self.emailBtn.SetBitmapDisabled(icons.ButtonIcon("email", 16).bitmap)
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
            value = AuthorInfo(
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
            # Supply an alpha channel
            alpha = icon.tobytes("raw", "A")

            icon = wx.Bitmap.FromBufferAndAlpha(
                width=icon.size[0],
                height=icon.size[1],
                data=icon.tobytes("raw", "RGB"),
                alpha=alpha
            )
        if not isinstance(icon, wx.Bitmap):
            icon = wx.Bitmap(icon)
        self.avatar.SetBitmap(icon)
        # Update name
        self.name.SetLabelText(value.name)
        # Add tooltip for OST
        if value == "ost":
            self.name.SetToolTip(_translate(
                "That's us! We make PsychoPy and Pavlovia!"
            ))
        else:
            self.name.SetToolTip("")
        # Show/hide buttons
        # self.emailBtn.Show(bool(value.email))
        self.githubBtn.Show(bool(value.github))

    def onEmailBtn(self, evt=None):
        webbrowser.open(f"mailto:{self.info.email}")

    def onGithubBtn(self, evt=None):
        webbrowser.open(f"github.com/{self.info.github}")


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
    def _setAllBitmaps(btn, bmp):
        """
        Set all bitmaps (enabled, disabled, focus, unfocus, etc.) for a button
        """
        btn.SetBitmap(bmp)
        btn.SetBitmapDisabled(bmp)
        btn.SetBitmapPressed(bmp)
        btn.SetBitmapCurrent(bmp)
        btn.SetBitmapMargins(6, 3)

    # Update plugin item
    if pluginItem:
        if installed is None:
            # If pending, show elipsis and refresh icon
            pluginItem.installBtn.Show()
            pluginItem.installBtn.SetLabel("...")
            _setAllBitmaps(pluginItem.installBtn, icons.ButtonIcon("view-refresh", 16).bitmap)
            # Hide active button while pending
            # pluginItem.activeBtn.Hide()
        elif installed:
            # If installed, hide install button
            pluginItem.installBtn.Hide()
            # Show active button when installed
            # pluginItem.activeBtn.Show()
        else:
            # If not installed, show "Install" and download icon
            pluginItem.installBtn.Show()
            pluginItem.installBtn.SetLabel(_translate("Install"))
            _setAllBitmaps(pluginItem.installBtn, icons.ButtonIcon("download", 16).bitmap)
            # Hide active button when not installed
            # pluginItem.activeBtn.Hide()
        # Refresh buttons
        pluginItem.Update()
        pluginItem.Layout()

    # Update panel (if applicable)
    if pluginPanel and pluginItem and pluginPanel.info == pluginItem.info:
        if installed is None:
            # If pending, show elipsis and refresh icon
            pluginPanel.installBtn.Show()
            pluginPanel.installBtn.Enable(__version__ in pluginItem.info.version)
            pluginPanel.installBtn.SetLabel("...")
            _setAllBitmaps(pluginPanel.installBtn, icons.ButtonIcon("view-refresh", 16).bitmap)
            # Hide active button while pending
            # pluginPanel.activeBtn.Hide()
        elif installed:
            # If installed, show as installed with tick
            pluginPanel.installBtn.Show()
            pluginPanel.installBtn.Disable()
            pluginPanel.installBtn.SetLabelText(_translate("Installed"))
            _setAllBitmaps(pluginPanel.installBtn, icons.ButtonIcon("greytick", 16).bitmap)
            # Show active button when installed
            # pluginPanel.activeBtn.Show()
        else:
            # If not installed, show "Install" and download icon
            pluginPanel.installBtn.Show()
            pluginPanel.installBtn.Enable(__version__ in pluginItem.info.version)
            pluginPanel.installBtn.SetLabel(_translate("Install"))
            _setAllBitmaps(pluginPanel.installBtn, icons.ButtonIcon("download", 16).bitmap)
            # Hide active button when not installed
            # pluginPanel.activeBtn.Hide()
        # Refresh buttons
        pluginPanel.Update()


def markActive(pluginItem, pluginPanel, active=True):
    """
    Setup installed button according to install state

    Parameters
    ----------
    pluginItem : PluginBrowserList.PluginListItem
        Plugin list item associated with this plugin
    pluginPanel : PluginDetailsPanel
        Plugin viewer panel to update
    active : bool or None
        True if active, False if not active, None if pending/unclear
    """
    def _setAllBitmaps(btn, bmp):
        """
        Set all bitmaps (enabled, disabled, focus, unfocus, etc.) for a button
        """
        btn.SetBitmap(bmp)
        btn.SetBitmapDisabled(bmp)
        btn.SetBitmapPressed(bmp)
        btn.SetBitmapCurrent(bmp)
        btn.SetBitmapFocus(bmp)
        btn.SetBitmapMargins(6, 3)

    # Update plugin item
    if pluginItem:
        if active is None:
            # If pending, show elipsis and refresh icon
            pluginItem.activeBtn.SetLabel("...")
            _setAllBitmaps(pluginItem.activeBtn, icons.ButtonIcon("orangedot", 16).bitmap)
        elif active:
            # If active, show Enabled and green dot
            pluginItem.activeBtn.SetLabel(_translate("Enabled"))
            _setAllBitmaps(pluginItem.activeBtn, icons.ButtonIcon("greendot", 16).bitmap)
        else:
            # If not active, show Disabled and grey dot
            pluginItem.activeBtn.SetLabel(_translate("Disabled"))
            _setAllBitmaps(pluginItem.activeBtn, icons.ButtonIcon("greydot", 16).bitmap)
        # Refresh
        pluginItem.Update()
        pluginItem.Layout()

    # Update panel (if applicable)
    if pluginPanel and pluginItem and pluginPanel.info == pluginItem.info:
        if active is None:
            # If pending, show elipsis and refresh icon
            pluginPanel.activeBtn.SetLabel("...")
            _setAllBitmaps(pluginPanel.activeBtn, icons.ButtonIcon("orangedot", 16).bitmap)
        elif active:
            # If active, show Enabled and green dot
            pluginPanel.activeBtn.SetLabel(_translate("Enabled"))
            _setAllBitmaps(pluginPanel.activeBtn, icons.ButtonIcon("greendot", 16).bitmap)
        else:
            # If not active, show Disabled and grey dot
            pluginPanel.activeBtn.SetLabel(_translate("Disabled"))
            _setAllBitmaps(pluginPanel.activeBtn, icons.ButtonIcon("greydot", 16).bitmap)
        # Refresh
        pluginPanel.Update()


# store plugin objects for later use
_pluginObjects = None


def getAllPluginDetails():
    """Get all plugin details from the server and return as a list of
    `PluginInfo` objects.

    This function will download the plugin database from the server and
    return a list of `PluginInfo` objects, one for each plugin in the
    database. The database is cached locally and will only be replaced when
    the server version is newer than the local version. This allows the user 
    to use the plugin manager offline or when the server is down.

    Returns
    -------
    list of PluginInfo
        List of plugin details.

    """
    # check if the local `plugins.json` file exists and is up to date
    appPluginCacheDir = os.path.join(
        prefs.paths['userCacheDir'], 'appCache', 'plugins')
    
    # create the cache directory if it doesn't exist
    if not os.path.exists(appPluginCacheDir):
        try:
            os.makedirs(appPluginCacheDir)
        except OSError:
            pass

    # where the database is expected to be
    pluginDatabaseFile = os.path.join(appPluginCacheDir, 'plugins.json')

    def downloadPluginDatabase(srcURL="https://psychopy.org/plugins.json"):
        """Downloads the plugin database from the server and returns the text
        as a string. If the download fails, returns None.

        Parameters
        ----------
        srcURL : str
            The URL to download the plugin database from.

        Returns
        -------
        str or None
            The plugin database as a string, or None if the download failed.
        
        """
        try:
            resp = requests.get(srcURL)
            if resp.status_code == 404:
                return None
            return resp.text
        except requests.exceptions.ConnectionError:
            return None
        
    def readLocalPluginDatabase(srcFile):
        """Read the local plugin database file (if it exists) and return the
        text as a string. If the file doesn't exist, returns None.

        Parameters
        ----------
        srcFile : str
            The expected path to the plugin database file.
        
        Returns
        -------
        str or None
            The plugin database as a string, or None if the file doesn't exist.
        
        """
        if os.path.exists(srcFile):
            with open(srcFile, 'r') as f:
                return f.read()
            
        return None
    
    def deletePluginDlgCache():
        """Delete the local plugin database file and cached files related to 
        the Plugin dialog.
        """
        if os.path.exists(appPluginCacheDir):
            files = glob.glob(os.path.join(appPluginCacheDir, '*'))
            for f in files:
                os.remove(f)
                
    # get a copy of the plugin database from the server, check if it's newer
    # than the local copy, and if so, replace the local copy
    refreshPlugins = False  # database has changed
    serverPluginDatabase = downloadPluginDatabase()  # text
    localPluginDatabase = readLocalPluginDatabase(pluginDatabaseFile)  # text
    if serverPluginDatabase is not None:
        if localPluginDatabase is None:
            deletePluginDlgCache()
            # write the new plugin database file
            with open(pluginDatabaseFile, 'w') as f:  # save the file
                f.write(serverPluginDatabase)
            localPluginDatabase = json.loads(serverPluginDatabase)
        else:
            # exists, but does it need updating?
            localPluginDatabase = json.loads(localPluginDatabase)
            serverPluginDatabase = json.loads(serverPluginDatabase)
            if localPluginDatabase != serverPluginDatabase:
                # clear the old cache
                deletePluginDlgCache()
                # write the new plugin database file
                with open(pluginDatabaseFile, 'w') as f:  # save the file
                    json.dump(serverPluginDatabase, f, indent=True)
                localPluginDatabase = serverPluginDatabase
        refreshPlugins = True
    else:
        # no server connection, use local copy
        if localPluginDatabase is None:
            # no local copy, so no plugins
            return []
        else:
            # use local copy
            localPluginDatabase = json.loads(localPluginDatabase)
        refreshPlugins = True

    # check if we need to update plugin objects, if not return the cached data
    global _pluginObjects
    requiresRefresh = refreshPlugins or _pluginObjects is None
    if not requiresRefresh:
        return _pluginObjects

    # Create PluginInfo objects from info list
    objs = []
    for info in localPluginDatabase:
        objs.append(PluginInfo(**info))

    # Add info objects for local plugins which aren't found online
    localPlugins = plugins.listPlugins(which='all')
    for name in localPlugins:
        # Check whether plugin is accounted for
        if name not in objs:
            # If not, get its metadata
            data = plugins.pluginMetadata(name)
            # Create best representation we can from metadata
            author = AuthorInfo(
                name=data.get('Author', ''),
                email=data.get('Author-email', ''),
            )
            info = PluginInfo(
                pipname=name, name=name,
                author=author,
                homepage=data.get('Home-page', ''),
                keywords=data.get('Keywords', ''),
                description=data.get('Summary', ''),
            )
            # Add to list
            objs.append(info)

    _pluginObjects = objs  # cache for later

    return _pluginObjects


if __name__ == "__main__":
    pass



