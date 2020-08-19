# -*- coding: utf-8 -*-
"""Classes for the color picker."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
import wx.lib.agw.cubecolourdialog as ccd
from wx.adv import PseudoDC
from wx.lib.embeddedimage import PyEmbeddedImage
from psychopy.app.colorpicker.hsv import HSVColorPicker
from psychopy.app.colorpicker.chip import ColorChip
from psychopy.app.themes import ThemeMixin
from psychopy.visual.basevisual import Color, AdvancedColor
import wx.lib.agw.aui as aui


class PsychoColorPicker(wx.Dialog, ThemeMixin):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"Color Picker", pos=wx.DefaultPosition,
                           size=wx.Size(640, 500), style=wx.DEFAULT_DIALOG_STYLE)
        # Set main params
        self.color = Color((0,0,0,1), 'rgba')
        self.sizer = wx.BoxSizer(orient=wx.VERTICAL)
        # Add colourful top bar
        self.preview = ColorPreview(color=self.color, parent=self)
        self.sizer.Add(self.preview)
        # Add notebook of controls
        self.ctrls = aui.AuiNotebook(self, wx.ID_ANY, size=wx.Size(640, 500))
        self.sizer.Add(self.ctrls, wx.EXPAND)
        self.ctrls.AddPage(RGBcontrols(self.ctrls, self), 'RGB')
        # Standard controls
        sdbControls = wx.StdDialogButtonSizer()
        self.sdbControlsOK = wx.Button(self, wx.ID_OK)
        sdbControls.AddButton(self.sdbControlsOK)
        self.sdbControlsCancel = wx.Button(self, wx.ID_CANCEL)
        sdbControls.AddButton(self.sdbControlsCancel)
        sdbControls.Realize()
        self.sizer.Add(sdbControls, 0, wx.EXPAND, 5)

        #self.SetSizerAndFit(self.sizer)
        self.SetSizer(self.sizer)
        self._applyAppTheme()
        self._applyAppTheme(self.ctrls)

        self.Layout()
        self.Centre(wx.BOTH)
        self.Show(True)

    def setColor(self, color, space):
        self.color.set(color, space)
        self.preview.color = self.color

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

    def updateColorPicker(self, rgb):
        """Update the color picker dialog from a color picker page.

        Parameters
        ----------
        rgb : array_like
            RGB values to display in the spin controls and preview.

        """
        self._color = list(rgb)
        self._colorClipped = [(c + 1.) / 2. for c in self._color]
        previewColor = wx.Colour([int(c * 255.) for c in self._colorClipped])
        self.pnlPreview.setColor(previewColor)
        self.spnColorRed.SetValue(self._color[0])
        self.spnColorGreen.SetValue(self._color[1])
        self.spnColorBlue.SetValue(self._color[2])

    def OnRedChanged(self, event):
        newColor = [self.spnColorRed.GetValue(), self._color[1], self._color[2]]
        self.updateColorPicker(newColor)

    def OnGreenChanged(self, event):
        newColor = [self._color[0], self.spnColorGreen.GetValue(), self._color[2]]
        self.updateColorPicker(newColor)

    def OnBlueChanged(self, event):
        newColor = [self._color[0], self._color[1], self.spnColorBlue.GetValue()]
        self.updateColorPicker(newColor)

    def OnNormalizedChecked(self, event):
        event.Skip()

    def OnClipChecked(self, event):
        event.Skip()

    def OnCancel(self, event):
        event.Skip()

    def OnOK(self, event):
        event.Skip()

class ColorPreview(wx.Window):
    def __init__(self, color, parent):
        wx.Window.__init__(self, parent, size=(640,100))
        self.SetBackgroundColour(ThemeMixin.appColors['frame_bg'])
        self.parent = parent
        self.color = color
        self.Bind(wx.EVT_PAINT, self.onPaint)

    @property
    def color(self):
        return self._color
    @color.setter
    def color(self, value):
        self._color = value
        self.Refresh()

    def onPaint(self, event):
        self.pdc = wx.PaintDC(self)
        self.dc = wx.GCDC(self.pdc)
        self.pdc.SetBrush(wx.Brush(ThemeMixin.appColors['panel_bg']))
        self.pdc.SetPen(wx.Pen(ThemeMixin.appColors['panel_bg']))
        w = 10
        h = 10
        for x in range(0, self.GetSize()[0], w*2):
            for y in range(0+(x%2)*h, self.GetSize()[1], h*2):
                self.pdc.DrawRectangle(x, y, w, h)
                self.pdc.DrawRectangle(x+w, y+h, w, h)
        self.dc.SetBrush(wx.Brush(self.color.rgba255, wx.BRUSHSTYLE_TRANSPARENT))
        self.dc.SetPen(wx.Pen(self.color.rgba255, wx.PENSTYLE_TRANSPARENT))
        self.dc.DrawRectangle(0, 0, self.GetSize()[0], self.GetSize()[1])


class RGBcontrols(wx.Window, ThemeMixin):
    def __init__(self, parent, dlg):
        wx.Window.__init__(self, parent, size=wx.Size(640, 500))
        self.dlg = dlg
        self.sizer = wx.GridBagSizer(vgap=10, hgap=20)
        rowh = 30

        # Control red
        self.sizer.Add(wx.StaticText(parent=self, label="Red", size=(-1,rowh), style=wx.ALIGN_RIGHT), pos=(0,0))
        self.redSld = wx.Slider(self, name="Red", minValue=0, maxValue=255, size=(440, rowh))
        self.redSld.Bind(wx.EVT_COMMAND_SCROLL_CHANGED, self.onChange)
        self.sizer.Add(self.redSld, pos=(0, 1))
        self.redCtrl = wx.SpinCtrl(self, name="Red", min=0, max=255, size=(100,rowh-5))
        self.redCtrl.Bind(wx.EVT_SPINCTRL, self.onChange)
        self.sizer.Add(self.redCtrl, pos=(0, 2))

        # Control green
        self.sizer.Add(wx.StaticText(parent=self, label="Green", size=(-1,rowh), style=wx.ALIGN_RIGHT), pos=(1,0))
        self.greenSld = wx.Slider(self, name="Green", minValue=0, maxValue=255, size=(440, rowh))
        self.greenSld.Bind(wx.EVT_COMMAND_SCROLL_CHANGED, self.onChange)
        self.sizer.Add(self.greenSld, pos=(1, 1))
        self.greenCtrl = wx.SpinCtrl(self, name="Green", min=0, max=255, size=(100,rowh-5))
        self.greenCtrl.Bind(wx.EVT_SPINCTRL, self.onChange)
        self.sizer.Add(self.greenCtrl, pos=(1, 2))


        # Control blue
        self.sizer.Add(wx.StaticText(parent=self, label="Blue", size=(-1,rowh), style=wx.ALIGN_RIGHT), pos=(2,0))
        self.blueSld = wx.Slider(self, name="Blue", minValue=0, maxValue=255, size=(440, rowh))
        self.blueSld.Bind(wx.EVT_COMMAND_SCROLL_CHANGED, self.onChange)
        self.sizer.Add(self.blueSld, pos=(2, 1))
        self.blueCtrl = wx.SpinCtrl(self, name="Blue", min=0, max=255, size=(100,rowh-5))
        self.blueCtrl.Bind(wx.EVT_SPINCTRL, self.onChange)
        self.sizer.Add(self.blueCtrl, pos=(2, 2))


        # Control alpha
        self.sizer.Add(wx.StaticText(parent=self, label="Alpha", size=(-1,rowh), style=wx.ALIGN_RIGHT), pos=(3,0))
        self.alphaSld = wx.Slider(self, name="Alpha", minValue=0, maxValue=255, size=(440, rowh))
        self.alphaSld.Bind(wx.EVT_COMMAND_SCROLL_CHANGED, self.onChange)
        self.sizer.Add(self.alphaSld, pos=(3, 1))
        self.alphaCtrl = wx.SpinCtrl(self, name="Alpha", min=0, max=255, size=(100,rowh-5))
        self.alphaCtrl.Bind(wx.EVT_SPINCTRL, self.onChange)
        self.sizer.Add(self.alphaCtrl, pos=(3, 2))

        # Control space
        self.sizer.Add(wx.StaticText(parent=self, label="Space:", size=(-1,rowh), style=wx.ALIGN_RIGHT), pos=(4,0))
        self.spaceCtrl = wx.Choice(parent=self, choices=['rgb255', 'rgb1', 'rgb'], size=(100, rowh-5), name="Space")
        self.spaceCtrl.SetSelection(2)
        self.spaceCtrl.Bind(wx.EVT_CHOICE, self.spaceChange)
        self.sizer.Add(self.spaceCtrl, pos=(4,1))

        self.sizer.AddGrowableCol(1)
        self.sizer.AddGrowableRow(4)

        self.SetSizer(self.sizer)
        self.onOpen()

    def _applyAppTheme(self, target=None):
        self.SetBackgroundColour(ThemeMixin.appColors['tab_bg'])

    def onOpen(self):
        space = ('rgba255', 'rgba1', 'rgba')[self.spaceCtrl.GetSelection()]
        r, g, b, a = getattr(self.dlg.color, space)
        self.redSld.SetValue(r)
        self.greenSld.SetValue(g)
        self.blueSld.SetValue(b)
        self.alphaSld.SetValue(a)

    def onChange(self, event):
        obj = event.GetEventObject()
        val = obj.GetValue()
        space = ('rgba255', 'rgba1', 'rgba')[self.spaceCtrl.GetSelection()]
        r,g,b,a = getattr(self.dlg.color, space)
        if obj in [self.redSld, self.redCtrl]:
            r = val
            self.redSld.SetValue(val)
            self.redCtrl.SetValue(val)
        if obj in [self.greenSld, self.greenCtrl]:
            g = val
            self.greenSld.SetValue(val)
            self.greenCtrl.SetValue(val)
        if obj in [self.blueSld, self.blueCtrl]:
            b = val
            self.blueSld.SetValue(val)
            self.blueCtrl.SetValue(val)
        if obj in [self.alphaSld, self.alphaCtrl]:
            a = val
            self.alphaSld.SetValue(val)
            self.alphaCtrl.SetValue(val)
        self.dlg.setColor((r,g,b,a), space)

    def spaceChange(self, event):
        obj = event.GetEventObject()
        space = ['rgba255', 'rgba1', 'rgba'][obj.GetSelection()]
        val = getattr(self.dlg.color, space)
        max = getattr(Color((1, 1, 1, 1), 'rgba1'), space)
        min = getattr(Color((0, 0, 0, 0), 'rgba1'), space)
        sliders = [self.redSld, self.greenSld, self.blueSld, self.alphaSld]
        for i in range(len(sliders)):
            sliders[i].SetRange(min[i], max[i])
            sliders[i].SetValue(val[i])
        spinners = [self.redCtrl, self.greenCtrl, self.blueCtrl, self.alphaCtrl]
        for i in range(len(spinners)):
            spinners[i].SetRange(min[i], max[i])
            spinners[i].SetValue(val[i])