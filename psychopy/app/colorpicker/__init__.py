# -*- coding: utf-8 -*-
"""Classes for the color picker."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import sys

import wx
import wx.stc as stc
from .panels import ColorPresets, ColorPreview
from .pages import ColorPickerPageHSV, ColorPickerPageRGB
from .ui import ColorPickerDialog
from psychopy.colors import Color
from psychopy.localization import _translate

LAST_COLOR = Color((0, 0, 0, 1), space='rgba')
LAST_OUTPUT_SPACE = 0
SLIDER_RES = 255  # resolution of the slider for color channels, leave alone!


class ColorPickerState:
    """Class representing the state of the color picker. This is used to
    provide persistence between multiple invocations of the dialog within a
    single session.

    Parameters
    ----------
    color : Color
        Last color selected by the user.
    colorspace : Color
        Last colorspace specified.
    rgbInputMode : int
        RGB input mode selected by the user.

    """
    def __init__(self, color, colorspace, rgbInputMode):
        self.color = color
        self.colorspace = colorspace
        self.rgbInputMode = rgbInputMode


class PsychoColorPicker(ColorPickerDialog):
    """Class for the color picker dialog.

    This dialog is used to standardize color selection across platforms. It also
    supports PsychoPy's RGB representation directly.

    This is a subclass of the auto-generated `ColorPickerDialog` class.

    Parameters
    ----------
    parent : object
        Reference to a :class:`~wx.Frame` which owns this dialog.

    """
    def __init__(self, parent, context=None, allowInsert=False, allowCopy=False):
        ColorPickerDialog.__init__(self, parent)

        self.parent = parent
        self.allowInsert = allowInsert
        self.allowCopy = allowCopy

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetSize(wx.Size(640, 480))
        self.SetMinSize(wx.Size(640, 480))

        # store context
        self.context = context

        # current output color, should be displayed in the preview
        global LAST_COLOR
        self._color = LAST_COLOR.copy()

        # output spaces mapped to the `cboOutputSpace` object
        self._spaces = {
            0: 'rgb',
            1: 'rgb1',
            2: 'rgb255',
            3: 'hex',
            4: 'hsv'
        }
        # what to show in the output selection, maps to the spaces above
        self._outputChoices = [
            u'PsychoPy RGB (rgb)',
            u'Normalized RGB (rgb1)',
            u'8-bit RGB (rgb255)',
            u'Hex/HTML (hex)',
            u'Hue-Saturation-Value (hsv)'
        ]

        # set the available output spaces
        self.cboOutputSpace.SetItems(self._outputChoices)

        # Functions to convert slider units to an RGB format to display in the
        # double-spin controls beside them.
        self._posToValFunc = {0: lambda v: 2 * (v / SLIDER_RES) - 1,  # [-1:1]
                              1: lambda v: v / SLIDER_RES,  # [0:1]
                              2: lambda v: v}  # [0:255]

        # inverse of the above functions, converts values to positions
        self._valToPosFunc = {0: lambda p: int(SLIDER_RES * (p + 1) / 2.),  # [-1:1]
                              1: lambda p: int(p * SLIDER_RES),  # [0:1]
                              2: lambda p: int(p)}  # [0:255]

        # initialize the window controls
        midpoint = int(SLIDER_RES / 2.)
        self.sldRedChannel.SetValue(midpoint)
        self.sldGreenChannel.SetValue(midpoint)
        self.sldBlueChannel.SetValue(midpoint)
        self.sldRedChannel.SetMax(SLIDER_RES)
        self.sldGreenChannel.SetMax(SLIDER_RES)
        self.sldBlueChannel.SetMax(SLIDER_RES)
        self.sldHueChannel.SetRange(0.0, 360.0)
        self.sldStaturationChannel.SetRange(0, SLIDER_RES)
        self.sldValueChannel.SetRange(0, SLIDER_RES)

        self.updateRGBChannels()  # initialize
        self.updateRGBPage()
        self.updateHSVPage()
        self.updateDialog()

    @property
    def color(self):
        """Current color the user has specified. Should be reflected in the
        preview area. Value has type :class:`psychopy.colors.Color`.

        This is the primary setter for the dialog's color value. It will
        automatically update all color space pages to reflect this color value.
        Pages should absolutely not attempt to set other page's values directly
        or risk blowing up the call stack.

        """
        return self._color

    @color.setter
    def color(self, value):
        if value is None:
            value = Color('none', space='named')

        global LAST_COLOR
        self.pnlColorPreview.color = self._color = value
        LAST_COLOR = self._color.copy()

    @property
    def rgbInputMode(self):
        """The RGB input mode (`int`)."""
        # replaces the older radio box which returned indices
        if self.rdoRGBModePsychoPy.GetValue():
            return 0
        elif self.rdoRGBModeNormalized.GetValue():
            return 1
        elif self.rdoRGBMode255.GetValue():
            return 2
        else:
            return -1

    def updateDialog(self):
        """Update the color specified by the dialog. Call this whenever the
        color controls are updated by the user.

        """
        spinVals = [
            self.spnRedChannel.GetValue(),
            self.spnGreenChannel.GetValue(),
            self.spnBlueChannel.GetValue()]

        if self.rgbInputMode == 0:
            self.color.rgb = spinVals
        elif self.rgbInputMode == 1:
            self.color.rgb1 = spinVals
        elif self.rgbInputMode == 2:
            self.color.rgb255 = spinVals
        else:
            raise ValueError('Color channel format not supported.')

        # update the HSV page
        previewRGB = self.color.rgb255
        r, g, b = previewRGB
        self.pnlColorPreview.SetBackgroundColour(
            wx.Colour(r, g, b, alpha=wx.ALPHA_OPAQUE))
        self.pnlColorPreview.Refresh()

    def updateHSVPage(self):
        """Update values on the HSV page. This is called when some other page is
        used to pick the color and the HSV page needs to reflect that.

        """
        # get colors and convert to format wxPython controls can accept
        hsvColor = self.color.hsv
        self.sldHueChannel.SetValue(hsvColor[0])
        self.sldStaturationChannel.SetValue(hsvColor[1] * SLIDER_RES)
        self.sldValueChannel.SetValue(hsvColor[2] * SLIDER_RES)

        # set the value in the new range
        self.spnHueChannel.SetValue(hsvColor[0])
        self.spnSaturationChannel.SetValue(hsvColor[1])
        self.spnValueChannel.SetValue(hsvColor[2])

    def updateRGBPage(self):
        """Update values on the RGB page. This is called when some other page is
        used to pick the color and the RGB page needs to reflect that.

        """
        rgb255 = [int(i) for i in self.color.rgb255]
        self.sldRedChannel.SetValue(rgb255[0])
        self.sldGreenChannel.SetValue(rgb255[1])
        self.sldBlueChannel.SetValue(rgb255[2])
        # self.sldAlpha.SetValue(
        #    rgbaColor.alpha * SLIDER_RES)  # arrrg! should be 255!!!

        # set the value in the new range
        if self.rgbInputMode == 0:
            spnColVals = self.color.rgb
        elif self.rgbInputMode == 1:
            spnColVals = self.color.rgb1
        elif self.rgbInputMode == 2:
            spnColVals = self.color.rgb255
        else:
            raise ValueError(
                "Unknown RGB channel format specified. Did you add a new mode?")

        self.spnRedChannel.SetValue(spnColVals[0])
        self.spnGreenChannel.SetValue(spnColVals[1])
        self.spnBlueChannel.SetValue(spnColVals[2])

    def updateRGBChannels(self):
        """Update the values of the indicated RGB channels to reflect the
        selected color input mode.

        The RGB page has modes which changes the format of the input values.
        Calling this updates the controls to reflect the format.

        """
        # get colors and convert to format wxPython controls can accept
        channelMode = self.rgbInputMode
        convFunc = self._posToValFunc[channelMode]

        # update spinner values/ranges for each channel
        for spn in (self.spnRedChannel, self.spnGreenChannel, self.spnBlueChannel):
            spn.SetDigits(
                0 if channelMode == 2 else 4)
            spn.SetIncrement(
                1 if channelMode == 2 else 0.05)
            spn.SetMin(convFunc(0))
            spn.SetMax(convFunc(SLIDER_RES))

        self.updateRGBPage()

    # --------------------------------------------------------------------------
    # Events for RGB controls
    #

    def OnRedScroll(self, event):
        """Called when the red channel slider is moved. Updates the spin control
        and the color specified by the dialog.

        """
        self.spnRedChannel.SetValue(
            self._posToValFunc[self.rgbInputMode](
                event.Position))
        self.updateHSVPage()
        self.updateDialog()

    def OnGreenScroll(self, event):
        """Called when the green channel slider is moved. Updates the spin
        control and the color specified by the dialog.

        """
        self.spnGreenChannel.SetValue(
            self._posToValFunc[self.rgbInputMode](
                event.Position))
        self.updateHSVPage()
        self.updateDialog()

    def OnBlueScroll(self, event):
        """Called when the blue channel slider is moved. Updates the spin
        control and the color specified by the dialog.

        """
        self.spnBlueChannel.SetValue(
            self._posToValFunc[self.rgbInputMode](
                event.Position))
        self.updateHSVPage()
        self.updateDialog()

    def OnRedSpin(self, event):
        """Called when the red spin control is changed. Updates the hex value
        and the color specified by the dialog.

        """
        self.sldRedChannel.SetValue(
            self._valToPosFunc[self.rgbInputMode](event.Value))
        self.updateHSVPage()
        self.updateDialog()

    def OnGreenSpin(self, event):
        """Called when the green spin control is changed. Updates the hex value
        and the color specified by the dialog.

        """
        self.sldGreenChannel.SetValue(
            self._valToPosFunc[self.rgbInputMode](event.Value))
        self.updateHSVPage()
        self.updateDialog()

    def OnBlueSpin(self, event):
        """Called when the blue spin control. Updates the hex value and the
         color specified by the dialog.

         """
        self.sldBlueChannel.SetValue(
            self._valToPosFunc[self.rgbInputMode](event.Value))
        self.updateHSVPage()
        self.updateDialog()

    def OnRGBModePsychoPy(self, event):
        self.updateRGBChannels()

    def OnRGBModeNormalized(self, event):
        self.updateRGBChannels()

    def OnRGBMode255(self, event):
        self.updateRGBChannels()

    # --------------------------------------------------------------------------
    # Events for HSV controls
    #

    def OnHueSpin(self, event):
        """Called when the hue spin control is changed. Updates the hex value
        and the color specified by the dialog.

        """
        self.sldHueChannel.SetValue(event.GetValue())
        self.color.hsv = (
            self.spnHueChannel.GetValue(),
            self.spnSaturationChannel.GetValue(),
            self.spnValueChannel.GetValue())
        self.updateRGBPage()
        self.updateDialog()

    def OnHueScroll(self, event):
        self.spnHueChannel.SetValue(event.Position)
        self.color.hsv = (
            self.spnHueChannel.GetValue(),
            self.spnSaturationChannel.GetValue(),
            self.spnValueChannel.GetValue())
        self.updateRGBPage()
        self.updateDialog()

    def OnSaturationSpin(self, event):
        self.sldStaturationChannel.SetValue(event.GetValue() * SLIDER_RES)
        self.color.hsv = (
            self.spnHueChannel.GetValue(),
            self.spnSaturationChannel.GetValue(),
            self.spnValueChannel.GetValue())
        self.updateRGBPage()
        self.updateDialog()

    def OnSaturationScroll(self, event):
        self.spnSaturationChannel.SetValue(event.Position / SLIDER_RES)
        self.color.hsv = (
            self.spnHueChannel.GetValue(),
            self.spnSaturationChannel.GetValue(),
            self.spnValueChannel.GetValue())
        self.updateRGBPage()
        self.updateDialog()

    def OnValueSpin(self, event):
        self.sldValueChannel.SetValue(event.GetValue() * SLIDER_RES)
        self.color.hsv = (
            self.spnHueChannel.GetValue(),
            self.spnSaturationChannel.GetValue(),
            self.spnValueChannel.GetValue())
        self.updateRGBPage()
        self.updateDialog()

    def OnValueScroll(self, event):
        self.spnValueChannel.SetValue(event.Position / SLIDER_RES)
        self.color.hsv = (
            self.spnHueChannel.GetValue(),
            self.spnSaturationChannel.GetValue(),
            self.spnValueChannel.GetValue())
        self.updateRGBPage()
        self.updateDialog()

    def getOutputValue(self):
        """Get the string value using the specified output format.

        Returns
        -------
        str
            Color value using the current output format.

        """
        outputSpace = self.cboOutputSpace.GetSelection()
        dlgCol = self.GetTopLevelParent().color
        if outputSpace == 0:  # RGB
            colorOut = '{:.4f}, {:.4f}, {:.4f}'.format(*dlgCol.rgb)
        elif outputSpace == 1:  # RGB1
            colorOut = '{:.4f}, {:.4f}, {:.4f}'.format(*dlgCol.rgb1)
        elif outputSpace == 2:  # RGB255
            colorOut = '{:d}, {:d}, {:d}'.format(
                *[int(i) for i in dlgCol.rgb255])
        elif outputSpace == 3:  # Hex
            colorOut = "'{}'".format(dlgCol.hex)
        elif outputSpace == 4:  # HSV
            colorOut = '{:.4f}, {:.4f}, {:.4f}'.format(*dlgCol.hsv)
        else:
            raise ValueError(
                "Invalid output color space selection. Have you added any "
                "choices to `cboOutputSpace`?")

        return colorOut

    def _copyToClipboard(self, text):
        """Copy text to the clipboard.

        Shows an error dialog if the clipboard cannot be opened to inform the
        user the values have not been copied.

        Parameters
        ----------
        text : str
            Text to copy to the clipboard.

        """
        # copy the value to the clipboard
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(str(text)))
            wx.TheClipboard.Close()
        else:
            # Raised if the clipboard fails to open, warns the user the value
            # wasn't copied.
            errDlg = wx.MessageDialog(
                self,
                'Failed to open the clipboard, output value not copied.',
                'Clipboard Error',
                wx.OK | wx.ICON_ERROR)
            errDlg.ShowModal()
            errDlg.Destroy()

    def onInsertValue(self, event):
        """Event to copy the color to the clipboard as a an object.

        """
        if isinstance(self.context, wx.TextCtrl):
            self.context.SetValue(self.getOutputValue())
        elif isinstance(self.context, stc.StyledTextCtrl):
            self.context.InsertText(
                self.context.GetCurrentPos(), "(" + self.color + ")")

        self.Close()
        event.Skip()

    def onCopyValue(self, event):
        """Event to copy the color to the clipboard as a value.

        """
        self._copyToClipboard(self.getOutputValue())  # copy out to clipboard
        self.Close()
        event.Skip()

    def onClose(self, event):
        """Called when the cancel button is clicked."""
        self.Close()
        event.Skip()


if __name__ == "__main__":
    pass
