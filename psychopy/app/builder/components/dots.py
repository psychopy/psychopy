# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _visual import *
from psychopy.app.builder import components #for getInitVals()
from os import path

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'dots.png')
tooltip = _translate('Dots: Random Dot Kinematogram')
# only use _localized values for label values, nothing functional:
_localized = {'nDots': _translate('Number of dots'), 'dir': _translate('Direction'),
              'speed': _translate('Speed'), 'coherence': _translate('Coherence'),
              'dotSize': _translate('Dot size'), 'dotLife': _translate('Dot life-time'),
              'signalDots': _translate('Signal dots'), 'noiseDots': _translate('Noise dots'),
              'fieldShape': _translate('Field shape'), 'fieldSize': _translate('Field size'),
              'fieldPos': _translate('Field position')
              }

class DotsComponent(VisualComponent):
    """An event class for presenting Random Dot stimuli"""
    def __init__(self, exp, parentName, name='dots',
                nDots=100,
                direction=0.0, speed=0.1, coherence=1.0,
                dotSize=2,
                dotLife=3, signalDots='same', noiseDots='direction',
                fieldShape='circle', fieldSize=1.0, fieldPos=[0.0,0.0],
                color='$[1.0,1.0,1.0]',colorSpace='rgb',
                opacity=1.0,
                units='from exp settings',
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                startEstim='', durationEstim=''):
        #initialise main parameters from base stimulus
        super(DotsComponent, self).__init__(exp,parentName,name=name, units=units,
                    color=color, colorSpace=colorSpace,
                    startType=startType, startVal=startVal,
                    stopType=stopType, stopVal=stopVal,
                    startEstim=startEstim, durationEstim=durationEstim)
        self.type='Dots'
        self.url="http://www.psychopy.org/builder/components/dots.html"

        #params
        self.params['nDots']=Param(nDots, valType='code',
            updates='constant',
            hint=_translate("Number of dots in the field (for circular fields this will be average number of dots)"),
            label=_localized['nDots'], categ='Dots')
        self.params['dir']=Param(direction, valType='code',
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint=_translate("Direction of motion for the signal dots (degrees)"),
            label=_localized['dir'], categ='Dots')
        self.params['speed']=Param(speed, valType='code',
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint=_translate("Speed of the dots (displacement per frame in the specified units)"),
            label=_localized['speed'], categ='Dots')
        self.params['coherence']=Param(coherence, valType='code',
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint=_translate("Coherence of the dots (fraction moving in the signal direction on any one frame)"),
            label=_localized['coherence'], categ='Dots')
        self.params['dotSize']=Param(dotSize, valType='code',
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint=_translate("Size of the dots IN PIXELS regardless of the set units"),
            label=_localized['dotSize'], categ='Dots')
        self.params['dotLife']=Param(dotLife, valType='code',
            hint=_translate("Number of frames before each dot is killed and randomly assigned a new position"),
            label=_localized['dotLife'], categ='Dots')
        self.params['signalDots']=Param(signalDots, valType='str', allowedVals=['same','different'],
            hint=_translate("On each frame are the signals dots remaining the same or changing? See Scase et al."),
            label=_localized['signalDots'], categ='Dots')
        self.params['noiseDots']=Param(noiseDots, valType='str', allowedVals=['direction','position','walk'],
            hint=_translate("What governs the behaviour of the noise dots? See Scase et al."),
            label=_localized['noiseDots'], categ='Dots')
        self.params['fieldShape']=Param(fieldShape, valType='str', allowedVals=['circle','square'],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint=_translate("What is the shape of the field?"),
            label=_localized['fieldShape'])
        self.params['fieldSize']=Param(fieldSize, valType='code',
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint=_translate("What is the size of the field (in the specified units)?"),
            label=_localized['fieldSize'])
        self.params['fieldPos']=Param(fieldPos, valType='code',
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint=_translate("Where is the field centred (in the specified units)?"),
            label=_localized['fieldPos'])
        del self.params['size']#should be fieldSize
        del self.params['pos']#should be fieldPos
        del self.params['ori']#should be dir for dots

    def writeInitCode(self,buff):
        #do we need units code?
        if self.params['units'].val=='from exp settings': unitsStr=""
        else: unitsStr="units=%(units)s, " %self.params
        #do writing of init
        inits = components.getInitVals(self.params)#replaces variable params with sensible defaults
        depth = -self.getPosInRoutine()
        buff.writeIndented("%s = visual.DotStim(win=win, name='%s',%s\n" %(inits['name'], inits['name'],unitsStr))
        buff.writeIndented("    nDots=%(nDots)s, dotSize=%(dotSize)s,\n" %(inits))
        buff.writeIndented("    speed=%(speed)s, dir=%(dir)s, coherence=%(coherence)s,\n" %(inits))
        buff.writeIndented("    fieldPos=%(fieldPos)s, fieldSize=%(fieldSize)s,fieldShape=%(fieldShape)s,\n" %(inits))
        buff.writeIndented("    signalDots=%(signalDots)s, noiseDots=%(noiseDots)s,dotLife=%(dotLife)s,\n" %(inits))
        buff.writeIndented("    color=%(color)s, colorSpace=%(colorSpace)s, opacity=%(opacity)s," %(inits))
        buff.writeIndented("    depth=%.1f)\n" %(depth))
