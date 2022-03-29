import wx
import re

from ... import prefs
from . import colors


class CodeFont(wx.Font):
    def __init__(self, spec):
        # Make FontInfo object to initialise with
        info = wx.FontInfo(prefs.coder['codeFontSize'])
        # Set style
        if 'font' in spec:
            bold, italic = self.getFontStyle(spec['font'])
            info.Bold(bold)
            info.Italic(italic)
        # Initialise from info
        wx.Font.__init__(self, info)
        # Set face name
        if 'font' in spec:
            # Get font families
            names = self.getFontName(spec['font'])
            # Try faces sequentially until one works
            success = False
            for name in names:
                success = self.SetFaceName(name)
                if success:
                    break
            # If nothing worked, use the default monospace
            if not success:
                self.SetFaceName(wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT).GetFaceName())

        # Store foreground color
        if 'fg' in spec:
            self.fg = self.getColor(spec['fg'])
        else:
            self.fg = colors.app['text']
        # Store background color
        if 'bg' in spec:
            self.bg = self.getColor(spec['fg'])
        else:
            self.bg = colors.app['tab_bg']

    @staticmethod
    def getFontName(val):
        # Make sure val is a list
        if isinstance(val, str):
            # Get rid of any perentheses
            val = re.sub("[()[]]", "", val)
            # Split by comma
            val = val.split(",")
        # Clear style markers
        val = [p for p in val if val not in ("bold", "italic")]

        return val

    @staticmethod
    def getFontStyle(val):
        bold = "bold" in val
        italic = "italic" in val

        return bold, italic

    @staticmethod
    def getColor(val):
        val = str(val)
        # Split value according to operators, commas and spaces
        val = val.replace("+", " + ").replace("-", " - ").replace("\\", " \\ ")
        parts = re.split(r"[\\\s,()[]]", val)
        parts = [p for p in parts if p]
        # Set assumed values
        color = colors.scheme['black']
        modifier = +0
        alpha = 255
        for i, part in enumerate(parts):
            # If value is a named psychopy color, get it
            if part in colors.scheme:
                color = colors.scheme[part]
            # If assigned an operation, store it for application
            if part == "+" and i < len(parts) and parts[i+1].isnumeric():
                modifier = int(parts[i+1])
            if part == "-" and i < len(parts) and parts[i+1].isnumeric():
                modifier = -int(parts[i+1])
            if part == "*" and i < len(parts) and parts[i + 1].isnumeric():
                alpha = int(parts[i + 1])
            # If given a hex value, make a color from it
            if re.fullmatch(r"#(\dabcdefABCDEF){6}", part):
                part = part.replace("#", "")
                vals = [int(part[i:i+2], 16) for i in range(0, len(part), 2)] + [255]
                color = colors.BaseColor(*vals)
        # Apply modifier
        color = color + modifier
        # Apply alpha
        color = wx.Colour(color.Red(), color.Green(), color.Blue(), alpha=alpha)

        return color
