#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Base class for the color slider."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
import platform


class ColorSlider(wx.Panel):
    """Base class for implementing sliders for picking color values."""
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.NO_BORDER):
        super(ColorSlider, self).__init__(parent, id, pos, size, style)

        # client draw style
        self.SetDoubleBuffered(True)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)

        # slider position in client window coordinates
        self.sliderPosX = 0
        # slider position in normalized coordinates
        self.sliderNormX = 0.0
        # function for scaling the output
        self._scaleFunc = None

        # callback function for when the slider position changes
        self._cbfunc = None

        # events
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvent)

    def OnPaint(self, event):
        """Event called when the slider is redrawn."""
        dc = wx.AutoBufferedPaintDC(self)
        if platform.system() == 'Windows':
            dc.SetBackground(  # ugh...
                wx.Brush(self.GetParent().GetParent().GetThemeBackgroundColour()))
        else:
            dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour()))
        dc.Clear()

        clientRect = self.GetClientRect()

        self.fill(dc, clientRect)
        self.drawBorder(dc, clientRect)

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
        pass

    def drawBorder(self, dc, rect):
        """Draw a border around the control."""
        dc.SetPen(wx.BLACK_PEN)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawRectangle(rect)

    def OnMouseEvent(self, event):
        """Event when the mouse is clicked or moved over the control."""
        if event.LeftIsDown():
            clientRect = self.GetClientRect()
            self.sliderPosX = event.GetX()

            padleft = 4
            padright = 4
            bgStart = padleft
            bgEnd = clientRect.width - padright - padleft

            # prevent invalid values
            if self.sliderPosX > bgEnd:
                self.sliderPosX = bgEnd
            elif self.sliderPosX < bgStart:
                self.sliderPosX = bgStart

            self.sliderNormX = (self.sliderPosX - padleft) / float(bgEnd - bgStart)

            # prevent invalid values
            if self.sliderNormX > 1.0:
                self.sliderNormX = 1.0
            elif self.sliderNormX < 0.0:
                self.sliderNormX = 0.0

            if self._cbfunc is not None:
                self._cbfunc(self.sliderNormX)

        self.Refresh()  # redraw when changed

    def setSliderChangedCallback(self, cbfunc):
        """Set the callback function for when a slider changes."""
        if not callable(cbfunc):
            raise TypeError("Value for `cbfunc` must be callable.")
        self._cbfunc = cbfunc

    def setScaleFunc(self, func):
        """Function for scaling the output value."""
        if not callable(func):
            raise TypeError("Value for `scaleFunc` must be callable.")

        self._scaleFunc = func

    def GetValue(self):
        """Get the current value of the slider."""
        return self._scaleFunc(self.sliderNormX) \
            if self._scaleFunc is not None else self.sliderNormX

    def SetValue(self, value):
        """Get the current value of the slider."""
        w = self.GetClientRect().width
        self.sliderPosX = int(w * value)
        self.sliderNormX = self.sliderPosX / float(w)
        self.Refresh()

