#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import os
import subprocess
import sys

import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

from psychopy.app.colorpicker import PsychoColorPicker
from psychopy.app.dialogs import ListWidget
from psychopy.colors import Color
from psychopy.localization import _translate
from psychopy import data, prefs, experiment
import re
from pathlib import Path

from ..localizedStrings import _localizedDialogs as _localized
from ...themes import icons, fonts


class _ValidatorMixin:
    def validate(self, evt=None):
        """Redirect validate calls to global validate method, assigning
        appropriate `valType`.
        """
        validate(self, self.valType)

        if evt is not None:
            evt.Skip()

    def showValid(self, valid):
        """Style input box according to valid"""
        if not hasattr(self, "SetForegroundColour"):
            return

        if valid:
            self.SetForegroundColour(wx.Colour(0, 0, 0))
        else:
            self.SetForegroundColour(wx.Colour(1, 0, 0))

    def updateCodeFont(self, valType):
        """Style input box according to code wanted"""
        if not hasattr(self, "SetFont"):
            # Skip if font not applicable to object type
            return
        if self.GetName() == "name":
            # Name is never code
            valType = "str"

        fontNormal = self.GetTopLevelParent().app._mainFont
        if valType == "code" or hasattr(self, "dollarLbl"):
            # Set font
            fontCode = self.GetTopLevelParent().app._codeFont
            fontCodeBold = fontCode.Bold()
            if fontCodeBold.IsOk():
                self.SetFont(fontCodeBold)
            else:
                # use normal font if the bold version is invalid on the system
                self.SetFont(fontCode)
        else:
            self.SetFont(fontNormal)


class _FileMixin:
    @property
    def rootDir(self):
        if not hasattr(self, "_rootDir"):
            # Store location of root directory if not defined
            self._rootDir = Path(self.GetTopLevelParent().frame.exp.filename)
            if self._rootDir.is_file():
                # Move up a dir if root is a file
                self._rootDir = self._rootDir.parent
        # Return stored rootDir
        return self._rootDir
    @rootDir.setter
    def rootDir(self, value):
        self._rootDir = value

    def getFile(self, msg="Specify file ...", wildcard="All Files (*.*)|*.*"):
        dlg = wx.FileDialog(self, message=_translate(msg), defaultDir=str(self.rootDir),
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                            wildcard=_translate(wildcard))
        if dlg.ShowModal() != wx.ID_OK:
            return
        file = dlg.GetPath()
        try:
            filename = Path(file).relative_to(self.rootDir)
        except ValueError:
            filename = Path(file).absolute()
        return str(filename).replace("\\", "/")

    def getFiles(self, msg="Specify file or files...", wildcard="All Files (*.*)|*.*"):
        dlg = wx.FileDialog(self, message=_translate(msg), defaultDir=str(self.rootDir),
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE,
                            wildcard=_translate(wildcard))
        if dlg.ShowModal() != wx.ID_OK:
            return
        inList = dlg.GetPaths()
        outList = []
        for file in inList:
            try:
                filename = Path(file).relative_to(self.rootDir)
            except ValueError:
                filename = Path(file).absolute()
            outList.append(str(filename).replace("\\", "/"))
        return outList

    def getFolder(self, msg=_translate("Specify folder...")):
        # Open dialog
        dlg = wx.DirDialog(self, message=msg, defaultPath=str(self.rootDir),
                           style=wx.DD_SHOW_HIDDEN)
        if dlg.ShowModal() != wx.ID_OK:
            return
        # Get folder
        file = dlg.GetPath()
        try:
            dirname = Path(file).relative_to(self.rootDir)
        except ValueError:
            dirname = Path(file).absolute()
        return str(dirname).replace("\\", "/")


