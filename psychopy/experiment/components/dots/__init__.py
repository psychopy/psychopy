#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from os import path
from pathlib import Path
from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals, _translate


class DotsComponent(BaseVisualComponent):
    """An event class for presenting Random Dot stimuli"""

    categories = ['Stimuli']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'dots.png'
    tooltip = _translate('Dots: Random Dot Kinematogram')

    def __init__(self, exp, parentName, name='dots',
                 nDots=100,
                 direction=0.0, speed=0.1, coherence=1.0,
                 dotSize=2,
                 dotLife=3, signalDots='same', noiseDots='direction', refreshDots='repeat',
                 fieldShape='circle', fieldSize=1.0, fieldAnchor="center", fieldPos=(0.0, 0.0),
                 color='$[1.0,1.0,1.0]', colorSpace='rgb',
                 opacity="",
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
        self.url = "https://www.psychopy.org/builder/components/dots.html"
        # Put dot/field size and position where regular size and position are in param order
        self.order.insert(self.order.index("size"), "dotSize")
        self.order.insert(self.order.index("size"), "fieldSize")
        self.order.insert(self.order.index("pos"), "fieldPos")
        self.order += [
            "nDots", "dir", "speed"  # Dots tab
        ]

        # params
        msg = _translate("Number of dots in the field (for circular fields"
                         " this will be average number of dots)")
        self.params['nDots'] = Param(
            nDots, valType='int', inputType="spin", categ='Dots',
            updates='constant',
            hint=msg,
            label=_translate("Number of dots"))

        msg = _translate("Direction of motion for the signal dots (degrees)")
        self.params['dir'] = Param(
            direction, valType='num', inputType="spin", categ='Dots',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Direction"))

        msg = _translate("Speed of the dots (displacement per frame in the"
                         " specified units)")
        self.params['speed'] = Param(
            speed, valType='num', inputType="single", categ='Dots',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Speed"))

        msg = _translate("Coherence of the dots (fraction moving in the "
                         "signal direction on any one frame)")
        self.params['coherence'] = Param(
            coherence, valType='num', inputType="single", categ='Dots',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Coherence"))

        msg = _translate("Size of the dots IN PIXELS regardless of "
                         "the set units")
        self.params['dotSize'] = Param(
            dotSize, valType='num', inputType="spin", categ='Layout',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Dot size"))

        msg = _translate("Number of frames before each dot is killed and "
                         "randomly assigned a new position")
        self.params['dotLife'] = Param(
            dotLife, valType='num', inputType="spin", categ='Dots',
            hint=msg,
            label=_translate("Dot life-time"))

        msg = _translate("On each frame are the signals dots remaining "
                         "the same or changing? See Scase et al.")
        self.params['signalDots'] = Param(
            signalDots, valType='str', inputType="choice", allowedVals=['same', 'different'], categ='Dots',
            hint=msg,
            label=_translate("Signal dots"))
            
        msg = _translate("When should the whole sample of dots be refreshed")
        self.params['refreshDots'] = Param(
            refreshDots, valType='str', inputType="choice", allowedVals=['none', 'repeat'], categ='Dots',
            allowedUpdates=[],
            hint=msg, direct=False,
            label=_translate("Dot refresh rule"))
            

        msg = _translate("What governs the behaviour of the noise dots? "
                         "See Scase et al.")
        self.params['noiseDots'] = Param(
            noiseDots, valType='str', inputType="choice", categ='Dots',
            allowedVals=['direction', 'position', 'walk'],
            hint=msg,
            label=_translate("Noise dots"))

        self.params['fieldShape'] = Param(
            fieldShape, valType='str', inputType="choice", allowedVals=['circle', 'square'], categ='Layout',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=_translate("What is the shape of the field?"),
            label=_translate("Field shape"))

        msg = _translate("What is the size of the field "
                         "(in the specified units)?")
        self.params['fieldSize'] = Param(
            fieldSize, valType='num', inputType="single", categ='Layout',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Field size"))

        msg = _translate(
            "Where is the field centred (in the specified units)?")
        self.params['fieldPos'] = Param(
            fieldPos, valType='list', inputType="single", categ='Layout',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Field position"))

        self.params['anchor'] = Param(
            fieldAnchor, valType='str', inputType="choice", categ='Layout',
            allowedVals=['center',
                         'top-center',
                         'bottom-center',
                         'center-left',
                         'center-right',
                         'top-left',
                         'top-right',
                         'bottom-left',
                         'bottom-right',
                         ],
            updates='constant',
            hint=_translate("Which point on the field should be anchored to its exact position?"),
            label=_translate("Field anchor"))

        # Reword colour parameters
        self.params['color'].label = _translate("Dot color")
        self.params['colorSpace'].label = _translate("Dot color space")

        del self.params['size']  # should be fieldSize
        del self.params['pos']  # should be fieldPos
        del self.params['ori']  # should be dir for dots
        del self.params['fillColor']
        del self.params['borderColor']

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
                "    fieldPos=%(fieldPos)s, fieldSize=%(fieldSize)s, fieldAnchor=%(anchor)s, fieldShape=%(fieldShape)s,\n" % inits +
                "    signalDots=%(signalDots)s, noiseDots=%(noiseDots)s,dotLife=%(dotLife)s,\n" % inits +
                "    color=%(color)s, colorSpace=%(colorSpace)s, opacity=%(opacity)s,\n" % inits +
                "    depth=%.1f)\n" % depth)
        buff.writeIndentedLines(code)

    def writeRoutineStartCode(self,buff):
        super(DotsComponent, self).writeRoutineStartCode(buff)
        if self.params['refreshDots'].val in ['repeat', 'Repeat']:
            buff.writeIndented("%(name)s.refreshDots()\n" %self.params)
