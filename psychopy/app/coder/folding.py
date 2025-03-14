#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Functions and classes related to code folding with Scintilla."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx.stc


class CodeEditorFoldingMixin():
    """Mixin for adding code folding functionality to a CodeEditor control.

    """
    def OnMarginClick(self, evt):
        """Event for when a margin is clicked."""
        # fold and unfold as needed
        if evt.GetMargin() == 1:
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
        """Fold all code blocks."""
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


def getFolds(doc):
    """Get the lines and levels of folds found by the Scintilla. This can be
    used to create parsers for the source tree among other things.

    Parameters
    ----------
    doc : wx.stc.StyledText
        Styled text object.

    Returns
    -------
    list
        List of fold levels and line numbers.

    """
    # Go over file and get all the folds.
    foldLines = []
    for lineno in range(doc.GetLineCount()):
        foldLevelFlags = doc.GetFoldLevel(lineno)
        foldLevel = \
            (foldLevelFlags & wx.stc.STC_FOLDLEVELNUMBERMASK) - \
            wx.stc.STC_FOLDLEVELBASE  # offset
        isFoldStart = (foldLevelFlags & wx.stc.STC_FOLDLEVELHEADERFLAG) > 0

        if isFoldStart:
            foldLines.append((foldLevel, lineno))

    return foldLines
