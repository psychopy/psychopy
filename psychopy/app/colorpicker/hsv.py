#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes for the HSV tab of the color picker."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
import colorsys
from psychopy.app.colorpicker.slider import ColorSlider

import psychopy.tools.colorspacetools as cst


class HSVHueSlider(ColorSlider):
    """Class for creating a slider to pick a hue."""
    def __init__(self, parent, id, pos, size, style):
        super(HSVHueSlider, self).__init__(parent, id, pos, size, style)
        self.setScaleFunc(lambda x: x * 360.)

    def fill(self, dc, rect):
        """Art provider function for drawing the slider background. Subclasses
        can override this.

        Parameters
        ----------
        dc : AutoBufferedPaintDC
            Device context used by the control to draw the background.
        rect : wx.Rect
            Client position and dimensions in window coordinates (x, y, w, h).

        """
        padleft = 4
        padright = 4
        bgStart = padleft
        bgEnd = rect.width - padright - padleft

        v = 0.0
        step = 1.0 / (bgEnd - bgStart)

        for y_pos in range(bgStart, bgEnd):
            r, g, b = \
                [c * 255.0 for c in colorsys.hsv_to_rgb(
                    v, 1.0, 1.0)]
            colour = wx.Colour(int(r), int(g), int(b))
            dc.SetPen(wx.Pen(colour, 1, wx.PENSTYLE_SOLID))
            dc.DrawRectangle(y_pos, 3, 1, rect.height - 6)
            v = v + step

        dc.SetPen(wx.Pen(wx.WHITE, 1))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetLogicalFunction(wx.XOR)
        dc.DrawRectangle(self.sliderPosX - 4, 0, 8, rect.height)


class HSVSaturationSlider(ColorSlider):
    """Class for creating a slider to pick a hue."""
    def __init__(self, parent, id, pos, size, style):
        super(HSVSaturationSlider, self).__init__(parent, id, pos, size, style)
        self._targetHue = 1.0

    def fill(self, dc, rect):
        """Art provider function for drawing the slider background. Subclasses
        can override this.

        Parameters
        ----------
        dc : AutoBufferedPaintDC
            Device context used by the control to draw the background.
        rect : wx.Rect
            Client position and dimensions in window coordinates (x, y, w, h).

        """
        padleft = 4
        padright = 4
        bgStart = padleft
        bgEnd = rect.width - padright - padleft

        v = 0.0
        step = 1.0 / (bgEnd - bgStart)

        for y_pos in range(bgStart, bgEnd):
            r, g, b = \
                [c * 255.0 for c in colorsys.hsv_to_rgb(
                    self._targetHue, v, 1.0)]
            colour = wx.Colour(int(r), int(g), int(b))
            dc.SetPen(wx.Pen(colour, 1, wx.PENSTYLE_SOLID))
            dc.DrawRectangle(y_pos, 3, 1, rect.height - 6)
            v = v + step

        dc.SetPen(wx.Pen(wx.WHITE, 1))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetLogicalFunction(wx.XOR)
        dc.DrawRectangle(self.sliderPosX - 4, 0, 8, rect.height)

    def SetHue(self, value):
        """Set the hue to saturate."""
        self._targetHue = value / 360.
        self.Refresh()


