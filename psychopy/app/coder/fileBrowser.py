from __future__ import absolute_import, print_function

# from future import standard_library
# standard_library.install_aliases()
from builtins import chr
from builtins import str
from builtins import range
import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

import os
import time

# enums for file types
FILE_TYPE_PYTHON = 0
FILE_TYPE_DATA = 1
FILE_TYPE_IMAGE = 2
FILE_TYPE_UNKNOWN = 3
FOLDER_TYPE_NORMAL = 4
FOLDER_TYPE_NAV = 5
FOLDER_TYPE_NO_ACCESS = 6


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


class FileBrowserItem(object):
    """Class representing a file browser item."""

    def __init__(self, parent, basename, name):
        self.parent = parent  # browser panel
        self.basename = basename
        self.name = name
        self.abspath = os.path.abspath(os.path.join(self.basename, self.name))

    def open(self):
        """Called when an item is activated."""
        pass


class FolderItem(FileBrowserItem):
    """Class representing a folder in the file browser."""

    def __init__(self, parent, basename, name):
        super(FolderItem, self).__init__(parent, basename, name)
        self.subDirMarker = name == '..'

    def open(self):
        """Open the directory in the browser."""
        self.parent.gotoDir(self.abspath)

    def rename(self, newname):
        """Rename a folder."""
        dst = os.path.join(self.basename, newname)
        try:
            os.rename(self.abspath, dst)
        except OSError:
            return False

        newpath = os.path.abspath(os.path.join(self.basename, newname))

        if os.path.isdir(newpath):  # valid after rename?
            self.name = newname
            self.abspath = newpath
            return True

        return False

    def isValid(self):
        """Check if the directory still exists."""
        return os.path.isdir(self.abspath)

    def folderType(self):
        """Get the enum value for the file type."""
        if not self.subDirMarker:
            return FOLDER_TYPE_NORMAL
        else:
            return FOLDER_TYPE_NAV


class FileItem(FileBrowserItem):
    """Class representing a file in the file browser."""
    def __init__(self, parent, basename, name):
        super(FileItem, self).__init__(parent, basename, name)
        self.modTime = time.ctime(os.path.getmtime(self.abspath))
        self.sizeof = os.stat(self.abspath).st_size

    def open(self):
        """Open the file in PsychoPy."""
        self.parent.coder.fileOpen(None, self.abspath)

    def rename(self, newname):
        """Rename a folder."""
        dst = os.path.join(self.basename, newname)
        try:
            os.rename(self.abspath, dst)
        except OSError:
            return False

        newpath = os.path.abspath(os.path.join(self.basename, newname))

        if os.path.isfile(newpath):  # valid after rename?
            self.name = newname
            self.abspath = newpath
            return True

        return False

    def isValid(self):
        """Check if the file still exists."""
        return os.path.isdir(self.abspath)

    def getExtension(self):
        """Get the extension for this file."""
        nameParts = self.name.split('.')
        if not len(nameParts) > 1:  # actually split
            return None

        return nameParts[-1]  # likely extension

    def fileSize(self):
        """Get the size of a file as a string."""
        return convertBytes(self.sizeof)

    def modifiedDate(self):
        """Get the date/time a file as modified."""
        # (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime)
        t = time.strptime(self.modTime, "%a %b %d %H:%M:%S %Y")

        return time.strftime("%b %d, %Y, %I:%M %p", t)

    def fileType(self):
        """Get the enum value for the file type."""
        ext = self.getExtension()

        if ext is None:
            return FILE_TYPE_UNKNOWN

        if ext.lower() in ('py',):
            return FILE_TYPE_PYTHON
        elif ext.lower() in (
                'jpg', 'jpeg', 'png', 'tif', 'bmp',):
            return FILE_TYPE_IMAGE
        elif ext.lower() in ('csv', 'tsv', 'psydat',):
            return FILE_TYPE_DATA
        else:
            return FILE_TYPE_UNKNOWN


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


