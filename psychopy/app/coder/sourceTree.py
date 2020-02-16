#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for the coder source tree."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function
from collections import deque

import wx
import os
import re


class SourceTreePanel(wx.Panel):
    """Panel for the source tree browser."""
    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self.coder = frame

        # get graphics for toolbars and tree items
        rc = self.coder.paths['resources']
        self._treeImgList = wx.ImageList(16, 16)
        self._treeGfx = {
            'class': self._treeImgList.Add(
                wx.Bitmap(
                    os.path.join(rc, 'coderclass16.png'), wx.BITMAP_TYPE_PNG)),
            'def': self._treeImgList.Add(
                wx.Bitmap(
                    os.path.join(rc, 'coderfunc16.png'), wx.BITMAP_TYPE_PNG)),
            'attr': self._treeImgList.Add(
                wx.Bitmap(
                    os.path.join(rc, 'codervar16.png'), wx.BITMAP_TYPE_PNG)),
            'pyModule': self._treeImgList.Add(
                wx.Bitmap(
                    os.path.join(rc, 'coderpython16.png'), wx.BITMAP_TYPE_PNG)),
            'noDoc': self._treeImgList.Add(
                wx.Bitmap(
                    os.path.join(rc, 'docclose16.png'), wx.BITMAP_TYPE_PNG))
            # 'import': self._treeImgList.Add(
            #     wx.Bitmap(os.path.join(rc, 'coderimport16.png'), wx.BITMAP_TYPE_PNG)),
            # 'treeFolderClosed': _treeImgList.Add(
            #     wx.Bitmap(os.path.join(rc, 'folder16.png'), wx.BITMAP_TYPE_PNG)),
            # 'treeFolderOpened': _treeImgList.Add(
            #     wx.Bitmap(os.path.join(rc, 'folder-open16.png'), wx.BITMAP_TYPE_PNG))
        }

        self.SetDoubleBuffered(True)
        # create the source tree control
        self.treeId = wx.NewIdRef()
        self.srcTree = wx.TreeCtrl(
            self,
            self.treeId,
            pos=(0, 0),
            size=wx.Size(300, 300),
            style=wx.TR_HAS_BUTTONS)
        self.srcTree.SetImageList(self._treeImgList)

        # do layout
        szr = wx.BoxSizer(wx.VERTICAL)
        szr.Add(self.srcTree, flag=wx.EXPAND, proportion=1)
        self.SetSizer(szr)

        # bind events
        self.Bind(
            wx.EVT_TREE_ITEM_ACTIVATED, self.OnItemActivate, self.srcTree)
        self.Bind(
            wx.EVT_TREE_ITEM_EXPANDED, self.OnItemExpanded, self.srcTree)
        self.Bind(
            wx.EVT_TREE_ITEM_COLLAPSED, self.OnItemCollapsed, self.srcTree)

    def OnItemActivate(self, evt=None):
        """When a tree item is clicked on."""
        item = evt.GetItem()
        itemData = self.srcTree.GetItemData(item)
        if itemData is not None:
            self.coder.currentDoc.SetFirstVisibleLine(itemData[3] - 2)
            self.coder.currentDoc.GotoLine(itemData[3] - 1)
            #self.coder.currentDoc.SetSTCFocus(True)
            wx.CallAfter(self.coder.currentDoc.SetFocus)
        else:
            evt.Skip()

    def OnItemExpanded(self, evt):
        itemData = self.srcTree.GetItemData(evt.GetItem())
        if itemData is not None:
            self.coder.currentDoc.expandedItems[itemData[:3]] = True

    def OnItemCollapsed(self, evt):
        itemData = self.srcTree.GetItemData(evt.GetItem())
        if itemData is not None:
            self.coder.currentDoc.expandedItems[itemData[:3]] = False

    def GetScrollVert(self):
        """Get the vertical scrolling position fo the tree. This is used to
        keep track of where we are in the tree by the code editor. This prevents
        the tree viewer from moving back to the top when returning to a
        document, which may be jarring for users."""
        return self.srcTree.GetScrollPos(wx.VERTICAL)

    def createPySourceTree(self):
        """Create a Python source tree. This is called when code analysis runs
        and the document type is 'Python'.
        """
        # create the root item which is just the file name
        self.root = self.srcTree.AddRoot(self.coder.currentDoc.filename)
        self.srcTree.SetItemImage(
            self.root, self._treeGfx['pyModule'], wx.TreeItemIcon_Normal)

        # get the tokens for this document
        tokens = parsePyScript(self.coder.currentDoc.GetText())

        # split off imports and definitions, these are treated differently
        # importStmts = []
        defStmts = []
        for tok in tokens:
            # if tok[0] == 'import' or tok[0] == 'from' or tok[0] == 'importas':
            #    if tok[2] == 0:
            #        importStmts.append(tok)
            # else:
                defStmts.append(tok)

        # # create the entry for imports
        # importItemIdx = self.srcTree.AppendItem(root, '<imports>')
        # # keep track of imports already added for grouping
        # importGroups = {}
        # for i, tok in enumerate(importStmts):
        #     if tok[0] == 'import':
        #         itemIdx = self.srcTree.AppendItem(importItemIdx, tok[1])
        #         self.srcTree.SetItemImage(
        #             itemIdx, _treeGfx[tok[0]], wx.TreeItemIcon_Normal)
        #         self.srcTree.SetItemData(itemIdx, tok)
        #     elif tok[0] == 'importas':
        #         itemIdx = self.srcTree.AppendItem(importItemIdx, tok[1])
        #         self.srcTree.SetItemImage(
        #             itemIdx, _treeGfx['import'], wx.TreeItemIcon_Normal)
        #         self.srcTree.SetItemData(itemIdx, tok)
        #         subItemIdx = self.srcTree.AppendItem(itemIdx, tok[-1])
        #         self.srcTree.SetItemImage(
        #             subItemIdx, _treeGfx['attr'], wx.TreeItemIcon_Normal)
        #         self.srcTree.SetItemData(subItemIdx, tok)

        # build the tree for def statements
        nodes = deque([self.root])
        for i, tok in enumerate(defStmts):
            if tok[0] == 'import':
                continue
            # Get the next level of the tree, we use this to determine if we
            # should create a new level or move down a few.
            try:
                lookAheadLevel = defStmts[i + 1][2]
            except IndexError:
                lookAheadLevel = 0

            # add a node
            itemIdx = self.srcTree.AppendItem(nodes[0], tok[1])
            self.srcTree.SetItemImage(
                itemIdx, self._treeGfx[tok[0]], wx.TreeItemIcon_Normal)
            self.srcTree.SetItemData(itemIdx, tok)

            if lookAheadLevel > tok[2]:
                # create a new branch if the next item is at higher indent level
                nodes.appendleft(itemIdx)
            elif lookAheadLevel < tok[2]:
                # remove nodes to match next indent level
                indentDiff = tok[2] - lookAheadLevel
                for _ in range(indentDiff):
                    # check if we need to expand the item we dropped down from
                    itemData = self.srcTree.GetItemData(nodes[0])
                    if itemData is not None:
                        try:
                            if self.coder.currentDoc.expandedItems[itemData[:3]]:
                                self.srcTree.Expand(nodes.popleft())
                        except KeyError:
                            nodes.popleft()

        # clean up expanded items list
        addedItems = [tok[:3] for tok in tokens]
        temp = dict(self.coder.currentDoc.expandedItems)
        for itemData in self.coder.currentDoc.expandedItems.keys():
            if itemData not in addedItems:
                del temp[itemData]
        self.coder.currentDoc.expandedItems = temp

        self.srcTree.Expand(self.root)

    def createItems(self):
        """Walk through all the nodes in the AST and create tree items.
        """
        if self.coder.currentDoc is None:
            return

        self.srcTree.Freeze()
        self.srcTree.DeleteAllItems()

        if self.coder.currentDoc.getFileType() != 'Python':
            root = self.srcTree.AddRoot(
                'Source tree not available for this type of file.')
            self.srcTree.SetItemImage(
                root, self._treeGfx['noDoc'], wx.TreeItemIcon_Normal)
            self.srcTree.Thaw()
            return

        self.createPySourceTree()  # only one for now

        self.srcTree.Thaw()


