import wx
import sys
import subprocess as sp

from psychopy.app import utils
from psychopy.app.themes import handlers, icons
from psychopy.localization import _translate




class InstallErrorDlg(wx.Dialog, handlers.ThemeMixin):
    def __init__(self, cmd="", stdout="", stderr="", mode="plugin"):
        from psychopy.app.themes import fonts
        # Capitalise mode string
        mode = mode.title()
        # Initialise
        wx.Dialog.__init__(
            self, None,
            size=(480, 620),
            title=mode + _translate(" install error"),
            style=wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.CAPTION
        )
        # Setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # Create title sizer
        self.title = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.title, border=6, flag=wx.ALL | wx.EXPAND)
        # Create icon
        self.icon = wx.StaticBitmap(
            self, size=(32, 32),
            bitmap=icons.ButtonIcon(stem="stop", size=32).bitmap
        )
        self.title.Add(self.icon, border=6, flag=wx.ALL | wx.EXPAND)
        # Create title
        self.titleLbl = wx.StaticText(self, label=mode + _translate(" could not be installed."))
        self.titleLbl.SetFont(fonts.appTheme['h3'].obj)
        self.title.Add(self.titleLbl, proportion=1, border=6, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        # Show what we tried
        self.inLbl = wx.StaticText(self, label=_translate("We tried:"))
        self.sizer.Add(self.inLbl, border=6, flag=wx.ALL | wx.EXPAND)
        self.inCtrl = wx.TextCtrl(self, value=cmd, style=wx.TE_READONLY)
        self.inCtrl.SetBackgroundColour("white")
        self.inCtrl.SetFont(fonts.appTheme['code'].obj)
        self.sizer.Add(self.inCtrl, border=6, flag=wx.ALL | wx.EXPAND)
        # Show what we got
        self.outLbl = wx.StaticText(self, label=_translate("We got:"))
        self.sizer.Add(self.outLbl, border=6, flag=wx.ALL | wx.EXPAND)
        self.outCtrl = wx.TextCtrl(self, value=f"{stdout}\n{stderr}",
                                   size=(-1, 620), style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.outCtrl.SetFont(fonts.appTheme['code'].obj)
        self.sizer.Add(self.outCtrl, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)

        # Make buttons
        self.btns = self.CreateStdDialogButtonSizer(flags=wx.OK)
        self.border.Add(self.btns, border=6, flag=wx.ALIGN_RIGHT | wx.ALL)

        self.Layout()
        self._applyAppTheme()

    def ShowModal(self):
        # Make error noise
        wx.Bell()
        # Show as normal
        wx.Dialog.ShowModal(self)


class PackageManagerPanel(wx.Panel, handlers.ThemeMixin):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        # Setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # Add package list
        self.packageList = PackageListCtrl(self)
        self.packageList.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelectItem)
        self.sizer.Add(self.packageList, flag=wx.EXPAND | wx.ALL)
        # Seperator
        self.sizer.Add(wx.StaticLine(self, style=wx.LI_VERTICAL), border=6, flag=wx.EXPAND | wx.ALL)
        # Add details panel
        self.detailsPanel = PackageDetailsPanel(self)
        self.sizer.Add(self.detailsPanel, proportion=1, flag=wx.EXPAND | wx.ALL)

    def onSelectItem(self, evt=None):
        # Get package name
        pipname = evt.GetText()
        # Set pip details from name
        self.detailsPanel.package = pipname


class PIPTerminalPanel(wx.Panel):
    """
    Interface for interacting with PIP within the standalone PsychoPy environment.
    """

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Setup sizers
        self.border = wx.BoxSizer()
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(self.sizer, proportion=1, border=12, flag=wx.ALL | wx.EXPAND)

        # Add output
        self.output = wx.richtext.RichTextCtrl(
            self,
            value=_translate(
                "Type a PIP command below and press Enter to execute it in the installed PsychoPy environment, any "
                "returned text will appear below.\n"
                "\n"
            ),
            size=(480, -1),
            style=wx.TE_READONLY)
        self.sizer.Add(self.output, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)

        # Add text control
        self.consoleSzr = wx.BoxSizer(wx.HORIZONTAL)
        self.consoleLbl = wx.StaticText(self, label=">>")
        self.consoleSzr.Add(self.consoleLbl, border=6, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.console = wx.TextCtrl(self, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.console.Bind(wx.EVT_TEXT_ENTER, self.onEnter)
        self.consoleSzr.Add(self.console, proportion=1)
        self.sizer.Add(self.consoleSzr, border=6, flag=wx.ALL | wx.EXPAND)

        self._applyAppTheme()

        self.Center()

    def onEnter(self, evt=None):
        # Get current command
        cmd = self.console.GetValue()
        # Clear text entry
        self.console.Clear()
        # Run command
        self.runCommand(cmd)

    def runCommand(self, cmd):
        """Run the command."""
        emts = [sys.executable, "-m", cmd]
        output = sp.Popen(' '.join(emts),
                          stdout=sp.PIPE,
                          stderr=sp.PIPE,
                          shell=True,
                          universal_newlines=True)
        stdout, stderr = output.communicate()
        sys.stdout.write(stdout)
        sys.stderr.write(stderr)

        # Display input
        self.output.AppendText("\n>> " + cmd + "\n")

        # Display output if error
        if output.returncode != 0:
            self.output.AppendText(stderr)

        self.output.AppendText(stdout)

        # Update output ctrl to style new text
        handlers.ThemeMixin._applyAppTheme(self.output)

        # Scroll to bottom
        self.output.ShowPosition(self.output.GetLastPosition())

    def _applyAppTheme(self):
        # Style output ctrl
        handlers.ThemeMixin._applyAppTheme(self.output)
        # Apply code font to text ctrl
        from psychopy.app.themes import fonts
        self.console.SetFont(fonts.coderTheme.base.obj)


class PackageListCtrl(wx.Panel, handlers.ThemeMixin):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, size=(300, -1))
        # Setup sizers
        self.border = wx.BoxSizer()
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(self.sizer, proportion=1, border=12, flag=wx.ALL | wx.EXPAND)

        # Label
        self.lbl = wx.StaticText(self, label=_translate("Installed packages:"))
        self.sizer.Add(self.lbl, border=6, flag=wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND)
        # Search bar
        self.searchCtrl = wx.SearchCtrl(self)
        self.searchCtrl.Bind(wx.EVT_SEARCH, self.refresh)
        self.sizer.Add(self.searchCtrl, border=6, flag=wx.ALL | wx.EXPAND)
        # Create list ctrl
        self.ctrl = utils.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.ctrl.setResizeColumn(0)
        self.ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.ctrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.onRightClick)
        self.sizer.Add(self.ctrl, proportion=1, border=6, flag=wx.LEFT | wx.RIGHT | wx.EXPAND)
        # Create button sizer
        self.btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.btnSizer, border=3, flag=wx.ALL | wx.EXPAND)
        # Create add button
        self.addBtn = wx.Button(self, label="▼", size=(48, 24))
        self.addBtn.Bind(wx.EVT_BUTTON, self.onAddBtn)
        self.btnSizer.Add(self.addBtn, border=3, flag=wx.ALL | wx.EXPAND)
        # Add button to open pip
        self.terminalBtn = wx.Button(self, size=(24, 24))
        self.terminalBtn.SetToolTipString(_translate("Open PIP terminal to manage packages manually"))
        self.btnSizer.Add(self.terminalBtn, border=3, flag=wx.ALL | wx.EXPAND)
        self.terminalBtn.Bind(wx.EVT_BUTTON, self.onOpenPipTerminal)
        # Create refresh button
        self.btnSizer.AddStretchSpacer(1)
        self.refreshBtn = wx.Button(self, size=(24, 24))
        self.refreshBtn.Bind(wx.EVT_BUTTON, self.refresh)
        self.btnSizer.Add(self.refreshBtn, border=3, flag=wx.ALL | wx.EXPAND)
        # Initial data
        self.refresh()

        self.Layout()
        self._applyAppTheme()

    def _applyAppTheme(self):
        self.refreshBtn.SetBitmap(
            icons.ButtonIcon(stem="view-refresh", size=16).bitmap
        )
        self.addBtn.SetBitmap(
            icons.ButtonIcon(stem="plus", size=16).bitmap
        )
        self.terminalBtn.SetBitmap(
            icons.ButtonIcon(stem="libroot", size=16).bitmap
        )

    def onOpenPipTerminal(self, evt=None):
        # Make dialog
        dlg = wx.Dialog(self, title="PIP Terminal", size=(480, 480), style=wx.RESIZE_BORDER | wx.CAPTION | wx.CLOSE_BOX)
        # Setup sizer
        dlg.sizer = wx.BoxSizer(wx.VERTICAL)
        dlg.SetSizer(dlg.sizer)
        # Add panel
        panel = PIPTerminalPanel(dlg)
        dlg.sizer.Add(panel, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # Layout
        dlg.Layout()
        # Show
        dlg.Show()

    def onItemSelected(self, evt=None):
        # Post event so it can be caught by parent
        evt.SetEventObject(self)
        wx.PostEvent(self, evt)

    def onRightClick(self, evt=None):
        # Create menu
        menu = wx.Menu()
        uninstallOpt = menu.Append(wx.ID_ANY, item=_translate("Uninstall"))
        # Bind menu to functions
        menu.functions = {
            uninstallOpt.GetId(): self.onUninstall,
        }
        menu.Bind(wx.EVT_MENU, self.onRightClickMenuChoice)
        # Store pip name as attribute of menu
        menu.pipname = evt.GetText()
        # Show menu
        self.PopupMenu(menu)

    def onRightClickMenuChoice(self, evt=None):
        # Work out what was chosen
        menu = evt.GetEventObject()
        choice = evt.GetId()
        if choice not in menu.functions:
            return
        # Perform associated method
        menu.functions[choice](evt)

    def onUninstall(self, evt=None):
        # Get rightclick menu
        menu = evt.GetEventObject()
        pipname = menu.pipname
        msg = wx.MessageDialog(
            self,
            "Are you sure you want to uninstall package `{}`?".format(pipname),
            caption="Uninstall Package?",
            style=wx.YES_NO | wx.NO_DEFAULT)

        # if user selects NO, exit the routine
        if msg.ShowModal() == wx.ID_YES:
            # Issue uninstall command, use the `-y` argument to get around the
            # prompt that requires sending bytes to the console.
            cmd = ["uninstall", "-y", menu.pipname]
            self.execute(cmd)

        msg.Destroy()

    def refresh(self, evt=None):
        # Get search term
        searchTerm = self.searchCtrl.GetValue()
        # Clear
        self.ctrl.ClearAll()
        self.ctrl.AppendColumn(_translate("Package"))
        self.ctrl.AppendColumn(_translate("Version"))
        # Get list of packages
        cmd = f"{sys.executable} -m pip freeze"
        output = sp.Popen(cmd,
                          stdout=sp.PIPE,
                          stderr=sp.PIPE,
                          shell=True,
                          universal_newlines=True)
        stdout, stderr = output.communicate()
        # Parse output into a list of lines
        lines = stdout.split("\n")
        for line in lines:
            # If line is a valid version name - version pair, append to list
            parts = line.split("==")
            if len(parts) == 2:
                # Filter packages by search term
                if searchTerm in parts[0]:
                    self.ctrl.Append(parts)

    def onAddBtn(self, evt=None):
        # Get button
        btn = evt.GetEventObject()
        # Create menu
        menu = wx.Menu()
        nameOpt = menu.Append(wx.ID_ANY, item=_translate("Add package by name..."))
        fileOpt = menu.Append(wx.ID_ANY, item=_translate("Add package from file..."))
        # Bind menu to functions
        menu.functions = {
            nameOpt.GetId(): self.onAddByName,
            fileOpt.GetId(): self.onAddFromFile
        }
        menu.Bind(wx.EVT_MENU, self.onAddMenuChoice)
        # Show menu
        btn.PopupMenu(menu)

    def onAddMenuChoice(self, evt=None):
        # Work out what was chosen
        menu = evt.GetEventObject()
        choice = evt.GetId()
        if choice not in menu.functions:
            return
        # Perform associated method
        menu.functions[choice](evt)

    def onAddByName(self, evt=None):
        # Create dialog to get package name
        dlg = wx.TextEntryDialog(self, message=_translate("Package name:"))
        if dlg.ShowModal() == wx.ID_OK:
            self.add(dlg.GetValue())

    def onAddFromFile(self, evt=None):
        # Create dialog to get package file location
        dlg = wx.FileDialog(
            self,
            wildcard="Wheel files (.whl)|.whl|Source distribution files (.sdist)|.sdist",
            style=wx.FD_OPEN | wx.FD_SHOW_HIDDEN)
        if dlg.ShowModal() == wx.ID_OK:
            cmd = ["install", dlg.GetPath()]
            self.execute(cmd)

    def execute(self, params):
        """
        Execute a pip command

        Parameters
        ----------
        params : str or list
            Pip command params (everything after the word `pip`)
        """
        if not isinstance(params, str):
            params = " ".join(params)
        # Construct pip command
        cmd = f"{sys.executable} -m pip {params}"
        # Send to console
        output = sp.Popen(cmd,
                          stdout=sp.PIPE,
                          stderr=sp.PIPE,
                          shell=True,
                          universal_newlines=True)
        stdout, stderr = output.communicate()
        # Show error dialog if something went wrong
        if stderr:
            dlg = InstallErrorDlg(cmd=cmd, stdout=stdout, stderr=stderr, mode="package")
            dlg.ShowModal()
        else:
            dlg = wx.MessageDialog(
                self,
                message=_translate("Successfully completed: `pip {}`").format(params),
                style=wx.ICON_INFORMATION
            )
            dlg.ShowModal()
        # Refresh packages list
        self.refresh()


class PackageDetailsPanel(wx.Panel, handlers.ThemeMixin):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        # Setup sizers
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(self.sizer, proportion=1, border=12, flag=wx.ALL | wx.EXPAND)

        # Name sizer
        self.nameSzr = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.nameSzr)
        # Name
        self.nameCtrl = wx.StaticText(self)
        self.nameSzr.Add(self.nameCtrl, border=6, flag=wx.TOP | wx.LEFT | wx.RIGHT | wx.EXPAND)
        # Version
        self.versionCtrl = wx.Choice(self)
        self.nameSzr.Add(self.versionCtrl, border=6, flag=wx.ALIGN_BOTTOM | wx.ALL)
        # Author
        self.authorSzr = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.authorSzr, border=6, flag=wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.EXPAND)
        self.authorPre = wx.StaticText(self, label=_translate("by "))
        self.authorSzr.Add(self.authorPre, border=0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.authorCtrl = utils.HyperLinkCtrl(self)
        self.authorSzr.Add(self.authorCtrl, border=0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.licenseCtrl = wx.StaticText(self)
        self.authorSzr.Add(self.licenseCtrl, border=0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        # Header buttons sizer
        self.headBtnSzr = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.headBtnSzr, border=3, flag=wx.ALL | wx.EXPAND)
        # Homepage button
        self.homeBtn = wx.Button(self, label=_translate("Homepage"))
        self.headBtnSzr.Add(self.homeBtn, border=3, flag=wx.ALL | wx.EXPAND)
        # Location button
        self.dirBtn = wx.Button(self, label=_translate("Folder"))
        self.headBtnSzr.Add(self.dirBtn, border=3, flag=wx.ALL | wx.EXPAND)
        # Description
        self.descCtrl = wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE | wx.TE_NO_VSCROLL)
        self.sizer.Add(self.descCtrl, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # todo: Required by...

        self.package = None

        # Cache package information where possible to improve responsiveness of
        # the UI.
        self._packageInfoCache = {}
        self._generatePackageInfoCache()

    def _generatePackageInfoCache(self):
        """Generate package info cache.

        This iterates over all installed packages and obtains information about
        them. The data is cached for later use instead of obtained when the user
        clicks the item.

        """


    @property
    def package(self):
        if hasattr(self, "_package"):
            return self._package

    @package.setter
    def package(self, pipname):
        self._package = pipname

        # Disable/enable according to whether None
        active = pipname is not None
        self.homeBtn.Enable(active)
        self.dirBtn.Enable(active)
        self.nameCtrl.Enable(active)
        self.versionCtrl.Enable(active)
        self.authorPre.Enable(active)
        self.authorCtrl.Enable(active)
        self.licenseCtrl.Enable(active)
        self.descCtrl.Enable(active)
        # Clear choices on version ctrl
        self.versionCtrl.Clear()

        # If None, set everything to blank
        if pipname is None:
            self.nameCtrl.SetLabelText("...")
            self.authorCtrl.SetLabelText("...")
        else:
            # Use pip show to get details
            cmd = f"{sys.executable} -m pip show {pipname}"
            output = sp.Popen(cmd,
                              stdout=sp.PIPE,
                              stderr=sp.PIPE,
                              shell=True,
                              universal_newlines=True)
            stdout, stderr = output.communicate()
            # Parse pip show info
            lines = stdout.split("\n")
            self.params = {}
            for line in lines:
                if ":" not in line:
                    continue
                name, val = line.split(": ", 1)
                self.params[name] = val
            print(self.params)
            # Get versions info
            cmd = f"{sys.executable} -m pip index versions {pipname}"
            output = sp.Popen(cmd,
                              stdout=sp.PIPE,
                              stderr=sp.PIPE,
                              shell=True,
                              universal_newlines=True)
            stdout, stderr = output.communicate()
            # Parse versions info
            versions = stdout.split("\n")[1].strip()
            versions = versions.split(": ")[1]
            versions = versions.split(", ")

            # Set info
            self.nameCtrl.SetLabelText(self.params['Name'])
            self.authorCtrl.SetLabel(self.params['Author'])
            self.versionCtrl.AppendItems(versions)
            self.versionCtrl.SetStringSelection(self.params['Version'])
            self.authorCtrl.URL = "mailto:" + self.params['Author-email']
            self.licenseCtrl.SetLabelText(f" (License: {self.params['License']})")
            self.descCtrl.SetValue(self.params['Summary'])

        self.Layout()
        self._applyAppTheme()

    def _applyAppTheme(self):
        from psychopy.app.themes import fonts
        self.nameCtrl.SetFont(fonts.appTheme['h1'].obj)
        self.dirBtn.SetBitmap(icons.ButtonIcon(stem="folder", size=16).bitmap)
        self.authorCtrl.SetBackgroundColour("white")

