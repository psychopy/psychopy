#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from os import path
from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals, _translate

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'dots.png')
tooltip = _translate('Dots: Random Dot Kinematogram')
# only use _localized values for label values, nothing functional:
_localized = {'nDots': _translate('Number of dots'),
              'dir': _translate('Direction'),
              'speed': _translate('Speed'),
              'coherence': _translate('Coherence'),
              'dotSize': _translate('Dot size'),
              'dotLife': _translate('Dot life-time'),
              'signalDots': _translate('Signal dots'),
              'noiseDots': _translate('Noise dots'),
              'fieldShape': _translate('Field shape'),
              'fieldSize': _translate('Field size'),
              'fieldPos': _translate('Field position'),
              'refreshDots':_translate('Dot refresh rule')}


class DotsComponent(BaseVisualComponent):
    """An event class for presenting Random Dot stimuli"""

    def __init__(self, exp, parentName, name='dots',
                 nDots=100,
                 direction=0.0, speed=0.1, coherence=1.0,
                 dotSize=2,
                 dotLife=3, signalDots='same', noiseDots='direction', refreshDots='repeat',
                 fieldShape='circle', fieldSize=1.0, fieldPos=(0.0, 0.0),
                 color='$[1.0,1.0,1.0]', colorSpace='rgb',
                 opacity=1.0,
                 units='from exp settings',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim=''):
        super(DotsComponent, self).__init__(
            exp, parentName, name=name, units=units,
            color=color, colorSpace=colorSpace,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Dots'
        self.url = "http://www.psychopy.org/builder/components/dots.html"

        # params
        msg = _translate("Number of dots in the field (for circular fields"
                         " this will be average number of dots)")
        self.params['nDots'] = Param(
            nDots, valType='code',
            updates='constant',
            hint=msg,
            label=_localized['nDots'], categ='Dots')

        msg = _translate("Direction of motion for the signal dots (degrees)")
        self.params['dir'] = Param(
            direction, valType='code',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['dir'], categ='Dots')

        msg = _translate("Speed of the dots (displacement per frame in the"
                         " specified units)")
        self.params['speed'] = Param(
            speed, valType='code',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['speed'], categ='Dots')

        msg = _translate("Coherence of the dots (fraction moving in the "
                         "signal direction on any one frame)")
        self.params['coherence'] = Param(
            coherence, valType='code',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['coherence'], categ='Dots')

        msg = _translate("Size of the dots IN PIXELS regardless of "
                         "the set units")
        self.params['dotSize'] = Param(
            dotSize, valType='code',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['dotSize'], categ='Dots')

        msg = _translate("Number of frames before each dot is killed and "
                         "randomly assigned a new position")
        self.params['dotLife'] = Param(
            dotLife, valType='code',
            hint=msg,
            label=_localized['dotLife'], categ='Dots')

        msg = _translate("On each frame are the signals dots remaining "
                         "the same or changing? See Scase et al.")
        self.params['signalDots'] = Param(
            signalDots, valType='str', allowedVals=['same', 'different'],
            hint=msg,
            label=_localized['signalDots'], categ='Dots')
            
        msg = _translate("When should the whole sample of dots be refreshed")
        self.params['refreshDots'] = Param(
            refreshDots, valType='str', allowedVals=['none', 'repeat'],
            allowedUpdates=[],
            hint=msg,
            label=_localized['refreshDots'], categ='Dots')
            

        msg = _translate("What governs the behaviour of the noise dots? "
                         "See Scase et al.")
        self.params['noiseDots'] = Param(
            noiseDots, valType='str',
            allowedVals=['direction', 'position', 'walk'],
            hint=msg,
            label=_localized['noiseDots'], categ='Dots')

        self.params['fieldShape'] = Param(
            fieldShape, valType='str', allowedVals=['circle', 'square'],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=_translate("What is the shape of the field?"),
            label=_localized['fieldShape'])

        msg = _translate("What is the size of the field "
                         "(in the specified units)?")
        self.params['fieldSize'] = Param(
            fieldSize, valType='code',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['fieldSize'])

        msg = _translate(
            "Where is the field centred (in the specified units)?")
        self.params['fieldPos'] = Param(
            fieldPos, valType='code',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['fieldPos'])

        del self.params['size']  # should be fieldSize
        del self.params['pos']  # should be fieldPos
        del self.params['ori']  # should be dir for dots

    def writeInitCode(self, buff):
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        else:
            unitsStr = "units=%(units)s, " % self.params
        # do writing of init
        # replaces variable params with sensible defaults
        inits = getInitVals(self.params)
        depth = -self.getPosInRoutine()

        code = ("%s = visual.DotStim(\n" % inits['name'] +
                "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                "    nDots=%(nDots)s, dotSize=%(dotSize)s,\n" % inits +
                "    speed=%(speed)s, dir=%(dir)s, coherence=%(coherence)s,\n" % inits +
                "    fieldPos=%(fieldPos)s, fieldSize=%(fieldSize)s,fieldShape=%(fieldShape)s,\n" % inits +
                "    signalDots=%(signalDots)s, noiseDots=%(noiseDots)s,dotLife=%(dotLife)s,\n" % inits +
                "    color=%(color)s, colorSpace=%(colorSpace)s, opacity=%(opacity)s,\n" % inits +
                "    depth=%.1f)\n" % depth)
        buff.writeIndentedLines(code)

    def writeRoutineStartCode(self,buff):
        super(DotsComponent, self).writeRoutineStartCode(buff)
        if self.params['refreshDots'].val in ['repeat', 'Repeat']:
            buff.writeIndented("%(name)s.refreshDots()\n" %self.params)