class _HideMixin:
    def ShowAll(self, visible):
        # Get sizer, if present
        if hasattr(self, "_szr"):
            sizer = self._szr
        elif isinstance(self, DictCtrl):
            sizer = self
        else:
            sizer = self.GetSizer()
        # If there is a sizer, recursively hide children
        if sizer is not None:
            self.tunnelShow(sizer, visible)
        else:
            self.Show(visible)

    def HideAll(self):
        self.Show(False)

    def tunnelShow(self, sizer, visible):
        if sizer is not None:
            # Show/hide everything in the sizer
            for child in sizer.Children:
                if child.Window is not None:
                    child.Window.Show(visible)
                if child.Sizer is not None:
                    # If child is a sizer, recur
                    self.tunnelShow(child.Sizer, visible)


class _IconListMixin:
    def setupIcons(self):
        """
        Setup ImageList to handle icons for different filetypes and value types
        """
        # Create new ImageList
        self.imageList = wx.ImageList(16, 16)
        # Add each icon to list and store index
        self.iconIndices = {}
        for key in icons.filetypeIcons:
            self.iconIndices[key] = self.imageList.Add(
                    icons.ButtonIcon(icons.filetypeIcons[key], size=(16, 16)).bitmap
            )
        # Add custom icons (code and str)
        self.iconIndices["code"] = self.imageList.Add(
            icons.ButtonIcon(stem="filecode", size=16).bitmap
        )
        self.iconIndices["str"] = self.imageList.Add(
            icons.ButtonIcon(stem="filestr", size=16).bitmap
        )
        # Set image list
        self.SetImageList(self.imageList, wx.IMAGE_LIST_SMALL)
        self.Update()

    @staticmethod
    def getItemExt(item, rootDir=""):
        rootDir = Path(rootDir)
        # Get extension
        if str(item).startswith("$"):
            # If item is code, interpret literally and set icon to indicate code
            ext = "code"
        else:
            file = Path(item)
            if file.suffix in icons.filetypeIcons:
                # Get extension if it has a corresponding icon
                ext = file.suffix
            elif file.is_dir() or (rootDir / file).is_dir():
                # Extension for a directory is \
                ext = "\\"
            elif file.is_file() or (rootDir / file).is_file():
                # Use unknown extension otherwise
                ext = ".?"
            else:
                # If it's not a file, assume string
                ext = "str"

        return ext


class SingleLineCtrl(wx.TextCtrl, _ValidatorMixin, _HideMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 24), style=wx.TE_LEFT):
        # Create self
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size, style=style)
        self.valType = valType

        # On MacOS, we need to disable smart quotes
        if sys.platform == 'darwin':
            self.OSXDisableAllSmartSubstitutions()

        # Add sizer
        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        if not valType == "str" and not fieldName == "name":
            # Add $ for anything to be interpreted verbatim
            self.dollarLbl = wx.StaticText(parent, -1, "$", size=wx.Size(-1, -1), style=wx.ALIGN_RIGHT)
            self.dollarLbl.SetToolTip(_translate("This parameter will be treated as code - we have already put in the $, so you don't have to."))
            self._szr.Add(self.dollarLbl, border=5, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT)
        # Add self to sizer
        self._szr.Add(self, proportion=1, border=5, flag=wx.EXPAND)
        # Bind to validation
        self.Bind(wx.EVT_CHAR, self.validate)
        self.validate()

    def Show(self, value=True):
        wx.TextCtrl.Show(self, value)
        if hasattr(self, "dollarLbl"):
            self.dollarLbl.Show(value)
        if hasattr(self, "deleteBtn"):
            self.deleteBtn.Show(value)


class MultiLineCtrl(SingleLineCtrl, _ValidatorMixin, _HideMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 144)):
        SingleLineCtrl.__init__(self, parent, valType,
                                val=val, fieldName=fieldName,
                                size=size, style=wx.TE_MULTILINE)


