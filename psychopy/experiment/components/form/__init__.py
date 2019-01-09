#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from os import path
from psychopy.experiment.components import Param, getInitVals, _translate, BaseComponent

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
              'Item Padding': _translate('Item Padding'),
              'Data Format': _translate('Data Format'),
              'Randomize': _translate('Randomize')
              }

class FormComponent(BaseComponent):
    """A class for presenting a survey as a Builder component"""

    categories = ['Stimuli', 'Responses', 'Custom']

    def __init__(self, exp, parentName,
                 name='form',
                 items='.csv',
                 textHeight=.03,
                 randomize=False,
                 size=(1, .7),
                 pos=(0, 0),
                 itemPadding=0.05,
                 startType='time (s)', startVal='0.0',
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim=''):

        super(FormComponent, self).__init__(
            exp, parentName, name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Form'
        self.url = "http://www.psychopy.org/builder/components/"
        self.exp.requirePsychopyLibs(['visual', 'event', 'logging'])

        # params
        self.order = ['name',
                      'Items',
                      'Text Height',
                      'Size', 'Pos',
                      'Item Padding',
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
            label=_localized['Text Height'])

        self.params['Randomize'] = Param(
            randomize, valType='bool', allowedTypes=[],
            updates='constant',
            hint=_translate("Do you want to randomize the order of your questions?"),
            label=_localized['Randomize'])

        self.params['Item Padding'] = Param(
            itemPadding, valType='code', allowedTypes=[],
            updates='constant',
            hint=_translate("The padding or space between items."),
            label=_localized['Item Padding'])

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
                   "    itemPadding={Item Padding})\n".format(**inits))
        buff.writeIndented(initStr)

    def writeRoutineStartCode(self, buff):
        pass

    def writeFrameCode(self, buff):
        buff.writeIndented("%(name)s.draw()\n" % (self.params))

    def writeRoutineEndCode(self, buff):
        if self.params['Data Format'] == 'rows':
            code = ("{name}Data = {name}.getData()\n"
                    "while {name}Data['questions']:\n"
                    "    for dataTypes in {name}Data.keys():\n"
                    "        thisExp.addData(dataTypes, {name}Data[dataTypes].popleft())\n"
                    "    thisExp.nextEntry()\n".format(**self.params))
        elif self.params['Data Format'] == 'columns':
            code = ("{name}Data = {name}.getData()\n"
                    "for dataTypes in {name}Data.keys():\n"
                    "    for index, items in enumerate({name}Data[dataTypes]):\n"
                    "        thisExp.addData('{name}.' + str(index), items)\n"
                    "    thisExp.nextEntry()\n".format(**self.params))
        buff.writeIndented(code)


