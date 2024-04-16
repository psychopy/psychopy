#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import ast
import os
import subprocess
import sys
import webbrowser

import wx
import wx.stc

from psychopy.app.colorpicker import PsychoColorPicker
from psychopy.app.dialogs import ListWidget
from psychopy.colors import Color
from psychopy.localization import _translate
from psychopy import data, prefs, experiment
import re
from pathlib import Path

from . import CodeBox
from ...coder import BaseCodeEditor
from ...themes import icons, handlers
from ... import utils
from ...themes import icons


class _FrameMixin:
    @property
    def frame(self):
        """
        Top level frame associated with this ctrl
        """
        topParent = self.GetTopLevelParent()
        if hasattr(topParent, "frame"):
            return topParent.frame
        else:
            return topParent


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
            self.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNTEXT))
        else:
            self.SetForegroundColour(wx.Colour(1, 0, 0))

    def updateCodeFont(self, valType):
        """Style input box according to code wanted"""
        if not hasattr(self, "SetStyle"):
            # Skip if font not applicable to object type
            return
        if self.GetName() == "name":
            # Name is never code
            valType = "str"

        # get font
        if valType == "code" or hasattr(self, "dollarLbl"):
            font = self.GetTopLevelParent().app._codeFont.Bold()
        else:
            font = self.GetTopLevelParent().app._mainFont

        # set font
        if sys.platform == "linux":
            # have to go via SetStyle on Linux
            style = wx.TextAttr(self.GetForegroundColour(), font=font)
            self.SetStyle(0, len(self.GetValue()), style)
        else:
            # otherwise SetFont is fine
            self.SetFont(font)


class _FileMixin(_FrameMixin):
    @property
    def rootDir(self):
        if not hasattr(self, "_rootDir"):
            # Store location of root directory if not defined
            self._rootDir = Path(self.frame.exp.filename)
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
        self.Bind(wx.EVT_TEXT, self.validate)
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


class CodeCtrl(BaseCodeEditor, handlers.ThemeMixin, _ValidatorMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 144)):
        BaseCodeEditor.__init__(self, parent,
                                ID=wx.ID_ANY, pos=wx.DefaultPosition, size=size,
                                style=0)
        self.valType = valType
        self.SetValue(val)
        self.fieldName = fieldName
        self.params = fieldName
        # Setup lexer to style text
        self.SetLexer(wx.stc.STC_LEX_PYTHON)
        self._applyAppTheme()
        # Hide margin
        self.SetMarginWidth(0, 0)
        # Setup auto indent behaviour as in Code component
        self.Bind(wx.EVT_KEY_DOWN, self.onKey)

    def getValue(self, evt=None):
        return self.GetValue()

    def setValue(self, value):
        self.SetValue(value)

    @property
    def val(self):
        """
        Alias for Set/GetValue, as .val is used elsewhere
        """
        return self.getValue()

    @val.setter
    def val(self, value):
        self.setValue(value)

    def onKey(self, evt=None):
        CodeBox.OnKeyPressed(self, evt)


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
                 size=wx.Size(-1, -1)):
        self._choices = choices
        self._labels = labels
        # Create choice ctrl from labels
        wx.Choice.__init__(self)
        self.Create(parent, -1, name=fieldName)
        self.populate()
        self.valType = valType
        self.SetStringSelection(val)

    def populate(self):
        if callable(self._choices):
            # if choices are given as a partial, execute it now to get values
            choices = self._choices()
        else:
            # otherwise, treat it as a list
            choices = list(self._choices)

        if callable(self._labels):
            # if labels are given as a partial, execute it now to get values
            labels = self._labels()
        elif self._labels:
            # otherwise, treat it as a list
            labels = list(self._labels)
        else:
            # if not given any labels, alias values
            labels = choices
        # Map labels to values
        _labels = {}
        for i, value in enumerate(choices):
            if i < len(labels):
                _labels[value] = _translate(labels[i]) if labels[i] != '' else ''
            else:
                _labels[value] = _translate(value) if value != '' else ''
        labels = _labels
        # store labels and choices
        self.labels = labels
        self.choices = choices

        # apply to ctrl
        self.SetItems([str(self.labels[c]) for c in self.choices])

    def SetStringSelection(self, string):
        strChoices = [str(choice) for choice in self.choices]
        if string not in self.choices:
            if string in strChoices:
                # If string is a stringified version of a value in choices, stringify the value in choices
                i = strChoices.index(string)
                self.labels[string] = self.labels.pop(self.choices[i])
                self.choices[i] = string
            else:
                # Otherwise it is a genuinely new value, so add it to options
                self.choices.append(string)
                self.labels[string] = string
            # Refresh items
            self.SetItems(
                [str(self.labels[c]) for c in self.choices]
            )
        # Don't use wx.Choice.SetStringSelection here because label string is localized.
        wx.Choice.SetSelection(self, self.choices.index(string))

    def getValue(self):
        # Don't use wx.Choice.GetStringSelection here because label string is localized.
        return self.choices[self.GetSelection()]


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


