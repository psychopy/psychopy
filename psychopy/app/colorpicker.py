# select a colour with wxPython's wx.ColourDialog(parent, data)
# largely copies: http://www.python-forum.org/pythonforum/viewtopic.php?f=2&t=10137

import wx

class ColorPicker(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self.SetBackgroundColour("grey")
        self.button = wx.Button(self, wx.ID_ANY, label='Show color dialog', pos=(10, 10))
        self.button.Bind(wx.EVT_BUTTON, self.selectColour)
        self.label = wx.StaticText(self, wx.ID_ANY, "", (10, 40))
        self.label.SetBackgroundColour("white")
        self.selectColour(None)

    def selectColour(self, event):
        """display the colour dialog and select"""
        dlg = wx.ColourDialog(self)
        dlg.GetColourData().SetChooseFull(True)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            rgb = data.GetColour().Get()
            s = 'RGB = %s, copied to clip-board' % str(rgb)
            self.label.SetLabel(s)
            self.SetBackgroundColour(rgb)
            self.Refresh()
            if wx.TheClipboard.Open():
                wx.TheClipboard.Clear()
                wx.TheClipboard.SetData(wx.TextDataObject(str(rgb)))
                wx.TheClipboard.Close()
        dlg.Destroy()

if __name__ == '__main__':
    app = wx.App(0)
    # create a frame, no parent, use default ID, title, size
    mytitle = "Select a color with the wx.ColourDialog"
    width = 450
    height = 200
    frame = wx.Frame(None, wx.ID_ANY, mytitle, size=(width, height))
    ColorPicker(frame)
    frame.Center()
    frame.Show()
    app.MainLoop()