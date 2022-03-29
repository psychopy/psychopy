import subprocess
import sys
from copy import copy

import wx
from pathlib import Path
from . import theme, Theme
from psychopy.localization import _translate
from ... import prefs


class ThemeSwitcher(wx.Menu):
    """Class to make a submenu for switching theme, meaning that the menu will
    always be the same across frames."""
    order = ["PsychopyDark", "PsychopyLight", "ClassicDark", "Classic"]

    def __init__(self, frame):
        # Get list of themes
        themeFolder = Path(__file__).parent / "spec"
        themeList = []
        for file in themeFolder.glob("*.json"):
            themeList.append(Theme(file.stem))
        # Reorder so that priority items are at the start
        self.themes = []
        order = copy(self.order)
        order.reverse()
        for name in order:
            for i, obj in enumerate(themeList):
                if obj.code == name:
                    self.themes.append(themeList.pop())
        self.themes.extend(themeList)

        # Make menu
        wx.Menu.__init__(self)
        # Make buttons
        for obj in self.themes:
            item = self.AppendRadioItem(id=wx.ID_ANY, item=obj.code, help=obj.info)
            item.Check(obj == theme)
            frame.Bind(wx.EVT_MENU, frame.app.onThemeChange, item)
        self.AppendSeparator()
        # Add Theme Folder button
        item = self.Append(wx.ID_ANY, _translate("Open theme folder"))
        frame.Bind(wx.EVT_MENU, self.openThemeFolder, item)

    def openThemeFolder(self, event):
        # Choose a command according to OS
        if sys.platform in ['win32']:
            comm = "explorer"
        elif sys.platform in ['darwin']:
            comm = "open"
        elif sys.platform in ['linux', 'linux2']:
            comm = "dolphin"
        # Use command to open themes folder
        subprocess.call(f"{comm} {prefs.paths['themes']}", shell=True)
