#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for the document list browser panel."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function
from ..themes import ThemeMixin

import wx
import wx.stc
import os


class DocumentTreePanel(wx.Panel):
    """Panel to show/list currently opened documents.

    Documents are displayed in a tree where root items are folders and files
    appear under them. Clicking on files will switch to them in the editor.
    Files and folders are automatically sorted by name in the view.

    """
    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self.coder = frame
        self.app = frame.app

        # double buffered better rendering except if retina
        self.SetDoubleBuffered(self.coder.IsDoubleBuffered())

        # create the source tree control
        self.treeId = wx.NewIdRef()
        self.docTree = wx.TreeCtrl(
            self,
            self.treeId,
            pos=(0, 0),
            size=wx.Size(300, 300),
            style=wx.TR_HAS_BUTTONS | wx.BORDER_NONE | wx.TR_HIDE_ROOT)

        # keep track of the items associated with each file
        self.fileItems = dict()

        # do layout
        szr = wx.BoxSizer(wx.VERTICAL)
        szr.Add(self.docTree, flag=wx.EXPAND, proportion=1)
        self.SetSizer(szr)

        # bind events
        self.Bind(
            wx.EVT_TREE_ITEM_ACTIVATED, self.OnItemActivate, self.docTree)
        self.Bind(
            wx.EVT_TREE_SEL_CHANGED, self.OnItemSelected, self.docTree)

        self._applyAppTheme()

    def _applyAppTheme(self, target=None):
        cs = ThemeMixin.appColors
        iconCache = self.app.iconCache
        self.docTree.SetOwnBackgroundColour(cs['tab_bg'])
        self.docTree.SetOwnForegroundColour(cs['text'])

        # get graphics for toolbars and tree items
        self._treeImgList = wx.ImageList(16, 16)
        self._treeGfx = {
            'folder': self._treeImgList.Add(
                iconCache.getBitmap(name='folder16.png', size=16)),
            'pyFile': self._treeImgList.Add(
                iconCache.getBitmap(name='coderpython16.png', size=16)),
            'txtFile': self._treeImgList.Add(
                iconCache.getBitmap(name='fileunknown16.png', size=16))
        }
        self.docTree.SetImageList(self._treeImgList)

    def OnItemSelected(self, evt=None):
        """When a tree item is clicked on."""
        item = evt.GetItem()
        itemData = self.docTree.GetItemData(item)
        if itemData is not None:
            if itemData != self.coder.currentDoc:
                self.coder.setCurrentDoc(itemData)
                wx.CallAfter(self.coder.currentDoc.SetFocus)
        else:
            evt.Skip()

    def OnItemActivate(self, evt=None):
        """When a tree item is clicked on."""
        evt.Skip()

    def selectDocument(self, filename):
        """Highlight a document in the tree."""
        if self.fileItems:
            try:
                self.docTree.SelectItem(self.fileItems[filename], True)
            except KeyError:
                pass

    def createDocTree(self):
        """Update the items for the document tree."""
        openFiles = self.coder.getOpenFilenames()
        if openFiles is None:
            return   # nop if empty

        # create the root item which is just the file name
        self.docTree.Freeze()
        self.docTree.DeleteAllItems()
        self.root = self.docTree.AddRoot("Open Documents")

        docTree = dict()

        # start building the source tree
        for docPath in openFiles:
            if os.path.isabs(docPath):
                pathName, fileName = os.path.split(docPath)
            else:
                fileName = docPath
                pathName = 'Untitled'

            # check if a folder is
            if pathName not in docTree.keys():
                docTree[pathName] = [fileName]
            else:
                docTree[pathName].append(fileName)

        # create tree items
        self.fileItems = dict()
        for pathName in sorted(docTree.keys()):
            folderRoot = self.docTree.AppendItem(self.root, pathName)
            self.docTree.SetItemImage(
                folderRoot, self._treeGfx['folder'],
                wx.TreeItemIcon_Normal)

            for fileName in sorted(docTree[pathName]):
                item = self.docTree.AppendItem(folderRoot, fileName)
                fileLower = fileName.lower()

                # pick the graphics to use for the file icon
                if fileLower.endswith('.py'):
                    img = self._treeGfx['pyFile']
                else:
                    img = self._treeGfx['txtFile']

                self.docTree.SetItemImage(
                    item, img,
                    wx.TreeItemIcon_Normal)

                if pathName != 'Untitled':
                    fullPath = os.path.join(pathName, fileName)
                else:
                    fullPath = fileName

                self.docTree.SetItemData(item, fullPath)
                self.fileItems[fullPath] = item

            self.docTree.Expand(folderRoot)

        self.docTree.Thaw()
