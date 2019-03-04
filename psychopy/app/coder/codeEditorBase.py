#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides class BaseCodeEditor; base class for
    CodeEditor class in Coder
    and CodeBox class in dlgCode (code component)
"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import wx
import sys
from pkg_resources import parse_version
from psychopy.constants import PY3
from psychopy import logging


class BaseCodeEditor(wx.stc.StyledTextCtrl):
    """Provides base class for code editors
       See the wxPython demo styledTextCtrl 2.
    """

    def __init__(self, parent, ID, pos, size, style):
        wx.stc.StyledTextCtrl.__init__(self, parent, ID, pos, size, style)

        self.notebook = parent
        self.UNSAVED = False
        self.filename = ""
        self.fileModTime = None  # was file modified outside of CodeEditor
        self.AUTOCOMPLETE = True
        self.autoCompleteDict = {}
        self._commentType = {'Py': '#', 'JS': '//', 'Both': '//' or '#'}

        # doesn't pause strangely
        self.locals = None  # will contain the local environment of the script
        self.prevWord = None
        # remove some annoying stc key commands
        CTRL = wx.stc.STC_SCMOD_CTRL
        self.CmdKeyClear(ord('['), CTRL)
        self.CmdKeyClear(ord(']'), CTRL)
        self.CmdKeyClear(ord('/'), CTRL)
        self.CmdKeyClear(ord('/'), CTRL | wx.stc.STC_SCMOD_SHIFT)

        # 4 means 'tabs are bad'; 1 means 'flag inconsistency'
        self.SetMargins(0, 0)
        self.SetUseTabs(False)
        self.SetTabWidth(4)
        self.SetIndent(4)
        self.SetBufferedDraw(False)
        self.SetEOLMode(wx.stc.STC_EOL_LF)

        # Setup a margin to hold fold markers
        self.SetMarginType(2, wx.stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, wx.stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(2, True)
        self.SetMarginWidth(2, 12)

        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPEN,
                          wx.stc.STC_MARK_BOXMINUS, "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDER,
                          wx.stc.STC_MARK_BOXPLUS, "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERSUB,
                          wx.stc.STC_MARK_VLINE, "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERTAIL,
                          wx.stc.STC_MARK_LCORNER, "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEREND,
                          wx.stc.STC_MARK_BOXPLUSCONNECTED, "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPENMID,
                          wx.stc.STC_MARK_BOXMINUSCONNECTED, "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERMIDTAIL,
                          wx.stc.STC_MARK_TCORNER, "white", "#808080")

        # Bind context menu
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def OnContextMenu(self, event):
        """Sets the context menu for components using code editor base class"""

        if not hasattr(self, "UndoID"):
            # Create a new ID for all items
            self.UndoID = wx.NewId()
            self.RedoID = wx.NewId()
            self.CutID = wx.NewId()
            self.CopyID = wx.NewId()
            self.PasteID = wx.NewId()
            self.DeleteID = wx.NewId()
            self.SelectAllID = wx.NewId()

        # Bind items to relevant method
        self.Bind(wx.EVT_MENU, self.onUndo, id=self.UndoID)
        self.Bind(wx.EVT_MENU, self.onRedo, id=self.RedoID)
        self.Bind(wx.EVT_MENU, self.onCut, id=self.CutID)
        self.Bind(wx.EVT_MENU, self.onCopy, id=self.CopyID)
        self.Bind(wx.EVT_MENU, self.onPaste, id=self.PasteID)
        self.Bind(wx.EVT_MENU, self.onDelete, id=self.DeleteID)
        self.Bind(wx.EVT_MENU, self.onSelectAll, id=self.SelectAllID)

        # Create menu and menu items
        menu = wx.Menu()
        undoItem = wx.MenuItem(menu, self.UndoID, "Undo")
        redoItem = wx.MenuItem(menu, self.RedoID, "Redo")
        cutItem = wx.MenuItem(menu, self.CutID, "Cut")
        copyItem = wx.MenuItem(menu, self.CopyID, "Copy")
        pasteItem = wx.MenuItem(menu, self.PasteID, "Paste")
        deleteItem = wx.MenuItem(menu, self.DeleteID, "Delete")
        selectItem = wx.MenuItem(menu, self.SelectAllID, "Select All")

        # Check whether items should be enabled
        undoItem.Enable(self.CanUndo())
        redoItem.Enable(self.CanRedo())
        cutItem.Enable(self.CanCut())
        copyItem.Enable(self.CanCopy())
        pasteItem.Enable(self.CanPaste())
        deleteItem.Enable(self.CanCopy())

        # Append items to menu
        menu.Append(undoItem)
        menu.Append(redoItem)
        menu.AppendSeparator()
        menu.Append(cutItem)
        menu.Append(copyItem)
        menu.Append(pasteItem)
        menu.AppendSeparator()
        menu.Append(deleteItem)
        menu.Append(selectItem)

        self.PopupMenu(menu)
        menu.Destroy()

    def onUndo(self, event):
        """For context menu Undo"""
        foc = self.FindFocus()
        if hasattr(foc, 'Undo'):
            foc.Undo()

    def onRedo(self, event):
        """For context menu Redo"""
        foc = self.FindFocus()
        if hasattr(foc, 'Redo'):
            foc.Redo()

    def onCut(self, event):
        """For context menu Cut"""
        foc = self.FindFocus()
        if hasattr(foc, 'Cut'):
            foc.Cut()

    def onCopy(self, event):
        """For context menu Copy"""
        foc = self.FindFocus()
        if hasattr(foc, 'Copy'):
            foc.Copy()

    def onPaste(self, event):
        """For context menu Paste"""
        foc = self.FindFocus()
        if hasattr(foc, 'Paste'):
            foc.Paste()

    def onSelectAll(self, event):
        """For context menu Select All"""
        foc = self.FindFocus()
        if hasattr(foc, 'SelectAll'):
            foc.SelectAll()

    def onDelete(self, event):
        """For context menu Delete"""
        foc = self.FindFocus()
        if hasattr(foc, 'DeleteBack'):
            foc.DeleteBack()

    def OnKeyPressed(self, event):
        pass

    def HashtagCounter(self, text, nTags=0):
        # Hashtag counter - counts lines beginning with hashtags in selected text
        for lines in text.splitlines():
            if lines.startswith('#'):
                nTags += 1
            elif lines.startswith('//'):
                nTags += 2
        return nTags

    def toggleCommentLines(self, codeType='Py'):
        # toggle comment

        startText, endText = self._GetPositionsBoundingSelectedLines()
        nLines = len(self._GetSelectedLineNumbers())
        nHashtags = self.HashtagCounter(self.GetTextRange(startText, endText))
        passDec = False # pass decision - only pass  if line is blank
        # Test decision criteria, and catch devision errors
        # when caret starts at line with no text, or at beginning of line...
        try:
            devCrit, decVal = .6, nHashtags / nLines # Decision criteria and value
        except ZeroDivisionError:
            if self.LineLength(self.GetCurrentLine()) == 1:
                self._ReplaceSelectedLines(self._commentType[codeType])
                devCrit, decVal, passDec = 1, 0, True
            else:
                self.CharRightExtend() # Move caret so line is counted
                devCrit, decVal = .6, nHashtags / len(self._GetSelectedLineNumbers())
        newText = ''
        # Add or remove hashtags/JS comments from selected text, but pass if # added tp blank line
        if decVal < devCrit and passDec == False:
            for lineNo in self._GetSelectedLineNumbers():
                lineText = self.GetLine(lineNo)
                newText = newText + self._commentType[codeType] + lineText
        elif decVal >= devCrit and passDec == False:
            for lineNo in self._GetSelectedLineNumbers():
                lineText = self.GetLine(lineNo)
                if lineText.startswith(self._commentType[codeType]):
                    lineText = lineText[len(self._commentType[codeType]):]
                newText = newText + lineText
        self._ReplaceSelectedLines(newText)

    def _GetSelectedLineNumbers(self):
        # used for the comment/uncomment machinery from ActiveGrid
        selStart, selEnd = self._GetPositionsBoundingSelectedLines()
        start = self.LineFromPosition(selStart)
        end = self.LineFromPosition(selEnd)
        if selEnd == self.GetTextLength():
            end += 1
        return list(range(start, end))

    def _GetPositionsBoundingSelectedLines(self):
        # used for the comment/uncomment machinery from ActiveGrid
        startPos = self.GetCurrentPos()
        endPos = self.GetAnchor()
        if startPos > endPos:
            startPos, endPos = endPos, startPos
        if endPos == self.PositionFromLine(self.LineFromPosition(endPos)):
        # If it's at the very beginning of a line, use the line above it
        # as the ending line
            endPos = endPos - 1
        selStart = self.PositionFromLine(self.LineFromPosition(startPos))
        selEnd = self.PositionFromLine(self.LineFromPosition(endPos) + 1)
        return selStart, selEnd

    def _ReplaceSelectedLines(self, text):
        # used for the comment/uncomment machinery from ActiveGrid
        # If multi line selection - keep lines selected
        # For single lines, move to next line and select that line
        if len(text) == 0:
            return
        selStart, selEnd = self._GetPositionsBoundingSelectedLines()
        self.SetSelection(selStart, selEnd)
        self.ReplaceSelection(text)
        if len(text.splitlines()) > 1:
            self.SetSelection(selStart, selStart + len(text))
        else:
            self.SetSelection(self.GetCurrentPos(), self.GetLineEndPosition(self.GetCurrentLine()))

    def smartIdentThisLine(self, codeType='Py'):
        startLineNum = self.LineFromPosition(self.GetSelectionStart())
        endLineNum = self.LineFromPosition(self.GetSelectionEnd())
        prevLine = self.GetLine(startLineNum - 1)
        prevIndent = self.GetLineIndentation(startLineNum - 1)
        signal = {'Py': [':'], 'JS': ['{'], 'Both': ['{', ':']}

        # set the indent
        self.SetLineIndentation(startLineNum, prevIndent)
        # self.LineEnd()  # move cursor to end of line - is good if user
        #     is starting a new line but not if they hit shift-tab
        # self.SetPosition(startLineNum+prevIndent)  # move cursor to the end
        # of the indented section
        self.VCHome()

        # check for a colon (Python) or curly brace (JavaScript) to signal an indent
        prevLogical = prevLine.split(self._commentType[codeType])[0]
        prevLogical = prevLogical.strip()
        if len(prevLogical) > 0 and prevLogical[-1] in signal[codeType]:
            self.CmdKeyExecute(wx.stc.STC_CMD_TAB)
        elif len(prevLogical) > 0 and prevLogical[-1] == '}' and codeType in ['JS', 'Both']:
            self.CmdKeyExecute(wx.stc.STC_SCMOD_SHIFT + wx.stc.STC_CMD_TAB)

    def smartIndent(self):
        # find out about current positions and indentation
        startLineNum = self.LineFromPosition(self.GetSelectionStart())
        endLineNum = self.LineFromPosition(self.GetSelectionEnd())
        prevLine = self.GetLine(startLineNum - 1)
        prevIndent = self.GetLineIndentation(startLineNum - 1)
        startLineIndent = self.GetLineIndentation(startLineNum)

        # calculate how much we need to increment/decrement the current lines
        incr = prevIndent - startLineIndent
        # check for a colon to signal an indent decrease
        prevLogical = prevLine.split('#')[0]
        prevLogical = prevLogical.strip()
        if len(prevLogical) > 0 and prevLogical[-1] == ':':
            incr = incr + 4
        # set each line to the correct indentation
        for lineNum in range(startLineNum, endLineNum + 1):
            thisIndent = self.GetLineIndentation(lineNum)
            self.SetLineIndentation(lineNum, thisIndent + incr)

    def shouldTrySmartIndent(self):
        # used when the user presses tab key: decide whether to insert
        # a tab char or whether to smart indent text

        # if some text has been selected then use indentation
        if len(self.GetSelectedText()) > 0:
            return True

        # test whether any text precedes current pos
        lineText, posOnLine = self.GetCurLine()
        textBeforeCaret = lineText[:posOnLine]
        if textBeforeCaret.split() == []:
            return True
        else:
            return False

    def indentSelection(self, howFar=4):
        # Indent or outdent current selection by 'howFar' spaces
        # (which could be positive or negative int).
        startLineNum = self.LineFromPosition(self.GetSelectionStart())
        endLineNum = self.LineFromPosition(self.GetSelectionEnd())
        # go through line-by-line
        for lineN in range(startLineNum, endLineNum + 1):
            newIndent = self.GetLineIndentation(lineN) + howFar
            if newIndent < 0:
                newIndent = 0
            self.SetLineIndentation(lineN, newIndent)

    def Paste(self, event=None):
        dataObj = wx.TextDataObject()
        clip = wx.Clipboard().Get()
        clip.Open()
        success = clip.GetData(dataObj)
        clip.Close()
        if success:
            txt = dataObj.GetText()
            # dealing with unicode error in wx3 for Mac
            if parse_version(wx.__version__) >= parse_version('3') and sys.platform == 'darwin' and not PY3:
                try:
                    # if we can decode from utf-8 then all is good
                    txt.decode('utf-8')
                except Exception as e:
                    logging.error(str(e))
                    # if not then wx conversion broke so get raw data instead
                    txt = dataObj.GetDataHere()
            self.ReplaceSelection(txt.replace("\r\n", "\n").replace("\r", "\n"))