class RichChoiceCtrl(wx.Panel, _ValidatorMixin, _HideMixin):
    class RichChoiceItem(wx.Panel):
        def __init__(self, parent, value, label, body="", linkText="", link="", startShown="always", viewToggle=True):
            # Initialise
            wx.Panel.__init__(self, parent, style=wx.BORDER_THEME)
            self.parent = parent
            self.value = value
            self.startShown = startShown
            # Setup sizer
            self.border = wx.BoxSizer()
            self.SetSizer(self.border)
            self.sizer = wx.FlexGridSizer(cols=3)
            self.sizer.AddGrowableCol(idx=1, proportion=1)
            self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
            # Check
            self.check = wx.CheckBox(self, label=" ")
            self.check.Bind(wx.EVT_CHECKBOX, self.onCheck)
            self.check.Bind(wx.EVT_KEY_UP, self.onToggle)
            self.sizer.Add(self.check, border=3, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
            # Title
            self.title = wx.StaticText(self, label=label)
            self.title.SetFont(self.title.GetFont().Bold())
            self.sizer.Add(self.title, border=3,  flag=wx.ALL | wx.EXPAND)
            # Toggle
            self.toggleView = wx.ToggleButton(self, style=wx.BU_EXACTFIT)
            self.toggleView.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleView)
            self.toggleView.Show(viewToggle)
            self.sizer.Add(self.toggleView, border=3, flag=wx.ALL | wx.EXPAND)
            # Body
            self.body = utils.WrappedStaticText(self, label=body)
            self.sizer.AddStretchSpacer(1)
            self.sizer.Add(self.body, border=3, proportion=1, flag=wx.ALL | wx.EXPAND)
            self.sizer.AddStretchSpacer(1)
            # Link
            self.link = utils.HyperLinkCtrl(self, label=linkText, URL=link)
            self.link.SetBackgroundColour(self.GetBackgroundColour())
            self.sizer.AddStretchSpacer(1)
            self.sizer.Add(self.link, border=3, flag=wx.ALL | wx.ALIGN_LEFT)
            self.sizer.AddStretchSpacer(1)

            # Style
            self.SetBackgroundColour("white")
            self.body.SetBackgroundColour("white")
            self.link.SetBackgroundColour("white")

            self.Layout()

        def getChecked(self):
            return self.check.GetValue()

        def setChecked(self, state):
            if self.parent.multi:
                # If multi select is allowed, leave other values unchanged
                values = self.parent.getValue()
                if not isinstance(values, (list, tuple)):
                    values = [values]
                if state:
                    # Add this item to list if checked
                    values.append(self.value)
                else:
                    # Remove this item from list if unchecked
                    if self.value in values:
                        values.remove(self.value)
                self.parent.setValue(values)
            elif state:
                # If single only, set at parent level so others are unchecked
                self.parent.setValue(self.value)

        def onCheck(self, evt):
            self.setChecked(evt.IsChecked())

        def onToggle(self, evt):
            if evt.GetUnicodeKey() in (wx.WXK_SPACE, wx.WXK_NUMPAD_SPACE):
                self.setChecked(not self.check.IsChecked())

        def onToggleView(self, evt):
            # If called with a boolean, use it directly, otherwise get bool from event
            if isinstance(evt, bool):
                val = evt
            else:
                val = evt.IsChecked()
            # Update toggle ctrl label
            if val:
                lbl = "⯆"
            else:
                lbl = "⯇"
            self.toggleView.SetLabel(lbl)
            # Show/hide body based on value
            self.body.Show(val)
            self.link.Show(val)
            # Layout
            self.Layout()
            self.parent.parent.Layout()  # layout params notebook page

    def __init__(self, parent, valType,
                 vals="", fieldName="",
                 choices=[], labels=[],
                 size=wx.Size(-1, -1),
                 viewToggle=True):
        # Initialise
        wx.Panel.__init__(self, parent, size=size)
        self.parent = parent
        self.valType = valType
        self.fieldName = fieldName
        self.multi = False
        self.viewToggle = viewToggle
        # Setup sizer
        self.border = wx.BoxSizer()
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        self.SetSizer(self.border)
        # Store values
        self.choices = {}
        for i, val in enumerate(choices):
            self.choices[val] = labels[i]
        # Populate
        self.populate()
        # Set value
        self.setValue(vals)
        # Start off showing according to param
        for obj in self.items:
            # Work out if we should start out shown
            if self.viewToggle:
                if obj.startShown == "never":
                    startShown = False
                elif obj.startShown == "checked":
                    startShown = obj.check.IsChecked()
                elif obj.startShown == "unchecked":
                    startShown = not obj.check.IsChecked()
                else:
                    startShown = True
            else:
                startShown = True
            # Apply starting view
            obj.toggleView.SetValue(startShown)
            obj.onToggleView(startShown)

        self.Layout()

    def populate(self):
        self.items = []
        for val, label in self.choices.items():
            if not isinstance(label, dict):
                # Make sure label is dict
                label = {"label": label}
            # Add item control
            self.addItem(val, label=label)
        self.Layout()

    def addItem(self, value, label={}):
        # Create item object
        item = self.RichChoiceItem(self, value=value, viewToggle=self.viewToggle, **label)
        self.items.append(item)
        # Add to sizer
        self.sizer.Add(item, border=3, flag=wx.ALL | wx.EXPAND)

    def getValue(self):
        # Get corresponding value for each checked item
        values = []
        for item in self.items:
            if item.getChecked():
                # If checked, append value
                values.append(item.value)
        # Strip list if not multi
        if not self.multi:
            if len(values):
                values = values[0]
            else:
                values = ""

        return values

    def setValue(self, value):
        # Make sure value is iterable
        if not isinstance(value, (list, tuple)):
            value = [value]
        # Check/uncheck corresponding items
        for item in self.items:
            state = item.value in value
            item.check.SetValue(state)

        # Post event
        evt = wx.ListEvent(commandType=wx.EVT_CHOICE.typeId, id=-1)
        evt.SetEventObject(self)
        wx.PostEvent(self, evt)

        self.Layout()


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
        fldr = icons.ButtonIcon(stem="folder", size=16, theme="light").bitmap
        self.findBtn = wx.BitmapButton(parent, -1, bitmap=fldr, style=wx.BU_EXACTFIT)
        self.findBtn.SetToolTip(_translate("Specify file ..."))
        self.findBtn.Bind(wx.EVT_BUTTON, self.findFile)
        self._szr.Add(self.findBtn)
        # Configure validation
        self.Bind(wx.EVT_TEXT, self.validate)
        self.validate()

    def findFile(self, evt):
        file = self.getFile()
        if file:
            self.setFile(file)
            self.validate(evt)

    def setFile(self, file):
        # Set text value
        wx.TextCtrl.SetValue(self, file)
        # Post event
        evt = wx.FileDirPickerEvent(wx.EVT_FILEPICKER_CHANGED.typeId, self, -1, file)
        evt.SetEventObject(self)
        wx.PostEvent(self, evt)
        # Post keypress event to trigger onchange
        evt = wx.FileDirPickerEvent(wx.EVT_KEY_UP.typeId, self, -1, file)
        evt.SetEventObject(self)
        wx.PostEvent(self, evt)


