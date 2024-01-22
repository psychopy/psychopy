#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Error dialog for showing unhandled exceptions that occur within the PsychoPy
app."""
from requests.exceptions import ConnectionError, ReadTimeout
import wx
import traceback
import psychopy.preferences
import sys
from psychopy.localization import _translate


_error_dlg = None  # keep error dialogs from stacking


class ErrorMsgDialog(wx.Dialog):
    """Class for creating an error report dialog. Should never be created
    directly.
    """
    def __init__(self, parent, traceback=''):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY,
                           title=_translate(u"PsychoPy3 Error"),
                           pos=wx.DefaultPosition, size=wx.Size(750, -1),
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.details = traceback

        # message to show at the top of the error box, needs translation
        msg = _translate(u"PsychoPy encountered an unhandled internal error! " \
                u"Please send the report under \"Details\" to the " \
                u"developers with a description of what you were doing " \
                u"with the software when the error occurred.")

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        szErrorMsg = wx.BoxSizer(wx.VERTICAL)
        szHeader = wx.FlexGridSizer(0, 3, 0, 0)
        szHeader.AddGrowableCol(1)
        szHeader.SetFlexibleDirection(wx.BOTH)
        szHeader.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
        self.imgErrorIcon = wx.StaticBitmap(
            self, wx.ID_ANY, wx.ArtProvider.GetBitmap(
                wx.ART_ERROR, wx.ART_MESSAGE_BOX),
            wx.DefaultPosition, wx.DefaultSize, 0)
        szHeader.Add(self.imgErrorIcon, 0, wx.ALL, 5)
        self.lblErrorMsg = wx.StaticText(
            self, wx.ID_ANY, msg, wx.DefaultPosition, wx.DefaultSize, 0)
        self.lblErrorMsg.Wrap(560)
        szHeader.Add(self.lblErrorMsg, 0, wx.ALL, 5)
        szHeaderButtons = wx.BoxSizer(wx.VERTICAL)
        self.cmdOK = wx.Button(
            self, wx.ID_OK, _translate(u"&OK"), wx.DefaultPosition, wx.DefaultSize, 0)
        szHeaderButtons.Add(self.cmdOK, 0, wx.LEFT | wx.EXPAND, 5)
        self.cmdExit = wx.Button(
            self, wx.ID_EXIT, _translate(u"E&xit PsychoPy"), wx.DefaultPosition,
            wx.DefaultSize, 0)
        szHeaderButtons.Add(self.cmdExit, 0, wx.TOP | wx.LEFT | wx.EXPAND, 5)
        szHeader.Add(szHeaderButtons, 0, wx.ALL | wx.EXPAND, 5)
        szErrorMsg.Add(szHeader, 0, wx.TOP | wx.LEFT | wx.RIGHT | wx.EXPAND, 5)

        self.pnlDetails = wx.CollapsiblePane(
            self, wx.ID_ANY, _translate(u"&Details"), wx.DefaultPosition, wx.DefaultSize,
            wx.CP_DEFAULT_STYLE)
        self.pnlDetails.Collapse(True)
        szDetailsPane = wx.BoxSizer(wx.VERTICAL)
        self.txtErrorOutput = wx.TextCtrl(
            self.pnlDetails.GetPane(), wx.ID_ANY, self.details,
            wx.DefaultPosition, wx.Size(640, 150),
            wx.TE_AUTO_URL | wx.TE_BESTWRAP | wx.TE_MULTILINE | wx.TE_READONLY |
            wx.TE_WORDWRAP)
        szDetailsPane.Add(self.txtErrorOutput, 1, wx.ALL | wx.EXPAND, 5)
        szTextButtons = wx.BoxSizer(wx.HORIZONTAL)
        self.cmdCopyError = wx.Button(
            self.pnlDetails.GetPane(), wx.ID_ANY, _translate(u"&Copy"), wx.DefaultPosition,
            wx.DefaultSize, 0)
        szTextButtons.Add(self.cmdCopyError, 0, wx.RIGHT, 5)
        self.cmdSaveError = wx.Button(
            self.pnlDetails.GetPane(), wx.ID_ANY, _translate(u"&Save"), wx.DefaultPosition,
            wx.DefaultSize, 0)
        szTextButtons.Add(self.cmdSaveError, 0)
        szDetailsPane.Add(szTextButtons, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        self.pnlDetails.Expand()
        self.pnlDetails.GetPane().SetSizer(szDetailsPane)
        self.pnlDetails.GetPane().Layout()
        szDetailsPane.Fit(self.pnlDetails.GetPane())
        szErrorMsg.Add(self.pnlDetails, 1, wx.ALL | wx.BOTTOM | wx.EXPAND, 5)

        self.SetSizer(szErrorMsg)
        self.Layout()
        self.Fit()

        self.Centre(wx.BOTH)

        # Connect Events
        self.cmdOK.Bind(wx.EVT_BUTTON, self.onOkay)
        self.cmdExit.Bind(wx.EVT_BUTTON, self.onExit)
        self.cmdCopyError.Bind(wx.EVT_BUTTON, self.onCopyDetails)
        self.cmdSaveError.Bind(wx.EVT_BUTTON, self.onSaveDetails)

        # ding!
        wx.Bell()

    def __del__(self):
        pass

    def onOkay(self, event):
        """Called when OK is clicked."""
        event.Skip()

    def onExit(self, event):
        """Called when the user requests to close PsychoPy. This can be called
        if the error if unrecoverable or if the errors are being constantly
        generated.

        Will try to close things safely, allowing the user to save files while
        suppressing further errors.

        """
        dlg = wx.MessageDialog(
            self,
            _translate("Are you sure you want to exit PsychoPy? Unsaved work may be lost "
            "(but we'll try to save opened files)."),
            _translate("Exit PsychoPy?"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING | wx.CENTRE)
        if dlg.ShowModal() == wx.ID_YES:
            wx.GetApp().quit()
            # wx.Exit()  # nuclear option
        else:
            dlg.Destroy()
            event.Skip()

    def onCopyDetails(self, event):
        """Copy the contents of the details text box to the clipboard. This is
        to allow the user to paste the traceback into an email, forum post,
        issue ticket, etc. to report the error to the developers. If there is a
        selection range, only that text will be copied.

        """
        # check if we have a selection
        start, end = self.txtErrorOutput.GetSelection()
        if start != end:
            txt = self.txtErrorOutput.GetStringSelection()
        else:
            txt = self.txtErrorOutput.GetValue()

        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(txt))
            wx.TheClipboard.Close()

        event.Skip()

    def onSaveDetails(self, event):
        """Dump the traceback data to a file. This can be used to save the error
        data so it can be reported to the developers at a later time. Brings up
        a file save dialog to select where to write the file.

        """
        with wx.FileDialog(
                self, _translate("Save error traceback"),
                wildcard="Text files (*.txt)|*.txt",
                defaultFile='psychopy_traceback.txt',
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # dump traceback to file
            pathname = fileDialog.GetPath()
            try:
                with open(pathname, 'w') as file:
                    file.write(self.txtErrorOutput.GetValue())
            except IOError:
                # error in an error ... ;)
                errdlg = wx.MessageDialog(
                    self,
                    _translate("Cannot save to file '%s'.") % pathname,
                    _translate("File save error"),
                    wx.OK_DEFAULT | wx.ICON_ERROR | wx.CENTRE)
                errdlg.ShowModal()
                errdlg.Destroy()

        event.Skip()


def isErrorDialogVisible():
    """Check if the error dialog is open. This can be used to prevent background
    routines from running while the user deals with an error.

    Returns
    -------
    bool
        Error dialog is currently active.

    """
    return _error_dlg is not None


def exceptionCallback(exc_type: object, exc_value: object, exc_traceback: object) -> object:
    """Hook when an unhandled exception is raised within the current application
    thread. Gets the exception message and creates an error dialog box.

    When this function is patched into `sys.excepthook`, all unhandled
    exceptions will result in a dialog being displayed.

    """
    # Catch connection errors
    if exc_type in (ConnectionError, ReadTimeout):
        dlg = wx.MessageDialog(parent=None, caption=_translate("Connection Error"), message=_translate(
            "Could not connect to Pavlovia server. \n"
            "\n"
            "Please check that you are connected to the internet. If you are connected, then the Pavlovia servers may be down. You can check their status here: \n"
            "\n"
            "https://pavlovia.org/status"
        ), style=wx.ICON_ERROR)
        dlg.ShowModal()
        return

    if psychopy.preferences.prefs.app['errorDialog'] is False:
        # have the error go out to stdout if dialogs are disabled
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout)
        return

    global _error_dlg
    if not isErrorDialogVisible():
        # format the traceback text
        tbText = ''.join(traceback.format_exception(
            exc_type, exc_value, exc_traceback))
        _error_dlg = ErrorMsgDialog(None, tbText)

        # show the dialog
        _error_dlg.ShowModal()
        _error_dlg.Destroy()
        _error_dlg = None