class InvalidCtrl(SingleLineCtrl, _ValidatorMixin, _HideMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 24), style=wx.DEFAULT):
        SingleLineCtrl.__init__(self, parent, valType,
                                val=val, fieldName=fieldName,
                                size=size, style=style)
        self.Disable()
        # Add delete button
        self.deleteBtn = wx.Button(parent, label="×", size=(24, 24))
        self.deleteBtn.SetForegroundColour("red")
        self.deleteBtn.Bind(wx.EVT_BUTTON, self.deleteParam)
        self.deleteBtn.SetToolTip(_translate(
            "This parameter has come from an older version of PsychoPy. "
            "In the latest version of PsychoPy, it is not used. Click this "
            "button to delete it. WARNING: This may affect how this experiment "
            "works in older versions!"))
        self._szr.Add(self.deleteBtn, border=6, flag=wx.LEFT | wx.RIGHT)
        # Add deleted label
        self.deleteLbl = wx.StaticText(parent, label=_translate("DELETED"))
        self.deleteLbl.SetForegroundColour("red")
        self.deleteLbl.Hide()
        self._szr.Add(self.deleteLbl, border=6, proportion=1, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        # Add undo delete button
        self.undoBtn = wx.Button(parent, label="⟲", size=(24, 24))
        self.undoBtn.SetToolTip(_translate(
            "This parameter will not be deleted until you click Okay. "
            "Click this button to revert the deletion and keep the parameter."))
        self.undoBtn.Hide()
        self.undoBtn.Bind(wx.EVT_BUTTON, self.undoDelete)
        self._szr.Add(self.undoBtn, border=6, flag=wx.LEFT | wx.RIGHT)

        # Set deletion flag
        self.forDeletion = False

    def deleteParam(self, evt=None):
        """
        When the remove button is pressed, mark this param as for deletion
        """
        # Mark for deletion
        self.forDeletion = True
        # Hide value ctrl and delete button
        self.Hide()
        self.deleteBtn.Hide()
        # Show delete label and
        self.undoBtn.Show()
        self.deleteLbl.Show()

        self._szr.Layout()

    def undoDelete(self, evt=None):
        # Mark not for deletion
        self.forDeletion = False
        # Show value ctrl and delete button
        self.Show()
        self.deleteBtn.Show()
        # Hide delete label and
        self.undoBtn.Hide()
        self.deleteLbl.Hide()

        self._szr.Layout()


class IntCtrl(wx.SpinCtrl, _ValidatorMixin, _HideMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 24), limits=None):
        wx.SpinCtrl.__init__(self)
        limits = limits or (-100,100)
        self.Create(parent, -1, str(val), name=fieldName, size=size, min=min(limits), max=max(limits))
        self.valType = valType
        self.Bind(wx.EVT_SPINCTRL, self.spin)

    def spin(self, evt):
        """Redirect validate calls to global validate method, assigning appropriate valType"""
        if evt.EventType == wx.EVT_SPIN_UP.evtType[0]:
            self.SetValue(str(int(self.GetValue())+1))
        elif evt.EventType == wx.EVT_SPIN_DOWN.evtType[0]:
            self.SetValue(str(int(self.GetValue()) - 1))
        validate(self, "int")


BoolCtrl = wx.CheckBox


class ChoiceCtrl(wx.Choice, _ValidatorMixin, _HideMixin):
    def __init__(self, parent, valType,
                 val="", choices=[], labels=[], fieldName="",
                 size=wx.Size(-1, 24)):
        self._choices = list(choices)
        # If not given any labels, alias values
        if not labels:
            labels = self._choices
        # Map labels to values
        self._labels = {}
        for i, value in enumerate(self._choices):
            if i < len(labels):
                self._labels[value] = labels[i]
            else:
                self._labels[value] = value
        # Translate labels
        for k in self._labels.keys():
            if k in _localized:
                self._labels[k] = _localized[k]
        # Create choice ctrl from labels
        wx.Choice.__init__(self)
        self.Create(parent, -1, size=size, choices=[self._labels[c] for c in self._choices], name=fieldName)
        self.valType = valType
        self.SetStringSelection(val)

    def SetStringSelection(self, string):
        if string not in self._choices:
            self._choices.append(string)
            self._labels[string] = string
            self.SetItems(
                [self._labels[c] for c in self._choices]
            )
        # Don't use wx.Choice.SetStringSelection here because label string is localized.
        wx.Choice.SetSelection(self, self._choices.index(string))

    def GetValue(self):
        # Don't use wx.Choice.GetStringSelection here because label string is localized.
        return self._choices[self.GetSelection()]


