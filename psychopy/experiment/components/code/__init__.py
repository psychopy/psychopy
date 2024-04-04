#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path
from psychopy import prefs
from psychopy.experiment.components import BaseComponent, Param, _translate
from psychopy.alerts import alerttools


class CodeComponent(BaseComponent):
    """An event class for inserting arbitrary code into Builder experiments"""

    categories = ['Custom']
    targets = ['PsychoPy', 'PsychoJS']
    iconFile = Path(__file__).parent / 'code.png'
    tooltip = _translate('Code: insert python commands into an experiment')

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
        self.url = "https://www.psychopy.org/builder/components/code.html"
        # params
        # want a copy, else codeParamNames list gets mutated
        self.order = ['name', 'Code Type', 'disabled',
                      'Before Experiment', 'Begin Experiment', 'Begin Routine',
                      'Each Frame', 'End Routine', 'End Experiment',
                      'Before JS Experiment', 'Begin JS Experiment', 'Begin JS Routine',
                      'Each JS Frame', 'End JS Routine', 'End JS Experiment',
                      ]
        if not codeType:
            codeType = prefs.builder['codeComponentLanguage']

        msg = _translate("Display Python or JS Code")
        self.params['Code Type'] = Param(
            codeType, valType='str', inputType="choice", allowedTypes=[],
            allowedVals=['Py', 'JS', 'Both', 'Auto->JS'],
            hint=msg, direct=False,
            label=_translate("Code type"))

        msg = _translate("Code to run before the experiment starts "
                         "(initialization); right-click checks syntax")
        self.params['Before Experiment'] = Param(
            beforeExp, valType='extendedCode', inputType="multi", allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Before experiment"))

        msg = _translate("Code at the start of the experiment ; right-click "
                         "checks syntax")
        self.params['Begin Experiment'] = Param(
            beginExp, valType='extendedCode', inputType="multi", allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Begin experiment"))

        msg = _translate("Code to be run at the start of each repeat of the "
                         "Routine (e.g. each trial); "
                         "right-click checks syntax")
        self.params['Begin Routine'] = Param(
            beginRoutine, valType='extendedCode', inputType="multi", allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Begin Routine"))

        msg = _translate("Code to be run on every video frame during for the"
                         " duration of this Routine; "
                         "right-click checks syntax")
        self.params['Each Frame'] = Param(
            eachFrame, valType='extendedCode', inputType="multi", allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Each frame"))

        msg = _translate("Code at the end of this repeat of the Routine (e.g."
                         " getting/storing responses); "
                         "right-click checks syntax")
        self.params['End Routine'] = Param(
            endRoutine, valType='extendedCode', inputType="multi", allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("End Routine"))

        msg = _translate("Code at the end of the entire experiment (e.g. "
                         "saving files, resetting computer); "
                         "right-click checks syntax")
        self.params['End Experiment'] = Param(
            endExperiment, valType='extendedCode', inputType="multi", allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("End experiment"))
        # todo: copy initial vals once javscript interp can do comments
        msg = _translate("Code before the start of the experiment (initialization"
                         "); right-click checks syntax")
        self.params['Before JS Experiment'] = Param(
            '', valType='extendedCode', inputType="multi", allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Before JS experiment"))
        msg = _translate("Code at the start of the experiment (initialization"
                         "); right-click checks syntax")
        self.params['Begin JS Experiment'] = Param(
            '', valType='extendedCode', inputType="multi", allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Begin JS experiment"))

        msg = _translate("Code to be run at the start of each repeat of the "
                         "Routine (e.g. each trial); "
                         "right-click checks syntax")
        self.params['Begin JS Routine'] = Param(
            '', valType='extendedCode', inputType="multi", allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Begin JS Routine"))

        msg = _translate("Code to be run on every video frame during for the"
                         " duration of this Routine; "
                         "right-click checks syntax")
        self.params['Each JS Frame'] = Param(
            '', valType='extendedCode', inputType="multi", allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Each JS frame"))

        msg = _translate("Code at the end of this repeat of the Routine (e.g."
                         " getting/storing responses); "
                         "right-click checks syntax")
        self.params['End JS Routine'] = Param(
            '', valType='extendedCode', inputType="multi", allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("End JS Routine"))

        msg = _translate("Code at the end of the entire experiment (e.g. "
                         "saving files, resetting computer); "
                         "right-click checks syntax")
        self.params['End JS Experiment'] = Param(
            '', valType='extendedCode', inputType="multi", allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("End JS experiment"))

        # these inherited params are harmless but might as well trim:
        for p in ('startType', 'startVal', 'startEstim', 'stopVal',
                  'stopType', 'durationEstim',
                  'saveStartStop', 'syncScreenRefresh'):
            if p in self.params:
                del self.params[p]

    def integrityCheck(self):
        python_parts = {
            'Before Experiment',
            'Begin Experiment',
            'Begin Routine',
            'Each Frame',
            'End Routine',
            'End Experiment'}
        js_parts = {
            'Before JS Experiment',
            'Begin JS Experiment',
            'Begin JS Routine',
            'Each JS Frame',
            'End JS Routine',
            'End JS Experiment'}
        for part in python_parts:
            if len(str(self.params[part])):
                alerttools.checkPythonSyntax(self, part)

        for part in js_parts:
            if len(str(self.params[part])):
                alerttools.checkJavaScriptSyntax(self, part)

    def writePreCode(self, buff):
        if len(str(self.params['Before Experiment'])) and not self.params['disabled']:
            alerttools.checkPythonSyntax(self, 'Before Experiment')
            if self.params['Before Experiment']:
                buff.writeIndentedLines("# Run 'Before Experiment' code from %(name)s" % self.params)
            buff.writeIndentedLines(str(self.params['Before Experiment']) + '\n')

    def writePreCodeJS(self, buff):
        if len(str(self.params['Before JS Experiment'])) and not self.params['disabled']:
            alerttools.checkJavaScriptSyntax(self, 'Before JS Experiment')
            if self.params['Before Experiment']:
                buff.writeIndentedLines("// Run 'Before Experiment' code from %(name)s" % self.params)
            buff.writeIndentedLines(str(self.params['Before JS Experiment']) + '\n')

    def writeInitCode(self, buff):
        if len(str(self.params['Begin Experiment'])) and not self.params['disabled']:
            alerttools.checkPythonSyntax(self, 'Begin Experiment')
            if self.params['Begin Experiment']:
                buff.writeIndentedLines("# Run 'Begin Experiment' code from %(name)s" % self.params)
            buff.writeIndentedLines(str(self.params['Begin Experiment']) + '\n')

    def writeInitCodeJS(self, buff):
        if len(str(self.params['Begin JS Experiment'])) and not self.params['disabled']:
            alerttools.checkJavaScriptSyntax(self, 'Begin JS Experiment')
            if self.params['Begin Experiment']:
                buff.writeIndentedLines("// Run 'Begin Experiment' code from %(name)s" % self.params)
            buff.writeIndentedLines(str(self.params['Begin JS Experiment']) + '\n')

    def writeRoutineStartCode(self, buff):
        if len(str(self.params['Begin Routine'])) and not self.params['disabled']:
            alerttools.checkPythonSyntax(self, 'Begin Routine')
            if self.params['Begin Routine']:
                buff.writeIndentedLines("# Run 'Begin Routine' code from %(name)s" % self.params)
            buff.writeIndentedLines(str(self.params['Begin Routine']) + '\n')

    def writeRoutineStartCodeJS(self, buff):
        if len(str(self.params['Begin JS Routine'])) and not self.params['disabled']:
            alerttools.checkJavaScriptSyntax(self, 'Begin JS Routine')
            if self.params['Begin Routine']:
                buff.writeIndentedLines("// Run 'Begin Routine' code from %(name)s" % self.params)
            buff.writeIndentedLines(str(self.params['Begin JS Routine']) + '\n')

    def writeFrameCode(self, buff):
        if len(str(self.params['Each Frame'])) and not self.params['disabled']:
            alerttools.checkPythonSyntax(self, 'Each Frame')
            if self.params['Each Frame']:
                buff.writeIndentedLines("# Run 'Each Frame' code from %(name)s" % self.params)
            buff.writeIndentedLines(str(self.params['Each Frame']) + '\n')

    def writeFrameCodeJS(self, buff):
        if len(str(self.params['Each JS Frame'])) and not self.params['disabled']:
            alerttools.checkJavaScriptSyntax(self, 'Each JS Frame')
            if self.params['Each Frame']:
                buff.writeIndentedLines("// Run 'Each Frame' code from %(name)s" % self.params)
            buff.writeIndentedLines(str(self.params['Each JS Frame']) + '\n')

    def writeRoutineEndCode(self, buff):
        if len(str(self.params['End Routine'])) and not self.params['disabled']:
            alerttools.checkPythonSyntax(self, 'End Routine')
            if self.params['End Routine']:
                buff.writeIndentedLines("# Run 'End Routine' code from %(name)s" % self.params)
            buff.writeIndentedLines(str(self.params['End Routine']) + '\n')

    def writeRoutineEndCodeJS(self, buff):
        if len(str(self.params['End JS Routine'])) and not self.params['disabled']:
            alerttools.checkJavaScriptSyntax(self, 'End JS Routine')
            if self.params['End Routine']:
                buff.writeIndentedLines("// Run 'End Routine' code from %(name)s" % self.params)
            buff.writeIndentedLines(str(self.params['End JS Routine']) + '\n')

    def writeExperimentEndCode(self, buff):
        if len(str(self.params['End Experiment'])) and not self.params['disabled']:
            alerttools.checkPythonSyntax(self, 'End Experiment')
            if self.params['End Experiment']:
                buff.writeIndentedLines("# Run 'End Experiment' code from %(name)s" % self.params)
            buff.writeIndentedLines(str(self.params['End Experiment']) + '\n')

    def writeExperimentEndCodeJS(self, buff):
        if len(str(self.params['End JS Experiment'])) and not self.params['disabled']:
            alerttools.checkJavaScriptSyntax(self, 'End JS Experiment')
            if self.params['End Experiment']:
                buff.writeIndentedLines("// Run 'End Experiment' code from %(name)s" % self.params)
            buff.writeIndentedLines(str(self.params['End JS Experiment']) + '\n')
