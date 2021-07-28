#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for the REPL shell in PsychoPy Coder."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
import wx.richtext
from collections import deque
from psychopy.app.themes import ThemeMixin


class ConsoleTextCtrl(wx.richtext.RichTextCtrl, ThemeMixin):
    """Class for the console text control. This is needed to allow for theming.
    """
    def __init__(self, parent, id_=wx.ID_ANY, value="", pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0,
                 name=wx.TextCtrlNameStr):

        wx.richtext.RichTextCtrl.__init__(
            self, parent, id=id_, value=value, pos=pos, size=size, style=style,
            validator=wx.DefaultValidator, name=name)


class PythonREPLCtrl(wx.Panel, ThemeMixin):
    """Class for a Python REPL control.

    An interactive shell (REPL) for interfacing with a Python interpreter in
    another process owned by the control.

    This class doe not emulate a terminal/console perfectly, so things like
    'curses' and control characters (e.g., Ctrl+C) do not work. Unresponsive
    scripts must be stopped manually, resulting in a loss of the objects in the
    namespace. Therefore, it is recommended that users push lines to the
    shell using the script editor.

    """
    def __init__(self,
                 parent,
                 id_=wx.ID_ANY,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL,
                 name=wx.EmptyString):

        wx.Panel.__init__(self, parent, id=id_, pos=pos, size=size, style=style,
                          name=name)

        # sizer for the panel
        szrMain = wx.BoxSizer(wx.VERTICAL)
        # TextCtrl used to display the text from the terminal
        styleFlags = (wx.HSCROLL | wx.TE_MULTILINE | wx.TE_PROCESS_ENTER |
                      wx.TE_PROCESS_TAB | wx.NO_BORDER)
        self.txtTerm = ConsoleTextCtrl(
            self,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.DefaultSize,
            styleFlags)
        szrMain.Add(self.txtTerm, 1, wx.ALL | wx.EXPAND, 0)
        self.SetSizer(szrMain)
        self.Layout()

        # set font
        # font1 = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Consolas')
        # self.txtTerm.SetFont(font1)
        # self.txtTerm.SetMargins(8)

        # capture keypresses
        self.txtTerm.Bind(wx.EVT_CHAR, self.onChar)
        self.txtTerm.Bind(wx.EVT_TEXT, self.onText)
        self.txtTerm.Bind(wx.EVT_TEXT_ENTER, self.onEnter)
        self.txtTerm.Bind(wx.EVT_TEXT_MAXLEN, self.onMaxLength)
        self.txtTerm.Bind(wx.EVT_TEXT_URL, self.onURL)

        self._history = deque([])
        self._historyIdx = 0

        # idle event
        self.Bind(wx.EVT_IDLE, self.onIdle)

        # hooks for the process we're communicating with
        self._process = self._pid = None

        # interpreter state information
        self._isBusy = self._suppress = False
        self._stdin_buffer = []
        self._lastTextPos = 0

        # self.start()  # start an interpreter

        self.txtTerm.WriteText("Hit [Return] to start a Python REPL.")
        self._lastTextPos = self.txtTerm.GetLastPosition()

    def onTerminate(self, event):
        # hooks for the process we're communicating with
        self._process = self._pid = None

        # interpreter state information
        self._isBusy = self._suppress = False
        self._stdin_buffer = []
        self._lastTextPos = 0

        self.start()

    @property
    def isStarted(self):
        """`True` if the interpreter process has been started."""
        return self._process is not None

    @property
    def isBusy(self):
        """`True` if the interpreter process is busy."""
        return self._isBusy

    @property
    def suppressed(self):
        """`True` if the interpreter output is suppressed."""
        return self._suppress

    @property
    def process(self):
        """Process object for the interpreter (`wx.Process`)."""
        return self._process

    @property
    def pid(self):
        """Process ID for the interpreter (`int`)."""
        return self._pid

    def getPid(self):
        """Get the process ID for the active interpreter (`int`)."""
        return self._pid

    def getPwd(self):
        """Get the present working directory for the interpreter."""
        pass

    def setPwd(self):
        """Set the present working directory for the interpreter."""
        pass

    def getNamespace(self):
        """Get variable names in the current namespace."""
        self.push('dir()')  # get namespace values

    def onIdle(self, event):
        """Idle event.

        This is hooked into the main application even loop. When idle, the
        input streams are checked and any data is writen to the text box.

        """
        # don't do anything unless we have an active process
        if not self.isStarted:
            return

        # we have new characters
        newChars = False

        # check if we have input text to process
        if self._process.IsInputAvailable():
            stdin_text = self._process.InputStream.read()
            txt = stdin_text.decode('utf-8')
            self.txtTerm.WriteText(txt)
            if txt == '\r':
                pass

            # hack to get the interactive help working
            try:
                if self.txtTerm.GetValue()[-6:] == 'help> ':
                    self._isBusy = False
            except IndexError:
                pass

            newChars = True

        # check if the input stream has bytes to process
        if self._process.IsErrorAvailable():
            stderr_text = self._process.ErrorStream.read()
            self.txtTerm.WriteText(stderr_text.decode('utf-8'))
            self._isBusy = False
            newChars = True

        # If we have received new character from either stream, advance the
        # boundary of the editable area.
        if newChars:
            self._lastTextPos = self.txtTerm.GetLastPosition()

    def resetCaret(self):
        """Place the caret at the entry position if not in an editable region.
        """
        if self.txtTerm.GetInsertionPoint() < self._lastTextPos:
            self.txtTerm.SetInsertionPoint(self._lastTextPos)
            return

    def push(self, line, submit=True):
        """Push a line to the interpreter.

        Parameter
        ---------
        line : str
            Statement to push to the terminal.

        """
        if not self.isStarted:
            return

        # convert to bytes
        line = str.encode(line if not submit else line + '\n')

        if submit:
            self._isBusy = True  # flag that something has been sent
            self._process.OutputStream.write(line)
            self._process.OutputStream.flush()

    def start(self):
        """Start a new interpreter process."""
        # inform the user that we're starting the console
        self.txtTerm.Clear()
        self.txtTerm.WriteText(
            "Starting Python interpreter session, please wait ...\n")

        # setup the sub-process
        wx.BeginBusyCursor()
        self._process = wx.Process(self)
        self._process.Redirect()
        self._pid = wx.Execute('python -i', wx.EXEC_ASYNC, self._process)

        # bind the event called when the process ends
        self._process.Bind(wx.EVT_END_PROCESS, self.onTerminate)

        # clear all text in the widget and display the welcome message
        self.txtTerm.Clear()
        self.txtTerm.WriteText(
            "Python REPL in PsychoPy (pid:{}) - type some commands!\n\n".format(
                self._pid))
        self._lastTextPos = self.txtTerm.GetLastPosition()
        wx.EndBusyCursor()

    def close(self):
        """Close an open interpreter."""
        if self.isStarted:
            wx.Process.Kill(self._pid, wx.SIGKILL)

    def restart(self):
        """Close the running interpreter (if running) and spawn a new one."""
        pass

    def clear(self):
        """Clear the contents of the console."""
        pass

    def onText(self, event):
        event.Skip()

    def onEnter(self, event):
        event.Skip()

    def onMaxLength(self, event):
        event.Skip()

    def onURL(self, event):
        event.Skip()

    def __del__(self):
        pass

    def _clearAndReplaceTyped(self, replaceWith=''):
        """Clear any text that has been typed."""
        self.txtTerm.Remove(self._lastTextPos, self.txtTerm.GetLastPosition())
        if replaceWith:
            self.txtTerm.WriteText(replaceWith)

        self.txtTerm.SetInsertionPoint(self.txtTerm.GetLastPosition())

    def _getTyped(self):
        """Get the text that was typed or is editable (`str`)."""
        return self.txtTerm.GetRange(
            self._lastTextPos,
            self.txtTerm.GetLastPosition())

    # Virtual event handlers, overide them in your derived class
    def onChar(self, event):
        self.resetCaret()

        if not self.isStarted:
            if event.GetKeyCode() == wx.WXK_RETURN:
                self.start()

            return

        # if self._isBusy:  # dont capture events when busy
        #     return

        if event.GetKeyCode() == wx.WXK_RETURN:
            self.txtTerm.SetInsertionPointEnd()
            entry = self._getTyped()
            if entry:
                self._history.appendleft(entry)
            self.push(entry)
            self._historyIdx = 0
        elif event.GetKeyCode() == wx.WXK_BACK:
            if self.txtTerm.GetInsertionPoint() <= self._lastTextPos:
                self.txtTerm.SetInsertionPoint(self._lastTextPos)
                return
        elif event.GetKeyCode() == wx.WXK_UP:
            if self._history:
                self._historyIdx = max(0, self._historyIdx + 1)
                self._clearAndReplaceTyped(self._history[self._historyIdx])
            return
        elif event.GetKeyCode() == wx.WXK_DOWN:
            if self._history:
                self._historyIdx = min(len(self._history), self._historyIdx - 1)
                self._clearAndReplaceTyped(self._history[self._historyIdx])
            return
        else:
            if self._history:
                self._historyIdx = 0

        event.Skip()


if __name__ == "__main__":
    pass