class MultiChoiceCtrl(wx.CheckListBox, _ValidatorMixin, _HideMixin):
    def __init__(self, parent, valType,
                 vals="", choices=[], fieldName="",
                 size=wx.Size(-1, -1)):
        wx.CheckListBox.__init__(self)
        self.Create(parent, id=wx.ID_ANY, size=size, choices=choices, name=fieldName, style=wx.LB_MULTIPLE)
        self.valType = valType
        self._choices = choices
        # Make initial selection
        if isinstance(vals, str):
            # Convert to list if needed
            vals = data.utils.listFromString(vals, excludeEmpties=True)
        self.SetCheckedStrings(vals)
        self.validate()

    def SetCheckedStrings(self, strings):
        if not isinstance(strings, (list, tuple)):
            strings = [strings]
        for s in strings:
            if s not in self._choices:
                self._choices.append(s)
                self.SetItems(self._choices)
        wx.CheckListBox.SetCheckedStrings(self, strings)

    def GetValue(self, evt=None):
        return self.GetCheckedStrings()


class FileCtrl(wx.TextCtrl, _ValidatorMixin, _HideMixin, _FileMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        # Create self
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)
        self.valType = valType
        # Add sizer
        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        self._szr.Add(self, border=5, proportion=1, flag=wx.EXPAND | wx.RIGHT)
        # Add button to browse for file
        fldr = icons.ButtonIcon(stem="folder", size=16).bitmap
        self.findBtn = wx.BitmapButton(parent, -1, size=wx.Size(24, 24), bitmap=fldr)
        self.findBtn.SetToolTip(_translate("Specify file ..."))
        self.findBtn.Bind(wx.EVT_BUTTON, self.findFile)
        self._szr.Add(self.findBtn)
        # Configure validation
        self.Bind(wx.EVT_TEXT, self.validate)
        self.validate()

    def findFile(self, evt):
        file = self.getFile()
        if file:
            self.SetValue(file)
            self.validate(evt)


