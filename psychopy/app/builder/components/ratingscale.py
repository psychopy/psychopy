# Part of the PsychoPy library
# Copyright (C) 2011 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path
from psychopy.app.builder.experiment import Param
from psychopy.app.builder import inf # infinity
import re

__author__ = 'Jeremy Gray'

thisFolder = path.abspath(path.dirname(__file__)) # the absolute path to the folder containing this path
iconFile = path.join(thisFolder, 'ratingscale.png')

class RatingScaleComponent(BaseComponent):
    """A class for presenting a rating scale as a builder component"""
    def __init__(self, exp, parentName,
                 name='rating',
                 scaleDescription='',
                 categoryChoices='',
                 visualAnalogScale=False,
                 low=1, high=7,
                 size=1.0,
                 pos='0, -0.4',
                 startTime=0, duration='',
                 forceEndTrial=True,
                 storeRating=True, storeRatingTime=True,
                 lowAnchorText='', highAnchorText='',
                 customize_everything=''
                 ):
        self.type='RatingScale'
        self.url="http://www.psychopy.org/builder/components/ratingscale.html"
        self.exp=exp
        self.exp.requirePsychopyLibs(['visual', 'event'])
        
        #params
        self.order = ['name', 'visualAnalogScale', 'categoryChoices', 'scaleDescription', 'low', 'high', 'size']
        self.params = {} 
        self.params['advancedParams'] = ['startTime', 'forceEndTrial', 'size',
                        'pos', 'duration', 'storeRatingTime', 'storeRating', 'lowAnchorText', 'highAnchorText', 'customize_everything']
        
        # normal params:
        self.params['name'] = Param(name, valType='code', allowedTypes=[],
            hint="A rating scale only collects the response; it does not display the stimulus to be rated.")
        self.params['visualAnalogScale'] = Param(visualAnalogScale, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Show a continuous visual analog scale; returns 0.00 to 1.00; takes precedence over numeric scale or categorical choices")
        self.params['categoryChoices'] = Param(categoryChoices, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="A list of categories (non-numeric alternatives) to present, space or comma-separated; these take precedence over a numeric scale")
        self.params['scaleDescription'] = Param(scaleDescription, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Brief instructions, such as a description of the scale numbers as seen by the subject.")
        self.params['low'] = Param(low, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[], hint="Lowest rating (low end of the scale); not used for categories.")
        self.params['high'] = Param(high, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[], hint="Highest rating (top end of the scale); not used for categories.")
        
        # advanced params:
        self.params['size'] = Param(size, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Relative size on the screen; size > 1 is larger than default; size < 1 is smaller")
        self.params['storeRating'] = Param(storeRating, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="store the rating")
        self.params['storeRatingTime'] = Param(storeRatingTime, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="store the time taken to make the choice (in seconds)")
        self.params['pos'] = Param(pos, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[], hint="x,y position on the screen")
        self.params['duration'] = Param(duration, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="How many seconds to wait for a response; leave blank for 'forever'")
        self.params['forceEndTrial'] = Param(forceEndTrial, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Should accepting a rating cause the end of the routine (e.g. trial)?")
        self.params['lowAnchorText'] = Param(lowAnchorText, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Description of the low end of the scale")
        self.params['highAnchorText'] = Param(highAnchorText, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Description of the high end of the scale")
        self.params['customize_everything'] = Param(customize_everything, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Use this text to create the rating scale as you would in a code component; OVERRIDES ALL other settings")
        
        # required (?)
        self.params['startTime'] = Param(0.0, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[], hint="")
        
    def writeInitCode(self, buff):
        # Builder-code set-up:
        try:
            f = float(self.params['duration'].val)
            if f < 0 or self.params['forceEndTrial']:
                self.params['duration'].val = inf
        except:
            self.params['duration'].val = str(inf)
        
        # build up an initialization string for RatingScale():
        init_str = "%(name)s=visual.RatingScale(win=win" % (self.params)
        if self.params['customize_everything'].val.strip() != '':
            # clean it up a little, remove win=*, leading / trailing typos
            self.params['customize_everything'].val = re.sub(r"[\\s,]*win=[^,]*,", '', self.params['customize_everything'].val)
            init_str += ', ' + self.params['customize_everything'].val.lstrip().lstrip('(').lstrip(',').strip().strip(')').strip(',')
        else:
            init_str += ", escapeKeys=['escape']"
            # size:
            try: s = float(self.params['size'].val) 
            except: s = 1.0
            init_str += ", displaySizeFactor=%.2f" % s
            
            # position: x -> (x,x); x,y -> (x,y)
            try:
                s = str(self.params['pos'].val)
                s = s.lstrip().lstrip('(').lstrip('[').strip().strip('(').strip('[')
                pos = map(float, s.split(',')) * 2
                init_str += ",\n    pos=%s" % pos[0:2]
            except:
                pass # pos = None
                
            # type of scale:
            choices = str(self.params['categoryChoices'].val).strip().strip(',').lstrip().lstrip(',')
            scaleDescription = str(self.params['scaleDescription'].val)
            if self.params['visualAnalogScale'].val:
                if self.params['lowAnchorText'].val == '': self.params['lowAnchorText'].val = '0%'
                if self.params['highAnchorText'].val == '': self.params['highAnchorText'].val = '100%'
                init_str += ", low=0, high=1, showScale=False, lowAnchorText='"+self.params['lowAnchorText'].val+"', highAnchorText='"+self.params['highAnchorText'].val+"'"
                init_str += ",\n    precision=100, markerStyle='glow', showValue=False, markerExpansion=0"
            elif len(choices):
                if choices.find(',') > -1:
                    ch_list = choices.split(',')
                else:
                    ch_list = choices.split(' ')
                ch_list = [c.strip().strip(',').lstrip().lstrip(',') for c in ch_list]
                init_str += ', choices=' + str(ch_list)
            if not len(choices) and len(str(scaleDescription)):
                init_str += ", scale='" + str(scaleDescription) +"'"
        
        # write the RatingScale() instantiation code:
        init_str += ")\n"
        buff.writeIndented(init_str)
        
    def writeRoutineStartCode(self, buff):
        buff.writeIndented("%(name)s.reset()\n" % (self.params)) 
    
    def writeFrameCode(self, buff):
        name = self.params['name']
        buff.writeIndented("%(name)s.draw()\n" % (self.params))
        # if requested, force end of trial when the subject 'accepts' the current rating:
        if self.params['forceEndTrial']:
            continueName = self.exp.flow._currentRoutine._continueName
            buff.writeIndented("%s = %s.noResponse\n" % (continueName, name))
        # only need to do the following the first time it goes False, here gets set every frame:
        buff.writeIndented("if %s.noResponse == False:\n" % name)
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("%s.response = %s.getRating()\n" % (name, name));
        if self.params['storeRatingTime'].val:
            buff.writeIndented("%s.rt = %s.getRT()\n" % (name, name)); 
        buff.setIndentLevel(-1, relative=True)
    
    def writeRoutineEndCode(self, buff):
        name = self.params['name']
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1] # last (outer-most) loop
        else:
            currLoop = None
        
        #write the actual code
        if currLoop and (self.params['storeRating'].val or self.params['storeRatingTime'].val):
            if currLoop.type in ['StairHandler', 'QuestHandler']:
                buff.writeIndented("#NB PsychoPy doesn't handle a 'correct answer' for ratingscale " +
                               "events so doesn't know what to tell a StairHandler (or QuestHandler)")
            elif currLoop.type == 'TrialHandler': 
                if self.params['storeRating'].val == True:
                    buff.writeIndented("%s.addData('%s.response', %s.getRating())\n" \
                                       % (currLoop.params['name'], name, name))
                if self.params['storeRatingTime'].val == True:
                    buff.writeIndented("%s.addData('%s.rt', %s.getRT())\n" \
                                       % (currLoop.params['name'], name, name))
            else:
                buff.writeIndented("#RatingScaleComponent: unknown loop type, not saving any data.")
  
