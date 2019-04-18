#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

# from future import standard_library
# standard_library.install_aliases()
from builtins import chr
from builtins import str
from builtins import range
import time
import types
import wx
import wx.stc
import wx.richtext
from wx.html import HtmlEasyPrinting

import psychopy.app.pavlovia_ui.menu

try:
    from wx import aui
except Exception:
    import wx.lib.agw.aui as aui  # some versions of phoenix

import keyword
import os
import sys
import glob
import io
import threading
import bdb
import pickle
import py_compile
import locale

from . import psychoParser
from .. import stdOutRich, dialogs
from .. import pavlovia_ui
from psychopy import logging
from psychopy.localization import _translate
from ..utils import FileDropTarget
from psychopy.constants import PY3
from psychopy.projects import pavlovia
from psychopy.app.coder.codeEditorBase import BaseCodeEditor

# advanced prefs (not set in prefs files)
prefTestSubset = ""
analysisLevel = 1
analyseAuto = True
runScripts = 'process'

try:  # needed for wx.py shell
    import code

    haveCode = True
except Exception:
    haveCode = False

_localized = {'basic': _translate('basic'),
              'input': _translate('input'),
              'stimuli': _translate('stimuli'),
              'experiment control': _translate('exp control'),
              'iohub': 'ioHub',  # no translation
              'hardware': _translate('hardware'),
              'timing': _translate('timing'),
              'misc': _translate('misc')}


def toPickle(filename, data):
    """save data (of any sort) as a pickle file

    simple wrapper of the cPickle module in core python
    """
    with io.open(filename, 'wb') as f:
        pickle.dump(data, f)


def fromPickle(filename):
    """load data (of any sort) from a pickle file

    simple wrapper of the cPickle module in core python
    """
    with io.open(filename, 'rb') as f:
        contents = pickle.load(f)

    return contents


class Printer(HtmlEasyPrinting):
    """bare-bones printing, no control over anything

    from http://wiki.wxpython.org/Printing
    """

    def __init__(self):
        HtmlEasyPrinting.__init__(self)

    def GetHtmlText(self, text):
        "Simple conversion of text."

        text = text.replace('&', '&amp;')
        text = text.replace('<P>', '&#60;P&#62;')
        text = text.replace('<BR>', '&#60;BR&#62;')
        text = text.replace('<HR>', '&#60;HR&#62;')
        text = text.replace('<p>', '&#60;p&#62;')
        text = text.replace('<br>', '&#60;br&#62;')
        text = text.replace('<hr>', '&#60;hr&#62;')
        text = text.replace('\n\n', '<P>')
        text = text.replace('\t', '    ')  # tabs -> 4 spaces
        text = text.replace(' ', '&nbsp;')  # preserve indentation
        html_text = text.replace('\n', '<BR>')
        return html_text

    def Print(self, text, doc_name):
        self.SetHeader(doc_name)
        self.PrintText('<HR>' + self.GetHtmlText(text), doc_name)


class ScriptThread(threading.Thread):
    """A subclass of threading.Thread, with a kill() method.
    """

    def __init__(self, target, gui):
        threading.Thread.__init__(self, target=target)
        self.killed = False
        self.gui = gui

    def start(self):
        """Start the thread.
        """
        self.__run_backup = self.run
        self.run = self.__run  # force the Thread to install our trace.
        threading.Thread.start(self)

    def __run(self):
        """Hacked run function, which installs the trace.
        """
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup
        # we're done - send the App a message
        self.gui.onProcessEnded(event=None)

    def globaltrace(self, frame, why, arg):
        if why == 'call':
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, why, arg):
        if self.killed:
            if why == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True


class PsychoDebugger(bdb.Bdb):
    # this is based on effbot: http://effbot.org/librarybook/bdb.htm

    def __init__(self):
        bdb.Bdb.__init__(self)
        self.starting = True

    def user_call(self, frame, args):
        name = frame.f_code.co_name or "<unknown>"
        self.set_continue()  # continue

    def user_line(self, frame):
        if self.starting:
            self.starting = False
            self.set_trace()  # start tracing
        else:
            # arrived at breakpoint
            name = frame.f_code.co_name or "<unknown>"
            filename = self.canonic(frame.f_code.co_filename)
            print("break at %s %i in %s" % (filename, frame.f_lineno, name))
        self.set_continue()  # continue to next breakpoint

    def user_return(self, frame, value):
        name = frame.f_code.co_name or "<unknown>"
        self.set_continue()  # continue

    def user_exception(self, frame, exception):
        name = frame.f_code.co_name or "<unknown>"
        self.set_continue()  # continue

    def quit(self):
        self._user_requested_quit = 1
        self.set_quit()
        return 1


class UnitTestFrame(wx.Frame):
    class _unitTestOutRich(stdOutRich.StdOutRich):
        """richTextCtrl window for unit test output"""

        def __init__(self, parent, style, size=None, **kwargs):
            stdOutRich.StdOutRich.__init__(self, parent=parent, style=style,
                                           size=size)
            self.bad = [150, 0, 0]
            self.good = [0, 150, 0]
            self.skip = [170, 170, 170]
            self.png = []

        def write(self, inStr):
            self.MoveEnd()  # always 'append' text rather than 'writing' it
            for thisLine in inStr.splitlines(True):
                if thisLine.startswith('OK'):
                    self.BeginBold()
                    self.BeginTextColour(self.good)
                    self.WriteText("OK")
                    self.EndTextColour()
                    self.EndBold()
                    self.WriteText(thisLine[2:])  # for OK (SKIP=xx)
                    self.parent.status = 1
                elif thisLine.startswith('#####'):
                    self.BeginBold()
                    self.WriteText(thisLine)
                    self.EndBold()
                elif 'FAIL' in thisLine or 'ERROR' in thisLine:
                    self.BeginTextColour(self.bad)
                    self.WriteText(thisLine)
                    self.EndTextColour()
                    self.parent.status = -1
                elif thisLine.find('SKIP') > -1:
                    self.BeginTextColour(self.skip)
                    self.WriteText(thisLine.strip())
                    # show the new image, double size for easier viewing:
                    if thisLine.strip().endswith('.png'):
                        newImg = thisLine.split()[-1]
                        img = os.path.join(self.parent.paths['tests'],
                                           'data', newImg)
                        self.png.append(wx.Image(img, wx.BITMAP_TYPE_ANY))
                        self.MoveEnd()
                        self.WriteImage(self.png[-1])
                    self.MoveEnd()
                    self.WriteText('\n')
                    self.EndTextColour()
                else:  # line to write as simple text
                    self.WriteText(thisLine)
                if thisLine.find('Saved copy of actual frame') > -1:
                    # show the new images, double size for easier viewing:
                    newImg = [f for f in thisLine.split()
                              if f.find('_local.png') > -1]
                    newFile = newImg[0]
                    origFile = newFile.replace('_local.png', '.png')
                    img = os.path.join(self.parent.paths['tests'], origFile)
                    self.png.append(wx.Image(img, wx.BITMAP_TYPE_ANY))
                    self.MoveEnd()
                    self.WriteImage(self.png[-1])
                    self.MoveEnd()
                    self.WriteText('= ' + origFile + ';   ')
                    img = os.path.join(self.parent.paths['tests'], newFile)
                    self.png.append(wx.Image(img, wx.BITMAP_TYPE_ANY))
                    self.MoveEnd()
                    self.WriteImage(self.png[-1])
                    self.MoveEnd()
                    self.WriteText('= ' + newFile + '; ')

            self.MoveEnd()  # go to end of stdout so user can see updated text
            self.ShowPosition(self.GetLastPosition())

    def __init__(self, parent=None, ID=-1,
                 title=_translate('PsychoPy unit testing'),
                 files=(), app=None):
        self.app = app
        self.frameType = 'unittest'
        self.prefs = self.app.prefs
        self.paths = self.app.prefs.paths
        # deduce the script for running the tests
        try:
            import pytest
            havePytest = True
        except Exception:
            havePytest = False
        if havePytest:
            self.runpyPath = os.path.join(self.prefs.paths['tests'], 'run.py')
        else:
            # run the standalone version
            self.runpyPath = os.path.join(
                self.prefs.paths['tests'], 'runPytest.py')
        if sys.platform != 'win32':
            self.runpyPath = self.runpyPath.replace(' ', '\ ')
        # setup the frame
        self.IDs = self.app.IDs
        # to right, so Cancel button is clickable during a long test
        wx.Frame.__init__(self, parent, ID, title, pos=(450, 45))
        self.scriptProcess = None
        self.runAllText = 'all tests'
        border = 10
        # status = outcome of the last test run: -1 fail, 0 not run, +1 ok:
        self.status = 0

        # create menu items
        menuBar = wx.MenuBar()
        self.menuTests = wx.Menu()
        menuBar.Append(self.menuTests, _translate('&Tests'))
        _run = self.app.keys['runScript']
        self.menuTests.Append(wx.ID_APPLY,
                              _translate("&Run tests\t%s") % _run)
        self.Bind(wx.EVT_MENU, self.onRunTests, id=wx.ID_APPLY)
        _stop = self.app.keys['stopScript']
        self.menuTests.Append(self.IDs.stopFile,
                              _translate("&Cancel running test\t%s") % _stop,
                              _translate("Quit a test in progress"))
        self.Bind(wx.EVT_MENU, self.onCancelTests, id=self.IDs.stopFile)
        self.menuTests.AppendSeparator()
        self.menuTests.Append(wx.ID_CLOSE, _translate(
            "&Close tests panel\t%s") % self.app.keys['close'])
        self.Bind(wx.EVT_MENU, self.onCloseTests, id=wx.ID_CLOSE)
        _switch = self.app.keys['switchToCoder']
        self.menuTests.Append(self.IDs.openCoderView,
                              _translate("Go to &Coder view\t%s") % _switch,
                              _translate("Go to the Coder view"))
        self.Bind(wx.EVT_MENU, self.app.showCoder, id=self.IDs.openCoderView)
        # -------------quit
        self.menuTests.AppendSeparator()
        _quit = self.app.keys['quit']
        self.menuTests.Append(wx.ID_EXIT,
                              _translate("&Quit\t%s") % _quit,
                              _translate("Terminate PsychoPy"))
        self.Bind(wx.EVT_MENU, self.app.quit, id=wx.ID_EXIT)
        item = self.menuTests.Append(
            wx.ID_PREFERENCES, text=_translate("&Preferences"))
        self.Bind(wx.EVT_MENU, self.app.showPrefs, item)
        self.SetMenuBar(menuBar)

        # create controls
        buttonsSizer = wx.BoxSizer(wx.HORIZONTAL)
        _style = wx.TE_MULTILINE | wx.TE_READONLY | wx.EXPAND | wx.GROW
        _font = self.prefs.coder['outputFont']
        _fsize = self.prefs.coder['outputFontSize']
        self.outputWindow = self._unitTestOutRich(self, style=_style,
                                                  size=wx.Size(750, 500),
                                                  font=_font, fontSize=_fsize)

        knownTests = glob.glob(os.path.join(self.paths['tests'], 'test*'))
        knownTestList = [t.split(os.sep)[-1] for t in knownTests
                         if t.endswith('.py') or os.path.isdir(t)]
        self.knownTestList = [self.runAllText] + knownTestList
        self.testSelect = wx.Choice(parent=self, id=-1, pos=(border, border),
                                    choices=self.knownTestList)
        tip = _translate(
            "Select the test(s) to run, from:\npsychopy/tests/test*")
        self.testSelect.SetToolTip(wx.ToolTip(tip))
        prefTestSubset = self.prefs.appData['testSubset']
        # preselect the testGroup in the drop-down menu for display:
        if prefTestSubset in self.knownTestList:
            self.testSelect.SetStringSelection(prefTestSubset)

        self.btnRun = wx.Button(parent=self, label=_translate("Run tests"))
        self.btnRun.Bind(wx.EVT_BUTTON, self.onRunTests)
        self.btnCancel = wx.Button(parent=self, label=_translate("Cancel"))
        self.btnCancel.Bind(wx.EVT_BUTTON, self.onCancelTests)
        self.btnCancel.Disable()
        self.Bind(wx.EVT_END_PROCESS, self.onTestsEnded)

        self.chkCoverage = wx.CheckBox(
            parent=self, label=_translate("Coverage Report"))
        _tip = _translate("Include coverage report (requires coverage module)")
        self.chkCoverage.SetToolTip(wx.ToolTip(_tip))
        self.chkCoverage.Disable()
        self.chkAllStdOut = wx.CheckBox(
            parent=self, label=_translate("ALL stdout"))
        _tip = _translate(
            "Report all printed output & show any new rms-test images")
        self.chkAllStdOut.SetToolTip(wx.ToolTip(_tip))
        self.chkAllStdOut.Disable()
        self.Bind(wx.EVT_IDLE, self.onIdle)
        self.SetDefaultItem(self.btnRun)

        # arrange controls
        buttonsSizer.Add(self.chkCoverage, 0, wx.LEFT |
                         wx.RIGHT | wx.TOP, border=border)
        buttonsSizer.Add(self.chkAllStdOut, 0, wx.LEFT |
                         wx.RIGHT | wx.TOP, border=border)
        buttonsSizer.Add(self.btnRun, 0, wx.LEFT |
                         wx.RIGHT | wx.TOP, border=border)
        buttonsSizer.Add(self.btnCancel, 0, wx.LEFT |
                         wx.RIGHT | wx.TOP, border=border)
        self.sizer = wx.BoxSizer(orient=wx.VERTICAL)
        self.sizer.Add(buttonsSizer, 0, wx.ALIGN_RIGHT)
        self.sizer.Add(self.outputWindow, 0, wx.ALL |
                       wx.EXPAND | wx.GROW, border=border)
        self.SetSizerAndFit(self.sizer)
        self.Show()

    def onRunTests(self, event=None):
        """Run the unit tests
        """
        self.status = 0

        # create process
        # self is the parent (which will receive an event when the process
        # ends)
        self.scriptProcess = wx.Process(self)
        self.scriptProcess.Redirect()  # catch the stdout/stdin
        # include coverage report?
        if self.chkCoverage.GetValue():
            coverage = ' cover'
        else:
            coverage = ''
        # printing ALL output?
        if self.chkAllStdOut.GetValue():
            allStdout = ' -s'
        else:
            allStdout = ''
        # what subset of tests? (all tests == '')
        tselect = self.knownTestList[self.testSelect.GetCurrentSelection()]
        if tselect == self.runAllText:
            tselect = ''
        testSubset = tselect
        # self.prefs.appData['testSubset'] = tselect # in onIdle

        # launch the tests using wx.Execute():
        self.btnRun.Disable()
        self.btnCancel.Enable()
        if sys.platform == 'win32':
            testSubset = ' ' + testSubset
            args = (sys.executable, self.runpyPath, coverage,
                    allStdout, testSubset)
            command = '"%s" -u "%s" %s%s%s' % args  # quotes handle spaces
            print(command)
            self.scriptProcessID = wx.Execute(
                command, wx.EXEC_ASYNC, self.scriptProcess)
            # self.scriptProcessID = wx.Execute(command,
            #    # wx.EXEC_ASYNC| wx.EXEC_NOHIDE, self.scriptProcess)
        else:
            testSubset = ' ' + testSubset.replace(' ', '\ ')  # protect spaces
            args = (sys.executable, self.runpyPath, coverage,
                    allStdout, testSubset)
            command = '%s -u %s%s%s%s' % args
            _opt = wx.EXEC_ASYNC | wx.EXEC_MAKE_GROUP_LEADER
            self.scriptProcessID = wx.Execute(command,
                                              _opt, self.scriptProcess)
        msg = "\n##### Testing: %s%s%s%s   #####\n\n" % (
            self.runpyPath, coverage, allStdout, testSubset)
        self.outputWindow.write(msg)
        _notNormUnits = self.app.prefs.general['units'] != 'norm'
        if _notNormUnits and 'testVisual' in testSubset:
            msg = "Note: default window units = '%s' (in prefs); for visual tests 'norm' is recommended.\n\n"
            self.outputWindow.write(msg % self.app.prefs.general['units'])

    def onCancelTests(self, event=None):
        if self.scriptProcess != None:
            self.scriptProcess.Kill(
                self.scriptProcessID, wx.SIGTERM, wx.SIGKILL)
        self.scriptProcess = None
        self.scriptProcessID = None
        self.outputWindow.write("\n --->> cancelled <<---\n\n")
        self.status = 0
        self.onTestsEnded()

    def onIdle(self, event=None):
        # auto-save last selected subset:
        self.prefs.appData['testSubset'] = self.knownTestList[
            self.testSelect.GetCurrentSelection()]
        if self.scriptProcess != None:
            if self.scriptProcess.IsInputAvailable():
                stream = self.scriptProcess.GetInputStream()
                text = stream.read()
                self.outputWindow.write(text)
            if self.scriptProcess.IsErrorAvailable():
                stream = self.scriptProcess.GetErrorStream()
                text = stream.read()
                self.outputWindow.write(text)

    def onTestsEnded(self, event=None):
        self.onIdle()  # so that any final stdout/err gets written
        self.outputWindow.flush()
        self.btnRun.Enable()
        self.btnCancel.Disable()

    def onURL(self, evt):
        """decompose the URL of a file and line number"""
        # "C:\Program Files\wxPython2.8 Docs and Demos\samples\hangman\hangman.py"
        tmpFilename, tmpLineNumber = evt.GetString().rsplit('", line ', 1)
        filename = tmpFilename.split('File "', 1)[1]
        try:
            lineNumber = int(tmpLineNumber.split(',')[0])
        except ValueError:
            lineNumber = int(tmpLineNumber.split()[0])
        self.app.coder.gotoLine(filename, lineNumber)

    def onCloseTests(self, evt):
        self.Destroy()


