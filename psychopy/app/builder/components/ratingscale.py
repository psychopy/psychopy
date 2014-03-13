# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path
from psychopy.app.builder.experiment import Param
import re

__author__ = 'Jeremy Gray'

thisFolder = path.abspath(path.dirname(__file__)) # the absolute path to the folder containing this path
iconFile = path.join(thisFolder, 'ratingscale.png')
tooltip = 'Rating scale: obtain numerical or categorical responses'

class RatingScaleComponent(BaseComponent):
    """A class for presenting a rating scale as a builder component"""
    categories = ['Responses','Custom']
    def __init__(self, exp, parentName,
                 name='rating',
                 scaleDescription='',
                 categoryChoices='',
                 visualAnalogScale=False,
                 low='1', high='7',
                 singleClick=False,
                 showAccept=True,
                 labels='',
                 size='1.0',
                 tickHeight='',
                 pos='0, -0.4',
                 startType='time (s)', startVal='0.0',
                 stopType='condition', stopVal='',
                 startEstim='', durationEstim='',
                 forceEndRoutine=True,
                 disappear=False,
                 marker='triangle',
                 markerStart='',
                 storeRating=True, storeRatingTime=True, storeHistory=False,
                 customize_everything=''
                 ):
        self.type='RatingScale'
        self.url="http://www.psychopy.org/builder/components/ratingscale.html"
        self.exp=exp
        self.parentName=parentName
        self.exp.requirePsychopyLibs(['visual', 'event'])

        #params
        self.order = ['name', 'visualAnalogScale', 'categoryChoices', 'scaleDescription',
                      'low', 'high', 'labels', 'markerStart', 'size', 'pos', 'tickHeight']
        self.params = {}

        # normal params:
        self.params['name'] = Param(name, valType='code', allowedTypes=[],
            hint="A rating scale only collects the response; it does not display the stimulus to be rated.",
            label="Name")
        self.params['startType']=Param(startType, valType='str',
            allowedVals=['time (s)', 'frame N', 'condition'],
            hint="How do you want to define your start point?")
        self.params['stopType']=Param(stopType, valType='str',
            allowedVals=['duration (s)', 'duration (frames)', 'time (s)', 'frame N', 'condition'],
            hint="How do you want to define your end point?")
        self.params['startVal']=Param(startVal, valType='code', allowedTypes=[],
            hint="When does the rating scale start being shown?")
        self.params['stopVal']=Param(stopVal, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="How long to wait for a response (blank is forever)")
        self.params['startEstim']=Param(startEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected start (s) of stimulus, purely for representing in the timeline")
        self.params['durationEstim']=Param(durationEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected duration (s) of stimulus, purely for representing in the timeline")
        self.params['visualAnalogScale'] = Param(visualAnalogScale, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Show a continuous visual analog scale; returns 0.00 to 1.00; takes precedence over numeric scale or categorical choices",
            label="Visual analog scale")
        self.params['categoryChoices'] = Param(categoryChoices, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="A list of categories (non-numeric alternatives) to present, space or comma-separated; these take precedence over a numeric scale",
            label="Category choices")
        self.params['scaleDescription'] = Param(scaleDescription, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Brief instructions, such as a description of the scale numbers as seen by the subject.",
            label="Scale description")
        self.params['low'] = Param(low, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[], hint="Lowest rating (low end of the scale); not used for categories.",
            label="Low")
        self.params['high'] = Param(high, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[], hint="Highest rating (top end of the scale); not used for categories.",
            label="High")
        self.params['labels'] = Param(labels, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[], #categ="Advanced",
            hint="Labels for the ends of the scale, separated by commas")
        self.params['marker'] = Param(marker, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[], #categ="Advanced",
            hint="Style for the marker: triangle, circle, glow, slider, hover")
        self.params['markerStart'] = Param(markerStart, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[], #categ="Advanced",
            hint="initial position for the marker")

        # advanced params:
        self.params['singleClick'] = Param(singleClick, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[], categ="Advanced",
            hint="Should clicking the line accept that rating (without needing to confirm via 'accept')?")
        self.params['disappear'] = Param(disappear, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[], categ="Advanced",
            hint="Hide the scale when a rating has been accepted; False to remain on-screen")
        self.params['showAccept'] = Param(showAccept, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[], categ="Advanced",
            hint="Should the accept button by visible?")
        self.params['storeRating'] = Param(storeRating, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[], categ="Advanced",
            hint="store the rating")
        self.params['storeRatingTime'] = Param(storeRatingTime, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[], categ="Advanced",
            hint="store the time taken to make the choice (in seconds)")
        self.params['storeHistory'] = Param(storeHistory, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[], categ="Advanced",
            hint="store the history of (selection, time)")
        self.params['forceEndRoutine'] = Param(forceEndRoutine, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[], categ="Advanced",
            hint="Should accepting a rating cause the end of the routine (e.g. trial)?")
        self.params['size'] = Param(size, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[], categ="Advanced",
            hint="Relative size on the screen; size > 1 is larger than default; size < 1 is smaller")
        self.params['tickHeight'] = Param(tickHeight, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[], categ="Advanced",
            hint="height of tick marks (1 is upward, 0 is hidden, -1 is downward)")
        self.params['pos'] = Param(pos, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[], categ="Advanced",
            hint="x,y position on the screen")

        # customization:
        self.params['customize_everything'] = Param(customize_everything, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[], categ="Custom",
            hint="Use this text to create the rating scale as you would in a code component; overrides all"
                " dialog settings except time parameters, forceEndRoutine, storeRatingTime, storeRating")

    def writeInitCode(self, buff):
        # build up an initialization string for RatingScale():
        init_str = "%(name)s = visual.RatingScale(win=win, name='%(name)s'" % (self.params)
        if self.params['customize_everything'].val.strip() != '':
            # clean it up a little, remove win=*, leading / trailing typos
            self.params['customize_everything'].val = re.sub(r"[\\s,]*win=[^,]*,", '', self.params['customize_everything'].val)
            init_str += ', ' + self.params['customize_everything'].val.lstrip('(, ').strip('), ')
        else:
            if self.params['marker'].val:
                init_str += ', marker=%s' % repr(self.params['marker'].val)
                if self.params['marker'].val == 'glow':
                    init_str += ', markerExpansion=5'
            init_str += ", size=%s" % self.params['size']
            s = str(self.params['pos'].val)
            s = s.lstrip('([ ').strip(')] ')
            try:
                pos = map(float, s.split(',')) * 2
                init_str += ", pos=%s" % pos[0:2]
            except:
                pass # pos = None

            # type of scale:
            choices = unicode(self.params['categoryChoices'].val)
            if self.params['visualAnalogScale'].val:
                init_str += ", low=0, high=1, precision=100, marker='glow', showValue=False, markerExpansion=0"
            elif len(choices):
                if ',' in choices:
                    ch_list = choices.split(',')
                else:
                    ch_list = choices.split(' ')
                ch_list = [c.strip().strip(', ').lstrip(', ') for c in ch_list]
                init_str += ', choices=%s, tickHeight=' % unicode(ch_list)
                if self.params['tickHeight'].val:
                    init_str += "%s" % self.params['tickHeight'].val
                else:
                    init_str += "-1"
            else:
                # try to add low as int; but might be a var instead
                try:
                    init_str += ', low=%d' % int(self.params['low'].val)
                except ValueError:
                    if self.params['low'].val:
                        init_str += ", low=%s" % self.params['low']
                try:
                    init_str += ', high=%d' % int(self.params['high'].val)
                except ValueError:
                    if self.params['high'].val:
                        init_str += ", high=%s" % self.params['high']
                init_str += ', labels=%s' % repr(self.params['labels'].val.split(','))

            if not len(choices) and len(unicode(self.params['scaleDescription'])):
                init_str += ", scale=%s" % self.params['scaleDescription']
            if self.params['singleClick'].val:
                init_str += ", singleClick=True"
            if self.params['disappear'].val:
                init_str += ", disappear=True"
            if self.params['markerStart'].val:
                init_str += ", markerStart=%s" % self.params['markerStart']
            if not len(choices) and self.params['tickHeight'].val:
                init_str += ", tickHeight=%s" % self.params['markerStart']
            if not self.params['showAccept'].val:
                init_str += ", showAccept=False"
        # write the RatingScale() instantiation code:
        init_str += ")\n"
        buff.writeIndented(init_str)

    def writeRoutineStartCode(self, buff):
        buff.writeIndented("%(name)s.reset()\n" % (self.params))

    def writeFrameCode(self, buff):
        name = self.params['name']
        buff.writeIndented("# *%(name)s* updates\n" %(self.params))
        # try to handle blank start condition gracefully:
        if not self.params['startVal'].val.strip():
            self.params['startVal'].val = 0 # time, frame
            if self.params['startType'].val == 'condition':
                self.params['startVal'].val = 'True'
        if self.params['startType'].val == 'frame N':
            buff.writeIndented("if frameN > %(startVal)s:\n" % self.params)
        elif self.params['startType'].val == 'condition':
            buff.writeIndented("if %(startVal)s:\n" % self.params)
        else: # self.params['startType'].val == 'time (s)':
            buff.writeIndented("if t > %(startVal)s:\n" % self.params)
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("%(name)s.draw()\n" % (self.params))
        # if requested, force end of trial when the subject 'accepts' the current rating:
        if self.params['forceEndRoutine'].val:
            buff.writeIndented("continueRoutine = %s.noResponse\n" % (name))
        # only need to do the following the first time it goes False, here gets set every frame:
        buff.writeIndented("if %s.noResponse == False:\n" % name)
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("%s.response = %s.getRating()\n" % (name, name));
        if self.params['storeRatingTime'].val:
            buff.writeIndented("%s.rt = %s.getRT()\n" % (name, name));
        buff.setIndentLevel(-2, relative=True)

    def writeRoutineEndCode(self, buff):
        name = self.params['name']
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1] # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler

        #write the actual code
        if self.params['storeRating'].val or self.params['storeRatingTime'].val:
            if currLoop.type in ['StairHandler', 'QuestHandler']:
                buff.writeIndented("# NB PsychoPy doesn't handle a 'correct answer' for ratingscale " +
                               "events so doesn't know what to tell a StairHandler (or QuestHandler)\n")
            elif currLoop.type in ['TrialHandler', 'ExperimentHandler']:
                buff.writeIndented("# store data for %s (%s)\n" %(currLoop.params['name'], currLoop.type))
                if self.params['storeRating'].val == True:
                    buff.writeIndented("%s.addData('%s.response', %s.getRating())\n" \
                                       % (currLoop.params['name'], name, name))
                if self.params['storeRatingTime'].val == True:
                    buff.writeIndented("%s.addData('%s.rt', %s.getRT())\n" \
                                       % (currLoop.params['name'], name, name))
                if self.params['storeHistory'].val == True:
                    buff.writeIndented("%s.addData('%s.history', %s.getHistory())\n" \
                                       % (currLoop.params['name'], name, name))
                if currLoop.params['name'].val == self.exp._expHandler.name:
                    buff.writeIndented("%s.nextEntry()\n" % self.exp._expHandler.name)
            else:
                buff.writeIndented("# RatingScaleComponent: unknown loop type, not saving any data.\n")
