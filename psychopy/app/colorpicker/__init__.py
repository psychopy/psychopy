# -*- coding: utf-8 -*-
"""Classes for the color picker."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import sys

import wx
import wx.stc as stc
from .panels import ColorPresets, ColorPreview
from .pages import ColorPickerPageHSV, ColorPickerPageRGB
from psychopy.colors import Color
from psychopy.localization import _translate

LAST_COLOR = Color((0, 0, 0, 1), space='rgba')
LAST_OUTPUT_SPACE = 0


class PsychoColorPicker(wx.Dialog):
    """Class for the color picker dialog.

    This dialog is used to standardize color selection across platforms. It also
    supports PsychoPy's RGB representation directly.

    Parameters
    ----------
    parent : object
        Reference to a :class:`~wx.Frame` which owns this dialog.

    """
    def __init__(self, parent, context=None):
        wx.Dialog.__init__(
            self,
            parent,
            id=wx.ID_ANY,
            title=_translate("Color Picker"),
            pos=wx.DefaultPosition,
            size=wx.Size(680, 480),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.parent = parent

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetMinSize(wx.Size(600, 480))

        # Store context
        self.context = context

        # current output color, should be displayed in the preview
        global LAST_COLOR
        self._color = LAST_COLOR.copy()

        # output spaces mapped to the `cboOutputSpace` object
        self._spaces = {
            0: 'rgb',
            1: 'rgb1',
            2: 'rgb255',
            3: 'hex',
            4: 'hsv'
        }
        # what to show in the output selection, maps to the spaces above
        self._outputChoices = [
            u'PsychoPy RGB (rgb)',
            u'Normalized RGB (rgb1)',
            u'8-bit RGB (rgb255)',
            u'Hex/HTML (hex)',
            u'Hue-Saturation-Value (hsv)'
        ]

        # initialize the window controls
        self._setupUI()

    @property
    def color(self):
        """Current color the user has specified. Should be reflected in the
        preview area. Value has type :class:`psychopy.colors.Color`.

        This is the primary setter for the dialog's color value. It will
        automatically update all color space pages to reflect this color value.
        Pages should absolutely not attempt to set other page's values directly
        or risk blowing up the call stack.

        """
        return self._color

    @color.setter
    def color(self, value):
        if value is None:
            value = Color('none', space='named')

        global LAST_COLOR
        self.pnlColorPreview.color = self._color = value
        LAST_COLOR = self._color.copy()
        self._updateColorSpacePage()

    def _updateColorSpacePage(self):
        """Update the current colorspace page to reflect the current color being
        specified by the dialog. Called only on the current page or when the
        page has been changed. Pointless to update all pages at once.

        """
        page = self.nbColorSpaces.GetCurrentPage()

        if hasattr(page, 'updateChannels'):
            page.updateChannels()

        if hasattr(page, 'updateHex'):
            page.updateHex()

    def _addColorSpacePages(self):
        """Add pages for each supported color space.

        In the future this will be modified to support plugging in additional
        color spaces. Right now the pages are hard-coded in.

        """
        self.pnlRGB = ColorPickerPageRGB(self.nbColorSpaces)
        self.pnlHSV = ColorPickerPageHSV(self.nbColorSpaces)

        self.nbColorSpaces.AddPage(self.pnlRGB, _translate(u"RGB"), True)
        self.nbColorSpaces.AddPage(self.pnlHSV, _translate(u"HSV"), False)

    def _setupUI(self):
        """Setup the UI for the color picker dialog box.

        """
        szrMain = wx.BoxSizer(wx.VERTICAL)

        # Color area panel. Shows the preview, colorspace pages and presets
        # panels at the top portion of the dialog.
        #
        self.pnlColorArea = wx.Panel(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.TAB_TRAVERSAL)

        szrColorArea = wx.BoxSizer(wx.HORIZONTAL)

        # color preview panel
        self.pnlColorPreview = ColorPreview(
            self.pnlColorArea, self._color)
        self.pnlColorPreview.SetMinSize(wx.Size(100, -1))
        self.pnlColorPreview.SetMaxSize(wx.Size(100, -1))

        # color space notebook area
        self.nbColorSpaces = wx.Notebook(
            self.pnlColorArea,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            0)

        self._addColorSpacePages()  # add the pages to the notebook

        # preset panel
        self.colorPresets = ColorPresets(self.pnlColorArea)
        self.colorPresets.SetMinSize(wx.Size(140, -1))
        self.colorPresets.SetMaxSize(wx.Size(140, -1))

        szrColorArea.Add(self.pnlColorPreview, 0, wx.EXPAND | wx.ALL, 5)
        szrColorArea.Add(
            self.nbColorSpaces, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)
        szrColorArea.Add(self.colorPresets, 0, wx.EXPAND | wx.ALL, 5)

        self.pnlColorArea.SetSizer(szrColorArea)
        self.pnlColorArea.Layout()
        szrColorArea.Fit(self.pnlColorArea)
        szrMain.Add(self.pnlColorArea, 1, wx.ALL| wx.EXPAND, 5)

        # line to divide the color area from the dialog controls, looks neat
        self.stlMain = wx.StaticLine(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL)

        szrMain.Add(self.stlMain, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # Dialog controls area. Shows buttons for closing the dialog or copying
        # colors. Also shows the output format to use when copying to the
        # clipboard.
        #
        szrDlgButtonArea = wx.BoxSizer(wx.VERTICAL)
        szrDlgCtrls = wx.FlexGridSizer(1, 5, 0, 5)
        szrDlgCtrls.AddGrowableCol(1)
        szrDlgCtrls.SetFlexibleDirection(wx.BOTH)
        szrDlgCtrls.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        self.lblResult = wx.StaticText(
            self,
            wx.ID_ANY,
            _translate("Output Space:"),
            wx.DefaultPosition,
            wx.DefaultSize,
            0)
        self.lblResult.Wrap(-1)

        szrDlgCtrls.Add(
            self.lblResult,
            0,
            wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL,
            5)

        self.cboOutputSpace = wx.Choice(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            choices=self._outputChoices)
        self.cboOutputSpace.SetSelection(LAST_OUTPUT_SPACE)

        szrDlgCtrls.Add(self.cboOutputSpace, 1, wx.ALIGN_CENTER_VERTICAL, 5)

        self.cmdInsertColor = wx.Button(
            self, wx.ID_ANY, _translate(u"&Insert"), wx.DefaultPosition,
            wx.DefaultSize, 0)
        self.cmdCopy = wx.Button(
            self, wx.ID_ANY, _translate(u"&Copy"), wx.DefaultPosition,
            wx.DefaultSize, 0)
        self.cmdClose = wx.Button(
            self, wx.ID_ANY, _translate(u"Canc&el"), wx.DefaultPosition, wx.DefaultSize, 0)

        self.cmdInsertColor.SetToolTip(
            _translate(u"Insert color value."))
        self.cmdCopy.SetToolTip(
            _translate(u"Copy color value to clipboard."))

        if sys.platform == "win32":
            btns = [self.cmdCopy, self.cmdInsertColor, self.cmdClose]
        else:
            btns = [self.cmdClose, self.cmdCopy, self.cmdInsertColor]
        szrDlgCtrls.Add(btns[0], 0, wx.EXPAND, 5)
        szrDlgCtrls.Add(btns[1], 0, wx.EXPAND, 5)
        szrDlgCtrls.Add(btns[2], 0, wx.EXPAND, 5)

        szrDlgButtonArea.Add(szrDlgCtrls, 1, wx.ALL | wx.EXPAND, 5)

        szrMain.Add(szrDlgButtonArea, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(szrMain)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.nbColorSpaces.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChanged)
        self.cmdInsertColor.Bind(wx.EVT_BUTTON, self.onInsertValue)
        self.cmdCopy.Bind(wx.EVT_BUTTON, self.onCopyValue)
        self.cboOutputSpace.Bind(
            wx.EVT_CHOICE, self.onOutputSpaceChanged)
        self.cmdClose.Bind(wx.EVT_BUTTON, self.onClose)

        # disable insert if parent is not a valid context, allow copying though
        if self.parent is None:
            self.cmdInsertColor.Enable(False)

    def _copyToClipboard(self, text):
        """Copy text to the clipboard.

        Shows an error dialog if the clipboard cannot be opened to inform the
        user the values have not been copied.

        Parameters
        ----------
        text : str
            Text to copy to the clipboard.

        """
        # copy the value to the clipboard
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(str(text)))
            wx.TheClipboard.Close()
        else:
            # Raised if the clipboard fails to open, warns the user the value
            # wasn't copied.
            errDlg = wx.MessageDialog(
                self,
                'Failed to open the clipboard, output value not copied.',
                'Clipboard Error',
                wx.OK | wx.ICON_ERROR)
            errDlg.ShowModal()
            errDlg.Destroy()

    def getOutputValue(self):
        """Get the string value using the specified output format.

        Returns
        -------
        str
            Color value using the current output format.

        """
        outputSpace = self.cboOutputSpace.GetSelection()
        dlgCol = self.GetTopLevelParent().color
        if outputSpace == 0:  # RGB
            colorOut = '{:.4f}, {:.4f}, {:.4f}'.format(*dlgCol.rgb)
        elif outputSpace == 1:  # RGB1
            colorOut = '{:.4f}, {:.4f}, {:.4f}'.format(*dlgCol.rgb1)
        elif outputSpace == 2:  # RGB255
            colorOut = '{:d}, {:d}, {:d}'.format(
                *[int(i) for i in dlgCol.rgb255])
        elif outputSpace == 3:  # Hex
            colorOut = "'{}'".format(dlgCol.hex)
        elif outputSpace == 4:  # HSV
            colorOut = '{:.4f}, {:.4f}, {:.4f}'.format(*dlgCol.hsv)
        else:
            raise ValueError(
                "Invalid output color space selection. Have you added any "
                "choices to `cboOutputSpace`?")

        return colorOut

    def onOutputSpaceChanged(self, event):
        """Set when the output space choicebox is changed."""
        global LAST_OUTPUT_SPACE
        LAST_OUTPUT_SPACE = event.GetSelection()
        event.Skip()

    def onPageChanged(self, event):
        """Called when the color space notebook is changed. Updates the current
        page to show values appropriate for the current color specified by the
        dialog.

        """
        self._updateColorSpacePage()
        event.Skip()

    def onInsertValue(self, event):
        """Event to copy the color to the clipboard as a an object.

        """
        if isinstance(self.parent, wx.TextCtrl):
            self.parent.SetValue(self.getOutputValue())
        elif isinstance(self.parent, stc.StyledTextCtrl):
            self.parent.InsertText(
                self.parent.GetCurrentPos(), "(" + self.getOutputValue() + ")")

        self.Close()
        event.Skip()

    def onCopyValue(self, event):
        """Event to copy the color to the clipboard as a value.

        """
        self._copyToClipboard(self.getOutputValue())  # copy out to clipboard
        self.Close()
        event.Skip()

    def onClose(self, event):
        """Called when the cancel button is clicked."""
        self.Close()
        event.Skip()


if __name__ == "__main__":
    pass
