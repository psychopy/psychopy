"""ioHub.

.. file: ioHub/util/dialogs.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: ioHub Team

------------------------------------------------------------------------------------------------------------------------

"""
import os
import wx
import wx.lib.agw.genericmessagedialog as GMD
from pkg_resources import parse_version

class ioHubDialog(object):
    wxapp = None

    def __init__(self, display_index=0):
        self.dialog = None
        self.display_index = display_index
        if ioHubDialog.wxapp is None:
            if parse_version(wx.version()) < parse_version('2.9'):
                ioHubDialog.wxapp = wx.PySimpleApp()
            else:
                ioHubDialog.wxapp = wx.GetApp()
                if ioHubDialog.wxapp is None:
                    ioHubDialog.wxapp = wx.App(False)

    def set_frame_display(self):
        """Centers a wx window on the given Display index."""
        num_displays = wx.Display.GetCount()
        if self.display_index < 0:
            self.display_index = 0
        if self.display_index >= num_displays:
            self.display_index = 0
        x, y, w, h = wx.Display(self.display_index).GetGeometry()
        self.dialog.SetPosition((x, y))
        self.dialog.Center()

    def Destroy(self):
        if self.dialog is not None:
            self.dialog.Destroy()
            self.dialog = None

    def __del__(self):
        self.Destroy()
#
# ProgressBar
#

class ProgressBarDialog(ioHubDialog):
    """wx based progress bar interface."""

    def __init__(
            self,
            dialogTitle='Progress Dialog',
           dialogText='Percent Complete',
            maxValue=100.0,
            display_index=0):
        ioHubDialog.__init__(self, display_index)
        self.dialog = wx.ProgressDialog(
            dialogTitle,
            dialogText,
            maxValue,
            None,
            wx.PD_AUTO_HIDE | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME |
            wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME)

        self.set_frame_display()

        self.minimumValue = 0.0
        self.maximumValue = maxValue
        self.currentValue = self.minimumValue

    def updateStatus(self, value):
        self.dialog.Update(value)
        self.currentValue = value

    def close(self):
        self.Destroy()

    def getCurrentStatus(self):
        return self.currentValue

#
# MessageDialog
#


class MessageDialog(ioHubDialog):
    YES_NO_BUTTONS = wx.YES_NO
    OK_BUTTON = wx.OK
    CANCEL_BUTTON = wx.CANCEL
    YES_BUTTON = wx.YES
    NO_BUTTON = wx.NO

    INFORMATION_DIALOG = wx.ICON_INFORMATION
    WARNING_DIALOG = wx.ICON_WARNING
    IMPORTANT_DIALOG = wx.ICON_EXCLAMATION
    ERROR_DIALOG = wx.ICON_ERROR
    QUESTION_DIALOG = wx.ICON_QUESTION

    YES_RESULT = wx.ID_YES
    NO_RESULT = wx.ID_NO
    OK_RESULT = wx.ID_OK
    CANCEL_RESULT = wx.ID_CANCEL

    def __init__(self, msg, title=None, showButtons=wx.OK,
                 dialogType=wx.ICON_INFORMATION, allowCancel=True,
                 display_index=0):
        ioHubDialog.__init__(self, display_index)
        if showButtons not in [
                MessageDialog.YES_NO_BUTTONS,
                MessageDialog.OK_BUTTON]:
            raise AttributeError(
                'MessageDialog showButtons arg must be either MessageDialog.YES_NO_BUTTONS or MessageDialog.OK_BUTTON')
        if showButtons == MessageDialog.YES_NO_BUTTONS:
            showButtons |= wx.YES_DEFAULT
        if allowCancel:
            showButtons |= wx.CANCEL

        if dialogType not in [MessageDialog.INFORMATION_DIALOG,
                              MessageDialog.WARNING_DIALOG,
                              MessageDialog.IMPORTANT_DIALOG,
                              MessageDialog.ERROR_DIALOG,
                              MessageDialog.QUESTION_DIALOG]:
            raise AttributeError(
                'MessageDialog dialogType arg must one of MessageDialog.INFORMATION_DIALOG, MessageDialog.WARNING_DIALOG, MessageDialog.IMPORTANT_DIALOG, MessageDialog.ERROR_DIALOG, MessageDialog.QUESTION_DIALOG.')

        if title is None:
            if dialogType == MessageDialog.INFORMATION_DIALOG:
                title = 'For Your Information'
            elif dialogType == MessageDialog.WARNING_DIALOG:
                title = 'Warning'
            elif dialogType == MessageDialog.IMPORTANT_DIALOG:
                title = 'Important Note'
            elif dialogType == MessageDialog.ERROR_DIALOG:
                title = 'Error'
            elif dialogType == MessageDialog.QUESTION_DIALOG:
                title = 'Input Required'

        d = wx.Display(0)
        x, y, w, h = d.GetGeometry()
        d = None

        self.dialog = GMD.GenericMessageDialog(
            None, msg, title, showButtons | dialogType)  # , wrap=int(w/4))
        # TODO Change to own image
        import images
        self.dialog.SetIcon(images.Mondrian.GetIcon())

        self.set_frame_display()

    def show(self):
        result = self.dialog.ShowModal()
        self.Destroy()
        return result

#
# FileChooserDialog
#


class FileDialog(ioHubDialog):
    PYTHON_SCRIPT_FILES = 'Python source (*.py)|*.py'
    EXCEL_FILES = 'Spreadsheets (*.xls)|*.xls'
    IODATA_FILES = 'ioDataStore Files (*.hdf5)|*.hdf5'
    CONFIG_FILES = 'Configuration Files (*.yaml)|*.yaml'
    TEXT_FILES = 'Text Files (*.txt)|*.txt'
    ALL_FILES = 'All Files (*.*)|*.*'
    OK_RESULT = wx.ID_OK
    CANCEL_RESULT = wx.ID_CANCEL

    def __init__(
            self,
            message='Select a File',
            defaultDir=os.getcwd(),
            defaultFile='',
            openFile=True,
            allowMultipleSelections=False,
            allowChangingDirectories=True,
            fileTypes='All files (*.*)|*.*',
            display_index=0):
        ioHubDialog.__init__(self, display_index)
        dstyle = 0

        if openFile is True:
            dstyle = dstyle | wx.FD_OPEN
        if allowMultipleSelections is True:
            dstyle = dstyle | wx.MULTIPLE
        if allowChangingDirectories is True:
            dstyle = dstyle | wx.CHANGE_DIR

        fileTypesCombined = ''
        if isinstance(fileTypes, (list, tuple)):
            for ft in fileTypes:
                fileTypesCombined += ft
                fileTypesCombined += '|'
            fileTypesCombined = fileTypesCombined[:-1]

        self.dialog = wx.FileDialog(
            None, message=message,
            defaultDir=defaultDir,
            defaultFile=defaultFile,
            wildcard=fileTypesCombined,
            style=dstyle
        )

        self.set_frame_display()

    def show(self):
        result = self.dialog.ShowModal()
        selections = self.dialog.GetPaths()
        self.Destroy()
        return result, selections
