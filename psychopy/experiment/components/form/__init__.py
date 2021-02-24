#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from os import path
from psychopy.experiment.components import Param, getInitVals, _translate, BaseVisualComponent
from psychopy.visual import form
from psychopy.localization import _localized as __localized
_localized = __localized.copy()

__author__ = 'Jon Peirce, David Bridges, Anthony Haffey'

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'form.png')
tooltip = _translate('Form: a Psychopy survey tool')

# only use _localized values for label values, nothing functional:
_localized.update({'Items': _translate('Items'),
                   'Text Height': _translate('Text Height'),
                   'Style': _translate('Styles'),
                   'Item Padding': _translate('Item Padding'),
                   'Data Format': _translate('Data Format'),
                   'Randomize': _translate('Randomize')
                   })
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
                 color='white',
                 fillColor='red',
                 borderColor='white',
                 size=(1, .7),
                 pos=(0, 0),
                 style='dark',
                 itemPadding=0.05,
                 startType='time (s)', startVal='0.0',
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim=''):

        super(FormComponent, self).__init__(
            exp, parentName, name=name,
            pos=pos, size=size,
            color=color, fillColor=fillColor, borderColor=borderColor,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        # these are defined by the BaseVisual but we don't want them
        del self.params['ori']
        del self.params['units']  # we only support height units right now

        self.type = 'Form'
        self.url = "https://www.psychopy.org/builder/components/form.html"
        self.exp.requirePsychopyLibs(['visual', 'event', 'logging'])

        # params
        self.order += ['Items', 'Randomize',  # Basic tab
                       'Data Format',  # Data tab
                      ]
        self.order.insert(self.order.index("units"), "Item Padding")

        # normal params:
        # = the usual as inherited from BaseComponent plus:

        self.params['Items'] = Param(
            items, valType='file', inputType="table", allowedTypes=[], categ='Basic',
            updates='constant',
            hint=_translate("The csv filename containing the items for your survey."),
            label=_localized['Items'])

        self.params['Text Height'] = Param(
            textHeight, valType='num', inputType="single", allowedTypes=[], categ='Formatting',
            updates='constant',
            hint=_translate("The size of the item text for Form"),
            label=_localized['Text Height'])

        self.params['Randomize'] = Param(
            randomize, valType='bool', inputType="bool", allowedTypes=[], categ='Basic',
            updates='constant',
            hint=_translate("Do you want to randomize the order of your questions?"),
            label=_localized['Randomize'])

        self.params['Item Padding'] = Param(
            itemPadding, valType='num', inputType="single", allowedTypes=[], categ='Layout',
            updates='constant',
            hint=_translate("The padding or space between items."),
            label=_localized['Item Padding'])

        self.params['Data Format'] = Param(
            'rows', valType='str', inputType="choice", allowedTypes=[], categ='Basic',
            allowedVals=['columns', 'rows'],
            updates='constant',
            hint=_translate("Store item data by columns, or rows"),
            label=_localized['Data Format'])

        self.params['Style'] = Param(
            style, valType='str', inputType="choice", categ="Appearance",
            updates='constant', allowedVals=knownStyles,
            hint=_translate(
                    "Styles determine the appearance of the form"),
            label=_localized['Style'])

        self.params['color'].label = _translate("Text Color")
        self.params['color'].allowedUpdates = []
        self.params['fillColor'].label = _translate("Marker Colors")
        self.params['fillColor'].allowedUpdates = []
        self.params['borderColor'].label =_translate("Lines Color")
        self.params['borderColor'].allowedUpdates = []

        # TEMPORARY: Hide color params until we have something that works
        del self.params['color']
        del self.params['fillColor']
        del self.params['borderColor']

        self.params['pos'].allowedUpdates = []
        self.params['size'].allowedUpdates = []

    def writeInitCode(self, buff):
        inits = getInitVals(self.params)
        # build up an initialization string for Form():
        initStr = ("win.allowStencil = True\n"
                   "{name} = visual.Form(win=win, name='{name}',\n"
                   "    items={Items},\n"
                   "    textHeight={Text Height},\n"
                   "    randomize={Randomize},\n"
                   # "    color={color}, fillColor={fillColor}, borderColor={borderColor}, colorSpace={colorSpace}, \n"
                   "    size={size},\n"
                   "    pos={pos},\n"
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
                   "  size : {size},\n"
                   "  pos : {pos},\n"
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
