#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes for the HSV tab of the color picker."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
import colorsys
import platform
from psychopy.app.colorpicker.slider import ColorSlider
import wx.lib.agw.cubecolourdialog as ccd
from wx.lib.embeddedimage import PyEmbeddedImage

import psychopy.tools.colorspacetools as cst


class HSColorWheel(wx.Panel):
    """Base class for implementing a color wheel picker."""
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.NO_BORDER):
        super(HSColorWheel, self).__init__(parent, id, pos, size, style)

        # client draw style
        self.SetDoubleBuffered(True)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)

        # color wheel bitmap
        self._wheelBitmap = ccd.HSVWheelImage.GetBitmap()
        self._wheelBitmap.SetMask(
            wx.Mask(self._wheelBitmap, wx.Colour(192, 192, 192)))

        # marker and wheel bitmap position in client window coordinates
        self._markerPos = wx.Point()
        self._wheelCentre = wx.Point(0.0, 0.0)
        self._wheelRect = wx.Rect(0, 0, 0, 0)

        # angle and distance which corresponds to hue and saturation
        self._hueAngle = 0.0
        self._satDist = 0.0

        # radius of the color wheel in client coordinates
        self._wheelRadius = 100

        # callback function for when the slider position changes
        self._cbfunc = None

        # events
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvent)

        # manage slider
        self._hueSlider = None
        self._satSlider = None

    def OnPaint(self, event):
        """Event called when the slider is redrawn."""
        dc = wx.AutoBufferedPaintDC(self)
        if platform.system() == 'Windows':
            dc.SetBackground(  # ugh...
                wx.Brush(self.GetParent().GetParent().GetParent().GetThemeBackgroundColour()))
        else:
            dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour()))
        dc.Clear()

        clientRect = self.GetClientRect()

        self.fill(dc, clientRect)
        #self.drawBorder(dc, clientRect)

    def realize(self):
        """Call after sizing is done."""
        # bitmap offset to centre it
        clientRect = self.GetClientRect()
        self._wheelCentre = wx.Point(
            clientRect.width / 2.0, clientRect.height / 2.0)
        self._wheelRect = wx.Rect(
            (clientRect.width - self._wheelBitmap.Width) / 2.0,
            (clientRect.height - self._wheelBitmap.Height) / 2.0,
            self._wheelBitmap.Width,
            self._wheelBitmap.Height)
        self._markerPos = wx.Point(self._wheelCentre.x, self._wheelCentre.y)

        self.Refresh()

    def OnEraseBackground(self, event):
        """Called when the DC erases the background, does nothing by default."""
        pass

    def fill(self, dc, rect):
        """Art provider function for drawing the slider background. Subclasses
        can override this.

        Parameters
        ----------
        dc : AutoBufferedPaintDC
            Device context used by the control to draw the background.
        rect : wx.Rect
            Client positon and dimensions in window coordinates (x, y, w, h).

        """
        dc.DrawBitmap(
            self._wheelBitmap, self._wheelRect.x + 1, self._wheelRect.y + 1, True)

        dc.SetPen(wx.Pen(wx.WHITE, 1))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetLogicalFunction(wx.XOR)
        dc.DrawRectangle(
            self._markerPos.x - 3, self._markerPos.y - 3, 7, 7)

    def OnMouseEvent(self, event):
        """Event when the mouse is clicked or moved over the control."""
        if event.LeftIsDown():
            mousePos = wx.Point(event.GetX(), event.GetY())

            dist = ccd.Distance(self._wheelCentre, mousePos)
            self._satDist = dist / self._wheelRadius

            self._hueAngle = \
                ccd.rad2deg(ccd.AngleFromPoint(mousePos, self._wheelCentre))
            if self._hueAngle < 0.:
                self._hueAngle += 360.

            if self._satDist > 1.0:
                self._satDist = 1.0
                self._markerPos = ccd.PtFromAngle(
                    self._hueAngle, self._satDist * 255, self._wheelCentre)
            else:
                self._markerPos = mousePos

            if self._hueSlider is not None:
                self._hueSlider.SetValue(self._hueAngle)
            if self._satSlider is not None:
                self._satSlider.SetValue(self._satDist)

        self.Refresh()  # redraw when changed

    def manageHueSlider(self, slider):
        """Hue slider object to manage."""
        self._hueSlider = slider

    def manageSatSlider(self, slider):
        """Saturation slider object to manage."""
        self._satSlider = slider

    def UpdateHue(self):
        """Get hue and saturation for child sliders."""
        if self._hueSlider is not None:
            self._hueAngle = self._hueSlider.GetValue()

            self._markerPos = ccd.PtFromAngle(
                self._hueAngle, self._satDist * 255.0, self._wheelCentre)

            self.Refresh()

    def UpdateSat(self):
        if self._hueSlider is not None:
            self._satDist = self._satSlider.GetValue()

            self._markerPos = ccd.PtFromAngle(
                self._hueAngle, self._satDist * 255.0, self._wheelCentre)

            self.Refresh()

    #
    # def setSliderChangedCallback(self, cbfunc):
    #     """Set the callback function for when a slider changes."""
    #     if not callable(cbfunc):
    #         raise TypeError("Value for `cbfunc` must be callable.")
    #     self._cbfunc = cbfunc
    #
    # def setGetScaleFunc(self, func):
    #     """Function for scaling the input value."""
    #     if not callable(func):
    #         raise TypeError("Value for `_getScaleFunc` must be callable.")
    #
    #     self._getScaleFunc = func
    #
    # def setSetScaleFunc(self, func):
    #     """Function for scaling the output value."""
    #     if not callable(func):
    #         raise TypeError("Value for `_getSetScaleFunc` must be callable.")
    #
    #     self._setScaleFunc = func
    #
    # def GetValue(self):
    #     """Get the current value of the slider."""
    #     return self._getScaleFunc(self.sliderNormX) \
    #         if self._getScaleFunc is not None else self.sliderNormX
    #
    # def SetValue(self, value):
    #     """Get the current value of the slider."""
    #     scaledVal = (self._setScaleFunc(value)
    #         if self._setScaleFunc is not None else value)
    #
    #     self.sliderNormX = scaledVal
    #     w = self.GetClientRect().width
    #
    #     # fit in range
    #     padleft = 4
    #     padright = 4
    #     bgStart = padleft
    #     bgEnd = w - padright - padleft
    #     self.sliderPosX = padleft + int((bgEnd - bgStart) * self.sliderNormX)
    #
    #     self.Refresh()
    #
    #     if self._cbfunc is not None:
    #         self._cbfunc(self.GetValue())


