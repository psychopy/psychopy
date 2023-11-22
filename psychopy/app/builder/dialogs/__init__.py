#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Dialog classes for the Builder, including ParamCtrls
"""
import sys

import os
import copy
import time
from collections import OrderedDict

import numpy
import re
import wx

import psychopy.experiment.utils
from psychopy.experiment import Param

from ... import dialogs
from .. import experiment
from .. validators import NameValidator, CodeSnippetValidator, WarningManager
from .dlgsConditions import DlgConditions
from .dlgsCode import DlgCodeComponentProperties, CodeBox
from .findDlg import BuilderFindDlg
from . import paramCtrls
from psychopy import data, logging, exceptions
from psychopy.localization import _translate
from psychopy.tools import versionchooser as vc
from psychopy.alerts import alert
from ...colorpicker import PsychoColorPicker
from pathlib import Path

from ...themes import handlers, icons

white = wx.Colour(255, 255, 255, 255)
codeSyntaxOkay = wx.Colour(220, 250, 220, 255)  # light green


class ParamCtrls():

    def __init__(self, dlg, label, param, parent, fieldName,
                 browse=False, noCtrls=False, advanced=False, appPrefs=None):
        """Create a set of ctrls for a particular Component Parameter, to be
        used in Component Properties dialogs. These need to be positioned
        by the calling dlg.

        e.g.::

            param = experiment.Param(val='boo', valType='str')
            ctrls = ParamCtrls(dlg=self, label=fieldName,param=param)
            self.paramCtrls[fieldName] = ctrls  # keep track in the dlg
            sizer.Add(ctrls.nameCtrl, (currRow,0), (1,1),wx.ALIGN_RIGHT )
            sizer.Add(ctrls.valueCtrl, (currRow,1) )
            # these are optional (the parameter might be None)
            if ctrls.typeCtrl:
                sizer.Add(ctrls.typeCtrl, (currRow,2) )
            if ctrls.updateCtrl:
                sizer.Add(ctrls.updateCtrl, (currRow,3))

        If browse is True then a browseCtrl will be added (you need to
        bind events yourself). If noCtrls is True then no actual wx widgets
        are made, but attribute names are created

        `fieldName`'s value is always in en_US, and never for display,
        whereas `label` is only for display and can be translated or
        tweaked (e.g., add '$'). Component._localized.keys() are
        `fieldName`s, and .values() are `label`s.
        """
        super(ParamCtrls, self).__init__()
        self.param = param
        self.dlg = dlg
        self.dpi = self.dlg.dpi
        self.valueWidth = self.dpi * 3.5
        # try to find the experiment
        self.exp = None
        tryForExp = self.dlg

        while self.exp is None:
            if hasattr(tryForExp, 'frame'):
                self.exp = tryForExp.frame.exp
            else:
                try:
                    tryForExp = tryForExp.parent  # try going up a level
                except Exception:
                    tryForExp.parent

        # param has the fields:
        #   val, valType, allowedVals=[],allowedTypes=[],
        #   hint="", updates=None, allowedUpdates=None
        # we need the following:
        self.nameCtrl = self.valueCtrl = self.typeCtrl = None
        self.updateCtrl = self.browseCtrl = None
        if noCtrls:
            return  # we don't need to do any more

        if type(param.val) == numpy.ndarray:
            initial = param.val.tolist()  # convert numpy arrays to lists
        label = _translate(label)
        self.nameCtrl = wx.StaticText(parent, -1, label, size=wx.DefaultSize)

        if fieldName == 'Use version':
            # _localVersionsCache is the default (faster) when creating
            # settings. If remote info has become available in the meantime,
            # now populate with that as well
            if vc._remoteVersionsCache:
                options = vc._versionFilter(
                    vc.versionOptions(local=False), wx.__version__)
                versions = vc._versionFilter(
                    vc.availableVersions(local=False), wx.__version__)
                param.allowedVals = (options + [''] + versions)

        if param.inputType == "single":
            # Create single line string control
            self.valueCtrl = paramCtrls.SingleLineCtrl(
                parent, 
                val=str(param.val), 
                valType=param.valType,
                fieldName=fieldName, 
                size=wx.Size(int(self.valueWidth), 24))
        elif param.inputType == 'multi':
            if param.valType == "extendedCode":
                # Create multiline code control
                self.valueCtrl = paramCtrls.CodeCtrl(
                    parent, 
                    val=str(param.val), 
                    valType=param.valType, 
                    fieldName=fieldName, 
                    size=wx.Size(int(self.valueWidth), 144))
            else:
                # Create multiline string control
                self.valueCtrl = paramCtrls.MultiLineCtrl(
                    parent, 
                    val=str(param.val),
                    valType=param.valType,
                    fieldName=fieldName, 
                    size=wx.Size(int(self.valueWidth), 144))
            # Set focus if field is text of a Textbox or Text component
            if fieldName == 'text':
                self.valueCtrl.SetFocus()
        elif param.inputType == 'spin':
            # Create single line string control
            self.valueCtrl = paramCtrls.SingleLineCtrl(
                parent, 
                val=str(param.val), 
                valType=param.valType,
                fieldName=fieldName, 
                size=wx.Size(int(self.valueWidth), 24))
            # Will have to disable spinCtrl until we have a dropdown for inputType, sadly
            # self.valueCtrl = paramCtrls.IntCtrl(parent,
            #                                     val=param.val, valType=param.valType,
            #                                     fieldName=fieldName,size=wx.Size(self.valueWidth, 24),
            #                                     limits=param.allowedVals)
        elif param.inputType == 'choice':
            self.valueCtrl = paramCtrls.ChoiceCtrl(
                parent, 
                val=str(param.val), 
                valType=param.valType,
                choices=param.allowedVals, 
                labels=param.allowedLabels,
                fieldName=fieldName, 
                size=wx.Size(int(self.valueWidth), 24))
        elif param.inputType == 'multiChoice':
            self.valueCtrl = paramCtrls.MultiChoiceCtrl(
                parent, 
                valType=param.valType, 
                vals=param.val, 
                choices=param.allowedVals, 
                fieldName=fieldName,
                size=wx.Size(int(self.valueWidth), -1))
        elif param.inputType == 'richChoice':
            self.valueCtrl = paramCtrls.RichChoiceCtrl(
                parent, 
                valType=param.valType,
                vals=param.val,
                choices=param.allowedVals, 
                labels=param.allowedLabels,
                fieldName=fieldName,
                size=wx.Size(int(self.valueWidth), -1))
        elif param.inputType == 'bool':
            self.valueCtrl = paramCtrls.BoolCtrl(
                parent, 
                name=fieldName, 
                size=wx.Size(int(self.valueWidth), 24))
            self.valueCtrl.SetValue(bool(param))
        elif param.inputType == 'file' or browse:
            self.valueCtrl = paramCtrls.FileCtrl(
                parent, 
                val=str(param.val),
                valType=param.valType,
                fieldName=fieldName, 
                size=wx.Size(int(self.valueWidth), 24))
            self.valueCtrl.allowedVals = param.allowedVals
        elif param.inputType == 'survey':
            self.valueCtrl = paramCtrls.SurveyCtrl(
                parent, 
                val=str(param.val), 
                valType=param.valType,
                fieldName=fieldName, 
                size=wx.Size(int(self.valueWidth), 24))
            self.valueCtrl.allowedVals = param.allowedVals
        elif param.inputType == 'fileList':
            self.valueCtrl = paramCtrls.FileListCtrl(
                parent, 
                choices=param.val, 
                valType=param.valType,
                size=wx.Size(int(self.valueWidth), 100), 
                pathtype="rel")
        elif param.inputType == 'table':
            self.valueCtrl = paramCtrls.TableCtrl(
                parent, 
                val=param.val, 
                valType=param.valType,
                fieldName=fieldName, 
                size=wx.Size(int(self.valueWidth), 24))
        elif param.inputType == 'color':
            self.valueCtrl = paramCtrls.ColorCtrl(
                parent,
                val=param.val, 
                valType=param.valType,
                fieldName=fieldName, 
                size=wx.Size(int(self.valueWidth), 24))
        elif param.inputType == 'dict':
            self.valueCtrl = paramCtrls.DictCtrl(
                parent,
                val=param.val,
                labels=param.allowedLabels,
                valType=param.valType,
                fieldName=fieldName)
        elif param.inputType == 'inv':
            self.valueCtrl = paramCtrls.InvalidCtrl(
                parent,
                val=str(param.val), 
                valType=param.valType,
                fieldName=fieldName, 
                size=wx.Size(int(self.valueWidth), 24))
        else:
            self.valueCtrl = paramCtrls.SingleLineCtrl(
                parent,
                val=str(param.val), 
                valType=param.valType,
                fieldName=fieldName,
                size=wx.Size(int(self.valueWidth), 24))
            logging.warn(
                f"Parameter {fieldName} has unrecognised inputType \"{param.inputType}\"")

        # if fieldName == 'Experiment info':
        #     # for expInfo convert from a string to the list-of-dicts
        # val = self.expInfoToListWidget(param.val)
        #     self.valueCtrl = dialogs.ListWidget(
        #         parent, val, order=['Field', 'Default'])
        if hasattr(self.valueCtrl, 'SetToolTip'):
            self.valueCtrl.SetToolTip(wx.ToolTip(_translate(param.hint)))
        if not callable(param.allowedVals) and len(param.allowedVals) == 1 or param.readOnly:
            self.valueCtrl.Disable()  # visible but can't be changed

        # add a Validator to the valueCtrl
        if fieldName == "name":
            self.valueCtrl.SetValidator(NameValidator())
        elif param.inputType in ("single", "multi"):
            # only want anything that is valType code, or can be with $
            self.valueCtrl.SetValidator(CodeSnippetValidator(fieldName, param.label))

        # create the type control
        if len(param.allowedTypes):
            # are there any components with non-empty allowedTypes?
            self.typeCtrl = wx.Choice(parent, choices=param.allowedTypes)
            self.typeCtrl._choices = copy.copy(param.allowedTypes)
            index = param.allowedTypes.index(param.valType)
            self.typeCtrl.SetSelection(index)
            if len(param.allowedTypes) == 1:
                self.typeCtrl.Disable()  # visible but can't be changed

        # create update control
        _localizedUpdateLbls = {
            'constant': _translate('constant'),
            'set every repeat': _translate('set every repeat'),
            'set every frame': _translate('set every frame'),
        }
        if param.allowedUpdates is not None and len(param.allowedUpdates):
            # updates = display-only version of allowed updates
            updateLabels = [_localizedUpdateLbls.get(upd, upd) for upd in param.allowedUpdates]
            # allowedUpdates = extend version of allowed updates that includes
            # "set during:static period"
            allowedUpdates = copy.copy(param.allowedUpdates)
            for routineName, routine in list(self.exp.routines.items()):
                for static in routine.getStatics():
                    # Note: replacing following line with
                    # "localizedMsg = _translate(msg)",
                    # poedit would not able to find this message.
                    msg = "set during: "
                    localizedMsg = _translate("set during: ")
                    fullName = "{}.{}".format(
                        routineName, static.params['name'])
                    allowedUpdates.append(msg + fullName)
                    updateLabels.append(localizedMsg + fullName)
            self.updateCtrl = wx.Choice(parent, choices=updateLabels)
            # stash non-localized choices to allow retrieval by index:
            self.updateCtrl._choices = copy.copy(allowedUpdates)
            # If parameter isn't in list, default to the first choice
            if param.updates not in allowedUpdates:
                param.updates = allowedUpdates[0]
            # get index of the currently set update value, set display:
            index = allowedUpdates.index(param.updates)
            # set by integer index, not string value
            self.updateCtrl.SetSelection(index)

        if param.allowedUpdates != None and len(param.allowedUpdates) == 1:
            self.updateCtrl.Disable()  # visible but can't be changed

    def _getCtrlValue(self, ctrl):
        """Retrieve the current value form the control (whatever type of ctrl
        it is, e.g. checkbox.GetValue, choice.GetSelection)
        Different types of control have different methods for retrieving
        value. This function checks them all and returns the value or None.

        .. note::
            Don't use GetStringSelection() here to avoid that translated value
            is returned. Instead, use GetSelection() to get index of selection
            and get untranslated value from _choices attribute.
        """
        if ctrl is None:
            return None
        elif hasattr(ctrl, 'getValue'):
            return ctrl.getValue()
        elif ctrl == self.updateCtrl:
            return ctrl.GetStringSelection()
        elif hasattr(ctrl, 'GetText'):
            return ctrl.GetText()
        elif hasattr(ctrl, 'GetValue'):  # e.g. TextCtrl
            val = ctrl.GetValue()
            if isinstance(self.valueCtrl, dialogs.ListWidget):
                val = self.expInfoFromListWidget(val)
            return val
        elif hasattr(ctrl, 'GetCheckedStrings'):
            return ctrl.GetCheckedStrings()
        elif hasattr(ctrl, 'GetLabel'):  # for wx.StaticText
            return ctrl.GetLabel()
        else:
            print("failed to retrieve the value for %s" % ctrl)
            return None

    def _setCtrlValue(self, ctrl, newVal):
        """Set the current value of the control (whatever type of ctrl it
        is, e.g. checkbox.SetValue, choice.SetSelection)
        Different types of control have different methods for retrieving
        value. This function checks them all and returns the value or None.

        .. note::
            Don't use SetStringSelection() here to avoid using translated
            value.  Instead, get index of the value using _choices attribute
            and use SetSelection() to set the value.
        """
        if ctrl is None:
            return None
        elif hasattr(ctrl, "setValue"):
            ctrl.setValue(newVal)
        elif hasattr(ctrl, 'SetValue'):  # e.g. TextCtrl
            ctrl.SetValue(newVal)
        elif hasattr(ctrl, 'SetSelection'):  # for wx.Choice
            # _choices = list of non-localized strings, set during __init__
            # NOTE: add untranslated value to _choices if
            # _choices.index(newVal) fails.
            index = ctrl._choices.index(newVal)
            # set the display to the localized version of the string:
            ctrl.SetSelection(index)
        elif hasattr(ctrl, 'SetLabel'):  # for wx.StaticText
            ctrl.SetLabel(newVal)
        else:
            print("failed to retrieve the value for %s" % (ctrl))

    def getValue(self):
        """Get the current value of the value ctrl
        """
        return self._getCtrlValue(self.valueCtrl)

    def setValue(self, newVal):
        """Get the current value of the value ctrl
        """
        return self._setCtrlValue(self.valueCtrl, newVal)

    def getType(self):
        """Get the current value of the type ctrl
        """
        if self.typeCtrl:
            return self._getCtrlValue(self.typeCtrl)

    def getUpdates(self):
        """Get the current value of the updates ctrl
        """
        if self.updateCtrl:
            return self._getCtrlValue(self.updateCtrl)

    def setVisible(self, newVal=True):
        self._visible = newVal
        if hasattr(self.valueCtrl, "ShowAll"):
            self.valueCtrl.ShowAll(newVal)
        else:
            self.valueCtrl.Show(newVal)
        self.nameCtrl.Show(newVal)
        if self.updateCtrl:
            self.updateCtrl.Show(newVal)
        if self.typeCtrl:
            self.typeCtrl.Show(newVal)

    def getVisible(self):
        if hasattr(self, "_visible"):
            return self._visible
        else:
            return self.valueCtrl.IsShown()

    def expInfoToListWidget(self, expInfoStr):
        """Takes a string describing a dictionary and turns it into a format
        that the ListWidget can receive.

        returns: list of dicts of {Field:'', Default:''}
        """
        expInfo = self.exp.settings.getInfo()

        listOfDicts = []
        for field, default in list(expInfo.items()):
            listOfDicts.append({'Field': field, 'Default': default})
        return listOfDicts

    def expInfoFromListWidget(self, listOfDicts):
        """Creates a string representation of a dict from a list of
        field / default values.
        """
        expInfo = {}
        for field in listOfDicts:
            expInfo[field['Field']] = field['Default']
        expInfoStr = repr(expInfo)
        return expInfoStr

    def setChangesCallback(self, callbackFunction):
        """Set a callback to detect any changes in this value (whether it's
        a checkbox event or a text event etc

        :param callbackFunction: the function to be called when the valueCtrl
        changes value
        :return:
        """
        if isinstance(self.valueCtrl, wx.TextCtrl):
            self.valueCtrl.Bind(wx.EVT_KEY_UP, callbackFunction)
        elif isinstance(self.valueCtrl, CodeBox):
            self.valueCtrl.Bind(wx.stc.EVT_STC_CHANGE, callbackFunction)
        elif isinstance(self.valueCtrl, wx.ComboBox):
            self.valueCtrl.Bind(wx.EVT_COMBOBOX, callbackFunction)
        elif isinstance(self.valueCtrl, (wx.Choice, paramCtrls.RichChoiceCtrl)):
            self.valueCtrl.Bind(wx.EVT_CHOICE, callbackFunction)
        elif isinstance(self.valueCtrl, wx.CheckListBox):
            self.valueCtrl.Bind(wx.EVT_CHECKLISTBOX, callbackFunction)
        elif isinstance(self.valueCtrl, wx.CheckBox):
            self.valueCtrl.Bind(wx.EVT_CHECKBOX, callbackFunction)
        elif isinstance(self.valueCtrl, paramCtrls.CodeCtrl):
            self.valueCtrl.Bind(wx.EVT_KEY_UP, callbackFunction)
        elif isinstance(self.valueCtrl, (paramCtrls.DictCtrl, paramCtrls.FileListCtrl)):
            pass
        else:
            print("setChangesCallback doesn't know how to handle ctrl {}"
                  .format(type(self.valueCtrl)))


class StartStopCtrls(wx.GridBagSizer):
    def __init__(self, parent, params):
        wx.GridBagSizer.__init__(self, 0, 0)
        # Make ctrls
        self.ctrls = {}
        self.parent = parent
        empty = True
        for name, param in params.items():
            if name in ['startVal', 'stopVal']:
                # Add dollar sign
                self.dollar = wx.StaticText(parent, label="$")
                self.Add(self.dollar, (0, 0), border=6, flag=wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.RIGHT)
                # Add ctrl
                self.ctrls[name] = wx.TextCtrl(parent,
                                               value=str(param.val), size=wx.Size(-1, 24))
                self.ctrls[name].Bind(wx.EVT_TEXT, self.updateCodeFont)
                self.updateCodeFont(self.ctrls[name])
                self.label = wx.StaticText(parent, label=param.label)
                self.Add(self.ctrls[name], (0, 2), border=6, flag=wx.EXPAND | wx.TOP)
                # There is now content
                empty = False
            if name in ['startType', 'stopType']:
                localizedChoices = list(map(_translate, param.allowedVals or [param.val]))
                self.ctrls[name] = wx.Choice(parent,
                                             choices=localizedChoices,
                                             size=wx.Size(96, 24))
                self.ctrls[name]._choices = copy.copy(param.allowedVals)
                self.ctrls[name].SetSelection(param.allowedVals.index(str(param.val)))
                self.Add(self.ctrls[name], (0, 1), border=6, flag=wx.EXPAND | wx.TOP)
                # There is now content
                empty = False
            if name in ['startEstim', 'durationEstim']:
                self.ctrls[name] = wx.TextCtrl(parent,
                                               value=str(param.val), size=wx.Size(-1, 24))
                self.ctrls[name].Bind(wx.EVT_TEXT, self.updateCodeFont)
                self.updateCodeFont(self.ctrls[name])
                self.estimLabel = wx.StaticText(parent,
                                                label=param.label, size=wx.Size(-1, 24))
                self.estimLabel.SetForegroundColour("grey")
                self.Add(self.estimLabel, (1, 1), border=6, flag=wx.EXPAND | wx.ALL)
                self.Add(self.ctrls[name], (1, 2), border=6, flag=wx.EXPAND | wx.TOP | wx.BOTTOM)
                # There is now content
                empty = False
        if not empty:
            self.AddGrowableCol(2)

    def getVisible(self):
        return all(ctrl.IsShown() for ctrl in self.ctrls.values())

    def setVisible(self, visible=True):
        # Show/hide controls
        for ctrl in self.ctrls.values():
            ctrl.Show(visible)
        # Show/hide labels
        if hasattr(self, "estimLabel"):
            self.estimLabel.Show(visible)
        if hasattr(self, "label"):
            self.label.Show(visible)
        # Set value to None if hidden (specific to start/stop)
        if not visible:
            if "startVal" in self.ctrls:
                self.ctrls["startVal"].Value = ""
            if "stopVal" in self.ctrls:
                self.ctrls["stopVal"].Value = ""
        # Layout
        self.parent.Layout()

    def updateCodeFont(self, evt=None):
        """Style input box according to code wanted"""
        if isinstance(evt, wx.TextCtrl):
            obj = evt
        else:
            obj = evt.EventObject
        if psychopy.experiment.utils.unescapedDollarSign_re.match(obj.GetLineText(0)):
            # Set font if code
            obj.SetFont(self.parent.GetTopLevelParent().app._codeFont.Bold())
        else:
            # Set font if not
            obj.SetFont(self.parent.GetTopLevelParent().app._mainFont)


class ParamNotebook(wx.Notebook, handlers.ThemeMixin):
    class CategoryPage(wx.Panel, handlers.ThemeMixin):
        def __init__(self, parent, dlg, params, categ=None):
            wx.Panel.__init__(self, parent, size=(600, -1))
            self.parent = parent
            self.parent = parent
            self.dlg = dlg
            self.app = self.dlg.app
            self.categ = categ
            # Setup sizer
            self.border = wx.BoxSizer()
            self.SetSizer(self.border)
            self.sizer = wx.GridBagSizer(0, 0)
            self.border.Add(self.sizer, border=12, proportion=1, flag=wx.ALL | wx.EXPAND)
            # Add controls
            self.ctrls = {}
            self.row = 0
            # Sort params
            sortedParams = OrderedDict(params)
            for name in reversed(self.parent.element.order):
                if name in sortedParams:
                    sortedParams.move_to_end(name, last=False)
            # Make name ctrl
            if "name" in sortedParams:
                param = sortedParams.pop("name")
                self.addParam("name", param)
            # Make start controls
            startParams = OrderedDict()
            for name in ['startVal', 'startType', 'startEstim']:
                if name in sortedParams:
                    startParams[name] = sortedParams.pop(name)
            if startParams:
                self.startCtrl = self.addStartStopCtrl(startParams)
            # Make stop controls
            stopParams = OrderedDict()
            for name in ['stopVal', 'stopType', 'durationEstim']:
                if name in sortedParams:
                    stopParams[name] = sortedParams.pop(name)
            if stopParams:
                self.stopCtrl = self.addStartStopCtrl(stopParams)
            # Make controls
            for name, param in sortedParams.items():
                self.addParam(name, param)
            # Add growable
            self.sizer.AddGrowableCol(1, 1)
            # Check depends
            self.checkDepends()

        def addParam(self, name, param):
            # Make ctrl
            self.ctrls[name] = ParamCtrls(self.dlg, param.label, param, self, name)
            # Add value ctrl
            _flag = wx.EXPAND | wx.ALL
            if hasattr(self.ctrls[name].valueCtrl, '_szr'):
                self.sizer.Add(self.ctrls[name].valueCtrl._szr, (self.row, 1), border=6, flag=_flag)
            else:
                self.sizer.Add(self.ctrls[name].valueCtrl, (self.row, 1), border=6, flag=_flag)
            # Add other ctrl stuff
            _flag = wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
            self.sizer.Add(self.ctrls[name].nameCtrl, (self.row, 0), (1, 1), border=5, flag=_flag)
            if self.ctrls[name].typeCtrl:
                self.sizer.Add(self.ctrls[name].typeCtrl, (self.row, 2), border=5, flag=_flag)
            if self.ctrls[name].updateCtrl:
                self.sizer.Add(self.ctrls[name].updateCtrl, (self.row, 3), border=5, flag=_flag)
            # Link to depends callback
            self.ctrls[name].setChangesCallback(self.doValidate)
            if name == 'name':
                self.ctrls[name].valueCtrl.SetFocus()
            # Some param ctrls need to grow with page
            if param.inputType in ('multi', 'fileList'):
                self.sizer.AddGrowableRow(self.row, proportion=1)
            # Iterate row
            self.row += 1

        def addStartStopCtrl(self, params):
            # Make controls
            panel = StartStopCtrls(self, params)
            # Add to dict of ctrls
            self.ctrls.update(panel.ctrls)
            # Add label
            _flag = wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL
            self.sizer.Add(panel.label, (self.row, 0), (1, 1), border=5, flag=_flag)
            # Add ctrls
            _flag = wx.EXPAND | wx.ALL
            self.sizer.Add(panel, (self.row, 1), border=6, flag=_flag)
            # Iterate row
            self.row += 1

            return panel

        def checkDepends(self, event=None):
            """Checks the relationships between params that depend on each other

            Dependencies are a list of dicts like this (as in BaseComponent):
            {"dependsOn": "shape",
             "condition": "=='n vertices",
             "param": "n vertices",
             "true": "Enable",  # what to do with param if condition is True
             "false": "Disable",  # permitted: hide, show, enable, disable
            }"""
            isChanged = False
            for thisDep in self.parent.element.depends:
                if not (
                        thisDep['param'] in list(self.ctrls) + ['start', 'stop']
                        and thisDep['dependsOn'] in self.ctrls):
                    # If params are on another page, skip
                    continue
                # Get associated ctrl
                if thisDep['param'] == 'start':
                    dependentCtrls = self.startCtrl
                elif thisDep['param'] == 'stop':
                    dependentCtrls = self.stopCtrl
                else:
                    dependentCtrls = self.ctrls[thisDep['param']]
                dependencyCtrls = self.ctrls[thisDep['dependsOn']]
                condString = "dependencyCtrls.getValue() {}".format(thisDep['condition'])
                if eval(condString):
                    action = thisDep['true']
                else:
                    action = thisDep['false']
                if action == "hide":
                    # Track change if changed
                    if dependentCtrls.getVisible():
                        isChanged = True
                    # Apply visibiliy
                    dependentCtrls.setVisible(False)
                elif action == "show":
                    # Track change if changed
                    if not dependentCtrls.getVisible():
                        isChanged = True
                    dependentCtrls.setVisible(True)
                elif action == "populate":
                    # only repopulate if dependency ctrl has changed
                    dependencyParam = self.parent.element.params[thisDep['dependsOn']]
                    if dependencyParam.val != dependencyCtrls.getValue():
                        dependencyParam.val = dependencyCtrls.getValue()
                        if hasattr(dependentCtrls.valueCtrl, "populate"):
                            dependentCtrls.valueCtrl.populate()
                else:
                    # if action is "enable" then do ctrl.Enable() etc
                    for ctrlName in ['valueCtrl', 'nameCtrl', 'updatesCtrl']:
                        # disable/enable all parts of the control
                        if hasattr(dependentCtrls, ctrlName):
                            evalStr = ("dependentCtrls.{}.{}()"
                                       .format(ctrlName, action.title()))
                            eval(evalStr)
            # Update sizer
            if isChanged:
                self.sizer.SetEmptyCellSize((0, 0))
                self.sizer.Layout()
                if isinstance(self.dlg, wx.Dialog):
                    self.dlg.Fit()
                self.Refresh()

        def doValidate(self, event=None):
            self.Validate()
            self.checkDepends(event=event)
            if hasattr(self.dlg, "updateExperiment"):
                self.dlg.updateExperiment()

        def _applyAppTheme(self, target=None):
            self.SetBackgroundColour("white")

    def __init__(self, parent, element, experiment):
        # activate plugins so backends are available
        if hasattr(element, "loadBackends"):
            element.loadBackends()

        wx.Notebook.__init__(self, parent)
        self.parent = parent
        self.exp = experiment
        self.element = element
        self.params = element.params
        # Setup sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        # Get arrays of params
        paramsByCateg = OrderedDict()
        for name, param in self.params.items():
            # Add categ if not present
            if param.categ not in paramsByCateg:
                paramsByCateg[param.categ] = OrderedDict()
            # Append param to categ
            paramsByCateg[param.categ][name] = param
        # Move high priority categs to the front
        for categ in reversed(['Basic', 'Layout', 'Appearance', 'Formatting', 'Texture']):
            if categ in paramsByCateg:
                paramsByCateg.move_to_end(categ, last=False)
        # Move low priority categs to the end
        for categ in ['Data', 'Custom', 'Hardware', 'Testing']:
            if categ in paramsByCateg:
                paramsByCateg.move_to_end(categ, last=True)
        # Setup pages
        self.paramCtrls = {}
        for categ, params in paramsByCateg.items():
            page = self.CategoryPage(self, self.parent, params, categ=categ)
            self.paramCtrls.update(page.ctrls)
            # Add page to notebook
            self.AddPage(page, _translate(categ))

    def checkDepends(self, event=None):
        """
        When check depends is called on the whole notebook, check each page
        """
        for i in range(self.GetPageCount()):
            self.GetPage(i).checkDepends(event)

    def getParams(self):
        """retrieves data from any fields in self.paramCtrls
        (populated during the __init__ function)

        The new data from the dlg get inserted back into the original params
        used in __init__ and are also returned from this method.
        
        .. note::
            Don't use GetStringSelection() here to avoid that translated value
            is returned. Instead, use GetSelection() to get index of selection
            and get untranslated value from _choices attribute.
        """
        # Create empty list to store fieldnames of params for deletion
        killList = []
        # get data from input fields
        for fieldName in self.params:
            param = self.params[fieldName]
            # Get control
            ctrl = self.paramCtrls[fieldName]
            # Get value
            if hasattr(ctrl, "getValue"):
                param.val = ctrl.getValue()
            elif hasattr(ctrl, "GetValue"):
                param.val = ctrl.GetValue()
            elif isinstance(ctrl, wx.Choice):
                if hasattr(ctrl, "_choices"):
                    param.val = ctrl._choices[ctrl.GetSelection()]
                else:
                    # use GetStringSelection()
                    # only if this control doesn't has _choices
                    param.val = ctrl.GetStringSelection()
            # Get type
            if hasattr(ctrl, "typeCtrl"):
                if ctrl.typeCtrl:
                    param.valType = ctrl.typeCtrl._choices[ctrl.typeCtrl.GetSelection()]
            # Get update type
            if hasattr(ctrl, "updateCtrl"):
                if ctrl.updateCtrl:
                    updates = ctrl.updateCtrl._choices[ctrl.updateCtrl.GetSelection()]
                    # may also need to update a static
                    if param.updates != updates:
                        self._updateStaticUpdates(fieldName,
                                                  param.updates, updates)
                        param.updates = updates
            # If requested, mark param for deletion
            if hasattr(ctrl, "valueCtrl") and isinstance(ctrl.valueCtrl, paramCtrls.InvalidCtrl) and ctrl.valueCtrl.forDeletion:
                killList.append(fieldName)
        # Delete params on kill list
        for fieldName in killList:
            del self.params[fieldName]
        return self.params

    def getCategoryIndex(self, categ):
        """
        Get page index for a given category
        """
        # iterate through pages by index
        for i in range(self.GetPageCount()):
            # if this page is the correct category, return current index
            if self.GetPage(i).categ == categ:
                return i

    def _updateStaticUpdates(self, fieldName, updates, newUpdates):
        """If the old/new updates ctrl is using a Static component then we
        need to remove/add the component name to the appropriate static
        """
        exp = self.exp
        compName = self.params['name'].val
        if hasattr(updates, 'startswith') and "during:" in updates:
            # remove the part that says 'during'
            updates = updates.split(': ')[1]
            origRoutine, origStatic = updates.split('.')
            _comp = exp.routines[origRoutine].getComponentFromName(origStatic)
            if _comp is not None:
                _comp.remComponentUpdate(origRoutine, compName, fieldName)
        if hasattr(newUpdates, 'startswith') and "during:" in newUpdates:
            # remove the part that says 'during'
            newUpdates = newUpdates.split(': ')[1]
            newRoutine, newStatic = newUpdates.split('.')
            _comp = exp.routines[newRoutine].getComponentFromName(newStatic)
            _comp.addComponentUpdate(newRoutine, compName, fieldName)


class _BaseParamsDlg(wx.Dialog):
    _style = wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT | wx.TAB_TRAVERSAL

    def __init__(self, frame, element, experiment,
                 suppressTitles=True,
                 showAdvanced=False,
                 size=wx.DefaultSize,
                 style=_style, editing=False,
                 timeout=None, openToPage=None):

        # translate title
        if "name" in element.params:
            title = element.params['name'].val + _translate(' Properties')
        elif "expName" in element.params:
            title = element.params['expName'].val + _translate(' Properties')
        else:
            title = "Properties"
        # get help url
        if hasattr(element, 'url'):
            helpUrl = element.url
        else:
            helpUrl = None

        # use translated title for display
        wx.Dialog.__init__(self, parent=None, id=-1, title=title,
                           size=size, style=style)
        self.frame = frame
        self.app = frame.app
        self.dpi = self.app.dpi
        self.helpUrl = helpUrl
        self.params = params = element.params  # dict
        self.title = title
        self.timeout = timeout
        if (not editing and
                title != 'Experiment Settings' and
                'name' in self.params):
            # then we're adding a new component, so provide known-valid name:
            makeValid = self.frame.exp.namespace.makeValid
            self.params['name'].val = makeValid(params['name'].val)
        self.paramCtrls = {}
        CodeSnippetValidator.clsWarnings = {}
        self.suppressTitles = suppressTitles
        self.showAdvanced = showAdvanced
        self.order = element.order
        self.depends = element.depends
        self.data = []
        # max( len(str(self.params[x])) for x in keys )
        self.maxFieldLength = 10
        self.timeParams = ['startType', 'startVal', 'stopType', 'stopVal']
        self.codeFieldNameFromID = {}
        self.codeIDFromFieldName = {}
        # a list of all panels in the ctrl to be traversed by validator
        self.panels = []
        # need font size for STCs:
        if wx.Platform == '__WXMSW__':
            self.faceSize = 10
        elif wx.Platform == '__WXMAC__':
            self.faceSize = 14
        else:
            self.faceSize = 12

        # create main sizer
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.ctrls = ParamNotebook(self, element, experiment)
        self.paramCtrls = self.ctrls.paramCtrls
        # open to page
        if openToPage is not None:
            i = self.ctrls.getCategoryIndex(openToPage)
            self.ctrls.ChangeSelection(i)

        self.mainSizer.Add(self.ctrls,  # ctrls is the notebook of params
                           proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizerAndFit(self.mainSizer)

    def getParams(self):
        return self.ctrls.getParams()

    def openMonitorCenter(self, event):
        self.app.openMonitorCenter(event)
        self.paramCtrls['Monitor'].valueCtrl.SetFocus()
        # need to delay until the user closes the monitor center
        # self.paramCtrls['Monitor'].valueCtrl.Clear()
        # if wx.TheClipboard.Open():
        #    dataObject = wx.TextDataObject()
        #    if wx.TheClipboard.GetData(dataObject):
        #        self.paramCtrls['Monitor'].valueCtrl.
        #            WriteText(dataObject.GetText())
        #    wx.TheClipboard.Close()

    def launchColorPicker(self, event):
        # bring up a colorPicker
        dlg = PsychoColorPicker(self.frame)
        dlg.ShowModal()
        dlg.Destroy()

    @staticmethod
    def showScreenNumbers(evt=None, dur=5):
        """
        Spawn some PsychoPy windows to display each monitor's number.
        """
        from psychopy import visual
        for n in range(wx.Display.GetCount()):
            start = time.time()
            # Open a window on the appropriate screen
            win = visual.Window(
                pos=(0, 0),
                size=(128, 128),
                units="norm",
                screen=n,
                color="black"
            )
            # Draw screen number to the window
            screenNum = visual.TextBox2(
                win, text=str(n + 1),
                size=1, pos=0,
                alignment="center", anchor="center",
                letterHeight=0.5, bold=True,
                fillColor=None, color="white"
            )
            # Progress bar
            progBar = visual.Rect(
                win, anchor="bottom left",
                pos=(-1, -1), size=(0, 0.1), 
                fillColor='white'
            )

            # Frame loop
            t = 0
            while t < dur:
                t = time.time() - start
                # Set progress bar size
                progBar.size = (t / 5 * 2, 0.1)
                # Draw
                progBar.draw()
                screenNum.draw()
                win.flip()
            # Close window
            win.close()

    def onNewTextSize(self, event):
        self.Fit()  # for ExpandoTextCtrl this is needed

    def show(self, testing=False):
        """Adds an OK and cancel button, shows dialogue.

        This method returns wx.ID_OK (as from ShowModal), but also
        sets self.OK to be True or False
        """
        # add buttons for OK and Cancel
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        # help button if we know the url
        if self.helpUrl != None:
            helpBtn = wx.Button(self, wx.ID_HELP, _translate(" Help "))
            _tip = _translate("Go to online help about this component")
            helpBtn.SetToolTip(wx.ToolTip(_tip))
            helpBtn.Bind(wx.EVT_BUTTON, self.onHelp)
            buttons.Add(helpBtn, 0,
                        flag=wx.LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                        border=3)
        self.OKbtn = wx.Button(self, wx.ID_OK, _translate(" OK "))
        # intercept OK button if a loop dialog, in case file name was edited:
        if type(self) == DlgLoopProperties:
            self.OKbtn.Bind(wx.EVT_BUTTON, self.onOK)
        self.OKbtn.SetDefault()
        CANCEL = wx.Button(self, wx.ID_CANCEL, _translate(" Cancel "))

        # Add validator stuff
        self.warnings = WarningManager(self)
        self.mainSizer.Add(self.warnings.output, border=3, flag=wx.EXPAND | wx.ALL)
        self.Validate()  # disables OKbtn if bad name, syntax error, etc

        buttons.AddStretchSpacer()

        # Add Okay and Cancel buttons
        if sys.platform == "win32":
            btns = [self.OKbtn, CANCEL]
        else:
            btns = [CANCEL, self.OKbtn]
        buttons.Add(btns[0], 0,
                    wx.ALL | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
                    border=3)
        buttons.Add(btns[1], 0,
                    wx.ALL | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
                    border=3)

        # buttons.Realize()
        # add to sizer
        self.mainSizer.Add(buttons, flag=wx.ALL | wx.EXPAND, border=3)
        self.SetSizerAndFit(self.mainSizer)
        self.mainSizer.Layout()
        # move the position to be v near the top of screen and
        # to the right of the left-most edge of builder
        builderPos = self.frame.GetPosition()
        self.SetPosition((builderPos[0] + 200, 20))

        # self.paramCtrls['name'].valueCtrl.SetFocus()
        # do show and process return
        if self.timeout is not None:
            timeout = wx.CallLater(self.timeout, self.autoTerminate)
            timeout.Start()
        if testing:
            self.Show()
        else:
            retVal = self.ShowModal()
            self.OK = bool(retVal == wx.ID_OK)
        return wx.ID_OK

    def autoTerminate(self, event=None, retval=1):
        """Terminates the dialog early, for use with a timeout

        :param event: an optional wx.EVT
        :param retval: an optional int to pass to EndModal()
        :return:
        """
        self.EndModal(retval)

    def Validate(self, *args, **kwargs):
        """Validate form data and disable OK button if validation fails.
        """
        return self.ctrls.Validate()

    def onOK(self, event=None):
        """Handler for OK button which should validate dialog contents.
        """
        valid = self.Validate()
        if not valid:
            return
        event.Skip()

    def onTextEventCode(self, event=None):
        """process text events for code components: change color to grey
        """
        codeBox = event.GetEventObject()
        textBeforeThisKey = codeBox.GetText()
        keyCode = event.GetKeyCode()
        pos = event.GetPosition()
        # ord(10)='\n', ord(13)='\l'
        if keyCode < 256 and keyCode not in [10, 13]:
            # new line is trigger to check syntax
            codeBox.setStatus('changed')
        elif (keyCode in (10, 13) and
                len(textBeforeThisKey) and
                textBeforeThisKey[-1] != ':'):
            # ... but skip the check if end of line is colon ord(58)=':'
            self._setNameColor(self._testCompile(codeBox))
        event.Skip()

    def _testCompile(self, ctrl, mode='exec'):
        """checks whether code.val is legal python syntax,
        returns error status

        mode = 'exec' (statement or expr) or 'eval' (expr only)
        """
        if hasattr(ctrl, 'GetText'):
            val = ctrl.GetText()
        elif hasattr(ctrl, 'GetValue'):
            # e.g. TextCtrl
            val = ctrl.GetValue()
        else:
            msg = 'Unknown type of ctrl in _testCompile: %s'
            raise ValueError(msg % (type(ctrl)))
        try:
            compile(val, '', mode)
            syntaxOk = True
            ctrl.setStatus('OK')
        except SyntaxError:
            ctrl.setStatus('error')
            syntaxOk = False
        return syntaxOk

    def checkCodeSyntax(self, event=None):
        """Checks syntax for whole code component by code box,
        sets box bg-color.
        """
        if hasattr(event, 'GetEventObject'):
            codeBox = event.GetEventObject()
        elif hasattr(event, 'GetText'):
            # we were given the control itself, not an event
            codeBox = event
        else:
            msg = ('checkCodeSyntax received unexpected event object (%s). '
                   'Should be a wx.Event or a CodeBox')
            raise ValueError(msg % type(event))
        text = codeBox.GetText()
        if not text.strip():
            # if basically empty
            codeBox.SetBackgroundColour(white)
            return
        # test syntax:
        goodSyntax = self._testCompile(codeBox)
        # not quite every dialog has a name (e.g. settings)
        # but if so then set its color
        if 'name' in self.paramCtrls:
            self._setNameColor(goodSyntax)

    def _setNameColor(self, goodSyntax):
        if goodSyntax:
            _nValCtrl = self.paramCtrls['name'].valueCtrl
            _nValCtrl.SetBackgroundColour(codeSyntaxOkay)
            self.nameOKlabel.SetLabel('')
        else:
            self.paramCtrls['name'].valueCtrl.SetBackgroundColour(white)
            self.nameOKlabel.SetLabel('syntax error')

    def checkCodeWanted(self, event=None):
        """check whether a $ is present (if so, set the display font)
        """
        if hasattr(event, 'GetEventObject'):
            strBox = event.GetEventObject()
        elif hasattr(event, 'GetValue'):
            # we were given the control itself, not an event
            strBox = event
        else:
            raise ValueError('checkCodeWanted received unexpected event'
                             ' object (%s).')
        try:
            val = strBox.GetValue()
            stc = False
        except Exception:
            if not hasattr(strBox, 'GetText'):
                # eg, wx.Choice control
                if hasattr(event, 'Skip'):
                    event.Skip()
                return
            val = strBox.GetText()
            # might be StyledTextCtrl
            stc = True

        if hasattr(event, 'Skip'):
            event.Skip()

    def _checkName(self, event=None, name=None):
        """checks namespace, return error-msg (str), enable (bool)
        """
        if event:
            newName = event.GetString()
        elif name:
            newName = name
        elif hasattr(self, 'paramCtrls'):
            newName = self.paramCtrls['name'].getValue()
        elif hasattr(self, 'globalCtrls'):
            newName = self.globalCtrls['name'].getValue()
        if newName == '':
            return _translate("Missing name"), False
        else:
            namespace = self.frame.exp.namespace
            used = namespace.exists(newName)
            sameOldName = bool(newName == self.params['name'].val)
            if used and not sameOldName:
                msg = _translate(
                    "That name is in use (it's a %s). Try another name.")
                return msg % _translate(used), False
            elif not namespace.isValid(newName):  # valid as a var name
                msg = _translate("Name must be alphanumeric or _, no spaces")
                return msg, False
            # warn but allow, chances are good that its actually ok
            elif namespace.isPossiblyDerivable(newName):
                msg = namespace.isPossiblyDerivable(newName)
                return msg, True
            else:
                return "", True

    def onHelp(self, event=None):
        """Uses self.app.followLink() to self.helpUrl
        """
        self.app.followLink(url=self.helpUrl)


class DlgLoopProperties(_BaseParamsDlg):
    _style = wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT | wx.RESIZE_BORDER

    def __init__(self, frame, title="Loop Properties", loop=None,
                 helpUrl=None, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=_style, depends=[], timeout=None):
        # translate title
        localizedTitle = title.replace(' Properties',
                                       _translate(' Properties'))

        wx.Dialog.__init__(self, None, wx.ID_ANY, localizedTitle,
                           pos, size, style)
        self.helpUrl = helpUrl
        self.frame = frame
        self.expPath = Path(self.frame.filename).parent
        self.exp = frame.exp
        self.app = frame.app
        self.dpi = self.app.dpi
        self.params = {}
        self.timeout = timeout
        self.panel = wx.Panel(self, -1)
        self.globalCtrls = {}
        self.constantsCtrls = {}
        self.staircaseCtrls = {}
        self.multiStairCtrls = {}
        self.currentCtrls = {}
        self.data = []
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.conditions = None
        self.conditionsFile = None
        self.condNamesInFile = []
        # create a valid new name; save old name in case we need to revert
        namespace = frame.exp.namespace
        defaultName = namespace.makeValid('trials')
        oldLoopName = defaultName
        if loop:
            oldLoopName = loop.params['name'].val

        # create default instances of the diff loop types
        # for 'random','sequential', 'fullRandom'
        self.trialHandler = experiment.loops.TrialHandler(
            exp=self.exp, name=oldLoopName, loopType='random',
            nReps=5, conditions=[])
        # for staircases:
        self.stairHandler = experiment.loops.StairHandler(
            exp=self.exp, name=oldLoopName, nReps=50, nReversals='',
            stepSizes='[0.8,0.8,0.4,0.4,0.2]', stepType='log', startVal=0.5)
        self.multiStairHandler = experiment.loops.MultiStairHandler(
            exp=self.exp, name=oldLoopName, nReps=50, stairType='simple',
            switchStairs='random', conditions=[], conditionsFile='')

        # replace defaults with the loop we were given
        if loop is None:
            self.currentType = 'random'
            self.currentHandler = self.trialHandler
        elif loop.type == 'TrialHandler':
            self.conditions = loop.params['conditions'].val
            self.conditionsFile = loop.params['conditionsFile'].val
            self.trialHandler = self.currentHandler = loop
            # could be 'random', 'sequential', 'fullRandom'
            self.currentType = loop.params['loopType'].val
        elif loop.type == 'StairHandler':
            self.stairHandler = self.currentHandler = loop
            self.currentType = 'staircase'
        elif loop.type == 'MultiStairHandler':
            self.conditions = loop.params['conditions'].val
            self.conditionsFile = loop.params['conditionsFile'].val
            self.multiStairHandler = self.currentHandler = loop
            self.currentType = 'interleaved staircases'
        elif loop.type == 'QuestHandler':
            pass  # what to do for quest?
        # Store conditions file
        self.conditionsOrig = self.conditions
        self.params['name'] = self.currentHandler.params['name']
        self.globalPanel = self.makeGlobalCtrls()
        self.stairPanel = self.makeStaircaseCtrls()
        # the controls for Method of Constants
        self.constantsPanel = self.makeConstantsCtrls()
        self.multiStairPanel = self.makeMultiStairCtrls()
        self.mainSizer.Add(self.globalPanel, border=12,
                           flag=wx.ALL | wx.EXPAND)
        self.mainSizer.Add(wx.StaticLine(self), border=6,
                           flag=wx.ALL | wx.EXPAND)
        self.mainSizer.Add(self.stairPanel, border=12,
                           flag=wx.ALL | wx.EXPAND)
        self.mainSizer.Add(self.constantsPanel, border=12,
                           flag=wx.ALL | wx.EXPAND)
        self.mainSizer.Add(self.multiStairPanel, border=12,
                           flag=wx.ALL | wx.EXPAND)
        self.setCtrls(self.currentType)
        # create a list of panels in the dialog, for the validator to step
        # through
        self.panels = [self.globalPanel, self.stairPanel,
                       self.constantsPanel, self.multiStairPanel]

        self.params = {}
        self.params.update(self.trialHandler.params)
        self.params.update(self.stairHandler.params)
        self.params.update(self.multiStairHandler.params)
        self.paramCtrls = {}
        self.paramCtrls.update(self.globalCtrls)
        self.paramCtrls.update(self.constantsCtrls)
        self.paramCtrls.update(self.staircaseCtrls)
        self.paramCtrls.update(self.multiStairCtrls)

        if "conditionsFile" in self.globalCtrls:
            self.updateSummary()

        # show dialog and get most of the data
        self.show()
        if self.OK:
            self.params = self.getParams()
            # convert endPoints from str to list
            _endP = self.params['endPoints'].val
            self.params['endPoints'].val = eval("%s" % _endP)
            # then sort the list so the endpoints are in correct order
            self.params['endPoints'].val.sort()
            if loop:
                # editing an existing loop
                namespace.remove(oldLoopName)
            namespace.add(self.params['name'].val)
            # don't always have a conditionsFile
            if hasattr(self, 'condNamesInFile'):
                namespace.add(self.condNamesInFile)
            if hasattr(self, 'duplCondNames'):
                namespace.remove(self.duplCondNames)
        else:
            if loop is not None:
                # if we had a loop during init then revert to its old name
                loop.params['name'].val = oldLoopName

        # make sure we set this back regardless of whether OK
        # otherwise it will be left as a summary string, not a conditions
        if 'conditionsFile' in self.currentHandler.params:
            self.currentHandler.params['conditions'].val = self.conditions

    def Validate(self, *args, **kwargs):
        for ctrl in self.globalCtrls.values():
            checker = ctrl.valueCtrl.GetValidator()
            if checker:
                checker.Validate(self)
        return self.warnings.OK

    @property
    def conditionsFile(self):
        """
        Location of the conditions file, in whatever format it is best available in. Ideally
        relative to the experiment path, but if this is not possible, then absolute.
        """
        if not hasattr(self, "_conditionsFile") or self._conditionsFile is None:
            # If no file, return None
            return None
        elif "$" in str(self._conditionsFile):
            # If a variabel, return as string
            return str(self._conditionsFile)
        else:
            # Otherwise return as unix string
            return str(self._conditionsFile).replace("\\", "/")

    @conditionsFile.setter
    def conditionsFile(self, value):
        # Store last value
        self.conditionsFileOrig = self.conditionsFileAbs

        if value in (None, ""):
            # Store None as is
            self._conditionsFile = None
        elif "$" in str(value):
            # Store variable as is
            self._conditionsFile = str(value)
        else:
            # Otherwise convert to Path
            value = Path(value)
            try:
                # Relativise if possible
                self._conditionsFile = value.relative_to(self.expPath)
            except ValueError:
                # Otherwise as is
                self._conditionsFile = value

    @property
    def conditionsFileAbs(self):
        """
        Absolute path to the conditions file
        """
        if not hasattr(self, "_conditionsFile") or self._conditionsFile is None:
            # If no file, return None
            return None
        elif "$" in str(self._conditionsFile):
            # If variable. return as is
            return str(self._conditionsFile)
        elif self._conditionsFile.is_absolute():
            # Return as is if absolute
            return str(self._conditionsFile)
        else:
            # Append to experiment path if relative
            return str(self.expPath / self._conditionsFile)

    def makeGlobalCtrls(self):
        panel = wx.Panel(parent=self)
        panelSizer = wx.GridBagSizer(0, 0)
        panel.SetSizer(panelSizer)
        row = 0
        for fieldName in ('name', 'loopType', 'isTrials'):
            try:
                label = self.currentHandler.params[fieldName].label
            except Exception:
                label = fieldName
            self.globalCtrls[fieldName] = ctrls = ParamCtrls(
                dlg=self, parent=panel, label=label, fieldName=fieldName,
                param=self.currentHandler.params[fieldName])
            panelSizer.Add(ctrls.nameCtrl, [row, 0], border=3,
                           flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
            if hasattr(ctrls.valueCtrl, '_szr'):
                panelSizer.Add(ctrls.valueCtrl._szr, [row, 1], border=3,
                               flag=wx.EXPAND | wx.ALL)
            else:
                panelSizer.Add(ctrls.valueCtrl, [row, 1], border=3,
                               flag=wx.EXPAND | wx.ALL)
            row += 1
        panelSizer.AddGrowableCol(1, 1)
        self.globalCtrls['name'].valueCtrl.Bind(wx.EVT_TEXT, self.Validate)
        self.Bind(wx.EVT_CHOICE, self.onTypeChanged,
                  self.globalCtrls['loopType'].valueCtrl)
        return panel

    def makeConstantsCtrls(self):
        # a list of controls for the random/sequential versions
        # that can be hidden or shown
        handler = self.trialHandler
        # loop through the params
        keys = list(handler.params.keys())
        panel = wx.Panel(parent=self)
        panel.app=self.app
        panelSizer = wx.GridBagSizer(0, 0)
        panel.SetSizer(panelSizer)
        row = 0
        # add conditions stuff to the *end*
        if 'conditionsFile' in keys:
            keys.remove('conditionsFile')
            keys.append('conditionsFile')
        if 'conditions' in keys:
            keys.remove('conditions')
            keys.append('conditions')
        _flag = wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND
        # then step through them
        for fieldName in keys:
            # try and get alternative "label" for the parameter
            try:
                label = self.currentHandler.params[fieldName].label
                if not label:
                    # it might exist but be empty
                    label = fieldName
            except Exception:
                label = fieldName
            # handle special cases
            if fieldName == 'endPoints':
                continue  # this was deprecated in v1.62.00
            if fieldName in self.globalCtrls:
                # these have already been made and inserted into sizer
                ctrls = self.globalCtrls[fieldName]
            elif fieldName == 'conditions':
                if 'conditions' in handler.params:
                    _cond = handler.params['conditions'].val
                    text, OK = self.getTrialsSummary(_cond)
                else:
                    text = _translate("No parameters set")
                # we'll create our own widgets
                ctrls = ParamCtrls(dlg=self, parent=panel, label=label,
                                   fieldName=fieldName,
                                   param=text, noCtrls=True)
                ctrls.valueCtrl = wx.StaticText(
                    panel, label=text, style=wx.ALIGN_RIGHT)
                ctrls.valueCtrl._szr = wx.BoxSizer(wx.HORIZONTAL)
                ctrls.valueCtrl._szr.Add(ctrls.valueCtrl)
                panelSizer.Add(ctrls.valueCtrl._szr, (row, 1),
                               flag=wx.ALIGN_RIGHT)
                # create refresh button
                ctrls.refreshBtn = wx.Button(panel, style=wx.BU_EXACTFIT | wx.BORDER_NONE)
                ctrls.refreshBtn.SetBitmap(
                    icons.ButtonIcon("view-refresh", size=16).bitmap
                )
                ctrls.refreshBtn.Bind(wx.EVT_BUTTON, self.updateSummary)
                ctrls.valueCtrl._szr.Prepend(ctrls.refreshBtn, border=12, flag=wx.LEFT | wx.RIGHT | wx.ALIGN_TOP)

                row += 1
            else:  # normal text entry field
                ctrls = ParamCtrls(dlg=self, parent=panel, label=label,
                                   fieldName=fieldName,
                                   param=handler.params[fieldName])
                panelSizer.Add(ctrls.nameCtrl, [row, 0], border=3, flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL)
                if hasattr(ctrls.valueCtrl, "_szr"):
                    panelSizer.Add(ctrls.valueCtrl._szr, [row, 1], border=3, flag=wx.EXPAND | wx.ALL)
                else:
                    panelSizer.Add(ctrls.valueCtrl, [row, 1], border=3, flag=wx.EXPAND | wx.ALL)
                row += 1
            # Link conditions file browse button to its own special method
            if fieldName == 'conditionsFile':
                ctrls.valueCtrl.findBtn.Bind(wx.EVT_BUTTON, self.onBrowseTrialsFile)
                ctrls.setChangesCallback(self.setNeedUpdate)
            # store info about the field
            self.constantsCtrls[fieldName] = ctrls
        panelSizer.AddGrowableCol(1, 1)
        return panel

    def makeMultiStairCtrls(self):
        # a list of controls for the random/sequential versions
        panel = wx.Panel(parent=self)
        panel.app = self.app
        panelSizer = wx.GridBagSizer(0, 0)
        panel.SetSizer(panelSizer)
        row = 0
        # that can be hidden or shown
        handler = self.multiStairHandler
        # loop through the params
        keys = list(handler.params.keys())
        # add conditions stuff to the *end*
        # add conditions stuff to the *end*
        if 'conditionsFile' in keys:
            keys.remove('conditionsFile')
            keys.append('conditionsFile')
        if 'conditions' in keys:
            keys.remove('conditions')
            keys.append('conditions')
        # then step through them
        for fieldName in keys:
            # try and get alternative "label" for the parameter
            try:
                label = handler.params[fieldName].label
                if not label:  # it might exist but be empty
                    label = fieldName
            except Exception:
                label = fieldName
            # handle special cases
            if fieldName == 'endPoints':
                continue  # this was deprecated in v1.62.00
            if fieldName in self.globalCtrls:
                # these have already been made and inserted into sizer
                ctrls = self.globalCtrls[fieldName]
            elif fieldName == 'conditions':
                if 'conditions' in handler.params:
                    text, OK = self.getTrialsSummary(
                        handler.params['conditions'].val)
                else:
                    text = _translate(
                        "No parameters set (select a file above)")
                    OK = False
                # we'll create our own widgets
                ctrls = ParamCtrls(dlg=self, parent=panel, label=label,
                                   fieldName=fieldName,
                                   param=text, noCtrls=True)
                ctrls.valueCtrl = wx.StaticText(panel, label=text,
                                                style=wx.ALIGN_CENTER)
                if OK:
                    ctrls.valueCtrl.SetForegroundColour("Black")
                else:
                    ctrls.valueCtrl.SetForegroundColour("Red")
                if hasattr(ctrls.valueCtrl, "_szr"):
                    panelSizer.Add(ctrls.valueCtrl._szr, (row, 0),
                                   span=(1, 3), flag=wx.ALIGN_CENTER)
                else:
                    panelSizer.Add(ctrls.valueCtrl, (row, 0),
                                   span=(1, 3), flag=wx.ALIGN_CENTER)
                row += 1
            else:
                # normal text entry field
                ctrls = ParamCtrls(dlg=self, parent=panel, label=label,
                                   fieldName=fieldName,
                                   param=handler.params[fieldName])
                panelSizer.Add(ctrls.nameCtrl, [row, 0], border=3, flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL)
                if hasattr(ctrls.valueCtrl, "_szr"):
                    panelSizer.Add(ctrls.valueCtrl._szr, [row, 1], border=3, flag=wx.EXPAND | wx.ALL)
                else:
                    panelSizer.Add(ctrls.valueCtrl, [row, 1], border=3, flag=wx.EXPAND | wx.ALL)
                row += 1
            # Bind file button with its own special method
            if fieldName == 'conditionsFile':
                ctrls.valueCtrl.findBtn.Bind(wx.EVT_BUTTON, self.onBrowseTrialsFile)
            # store info about the field
            self.multiStairCtrls[fieldName] = ctrls
        panelSizer.AddGrowableCol(1, 1)
        return panel

    def makeStaircaseCtrls(self):
        """Setup the controls for a StairHandler
        """
        panel = wx.Panel(parent=self)
        panelSizer = wx.GridBagSizer(0, 0)
        panel.SetSizer(panelSizer)
        row = 0
        handler = self.stairHandler
        # loop through the params
        for fieldName in handler.params:
            # try and get alternative "label" for the parameter
            try:
                label = handler.params[fieldName].label
                if not label:
                    # it might exist but be empty
                    label = fieldName
            except Exception:
                label = fieldName
            # handle special cases
            if fieldName == 'endPoints':
                continue  # this was deprecated in v1.62.00
            if fieldName in self.globalCtrls:
                # these have already been made and inserted into sizer
                ctrls = self.globalCtrls[fieldName]
            else:  # normal text entry field
                ctrls = ParamCtrls(dlg=self, parent=panel, label=label,
                                   fieldName=fieldName,
                                   param=handler.params[fieldName])
                panelSizer.Add(ctrls.nameCtrl, [row, 0], border=3, flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL)
                if hasattr(ctrls.valueCtrl, "_szr"):
                    panelSizer.Add(ctrls.valueCtrl._szr, [row, 1], border=3, flag=wx.EXPAND | wx.ALL)
                else:
                    panelSizer.Add(ctrls.valueCtrl, [row, 1], border=3, flag=wx.EXPAND | wx.ALL)
                row += 1
            # store info about the field
            self.staircaseCtrls[fieldName] = ctrls
        panelSizer.AddGrowableCol(1, 1)
        return panel

    def getTrialsSummary(self, conditions):
        if type(conditions) == list and len(conditions) > 0:
            # get attr names (conditions[0].keys() inserts u'name' and u' is
            # annoying for novice)
            paramStr = "["
            for param in conditions[0]:
                # check for namespace clashes
                clashes = self.exp.namespace.getCategories(param)
                if clashes:
                    alert(4705, strFields={
                        'param': param,
                        'category': ", ".join(clashes)
                    })
                paramStr += (str(param) + ', ')
            paramStr = paramStr[:-2] + "]"  # remove final comma and add ]
            # generate summary info
            msg = _translate('%(nCondition)i conditions, with %(nParam)i '
                             'parameters\n%(paramStr)s')
            vals = {'nCondition': len(conditions),
                    'nParam': len(conditions[0]),
                    'paramStr': paramStr}
            return msg % vals, True
        else:
            if (self.conditionsFile and
                    not os.path.isfile(self.conditionsFile)):
                return _translate("No parameters set (conditionsFile not found)"), False
            # No condition file is not an error
            return _translate("No parameters set"), True

    def setCtrls(self, ctrlType):
        # choose the ctrls to show/hide
        if ctrlType == 'staircase':
            self.currentHandler = self.stairHandler
            self.stairPanel.Show()
            self.constantsPanel.Hide()
            self.multiStairPanel.Hide()
            self.currentCtrls = self.staircaseCtrls
        elif ctrlType == 'interleaved staircases':
            self.currentHandler = self.multiStairHandler
            self.stairPanel.Hide()
            self.constantsPanel.Hide()
            self.multiStairPanel.Show()
            self.currentCtrls = self.multiStairCtrls
        else:
            self.currentHandler = self.trialHandler
            self.stairPanel.Hide()
            self.constantsPanel.Show()
            self.multiStairPanel.Hide()
            self.currentCtrls = self.constantsCtrls
        self.currentType = ctrlType
        # redo layout
        self.mainSizer.Layout()
        self.Fit()
        self.Refresh()

    @property
    def type(self):
        """What type of loop is represented by this dlg"""
        if self.currentHandler.type == "MultiStairHandler":
            return "MultiStairHandler:" + self.currentHandler.params['stairType'].val
        else:
            return self.currentHandler.type

    @type.setter
    def type(self, value):
        self.setCtrls(value)

    def onTypeChanged(self, evt=None):
        newType = evt.GetString()
        if newType == self.currentType:
            return
        self.setCtrls(newType)

    def onBrowseTrialsFile(self, event):
        self.conditionsFileOrig = self.conditionsFile
        self.conditionsOrig = self.conditions
        dlg = wx.FileDialog(self, message=_translate("Open file ..."),
                            style=wx.FD_OPEN, defaultDir=str(self.expPath))
        if dlg.ShowModal() == wx.ID_OK:
            self.conditionsFile = dlg.GetPath()
            self.constantsCtrls['conditionsFile'].valueCtrl.SetValue(
                self.conditionsFile
            )
            self.updateSummary()

    def setNeedUpdate(self, evt=None):
        """
        Mark that conditions need an update, i.e. enable the refresh button
        """
        self.constantsCtrls['conditions'].refreshBtn.Enable()

    def updateSummary(self, evt=None):
        """
        Figure out what conditions we can get from the file and display them, or an error
        or message, as appropriate. Upon completion this will disable the update button as
        we are now up to date.
        """
        if "MultiStairHandler" in self.type:
            self.conditionsFile = self.multiStairCtrls['conditionsFile'].valueCtrl.GetValue()
        else:
            self.conditionsFile = self.constantsCtrls['conditionsFile'].valueCtrl.GetValue()
        # Check whether the file and path are the same as previously
        isSameFilePathAndName = self.conditionsFileAbs == self.conditionsFileOrig
        # Start off with no message and assumed valid
        msg = ""
        valid = True
        if self.conditionsFile in (None, ""):
            # If no conditions file, no message
            msg = ""
            valid = True
        elif "$" in str(self.conditionsFile):
            # If set from a variable, message but no error
            msg = _translate("Conditions file set from variable.")
            valid = True
        else:
            duplCondNames = []
            try:
                _c, _n = data.importConditions(self.conditionsFileAbs.strip(),
                                               returnFieldNames=True)
                self.conditions, self.condNamesInFile = _c, _n
                msg, valid = self.getTrialsSummary(self.conditions)
            except exceptions.ConditionsImportError as err:
                # If import conditions errors, then value is not valid
                valid = False
                errMsg = str(err)
                mo = re.search(r'".+\.[0-9]+"$', errMsg)
                if "Could not open" in errMsg:
                    msg = _translate('Could not read conditions from: %s\n') % self.conditionsFile
                    logging.error('Could not open as a conditions file: %s' % self.conditionsFileAbs)
                elif "Bad name:" in errMsg and "punctuation" in errMsg and mo:
                    # column name is something like "stim.1", which may
                    # be in conditionsFile or generated by pandas when
                    # duplicated column names are found.
                    msg = _translate(
                        'Bad name in %s: Parameters (column headers) cannot contain dots or be duplicated.'
                    ) % self.conditionsFile
                    logging.error(
                        ('Bad name in %s: Parameters (column headers) cannot contain dots or be '
                         'duplicated.') % self.conditionsFileAbs
                    )
                else:
                    msg = err.translated
                    logging.error(msg)

            # check for Builder variables
            builderVariables = []
            for condName in self.condNamesInFile:
                if condName in self.exp.namespace.builder:
                    builderVariables.append(condName)
            if builderVariables:
                msg = _translate('Builder variable(s) ({}) in file:{}').format(
                    ','.join(builderVariables), self.conditionsFile)
                logging.error(msg)
                valid = False
                msg = 'Rejected Builder variable(s) ({}) in file:{}'.format(
                    ','.join(builderVariables), self.conditionsFile)
                logging.error(msg)

            if len(self.condNamesInFile):
                for condName in self.condNamesInFile:
                    if self.exp.namespace.exists(condName):
                        duplCondNames.append(condName)
            # abbrev long strings to better fit in the dialog:
            duplCondNamesStr = ' '.join(duplCondNames)[:42]
            if len(duplCondNamesStr) == 42:
                duplCondNamesStr = duplCondNamesStr[:39] + '...'
            if len(duplCondNames):
                if isSameFilePathAndName:
                    logging.info(
                        'Assuming reloading file: same filename and '
                        'duplicate condition names in file: %s' % self.conditionsFile)
                else:
                    self.currentCtrls['conditionsFile'].setValue(self.conditionsFile or "")
                    logging.warning(
                        'Warning: Condition names conflict with existing'
                           ':\n[' + duplCondNamesStr + ']\nProceed'
                           ' anyway? (= safe if these are in old file)'
                    )
                    valid = False
                    msg = _translate(
                        'Duplicate condition names, different '
                        'conditions file: %s'
                    ) % duplCondNamesStr
            # stash condition names but don't add to namespace yet, user can
            # still cancel
            # add after self.show() in __init__:
            self.duplCondNames = duplCondNames

        # Update ctrl value in case it's been abbreviated by conditionsFile setter
        self.currentCtrls['conditionsFile'].setValue(self.conditionsFile or "")
        # Do actual value setting
        self.currentCtrls['conditions'].setValue(msg)
        if valid:
            self.currentCtrls['conditions'].valueCtrl.SetForegroundColour("Black")
        else:
            self.currentCtrls['conditions'].valueCtrl.SetForegroundColour("Red")
        self.Layout()
        self.Fit()
        # Disable update button now that we're up to date
        self.constantsCtrls['conditions'].refreshBtn.Disable()

    def getParams(self):
        """Retrieves data and re-inserts it into the handler and returns
        those handler params
        """
        # get data from input fields
        for fieldName in self.currentHandler.params:
            if fieldName == 'endPoints':
                continue  # this was deprecated in v1.62.00
            param = self.currentHandler.params[fieldName]
            if fieldName in ['conditionsFile']:
                param.val = self.conditionsFile or ""
                # not the value from ctrl - that was abbreviated
                # see onOK() for partial handling = check for '...'
            else:  # most other fields
                # the various dlg ctrls for this param
                ctrls = self.currentCtrls[fieldName]
                param.val = ctrls.getValue()
                # from _baseParamsDlg (handles diff control types)
                if ctrls.typeCtrl:
                    param.valType = ctrls.getType()
                if ctrls.updateCtrl:
                    param.updates = ctrls.getUpdates()
        return self.currentHandler.params

    def onOK(self, event=None):
        # intercept OK in case user deletes or edits the filename manually
        if 'conditionsFile' in self.currentCtrls:
            self.updateSummary()
        event.Skip()  # do the OK button press


class DlgComponentProperties(_BaseParamsDlg):

    def __init__(self, frame, element, experiment,
                 suppressTitles=True, size=wx.DefaultSize,
                 style=wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT,
                 editing=False,
                 timeout=None, testing=False, type=None,
                 openToPage=None):
        style = style | wx.RESIZE_BORDER
        self.type = type or element.type
        _BaseParamsDlg.__init__(self, frame=frame, element=element, experiment=experiment,
                                size=size,
                                style=style, editing=editing,
                                timeout=timeout, openToPage=openToPage)
        self.frame = frame
        self.app = frame.app
        self.dpi = self.app.dpi

        # for all components
        self.show(testing)
        if not testing:
            if self.OK:
                self.params = self.getParams()  # get new vals from dlg
            self.Destroy()


class DlgExperimentProperties(_BaseParamsDlg):

    def __init__(self, frame, element, experiment,
                 suppressTitles=False, size=wx.DefaultSize,
                 style=wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT,
                 timeout=None):
        style = style | wx.RESIZE_BORDER
        _BaseParamsDlg.__init__(self, frame=frame, element=element, experiment=experiment,
                                size=size,
                                style=style,
                                timeout=timeout)
        self.frame = frame
        self.app = frame.app
        self.dpi = self.app.dpi

        # for input devices:
        # do this just to set the initial values to be
        self.paramCtrls['Full-screen window'].setChangesCallback(self.onFullScrChange)
        self.onFullScrChange(event=None)
        self.Bind(wx.EVT_CHECKBOX, self.onFullScrChange,
                  self.paramCtrls['Full-screen window'].valueCtrl)

        # Add button to show screen numbers
        scrNumCtrl = self.paramCtrls['Screen'].valueCtrl
        self.screenNsBtn = wx.Button(scrNumCtrl.GetParent(), label=_translate("Show screen numbers"))
        scrNumCtrl._szr.Add(self.screenNsBtn, border=5, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT)
        scrNumCtrl.Layout()
        self.screenNsBtn.Bind(wx.EVT_BUTTON, self.showScreenNumbers)

        if timeout is not None:
            wx.FutureCall(timeout, self.Destroy)

        # for all components
        self.show()
        if self.OK:
            self.params = self.getParams()  # get new vals from dlg

        self.Destroy()

    def onFullScrChange(self, event=None):
        """full-screen has been checked / unchecked.
        Show or hide the window size field accordingly
        """
        if self.paramCtrls['Full-screen window'].valueCtrl.GetValue():
            # get screen size for requested display
            numDisplays = wx.Display.GetCount()
            try:
                screenValue = int(
                    self.paramCtrls['Screen'].valueCtrl.GetValue())
            except ValueError:
                # param control currently contains no integer value
                screenValue = 1
            if screenValue < 1 or screenValue > numDisplays:
                logging.error("User requested non-existent screen")
                screenN = 0
            else:
                screenN = screenValue - 1
            size = list(wx.Display(screenN).GetGeometry()[2:])
            # set vals and disable changes
            field = 'Window size (pixels)'
            self.paramCtrls[field].valueCtrl.SetValue(str(size))
            self.paramCtrls[field].param.val = size
            self.paramCtrls[field].valueCtrl.Disable()
            self.paramCtrls[field].nameCtrl.Disable()
            # enable show/hide mouse
            self.paramCtrls['Show mouse'].valueCtrl.Enable()
            self.paramCtrls['Show mouse'].nameCtrl.Enable()
        else:
            self.paramCtrls['Window size (pixels)'].valueCtrl.Enable()
            self.paramCtrls['Window size (pixels)'].nameCtrl.Enable()
            # set show mouse to visible and disable control
            self.paramCtrls['Show mouse'].valueCtrl.Disable()
            self.paramCtrls['Show mouse'].nameCtrl.Disable()
        self.mainSizer.Layout()
        self.Fit()
        self.Refresh()


class DlgNewRoutine(wx.Dialog):

    def __init__(self, parent, pos=wx.DefaultPosition, size=(512, -1),
                 style=wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT):
        self.parent = parent  # parent is probably the RoutinesNotebook (not the BuilderFrame)
        self.app = parent.app
        if hasattr(parent, 'frame'):
            self.frame = parent.frame
        else:
            self.frame = parent
        # Initialise dlg
        wx.Dialog.__init__(self, parent, title=_translate("New Routine"), name=_translate("New Routine"),
                           size=size, pos=pos, style=style)
        # Setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.FlexGridSizer(cols=2, vgap=0, hgap=6)
        self.border.Add(self.sizer, border=12, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP)
        # Get templates
        self.templates = self.frame.routineTemplates
        self.templatesByID = {}
        self.selectedTemplate = self.templates['Basic']['blank']  # until we know otherwise
        # New name ctrl
        self.nameLbl = wx.StaticText(self, -1, _translate("New Routine name:"))
        self.sizer.Add(self.nameLbl, border=6, flag=wx.ALL | wx.ALIGN_RIGHT)
        self.nameCtrl = wx.TextCtrl(self, -1, "", size=(200, -1))
        self.nameCtrl.SetToolTip(_translate(
            "What is the name for the new Routine? (e.g. instr, trial, feedback)"
        ))
        self.sizer.Add(self.nameCtrl, border=6, flag=wx.ALL | wx.ALIGN_TOP | wx.EXPAND)
        # Template picker
        self.templateLbl = wx.StaticText(self, -1, _translate("Routine Template:"))
        self.sizer.Add(self.templateLbl, border=6, flag=wx.ALL | wx.ALIGN_RIGHT)
        self.templateCtrl = wx.Button(self, -1, "Basic:blank", size=(200, -1))
        self.templateCtrl.SetToolTip(_translate(
            "Select a template to base your new Routine on"
        ))
        self.templateCtrl.Bind(wx.EVT_BUTTON, self.showTemplatesContextMenu)
        self.sizer.Add(self.templateCtrl, border=6, flag=wx.ALL | wx.ALIGN_TOP | wx.EXPAND)
        # Buttons
        self.btnSizer = wx.StdDialogButtonSizer()
        self.CANCEL = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.btnSizer.AddButton(self.CANCEL)
        self.OK = wx.Button(self, wx.ID_OK, "OK")
        self.btnSizer.AddButton(self.OK)
        self.btnSizer.Realize()
        self.border.Add(self.btnSizer, border=12, flag=wx.ALL | wx.ALIGN_RIGHT)

        self.Fit()
        self.Center()

    def showTemplatesContextMenu(self, evt):
        self.templateMenu = wx.Menu()
        self.templateMenu.Bind(wx.EVT_MENU, self.onSelectTemplate)
        self.templatesByID = {}
        for categName, categDict in self.templates.items():
            submenu = wx.Menu()
            self.templateMenu.Append(wx.ID_ANY, categName, submenu)
            for templateName, routine in categDict.items():
                id = wx.NewIdRef()
                self.templatesByID[id] = {
                    'routine': routine,
                    'name': templateName,
                    'categ': categName,
                }
                item = submenu.Append(id, templateName)

        btnPos = self.templateCtrl.GetRect()
        menuPos = (btnPos[0], btnPos[1] + btnPos[3])
        self.PopupMenu(self.templateMenu, menuPos)

    def onSelectTemplate(self, evt):

        id = evt.Id
        categ = self.templatesByID[id]['categ']
        templateName = self.templatesByID[id]['name']
        self.templateCtrl.SetLabelText(f"{categ}: {templateName}")
        self.selectedTemplate = self.templates[categ][templateName]
        self.Layout()  # update the size of the button
        self.Fit()
        # self.templateMenu.Destroy()  # destroy to avoid mem leak
