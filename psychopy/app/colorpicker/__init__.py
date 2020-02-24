# -*- coding: utf-8 -*-
"""Classes for the color picker."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
import wx.lib.agw.cubecolourdialog as ccd
from wx.lib.embeddedimage import PyEmbeddedImage
from psychopy.app.colorpicker.hsv import HSVColorPicker


class PsychoColorPicker(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"Color Picker", pos=wx.DefaultPosition,
                           size=wx.Size(640, 480), style=wx.DEFAULT_DIALOG_STYLE)

        self._color = [0.0, 0.0, 0.0]

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        sbColorPicker = wx.BoxSizer(wx.VERTICAL)

        sbTopPanel = wx.BoxSizer(wx.HORIZONTAL)

        sbColorSpace = wx.BoxSizer(wx.VERTICAL)

        self.nbColorSpace = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)

        self.pnlHSV = HSVColorPicker(self.nbColorSpace, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
        self.nbColorSpace.AddPage(self.pnlHSV, u" HSV ", True)

        sbColorSpace.Add(self.nbColorSpace, 1, wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT, 5)

        sbTopPanel.Add(sbColorSpace, 1, wx.EXPAND, 5)

        sbOutput = wx.BoxSizer(wx.VERTICAL)

        fraPreview = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, u" Preview "), wx.VERTICAL)

        self.pnlPreview = wx.Panel(fraPreview.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                   wx.BORDER_SUNKEN | wx.TAB_TRAVERSAL)
        self.pnlPreview.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_ACTIVECAPTION))

        fraPreview.Add(self.pnlPreview, 1, wx.EXPAND | wx.ALL, 5)

        sbOutput.Add(fraPreview, 1, wx.EXPAND | wx.LEFT, 5)

        fraColor = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, u" PsychoPy RGB "), wx.VERTICAL)

        sbColor = wx.FlexGridSizer(3, 2, 0, 0)
        sbColor.AddGrowableCol(1)
        sbColor.SetFlexibleDirection(wx.HORIZONTAL)
        sbColor.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        self.lblRed = wx.StaticText(fraColor.GetStaticBox(), wx.ID_ANY, u"R:", wx.DefaultPosition, wx.DefaultSize, 0)
        self.lblRed.Wrap(-1)

        sbColor.Add(self.lblRed, 0, wx.ALL | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.spnColorRed = wx.SpinCtrlDouble(fraColor.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                             wx.DefaultSize, wx.SP_ARROW_KEYS, -1, 1, 0, 0.01)
        self.spnColorRed.SetDigits(3)
        sbColor.Add(self.spnColorRed, 0, wx.ALL | wx.EXPAND, 5)

        self.lblGreen = wx.StaticText(fraColor.GetStaticBox(), wx.ID_ANY, u"G:", wx.DefaultPosition, wx.DefaultSize, 0)
        self.lblGreen.Wrap(-1)

        sbColor.Add(self.lblGreen, 0, wx.ALL | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.spnColorGreen = wx.SpinCtrlDouble(fraColor.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                               wx.DefaultSize, wx.SP_ARROW_KEYS, -1, 1, 0, 0.01)
        self.spnColorGreen.SetDigits(3)
        sbColor.Add(self.spnColorGreen, 0, wx.ALL | wx.EXPAND, 5)

        self.lblBlue = wx.StaticText(fraColor.GetStaticBox(), wx.ID_ANY, u"B:", wx.DefaultPosition, wx.DefaultSize, 0)
        self.lblBlue.Wrap(-1)

        sbColor.Add(self.lblBlue, 0, wx.ALL | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.spnColorBlue = wx.SpinCtrlDouble(fraColor.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                              wx.DefaultSize, wx.SP_ARROW_KEYS, -1, 1, 0, 0.01)
        self.spnColorBlue.SetDigits(3)
        sbColor.Add(self.spnColorBlue, 0, wx.ALL | wx.EXPAND, 5)

        fraColor.Add(sbColor, 0, wx.ALL | wx.EXPAND, 5)

        sbOutput.Add(fraColor, 0, wx.EXPAND | wx.TOP | wx.LEFT, 5)

        fraValues = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, u" Options  "), wx.VERTICAL)

        self.chkNormalized = wx.CheckBox(fraValues.GetStaticBox(), wx.ID_ANY, u"Rescale [0:1]", wx.DefaultPosition,
                                         wx.DefaultSize, 0)
        self.chkNormalized.SetToolTip(u"Rescale output values between 0 and 1")

        fraValues.Add(self.chkNormalized, 0, wx.ALL | wx.EXPAND, 5)

        self.chkClip = wx.CheckBox(fraValues.GetStaticBox(), wx.ID_ANY, u"Clip Range", wx.DefaultPosition,
                                   wx.DefaultSize, 0)
        self.chkClip.SetToolTip(u"Clip color values to be representable on the display")

        fraValues.Add(self.chkClip, 1, wx.ALL | wx.EXPAND, 5)

        sbOutput.Add(fraValues, 0, wx.EXPAND | wx.TOP | wx.LEFT, 5)

        sbTopPanel.Add(sbOutput, 0, wx.EXPAND | wx.TOP | wx.BOTTOM | wx.RIGHT, 5)

        sbColorPicker.Add(sbTopPanel, 1, wx.ALL | wx.EXPAND, 5)

        self.stlFrame = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        sbColorPicker.Add(self.stlFrame, 0, wx.EXPAND | wx.RIGHT | wx.LEFT, 10)

        sdbControls = wx.StdDialogButtonSizer()
        self.sdbControlsOK = wx.Button(self, wx.ID_OK)
        sdbControls.AddButton(self.sdbControlsOK)
        self.sdbControlsCancel = wx.Button(self, wx.ID_CANCEL)
        sdbControls.AddButton(self.sdbControlsCancel)
        sdbControls.Realize()

        sbColorPicker.Add(sdbControls, 0, wx.ALIGN_RIGHT | wx.ALL | wx.EXPAND, 5)

        self.SetSizer(sbColorPicker)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.nbColorSpace.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.spnColorRed.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnRedChanged)
        self.spnColorRed.Bind(wx.EVT_TEXT_ENTER, self.OnRedChanged)
        self.spnColorGreen.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnGreenChanged)
        self.spnColorGreen.Bind(wx.EVT_TEXT_ENTER, self.OnGreenChanged)
        self.spnColorBlue.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnBlueChanged)
        self.spnColorBlue.Bind(wx.EVT_TEXT_ENTER, self.OnBlueChanged)
        self.chkNormalized.Bind(wx.EVT_CHECKBOX, self.OnNormalizedChecked)
        self.chkClip.Bind(wx.EVT_CHECKBOX, self.OnClipChecked)
        self.sdbControlsCancel.Bind(wx.EVT_BUTTON, self.OnCancel)
        self.sdbControlsOK.Bind(wx.EVT_BUTTON, self.OnOK)

    def __del__(self):
        pass

    def OnEraseBackground(self, event):
        pass

    # def DrawHSVWheel(self, event):
    #     dc = wx.AutoBufferedPaintDC(self.pnlColorWheel)
    #     dc.SetBackground(wx.Brush(self.pnlColorWheel.GetParent().GetBackgroundColour()))
    #
    #     sz = self.pnlColorWheel.GetClientSize()
    #     dc.Clear()
    #     wheelBMP = ccd.HSVWheelImage.GetBitmap()
    #     mask = wx.Mask(wheelBMP, wx.Colour(192, 192, 192))
    #     wheelBMP.SetMask(mask)
    #     dc.DrawBitmap(wheelBMP, 0, 0, True)

    def OnPageChanged(self, event):
        event.Skip()

    def OnRedChanged(self, event):
        event.Skip()

    def OnGreenChanged(self, event):
        event.Skip()

    def OnBlueChanged(self, event):
        event.Skip()

    def OnNormalizedChecked(self, event):
        event.Skip()

    def OnClipChecked(self, event):
        event.Skip()

    def OnCancel(self, event):
        event.Skip()

    def OnOK(self, event):
        event.Skip()