class FileListCtrl(ListCtrlAutoWidthMixin, wx.ListCtrl, _ValidatorMixin, _HideMixin, _FileMixin, _IconListMixin):
    def __init__(self, parent, valType,
                 choices=[], size=None, pathtype="rel"):
        # Setup base class
        wx.ListCtrl.__init__(self, parent, size=size, style=wx.LC_REPORT | wx.LC_NO_HEADER)
        self.valType = valType
        self.app = parent.app

        # Setup sizers
        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        self._szr.Add(self, proportion=1, flag=wx.ALL | wx.EXPAND)
        self.btnSizer = wx.BoxSizer(wx.VERTICAL)
        self._szr.Add(self.btnSizer, border=6, flag=wx.LEFT | wx.EXPAND)
        # Create add button
        self.addBtn = wx.Button(parent, -1, label="+", size=(24, 24))
        self.addBtn.Bind(wx.EVT_BUTTON, self.onAddItem)
        self.btnSizer.Add(self.addBtn, border=3, flag=wx.BOTTOM | wx.EXPAND)
        # Create sub button
        self.subBtn = wx.Button(parent, -1, label="-", size=(24, 24))
        self.subBtn.Bind(wx.EVT_BUTTON, self.onRemoveItem)
        self.btnSizer.Add(self.subBtn, border=3, flag=wx.BOTTOM | wx.EXPAND)
        # Create edit button
        self.editBtn = wx.Button(parent, -1, label=chr(int("270E", 16)), size=(24, 24))
        self.editBtn.Bind(wx.EVT_BUTTON, self.onEditItem)
        self.btnSizer.Add(self.editBtn, border=3, flag=wx.BOTTOM | wx.EXPAND)

        # Add ondrop functionality
        parent.Bind(wx.EVT_DROP_FILES, self.onAddFile)
        # Setup icon list
        self.setupIcons()
        # Parse initial items
        if type(choices) == str:
            choices = data.utils.listFromString(choices)
        # Populate ctrl
        self.AppendColumn("items", width=wx.LIST_AUTOSIZE)
        self.setResizeColumn("LAST")
        for choice in choices:
            self.addItem(choice)

    def getValue(self):
        values = []
        for i in range(self.GetItemCount()):
            values.append(self.GetItemText(i))
        return values

    def GetValue(self):
        return self.getValue()

    def addItem(self, item, index=None):
        ext = self.getItemExt(item, rootDir=self.rootDir)
        # Get icon from extension
        icn = self.iconIndices[ext]
        # Handle None index
        if index is None:
            index = self.GetItemCount()
        # Create item
        itemObj = wx.ListItem()
        itemObj.SetText(str(item))
        itemObj.SetImage(icn)
        itemObj.SetId(index)
        # Style code
        if ext == "code":
            codeFont = fonts.coderTheme.base.obj
            itemObj.SetFont(codeFont.Bold())
        # Add item
        self.InsertItem(itemObj)
        # Update column width
        self.SetColumnWidth(0, wx.LIST_AUTOSIZE)

    def onRemoveItem(self, event):
        # Get selected item
        item = self.GetFocusedItem()
        # Skip if no item selected
        if item is -1:
            return
        # Remove item
        self.DeleteItem(item)

    def onEditItem(self, event):
        # Get selected item index
        i = self.GetFocusedItem()
        if i == -1:
            return
        item = self.GetItem(i)

        # Create string dialog
        msg = _translate("Edit item...")
        dlg = wx.TextEntryDialog(parent=self, value=item.GetText(), message=msg)
        # Show dialog
        if dlg.ShowModal() != wx.ID_OK:
            return
        # Get string
        stringEntry = dlg.GetValue()

        # Replace item
        self.DeleteItem(i)
        self.addItem(stringEntry, index=i)

    def onAddItem(self, event):
        """
        When the Add button is clicked, create a context menu to point to sub-functions
        """
        # Create menu
        menu = wx.Menu()
        # Add file
        btn = menu.Append(
            wx.ID_ANY,
            item=_translate("Add file(s)..."),
            helpString =_translate(
                "Add a file or files to this list."
            ),
            kind=wx.ITEM_NORMAL
        )
        btn.SetBitmap(
            icons.ButtonIcon(stem="fileunknown16", size=16).bitmap
        )
        menu.Bind(wx.EVT_MENU, self.onAddFile, btn)
        # Add folder
        btn = menu.Append(
            wx.ID_ANY,
            item=_translate("Add folder..."),
            helpString =_translate(
                "Add a folder to this list."
            ),
            kind=wx.ITEM_NORMAL
        )
        btn.SetBitmap(
            icons.ButtonIcon(stem="folder16", size=16).bitmap
        )
        menu.Bind(wx.EVT_MENU, self.onAddFolder, btn)
        # Add code
        btn = menu.Append(
            wx.ID_ANY,
            item=_translate("Add code..."),
            helpString =_translate(
                "Add a value to this list - will include a $ so that it is written as code."
            ),
            kind=wx.ITEM_NORMAL
        )
        btn.SetBitmap(
            icons.ButtonIcon(stem="filecode", size=16).bitmap
        )
        menu.Bind(wx.EVT_MENU, self.onAddCode, btn)
        # Add string
        btn = menu.Append(
            wx.ID_ANY,
            item=_translate("Add string..."),
            helpString =_translate(
                "Add a value to this list - will not include a $, so will be written as a string."
            ),
            kind=wx.ITEM_NORMAL
        )
        btn.SetBitmap(
            icons.ButtonIcon(stem="filestr", size=16).bitmap
        )
        menu.Bind(wx.EVT_MENU, self.onAddValue, btn)
        # Show menu
        obj = event.GetEventObject()
        obj.PopupMenu(menu, (0, obj.GetSize()[1]))

    def onAddFile(self, event):
        """
        When the Add File button is clicked
        """
        files = self.getFiles()
        if files is None:
            return
        for file in files:
            self.addItem(file, index=0)

    def onAddFolder(self, event):
        """
        When the Add Folder button is clicked
        """
        folder = self.getFolder()
        if folder is None:
            return
        self.addItem(folder, index=0)

    def onAddCode(self, event):
        """
        When the Add Code button is clicked
        """
        # Call the usual add value function to get value, but mark as code
        self.onAddValue(event, code=True)

    def onAddValue(self, event, code=False):
        """
        When the Add Value button is clicked
        """
        # Create string dialog
        if code:
            msg = _translate("Add code item...")
        else:
            msg = _translate("Add string item...")
        dlg = wx.TextEntryDialog(parent=self, message=msg)
        # Style if code
        for child in dlg.GetChildren():
            if isinstance(child, wx.TextCtrl):
                print(child)
        # Show dialog
        if dlg.ShowModal() != wx.ID_OK:
            return
        # Get string
        stringEntry = dlg.GetValue()
        # Append $ for code
        if code:
            stringEntry = f"${stringEntry}"
        # Add to list
        if stringEntry:
            self.addItem(stringEntry, index=0)