class HSVHueSlider(ColorSlider):
    """Class for creating a slider to pick a hue."""
    def __init__(self, parent, id, pos, size, style):
        super(HSVHueSlider, self).__init__(parent, id, pos, size, style)
        self.setGetScaleFunc(lambda x: x * 360.)
        self.setSetScaleFunc(lambda x: x / 360.)

        self._hsvWheel = None
        self._satSlider = None
        self._valSlider = None

    def realize(self):
        clientRect = self.GetClientSize()
        padleft = 4
        padright = 4
        bgStart = padleft
        bgEnd = clientRect.width - padright - padleft

        self._fillBitmap = wx.Bitmap(
            bgEnd - bgStart, clientRect.height - 6, depth=wx.BITMAP_SCREEN_DEPTH)

        dc = wx.MemoryDC()
        dc.SelectObject(self._fillBitmap)

        v = 0.0
        step = self._quantLevel / (bgEnd - bgStart)

        for y_pos in range(0, bgEnd - bgStart, self._quantLevel):
            r, g, b = \
                [c * 255.0 for c in colorsys.hsv_to_rgb(
                    v, 1.0, 1.0)]
            colour = wx.Colour(int(r), int(g), int(b))
            dc.SetPen(wx.Pen(colour, 1, wx.PENSTYLE_SOLID))
            dc.SetBrush(wx.Brush(colour, style=wx.BRUSHSTYLE_SOLID))
            if y_pos + self._quantLevel > bgEnd:
                segWidth = int((y_pos + self._quantLevel) - bgEnd)
            else:
                segWidth = int(self._quantLevel)

            dc.DrawRectangle(y_pos, 0, segWidth, clientRect.height - 6)
            v = v + step

        self.SetValue(0.0)

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

        if self._fillBitmap is not None:
            dc.DrawBitmap(self._fillBitmap, 4, 3, False)

        dc.SetPen(wx.Pen(wx.WHITE, 1))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetLogicalFunction(wx.XOR)
        dc.DrawRectangle(self.sliderPosX - 4, 0, 8, rect.height)

    def manageHSVWheel(self, wheel):
        self._hsvWheel = wheel

    def manageSatSlider(self, slider):
        self._satSlider = slider

    def manageValSlider(self, slider):
        self._valSlider = slider

    def OnValueChanged(self):
        """Called after a value changes."""
        if self._satSlider is not None:
            self._satSlider.SetHue(self.GetValue())

        if self._satSlider is not None:
            self._valSlider.SetHue(self.GetValue())

        if self._hsvWheel is not None:
            self._hsvWheel.UpdateHue()


