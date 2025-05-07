#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path
from psychopy.experiment.components import BaseVisualComponent, Param, \
    getInitVals, _translate


class GratingComponent(BaseVisualComponent):
    """A class for presenting grating stimuli"""

    categories = ['Stimuli']
    targets = ['PsychoPy', 'PsychoJS']
    iconFile = Path(__file__).parent / 'grating.png'
    tooltip = _translate('Grating: present cyclic textures, prebuilt or from a '
                         'file')

    def __init__(self, exp, parentName, name='grating', image='sin',
                 mask='', sf='', interpolate='linear',
                 units='from exp settings', color='$[1,1,1]', colorSpace='rgb',
                 contrast=1.0, pos=(0, 0), size=(0.5, 0.5), anchor="center",
                 ori=0, phase=0.0, texRes='128', draggable=False,
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0, blendmode='avg',
                 startEstim='', durationEstim=''):
        super(GratingComponent, self).__init__(
            exp, parentName, name=name, units=units,
            color=color, colorSpace=colorSpace, contrast=contrast,
            pos=pos, size=size, ori=ori,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Grating'
        self.url = "https://www.psychopy.org/builder/components/grating.html"
        self.order += [
            'tex', 'mask', 'phase', 'sf', 'texture resolution', 'interpolate',  # Texture tab
        ]

        # params
        msg = _translate("The (2D) texture of the grating - can be sin, sqr,"
                         " sinXsin... or a filename (including path)")
        self.params['tex'] = Param(
            image, valType='file', inputType="file", allowedVals=["sin", "sqr", "sinXsin"], allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Texture"))

        msg = _translate("An image to define the alpha mask (ie shape)- "
                         "gauss, circle... or a filename (including path)")
        self.params['mask'] = Param(
            mask, valType='file', inputType="file", allowedVals=["gauss", "circle"], allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Mask"))

        msg = _translate("Spatial frequency of image repeats across the "
                         "grating in 1 or 2 dimensions, e.g. 4 or [2,3]")
        self.params['sf'] = Param(
            sf, valType='num', inputType="single",  allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Spatial frequency"))

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
            label=_translate("Draggable?"),
            hint=_translate(
                "Should this stimulus be moveble by clicking and dragging?"
            )
        )

        msg = _translate("Spatial positioning of the image on the grating "
                         "(wraps in range 0-1.0)")
        self.params['phase'] = Param(
            phase, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Phase (in cycles)"))

        msg = _translate(
            "Resolution of the texture for standard ones such as sin, sqr "
            "etc. For most cases a value of 256 pixels will suffice")
        self.params['texture resolution'] = Param(
            texRes,
            valType='num', inputType="choice", allowedVals=['32', '64', '128', '256', '512'], categ='Texture',
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Texture resolution"))

        msg = _translate("How should the image be interpolated if/when "
                         "rescaled")
        self.params['interpolate'] = Param(
            interpolate, valType='str', inputType="choice", allowedVals=['linear', 'nearest'], categ='Texture',
            updates='constant', allowedUpdates=[],
            hint=msg, direct=False,
            label=_translate("Interpolate"))

        msg = _translate("OpenGL Blendmode: avg gives traditional transparency,"
                         " add is important to combine gratings)]")
        self.params['blendmode'] = Param(
            blendmode, valType='str', inputType="choice", allowedVals=['avg', 'add'], categ='Appearance',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("OpenGL blend mode"))

        del self.params['fillColor']
        del self.params['borderColor']

    def writeInitCode(self, buff):
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        else:
            unitsStr = "units=%(units)s, " % self.params

        # replaces variable params with defaults
        inits = getInitVals(self.params)
        code = ("%s = visual.GratingStim(\n" % inits['name'] +
                "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                "    tex=%(tex)s, mask=%(mask)s, anchor=%(anchor)s,\n" % inits +
                "    ori=%(ori)s, pos=%(pos)s, draggable=%(draggable)s, size=%(size)s, " % inits +
                "sf=%(sf)s, phase=%(phase)s,\n" % inits +
                "    color=%(color)s, colorSpace=%(colorSpace)s,\n" % inits +
                "    opacity=%(opacity)s, contrast=%(contrast)s, blendmode=%(blendmode)s,\n" % inits +
                # no newline - start optional parameters
                "    texRes=%(texture resolution)s" % inits)

        if self.params['interpolate'].val == 'linear':
            code += ", interpolate=True"
        else:
            code += ", interpolate=False"
        depth = -self.getPosInRoutine()
        code += ", depth=%.1f)\n" % depth
        buff.writeIndentedLines(code)

    def writeInitCodeJS(self, buff):
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = "units : undefined, "
        else:
            unitsStr = "units : %(units)s, " % self.params

        # replace variable params with defaults
        inits = getInitVals(self.params, 'PsychoJS')

        for paramName in inits:
            if inits[paramName].val in [None, 'None', 'none', '', 'sin']:
                inits[paramName].valType = 'code'
                inits[paramName].val = 'undefined'

        code = ("{inits[name]} = new visual.GratingStim({{\n"
                "  win : psychoJS.window,\n"
                "  name : '{inits[name]}', {units}\n"
                "  tex : {inits[tex]}, mask : {inits[mask]},\n"
                "  ori : {inits[ori]}, \n"
                "  pos : {inits[pos]},\n"
                "  draggable: {inits[draggable]},\n"
                "  anchor : {inits[anchor]},\n"
                "  sf : {inits[sf]}, phase : {inits[phase]},\n"
                "  size : {inits[size]},\n"
                "  color : new util.Color({inits[color]}), opacity : {inits[opacity]},\n"
                "  contrast : {inits[contrast]}, blendmode : {inits[blendmode]},\n"
                # no newline - start optional parameters
                "  texRes : {inits[texture resolution]}"
                .format(inits=inits,
                        units=unitsStr))

        if self.params['interpolate'].val == 'linear':
            code += ", interpolate : true"
        else:
            code += ", interpolate : false"

        depth = -self.getPosInRoutine()
        code += (", depth : %.1f \n"
                 "});\n" % (depth)
                 )
        buff.writeIndentedLines(code)
