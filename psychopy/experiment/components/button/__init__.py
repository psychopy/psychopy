#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from os import path

from psychopy.alerts import alerttools
from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals, _translate
from psychopy.localization import _localized as __localized
_localized = __localized.copy()

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'button.png')
tooltip = _translate('Button: A clickable textbox')

# only use _localized values for label values, nothing functional:
_localized.update({'callback': _translate("Callback Function"),
                   'forceEndRoutine': _translate('Force end of Routine'),
                   'text': _translate('Button text'),
                   'font': _translate('Font'),
                   'letterHeight': _translate('Letter height'),
                   'bold': _translate('Bold'),
                   'italic': _translate('Italic'),
                   'padding': _translate('Padding'),
                   'anchor': _translate('Anchor'),
                   'fillColor': _translate('Fill Colour'),
                   'borderColor': _translate('Border Colour'),
                   'borderWidth': _translate('Border Width'),
                   })

class ButtonComponent(BaseVisualComponent):
    """
    A component for presenting a clickable textbox with a programmable callback
    """
    categories = ['Stimuli', 'Responses']
    targets = ['PsychoPy']

    def __init__(self, exp, parentName, name="button",
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='',
                 text=_translate("Click here"), font='Arvo',
                 pos=(0, 0), size="", padding="", anchor='center', units='from exp settings', ori=0,
                 color="white", fillColor="None", borderColor="None", borderWidth=0, colorSpace='rgb', opacity=1,
                 letterHeight=0.05, bold=True, italic=False,
                 callback="", forceEndRoutine=True):
        super(ButtonComponent, self).__init__(exp, parentName, name,
                                            units=units,
                                            color=color, fillColor=fillColor, borderColor=borderColor,
                                            colorSpace=colorSpace,
                                            pos=pos,
                                            ori=ori,
                                            size=size,
                                            startType=startType,
                                            startVal=startVal,
                                            stopType=stopType,
                                            stopVal=stopVal,
                                            startEstim=startEstim,
                                            durationEstim=durationEstim)
        self.type = 'Button'
        self.url = "http://www.psychopy.org/builder/components/button.html"
        self.order += [  # controls order of params within tabs
            "forceEndRoutine", "text", "callback",  # Basic tab
            "borderWidth", "opacity",  # Appearance tab
            "font", "letterHeight", "lineSpacing", "bold", "italic",  # Formatting tab
        ]
        # params
        _allow3 = ['constant', 'set every repeat', 'set every frame']  # list
        self.params['color'].label = _translate("Text Color")

        self.params['forceEndRoutine'] = Param(
            forceEndRoutine, valType='bool', inputType="bool", categ='Basic',
            updates='constant',
            hint=_translate("Should a response force the end of the Routine "
                            "(e.g end the trial)?"),
            label=_localized['forceEndRoutine'])
        self.params['callback'] = Param(
            callback, valType='code', inputType="multi", allowedTypes=[], categ='Basic',
            updates='constant', allowedUpdates=['constant'],
            hint=_translate("Code to run when button is clicked"),
            label=_localized['callback'])
        self.params['text'] = Param(
            text, valType='str', inputType="single", allowedTypes=[], categ='Basic',
            updates='constant', allowedUpdates=_allow3[:],  # copy the list
            hint=_translate("The text to be displayed"),
            label=_localized['text'])
        self.params['font'] = Param(
            font, valType='str', inputType="single", allowedTypes=[], categ='Formatting',
            updates='constant', allowedUpdates=_allow3[:],  # copy the list
            hint=_translate("The font name (e.g. Comic Sans)"),
            label=_localized['font'])
        self.params['letterHeight'] = Param(
            letterHeight, valType='num', inputType="single", allowedTypes=[], categ='Formatting',
            updates='constant', allowedUpdates=_allow3[:],  # copy the list
            hint=_translate("Specifies the height of the letter (the width"
                            " is then determined by the font)"),
            label=_localized['letterHeight'])
        self.params['italic'] = Param(
            italic, valType='bool', inputType="bool", allowedTypes=[], categ='Formatting',
            updates='constant',
            hint=_translate("Should text be italic?"),
            label=_localized['italic'])
        self.params['bold'] = Param(
            bold, valType='bool', inputType="bool", allowedTypes=[], categ='Formatting',
            updates='constant',
            hint=_translate("Should text be bold?"),
            label=_localized['bold'])
        self.params['padding'] = Param(
            padding, valType='num', inputType="single", allowedTypes=[], categ='Layout',
            updates='constant', allowedUpdates=_allow3[:],
            hint=_translate("Defines the space between text and the textbox border"),
            label=_localized['padding'])
        self.params['anchor'] = Param(
            anchor, valType='str', inputType="choice", categ='Layout',
            allowedVals=['center',
                         'top-center',
                         'bottom-center',
                         'center-left',
                         'center-right',
                         'top-left',
                         'top-right',
                         'bottom-left',
                         'bottom-right',
                         ],
            updates='constant',
            hint=_translate("Should text anchor to the top, center or bottom of the box?"),
            label=_localized['anchor'])
        self.params['borderWidth'] = Param(
            borderWidth, valType='num', inputType="single", allowedTypes=[], categ='Appearance',
            updates='constant', allowedUpdates=_allow3[:],
            hint=_translate("Textbox border width"),
            label=_localized['borderWidth'])


    def writeInitCode(self, buff):
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        else:
            unitsStr = "units=%(units)s," % self.params
        # do writing of init
        inits = getInitVals(self.params, 'PsychoPy')
        code = (
                       "%(name)s = visual.ButtonStim(win, \n"
                       "    text=%(text)s, font=%(font)s,\n"
                       "     pos=%(pos)s," + unitsStr + "\n"
                       "     letterHeight=%(letterHeight)s,\n"
                       "     size=%(size)s, borderWidth=%(borderWidth)s,\n"
                       "     fillColor=%(fillColor)s, borderColor=%(borderColor)s,\n"
                       "     color=%(color)s, colorSpace=%(colorSpace)s,\n"
                       "     opacity=%(opacity)s,\n"
                       "     bold=%(bold)s, italic=%(italic)s,\n"
                       "     padding=%(padding)s,\n"
                       "     anchor=%(anchor)s,\n"
                       "     name='%(name)s')"
        )
        buff.writeIndentedLines(code % inits)

    def writeFrameCode(self, buff):
        BaseVisualComponent.writeFrameCode(self, buff)
        # do writing of init
        inits = getInitVals(self.params, 'PsychoPy')
        code = (
            "# check whether button \"%(name)s\" has been pressed\n"
            "if %(name)s.isClicked:\n"
            "   %(callback)s\n" +
            "   continueRoutine = False" if inits['forceEndRoutine'] else ""
        )
        buff.writeIndentedLines(code % inits)

    def writeRoutineEndCode(self, buff):
        BaseVisualComponent.writeRoutineEndCode(self, buff)
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler
        name = self.params['name']
        code = f"{currLoop.params['name']}.addData('{name}.rt', t)\n"
        buff.writeIndentedLines(code)
        # get parent to write code too (e.g. store onset/offset times)
        super().writeRoutineEndCode(buff)

    def integrityCheck(self):
        super().integrityCheck()  # run parent class checks first
        alerttools.testFont(self) # Test whether font is available locally