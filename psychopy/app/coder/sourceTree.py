#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for the coder source tree."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from collections import deque
from ..themes import icons, colors, handlers

import wx
import wx.stc
import os
import re
import string


CPP_DEFS = ['void', 'int', 'float', 'double', 'short', 'byte', 'struct', 'enum',
            'function', 'async function', 'class']  # javascript tokens
PYTHON_DEFS = ['def', 'class']


class SourceTreePanel(wx.Panel, handlers.ThemeMixin):
    """Panel for the source tree browser."""
    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self.coder = frame
        self.app = frame.app
        self.tabIcon = "coderclass"

        # double buffered better rendering except if retina
        self.SetDoubleBuffered(self.coder.IsDoubleBuffered())

        # create the source tree control
        self.treeId = wx.NewIdRef()
        self.srcTree = wx.TreeCtrl(
            self,
            self.treeId,
            pos=(0, 0),
            size=wx.Size(300, 300),
            style=wx.TR_HAS_BUTTONS | wx.BORDER_NONE)

        # do layout
        szr = wx.BoxSizer(wx.VERTICAL)
        szr.Add(self.srcTree, flag=wx.EXPAND, proportion=1)
        self.SetSizer(szr)

        # bind events
        self.Bind(
            wx.EVT_TREE_ITEM_ACTIVATED, self.OnItemActivate, self.srcTree)
        self.Bind(
            wx.EVT_TREE_SEL_CHANGED, self.OnItemSelected, self.srcTree)
        self.Bind(
            wx.EVT_TREE_ITEM_EXPANDED, self.OnItemExpanded, self.srcTree)
        self.Bind(
            wx.EVT_TREE_ITEM_COLLAPSED, self.OnItemCollapsed, self.srcTree)

        self._applyAppTheme()

    def _applyAppTheme(self):
        self.srcTree.SetOwnBackgroundColour(colors.app['tab_bg'])
        self.srcTree.SetOwnForegroundColour(colors.app['text'])

        # get graphics for toolbars and tree items
        self._treeImgList = wx.ImageList(16, 16)
        self._treeGfx = {
            'class': self._treeImgList.Add(
                icons.ButtonIcon('coderclass', size=16).bitmap),
            'def': self._treeImgList.Add(
                icons.ButtonIcon('coderfunc', size=16).bitmap),
            'attr': self._treeImgList.Add(
                icons.ButtonIcon('codervar', size=16).bitmap),
            'pyModule': self._treeImgList.Add(
                icons.ButtonIcon('coderpython', size=16).bitmap),
            'jsModule': self._treeImgList.Add(
                icons.ButtonIcon('coderjs', size=16).bitmap),
            'noDoc': self._treeImgList.Add(
                icons.ButtonIcon('docclose', size=16).bitmap)
            # 'import': self._treeImgList.Add(
            #     wx.Bitmap(os.path.join(rc, 'coderimport16.png'), wx.BITMAP_TYPE_PNG)),
            # 'treeFolderClosed': _treeImgList.Add(
            #     wx.Bitmap(os.path.join(rc, 'folder16.png'), wx.BITMAP_TYPE_PNG)),
            # 'treeFolderOpened': _treeImgList.Add(
            #     wx.Bitmap(os.path.join(rc, 'folder-open16.png'), wx.BITMAP_TYPE_PNG))
        }
        # for non-python functions
        self._treeGfx['function'] = self._treeGfx['def']
        self.srcTree.SetImageList(self._treeImgList)

    def OnItemSelected(self, evt=None):
        """When a tree item is clicked on."""
        item = evt.GetItem()
        itemData = self.srcTree.GetItemData(item)
        if itemData is not None:
            self.coder.currentDoc.SetFirstVisibleLine(itemData[2] - 1)
            self.coder.currentDoc.GotoLine(itemData[2])
            wx.CallAfter(self.coder.currentDoc.SetFocus)
        else:
            evt.Skip()

    def OnItemActivate(self, evt=None):
        """When a tree item is clicked on."""
        evt.Skip()

    def OnItemExpanded(self, evt):
        itemData = self.srcTree.GetItemData(evt.GetItem())
        if itemData is not None:
            self.coder.currentDoc.expandedItems[itemData] = True

    def OnItemCollapsed(self, evt):
        itemData = self.srcTree.GetItemData(evt.GetItem())
        if itemData is not None:
            self.coder.currentDoc.expandedItems[itemData] = False

    def GetScrollVert(self):
        """Get the vertical scrolling position for the tree. This is used to
        keep track of where we are in the tree by the code editor. This prevents
        the tree viewer from moving back to the top when returning to a
        document, which may be jarring for users."""
        return self.srcTree.GetScrollPos(wx.VERTICAL)

    def refresh(self):
        """Update the source tree using the current document. Examines all the
        fold levels and tries to create a tree with them."""
        doc = self.coder.currentDoc
        if doc is None:
            return

        # check if we can parse this file
        if self.coder.currentDoc.GetLexer() not in [wx.stc.STC_LEX_PYTHON,
                                                    wx.stc.STC_LEX_CPP]:
            self.srcTree.DeleteAllItems()
            root = self.srcTree.AddRoot(
                'Source tree unavailable for this file type.')
            self.srcTree.SetItemImage(
                root, self._treeGfx['noDoc'],
                wx.TreeItemIcon_Normal)
            return

        # Go over file and get all the folds.
        # We do this instead of parsing the files ourselves since Scintilla
        # lexers are probably better than anything *I* can come up with. -mdc
        foldLines = []
        for lineno in range(doc.GetLineCount()):
            foldLevelFlags = doc.GetFoldLevel(lineno)
            foldLevel = \
                (foldLevelFlags & wx.stc.STC_FOLDLEVELNUMBERMASK) - \
                wx.stc.STC_FOLDLEVELBASE  # offset
            isFoldStart = (foldLevelFlags & wx.stc.STC_FOLDLEVELHEADERFLAG) > 0

            if isFoldStart:
                foldLines.append(
                    (foldLevel, lineno, doc.GetLineText(lineno).lstrip()))

        # Build the trees for the given language, this is a dictionary which
        # represents the hierarchy of the document. This system is dead simple,
        # determining what's a function/class based on what the Scintilla lexer
        # thinks should be folded. This is really fast and works most of the
        # time (perfectly for Python). In the future, we may need to specify
        # additional code to handle languages which don't have strict whitespace
        # requirements.
        #
        currentLexer = self.coder.currentDoc.GetLexer()
        if currentLexer == wx.stc.STC_LEX_CPP:
            stripChars = string.whitespace
            kwrds = CPP_DEFS
        elif currentLexer == wx.stc.STC_LEX_PYTHON:
            stripChars = string.whitespace + ':'
            kwrds = PYTHON_DEFS
        else:
            return  # do nothing here

        indent = doc.GetIndent()
        # filter out only definitions
        defineList = []
        lastItem = None
        for df in foldLines:
            lineText = doc.GetLineText(df[1]).lstrip()
            # work out which keyword the line starts with
            kwrd = None
            for i in kwrds:
                i += " "  # add a space to avoid e.g. `defaultKeyboard` being read as a keyword
                if lineText.startswith(i):
                    kwrd = i
            # skip if it starts with no keywords
            if kwrd is None:
                continue

            if lastItem is not None:
                if df[0] > lastItem[3] + indent:
                    continue

            # slice off comment
            lineText = lineText.split('#')[0]
            # split into tokens
            lineTokens = [
                tok.strip(stripChars) for tok in re.split(
                    r' |\(|\)', lineText) if tok]

            # take value before keyword end as def type, value after as def name
            kwrdEnd = len(re.findall(r' |\(|\)', kwrd))
            try:
                defType = lineTokens[kwrdEnd-1]
                defName = lineTokens[kwrdEnd]
            except ValueError:
                # if for some reason the line is valid but cannot be parsed, ignore it
                continue

            lastItem = (defType, defName, df[1], df[0])
            defineList.append(lastItem)

        self.createSourceTree(defineList, doc.GetIndent())
        self.srcTree.Refresh()

    def createSourceTree(self, foldDefs, indents=4):
        """Create a Python source tree. This is called when code analysis runs
        and the document type is 'Python'.
        """
        # create the root item which is just the file name
        self.srcTree.Freeze()
        self.srcTree.DeleteAllItems()
        self.root = self.srcTree.AddRoot(
            os.path.split(self.coder.currentDoc.filename)[-1])
        if self.coder.currentDoc.filename.endswith('.py'):
            self.srcTree.SetItemImage(
                self.root, self._treeGfx['pyModule'], wx.TreeItemIcon_Normal)
        elif self.coder.currentDoc.filename.endswith('.js'):
            self.srcTree.SetItemImage(
                self.root, self._treeGfx['jsModule'], wx.TreeItemIcon_Normal)
        else:
            self.srcTree.SetItemImage(
                self.root, self._treeGfx['noDoc'], wx.TreeItemIcon_Normal)

        # start building the source tree
        nodes = deque([self.root])
        for i, foldLine in enumerate(foldDefs):
            defType, defName, lineno, foldLevel = foldLine
            foldLevel = int(foldLevel / indents)
            # Get the next level of the tree, we use this to determine if we
            # should create a new level or move down a few.
            try:
                lookAheadLevel = int(foldDefs[i + 1][3] / indents)
            except IndexError:
                lookAheadLevel = 0

            try:
                # catch an error if the deque is empty, this means something
                # went wrong
                itemIdx = self.srcTree.AppendItem(nodes[0], defName)
            except IndexError:
                self.srcTree.DeleteAllItems()
                root = self.srcTree.AddRoot(
                    'Error parsing current document.')
                self.srcTree.SetItemImage(
                    root, self._treeGfx['noDoc'],
                    wx.TreeItemIcon_Normal)
                return

            self.srcTree.SetItemImage(
                itemIdx, self._treeGfx.get(defType, self._treeGfx['function']),
                wx.TreeItemIcon_Normal)
            self.srcTree.SetItemData(itemIdx, foldLine)

            if lookAheadLevel > foldLevel:
                # create a new branch if the next item is at higher indent level
                nodes.appendleft(itemIdx)
            elif lookAheadLevel < foldLevel:
                # remove nodes to match next indent level
                indentDiff = foldLevel - lookAheadLevel
                for _ in range(int(indentDiff)):
                    # check if we need to expand the item we dropped down from
                    itemData = self.srcTree.GetItemData(nodes[0])
                    if itemData is not None:
                        try:
                            if self.coder.currentDoc.expandedItems[itemData]:
                                self.srcTree.Expand(nodes.popleft())
                            else:
                                nodes.popleft()
                        except KeyError:
                            if len(nodes) > 1:
                                nodes.popleft()
                            else:
                                self.srcTree.DeleteAllItems()
                                root = self.srcTree.AddRoot(
                                    'Error parsing current document.')
                                self.srcTree.SetItemImage(
                                    root, self._treeGfx['noDoc'],
                                    wx.TreeItemIcon_Normal)
                                return

        # clean up expanded items list
        temp = dict(self.coder.currentDoc.expandedItems)
        for itemData in self.coder.currentDoc.expandedItems.keys():
            if itemData not in foldDefs:
                del temp[itemData]
        self.coder.currentDoc.expandedItems = temp

        self.srcTree.Expand(self.root)
        self.srcTree.Thaw()
