import os
import wx

from psychopy.app.colorpicker import PsychoColorPicker
from psychopy.app.themes import ThemeMixin
from psychopy.colors import Color
from psychopy.localization import _translate
from psychopy import data, prefs, experiment
import re
from pathlib import Path

class _ValidatorMixin():
    def validate(self, evt):
        """Redirect validate calls to global validate method, assigning appropriate valType"""
        validate(self, self.valType)

    def showValid(self, valid):
        """Style input box according to valid"""
        if not hasattr(self, "SetForegroundColour"):
            return
        if valid:
            self.SetForegroundColour(wx.Colour(
                ThemeMixin.codeColors['base']['fg']
            ))
        else:
            self.SetForegroundColour(wx.Colour(
                1, 0, 0
            ))

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
        return str(filename)

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
            outList.append(str(filename))
        return outList


class SingleLineCtrl(wx.TextCtrl, _ValidatorMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        # Create self
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)
        self.valType = valType
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
        self.Bind(wx.EVT_TEXT, self.codeWanted)

    def codeWanted(self, evt):
        if self.GetValue().startswith("$") or not self.valType == "str":
            spec = ThemeMixin.codeColors.copy()
            base = spec['base']
            # Override base font with user spec if present
            if prefs.coder['codeFont'].lower() != "From Theme...".lower():
                base['font'] = prefs.coder['codeFont']
            validate(self, "code")
        else:
            validate(self, self.valType)


class MultiLineCtrl(SingleLineCtrl, _ValidatorMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 72)):
        SingleLineCtrl.__init__(self, parent, valType,
                                val=val, fieldName=fieldName,
                                size=size)
        self.SetWindowStyleFlag(wx.TE_MULTILINE)


class IntCtrl(wx.SpinCtrl, _ValidatorMixin):
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


class ChoiceCtrl(wx.Choice, _ValidatorMixin):
    def __init__(self, parent, valType,
                 val="", choices=[], fieldName="",
                 size=wx.Size(-1, 24)):
        wx.Choice.__init__(self)
        self.Create(parent, -1, size=size, choices=choices, name=fieldName)
        self._choices = choices
        self.valType = valType
        if val in choices:
            self.SetStringSelection(val)


class FileCtrl(wx.TextCtrl, _ValidatorMixin, _FileMixin):
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
        fldr = parent.app.iconCache.getBitmap(name="folder", size=16, theme="light")
        self.findBtn = wx.BitmapButton(parent, -1, size=wx.Size(24, 24), bitmap=fldr)
        self.findBtn.SetToolTip(_translate("Specify file ..."))
        self.findBtn.Bind(wx.EVT_BUTTON, self.findFile)
        self._szr.Add(self.findBtn)
        # Configure validation
        self.Bind(wx.EVT_TEXT, self.validate)

    def findFile(self, evt):
        file = self.getFile()
        if file:
            self.SetValue(file)
            self.validate(evt)


class FileListCtrl(wx.ListBox, _ValidatorMixin, _FileMixin):
    def __init__(self, parent, valType,
                 choices=[], size=None, pathtype="rel"):
        wx.ListBox.__init__(self)
        self.valType = valType
        parent.Bind(wx.EVT_DROP_FILES, self.addItem)
        self.app = parent.app
        if type(choices) == str:
            choices = data.utils.listFromString(choices)
        self.Create(id=wx.ID_ANY, parent=parent, choices=choices, size=size, style=wx.LB_EXTENDED | wx.LB_HSCROLL)
        self.addBtn = wx.Button(parent, -1, size=(24,24), style=wx.BU_EXACTFIT, label="+")
        self.addBtn.Bind(wx.EVT_BUTTON, self.addItem)
        self.subBtn = wx.Button(parent, -1, size=(24,24), style=wx.BU_EXACTFIT, label="-")
        self.subBtn.Bind(wx.EVT_BUTTON, self.removeItem)
        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        self.btns = wx.BoxSizer(wx.VERTICAL)
        self.btns.AddMany((self.addBtn, self.subBtn))
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

    def GetValue(self):
        return self.Items


