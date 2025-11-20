#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
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
from psychopy.app.themes import fonts, colors
from psychopy.colors import Color
from psychopy.experiment.exports import NameSpace
from psychopy.experiment.params import Param, toList
from psychopy.localization import _translate
from psychopy import data, exceptions, logging, prefs, experiment
import re
from pathlib import Path

from psychopy.tools import stringtools

from . import CodeBox
from ...coder import BaseCodeEditor
from ...themes import icons, handlers
from ... import utils
from ...themes import icons
from ... import getAppInstance

inputTypes = {}


EVT_PARAM_CHANGED = wx.PyEventBinder(wx.IdManager.ReserveId())
emptyNamespace = NameSpace(experiment.Experiment())


class ParamValueChangedEvent(wx.CommandEvent):
    def __init__(self, obj, param, trigger=None):
        wx.CommandEvent.__init__(self, EVT_PARAM_CHANGED.typeId)
        # set object
        self.SetEventObject(obj)
        # store param
        self.param = param
        # store triggering event
        self.trigger = trigger

    def getParam(self):
        return self.param


class BaseParamCtrl(wx.Panel):
    """
    Base class for all ParamCtrls, defines the minimum functions needed for a ParamCtrl to work.

    Attributes
    ----------
    inputType : str
        Input type which this ctrl corresponds to

    Parameters
    ----------
    parent : wx.Window
        Parent window for this ctrl
    field : str
        Name of the param which this ctrl represents
    param : psychopy.experiment.Param
        Parameter which this ctrl represents
    element
        Builder element (Component, Routine, Loop, etc.) to which this parameter belongs, if any
    """
    # what inputType does a Param need to have to get this ctrl?
    inputType = None

    # additional styles for the ctrl (used by overloaded makeCtrls)
    ctrlStyle = wx.DEFAULT
    
    def __init__(self, parent, field, param, element=None, warnings=None):
        # initialise
        wx.Panel.__init__(self, parent)
        # store details
        self.parent = parent
        self.field = field
        self.param = param.copy()
        self.element = element
        self.warnings = warnings
        # setup namespace
        if hasattr(element, "exp"):
            self.namespace = self.element.exp.namespace
        else:
            self.namespace = emptyNamespace
        # setup sizer
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)
        # call method which subclasses override to make controls
        self.makeCtrls()
        # set tooltip
        self.setTooltip(param.hint)
    
    def __init_subclass__(cls):
        # index subclasses of BaseParamCtrl by the inputType they represent
        if cls.inputType is not None and cls.inputType not in inputTypes:
            inputTypes[cls.inputType] = cls
    
    def makeCtrls(self):
        """
        Makes the actual control object.
        """
        raise NotImplementedError(
            "All subclasses of BaseParamCtrl should implement `makeCtrls`"
        )
    
    def getValue(self):
        """
        Returns the value of this ctrl
        """
        raise NotImplementedError(
            "All subclasses of BaseParamCtrl should implement `getValue`"
        )

    def setValue(self, value):
        """
        Returns the value of this ctrl
        """
        raise NotImplementedError(
            "All subclasses of BaseParamCtrl should implement `setValue`"
        )

    def setTooltip(self, text):
        """
        Set the tooltip on this control.

        Parameters
        ----------
        text : str
            Text to show in tooltip
        """
        # set tooltip on panel
        self.SetToolTip(wx.ToolTip(text))
        # set on ctrl if possible
        if hasattr(self.ctrl, 'SetToolTip'):
            self.ctrl.SetToolTip(wx.ToolTip(text))
    
    def getWarning(self):
        """
        Get the warning associated with this ctrl, if any
        """
        if self.warnings is not None:
            return self.warnings.getWarning(self)

    def setWarning(self, warning, allowed=True):
        """
        Set a warning on the warnings handler attached to this ctrl, if any.

        Parameters
        ----------
        warning : str
            Warning to display
        """
        if self.warnings is not None:
            self.warnings.setWarning(self, warning, allowed=allowed)
    
    def clearWarning(self):
        """
        Remove the warning handler attached to this ctrl, if any.
        """
        if self.warnings is not None:
            self.warnings.clearWarning(self)
    
    @property
    def isValid(self):
        """
        Returns True or False based on whether the current ctrl has generated any warnings
        """
        if self.warnings is not None:
            return self.warnings.getWarning(self) is None

    def validate(self):
        """
        Update warnings based on the value of this ctrl
        """
        # always start off with no warning
        self.clearWarning()

    def styleValid(self):
        """
        Style this ctrl according to whether its value is valid (`.isValid`)
        """
        # if not implemented, do nothing
        return

    @property
    def isCode(self):
        """
        Returns True if the contents of this ctrl should be styled as code.
        """
        # if needed, figure out from $
        if self.param.valType in ("extendedStr","str", "file", "table", "color"):
            return str(self.getValue()).startswith("$")
        
        return True

    def styleCode(self):
        """
        Style this ctrl according to whether it contains code (`.isCode`)
        """
        # if not implemented, do nothing
        return
    
    def onChange(self, evt=None):
        """
        Callback which updates the control and param when the value changes.

        Parameters
        ----------
        evt : wx.Event
            Whatever event triggered this function
        """
        # validate ctrl
        self.validate()
        # style according to whether value is code and valid
        self.styleCode()
        self.styleValid()
        # update
        self.Update()
        self.Refresh()
        # update param value
        self.param.val = self.getValue()
        # show any warnings
        if self.warnings is not None:
            self.warnings.showWarning()
        # process dependent params
        if hasattr(self.parent, "checkDepends"):
            self.parent.checkDepends()
        # emit a custom event
        evt = ParamValueChangedEvent(self, param=self.param, trigger=evt)
        wx.PostEvent(self, evt)
    
    def onElementOk(self, evt=None):
        """
        Method which is called when OK is pressed on the element containing this param, if any.
        """
        # assume no action
        return


