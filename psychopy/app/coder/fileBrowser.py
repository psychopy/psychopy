#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for the coder file browser pane."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

try:
    from wx import aui
except Exception:
    import wx.lib.agw.aui as aui  # some versions of phoenix

import os
import sys
import subprocess
import imghdr
from ..themes import ThemeMixin
from psychopy.localization import _translate

# enums for file types
FOLDER_TYPE_NORMAL = 0
FOLDER_TYPE_NAV = 1
FOLDER_TYPE_NO_ACCESS = 2

# IDs for menu events
ID_GOTO_BROWSE = wx.NewId()
ID_GOTO_CWD = wx.NewId()
ID_GOTO_FILE = wx.NewId()


def convertBytes(nbytes):
    """Convert a size in bytes to a string."""
    if nbytes >= 1e9:
        return '{:.1f} GB'.format(nbytes / 1e9)
    elif nbytes >= 1e6:
        return '{:.1f} MB'.format(nbytes / 1e6)
    elif nbytes >= 1e3:
        return '{:.1f} KB'.format(nbytes / 1e3)
    else:
        return '{:.1f} B'.format(nbytes)


class FolderItemData(object):
    """Class representing a folder item in the file browser."""
    __slots__ = ['name', 'abspath', 'basename']
    def __init__(self, name, abspath, basename):
        self.name = name
        self.abspath = abspath
        self.basename = basename


class FileItemData(object):
    """Class representing a file item in the file browser."""
    __slots__ = ['name', 'abspath', 'basename', 'fsize', 'mod']
    def __init__(self, name, abspath, basename, fsize, mod):
        self.name = name
        self.abspath = abspath
        self.basename = basename
        self.fsize = fsize
        self.mod = mod


class FileBrowserListCtrl(ListCtrlAutoWidthMixin, wx.ListCtrl):
    """Custom list control for the file browser."""

    def __init__(self, parent, id, pos, size, style):
        wx.ListCtrl.__init__(self,
                             parent,
                             id,
                             pos,
                             size,
                             style=style)
        ListCtrlAutoWidthMixin.__init__(self)

    def _applyAppTheme(self, target=None):
        cs = ThemeMixin.appColors
        self.SetBackgroundColour(wx.Colour(cs['frame_bg']))
        self.SetForegroundColour(wx.Colour(cs['text']))


