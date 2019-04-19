#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Dialog classes for the Builder, including ParamCtrls
"""

from __future__ import absolute_import, division, print_function

from builtins import map
from builtins import str
from builtins import object
import os
import copy
import numpy
import re
import wx

import psychopy.experiment.utils

try:
    from wx.lib.agw import flatnotebook
except ImportError:  # was here wx<4.0:
    from wx.lib import flatnotebook

from ... import dialogs
from .. import experiment
from .. validators import NameValidator, CodeSnippetValidator
from .dlgsConditions import DlgConditions
from .dlgsCode import DlgCodeComponentProperties, CodeBox
from psychopy import data, logging
from psychopy.localization import _translate
from psychopy.tools import versionchooser as vc


white = wx.Colour(255, 255, 255, 255)
codeSyntaxOkay = wx.Colour(220, 250, 220, 255)  # light green

from ..localizedStrings import _localizedDialogs as _localized


class ParamCtrls(object):

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
        _nonCode = ('name', 'Experiment info')
        label = _translate(label)
        if param.valType == 'code' and fieldName not in _nonCode:
            label += ' $'
        self.nameCtrl = wx.StaticText(parent, -1, label, size=wx.DefaultSize,
                                      style=wx.ALIGN_RIGHT)

        if fieldName == 'Use version':
            # _localVersionsCache is the default (faster) when creating
            # settings. If remote info has become available in the meantime,
            # now populate with that as well
            if vc._remoteVersionsCache:
                options = vc._versionFilter(vc.versionOptions(local=False), wx.__version__)
                versions = vc._versionFilter(vc.availableVersions(local=False), wx.__version__)
                param.allowedVals = (options + [''] + versions)
        if fieldName in ['text', 'customize_everything', 'customize']:
            # for text input we need a bigger (multiline) box
            if fieldName == 'customize_everything':
                sx, sy = 300, 400
            elif fieldName == 'customize':
                sx, sy = 300, 200
            else:
                sx, sy = 100, 200
            # set viewer small, then it SHOULD increase with wx.aui control
            self.valueCtrl = CodeBox(parent, -1, pos=wx.DefaultPosition,
                                     size=wx.Size(sx, sy), style=0,
                                     prefs=appPrefs)
            if len(param.val):
                self.valueCtrl.AddText(str(param.val))
            if fieldName == 'text':
                self.valueCtrl.SetFocus()
        elif fieldName == 'Experiment info':
            # for expInfo convert from a string to the list-of-dicts
            val = self.expInfoToListWidget(param.val)
            self.valueCtrl = dialogs.ListWidget(
                parent, val, order=['Field', 'Default'])
        elif param.valType == 'extendedCode':
            # set viewer small, then it will increase with wx.aui control
            self.valueCtrl = CodeBox(parent, -1, pos=wx.DefaultPosition,
                                     size=wx.Size(100, 100), style=0,
                                     prefs=appPrefs)
            if len(param.val):
                self.valueCtrl.AddText(str(param.val))
            # code input fields: one day change these to wx.stc fields?
            # self.valueCtrl = wx.TextCtrl(parent,-1,unicode(param.val),
            #    style=wx.TE_MULTILINE,
            #    size=wx.Size(self.valueWidth*2,160))
        elif param.valType == 'fixedList':
            self.valueCtrl = wx.CheckListBox(parent, -1, pos=wx.DefaultPosition,
                                             size=wx.Size(100, 200),
                                             choices=param.allowedVals)
            self.valueCtrl.SetCheckedStrings(param.val)
        elif param.valType == 'bool':
            # only True or False - use a checkbox
            self.valueCtrl = wx.CheckBox(parent,
                                         name=fieldName,
                                         size=wx.Size(self.valueWidth, -1))
            self.valueCtrl.SetValue(param.val)
        elif len(param.allowedVals) > 1:
            # there are limited options - use a Choice control
            # use localized text or fall through to non-localized,
            # for future-proofing, parallel-port addresses, etc:
            choiceLabels = []
            for val in param.allowedVals:
                try:
                    choiceLabels.append(_localized[val])
                except KeyError:
                    choiceLabels.append(val)
            self.valueCtrl = wx.Choice(parent, choices=choiceLabels,
                                       name=fieldName,
                                       size=wx.Size(self.valueWidth, -1))
            # stash original non-localized choices:
            self.valueCtrl._choices = copy.copy(param.allowedVals)
            # set display to the localized version of the currently selected
            # value:
            try:
                index = param.allowedVals.index(param.val)
            except Exception:
                msg = ("%r was given as parameter %r but it isn't "
                       "in the list of allowed values %s. "
                       "Reverting to use %r for this Component")
                vals = (param.val, fieldName,
                        param.allowedVals,
                        param.allowedVals[0])
                logging.warn(msg % vals)
                logging.flush()
                index = 0
            self.valueCtrl.SetSelection(index)
        else:
            # create the full set of ctrls
            val = str(param.val)
            self.valueCtrl = wx.TextCtrl(parent, -1, val, name=fieldName,
                                         size=wx.Size(self.valueWidth, -1))
            # set focus for these fields; seems to get reset elsewhere (?)
            focusFields = ('allowedKeys', 'image', 'movie', 'sound',
                           'scaleDescription', 'Begin Routine')
            if fieldName in focusFields:
                self.valueCtrl.SetFocus()

        try:
            self.valueCtrl.SetToolTip(wx.ToolTip(_translate(param.hint)))
        except AttributeError as e:
            self.valueCtrl.SetToolTipString(_translate(param.hint))

        if len(param.allowedVals) == 1 or param.readOnly:
            self.valueCtrl.Disable()  # visible but can't be changed

        # add a Validator to the valueCtrl
        if fieldName == "name":
            self.valueCtrl.SetValidator(NameValidator())
        elif isinstance(self.valueCtrl, (wx.TextCtrl, CodeBox)):
            # only want anything that is valType code, or can be with $
            self.valueCtrl.SetValidator(CodeSnippetValidator(fieldName))

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
        if param.allowedUpdates is not None and len(param.allowedUpdates):
            # updates = display-only version of allowed updates
            updateLabels = [_localized[upd] for upd in param.allowedUpdates]
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
            # get index of the currently set update value, set display:
            index = allowedUpdates.index(param.updates)
            # set by integer index, not string value
            self.updateCtrl.SetSelection(index)

        if param.allowedUpdates != None and len(param.allowedUpdates) == 1:
            self.updateCtrl.Disable()  # visible but can't be changed
        # create browse control
        if browse:
            # we don't need a label for this
            self.browseCtrl = wx.Button(parent, -1, _translate("Browse..."))

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
        elif hasattr(ctrl, 'GetText'):
            return ctrl.GetText()
        elif hasattr(ctrl, 'GetValue'):  # e.g. TextCtrl
            val = ctrl.GetValue()
            if isinstance(self.valueCtrl, dialogs.ListWidget):
                val = self.expInfoFromListWidget(val)
            return val
        elif hasattr(ctrl, 'GetCheckedStrings'):
            return ctrl.GetCheckedStrings()
        elif hasattr(ctrl, 'GetSelection'):  # for wx.Choice
            # _choices is defined during __init__ for all wx.Choice() ctrls
            # NOTE: add untranslated value to _choices if
            # _choices[ctrl.GetSelection()] fails.
            return ctrl._choices[ctrl.GetSelection()]
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
        self.valueCtrl.Show(newVal)
        self.nameCtrl.Show(newVal)
        if self.updateCtrl:
            self.updateCtrl.Show(newVal)
        if self.typeCtrl:
            self.typeCtrl.Show(newVal)

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
        if isinstance(self.valueCtrl, CodeBox):
            self.valueCtrl.Bind(wx.stc.EVT_STC_CHANGE, callbackFunction)
        elif isinstance(self.valueCtrl, wx.ComboBox):
            self.valueCtrl.Bind(wx.EVT_COMBOBOX, callbackFunction)
        elif isinstance(self.valueCtrl, wx.Choice):
            self.valueCtrl.Bind(wx.EVT_CHOICE, callbackFunction)
        elif isinstance(self.valueCtrl, wx.CheckBox):
            self.valueCtrl.Bind(wx.EVT_CHECKBOX, callbackFunction)
        else:
            print("setChangesCallback doesn't know how to handle ctrl {}"
                  .format(type(self.valueCtrl)))

class _BaseParamsDlg(wx.Dialog):
    _style = wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT | wx.TAB_TRAVERSAL

    def __init__(self, frame, title, params, order,
                 helpUrl=None, suppressTitles=True,
                 showAdvanced=False,
                 size=wx.DefaultSize,
                 style=_style, editing=False,
                 depends=[],
                 timeout=None):

        # translate title
        if ' Properties' in title:  # Components and Loops
            localizedTitle = title.replace(' Properties',
                                           _translate(' Properties'))
        else:
            localizedTitle = _translate(title)

        # use translated title for display
        wx.Dialog.__init__(self, parent=None, id=-1, title=localizedTitle,
                           size=size, style=style)
        self.frame = frame
        self.app = frame.app
        self.dpi = self.app.dpi
        self.helpUrl = helpUrl
        self.params = params  # dict
        self.title = title
        self.timeout = timeout
        self.warningsDict = {}  # to store warnings for all fields
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
        self.order = order
        self.depends = depends
        self.data = []
        self.nameOKlabel = None
        # max( len(str(self.params[x])) for x in keys )
        self.maxFieldLength = 10
        self.timeParams = ['startType', 'startVal', 'stopType', 'stopVal']
        self.codeFieldNameFromID = {}
        self.codeIDFromFieldName = {}
        # a list of all panels in the ctrl to be traversed by validator
        self.panels = []

        # for switching font to signal code:
        self.codeFaceName = 'Courier New'  # other monospace if not available
        # need font size for STCs:
        if wx.Platform == '__WXMSW__':
            self.faceSize = 10
        elif wx.Platform == '__WXMAC__':
            self.faceSize = 14
        else:
            self.faceSize = 12

        # organise the param names by category
        categs = {'Basic': []}
        for thisName in sorted(self.params):
            thisParam = self.params[thisName]
            if type(thisParam) == list:
                # not really a param as such
                continue
            thisCateg = thisParam.categ
            if thisCateg not in categs:
                categs[thisCateg] = [thisName]
            else:
                categs[thisCateg].append(thisName)
        if not categs['Basic']:
            # there were no entries of this categ so delete it
            del categs['Basic']

        # create main sizer
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        agwStyle = flatnotebook.FNB_NO_X_BUTTON
        if hasattr(flatnotebook, "FNB_NAV_BUTTONS_WHEN_NEEDED"):
            # not available in wxPython 2.8
            agwStyle |= flatnotebook.FNB_NAV_BUTTONS_WHEN_NEEDED
        if hasattr(flatnotebook, "FNB_NO_TAB_FOCUS"):
            # not available in wxPython 2.8.10
            agwStyle |= flatnotebook.FNB_NO_TAB_FOCUS
        self.ctrls = flatnotebook.FlatNotebook(self, style=agwStyle)
        self.mainSizer.Add(self.ctrls,  # ctrls is the notebook of params
                           proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        categNames = sorted(categs)
        if 'Basic' in categNames:
            # move it to be the first category we see
            categNames.insert(0, categNames.pop(categNames.index('Basic')))
        # move into _localized after merge branches:
        categLabel = {'Basic': _translate('Basic'),
                      'Data': _translate('Data'),
                      'Screen': _translate('Screen'),
                      'Dots': _translate('Dots'),
                      'Grating': _translate('Grating'),
                      'Advanced': _translate('Advanced'),
                      'Custom': _translate('Custom'),
                      'Carrier': _translate('Carrier'),
                      'Envelope': _translate('Envelope'),
                      'Appearance': _translate('Appearance'),
                      'Save': _translate('Save'),
                      'Online':_translate('Online')}
        for categName in categNames:
            theseParams = categs[categName]
            page = wx.Panel(self.ctrls, -1)
            ctrls = self.addCategoryOfParams(theseParams, parent=page)
            if categName in categLabel:
                cat = categLabel[categName]
            else:
                cat = categName
            self.ctrls.AddPage(page, cat)
            # so the validator finds this set of controls
            self.panels.append(page)
            if 'customize_everything' in self.params:
                if self.params['customize_everything'].val.strip():
                    # set focus to the custom panel
                    page.SetFocus()
                    self.ctrls.SetSelection(self.ctrls.GetPageCount() - 1)
            else:
                self.ctrls.GetPage(0).SetFocus()
                self.ctrls.SetSelection(0)
                if hasattr(self, 'paramCtrls'):
                    if 'name' in self.paramCtrls:
                        self.paramCtrls['name'].valueCtrl.SetFocus()
                    if 'expName' in self.paramCtrls:
                        # ExperimentSettings has expName instead
                        self.paramCtrls['expName'].valueCtrl.SetFocus()
            page.SetSizerAndFit(ctrls)
            page.SetAutoLayout(True)
        self.SetSizerAndFit(self.mainSizer)
        #set up callbacks for any dependent params to update others
        for thisDepend in self.depends:
            paramName = thisDepend['dependsOn']
            paramCtrl = self.paramCtrls[paramName]  # hint : ParamCtrl
            paramCtrl.setChangesCallback(self.checkDepends)
        self.checkDepends()

    def checkDepends(self, event=None):
        """Checks the relationships between params that depend on each other

        Dependencies are a list of dicts like this (as in BaseComponent):
        {"dependsOn": "shape",
         "condition": "=='n vertices",
         "param": "n vertices",
         "true": "Enable",  # what to do with param if condition is True
         "false": "Disable",  # permitted: hide, show, enable, disable
        }"""
        for thisDep in self.depends:
            dependentCtrls = self.paramCtrls[thisDep['param']]
            dependencyCtrls = self.paramCtrls[thisDep['dependsOn']]
            condString = "dependencyCtrls.getValue() {}".format(thisDep['condition'])
            if eval(condString):
                action = thisDep['true']
            else:
                action = thisDep['false']
            if action == "hide":
                dependentCtrls.setVisible(False)
            elif action == "show":
                dependentCtrls.setVisible(True)
            else:
                # if action is "enable" then do ctrl.Enable() etc
                for ctrlName in ['valueCtrl', 'nameCtrl', 'updatesCtrl']:
                    # disable/enable all parts of the control
                    if hasattr(dependentCtrls, ctrlName):
                        evalStr = ("dependentCtrls.{}.{}()"
                                   .format(ctrlName, action.title()))
                        eval(evalStr)
            self.mainSizer.Layout()
            self.Fit()
            self.Refresh()

    def addCategoryOfParams(self, paramNames, parent):
        """Add all the params for a single category
        (after its tab has been created)
        """
        # create the sizers to fit the params and set row to zero
        sizer = wx.GridBagSizer(vgap=2, hgap=2)
        currRow = 0
        # does the dlg need an 'updates' row (do any params use it?)
        self.useUpdates = False

        # create a header row of titles
        if not self.suppressTitles:
            size = wx.Size(1.5 * self.dpi, -1)
            sizer.Add(wx.StaticText(parent, -1, 'Parameter', size=size,
                                    style=wx.ALIGN_CENTER), (currRow, 0))
            sizer.Add(wx.StaticText(parent, -1, 'Value', size=size,
                                    style=wx.ALIGN_CENTER), (currRow, 1))
            # self.sizer.Add(wx.StaticText(self,-1,'Value Type',size=size,
            #   style=wx.ALIGN_CENTER),(currRow,3))
            sizer.Add(wx.StaticText(parent, -1, 'Updates', size=size,
                                    style=wx.ALIGN_CENTER), (currRow, 2))
            currRow += 1
            sizer.Add(wx.StaticLine(parent, size=wx.Size(100, 20)),
                      (currRow, 0), (1, 2), wx.ALIGN_CENTER | wx.EXPAND)
        currRow += 1

        # get all params and sort
        remaining = copy.copy(paramNames)

        # start with the name (always)
        if 'name' in remaining:
            self.addParam('name', parent, sizer, currRow)
            currRow += 1
            remaining.remove('name')
            if 'name' in self.order:
                self.order.remove('name')
            currRow += 1
        # add start/stop info
        if 'startType' in remaining:
            remaining, currRow = self.addStartStopCtrls(remaining,
                                                        parent, sizer,
                                                        currRow)
        currRow += 1
        # loop through the prescribed order (the most important?)
        for fieldName in self.order:
            if fieldName not in paramNames:
                continue  # skip advanced params
            self.addParam(fieldName, parent, sizer, currRow,
                          valType=self.params[fieldName].valType)
            currRow += 1
            remaining.remove(fieldName)
        # add any params that weren't specified in the order
        for fieldName in remaining:
            self.addParam(fieldName, parent, sizer, currRow,
                          valType=self.params[fieldName].valType)
            currRow += 1
        sizer.AddGrowableCol(1)
        return sizer

    def addStartStopCtrls(self, remaining, parent, sizer, currRow):
        """Add controls for startType, startVal, stopType, stopVal
        remaining refers to
        """
        # Start point
        startTypeParam = self.params['startType']
        startValParam = self.params['startVal']
        # create label
        label = wx.StaticText(parent, -1, _translate('Start'),
                              style=wx.ALIGN_CENTER)
        labelEstim = wx.StaticText(parent, -1,
                                   _translate('Expected start (s)'),
                                   style=wx.ALIGN_CENTER)
        labelEstim.SetForegroundColour('gray')
        # the method to be used to interpret this start/stop
        _choices = list(map(_translate, startTypeParam.allowedVals))
        self.startTypeCtrl = wx.Choice(parent, choices=_choices)
        self.startTypeCtrl.SetStringSelection(_translate(startTypeParam.val))
        msg = self.params['startType'].hint
        self.startTypeCtrl.SetToolTip(wx.ToolTip(_translate(msg)))
        # the value to be used as the start/stop
        _start = str(startValParam.val)
        self.startValCtrl = wx.TextCtrl(parent, -1, _start)
        msg = self.params['startVal'].hint
        self.startValCtrl.SetToolTip(wx.ToolTip(_translate(msg)))
        # the value to estimate start/stop if not numeric
        _est = str(self.params['startEstim'].val)
        self.startEstimCtrl = wx.TextCtrl(parent, -1, _est)
        msg = self.params['startEstim'].hint
        self.startEstimCtrl.SetToolTip(wx.ToolTip(_translate(msg)))
        # add the controls to a new line
        startSizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        startSizer.Add(self.startTypeCtrl)
        startSizer.Add(self.startValCtrl, 1, flag=wx.EXPAND)
        startEstimSizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        startEstimSizer.Add(labelEstim,
                            flag=wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT)
        startEstimSizer.Add(self.startEstimCtrl, flag=wx.ALIGN_BOTTOM)
        startAllCrtlSizer = wx.BoxSizer(orient=wx.VERTICAL)
        startAllCrtlSizer.Add(startSizer, flag=wx.EXPAND)
        startAllCrtlSizer.Add(startEstimSizer, flag=wx.ALIGN_RIGHT)
        sizer.Add(label, (currRow, 0), (1, 1), wx.ALIGN_RIGHT)
        # add our new row
        sizer.Add(startAllCrtlSizer, (currRow, 1), (1, 1), flag=wx.EXPAND)
        currRow += 1
        remaining.remove('startType')
        remaining.remove('startVal')
        remaining.remove('startEstim')

        # Stop point
        stopTypeParam = self.params['stopType']
        stopValParam = self.params['stopVal']
        # create label
        label = wx.StaticText(parent, -1, _translate('Stop'),
                              style=wx.ALIGN_CENTER)
        labelEstim = wx.StaticText(parent, -1,
                                   _translate('Expected duration (s)'),
                                   style=wx.ALIGN_CENTER)
        labelEstim.SetForegroundColour('gray')
        # the method to be used to interpret this start/stop
        _choices = list(map(_translate, stopTypeParam.allowedVals))
        self.stopTypeCtrl = wx.Choice(parent, choices=_choices)
        self.stopTypeCtrl.SetStringSelection(_translate(stopTypeParam.val))
        msg = self.params['stopType'].hint
        self.stopTypeCtrl.SetToolTip(wx.ToolTip(_translate(msg)))
        # the value to be used as the start/stop
        self.stopValCtrl = wx.TextCtrl(parent, -1, str(stopValParam.val))
        msg = self.params['stopVal'].hint
        self.stopValCtrl.SetToolTip(wx.ToolTip(_translate(msg)))
        # the value to estimate start/stop if not numeric
        _est = str(self.params['durationEstim'].val)
        self.durationEstimCtrl = wx.TextCtrl(parent, -1, _est)
        msg = self.params['durationEstim'].hint
        self.durationEstimCtrl.SetToolTip(wx.ToolTip(_translate(msg)))
        # add the controls to a new line
        stopSizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        stopSizer.Add(self.stopTypeCtrl)
        stopSizer.Add(self.stopValCtrl, 1, flag=wx.EXPAND)
        stopEstimSizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        stopEstimSizer.Add(labelEstim, flag=wx.ALIGN_CENTRE_VERTICAL)
        stopEstimSizer.Add(self.durationEstimCtrl,
                           flag=wx.ALIGN_CENTRE_VERTICAL)
        stopAllCrtlSizer = wx.BoxSizer(orient=wx.VERTICAL)
        stopAllCrtlSizer.Add(stopSizer, flag=wx.EXPAND)
        stopAllCrtlSizer.Add(stopEstimSizer,
                             flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTRE_VERTICAL)
        sizer.Add(label, (currRow, 0), (1, 1), wx.ALIGN_RIGHT)
        # add our new row
        sizer.Add(stopAllCrtlSizer, (currRow, 1), (1, 1), flag=wx.EXPAND)
        currRow += 1
        remaining.remove('stopType')
        remaining.remove('stopVal')
        remaining.remove('durationEstim')

        # use monospace font to signal code:
        self.checkCodeWanted(self.startValCtrl)
        self.startValCtrl.Bind(wx.EVT_KEY_UP, self.checkCodeWanted)
        self.startValCtrl.SetValidator(CodeSnippetValidator('startVal'))
        self.startValCtrl.Bind(wx.EVT_KEY_UP, self.doValidate)
        self.checkCodeWanted(self.stopValCtrl)
        self.stopValCtrl.Bind(wx.EVT_KEY_UP, self.checkCodeWanted)
        self.stopValCtrl.SetValidator(CodeSnippetValidator('stopVal'))
        self.stopValCtrl.Bind(wx.EVT_KEY_UP, self.doValidate)

        return remaining, currRow

    def addParam(self, fieldName, parent, sizer, currRow, advanced=False,
                 valType=None):
        """Add a parameter to the basic sizer
        """
        param = self.params[fieldName]
        if param.label not in [None, '']:
            label = param.label
        else:
            label = fieldName
        ctrls = ParamCtrls(dlg=self, parent=parent, label=label,
                           fieldName=fieldName, param=param,
                           advanced=advanced, appPrefs=self.app.prefs)
        self.paramCtrls[fieldName] = ctrls
        if fieldName == 'name':
            ctrls.valueCtrl.Bind(wx.EVT_KEY_UP, self.doValidate)
            ctrls.valueCtrl.SetFocus()
        elif isinstance(ctrls.valueCtrl, (wx.TextCtrl, CodeBox)):
            ctrls.valueCtrl.Bind(wx.EVT_KEY_UP, self.doValidate)

        # add the controls to the sizer
        _flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTRE_VERTICAL | wx.LEFT | wx.RIGHT
        sizer.Add(ctrls.nameCtrl, (currRow, 0), border=5, flag=_flag)
        if ctrls.updateCtrl:
            sizer.Add(ctrls.updateCtrl, (currRow, 2), flag=_flag)
        if ctrls.typeCtrl:
            sizer.Add(ctrls.typeCtrl, (currRow, 3), flag=_flag)
        # different flag for the value control (expand)
        _flag = wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL | wx.ALL
        sizer.Add(ctrls.valueCtrl, (currRow, 1), border=5, flag=_flag)

        # use monospace font to signal code:
        if fieldName != 'name' and hasattr(ctrls.valueCtrl, 'GetFont'):
            if self.params[fieldName].valType == 'code':
                ctrls.valueCtrl.SetFont(self.app._codeFont)
            elif self.params[fieldName].valType == 'str':
                ctrls.valueCtrl.Bind(wx.EVT_KEY_UP, self.checkCodeWanted)
                try:
                    self.checkCodeWanted(ctrls.valueCtrl)
                except Exception:
                    pass

        if fieldName in ['text']:
            sizer.AddGrowableRow(currRow)  # doesn't seem to work though
            # self.Bind(EVT_ETC_LAYOUT_NEEDED, self.onNewTextSize,
            #    ctrls.valueCtrl)
            ctrls.valueCtrl.Bind(wx.EVT_KEY_UP, self.doValidate)
        elif fieldName in ('color', 'fillColor', 'lineColor'):
            ctrls.valueCtrl.Bind(wx.EVT_RIGHT_DOWN, self.launchColorPicker)
        elif valType == 'extendedCode':
            sizer.AddGrowableRow(currRow)  # doesn't seem to work though
            ctrls.valueCtrl.Bind(wx.EVT_KEY_DOWN, self.onTextEventCode)
        elif fieldName == 'Monitor':
            ctrls.valueCtrl.Bind(wx.EVT_RIGHT_DOWN, self.openMonitorCenter)


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
        rgb = self.app.colorPicker(None)  # str, remapped to -1..+1
        # apply to color ctrl
        ctrlName = event.GetEventObject().GetName()
        thisParam = self.paramCtrls[ctrlName]
        thisParam.valueCtrl.SetValue('$' + rgb)  # $ flag as code
        # make sure we set colorspace to rgb
        colorSpace = self.paramCtrls[ctrlName + 'Space']
        colorSpace.valueCtrl.SetStringSelection('rgb')

    def onNewTextSize(self, event):
        self.Fit()  # for ExpandoTextCtrl this is needed

    def show(self):
        """Adds an OK and cancel button, shows dialogue.

        This method returns wx.ID_OK (as from ShowModal), but also
        sets self.OK to be True or False
        """
        # add a label to check name
        if 'name' in self.params:
            # if len(self.params['name'].val):
            #    nameInfo=''
            # else:
            #    nameInfo='Need a name'
            nameInfo = ''
            self.nameOKlabel = wx.StaticText(self, -1, nameInfo,
                                             style=wx.ALIGN_CENTRE)
            self.nameOKlabel.SetForegroundColour(wx.RED)
            self.mainSizer.Add(self.nameOKlabel, 0, flag=wx.ALIGN_CENTRE|wx.ALL, border=3)
        # add buttons for OK and Cancel
        buttons = wx.StdDialogButtonSizer()
        # help button if we know the url
        if self.helpUrl != None:
            helpBtn = wx.Button(self, wx.ID_HELP, _translate(" Help "))
            _tip = _translate("Go to online help about this component")
            helpBtn.SetToolTip(wx.ToolTip(_tip))
            helpBtn.Bind(wx.EVT_BUTTON, self.onHelp)
            buttons.Add(helpBtn, 0, flag=wx.ALIGN_LEFT | wx.ALL, border=3)
            buttons.AddSpacer(12)
        self.OKbtn = wx.Button(self, wx.ID_OK, _translate(" OK "))
        # intercept OK button if a loop dialog, in case file name was edited:
        if type(self) == DlgLoopProperties:
            self.OKbtn.Bind(wx.EVT_BUTTON, self.onOK)
        self.OKbtn.SetDefault()

        self.doValidate()  # disables OKbtn if bad name, syntax error, etc
        buttons.Add(self.OKbtn, 0, wx.ALL, border=3)
        CANCEL = wx.Button(self, wx.ID_CANCEL, _translate(" Cancel "))
        buttons.Add(CANCEL, 0, wx.ALL, border=3)
        buttons.Realize()
        # add to sizer
        self.mainSizer.Add(buttons, flag=wx.ALIGN_RIGHT | wx.ALL, border=2)
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
        valid = super(_BaseParamsDlg, self).Validate(*args, **kwargs)
        # also validate each page in the ctrls notebook
        for thisPanel in self.panels:
            stillValid = thisPanel.Validate()
            valid = valid and stillValid
        if valid:
            self.OKbtn.Enable()
        else:
            self.OKbtn.Disable()
        return valid

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

        # set display font based on presence of $ (without \$)?
        font = strBox.GetFont()
        if psychopy.experiment.utils.unescapedDollarSign_re.search(val):
            strBox.SetFont(self.app._codeFont)
        else:
            strBox.SetFont(self.app._mainFont)

        if hasattr(event, 'Skip'):
            event.Skip()

    def getParams(self):
        """retrieves data from any fields in self.paramCtrls
        (populated during the __init__ function)

        The new data from the dlg get inserted back into the original params
        used in __init__ and are also returned from this method.
        """
        # get data from input fields
        for fieldName in self.params:
            param = self.params[fieldName]
            if fieldName == 'advancedParams':
                pass
            elif fieldName == 'startType':
                idx = self.startTypeCtrl.GetCurrentSelection()
                param.val = self.params['startType'].allowedVals[idx]
            elif fieldName == 'stopType':
                idx = self.stopTypeCtrl.GetCurrentSelection()
                param.val = self.params['stopType'].allowedVals[idx]
            elif fieldName == 'startVal':
                param.val = self.startValCtrl.GetValue()
            elif fieldName == 'stopVal':
                param.val = self.stopValCtrl.GetValue()
            elif fieldName == 'startEstim':
                param.val = self.startEstimCtrl.GetValue()
            elif fieldName == 'durationEstim':
                param.val = self.durationEstimCtrl.GetValue()
            else:
                # the various dlg ctrls for this param
                ctrls = self.paramCtrls[fieldName]
                param.val = ctrls.getValue()
                if ctrls.typeCtrl:
                    param.valType = ctrls.getType()
                if ctrls.updateCtrl:
                    # may also need to update a static
                    updates = ctrls.getUpdates()
                    if param.updates != updates:
                        self._updateStaticUpdates(fieldName,
                                                  param.updates, updates)
                        param.updates = updates
        return self.params

    def _updateStaticUpdates(self, fieldName, updates, newUpdates):
        """If the old/new updates ctrl is using a Static component then we
        need to remove/add the component name to the appropriate static
        """
        exp = self.frame.exp
        compName = self.params['name'].val
        if hasattr(updates, 'startswith') and "during:" in updates:
            # remove the part that says 'during'
            updates = updates.split(': ')[1]
            origRoutine, origStatic = updates.split('.')
            _comp = exp.routines[origRoutine].getComponentFromName(origStatic)
            if _comp != None:
                _comp.remComponentUpdate(origRoutine, compName, fieldName)
        if hasattr(newUpdates, 'startswith') and "during:" in newUpdates:
            # remove the part that says 'during'
            newUpdates = newUpdates.split(': ')[1]
            newRoutine, newStatic = newUpdates.split('.')
            _comp = exp.routines[newRoutine].getComponentFromName(newStatic)
            _comp.addComponentUpdate(newRoutine, compName, fieldName)

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
                return msg % namespace._localized[used], False
            elif not namespace.isValid(newName):  # valid as a var name
                msg = _translate("Name must be alpha-numeric or _, no spaces")
                return msg, False
            # warn but allow, chances are good that its actually ok
            elif namespace.isPossiblyDerivable(newName):
                msg = namespace.isPossiblyDerivable(newName)
                return namespace._localized[msg], True
            else:
                return "", True

    def doValidate(self, event=None):
        """Issue a form validation on event, e.g., name or text change.
        """
        self.Validate()

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
        self.warningsDict = {}
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
        self.params['name'] = self.currentHandler.params['name']
        self.globalPanel = self.makeGlobalCtrls()
        self.stairPanel = self.makeStaircaseCtrls()
        # the controls for Method of Constants
        self.constantsPanel = self.makeConstantsCtrls()
        self.multiStairPanel = self.makeMultiStairCtrls()
        self.mainSizer.Add(self.globalPanel, border=5,
                           flag=wx.ALL | wx.ALIGN_CENTRE)
        self.mainSizer.Add(wx.StaticLine(self), border=5,
                           flag=wx.ALL | wx.EXPAND)
        self.mainSizer.Add(self.stairPanel, border=5,
                           flag=wx.ALL | wx.ALIGN_CENTRE)
        self.mainSizer.Add(self.constantsPanel, border=5,
                           flag=wx.ALL | wx.ALIGN_CENTRE)
        self.mainSizer.Add(self.multiStairPanel, border=5,
                           flag=wx.ALL | wx.ALIGN_CENTRE)
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

    def makeGlobalCtrls(self):
        panel = wx.Panel(parent=self)
        panelSizer = wx.GridBagSizer(5, 5)
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
            panelSizer.Add(ctrls.nameCtrl, [row, 0], border=1,
                           flag=wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL | wx.ALL)
            panelSizer.Add(ctrls.valueCtrl, [row, 1], border=1,
                           flag=wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL | wx.ALL)
            row += 1

        self.globalCtrls['name'].valueCtrl.Bind(wx.EVT_TEXT, self.doValidate)
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
        panelSizer = wx.GridBagSizer(5, 5)
        panel.SetSizer(panelSizer)
        row = 0
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
            elif fieldName == 'conditionsFile':
                ctrls = ParamCtrls(dlg=self, parent=panel, label=label,
                                   fieldName=fieldName,
                                   param=handler.params[fieldName],
                                   browse=True)
                self.Bind(wx.EVT_BUTTON, self.onBrowseTrialsFile,
                          ctrls.browseCtrl)
                ctrls.valueCtrl.Bind(wx.EVT_RIGHT_DOWN, self.viewConditions)
                panelSizer.Add(ctrls.nameCtrl, [row, 0])
                panelSizer.Add(ctrls.valueCtrl, [row, 1])
                panelSizer.Add(ctrls.browseCtrl, [row, 2])
                row += 1
            elif fieldName == 'conditions':
                if 'conditions' in handler.params:
                    _cond = handler.params['conditions'].val
                    text = self.getTrialsSummary(_cond)
                else:
                    text = _translate("No parameters set")
                # we'll create our own widgets
                ctrls = ParamCtrls(dlg=self, parent=panel, label=label,
                                   fieldName=fieldName,
                                   param=text, noCtrls=True)
                size = wx.Size(350, 50)
                ctrls.valueCtrl = wx.StaticText(
                    panel, label=text, size=size, style=wx.ALIGN_CENTER)
                panelSizer.Add(ctrls.valueCtrl, (row, 0),
                               span=(1, 3), flag=wx.ALIGN_CENTER)
                row += 1
            else:  # normal text entry field
                ctrls = ParamCtrls(dlg=self, parent=panel, label=label,
                                   fieldName=fieldName,
                                   param=handler.params[fieldName])
                panelSizer.Add(ctrls.nameCtrl, [row, 0])
                panelSizer.Add(ctrls.valueCtrl, [row, 1])
                row += 1
            # store info about the field
            self.constantsCtrls[fieldName] = ctrls
        return panel

    def makeMultiStairCtrls(self):
        # a list of controls for the random/sequential versions
        panel = wx.Panel(parent=self)
        panelSizer = wx.GridBagSizer(5, 5)
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
            elif fieldName == 'conditionsFile':
                ctrls = ParamCtrls(dlg=self, parent=panel, label=label,
                                   fieldName=fieldName,
                                   param=handler.params[fieldName],
                                   browse=True)
                self.Bind(wx.EVT_BUTTON, self.onBrowseTrialsFile,
                          ctrls.browseCtrl)
                panelSizer.Add(ctrls.nameCtrl, [row, 0])
                panelSizer.Add(ctrls.valueCtrl, [row, 1])
                panelSizer.Add(ctrls.browseCtrl, [row, 2])
                row += 1
            elif fieldName == 'conditions':
                if 'conditions' in handler.params:
                    text = self.getTrialsSummary(
                        handler.params['conditions'].val)
                else:
                    text = _translate(
                        "No parameters set (select a file above)")
                # we'll create our own widgets
                ctrls = ParamCtrls(dlg=self, parent=panel, label=label,
                                   fieldName=fieldName,
                                   param=text, noCtrls=True)
                size = wx.Size(350, 50)
                ctrls.valueCtrl = wx.StaticText(panel, label=text, size=size,
                                                style=wx.ALIGN_CENTER)
                panelSizer.Add(ctrls.valueCtrl, (row, 0),
                               span=(1, 3), flag=wx.ALIGN_CENTER)
                row += 1
            else:
                # normal text entry field
                ctrls = ParamCtrls(dlg=self, parent=panel, label=label,
                                   fieldName=fieldName,
                                   param=handler.params[fieldName])
                panelSizer.Add(ctrls.nameCtrl, [row, 0])
                panelSizer.Add(ctrls.valueCtrl, [row, 1])
                row += 1
            # store info about the field
            self.multiStairCtrls[fieldName] = ctrls
        return panel

    def makeStaircaseCtrls(self):
        """Setup the controls for a StairHandler
        """
        panel = wx.Panel(parent=self)
        panelSizer = wx.GridBagSizer(5, 5)
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
                panelSizer.Add(ctrls.nameCtrl, [row, 0])
                panelSizer.Add(ctrls.valueCtrl, [row, 1])
                row += 1
            # store info about the field
            self.staircaseCtrls[fieldName] = ctrls
        return panel

    def getTrialsSummary(self, conditions):
        if type(conditions) == list and len(conditions) > 0:
            # get attr names (conditions[0].keys() inserts u'name' and u' is
            # annoying for novice)
            paramStr = "["
            for param in conditions[0]:
                paramStr += (str(param) + ', ')
            paramStr = paramStr[:-2] + "]"  # remove final comma and add ]
            # generate summary info
            msg = _translate('%(nCondition)i conditions, with %(nParam)i '
                             'parameters\n%(paramStr)s')
            vals = {'nCondition': len(conditions),
                    'nParam': len(conditions[0]),
                    'paramStr': paramStr}
            return msg % vals
        else:
            if (self.conditionsFile and
                    not os.path.isfile(self.conditionsFile)):
                return _translate("No parameters set (conditionsFile not found)")
            return _translate("No parameters set")

    def viewConditions(self, event):
        """display Condition x Parameter values from within a file
        make new if no self.conditionsFile is set
        """
        self.refreshConditions()
        conditions = self.conditions  # list of dict
        if self.conditionsFile:
            # get name + dir, like BART/trialTypes.xlsx
            fileName = os.path.abspath(self.conditionsFile)
            fileName = fileName.rsplit(os.path.sep, 2)[1:]
            fileName = os.path.join(*fileName)
            if fileName.endswith('.pkl'):
                # edit existing .pkl file, loading from file
                gridGUI = DlgConditions(fileName=self.conditionsFile,
                                        parent=self, title=fileName)
            else:
                # preview existing .csv or .xlsx file that has already
                # been loaded -> conditions
                # better to reload file, get fieldOrder as well
                gridGUI = DlgConditions(conditions, parent=self,
                                        title=fileName, fixed=True)
        else:  # edit new empty .pkl file
            gridGUI = DlgConditions(parent=self)
            # should not check return value, its meaningless
            if gridGUI.OK:
                self.conditions = gridGUI.asConditions()
                if hasattr(gridGUI, 'fileName'):
                    self.conditionsFile = gridGUI.fileName
        self.currentHandler.params['conditionsFile'].val = self.conditionsFile
        # as set via DlgConditions
        if 'conditionsFile' in self.currentCtrls:
            valCtrl = self.currentCtrls['conditionsFile'].valueCtrl
            valCtrl.Clear()
            valCtrl.WriteText(self.conditionsFile)
        # still need to do namespace and internal updates (see end of
        # onBrowseTrialsFile)

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

    def onTypeChanged(self, evt=None):
        newType = evt.GetString()
        if newType == self.currentType:
            return
        self.setCtrls(newType)

    def onBrowseTrialsFile(self, event):
        self.conditionsFileOrig = self.conditionsFile
        self.conditionsOrig = self.conditions
        expFolder, expName = os.path.split(self.frame.filename)
        dlg = wx.FileDialog(self, message=_translate("Open file ..."),
                            style=wx.FD_OPEN, defaultDir=expFolder)
        if dlg.ShowModal() == wx.ID_OK:
            newFullPath = dlg.GetPath()
            if self.conditionsFile:
                _path = os.path.join(expFolder, self.conditionsFile)
                oldFullPath = os.path.abspath(_path)
                isSameFilePathAndName = bool(newFullPath == oldFullPath)
            else:
                isSameFilePathAndName = False
            newPath = _relpath(newFullPath, expFolder)
            self.conditionsFile = newPath
            needUpdate = False
            try:
                _c, _n = data.importConditions(dlg.GetPath(),
                                               returnFieldNames=True)
                self.conditions, self.condNamesInFile = _c, _n
                needUpdate = True
            except ImportError as msg:
                msg = str(msg)
                if msg.startswith('Could not open'):
                    msg = _translate('Could not read conditions from:\n')
                    _file = newFullPath.split(os.path.sep)[-1]
                    self.currentCtrls['conditions'].setValue(msg + _file)
                    logging.error(
                        'Could not open as a conditions file: %s' % newFullPath)
                else:
                    m2 = msg.replace('Conditions file ', '')
                    sep2 = os.linesep * 2
                    _title = _translate(
                        'Configuration error in conditions file')
                    dlgErr = dialogs.MessageDialog(
                        parent=self.frame, message=m2.replace(': ', sep2),
                        type='Info', title=_title).ShowModal()
                    msg = _translate('Bad condition name(s) in file:\n')
                    val = msg + newFullPath.split(os.path.sep)[-1]
                    self.currentCtrls['conditions'].setValue(val)
                    msg = 'Rejected bad condition name(s) in file: %s'
                    logging.error(msg % newFullPath)
                self.conditionsFile = self.conditionsFileOrig
                self.conditions = self.conditionsOrig
                return  # no update or display changes
            
            # check for Builder variables
            builderVariables = []
            for condName in self.condNamesInFile:
                if condName in self.exp.namespace.builder:
                    builderVariables.append(condName)
            if builderVariables:
                msg = _translate('Builder variable(s) ({}) in file:{}'.format(
                    ','.join(builderVariables), newFullPath.split(os.path.sep)[-1]))
                self.currentCtrls['conditions'].setValue(msg)
                msg = 'Rejected Builder variable(s) ({}) in file:{}'.format(
                    ','.join(builderVariables), newFullPath.split(os.path.sep)[-1])
                logging.error(msg)
                self.conditionsFile = self.conditionsFileOrig
                self.conditions = self.conditionsOrig
                return  # no update or display changes
            
            duplCondNames = []
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
                    msg = ('Assuming reloading file: same filename and '
                           'duplicate condition names in file: %s')
                    logging.info(msg % self.conditionsFile)
                else:
                    self.currentCtrls['conditionsFile'].setValue(newPath)
                    val = ('Warning: Condition names conflict with existing'
                           ':\n[' + duplCondNamesStr + ']\nProceed'
                           ' anyway? (= safe if these are in old file)')
                    self.currentCtrls['conditions'].setValue(val)
                    msg = ('Duplicate condition names, different '
                           'conditions file: %s')
                    logging.warning(msg % duplCondNamesStr)
            # stash condition names but don't add to namespace yet, user can
            # still cancel
            # add after self.show() in __init__:
            self.duplCondNames = duplCondNames

            if (needUpdate
                    or ('conditionsFile' in list(self.currentCtrls.keys())
                        and not duplCondNames)):
                self.currentCtrls['conditionsFile'].setValue(newPath)
                self.currentCtrls['conditions'].setValue(
                    self.getTrialsSummary(self.conditions))

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
                param.val = self.conditionsFile
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

    def refreshConditions(self):
        """user might have manually edited the conditionsFile name,
        which in turn affects self.conditions and namespace. It's harder
        to handle changes to long names that have been abbrev()'d, so
        skip them (names containing '...').
        """
        val = self.currentCtrls['conditionsFile'].valueCtrl.GetValue()
        if val.find('...') == -1 and self.conditionsFile != val:
            self.conditionsFile = val
            if self.conditions:
                self.exp.namespace.remove(list(self.conditions[0].keys()))
            if os.path.isfile(self.conditionsFile):
                try:
                    self.conditions = data.importConditions(
                        self.conditionsFile)
                    self.currentCtrls['conditions'].setValue(
                        self.getTrialsSummary(self.conditions))
                except ImportError as e:
                    msg1 = _translate(
                        'Badly formed condition name(s) in file:\n')
                    msg2 = _translate('.\nNeed to be legal as var name; '
                                      'edit file, try again.')
                    val = msg1 + str(e).replace(':', '\n') + msg2
                    self.currentCtrls['conditions'].setValue(val)
                    self.conditions = ''
                    msg3 = 'Reject bad condition name in conditions file: %s'
                    logging.error(msg3 % str(e).split(':')[0])
            else:
                self.conditions = None
                self.currentCtrls['conditions'].setValue(_translate(
                    "No parameters set (conditionsFile not found)"))
        else:
            msg = ('DlgLoop: could not determine if a condition'
                   ' filename was edited')
            logging.debug(msg)
            # self.currentCtrls['conditions'] could be misleading here

    def onOK(self, event=None):
        # intercept OK in case user deletes or edits the filename manually
        if 'conditionsFile' in self.currentCtrls:
            self.refreshConditions()
        event.Skip()  # do the OK button press


class DlgComponentProperties(_BaseParamsDlg):

    def __init__(self, frame, title, params, order,
                 helpUrl=None, suppressTitles=True, size=wx.DefaultSize,
                 style=wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT,
                 editing=False, depends=[],
                 timeout=None):
        style = style | wx.RESIZE_BORDER
        _BaseParamsDlg.__init__(self, frame, title, params, order,
                                helpUrl=helpUrl, size=size, style=style,
                                editing=editing, depends=depends,
                                timeout=timeout)
        self.frame = frame
        self.app = frame.app
        self.dpi = self.app.dpi

        # for input devices:
        if 'storeCorrect' in self.params:
            # do this just to set the initial values to be
            self.onStoreCorrectChange(event=None)
            self.Bind(wx.EVT_CHECKBOX, self.onStoreCorrectChange,
                      self.paramCtrls['storeCorrect'].valueCtrl)

        # for all components
        self.show()
        if self.OK:
            self.params = self.getParams()  # get new vals from dlg
        self.Destroy()

    def onStoreCorrectChange(self, event=None):
        """store correct has been checked/unchecked. Show or hide the
        correctAns field accordingly
        """
        if self.paramCtrls['storeCorrect'].valueCtrl.GetValue():
            self.paramCtrls['correctAns'].valueCtrl.Show()
            self.paramCtrls['correctAns'].nameCtrl.Show()
            # self.paramCtrls['correctAns'].typeCtrl.Show()
            # self.paramCtrls['correctAns'].updateCtrl.Show()
        else:
            self.paramCtrls['correctAns'].valueCtrl.Hide()
            self.paramCtrls['correctAns'].nameCtrl.Hide()
            # self.paramCtrls['correctAns'].typeCtrl.Hide()
            # self.paramCtrls['correctAns'].updateCtrl.Hide()
        self.mainSizer.Layout()
        self.Fit()
        self.Refresh()


class DlgExperimentProperties(_BaseParamsDlg):

    def __init__(self, frame, title, params, order, suppressTitles=False,
                 size=wx.DefaultSize, helpUrl=None,
                 style=wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT,
                 depends=[],
                 timeout=None):
        style = style | wx.RESIZE_BORDER
        _BaseParamsDlg.__init__(self, frame, 'Experiment Settings',
                                params, order, depends=depends,
                                size=size, style=style, helpUrl=helpUrl,
                                timeout=timeout)
        self.frame = frame
        self.app = frame.app
        self.dpi = self.app.dpi

        # for input devices:
        # do this just to set the initial values to be
        self.onFullScrChange(event=None)
        self.Bind(wx.EVT_CHECKBOX, self.onFullScrChange,
                  self.paramCtrls['Full-screen window'].valueCtrl)

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
            self.paramCtrls[field].valueCtrl.Disable()
            self.paramCtrls[field].nameCtrl.Disable()
        else:
            self.paramCtrls['Window size (pixels)'].valueCtrl.Enable()
            self.paramCtrls['Window size (pixels)'].nameCtrl.Enable()
        self.mainSizer.Layout()
        self.Fit()
        self.Refresh()

    def show(self):
        """Adds an OK and cancel button, shows dialogue.

        This method returns wx.ID_OK (as from ShowModal), but also
        sets self.OK to be True or False
        """
        # add buttons for help, OK and Cancel
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        buttons = wx.StdDialogButtonSizer()
        if self.helpUrl is not None:
            helpBtn = wx.Button(self, wx.ID_HELP, _translate(" Help "))
            helpBtn.SetHelpText(_translate("Get help about this component"))
            helpBtn.Bind(wx.EVT_BUTTON, self.onHelp)
            buttons.Add(helpBtn, 0, wx.ALIGN_RIGHT | wx.ALL, border=3)
        self.OKbtn = wx.Button(self, wx.ID_OK, _translate(" OK "))
        self.OKbtn.SetDefault()
        buttons.Add(self.OKbtn, 0, wx.ALIGN_RIGHT | wx.ALL, border=3)
        CANCEL = wx.Button(self, wx.ID_CANCEL, _translate(" Cancel "))
        buttons.Add(CANCEL, 0, wx.ALIGN_RIGHT | wx.ALL, border=3)

        buttons.Realize()
        self.ctrls.Fit()
        self.mainSizer.Add(self.ctrls, proportion=1, flag=wx.EXPAND)
        self.mainSizer.Add(buttons, flag=wx.ALIGN_RIGHT)
        self.SetSizerAndFit(self.mainSizer)

        # move the position to be v near the top of screen and to the
        # right of the left-most edge of builder
        builderPos = self.frame.GetPosition()
        self.SetPosition((builderPos[0] + 200, 20))

        # do show and process return
        if self.timeout is not None:
            timeout = wx.CallLater(self.timeout, self.autoTerminate)
            timeout.Start()
        retVal = self.ShowModal()
        if retVal == wx.ID_OK:
            self.OK = True
        else:
            self.OK = False
        return wx.ID_OK


def _relpath(path, start='.'):
    """This code is based on os.path.relpath in the Python 2.6 distribution,
    included here for compatibility with Python 2.5
    """

    if not path:
        raise ValueError("no path specified")

    startList = os.path.abspath(start).split(os.path.sep)
    pathList = os.path.abspath(path).split(os.path.sep)

    # Work out how much of the filepath is shared by start and path.
    i = len(os.path.commonprefix([startList, pathList]))

    relList = ['..'] * (len(startList) - i) + pathList[i:]
    if not relList:
        return path
    return os.path.join(*relList)