class ParamCtrl:
    """
    Constructor which looks for the appropriate subclass of BaseParamCtrl and initialises that.
    """
    def __new__(cls, parent, field, param, element=None, warnings=None):
        if param.inputType in inputTypes:
            # if a known type, get associated control
            ctrlCls = inputTypes[param.inputType]
        else:
            # otherwise, make a single line text ctrl
            ctrlCls = SingleLineCtrl
        
        return ctrlCls(parent, field, param, element, warnings)

class SingleLineCtrl(BaseParamCtrl):
    inputType = "single"

    # overload this in subclasses to control style
    ctrlStyle = wx.TE_LEFT

    def makeCtrls(self):
        # add dollar label
        self.dollarLbl = wx.StaticText(
            self, label="$", style=wx.ALIGN_RIGHT
        )
        self.dollarLbl.SetToolTip(_translate(
            "This parameter will be treated as code - we have already put in the $, so you don't "
            "have to."
        ))
        self.sizer.Add(
            self.dollarLbl, border=6, flag=wx.CENTER | wx.RIGHT
        )
        # show/hide dollar according to valType
        self.dollarLbl.Show(
            self.param.valType in ("code", "extendedCode", "num", "list", "int", "fixedList")
        )
        # add value ctrl
        self.ctrl = wx.TextCtrl(
            self, value=str(self.param.val), name=self.field, style=self.ctrlStyle
        )
        self.sizer.Add(
            self.ctrl, proportion=1, flag=wx.EXPAND
        )
        # enforce a minimum height on multiline ctrls
        if self.ctrlStyle | wx.TE_MULTILINE == self.ctrlStyle:
            self.ctrl.SetMinSize((-1, 128))
        # map change event
        self.ctrl.Bind(
            wx.EVT_TEXT, self.onChange
        )
        # also do styling once now
        self.onChange()
    
    def getValue(self):
        return self.ctrl.GetValue()

    def setValue(self, value, silent=False):
        # get insertion point if possible
        pt = self.ctrl.GetInsertionPoint()
        # set value
        if silent:
            self.ctrl.ChangeValue(str(value))
        else:
            self.ctrl.SetValue(str(value))
        # restore insertion point if possible
        try:
            self.ctrl.SetInsertionPoint(pt)
        except:
            pass
    
    def validateCode(self):
        # get value without any dollar syntax
        value = experiment.getCodeFromParamStr(
            self.getValue(), 
            target="PsychoPy"
        )
        # if blank, there's no code yet to be invalid
        if not value:
            return
        try:
            variableDefs = stringtools.getVariableDefs(value)
            variables = stringtools.getVariables(value)
        except (SyntaxError, TypeError) as e:
            # if failed to get variables, add warning and mark invalid
            self.setWarning(_translate(
                "Python syntax error in field `{}`:  {}"
            ).format(self.param.label, e))
            return
        # for multiline code, check that any variable defs don't break the namespace
        if self.param.valType == "extendedCode":
            # check that nothing important is being overwritten
            if self.element:
                # iterate through variable defs in code (if any)
                for name in variableDefs:
                    # is it overwriting something?
                    used = self.namespace.exists(name)
                    if used:
                        # warn but allow
                        self.setWarning(_translate(
                            "Setting the variable `{}` will overwrite an existing variable ({})"
                        ).format(name, used), allowed=True)
        else:
            # check any dynamic parameters
            if self.param.updates == "constant": 
                # if references a name, is it one defined before experiment start?
                for name in variables:
                    if name not in NameSpace.nonUserBuilder:
                        # if not, warn but allow
                        self.setWarning(_translate(
                            "Looks like your variable '{}' in '{}' should be set to "
                            "update."
                        ).format(name, self.param.label), allowed=True)
    
    def validateStr(self):
        # warn for unescaped "
        if re.findall(r"(?<!\\)[\"\']", self.getValue()):
            self.setWarning(_translate(
                "Quotation marks (\" or ') need to be escaped (\\\" or \\')"
            ))

    def validate(self):
        # start off valid
        BaseParamCtrl.validate(self)
        # use different method for code vs string
        if self.isCode:
            return self.validateCode()
        else:
            return self.validateStr()
    
    def styleValid(self):
        # text turns red if invalid
        if self.isValid:
            appHandle = getAppInstance()  # get theme info
            if appHandle is not None and appHandle.isDarkMode:
                self.ctrl.SetForegroundColour(
                    colors.scheme['white']
                )
            else:
                self.ctrl.SetForegroundColour(
                    colors.scheme['black']
                )
        else:
            self.ctrl.SetForegroundColour(
                colors.scheme['red']
            )
        self.ctrl.Refresh()
    
    def styleCode(self):
        def _setFont(font):
            # text becomes monospace if code
            if sys.platform == "linux":
                # have to go via SetStyle on Linux
                style = wx.TextAttr(self.ctrl.GetForegroundColour(), font=font)
                self.ctrl.SetStyle(0, len(self.ctrl.GetValue()), style)
            else:
                # otherwise SetFont is fine
                self.ctrl.SetFont(font)

        if self.isCode:
            _setFont(
                fonts.CodeFont(bold=True).obj
            )
        else:
            _setFont(
                fonts.AppFont().obj
            )
        self.ctrl.Refresh()
    
    def onChange(self, evt=None):
        # do some sanitization before usual onchange behaviour
        if self.isCode:
            # replace unescaped curly quotes
            if re.findall(r"(?<!\\)[\u201c\u201d]", self.getValue()):
                self.setValue(
                    re.sub(r"(?<!\\)[\u201c\u201d]", "\"", self.getValue())
                )
            if re.findall(r"(?<!\\)[\u2018\u2019]", self.getValue()):
                self.setValue(
                    re.sub(r"(?<!\\)[\u2018\u2019]", "\'", self.getValue())
                )
        else:
            pass

        BaseParamCtrl.onChange(self, evt)


