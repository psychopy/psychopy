#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path
from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals, _translate


class PatchComponent(BaseVisualComponent):
    """An event class for presenting image-based stimuli"""

    categories = ['Stimuli']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'patch.png'
    tooltip = _translate('Patch: present images (bmp, jpg, tif...) or textures '
                         'like gratings')

    def __init__(self, exp, parentName, name='patch', image='sin', mask='None',
                 sf='None', interpolate='linear',
                 units='from exp settings', color='$[1,1,1]', colorSpace='rgb',
                 pos=(0, 0), size=(0.5, 0.5), ori=0, phase=0.0, texRes='128',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim=''):
        super(PatchComponent, self).__init__(
            exp, parentName, name=name, units=units,
            color=color, colorSpace=colorSpace,
            pos=pos, size=size, ori=ori,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Patch'
        self.url = "https://www.psychopy.org/builder/components/patch.html"
        # params

        msg = _translate("The image to be displayed - 'sin','sqr'... or a "
                         "filename (including path)")
        self.params['image'] = Param(
            image, valType='file', inputType="file", allowedTypes=[], categ='Basic',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Image/tex"))

        msg = _translate("An image to define the alpha mask (ie shape)- "
                         "gauss, circle... or a filename (including path)")
        self.params['mask'] = Param(
            mask, valType='str', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Mask"))

        msg = _translate("Spatial frequency of image repeats across the "
                         "patch, e.g. 4 or [2,3]")
        self.params['sf'] = Param(
            sf, valType='list', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Spatial frequency"))

        msg = _translate(
            "Spatial positioning of the image on the patch (in range 0-1.0)")
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
            hint=msg,
            label=_translate("Interpolate"))

    def writeInitCode(self, buff):
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        else:
            unitsStr = "units=%(units)s, " % self.params
        # replaces variable params with defaults
        inits = getInitVals(self.params)

        code = ("%s = visual.PatchStim(\n" % inits['name'] +
                "    win=win, name='%s',%s\n" % (inits['name'], unitsStr))

        code += ("    tex=%(image)s, mask=%(mask)s,\n"
                 "    ori=%(ori)s, pos=%(pos)s, size=%(size)s, sf=%(sf)s, phase=%(phase)s,\n"
                 "    color=%(color)s, colorSpace=%(colorSpace)s, opacity=%(opacity)s,\n"
                 # no newline - start optional parameters
                 "    texRes=%(texture resolution)s" %
                 inits)

        buff.writeIndentedLines(code)

        if self.params['interpolate'].val == 'linear':
            buff.write(", interpolate=True")
        else:
            buff.write(", interpolate=False")

        depth = -self.getPosInRoutine()
        buff.write(", depth=%.1f)\n" % depth)  # finish with newline
