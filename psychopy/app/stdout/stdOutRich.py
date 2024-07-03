#!/usr/bin/env python
# -*- coding: utf-8 -*-
import webbrowser

import wx
import re
import wx.richtext
import locale

from psychopy import prefs
from psychopy.localization import _translate
from psychopy.app.utils import sanitize
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for the script output."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import re
import locale
import wx
import wx.richtext
import webbrowser
from psychopy.localization import _translate
from psychopy.app.themes import handlers, icons, colors, fonts

_prefEncoding = locale.getpreferredencoding()

from psychopy.alerts._alerts import AlertEntry
from psychopy.alerts._errorHandler import _BaseErrorHandler


class StdOutRich(wx.richtext.RichTextCtrl, _BaseErrorHandler, handlers.ThemeMixin):
    """
    A rich text ctrl for handling stdout/stderr
    """

    def __init__(self, parent, style, size=None, font=None, fontSize=None, app=None):
        kwargs = {'parent': parent, 'style': style}
        if size is not None:
            kwargs['size'] = size

        _BaseErrorHandler.__init__(self)
        wx.richtext.RichTextCtrl.__init__(self, **kwargs)

        self.prefs = prefs
        self.paths = prefs.paths

        if font and fontSize:
            currFont = self.GetFont()
            currFont.SetFaceName(font)
            currFont.SetPointSize(fontSize)
            self.BeginFont(currFont)

        self.parent = parent
        self.app = app
        self.Bind(wx.EVT_TEXT_URL, self.onURL)
        self._applyAppTheme()

    def _applyAppTheme(self):
        # do usual theme stuff
        handlers.ThemeMixin._applyAppTheme(self)
        # get base font
        font = fonts.coderTheme.base
        # dict of styles
        self._styles = {
            'base': wx.richtext.RichTextAttr(wx.TextAttr(
                colText=font.foreColor,
                colBack=font.backColor,
                font=font.obj,
            )),
            'error': wx.richtext.RichTextAttr(wx.TextAttr(
                colText=colors.scheme['red'],
                colBack=font.backColor,
                font=font.obj,
            )),
            'warning': wx.richtext.RichTextAttr(wx.TextAttr(
                colText=colors.scheme['orange'],
                colBack=font.backColor,
                font=font.obj,
            )),
            'info': wx.richtext.RichTextAttr(wx.TextAttr(
                colText=colors.scheme['lightgrey'],
                colBack=font.backColor,
                font=font.obj,
            )),
            'link': wx.richtext.RichTextAttr(wx.TextAttr(
                colText=colors.scheme['blue'],
                colBack=font.backColor,
                font=font.obj,
            )),
        }

    def onURL(self, evt=None):
        wx.BeginBusyCursor()
        try:
            if evt.String.startswith("http"):
                webbrowser.open(evt.String)
            else:
                # decompose the URL of a file and line number"""
                # "C:\Program Files\wxPython...\samples\hangman\hangman.py"
                filename = evt.GetString().split('"')[1]
                lineNumber = int(evt.GetString().split(',')[1][5:])
                self.app.showCoder()
                self.app.coder.gotoLine(filename, lineNumber)
        except Exception as e:
            print("##### Could not open URL: {} #####\n".format(evt.String))
            print(e)
        wx.EndBusyCursor()

    def write(self, inStr, evt=None):
        self.MoveEnd()  # always 'append' text rather than 'writing' it
        """tracebacks have the form:
        Traceback (most recent call last):
        File "C:\\Program Files\\wxPython2.8 Docs and Demos\\samples\\hangman\\hangman.py", line 21, in <module>
            class WordFetcher:
        File "C:\\Program Files\\wxPython2.8 Docs and Demos\\samples\\hangman\\hangman.py", line 23, in WordFetcher
        """

        if type(inStr) == AlertEntry:
            alert = inStr
            # sanitize message
            alert.msg = sanitize(alert.msg)

            # Write Code
            self.BeginStyle(self._styles['link'])
            self.BeginURL(alert.url)
            self.WriteText("Alert {}:".format(alert.code))
            self.EndURL()

            # Write Message
            self.BeginStyle(self._styles['base'])
            self.WriteText("\n\t" + alert.msg)

            # Write URL
            self.BeginStyle(self._styles['base'])
            self.WriteText("\n\t"+_translate("For further info see "))
            self.BeginStyle(self._styles['link'])
            self.BeginURL(alert.url)
            self.WriteText("{:<15}".format(alert.url))
            self.EndURL()

            self.Newline()
            self.ShowPosition(self.GetLastPosition())
        else:
            # if it comes form a stdout in Py3 then convert to unicode
            if type(inStr) == bytes:
                try:
                    inStr = inStr.decode('utf-8')
                except UnicodeDecodeError:
                    inStr = inStr.decode(_prefEncoding)

            # sanitize message
            inStr = sanitize(inStr)

            for thisLine in inStr.splitlines(True):
                try:
                    thisLine = thisLine.replace("\t", "    ")
                except Exception as e:
                    self.WriteText(str(e))

                if len(re.findall('".*", line.*', thisLine)) > 0:
                    # this line contains a file/line location so write as URL
                    self.BeginStyle(self._styles['link'])
                    self.BeginURL(thisLine)
                    self.WriteText(thisLine)
                    self.EndURL()
                elif re.match('https?://.*', thisLine):
                    # this line contains an actual URL
                    self.BeginStyle(self._styles['link'])
                    self.BeginURL(thisLine)
                    self.WriteText(thisLine)
                    self.EndURL()
                elif len(re.findall('CRITICAL|ERROR', thisLine)) > 0:
                    # this line contains an error
                    self.BeginStyle(self._styles['error'])
                    self.WriteText(thisLine)
                elif len(re.findall('WARNING|DEPRECATION', thisLine)) > 0:
                    # this line contains a warning
                    self.BeginStyle(self._styles['warning'])
                    self.WriteText(thisLine)
                elif len(re.findall('DATA|EXP|INFO|DEBUG', thisLine)):
                    # this line contains logging
                    self.BeginStyle(self._styles['info'])
                    self.WriteText(thisLine)
                else:
                    # anything else
                    self.BeginStyle(self._styles['base'])
                    self.WriteText(thisLine)
        # cap number of lines
        text = self.GetValue()
        maxLength = 100000
        if len(text) > maxLength:
            self.Remove(0, 1000)
        # go to end of stdout so user can see updated text
        self.MoveEnd()
        self.ShowPosition(self.GetLastPosition())

        if evt is not None:
            evt.Skip()

    def flush(self):
        for alert in self.alerts:
            self.write(alert)

        for err in self.errors:
            print(err)

        self.errors = []
        self.alerts = []

    def getText(self):
        """Get and return the text of the current buffer."""
        return self.GetValue()

    def setStatus(self, status):
        self.SetValue(status)
        self.Refresh()
        self.Layout()
        wx.Yield()

    def statusAppend(self, newText):
        text = self.GetValue() + newText
        self.setStatus(text)


