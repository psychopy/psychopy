#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from os import path
from psychopy.experiment.components import Param, getInitVals, _translate, BaseVisualComponent
from psychopy.visual import form

__author__ = 'Jon Peirce, David Bridges, Anthony Haffey'

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'form.png')
tooltip = _translate('Form: a Psychopy survey tool')

# only use _localized values for label values, nothing functional:
_localized = {'Items': _translate('Items'),
              'Text Height': _translate('Text Height'),
              'Size': _translate('Size'),
              'Pos': _translate('Pos'),
              'Style': _translate('Styles'),
              'Item Padding': _translate('Item Padding'),
              'Data Format': _translate('Data Format'),
              'Randomize': _translate('Randomize')
              }
knownStyles = form.Form.knownStyles

class FormComponent(BaseVisualComponent):
    """A class for presenting a survey as a Builder component"""

    categories = ['Responses']
    targets = ['PsychoPy', 'PsychoJS']

    def __init__(self, exp, parentName,
                 name='form',
                 items='.csv',
                 textHeight=.03,
                 randomize=False,
                 size=(1, .7),
                 pos=(0, 0),
                 style=['dark'],
                 itemPadding=0.05,
                 startType='time (s)', startVal='0.0',
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim=''):

        super(FormComponent, self).__init__(
            exp, parentName, name=name,
            pos=pos, size=size,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        # these are defined by the BaseVisual but we don't want them
        del self.params['color']
        del self.params['colorSpace']
        del self.params['ori']
        del self.params['units']  # we only support height units right now

        self.type = 'Form'
        self.url = "http://www.psychopy.org/builder/components/"
        self.exp.requirePsychopyLibs(['visual', 'event', 'logging'])

        # params
        self.order = ['name',
                      'Items',
                      'Size', 'Pos',
                      'Data Format',
                      'Randomize',
                      ]

        # normal params:
        # = the usual as inherited from BaseComponent plus:

        self.params['Items'] = Param(
            items, valType='str', allowedTypes=[],
            updates='constant',
            hint=_translate("The csv filename containing the items for your survey."),
            label=_localized['Items'])

        self.params['Size'] = Param(
            size, valType='code', allowedTypes=[],
            updates='constant',
            hint=_translate(
                "Size of the Form on screen in 'height' units. e.g. (1, .7) height units for horizontal,"
                "and vertical, respectively"),
            label=_localized['Size'])

        self.params['Pos'] = Param(
            pos, valType='code', allowedTypes=[],
            updates='constant',
            hint=_translate("x,y position of the form on screen"),
            label=_localized['Pos'])

        self.params['Text Height'] = Param(
            textHeight, valType='code', allowedTypes=[],
            updates='constant',
            hint=_translate("The size of the item text for Form"),
            label=_localized['Text Height'],
            categ="Appearance")

        self.params['Randomize'] = Param(
            randomize, valType='bool', allowedTypes=[],
            updates='constant',
            hint=_translate("Do you want to randomize the order of your questions?"),
            label=_localized['Randomize'])

        self.params['Style'] = Param(
            style, valType='fixedList',
            updates='constant', allowedVals=knownStyles,
            hint=_translate(
                    "Styles determine the appearance of the form"),
            label=_localized['Style'],
            categ="Appearance")

        self.params['Item Padding'] = Param(
            itemPadding, valType='code', allowedTypes=[],
            updates='constant',
            hint=_translate("The padding or space between items."),
            label=_localized['Item Padding'],
            categ="Appearance")

        self.params['Data Format'] = Param(
            'rows', valType='str', allowedTypes=[],
            allowedVals=['columns', 'rows'],
            updates='constant',
            hint=_translate("Store item data by columns, or rows"),
            label=_localized['Data Format'])

    def writeInitCode(self, buff):
        inits = getInitVals(self.params)
        # build up an initialization string for Form():
        initStr = ("win.allowStencil = True\n"
                   "{name} = visual.Form(win=win, name='{name}',\n"
                   "    items={Items},\n"
                   "    textHeight={Text Height},\n"
                   "    randomize={Randomize},\n"
                   "    size={Size},\n"
                   "    pos={Pos},\n"
                   "    style={Style},\n"
                   "    itemPadding={Item Padding},"
                   ")\n".format(**inits))
        buff.writeIndented(initStr)

    def writeInitCodeJS(self, buff):
        inits = getInitVals(self.params)
        # build up an initialization string for Form():
        initStr = ("{name} = new visual.Form({{\n"
                   "  win : psychoJS.window, name:'{name}',\n"
                   "  items : {Items},\n"
                   "  textHeight : {Text Height},\n"
                   "  randomize : {Randomize},\n"
                   "  size : {Size},\n"
                   "  pos : {Pos},\n"
                   "  style : {Style},\n"
                   "  itemPadding : {Item Padding}\n"
                   "}});\n".format(**inits))
        buff.writeIndentedLines(initStr)

    def writeRoutineEndCode(self, buff):
        # save data, according to row/col format
        buff.writeIndented("{name}.addDataToExp(thisExp, {Data Format})\n"
                           .format(**self.params))
        buff.writeIndented("{name}.autodraw = False\n"
                           .format(**self.params))

    def writeRoutineEndCodeJS(self, buff):
        # save data, according to row/col format
        buff.writeIndented("{name}.addDataToExp(psychoJS.experiment, {Data Format});\n"
                           .format(**self.params))