class TableCtrl(wx.TextCtrl, _ValidatorMixin, _HideMixin, _FileMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        # Create self
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)
        self.valType = valType
        # Add sizer
        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        self._szr.Add(self, proportion=1, border=5, flag=wx.EXPAND | wx.RIGHT)
        # Add button to browse for file
        fldr = icons.ButtonIcon(stem="folder", size=16).bitmap
        self.findBtn = wx.BitmapButton(parent, -1, size=wx.Size(24,24), bitmap=fldr)
        self.findBtn.SetToolTip(_translate("Specify file ..."))
        self.findBtn.Bind(wx.EVT_BUTTON, self.findFile)
        self._szr.Add(self.findBtn)
        # Add button to open in Excel
        xl = icons.ButtonIcon(stem="filecsv", size=16).bitmap
        self.xlBtn = wx.BitmapButton(parent, -1, size=wx.Size(24,24), bitmap=xl)
        self.xlBtn.SetToolTip(_translate("Open/create in your default table editor"))
        self.xlBtn.Bind(wx.EVT_BUTTON, self.openExcel)
        self._szr.Add(self.xlBtn)
        # Link to Excel templates for certain contexts
        cmpRoot = Path(experiment.components.__file__).parent
        expRoot = Path(cmpRoot).parent
        self.templates = {
            'Form': Path(cmpRoot) / "form" / "formItems.xltx",
            'TrialHandler': Path(expRoot) / "loopTemplate.xltx",
            'StairHandler': Path(expRoot) / "loopTemplate.xltx",
            'MultiStairHandler': Path(expRoot) / "loopTemplate.xltx",
            'QuestHandler': Path(expRoot) / "loopTemplate.xltx",
            'None': Path(expRoot) / 'blankTemplate.xltx',
        }
        # Specify valid extensions
        self.validExt = [".csv",".tsv",".txt",
                         ".xl",".xlsx",".xlsm",".xlsb",".xlam",".xltx",".xltm",".xls",".xlt",
                         ".htm",".html",".mht",".mhtml",
                         ".xml",".xla",".xlm",
                         ".odc",".ods",
                         ".udl",".dsn",".mdb",".mde",".accdb",".accde",".dbc",".dbf",
                         ".iqy",".dqy",".rqy",".oqy",
                         ".cub",".atom",".atomsvc",
                         ".prn",".slk",".dif"]
        # Configure validation
        self.Bind(wx.EVT_TEXT, self.validate)
        self.validate()

    def validate(self, evt=None):
        """Redirect validate calls to global validate method, assigning appropriate valType"""
        validate(self, "file")
        # Enable Excel button if valid
        self.xlBtn.Enable(self.valid)
        # Is component type available?
        if self.GetValue() in [None, ""] + self.validExt and hasattr(self.GetTopLevelParent(), 'type'):
            # Does this component have a default template?
            if self.GetTopLevelParent().type in self.templates:
                self.xlBtn.Enable(True)

    def openExcel(self, event):
        """Either open the specified excel sheet, or make a new one from a template"""
        file = self.rootDir / self.GetValue()
        if not (file.is_file() and file.suffix in self.validExt): # If not a valid file
            dlg = wx.MessageDialog(self, _translate(
                "Once you have created and saved your table,"
                "please remember to add it to {name}").format(name=_translate(self.Name)),
                             caption=_translate("Reminder"))
            dlg.ShowModal()
            if hasattr(self.GetTopLevelParent(), 'type'):
                if self.GetTopLevelParent().type in self.templates:
                    file = self.templates[self.GetTopLevelParent().type] # Open type specific template
                else:
                    file = self.templates['None'] # Open blank template
        # Open whatever file is used
        try:
            os.startfile(file)
        except AttributeError:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, file])

    def findFile(self, event):
        _wld = f"All Table Files({'*'+';*'.join(self.validExt)})|{'*'+';*'.join(self.validExt)}|All Files (*.*)|*.*"
        file = self.getFile(msg="Specify table file ...", wildcard=_wld)
        if file:
            self.SetValue(file)
            self.validate(event)