class FileBrowserPanel(wx.Panel):
    """Panel for a file browser."""

    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self.coder = frame
        self.currentPath = None
        self.currentDirContents = {'folders': [], 'files': []}
        self.selectedItem = None
        self.isSubDir = False
        self.pathData = {}

        # get graphics for toolbars and tree items
        rc = self.coder.paths['resources']
        join = os.path.join

        # handles for icon graphics in the image list
        self.fileImgList = wx.ImageList(16, 16)
        self._lstGfx = {
            FOLDER_TYPE_NORMAL: self.fileImgList.Add(
                wx.Bitmap(join(rc, 'folder16.png'), wx.BITMAP_TYPE_PNG)),
            FOLDER_TYPE_NAV: self.fileImgList.Add(
                wx.Bitmap(join(rc, 'folder-open16.png'), wx.BITMAP_TYPE_PNG)),
            FILE_TYPE_UNKNOWN: self.fileImgList.Add(
                wx.Bitmap(join(rc, 'fileunknown16.png'), wx.BITMAP_TYPE_PNG)),
            FILE_TYPE_DATA: self.fileImgList.Add(
                wx.Bitmap(join(rc, 'filecsv16.png'), wx.BITMAP_TYPE_PNG)),
            FILE_TYPE_IMAGE: self.fileImgList.Add(
                wx.Bitmap(join(rc, 'fileimage16.png'), wx.BITMAP_TYPE_PNG)),
            FILE_TYPE_PYTHON: self.fileImgList.Add(
                wx.Bitmap(join(rc, 'coderpython16.png'), wx.BITMAP_TYPE_PNG))
        }

        # self.SetDoubleBuffered(True)

        # create an address bar
        self.lblDir = wx.StaticText(self, label="Directory:")
        self.txtAddr = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)

        # create the source tree control
        self.flId = wx.NewIdRef()
        self.fileList = FileBrowserListCtrl(
            self,
            self.flId,
            pos=(0, 0),
            size=wx.Size(300, 300),
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.fileList.SetImageList(self.fileImgList, wx.IMAGE_LIST_SMALL)

        # do layout
        szrAddr = wx.BoxSizer(wx.HORIZONTAL)
        szrAddr.Add(self.lblDir, 0, flag=wx.RIGHT | wx.ALIGN_CENTRE_VERTICAL, border=5)
        szrAddr.Add(self.txtAddr, 1, flag=wx.ALIGN_CENTRE_VERTICAL)

        szr = wx.BoxSizer(wx.VERTICAL)

        szr.Add(szrAddr, 0, flag=wx.EXPAND | wx.ALL, border=5)
        szr.Add(self.fileList, 1, flag=wx.EXPAND)
        self.SetSizer(szr)

        # bind events
        self.Bind(
            wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemSelected, self.fileList)
        self.Bind(
            wx.EVT_TEXT_ENTER, self.OnAddrEnter, self.txtAddr)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu, self.fileList)

        # add columns
        self.fileList.InsertColumn(0, "Name")
        self.fileList.InsertColumn(1, "Size", wx.LIST_FORMAT_RIGHT)
        self.fileList.InsertColumn(2, "Modified")
        self.fileList.SetColumnWidth(0, 250)
        self.fileList.SetColumnWidth(1, 60)
        self.fileList.SetColumnWidth(2, 100)

        self.gotoDir(os.getcwd())

    def OnContextMenu(self, event):
        sel = self.fileList.GetFirstSelected()
        if sel == -1:
            event.Skip()
            return

        self.selectedItem = self.dirData[sel]
        if isinstance(self.selectedItem, FolderItem):
            self.showFolderContextMenu()
        elif isinstance(self.selectedItem, FileItem):
            self.showFileContextMenu()

    def showFolderContextMenu(self):
        # only do this part the first time so the events are only bound once
        #
        # Yet another anternate way to do IDs. Some prefer them up top to
        # avoid clutter, some prefer them close to the object of interest
        # for clarity.
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewIdRef()
            self.popupID2 = wx.NewIdRef()
            self.popupID3 = wx.NewIdRef()
            self.popupID4 = wx.NewIdRef()
            self.popupID5 = wx.NewIdRef()
            self.popupID6 = wx.NewIdRef()
            self.popupID7 = wx.NewIdRef()
            self.popupID8 = wx.NewIdRef()
            self.popupID9 = wx.NewIdRef()

            self.Bind(wx.EVT_MENU, self.OnPopupTwo, id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.OnPopupOne, id=self.popupID2)
            self.Bind(wx.EVT_MENU, self.OnPopupThree, id=self.popupID3)
            self.Bind(wx.EVT_MENU, self.OnPopupFour, id=self.popupID4)
            self.Bind(wx.EVT_MENU, self.OnPopupFive, id=self.popupID5)
            self.Bind(wx.EVT_MENU, self.OnPopupSix, id=self.popupID6)
            self.Bind(wx.EVT_MENU, self.OnPopupSeven, id=self.popupID7)
            self.Bind(wx.EVT_MENU, self.OnPopupEight, id=self.popupID8)
            self.Bind(wx.EVT_MENU, self.OnPopupNine, id=self.popupID9)

        # make a menu
        menu = wx.Menu()
        # Show how to put an icon in the menu
        item = wx.MenuItem(menu, self.popupID1, "Open")
        # bmp = images.Smiles.GetBitmap()
        # item.SetBitmap(bmp)
        menu.Append(item)
        menu.AppendSeparator()
        # Make sure we are not renaming the `up` directory item
        if self.isSubDir:
            if self.fileList.GetFirstSelected() > 0:
                menu.Append(self.popupID2, "Rename `{}`".format(self.selectedItem.name))
        else:
            menu.Append(self.popupID2, "Rename `{}`".format(self.selectedItem.name))

        menu.Append(self.popupID3, "Three")
        menu.Append(self.popupID4, "Four")
        menu.Append(self.popupID5, "Five")
        menu.Append(self.popupID6, "Six")
        # make a submenu
        sm = wx.Menu()
        sm.Append(self.popupID8, "sub item 1")
        sm.Append(self.popupID9, "sub item 1")
        menu.Append(self.popupID7, "Test Submenu", sm)

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()

    def showFileContextMenu(self):
        # only do this part the first time so the events are only bound once
        #
        # Yet another anternate way to do IDs. Some prefer them up top to
        # avoid clutter, some prefer them close to the object of interest
        # for clarity.
        if not hasattr(self, "filePopUpID1"):
            self.filePopUpID1 = wx.NewIdRef()
            self.Bind(wx.EVT_MENU, self.OnPopupTwo, id=self.filePopUpID1)

        # make a menu
        menu = wx.Menu()
        # Show how to put an icon in the menu
        item = wx.MenuItem(menu, self.filePopUpID1,
                           "Open `{}` in Coder".format(self.selectedItem.name))
        # bmp = images.Smiles.GetBitmap()
        # item.SetBitmap(bmp)
        menu.Append(item)
        menu.AppendSeparator()
        # # Make sure we are not renaming the `up` directory item
        # menu.Append(self.popupID2, "Rename `{}`".format(self.selectedName))
        #
        # menu.Append(self.popupID3, "Three")
        # menu.Append(self.popupID4, "Four")
        # menu.Append(self.popupID5, "Five")
        # menu.Append(self.popupID6, "Six")
        # # make a submenu
        # sm = wx.Menu()
        # sm.Append(self.popupID8, "sub item 1")
        # sm.Append(self.popupID9, "sub item 1")
        # menu.Append(self.popupID7, "Test Submenu", sm)

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()

    def OnPopupOne(self, event=None):
        self.rename(self.selectedItem.name)

    def rename(self, what):
        """Rename a file or directory."""
        absPath = os.path.join(self.currentPath, what)
        if os.path.isdir(absPath):  # rename a directory
            dlg = wx.TextEntryDialog(
                self, 'Rename folder `{}`.'.format(what),
                'Rename Folder', what)

            if dlg.ShowModal() == wx.ID_OK:
                newName = dlg.GetValue()
                result = self.selectedItem.rename(newName)
                if not result:
                    dlg2 = wx.MessageDialog(
                        self,
                        "Cannot rename `{}` to `{}`.".format(what, newName),
                        style=wx.ICON_ERROR | wx.OK)
                    dlg2.ShowModal()
                    dlg2.Destroy()
                    dlg.Destroy()
                    return

                self.gotoDir(self.currentPath)

            dlg.Destroy()

    def open(self):
        if self.selectedItem is not None:
            self.selectedItem.open()

    def OnPopupTwo(self, event):
        self.open()

    def OnPopupThree(self, event):
        print("Popup three\n")

    def OnPopupFour(self, event):
        print("Popup four\n")

    def OnPopupFive(self, event):
        print("Popup five\n")

    def OnPopupSix(self, event):
        print("Popup six\n")

    def OnPopupSeven(self, event):
        print("Popup seven\n")

    def OnPopupEight(self, event):
        print("Popup eight\n")

    def OnPopupNine(self, event):
        print("Popup nine\n")

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
                "Specified path `{}` is not a directory.".format(path),
                style=wx.ICON_ERROR | wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            self.txtAddr.SetValue(self.currentPath)

    def OnItemSelected(self, evt=None):
        itemIdx = self.fileList.GetFirstSelected()
        if itemIdx >= 0:
            self.dirData[itemIdx].open()

    def scanDir(self, path):
        """Scan a directory and update file and folder items."""
        self.dirData = []

        # are we in a sub directory?
        upPath = os.path.abspath(os.path.join(path, '..'))
        self.isSubDir = upPath != path
        if self.isSubDir:  # add special item that goes up a directory
            self.dirData.append(FolderItem(self, path, '..'))

        # scan the directory and create item objects
        try:
            contents = os.listdir(path)
            for f in contents:
                absPath = os.path.join(path, f)
                if os.path.isdir(absPath):
                    self.dirData.append(FolderItem(self, path, f))
            for f in contents:
                absPath = os.path.join(path, f)
                if os.path.isfile(absPath):
                    self.dirData.append(FileItem(self, path, f))
        except OSError:
            dlg = wx.MessageDialog(
                self,
                "Cannot access directory `{}`, permission denied.".format(path),
                style=wx.ICON_ERROR | wx.OK)
            dlg.ShowModal()
            self.txtAddr.SetValue(self.currentPath)  # use last path
            return False

        return True

    def updateFileBrowser(self):
        """Update the contents of the file browser.
        """
        # start off with adding folders to the list
        self.fileList.DeleteAllItems()
        for obj in self.dirData:
            if isinstance(obj, FolderItem):
                img = obj.folderType()
                print(img)
                index = self.fileList.InsertItem(
                    self.fileList.GetItemCount(), obj.name, self._lstGfx[img])
            elif isinstance(obj, FileItem):
                index = self.fileList.InsertItem(
                    self.fileList.GetItemCount(),
                    obj.name,
                    self._lstGfx[obj.fileType()])
                self.fileList.SetItem(index, 1, obj.fileSize())
                self.fileList.SetItem(index, 2, obj.modifiedDate())

        # for fileName, filePath in self.currentDirContents['files']:
        #     # chose the appropriate icon
        #     fileSplit = fileName.split('.')
        #     if len(fileSplit) > 1:
        #         ext = fileSplit[-1]
        #         if ext == 'py':
        #             useIcon = self._lstGfx['filePy']
        #         elif ext in ('csv', 'tsv', 'psydat'):
        #             useIcon = self._lstGfx['fileCSV']
        #         else:
        #             useIcon = self._lstGfx['fileUnknown']
        #     else:
        #         useIcon = self._lstGfx['fileUnknown']
        #
        #     index = self.fileList.InsertItem(
        #         self.fileList.GetItemCount(), fileName, useIcon)
        #     fileAbsPath = filePath
        #     self.pathData[nPaths] = fileAbsPath
        #     self.fileList.SetItem(index, 1, self.reportFileSize(fileAbsPath))
        #     self.fileList.SetItem(index, 2, self.reportModifiedDate(fileAbsPath))
        #     self.fileList.SetItemData(index, nPaths)
        #
        #     nPaths += 1

    def addItem(self, name, absPath):
        """Add an item to the directory browser."""
        pass

    def gotoDir(self, path):
        """Set the file browser to a directory."""
        # check if a directory
        if not os.path.isdir(path):
            dlg = wx.MessageDialog(
                self,
                "Cannot access directory `{}`, not a directory.".format(path),
                style=wx.ICON_ERROR | wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            self.txtAddr.SetValue(self.currentPath)  # use last path

        # check if we have access
        # if not os.access(path, os.R_OK):
        #     dlg = wx.MessageDialog(
        #         self,
        #         "Cannot access directory `{}`, permission denied.".format(path),
        #         style=wx.ICON_ERROR | wx.OK)
        #     dlg.ShowModal()
        #     return

        # update files and folders
        self.scanDir(path)

        # change the current path
        self.currentPath = path
        self.txtAddr.SetValue(self.currentPath)
        self.updateFileBrowser()

    def getMimeType(self, fileName):
        pass