class CodeEditor(BaseCodeEditor):
    # this comes mostly from the wxPython demo styledTextCtrl 2

    def __init__(self, parent, ID, frame,
                 # set the viewer to be small, then it will increase with aui
                 # control
                 pos=wx.DefaultPosition, size=wx.Size(100, 100),
                 style=0, readonly=False):
        BaseCodeEditor.__init__(self, parent, ID, pos, size, style)

        self.coder = frame
        self.SetViewWhiteSpace(self.coder.appData['showWhitespace'])
        self.SetViewEOL(self.coder.appData['showEOLs'])
        self.Bind(wx.EVT_DROP_FILES, self.coder.filesDropped)
        self.Bind(wx.stc.EVT_STC_MODIFIED, self.onModified)
        # self.Bind(wx.stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
        self.Bind(wx.stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyPressed)

        # black-and-white text signals read-only file open in Coder window
        if not readonly:
            self.setFonts()
        self.SetDropTarget(FileDropTarget(targetFrame=self.coder))

        # set to python syntax code coloring
        self.setLexer('python')

    def setFonts(self):
        """Make some styles,  The lexer defines what each style is used for,
        we just have to define what each style looks like.  This set is
        adapted from Scintilla sample property files."""

        if wx.Platform == '__WXMSW__':
            faces = {'size': 10}
        elif wx.Platform == '__WXMAC__':
            faces = {'size': 14}
        else:
            faces = {'size': 12}
        if self.coder.prefs['codeFontSize']:
            faces['size'] = int(self.coder.prefs['codeFontSize'])
        faces['small'] = faces['size'] - 2
        # Global default styles for all languages
        # ,'Arial']  # use arial as backup
        faces['code'] = self.coder.prefs['codeFont']
        # ,'Arial']  # use arial as backup
        faces['comment'] = self.coder.prefs['commentFont']
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,
                          "face:%(code)s,size:%(size)d" % faces)
        self.StyleClearAll()  # Reset all to be like the default

        # Global default styles for all languages
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,
                          "face:%(code)s,size:%(size)d" % faces)
        self.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER,
                          "back:#C0C0C0,face:%(code)s,size:%(small)d" % faces)
        self.StyleSetSpec(wx.stc.STC_STYLE_CONTROLCHAR,
                          "face:%(comment)s" % faces)
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACELIGHT,
                          "fore:#FFFFFF,back:#0000FF,bold")
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACEBAD,
                          "fore:#000000,back:#FF0000,bold")

        # Python styles
        # Default
        self.StyleSetSpec(wx.stc.STC_P_DEFAULT,
                          "fore:#000000,face:%(code)s,size:%(size)d" % faces)
        # Comments
        self.StyleSetSpec(wx.stc.STC_P_COMMENTLINE,
                          "fore:#007F00,face:%(comment)s,size:%(size)d" % faces)
        # Number
        self.StyleSetSpec(wx.stc.STC_P_NUMBER,
                          "fore:#007F7F,size:%(size)d" % faces)
        # String
        self.StyleSetSpec(wx.stc.STC_P_STRING,
                          "fore:#7F007F,face:%(code)s,size:%(size)d" % faces)
        # Single quoted string
        self.StyleSetSpec(wx.stc.STC_P_CHARACTER,
                          "fore:#7F007F,face:%(code)s,size:%(size)d" % faces)
        # Keyword
        self.StyleSetSpec(wx.stc.STC_P_WORD,
                          "fore:#00007F,bold,size:%(size)d" % faces)
        # Triple quotes
        self.StyleSetSpec(wx.stc.STC_P_TRIPLE,
                          "fore:#7F0000,size:%(size)d" % faces)
        # Triple double quotes
        self.StyleSetSpec(wx.stc.STC_P_TRIPLEDOUBLE,
                          "fore:#7F0000,size:%(size)d" % faces)
        # Class name definition
        self.StyleSetSpec(wx.stc.STC_P_CLASSNAME,
                          "fore:#0000FF,bold,underline,size:%(size)d" % faces)
        # Function or method name definition
        self.StyleSetSpec(wx.stc.STC_P_DEFNAME,
                          "fore:#007F7F,bold,size:%(size)d" % faces)
        # Operators
        self.StyleSetSpec(wx.stc.STC_P_OPERATOR, "bold,size:%(size)d" % faces)
        # Identifiers
        self.StyleSetSpec(wx.stc.STC_P_IDENTIFIER,
                          "fore:#000000,face:%(code)s,size:%(size)d" % faces)
        # Comment-blocks
        self.StyleSetSpec(wx.stc.STC_P_COMMENTBLOCK,
                          "fore:#7F7F7F,size:%(size)d" % faces)
        # End of line where string is not closed
        self.StyleSetSpec(wx.stc.STC_P_STRINGEOL,
                          "fore:#000000,face:%(code)s,back:#E0C0E0,eol,size:%(size)d" % faces)

        self.SetCaretForeground("BLUE")

    def OnKeyPressed(self, event):
        # various stuff to handle code completion and tooltips
        # enable in the _-init__
        if self.CallTipActive():
            self.CallTipCancel()
        keyCode = event.GetKeyCode()
        _mods = event.GetModifiers()

        # handle some special keys
        if keyCode == ord('[') and wx.MOD_CONTROL == _mods:
            self.indentSelection(-4)
            # if there are no characters on the line then also move caret to
            # end of indentation
            txt, charPos = self.GetCurLine()
            if charPos == 0:
                # if caret is at start of line, move to start of text instead
                self.VCHome()
        if keyCode == ord(']') and wx.MOD_CONTROL == _mods:
            self.indentSelection(4)
            # if there are no characters on the line then also move caret to
            # end of indentation
            txt, charPos = self.GetCurLine()
            if charPos == 0:
                # if caret is at start of line, move to start of text instead
                self.VCHome()

        if keyCode == ord('/') and wx.MOD_CONTROL == _mods:
            self.commentLines()
        if keyCode == ord('/') and wx.MOD_CONTROL | wx.MOD_SHIFT == _mods:
            self.uncommentLines()

        # do code completion
        if self.AUTOCOMPLETE:
            # get last word any previous word (if there was a dot instead of
            # space)
            isAlphaNum = bool(keyCode in list(range(65, 91)) + list(range(97, 123)))
            isDot = bool(keyCode == 46)
            prevWord = None
            if isAlphaNum:  # any alphanum
                # is character key
                key = chr(keyCode)
                # if keyCode == 32 and event.ControlDown():  # Ctrl-space
                pos = self.GetCurrentPos()
                prevStartPos = startPos = self.WordStartPosition(pos, True)
                currWord = self.GetTextRange(startPos, pos) + key

                # check if this is an attribute of another class etc...
                # then previous char was .
                while self.GetCharAt(prevStartPos - 1) == 46:
                    prevStartPos = self.WordStartPosition(
                        prevStartPos - 1, True)
                    prevWord = self.GetTextRange(prevStartPos, startPos - 1)

            # slightly different if this char is itself a dot
            elif isDot:  # we have a '.' so look for methods/attributes
                pos = self.GetCurrentPos()
                prevStartPos = startPos = self.WordStartPosition(pos, True)
                prevWord = self.GetTextRange(startPos, pos)
                currWord = ''
                # then previous char was .
                while self.GetCharAt(prevStartPos - 1) == 46:
                    prevStartPos = self.WordStartPosition(prevStartPos - 1,
                                                          True)
                    prevWord = self.GetTextRange(prevStartPos, pos - 1)

            self.AutoCompSetIgnoreCase(True)
            self.AutoCompSetAutoHide(True)
            # try to get attributes for this object
            event.Skip()
            if isAlphaNum or isDot:
                if True:
                    # use our own dictionary
                    # after a '.' show attributes
                    subList = []  # by default
                    # did we get a word?
                    if prevWord:
                        # is it in dictionary?
                        if prevWord in self.autoCompleteDict:
                            attrs = self.autoCompleteDict[prevWord]['attrs']
                            # does it have known attributes?
                            if type(attrs) == list and len(attrs) >= 1:
                                subList = [s for s in attrs if
                                           currWord.lower() in s.lower()]
                    # for objects show simple completions
                    else:  # there was no preceding '.'
                        # start trying after 2 characters
                        autokeys = list(self.autoCompleteDict.keys())
                        if len(currWord) > 1 and len(autokeys) > 1:
                            subList = [s for s in autokeys
                                       if currWord.lower() in s.lower()]
                else:
                    # use introspect (from wxpython's py package)
                    pass
                # if there were any reasonable matches then show them
                if len(subList) > 0:
                    subList.sort()
                    self.AutoCompShow(len(currWord) - 1, " ".join(subList))

        if keyCode == wx.WXK_RETURN and not self.AutoCompActive():
            # prcoess end of line and then do smart indentation
            event.Skip(False)
            self.CmdKeyExecute(wx.stc.STC_CMD_NEWLINE)
            self.smartIdentThisLine()
            return  # so that we don't reach the skip line at end

        event.Skip()

    def MacOpenFile(self, evt):
        logging.debug('PsychoPyCoder: got MacOpenFile event')

    def OnUpdateUI(self, evt):
        # check for matching braces
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        caretPos = self.GetCurrentPos()

        if caretPos > 0:
            charBefore = self.GetCharAt(caretPos - 1)
            styleBefore = self.GetStyleAt(caretPos - 1)

        # check before
        if charBefore and chr(charBefore) in "[]{}()":
            if styleBefore == wx.stc.STC_P_OPERATOR:
                braceAtCaret = caretPos - 1

        # check after
        if braceAtCaret < 0:
            charAfter = self.GetCharAt(caretPos)
            styleAfter = self.GetStyleAt(caretPos)
            if charAfter and chr(charAfter) in "[]{}()":
                if styleAfter == wx.stc.STC_P_OPERATOR:
                    braceAtCaret = caretPos

        if braceAtCaret >= 0:
            braceOpposite = self.BraceMatch(braceAtCaret)

        if braceAtCaret != -1 and braceOpposite == -1:
            self.BraceBadLight(braceAtCaret)
        else:
            self.BraceHighlight(braceAtCaret, braceOpposite)

    #
    # The code to handle the Source Assistant (using introspect) was broken and removed in 1.90.0
    #     if self.coder.prefs['showSourceAsst']:
    #         # check current word including .
    #         if charBefore == ord('('):
    #             startPos = self.WordStartPosition(caretPos - 2, True)
    #             endPos = caretPos - 1
    #         else:
    #             startPos = self.WordStartPosition(caretPos, True)
    #             endPos = self.WordEndPosition(caretPos, True)
    #         # extend starPos back to beginning of class separated by .
    #         while self.GetCharAt(startPos - 1) == ord('.'):
    #             startPos = self.WordStartPosition(startPos - 1, True)
    #         # now retrieve word
    #         currWord = self.GetTextRange(startPos, endPos)
    #
    #         # lookfor word in dictionary
    #         if currWord in self.autoCompleteDict:
    #             helpText = self.autoCompleteDict[currWord]['help']
    #             thisIs = self.autoCompleteDict[currWord]['is']
    #             thisType = self.autoCompleteDict[currWord]['type']
    #             thisAttrs = self.autoCompleteDict[currWord]['attrs']
    #             if type(thisIs) == str:  # if this is a module
    #                 searchFor = thisIs
    #             else:
    #                 searchFor = currWord
    #         else:
    #             helpText = None
    #             thisIs = None
    #             thisAttrs = None
    #             thisType = None
    #             searchFor = currWord
    #
    #         if self.prevWord != currWord:
    #             # if we have a class or function then use introspect (because
    #             # it retrieves args as well as __doc__)
    #             if thisType is not 'instance':
    #                 wd, kwArgs, helpText = introspect.getCallTip(
    #                     searchFor, locals=self.locals)
    #             # then pass all info to sourceAsst
    #             # for an instance inclue known attrs
    #             self.updateSourceAsst(
    #                 currWord, thisIs, helpText, thisType, thisAttrs)
    #
    #             self.prevWord = currWord  # update for next time
    #
    # def updateSourceAsst(self, currWord, thisIs, helpText, thisType=None,
    #                      knownAttrs=None):
    #         # update the source assistant window
    #     sa = self.coder.sourceAsstWindow
    #     assert isinstance(sa, wx.richtext.RichTextCtrl)
    #     # clear the buffer
    #     sa.Clear()
    #
    #     # add current symbol
    #     sa.BeginBold()
    #     sa.WriteText('Symbol: ')
    #     sa.BeginTextColour('BLUE')
    #     sa.WriteText(currWord + '\n')
    #     sa.EndTextColour()
    #     sa.EndBold()
    #
    #     # add expected type
    #     sa.BeginBold()
    #     sa.WriteText('is: ')
    #     sa.EndBold()
    #     if thisIs:
    #         sa.WriteText(str(thisIs) + '\n')
    #     else:
    #         sa.WriteText('\n')
    #
    #     # add expected type
    #     sa.BeginBold()
    #     sa.WriteText('type: ')
    #     sa.EndBold()
    #     if thisIs:
    #         sa.WriteText(str(thisType) + '\n')
    #     else:
    #         sa.WriteText('\n')
    #
    #     # add help text
    #     sa.BeginBold()
    #     sa.WriteText('Help:\n')
    #     sa.EndBold()
    #     if helpText:
    #         sa.WriteText(helpText + '\n')
    #     else:
    #         sa.WriteText('\n')
    #
    #     # add attrs
    #     sa.BeginBold()
    #     sa.WriteText('Known methods:\n')
    #     sa.EndBold()
    #     if knownAttrs:
    #         if len(knownAttrs) > 500:
    #             sa.WriteText('\ttoo many to list (i.e. more than 500)!!\n')
    #         else:
    #             for thisAttr in knownAttrs:
    #                 sa.WriteText('\t' + thisAttr + '\n')
    #     else:
    #         sa.WriteText('\n')

    def OnMarginClick(self, evt):
        # fold and unfold as needed
        if evt.GetMargin() == 2:
            if evt.GetShift() and evt.GetControl():
                self.FoldAll()
            else:
                lineClicked = self.LineFromPosition(evt.GetPosition())
                _flag = wx.stc.STC_FOLDLEVELHEADERFLAG
                if self.GetFoldLevel(lineClicked) & _flag:
                    if evt.GetShift():
                        self.SetFoldExpanded(lineClicked, True)
                        self.Expand(lineClicked, True, True, 1)
                    elif evt.GetControl():
                        if self.GetFoldExpanded(lineClicked):
                            self.SetFoldExpanded(lineClicked, False)
                            self.Expand(lineClicked, False, True, 0)
                        else:
                            self.SetFoldExpanded(lineClicked, True)
                            self.Expand(lineClicked, True, True, 100)
                    else:
                        self.ToggleFold(lineClicked)

    def FoldAll(self):
        lineCount = self.GetLineCount()
        expanding = True

        # find out if we are folding or unfolding
        for lineNum in range(lineCount):
            if self.GetFoldLevel(lineNum) & wx.stc.STC_FOLDLEVELHEADERFLAG:
                expanding = not self.GetFoldExpanded(lineNum)
                break

        lineNum = 0
        _flag = wx.stc.STC_FOLDLEVELHEADERFLAG
        _mask = wx.stc.STC_FOLDLEVELNUMBERMASK
        _base = wx.stc.STC_FOLDLEVELBASE
        while lineNum < lineCount:
            level = self.GetFoldLevel(lineNum)
            if level & _flag and level & _mask == _base:
                if expanding:
                    self.SetFoldExpanded(lineNum, True)
                    lineNum = self.Expand(lineNum, True)
                    lineNum -= 1
                else:
                    lastChild = self.GetLastChild(lineNum, -1)
                    self.SetFoldExpanded(lineNum, False)
                    if lastChild > lineNum:
                        self.HideLines(lineNum + 1, lastChild)
            lineNum += 1

    def Expand(self, line, doExpand, force=False, visLevels=0, level=-1):
        lastChild = self.GetLastChild(line, level)
        line += 1

        while line <= lastChild:
            if force:
                if visLevels > 0:
                    self.ShowLines(line, line)
                else:
                    self.HideLines(line, line)
            else:
                if doExpand:
                    self.ShowLines(line, line)
            if level == -1:
                level = self.GetFoldLevel(line)
            if level & wx.stc.STC_FOLDLEVELHEADERFLAG:
                if force:
                    if visLevels > 1:
                        self.SetFoldExpanded(line, True)
                    else:
                        self.SetFoldExpanded(line, False)
                    line = self.Expand(line, doExpand, force, visLevels - 1)
                else:
                    if doExpand and self.GetFoldExpanded(line):
                        line = self.Expand(line, True, force, visLevels - 1)
                    else:
                        line = self.Expand(line, False, force, visLevels - 1)
            else:
                line += 1
        return line

    def commentLines(self):
        # used for the comment/uncomment machinery from ActiveGrid
        newText = ""
        for lineNo in self._GetSelectedLineNumbers():
            lineText = self.GetLine(lineNo)
            oneSharp = bool(len(lineText) > 1 and lineText[0] == '#')
            # todo: is twoSharp ever True when oneSharp is not?
            twoSharp = bool(len(lineText) > 2 and lineText[:2] == '##')
            lastLine = bool(lineNo == self.GetLineCount() - 1
                            and self.GetLineLength(lineNo) == 0)
            if oneSharp or twoSharp or lastLine:
                newText = newText + lineText
            else:
                newText = newText + "#" + lineText
        self._ReplaceSelectedLines(newText)

    def uncommentLines(self):
        # used for the comment/uncomment machinery from ActiveGrid
        newText = ""
        for lineNo in self._GetSelectedLineNumbers():
            lineText = self.GetLine(lineNo)
            # todo: is the next line ever True? seems like should be == '##'
            if len(lineText) >= 2 and lineText[:2] == "#":
                lineText = lineText[2:]
            elif len(lineText) >= 1 and lineText[:1] == "#":
                lineText = lineText[1:]
            newText = newText + lineText
        self._ReplaceSelectedLines(newText)

    def increaseFontSize(self):
        self.SetZoom(self.GetZoom() + 1)

    def decreaseFontSize(self):
        # Minimum zoom set to - 6
        if self.GetZoom() == -6:
            self.SetZoom(self.GetZoom())
        else:
            self.SetZoom(self.GetZoom() - 1)

    # the Source Assistant and introspection functinos were broekn and removed frmo PsychoPy 1.90.0
    def analyseScript(self):
        # analyse the file
        buffer = io.StringIO()
        buffer.write(self.GetText())
        buffer.seek(0)
        try:
            ii, tt = psychoParser.getTokensAndImports(buffer)
            importStatements, tokenDict = ii, tt
            successfulParse = True
        except Exception:
            successfulParse = False
        buffer.close()

        #     # if we parsed the tokens then process them
        if successfulParse:
            # import the libs used by the script
            if self.coder.modulesLoaded:
                for thisLine in importStatements:
                    # check what file we're importing from
                    tryImport = True
                    words = thisLine.split()
                    # don't import from files in this folder (user files)
                    for word in words:
                        if os.path.isfile(word + '.py'):
                            tryImport = False
                    if tryImport:
                        try:  # it might not import
                            exec(thisLine)
                        except Exception:
                            pass
                    self.locals = locals()  # keep a track of our new locals
                self.autoCompleteDict = {}

            # go through imported symbols (using dir())
            # loop through to appropriate level of module tree getting all
            # possible symbols
            symbols = dir()
            # remove some tokens that are just from here
            symbols.remove('self')
            symbols.remove('buffer')
            symbols.remove('tokenDict')
            symbols.remove('successfulParse')
            for thisSymbol in symbols:
                # create an actual obj from the name
                thisObj = eval('%s' % thisSymbol)
                # (try to) get the attributes of the object
                try:
                    newAttrs = dir(thisObj)
                except Exception:
                    newAttrs = []

                # only dig deeper if we haven't exceeded the max level of
                # analysis
                if thisSymbol.find('.') < analysisLevel:
                    # we should carry on digging deeper
                    for thisAttr in newAttrs:
                        # by appending the symbol it will also get analysed!
                        symbols.append(thisSymbol + '.' + thisAttr)

                # but (try to) add data for all symbols including this level
                try:
                    self.autoCompleteDict[thisSymbol] = {
                        'is': thisObj, 'type': type(thisObj),
                        'attrs': newAttrs, 'help': thisObj.__doc__}
                except Exception:
                    pass  # not sure what happened - maybe no __doc__?

            # add keywords
            for thisName in keyword.kwlist[:]:
                self.autoCompleteDict[thisName] = {
                    'is': 'Keyword', 'type': 'Keyword',
                    'attrs': None, 'help': None}
            self.autoCompleteDict['self'] = {
                'is': 'self', 'type': 'self', 'attrs': None, 'help': None}

            # then add the tokens (i.e. instances) from this script
            for thisKey in tokenDict:
                # the default is to have no fields filled
                thisObj = thisIs = thisHelp = thisType = thisAttrs = None
                keyIsStr = tokenDict[thisKey]['is']
                try:
                    thisObj = eval('%s' % keyIsStr)
                    if type(thisObj) == types.FunctionType:
                        thisIs = 'returned from functon'
                    else:
                        thisIs = str(thisObj)
                        thisType = 'instance'
                        thisHelp = thisObj.__doc__
                        thisAttrs = dir(thisObj)
                except Exception:
                    pass
                self.autoCompleteDict[thisKey] = {
                    'is': thisIs, 'type': thisType,
                    'attrs': thisAttrs, 'help': thisHelp}

    def setLexer(self, lexer=None):
        """Lexer is a simple string (e.g. 'python', 'html')
        that will be converted to use the right STC_LEXER_XXXX value
        """
        try:
            lex = getattr(wx.stc, "STC_LEX_%s" % (lexer.upper()))
        except AttributeError:
            logging.warn("Unknown lexer %r. Using 'python' instead" % lexer)
            lex = wx.stc.STC_LEX_PYTHON
            lexer = 'python'
        # then actually set it
        self.SetLexer(lex)
        if lexer == 'python':
            self.SetKeyWords(0, " ".join(keyword.kwlist))
            self.SetIndentationGuides(self.coder.appData['showIndentGuides'])
            self.SetStyleBits(5)  # in case we had html before
            self.SetProperty("fold", "1")  # wllow folding
            self.SetProperty("tab.timmy.whinge.level", "1")
        elif lexer.lower() == 'html':
            self.SetStyleBits(7)  # apprently!
            self.SetProperty("fold", "1")  # wllow folding
            # 4 means 'tabs are bad'; 1 means 'flag inconsistency'
            self.SetProperty("tab.timmy.whinge.level", "1")
        else:
            self.SetIndentationGuides(0)
            self.SetProperty("tab.timmy.whinge.level", "0")

        self.Colourise(0, -1)

    def onModified(self, event):
        # update the UNSAVED flag and the save icons
        notebook = self.GetParent()
        mainFrame = notebook.GetParent()
        mainFrame.setFileModified(True)

    def DoFindNext(self, findData, findDlg=None):
        # this comes straight from wx.py.editwindow  (which is a subclass of
        # STC control)
        backward = not (findData.GetFlags() & wx.FR_DOWN)
        matchcase = (findData.GetFlags() & wx.FR_MATCHCASE) != 0
        end = self.GetLength()
        textstring = self.GetTextRange(0, end)
        findstring = findData.GetFindString()
        if not matchcase:
            textstring = textstring.lower()
            findstring = findstring.lower()
        if backward:
            start = self.GetSelection()[0]
            loc = textstring.rfind(findstring, 0, start)
        else:
            start = self.GetSelection()[1]
            loc = textstring.find(findstring, start)

        # if it wasn't found then restart at begining
        if loc == -1 and start != 0:
            if backward:
                start = end
                loc = textstring.rfind(findstring, 0, start)
            else:
                start = 0
                loc = textstring.find(findstring, start)

        # was it still not found?
        if loc == -1:
            dlg = dialogs.MessageDialog(self, message=_translate(
                'Unable to find "%s"') % findstring, type='Info')
            dlg.ShowModal()
            dlg.Destroy()
        else:
            # show and select the found text
            line = self.LineFromPosition(loc)
            # self.EnsureVisible(line)
            self.GotoLine(line)
            self.SetSelection(loc, loc + len(findstring))
        if findDlg:
            if loc == -1:
                wx.CallAfter(findDlg.SetFocus)
                return
            else:
                findDlg.Close()


