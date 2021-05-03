# -*- coding: utf-8 -*-
"""Classes for color space pages for the color picker."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
from psychopy.colors import Color


SLIDER_RES = 255  # resolution of the slider for color channels, leave alone!
# remember the last color and output space


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

        # Make sure the top-level has the correct type. We use
        # `GetTopLevelParent` to avoid creating a reference to the dialog which
        # keeps it alive and causes an access violation when PsychoPy shuts
        # down, or worse, a memory leak.
        # assert isinstance(self.GetTopLevelParent(), PsychoColorPicker)

        # Functions to convert slider units to an RGB format to display in the
        # double-spin controls beside them.
        self._posToValFunc = {0: lambda v: 2 * (v / SLIDER_RES) - 1,  # [-1:1]
                              1: lambda v: v / SLIDER_RES,  # [0:1]
                              2: lambda v: v}  # [0:255]

        # inverse of the above functions, converts values to positions
        self._valToPosFunc = {0: lambda p: int(SLIDER_RES * (p + 1) / 2.),  # [-1:1]
                              1: lambda p: int(p * SLIDER_RES),  # [0:1]
                              2: lambda p: int(p)}  # [0:255]

        self._initUI()  # setup the UI controls
        self.updateChannels()
        self.updateHex()

    def _initUI(self):
        """Initialize window controls. Called once when the page is created.

        """
        szrRGBPage = wx.BoxSizer(wx.VERTICAL)

        fraRGBChannels = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, u"RGBA Channels"), wx.VERTICAL)

        szrRGBArea = wx.FlexGridSizer(4, 3, 5, 5)
        szrRGBArea.AddGrowableCol(1)
        szrRGBArea.SetFlexibleDirection(wx.BOTH)
        szrRGBArea.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        # labels for color channels
        self.lblRed = wx.StaticText(
            fraRGBChannels.GetStaticBox(),
            wx.ID_ANY,
            u"R:",
            wx.DefaultPosition,
            wx.DefaultSize, 0)
        self.lblGreen = wx.StaticText(
            fraRGBChannels.GetStaticBox(),
            wx.ID_ANY,
            u"G:",
            wx.DefaultPosition,
            wx.DefaultSize, 0)
        self.lblBlue = wx.StaticText(
            fraRGBChannels.GetStaticBox(),
            wx.ID_ANY,
            u"B:",
            wx.DefaultPosition,
            wx.DefaultSize, 0)
        self.lblAlpha = wx.StaticText(
            fraRGBChannels.GetStaticBox(),
            wx.ID_ANY,
            u"A:",
            wx.DefaultPosition,
            wx.DefaultSize, 0)

        self.lblRed.Wrap(-1)
        self.lblGreen.Wrap(-1)
        self.lblBlue.Wrap(-1)
        self.lblAlpha.Wrap(-1)

        # sliders for setting each channel
        self.sldRed = wx.Slider(
            fraRGBChannels.GetStaticBox(),
            wx.ID_ANY,
            int(SLIDER_RES / 2), 0, SLIDER_RES,  # value, min, max
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.SL_HORIZONTAL)
        self.sldGreen = wx.Slider(
            fraRGBChannels.GetStaticBox(),
            wx.ID_ANY,
            int(SLIDER_RES / 2), 0, SLIDER_RES,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.SL_HORIZONTAL)
        self.sldBlue = wx.Slider(
            fraRGBChannels.GetStaticBox(),
            wx.ID_ANY,
            int(SLIDER_RES / 2), 0, SLIDER_RES,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.SL_HORIZONTAL)
        self.sldAlpha = wx.Slider(
            fraRGBChannels.GetStaticBox(),
            wx.ID_ANY,
            SLIDER_RES, 0, SLIDER_RES,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.SL_HORIZONTAL)

        # spin (double) controls
        self.spnRed = wx.SpinCtrlDouble(
            fraRGBChannels.GetStaticBox(),
            wx.ID_ANY,
            u"0",
            wx.DefaultPosition,
            wx.DefaultSize, wx.SP_ARROW_KEYS,
            -1, 1, 0, 0.05)  # min, max, value, inc
        self.spnGreen = wx.SpinCtrlDouble(
            fraRGBChannels.GetStaticBox(),
            wx.ID_ANY,
            u"0",
            wx.DefaultPosition,
            wx.DefaultSize, wx.SP_ARROW_KEYS,
            -1, 1, 0, 0.05)
        self.spnBlue = wx.SpinCtrlDouble(
            fraRGBChannels.GetStaticBox(),
            wx.ID_ANY,
            u"0",
            wx.DefaultPosition,
            wx.DefaultSize, wx.SP_ARROW_KEYS,
            -1, 1, 0, 0.05)
        self.spnAlpha = wx.SpinCtrlDouble(
            fraRGBChannels.GetStaticBox(),
            wx.ID_ANY,
            u"1",
            wx.DefaultPosition,
            wx.DefaultSize, wx.SP_ARROW_KEYS,
            0, 1, 0, 0.05)  # non-standard specification for alpha here!!!

        self.spnRed.SetDigits(4)
        self.spnGreen.SetDigits(4)
        self.spnBlue.SetDigits(4)
        self.spnAlpha.SetDigits(4)

        # add widgets to the color channel area
        szrRGBArea.Add(
            self.lblRed, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)
        szrRGBArea.Add(self.sldRed, 1, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)
        szrRGBArea.Add(self.spnRed, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)

        szrRGBArea.Add(
            self.lblGreen, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)
        szrRGBArea.Add(self.sldGreen, 1, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)
        szrRGBArea.Add(self.spnGreen, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)

        szrRGBArea.Add(
            self.lblBlue, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)
        szrRGBArea.Add(self.sldBlue, 1, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)
        szrRGBArea.Add(self.spnBlue, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)

        szrRGBArea.Add(
            self.lblAlpha, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)
        szrRGBArea.Add(
            self.sldAlpha, 1, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)
        szrRGBArea.Add(self.spnAlpha, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)

        fraRGBChannels.Add(szrRGBArea, 1, wx.ALL | wx.EXPAND, 5)
        szrRGBPage.Add(
            fraRGBChannels, 0, wx.TOP | wx.LEFT | wx.RIGHT | wx.EXPAND, 5)

        szrRGBOptions = wx.BoxSizer(wx.HORIZONTAL)
        fraHexRGB = wx.StaticBoxSizer(
            wx.StaticBox(
                self,
                wx.ID_ANY,
                u"Hex/HTML (no Alpha)"),
            wx.VERTICAL)

        self.txtHex = wx.TextCtrl(
            fraHexRGB.GetStaticBox(),
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.TE_PROCESS_ENTER)
        fraHexRGB.Add(self.txtHex, 0, wx.ALL | wx.EXPAND, 5)

        szrRGBOptions.Add(fraHexRGB, 2, 0, 5)

        # the index of each item maps to the conversion functions
        rbxRGBModeChoices = [
            u"PsychoPy RGB [-1:1]",
            u"Normalized RGB [0:1]",
            u"8-Bit RGB [0:255]"]
        self.rbxRGBFormat = wx.RadioBox(
            self,
            wx.ID_ANY,
            u"RGB Format",
            wx.DefaultPosition,
            wx.DefaultSize,
            rbxRGBModeChoices,
            1, wx.RA_SPECIFY_COLS)
        self.rbxRGBFormat.SetSelection(0)
        # self.rbxRGBFormat.SetToolTip(
        #     u"Format to use for specifying RGBA channels.")

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
        self.txtHex.Bind(wx.EVT_TEXT_ENTER, self.onHexChanged)
        self.rbxRGBFormat.Bind(wx.EVT_RADIOBOX, self.onRGBMode)

    def updateDialog(self):
        """Update the color specified by the dialog.

        """
        # update the color specified by the dialog
        dlg = self.GetTopLevelParent()
        dlgColor = self.GetTopLevelParent().color

        spinVals = [
            self.spnRed.GetValue(),
            self.spnGreen.GetValue(),
            self.spnBlue.GetValue(),
            self.spnAlpha.GetValue()]

        channelFormat = self.rbxRGBFormat.GetSelection()
        if channelFormat == 0:
            dlgColor.rgba = spinVals
        elif channelFormat == 1:
            dlgColor.rgba1 = spinVals
        elif channelFormat == 2:
            dlgColor.rgba255 = spinVals
        else:
            raise ValueError('Color channel format not supported.')

        if hasattr(dlg, 'pnlColorPreview'):
            dlg.pnlColorPreview.Refresh()

    def updateChannels(self):
        """Update the values of the channels to reflect the color specified by
        the dialog. This should never be called within any event handler for
        controls within the channels frame!

        """
        # get colors and convert to format wxPython controls can accept
        rgbaColor = self.GetTopLevelParent().color
        rgba255 = [int(i) for i in rgbaColor.rgba255]
        self.sldRed.SetValue(rgba255[0])
        self.sldGreen.SetValue(rgba255[1])
        self.sldBlue.SetValue(rgba255[2])
        self.sldAlpha.SetValue(rgbaColor.alpha * SLIDER_RES)  # arrrg! should be 255!!!

        channelMode = self.rbxRGBFormat.GetSelection()
        convFunc = self._posToValFunc[channelMode]

        # update spinner values/ranges for each channel
        for spn in (self.spnRed, self.spnGreen, self.spnBlue):
            spn.SetDigits(
                0 if self.rbxRGBFormat.GetSelection() == 2 else 4)
            spn.SetIncrement(
                1 if self.rbxRGBFormat.GetSelection() == 2 else 0.05)
            spn.SetMin(convFunc(0))
            spn.SetMax(convFunc(SLIDER_RES))

        # set the value in the new range

        if channelMode == 0:
            spnColVals = rgbaColor.rgba
        elif channelMode == 1:
            spnColVals = rgbaColor.rgba1
        elif channelMode == 2:
            spnColVals = rgbaColor.rgba255
        else:
            raise ValueError("Unknown RGB channel format specified. Did you add"
                             "items to `rbxRGBFormat`?")

        self.spnRed.SetValue(spnColVals[0])
        self.spnGreen.SetValue(spnColVals[1])
        self.spnBlue.SetValue(spnColVals[2])
        self.spnAlpha.SetValue(rgbaColor.alpha)

    def onRedScroll(self, event):
        """Called when the red channel slider is moved. Updates the spin control
        and the color specified by the dialog.

        """
        self.spnRed.SetValue(
            self._posToValFunc[self.rbxRGBFormat.GetSelection()](
                event.Position))
        self.updateHex()
        self.updateDialog()
        event.Skip()

    def onRedUpdate(self, event):
        """Called when the red channel spin control is changed. Updates the hex
        value and the color specified by the dialog.

        """
        self.sldRed.SetValue(
            self._valToPosFunc[self.rbxRGBFormat.GetSelection()](event.Value))
        self.updateHex()
        self.updateDialog()
        event.Skip()

    def onGreenScroll(self, event):
        """Called when the green channel slider is moved. Updates the spin
        control and the color specified by the dialog.

        """
        self.spnGreen.SetValue(
            self._posToValFunc[self.rbxRGBFormat.GetSelection()](
                event.Position))
        self.updateHex()
        self.updateDialog()
        event.Skip()

    def onGreenUpdate(self, event):
        """Called when the green channel spin control is changed. Updates the
        hex value and the color specified by the dialog.

        """
        self.sldGreen.SetValue(
            self._valToPosFunc[self.rbxRGBFormat.GetSelection()](event.Value))
        self.updateHex()
        self.updateDialog()
        event.Skip()

    def onBlueScroll(self, event):
        """Called when the blue channel slider is moved. Updates the spin
        control and the color specified by the dialog.

        """
        self.spnBlue.SetValue(
            self._posToValFunc[self.rbxRGBFormat.GetSelection()](
                event.Position))
        self.updateHex()
        self.updateDialog()
        event.Skip()

    def onBlueUpdate(self, event):
        """Called when the blue channel spin control is changed. Updates the hex
        value and the color specified by the dialog.

        """
        self.sldBlue.SetValue(
            self._valToPosFunc[self.rbxRGBFormat.GetSelection()](event.Value))
        self.updateHex()
        self.updateDialog()
        event.Skip()

    def onAlphaScroll(self, event):
        """Called when the alpha (transparency) channel slider is moved. Updates
        the spin control and the color specified by the dialog.

        """
        self.spnAlpha.SetValue(event.Position / SLIDER_RES)
        self.updateHex()
        self.updateDialog()
        event.Skip()

    def onAlphaUpdate(self, event):
        """Called when the alpha channel spin control is changed. Updates the
        hex value and the color specified by the dialog.

        """
        self.sldAlpha.SetValue(event.Value * SLIDER_RES)
        self.updateHex()
        self.updateDialog()
        event.Skip()

    def onHexChanged(self, event):
        """Called when the user manually enters a hex value into the field.
        If the color value is valid, the new value will appear and the channels
        will update.

        """
        dlgColor = self.GetTopLevelParent().color
        try:
            dlgColor.rgba = Color(self.txtHex.GetValue(), space='hex').rgba
        except ValueError:
            pass

        self.updateHex()
        self.updateChannels()
        self.updateDialog()
        event.Skip()

    def updateHex(self):
        """Update the hex/HTML value using the color specified by the dialog.

        """
        self.txtHex.SetValue(self.GetTopLevelParent().color.hex)

    def onRGBMode(self, event):
        """Called when the RGB mode is changed. This re-ranges all the spin
        controls and updates the interface."""
        self.updateChannels()
        self.updateHex()
        event.Skip()


class ColorPickerPageHSV(wx.Panel):
    """Class for the HSV page of the color picker.

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

        self._initUI()  # setup the UI controls
        self.updateChannels()

    def _initUI(self):
        """Initialize window controls. Called once when the page is created.

        """
        szrRGBPage = wx.BoxSizer(wx.VERTICAL)

        fraHSVChannels = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, u"HSV/HSB Values"), wx.VERTICAL)

        szrHSVArea = wx.FlexGridSizer(4, 3, 5, 5)
        szrHSVArea.AddGrowableCol(1)
        szrHSVArea.SetFlexibleDirection(wx.BOTH)
        szrHSVArea.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        # labels for color channels
        self.lblHue = wx.StaticText(
            fraHSVChannels.GetStaticBox(),
            wx.ID_ANY,
            u"H:",
            wx.DefaultPosition,
            wx.DefaultSize, 0)
        self.lblSat = wx.StaticText(
            fraHSVChannels.GetStaticBox(),
            wx.ID_ANY,
            u"S:",
            wx.DefaultPosition,
            wx.DefaultSize, 0)
        self.lblVal = wx.StaticText(
            fraHSVChannels.GetStaticBox(),
            wx.ID_ANY,
            u"V:",
            wx.DefaultPosition,
            wx.DefaultSize, 0)
        self.lblAlpha = wx.StaticText(
            fraHSVChannels.GetStaticBox(),
            wx.ID_ANY,
            u"A:",
            wx.DefaultPosition,
            wx.DefaultSize, 0)

        self.lblHue.Wrap(-1)
        self.lblSat.Wrap(-1)
        self.lblVal.Wrap(-1)
        self.lblAlpha.Wrap(-1)

        # sliders for setting each channel
        self.sldHue = wx.Slider(
            fraHSVChannels.GetStaticBox(),
            wx.ID_ANY,
            0, 0, 360,  # value, min, max
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.SL_HORIZONTAL)
        self.sldSat = wx.Slider(
            fraHSVChannels.GetStaticBox(),
            wx.ID_ANY,
            0, 0, SLIDER_RES,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.SL_HORIZONTAL)
        self.sldVal = wx.Slider(
            fraHSVChannels.GetStaticBox(),
            wx.ID_ANY,
            0, 0, SLIDER_RES,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.SL_HORIZONTAL)
        self.sldAlpha = wx.Slider(
            fraHSVChannels.GetStaticBox(),
            wx.ID_ANY,
            0, 0, SLIDER_RES,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.SL_HORIZONTAL)

        # spin (double) controls
        self.spnHue = wx.SpinCtrlDouble(
            fraHSVChannels.GetStaticBox(),
            wx.ID_ANY,
            u"0",
            wx.DefaultPosition,
            wx.DefaultSize, wx.SP_ARROW_KEYS,
            0, 360, 0, 1.0)  # min, max, value, inc
        self.spnSat = wx.SpinCtrlDouble(
            fraHSVChannels.GetStaticBox(),
            wx.ID_ANY,
            u"0",
            wx.DefaultPosition,
            wx.DefaultSize, wx.SP_ARROW_KEYS,
            0, 1, 0, 0.05)
        self.spnVal = wx.SpinCtrlDouble(
            fraHSVChannels.GetStaticBox(),
            wx.ID_ANY,
            u"0",
            wx.DefaultPosition,
            wx.DefaultSize, wx.SP_ARROW_KEYS,
            0, 1, 0, 0.05)
        self.spnAlpha = wx.SpinCtrlDouble(
            fraHSVChannels.GetStaticBox(),
            wx.ID_ANY,
            u"1",
            wx.DefaultPosition,
            wx.DefaultSize, wx.SP_ARROW_KEYS,
            0, 1, 0, 0.05)

        self.spnHue.SetDigits(4)
        self.spnSat.SetDigits(4)
        self.spnVal.SetDigits(4)
        self.spnAlpha.SetDigits(4)

        # add widgets to the color channel area
        szrHSVArea.Add(
            self.lblHue, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)
        szrHSVArea.Add(self.sldHue, 1, wx.EXPAND, 5)
        szrHSVArea.Add(self.spnHue, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)

        szrHSVArea.Add(
            self.lblSat, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)
        szrHSVArea.Add(self.sldSat, 1, wx.EXPAND, 5)
        szrHSVArea.Add(self.spnSat, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)

        szrHSVArea.Add(
            self.lblVal, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)
        szrHSVArea.Add(self.sldVal, 10, wx.EXPAND, 5)
        szrHSVArea.Add(self.spnVal, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)

        szrHSVArea.Add(
            self.lblAlpha, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)
        szrHSVArea.Add(
            self.sldAlpha, 1, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)
        szrHSVArea.Add(self.spnAlpha, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)

        fraHSVChannels.Add(szrHSVArea, 1, wx.ALL | wx.EXPAND, 5)
        szrRGBPage.Add(
            fraHSVChannels, 0, wx.TOP | wx.LEFT | wx.RIGHT | wx.EXPAND, 5)

        self.SetSizer(szrRGBPage)
        self.Layout()

        # Connect Events
        self.sldHue.Bind(wx.EVT_SCROLL, self.onHueScroll)
        self.spnHue.Bind(wx.EVT_SPINCTRLDOUBLE, self.onHueUpdate)
        self.spnHue.Bind(wx.EVT_TEXT_ENTER, self.onHueUpdate)
        self.sldSat.Bind(wx.EVT_SCROLL, self.onSatScroll)
        self.spnSat.Bind(wx.EVT_SPINCTRLDOUBLE, self.onSatUpdate)
        self.spnSat.Bind(wx.EVT_TEXT_ENTER, self.onSatUpdate)
        self.sldVal.Bind(wx.EVT_SCROLL, self.onValScroll)
        self.spnVal.Bind(wx.EVT_SPINCTRLDOUBLE, self.onValUpdate)
        self.spnVal.Bind(wx.EVT_TEXT_ENTER, self.onValUpdate)
        self.sldAlpha.Bind(wx.EVT_SCROLL, self.onAlphaScroll)
        self.spnAlpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.onAlphaUpdate)
        self.spnAlpha.Bind(wx.EVT_TEXT_ENTER, self.onAlphaUpdate)

    def updateDialog(self):
        """Update the color specified by the dialog.

        """
        # update the color specified by the dialog
        dlg = self.GetTopLevelParent()
        dlgColor = self.GetTopLevelParent().color

        spinVals = [
            self.spnHue.GetValue(),
            self.spnSat.GetValue(),
            self.spnVal.GetValue(),
            self.spnAlpha.GetValue()]

        dlgColor.hsva = spinVals

        if hasattr(dlg, 'pnlColorPreview'):
            dlg.pnlColorPreview.Refresh()

    def updateChannels(self):
        """Update the values of the channels to reflect the color specified by
        the dialog. This should never be called within any event handler for
        controls within the channels frame!

        """
        # get colors and convert to format wxPython controls can accept
        rgbaColor = self.GetTopLevelParent().color
        hsva = [i for i in rgbaColor.hsva]

        self.sldHue.SetValue(hsva[0])
        self.sldSat.SetValue(hsva[1] * SLIDER_RES)
        self.sldVal.SetValue(hsva[2] * SLIDER_RES)
        self.sldAlpha.SetValue(hsva[3] * SLIDER_RES)  # arrrg! should be 255!!!

        # set the value in the new range
        self.spnHue.SetValue(hsva[0])
        self.spnSat.SetValue(hsva[1])
        self.spnVal.SetValue(hsva[2])
        self.spnAlpha.SetValue(hsva[3])

    def onHueScroll(self, event):
        """Called when the red channel slider is moved. Updates the spin control
        and the color specified by the dialog.

        """
        self.spnHue.SetValue(event.Position)
        self.updateDialog()
        event.Skip()

    def onHueUpdate(self, event):
        """Called when the red spin control. Updates the hex value and the color
        specified by the dialog.

        """
        self.sldHue.SetValue(int(event.GetValue()))
        self.updateDialog()
        event.Skip()

    def onSatScroll(self, event):
        """Called when the green channel slider is moved. Updates the spin
        control and the color specified by the dialog.

        """
        self.spnSat.SetValue(event.Position / SLIDER_RES)
        self.updateDialog()
        event.Skip()

    def onSatUpdate(self, event):
        """Called when the green spin control. Updates the hex value and the
        color specified by the dialog.

        """
        self.sldSat.SetValue(event.GetValue() * SLIDER_RES)
        self.updateDialog()
        event.Skip()

    def onValScroll(self, event):
        """Called when the blue channel slider is moved. Updates the spin
        control and the color specified by the dialog.

        """
        self.spnVal.SetValue(event.Position / SLIDER_RES)
        self.updateDialog()
        event.Skip()

    def onValUpdate(self, event):
        """Called when the blue spin control. Updates the hex value and the
        color specified by the dialog.

        """
        self.sldVal.SetValue(event.GetValue() * SLIDER_RES)
        self.updateDialog()
        event.Skip()

    def onAlphaScroll(self, event):
        """Called when the alpha (transparency) channel slider is moved. Updates
        the spin control and the color specified by the dialog.

        """
        self.spnAlpha.SetValue(event.Position / SLIDER_RES)
        self.updateDialog()
        event.Skip()

    def onAlphaUpdate(self, event):
        """Called when the alpha spin control. Updates the hex value and the
        color specified by the dialog.

        """
        self.sldAlpha.SetValue(event.GetValue() * SLIDER_RES)
        self.updateDialog()
        event.Skip()


if __name__ == "__main__":
    pass