class FileListCtrl(wx.ListBox, _ValidatorMixin, _HideMixin, _FileMixin):
    def __init__(self, parent, valType,
                 choices=[], size=None, pathtype="rel"):
        wx.ListBox.__init__(self)
        self.valType = valType
        parent.Bind(wx.EVT_DROP_FILES, self.addItem)
        self.app = parent.app
        if type(choices) == str:
            choices = data.utils.listFromString(choices)
        self.Create(id=wx.ID_ANY, parent=parent, choices=choices, size=size, style=wx.LB_EXTENDED | wx.LB_HSCROLL)
        self.addCustomBtn = wx.Button(parent, -1, size=(24,24), style=wx.BU_EXACTFIT, label="...")
        self.addCustomBtn.Bind(wx.EVT_BUTTON, self.addCustomItem)
        self.addBtn = wx.Button(parent, -1, size=(24,24), style=wx.BU_EXACTFIT, label="+")
        self.addBtn.Bind(wx.EVT_BUTTON, self.addItem)
        self.subBtn = wx.Button(parent, -1, size=(24,24), style=wx.BU_EXACTFIT, label="-")
        self.subBtn.Bind(wx.EVT_BUTTON, self.removeItem)
        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        self.btns = wx.BoxSizer(wx.VERTICAL)
        self.btns.AddMany((self.addCustomBtn, self.addBtn, self.subBtn))
        self._szr.Add(self, proportion=1, flag=wx.EXPAND)
        self._szr.Add(self.btns)

    def addItem(self, event):
        # Get files
        if event.GetEventObject() == self.addBtn:
            fileList = self.getFiles()
        else:
            fileList = event.GetFiles()
            for i, filename in enumerate(fileList):
                try:
                    fileList[i] = Path(filename).relative_to(self.rootDir)
                except ValueError:
                    fileList[i] = Path(filename).absolute()
        # Add files to list
        if fileList:
            self.InsertItems(fileList, 0)

    def removeItem(self, event):
        i = self.GetSelections()
        if isinstance(i, int):
            i = [i]
        items = [item for index, item in enumerate(self.Items)
                 if index not in i]
        self.SetItems(items)

    def addCustomItem(self, event):
        # Create string dialog
        dlg = wx.TextEntryDialog(parent=self, message=_translate("Add custom item"))
        # Show dialog
        if dlg.ShowModal() != wx.ID_OK:
            return
        # Get string
        stringEntry = dlg.GetValue()
        # Add to list
        if stringEntry:
            self.InsertItems([stringEntry], 0)

    def GetValue(self):
        return self.Items


