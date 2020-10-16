#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from builtins import str
from os import path

from psychopy import prefs
from psychopy.experiment.components import BaseComponent, Param, _translate
from psychopy.alerts import alerttools

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'code.png')
tooltip = _translate('Code: insert python commands into an experiment')
_localized = {'Code Type': _translate('Code Type'),
              'Before Experiment': _translate('BeforeExperiment'),
              'Begin Experiment': _translate('Begin Experiment'),
              'Begin Routine': _translate('Begin Routine'),
              'Each Frame': _translate('Each Frame'),
              'End Routine': _translate('End Routine'),
              'End Experiment': _translate('End Experiment'),
              'Before JS Experiment': _translate('Before JS Experiment'),
              'Begin JS Experiment': _translate('Begin JS Experiment'),
              'Begin JS Routine': _translate('Begin JS Routine'),
              'Each JS Frame': _translate('Each JS Frame'),
              'End JS Routine': _translate('End JS Routine'),
              'End JS Experiment': _translate('End JS Experiment'),
              }


class CodeComponent(BaseComponent):
    # an attribute of the class, determines the section in the components panel
    categories = ['Custom']
    """An event class for inserting arbitrary code into Builder experiments"""

    def __init__(self, exp, parentName, name='code',
                 beforeExp="",
                 beginExp="",
                 beginRoutine="",
                 eachFrame="",
                 endRoutine="",
                 endExperiment="",
                 codeType=None, translator="manual"):
        super(CodeComponent, self).__init__(exp, parentName, name)
        self.type = 'Code'
        self.targets = ['PsychoPy', 'PsychoJS']
        self.url = "http://www.psychopy.org/builder/components/code.html"
        # params
        # want a copy, else codeParamNames list gets mutated
        self.order = ['name', 'Code Type',
                      'Before Experiment', 'Begin Experiment', 'Begin Routine',
                      'Each Frame', 'End Routine', 'End Experiment',
                      'Before JS Experiment', 'Begin JS Experiment', 'Begin JS Routine',
                      'Each JS Frame', 'End JS Routine', 'End JS Experiment',
                      ]
        if not codeType:
            codeType = prefs.builder['codeComponentLanguage']

        msg = _translate("Display Python or JS Code")
        self.params['Code Type'] = Param(
            codeType, valType='str', allowedTypes=[],
            allowedVals=['Py', 'JS', 'Both', 'Auto->JS'],
            hint=msg,
            label=_localized['Code Type'])

        msg = _translate("Code to run before the experiment starts "
                         "(initialization); right-click checks syntax")
        self.params['Before Experiment'] = Param(
            beforeExp, valType='extendedCode', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['Before Experiment'])

        msg = _translate("Code at the start of the experiment ; right-click "
                         "checks syntax")
        self.params['Begin Experiment'] = Param(
            beginExp, valType='extendedCode', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['Begin Experiment'])

        msg = _translate("Code to be run at the start of each repeat of the "
                         "Routine (e.g. each trial); "
                         "right-click checks syntax")
        self.params['Begin Routine'] = Param(
            beginRoutine, valType='extendedCode', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['Begin Routine'])

        msg = _translate("Code to be run on every video frame during for the"
                         " duration of this Routine; "
                         "right-click checks syntax")
        self.params['Each Frame'] = Param(
            eachFrame, valType='extendedCode', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['Each Frame'])

        msg = _translate("Code at the end of this repeat of the Routine (e.g."
                         " getting/storing responses); "
                         "right-click checks syntax")
        self.params['End Routine'] = Param(
            endRoutine, valType='extendedCode', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['End Routine'])

        msg = _translate("Code at the end of the entire experiment (e.g. "
                         "saving files, resetting computer); "
                         "right-click checks syntax")
        self.params['End Experiment'] = Param(
            endExperiment, valType='extendedCode', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['End Experiment'])
        # todo: copy initial vals once javscript interp can do comments
        msg = _translate("Code before the start of the experiment (initialization"
                         "); right-click checks syntax")
        self.params['Before JS Experiment'] = Param(
            '', valType='extendedCode', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['Before JS Experiment'])
        msg = _translate("Code at the start of the experiment (initialization"
                         "); right-click checks syntax")
        self.params['Begin JS Experiment'] = Param(
            '', valType='extendedCode', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['Begin JS Experiment'])

        msg = _translate("Code to be run at the start of each repeat of the "
                         "Routine (e.g. each trial); "
                         "right-click checks syntax")
        self.params['Begin JS Routine'] = Param(
            '', valType='extendedCode', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['Begin JS Routine'])

        msg = _translate("Code to be run on every video frame during for the"
                         " duration of this Routine; "
                         "right-click checks syntax")
        self.params['Each JS Frame'] = Param(
            '', valType='extendedCode', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['Each JS Frame'])

        msg = _translate("Code at the end of this repeat of the Routine (e.g."
                         " getting/storing responses); "
                         "right-click checks syntax")
        self.params['End JS Routine'] = Param(
            '', valType='extendedCode', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['End JS Routine'])

        msg = _translate("Code at the end of the entire experiment (e.g. "
                         "saving files, resetting computer); "
                         "right-click checks syntax")
        self.params['End JS Experiment'] = Param(
            '', valType='extendedCode', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['End JS Experiment'])

        # these inherited params are harmless but might as well trim:
        for p in ('startType', 'startVal', 'startEstim', 'stopVal',
                  'stopType', 'durationEstim',
                  'saveStartStop', 'syncScreenRefresh'):
            if p in self.params:
                del self.params[p]

    def writePreCode(self, buff):
        if len(str(self.params['Before Experiment'])):
            alerttools.checkPythonSyntax(self, 'Before Experiment')
            buff.writeIndentedLines(str(self.params['Before Experiment']) + '\n')

    def writePreCodeJS(self, buff):
        if len(str(self.params['Before JS Experiment'])):
            alerttools.checkPythonSyntax(self, 'Before Experiment')
            buff.writeIndentedLines(str(self.params['Before JS Experiment']) + '\n')

    def writeInitCode(self, buff):
        if len(str(self.params['Begin Experiment'])):
            alerttools.checkPythonSyntax(self, 'Begin Experiment')
            buff.writeIndentedLines(str(self.params['Begin Experiment']) + '\n')

    def writeInitCodeJS(self, buff):
        if len(str(self.params['Begin JS Experiment'])):
            alerttools.checkJavaScriptSyntax(self, 'Begin JS Experiment')
            buff.writeIndentedLines(str(self.params['Begin JS Experiment']) + '\n')

    def writeRoutineStartCode(self, buff):
        if len(str(self.params['Begin Routine'])):
            alerttools.checkPythonSyntax(self, 'Begin Routine')
            buff.writeIndentedLines(str(self.params['Begin Routine']) + '\n')

    def writeRoutineStartCodeJS(self, buff):
        if len(str(self.params['Begin JS Routine'])):
            alerttools.checkJavaScriptSyntax(self, 'Begin JS Routine')
            buff.writeIndentedLines(str(self.params['Begin JS Routine']) + '\n')

    def writeFrameCode(self, buff):
        if len(str(self.params['Each Frame'])):
            alerttools.checkPythonSyntax(self, 'Each Frame')
            buff.writeIndentedLines(str(self.params['Each Frame']) + '\n')

    def writeFrameCodeJS(self, buff):
        if len(str(self.params['Each JS Frame'])):
            alerttools.checkJavaScriptSyntax(self, 'Each JS Frame')
            buff.writeIndentedLines(str(self.params['Each JS Frame']) + '\n')

    def writeRoutineEndCode(self, buff):
        if len(str(self.params['End Routine'])):
            alerttools.checkPythonSyntax(self, 'End Routine')
            buff.writeIndentedLines(str(self.params['End Routine']) + '\n')

    def writeRoutineEndCodeJS(self, buff):
        if len(str(self.params['End JS Routine'])):
            alerttools.checkJavaScriptSyntax(self, 'End JS Routine')
            buff.writeIndentedLines(str(self.params['End JS Routine']) + '\n')

    def writeExperimentEndCode(self, buff):
        if len(str(self.params['End Experiment'])):
            alerttools.checkPythonSyntax(self, 'End Experiment')
            buff.writeIndentedLines(str(self.params['End Experiment']) + '\n')

    def writeExperimentEndCodeJS(self, buff):
        if len(str(self.params['End JS Experiment'])):
            alerttools.checkJavaScriptSyntax(self, 'End JS Experiment')
            buff.writeIndentedLines(str(self.params['End JS Experiment']) + '\n')
