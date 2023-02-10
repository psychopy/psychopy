#!/usr/bin/env python
# -*- coding: utf-8 -*-
import webbrowser

import wx
import re
import wx.richtext
import locale
from psychopy.localization import _translate
from .utils import sanitize

_prefEncoding = locale.getpreferredencoding()

from psychopy.alerts._alerts import AlertEntry
from psychopy.alerts._errorHandler import _BaseErrorHandler


class StdOutRich(wx.richtext.RichTextCtrl, _BaseErrorHandler):
    """
    A rich text ctrl for handling stdout/stderr
    """

    def __init__(self, parent, style, size=None, font=None, fontSize=None, app=None):
        kwargs = {'parent': parent, 'style': style}
        if size is not None:
            kwargs['size'] = size

        _BaseErrorHandler.__init__(self)
        wx.richtext.RichTextCtrl.__init__(self, **kwargs)

        if font and fontSize:
            currFont = self.GetFont()
            currFont.SetFaceName(font)
            currFont.SetPointSize(fontSize)
            self.BeginFont(currFont)

        self.parent = parent
        self.app = app
        self.Bind(wx.EVT_TEXT_URL, self.onURL)

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

            # Write name of component
            # self.BeginTextColour([200, 0, 230])
            # self.WriteText("{:<20}".format(alert.name))
            # self.EndTextColour()

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
            return

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
        self.MoveEnd()  # go to end of stdout so user can see updated text
        self.ShowPosition(self.GetLastPosition())

    def flush(self):

        for alert in self.alerts:
            self.write(alert)

        for err in self.errors:
            print(err)

        self.errors = []
        self.alerts = []
