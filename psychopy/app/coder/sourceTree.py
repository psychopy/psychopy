from __future__ import absolute_import, print_function
from collections import deque, OrderedDict

import wx
import wx.stc
import wx.richtext

try:
    from wx import aui
except Exception:
    import wx.lib.agw.aui as aui  # some versions of phoenix

import os
import re

_treeImgList = _treeGfx = None


def _initGraphics(rc):
    """Load graphics needed by the source browser."""
    global _treeImgList, _treeGfx

    _treeImgList = wx.ImageList(16, 16)
    _treeGfx = {
        'class': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'coderclass16.png'), wx.BITMAP_TYPE_PNG)),
        'def': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'coderfunc16.png'), wx.BITMAP_TYPE_PNG)),
        'attr': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'codervar16.png'), wx.BITMAP_TYPE_PNG)),
        'pyModule': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'coderpython16.png'), wx.BITMAP_TYPE_PNG)),
        'import': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'coderimport16.png'), wx.BITMAP_TYPE_PNG)),
        'treeFolderClosed': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'folder16.png'), wx.BITMAP_TYPE_PNG)),
        'treeWindowClass': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'monitor16.png'), wx.BITMAP_TYPE_PNG)),
        'treeFolderOpened': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'folder-open16.png'), wx.BITMAP_TYPE_PNG)),
        'noDoc': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'docclose16.png'), wx.BITMAP_TYPE_PNG)),
        'treeImageStimClass': _treeImgList.Add(
            wx.Bitmap(os.path.join(rc, 'fileimage16.png'), wx.BITMAP_TYPE_PNG))}


class SourceTreePanel(wx.Panel):
    """Panel for the source tree browser."""
    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self.coder = frame

        # get graphics for toolbars and tree items
        rc = self.coder.paths['resources']
        _initGraphics(rc)

        self.SetDoubleBuffered(True)
        # create the source tree control
        self.treeId = wx.NewIdRef()
        self.srcTree = wx.TreeCtrl(
            self,
            self.treeId,
            pos=(0, 0),
            size=wx.Size(300, 300),
            style=wx.TR_HAS_BUTTONS)
        self.srcTree.SetImageList(_treeImgList)

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
        if evt is None:
            evt.Skip()

        item = evt.GetItem()
        itemData = self.srcTree.GetItemData(item)
        if itemData is not None:
            self.coder.currentDoc.SetFirstVisibleLine(itemData[3] - 2)
            self.coder.currentDoc.SetSTCFocus()
        else:
            self.srcTree.Expand(item)

    def OnItemExpanded(self, evt):
        itemData = self.srcTree.GetItemData(evt.GetItem())
        if itemData is not None:
            self.coder.currentDoc.expandedItems[itemData[:3]] = True

    def OnItemCollapsed(self, evt):
        itemData = self.srcTree.GetItemData(evt.GetItem())
        if itemData is not None:
            self.coder.currentDoc.expandedItems[itemData[:3]] = False

    def GetScrollVert(self):
        """Keep track of where we scrolled for the current document. This keeps
        the tree viewer from moving back to the top when returning to a
        document, which may be jarring for users."""
        return self.srcTree.GetScrollPos(wx.VERTICAL)

    def createPySourceTree(self):
        """Create a Python source tree."""
        # create the root item which is just the file name
        root = self.srcTree.AddRoot(self.coder.currentDoc.filename)
        self.srcTree.SetItemImage(
            root, _treeGfx['pyModule'], wx.TreeItemIcon_Normal)

        # get the tokens for this document
        tokens = parsePyScript(self.coder.currentDoc.GetText())

        # split off imports and definitions, these are treated differently
        importStmts = []
        defStmts = []
        for tok in tokens:
            if tok[0] == 'import' or tok[0] == 'from':
                if tok[2] == 0:
                    importStmts.append(tok)
            else:
                defStmts.append(tok)

        # create the entry for imports
        importItemIdx = self.srcTree.AppendItem(root, '<imports>')
        # keep track of imports already added for grouping
        importGroups = {}
        for i, tok in enumerate(importStmts):
            if tok[0] == 'import':
                for name in tok[1]:
                    itemIdx = self.srcTree.AppendItem(importItemIdx, name)
                    self.srcTree.SetItemImage(
                        itemIdx, _treeGfx[tok[0]], wx.TreeItemIcon_Normal)
                    self.srcTree.SetItemData(itemIdx, tok)

        # build the tree for def statements
        nodes = deque([root])
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
                itemIdx, _treeGfx[tok[0]], wx.TreeItemIcon_Normal)
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

        self.srcTree.Expand(root)

    def createItems(self):
        """Walk through all the nodes in the AST and create tree items.
        """
        if self.coder.currentDoc is None:
            return

        self.srcTree.Freeze()
        self.srcTree.DeleteAllItems()

        if self.coder.currentDoc.getFileType() != 'python':
            root = self.srcTree.AddRoot(
                'Source tree not available for this type of file.')
            self.srcTree.SetItemImage(
                root, _treeGfx['noDoc'], wx.TreeItemIcon_Normal)
            self.srcTree.Thaw()
            return

        self.createPySourceTree()  # only one for now

        self.srcTree.Thaw()

    def updateSourceTree(self):
        """Update the source tree using the parsed AST from the active document.
        """
        self.createItems()


def parsePyScript(src):
    """Parse a Python script for the source tree viewer."""
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
            # slice off things after the definition
            lineText = lineText.split(':')[0]
            lineTokens = [
                tok.strip() for tok in re.split(' |\(|\)', lineText) if tok]
            defType, defName = lineTokens[:2]
            foundDefs.append((defType, defName, lineIndent, lineno))
        elif lineText.startswith('import '):
            lineText = lineText.split('#')[0]

            if ' as ' not in lineText:
                lineTokens = [
                    tok.strip() for tok in re.split(
                        ' |,', lineText[len('import '):]) if tok]
            else:
                lineTokens = [lineText[len('import '):].strip()]

            foundDefs.append(('import', lineTokens, lineIndent, lineno))

    return foundDefs
