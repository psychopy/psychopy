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
iconFile = path.join(thisFolder, 'polygon.png')
tooltip = _translate('Polygon: any regular polygon (line, triangle, square'
                     '...circle)')

# only use _localized values for label values, nothing functional:
_localized = {'nVertices': _translate('Num. vertices'),
              'fillColorSpace': _translate('Fill color-space'),
              'fillColor': _translate('Fill color'),
              'lineColorSpace': _translate('Line color-space'),
              'lineColor': _translate('Line color'),
              'lineWidth': _translate('Line width'),
              'interpolate': _translate('Interpolate'),
              'size': _translate("Size [w,h]"),
              'shape': _translate("Shape")}


class PolygonComponent(BaseVisualComponent):
    """A class for presenting grating stimuli"""

    def __init__(self, exp, parentName, name='polygon', interpolate='linear',
                 units='from exp settings',
                 lineColor='$[1,1,1]', lineColorSpace='rgb', lineWidth=1,
                 fillColor='$[1,1,1]', fillColorSpace='rgb',
                 shape='triangle', nVertices=4,
                 pos=(0, 0), size=(0.5, 0.5), ori=0,
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim=''):
        super(PolygonComponent, self).__init__(
            exp, parentName, name=name, units=units,
            pos=pos, size=size, ori=ori,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Polygon'
        self.url = "http://www.psychopy.org/builder/components/polygon.html"
        self.exp.requirePsychopyLibs(['visual'])
        self.targets = ['PsychoPy', 'PsychoJS']
        self.order = ['shape', 'nVertices']
        self.depends = [  # allows params to turn each other off/on
            {"dependsOn": "shape",  # must be param name
             "condition": "=='regular polygon...'",  # val to check for
             "param": "nVertices",  # param property to alter
             "true": "enable",  # what to do with param if condition is True
             "false": "disable",  # permitted: hide, show, enable, disable
             }
        ]

        # params
        msg = _translate("How many vertices in your regular polygon?")
        self.params['nVertices'] = Param(
            nVertices, valType='int',
            updates='constant',
            allowedUpdates=['constant'],
            hint=msg,
            label=_localized['nVertices'])

        msg = _translate("What shape is this? With 'regular polygon...' you "
                         "can set number of vertices")
        self.params['shape'] = Param(
            shape, valType='str',
            allowedVals=["line", "triangle", "rectangle", "cross", "star",
                         "regular polygon..."],
            updates='constant',
            allowedUpdates=['constant'],
            hint=msg,
            label=_localized['shape'])

        msg = _translate("Choice of color space for the fill color "
                         "(rgb, dkl, lms, hsv)")
        self.params['fillColorSpace'] = Param(
            fillColorSpace,
            valType='str', allowedVals=['rgb', 'dkl', 'lms', 'hsv', 'rgb255'],
            updates='constant',
            hint=msg,
            label=_localized['fillColorSpace'], categ='Advanced')

        msg = _translate("Fill color of this shape; Right-click to bring up a"
                         " color-picker (rgb only)")
        self.params['fillColor'] = Param(
            fillColor, valType='str', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['fillColor'], categ='Advanced')

        msg = _translate("Choice of color space for the fill color "
                         "(rgb, dkl, lms, hsv)")
        self.params['lineColorSpace'] = Param(
            lineColorSpace, valType='str',
            allowedVals=['rgb', 'dkl', 'lms', 'hsv'],
            updates='constant',
            hint=msg,
            label=_localized['lineColorSpace'], categ='Advanced')

        msg = _translate("Line color of this shape; Right-click to bring"
                         " up a color-picker (rgb only)")
        self.params['lineColor'] = Param(
            lineColor, valType='str', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['lineColor'], categ='Advanced')

        msg = _translate("Width of the shape's line (always in pixels - this"
                         " does NOT use 'units')")
        self.params['lineWidth'] = Param(
            lineWidth, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['lineWidth'])

        msg = _translate(
            "How should the image be interpolated if/when rescaled")
        self.params['interpolate'] = Param(
            interpolate, valType='str', allowedVals=['linear', 'nearest'],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['interpolate'], categ='Advanced')

        msg = _translate(
            "Size of this stimulus [w,h]. Note that for a line only the "
            "first value is used, for triangle and rect the [w,h] is as "
            "expected,\n but for higher-order polygons it represents the "
            "[w,h] of the ellipse that the polygon sits on!! ")
        self.params['size'] = Param(
            size, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['size'])

        del self.params['color']
        del self.params['colorSpace']

    def writeInitCode(self, buff):
        # do we need units code?

        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        else:
            unitsStr = "units=%(units)s, " % self.params

        # replace variable params with defaults
        inits = getInitVals(self.params)
        if inits['size'].val in ['1.0', '1']:
            inits['size'].val = '[1.0, 1.0]'

        if self.params['shape'] == 'regular polygon...':
            vertices = self.params['nVertices']
        else:
            vertices = self.params['shape']
        if vertices in ['line', '2']:
            code = ("%s = visual.Line(\n" % inits['name'] +
                    "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                    "    start=(-%(size)s[0]/2.0, 0), end=(+%(size)s[0]/2.0, 0),\n" % inits)
        elif vertices in ['triangle', '3']:
            code = ("%s = visual.ShapeStim(\n" % inits['name'] +
                    "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                    "    vertices=[[-%(size)s[0]/2.0,-%(size)s[1]/2.0], [+%(size)s[0]/2.0,-%(size)s[1]/2.0], [0,%(size)s[1]/2.0]],\n" % inits)
        elif vertices in ['rectangle', '4']:
            code = ("%s = visual.Rect(\n" % inits['name'] +
                    "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                    "    width=%(size)s[0], height=%(size)s[1],\n" % inits)
        elif vertices in ['star']:
            code = ("%s = visual.ShapeStim(\n" % inits['name'] +
                    "    win=win, name='%s', vertices='star7',%s\n" % (inits['name'], unitsStr) +
                    "    size=%(size)s,\n" % inits)
        elif vertices in ['cross']:
            code = ("%s = visual.ShapeStim(\n" % inits['name'] +
                    "    win=win, name='%s', vertices='cross',%s\n" % (inits['name'], unitsStr) +
                    "    size=%(size)s,\n" % inits)
        else:
            code = ("%s = visual.Polygon(\n" % inits['name'] +
                    "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                    "    edges=%s," % str(inits['nVertices'].val) +
                    " size=%(size)s,\n" % inits)

        code += ("    ori=%(ori)s, pos=%(pos)s,\n"
                 "    lineWidth=%(lineWidth)s, lineColor=%(lineColor)s, lineColorSpace=%(lineColorSpace)s,\n"
                 "    fillColor=%(fillColor)s, fillColorSpace=%(fillColorSpace)s,\n"
                 "    opacity=%(opacity)s, " % inits)

        depth = -self.getPosInRoutine()
        code += "depth=%.1f, " % depth

        if self.params['interpolate'].val == 'linear':
            code += "interpolate=True)\n"
        else:
            code += "interpolate=False)\n"

        buff.writeIndentedLines(code)

    def writeInitCodeJS(self, buff):

        # Check for unsupported units
        if self.params['units'].val in ['from exp settings', 'cm', 'deg', 'degFlatPos', 'degFlat']:
            msg = "'{units}' units for your '{name}' shape is not currently supported for PsychoJS: " \
                  "switching units to 'height'."
            logging.warning(msg.format(units=self.params['units'].val,
                                       name=self.params['name'].val,))
            unitsStr = "'height'"
        else:
            unitsStr = self.params['units']

        # replace variable params with defaults
        inits = getInitVals(self.params)

        # check for NoneTypes
        for param in inits:
            if inits[param] in [None, 'None', 'none', '']:
                inits[param].val = 'undefined'

        if inits['size'].val in ['1.0', '1']:
            inits['size'].val = '[1.0, 1.0]'

        if self.params['shape'] == 'regular polygon...':
            vertices = self.params['nVertices']
        else:
            vertices = self.params['shape']

        # Temporary checks to catch use of unsupported shapes/polygons
        if vertices in ['cross', 'star']:
            msg = "{} shape is in development. Not currently supported in PsychoJS.".format(vertices)
            raise NotImplementedError(msg)

        elif self.params['shape'] == 'regular polygon...' and self.params['nVertices'].val not in ['2', '3', '4']:
            msg = ("Regular polygon is currently in development "
                   "and not yet supported in PsychoJS.".
                   format(vertices))
            raise NotImplementedError(msg)

        if vertices in ['line', '2']:
            code = ("{name} = new visual.ShapeStim ({{\n"
                    "  win: psychoJS.window, name: '{name}',\n"
                    "  units: {unitsStr},\n"
                    "  vertices: [[-{size}[0]/2.0, 0], [+{size}[0]/2.0, 0]],\n")
        elif vertices in ['triangle', '3']:
            code = ("{name} = new visual.ShapeStim ({{\n"
                    "  win: psychoJS.window, name: '{name}',\n"
                    "  units: {unitsStr},\n"
                    "  vertices: [[-{size}[0]/2.0, -{size}[1]/2.0], [+{size}[0]/2.0, -{size}[1]/2.0], [0, {size}[1]/2.0]],\n")
        elif vertices in ['rectangle', '4']:
            code = ("{name} = new visual.Rect ({{\n"
                    "  win: psychoJS.window, name: '{name}',\n"
                    "  units: {unitsStr},\n"
                    "  width: {size}[0], height: {size}[1],\n")

        depth = -self.getPosInRoutine()

        interpolate = 'true'
        if self.params['interpolate'].val != 'linear':
            interpolate = 'false'

        code += ("  ori: {ori}, pos: {pos},\n"
                 "  lineWidth: {lineWidth}, lineColor: new util.Color({lineColor}),\n"
                 "  fillColor: new util.Color({fillColor}),\n"
                 "  opacity: {opacity}, depth: {depth}, interpolate: {interpolate},\n"
                 "}});\n\n")

        buff.writeIndentedLines(code.format(name=inits['name'],
                                            unitsStr=unitsStr,
                                            lineWidth=inits['lineWidth'],
                                            size=inits['size'],
                                            ori=inits['ori'],
                                            pos=inits['pos'],
                                            lineColor=inits['lineColor'],
                                            fillColor=inits['fillColor'],
                                            opacity=inits['opacity'],
                                            depth=depth,
                                            interpolate=interpolate,
                                            ))
