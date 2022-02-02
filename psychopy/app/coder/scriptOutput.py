#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for the script output."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import re
import locale
import wx
import wx.richtext
import webbrowser
from psychopy.localization import _translate
from psychopy.alerts._alerts import AlertEntry
from psychopy.app.themes import ThemeMixin

_prefEncoding = locale.getpreferredencoding()


class ScriptOutputPanel(wx.richtext.RichTextCtrl, ThemeMixin):
    """Class for the script output window in Coder.

    Parameters
    ----------
    parent : :class:`wx.Window`
        Window this object belongs to.
    style : int
        Symbolic constants for style flags.
    size : ArrayLike or None
        Size of the control in pixels `(w, h)`. Use `None` for default.
    font : str or None
        Font to use for output, fixed-width is preferred. If `None`, the theme
        defaults will be used.
    fontSize : int or None
        Point size of the font. If `None`, the theme defaults will be used.

    """
    def __init__(self,
                 parent,
                 style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE,
                 size=None,
                 font=None,
                 fontSize=None):

        wx.richtext.RichTextCtrl.__init__(
            self,
            parent,
            id=wx.ID_ANY,
            value="",
            pos=wx.DefaultPosition,
            size=wx.DefaultSize if size is None else size,
            style=style,
            validator=wx.DefaultValidator,
            name=wx.TextCtrlNameStr)

        self.parent = parent
        self._font = font
        self._fontSize = fontSize
        self.Bind(wx.EVT_TEXT_URL, self.onURL)

    def write(self, inStr):
        """Write (append) text to the control.

        Formatting is automatically applied to the text assuming the text
        follows PsychoPy's standard formatting conventions.

        Parameters
        ----------
        inStr : str
            Text to append.

        """
        # mostly taken from the existing StdOutRich class used by runner
        self.MoveEnd()  # always 'append' text rather than 'writing' it

        if isinstance(inStr, AlertEntry):
            alert = inStr
            # Write Code
            self.BeginBold()
            self.BeginTextColour(wx.BLUE)
            self.BeginURL(alert.url)
            self.WriteText("Alert {}:".format(alert.code))
            self.EndURL()
            self.EndBold()
            self.EndTextColour()

            # Write Message
            self.BeginTextColour([0, 0, 0])
            self.WriteText(alert.msg)
            self.EndTextColour()

            # Write URL
            self.WriteText("\n\t"+_translate("For further info see "))
            self.BeginBold()
            self.BeginTextColour(wx.BLUE)
            self.BeginURL(alert.url)
            self.WriteText("{:<15}".format(alert.url))
            self.EndURL()
            self.EndBold()
            self.EndTextColour()

            self.Newline()
            self.ShowPosition(self.GetLastPosition())

            self._applyAppTheme()

            return

        # convert to unicode if needed
        if isinstance(inStr, bytes):
            try:
                inStr = inStr.decode('utf-8')
            except UnicodeDecodeError:
                inStr = inStr.decode(_prefEncoding)

        # process the line, apply formatting and append
        for thisLine in inStr.splitlines(True):
            try:
                thisLine = thisLine.replace("\t", "    ")
            except Exception as e:
                self.WriteText(str(e))

            if len(re.findall('".*", line.*', thisLine)) > 0:
                # this line contains a file/line location so write as URL
                # self.BeginStyle(self.urlStyle)  # this should be done with
                # styles, but they don't exist in wx as late as 2.8.4.0
                self.BeginBold()
                self.BeginTextColour(wx.BLUE)
                self.BeginURL(thisLine)
                self.WriteText(thisLine)
                self.EndURL()
                self.EndBold()
                self.EndTextColour()
            elif len(re.findall('WARNING', thisLine)) > 0:
                self.BeginTextColour([0, 150, 0])
                self.WriteText(thisLine)
                self.EndTextColour()
            elif len(re.findall('ERROR', thisLine)) > 0:
                self.BeginTextColour([150, 0, 0])
                self.WriteText(thisLine)
                self.EndTextColour()
            else:
                # line to write as simple text
                self.WriteText(thisLine)
        self._applyAppTheme()
        self.MoveEnd()  # go to end of stdout so user can see updated text
        self.ShowPosition(self.GetLastPosition())

    def onURL(self, evt):
        """Open link in default browser."""
        wx.BeginBusyCursor()
        try:
            if evt.String.startswith("http"):
                webbrowser.open(evt.String)
            else:
                # decompose the URL of a file and line number"""
                # "C:\Program Files\wxPython...\samples\hangman\hangman.py"
                filename = evt.GetString().split('"')[1]
                lineNumber = int(evt.GetString().split(',')[1][5:])
                self.GetTopLevelParent().gotoLine(filename, lineNumber)
        except Exception as e:
            print("##### Could not open URL: {} #####\n".format(evt.String))
            print(e)
        wx.EndBusyCursor()


if __name__ == "__main__":
    pass