class NameCtrl(SingleLineCtrl):
    inputType = "name"

    def styleCode(self):
        # a name is always code, we don't need to remind the user, so style as normal
        self.dollarLbl.Hide()
        self.ctrl.Refresh()
        self.ctrl.Layout()
    
    def validate(self):
        # start off valid
        BaseParamCtrl.validate(self)
        # is name a valid name?
        if self.getValue() == "":
            # prompt to enter a name if blank
            self.setWarning(_translate(
                "Please enter a name"
            ), allowed=False)
        elif NameSpace.isValid(self.getValue()):
            # if we have an experiment, is the name used already?
            if self.element:
                # if unchanged from original name, it does exist but is valid
                if self.getValue() == self.element.name:
                    return
                # otherwise, check against extant names
                exists = self.namespace.exists(self.getValue())
                if exists:
                    self.setWarning(_translate(
                        "Name is already in use ({})"
                    ).format(exists), allowed=False)
        else:
            self.setWarning(_translate(
                "Name is not valid"
            ), allowed=False)


class MultiLineCtrl(SingleLineCtrl):
    inputType = "multi"

    ctrlStyle = wx.TE_LEFT | wx.TE_MULTILINE


class InvalidCtrl(SingleLineCtrl):
    inputType = "inv"

    def makeCtrls(self):        
        SingleLineCtrl.makeCtrls(self)
        self.ctrl.Disable()
        # add delete button
        self.deleteBtn = wx.Button(self, label="×", size=(24, 24))
        self.deleteBtn.SetForegroundColour("red")
        self.deleteBtn.Bind(wx.EVT_BUTTON, self.deleteParam)
        self.deleteBtn.SetToolTip(_translate(
            "This parameter has come from an older version of PsychoPy. "
            "In the latest version of PsychoPy, it is not used. Click this "
            "button to delete it. WARNING: This may affect how this experiment "
            "works in older versions!"))
        self.sizer.Add(self.deleteBtn, border=6, flag=wx.LEFT | wx.RIGHT)
        # add deleted label
        self.deleteLbl = wx.StaticText(self, label=_translate("DELETED"))
        self.deleteLbl.SetForegroundColour("red")
        self.deleteLbl.Hide()
        self.sizer.Add(self.deleteLbl, border=6, proportion=1, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        # add undo delete button
        self.undoBtn = wx.Button(self, label="⟲", size=(24, 24))
        self.undoBtn.SetToolTip(_translate(
            "This parameter will not be deleted until you click Okay. "
            "Click this button to revert the deletion and keep the parameter."))
        self.undoBtn.Hide()
        self.undoBtn.Bind(wx.EVT_BUTTON, self.undoDelete)
        self.sizer.Add(self.undoBtn, border=6, flag=wx.LEFT | wx.RIGHT)

        # set deletion flag
        self.forDeletion = False

    def deleteParam(self, evt=None):
        """
        When the remove button is pressed, mark this param as for deletion
        """
        # mark for deletion
        self.forDeletion = True
        # hide value ctrl and delete button
        self.ctrl.Hide()
        self.deleteBtn.Hide()
        # show delete label and
        self.undoBtn.Show()
        self.deleteLbl.Show()

        self.sizer.Layout()

    def undoDelete(self, evt=None):
        # mark not for deletion
        self.forDeletion = False
        # show value ctrl and delete button
        self.ctrl.Show()
        self.deleteBtn.Show()
        # hide delete label and
        self.undoBtn.Hide()
        self.deleteLbl.Hide()

        self.sizer.Layout()


class BoolCtrl(BaseParamCtrl):
    inputType = "bool"

    def makeCtrls(self):
        # add checkbox
        self.ctrl = wx.CheckBox(self)
        self.ctrl.SetValue(bool(self.param))
        self.sizer.Add(
            self.ctrl, border=6, flag=wx.EXPAND | wx.ALL
        )
        # connect onChange
        self.ctrl.Bind(
            wx.EVT_CHECKBOX, self.onChange
        )
    
    def getValue(self):
        return self.ctrl.IsChecked()

    def setValue(self, value):
        self.ctrl.SetValue(bool(value))


class ChoiceCtrl(BaseParamCtrl):
    inputType = "choice"

    def makeCtrls(self):
        # add choice ctrl
        self.ctrl = wx.Choice(self)
        self.sizer.Add(
            self.ctrl, proportion=1, flag=wx.EXPAND | wx.ALL
        )
        # connect onChange
        self.ctrl.Bind(
            wx.EVT_CHOICE, self.onChange
        )
        # set initial choices
        self.populate()

    def populate(self):
        # convert values to a list (by executing method of just converting value)
        if callable(self.param.allowedVals):
            choices = [str(val) for val in self.param.allowedVals()]
        else:
            choices = [str(val) for val in self.param.allowedVals]
        # convert labels to a list (by executing method of just converting value)
        if callable(self.param.allowedLabels):
            labels = self.param.allowedLabels()
        elif self.param.allowedLabels:
            labels = list(self.param.allowedLabels)
        else:
            # if not given any labels, alias values
            labels = choices
        # make arrays the same length
        self.choices = []
        self.labels = []
        for i in range(max(len(choices), len(labels))):
            # fill in missing choices with label
            if i < len(choices):
                self.choices.append(choices[i])
            else:
                self.choices.append(labels[i])
            # fill in missing labels with choices
            if i < len(labels):
                self.labels.append(str(labels[i]))
            else:
                self.labels.append(str(choices[i]))
        # translate labels
        for i in range(len(self.labels)):
            # An empty string must not be translated
            # because it returns meta information of
            # .mo file (due to specification of gettext)
            if self.labels[i] != '':
                self.labels[i] = _translate(self.labels[i])
        # apply to ctrl
        self.ctrl.SetItems(self.labels)
        # disable if param is readonly
        self.ctrl.Enable(not self.param.readOnly)
        # apply (or re-apply) selection
        self.setValue(self.param.val)
    
    def getValue(self):
        return self.choices[self.ctrl.GetSelection()]
    
    def setValue(self, value):
        if str(value) not in self.choices:
            # if not known, add it to possible choices
            self.choices.append(str(value))
            # translate label if the value is not ''
            if str(value) != '':
                self.labels.append(_translate(str(value)))
            else:
                self.labels.append(str(value))
            self.ctrl.SetItems(self.labels)
        # set
        self.ctrl.SetSelection(
            self.choices.index(str(value))
        )


class MultiChoiceCtrl(ChoiceCtrl):
    inputType = "multiChoice"

    def makeCtrls(self):
        self.ctrl = wx.CheckListBox(self, style=wx.LB_MULTIPLE)
        self.sizer.Add(
            self.ctrl, proportion=1, flag=wx.EXPAND | wx.ALL
        )
        # connect onChange
        self.ctrl.Bind(
            wx.EVT_CHECKLISTBOX, self.onChange
        )

        self.populate()
    
    def getValue(self):
        return [
            self.choices[i] for i in self.ctrl.GetCheckedItems()
        ]
    
    def setValue(self, value):
        # coerce to list
        value = data.utils.listFromString(value)
        # iterate through values
        selected = []
        for val in value:
            # if not known, add it to possible choices
            if val not in self.choices:
                self.choices.append(val)
                self.labels.append(str(val))
                self.ctrl.SetItems(self.labels)
            # add index
            selected.append(
                self.choices.index(val)
            )
        # set
        self.ctrl.SetCheckedItems(selected)


class FileCtrl(SingleLineCtrl):
    inputType = "file"

    dlgWildcard = "All Files (*.*)|*.*"
    icon = "folder"
    dlgStyle = wx.FD_FILE_MUST_EXIST

    def makeCtrls(self):
        SingleLineCtrl.makeCtrls(self)
        # add a file browse button
        self.fileBtn = wx.Button(self, style=wx.BU_EXACTFIT)
        self.fileBtn.SetBitmap(
            icons.ButtonIcon(stem=self.icon, size=16, theme="light").bitmap
        )
        self.fileBtn.SetToolTip(
            _translate("Browse for a file")
        )
        self.fileBtn.Bind(wx.EVT_BUTTON, self.openFileBrowser)
        self.sizer.Add(
            self.fileBtn, border=6, flag=wx.EXPAND | wx.LEFT
        )
    
    def styleValid(self):
        # style as normal
        SingleLineCtrl.styleValid(self)
        # if not code, check for a link
        if not self.isCode:
            if stringtools.is_url(self.getValue()):
                self.ctrl.SetForegroundColour(
                    colors.scheme['blue']
                )
                self.ctrl.Refresh()
    
    @property
    def rootDir(self):
        # if no element, use system root
        if self.element is None or not hasattr(self.element, "exp"):
            return Path()
        # otherwise, get from experiment
        root = Path(self.element.exp.filename)
        # move up a dir if root is a file
        if root.is_file():
            root = root.parent
        
        return root
    
    def openFileBrowser(self, evt=None):
        # open a file browser dialog
        dlg = wx.FileDialog(
            self, 
            message=_translate("Specify file..."), 
            defaultDir=str(self.rootDir),
            style=wx.FD_OPEN | self.dlgStyle,
            wildcard=self.dlgWildcard
        )
        if dlg.ShowModal() != wx.ID_OK:
            return
        # get path
        file = dlg.GetPath()
        # relativise
        try:
            filename = Path(file).relative_to(self.rootDir)
        except ValueError:
            filename = Path(file).absolute()
        # set value
        self.setValue(
            str(filename).replace("\\", "/")
        )
    
    def validate(self):
        from psychopy.tools.filetools import defaultStim
        # start off valid
        BaseParamCtrl.validate(self)
        # if given as code, use regular code checking
        if self.isCode:
            return SingleLineCtrl.validateCode(self)
        # if given a link, it's valid
        if stringtools.is_url(self.getValue()):
            self.clearWarning()
            return
        # if blank, don't worry about it
        if self.getValue() == "":
            self.clearWarning()
            return
        # if it's a string, convert to file
        try:
            file = Path(self.getValue())
        except:
            # if it can't be a file at all, show warning
            self.setWarning(_translate(
                "Not a valid file path: {}"
            ).format(self.getValue()))
            return
        # make path absolute
        if not file.is_absolute():
            file = self.rootDir / file
        # valid only if file exists
        if all((
            not file.is_file(),
            file.name not in defaultStim
        )):
            self.setWarning(_translate(
                "No file named {}"
            ).format(self.getValue()))


class SoundCtrl(FileCtrl):
    inputType = "soundFile"

    def validate(self):
        from psychopy.tools.audiotools import knownNoteNames
        # validate like a normal file
        FileCtrl.validate(self)
        # if given a note, this is fine
        if str(self.getValue()).capitalize() in knownNoteNames:
            self.clearWarning()


class TableCtrl(FileCtrl):
    inputType = "table"

    validExt = [
        ".csv", ".tsv", ".txt", ".xl", ".xlsx", ".xlsm", ".xlsb", ".xlam", ".xltx", ".xltm", 
        ".xls", ".xlt", ".htm", ".html", ".mht", ".mhtml", ".xml", ".xla", ".xlm", ".odc", ".ods", 
        ".udl", ".dsn", ".mdb", ".mde", ".accdb", ".accde", ".dbc", ".dbf", ".iqy", ".dqy", ".rqy", 
        ".oqy", ".cub", ".atom", ".atomsvc", ".prn", ".slk", ".dif"
    ]
    dlgWildcard = (
        f"All Table Files({'*'+';*'.join(validExt)})"
        f"|{'*'+';*'.join(validExt)}"
        f"|All Files (*.*)"
        f"|*.*"
    )

    def makeCtrls(self):
        FileCtrl.makeCtrls(self)
        # Add button to open in Excel
        self.xlBtn = wx.Button(self, style=wx.BU_EXACTFIT)
        self.xlBtn.SetBitmap(
            icons.ButtonIcon(stem="filecsv", size=16, theme="light").bitmap
        )
        self.xlBtn.SetToolTip(
            _translate("Open/create in your default table editor")
        )
        self.xlBtn.Bind(wx.EVT_BUTTON, self.openExcel)
        self.sizer.Add(
            self.xlBtn, border=6, flag=wx.EXPAND | wx.LEFT
        )
        # call initial onChange
        self.onChange()
    
    def onChange(self, evt=None):
        FileCtrl.onChange(self, evt)
        # if calling before finished initialising, skip
        if not hasattr(self, "xlBtn"):
            return
        
        if not self.getValue().strip():
            # if blank, enable/disable according to presence of template
            self.xlBtn.Enable("template" in self.param.ctrlParams)
        else:
            # otherwise, enable/disable according to validity
            self.xlBtn.Enable(self.isValid)

    def openExcel(self, event):
        """
        Either open the specified excel sheet, or make a new one from a template
        """
        file = Path(self.getValue())
        # make path absolute
        if not file.is_absolute():
            file = self.rootDir / file
        # open a template if not a valid file
        if file == self.rootDir or not (file.is_file() or file.suffix not in self.validExt):
            dlg = wx.MessageDialog(self, _translate(
                    "Once you have created and saved your table, remember to add it here."
                ),
                caption=_translate("Reminder")
            )
            dlg.ShowModal()
            # get template
            if "template" in self.param.ctrlParams:
                file = self.param.ctrlParams['template']
                # if template is specified as a method, call it now to get the value live
                if callable(file):
                    file = file()
                # convert to Path
                file = Path(file)
            else:
                # use blank template if none given
                file = Path(experiment.__file__).parent / 'blankTemplate.xltx',
        # Open whatever file is used
        try:
            os.startfile(file)
        except AttributeError:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, file])