class HSVValueSlider(ColorSlider):
    """Class for creating a slider to pick a a hues brightness."""

    def __init__(self, parent, id, pos, size, style):
        super(HSVValueSlider, self).__init__(parent, id, pos, size, style)
        self._targetHue = self._targetSat = 1.0

    def fill(self, dc, rect):
        """Art provider function for drawing the slider background. Subclasses
        can override this.

        Parameters
        ----------
        dc : AutoBufferedPaintDC
            Device context used by the control to draw the background.
        rect : wx.Rect
            Client position and dimensions in window coordinates (x, y, w, h).

        """
        padleft = 4
        padright = 4
        bgStart = padleft
        bgEnd = rect.width - padright - padleft

        v = 0.0
        step = 1.0 / (bgEnd - bgStart)

        for y_pos in range(bgStart, bgEnd):
            r, g, b = \
                [c * 255.0 for c in colorsys.hsv_to_rgb(
                    self._targetHue, self._targetSat, v)]
            colour = wx.Colour(int(r), int(g), int(b))
            dc.SetPen(wx.Pen(colour, 1, wx.PENSTYLE_SOLID))
            dc.DrawRectangle(y_pos, 3, 1, rect.height - 6)
            v = v + step

        dc.SetPen(wx.Pen(wx.WHITE, 1))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetLogicalFunction(wx.XOR)
        dc.DrawRectangle(self.sliderPosX - 4, 0, 8, rect.height)

    def SetHue(self, value):
        """Set the hue to saturate."""
        self._targetHue = value / 360.
        self.Refresh()

    def SetSaturation(self, value):
        """Set the staturation of the target hue."""
        self._targetSat = value
        self.Refresh()


