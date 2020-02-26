"""Classes for displaying color chips."""

import wx

class ColorChip(wx.Panel):
    """Base class for implementing sliders for picking color values."""
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.NO_BORDER):
        super(ColorChip, self).__init__(parent, id, pos, size, style)

        # events
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.SetDoubleBuffered(True)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)

    def setColor(self, col):
        """RGB color to set the chip color to."""

        if not isinstance(col, wx.Colour):
            col = wx.Colour(col)

        self.SetBackgroundColour(col)
        self.Refresh()

    def OnEraseBackground(self, event):
        """Called when the background is erased."""
        pass

    def OnPaint(self, event):
        """Event called when the slider is redrawn."""
        dc = wx.AutoBufferedPaintDC(self)
        dc.Clear()

        clientRect = self.GetClientRect()

        vparts = clientRect.height / 3

        for i, col in enumerate(['#FFFFFF', '#808080', '#000000']):
            colour = wx.Colour(col)
            dc.SetPen(wx.Pen(colour, 1, wx.PENSTYLE_SOLID))
            dc.SetBrush(wx.Brush(colour, style=wx.BRUSHSTYLE_SOLID))
            dc.DrawRectangle(clientRect.width - 20, vparts * i, 20, vparts + 1)
