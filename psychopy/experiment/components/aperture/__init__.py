#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path

from psychopy.experiment import Param
from psychopy.experiment.components import getInitVals, _translate
from psychopy.experiment.components.polygon import PolygonComponent

__author__ = 'Jeremy Gray, Jon Peirce'
# March 2011; builder-component for Yuri Spitsyn's visual.Aperture class
# July 2011: jwp added the code for it to be enabled only when needed


class ApertureComponent(PolygonComponent):
    """An event class for using GL stencil to restrict the viewing area to a
    circle or square of a given size and position"""

    categories = ['Stimuli']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'aperture.png'
    label = _translate("Aperture")
    tooltip = _translate('Aperture: restrict the drawing of stimuli to a given '
                         'region')

    def __init__(self, exp, parentName, name='aperture', units='norm',
                 size=1, pos=(0, 0), anchor="center", ori=0,
                 shape='triangle', nVertices=4, vertices="",
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim=''):
        # initialise main parameters
        super(ApertureComponent, self).__init__(
            exp, parentName, name=name, units=units,
            pos=pos, size=size, ori=ori,
            shape=shape, nVertices=nVertices, vertices=vertices,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Aperture'
        self.url = "https://www.psychopy.org/builder/components/aperture.html"
        self.order += []

        msg = _translate(
            "How big is the aperture? (a single number for diameter)")
        self.params['size'].hint = msg

        self.params['anchor'] = Param(
            anchor, valType='str', inputType="choice", categ='Layout',
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
            hint=_translate("Which point on the aperture should be anchored to its exact position?"),
            label=_translate("Anchor"))

        # only localize hints and labels
        self.params['size'].label = _translate("Size")
        self.params['pos'].hint = _translate("Where is the aperture centred?")

        # Remove Polygon params which are not needed
        del self.params['colorSpace']
        del self.params['fillColor']
        del self.params['lineColor']
        del self.params['lineWidth']
        del self.params['contrast']
        del self.params['opacity']
        del self.params['interpolate']

    def writeInitCode(self, buff):
        # do writing of init
        inits = getInitVals(self.params)
        inits['depth'] = -self.getPosInRoutine()

        # additional substitutions
        if self.params['units'].val == 'from exp settings':
            inits['units'].val = None

        if self.params['shape'] == 'regular polygon...':
            inits['vertices'] = self.params['nVertices']
        elif self.params['shape'] != 'custom polygon...':
            inits['vertices'] = self.params['shape']

        code = (
            "%(name)s = visual.Aperture(\n"
        )
        buff.writeIndentedLines(code % inits)

        buff.setIndentLevel(1, relative=True)
        code = (
                "win=win, name='%(name)s',\n"
                "units=%(units)s, size=%(size)s, pos=%(pos)s, ori=%(ori)s,\n"
                "shape=%(vertices)s, anchor=%(anchor)s\n,"
                "depth=%(depth)s\n"
        )
        buff.writeIndentedLines(code % inits)

        buff.setIndentLevel(-1, relative=True)
        code = (
                ")\n"
                "%(name)s.disable()  # disable until its actually used\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeFrameCode(self, buff):
        """Only activate the aperture for the required frames
        """
        params = self.params
        code = (f"\n"
                f"# *{params['name']}* updates\n")
        buff.writeIndented(code)
        # writes an if statement to determine whether to draw etc
        indented = self.writeStartTestCode(buff)
        if indented:
            buff.writeIndented("%(name)s.enabled = True\n" % self.params)
        # to get out of the if statement
        buff.setIndentLevel(-indented, relative=True)
        indented = self.writeStopTestCode(buff)
        if indented:
            buff.writeIndented("%(name)s.enabled = False\n" % self.params)
        # to get out of the if statement
        buff.setIndentLevel(-indented, relative=True)
        # set parameters that need updating every frame
        # do any params need updating? (this method inherited from _base)
        if self.checkNeedToUpdate('set every frame'):
            code = ("if %(name)s.status == STARTED:  # only update if being  drawn\n")
            buff.writeIndented(code % self.params)

            buff.setIndentLevel(+1, relative=True)  # to enter the if block
            self.writeParamUpdates(buff, 'set every frame')
            buff.setIndentLevel(-1, relative=True)  # to exit the if block

    def writeRoutineEndCode(self, buff):
        msg = "%(name)s.enabled = False  # just in case it was left enabled\n"
        buff.writeIndented(msg % self.params)

        # get parent to write code too (e.g. store onset/offset times)
        super().writeRoutineEndCode(buff)
