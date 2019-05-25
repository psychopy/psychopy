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
                 lineColor='$[1,1,1]', lineColorSpace='rgb',
                 lineWidth=1.5, opacity=1,
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
            allowedUpdates=['constant', 'set every repeat'],
            hint=msg,
            label=_localized['lineColor'], categ='Advanced')

        msg = _translate("Width of the brush's line (always in pixels and limited to 10px max width)")
        self.params['lineWidth'] = Param(
            lineWidth, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat'],
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

        msg = _translate("The line opacity")
        self.params['opacity'] = Param(
            opacity, valType='str',
            allowedVals=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat'],
            hint=msg,
            label=_localized['opacity'])

    def writeInitCode(self, buff):
        params = getInitVals(self.params)
        code = ("{name} = visual.Brush(win=win, name='{name}',\n"
                "   lineWidth={lineWidth},\n"
                "   lineColor={lineColor},\n"
                "   lineColorSpace={lineColorSpace},\n"
                "   opacity={opacity})").format(name=params['name'],
                                                lineWidth=params['lineWidth'],
                                                lineColor=params['lineColor'],
                                                lineColorSpace=params['lineColorSpace'],
                                                opacity=params['opacity'])
        buff.writeIndentedLines(code)

    def writeInitCodeJS(self, buff):
        # JS code does not use Brush class
        params = getInitVals(self.params)
        code = ("get{name} = function() {{\n"
                "  new visual.ShapeStim({{\n"
                "    win: psychoJS.window,\n"
                "    vertices: [[0, 0]],\n"
                "    lineWidth: {lineWidth},\n"
                "    lineColor: new util.Color({lineColor}),\n"
                "    opacity: {opacity},\n"
                "    closeShape: false,\n"
                "    autoDraw: true,\n"
                "    autoLog: false\n"
                "    }})\n"
                "}}\n\n").format(name=params['name'],
                                 lineWidth=params['lineWidth'],
                                 lineColor=params['lineColor'],
                                 opacity=params['opacity'])

        buff.writeIndentedLines(code)
        # add reset function
        code = ("{name}Reset = function() {{\n"
                "  if ({name}Shapes.length > 0) {{\n"
                "    for (let shape of {name}Shapes) {{\n"
                "      shape.setAutoDraw(false);\n"
                "    }}\n"
                "  }}\n"
                "  {name}AtStartPoint = false;\n"
                "  {name}Shapes = [];\n"
                "}}\n\n").format(name=params['name'])
        buff.writeIndentedLines(code)

        # Define vars for drawing
        code = ("{name}CurrentShape = 0;\n"
                "{name}BrushDown = false;\n"
                "{name}Pointer = new core.Mouse({{win: psychoJS.window}});\n"
                "{name}AtStartPoint = false;\n"
                "{name}Shapes = [];\n").format(name=params['name'])
        buff.writeIndentedLines(code)
        #
        # TODO: add onBrushDown, currentShape and onBrushDrag functions for HS
        #

    def writeRoutineStartCode(self, buff):
        # Write update code
        super(BrushComponent, self).writeRoutineStartCode(buff)
        # Reset shapes for each trial
        buff.writeIndented("{}.reset()\n".format(self.params['name']))
