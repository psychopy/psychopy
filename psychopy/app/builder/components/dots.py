# Part of the PsychoPy library
# Copyright (C) 2011 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _visual import *
from os import path

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'dots.png')
tooltip = 'Random Dot Kinematogram'

class DotsComponent(VisualComponent):
    """An event class for presenting Random Dot stimuli"""
    def __init__(self, exp, parentName, name='dots',
                nDots=100,
                direction=0.0, speed=0.1, coherence=1.0,
                dotSize=1.0,
                dotlife=3, signalDots='different', noiseDots='direction',
                fieldShape='circle', fieldSize=1.0, fieldPos=[0.0,0.0],
                color='$[1.0,1.0,1.0]',colorSpace='rgb',
                opacity=1.0,
                units='window units',
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                startEstim='', durationEstim=''):
        #initialise main parameters from base stimulus
        VisualComponent.__init__(self,parentName,name=name, units=units,
                    color=color, colorSpace=colorSpace,
                    startType=startType, startVal=startVal,
                    stopType=stopType, stopVal=stopVal,
                    startEstim=startEstim, durationEstim=durationEstim)
        self.type='Dots'
        self.url="http://www.psychopy.org/builder/components/dots.html"
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['visual'])
        self.parentName=parentName
        #params
        self.params['advancedParams']=['signalDots','noiseDots']
        self.params['name']=Param(name, valType='code', allowedTypes=[])
        self.params['n dots']=Param(nDots, valType='code',
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Number of dots in the field (for circular fields this will be average number of dots)")
        self.params['direction']=Param(direction, valType='code',
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Direction of motion for the signal dots (degrees)")
        self.params['speed']=Param(speed, valType='code',
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Speed of the dots (displacement per frame in the specified units)")
        self.params['coherence']=Param(coherence, valType='code',
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Coherence of the dots (fraction moving in the signal direction on any one frame)")
        self.params['dotSize']=Param(dotSize, valType='code',
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Size of the dots IN PIXELS regardless of the set units")
        self.params['dotlife']=Param(dotlife, valType='code',
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Number of frames before each dot is killed and randomly assigned a new position")
        self.params['signalDots']=Param(signalDots, valType='str', allowedVals=['same','different'],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Are the signal dots the same population as the noise dot? See Scase et al.")
        self.params['noiseDots']=Param(noiseDots, valType='str', allowedVals=['direction','position','walk'],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="What governs the behaviour of the noise dots? See Scase et al.")
        self.params['fieldShape']=Param(fieldShape, valType='str', allowedVals=['circle','square'],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="What is the shape of the field?")
        self.params['fieldSize']=Param(fieldSize, valType='code',
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="What is the size of the field (in the specified units)?")
        self.params['fieldPos']=Param(fieldPos, valType='code',
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Where is the field centred (in the specified units)?")
        del self.params['size']#should be fieldSize
        del self.params['pos']#should be fieldPos
        del self.params['ori']#should be dir for dots

    def writeInitCode(self,buff):
        #do we need units code?
        if self.params['units'].val=='window units': unitsStr=""
        else: unitsStr="units=%(units)s, " %self.params
        #do writing of init
        inits = getInitVals(self.params)#replaces variable params with sensible defaults
        buff.writeIndented("%(name)s=visual.DotStim(win=win, ori=%(ori)s, name='%(name)s',\n" %(inits))
        buff.writeIndented("    color=%(color)s, colorSpace=%(colorSpace)s)\n" %(inits))