class TableCtrl(wx.TextCtrl, _ValidatorMixin, _FileMixin):
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
        cmpRoot = os.path.dirname(experiment.components.__file__)
        expRoot = os.path.normpath(os.path.join(cmpRoot, ".."))
        self.templates = {
            'Form': os.path.join(cmpRoot, "form", "formItems.xltx"),
            'Loop': os.path.join(expRoot, "loopTemplate.xltx")
        }
        # Configure validation
        self.Bind(wx.EVT_TEXT, self.validate)
        self.validExt = [".csv",".tsv",".txt",
                         ".xl",".xlsx",".xlsm",".xlsb",".xlam",".xltx",".xltm",".xls",".xlt",
                         ".htm",".html",".mht",".mhtml",
                         ".xml",".xla",".xlm",
                         ".odc",".ods",
                         ".udl",".dsn",".mdb",".mde",".accdb",".accde",".dbc",".dbf",
                         ".iqy",".dqy",".rqy",".oqy",
                         ".cub",".atom",".atomsvc",
                         ".prn",".slk",".dif"]
    def validate(self, evt):
        """Redirect validate calls to global validate method, assigning appropriate valType"""
        validate(self, "file")
        # Enable Excel button if valid
        self.xlBtn.Enable(self.valid)
        # Is component type available?
        if hasattr(self.GetTopLevelParent(), 'type'):
            # Does this component have a default template?
            if self.GetTopLevelParent().type in self.templates:
                self.xlBtn.Enable(True)

    def openExcel(self, event):
        """Either open the specified excel sheet, or make a new one from a template"""
        file = self.rootDir / self.GetValue()
        if file.is_file() and file.suffix in self.validExt:
            os.startfile(file)
        else:
            dlg = wx.MessageDialog(self, _translate(
                f"Once you have created and saved your table, please remember to add it to {self.Name}"),
                             caption="Reminder")
            dlg.ShowModal()
            os.startfile(self.templates[self.GetTopLevelParent().type])

    def findFile(self, event):
        _wld = f"All Table Files({'*'+';*'.join(self.validExt)})|{'*'+';*'.join(self.validExt)}|All Files (*.*)|*.*"
        file = self.getFile(msg="Specify table file ...", wildcard=_wld)
        if file:
            self.SetValue(file)
            self.validate(event)


class ColorCtrl(wx.TextCtrl, _ValidatorMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        # Create self
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)
        self.valType = valType
        # Add sizer
        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        if not valType == "str":
            # Add $ for anything to be interpreted verbatim
            self.dollarLbl = wx.StaticText(parent, -1, "$", size=wx.Size(-1, -1), style=wx.ALIGN_RIGHT)
            self.dollarLbl.SetToolTip(_translate("This parameter will be treated as code - we have already put in the $, so you don't have to."))
            self._szr.Add(self.dollarLbl, border=5, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT)
        # Add ctrl to sizer
        self._szr.Add(self, proportion=1, border=5, flag=wx.EXPAND | wx.RIGHT)
        # Add button to activate color picker
        fldr = parent.app.iconCache.getBitmap(name="color", size=16, theme="light")
        self.pickerBtn = wx.BitmapButton(parent, -1, size=wx.Size(24,24), bitmap=fldr)
        self.pickerBtn.SetToolTip(_translate("Specify color ..."))
        self.pickerBtn.Bind(wx.EVT_BUTTON, self.colorPicker)
        self._szr.Add(self.pickerBtn)
        # Bind to validation
        self.Bind(wx.EVT_TEXT, self.validate)

    def colorPicker(self, evt):
        PsychoColorPicker(self.GetTopLevelParent().frame)

def validate(obj, valType):
    val = str(obj.GetValue())
    valid = True
    if val.startswith("$"):
        # If indicated as code, cancel
        return
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
        # For now, accept all code
        pass
    # Validate num
    if valType == "num":
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
            obj.color = Color(val)
            if not obj.color:
                # If invalid object is created, input is invalid
                valid = False
        except:
            # If object creation fails, input is invalid
            valid = False
    if valType == "file":
        if not os.path.isfile(os.path.abspath(val)):
            # Is value a valid filepath?
            valid = False
        if hasattr(obj, "validExt"):
            if not val.endswith(tuple(obj.validExt)):
                # If control has specified list of ext, does value end in correct ext?
                valid = False
    # If additional allowed values are defined, override validation
    if hasattr(obj, "allowedVals"):
        if val in obj.allowedVals:
            valid = True

    # Apply valid status to object
    obj.valid = valid
    if hasattr(obj, "showValid"):
        obj.showValid(valid)