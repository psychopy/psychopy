#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides class BaseCodeEditor; base class for
    CodeEditor class in Coder
    and CodeBox class in dlgCode (code component)
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
import wx.stc
from ..themes import handlers

from psychopy.localization import _translate


class BaseCodeEditor(wx.stc.StyledTextCtrl, handlers.ThemeMixin):
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

        # setup margins for line numbers
        self.SetMarginType(0, wx.stc.STC_MARGIN_NUMBER)
        self.SetMarginWidth(0, 40)

        # Setup a margin to hold fold markers
        self.SetMarginType(1, wx.stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(1, wx.stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(1, True)
        self.SetMarginWidth(1, 12)

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

        # Set what kind of events will trigger a modified event
        self.SetModEventMask(wx.stc.STC_MOD_DELETETEXT |
                             wx.stc.STC_MOD_INSERTTEXT)

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
        undoItem = wx.MenuItem(menu, self.UndoID, _translate("Undo"))
        redoItem = wx.MenuItem(menu, self.RedoID, _translate("Redo"))
        cutItem = wx.MenuItem(menu, self.CutID, _translate("Cut"))
        copyItem = wx.MenuItem(menu, self.CopyID, _translate("Copy"))
        pasteItem = wx.MenuItem(menu, self.PasteID, _translate("Paste"))
        deleteItem = wx.MenuItem(menu, self.DeleteID, _translate("Delete"))
        selectItem = wx.MenuItem(menu, self.SelectAllID, _translate("Select All"))

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

    def toggleCommentLines(self):

        codeType = "Py"
        if hasattr(self, "codeType"):
            codeType = self.codeType

        startText, endText = self._GetPositionsBoundingSelectedLines()
        nLines = len(self._GetSelectedLineNumbers())
        nHashtags = self.HashtagCounter(self.GetTextRange(startText, endText))
        passDec = False # pass decision - only pass  if line is blank
        # Test decision criteria, and catch division errors
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
            self.SetSelection(
                self.GetCurrentPos(),
                self.GetLineEndPosition(self.GetCurrentLine()))

    def smartIdentThisLine(self):

        codeType = "Py"
        if hasattr(self, "codeType"):
            codeType = self.codeType

        startLineNum = self.LineFromPosition(self.GetSelectionStart())
        endLineNum = self.LineFromPosition(self.GetSelectionEnd())
        prevLine = self.GetLine(startLineNum - 1)
        prevIndent = self.GetLineIndentation(startLineNum - 1)
        signal = {'Py': ':', 'JS': '{'}

        # set the indent
        self.SetLineIndentation(startLineNum, prevIndent)
        self.VCHome()

        # check for a colon (Python) or curly brace (JavaScript) to signal an indent
        prevLogical = prevLine.split(self._commentType[codeType])[0]
        prevLogical = prevLogical.strip()
        if len(prevLogical) > 0 and prevLogical[-1] == signal[codeType]:
            self.CmdKeyExecute(wx.stc.STC_CMD_TAB)
        elif len(prevLogical) > 0 and prevLogical[-1] == '}' and codeType == 'JS':
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
        self.BeginUndoAction()
        for lineNum in range(startLineNum, endLineNum + 1):
            thisIndent = self.GetLineIndentation(lineNum)
            self.SetLineIndentation(lineNum, thisIndent + incr)
        self.EndUndoAction()

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
        self.BeginUndoAction()
        for lineN in range(startLineNum, endLineNum + 1):
            newIndent = self.GetLineIndentation(lineN) + howFar
            if newIndent < 0:
                newIndent = 0
            self.SetLineIndentation(lineN, newIndent)
        self.EndUndoAction()

    def Paste(self, event=None):
        dataObj = wx.TextDataObject()
        clip = wx.Clipboard().Get()
        clip.Open()
        success = clip.GetData(dataObj)
        clip.Close()
        if success:
            txt = dataObj.GetText()
            self.ReplaceSelection(txt.replace("\r\n", "\n").replace("\r", "\n"))

        self.analyseScript()

    def analyseScript(self):
        """Analyse the script."""
        pass

    @property
    def edgeGuideVisible(self):
        return self.GetEdgeMode() != wx.stc.STC_EDGE_NONE

    @edgeGuideVisible.setter
    def edgeGuideVisible(self, value):
        if value is True:
            self.SetEdgeMode(wx.stc.STC_EDGE_LINE)
        else:
            self.SetEdgeMode(wx.stc.STC_EDGE_NONE)

    @property
    def edgeGuideColumn(self):
        return self.GetEdgeColumn()

    @edgeGuideColumn.setter
    def edgeGuideColumn(self, value):
        self.SetEdgeColumn(value)

    # def _applyAppTheme(self, target=None):
    #     """Overrides theme change from ThemeMixin.
    #     Don't call - this is called at the end of theme.setter"""
    #     # ThemeMixin._applyAppTheme()  # only needed for children
    #     spec = ThemeMixin.codeColors
    #     base = spec['base']
    #
    #     # Check for language specific spec
    #     if self.GetLexer() in self.lexers:
    #         lexer = self.lexers[self.GetLexer()]
    #     else:
    #         lexer = 'invlex'
    #     if lexer in spec:
    #         # If there is lang specific spec, delete subkey...
    #         lang = spec[lexer]
    #         del spec[lexer]
    #         #...and append spec to root, overriding any generic spec
    #         spec.update({key: lang[key] for key in lang})
    #     else:
    #         lang = {}
    #
    #     # Override base font with user spec if present
    #     key = 'outputFont' if isinstance(self, wx.py.shell.Shell) else 'codeFont'
    #     if prefs.coder[key] != "From theme...":
    #         base['font'] = prefs.coder[key]
    #
    #     # Pythonise the universal data (hex -> rgb, tag -> wx int)
    #     invalid = []
    #     for key in spec:
    #         # Check that key is in tag list and full spec is defined, discard if not
    #         if key in self.tags \
    #                 and all(subkey in spec[key] for subkey in ['bg', 'fg', 'font']):
    #             spec[key]['bg'] = self.hex2rgb(spec[key]['bg'], base['bg'])
    #             spec[key]['fg'] = self.hex2rgb(spec[key]['fg'], base['fg'])
    #             if not spec[key]['font']:
    #                 spec[key]['font'] = base['font']
    #             spec[key]['size'] = int(self.prefs['codeFontSize'])
    #         else:
    #             invalid += [key]
    #     for key in invalid:
    #         del spec[key]
    #     # Set style for undefined lexers
    #     for key in [getattr(wx._stc, item) for item in dir(wx._stc) if item.startswith("STC_LEX")]:
    #         self.StyleSetBackground(key, base['bg'])
    #         self.StyleSetForeground(key, base['fg'])
    #         self.StyleSetSpec(key, "face:%(font)s,size:%(size)d" % base)
    #     # Set style from universal data
    #     for key in spec:
    #         if self.tags[key] is not None:
    #             self.StyleSetBackground(self.tags[key], spec[key]['bg'])
    #             self.StyleSetForeground(self.tags[key], spec[key]['fg'])
    #             self.StyleSetSpec(self.tags[key], "face:%(font)s,size:%(size)d" % spec[key])
    #     # Apply keywords
    #     for level, val in self.lexkw.items():
    #         self.SetKeyWords(level, " ".join(val))
    #
    #     # Make sure there's some spec for margins
    #     if 'margin' not in spec:
    #         spec['margin'] = base
    #     # Set margin colours to match linenumbers if set
    #     if 'margin' in spec:
    #         mar = spec['margin']['bg']
    #     else:
    #         mar = base['bg']
    #     self.SetFoldMarginColour(True, mar)
    #     self.SetFoldMarginHiColour(True, mar)
    #
    #     # Make sure there's some spec for caret
    #     if 'caret' not in spec:
    #         spec['caret'] = base
    #     # Set caret colour
    #     self.SetCaretForeground(spec['caret']['fg'])
    #     self.SetCaretLineBackground(spec['caret']['bg'])
    #     self.SetCaretWidth(1 + ('bold' in spec['caret']['font']))
    #
    #     # Make sure there's some spec for selection
    #     if 'select' not in spec:
    #         spec['select'] = base
    #         spec['select']['bg'] = self.shiftColour(base['bg'], 30)
    #     # Set selection colour
    #     self.SetSelForeground(True, spec['select']['fg'])
    #     self.SetSelBackground(True, spec['select']['bg'])
    #
    #     # Set wrap point
    #     self.edgeGuideColumn = self.prefs['edgeGuideColumn']
    #     self.edgeGuideVisible = self.edgeGuideColumn > 0
    #
    #     # Set line spacing
    #     spacing = min(int(self.prefs['lineSpacing'] / 2), 64) # Max out at 64
    #     self.SetExtraAscent(spacing)
    #     self.SetExtraDescent(spacing)
