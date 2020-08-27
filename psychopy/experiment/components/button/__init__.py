#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from builtins import str
from os import path
import copy
from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals, _translate
from psychopy.experiment.components.textbox import TextboxComponent
from psychopy import logging
from psychopy.localization import _localized as __localized
_localized = __localized.copy()

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'button.png')
tooltip = _translate('Button: A clickable button')

_localized.update({
    'text': _translate("Text"),
    'font': _translate("Font"),
    'enabled': _translate("Enabled?"),
    'forceEndRoutine': _translate("Force End Routine?"),
    'callback': _translate("Callback Function"),
    'autoLog': _translate("Auto Log?")})


class ButtonComponent(TextboxComponent):
    """A class for creating a clickable button"""
    categories = ['Responses']
    targets = ['PsychoPy', 'PsychoJS']
    def __init__(self, exp, parentName, name='button', text="", font='Arial',
                 pos=(0, 0), units='pix', size=None, lineHeight=None, letterHeight=None,
                 color='white', colorSpace='named',
                 fillColor=(-0.98, 0.32, 0.84), fillColorSpace='rgb',
                 borderWidth=1, borderColor='white', borderColorSpace='named',
                 enabled=True, callback="", forceEndRoutine=True,
                 autoLog=False):
        TextboxComponent.__init__(self, exp, parentName, name=name, text=text, font=font,
                                  pos=pos, size=size, units=units, letterHeight=letterHeight,
                                  color=color, colorSpace=colorSpace,
                                  fillColor=fillColor,
                                  borderWidth=borderWidth, borderColor=borderColor,
                                  bold=True, editable=False,
                                  autoLog=autoLog)

        self.type = 'Button'
        self.url = "http://www.psychopy.org/builder/components/button.html"
        self.targets = ['PsychoPy', 'PsychoJS']

        _allow3 = ['constant', 'set every repeat', 'set every frame']  # list
        self.params['callback'] = Param(
            callback, valType='extendedCode', allowedTypes=[], categ='Custom',
            updates='constant',
            hint=_translate(
                'Run a custom function when this button is pressed'),
            label=_localized['callback'])
        self.params['forceEndRoutine'] = Param(
            forceEndRoutine, valType='bool', categ='Basic',
            updates='constant',
            hint=_translate("Should a button press force the end of the routine"
                         " (e.g end the trial)?"),
            label=_localized['forceEndRoutine'])
        self.params['enabled'] = Param(
            enabled, valType='bool', allowedTypes=[],
            updates='constant',
            hint=_translate("Should button be enabled?"),
            label=_localized['enabled'])

        del self.params['editable']

    def writeInitCode(self, buff):
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        else:
            unitsStr = "units=%(units)s," % self.params
        # do writing of init
        # replaces variable params with sensible defaults
        inits = getInitVals(self.params, 'PsychoPy')

        code = ("%(name)s = visual.ButtonStim(win, '%(name)s', %(text)s, font=%(font)s,\n"
                "   pos=%(pos)s, units=%(units)s, size=%(size)s, letterHeight=%(letterHeight)s,\n"
                "   color=%(color)s, colorSpace=%(colorSpace)s,\n"
                "   fillColor=%(fillColor)s, fillColorSpace=%(fillColorSpace)s,\n"
                "   borderWidth=%(borderWidth)s, borderColor=%(borderColor)s, borderColorSpace=%(borderColorSpace)s,\n"
                "   enabled=%(enabled)s, forceEndRoutine=%(forceEndRoutine)s,\n"
                "   autoLog=%(autoLog)s)\n"
                "%(name)s.draw()")
        buff.writeIndentedLines(code % inits)

    def writeInitCodeJS(self, buff):
        return

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame"""
        inits = getInitVals(self.params)
        if inits['forceEndRoutine']:
            code = ("if %(name)s.isPressed():\n"
                    "   %(callback)s\n"
                    "   continueRoutine = False\n"
                    "%(name)s.draw()\n")
        else:
            code = ("%(name)s.draw()\n")
        buff.writeIndentedLines(code % inits)

    def writeFrameCodeJS(self, buff):
        return

    def writeRoutineEndCode(self, buff):
        return

    def writeRoutineEndCodeJS(self, buff):
        return
