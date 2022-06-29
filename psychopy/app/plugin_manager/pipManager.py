import wx
import wx.richtext

from psychopy.app.themes import handlers, fonts
from psychopy.localization import _translate

import sys
import subprocess as sp


class PIPManagerDlg(wx.Dialog, handlers.ThemeMixin):
    """
    Interface for interacting with PIP within the standalone PsychoPy environment.
    """

    def __init__(self):
        wx.Dialog.__init__(self, None, title="PIP installer",
                           size=(480, 240),
                           style=wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT)

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
        self.sizer.Add(self.instr, border=3, flag=wx.ALL | wx.EXPAND)

        # Add text control
        self.consoleSzr = wx.BoxSizer(wx.HORIZONTAL)
        self.consoleLbl = wx.StaticText(self, label=">>")
        self.consoleSzr.Add(self.consoleLbl, border=6, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.console = wx.TextCtrl(self, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.console.Bind(wx.EVT_TEXT_ENTER, self.onEnter)
        self.consoleSzr.Add(self.console, proportion=1)
        self.sizer.Add(self.consoleSzr, border=3, flag=wx.ALL | wx.EXPAND)

        # Add output
        self.output = wx.richtext.RichTextCtrl(self, size=(480, -1), style=wx.TE_READONLY)
        self.sizer.Add(self.output, proportion=1, border=3, flag=wx.ALL | wx.EXPAND)

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
        cmd = ' '.join([sys.executable, '-m', cmd])
        output = sp.Popen(cmd,
                          stdout=sp.PIPE,
                          stderr=sp.PIPE,
                          shell=True,
                          universal_newlines=True)
        stdout, stderr = output.communicate()
        sys.stdout.write(stdout)
        sys.stderr.write(stderr)

        # Display output
        self.output.SetValue(stdout + stderr)
        # Update output ctrl to style new text
        handlers.ThemeMixin._applyAppTheme(self.output)

    def _applyAppTheme(self):
        # Apply code font to text ctrl
        self.console.SetFont(fonts.coderTheme.base.obj)
