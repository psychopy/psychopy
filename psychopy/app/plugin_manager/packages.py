import wx
import sys
import subprocess as sp

from psychopy.plugins import InstallErrorDlg
from psychopy.app import utils
from psychopy.app.themes import handlers, icons
from psychopy.localization import _translate


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
        self.packageList.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onActivateItem)
        self.packageList.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.onRightClickItem)
        self.sizer.Add(self.packageList, flag=wx.EXPAND | wx.ALL)
        # Seperator
        self.sizer.Add(wx.StaticLine(self, style=wx.LI_VERTICAL), border=6, flag=wx.EXPAND | wx.ALL)
        # Add pip terminal
        self.pipCtrl = PIPTerminalPanel(self)
        self.sizer.Add(self.pipCtrl, proportion=1, flag=wx.EXPAND | wx.ALL)

    def onActivateItem(self, evt=None):
        # Get package name
        pipname = evt.GetText()
        # Pre-fill "pip show" for the user
        self.pipCtrl.console.SetValue(f"pip show {pipname}")
        # Switch focus to pip ctrl
        self.pipCtrl.console.SetFocus()

    def onRightClickItem(self, evt=None):
        # Create menu
        menu = wx.Menu()
        # Define commands / labels
        menu.commands = {
            _translate("View"): ("show", ""),
            _translate("Update"): ("install", "--upgrade"),
            _translate("Uninstall"): ("uninstall", "")
        }
        # Add menu options
        for lbl in menu.commands:
            menu.Append(wx.ID_ANY, lbl)
        # Store pip name as attribute of menu
        menu.pipname = evt.GetText()
        # Bind menu choice to function
        menu.Bind(wx.EVT_MENU, self.onRightClickMenuChoice)
        # Show menu
        self.PopupMenu(menu)

    def onRightClickMenuChoice(self, evt=None):
        # Get menu object
        menu = evt.GetEventObject()
        # Get choice
        choiceId = evt.GetId()
        choice = menu.GetLabel(choiceId)
        # Get command and params from choice
        cmd = menu.commands[choice][0]
        params = " ".join(menu.commands[choice][1:])
        # Pre-fill "pip ..." for the user
        self.pipCtrl.console.SetValue(f"pip {cmd} {menu.pipname} {params}")
        # Switch focus to pip ctrl
        self.pipCtrl.console.SetFocus()


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
        self.ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onDoubleClick)
        self.ctrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.onRightClick)
        self.sizer.Add(self.ctrl, proportion=1, border=6, flag=wx.LEFT | wx.RIGHT | wx.EXPAND)
        # Create button sizer
        self.btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.btnSizer, flag=wx.EXPAND)
        # Create add button
        self.addBtn = wx.Button(self, label="▼", size=(48, 24))
        self.addBtn.Bind(wx.EVT_BUTTON, self.onAddBtn)
        self.btnSizer.Add(self.addBtn, border=6, flag=wx.ALL | wx.EXPAND)
        # Create refresh button
        self.btnSizer.AddStretchSpacer(1)
        self.refreshBtn = wx.Button(self, size=(24, 24))
        self.refreshBtn.Bind(wx.EVT_BUTTON, self.refresh)
        self.btnSizer.Add(self.refreshBtn, border=6, flag=wx.ALL | wx.EXPAND)
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

    def onDoubleClick(self, evt=None):
        # Post event so it can be caught by parent
        evt.SetEventObject(self)
        wx.PostEvent(self, evt)

    def onRightClick(self, evt=None):
        # Post event so it can be caught by parent
        evt.SetEventObject(self)
        wx.PostEvent(self, evt)

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
            self.add(dlg.GetPath())

    def add(self, ref):
        """
        Add a package

        Parameters
        ----------
        ref : str
            Reference to the package, either a pip name or the location of a wheel/egg file
        """
        # Construct pip command
        cmd = f"{sys.executable} -m pip install {ref}"
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
        # Refresh packages list
        self.refresh()
