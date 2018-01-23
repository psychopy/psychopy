#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

import wx
import sys
import re
import wx.richtext
import locale
from psychopy.localization import _translate

_prefEncoding = locale.getpreferredencoding()

class StdOutRich(wx.richtext.RichTextCtrl):
    """A rich text ctrl for handling stdout/stderr
    """

    def __init__(self, parent, style, size=None, font=None, fontSize=None):
        kwargs = {'parent': parent, 'style': style}
        if size is not None:
            kwargs['size'] = size
        wx.richtext.RichTextCtrl.__init__(self, **kwargs)

        if font and fontSize:
            currFont = self.GetFont()
            currFont.SetFaceName(font)
            currFont.SetPointSize(fontSize)
            self.BeginFont(currFont)

        self.parent = parent
        self.Bind(wx.EVT_TEXT_URL, parent.onURL)
        # define style for filename links (URLS) needs wx as late as 2.8.4.0
        # self.urlStyle = wx.richtext.RichTextAttr()
        # self.urlStyle.SetTextColour(wx.BLUE)
        # self.urlStyle.SetFontWeight(wx.BOLD)
        # self.urlStyle.SetFontUnderlined(False)

    def write(self, inStr):
        self.MoveEnd()  # always 'append' text rather than 'writing' it
        """tracebacks have the form:
        Traceback (most recent call last):
        File "C:\Program Files\wxPython2.8 Docs and Demos\samples\hangman\hangman.py", line 21, in <module>
            class WordFetcher:
        File "C:\Program Files\wxPython2.8 Docs and Demos\samples\hangman\hangman.py", line 23, in WordFetcher
        """

        # if it comes form a stdout in Py3 then convert to unicode
        if type(inStr) == bytes:
            try:
                inStr = inStr.decode('utf-8')
            except UnicodeDecodeError:
                inStr = inStr.decode(_prefEncoding)

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
        pass  # needed so stdout has a flush method, but can't do much with it


class StdOutFrame(wx.Frame):
    """A frame for holding stdOut/stdErr with ability to save and clear
    """

    def __init__(self, parent=None, ID=-1, app=None, title="PsychoPy output",
                 size=wx.DefaultSize):
        wx.Frame.__init__(self, parent, ID, title, size=size)
        panel = wx.Panel(self)

        self.parent = parent  # e.g. the builder frame
        self.app = app
        self.stdoutOrig = sys.stdout
        self.stderrOrig = sys.stderr
        self.lenLastRun = 0

        self.menuBar = wx.MenuBar()
        self.fileMenu = wx.Menu()
        # item = self.fileMenu.Append(wx.ID_SAVE,
        # "&Save output window\t%s" %app.keys['save'])
        # self.Bind(wx.EVT_MENU, self.save, item)
        mtxt = _translate("&Close output window\t%s") % app.keys['close']
        item = self.fileMenu.Append(wx.ID_CLOSE, mtxt)
        self.Bind(wx.EVT_MENU, self.closeFrame, item)
        self.fileMenu.AppendSeparator()
        mtxt = _translate("&Quit (PsychoPy)\t%s")
        item = self.fileMenu.Append(wx.ID_EXIT, mtxt % app.keys['quit'],
                                    _translate("Terminate the application"))
        self.Bind(wx.EVT_MENU, self.quit, item)

        self.menuBar.Append(self.fileMenu, _translate("&File"))
        self.SetMenuBar(self.menuBar)

        self.stdoutCtrl = StdOutRich(
            parent=self, style=wx.TE_MULTILINE, size=size)

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.stdoutCtrl)
        self.SetSizerAndFit(self.mainSizer)
        self.Center()

    def quit(self, event=None):
        """quit entire app
        """
        self.Destroy()
        self.app.quit()

    def checkSave(self):
        return 1

    def closeFrame(self, checkSave=False):
        # the app (or frame of the app) should control redirection of stdout,
        # but just in case the user closes the window while it is receiving
        # input we should direct it back to orig
        sys.stdout = self.stdoutOrig
        sys.stderr = self.stderrOrig
        self.Hide()

    def saveAs(self):
        pass

    def save(self):
        pass

    def write(self, text):
        self.stdoutCtrl.write(text)

    def flush(self):
        self.stdoutCtrl.flush()

    def onURL(self, evt):
        self.parent.onURL(evt)  # just pass this one on

    def getText(self):
        """Return the text of the current buffer
        """
        return self.stdoutCtrl.GetValue()