class HSVSaturationSlider(ColorSlider):
    """Class for creating a slider to pick a hue."""
    def __init__(self, parent, id, pos, size, style):
        super(HSVSaturationSlider, self).__init__(parent, id, pos, size, style)
        self._targetHue = 1.0
        self._valSlider = None
        self._hsvWheel = None

    def realize(self):
        self.SetValue(0.5)

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
        step = self._quantLevel / (bgEnd - bgStart)

        for y_pos in range(bgStart, bgEnd, self._quantLevel):
            r, g, b = \
                [c * 255.0 for c in colorsys.hsv_to_rgb(
                    self._targetHue, v, 1.0)]
            colour = wx.Colour(int(r), int(g), int(b))
            dc.SetPen(wx.Pen(colour, 1, wx.PENSTYLE_SOLID))
            dc.SetBrush(wx.Brush(colour, style=wx.BRUSHSTYLE_SOLID))
            if (y_pos + self._quantLevel) >= bgEnd:
                segWidth = \
                    self._quantLevel - int((y_pos + self._quantLevel) - bgEnd)
            else:
                segWidth = int(self._quantLevel)

            dc.DrawRectangle(y_pos, 3, segWidth, rect.height - 6)
            v = v + step

        dc.SetPen(wx.Pen(wx.WHITE, 1))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetLogicalFunction(wx.XOR)
        dc.DrawRectangle(self.sliderPosX - 4, 0, 8, rect.height)

    def SetHue(self, value):
        """Set the hue to saturate."""
        self._targetHue = value / 360.
        self.Refresh()

    def manageHSVWheel(self, wheel):
        self._hsvWheel = wheel

    def manageValSlider(self, slider):
        self._valSlider = slider

    def OnValueChanged(self):
        """Called after a value changes."""
        if self._hsvWheel is not None:
            self._hsvWheel.UpdateSat()

        if self._valSlider is not None:
            self._valSlider.SetSaturation(self.GetValue())


class HSVValueSlider(ColorSlider):
    """Class for creating a slider to pick a a hues brightness."""

    def __init__(self, parent, id, pos, size, style):
        super(HSVValueSlider, self).__init__(parent, id, pos, size, style)
        self._targetHue = self._targetSat = 1.0

    def realize(self):
        self.SetValue(0.5)

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
        step = self._quantLevel / (bgEnd - bgStart)

        for y_pos in range(bgStart, bgEnd, self._quantLevel):
            r, g, b = \
                [c * 255.0 for c in colorsys.hsv_to_rgb(
                    self._targetHue, self._targetSat, v)]
            colour = wx.Colour(int(r), int(g), int(b))
            dc.SetPen(wx.Pen(colour, 1, wx.PENSTYLE_SOLID))
            dc.SetBrush(wx.Brush(colour, style=wx.BRUSHSTYLE_SOLID))
            if y_pos + self._quantLevel > bgEnd:
                segWidth = \
                    self._quantLevel - int((y_pos + self._quantLevel) - bgEnd)
            else:
                segWidth = int(self._quantLevel)

            dc.DrawRectangle(y_pos, 3, segWidth, rect.height - 6)
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
        fraColorWheel = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, u" Hue + Saturation "), wx.VERTICAL)

        self.pnlColorWheel = HSColorWheel(fraColorWheel.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                      wx.TAB_TRAVERSAL)

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
                                           wx.SP_ARROW_KEYS | wx.TE_PROCESS_ENTER, 0, 360., 0, 1.0)
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
                                           wx.SP_ARROW_KEYS | wx.TE_PROCESS_ENTER, 0, 1, 0, 0.01)
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
                                             wx.SP_ARROW_KEYS | wx.TE_PROCESS_ENTER, 0, 1, 0, 0.01)
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

    def realize(self):
        self.pnlHue.realize()
        self.pnlSat.realize()
        self.pnlValue.realize()
        self.pnlColorWheel.realize()

        self.pnlColorWheel.manageHueSlider(self.pnlHue)
        self.pnlColorWheel.manageSatSlider(self.pnlSat)
        self.pnlHue.manageHSVWheel(self.pnlColorWheel)
        self.pnlHue.manageSatSlider(self.pnlSat)
        self.pnlHue.manageValSlider(self.pnlValue)
        self.pnlSat.manageHSVWheel(self.pnlColorWheel)
        self.pnlSat.manageValSlider(self.pnlValue)

    def updatePickerRGB(self):
        self.GetTopLevelParent().updateColorPicker(cst.hsv2rgb(self._colorHSV))

    def BindEvents(self):
        self.pnlColorWheel.Bind(wx.EVT_LEFT_DOWN, self.OnHSVWheelMouseDown)
        self.spnValueHSV.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnValueHSVChanged)
        self.spnValueHSV.Bind(wx.EVT_TEXT_ENTER, self.OnValueHSVChanged)
        self.spnSatHSV.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSatHSVChanged)
        self.spnSatHSV.Bind(wx.EVT_TEXT_ENTER, self.OnSatHSVChanged)
        self.spnHueHSV.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnHueHSVChanged)
        self.spnHueHSV.Bind(wx.EVT_TEXT_ENTER, self.OnHueHSVChanged)

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
        self._colorHSV[2] = self.spnValueHSV.GetValue()
        self.pnlValue.SetValue(self._colorHSV[2])
        self.pnlValue.Refresh()
        self.updatePickerRGB()
        event.Skip()

    def OnSatHSVChanged(self, event):
        self._colorHSV[1] = self.spnSatHSV.GetValue()
        self.pnlSat.SetValue(self._colorHSV[1])
        self.pnlSat.Refresh()
        self.updatePickerRGB()
        event.Skip()

    def OnHueHSVChanged(self, event):
        self._colorHSV[0] = self.spnHueHSV.GetValue()
        self.pnlHue.SetValue(self._colorHSV[0])
        self.pnlHue.Refresh()
        self.updatePickerRGB()
        event.Skip()


