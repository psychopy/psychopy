import wx
import wx.richtext
from psychopy.app.themes import handlers, icons
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


def installPackage(package, stream):
    """
    Call `pkgtools.installPackage` and handle any errors cleanly.
    """
    # Show output
    stream.open()
    # Install package
    retcode, info = pkgtools.installPackage(package)
    # Write command
    stream.writeCmd(" ".join(info['cmd']))
    # Write output
    stream.writeStdOut(info['stdout'])
    stream.writeStdErr(info['stderr'])
    # Report success
    if retcode:
        stream.writeStdOut(_translate("Installation complete. See above for info.\n"))
    else:
        stream.writeStdErr(_translate("Installation failed. See above for info.\n"))

    return stream
