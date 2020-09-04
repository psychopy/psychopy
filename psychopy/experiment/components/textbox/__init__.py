#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from os import path
from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals, _translate

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'textbox.png')
tooltip = _translate('Textbox: present text stimuli but cooler')

# only use _localized values for label values, nothing functional:
_localized = {'text': _translate('Text'),
              'font': _translate('Font'),
              'letterHeight': _translate('Letter height'),
              'flipHorizontal': _translate('Flip horizontal'),
              'flipVertical': _translate('Flip vertical'),
              'languageStyle': _translate('Language style'),
              'bold': _translate('Bold'),
              'italic': _translate('Italic'),
              'lineSpacing': _translate('Line Spacing'),
              'padding': _translate('Padding'),
              'anchor': _translate('Anchor'),
              'fillColor': _translate('Fill Colour'),
              'borderColor': _translate('Border Colour'),
              'borderWidth': _translate('Border Width'),
              'editable': _translate('Editable?'),
              'autoLog': _translate('Auto Log')
              }


class TextboxComponent(BaseVisualComponent):
    """An event class for presenting text-based stimuli
    """
    categories = ['Stimuli', 'Responses']
    targets = ['PsychoPy', 'PsychoJS']
    def __init__(self, exp, parentName, name='textbox',
                 # effectively just a display-value
                 text=_translate('Any text\n\nincluding line breaks'),
                 font='Arial', units='from exp settings', bold=False, italic=False,
                 color='white', colorSpace='rgb', opacity=1.0,
                 pos=(0, 0), size='', letterHeight=0.05, ori=0,
                 lineSpacing=1.0, padding=None,  # gap between box and text
                 startType='time (s)', startVal=0.0, anchor='center',
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='',
                 languageStyle='LTR', fillColor=None,
                 borderColor=None, borderWidth=2,
                 flipHoriz=False,
                 flipVert=False,
                 editable=False, autoLog=True):
        super(TextboxComponent, self).__init__(exp, parentName, name=name,
                                            units=units,
                                            color=color,
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
        self.type = 'Textbox'
        self.url = "http://www.psychopy.org/builder/components/text.html"
        self.order = [  # controls both tab order and params within tabs
            "font", # Format tab
            "color", "fillColor",  # Color tab next
            "anchor",  # Layout tab
                      ]
        # params
        _allow3 = ['constant', 'set every repeat', 'set every frame']  # list
        self.params['color'].label = _translate("Letter color")
        self.params['color'].categ = "Color"
        self.params['opacity'].categ = "Color"

        self.params['text'] = Param(
            text, valType='extendedStr', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],  # copy the list
            hint=_translate("The text to be displayed"),
            label=_localized['text'])
        self.params['font'] = Param(
            font, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],  # copy the list
            hint=_translate("The font name (e.g. Comic Sans)"),
            label=_localized['font'],
            categ='Format')
        self.params['letterHeight'] = Param(
            letterHeight, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],  # copy the list
            hint=_translate("Specifies the height of the letter (the width"
                            " is then determined by the font)"),
            label=_localized['letterHeight'])
        self.params['flipHoriz'] = Param(
            flipHoriz, valType='bool', allowedTypes=[],
            updates='constant',
            hint=_translate("horiz = left-right reversed; vert = up-down"
                            " reversed; $var = variable"),
            label=_localized['flipHorizontal'])
        self.params['flipVert'] = Param(
            flipVert, valType='bool', allowedTypes=[],
            updates='constant',
            hint=_translate("horiz = left-right reversed; vert = up-down"
                            " reversed; $var = variable"),
            label=_localized['flipVertical'])
        self.params['languageStyle'] = Param(
            languageStyle, valType='str',
            allowedVals=['LTR', 'RTL', 'Arabic'],
            hint=_translate("Handle right-to-left (RTL) languages and Arabic reshaping"),
            label=_localized['languageStyle'],
            categ='Layout')
        self.params['italic'] = Param(
            italic, valType='bool', allowedTypes=[],
            updates='constant',
            hint=_translate("Should text be italic?"),
            label=_localized['italic'],
            categ='Format')
        self.params['bold'] = Param(
            bold, valType='bool', allowedTypes=[],
            updates='constant',
            hint=_translate("Should text be bold?"),
            label=_localized['bold'],
            categ='Format')
        self.params['lineSpacing'] = Param(
            lineSpacing, valType='num', allowedTypes=[],
            updates='constant',
            hint=_translate("Defines the space between lines"),
            label=_localized['lineSpacing'],
            categ='Format')
        self.params['padding'] = Param(
            padding, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],
            hint=_translate("Defines the space between text and the textbox border"),
            label=_localized['padding'],
            categ='Layout')
        self.params['anchor'] = Param(
            anchor, valType='str',
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
            label=_localized['anchor'],
            categ='Layout')
        self.params['fillColor'] = Param(
            fillColor, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],
            hint=_translate("Textbox background colour"),
            label=_localized['fillColor'],
            categ='Color')
        self.params['borderColor'] = Param(
            borderColor, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],
            hint=_translate("Textbox border colour"),
            label=_localized['borderColor'],
            categ='Color')
        self.params['borderWidth'] = Param(
            borderWidth, valType='num', allowedTypes=[],
            updates='constant', allowedUpdates=_allow3[:],
            hint=_translate("Textbox border width"),
            label=_localized['borderWidth'],
            categ='Layout')
        self.params['editable'] = Param(
            editable, valType='bool', allowedTypes=[],
            updates='constant',
            hint=_translate("Should textbox be editable?"),
            label=_localized['editable'])
        self.params['autoLog'] = Param(
            autoLog, valType='bool', allowedTypes=[],
            updates='constant',
            hint=_translate(
                    'Automatically record all changes to this in the log file'),
            label=_localized['autoLog'],
            categ='Data')

        for param in ('ori', 'units',
                    'flipHoriz', 'flipVert'):
            self.params[param].categ = 'Layout'
        for param in ('colorSpace',):
            self.params[param].categ = 'Color'

    def writeInitCode(self, buff):
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        else:
            unitsStr = "units=%(units)s," % self.params
        # do writing of init
        # replaces variable params with sensible defaults
        inits = getInitVals(self.params, 'PsychoPy')
        code = (
            "%(name)s = visual.TextBox2(\n"
            "     win, text=%(text)s, font=%(font)s,\n"
            "     pos=%(pos)s," + unitsStr +
            "     letterHeight=%(letterHeight)s,\n"
            "     size=%(size)s, borderWidth=%(borderWidth)s,\n"
            "     color=%(color)s, colorSpace=%(colorSpace)s,\n"
            "     opacity=%(opacity)s,\n"
            "     bold=%(bold)s, italic=%(italic)s,\n"
            "     lineSpacing=%(lineSpacing)s,\n"
            "     padding=%(padding)s,\n"
            "     anchor=%(anchor)s,\n"
            "     fillColor=%(fillColor)s, borderColor=%(borderColor)s,\n"
            "     flipHoriz=%(flipHoriz)s, flipVert=%(flipVert)s,\n"
            "     editable=%(editable)s,\n"
            "     name='%(name)s',\n"
            "     autoLog=%(autoLog)s,\n"
            ")\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeInitCodeJS(self, buff):
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = "  units: undefined, \n"
        else:
            unitsStr = "  units: %(units)s, \n" % self.params
        # do writing of init
        # replaces variable params with sensible defaults
        inits = getInitVals(self.params, 'PsychoJS')

        # check for NoneTypes
        for param in inits:
            if inits[param] in [None, 'None', '']:
                inits[param].val = 'undefined'
                if param == 'text':
                    inits[param].val = "''"

        code = ("%(name)s = new visual.TextBox({\n"
                "  win: psychoJS.window,\n"
                "  name: '%(name)s',\n"
                "  text: %(text)s,\n"
                "  font: %(font)s,\n" 
                "  pos: %(pos)s, letterHeight: %(letterHeight)s,\n"
                "  size: %(size)s," + unitsStr +
                "  color: %(color)s, colorSpace: %(colorSpace)s,\n"
                "  fillColor: %(fillColor)s, borderColor: %(borderColor)s,\n"
                "  bold: %(bold)s, italic: %(italic)s,\n"
                "  opacity: %(opacity)s,\n"
                "  padding: %(padding)s,\n"
                "  editable: %(editable)s,\n"
                "  anchor: %(anchor)s,\n")
        buff.writeIndentedLines(code % inits)

        depth = -self.getPosInRoutine()
        code = ("  depth: %.1f \n"
                "});\n\n" % (depth))
        buff.writeIndentedLines(code)

    def writeRoutineEndCode(self, buff):
        name = self.params['name']
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler
        if self.params['editable']:
            buff.writeIndented("%s.addData('%s.text',%s.text)\n" %
                               (currLoop.params['name'], name, name))
        # get parent to write code too (e.g. store onset/offset times)
        super().writeRoutineEndCode(buff)

    def writeRoutineEndCodeJS(self, buff):
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler
        if self.params['editable']:
            buff.writeIndented("psychoJS.experiment.addData('%(name)s.text', %(name)s.text);\n" %
                               self.params)
        # get parent to write code too (e.g. store onset/offset times)
        super().writeRoutineEndCodeJS(buff)
