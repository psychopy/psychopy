import wx
import sys
import subprocess as sp

from psychopy.app.themes import handlers, icons, fonts
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
        self.sizer.Add(self.packageList, flag=wx.EXPAND | wx.ALL)
        # Seperator
        self.sizer.Add(wx.StaticLine(self, style=wx.LI_VERTICAL), border=6, flag=wx.EXPAND | wx.ALL)
        # Add pip terminal
        self.pipCtrl = PIPTerminalPanel(self)
        self.sizer.Add(self.pipCtrl, flag=wx.EXPAND | wx.ALL)


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

        # Add instructions
        self.instr = wx.StaticText(self, label=_translate(
            "Type a PIP command below and press Enter to execute it in the installed PsychoPy environment, any "
            "returned text will appear below."
        ))
        self.instr.Wrap(self.GetSize()[0] - 24 - 6)
        self.sizer.Add(self.instr, border=6, flag=wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND)

        # Add text control
        self.consoleSzr = wx.BoxSizer(wx.HORIZONTAL)
        self.consoleLbl = wx.StaticText(self, label=">>")
        self.consoleSzr.Add(self.consoleLbl, border=6, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.console = wx.TextCtrl(self, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.console.Bind(wx.EVT_TEXT_ENTER, self.onEnter)
        self.consoleSzr.Add(self.console, proportion=1)
        self.sizer.Add(self.consoleSzr, border=6, flag=wx.ALL | wx.EXPAND)

        # Add output
        self.output = wx.richtext.RichTextCtrl(self, size=(480, -1), style=wx.TE_READONLY)
        self.sizer.Add(self.output, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)

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
        self.output.AppendText("\n>> " + cmd)

        # Display output if error
        if output.returncode != 0:
            self.output.AppendText(stderr)

        self.output.AppendText(stdout)

        # Update output ctrl to style new text
        handlers.ThemeMixin._applyAppTheme(self.output)

    def _applyAppTheme(self):
        # Apply code font to text ctrl
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
        self.sizer.Add(self.lbl, border=6, flag=wx.ALL | wx.EXPAND)
        # Create list ctrl
        self.ctrl = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.sizer.Add(self.ctrl, proportion=1, border=6, flag=wx.LEFT | wx.RIGHT | wx.EXPAND)
        # Create refresh button
        self.refreshBtn = wx.Button(self, size=(24, 24))
        self.refreshBtn.Bind(wx.EVT_BUTTON, self.refresh)
        self.sizer.Add(self.refreshBtn, border=6, flag=wx.ALL | wx.ALIGN_RIGHT)
        # Initial data
        self.refresh()

        self.Layout()
        self._applyAppTheme()

    def _applyAppTheme(self):
        self.refreshBtn.SetBitmap(
            icons.ButtonIcon(stem="view-refresh", size=16).bitmap
        )

    def refresh(self, evt=None):
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
                self.ctrl.Append(parts)