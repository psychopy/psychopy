#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for the coder source tree."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function
from collections import deque
from ..themes import ThemeMixin
from psychopy.app.coder.folding import getFolds

import wx
import wx.stc
import os, sys
import re


class SourceTreePanel(wx.Panel):
    """Panel for the source tree browser."""
    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self.coder = frame
        self.app = frame.app

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

    def _applyAppTheme(self, target=None):
        cs = ThemeMixin.appColors
        iconCache = self.app.iconCache
        self.srcTree.SetOwnBackgroundColour(cs['tab_bg'])
        self.srcTree.SetOwnForegroundColour(cs['text'])

        # get graphics for toolbars and tree items
        self._treeImgList = wx.ImageList(16, 16)
        self._treeGfx = {
            'class': self._treeImgList.Add(
                iconCache.getBitmap(name='coderclass.png', size=16)),
            'def': self._treeImgList.Add(
                iconCache.getBitmap(name='coderfunc.png', size=16)),
            'attr': self._treeImgList.Add(
                iconCache.getBitmap(name='codervar.png', size=16)),
            'pyModule': self._treeImgList.Add(
                iconCache.getBitmap(name='coderpython.png', size=16)),
            'noDoc': self._treeImgList.Add(
                iconCache.getBitmap(name='docclose.png', size=16))
            # 'import': self._treeImgList.Add(
            #     wx.Bitmap(os.path.join(rc, 'coderimport16.png'), wx.BITMAP_TYPE_PNG)),
            # 'treeFolderClosed': _treeImgList.Add(
            #     wx.Bitmap(os.path.join(rc, 'folder16.png'), wx.BITMAP_TYPE_PNG)),
            # 'treeFolderOpened': _treeImgList.Add(
            #     wx.Bitmap(os.path.join(rc, 'folder-open16.png'), wx.BITMAP_TYPE_PNG))
        }
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
        """Get the vertical scrolling position fo the tree. This is used to
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
        if self.coder.currentDoc.GetLexer() not in [wx.stc.STC_LEX_PYTHON]:
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

        # build the trees for the given language
        if self.coder.currentDoc.GetLexer() == wx.stc.STC_LEX_PYTHON:
            indent = doc.GetIndent()
            # filter out only definitions
            defineList = []
            lastItem = None
            for df in foldLines:
                lineText = doc.GetLineText(df[1]).lstrip()
                if not (lineText.startswith('class ') or
                        lineText.startswith('def ')):
                    continue

                if lastItem is not None:
                    if df[0] > lastItem[3] + indent:
                        continue

                # slice off comment
                lineText = lineText.split('#')[0]
                lineTokens = [
                    tok.strip() for tok in re.split(' |\(|\)', lineText) if tok]
                defType, defName = lineTokens[:2]

                lastItem = (defType, defName, df[1], df[0])
                defineList.append(lastItem)

            self.createPySourceTree(defineList, doc.GetIndent())

        self.srcTree.Refresh()

    def createPySourceTree(self, foldDefs, indents=4):
        """Create a Python source tree. This is called when code analysis runs
        and the document type is 'Python'.
        """
        # create the root item which is just the file name
        self.srcTree.Freeze()
        self.srcTree.DeleteAllItems()
        self.root = self.srcTree.AddRoot(
            os.path.split(self.coder.currentDoc.filename)[-1])
        self.srcTree.SetItemImage(
            self.root, self._treeGfx['pyModule'], wx.TreeItemIcon_Normal)

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
                itemIdx, self._treeGfx[defType], wx.TreeItemIcon_Normal)
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
