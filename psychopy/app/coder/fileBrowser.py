#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for the coder file browser pane."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

try:
    from wx import aui
except Exception:
    import wx.lib.agw.aui as aui  # some versions of phoenix

import os
import sys
import subprocess
import mimetypes
from ..themes import icons, colors, handlers
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


class FolderItemData:
    """Class representing a folder item in the file browser."""
    __slots__ = ['name', 'abspath', 'basename']
    def __init__(self, name, abspath, basename):
        self.name = name
        self.abspath = abspath
        self.basename = basename


class FileItemData:
    """Class representing a file item in the file browser."""
    __slots__ = ['name', 'abspath', 'basename', 'fsize', 'mod']
    def __init__(self, name, abspath, basename, fsize, mod):
        self.name = name
        self.abspath = abspath
        self.basename = basename
        self.fsize = fsize
        self.mod = mod


class FileBrowserListCtrl(ListCtrlAutoWidthMixin, wx.ListCtrl, handlers.ThemeMixin):
    """Custom list control for the file browser."""

    def __init__(self, parent, id, pos, size, style):
        wx.ListCtrl.__init__(self,
                             parent,
                             id,
                             pos,
                             size,
                             style=style)
        self.parent = parent
        ListCtrlAutoWidthMixin.__init__(self)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick)

    def OnRightClick(self, evt=None):
        # create menu
        menu = wx.Menu()
        # create new menu
        newMenu = wx.Menu()
        btn = newMenu.Append(
            wx.ID_NEW,
            item=_translate("Folder"),
            helpString=_translate("Create a new folder here.")
        )
        newMenu.Bind(wx.EVT_MENU, self.parent.OnNewFolderTool, source=btn)
        menu.AppendSubMenu(newMenu, _translate("New..."))
        # rename btn
        btn = menu.Append(
            wx.ID_ANY,
            item=_translate("Rename"),
            helpString=_translate("Rename the file"))
        menu.Bind(wx.EVT_MENU, self.parent.OnRenameTool, source=btn)
        # delete btn
        btn = menu.Append(
            wx.ID_DELETE,
            item=_translate("Delete"),
            helpString=_translate("Delete the file"))
        menu.Bind(wx.EVT_MENU, self.parent.OnDeleteTool, source=btn)
        # show menu
        self.PopupMenu(menu, pos=evt.GetPoint())

    def _applyAppTheme(self, target=None):
        self.SetBackgroundColour(colors.app['tab_bg'])
        self.SetForegroundColour(colors.app['text'])