class CoderFrame(wx.Frame):

    def __init__(self, parent, ID, title, files=(), app=None):
        self.app = app  # type: PsychoPyApp
        self.frameType = 'coder'
        # things the user doesn't set like winsize etc
        self.appData = self.app.prefs.appData['coder']
        self.prefs = self.app.prefs.coder  # things about coder that get set
        self.appPrefs = self.app.prefs.app
        self.paths = self.app.prefs.paths
        self.IDs = self.app.IDs
        self.currentDoc = None
        self.ignoreErrors = False
        self.fileStatusLastChecked = time.time()
        self.fileStatusCheckInterval = 5 * 60  # sec
        self.showingReloadDialog = False
        self.btnHandles = {}  # stores toolbar buttons so they can be altered

        # we didn't have the key or the win was minimized/invalid
        if self.appData['winH'] == 0 or self.appData['winW'] == 0:
            self.appData['winH'], self.appData['winW'] = wx.DefaultSize
            self.appData['winX'], self.appData['winY'] = wx.DefaultPosition
        if self.appData['winY'] < 20:
            self.appData['winY'] = 20
        # fix issue in Windows when frame was closed while iconized
        if self.appData['winX'] == -32000:
            self.appData['winX'], self.appData['winY'] = wx.DefaultPosition
            self.appData['winH'], self.appData['winW'] = wx.DefaultSize
        wx.Frame.__init__(self, parent, ID, title,
                          (self.appData['winX'], self.appData['winY']),
                          size=(self.appData['winW'], self.appData['winH']))

        # self.panel = wx.Panel(self)
        self.Hide()  # ugly to see it all initialise
        # create icon
        if sys.platform == 'darwin':
            pass  # doesn't work and not necessary - handled by app bundle
        else:
            iconFile = os.path.join(self.paths['resources'], 'psychopy.ico')
            if os.path.isfile(iconFile):
                self.SetIcon(wx.Icon(iconFile, wx.BITMAP_TYPE_ICO))
        # NB not the same as quit - just close the window
        self.Bind(wx.EVT_CLOSE, self.closeFrame)
        self.Bind(wx.EVT_IDLE, self.onIdle)

        if 'state' in self.appData and self.appData['state'] == 'maxim':
            self.Maximize()
        # initialise some attributes
        self.modulesLoaded = False  # goes true when loading thread completes
        self.findDlg = None
        self.findData = wx.FindReplaceData()
        self.findData.SetFlags(wx.FR_DOWN)
        self.importedScripts = {}
        self.scriptProcess = None
        self.scriptProcessID = None
        self.db = None  # debugger
        self._lastCaretPos = None

        # setup statusbar
        self.makeToolbar()  # must be before the paneManager for some reason
        self.makeMenus()
        self.CreateStatusBar()
        self.SetStatusText("")
        self.fileMenu = self.editMenu = self.viewMenu = None
        self.helpMenu = self.toolsMenu = None

        # setup universal shortcuts
        accelTable = self.app.makeAccelTable()
        self.SetAcceleratorTable(accelTable)

        # make the pane manager
        self.paneManager = aui.AuiManager()

        # create an editor pane
        self.paneManager.SetFlags(aui.AUI_MGR_RECTANGLE_HINT)
        self.paneManager.SetManagedWindow(self)
        # make the notebook
        _style = (aui.AUI_NB_TOP |
                  aui.AUI_NB_SCROLL_BUTTONS |
                  aui.AUI_NB_TAB_SPLIT |
                  aui.AUI_NB_TAB_MOVE |
                  aui.AUI_NB_CLOSE_ON_ACTIVE_TAB |
                  aui.AUI_NB_WINDOWLIST_BUTTON)
        self.notebook = aui.AuiNotebook(self, -1,
                                        size=wx.Size(600, 600),
                                        style=_style)
        self.paneManager.AddPane(self.notebook, aui.AuiPaneInfo().
                                 Name("Editor").
                                 Caption(_translate("Editor")).
                                 CenterPane().  # 'center panes' expand
                                 CloseButton(False).
                                 MaximizeButton(True))
        self.notebook.SetFocus()
        self.notebook.SetDropTarget(FileDropTarget(targetFrame=self))

        self.notebook.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.fileClose)
        self.notebook.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.pageChanged)
        # self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.pageChanged)
        self.SetDropTarget(FileDropTarget(targetFrame=self))
        self.Bind(wx.EVT_DROP_FILES, self.filesDropped)
        self.Bind(wx.EVT_FIND, self.OnFindNext)
        self.Bind(wx.EVT_FIND_NEXT, self.OnFindNext)
        self.Bind(wx.EVT_FIND_CLOSE, self.OnFindClose)
        self.Bind(wx.EVT_END_PROCESS, self.onProcessEnded)

        # take files from arguments and append the previously opened files
        if files not in [None, [], ()]:
            for filename in files:
                if not os.path.isfile(filename):
                    continue
                self.setCurrentDoc(filename, keepHidden=True)

        # create the shelf for shell and output views
        _style = (aui.AUI_NB_TOP | aui.AUI_NB_TAB_SPLIT |
                  aui.AUI_NB_SCROLL_BUTTONS | aui.AUI_NB_TAB_MOVE)
        self.shelf = aui.AuiNotebook(self, wx.ID_ANY, size=wx.Size(600, 600),
                                     style=_style)
        self.paneManager.AddPane(self.shelf,
                                 aui.AuiPaneInfo().
                                 Name("Shelf").
                                 Caption(_translate("Shelf")).
                                 RightDockable(True).LeftDockable(True).
                                 CloseButton(False).
                                 Bottom())

        # create output viewer
        self._origStdOut = sys.stdout  # keep track of previous output
        self._origStdErr = sys.stderr

        _style = wx.TE_MULTILINE | wx.TE_READONLY | wx.VSCROLL
        self.outputWindow = stdOutRich.StdOutRich(
            self, style=_style,
            font=self.prefs['outputFont'],
            fontSize=self.prefs['outputFontSize'])
        self.outputWindow.write(_translate('Welcome to PsychoPy3!') + '\n')
        self.outputWindow.write("v%s\n" % self.app.version)
        # Add context manager to output window
        self.outputWindow.Bind(wx.EVT_CONTEXT_MENU, self.outputContextMenu)
        self.shelf.AddPage(self.outputWindow, _translate('Output'))

        if self.app._appLoaded:
            self.setOutputWindow()

        if haveCode:
            useDefaultShell = True
            if self.prefs['preferredShell'].lower() == 'ipython':
                try:
                    import IPython.gui.wx.ipython_view
                    # IPython shell is nice, but crashes if you draw stimuli
                    self.shell = IPython.gui.wx.ipython_view.IPShellWidget(
                        parent=self, background_color='WHITE', )
                    useDefaultShell = False
                except Exception:
                    msg = _translate('IPython failed as shell, using pyshell'
                                     ' (IPython v0.12 can fail on wx)')
                    logging.warn(msg)
            if useDefaultShell:
                from wx import py
                msg = _translate('PyShell in PsychoPy - type some commands!')
                self.shell = py.shell.Shell(
                    self.shelf, -1, introText=msg + '\n\n')
            self.shelf.AddPage(self.shell, _translate('Shell'))

        # add help window
        _style = wx.TE_MULTILINE | wx.TE_READONLY
        self.sourceAsstWindow = wx.richtext.RichTextCtrl(
            self, -1, size=wx.Size(300, 300), style=_style)
        self.paneManager.AddPane(self.sourceAsstWindow,
                                 aui.AuiPaneInfo().
                                 BestSize((600, 600)).
                                 Name("SourceAsst").
                                 Caption(_translate("Source Assistant")).
                                 RightDockable(True).
                                 LeftDockable(True).
                                 CloseButton(False).
                                 Right())
        # will we show the pane straight away?
        if self.prefs['showSourceAsst']:
            self.paneManager.GetPane('SourceAsst').Show()
        else:
            self.paneManager.GetPane('SourceAsst').Hide()
        self.unitTestFrame = None

        # self.SetSizer(self.mainSizer)  # not necessary for aui type controls
        if (self.appData['auiPerspective'] and
                'Shelf' in self.appData['auiPerspective']):
            self.paneManager.LoadPerspective(self.appData['auiPerspective'])
            self.paneManager.GetPane('Shelf').Caption(_translate("Shelf"))
            self.paneManager.GetPane('SourceAsst').Caption(
                _translate("Source Assistant"))
            self.paneManager.GetPane('Editor').Caption(_translate("Editor"))
        else:
            self.SetMinSize(wx.Size(400, 600))  # min size for whole window
            self.Fit()
            self.paneManager.Update()
        self.SendSizeEvent()
        self.app.trackFrame(self)

    def outputContextMenu(self, event):
        """Custom context menu for output window.

        Provides menu items to clear all, select all and copy selected text."""
        if not hasattr(self, "outputMenuID1"):
            self.outputMenuID1 = wx.NewId()
            self.outputMenuID2 = wx.NewId()
            self.outputMenuID3 = wx.NewId()

            self.Bind(wx.EVT_MENU, self.outputClear, id=self.outputMenuID1)
            self.Bind(wx.EVT_MENU, self.outputSelectAll, id=self.outputMenuID2)
            self.Bind(wx.EVT_MENU, self.outputCopy, id=self.outputMenuID3)

        menu = wx.Menu()
        itemClear = wx.MenuItem(menu, self.outputMenuID1, "Clear All")
        itemSelect = wx.MenuItem(menu, self.outputMenuID2, "Select All")
        itemCopy = wx.MenuItem(menu, self.outputMenuID3, "Copy")

        menu.Append(itemClear)
        menu.AppendSeparator()
        menu.Append(itemSelect)
        menu.Append(itemCopy)
        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()

    def outputClear(self, event):
        """Clears the output window in Coder"""
        self.outputWindow.Clear()

    def outputSelectAll(self, event):
        """Selects all text from the output window in Coder"""
        self.outputWindow.SelectAll()

    def outputCopy(self, event):
        """Copies all text from the output window in Coder"""
        self.outputWindow.Copy()

    def makeMenus(self):
        # ---Menus---#000000#FFFFFF-------------------------------------------
        menuBar = wx.MenuBar()
        # ---_file---#000000#FFFFFF-------------------------------------------
        self.fileMenu = wx.Menu()
        menuBar.Append(self.fileMenu, _translate('&File'))

        # create a file history submenu
        self.fileHistory = wx.FileHistory(maxFiles=10)
        self.recentFilesMenu = wx.Menu()
        self.fileHistory.UseMenu(self.recentFilesMenu)
        for filename in self.appData['fileHistory']:
            self.fileHistory.AddFileToHistory(filename)
        self.Bind(wx.EVT_MENU_RANGE, self.OnFileHistory,
                  id=wx.ID_FILE1, id2=wx.ID_FILE9)

        # add items to file menu
        keyCodes = self.app.keys
        menu = self.fileMenu
        menu.Append(wx.ID_NEW, _translate("&New\t%s") % keyCodes['new'])
        menu.Append(wx.ID_OPEN, _translate("&Open...\t%s") % keyCodes['open'])
        menu.AppendSubMenu(self.recentFilesMenu, _translate("Open &Recent"))
        menu.Append(wx.ID_SAVE,
                    _translate("&Save\t%s") % keyCodes['save'],
                    _translate("Save current file"))
        menu.Append(wx.ID_SAVEAS,
                    _translate("Save &as...\t%s") % keyCodes['saveAs'],
                    _translate("Save current python file as..."))
        menu.Append(wx.ID_CLOSE,
                    _translate("&Close file\t%s") % keyCodes['close'],
                    _translate("Close current python file"))
        self.Bind(wx.EVT_MENU, self.fileNew, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.fileOpen, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.fileSave, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.fileSaveAs, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.fileClose, id=wx.ID_CLOSE)
        item = menu.Append(wx.ID_ANY,
                           _translate("Print\t%s") % keyCodes['print'])
        self.Bind(wx.EVT_MENU, self.filePrint, id=item.GetId())
        msg = _translate("&Preferences\t%s")
        item = menu.Append(wx.ID_PREFERENCES,
                           msg % keyCodes['preferences'])
        self.Bind(wx.EVT_MENU, self.app.showPrefs, id=item.GetId())
        # -------------quit
        menu.AppendSeparator()
        menu.Append(wx.ID_EXIT,
                    _translate("&Quit\t%s") % keyCodes['quit'],
                    _translate("Terminate the program"))
        self.Bind(wx.EVT_MENU, self.quit, id=wx.ID_EXIT)

        # ---_edit---#000000#FFFFFF-------------------------------------------
        self.editMenu = wx.Menu()
        menu = self.editMenu
        menuBar.Append(self.editMenu, _translate('&Edit'))
        menu.Append(wx.ID_CUT, _translate("Cu&t\t%s") % keyCodes['cut'])
        self.Bind(wx.EVT_MENU, self.cut, id=wx.ID_CUT)
        menu.Append(wx.ID_COPY, _translate("&Copy\t%s") % keyCodes['copy'])
        self.Bind(wx.EVT_MENU, self.copy, id=wx.ID_COPY)
        menu.Append(wx.ID_PASTE, _translate("&Paste\t%s") % keyCodes['paste'])
        self.Bind(wx.EVT_MENU, self.paste, id=wx.ID_PASTE)
        hnt = _translate("Duplicate the current line (or current selection)")
        menu.Append(wx.ID_DUPLICATE,
                    _translate("&Duplicate\t%s") % keyCodes['duplicate'],
                    hnt)
        self.Bind(wx.EVT_MENU, self.duplicateLine, id=wx.ID_DUPLICATE)

        menu.AppendSeparator()
        item = menu.Append(wx.ID_ANY,
                           _translate("&Find\t%s") % keyCodes['find'])
        self.Bind(wx.EVT_MENU, self.OnFindOpen, id=item.GetId())
        item = menu.Append(wx.ID_ANY,
                           _translate("Find &Next\t%s") % keyCodes['findAgain'])
        self.Bind(wx.EVT_MENU, self.OnFindNext, id=item.GetId())

        menu.AppendSeparator()
        item = menu.Append(wx.ID_ANY,
                           _translate("Comment\t%s") % keyCodes['comment'],
                           _translate("Comment selected lines"),
                           wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.commentSelected, id=item.GetId())
        item = menu.Append(wx.ID_ANY,
                           _translate("Uncomment\t%s") % keyCodes['uncomment'],
                           _translate("Un-comment selected lines"),
                           wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.uncommentSelected, id=item.GetId())

        item = menu.Append(wx.ID_ANY,
                           _translate("Toggle comment\t%s") % keyCodes['toggle comment'],
                           _translate("Toggle commenting of selected lines"),
                           wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.toggleComments, id=item.GetId())

        item = menu.Append(wx.ID_ANY,
                           _translate("Toggle fold\t%s") % keyCodes['fold'],
                           _translate("Toggle folding of top level"),
                           wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.foldAll, id=item.GetId())

        menu.AppendSeparator()
        item = menu.Append(wx.ID_ANY,
                           _translate("Indent selection\t%s") % keyCodes['indent'],
                           _translate("Increase indentation of current line"),
                           wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.indent, id=item.GetId())
        item = menu.Append(wx.ID_ANY,
                           _translate("Dedent selection\t%s") % keyCodes['dedent'],
                           _translate("Decrease indentation of current line"),
                           wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.dedent, id=item.GetId())
        hnt = _translate("Try to indent to the correct position w.r.t. "
                         "last line")
        item = menu.Append(wx.ID_ANY,
                           _translate("SmartIndent\t%s") % keyCodes['smartIndent'],
                           hnt,
                           wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.smartIndent, id=item.GetId())

        menu.AppendSeparator()
        menu.Append(wx.ID_UNDO,
                    _translate("Undo\t%s") % self.app.keys['undo'],
                    _translate("Undo last action"),
                    wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.undo, id=wx.ID_UNDO)
        menu.Append(wx.ID_REDO,
                    _translate("Redo\t%s") % self.app.keys['redo'],
                    _translate("Redo last action"),
                    wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.redo, id=wx.ID_REDO)

        menu.AppendSeparator()
        item = menu.Append(wx.ID_ANY,
                           _translate("Enlarge font\t%s") % self.app.keys['enlargeFont'],
                           _translate("Increase font size"),
                           wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.bigFont, id=item.GetId())
        item = menu.Append(wx.ID_ANY,
                           _translate("Shrink font\t%s") % self.app.keys['shrinkFont'],
                           _translate("Decrease font size"),
                           wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.smallFont, id=item.GetId())
        # menu.Append(ID_UNFOLDALL, "Unfold All\tF3",
        #   "Unfold all lines", wx.ITEM_NORMAL)
        # self.Bind(wx.EVT_MENU,  self.unfoldAll, id=ID_UNFOLDALL)
        # ---_tools---#000000#FFFFFF------------------------------------------
        self.toolsMenu = wx.Menu()
        menu = self.toolsMenu
        menuBar.Append(self.toolsMenu, _translate('&Tools'))
        item = menu.Append(wx.ID_ANY,
                           _translate("Monitor Center"),
                           _translate("To set information about your monitor"))
        self.Bind(wx.EVT_MENU, self.app.openMonitorCenter, id=item.GetId())
        # self.analyseAutoChk = self.toolsMenu.AppendCheckItem(self.IDs.analyzeAuto,
        #   "Analyse on file save/open",
        #   "Automatically analyse source (for autocomplete etc...).
        #   Can slow down the editor on a slow machine or with large files")
        # self.Bind(wx.EVT_MENU,  self.setAnalyseAuto, id=self.IDs.analyzeAuto)
        # self.analyseAutoChk.Check(self.prefs['analyseAuto'])
        # self.toolsMenu.Append(self.IDs.analyzeNow,
        #   "Analyse now\t%s" %self.app.keys['analyseCode'],
        #   "Force a reananalysis of the code now")
        # self.Bind(wx.EVT_MENU,  self.analyseCodeNow, id=self.IDs.analyzeNow)

        self.IDs.cdrRun = menu.Append(wx.ID_ANY,
                                      _translate("Run\t%s") % keyCodes['runScript'],
                                      _translate("Run the current script")).GetId()
        self.Bind(wx.EVT_MENU, self.runFile, id=self.IDs.cdrRun)
        self.IDs.cdrStop = menu.Append(wx.ID_ANY,
                                       _translate("Stop\t%s") % keyCodes['stopScript'],
                                       _translate("Stop the current script")).GetId()
        self.Bind(wx.EVT_MENU, self.stopFile, id=self.IDs.cdrStop)

        menu.AppendSeparator()
        item = menu.Append(wx.ID_ANY,
                           _translate("PsychoPy updates..."),
                           _translate("Update PsychoPy to the latest, or a specific, version"))
        self.Bind(wx.EVT_MENU, self.app.openUpdater, id=item.GetId())
        item = menu.Append(wx.ID_ANY,
                           _translate("Benchmark wizard"),
                           _translate("Check software & hardware, generate report"))
        self.Bind(wx.EVT_MENU, self.app.benchmarkWizard, id=item.GetId())
        item = menu.Append(wx.ID_ANY,
                           _translate("csv from psydat"),
                           _translate("Create a .csv file from an existing .psydat file"))
        self.Bind(wx.EVT_MENU, self.app.csvFromPsydat, id=item.GetId())

        if self.appPrefs['debugMode']:
            item = menu.Append(wx.ID_ANY,
                               _translate("Unit &testing...\tCtrl-T"),
                               _translate("Show dialog to run unit tests"))
        self.Bind(wx.EVT_MENU, self.onUnitTests, id=item.GetId())

        # ---_view---#000000#FFFFFF-------------------------------------------
        self.viewMenu = wx.Menu()
        menu = self.viewMenu
        menuBar.Append(self.viewMenu, _translate('&View'))

        # indent guides
        key = keyCodes['toggleIndentGuides']
        hint = _translate("Shows guides in the editor for your "
                          "indentation level")
        self.indentGuideChk = menu.AppendCheckItem(wx.ID_ANY,
                                                   _translate("&Indentation guides\t%s") % key,
                                                   hint)
        self.indentGuideChk.Check(self.appData['showIndentGuides'])
        self.Bind(wx.EVT_MENU, self.setShowIndentGuides, self.indentGuideChk)
        # whitespace
        key = keyCodes['toggleWhitespace']
        hint = _translate("Show whitespace characters in the code")
        self.showWhitespaceChk = menu.AppendCheckItem(wx.ID_ANY,
                                                      _translate("&Whitespace\t%s") % key,
                                                      hint)
        self.showWhitespaceChk.Check(self.appData['showWhitespace'])
        self.Bind(wx.EVT_MENU, self.setShowWhitespace, self.showWhitespaceChk)
        # EOL markers
        key = keyCodes['toggleEOLs']
        hint = _translate("Show End Of Line markers in the code")
        self.showEOLsChk = menu.AppendCheckItem(
            wx.ID_ANY,
            _translate("Show &EOLs\t%s") % key,
            hint)
        self.showEOLsChk.Check(self.appData['showEOLs'])
        self.Bind(wx.EVT_MENU, self.setShowEOLs, id=self.showEOLsChk.GetId())

        menu.AppendSeparator()
        # output window
        key = keyCodes['toggleOutputPanel']
        hint = _translate("Shows the output and shell panes (and starts "
                          "capturing stdout)")
        self.outputChk = menu.AppendCheckItem(wx.ID_ANY,
                                              _translate("Show &Output/Shell\t%s") % key,
                                              hint)
        self.outputChk.Check(self.prefs['showOutput'])
        self.Bind(wx.EVT_MENU, self.setOutputWindow, id=self.outputChk.GetId())
        # source assistant
        hint = _translate("Provides help functions and attributes of classes"
                          " in your script")
        self.sourceAsstChk = menu.AppendCheckItem(wx.ID_ANY,
                                                  _translate("&Source Assistant"),
                                                  hint)
        self.sourceAsstChk.Check(self.prefs['showSourceAsst'])
        self.Bind(wx.EVT_MENU, self.setSourceAsst,
                  id=self.sourceAsstChk.GetId())

        menu.AppendSeparator()

        key = self.app.keys['switchToBuilder']
        item = menu.Append(wx.ID_ANY,
                           _translate("Go to &Builder view\t%s") % key,
                           _translate("Go to the Builder view"))
        self.Bind(wx.EVT_MENU, self.app.showBuilder, id=item.GetId())
        # self.viewMenu.Append(self.IDs.openShell,
        #   "Go to &IPython Shell\t%s" %self.app.keys['switchToShell'],
        #   "Go to a shell window for interactive commands")
        # self.Bind(wx.EVT_MENU,  self.app.showShell, id=self.IDs.openShell)
        # self.viewMenu.Append(self.IDs.openIPythonNotebook,
        #   "Go to &IPython notebook",
        #   "Open an IPython notebook (unconnected in a browser)")
        # self.Bind(wx.EVT_MENU, self.app.openIPythonNotebook,
        #    id=self.IDs.openIPythonNotebook)

        self.demosMenu = wx.Menu()
        self.demos = {}
        menuBar.Append(self.demosMenu, _translate('&Demos'))
        # for demos we need a dict of {event ID: filename, ...}
        # add folders
        folders = glob.glob(os.path.join(self.paths['demos'], 'coder', '*'))
        for folder in folders:
            # if it isn't a folder then skip it
            if (not os.path.isdir(folder)):
                continue
            # otherwise create a submenu
            folderDisplayName = os.path.split(folder)[-1]
            if folderDisplayName.startswith('_'):
                continue  # don't include private folders
            if folderDisplayName in _localized:
                folderDisplayName = _localized[folderDisplayName]
            submenu = wx.Menu()
            self.demosMenu.AppendSubMenu(submenu, folderDisplayName)

            # find the files in the folder (search two levels deep)
            demoList = glob.glob(os.path.join(folder, '*.py'))
            demoList += glob.glob(os.path.join(folder, '*', '*.py'))
            demoList += glob.glob(os.path.join(folder, '*', '*', '*.py'))

            demoList.sort()

            for thisFile in demoList:
                shortname = thisFile.split(os.path.sep)[-1]
                if shortname == "run.py":
                    # file is just "run" so get shortname from directory name
                    # instead
                    shortname = thisFile.split(os.path.sep)[-2]
                elif shortname.startswith('_'):
                    continue  # remove any 'private' files
                item = submenu.Append(wx.ID_ANY, shortname)
                thisID = item.GetId()
                self.demos[thisID] = thisFile
                self.Bind(wx.EVT_MENU, self.loadDemo, id=thisID)
        # also add simple demos to root
        self.demosMenu.AppendSeparator()
        demos = glob.glob(os.path.join(self.paths['demos'], 'coder', '*.py'))
        for thisFile in demos:
            shortname = thisFile.split(os.path.sep)[-1]
            if shortname.startswith('_'):
                continue  # remove any 'private' files
            item = self.demosMenu.Append(wx.ID_ANY, shortname)
            thisID = item.GetId()
            self.demos[thisID] = thisFile
            self.Bind(wx.EVT_MENU, self.loadDemo, id=thisID)

        # ---_projects---#000000#FFFFFF---------------------------------------
        self.pavloviaMenu = psychopy.app.pavlovia_ui.menu.PavloviaMenu(parent=self)
        menuBar.Append(self.pavloviaMenu, _translate("Pavlovia.org"))

        # ---_help---#000000#FFFFFF-------------------------------------------
        self.helpMenu = wx.Menu()
        menuBar.Append(self.helpMenu, _translate('&Help'))
        item = self.helpMenu.Append(wx.ID_ANY,
                                    _translate("&PsychoPy Homepage"),
                                    _translate("Go to the PsychoPy homepage"))
        self.Bind(wx.EVT_MENU, self.app.followLink, id=item.GetId())
        self.app.urls[item.GetId()] = self.app.urls['psychopyHome']
        item = self.helpMenu.Append(wx.ID_ANY,
                                    _translate("&PsychoPy Coder Tutorial"),
                                    _translate("Go to the online PsychoPy tutorial"))
        self.Bind(wx.EVT_MENU, self.app.followLink, id=item.GetId())
        self.app.urls[item.GetId()] = self.app.urls['coderTutorial']
        item = self.helpMenu.Append(wx.ID_ANY,
                                    _translate("&PsychoPy API (reference)"),
                                    _translate("Go to the online PsychoPy reference manual"))
        self.Bind(wx.EVT_MENU, self.app.followLink, id=item.GetId())
        self.app.urls[item.GetId()] = self.app.urls['psychopyReference']
        self.helpMenu.AppendSeparator()
        # on mac this will move to the application menu
        self.helpMenu.Append(wx.ID_ABOUT,
                             _translate("&About..."),
                             _translate("About PsychoPy"))
        self.Bind(wx.EVT_MENU, self.app.showAbout, id=wx.ID_ABOUT)

        item = self.helpMenu.Append(wx.ID_ANY,
                                    _translate("&News..."),
                                    _translate("News"))
        self.Bind(wx.EVT_MENU, self.app.showNews, id=item.GetId())

        self.SetMenuBar(menuBar)

    def makeToolbar(self):
        # ---toolbar---#000000#FFFFFF-----------------------------------------
        _style = wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT
        self.toolbar = self.CreateToolBar(_style)

        if sys.platform == 'win32' or sys.platform.startswith('linux'):
            if self.appPrefs['largeIcons']:
                toolbarSize = 32
            else:
                toolbarSize = 16
        else:
            # mac: 16 either doesn't work, or looks really bad with wx3
            toolbarSize = 32

        self.toolbar.SetToolBitmapSize((toolbarSize, toolbarSize))
        rc = self.paths['resources']
        join = os.path.join
        PNG = wx.BITMAP_TYPE_PNG
        size = toolbarSize
        newBmp = wx.Bitmap(join(rc, 'filenew%i.png' % size), PNG)
        openBmp = wx.Bitmap(join(rc, 'fileopen%i.png' % size), PNG)
        saveBmp = wx.Bitmap(join(rc, 'filesave%i.png' % size), PNG)
        saveAsBmp = wx.Bitmap(join(rc, 'filesaveas%i.png' % size), PNG)
        undoBmp = wx.Bitmap(join(rc, 'undo%i.png' % size), PNG)
        redoBmp = wx.Bitmap(join(rc, 'redo%i.png' % size), PNG)
        stopBmp = wx.Bitmap(join(rc, 'stop%i.png' % size), PNG)
        runBmp = wx.Bitmap(join(rc, 'run%i.png' % size), PNG)
        preferencesBmp = wx.Bitmap(join(rc, 'preferences%i.png' % size), PNG)
        monitorsBmp = wx.Bitmap(join(rc, 'monitors%i.png' % size), PNG)
        colorpickerBmp = wx.Bitmap(join(rc, 'color%i.png' % size), PNG)

        # show key-bindings in tool-tips in an OS-dependent way
        if sys.platform == 'darwin':
            ctrlKey = 'Cmd+'
        else:
            ctrlKey = 'Ctrl+'
        tb = self.toolbar

        key = _translate("New [%s]") % self.app.keys['new']
        if 'phoenix' in wx.PlatformInfo:
            item = tb.AddTool(wx.ID_ANY,
                              key.replace('Ctrl+', ctrlKey),
                              newBmp,
                              _translate("Create new python file"))
        else:
            item = tb.AddSimpleTool(wx.ID_ANY,
                                    newBmp,
                                    key.replace('Ctrl+', ctrlKey),
                                    _translate("Create new python file"))
        tb.Bind(wx.EVT_TOOL, self.fileNew, id=item.GetId())

        key = _translate("Open [%s]") % self.app.keys['open']
        if 'phoenix' in wx.PlatformInfo:
            item = tb.AddTool(wx.ID_ANY,
                              key.replace('Ctrl+', ctrlKey),
                              openBmp,
                              _translate("Open an existing file"))
        else:
            item = tb.AddSimpleTool(wx.ID_ANY,
                                    openBmp,
                                    key.replace('Ctrl+', ctrlKey),
                                    _translate("Open an existing file"))
        tb.Bind(wx.EVT_TOOL, self.fileOpen, id=item.GetId())

        key = _translate("Save [%s]") % self.app.keys['save']
        if 'phoenix' in wx.PlatformInfo:
            self.IDs.cdrBtnSave = tb.AddTool(
                wx.ID_ANY,
                key.replace('Ctrl+', ctrlKey),
                saveBmp,
                _translate("Save current file")).GetId()
        else:
            self.IDs.cdrBtnSave = tb.AddSimpleTool(
                wx.ID_ANY,
                saveBmp,
                key.replace('Ctrl+', ctrlKey),
                _translate("Save current file")).GetId()
        tb.EnableTool(self.IDs.cdrBtnSave, False)
        tb.Bind(wx.EVT_TOOL, self.fileSave, id=self.IDs.cdrBtnSave)

        key = _translate("Save As... [%s]") % self.app.keys['saveAs']
        if 'phoenix' in wx.PlatformInfo:
            item = tb.AddTool(
                wx.ID_ANY,
                key.replace('Ctrl+', ctrlKey),
                saveAsBmp,
                _translate("Save current python file as..."))
        else:
            item = tb.AddSimpleTool(
                wx.ID_ANY,
                saveAsBmp,
                key.replace('Ctrl+', ctrlKey),
                _translate("Save current python file as..."))
        tb.Bind(wx.EVT_TOOL, self.fileSaveAs, id=item.GetId())

        key = _translate("Undo [%s]") % self.app.keys['undo']
        if 'phoenix' in wx.PlatformInfo:
            self.IDs.cdrBtUndo = tb.AddTool(
                wx.ID_ANY,
                key.replace('Ctrl+', ctrlKey),
                undoBmp,
                _translate("Undo last action")).GetId()
        else:
            self.IDs.cdrBtUndo = tb.AddSimpleTool(
                wx.ID_ANY,
                undoBmp,
                key.replace('Ctrl+', ctrlKey),
                _translate("Undo last action")).GetId()
        tb.Bind(wx.EVT_TOOL, self.undo, id=self.IDs.cdrBtUndo)

        key = _translate("Redo [%s]") % self.app.keys['redo']
        if 'phoenix' in wx.PlatformInfo:
            self.IDs.cdrBtRedo = tb.AddTool(
                wx.ID_ANY,
                key.replace('Ctrl+', ctrlKey),
                redoBmp,
                _translate("Redo last action")).GetId()
        else:
            self.IDs.cdrBtRedo = tb.AddSimpleTool(
                wx.ID_ANY,
                redoBmp,
                key.replace('Ctrl+', ctrlKey),
                _translate("Redo last action")).GetId()
        tb.Bind(wx.EVT_TOOL, self.redo, id=self.IDs.cdrBtRedo)

        tb.AddSeparator()

        if 'phoenix' in wx.PlatformInfo:
            item = tb.AddTool(
                wx.ID_ANY,
                _translate("Monitor Center"),
                monitorsBmp,
                _translate("Monitor settings and calibration"))
        else:
            item = tb.AddSimpleTool(
                wx.ID_ANY,
                monitorsBmp,
                _translate("Monitor Center"),
                _translate("Monitor settings and calibration"))
        tb.Bind(wx.EVT_TOOL, self.app.openMonitorCenter, id=item.GetId())

        if 'phoenix' in wx.PlatformInfo:
            item = tb.AddTool(
                wx.ID_ANY,
                _translate("Color Picker -> clipboard"),
                colorpickerBmp,
                _translate("Color Picker -> clipboard"))
        else:
            item = tb.AddSimpleTool(
                wx.ID_ANY,
                colorpickerBmp,
                _translate("Color Picker -> clipboard"),
                _translate("Color Picker -> clipboard"))
        tb.Bind(wx.EVT_TOOL, self.app.colorPicker, id=item.GetId())

        self.toolbar.AddSeparator()

        key = _translate("Run [%s]") % self.app.keys['runScript']
        if 'phoenix' in wx.PlatformInfo:
            self.IDs.cdrBtnRun = self.toolbar.AddTool(
                wx.ID_ANY,
                key.replace('Ctrl+', ctrlKey),
                runBmp,
                _translate("Run current script")).GetId()
        else:
            self.IDs.cdrBtnRun = self.toolbar.AddSimpleTool(
                wx.ID_ANY,
                runBmp,
                key.replace('Ctrl+', ctrlKey),
                _translate("Run current script")).GetId()
        self.toolbar.Bind(wx.EVT_TOOL, self.runFile, id=self.IDs.cdrBtnRun)

        key = _translate("Stop [%s]") % self.app.keys['stopScript']
        if 'phoenix' in wx.PlatformInfo:
            self.IDs.cdrBtnStop = self.toolbar.AddTool(
                wx.ID_ANY,
                key.replace('Ctrl+', ctrlKey),
                stopBmp,
                _translate("Stop current script")).GetId()
        else:
            self.IDs.cdrBtnStop = self.toolbar.AddSimpleTool(
                wx.ID_ANY,
                stopBmp,
                key.replace('Ctrl+', ctrlKey),
                _translate("Stop current script")).GetId()
        tb.Bind(wx.EVT_TOOL, self.stopFile, id=self.IDs.cdrBtnStop)
        tb.EnableTool(self.IDs.cdrBtnStop, False)

        self.toolbar.AddSeparator()
        pavButtons = pavlovia_ui.toolbar.PavloviaButtons(self, toolbar=tb, tbSize=size)
        pavButtons.addPavloviaTools(
                buttons=['pavloviaSync', 'pavloviaSearch', 'pavloviaUser'])
        self.btnHandles.update(pavButtons.btnHandles)

        tb.Realize()

    def onIdle(self, event):
        # check the script outputs to see if anything has been written to
        # stdout
        if self.scriptProcess is not None:
            if self.scriptProcess.IsInputAvailable():
                stream = self.scriptProcess.GetInputStream()
                text = stream.read()
                self.outputWindow.write(text)
            if self.scriptProcess.IsErrorAvailable():
                stream = self.scriptProcess.GetErrorStream()
                text = stream.read()
                self.outputWindow.write(text)
        # check if we're in the same place as before
        if hasattr(self.currentDoc, 'GetCurrentPos'):
            pos = self.currentDoc.GetCurrentPos()
            if self._lastCaretPos != pos:
                self.currentDoc.OnUpdateUI(evt=None)
                self._lastCaretPos = pos
        last = self.fileStatusLastChecked
        interval = self.fileStatusCheckInterval
        if time.time() - last > interval and not self.showingReloadDialog:
            if not self.expectedModTime(self.currentDoc):
                self.showingReloadDialog = True
                filename = os.path.basename(self.currentDoc.filename)
                msg = _translate("'%s' was modified outside of PsychoPy:\n\n"
                                 "Reload (without saving)?") % filename
                dlg = dialogs.MessageDialog(self, message=msg, type='Warning')
                if dlg.ShowModal() == wx.ID_YES:
                    self.SetStatusText(_translate('Reloading file'))
                    self.fileReload(event,
                                    filename=self.currentDoc.filename,
                                    checkSave=False)
                self.showingReloadDialog = False
                self.SetStatusText('')
                try:
                    dlg.destroy()
                except Exception:
                    pass
            self.fileStatusLastChecked = time.time()

    def pageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        self.currentDoc = self.notebook.GetPage(new)
        self.setFileModified(self.currentDoc.UNSAVED)
        self.SetLabel('%s - PsychoPy Coder' % self.currentDoc.filename)
        # todo: reduce redundancy w.r.t OnIdle()
        if not self.expectedModTime(self.currentDoc):
            filename = os.path.basename(self.currentDoc.filename)
            msg = _translate("'%s' was modified outside of PsychoPy:\n\n"
                             "Reload (without saving)?") % filename
            dlg = dialogs.MessageDialog(self, message=msg, type='Warning')
            if dlg.ShowModal() == wx.ID_YES:
                self.SetStatusText(_translate('Reloading file'))
                self.fileReload(event,
                                filename=self.currentDoc.filename,
                                checkSave=False)
                self.setFileModified(False)
            self.SetStatusText('')
            try:
                dlg.destroy()
            except Exception:
                pass

    def filesDropped(self, event):
        fileList = event.GetFiles()
        for filename in fileList:
            if os.path.isfile(filename):
                if filename.lower().endswith('.psyexp'):
                    self.app.newBuilderFrame(filename)
                else:
                    self.setCurrentDoc(filename)

    def OnFindOpen(self, event):
        # open the find dialog if not already open
        if self.findDlg is not None:
            return
        win = wx.Window.FindFocus()
        self.findDlg = wx.FindReplaceDialog(win, self.findData, "Find",
                                            wx.FR_NOWHOLEWORD)
        self.findDlg.Show()

    def OnFindNext(self, event):
        # find the next occurence of text according to last find dialogue data
        if not self.findData.GetFindString():
            self.OnFindOpen(event)
            return
        self.currentDoc.DoFindNext(self.findData, self.findDlg)
        if self.findDlg is not None:
            self.OnFindClose(None)

    def OnFindClose(self, event):
        self.findDlg.Destroy()
        self.findDlg = None

    def OnFileHistory(self, evt=None):
        # get the file based on the menu ID
        fileNum = evt.GetId() - wx.ID_FILE1
        path = self.fileHistory.GetHistoryFile(fileNum)
        self.setCurrentDoc(path)  # load the file
        # add it back to the history so it will be moved up the list
        self.fileHistory.AddFileToHistory(path)

    def gotoLine(self, filename=None, line=0):
        # goto a specific line in a specific file and select all text in it
        self.setCurrentDoc(filename)
        self.currentDoc.EnsureVisible(line)
        self.currentDoc.GotoLine(line)
        endPos = self.currentDoc.GetCurrentPos()

        self.currentDoc.GotoLine(line - 1)
        stPos = self.currentDoc.GetCurrentPos()

        self.currentDoc.SetSelection(stPos, endPos)

    def getOpenFilenames(self):
        """Return the full filename of each open tab"""
        names = []
        for ii in range(self.notebook.GetPageCount()):
            names.append(self.notebook.GetPage(ii).filename)
        return names

    def quit(self, event):
        self.app.quit()

    def checkSave(self):
        """Loop through all open files checking whether they need save
        """
        for ii in range(self.notebook.GetPageCount()):
            doc = self.notebook.GetPage(ii)
            filename = doc.filename
            if doc.UNSAVED:
                self.notebook.SetSelection(ii)  # fetch that page and show it
                # make sure frame is at front
                self.Show(True)
                self.Raise()
                self.app.SetTopWindow(self)
                # then bring up dialog
                msg = _translate('Save changes to %s before quitting?')
                dlg = dialogs.MessageDialog(self, message=msg % filename,
                                            type='Warning')
                resp = dlg.ShowModal()
                sys.stdout.flush()
                dlg.Destroy()
                if resp == wx.ID_CANCEL:
                    return 0  # return, don't quit
                elif resp == wx.ID_YES:
                    self.fileSave()  # save then quit
                elif resp == wx.ID_NO:
                    pass  # don't save just quit
        return 1

    def closeFrame(self, event=None, checkSave=True):
        """Close open windows, update prefs.appData (but don't save)
        and either close the frame or hide it
        """
        if len(self.app.getAllFrames(frameType="builder")) == 0 and sys.platform != 'darwin':
            if not self.app.quitting:
                # send the event so it can be vetoed if neded
                self.app.quit(event)
                return  # app.quit() will have closed the frame already

        # check all files before initiating close of any
        if checkSave and self.checkSave() == 0:
            return 0  # this signals user cancelled

        wasShown = self.IsShown()
        self.Hide()  # ugly to see it close all the files independently

        sys.stdout = self._origStdOut  # discovered during __init__
        sys.stderr = self._origStdErr

        # store current appData
        self.appData['prevFiles'] = []
        currFiles = self.getOpenFilenames()
        for thisFileName in currFiles:
            self.appData['prevFiles'].append(thisFileName)
        # get size and window layout info
        if self.IsIconized():
            self.Iconize(False)  # will return to normal mode to get size info
            self.appData['state'] = 'normal'
        elif self.IsMaximized():
            # will briefly return to normal mode to get size info
            self.Maximize(False)
            self.appData['state'] = 'maxim'
        else:
            self.appData['state'] = 'normal'
        self.appData['auiPerspective'] = self.paneManager.SavePerspective()
        self.appData['winW'], self.appData['winH'] = self.GetSize()
        self.appData['winX'], self.appData['winY'] = self.GetPosition()
        if sys.platform == 'darwin':
            # for some reason mac wxpython <=2.8 gets this wrong (toolbar?)
            self.appData['winH'] -= 39
        self.appData['fileHistory'] = []
        for ii in range(self.fileHistory.GetCount()):
            self.appData['fileHistory'].append(
                self.fileHistory.GetHistoryFile(ii))

        # as of wx3.0 the AUI manager needs to be uninitialised explicitly
        self.paneManager.UnInit()

        self.app.forgetFrame(self)
        self.Destroy()
        self.app.coder = None

    def filePrint(self, event=None):
        pr = Printer()
        docName = self.currentDoc.filename
        text = open(docName, 'r').read()
        pr.Print(text, docName)

    def fileNew(self, event=None, filepath=""):
        self.setCurrentDoc(filepath)

    def fileReload(self, event, filename=None, checkSave=False):
        if filename is None:
            return  # should raise an exception

        docId = self.findDocID(filename)
        if docId == -1:
            return
        doc = self.notebook.GetPage(docId)

        # is the file still there
        if os.path.isfile(filename):
            with io.open(filename, 'r', encoding='utf-8-sig') as f:
                doc.SetText(f.read())
            doc.fileModTime = os.path.getmtime(filename)
            doc.EmptyUndoBuffer()
            doc.Colourise(0, -1)
            doc.UNSAVED = False
        else:
            # file was removed after we found the changes, lets
            # give the user a chance to save his file.
            self.UNSAVED = True

        if doc == self.currentDoc:
            self.toolbar.EnableTool(self.IDs.cdrBtnSave, doc.UNSAVED)

    def findDocID(self, filename):
        # find the ID of the current doc
        for ii in range(self.notebook.GetPageCount()):
            if self.notebook.GetPage(ii).filename == filename:
                return ii
        return -1

    def setCurrentDoc(self, filename, keepHidden=False):
        # check if this file is already open
        docID = self.findDocID(filename)
        readOnlyPref = 'readonly' in self.app.prefs.coder
        readonly = readOnlyPref and self.app.prefs.coder['readonly']
        if docID >= 0:
            self.currentDoc = self.notebook.GetPage(docID)
            self.notebook.SetSelection(docID)
        else:  # create new page and load document
            # if there is only a placeholder document then close it
            if len(self.getOpenFilenames()) == 1:
                if (len(self.currentDoc.GetText()) == 0 and
                        self.currentDoc.filename.startswith('untitled')):
                    self.fileClose(self.currentDoc.filename)

            # create an editor window to put the text in
            p = self.currentDoc = CodeEditor(self.notebook, -1, frame=self,
                                             readonly=readonly)
            # load text from document
            if os.path.isfile(filename):
                try:
                    with io.open(filename, 'r', encoding='utf-8-sig') as f:
                        self.currentDoc.SetText(f.read())
                        self.currentDoc.newlines = f.newlines
                except UnicodeDecodeError:
                    dlg = dialogs.MessageDialog(self, message=_translate(
                        'Failed to open {}. Make sure that encoding of '
                        'the file is utf-8.').format(filename), type='Info')
                    dlg.ShowModal()
                    dlg.Destroy()
                self.currentDoc.fileModTime = os.path.getmtime(filename)
                self.fileHistory.AddFileToHistory(filename)
            else:
                self.currentDoc.SetText("")
            self.currentDoc.EmptyUndoBuffer()
            if filename.endswith('.py'):
                self.currentDoc.setLexer('python')
            elif filename.endswith('.m'):
                self.currentDoc.setLexer('matlab')
            elif filename.endswith('.sh'):
                self.currentDoc.setLexer('bash')
            elif filename.endswith('.c'):
                self.currentDoc.setLexer('c')
            elif filename.endswith('.html'):
                self.currentDoc.setLexer('html')
            elif filename.endswith('.R'):
                self.currentDoc.setLexer('r')
            elif filename.endswith('.xml'):
                self.currentDoc.setLexer('xml')
            elif filename.endswith('.yaml'):
                self.currentDoc.setLexer('yaml')

            # line numbers in the margin
            self.currentDoc.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
            self.currentDoc.SetMarginWidth(1, 32)
            # set name for an untitled document
            if filename == "":
                filename = shortName = 'untitled.py'
                allFileNames = self.getOpenFilenames()
                n = 1
                while filename in allFileNames:
                    filename = shortName = 'untitled%i.py' % n
                    n += 1
            else:
                path, shortName = os.path.split(filename)
            self.notebook.AddPage(p, shortName)
            nbIndex = len(self.getOpenFilenames()) - 1
            if isinstance(self.notebook, wx.Notebook):
                self.notebook.ChangeSelection(nbIndex)
            elif isinstance(self.notebook, aui.AuiNotebook):
                self.notebook.SetSelection(nbIndex)
            self.currentDoc.filename = filename
            self.setFileModified(False)
            self.currentDoc.SetFocus()
        self.SetLabel('%s - PsychoPy Coder' % self.currentDoc.filename)
        if analyseAuto and len(self.getOpenFilenames()) > 0:
            self.SetStatusText(_translate('Analyzing code'))
            self.currentDoc.analyseScript()
            self.SetStatusText('')
        if not keepHidden:
            self.Show()  # if the user had closed the frame it might be hidden
        if readonly:
            self.currentDoc.SetReadOnly(True)

    def fileOpen(self, event=None, filename=None):
        if not filename:
            # get path of current file (empty if current file is '')
            if hasattr(self.currentDoc, 'filename'):
                initPath = os.path.split(self.currentDoc.filename)[0]
            else:
                initPath = ''
            dlg = wx.FileDialog(
                self, message=_translate("Open file ..."),
                defaultDir=initPath, style=wx.FD_OPEN
            )

            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                self.SetStatusText(_translate('Loading file'))
            else:
                return -1

        if filename and os.path.isfile(filename):
            if filename.lower().endswith('.psyexp'):
                self.app.newBuilderFrame(fileName=filename)
            else:
                self.setCurrentDoc(filename)
                self.setFileModified(False)
        self.SetStatusText('')
        # self.fileHistory.AddFileToHistory(newPath)  # this is done by
        # setCurrentDoc

    def expectedModTime(self, doc):
        # check for possible external changes to the file, based on
        # mtime-stamps
        if doc is None:
            return True  # we have no file loaded
        # files that don't exist DO have the expected mod-time
        filename = doc.filename
        if not os.path.exists(filename):
            return True
        actualModTime = os.path.getmtime(filename)
        expectedModTime = doc.fileModTime
        if actualModTime != expectedModTime:
            msg = 'File %s modified outside of the Coder (IDE).' % filename
            print(msg)
            return False
        return True

    def fileSave(self, event=None, filename=None, doc=None):
        """Save a ``doc`` with a particular ``filename``.
        If ``doc`` is ``None`` then the current active doc is used.
        If the ``filename`` is ``None`` then the ``doc``'s current filename
        is used or a dlg is presented to get a new filename.
        """
        if self.currentDoc.AutoCompActive():
            self.currentDoc.AutoCompCancel()

        if doc is None:
            doc = self.currentDoc
        if filename is None:
            filename = doc.filename
        if filename.startswith('untitled'):
            self.fileSaveAs(filename)
            # self.setFileModified(False) # done in save-as if saved; don't
            # want here if not saved there
        else:
            # here detect odd conditions, and set failToSave = True to try
            # 'Save-as' rather than 'Save'
            failToSave = False
            if not self.expectedModTime(doc) and os.path.exists(filename):
                msg = _translate("File appears to have been modified outside "
                                 "of PsychoPy:\n   %s\nOK to overwrite?")
                basefile = os.path.basename(doc.filename)
                dlg = dialogs.MessageDialog(self, message=msg % basefile,
                                            type='Warning')
                if dlg.ShowModal() != wx.ID_YES:
                    failToSave = True
                try:
                    dlg.destroy()
                except Exception:
                    pass
            if os.path.exists(filename) and not os.access(filename, os.W_OK):
                msg = _translate("File '%s' lacks write-permission:\n"
                                 "Will try save-as instead.")
                basefile = os.path.basename(doc.filename)
                dlg = dialogs.MessageDialog(self, message=msg % basefile,
                                            type='Info')
                dlg.ShowModal()
                failToSave = True
                try:
                    dlg.destroy()
                except Exception:
                    pass
            try:
                if failToSave:
                    raise IOError
                self.SetStatusText(_translate('Saving file'))
                newlines = '\n'  # system default, os.linesep
                with io.open(filename, 'w', encoding='utf-8', newline=newlines) as f:
                    f.write(doc.GetText())
                self.setFileModified(False)
                doc.fileModTime = os.path.getmtime(filename)  # JRG
            except Exception:
                print("Unable to save %s... trying save-as instead." %
                      os.path.basename(doc.filename))
                self.fileSaveAs(filename)

        if analyseAuto and len(self.getOpenFilenames()) > 0:
            self.SetStatusText(_translate('Analyzing current source code'))
            self.currentDoc.analyseScript()
        # reset status text
        self.SetStatusText('')
        self.fileHistory.AddFileToHistory(filename)

    def fileSaveAs(self, event, filename=None, doc=None):
        """Save a ``doc`` with a new ``filename``, after presenting a dlg
        to get a new filename.

        If ``doc`` is ``None`` then the current active doc is used.

        If the ``filename`` is not ``None`` then this will be the initial
        value for the filename in the dlg.
        """
        # cancel autocomplete if active
        if self.currentDoc.AutoCompActive():
            self.currentDoc.AutoCompCancel()

        if doc is None:
            doc = self.currentDoc
            docId = self.notebook.GetSelection()
        else:
            docId = self.findDocID(doc.filename)
        if filename is None:
            filename = doc.filename
        # if we have an absolute path then split it
        initPath, filename = os.path.split(filename)
        # set wildcards; need strings to appear inside _translate
        if sys.platform != 'darwin':
            wildcard = _translate("Python scripts (*.py)|*.py|Text file "
                                  "(*.txt)|*.txt|Any file (*.*)|*.*")
        else:
            wildcard = _translate("Python scripts (*.py)|*.py|Text file "
                                  "(*.txt)|*.txt|Any file (*.*)|*")

        dlg = wx.FileDialog(
            self, message=_translate("Save file as ..."), defaultDir=initPath,
            defaultFile=filename, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            wildcard=wildcard)

        if dlg.ShowModal() == wx.ID_OK:
            newPath = dlg.GetPath()
            doc.filename = newPath
            self.fileSave(event=None, filename=newPath, doc=doc)
            path, shortName = os.path.split(newPath)
            self.notebook.SetPageText(docId, shortName)
            self.setFileModified(False)
            # JRG: 'doc.filename' should = newPath = dlg.getPath()
            doc.fileModTime = os.path.getmtime(doc.filename)

        try:  # this seems correct on PC, but can raise errors on mac
            dlg.destroy()
        except Exception:
            pass

    def fileClose(self, event, filename=None, checkSave=True):
        if self.currentDoc is None:
            # so a coder window with no files responds like the builder window
            # to self.keys.close
            self.closeFrame()
            return
        if filename is None:
            filename = self.currentDoc.filename
        self.currentDoc = self.notebook.GetPage(self.notebook.GetSelection())
        if self.currentDoc.UNSAVED and checkSave:
            sys.stdout.flush()
            msg = _translate('Save changes to %s before quitting?') % filename
            dlg = dialogs.MessageDialog(self, message=msg, type='Warning')
            resp = dlg.ShowModal()
            sys.stdout.flush()
            dlg.Destroy()
            if resp == wx.ID_CANCEL:
                return -1  # return, don't quit
            elif resp == wx.ID_YES:
                # save then quit
                self.fileSave(None)
            elif resp == wx.ID_NO:
                pass  # don't save just quit
        # remove the document and its record
        currId = self.notebook.GetSelection()
        # if this was called by AuiNotebookEvent, then page has closed already
        if not isinstance(event, aui.AuiNotebookEvent):
            self.notebook.DeletePage(currId)
            newPageID = self.notebook.GetSelection()
        else:
            newPageID = self.notebook.GetSelection() - 1
        # set new current doc
        if newPageID < 0:
            self.currentDoc = None
            self.SetLabel("PsychoPy v%s (Coder)" % self.app.version)
        else:
            self.currentDoc = self.notebook.GetPage(newPageID)
            # set to current file status
            self.setFileModified(self.currentDoc.UNSAVED)
        # return 1

    def _runFileAsImport(self):
        fullPath = self.currentDoc.filename
        path, scriptName = os.path.split(fullPath)
        importName, ext = os.path.splitext(scriptName)
        # set the directory and add to path
        os.chdir(path)  # try to rewrite to avoid doing chdir in the coder
        sys.path.insert(0, path)

        # update toolbar
        self.toolbar.EnableTool(self.IDs.cdrBtnRun, False)
        self.toolbar.EnableTool(self.IDs.cdrBtnStop, True)

        # do an 'import' on the file to run it
        # delete the sys reference to it (so we think its a new import)
        if importName in sys.modules:
            sys.modules.pop(importName)
        exec('import %s' % (importName))  # or run first time

    def _runFileInDbg(self):
        # setup a debugger and then runFileAsImport
        fullPath = self.currentDoc.filename
        path, scriptName = os.path.split(fullPath)
        # importName, ext = os.path.splitext(scriptName)
        # set the directory and add to path
        os.chdir(path)  # try to rewrite to avoid doing chdir in the coder

        self.db = PsychoDebugger()
        self.db.runcall(self._runFileAsImport)

    def _runFileAsProcess(self):
        fullPath = self.currentDoc.filename
        path, scriptName = os.path.split(fullPath)
        # importName, ext = os.path.splitext(scriptName)
        # set the directory and add to path
        # try to rewrite to avoid doing chdir in the coder; do through
        # wx.Shell?
        os.chdir(path)
        # self is the parent (which will receive an event when the process
        # ends)
        self.scriptProcess = wx.Process(self)
        self.scriptProcess.Redirect()  # catch the stdout/stdin

        if sys.platform == 'win32':
            # the quotes allow file paths with spaces
            command = '"%s" -u "%s"' % (sys.executable, fullPath)
            # self.scriptProcessID = wx.Execute(command, wx.EXEC_ASYNC,
            #    self.scriptProcess)
            if hasattr(wx, "EXEC_NOHIDE"):
                _opts = wx.EXEC_ASYNC | wx.EXEC_NOHIDE  # that hid console!
            else:
                _opts = wx.EXEC_ASYNC | wx.EXEC_SHOW_CONSOLE
        else:
            fullPath = fullPath.replace(' ', '\ ')
            pythonExec = sys.executable.replace(' ', '\ ')
            # the quotes would break a unix system command
            command = '%s -u %s' % (pythonExec, fullPath)
            _opts = wx.EXEC_ASYNC | wx.EXEC_MAKE_GROUP_LEADER
        # launch the command
        self.scriptProcessID = wx.Execute(command, _opts,
                                          self.scriptProcess)
        self.toolbar.EnableTool(self.IDs.cdrBtnRun, False)
        self.toolbar.EnableTool(self.IDs.cdrBtnStop, True)

    def runFile(self, event):
        """Runs files by one of various methods
        """
        fullPath = self.currentDoc.filename
        filename = os.path.split(fullPath)[1]
        # does the file need saving before running?
        if self.currentDoc.UNSAVED:
            sys.stdout.flush()
            msg = _translate('Save changes to %s before running?') % filename
            dlg = dialogs.MessageDialog(self, message=msg, type='Warning')
            resp = dlg.ShowModal()
            sys.stdout.flush()
            dlg.Destroy()
            if resp == wx.ID_CANCEL:
                return -1  # return, don't run
            elif resp == wx.ID_YES:
                self.fileSave(None)  # save then run
            elif resp == wx.ID_NO:
                pass  # just run

        if sys.platform in ['darwin']:
            # restore normal text color for coder output window (stdout);
            # doesn't fix the issue
            print("\033")
        else:
            print()

        # check syntax by compiling - errors printed (not raised as error)
        try:
            if not PY3 or type(fullPath) == bytes:
                # py_compile.compile doesn't accept Unicode filename.
                py_compile.compile(fullPath.encode(
                    sys.getfilesystemencoding()), doraise=False)
            else:
                py_compile.compile(fullPath, doraise=False)
        except Exception as e:
            print("Problem compiling: %s" % e)

        # provide a running... message; long fullPath --> no # are displayed
        # unless you add some manually
        print(("##### Running: %s #####" % (fullPath)).center(80, "#"))

        self.ignoreErrors = False
        self.SetEvtHandlerEnabled(False)
        self.Bind(wx.EVT_IDLE, None)

        # try to run script
        try:  # try to capture any errors in the script
            if runScripts == 'thread':
                self.thread = ScriptThread(
                    target=self._runFileAsImport, gui=self)
                self.thread.start()
            elif runScripts == 'process':
                self._runFileAsProcess()

            elif runScripts == 'dbg':
                # create a thread and run file as debug within that thread
                self.thread = ScriptThread(target=self._runFileInDbg, gui=self)
                self.thread.start()
            elif runScripts == 'import':
                raise NotImplementedError()
                # simplest possible way, but fragile
                # USING import of scripts (clunky)
                # if importName in sys.modules:  # delete the sys reference to it
                #     sys.modules.pop(importName)
                # exec('import %s' % (importName))  # or run first time

                # NB execfile() would be better doesn't run the import
                # statements properly! functions defined in the script have
                # a separate namespace to the main body of the script(!?)
                # execfile(thisFile)
        # except SystemExit:  # this is used in psychopy.core.quit()
        #     pass
        except Exception:  # report any errors, SystemExit is not caught
            if self.ignoreErrors:
                pass
            else:
                # traceback.print_exc()
                # tb = traceback.extract_tb(sys.last_traceback)
                # for err in tb:
                #    print('%s, line:%i,function:%s\n%s' %tuple(err))
                print('')  # just a new line

        self.SetEvtHandlerEnabled(True)
        self.Bind(wx.EVT_IDLE, self.onIdle)

    def stopFile(self, event):
        self.toolbar.EnableTool(self.IDs.cdrBtnRun, True)
        self.toolbar.EnableTool(self.IDs.cdrBtnStop, False)
        self.app.terminateHubProcess()
        if runScripts in ['thread', 'dbg']:
            # killing a debug context doesn't really work on pygame scripts
            # because of the extra
            if runScripts == 'dbg':
                self.db.quit()
            try:
                pygame.display.quit()  # if pygame is running, try to kill it
            except Exception:
                pass
            self.thread.kill()
            # stop listening for errors if the script has ended:
            self.ignoreErrors = False
        elif runScripts == 'process':
            # try to kill it gently first
            success = wx.Kill(self.scriptProcessID, wx.SIGTERM)
            if success[0] != wx.KILL_OK:
                # kill it aggressively
                wx.Kill(self.scriptProcessID, wx.SIGKILL)

    def copy(self, event):
        foc = self.FindFocus()
        foc.Copy()
        # if isinstance(foc, CodeEditor):
        #    self.currentDoc.Copy()  # let the text ctrl handle this
        # elif isinstance(foc, StdOutRich):

    def duplicateLine(self, event):
        self.currentDoc.LineDuplicate()

    def cut(self, event):
        self.currentDoc.Cut()  # let the text ctrl handle this

    def paste(self, event):
        foc = self.FindFocus()
        if hasattr(foc, 'Paste'):
            foc.Paste()

    def undo(self, event):
        self.currentDoc.Undo()

    def redo(self, event):
        self.currentDoc.Redo()

    def commentSelected(self, event):
        self.currentDoc.commentLines()

    def uncommentSelected(self, event):
        self.currentDoc.uncommentLines()

    def toggleComments(self, event):
        self.currentDoc.toggleCommentLines()

    def bigFont(self, event):
        self.currentDoc.increaseFontSize()

    def smallFont(self, event):
        self.currentDoc.decreaseFontSize()

    def foldAll(self, event):
        self.currentDoc.FoldAll()

    # def unfoldAll(self, event):
    #   self.currentDoc.ToggleFoldAll(expand = False)

    def setOutputWindow(self, event=None, value=None):
        # show/hide the output window (from the view menu control)
        if value is None:
            value = self.outputChk.IsChecked()
        if value:
            # show the pane
            self.prefs['showOutput'] = True
            self.paneManager.GetPane('Shelf').Show()
            # will we actually redirect the output?
            # don't if we're doing py.tests or we lose the output
            if not self.app.testMode:
                sys.stdout = self.outputWindow
                sys.stderr = self.outputWindow
        else:
            # show the pane
            self.prefs['showOutput'] = False
            self.paneManager.GetPane('Shelf').Hide()
            sys.stdout = self._origStdOut  # discovered during __init__
            sys.stderr = self._origStdErr
        self.app.prefs.saveUserPrefs()  # includes a validation

        self.paneManager.Update()

    def setShowIndentGuides(self, event):
        # show/hide the source assistant (from the view menu control)
        newVal = self.indentGuideChk.IsChecked()
        self.appData['showIndentGuides'] = newVal
        for ii in range(self.notebook.GetPageCount()):
            self.notebook.GetPage(ii).SetIndentationGuides(newVal)

    def setShowWhitespace(self, event):
        newVal = self.showWhitespaceChk.IsChecked()
        self.appData['showWhitespace'] = newVal
        for ii in range(self.notebook.GetPageCount()):
            self.notebook.GetPage(ii).SetViewWhiteSpace(newVal)

    def setShowEOLs(self, event):
        newVal = self.showEOLsChk.IsChecked()
        self.appData['showEOLs'] = newVal
        for ii in range(self.notebook.GetPageCount()):
            self.notebook.GetPage(ii).SetViewEOL(newVal)

    def setSourceAsst(self, event):
        # show/hide the source assistant (from the view menu control)
        if not self.sourceAsstChk.IsChecked():
            self.paneManager.GetPane("SourceAsst").Hide()
            self.prefs['showSourceAsst'] = False
        else:
            self.paneManager.GetPane("SourceAsst").Show()
            self.prefs['showSourceAsst'] = True
        self.paneManager.Update()

    def analyseCodeNow(self, event):
        self.SetStatusText(_translate('Analyzing code'))
        if self.currentDoc is not None:
            self.currentDoc.analyseScript()
        else:
            # todo: add _translate()
            txt = 'Open a file from the File menu, or drag one onto this app, or open a demo from the Help menu'
            print(txt)

        self.SetStatusText(_translate('ready'))

    # def setAnalyseAuto(self, event):
    #     set autoanalysis (from the check control in the tools menu)
    #     if self.analyseAutoChk.IsChecked():
    #        self.prefs['analyseAuto']=True
    #     else:
    #        self.prefs['analyseAuto']=False

    def loadDemo(self, event):
        self.setCurrentDoc(self.demos[event.GetId()])

    def tabKeyPressed(self, event):
        # if several chars are selected then smartIndent
        # if we're at the start of the line then smartIndent
        if self.currentDoc.shouldTrySmartIndent():
            self.smartIndent(event=None)
        else:
            # self.currentDoc.CmdKeyExecute(wx.stc.STC_CMD_TAB)
            pos = self.currentDoc.GetCurrentPos()
            self.currentDoc.InsertText(pos, '\t')
            self.currentDoc.SetCurrentPos(pos + 1)
            self.currentDoc.SetSelection(pos + 1, pos + 1)

    def smartIndent(self, event):
        self.currentDoc.smartIndent()

    def indent(self, event):
        self.currentDoc.indentSelection(4)

    def dedent(self, event):
        self.currentDoc.indentSelection(-4)

    def setFileModified(self, isModified):
        # changes the document flag, updates save buttons
        self.currentDoc.UNSAVED = isModified
        # disabled when not modified
        self.toolbar.EnableTool(self.IDs.cdrBtnSave, isModified)
        # self.fileMenu.Enable(self.fileMenu.FindItem('&Save\tCtrl+S"'),
        #     isModified)

    def onProcessEnded(self, event):
        # this is will check the stdout and stderr for any last messages
        self.onIdle(event=None)
        self.scriptProcess = None
        self.scriptProcessID = None
        self.toolbar.EnableTool(self.IDs.cdrBtnRun, True)
        self.toolbar.EnableTool(self.IDs.cdrBtnStop, False)

    def onURL(self, evt):
        """decompose the URL of a file and line number"""
        # "C:\Program Files\wxPython2.8 Docs and Demos\samples\hangman\hangman.py"
        tmpFilename, tmpLineNumber = evt.GetString().rsplit('", line ', 1)
        filename = tmpFilename.split('File "', 1)[1]
        try:
            lineNumber = int(tmpLineNumber.split(',')[0])
        except ValueError:
            lineNumber = int(tmpLineNumber.split()[0])
        self.gotoLine(filename, lineNumber)

    def onUnitTests(self, evt=None):
        """Show the unit tests frame"""
        if self.unitTestFrame:
            self.unitTestFrame.Raise()
        else:
            self.unitTestFrame = UnitTestFrame(app=self.app)
        # UnitTestFrame.Show()

    def onPavloviaSync(self, evt=None):
        """Push changes to project repo, or create new proj if proj is None"""
        self.project = pavlovia.getProject(self.currentDoc.filename)
        self.fileSave(self.currentDoc.filename)  # Must save on sync else changes not pushed
        pavlovia_ui.syncProject(parent=self, project=self.project)

    def onPavloviaRun(self, evt=None):
        # TODO: Allow user to run project from coder
        pass

    def setPavloviaUser(self, user):
        # TODO: update user icon on button to user avatar
        pass