class ScriptOutputPanel(wx.Panel, handlers.ThemeMixin):
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
    class OutputToolbar(wx.Panel, handlers.ThemeMixin):
        def __init__(self, parent):
            wx.Panel.__init__(self, parent, size=(30, 90))
            self.parent = parent

            # Setup sizer
            self.borderBox = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.borderBox)
            self.sizer = wx.BoxSizer(wx.VERTICAL)
            self.borderBox.Add(self.sizer, border=6, flag=wx.ALL)

            # Clear button
            self.clrBtn = wx.Button(self, size=(16, 16), style=wx.BORDER_NONE)
            self.clrBtn.SetToolTip(_translate(
                "Clear all previous output."
            ))
            self.clrBtn.SetBitmap(
                icons.ButtonIcon(stem="clear", size=16).bitmap
            )
            self.sizer.Add(self.clrBtn, border=6, flag=wx.BOTTOM)
            self.clrBtn.Bind(wx.EVT_BUTTON, self.parent.ctrl.clear)

            self.Layout()


        def _applyAppTheme(self):
            # Set background
            self.SetBackgroundColour(fonts.coderTheme.base.backColor)
            # Style buttons
            for btn in (self.clrBtn,):
                btn.SetBackgroundColour(fonts.coderTheme.base.backColor)
            self.Refresh()
            self.Update()

    def __init__(self,
                 parent,
                 style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE,
                 font=None,
                 fontSize=None):
        # Init superclass
        wx.Panel.__init__(self, parent, size=(480, 480), style=style)
        self.tabIcon = "stdout"

        # Setup sizer
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        # Text control
        self.ctrl = ScriptOutputCtrl(self,
                                     style=style,
                                     font=font,
                                     fontSize=fontSize)
        self.sizer.Add(self.ctrl, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)

        # Sep
        self.sep = wx.Window(self, size=(1, -1))
        self.sizer.Prepend(self.sep, border=12, flag=wx.EXPAND | wx.TOP | wx.BOTTOM)

        # Toolbar
        self.toolbar = self.OutputToolbar(self)
        self.sizer.Prepend(self.toolbar, border=6, flag=wx.EXPAND | wx.TOP | wx.BOTTOM)

    def _applyAppTheme(self):
        self.ctrl._applyAppTheme()
        # Set background
        self.SetBackgroundColour(fonts.coderTheme.base.backColor)
        self.Refresh()
        self.Update()
        # Match line
        self.sep.SetBackgroundColour(fonts.coderTheme.margin.backColor)
        self.Refresh()
        self.Update()


class ScriptOutputCtrl(StdOutRich, handlers.ThemeMixin):

    def __init__(self, parent,
                 style=wx.TE_READONLY | wx.TE_MULTILINE | wx.BORDER_NONE,
                 size=None,
                 font=None,
                 fontSize=None):

        StdOutRich.__init__(
            self,
            parent,
            size=wx.DefaultSize if size is None else size,
            style=style)

        self.parent = parent
        self.tabIcon = "stdout"
        self._font = font
        self._fontSize = fontSize
        self.Bind(wx.EVT_TEXT_URL, self.onURL)

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
                # get handle to app
                app = self.GetTopLevelParent().app
                # make sure we have a Coder window
                app.showCoder()
                # open in coder
                app.coder.gotoLine(filename, lineNumber)
        except Exception as e:
            print("##### Could not open URL: {} #####\n".format(evt.String))
            print(e)
        wx.EndBusyCursor()

    def clear(self, evt=None):
        self.Clear()

    def flush(self):

        for alert in self.alerts:
            self.write(alert)

        for err in self.errors:
            print(err)

        self.errors = []
        self.alerts = []


if __name__ == "__main__":
    pass
