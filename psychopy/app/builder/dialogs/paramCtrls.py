import os
import wx

import psychopy
from psychopy.app.themes import ThemeMixin
from psychopy.localization import _translate
from psychopy import data, logging, prefs
import re

BoolCtrl = wx.CheckBox


ChoiceCtrl = wx.Choice


class ListCtrl(wx.TextCtrl):
    def __init__(self, parent,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)
        self.Bind(wx.EVT_TEXT, self.validate)
        self.style = 'empty'

    def validate(self):
        val = self.GetValue()
        # Start with regular colour
        self.SetForegroundColour(wx.Colour(
            ThemeMixin.codeColors['base']['fg']
        ))
        if not val:
            # If empty, style is empty
            self.style = 'empty'
        elif re.match(r"[\(\[].*[\]\)]", val):
            # If user put contents in parentheses, style is full
            self.style = 'full'
        elif "," in val:
            # If user has comma separated contents, style is partial
            self.style = 'partial'
        elif " " not in val or re.match(r"[\"\'].*[\"\']", val):
            # If user has given a single value, style is single
            self.style = 'single'
        else:
            # If none of the above, colour text red to mark error
            self.SetForegroundColour(wx.Colour(
                1, 0, 0
            ))


class NumCtrl(wx.TextCtrl):
    def __init__(self, parent,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)
        self.Bind(wx.EVT_TEXT, self.validate)

    def validate(self, evt):
        try:
            float(self.GetValue())
        except ValueError:
            self.SetForegroundColour(wx.Colour(
                1, 0, 0
            ))
        else:
            self.SetForegroundColour(wx.Colour(
                ThemeMixin.codeColors['base']['fg']
            ))


IntCtrl = wx.SpinCtrl


class CodeCtrl(wx.TextCtrl):
    def __init__(self, parent,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)

class ExtendedCodeCtrl(CodeCtrl):
    def __init__(self, parent,
                 val="", fieldName="",
                 size=wx.Size(-1, 72)):
        CodeCtrl.__init__(self, parent, val, fieldName, size)
        self.SetWindowStyleFlag(wx.TE_MULTILINE)

class StringCtrl(wx.TextCtrl):
    def __init__(self, parent,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)
        self.Bind(wx.EVT_TEXT, self.codeWanted)

    def codeWanted(self, evt):
        if self.GetValue().startswith("$"):
            spec = ThemeMixin.codeColors.copy()
            base = spec['base']
            # Override base font with user spec if present
            if prefs.coder['codeFont'].lower() != "From Theme...".lower():
                base['font'] = prefs.coder['codeFont']
        else:
            return


class ExtendedStringCtrl(StringCtrl):
    def __init__(self, parent,
                 val="", fieldName="",
                 size=wx.Size(-1, 72)):
        StringCtrl.__init__(self, parent, val, fieldName, size)
        self.SetWindowStyleFlag(wx.TE_MULTILINE)

class ColorCtrl(wx.TextCtrl):
    def __init__(self, parent,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        # Create self
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)
        # Add sizer
        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        self._szr.Add(self, border=5, flag=wx.EXPAND | wx.RIGHT)
        # Add button to activate color picker
        fldr = parent.app.iconCache.getBitmap(name="color", size=16, theme="light")
        self.findBtn = wx.BitmapButton(parent, -1, size=wx.Size(24,24), bitmap=fldr)
        self.findBtn.SetToolTip(_translate("Specify file ..."))
        self.findBtn.Bind(wx.EVT_BUTTON, self.findFile)
        self._szr.Add(self.findBtn)

class TableCtrl(wx.TextCtrl):
    def __init__(self, parent,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        # Create self
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)
        # Add sizer
        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        self._szr.Add(self, border=5, flag=wx.EXPAND | wx.RIGHT)
        # Add button to browse for file
        fldr = parent.app.iconCache.getBitmap(name="folder", size=16, theme="light")
        self.findBtn = wx.BitmapButton(parent, -1, size=wx.Size(24,24), bitmap=fldr)
        self.findBtn.SetToolTip(_translate("Specify file ..."))
        self.findBtn.Bind(wx.EVT_BUTTON, self.findFile)
        self._szr.Add(self.findBtn)
        # Add button to open in Excel
        xl = parent.app.iconCache.getBitmap(name="filecsv", size=16, theme="light")
        self.xlBtn = wx.BitmapButton(parent, -1, size=wx.Size(24,24), bitmap=xl)
        self.xlBtn.SetToolTip(_translate("Open/create in your default table editor"))
        self.xlBtn.Bind(wx.EVT_BUTTON, self.openExcel)
        self._szr.Add(self.xlBtn)
        # Link to Excel templates for certain contexts
        cmpRoot = os.path.dirname(psychopy.experiment.components.__file__)
        self.templates = {
            'Form': os.path.join(cmpRoot, "form", "formItems.xltx")
        }
        # Configure validation
        self.Bind(wx.EVT_TEXT, self.validateInput)
        self.validExt = [".csv",".tsv",".txt",
                         ".xl",".xlsx",".xlsm",".xlsb",".xlam",".xltx",".xltm",".xls",".xlt",
                         ".htm",".html",".mht",".mhtml",
                         ".xml",".xla",".xlm",
                         ".odc",".ods",
                         ".udl",".dsn",".mdb",".mde",".accdb",".accde",".dbc",".dbf",
                         ".iqy",".dqy",".rqy",".oqy",
                         ".cub",".atom",".atomsvc",
                         ".prn",".slk",".dif"]

    def validateInput(self, event):
        """Check whether input is openable and valid"""
        valid = False
        file = self.GetValue()
        # Is component type available?
        if hasattr(self.GetTopLevelParent(), 'type'):
            # Does this component have a default template?
            if self.GetTopLevelParent().type in self.templates:
                valid = True
        # Has user entered a full filepath, but it is invalid?
        if file and file not in self.validExt:
            valid = False
        # Is value a valid filepath?
        if os.path.isfile(os.path.abspath(file)) and file.endswith(tuple(self.validExt)):
            valid = True
        # Set excel button accordingly
        self.xlBtn.Enable(valid)

    def openExcel(self, event):
        """Either open the specified excel sheet, or make a new one from a template"""
        file = self.GetValue()
        if os.path.isfile(file) and file.endswith(tuple(self.validExt)):
            os.startfile(file)
        else:
            dlg = wx.MessageDialog(self, _translate(
                f"Once you have created and saved your table, please remember to add it to {self.Name}"),
                             caption="Reminder")
            dlg.ShowModal()
            os.startfile(self.templates[self.GetTopLevelParent().type])

    def findFile(self, event):
        _wld = f"All Table Files({'*'+';*'.join(self.validExt)})|{'*'+';*'.join(self.validExt)}|All Files (*.*)|*.*"
        dlg = wx.FileDialog(self, message=_translate("Specify file ..."),
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                            wildcard=_translate(_wld))
        if dlg.ShowModal() != wx.ID_OK:
            return 0
        filename = dlg.GetPath()
        relname = os.path.relpath(filename)
        self.SetValue(relname)
        self.validateInput(event)