class HSVColorPicker(wx.Panel):
    """Class for the HSV color picker panel."""
    def __init__(self, parent, id, pos, size, style):
        super(HSVColorPicker, self).__init__(parent, id, pos, size, style)

        # internal HSV color value
        self._colorHSV = [0.0, 0.0, 0.0]

        sbHSVPanel = wx.BoxSizer(wx.VERTICAL)
        fraColorWheel = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, u"Color Wheel"), wx.VERTICAL)

        self.pnlColorWheel = wx.Panel(fraColorWheel.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                      wx.BORDER_SUNKEN | wx.TAB_TRAVERSAL)
        self.pnlColorWheel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_ACTIVEBORDER))

        fraColorWheel.Add(self.pnlColorWheel, 1, wx.EXPAND | wx.ALL, 5)

        sbHSVPanel.Add(fraColorWheel, 1, wx.ALL | wx.EXPAND, 10)

        fgHSVColor = wx.FlexGridSizer(3, 3, 0, 0)
        fgHSVColor.AddGrowableCol(2)
        fgHSVColor.SetFlexibleDirection(wx.HORIZONTAL)
        fgHSVColor.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_ALL)

        self.lblHue = wx.StaticText(self, wx.ID_ANY, u"Hue (Deg)", wx.DefaultPosition, wx.DefaultSize, 0)
        self.lblHue.Wrap(-1)

        fgHSVColor.Add(self.lblHue, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.ALIGN_RIGHT, 5)

        self.spnHueHSV = wx.SpinCtrlDouble(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                           wx.SP_ARROW_KEYS, 0, 360., 0, 0.01)
        self.spnHueHSV.SetDigits(3)
        self.spnHueHSV.SetMaxSize(wx.Size(80, -1))

        fgHSVColor.Add(self.spnHueHSV, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, 5)

        self.pnlHue = HSVHueSlider(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                               wx.TAB_TRAVERSAL)
        self.pnlHue.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_ACTIVEBORDER))

        fgHSVColor.Add(self.pnlHue, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND | wx.BOTTOM | wx.RIGHT | wx.LEFT, 5)

        self.lblSat = wx.StaticText(self, wx.ID_ANY, u"Saturation", wx.DefaultPosition, wx.DefaultSize, 0)
        self.lblSat.Wrap(-1)

        fgHSVColor.Add(self.lblSat, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT | wx.RIGHT, 5)

        self.spnSatHSV = wx.SpinCtrlDouble(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                           wx.SP_ARROW_KEYS, 0, 100, 0, 0.01)
        self.spnSatHSV.SetDigits(3)
        self.spnSatHSV.SetMaxSize(wx.Size(80, -1))

        fgHSVColor.Add(self.spnSatHSV, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, 5)

        self.pnlSat = HSVSaturationSlider(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                               wx.TAB_TRAVERSAL)
        self.pnlSat.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_ACTIVEBORDER))

        fgHSVColor.Add(self.pnlSat, 1, wx.EXPAND | wx.BOTTOM | wx.RIGHT | wx.LEFT, 5)

        self.lblValue = wx.StaticText(self, wx.ID_ANY, u"Value", wx.DefaultPosition, wx.DefaultSize, 0)
        self.lblValue.Wrap(-1)

        fgHSVColor.Add(self.lblValue, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)

        self.spnValueHSV = wx.SpinCtrlDouble(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                             wx.SP_ARROW_KEYS, 0, 100, 0, 0.01)
        self.spnValueHSV.SetDigits(3)
        self.spnValueHSV.SetMaxSize(wx.Size(80, -1))

        fgHSVColor.Add(self.spnValueHSV, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, 5)

        self.pnlValue = HSVValueSlider(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                 wx.TAB_TRAVERSAL)
        self.pnlValue.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_ACTIVEBORDER))

        fgHSVColor.Add(self.pnlValue, 1, wx.EXPAND | wx.BOTTOM | wx.RIGHT | wx.LEFT, 5)

        sbHSVPanel.Add(fgHSVColor, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(sbHSVPanel)
        self.Layout()
        sbHSVPanel.Fit(self)

        # bind events
        self.BindEvents()

    def updatePickerRGB(self):
        r, g, b = cst.hsv2rgb(self._colorHSV)
        pickerFrame = self.GetTopLevelParent()
        pickerFrame.spnColorRed.SetValue(r)
        pickerFrame.spnColorGreen.SetValue(g)
        pickerFrame.spnColorBlue.SetValue(b)

    def BindEvents(self):
        self.pnlColorWheel.Bind(wx.EVT_LEFT_DOWN, self.OnHSVWheelMouseDown)
        self.spnValueHSV.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnValueHSVChanged)
        self.spnValueHSV.Bind(wx.EVT_TEXT_ENTER, self.OnValueHSVChanged)
        self.pnlHue.Bind(wx.EVT_LEFT_DOWN, self.OnHSVHueMouseDown)
        self.spnSatHSV.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSatHSVChanged)
        self.spnSatHSV.Bind(wx.EVT_TEXT_ENTER, self.OnSatHSVChanged)
        self.pnlSat.Bind(wx.EVT_LEFT_DOWN, self.OnHSVSatMouseDown)
        self.spnHueHSV.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnHueHSVChanged)
        self.spnHueHSV.Bind(wx.EVT_TEXT_ENTER, self.OnHueHSVChanged)
        self.pnlValue.Bind(wx.EVT_LEFT_DOWN, self.OnHSVValMouseDown)

        # assign callbacks
        self.pnlHue.setSliderChangedCallback(self.OnHSVHueChangedCallback)
        self.pnlSat.setSliderChangedCallback(self.OnHSVSatChangedCallback)
        self.pnlValue.setSliderChangedCallback(self.OnHSVValueChangedCallback)

    def OnHSVHueChangedCallback(self, val):
        self._colorHSV[0] = self.pnlHue.GetValue()
        self.spnHueHSV.SetValue(self._colorHSV[0])
        self.pnlValue.SetHue(self._colorHSV[0])
        self.pnlSat.SetHue(self._colorHSV[0])

        self.updatePickerRGB()

    def OnHSVSatChangedCallback(self, val):
        self._colorHSV[1] = val
        self.spnSatHSV.SetValue(self._colorHSV[1])
        self.pnlValue.SetSaturation(self._colorHSV[1])

        self.updatePickerRGB()

    def OnHSVValueChangedCallback(self, val):
        self._colorHSV[2] = val
        self.spnValueHSV.SetValue(self._colorHSV[2])
        self.updatePickerRGB()

    # Virtual event handlers, overide them in your derived class

    def OnHSVWheelMouseDown(self, event):
        event.Skip()

    def OnValueHSVChanged(self, event):
        event.Skip()

    def OnHSVHueMouseDown(self, event):
        event.Skip()

    def OnSatHSVChanged(self, event):
        print()

    def OnHSVSatMouseDown(self, event):
        event.Skip()

    def OnHueHSVChanged(self, event):
        event.Skip()

    def OnHSVValMouseDown(self, event):
        event.Skip()