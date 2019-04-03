#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function
from builtins import super  # provides Py3-style super() using python-future

from os import path
from psychopy.experiment.components import BaseVisualComponent, Param, \
    getInitVals, _translate
from psychopy.visual import slider
from psychopy.experiment import py2js

__author__ = 'Jon Peirce'

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'slider.png')
tooltip = _translate('Slider: A simple, flexible object for getting ratings')

# only use _localized values for label values, nothing functional:
_localized = {
    'categoryChoices': _translate('Category choices'),
    'labels': _translate('Labels'),
    'ticks': _translate('Ticks'),
    'size': _translate('Size'),
    'pos': _translate('Position [x,y]'),
    'forceEndRoutine': _translate('Force end of Routine'),
    'storeHistory': _translate('Store history'),
    'storeRating': _translate('Store rating'),
    'storeRatingTime': _translate('Store rating time')}

knownStyles = slider.Slider.knownStyles


# ticks = (1, 2, 3, 4, 5),
# labels = None,
# pos = None,
# size = None,
# units = None,
# flip = False,
# style = 'rating',
# granularity = 0,
# textSize = 1.0,
# readOnly = False,
# color = 'LightGray',
# textFont = 'Helvetica Bold',

class SliderComponent(BaseVisualComponent):
    """A class for presenting a rating scale as a builder component
    """
    categories = ['Responses', 'Custom']

    def __init__(self, exp, parentName,
                 name='slider',
                 labels='',
                 ticks="(1, 2, 3, 4, 5)",
                 size='(1.0, 0.1)',
                 pos='(0, -0.4)',
                 flip=False,
                 style=['rating'],
                 granularity=0,
                 color="LightGray",
                 font="HelveticaBold",
                 startType='time (s)', startVal='0.0',
                 stopType='condition', stopVal='',
                 startEstim='', durationEstim='',
                 forceEndRoutine=True,
                 storeRating=True, storeRatingTime=True, storeHistory=False):
        super(SliderComponent, self).__init__(
                exp, parentName, name,
                startType=startType, startVal=startVal,
                stopType=stopType, stopVal=stopVal,
                startEstim=startEstim, durationEstim=durationEstim)
        self.type = 'Slider'
        self.url = "http://www.psychopy.org/builder/components/slidercomponent.html"
        self.exp.requirePsychopyLibs(['visual', 'event'])
        self.targets = ['PsychoPy', 'PsychoJS']

        # params
        self.order = ['name',
                      'size', 'pos',
                      'ticks', 'labels',  'granularity',
                      'font','flip','color','styles',
                      ]

        # normal params:
        # = the usual as inherited from BaseVisual plus:
        self.params['ticks'] = Param(
                ticks, valType='list', allowedTypes=[],
                updates='constant',
                allowedUpdates=['constant', 'set every repeat'],
                hint=_translate("Tick positions (numerical) on the scale, "
                                "separated by commas"),
                label=_localized['ticks'])
        self.params['labels'] = Param(
                labels, valType='list', allowedTypes=[],
                updates='constant',
                allowedUpdates=['constant', 'set every repeat'],
                hint=_translate("Labels for the tick marks on the scale, "
                                "separated by commas"),
                label=_localized['labels'])
        self.params['granularity'] = Param(
                granularity, valType='code', allowedTypes=[],
                updates='constant',
                allowedUpdates=['constant', 'set every repeat'],
                hint=_translate("Specifies the minimum step size "
                                "(0 for a continuous scale, 1 for integer "
                                "rating scale)"),
                label=_translate('Granularity'))
        self.params['forceEndRoutine'] = Param(
                forceEndRoutine, valType='bool', allowedTypes=[],
                updates='constant', allowedUpdates=[],
                hint=_translate("Should setting a rating (releasing the mouse) "
                                "cause the end of the routine (e.g. trial)?"),
                label=_localized['forceEndRoutine'])
        self.params['pos'] = Param(
                pos, valType='code', allowedTypes=[],
                updates='constant',
                allowedUpdates=['constant', 'set every repeat',
                                'set every frame'],
                hint=_translate("x,y position on the screen"),
                label=_localized['pos'])
        self.params['size'] = Param(
                size, valType='code', allowedTypes=[],
                updates='constant',
                allowedUpdates=['constant', 'set every repeat',
                                'set every frame'],
                hint=_translate(
                        "Size on screen. e.g. (500,10) pix for horizontal,"
                        "(10,500) pix for vertical"),
                label=_localized['size'])

        # advanced params:
        self.params['flip'] = Param(
                flip, valType='bool',
                updates='constant', allowedUpdates=[],
                hint=_translate(
                        "By default the labels will be on the bottom or "
                        "left of the scale, but this can be flipped to the "
                        "other side."),
                label=_translate('Flip'),
                categ='Appearance')
        self.params['color'] = Param(
                color, valType='str',
                updates='constant',
                allowedUpdates=['constant', 'set every repeat',
                                'set every frame'],
                hint=_translate(
                        "Color of the lines and labels (might be"
                        "overridden by the style setting)"),
                label=_translate('Color'),
                categ='Appearance')
        self.params['font'] = Param(
                font, valType='str',
                updates='constant',
                allowedUpdates=['constant', 'set every repeat'],
                hint=_translate(
                        "Font for the labels"),
                label=_translate('Font'),
                categ='Appearance')

        self.params['styles'] = Param(
                style, valType='fixedList',
                updates='constant', allowedVals=knownStyles,
                hint=_translate(
                        "Styles determine the appearance of the slider"),
                label=_translate('Styles'),
                categ='Appearance')

        # data params
        self.params['storeRating'] = Param(
                storeRating, valType='bool', allowedTypes=[],
                updates='constant', allowedUpdates=[],
                hint=_translate("store the rating"),
                label=_localized['storeRating'],
                categ='Data')
        self.params['storeRatingTime'] = Param(
                storeRatingTime, valType='bool', allowedTypes=[],
                updates='constant', allowedUpdates=[],
                hint=_translate("Store the time taken to make the choice (in "
                                "seconds)"),
                label=_localized['storeRatingTime'],
                categ='Data')
        self.params['storeHistory'] = Param(
                storeHistory, valType='bool', allowedTypes=[],
                updates='constant', allowedUpdates=[],
                hint=_translate("store the history of (selection, time)"),
                label=_localized['storeHistory'],
                categ='Data')

    def writeInitCode(self, buff):

        inits = getInitVals(self.params)
        # build up an initialization string for Slider():
        initStr = ("{name} = visual.Slider(win=win, name='{name}',\n"
                   "    size={size}, pos={pos},\n"
                   "    labels={labels}, ticks={ticks},\n"
                   "    granularity={granularity}, style={styles},\n"
                   "    color={color}, font={font},\n"
                   "    flip={flip})\n"
                   .format(**inits))
        buff.writeIndented(initStr)

    def writeInitCodeJS(self, buff):
        inits = getInitVals(self.params)
        for param in inits:
            if inits[param].val in ['', None, 'None', 'none']:
                inits[param].val = 'undefined'
        boolConverter = {False: 'false', True: 'true'}
        sliderStyles = {'slider': 'SLIDER',
                        '()': 'RATING',
                        'rating': 'RATING',
                        'radio': 'RADIO',
                        'labels45': 'LABELS_45',
                        'whiteOnBlack': 'WHITE_ON_BLACK',
                        'triangleMarker': 'TRIANGLE_MARKER'}

        # If no style given, set default 'rating' as list
        if len(inits['styles'].val) == 0:
            inits['styles'].val = ['rating']

        # reformat styles for JS
        inits['styles'].val = ', '.join(["visual.Slider.Style.{}".
                                        format(sliderStyles[style]) for style in inits['styles'].val])
        # add comma so is treated as tuple in py2js and converted to list, as required
        inits['styles'].val += ','
        inits['styles'].val = py2js.expression2js(inits['styles'].val)

        # build up an initialization string for Slider():
        initStr = ("{name} = new visual.Slider({{\n"
                   "  win: psychoJS.window, name: '{name}',\n"
                   "  size: {size}, pos: {pos},\n"
                   "  labels: {labels}, ticks: {ticks},\n"
                   "  granularity: {granularity}, style: {styles},\n"
                   "  color: new util.Color({color}), \n"
                   "  fontFamily: {font}, bold: true, italic: false, \n"
                   ).format(**inits)
        initStr += ("  flip: {flip},\n"
                    "}});\n\n").format(flip=boolConverter[inits['flip'].val])
        buff.writeIndentedLines(initStr)

    def writeRoutineStartCode(self, buff):
        buff.writeIndented("%(name)s.reset()\n" % (self.params))

    def writeRoutineStartCodeJS(self, buff):
        buff.writeIndented("%(name)s.reset()\n" % (self.params))

    def writeFrameCode(self, buff):
        super(SliderComponent, self).writeFrameCode(buff)  # Write basevisual frame code
        forceEnd = self.params['forceEndRoutine'].val
        if forceEnd:
            code = ("\n# Check %(name)s for response to end routine\n"
                    "if %(name)s.getRating() is not None and %(name)s.status == STARTED:\n"
                    "    continueRoutine = False")
            buff.writeIndentedLines(code % (self.params))

    def writeFrameCodeJS(self, buff):
        super(SliderComponent, self).writeFrameCodeJS(buff)  # Write basevisual frame code
        forceEnd = self.params['forceEndRoutine'].val
        if forceEnd:
            code = ("\n// Check %(name)s for response to end routine\n"
                    "if (%(name)s.getRating() !== undefined && %(name)s.status === PsychoJS.Status.STARTED) {\n"
                    "  continueRoutine = false; }\n")
            buff.writeIndentedLines(code % (self.params))

    def writeRoutineEndCode(self, buff):
        name = self.params['name']
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler

        # write the actual code
        storeTime = self.params['storeRatingTime'].val
        if self.params['storeRating'].val or storeTime:
            if currLoop.type in ['StairHandler', 'QuestHandler']:
                msg = ("# NB PsychoPy doesn't handle a 'correct answer' "
                       "for Slider events so doesn't know what to "
                       "tell a StairHandler (or QuestHandler)\n")
                buff.writeIndented(msg)
            elif currLoop.type in ['TrialHandler', 'ExperimentHandler']:
                loopName = currLoop.params['name']
            else:
                loopName = 'thisExp'

            if self.params['storeRating'].val == True:
                code = "%s.addData('%s.response', %s.getRating())\n"
                buff.writeIndented(code % (loopName, name, name))
            if self.params['storeRatingTime'].val == True:
                code = "%s.addData('%s.rt', %s.getRT())\n"
                buff.writeIndented(code % (loopName, name, name))
            if self.params['storeHistory'].val == True:
                code = "%s.addData('%s.history', %s.getHistory())\n"
                buff.writeIndented(code % (loopName, name, name))

            # get parent to write code too (e.g. store onset/offset times)
            super().writeRoutineEndCode(buff)

    def writeRoutineEndCodeJS(self, buff):
        name = self.params['name']
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler

        # write the actual code
        storeTime = self.params['storeRatingTime'].val
        if self.params['storeRating'].val or storeTime:
            if currLoop.type in ['StairHandler', 'QuestHandler']:
                msg = ("/* NB PsychoPy doesn't handle a 'correct answer' "
                       "for Slider events so doesn't know what to "
                       "tell a StairHandler (or QuestHandler)*/\n")
                buff.writeIndented(msg)

            if self.params['storeRating'].val == True:
                code = "psychoJS.experiment.addData('%s.response', %s.getRating());\n"
                buff.writeIndented(code % (name, name))
            if self.params['storeRatingTime'].val == True:
                code = "psychoJS.experiment.addData('%s.rt', %s.getRT());\n"
                buff.writeIndented(code % (name, name))
            if self.params['storeHistory'].val == True:
                code = "psychoJS.experiment.addData('%s.history', %s.getHistory());\n"
                buff.writeIndented(code % (name, name))
