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
# iconFile = path.join(thisFolder, 'polygon.png')
tooltip = _translate('Pen: a drawing tool')

# only use _localized values for label values, nothing functional:
_localized = {'nStrokes': _translate('Num. strokes'),
              'lineColorSpace': _translate('Line color-space'),
              'lineColor': _translate('Line color'),
              'lineWidth': _translate('Line width'),
              'opacity': _translate('Opacity'),
              }

class PenComponent(BaseVisualComponent):
    """A class for drawing freehand responses"""

    categories = ['Responses', 'Custom']

    def __init__(self, exp, parentName, name='pen',
                 nStrokes=100,
                 lineColor='$[1,1,1]', lineColorSpace='rgb', lineWidth=1.5,
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim=''):
        super(PenComponent, self).__init__(
            exp, parentName, name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Pen'
        self.url = "http://www.psychopy.org/builder/components/pen.html"
        self.exp.requirePsychopyLibs(['visual'])
        self.targets = ['PsychoPy', 'PsychoJS']
        self.order = ['nStrokes', 'lineWidth', 'lineColor', 'opacity']

        del self.params['color']  # because color is defined by lineColor
        del self.params['colorSpace']  # because color is defined by lineColor
        del self.params['size']  # because size determined by lineWidth
        del self.params['ori']
        del self.params['pos']
        del self.params['units']  # always in pix

        # params
        msg = _translate("How many individual strokes can your pen make?")
        self.params['nStrokes'] = Param(
            nStrokes, valType='int',
            updates='constant',
            allowedUpdates=['constant'],
            hint=msg,
            label=_localized['nStrokes'])

        msg = _translate("Line color of this pen; Right-click to bring"
                         " up a color-picker (rgb only)")
        self.params['lineColor'] = Param(
            lineColor, valType='str', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['lineColor'], categ='Advanced')

        msg = _translate("Width of the pen's line (always in pixels - this"
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
        code = ("{name} = visual.Pen(win=win, name='{name}',\n"
                "   nStrokes={nStrokes},\n"
                "   lineWidth={lineWidth},\n"
                "   lineColor={lineColor},\n"
                "   lineColorSpace={lineColorSpace},\n"
                "   opacity={opacity})").format(name=self.params['name'],
                                                nStrokes=self.params['nStrokes'],
                                                lineWidth=self.params['lineWidth'],
                                                lineColor=self.params['lineColor'],
                                                lineColorSpace=self.params['lineColorSpace'],
                                                opacity=self.params['opacity'])
        buff.writeIndentedLines(code)

