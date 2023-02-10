import webbrowser
import wx
import wx.richtext
from psychopy.app.themes import handlers, icons, colors
from psychopy.localization import _translate
from psychopy.tools import pkgtools


class InstallErrorDlg(wx.Dialog, handlers.ThemeMixin):
    """
    Dialog to display when something fails to install, contains info on what
    command was tried and what output was received.
    """
    def __init__(self, label, caption=_translate("PIP error"), cmd="", stdout="", stderr=""):
        from psychopy.app.themes import fonts
        # Initialise
        wx.Dialog.__init__(
            self, None,
            size=(480, 620),
            title=caption,
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
        self.titleLbl = wx.StaticText(self, label=label)
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


class InstallStdoutDlg(wx.Dialog, handlers.ThemeMixin):
    def __init__(self, parent, pipname="package"):
        wx.Dialog.__init__(
            self, parent,
            size=(480, 620),
            title=_translate("Installing..."),
            style=wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.CAPTION
        )
        # Setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # Create title
        self.titleLbl = wx.StaticText(self, label=_translate("Installing %s...") % pipname)
        self.sizer.Add(self.titleLbl, border=6, flag=wx.ALL | wx.EXPAND)
        # Output
        self.output = wx.richtext.RichTextCtrl(self)
        self.output.Bind(wx.EVT_TEXT_URL, self.onLink)
        self.sizer.Add(self.output, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # Close
        btns = self.CreateStdDialogButtonSizer(flags=wx.CLOSE)
        self.sizer.Add(btns, border=6, flag=wx.ALL | wx.EXPAND)

        self.Layout()
        self.Update()
        self.Refresh()

    def write(self, content, color="black", style=""):
        from psychopy.app.themes import fonts
        self.output.BeginFont(fonts.CodeFont().obj)
        # Set style
        self.output.BeginTextColour(color)
        if "b" in style:
            self.output.BeginBold()
        if "i" in style:
            self.output.BeginItalic()
        # Write content
        self.output.WriteText(content)
        # End style
        self.output.EndTextColour()
        self.output.EndBold()
        self.output.EndItalic()
        # Scroll to end
        self.output.ShowPosition(self.output.GetLastPosition())
        # Update
        self.Update()
        self.Refresh()

    def writeLink(self, content, link=""):
        # Begin style
        self.output.BeginURL(link)
        # Write content
        self.write(content, color=colors.scheme["blue"], style="i")
        # End style
        self.output.EndURL()

    def writeCmd(self, cmd=""):
        self.write(f">> {cmd}\n", style="bi")

    def writeStdOut(self, lines=""):
        self.write(f"{lines}\n")

    def writeStdErr(self, lines=""):
        self.write(f"{lines}\n", color=colors.scheme["red"])

    def writeTerminus(self):
        self.write("\n\n---\n\n", color=colors.scheme["green"])

    def onLink(self, evt=None):
        webbrowser.open(evt.String)


def uninstallPackage(package):
    """
    Call `pkgtools.uninstallPackage` and handle any errors cleanly.
    """
    retcode, info = pkgtools.uninstallPackage(package)

    # Handle errors
    if retcode != 0:
        # Display output if error
        cmd = "\n>> " + " ".join(info['cmd']) + "\n"
        dlg = InstallErrorDlg(
            cmd=cmd,
            stdout=info['stdout'],
            stderr=info['stderr'],
            label=_translate("Package {} could not be uninstalled.").format(package)
        )
    else:
        # Display success message if success
        dlg = wx.MessageDialog(
            parent=None,
            caption=_translate("Package installed"),
            message=_translate("Package {} successfully uninstalled!").format(package),
            style=wx.ICON_INFORMATION
        )
    dlg.ShowModal()


def installPackage(package):
    """
    Call `pkgtools.installPackage` and handle any errors cleanly.
    """
    # Show install dialog
    dlg = InstallStdoutDlg(
        parent=None, pipname=package
    )
    dlg.Show()
    # Install package
    retcode, info = pkgtools.installPackage(package)
    # Write command
    dlg.writeCmd(" ".join(info['cmd']))
    # Write output
    dlg.writeStdOut(info['stdout'])
    dlg.writeStdErr(info['stderr'])
    # Terminate output
    dlg.writeTerminus()
    # Report success
    if retcode:
        dlg.writeStdOut(_translate("Installation complete. See above for info.\n"))
    else:
        dlg.writeStdErr(_translate("Installation failed. See above for info.\n"))

    return dlg
