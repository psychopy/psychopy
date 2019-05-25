#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from builtins import str
from os import path
from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals, _translate
from psychopy import logging

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'brush.png')
tooltip = _translate('Brush: a drawing tool')

# only use _localized values for label values, nothing functional:
_localized = {'lineColorSpace': _translate('Line color-space'),
              'lineColor': _translate('Line color'),
              'lineWidth': _translate('Line width'),
              'opacity': _translate('Opacity'),
              }

class BrushComponent(BaseVisualComponent):
    """A class for drawing freehand responses"""

    categories = ['Responses', 'Custom']

    def __init__(self, exp, parentName, name='brush',
                 lineColor='$[1,1,1]', lineColorSpace='rgb', lineWidth=1.5,
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim=''):
        super(BrushComponent, self).__init__(
            exp, parentName, name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Brush'
        self.url = "http://www.psychopy.org/builder/components/brush.html"
        self.exp.requirePsychopyLibs(['visual'])
        self.targets = ['PsychoPy', 'PsychoJS']
        self.order = ['lineWidth', 'lineColor', 'opacity']

        del self.params['color']  # because color is defined by lineColor
        del self.params['colorSpace']  # because color is defined by lineColor
        del self.params['size']  # because size determined by lineWidth
        del self.params['ori']
        del self.params['pos']
        del self.params['units']  # always in pix

        # params
        msg = _translate("Line color of this brush; Right-click to bring"
                         " up a color-picker (rgb only)")
        self.params['lineColor'] = Param(
            lineColor, valType='str', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['lineColor'], categ='Advanced')

        msg = _translate("Width of the brush's line (always in pixels - this"
                         " does NOT use 'units')")
        self.params['lineWidth'] = Param(
            lineWidth, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['lineWidth'])

        msg = _translate("Choice of color space for the fill color "
                         "(rgb, dkl, lms, hsv)")
        self.params['lineColorSpace'] = Param(
            lineColorSpace, valType='str',
            allowedVals=['rgb', 'dkl', 'lms', 'hsv'],
            updates='constant',
            hint=msg,
            label=_localized['lineColorSpace'], categ='Advanced')

    def writeInitCode(self, buff):
        code = ("{name} = visual.Brush(win=win, name='{name}',\n"
                "   lineWidth={lineWidth},\n"
                "   lineColor={lineColor},\n"
                "   lineColorSpace={lineColorSpace},\n"
                "   opacity={opacity})").format(name=self.params['name'],
                                                lineWidth=self.params['lineWidth'],
                                                lineColor=self.params['lineColor'],
                                                lineColorSpace=self.params['lineColorSpace'],
                                                opacity=self.params['opacity'])
        buff.writeIndentedLines(code)


    def writeRoutineStartCode(self, buff):
        pass