class SurveyCtrl(wx.TextCtrl, _ValidatorMixin, _HideMixin):
    class SurveyFinderDlg(wx.Dialog, utils.ButtonSizerMixin):
        def __init__(self, parent, session):
            wx.Dialog.__init__(self, parent=parent, size=(-1, 496), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
            self.session = session
            # Setup sizer
            self.border = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.border)
            self.sizer = wx.BoxSizer(wx.VERTICAL)
            self.border.Add(self.sizer, border=12, proportion=1, flag=wx.ALL | wx.EXPAND)
            # Add instructions
            self.instr = utils.WrappedStaticText(self, label=_translate(
                "Below are all of the surveys linked to your Pavlovia account - select the one you want and "
                "press OK to add its ID."
            ))
            self.sizer.Add(self.instr, border=6, flag=wx.ALL | wx.EXPAND)
            # Add ctrl
            self.ctrl = wx.ListCtrl(self, size=(-1, 248), style=wx.LC_REPORT)
            self.sizer.Add(self.ctrl, border=6, proportion=1, flag=wx.ALL | wx.EXPAND)
            # Add placeholder for when there are no surveys
            self.placeholder = wx.TextCtrl(self, size=(-1, 248), value=_translate(
                "There are no surveys linked to your Pavlovia account."
            ), style=wx.TE_READONLY | wx.TE_MULTILINE)
            self.sizer.Add(self.placeholder, border=6, proportion=1, flag=wx.ALL | wx.EXPAND)
            self.placeholder.Hide()
            # Sizer for extra ctrls
            self.extraCtrls = wx.Panel(self)
            self.extraCtrls.sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.extraCtrls.SetSizer(self.extraCtrls.sizer)
            self.sizer.Add(self.extraCtrls, border=6, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND)
            # Link to Pavlovia
            self.pavLink = utils.HyperLinkCtrl(self.extraCtrls, label=_translate(
                "Click here to manage surveys on Pavlovia."
            ), URL="https://pavlovia.org/dashboard?tab=4")
            self.extraCtrls.sizer.Add(self.pavLink, flag=wx.ALL | wx.ALIGN_LEFT)
            # Update button
            self.updateBtn = wx.Button(self.extraCtrls, size=(24, 24))
            self.updateBtn.SetBitmap(icons.ButtonIcon(stem="view-refresh", size=16).bitmap)
            self.updateBtn.SetToolTip(_translate(
                "Refresh survey list"
            ))
            self.updateBtn.Bind(wx.EVT_BUTTON, self.populate)
            self.extraCtrls.sizer.AddStretchSpacer(prop=1)
            self.extraCtrls.sizer.Add(self.updateBtn, flag=wx.ALL | wx.EXPAND)

            # Setup dialog buttons
            self.btnSizer = self.CreatePsychoPyDialogButtonSizer(flags=wx.OK | wx.CANCEL | wx.HELP)
            self.sizer.AddSpacer(12)
            self.border.Add(self.btnSizer, border=6, flag=wx.ALL | wx.EXPAND)

            # Populate
            self.populate()
            self.Layout()

        def populate(self, evt=None):
            # Clear ctrl
            self.ctrl.ClearAll()
            self.ctrl.InsertColumn(0, "Name")
            self.ctrl.InsertColumn(1, "ID")
            # Ask Pavlovia for list of surveys
            resp = self.session.session.get(
                "https://pavlovia.org/api/v2/surveys",
                timeout=10
            ).json()
            # Get surveys from returned json
            surveys = resp['surveys']
            # If there are no surveys, hide the ctrl and present link to survey designer
            if len(surveys):
                self.ctrl.Show()
                self.placeholder.Hide()
            else:
                self.ctrl.Hide()
                self.placeholder.Show()
            # Populate control
            for survey in surveys:
                self.ctrl.Append([
                    survey['surveyName'],
                    survey['surveyId']
                ])
            # Resize columns
            self.ctrl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
            self.ctrl.SetColumnWidth(1, wx.LIST_AUTOSIZE)

        def getValue(self):
            i = self.ctrl.GetFirstSelected()
            if i > -1:
                return self.ctrl.GetItem(i, col=1).Text
            else:
                return ""

    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        # Create self
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)
        self.valType = valType
        # Add CTRL + click behaviour
        self.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick)
        # Add placeholder
        self.SetHint("e.g. e89cd6eb-296e-4960-af14-103026a59c14")
        # Add sizer
        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        self._szr.Add(self, border=5, proportion=1, flag=wx.EXPAND | wx.RIGHT)
        # Add button to browse for survey
        self.findBtn = wx.Button(
            parent, -1,
            label=_translate("Find online..."),
            size=wx.Size(-1, 24)
        )
        self.findBtn.SetBitmap(
            icons.ButtonIcon(stem="search", size=16).bitmap
        )
        self.findBtn.SetToolTip(_translate(
            "Get survey ID from a list of your surveys on Pavlovia"
        ))
        self.findBtn.Bind(wx.EVT_BUTTON, self.findSurvey)
        self._szr.Add(self.findBtn)
        # Configure validation
        self.Bind(wx.EVT_TEXT, self.validate)
        self.validate()

    def onRightClick(self, evt=None):
        menu = wx.Menu()
        thisId = menu.Append(wx.ID_ANY, item=f"https://pavlovia.org/surveys/{self.getValue()}")
        menu.Bind(wx.EVT_MENU, self.openSurvey, source=thisId)
        self.PopupMenu(menu)

    def openSurvey(self, evt=None):
        """
        Open current survey in web browser
        """
        webbrowser.open(f"https://pavlovia.org/surveys/{self.getValue()}")

    def findSurvey(self, evt=None):
        # Import Pavlovia modules locally to avoid Pavlovia bugs affecting other param ctrls
        from psychopy.projects.pavlovia import getCurrentSession
        from ...pavlovia_ui import checkLogin
        # Get session
        session = getCurrentSession()
        # Check Pavlovia login
        if checkLogin(session):
            # Get session again incase login process changed it
            session = getCurrentSession()
            # Show survey finder dialog
            dlg = self.SurveyFinderDlg(self, session)
            if dlg.ShowModal() == wx.ID_OK:
                # If OK, get value
                self.SetValue(dlg.getValue())
                # Validate
                self.validate()
                # Raise event
                evt = wx.ListEvent(wx.EVT_KEY_UP.typeId)
                evt.SetEventObject(self)
                wx.PostEvent(self, evt)

    def getValue(self, evt=None):
        """
        Get the value of the text control, but sanitize such that if the user pastes a full survey URL
        we only take the survey ID
        """
        # Get value by usual wx method
        value = self.GetValue()
        # Strip pavlovia run url
        if "run.pavlovia.org/pavlovia/survey/?surveyId=" in value:
            # Keep only the values after the URL
            value = value.split("run.pavlovia.org/pavlovia/survey/?surveyId=")[-1]
            if "&" in value:
                # If there are multiple URL parameters, only keep the Id
                value = value.split("&")[0]
        # Strip regular pavlovia url
        elif "pavlovia.org/surveys/" in value:
            # Keep only the values after the URL
            value = value.split(".pavlovia.org/pavlovia/survey/")[-1]
            if "&" in value:
                # If there are URL parameters, only keep the Id
                value = value.split("?")[0]

        return value


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
        fldr = icons.ButtonIcon(stem="folder", size=16, theme="light").bitmap
        self.findBtn = wx.BitmapButton(parent, -1, bitmap=fldr, style=wx.BU_EXACTFIT)
        self.findBtn.SetToolTip(_translate("Specify file ..."))
        self.findBtn.Bind(wx.EVT_BUTTON, self.findFile)
        self._szr.Add(self.findBtn)
        # Add button to open in Excel
        xl = icons.ButtonIcon(stem="filecsv", size=16, theme="light").bitmap
        self.xlBtn = wx.BitmapButton(parent, -1, bitmap=xl, style=wx.BU_EXACTFIT)
        self.xlBtn.SetToolTip(_translate("Open/create in your default table editor"))
        self.xlBtn.Bind(wx.EVT_BUTTON, self.openExcel)
        self._szr.Add(self.xlBtn)
        # Link to Excel templates for certain contexts
        cmpRoot = Path(experiment.components.__file__).parent
        expRoot = Path(cmpRoot).parent
        self.templates = {
            'Form': Path(cmpRoot) / "form" / "formItems.xltx",
            'CounterBalance': Path(expRoot) / "routines" / "counterbalance" / "counterbalanceItems.xltx",
            'TrialHandler': Path(expRoot) / "loopTemplate.xltx",
            'StairHandler': Path(expRoot) / "loopTemplate.xltx",
            'MultiStairHandler:simple': Path(expRoot) / "staircaseTemplate.xltx",
            'MultiStairHandler:QUEST': Path(expRoot) / "questTemplate.xltx",
            'MultiStairHandler:QUESTPLUS': Path() / "questPlugTemplate.xltx",
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
        # Disable Excel button if value is from a variable
        if "$" in self.GetValue():
            self.xlBtn.Disable()
            return
        # enable Excel button if valid
        self.xlBtn.Enable(self.valid)
        # get frame
        frame = self.GetParent()
        if frame is None:
            frame = self.GetTopLevelParent()
        while hasattr(frame, "GetParent") and not (
                hasattr(frame, "routine") or hasattr(frame, "component") or hasattr(frame, "type")
        ):
            frame = frame.GetParent()
        # get comp type from frame
        if hasattr(frame, "component"):
            thisType = frame.component.type
        elif hasattr(frame, "routine"):
            thisType = frame.routine.type
        elif hasattr(frame, "type"):
            thisType = frame.type
        else:
            thisType = None
        # does this component have a default template?
        if thisType in self.templates:
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
            # get frame
            frame = self.GetParent()
            while hasattr(frame, "GetParent") and not (hasattr(frame, "routine") or hasattr(frame, "component")):
                frame = frame.GetParent()
            # get comp type from frame
            if hasattr(frame, "component"):
                thisType = frame.component.type
            elif hasattr(frame, "routine"):
                thisType = frame.routine.type
            elif hasattr(frame, "type"):
                thisType = frame.type
            else:
                thisType = "None"
            # open type specific template, or blank
            if thisType in self.templates:
                file = self.templates[thisType]
            else:
                file = self.templates['None']
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
        fldr = icons.ButtonIcon(stem="color", size=16, theme="light").bitmap
        self.pickerBtn = wx.BitmapButton(parent, -1, bitmap=fldr, style=wx.BU_EXACTFIT)
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
            frame = obj.GetTopLevelParent()
            if hasattr(frame, "frame"):
                frame = frame.frame
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
                 val={}, labels=(_translate("Field"), _translate("Default")), valType='dict',
                 fieldName=""):
        # try to convert to a dict if given a string
        if isinstance(val, str):
            try:
                val = ast.literal_eval(val)
            except:
                raise ValueError(_translate("Could not interpret parameter value as a dict:\n{}").format(val))
        # raise error if still not a dict
        if not isinstance(val, (dict, list)):
            raise ValueError("DictCtrl must be supplied with either a dict or a list of 1-long dicts, value supplied was {}: {}".format(type(val), val))
        # Get labels
        keyLbl, valLbl = labels
        # If supplied with a dict, convert it to a list of dicts
        if isinstance(val, dict):
            newVal = []
            for key, v in val.items():
                if hasattr(v, "val"):
                    v = v.val
                newVal.append({keyLbl: key, valLbl: v})
            val = newVal
        # Make sure we have at least 1 value
        if not len(val):
            val = [{keyLbl: "", valLbl: ""}]
        # If any items within the list are not dicts or are dicts longer than 1, throw error
        if not all(isinstance(v, dict) and len(v) == 2 for v in val):
            raise ValueError("DictCtrl must be supplied with either a dict or a list of 1-long dicts, value supplied was {}".format(val))
        # Create ListWidget
        ListWidget.__init__(self, parent, val, order=labels)

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
