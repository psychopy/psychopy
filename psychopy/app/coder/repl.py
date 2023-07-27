#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for the REPL shell in PsychoPy Coder."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import sys
import wx
import wx.richtext
from psychopy.app.themes import handlers, colors, icons, fonts
from psychopy.localization import _translate
import os


class ConsoleTextCtrl(wx.richtext.RichTextCtrl, handlers.ThemeMixin):
    """Class for the console text control. This is needed to allow for theming.
    """
    def __init__(self, parent, id_=wx.ID_ANY, value="", pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0,
                 name=wx.TextCtrlNameStr):

        wx.richtext.RichTextCtrl.__init__(
            self, parent, id=id_, value=value, pos=pos, size=size, style=style,
            validator=wx.DefaultValidator, name=name)


class PythonREPLCtrl(wx.Panel, handlers.ThemeMixin):
    """Class for a Python REPL control.

    An interactive shell (REPL) for interfacing with a Python interpreter in
    another process owned by the control.

    This class does not emulate a terminal/console perfectly, so things like
    'curses' and control characters (e.g., Ctrl+C) do not work. Unresponsive
    scripts must be stopped manually, resulting in a loss of the objects in the
    namespace. Therefore, it is recommended that users push lines to the
    shell using the script editor.

    """
    class PythonREPLToolbar(wx.Panel, handlers.ThemeMixin):
        def __init__(self, parent):
            wx.Panel.__init__(self, parent, size=(30, -1))
            self.parent = parent

            # Setup sizer
            self.borderBox = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.borderBox)
            self.sizer = wx.BoxSizer(wx.VERTICAL)
            self.borderBox.Add(self.sizer, border=6, flag=wx.ALL)
            # Start button
            self.startBtn = wx.Button(self, size=(16, 16), style=wx.BORDER_NONE)
            self.startBtn.SetToolTip(_translate(
                "Close the current shell."
            ))
            self.startBtn.SetBitmap(
                icons.ButtonIcon(stem="start", size=16).bitmap
            )
            self.sizer.Add(self.startBtn, border=6, flag=wx.BOTTOM)
            self.startBtn.Bind(wx.EVT_BUTTON, self.parent.start)
            # Restart button
            self.restartBtn = wx.Button(self, size=(16, 16), style=wx.BORDER_NONE)
            self.restartBtn.SetToolTip(_translate(
                "Close the current shell and start a new one, this will clear any variables."
            ))
            self.restartBtn.SetBitmap(
                icons.ButtonIcon(stem="restart", size=16).bitmap
            )
            self.sizer.Add(self.restartBtn, border=6, flag=wx.BOTTOM)
            self.restartBtn.Bind(wx.EVT_BUTTON, self.parent.restart)
            # Stop button
            self.stopBtn = wx.Button(self, size=(16, 16), style=wx.BORDER_NONE)
            self.stopBtn.SetToolTip(_translate(
                "Close the current shell."
            ))
            self.stopBtn.SetBitmap(
                icons.ButtonIcon(stem="stop", size=16).bitmap
            )
            self.sizer.Add(self.stopBtn, border=6, flag=wx.BOTTOM)
            self.stopBtn.Bind(wx.EVT_BUTTON, self.parent.close)
            # Clear button
            self.clrBtn = wx.Button(self, size=(16, 16), style=wx.BORDER_NONE)
            self.clrBtn.SetToolTip(_translate(
                "Clear all previous output."
            ))
            self.clrBtn.SetBitmap(
                icons.ButtonIcon(stem="clear", size=16).bitmap
            )
            self.sizer.Add(self.clrBtn, border=6, flag=wx.BOTTOM)
            self.clrBtn.Bind(wx.EVT_BUTTON, self.parent.clear)

            self.update()
            self.Layout()

        def update(self):
            self.startBtn.Show(not self.parent.isStarted)
            self.restartBtn.Show(self.parent.isStarted)
            self.stopBtn.Show(self.parent.isStarted)
            self.Layout()

        def _applyAppTheme(self):
            # Set background
            self.SetBackgroundColour(fonts.coderTheme.base.backColor)
            # Style buttons
            for btn in (self.startBtn, self.stopBtn, self.clrBtn, self.restartBtn):
                btn.SetBackgroundColour(fonts.coderTheme.base.backColor)
            self.Refresh()
            self.Update()

    def __init__(self,
                 parent,
                 id_=wx.ID_ANY,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL,
                 name=wx.EmptyString):

        wx.Panel.__init__(self, parent, id=id_, pos=pos, size=size, style=style,
                          name=name)
        self.tabIcon = "coderpython"

        # sizer for the panel
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Toolbar
        self.toolbar = self.PythonREPLToolbar(self)
        self.sizer.Add(self.toolbar, border=6, flag=wx.EXPAND | wx.TOP | wx.BOTTOM)

        # Sep
        self.sep = wx.Window(self, size=(1, -1))
        self.sizer.Add(self.sep, border=12, flag=wx.EXPAND | wx.TOP | wx.BOTTOM)

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
        self.sizer.Add(self.txtTerm, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        self.SetSizer(self.sizer)
        self.Layout()

        # capture keypresses
        if wx.Platform == '__WXMAC__' or wx.Platform == '__WXMSW__':
            # need to use this on MacOS and Windows
            keyDownBindingId = wx.EVT_KEY_DOWN
        else:
            keyDownBindingId = wx.EVT_CHAR

        self.txtTerm.Bind(keyDownBindingId, self.onChar)
        self.txtTerm.Bind(wx.EVT_TEXT_MAXLEN, self.onMaxLength)

        # history
        self._history = []
        self._historyIdx = 0

        # idle event
        self.Bind(wx.EVT_IDLE, self.onIdle)

        # hooks for the process we're communicating with
        self._process = self._pid = None

        # interpreter state information
        self._isBusy = self._suppress = False
        self._stdin_buffer = []
        self._lastTextPos = 0

        # Disable smart substitutions for quotes and slashes, uses illegal
        # characters that cannot be evaluated by the interpreter correctly.
        # if wx.Platform == '__WXMAC__':
        #     self.txtTerm.OSXDisableAllSmartSubstitutions()
        #     self.txtTerm.MacCheckSpelling(False)

        self.txtTerm.WriteText(_translate("Hit [Return] to start a Python session."))
        self._lastTextPos = self.txtTerm.GetLastPosition()

        # Setup fonts and margins
        self.setFonts()

    def setFonts(self):
        """Set the font for the console."""
        self.txtTerm._applyAppTheme()

    def onTerminate(self, event):
        # hooks for the process we're communicating with
        self._process = self._pid = None

        # interpreter state information
        self._isBusy = self._suppress = False
        self._stdin_buffer = []

        self.txtTerm.Clear()
        self.txtTerm.WriteText(_translate("Hit [Return] to start a Python shell."))
        self._lastTextPos = self.txtTerm.GetLastPosition()
        self.setFonts()
        self.toolbar.update()

    @property
    def isStarted(self):
        """`True` if the interpreter process has been started."""
        return self.process is not None

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
        if hasattr(self, "_process"):
            return self._process

    @property
    def pid(self):
        """Process ID for the interpreter (`int`)."""
        return self.getPid()

    def getPid(self):
        """Get the process ID for the active interpreter (`int`)."""
        return self._pid

    # def getPwd(self):
    #     """Get the present working directory for the interpreter.
    #     """
    #     pass
    #
    # def setPwd(self):
    #     """Set the present working directory for the interpreter.
    #     """
    #     pass

    def getNamespace(self):
        """Get variable names in the current namespace.
        """
        self.push('dir()')  # get namespace values

    def onIdle(self, event):
        """Idle event.

        This is hooked into the main application even loop. When idle, the
        input streams are checked and any data is written to the text box.

        Output from `stderr` is ignored until there is nothing left to read from
        the input stream.

        """
        # don't do anything unless we have an active process
        if not self.isStarted:
            return

        # we have new characters
        newChars = False

        # reset
        stdin_text = ''
        stderr_text = ''

        # check if we have input text to process
        if self._process.IsInputAvailable():
            stdin_text = self._process.InputStream.read()
            txt = stdin_text.decode('utf-8')
            self.txtTerm.WriteText(txt)

            # special stuff
            if txt == '\r':  # handle carriage returns at some point
                pass

            # hack to get the interactive help working
            try:
                if self.txtTerm.GetValue()[-6:] == 'help> ':
                    self._isBusy = False
            except IndexError:
                pass

            newChars = True
        else:
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
            self.txtTerm.SetInsertionPoint(-1)
            self.txtTerm.ShowPosition(self._lastTextPos)
            # self.setFonts()  # update fonts

    def resetCaret(self):
        """Place the caret at the entry position if not in an editable region.
        """
        if self.txtTerm.GetInsertionPoint() < self._lastTextPos:
            self.txtTerm.SetInsertionPoint(self._lastTextPos)
            return

    def push(self, lines):
        """Push a line to the interpreter.

        Parameter
        ---------
        line : str
            Lines to push to the terminal.

        """
        if not self.isStarted:
            return

        # convert to bytes
        for line in lines.split('\n'):
            self.submit(line)

    def submit(self, line):
        """Submit the current line to the interpreter.
        """
        if not self.isStarted:
            return

        if not line.endswith('\n'):
            line += '\n'

        self._process.OutputStream.write(line.encode())
        self._process.OutputStream.flush()

        self._isBusy = True

    def start(self, evt=None):
        """Start a new interpreter process.
        """
        if self.isStarted:  # nop if started already
            self.toolbar.update()
            return

        # inform the user that we're starting the console
        self.txtTerm.Clear()
        self.txtTerm.WriteText(
            "Starting Python interpreter session, please wait ...\n")

        self.txtTerm._applyAppTheme()

        # setup the sub-process
        wx.BeginBusyCursor()
        self._process = wx.Process(self)
        self._process.Redirect()

        # get the path to the interpreter
        interpPath = '"' + sys.executable + '"'

        # start the sub-process
        self._pid = wx.Execute(
            r' '.join([interpPath, r'-i']),
            wx.EXEC_ASYNC,
            self._process)

        # bind the event called when the process ends
        self._process.Bind(wx.EVT_END_PROCESS, self.onTerminate)

        # clear all text in the widget and display the welcome message
        self.txtTerm.Clear()
        self.txtTerm.WriteText(
            "Python shell in PsychoPy (pid:{}) - type some commands!\n".format(
                self._pid))  # show the subprocess PID for reference
        self._lastTextPos = self.txtTerm.GetLastPosition()
        self.toolbar.update()

        self.setFonts()
        wx.EndBusyCursor()

    def interrupt(self, evt=None):
        """Send a keyboard interrupt signal to the interpreter.
        """
        if self.isStarted:
            os.kill(self._pid, wx.SIGINT)
        self.toolbar.update()

    def close(self, evt=None):
        """Close an open interpreter.
        """
        if self.isStarted:
            os.kill(self._pid, wx.SIGTERM)

    def restart(self, evt=None):
        """Close the running interpreter (if running) and spawn a new one.
        """
        self.close()
        self.start()

    def clear(self, evt=None):
        """Clear the contents of the console.
        """
        self.txtTerm.Clear()
        self._lastTextPos = self.txtTerm.GetLastPosition()
        self.push('')
        self.setFonts()

    def onMaxLength(self, event):
        """What to do if we exceed the buffer size limit for the control.
        """
        event.Skip()

    def __del__(self):
        pass

    def clearAndReplaceTyped(self, replaceWith=''):
        """Clear any text that has been typed.
        """
        self.txtTerm.Remove(self._lastTextPos, self.txtTerm.GetLastPosition())
        if replaceWith:
            self.txtTerm.WriteText(replaceWith)

        self.txtTerm.SetInsertionPoint(self.txtTerm.GetLastPosition())

    def getTyped(self):
        """Get the text that was typed or is editable (`str`).
        """
        return self.txtTerm.GetRange(
            self._lastTextPos,
            self.txtTerm.GetLastPosition())

    def onChar(self, event):
        """Called when the shell gets a keypress event.
        """
        self.resetCaret()

        if not self.isStarted:
            if event.GetKeyCode() == wx.WXK_RETURN:
                self.start()

            event.Skip()
            return

        # if self._isBusy:  # dont capture events when busy
        #     return
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.txtTerm.SetInsertionPointEnd()
            entry = self.getTyped()
            if entry:
                self._history.insert(0, entry)
            self.push(entry)
            self._historyIdx = -1
        elif event.GetKeyCode() == wx.WXK_BACK or event.GetKeyCode() == wx.WXK_LEFT:
            # prevent the cursor from leaving the editable region
            if self.txtTerm.GetInsertionPoint() <= self._lastTextPos:
                self.txtTerm.SetInsertionPoint(self._lastTextPos)
                return
        elif event.GetKeyCode() == wx.WXK_UP:
            # get previous (last entered) item in history
            if self._history:
                self._historyIdx = min(
                    max(0, self._historyIdx + 1),
                    len(self._history) - 1)
                self.clearAndReplaceTyped(self._history[self._historyIdx])
            return
        elif event.GetKeyCode() == wx.WXK_DOWN:
            # get next item in history
            if self._history:
                self._historyIdx = max(self._historyIdx - 1, -1)
                if self._historyIdx >= 0:
                    self.clearAndReplaceTyped(self._history[self._historyIdx])
                else:
                    self.clearAndReplaceTyped()
            return
        elif event.GetKeyCode() == wx.WXK_F8:  # interrupt a misbehaving terminal
            self.interrupt()
        elif event.GetKeyCode() == wx.WXK_F4:  # clear the screen
            self.clear()
        else:
            if self._history:
                self._historyIdx = -1

        event.Skip()

    def _applyAppTheme(self):
        # Set background
        self.SetBackgroundColour(fonts.coderTheme.base.backColor)
        self.Refresh()
        self.Update()
        # Match line
        self.sep.SetBackgroundColour(fonts.coderTheme.margin.backColor)
        self.Refresh()
        self.Update()


if __name__ == "__main__":
    pass
