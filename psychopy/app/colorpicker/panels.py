# -*- coding: utf-8 -*-
"""Classes for color picker dialog panels."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
from wx.lib.buttons import GenButton
from wx.lib.scrolledpanel import ScrolledPanel
from psychopy.colors import Color, colorNames
import numpy as np


class ColorPresets(ScrolledPanel):
    """Class for creating a scrollable button list that displays all preset
    colors.

    Parameters
    ----------
    parent : object
        Object this panel belongs to (i.e. :class:`wx.Frame` or `wx.Panel`).

    """
    def __init__(self, parent):
        # originally made by Todd Parsons
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
        """Event called when the user clicks a color button. Value is passed to
        the dialog and updates the color. This in turn will update the values of
        all the color space pages.

        """
        self.GetTopLevelParent().color = event.GetEventObject().colorData.copy()
        event.Skip()


class ColorPreview(wx.Panel):
    """Class for the color preview panel in the color picker.

    This panel displays the current color specified by the user. A background
    checkerboard pattern is drawn as a background making transparency more
    apparent.

    """
    def __init__(self, parent, color):
        wx.Panel.__init__(self, parent, size=(100, -1))
        # device contexts for drawing
        self.pdc = self.dc = None

        self.parent = parent
        self.SetDoubleBuffered(True)
        self.color = color
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
        self.pdc = wx.PaintDC(self)
        self.dc = wx.GCDC(self.pdc)

        # only draw background if there is transparency, reduces draw calls
        if self._color.alpha < 1.0:
            self._paintCheckerboard()

        self._paintPreviewColor()

    def _paintPreviewColor(self):
        """Paint the current color. Called when `onPaint` is invoked, but after
        the checkerboard is drawn.

        """
        if self.dc is None:
            return  # nop

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
        if self.pdc is None:
            return  # nop

        self.pdc.SetBrush(wx.LIGHT_GREY_BRUSH)
        self.pdc.SetPen(wx.LIGHT_GREY_PEN)

        # originally written by Todd Parsons
        w = h = gridRes
        for x in range(0, self.GetSize()[0], w * 2):
            for y in range(0 + (x % 2) * h, self.GetSize()[1], h * 2):
                self.pdc.DrawRectangle(x, y, w, h)
                self.pdc.DrawRectangle(x + w, y + h, w, h)


if __name__ == "__main__":
    pass
