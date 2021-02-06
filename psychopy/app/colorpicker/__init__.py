# -*- coding: utf-8 -*-
"""Classes for the color picker."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
from wx.lib.buttons import GenButton
from wx.lib.scrolledpanel import ScrolledPanel
import numpy as np

from psychopy.app.themes import ThemeMixin
from psychopy.colors import Color, colorNames


class ColorPresets(ScrolledPanel):
    """Class for creating a scrollable button list that displays all preset
    colors.

    """
    def __init__(self, parent):
        ScrolledPanel.__init__(
            self,
            parent,
            size=wx.Size(120, -1),
            style=wx.VSCROLL | wx.BORDER_NONE)

        self.parent = parent
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self._createColorButtons()
        self.SetSizer(self.sizer)
        self.SetupScrolling()

    def _createColorButtons(self):
        """Generate color buttons based on the presets defined in the `colors`
        module.

        When a user clicks on the buttons, it changes the current color the
        colorspace page is displaying.
        """
        # create buttons for each preset color
        colorList = list(colorNames)
        btnSize = wx.Size(120, 24)
        for color in colorList:
            btn = GenButton(self, size=btnSize, label=color, name=color)
            btn.colorData = col = Color(color, 'named')
            btn.SetOwnBackgroundColour(col.rgba255)

            # Compute the (perceived) luminance of the color, used to set the
            # foreground text to ensure it's legible on the background. Uses the
            # the luminance part of formula to convert RGB1 to YIQ.
            luminance = np.sum(np.asarray((0.299, 0.587, 0.114)) * col.rgb1)
            if luminance < 0.5:
                btn.SetForegroundColour(wx.WHITE)
            else:
                btn.SetForegroundColour(wx.BLACK)

            btn.SetBezelWidth(0)
            btn.SetUseFocusIndicator(False)
            btn.Bind(wx.EVT_BUTTON, self.onClick)
            self.sizer.Add(btn, 1, wx.ALL | wx.EXPAND, 0)

    def onClick(self, event):
        #self.parent.setColor(event.GetEventObject().colorData, 'named')
        event.Skip()


class ColorPreview(wx.Panel):
    """Class for the color preview panel in the color picker.

    This panel displays the current color specified by the user. A background
    checkerboard pattern is drawn as a background making transparency more
    apparent.

    """
    def __init__(self, parent, color):
        wx.Panel.__init__(self, parent, size=(100, -1))
        # self.SetBackgroundColour(ThemeMixin.appColors['frame_bg'])

        self.parent = parent
        self.SetDoubleBuffered(True)
        self.color = color
        self.pdc = wx.PaintDC(self)
        self.dc = wx.GCDC(self.pdc)
        self.Bind(wx.EVT_PAINT, self.onPaint)

    @property
    def color(self):
        """Color being displayed (:class:`~psychopy.colors.Color`)."""
        return self._color

    @color.setter
    def color(self, value):
        self._color = value
        self.Refresh()

    def onPaint(self, event):
        """Called each time the preview is updated or `color` is changed. Bound
        to `EVT_PAINT`. The background is only drawn if the color is
        transparent.
        """
        # self.pdc.SetBrush(wx.Brush(ThemeMixin.appColors['panel_bg']))
        # self.pdc.SetPen(wx.Pen(ThemeMixin.appColors['panel_bg']))

        # only draw background if there is transparency
        if self._color.alpha < 1.0:
            self._paintCheckerboard()

        self._paintPreviewColor()

    def _paintPreviewColor(self):
        """Paint the current color. Called when `onPaint` is invoked, but after
        the checkerboard is drawn.
        """
        # originally written by Todd Parsons
        self.dc.SetBrush(
            wx.Brush(list(self.color.rgb255) + [self.color.alpha * 255],
                     wx.BRUSHSTYLE_TRANSPARENT))
        self.dc.SetPen(
            wx.Pen(list(self.color.rgb255) + [self.color.alpha * 255],
                   wx.PENSTYLE_TRANSPARENT))
        self.dc.DrawRectangle(0, 0, self.GetSize()[0], self.GetSize()[1])

    def _paintCheckerboard(self, gridRes=10):
        """Paint the background checkerboard grid of the color preview area.
        this provides a background to make the effect of adjusting the alpha
        channel more apparent.

        Must be called within the `onPaint` method only when the color is
        transparent. Don't call elsewhere.

        Parameters
        ----------
        gridRes : int
            Width and height of each grid square.

        """
        # originally written by Todd Parsons
        w = h = gridRes
        for x in range(0, self.GetSize()[0], w*2):
            for y in range(0 + (x % 2) * h, self.GetSize()[1], h * 2):
                self.pdc.DrawRectangle(x, y, w, h)
                self.pdc.DrawRectangle(x + w, y + h, w, h)


class PsychoColorPicker(wx.Dialog):
    """Class for the color picker dialog.

    This dialog is used to standardize color selection across platforms. It also
    supports PsychoPy's RGB representation directly.

    Parameters
    ----------
    parent : object
        Reference to a :class:`~wx.Frame` which owns this dialog.

    """
    def __init__(self, parent):
        wx.Dialog.__init__(
            self,
            parent,
            id=wx.ID_ANY,
            title=u"Color Picker",
            pos=wx.DefaultPosition,
            size=wx.Size(640, 480),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetMinSize(wx.Size(480, 480))

        # current output color, should be displayed in the preview
        self._color = Color((0, 0, 0, 1), space='rgba')

        # initialize the window controls
        self._setupUI()

    def __del__(self):
        pass

    @property
    def color(self):
        """Current color the user has specified. Should be reflected in the
        preview area. Value has type :class:`psychopy.colors.Color`."""
        return self._color

    @color.setter
    def color(self, value):
        self.pnlColorPreview.color = self._color = value

    def _updateColorSpacePages(self):
        """Update all the color space pages to reflect the current value for
        `color`."""
        pass

    def _addColorSpacePages(self):
        """Add pages for each supported color space.

        In the future this will be modified to support plugging in additional
        colorspaces. Right now the pages are hard-coded in.

        """
        self.pnlRGB = ColorPickerPageRGB(self.nbColorSpaces)
        self.pnlHSV = wx.Panel(
            self.nbColorSpaces,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.TAB_TRAVERSAL)

        self.nbColorSpaces.AddPage(self.pnlRGB, u"RGB", True)
        self.nbColorSpaces.AddPage(self.pnlHSV, u"HSV", False)

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
        szrColorArea.Add(self.nbColorSpaces, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)
        szrColorArea.Add(self.colorPresets, 0, wx.EXPAND | wx.ALL, 5)

        self.pnlColorArea.SetSizer(szrColorArea)
        self.pnlColorArea.Layout()
        szrColorArea.Fit(self.pnlColorArea)
        szrMain.Add(self.pnlColorArea, 1, wx.EXPAND, 5)

        # line to divide the color area from the dialog controls, looks neat
        self.stlMain = wx.StaticLine(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.LI_HORIZONTAL)

        szrMain.Add(self.stlMain, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

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
            u"Result (RGBA):",
            wx.DefaultPosition,
            wx.DefaultSize,
            0)
        self.lblResult.Wrap(-1)

        szrDlgCtrls.Add(
            self.lblResult,
            0,
            wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL,
            5)

        self.txtResult = wx.TextCtrl(
            self,
            wx.ID_ANY,
            u"",
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.TE_READONLY)

        szrDlgCtrls.Add(
            self.txtResult, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)

        self.cmdCopyObject = wx.Button(
            self, wx.ID_ANY, u"Copy as &Object", wx.DefaultPosition,
            wx.DefaultSize, 0)

        szrDlgCtrls.Add(self.cmdCopyObject, 0, wx.EXPAND, 5)

        self.cmdCopy = wx.Button(
            self, wx.ID_ANY, u"Copy as &Value", wx.DefaultPosition,
            wx.DefaultSize, 0)

        szrDlgCtrls.Add(self.cmdCopy, 0, wx.EXPAND, 5)

        self.cmdClose = wx.Button(
            self, wx.ID_ANY, u"Clos&e", wx.DefaultPosition, wx.DefaultSize, 0)
        szrDlgCtrls.Add(self.cmdClose, 0, wx.EXPAND, 5)

        szrDlgButtonArea.Add(szrDlgCtrls, 1, wx.ALL | wx.EXPAND, 5)

        szrMain.Add(szrDlgButtonArea, 0, wx.EXPAND, 5)

        self.SetSizer(szrMain)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.nbColorSpaces.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChanged)
        self.nbColorSpaces.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.onPageChanging)
        self.cmdCopyObject.Bind(wx.EVT_BUTTON, self.onCopyObject)
        self.cmdCopy.Bind(wx.EVT_BUTTON, self.onCopyValue)
        self.cmdClose.Bind(wx.EVT_BUTTON, self.onClose)

    def onPageChanged(self, event):
        event.Skip()

    def onPageChanging(self, event):
        event.Skip()

    def onCopyObject(self, event):
        event.Skip()

    def onCopyValue(self, event):
        event.Skip()

    def onClose(self, event):
        event.Skip()


class ColorPickerPageRGB(wx.Panel):
    """Class for the RGB page of the color picker.
    """
    def __init__(self,
                 parent,
                 id=wx.ID_ANY,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.TAB_TRAVERSAL,
                 name=wx.EmptyString):
        wx.Panel.__init__(
            self, parent, id=id, pos=pos, size=size, style=style, name=name)

        # reference to the color picker dialog or some other container
        self.colorPickerDlg = self.GetTopLevelParent()

        # Functions to convert slider units to an RGB format to display in the
        # double-spin controls beside them.
        self._posToValFunc = {0: lambda v: 2 * (v / 255.) - 1,  # [-1:1]
                              1: lambda v: v / 255.,  # [0:1]
                              2: lambda v: v}  # [0:255]

        # inverse of the above functions, converts values to positions
        self._valToPosFunc = {0: lambda p: int(255 * (p + 1) / 2.),  # [-1:1]
                              1: lambda p: int(p * 255),  # [0:1]
                              2: lambda p: int(p)}  # [0:255]

        self._initUI()  # setup the UI controls

    def _initUI(self):
        """Initialize window controls. Called once when the page is created.
        """
        szrRGBPage = wx.BoxSizer(wx.VERTICAL)

        fraRGBChannels = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, u"Channels"), wx.VERTICAL)

        szrRGBArea = wx.FlexGridSizer(4, 3, 5, 5)
        szrRGBArea.AddGrowableCol(1)
        szrRGBArea.SetFlexibleDirection(wx.BOTH)
        szrRGBArea.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        self.lblRed = wx.StaticText(fraRGBChannels.GetStaticBox(), wx.ID_ANY, u"Red", wx.DefaultPosition,
                                    wx.DefaultSize, 0)
        self.lblRed.Wrap(-1)

        szrRGBArea.Add(self.lblRed, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)

        self.sldRed = wx.Slider(fraRGBChannels.GetStaticBox(), wx.ID_ANY, 127, 0, 255, wx.DefaultPosition,
                                wx.DefaultSize, wx.SL_HORIZONTAL)
        szrRGBArea.Add(self.sldRed, 0, wx.EXPAND, 5)

        self.spnRed = wx.SpinCtrlDouble(fraRGBChannels.GetStaticBox(), wx.ID_ANY, u"0", wx.DefaultPosition,
                                        wx.DefaultSize, wx.SP_ARROW_KEYS, -1, 1, 0, 0.05)
        self.spnRed.SetDigits(4)
        szrRGBArea.Add(self.spnRed, 0, 0, 5)

        self.lblGreen = wx.StaticText(fraRGBChannels.GetStaticBox(), wx.ID_ANY, u"Green", wx.DefaultPosition,
                                      wx.DefaultSize, 0)
        self.lblGreen.Wrap(-1)

        szrRGBArea.Add(self.lblGreen, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)

        self.sldGreen = wx.Slider(fraRGBChannels.GetStaticBox(), wx.ID_ANY, 127, 0, 255, wx.DefaultPosition,
                                  wx.DefaultSize, wx.SL_HORIZONTAL)
        szrRGBArea.Add(self.sldGreen, 0, wx.EXPAND, 5)

        self.spnGreen = wx.SpinCtrlDouble(fraRGBChannels.GetStaticBox(), wx.ID_ANY, u"0", wx.DefaultPosition,
                                          wx.DefaultSize, wx.SP_ARROW_KEYS, -1, 1, 0, 0.05)
        self.spnGreen.SetDigits(4)
        szrRGBArea.Add(self.spnGreen, 0, 0, 5)

        self.lblBlue = wx.StaticText(fraRGBChannels.GetStaticBox(), wx.ID_ANY, u"Blue", wx.DefaultPosition,
                                     wx.DefaultSize, 0)
        self.lblBlue.Wrap(-1)

        szrRGBArea.Add(self.lblBlue, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)

        self.sldBlue = wx.Slider(fraRGBChannels.GetStaticBox(), wx.ID_ANY, 127, 0, 255, wx.DefaultPosition,
                                 wx.DefaultSize, wx.SL_HORIZONTAL)
        szrRGBArea.Add(self.sldBlue, 0, wx.EXPAND, 5)

        self.spnBlue = wx.SpinCtrlDouble(fraRGBChannels.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                         wx.DefaultSize, wx.SP_ARROW_KEYS, -1, 1, 0, 0.05)
        self.spnBlue.SetDigits(4)
        szrRGBArea.Add(self.spnBlue, 0, 0, 5)

        self.lblAlpha = wx.StaticText(fraRGBChannels.GetStaticBox(), wx.ID_ANY, u"Alpha", wx.DefaultPosition,
                                      wx.DefaultSize, 0)
        self.lblAlpha.Wrap(-1)

        szrRGBArea.Add(self.lblAlpha, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)

        self.sldAlpha = wx.Slider(fraRGBChannels.GetStaticBox(), wx.ID_ANY, 255, 0, 255, wx.DefaultPosition,
                                  wx.DefaultSize, wx.SL_HORIZONTAL)
        szrRGBArea.Add(self.sldAlpha, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)

        self.spnAlpha = wx.SpinCtrlDouble(fraRGBChannels.GetStaticBox(), wx.ID_ANY, u"1", wx.DefaultPosition,
                                          wx.DefaultSize, wx.SP_ARROW_KEYS, -1, 1, 1, 0.05)
        self.spnAlpha.SetDigits(4)
        szrRGBArea.Add(self.spnAlpha, 0, 0, 5)

        fraRGBChannels.Add(szrRGBArea, 1, wx.ALL | wx.EXPAND, 5)

        szrRGBPage.Add(fraRGBChannels, 0, wx.TOP | wx.LEFT | wx.RIGHT | wx.EXPAND, 5)

        szrRGBOptions = wx.BoxSizer(wx.HORIZONTAL)

        fraHexRGB = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, u"Hex"), wx.VERTICAL)

        self.spnHex = wx.SpinCtrl(fraHexRGB.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                  wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0)
        fraHexRGB.Add(self.spnHex, 0, wx.ALL | wx.EXPAND, 5)

        szrRGBOptions.Add(fraHexRGB, 2, 0, 5)

        rbxRGBModeChoices = [u"PsychoPy RGBA [-1:1]", u"Normalized RGBA [0:1]", u"8-Bit RGBA [0:255]"]
        self.rbxRGBFormat = wx.RadioBox(self, wx.ID_ANY, u"Channel Format", wx.DefaultPosition, wx.DefaultSize, rbxRGBModeChoices,
                                        1, wx.RA_SPECIFY_COLS)
        self.rbxRGBFormat.SetSelection(0)
        szrRGBOptions.Add(self.rbxRGBFormat, 0, wx.LEFT, 5)

        szrRGBPage.Add(szrRGBOptions, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(szrRGBPage)
        self.Layout()

        # Connect Events
        self.sldRed.Bind(wx.EVT_SCROLL, self.onRedScroll)
        self.spnRed.Bind(wx.EVT_SPINCTRLDOUBLE, self.onRedUpdate)
        self.spnRed.Bind(wx.EVT_TEXT_ENTER, self.onRedUpdate)
        self.sldGreen.Bind(wx.EVT_SCROLL, self.onGreenScroll)
        self.spnGreen.Bind(wx.EVT_SPINCTRLDOUBLE, self.onGreenUpdate)
        self.spnGreen.Bind(wx.EVT_TEXT_ENTER, self.onGreenUpdate)
        self.sldBlue.Bind(wx.EVT_SCROLL, self.onBlueScroll)
        self.spnBlue.Bind(wx.EVT_SPINCTRLDOUBLE, self.onBlueUpdate)
        self.spnBlue.Bind(wx.EVT_TEXT_ENTER, self.onBlueUpdate)
        self.sldAlpha.Bind(wx.EVT_SCROLL, self.onAlphaScroll)
        self.spnAlpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.onAlphaUpdate)
        self.spnAlpha.Bind(wx.EVT_TEXT_ENTER, self.onAlphaUpdate)
        self.spnHex.Bind(wx.EVT_SPINCTRL, self.onHexChanged)
        self.rbxRGBFormat.Bind(wx.EVT_RADIOBOX, self.onRGBMode)

    def __del__(self):
        pass

    def getRGBA(self):
        """Get the current RGBA color being displayed on the page.

        Returns
        -------
        tuple
            RGBA color.

        """
        convFunc = self._valToPosFunc[self.rbxRGBFormat.GetSelection()]
        return (convFunc(self.spnRed.GetValue()),
                convFunc(self.spnGreen.GetValue()),
                convFunc(self.spnBlue.GetValue()),
                convFunc(self.spnAlpha.GetValue()))

    def updateResultField(self):
        """Update the result field of the parent dialog."""
        if hasattr(self.colorPickerDlg, 'txtResult'):
            self.colorPickerDlg.txtResult.Value = str(self.getRGBA())

        if hasattr(self.colorPickerDlg, 'pnlColorPreview'):
            self.colorPickerDlg.pnlColorPreview.color.rgba255 = self.getRGBA()
            self.colorPickerDlg.pnlColorPreview.color.alpha = self.getRGBA()[3] / 255.
            self.colorPickerDlg.pnlColorPreview.Refresh()

    def onRedScroll(self, event):
        self.spnRed.SetValue(
            self._posToValFunc[self.rbxRGBFormat.GetSelection()](event.Position))
        self.updateResultField()

    def onRedUpdate(self, event):
        self.sldRed.SetValue(
            self._valToPosFunc[self.rbxRGBFormat.GetSelection()](event.Value))
        self.updateResultField()

    def onGreenScroll(self, event):
        self.spnGreen.SetValue(
            self._posToValFunc[self.rbxRGBFormat.GetSelection()](event.Position))
        self.updateResultField()

    def onGreenUpdate(self, event):
        self.sldGreen.SetValue(
            self._valToPosFunc[self.rbxRGBFormat.GetSelection()](event.Value))
        self.updateResultField()

    def onBlueScroll(self, event):
        self.spnBlue.SetValue(
            self._posToValFunc[self.rbxRGBFormat.GetSelection()](event.Position))
        self.updateResultField()

    def onBlueUpdate(self, event):
        self.sldBlue.SetValue(
            self._valToPosFunc[self.rbxRGBFormat.GetSelection()](event.Value))
        self.updateResultField()

    def onAlphaScroll(self, event):
        self.spnAlpha.SetValue(
            self._posToValFunc[self.rbxRGBFormat.GetSelection()](event.Position))
        self.updateResultField()

    def onAlphaUpdate(self, event):
        self.sldAlpha.SetValue(
            self._valToPosFunc[self.rbxRGBFormat.GetSelection()](event.Value))
        self.updateResultField()

    def onHexChanged(self, event):
        event.Skip()

    def onRGBMode(self, event):
        """Called when the RGB mode is changed."""
        convFunc = self._posToValFunc[event.GetSelection()]

        # update spinner values/ranges for each channel
        for spn in (self.spnRed, self.spnGreen, self.spnBlue, self.spnAlpha):
            spn.SetDigits(0 if event.GetSelection() == 2 else 4)
            spn.SetIncrement(1 if event.GetSelection() == 2 else 0.05)
            spn.SetMin(convFunc(0))
            spn.SetMax(convFunc(255))

        # set the value in the new range
        self.spnRed.SetValue(convFunc(self.sldRed.Value))
        self.spnGreen.SetValue(convFunc(self.sldGreen.Value))
        self.spnBlue.SetValue(convFunc(self.sldBlue.Value))
        self.spnAlpha.SetValue(convFunc(self.sldAlpha.Value))

        self.updateResultField()

# class HexControl(ColorControl):
#    def __init__(self, parent=None, row=0, id=None, name="", value=0):
#        ColorControl.__init__(self, parent=parent, row=row, id=id, name=name, value=value, min=0, max=255, interval=1)
#        self.spinner.SetBase(16)
