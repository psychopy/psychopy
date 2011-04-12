# select a colour with wxPython's
# wx.ColourDialog(parent, data)
# source: Dietrich   20nov2008
# http://www.python-forum.org/pythonforum/viewtopic.php?f=2&t=10137

import wx

class ColorPicker(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self.SetBackgroundColour("black")

        self.button = wx.Button(self, wx.ID_ANY,
            label='Show colour dialog', pos=(80, 10))
        # bind mouse event to a method
        self.button.Bind(wx.EVT_BUTTON, self.selectColour)
        # a label to show colour rgb value
        self.label = wx.StaticText(self, wx.ID_ANY, "", (10, 80))
        self.label.SetBackgroundColour("white")
        #self.selectColour(None)

    def selectColour(self, event):
        """display the colour dialog and select"""
        dlg = wx.ColourDialog(self)
        # get the full colour dialog
        # default is False and gives the abbreviated version
        dlg.GetColourData()#.SetChooseFull(True)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            # gives red, green, blue tuple (r, g, b)
            # each rgb value has a range of 0 to 255
            rgb = data.GetColour().Get()
            s = 'The selected colour (r, g, b) = %s' % str(rgb)
            self.label.SetLabel(s)
            # set the panel's color and refresh
            self.SetBackgroundColour(rgb)
            self.Refresh()
        dlg.Destroy()

if __name__ == '__main__':
    app = wx.App(0)
    # create a frame, no parent, use default ID, title, size
    mytitle = "Select a colour with the wx.ColourDialog"
    width = 450
    height = 200
    frame = wx.Frame(None, wx.ID_ANY, mytitle, size=(width, height))
    # use a panel, it's easier to refresh colours
    ColorPicker(frame)
    frame.Center()
    frame.Show()
    app.MainLoop()