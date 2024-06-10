#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path

from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals, _translate
from psychopy import logging


class PolygonComponent(BaseVisualComponent):
    """A class for presenting grating stimuli"""

    categories = ['Stimuli']
    targets = ['PsychoPy', 'PsychoJS']
    iconFile = Path(__file__).parent / 'polygon.png'
    tooltip = _translate('Polygon: any regular polygon (line, triangle, square'
                         '...circle)')

    def __init__(self, exp, parentName, name='polygon', interpolate='linear',
                 units='from exp settings', anchor='center',
                 lineColor='white', lineColorSpace='rgb', lineWidth=1,
                 fillColor='white', fillColorSpace='rgb',
                 shape='triangle', nVertices=4, vertices="",
                 pos=(0, 0), size=(0.5, 0.5), ori=0,
                 draggable=False,
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim=''):
        super(PolygonComponent, self).__init__(
            exp, parentName, name=name, units=units,
            fillColor=fillColor, borderColor=lineColor,
            pos=pos, size=size, ori=ori,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Polygon'
        self.url = "https://www.psychopy.org/builder/components/polygon.html"
        self.exp.requirePsychopyLibs(['visual'])
        self.order += ['shape', 'nVertices',  # Basic tab
                      ]
        self.order.insert(self.order.index("borderColor"), "lineColor")
        self.depends = [  # allows params to turn each other off/on
            {"dependsOn": "shape",  # must be param name
             "condition": "=='regular polygon...'",  # val to check for
             "param": "nVertices",  # param property to alter
             "true": "show",  # what to do with param if condition is True
             "false": "hide",  # permitted: hide, show, enable, disable
             },
            {"dependsOn": "shape",  # must be param name
             "condition": "=='custom polygon...'",  # val to check for
             "param": "vertices",  # param property to alter
             "true": "show",  # what to do with param if condition is True
             "false": "hide",  # permitted: hide, show, enable, disable
             },
        ]

        # params
        msg = _translate("How many vertices in your regular polygon?")
        self.params['nVertices'] = Param(
            nVertices, valType='int', inputType="single", categ='Basic',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Num. vertices"))

        msg = _translate("What are the vertices of your polygon? Should be an nx2 array or a list of [x, y] lists")
        self.params['vertices'] = Param(
            vertices, valType='list', inputType='single', categ='Basic',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Vertices")
        )
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
            hint=_translate("Which point on the stimulus should be anchored to its exact position?"),
            label=_translate("Anchor"))
        self.params['draggable'] = Param(
            draggable, valType="code", inputType="bool", categ="Layout",
            updates="constant",
            label="Draggable?",
            hint=_translate(
                "Should this stimulus be moveble by clicking and dragging?"
            )
        )

        msg = _translate("What shape is this? With 'regular polygon...' you "
                         "can set number of vertices and with 'custom "
                         "polygon...' you can set vertices")
        self.params['shape'] = Param(
            shape, valType='str', inputType="choice", categ='Basic',
            allowedVals=["line", "triangle", "rectangle", "circle", "cross", "star7", "arrow",
                         "regular polygon...", "custom polygon..."],
            allowedLabels=["Line", "Triangle", "Rectangle", "Circle", "Cross", "Star", "Arrow",
                           "Regular polygon...", "Custom polygon..."],
            hint=msg, direct=False,
            label=_translate("Shape"))

        self.params['lineColor'] = self.params['borderColor']
        del self.params['borderColor']

        msg = _translate("Width of the shape's line (always in pixels - this"
                         " does NOT use 'units')")
        self.params['lineWidth'] = Param(
            lineWidth, valType='num', inputType="single", allowedTypes=[], categ='Appearance',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Line width"))

        msg = _translate(
            "How should the image be interpolated if/when rescaled")
        self.params['interpolate'] = Param(
            interpolate, valType='str', inputType="choice", allowedVals=['linear', 'nearest'], categ='Texture',
            updates='constant', allowedUpdates=[], direct=False,
            hint=msg,
            label=_translate("Interpolate"))


        self.params['size'].hint = _translate(
            "Size of this stimulus [w,h]. Note that for a line only the "
            "first value is used, for triangle and rect the [w,h] is as "
            "expected,\n but for higher-order polygons it represents the "
            "[w,h] of the ellipse that the polygon sits on!! ")

        del self.params['color']

    def writeInitCode(self, buff):
        # do we need units code?

        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        else:
            unitsStr = "units=%(units)s, " % self.params

        # handle dependent params
        params = self.params.copy()
        if params['shape'] == 'regular polygon...':
            params['shape'] = params['nVertices']
        elif params['shape'] == 'custom polygon...':
            params['shape'] = params['vertices']

        # replace variable params with defaults
        inits = getInitVals(params)
        if inits['size'].val in ['1.0', '1']:
            inits['size'].val = '[1.0, 1.0]'
        vertices = inits['shape']
        if vertices in ['line', '2']:
            code = ("%s = visual.Line(\n" % inits['name'] +
                    "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                    "    size=%(size)s,\n" % inits)
        elif vertices in ['triangle', '3']:
            code = ("%s = visual.ShapeStim(\n" % inits['name'] +
                    "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                    "    size=%(size)s, vertices='triangle',\n" % inits)
        elif vertices in ['rectangle', '4']:
            code = ("%s = visual.Rect(\n" % inits['name'] +
                    "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                    "    width=%(size)s[0], height=%(size)s[1],\n" % inits)
        elif vertices in ['circle', '100']:
            code = ("%s = visual.ShapeStim(\n" % inits['name'] +
                    "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                    "    size=%(size)s, vertices='circle',\n" % inits)
        elif vertices in ['star', 'star7']:
            code = ("%s = visual.ShapeStim(\n" % inits['name'] +
                    "    win=win, name='%s', vertices='star7',%s\n" % (inits['name'], unitsStr) +
                    "    size=%(size)s,\n" % inits)
        elif vertices in ['cross']:
            code = ("%s = visual.ShapeStim(\n" % inits['name'] +
                    "    win=win, name='%s', vertices='cross',%s\n" % (inits['name'], unitsStr) +
                    "    size=%(size)s,\n" % inits)
        elif self.params['shape'] == 'regular polygon...':
            code = ("%s = visual.Polygon(\n" % inits['name'] +
                    "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                    "    edges=%s," % str(inits['nVertices'].val) +
                    " size=%(size)s,\n" % inits)
        else:
            code = ("%s = visual.ShapeStim(\n" % inits['name'] +
                    "    win=win, name='%s', vertices=%s,%s\n" % (inits['name'], vertices, unitsStr) +
                    "    size=%(size)s,\n" % inits)

        code += ("    ori=%(ori)s, pos=%(pos)s, draggable=%(draggable)s, anchor=%(anchor)s,\n"
                 "    lineWidth=%(lineWidth)s, "
                 "    colorSpace=%(colorSpace)s,  lineColor=%(lineColor)s, fillColor=%(fillColor)s,\n"
                 "    opacity=%(opacity)s, " % inits)

        depth = -self.getPosInRoutine()
        code += "depth=%.1f, " % depth

        if self.params['interpolate'].val == 'linear':
            code += "interpolate=True)\n"
        else:
            code += "interpolate=False)\n"

        buff.writeIndentedLines(code)

    def writeInitCodeJS(self, buff):

        inits = getInitVals(self.params)

        # Check for unsupported units
        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        elif inits['units'].val in ['cm', 'deg', 'degFlatPos', 'degFlat']:
            msg = "'{units}' units for your '{name}' shape is not currently supported for PsychoJS: " \
                  "switching units to 'height'."
            logging.warning(msg.format(units=inits['units'].val,
                                       name=self.params['name'].val,))
            unitsStr = "units : 'height', "
        else:
            unitsStr = "units : %(units)s, " % self.params

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

        if vertices in ['line', '2']:
            code = ("{name} = new visual.ShapeStim ({{\n"
                    "  win: psychoJS.window, name: '{name}', {unitsStr}\n"
                    "  vertices: [[-{size}[0]/2.0, 0], [+{size}[0]/2.0, 0]],\n")
        elif vertices in ['triangle', '3']:
            code = ("{name} = new visual.ShapeStim ({{\n"
                    "  win: psychoJS.window, name: '{name}', {unitsStr}\n"
                    "  vertices: [[-{size}[0]/2.0, -{size}[1]/2.0], [+{size}[0]/2.0, -{size}[1]/2.0], [0, {size}[1]/2.0]],\n")
        elif vertices in ['rectangle', '4']:
            code = ("{name} = new visual.Rect ({{\n"
                    "  win: psychoJS.window, name: '{name}', {unitsStr}\n"
                    "  width: {size}[0], height: {size}[1],\n")
        elif vertices in ['circle', '100']:
            code = ("{name} = new visual.Polygon({{\n"
                    "  win: psychoJS.window, name: '{name}', {unitsStr}\n"
                    "  edges: 100, size:{size},\n")
        elif vertices in ['star']:
            code = ("{name} = new visual.ShapeStim ({{\n"
                    "  win: psychoJS.window, name: '{name}', {unitsStr}\n"
                    "  vertices: 'star7', size: {size},\n")
        elif vertices in ['cross']:
            code = ("{name} = new visual.ShapeStim ({{\n"
                    "  win: psychoJS.window, name: '{name}', {unitsStr}\n"
                    "  vertices: 'cross', size:{size},\n")
        elif vertices in ['arrow']:
            code = ("{name} = new visual.ShapeStim ({{\n"
                    "  win: psychoJS.window, name: '{name}', {unitsStr}\n"
                    "  vertices: 'arrow', size:{size},\n")
        elif self.params['shape'] == 'regular polygon...':
            code = ("{name} = new visual.Polygon ({{\n"
                    "  win: psychoJS.window, name: '{name}', {unitsStr}\n"
                    "  edges: {nVertices}, size:{size},\n")
        else:
            code = ("{name} = new visual.ShapeStim({{\n" +
                    "  win: psychoJS.window, name: '{name}', {unitsStr}\n"
                    "  vertices: {vertices}, size: {size},\n")

        depth = -self.getPosInRoutine()

        interpolate = 'true'
        if self.params['interpolate'].val != 'linear':
            interpolate = 'false'

        code += ("  ori: {ori}, \n"
                 "  pos: {pos}, \n"
                 "  draggable: {draggable}, \n"
                 "  anchor: {anchor},\n"
                 "  lineWidth: {lineWidth}, \n"
                 "  colorSpace: {colorSpace},\n")      

        if inits['lineColor'] == 'undefined':
            code +=  "  lineColor: {lineColor},\n"
        else:    
            code +=  "  lineColor: new util.Color({lineColor}),\n"

        if inits['fillColor'] == 'undefined':
            code +=  "  fillColor: {fillColor},\n"
        else:    
            code +=  "  fillColor: new util.Color({fillColor}),\n"


        code += (        "  fillColor: {fillColor},\n"
                 "  opacity: {opacity}, depth: {depth}, interpolate: {interpolate},\n"
                 "}});\n\n")

        buff.writeIndentedLines(code.format(name=inits['name'],
                                            unitsStr=unitsStr,
                                            anchor=inits['anchor'],
                                            lineWidth=inits['lineWidth'],
                                            size=inits['size'],
                                            ori=inits['ori'],
                                            pos=inits['pos'],
                                            colorSpace=inits['colorSpace'],
                                            lineColor=inits['lineColor'],
                                            fillColor=inits['fillColor'],
                                            opacity=inits['opacity'],
                                            depth=depth,
                                            interpolate=interpolate,
                                            nVertices=inits['nVertices'],
                                            vertices=inits['vertices'],
                                            draggable=inits['draggable']
                                            ))