class ConditionsCtrl(TableCtrl):
    inputType = "conditions"


class SurveyCtrl(SingleLineCtrl):
    inputType = "survey"

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

    def makeCtrls(self):
        SingleLineCtrl.makeCtrls(self)
        # Add CTRL + click behaviour
        self.ctrl.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick)
        # add placeholder
        self.ctrl.SetHint("e.g. e89cd6eb-296e-4960-af14-103026a59c14")
        # Add button to browse for survey
        self.findBtn = wx.Button(
            self, -1,
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
        self.sizer.Add(self.findBtn, border=6, flag=wx.LEFT)

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
                self.ctrl.SetValue(dlg.getValue())
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
        value = self.ctrl.GetValue()
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


class ColorCtrl(SingleLineCtrl):
    inputType = "color"

    def makeCtrls(self):
        SingleLineCtrl.makeCtrls(self)
        # add button to activate color picker
        self.pickerBtn = wx.Button(self, style=wx.BU_EXACTFIT)
        self.pickerBtn.SetBitmap(
            icons.ButtonIcon(stem="color", size=16, theme="light").bitmap
        )
        self.pickerBtn.SetToolTip(_translate("Specify color ..."))
        self.pickerBtn.Bind(wx.EVT_BUTTON, self.colorPicker)
        self.sizer.Add(self.pickerBtn)

    def colorPicker(self, evt):
        # show color picker
        dlg = PsychoColorPicker(self, context=self, allowCopy=False)  # open a color picker
        ret = dlg.ShowModal()
        if ret == wx.ID_OK:
            self.setValue(
                f"$({dlg.getOutputValue()})"
            )
        else:
            pass
        dlg.Destroy()


class FontCtrl(SingleLineCtrl):
    inputType = "font"

    def onElementOk(self, evt=None):
        # get a font manager
        from psychopy.tools.fontmanager import FontManager, MissingFontError
        fm = FontManager()
        # check whether the font is installed
        if self.element and hasattr(self.element, "exp") and self.element.exp.filename:
            currentDir = Path(self.element.exp.filename).parent
        else:
            currentDir = Path(".")
        installed = fm.getFontsMatching(self.getValue(), fallback=False, currentDir=currentDir)
        # if not installed, ask the user whether to download from Google Fonts
        if not installed:
            # create dialog
            dlg = wx.MessageDialog(
                self.GetTopLevelParent(),
                _translate(
                    "Font {} is not installed, would you like to download it from Google Fonts?"
                ).format(self.getValue()),
                style=wx.YES|wx.NO|wx.ICON_QUESTION
            )
            # download if yes
            if dlg.ShowModal() == wx.ID_YES:
                try:
                    fm.addGoogleFont(self.getValue().strip())
                except MissingFontError as err:
                    dlg = wx.MessageDialog(
                        self.GetTopLevelParent(),
                        _translate(
                            "Could not download font {} from Google Fonts, reason: {}"
                        ).format(self.getValue(), err),
                        style=wx.OK|wx.ICON_ERROR
                    )
                    dlg.ShowModal()
                else:
                    dlg = wx.MessageDialog(
                        self.GetTopLevelParent(),
                        _translate(
                            "Font download successfully"
                        ),
                        style=wx.OK|wx.ICON_INFORMATION
                    )
                    dlg.ShowModal()


class CodeCtrl(BaseParamCtrl, handlers.ThemeMixin):
    inputType = "code"

    def makeCtrls(self):
        self.ctrl = CodeBox(
            self, wx.ID_ANY, prefs, 
            pos=wx.DefaultPosition, size=(-1, 128), style=wx.DEFAULT
        )
        self.sizer.Add(
            self.ctrl, proportion=1, flag=wx.EXPAND | wx.ALL
        )
        # hide margin
        self.ctrl.SetMarginWidth(0, 0)
        # set initial value
        self.setValue(self.param.val)
        # setup auto indent behaviour as in Code component
        self.ctrl.Bind(wx.EVT_KEY_DOWN, self.onChange)

    def getValue(self):
        return self.ctrl.GetText()

    def setValue(self, value):
        # get insertion point if possible
        pt = self.ctrl.GetInsertionPoint()
        # set value
        self.ctrl.SetText(str(value))
        # restore insertion point if possible
        try:
            self.ctrl.SetInsertionPoint(pt)
        except:
            pass

    def onChange(self, evt=None):
        CodeBox.OnKeyPressed(self.ctrl, evt)
        BaseParamCtrl.onChange(self, evt)
    
    def styleValid(self):
        # red border if error
        if self.isValid:
            self.ctrl.SetFoldMarginColour(0, colors.scheme['red'])
        else:
            self.ctrl._applyAppTheme()
        self.ctrl.Refresh()

    def validate(self):
        BaseParamCtrl.validate(self)
        return SingleLineCtrl.validateCode(self)
        

class RichChoiceCtrl(BaseParamCtrl):
    inputType = "richChoice"

    viewToggle = True
    multi = False

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
            self.toggleView.SetBackgroundColour("white")

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
            
            # post event
            evt = wx.ListEvent(commandType=wx.EVT_CHOICE.typeId, id=-1)
            evt.SetString(self.value)
            evt.SetEventObject(self.parent)
            wx.PostEvent(self.parent, evt)

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

    def makeCtrls(self):
        self.ctrl = self
        # make sizer for options
        self.optionsSizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(
            self.optionsSizer, proportion=1, flag=wx.EXPAND | wx.ALL
        )
        # store values
        self.choices = {}
        for i, val in enumerate(self.param.allowedVals):
            self.choices[val] = self.param.allowedLabels[i]
        # Populate
        self.populate()
        # Set value
        self.setValue(self.param.val)
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
        # bind onChange
        self.Bind(wx.EVT_CHOICE, self.onChange)

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
        self.optionsSizer.Add(item, border=3, flag=wx.ALL | wx.EXPAND)

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
        value = data.utils.listFromString(value)
        # Check/uncheck corresponding items
        for item in self.items:
            state = item.value in value
            item.check.SetValue(state)

        self.Layout()


class FileListCtrl(BaseParamCtrl):
    inputType = "fileList"

    dlgWildcard = "All Files (*.*)|*.*"
    dlgStyle = wx.FD_FILE_MUST_EXIST

    class FileListItem(FileCtrl):
        def makeCtrls(self):
            FileCtrl.makeCtrls(self)
            # add a delete button
            self.deleteBtn = wx.Button(self, style=wx.BU_EXACTFIT)
            self.deleteBtn.SetBitmap(
                icons.ButtonIcon("delete", size=16, theme="light").bitmap
            )
            self.sizer.Add(
                self.deleteBtn, border=6, flag=wx.EXPAND | wx.LEFT
            )
            self.deleteBtn.Bind(wx.EVT_BUTTON, self.deleteSelf)

            self.Layout()
        
        def deleteSelf(self, evt=None):
            # remove from parent sizer and array
            self.parent.items.pop(
                self.parent.items.index(self)
            )
            self.parent.itemsSizer.Detach(self)
            # clear any warnings
            self.clearWarning()
            # delete
            self.Destroy()
            self.parent.Layout()
        
        def onChange(self, evt=None):
            FileCtrl.onChange(self, evt)
            self.parent.onChange(evt)

    def makeCtrls(self):
        self.ctrl = self
        # make own sizer vertical
        self.sizer.SetOrientation(wx.VERTICAL)
        # array to store items
        self.items = []
        # sizer to layout items
        self.itemsSizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(
            self.itemsSizer, border=6, proportion=1, flag=wx.EXPAND | wx.BOTTOM
        )
        # add multiple button
        self.addManyBtn = wx.Button(self, label=_translate("Add multiple items"))
        self.addManyBtn.SetBitmap(
            icons.ButtonIcon("add_many", size=16, theme="light").bitmap
        )
        self.sizer.Add(
            self.addManyBtn, border=6, flag=wx.ALIGN_LEFT | wx.BOTTOM
        )
        self.addManyBtn.Bind(wx.EVT_BUTTON, self.addMultiItems)
        # add button
        self.addBtn = wx.Button(self, label=_translate("Add item"))
        self.addBtn.SetBitmap(
            icons.ButtonIcon("add", size=16, theme="light").bitmap
        )
        self.sizer.Add(
            self.addBtn, border=6, flag=wx.ALIGN_LEFT | wx.BOTTOM
        )
        self.addBtn.Bind(wx.EVT_BUTTON, self.addItem)
        # set initial value
        self.setValue(self.param.val)
    
    def layout(self):
        """
        Layout this element, and fit its parent around it.
        """
        self.Layout()
        self.GetParent().Layout()
        self.GetTopLevelParent().Layout()
        self.GetTopLevelParent().Fit()
    
    def addItem(self, evt=None):
        """
        Add a new item to this ctrl
        """
        # make a file control for a param not attached to anything
        item = self.FileListItem(
            parent=self, 
            field=str(len(self.items)),
            param=Param("", valType="str", inputType="file"),
            element=self.element,
            warnings=self.warnings
        )
        # append it to items array
        self.items.append(item)
        # add it to the items sizer
        self.itemsSizer.Add(
            item, border=6, flag=wx.EXPAND | wx.BOTTOM
        )

        self.layout()

        return item
    
    def addMultiItems(self, evt=None):
        """
        Add several new items to this ctrl
        """
        items = []
        # open a file browser dialog
        dlg = wx.FileDialog(
            self, 
            message=_translate("Specify file..."), 
            defaultDir=str(self.rootDir),
            style=wx.FD_OPEN | wx.FD_MULTIPLE | self.dlgStyle,
            wildcard=self.dlgWildcard,
        )
        if dlg.ShowModal() != wx.ID_OK:
            return
        # get path
        for file in dlg.GetPaths():
            # relativise
            try:
                filename = Path(file).relative_to(self.rootDir)
            except ValueError:
                filename = Path(file).absolute()
            # make a file control for a param not attached to anything
            item = self.FileListItem(
                parent=self, 
                field=str(len(self.items)),
                param=Param(str(filename).replace("\\", "/"), valType="str", inputType="file"),
                element=self.element,
                warnings=self.warnings
            )
            items.append(item)
            # append it to items array
            self.items.append(item)
            # add it to the items sizer
            self.itemsSizer.Add(
                item, border=6, flag=wx.EXPAND | wx.BOTTOM
            )

        self.layout()

        return items
    
    def clearItems(self):
        """
        Clear all items from this ctrl
        """
        for item in self.items:
            item.deleteSelf()
        
        self.layout()
    
    def getValue(self):
        return [item.getValue() for item in self.items]

    def setValue(self, value):
        # unstring value into an actual list
        value = data.utils.listFromString(value)
        # clear all items
        self.clearItems()
        # make a new item for each value
        for item in value:
            ctrl = self.addItem()
            ctrl.setValue(item)
    
    @property
    def isValid(self):
        # return True if all children are valid
        return all([
            item.isValid 
            for item in self.items
        ])
        
    def validate(self):
        for item in self.items:
            item.validate()
    
    @property
    def rootDir(self):
        # if no element, use system root
        if self.element is None or not hasattr(self.element, "exp"):
            return Path()
        # otherwise, get from experiment
        root = Path(self.element.exp.filename)
        # move up a dir if root is a file
        if root.is_file():
            root = root.parent
        
        return root


class DictCtrl(BaseParamCtrl):
    inputType = "dict"

    class DictKey(SingleLineCtrl):
        def validate(self):
            """
            Dict keys can't key variables
            """            
            if self.isCode:
                self.setWarning(_translate(
                    "Dictionary keys can't be code"
                ), allowed=False)
            else:
                SingleLineCtrl.validate(self)
        
        def onChange(self, evt=None):
            SingleLineCtrl.onChange(self, evt)
            self.parent.onChange(evt)
    
    class DictValue(SingleLineCtrl):
        def validate(self):
            # update param label so the error reports the value of keyctrl
            if hasattr(self, "keyCtrl"):
                self.param.label = f"{self.parent.param.label}:{self.keyCtrl.getValue()}"

            # validate first as code
            self.param.valType = "code"
            self.dollarLbl.Show()
            self.warnings.clearWarning(self)
            self.validateCode()
            # if this failed, try as string
            if self.warnings.getWarning(self):
                self.warnings.clearWarning(self)
                self.param.valType = "str"
                self.validateStr()
            
            self.dollarLbl.Show(self.param.valType == "code")
            
            self.Refresh()
            self.Layout()

        def onChange(self, evt=None):
            SingleLineCtrl.onChange(self, evt)
            self.parent.onChange(evt)

    class DictField:
        def __init__(self, parent):
            # store parent
            self.parent = parent
            # add ctrl for key
            self.keyCtrl = DictCtrl.DictKey(
                parent=parent, 
                field=f"key{len(parent.items)}",
                param=Param("", valType="str", inputType="single"),
                element=parent.element,
                warnings=parent.warnings
            )
            # add ctrl for value
            self.valueCtrl = DictCtrl.DictValue(
                parent=parent, 
                field=f"value{len(parent.items)}",
                param=Param("", valType="code", inputType="single"),
                element=parent.element,
                warnings=parent.warnings
            )
            self.valueCtrl.keyCtrl = self.keyCtrl
            # add delete button
            self.deleteBtn = wx.Button(parent, style=wx.BU_EXACTFIT)
            self.deleteBtn.SetBitmap(
                icons.ButtonIcon("delete", size=16, theme="light").bitmap
            )
            self.deleteBtn.Bind(wx.EVT_BUTTON, self.deleteSelf)
        
        def deleteSelf(self, evt=None):
            # remove from parent array
            self.parent.items.pop(
                self.parent.items.index(self)
            )
            # clear any warnings
            self.keyCtrl.clearWarning()
            self.valueCtrl.clearWarning()
            # remove all windows from parent sizer
            self.parent.itemsSizer.Detach(self.keyCtrl)
            self.parent.itemsSizer.Detach(self.valueCtrl)
            self.parent.itemsSizer.Detach(self.deleteBtn)
            # delete all windows
            self.keyCtrl.Destroy()
            self.valueCtrl.Destroy()
            self.deleteBtn.Destroy()
            # layout
            self.parent.layout()

    def makeCtrls(self):
        self.ctrl = self
        # make own sizer vertical
        self.sizer.SetOrientation(wx.VERTICAL)
        # array to store items
        self.items = []
        # sizer to layout items
        self.itemsSizer = wx.FlexGridSizer(3, vgap=6, hgap=6)
        self.itemsSizer.AddGrowableCol(0, proportion=1)
        self.itemsSizer.AddGrowableCol(1, proportion=1)
        self.sizer.Add(
            self.itemsSizer, border=6, proportion=1, flag=wx.EXPAND | wx.BOTTOM
        )
        # add button
        self.addBtn = wx.Button(self, label=_translate("Add item"))
        self.addBtn.SetBitmap(
            icons.ButtonIcon("add", size=16, theme="light").bitmap
        )
        self.sizer.Add(
            self.addBtn, border=6, flag=wx.ALIGN_LEFT | wx.BOTTOM
        )
        self.addBtn.Bind(wx.EVT_BUTTON, self.addItem)
        # set initial value
        self.setValue(self.param.val)
    
    def layout(self):
        """
        Layout this element, and fit its parent around it.
        """
        self.Layout()
        self.GetParent().Layout()
        self.GetTopLevelParent().Layout()
        self.GetTopLevelParent().Fit()
    
    def addItem(self, evt=None):
        # create item
        item = self.DictField(self)
        # append to array
        self.items.append(item)
        # add to sizer
        self.itemsSizer.Add(
            item.keyCtrl, proportion=1, flag=wx.EXPAND
        )
        self.itemsSizer.Add(
            item.valueCtrl, proportion=1, flag=wx.EXPAND
        )
        self.itemsSizer.Add(
            item.deleteBtn, flag=wx.EXPAND
        )
        # layout
        self.layout()

        return item
    
    def clearItems(self):
        # delete each item
        for item in self.items:
            item.deleteSelf()
        # layout
        self.layout()
    
    def getValue(self):
        return {
            item.keyCtrl.getValue(): item.valueCtrl.getValue() 
            for item in self.items
        }

    def setValue(self, value):
        # clear items
        self.clearItems()
        # make sure value is a dict
        value = data.utils.dictFromString(value)
        # iterate through key:val pairs
        for key, val in value.items():
            # add an item ctrl for each
            item = self.addItem()
            # populate
            item.keyCtrl.setValue(key)
            item.valueCtrl.setValue(val)
    
    def validate(self):
        # check for duplicate keys
        used = []
        for key in self.getValue():
            if key in used:
                self.setWarning(_translate(
                    "Duplicate dictionary key: {}"
                ).format(key))
                return
            used.append(key)
        # otherwise validate all children
        for item in self.items:
            item.keyCtrl.validate()
            item.valueCtrl.validate()
    
    @property
    def isValid(self):
        # return true if self has no warnings and children have no warnings
        return BaseParamCtrl.isValid.fget(self) and all([
            item.keyCtrl.isValid and item.valueCtrl.isValid 
            for item in self.items
        ])


class DeviceCtrl(ChoiceCtrl):
    inputType = "device"

    def makeCtrls(self):
        ChoiceCtrl.makeCtrls(self)
        # add a button to open device manager
        self.deviceMgrBtn = wx.Button(self, style=wx.BU_EXACTFIT)
        self.deviceMgrBtn.Bind(wx.EVT_BUTTON, self.openDeviceManager)
        self.deviceMgrBtn.SetBitmap(
            icons.ButtonIcon("devices", size=16, theme="light").bitmap
        )
        self.deviceMgrBtn.SetToolTip(_translate(
            "Open the Device Manager to setup devices"
        ))
        self.sizer.Add(
            self.deviceMgrBtn, border=6, flag=wx.EXPAND | wx.LEFT
        )

    def openDeviceManager(self, evt=None):
        from psychopy.app.deviceManager import DeviceManagerDlg
        # create dialog
        dlg = DeviceManagerDlg(parent=self.GetTopLevelParent())
        # show it
        dlg.ShowModal()
        # repopulate devices
        self.populate()
        # also repopulate sibling controls
        for sibling in self.GetParent().GetChildren():
            if isinstance(sibling, DeviceCtrl) and sibling is not self:
                sibling.populate()
    
    def onElementOk(self, evt=None):
        # get the device manager
        from psychopy.preferences import prefs
        from psychopy.app.deviceManager import AddDeviceDlg
        # if not setup, ask the user whether they want to set it up
        if self.getValue() and self.getValue() not in prefs.devices:
            # create dialog
            dlg = wx.MessageDialog(
                self.GetTopLevelParent(),
                _translate(
                    "No device named `{}` has been setup in the Device Manager, set one up now?"
                ).format(self.getValue()),
                style=wx.YES|wx.NO|wx.ICON_QUESTION
            )
            # open device manager if yes
            if dlg.ShowModal() == wx.ID_YES:
                dlg = AddDeviceDlg(self, deviceName=self.getValue())
                # on OK, add device and refresh list
                if dlg.ShowModal() == wx.ID_OK:
                    device = dlg.getDevice()
                    prefs.devices[device.name] = device
                    prefs.devices.save()
                    self.populate()