class FileBrowserPanel(wx.Panel):
    """Panel for a file browser.
    """
    fileImgExt = {
            "..": 'dirup16.png',
            "\\": 'folder16.png',
            ".?": 'fileunknown16.png',
            ".csv": 'filecsv16.png',
            ".xlsx": 'filecsv16.png',
            ".xls": 'filecsv16.png',
            ".tsv": 'filecsv16.png',
            ".png": 'fileimage16.png',
            ".jpeg": 'fileimage16.png',
            ".jpg": 'fileimage16.png',
            ".bmp": 'fileimage16.png',
            ".tiff": 'fileimage16.png',
            ".tif": 'fileimage16.png',
            ".ppm": 'fileimage16.png',
            ".gif": 'fileimage16.png',
            ".py": 'coderpython16.png'
        }

    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent, -1, style=wx.BORDER_NONE)
        self.parent = parent
        self.coder = frame
        self.app = frame.app
        self.currentPath = None
        self.selectedItem = None
        self.isSubDir = False
        self.fileImgList = None  # will be a wx ImageList to store icons
        self.pathData = {}
        # create the toolbar
        szrToolbar = wx.BoxSizer(wx.HORIZONTAL)
        self.toolBar = wx.ToolBar(
            self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
            aui.AUI_TB_HORZ_LAYOUT | aui.AUI_TB_HORZ_TEXT | wx.BORDER_NONE |
            wx.TB_FLAT | wx.TB_NODIVIDER)
        self.toolBar.AdjustForLayoutDirection(16, 300, 300)
        self.toolBar.SetToolBitmapSize((21, 16))
        self.Bind(wx.EVT_MENU, self.OnBrowse, id=ID_GOTO_BROWSE)
        self.Bind(wx.EVT_MENU, self.OnGotoCWD, id=ID_GOTO_CWD)
        self.Bind(wx.EVT_MENU, self.OnGotoFileLocation, id=ID_GOTO_FILE)

        szrToolbar.Add(self.toolBar, 1, flag=wx.ALL | wx.EXPAND)

        # create an address bar
        self.lblDir = wx.StaticText(self, label=_translate("Directory:"))
        self.txtAddr = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)

        # create the source tree control
        self.flId = wx.NewIdRef()
        self.fileList = FileBrowserListCtrl(
            self,
            self.flId,
            pos=(0, 0),
            size=wx.Size(300, 300),
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_NONE |
                  wx.LC_NO_HEADER)
        # bind events for list control
        self.Bind(
            wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.fileList)
        self.Bind(
            wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated, self.fileList)
        self.Bind(
            wx.EVT_TEXT_ENTER, self.OnAddrEnter, self.txtAddr)

        # do layout
        szrAddr = wx.BoxSizer(wx.HORIZONTAL)
        szrAddr.Add(
            self.lblDir, 0, flag=wx.RIGHT | wx.ALIGN_CENTRE_VERTICAL, border=5)
        szrAddr.Add(self.txtAddr, 1, flag=wx.ALIGN_CENTRE_VERTICAL)
        szr = wx.BoxSizer(wx.VERTICAL)
        szr.Add(szrToolbar, 0, flag=wx.EXPAND | wx.ALL)
        szr.Add(szrAddr, 0, flag=wx.EXPAND | wx.ALL, border=5)
        szr.Add(self.fileList, 1, flag=wx.EXPAND)
        self.SetSizer(szr)
        self.makeFileImgIcons()
        self.makeTools()

        # add columns
        self.fileList.InsertColumn(0, "Name")
        #self.fileList.InsertColumn(1, "Size", wx.LIST_FORMAT_LEFT)
        #self.fileList.InsertColumn(2, "Modified")
        self.fileList.SetColumnWidth(0, 280)
        #self.fileList.SetColumnWidth(1, 80)
        #self.fileList.SetColumnWidth(2, 100)

        self.gotoDir(os.getcwd())

    def _applyAppTheme(self, target=None):
        cs = ThemeMixin.appColors
        # Set background for Directory bar
        self.SetBackgroundColour(wx.Colour(cs['tab_bg']))
        self.SetForegroundColour(wx.Colour(cs['text']))
        self.fileList._applyAppTheme()
        self.toolBar.SetBackgroundColour(cs['tab_bg'])
        self.toolBar.SetForegroundColour(cs['text'])
        self.makeFileImgIcons()
        ThemeMixin._applyAppTheme(self.coder, self.txtAddr)
        self.lblDir.SetForegroundColour(ThemeMixin.codeColors['base']['fg'])


    def makeFileImgIcons(self):

        iconCache = self.app.iconCache
        # handles for icon graphics in the image list
        self.fileImgInds = {}
        if self.fileImgList:
            self.fileImgList.RemoveAll()
        else:
            self.fileImgList = wx.ImageList(16, 16)
        for key in self.fileImgExt:
            self.fileImgInds[key] = self.fileImgList.Add(
                    iconCache.getBitmap(name=self.fileImgExt[key],
                                        theme=ThemeMixin.icons,
                                        ))
        self.fileList.SetImageList(self.fileImgList, wx.IMAGE_LIST_SMALL)
        self.Update()

    def makeTools(self):

        iconCache = self.app.iconCache
        iconSize = 16
        # Load in icons for toolbars
        # Redraw toolbar buttons
        self.newFolderTool = iconCache.makeBitmapButton(
                self,
                filename='foldernew',
                name='foldernew',
                label=_translate(
                        'New Folder'),
                toolbar=self.toolBar,
                tip=_translate(
                        "Create a new folder in the current folder"),
                size=iconSize)
        self.renameTool = iconCache.makeBitmapButton(
                self, filename='rename',
                name='rename',
                label=_translate('Rename'),
                toolbar=self.toolBar,
                tip=_translate(
                        "Rename the selected folder or file"),
                size=iconSize)
        self.deleteTool = iconCache.makeBitmapButton(
                self, filename='delete',
                name='delete',
                label=_translate('Delete'),
                toolbar=self.toolBar,
                tip=_translate(
                        "Delete the selected folder or file"),
                size=iconSize)
        self.gotoTool = iconCache.makeBitmapButton(
                self, filename='goto',
                name='goto',
                label=_translate('Goto'),
                toolbar=self.toolBar,
                tip=_translate(
                        "Jump to another folder"),
                size=iconSize,
                tbKind=wx.ITEM_DROPDOWN)
        # create the dropdown menu for goto
        self.gotoMenu = wx.Menu()
        item = self.gotoMenu.Append(
            wx.ID_ANY,
            _translate("Browse ..."),
            _translate("Browse the file system for a directory to open"))
        self.Bind(wx.EVT_MENU, self.OnBrowse, id=item.GetId())
        self.gotoMenu.AppendSeparator()
        item = self.gotoMenu.Append(
            wx.ID_ANY,
            _translate("Current working directory"),
            _translate("Open the current working directory"))
        self.Bind(wx.EVT_MENU, self.OnGotoCWD, id=item.GetId())
        item = self.gotoMenu.Append(
            wx.ID_ANY,
            _translate("Editor file location"),
            _translate("Open the directory the current editor file is located"))
        self.Bind(wx.EVT_MENU, self.OnGotoFileLocation, id=item.GetId())
        # Bind toolbar buttons
        self.Bind(wx.EVT_TOOL, self.OnBrowse, self.gotoTool)
        self.Bind(aui.EVT_AUITOOLBAR_TOOL_DROPDOWN, self.OnGotoMenu, self.gotoTool)
        self.Bind(wx.EVT_TOOL, self.OnNewFolderTool, self.newFolderTool)
        self.Bind(wx.EVT_TOOL, self.OnDeleteTool, self.deleteTool)
        self.Bind(wx.EVT_TOOL, self.OnRenameTool, self.renameTool)
        self.gotoTool.SetDropdownMenu(self.gotoMenu)

        # Realise
        self.toolBar.Realize()


    def OnGotoFileLocation(self, evt):
        """Goto the currently opened file location."""
        filename = self.coder.currentDoc.filename
        filedir = os.path.split(filename)[0]
        if os.path.isabs(filedir):
            self.gotoDir(filedir)

            # select the file in the browser
            for idx, item in enumerate(self.dirData):
                if item.abspath == filename:
                    self.fileList.Select(idx, True)
                    self.fileList.EnsureVisible(idx)
                    self.selectedItem = self.dirData[idx]
                    self.fileList.SetFocus()
                    break
        else:
            dlg = wx.MessageDialog(
                self,
                _translate(
                "Cannot change working directory to location of file `{}`. It"
                " needs to be saved first.").format(filename),
                style=wx.ICON_ERROR | wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            evt.Skip()

    def OnGotoMenu(self, event):
        mnuGoto = wx.Menu()
        mnuGoto.Append(
            ID_GOTO_BROWSE,
            _translate("Browse ..."),
            _translate("Browse the file system for a directory to open"))
        mnuGoto.AppendSeparator()
        mnuGoto.Append(
            ID_GOTO_CWD,
            _translate("Current working directory"),
            _translate("Open the current working directory"))
        mnuGoto.Append(
            ID_GOTO_FILE,
            _translate("Editor file location"),
            _translate("Open the directory the current editor file is located"))

        self.PopupMenu(mnuGoto)
        mnuGoto.Destroy()

        #event.Skip()

    def OnBrowse(self, event=None):
        dlg = wx.DirDialog(self, _translate("Choose directory ..."), "",
                           wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.gotoDir(dlg.GetPath())

        dlg.Destroy()

    def OnNewFolderTool(self, event):
        """When the new folder tool is clicked."""

        # ask for the name of the folder
        dlg = wx.TextEntryDialog(self, _translate('Enter folder name:'), 
                                       _translate('New folder'), '')

        if dlg.ShowModal() == wx.ID_CANCEL:
            dlg.Destroy()
            event.Skip()
            return

        folderName = dlg.GetValue()
        if folderName == '':
            dlg = wx.MessageDialog(
                self,
                _translate("Folder name cannot be empty.").format(folderName),
                style=wx.ICON_ERROR | wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            event.Skip()
            return

        abspath = os.path.join(self.currentPath, folderName)

        if os.path.isdir(abspath):  # folder exists, warn and exit
            dlg = wx.MessageDialog(
                self,
                _translate("Cannot create folder `{}`, already exists.").format(folderName),
                style=wx.ICON_ERROR | wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            event.Skip()
            return

        # try to create the folder
        try:
            os.mkdir(abspath)
        except OSError:
            dlg = wx.MessageDialog(
                self,
                _translate("Cannot create folder `{}`, permission denied.").format(folderName),
                style=wx.ICON_ERROR | wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            event.Skip()
            return

        # open the folder we just created
        self.gotoDir(abspath)

    def OnDeleteTool(self, event=None):
        """Activated when the delete tool is pressed."""
        if self.selectedItem is not None:
            if isinstance(self.selectedItem, FolderItemData):
                if self.selectedItem.name == '..':
                    return  # is a sub directory marker

            self.delete()

    def OnRenameTool(self, event):
        """Activated when the rename tool is pressed."""
        if self.selectedItem is not None:
            if isinstance(self.selectedItem, FolderItemData):
                if self.selectedItem.name == '..':
                    return  # is a sub directory marker
            self.rename()

    def OnGotoCWD(self, event):
        """Activated when the goto CWD menu item is clicked."""
        cwdpath = os.getcwd()
        if os.getcwd() != '':
            self.gotoDir(cwdpath)
    #
    # def OnCopyTool(self, event=None):
    #     """Activated when the copy tool is pressed."""
    #     pass  # mdc - will add this in a later version

    def rename(self):
        """Rename a file or directory."""
        if os.path.isdir(self.selectedItem.abspath):  # rename a directory
            dlg = wx.TextEntryDialog(
                self,
                _translate('Rename folder `{}` to:').format(self.selectedItem.name),
                _translate('Rename Folder'), self.selectedItem.name)

            if dlg.ShowModal() == wx.ID_OK:
                newName = dlg.GetValue()
                try:
                    os.rename(self.selectedItem.abspath,
                              os.path.join(self.selectedItem.basename, newName))
                except OSError:
                    dlg2 = wx.MessageDialog(
                        self,
                        _translate("Cannot rename `{}` to `{}`.").format(
                            self.selectedItem.name, newName),
                        style=wx.ICON_ERROR | wx.OK)
                    dlg2.ShowModal()
                    dlg2.Destroy()
                    dlg.Destroy()
                    return

                self.gotoDir(self.currentPath)  # refresh

                for idx, item in enumerate(self.dirData):
                    abspath = os.path.join(self.currentPath, newName)
                    if item.abspath == abspath:
                        self.fileList.Select(idx, True)
                        self.fileList.EnsureVisible(idx)
                        self.selectedItem = self.dirData[idx]
                        self.fileList.SetFocus()
                        break

            dlg.Destroy()
        elif os.path.isfile(self.selectedItem.abspath):  # rename a directory
            dlg = wx.TextEntryDialog(
                self,
                _translate('Rename file `{}` to:').format(self.selectedItem.name),
                _translate('Rename file'), self.selectedItem.name)

            if dlg.ShowModal() == wx.ID_OK:
                newName = dlg.GetValue()

                try:
                    newPath = os.path.join(self.selectedItem.basename, newName)
                    os.rename(self.selectedItem.abspath,
                              newPath)
                except OSError:
                    dlgError = wx.MessageDialog(
                        self,
                        _translate("Cannot rename `{}` to `{}`.").format(
                            self.selectedItem.name, newName),
                        style=wx.ICON_ERROR | wx.OK)
                    dlgError.ShowModal()
                    dlgError.Destroy()
                    dlg.Destroy()
                    return

                self.gotoDir(self.currentPath)  # refresh

                for idx, item in enumerate(self.dirData):
                    if newPath == item.abspath:
                        self.fileList.Select(idx, True)
                        self.fileList.EnsureVisible(idx)
                        self.selectedItem = self.dirData[idx]
                        self.fileList.SetFocus()
                        break

            dlg.Destroy()

    def delete(self):
        """Delete a file or directory."""
        if os.path.isdir(self.selectedItem.abspath):  # delete a directory
            dlg = wx.MessageDialog(
                self,
                _translate("Are you sure you want to PERMANENTLY delete folder "
                      "`{}`?").format(self.selectedItem.name),
                'Confirm delete', style=wx.YES_NO | wx.NO_DEFAULT |
                                        wx.ICON_WARNING)

            if dlg.ShowModal() == wx.ID_YES:
                try:
                    os.rmdir(self.selectedItem.abspath)
                except FileNotFoundError:  # file was removed
                    dlgError = wx.MessageDialog(
                        self, _translate("Cannot delete folder `{}`, directory does not "
                              "exist.").format(self.selectedItem.name),
                        'Error', style=wx.OK | wx.ICON_ERROR)
                    dlgError.ShowModal()
                    dlgError.Destroy()
                except OSError:  # permission or directory not empty error
                    dlgError = wx.MessageDialog(
                        self, _translate("Cannot delete folder `{}`, directory is not "
                              "empty or permission denied.").format(
                            self.selectedItem.name),
                        'Error', style=wx.OK | wx.ICON_ERROR)
                    dlgError.ShowModal()
                    dlgError.Destroy()

                self.gotoDir(self.currentPath)

            dlg.Destroy()
        elif os.path.isfile(self.selectedItem.abspath):  # delete a file
            dlg = wx.MessageDialog(
                self, _translate("Are you sure you want to PERMANENTLY delete file "
                      "`{}`?").format(self.selectedItem.name),
                'Confirm delete', style=wx.YES_NO | wx.NO_DEFAULT |
                                        wx.ICON_WARNING)

            if dlg.ShowModal() == wx.ID_YES:
                try:
                    os.remove(self.selectedItem.abspath)
                except FileNotFoundError:
                    dlgError = wx.MessageDialog(
                        self, _translate("Cannot delete folder `{}`, file does not "
                              "exist.").format(self.selectedItem.name),
                        'Error', style=wx.OK | wx.ICON_ERROR)
                    dlgError.ShowModal()
                    dlgError.Destroy()
                except OSError:
                    dlgError = wx.MessageDialog(
                        self, _translate("Cannot delete file `{}`, permission "
                              "denied.").format(self.selectedItem.name),
                        'Error', style=wx.OK | wx.ICON_ERROR)
                    dlgError.ShowModal()
                    dlgError.Destroy()

                self.gotoDir(self.currentPath)

            dlg.Destroy()

    def OnAddrEnter(self, evt=None):
        """When enter is pressed."""
        path = self.txtAddr.GetValue()
        if path == self.currentPath:
            return

        if os.path.isdir(path):
            self.gotoDir(path)
        else:
            dlg = wx.MessageDialog(
                self,
                _translate("Specified path `{}` is not a directory.").format(path),
                style=wx.ICON_ERROR | wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            self.txtAddr.SetValue(self.currentPath)

    def OnItemActivated(self, evt):
        """Even for when an item is double-clicked or activated."""
        if self.selectedItem is not None:
            if isinstance(self.selectedItem, FolderItemData):
                self.gotoDir(self.selectedItem.abspath)
            elif isinstance(self.selectedItem, FileItemData):
                # check if an image file
                if not imghdr.what(self.selectedItem.abspath):
                    self.coder.fileOpen(None, self.selectedItem.abspath)
                else:
                    if sys.platform == 'win32':
                        imgCmd = 'explorer'
                    elif sys.platform == 'darwin':
                        imgCmd = 'open'
                    elif sys.platform == 'linux':
                        imgCmd = 'xdg-open'
                    else:
                        return  # not supported

                    # show image in viewer
                    subprocess.run(
                        [imgCmd, self.selectedItem.abspath], shell=True)

    def OnItemSelected(self, evt=None):
        """Event for when an item is selected."""
        itemIdx = self.fileList.GetFirstSelected()
        if itemIdx >= 0:
            self.selectedItem = self.dirData[itemIdx]

    def scanDir(self, path):
        """Scan a directory and update file and folder items."""
        self.dirData = []

        # are we in a sub directory?
        upPath = os.path.abspath(os.path.join(path, '..'))
        if upPath != path:  # add special item that goes up a directory
            self.dirData.append(FolderItemData('..', upPath, None))

        # scan the directory and create item objects
        try:
            contents = os.listdir(path)
            for f in contents:
                absPath = os.path.join(path, f)
                if os.path.isdir(absPath):
                    self.dirData.append(FolderItemData(f, absPath, path))
            for f in contents:
                absPath = os.path.join(path, f)
                if os.path.isfile(absPath):
                    fsize = convertBytes(os.stat(absPath).st_size)
                    self.dirData.append(
                        FileItemData(f, absPath, path, fsize, None))
        except OSError:
            dlg = wx.MessageDialog(
                self,
                _translate("Cannot access directory `{}`, permission denied.").format(path),
                style=wx.ICON_ERROR | wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        return True

    def updateFileBrowser(self):
        """Update the contents of the file browser.
        """
        # start off with adding folders to the list
        self.fileList.DeleteAllItems()
        for obj in self.dirData:
            if isinstance(obj, FolderItemData):
                if obj.name == '..':
                    img = self.fileImgInds['..']
                else:
                    img = self.fileImgInds['\\']

                self.fileList.InsertItem(
                    self.fileList.GetItemCount(), obj.name, img)
            elif isinstance(obj, FileItemData):
                ext = os.path.splitext(obj.name)[1]
                if ext in self.fileImgInds:
                    img = self.fileImgInds[ext]
                else:
                    img = self.fileImgInds['.?']
                self.fileList.InsertItem(
                    self.fileList.GetItemCount(),
                    obj.name,
                    img)
                #self.fileList.SetItem(index, 1, obj.fsize)
                #self.fileList.SetItem(index, 2, obj.mod)

    def addItem(self, name, absPath):
        """Add an item to the directory browser."""
        pass

    def gotoDir(self, path):
        """Set the file browser to a directory."""
        # check if a directory
        if not os.path.isdir(path):
            dlg = wx.MessageDialog(
                self,
                _translate("Cannot access directory `{}`, not a directory.").format(path),
                style=wx.ICON_ERROR | wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # check if we have access
        # if not os.access(path, os.R_OK):
        #     dlg = wx.MessageDialog(
        #         self,
        #         "Cannot access directory `{}`, permission denied.".format(path),
        #         style=wx.ICON_ERROR | wx.OK)
        #     dlg.ShowModal()
        #     return

        # update files and folders
        if not self.scanDir(path):  # if failed, return the current directory
            self.gotoDir(self.currentPath)
            return

        # change the current path
        self.currentPath = path
        self.txtAddr.SetValue(self.currentPath)
        self.updateFileBrowser()