class ColorCtrl(wx.TextCtrl, _ValidatorMixin, _HideMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        # Create self
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)
        self.valType = valType
        # Add sizer
        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        if valType == "code":
            # Add $ for anything to be interpreted verbatim
            self.dollarLbl = wx.StaticText(parent, -1, "$", size=wx.Size(-1, -1), style=wx.ALIGN_RIGHT)
            self.dollarLbl.SetToolTip(_translate("This parameter will be treated as code - we have already put in the $, so you don't have to."))
            self._szr.Add(self.dollarLbl, border=5, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT)
        # Add ctrl to sizer
        self._szr.Add(self, proportion=1, border=5, flag=wx.EXPAND | wx.RIGHT)
        # Add button to activate color picker
        fldr = icons.ButtonIcon(stem="color", size=16).bitmap
        self.pickerBtn = wx.BitmapButton(parent, -1, size=wx.Size(24,24), bitmap=fldr)
        self.pickerBtn.SetToolTip(_translate("Specify color ..."))
        self.pickerBtn.Bind(wx.EVT_BUTTON, self.colorPicker)
        self._szr.Add(self.pickerBtn)
        # Bind to validation
        self.Bind(wx.EVT_CHAR, self.validate)
        self.validate()

    def colorPicker(self, evt):
        dlg = PsychoColorPicker(self, context=self, allowCopy=False)  # open a color picker
        dlg.ShowModal()
        dlg.Destroy()


