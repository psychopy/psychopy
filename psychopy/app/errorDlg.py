# -*- coding: utf-8 -*-
"""Error dialog for showing unhandled exceptions that occur within the PsychoPy
app."""

import wx
import traceback

_error_dlg_visible = False  # keep error dialogs from stacking


class ErrorMsgDialog(wx.Dialog):
    """Class for creating an error report dialog"""
    def __init__(self, parent, details=None):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"PsychoPy3 Error",
                           pos=wx.DefaultPosition, size=wx.Size(735, 118),
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.details = details
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        szErrorMsg = wx.BoxSizer(wx.VERTICAL)

        szHeader = wx.FlexGridSizer(0, 3, 0, 0)
        szHeader.AddGrowableCol(1)
        szHeader.SetFlexibleDirection(wx.BOTH)
        szHeader.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        self.imgErrorIcon = wx.StaticBitmap(self, wx.ID_ANY, wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_MESSAGE_BOX),
                                            wx.DefaultPosition, wx.DefaultSize, 0)
        szHeader.Add(self.imgErrorIcon, 0, wx.ALL, 5)

        self.lblErrorMsg = wx.StaticText(self, wx.ID_ANY,
                                         u"PsychoPy has encountered an unhandled internal error! Click \"Details\" to view the error report and please send it to the developers to help improve PsychoPy.",
                                         wx.DefaultPosition, wx.DefaultSize, 0)
        self.lblErrorMsg.Wrap(560)

        szHeader.Add(self.lblErrorMsg, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.cmdOK = wx.Button(self, wx.ID_OK, u"&OK", wx.DefaultPosition, wx.DefaultSize, 0)
        szHeader.Add(self.cmdOK, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        szErrorMsg.Add(szHeader, 0, wx.ALL | wx.EXPAND, 5)

        self.pnlDetails = wx.CollapsiblePane(self, wx.ID_ANY, u"&Details", wx.DefaultPosition, wx.DefaultSize,
                                             wx.CP_DEFAULT_STYLE)
        self.pnlDetails.Collapse(True)

        szDetailsPane = wx.BoxSizer(wx.VERTICAL)

        self.txtErrorOutput = wx.TextCtrl(self.pnlDetails.GetPane(), wx.ID_ANY, self.details, wx.DefaultPosition,
                                          wx.Size(640, 150),
                                          wx.TE_AUTO_URL | wx.TE_BESTWRAP | wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)

        szDetailsPane.Add(self.txtErrorOutput, 1, wx.ALL | wx.EXPAND, 5)

        szTextButtons = wx.BoxSizer(wx.HORIZONTAL)

        self.cmdCopyError = wx.Button(self.pnlDetails.GetPane(), wx.ID_ANY, u"&Copy", wx.DefaultPosition,
                                      wx.DefaultSize, 0)
        szTextButtons.Add(self.cmdCopyError, 0, wx.RIGHT, 5)

        self.cmdSaveError = wx.Button(self.pnlDetails.GetPane(), wx.ID_ANY, u"&Save", wx.DefaultPosition,
                                      wx.DefaultSize, 0)
        szTextButtons.Add(self.cmdSaveError, 0)

        szDetailsPane.Add(szTextButtons, 0, wx.ALL | wx.ALIGN_RIGHT, 5)

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
        self.cmdCopyError.Bind(wx.EVT_BUTTON, self.onCopyDetails)
        self.cmdSaveError.Bind(wx.EVT_BUTTON, self.onSaveDetails)

        # ding!
        wx.Bell()

    def __del__(self):
        pass

    def onOkay(self, event):
        event.Skip()

    def onCopyDetails(self, event):
        event.Skip()

    def onSaveDetails(self, event):
        event.Skip()


def exceptionCallback(exc_type, exc_value, exc_traceback):
    """Hook when an unhandled exception is raised within the current application
    thread. Gets the exception message and creates and error dialog box.

    """
    global _error_dlg_visible
    if not _error_dlg_visible:
        _error_dlg_visible = True
        # format the traceback text
        tbText = ''.join(traceback.format_exception(
            exc_type, exc_value, exc_traceback, limit=8))

        # show the dialog
        dlg = ErrorMsgDialog(None, details=tbText)
        dlg.ShowModal()
        dlg.Destroy()
        _error_dlg_visible = False
