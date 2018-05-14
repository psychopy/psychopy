#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from builtins import str
from builtins import map
from os import path
import re
from psychopy.experiment.components import BaseComponent, Param, _translate

__author__ = 'Jon Peirce'

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'slider.png')
tooltip = _translate('Slider: A simple, flexible object for getting ratings')

# only use _localized values for label values, nothing functional:
_localized = {
              'categoryChoices': _translate('Category choices'),
              'labels': _translate('Labels'),
              'marker': _translate('Marker type'),
              'size': _translate('Size'),
              'pos': _translate('Position [x,y]'),
              'forceEndRoutine': _translate('Force end of Routine'),
              'storeHistory': _translate('Store history'),
              'storeRating': _translate('Store rating'),
              'storeRatingTime': _translate('Store rating time')}

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

class SliderComponent(BaseComponent):
    """A class for presenting a rating scale as a builder component
    """
    categories = ['Responses', 'Custom']

    def __init__(self, exp, parentName,
                 name='slider',
                 labels='',
                 ticks="(1, 2, 3, 4, 5)",
                 size='1.0',
                 pos='0, -0.4',
                 flip=False,
                 style='rating',
                 granularity=0,
                 textSize=1.0,
                 color="LightGray",
                 font="HelveticaBold",
                 startType='time (s)', startVal='0.0',
                 stopType='condition', stopVal='',
                 startEstim='', durationEstim='',
                 forceEndRoutine=True,
                 marker='triangle',
                 storeRating=True, storeRatingTime=True, storeHistory=False,
                 style=''):
        super(SliderComponent, self).__init__(
            exp, parentName, name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)
        self.type = 'SliderComponent'
        self.url = "http://www.psychopy.org/builder/components/slidercomponent.html"
        self.exp.requirePsychopyLibs(['visual', 'event'])

        # params
        self.order = ['name', 'ticks','labels',
                      'markerStart', 'size', 'pos', 'tickHeight']

        # normal params:
        # = the usual as inherited from BaseVisual plus:
        self.params['labels'] = Param(
            labels, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[],  # categ="Advanced",
            hint=_translate("Labels for the tick marks on the scale, "
                            "separated by commas"),
            label=_localized['labels'])
        self.params['marker'] = Param(
            marker, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[],  # categ="Advanced",
            hint=_translate("Style for the marker"),
            label=_localized['marker'])
        self.params['forceEndRoutine'] = Param(
            forceEndRoutine, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[], categ="Advanced",
            hint=_translate("Should setting a rating (releasing the mouse) "
                            "cause the end of the routine (e.g. trial)?"),
            label=_localized['forceEndRoutine'])
        self.params['pos'] = Param(
            pos, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=_translate("x,y position on the screen"),
            label=_localized['pos'])
        self.params['size'] = Param(
            size, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=_translate("Size on screen. e.g. (500,10) pix for horizontal,"
                            "(10,500) pix for vertical"),
            label=_localized['size'])

        # advanced params:
        self.params['storeRating'] = Param(
            storeRating, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[], categ="Advanced",
            hint=_translate("store the rating"),
            label=_localized['storeRating'])
        self.params['storeRatingTime'] = Param(
            storeRatingTime, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[], categ="Advanced",
            hint=_translate("Store the time taken to make the choice (in "
                            "seconds)"),
            label=_localized['storeRatingTime'])
        self.params['storeHistory'] = Param(
            storeHistory, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[], categ="Advanced",
            hint=_translate("store the history of (selection, time)"),
            label=_localized['storeHistory'])

    def writeInitCode(self, buff):
        # build up an initialization string for RatingScale():
        _in = "%(name)s = visual.Slider(win=win, name='%(name)s'"
        init_str = _in % self.params
        init_str += ", size=%s" % self.params['size']
        s = str(self.params['pos'].val)
        s = s.lstrip('([ ').strip(')] ')
        try:
            pos = list(map(float, s.split(','))) * 2
            init_str += ", pos=%s" % pos[0:2]
        except Exception:
            pass  # pos = None

            init_str += ', labels=%s' % repr(
                self.params['labels'].val.split(','))
        # write the RatingScale() instantiation code:
        init_str += ")\n"
        buff.writeIndented(init_str)

    def writeRoutineStartCode(self, buff):
        buff.writeIndented("%(name)s.reset()\n" % (self.params))

    def writeFrameCode(self, buff):
        name = self.params['name']
        buff.writeIndented("# *%(name)s* updates\n" % (self.params))
        # try to handle blank start condition gracefully:
        if not self.params['startVal'].val.strip():
            self.params['startVal'].val = 0  # time, frame
            if self.params['startType'].val == 'condition':
                self.params['startVal'].val = 'True'

        self.writeStartTestCode(buff)
        buff.writeIndented("%(name)s.setAutoDraw(True)\n" % (self.params))
        buff.setIndentLevel(-1, relative=True)

        # handle a response:
        # if requested, force end of trial when the subject 'accepts' the
        # current rating:
        if self.params['forceEndRoutine'].val:
            code = ("continueRoutine &= %s.noResponse  "
                    "# a response ends the trial\n")
            buff.writeIndented(code % name)

        # for completeness: could handle going beyond
        # self.params['stopVal'].val with no response

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
                       "for ratingscale events so doesn't know what to "
                       "tell a StairHandler (or QuestHandler)\n")
                buff.writeIndented(msg)
            elif currLoop.type in ['TrialHandler', 'ExperimentHandler']:
                buff.writeIndented("# store data for %s (%s)\n" % (
                    currLoop.params['name'], currLoop.type))
                if self.params['storeRating'].val == True:
                    code = "%s.addData('%s.response', %s.getRating())\n"
                    buff.writeIndented(code % (currLoop.params['name'],
                                               name, name))
                if self.params['storeRatingTime'].val == True:
                    code = "%s.addData('%s.rt', %s.getRT())\n"
                    buff.writeIndented(code % (currLoop.params['name'],
                                               name, name))
                if self.params['storeHistory'].val == True:
                    code = "%s.addData('%s.history', %s.getHistory())\n"
                    buff.writeIndented(code % (currLoop.params['name'],
                                               name, name))
                if currLoop.params['name'].val == self.exp._expHandler.name:
                    buff.writeIndented("%s.nextEntry()\n" %
                                       self.exp._expHandler.name)
            else:
                buff.writeIndented("# RatingScaleComponent: unknown loop "
                                   "type, not saving any data.\n")