class FileBrowserPanel(wx.Panel, handlers.ThemeMixin):
    """Panel for a file browser.
    """
    fileImgExt = {
            "..": 'dirup16',
            "\\": 'folder16',
            ".?": 'fileunknown16',
            ".csv": 'filecsv16',
            ".xlsx": 'filecsv16',
            ".xls": 'filecsv16',
            ".tsv": 'filecsv16',
            ".png": 'fileimage16',
            ".jpeg": 'fileimage16',
            ".jpg": 'fileimage16',
            ".bmp": 'fileimage16',
            ".tiff": 'fileimage16',
            ".tif": 'fileimage16',
            ".ppm": 'fileimage16',
            ".gif": 'fileimage16',
            ".py": 'coderpython',
            ".js": 'coderjs'
        }

    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent, -1, style=wx.BORDER_NONE)
        self.parent = parent
        self.coder = frame
        self.app = frame.app
        self.tabIcon = "folder"

        self.currentPath = None
        self.selectedItem = None
        self.isSubDir = False
        self.fileImgList = None  # will be a wx ImageList to store icons
        self.pathData = {}

        # setup sizer
        szr = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(szr)

        # create a navigation toolbar
        self.lblDir = wx.StaticText(self, label=_translate("Directory:"))
        szr.Add(self.lblDir, border=5, flag=wx.TOP | wx.LEFT | wx.RIGHT | wx.EXPAND)
        self.navBar = wx.BoxSizer(wx.HORIZONTAL)
        szr.Add(self.navBar, border=3, flag=wx.ALL | wx.EXPAND)
        # file path ctrl
        self.txtAddr = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnAddrEnter, self.txtAddr)
        self.navBar.Add(self.txtAddr, proportion=1, border=5, flag=wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.EXPAND)
        # browse button
        self.browseBtn = wx.Button(self, size=(16, 16), style=wx.BORDER_NONE)
        self.browseBtn.Bind(wx.EVT_BUTTON, self.OnBrowse)
        self.navBar.Add(self.browseBtn, border=3, flag=wx.ALL | wx.EXPAND)
        self.browseBtn.SetToolTip(_translate(
            "Browse for a folder to open."
        ))
        # library root button
        self.libRootBtn = wx.Button(self, size=(16, 16), style=wx.BORDER_NONE)
        self.libRootBtn.SetToolTip(_translate(
            "Navigate to PsychoPy library root."
        ))
        self.libRootBtn.Bind(wx.EVT_BUTTON, self.OnGotoCWD)
        self.navBar.Add(self.libRootBtn, border=3, flag=wx.ALL | wx.EXPAND)
        # current file button
        self.currentFileBtn = wx.Button(self, size=(16, 16), style=wx.BORDER_NONE)
        self.currentFileBtn.SetToolTip(_translate(
            "Navigate to current open file."
        ))
        self.currentFileBtn.Bind(wx.EVT_BUTTON, self.OnGotoFileLocation)
        self.navBar.Add(self.currentFileBtn, border=3, flag=wx.ALL | wx.EXPAND)

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

        szr.Add(self.fileList, 1, flag=wx.EXPAND)
        self.makeFileImgIcons()

        # add columns
        self.fileList.InsertColumn(0, "Name")
        #self.fileList.InsertColumn(1, "Size", wx.LIST_FORMAT_LEFT)
        #self.fileList.InsertColumn(2, "Modified")
        self.fileList.SetColumnWidth(0, 280)
        #self.fileList.SetColumnWidth(1, 80)
        #self.fileList.SetColumnWidth(2, 100)

        self.gotoDir(os.getcwd())

    def _applyAppTheme(self, target=None):
        # Set background
        self.SetBackgroundColour(colors.app['tab_bg'])
        self.SetForegroundColour(colors.app['text'])
        # Style nav bar
        btns = {
            self.currentFileBtn: icons.ButtonIcon(stem="currentFile", size=16).bitmap,
            self.libRootBtn: icons.ButtonIcon(stem="libroot", size=16).bitmap,
            self.browseBtn: icons.ButtonIcon(stem="fileopen", size=16).bitmap
        }
        for btn, bmp in btns.items():
            btn.SetBackgroundColour(colors.app['tab_bg'])
            btn.SetBitmap(bmp)
            btn.SetBitmapFocus(bmp)
            btn.SetBitmapDisabled(bmp)
            btn.SetBitmapPressed(bmp)
            btn.SetBitmapCurrent(bmp)
        # Make sure directory label is correct color
        self.lblDir.SetForegroundColour(colors.app['text'])
        # Remake icons
        self.makeFileImgIcons()
        # Refresh
        self.Refresh()

    def makeFileImgIcons(self):
        # handles for icon graphics in the image list
        self.fileImgInds = {}
        if self.fileImgList:
            self.fileImgList.RemoveAll()
        else:
            self.fileImgList = wx.ImageList(16, 16)
        for key in self.fileImgExt:
            self.fileImgInds[key] = self.fileImgList.Add(
                    icons.ButtonIcon(self.fileImgExt[key], size=(16, 16)).bitmap
            )
        self.fileList.SetImageList(self.fileImgList, wx.IMAGE_LIST_SMALL)
        self.Update()

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
                # add some mimetypes which aren't recognised by default
                mimetypes.add_type("text/xml", ".psyexp")
                mimetypes.add_type("text/json", ".psyrun")
                mimetypes.add_type("text/markdown", ".md")
                mimetypes.add_type("text/config", ".cfg")
                mimetypes.add_type("text/plain", ".log")
                mimetypes.add_type("text/plain", ".yaml")
                # try to guess data type
                dataType = mimetypes.guess_type(self.selectedItem.abspath)[0]

                if dataType and "text" in dataType:
                    # open text files in editor
                    self.coder.fileOpen(None, self.selectedItem.abspath)
                else:
                    # open other files in system default
                    if sys.platform == 'win32':
                        cmd = 'explorer'
                    elif sys.platform == 'darwin':
                        cmd = 'open'
                    elif sys.platform == 'linux':
                        cmd = 'xdg-open'
                    else:
                        return  # not supported

                    subprocess.run(
                        [cmd, self.selectedItem.abspath], shell=True)

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
        # Enable/disable "go to current file" button based on current file
        self.currentFileBtn.Enable(self.GetTopLevelParent().filename is not None)

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
