#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Dialog prompting the user to configure their system for Linux specific
optimizations.
"""

__all__ = [
    'LinuxConfigDialog',
    'linuxConfigFileExists'
]

import os.path
import sys

import wx
from .ui import BaseLinuxConfigDialog

# Text that appears at the top of the dialog with provides instructions to the
# user.
_introStr = (
    u"For optimal performance on Linux, Psychtoolbox requires additional "
    u"configuration changes to be made to this system by entering the "
    u"following commands into your terminal:"
)

# config file path
_confPath = u"/etc/security/limits.d/99-psychopylimits.conf"

# these are the commands we want the user to run in their terminal
_cmdStr = (
    u"sudo groupadd --force psychopy\n\n"
    u"sudo usermod -a -G psychopy $USER\n\n"
    u"sudo gedit {fpath}\n"
    u"@psychopy - nice -20\n"
    u"@psychopy - rtprio 50\n"
    u"@psychopy - memlock unlimited")
_cmdStr = _cmdStr.format(fpath=_confPath)


class LinuxConfigDialog(BaseLinuxConfigDialog):
    """Class for the Linux one-time setup dialog.

    This dialog appears to users running PsychoPy on Linux for the first time.
    It prompts the user to open a terminal and enter the indicated commands that
    configure the environment to run Psychtoolbox with optimal settings.

    This dialog will appear at startup until the user completes the
    configuration steps. We determine if configuration is complete by testing if
    the expected file is present at the required location.

    Parameters
    ----------
    parent : wx.Window or None
        Dialog parent.
    timeout : int or None
        Milliseconds to keep the dialog open. Setting to `None` keeps the dialog
        open. Specify a time if we're running in a test environment to prevent
        the UI from locking up the test suite.

    """
    def __init__(self, parent, timeout=None):
        BaseLinuxConfigDialog.__init__(self, parent)

        # intro text which provides instructions for the user
        self.lblIntro.SetLabel(_introStr)
        self.lblIntro.Wrap(640)

        # make the text box show the commands for the user to enter into their
        # terminal
        self.txtCmdList.SetValue(_cmdStr)
        self.txtCmdList.SetMinSize((320, 240))

        # redo the layout
        self.DoLayoutAdaptation()

        self.timeout = timeout

        if self.timeout is not None:
            timeout = wx.CallLater(self.timeout, self.Close)
            timeout.Start()

    def OnOpenTerminal(self, event):
        event.Skip()

    def OnCopy(self, event):
        """Called when the copy button is clicked.
        """
        # check if we have a selection
        start, end = self.txtCmdList.GetSelection()
        if start != end:
            txt = self.txtCmdList.GetStringSelection()
        else:
            txt = self.txtCmdList.GetValue()

        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(txt))
            wx.TheClipboard.Close()

        event.Skip()

    def OnDone(self, event):
        """Called when the 'Done' button is clicked.
        """
        if not linuxConfigFileExists():
            msgText = (
                u"Setup does not appear to be complete, would you like to "
                u"continue anyways?\nNote that PTB audio timing performance "
                u"may not be optimal this session until this configuration "
                u"step is completed."
            )
            # show dialog
            dlg = wx.MessageDialog(
                self,
                msgText,
                style=wx.YES_NO | wx.YES_DEFAULT
            )
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                self.Close()
            else:
                event.Skip()

            dlg.Destroy()


def linuxConfigFileExists():
    """Check if the required configuration file has been written.

    Returns
    -------
    bool
        `True` if the file exists or not on Linux.

    """
    # if not on linux, just pass it
    if sys.platform != 'linux':
        return True

    return os.path.isfile(_confPath)