class FileCtrl(wx.TextCtrl):
    def __init__(self, parent,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        # Create self
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)
        # Add sizer
        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        self._szr.Add(self, border=5, flag=wx.EXPAND | wx.RIGHT)
        # Add button to browse for file
        fldr = parent.app.iconCache.getBitmap(name="folder", size=16, theme="light")
        self.findBtn = wx.BitmapButton(parent, -1, size=wx.Size(24, 24), bitmap=fldr)
        self.findBtn.SetToolTip(_translate("Specify file ..."))
        self.findBtn.Bind(wx.EVT_BUTTON, self.findFile)
        self._szr.Add(self.findBtn)
        # Configure validation
        self.Bind(wx.EVT_TEXT, self.validate)

    def findFile(self, evt):
        _wld = f"All Files (*.*)|*.*"
        dlg = wx.FileDialog(self, message=_translate("Specify file ..."),
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                            wildcard=_translate(_wld))
        if dlg.ShowModal() != wx.ID_OK:
            return 0
        filename = dlg.GetPath()
        relname = os.path.relpath(filename)
        self.SetValue(relname)
        self.validate()

    def validate(self):
        """Check whether input is openable and valid"""
        valid = False
        file = self.GetValue()
        # Has user entered a full filepath, but it is invalid?
        if file and file not in self.validExt:
            valid = False
        # Is value a valid filepath?
        if os.path.isfile(os.path.abspath(file)) and file.endswith(tuple(self.validExt)):
            valid = True
        # Set color accordingly
        if valid:
            self.SetForegroundColour(wx.Colour(
                ThemeMixin.codeColors['base']['fg']
            ))
        else:
            self.SetForegroundColour(wx.Colour(
                1, 0, 0
            ))


class FileListCtrl(wx.ListBox):
    def __init__(self, parent, choices=[], size=None, pathtype="rel"):
        wx.ListBox.__init__(self)
        parent.Bind(wx.EVT_DROP_FILES, self.addItem)
        self.app = parent.app
        if type(choices) == str:
            choices = data.utils.listFromString(choices)
        self.Create(id=wx.ID_ANY, parent=parent, choices=choices, size=size, style=wx.LB_EXTENDED | wx.LB_HSCROLL)
        self.addBtn = wx.Button(parent, -1, style=wx.BU_EXACTFIT, label="+")
        self.addBtn.Bind(wx.EVT_BUTTON, self.addItem)
        self.subBtn = wx.Button(parent, -1, style=wx.BU_EXACTFIT, label="-")
        self.subBtn.Bind(wx.EVT_BUTTON, self.removeItem)

        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        self.btns = wx.BoxSizer(wx.VERTICAL)
        self.btns.AddMany((self.addBtn, self.subBtn))
        self._szr.Add(self, proportion=1, flag=wx.EXPAND)
        self._szr.Add(self.btns)

    def addItem(self, event):
        if event.GetEventObject() == self.addBtn:
            _wld = "Any file (*.*)|*"
            dlg = wx.FileDialog(self, message=_translate("Specify file ..."),
                                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE,
                                wildcard=_translate(_wld))
            if dlg.ShowModal() != wx.ID_OK:
                return 0
            filenames = dlg.GetPaths()
            relname = []
            for filename in filenames:
                relname.append(
                    os.path.relpath(filename, self.GetTopLevelParent().frame.filename))
            self.InsertItems(relname, 0)
        else:
            fileList = event.GetFiles()
            for filename in fileList:
                if os.path.isfile(filename):
                    self.InsertItems(filename, 0)

    def removeItem(self, event):
        i = self.GetSelections()
        if isinstance(i, int):
            i = [i]
        items = [item for index, item in enumerate(self.Items)
                 if index not in i]
        self.SetItems(items)

    def GetValue(self):
        return self.Items