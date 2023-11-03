#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path
from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals
from psychopy.localization import _translate


class ImageComponent(BaseVisualComponent):
    """An event class for presenting image-based stimuli"""

    categories = ['Stimuli']
    targets = ['PsychoPy', 'PsychoJS']
    iconFile = Path(__file__).parent / 'image.png'
    tooltip = _translate('Image: present images (bmp, jpg, tif...)')

    def __init__(self, exp, parentName, name='image', image='', mask='',
                 interpolate='linear', units='from exp settings',
                 color='$[1,1,1]', colorSpace='rgb', pos=(0, 0),
                 size=(0.5, 0.5), anchor="center", ori=0, texRes='128', flipVert=False,
                 flipHoriz=False,
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim=''):
        super(ImageComponent, self).__init__(
            exp, parentName, name=name, units=units,
            color=color, colorSpace=colorSpace,
            pos=pos, size=size, ori=ori,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)
        self.type = 'Image'
        self.url = "https://www.psychopy.org/builder/components/image.html"
        self.exp.requirePsychopyLibs(['visual'])
        # params
        self.order += ['image',  # Basic tab
                       'mask', 'texture resolution',  # Texture tab
                       ]

        msg = _translate(
            "The image to be displayed - a filename, including path")
        self.params['image'] = Param(
            image, valType='file', inputType="file", allowedTypes=[], categ='Basic',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Image"))

        msg = _translate(
            "An image to define the alpha mask through which the image is "
            "seen - gauss, circle, None or a filename (including path)")
        self.params['mask'] = Param(
            mask, valType='str', inputType="file", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Mask"))

        msg = _translate("Resolution of the mask if one is used.")
        self.params['texture resolution'] = Param(
            texRes, valType='num', inputType="choice", categ='Texture',
            allowedVals=['32', '64', '128', '256', '512'],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Texture resolution"))

        msg = _translate(
            "How should the image be interpolated if/when rescaled")
        self.params['interpolate'] = Param(
            interpolate, valType='str', inputType="choice", allowedVals=['linear', 'nearest'], categ='Texture',
            updates='constant', allowedUpdates=[],
            hint=msg, direct=False,
            label=_translate("Interpolate"))

        msg = _translate(
            "Should the image be flipped vertically (top to bottom)?")
        self.params['flipVert'] = Param(
            flipVert, valType='bool', inputType="bool", categ='Layout',
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Flip vertically"))

        msg = _translate(
            "Should the image be flipped horizontally (left to right)?")
        self.params['flipHoriz'] = Param(
            flipHoriz, valType='bool', inputType="bool", categ='Layout',
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Flip horizontally"))
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

        del self.params['fillColor']
        del self.params['borderColor']

    def writeInitCode(self, buff):
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        else:
            unitsStr = "units=%(units)s, " % self.params

        # replace variable params with defaults
        inits = getInitVals(self.params, 'PsychoPy')
        code = ("{inits[name]} = visual.ImageStim(\n"
                "    win=win,\n"
                "    name='{inits[name]}', {units}\n"
                "    image={inits[image]}, mask={inits[mask]}, anchor={inits[anchor]},\n"
                "    ori={inits[ori]}, pos={inits[pos]}, size={inits[size]},\n"
                "    color={inits[color]}, colorSpace={inits[colorSpace]}, opacity={inits[opacity]},\n"
                "    flipHoriz={inits[flipHoriz]}, flipVert={inits[flipVert]},\n"
                # no newline - start optional parameters
                "    texRes={inits[texture resolution]}"
                .format(inits=inits,
                        units=unitsStr))

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
            val = inits[paramName].val
            if val is True:
                inits[paramName] = 'true'
            elif val is False:
                inits[paramName] = 'false'
            elif val in [None, 'None', 'none', '', 'sin']:
                inits[paramName].valType = 'code'
                inits[paramName].val = 'undefined'

        code = ("{inits[name]} = new visual.ImageStim({{\n"
                "  win : psychoJS.window,\n"
                "  name : '{inits[name]}', {units}\n"
                "  image : {inits[image]}, mask : {inits[mask]},\n"
                "  anchor : {inits[anchor]},\n"
                "  ori : {inits[ori]}, pos : {inits[pos]}, size : {inits[size]},\n"
                "  color : new util.Color({inits[color]}), opacity : {inits[opacity]},\n"
                "  flipHoriz : {inits[flipHoriz]}, flipVert : {inits[flipVert]},\n"
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