def validate(obj, valType):
    val = str(obj.GetValue())
    valid = True
    if val.startswith("$"):
        # If indicated as code, treat as code
        valType = "code"
    # Validate string
    if valType == "str":
        if re.findall(r"(?<!\\)\"", val):
            # If there are unescaped "
            valid = False
        if re.findall(r"(?<!\\)\'", val):
            # If there are unescaped '
            valid = False
    # Validate code
    if valType == "code":
        # Replace unescaped curly quotes
        if re.findall(r"(?<!\\)[\u201c\u201d]", val):
            pt = obj.GetInsertionPoint()
            obj.SetValue(re.sub(r"(?<!\\)[\u201c\u201d]", "\"", val))
            obj.SetInsertionPoint(pt)
        # For now, ignore
        pass
    # Validate num
    if valType in ["num", "int"]:
        try:
            # Try to convert value to a float
            float(val)
        except ValueError:
            # If conversion fails, value is invalid
            valid = False
    # Validate bool
    if valType == "bool":
        if val not in ["True", "False"]:
            # If value is not True or False, it is invalid
            valid = False
    # Validate list
    if valType == "list":
        empty = not bool(val) # Is value empty?
        fullList = re.fullmatch(r"[\(\[].*[\]\)]", val) # Is value full list with parentheses?
        partList = "," in val and not re.match(r"[\(\[].*[\]\)]", val) # Is value list without parentheses?
        singleVal = not " " in val or re.match(r"[\"\'].*[\"\']", val) # Is value a single value?
        if not any([empty, fullList, partList, singleVal]):
            # If value is not any of valid types, it is invalid
            valid = False
    # Validate color
    if valType == "color":
        # Strip function calls
        if re.fullmatch(r"\$?(Advanced)?Color\(.*\)", val):
            val = re.sub(r"\$?(Advanced)?Color\(", "", val[:-1])
        try:
            # Try to create a Color object from value
            obj.color = Color(val, False)
            if not obj.color:
                # If invalid object is created, input is invalid
                valid = False
        except:
            # If object creation fails, input is invalid
            valid = False
    if valType == "file":
        val = Path(str(val))
        if not val.is_absolute():
            frame = obj.GetTopLevelParent().frame
            # If not an absolute path, append to current directory
            val = Path(frame.filename).parent / val
        if not val.is_file():
            # Is value a valid filepath?
            valid = False
        if hasattr(obj, "validExt"):
            # If control has specified list of ext, does value end in correct ext?
            if val.suffix not in obj.validExt:
                valid = False

    # If additional allowed values are defined, override validation
    if hasattr(obj, "allowedVals"):
        if val in obj.allowedVals:
            valid = True

    # Apply valid status to object
    obj.valid = valid
    if hasattr(obj, "showValid"):
        obj.showValid(valid)

    # Update code font
    obj.updateCodeFont(valType)


class DictCtrl(ListWidget, _ValidatorMixin, _HideMixin):
    def __init__(self, parent,
                 val={}, valType='dict',
                 fieldName=""):
        if not isinstance(val, (dict, list)):
            raise ValueError("DictCtrl must be supplied with either a dict or a list of 1-long dicts, value supplied was {}".format(val))
        # If supplied with a dict, convert it to a list of dicts
        if isinstance(val, dict):
            newVal = []
            for key, v in val.items():
                newVal.append({'Field': key, 'Default': v.val})
            val = newVal
        # If any items within the list are not dicts or are dicts longer than 1, throw error
        if not all(isinstance(v, dict) and len(v) == 2 for v in val):
            raise ValueError("DictCtrl must be supplied with either a dict or a list of 1-long dicts, value supplied was {}".format(val))
        # Create ListWidget
        ListWidget.__init__(self, parent, val, order=['Field', 'Default'])

    def SetForegroundColour(self, color):
        for child in self.Children:
            if hasattr(child, "SetForegroundColour"):
                child.SetForegroundColour(color)

    def Enable(self, enable=True):
        """
        Enable or disable all items in the dict ctrl
        """
        # Iterate through all children
        for cell in self.Children:
            # Get the actual child rather than the sizer item
            child = cell.Window
            # If it can be enabled/disabled, enable/disable it
            if hasattr(child, "Enable"):
                child.Enable(enable)

    def Disable(self):
        """
        Disable all items in the dict ctrl
        """
        self.Enable(False)

    def Show(self, show=True):
        """
        Show or hide all items in the dict ctrl
        """
        # Iterate through all children
        for cell in self.Children:
            # Get the actual child rather than the sizer item
            child = cell.Window
            # If it can be shown/hidden, show/hide it
            if hasattr(child, "Show"):
                child.Show(show)

    def Hide(self):
        """
        Hide all items in the dict ctrl
        """
        self.Show(False)