def parsePyScript(src):
    """Parse a Python script for the source tree viewer.

    Parameters
    ----------
    src : str
        Python source code to parse.

    Returns
    -------
    list
        List of found items.

    """
    foundDefs = []
    for nLine, line in enumerate(src.split('\n')):
        lineno = nLine + 1
        lineFullLen = len(line)
        lineText = line.lstrip()
        lineIndent = int((lineFullLen - len(lineText)) / 4)  # to indent level

        # filter out defs that are nested in if statements
        if nLine > 1 and foundDefs:
            lastIndent = foundDefs[-1][2]
            if lineIndent - lastIndent > 1:
                continue

        # is definition?
        if lineText.startswith('class ') or lineText.startswith('def '):
            # slice off comment
            lineText = lineText.split('#')[0]
            lineTokens = [
                tok.strip() for tok in re.split(' |\(|\)', lineText) if tok]
            defType, defName = lineTokens[:2]
            foundDefs.append((defType, defName, lineIndent, lineno))

        # mdc - holding off on showing attributes and imports for now
        # elif lineText.startswith('import ') and lineIndent == 0:
        #     lineText = lineText.split('#')[0]  # clean the line
        #     # check if we have a regular import statement or an 'as' one
        #     if ' as ' not in lineText:
        #         lineTokens = [
        #             tok.strip() for tok in re.split(
        #                 ' |,', lineText[len('import '):]) if tok]
        #
        #         # create a new import declaration for import if a list
        #         for name in lineTokens:
        #             foundDefs.append(('import', name, lineIndent, lineno))
        #     else:
        #         impStmt = lineText[len('import '):].strip().split(' as ')
        #         name, attrs = impStmt
        #
        #         foundDefs.append(('importas', name, lineIndent, lineno, attrs))
        # elif lineText.startswith('from ') and lineIndent == 0:
        #     pass

    return foundDefs
