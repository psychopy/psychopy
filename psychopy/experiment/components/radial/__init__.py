#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path
from psychopy.experiment.components import BaseVisualComponent, Param, \
    getInitVals, _translate

__author__ = 'Bartu Atabek'


class RadialComponent(BaseVisualComponent):
    """A class for presenting radial stimuli"""

    categories = ['Stimuli']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'radial.png'
    tooltip = _translate('Radial: present radial stimuli, prebuilt or from a '
                         'file')

    def __init__(self, exp, parentName,
                 name='radial',
                 image='sqrXsqr',
                 mask='',
                 interpolate='Linear',
                 units='from exp settings',
                 color='$[1,1,1]',
                 colorSpace='rgb',
                 contrast=1.0,
                 pos=(0, 0),
                 size=(0.5, 0.5),
                 ori=0,
                 texRes='128',
                 radialCycles=3,
                 angularCycles=4,
                 radialPhase=0,
                 angularPhase=0,
                 visibleWedge=(0, 360),
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim=''):
        super(RadialComponent, self).__init__(
            exp, parentName, name=name, units=units,
            color=color, colorSpace=colorSpace, contrast=contrast,
            pos=pos, size=size, ori=ori,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Radial'
        self.url = "https://www.psychopy.org/builder/components/radial.html"
        self.order += [
            'tex', 'mask', 'radial cycles', 'angular cycles', 'radial phase', 'angular phase', 'visible wedge',
            'texture resolution', 'interpolate',  # Texture tab
        ]

        # params
        msg = _translate("The (2D) texture of the grating - can be sin, sqr,"
                         " sqrXsqr. or a filename (including path)")
        self.params['tex'] = Param(
            image, valType='file', inputType="file", allowedVals=["sin", "sqr", "sqrXsqr"], allowedTypes=[],
            categ='Texture',
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

        msg = _translate("Number of texture cycles from centre to periphery, i.e. it controls the number of ‘rings’.")
        self.params['radialCycles'] = Param(
            radialCycles, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Radial Cycles"))

        msg = _translate("Number of cycles going around the stimulus. i.e. it controls the number of ‘spokes’.")
        self.params['angularCycles'] = Param(
            angularCycles, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Angular Cycles"))

        msg = _translate("This is the phase of the texture from the centre to the perimeter of the stimulus"
                         " (in radians). Can be used to drift concentric rings out/inwards.")
        self.params['radialPhase'] = Param(
            radialPhase, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Radial Phase"))

        msg = _translate("This is akin to setting the orientation of the texture around the stimulus in radians."
                         " If possible, it is more efficient to rotate the stimulus using its ori setting instead.")
        self.params['angularPhase'] = Param(
            angularPhase, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Angular Phase"))

        msg = _translate("Determines visible range.")
        self.params['visibleWedge'] = Param(
            visibleWedge, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Visible Wedge"))

        msg = _translate("How should the image be interpolated if/when "
                         "rescaled")
        self.params['interpolate'] = Param(
            interpolate, valType='str', inputType="choice", allowedVals=['linear', 'nearest'], categ='Texture',
            updates='constant', allowedUpdates=[],
            hint=msg, direct=False,
            label=_translate("Interpolate"))

        msg = _translate(
            "Resolution of the texture for standard ones such as sin, sqr "
            "etc. For most cases a value of 256 pixels will suffice")
        self.params['texture resolution'] = Param(
            texRes,
            valType='num', inputType="choice", allowedVals=['32', '64', '128', '256', '512'], categ='Texture',
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Texture resolution"))

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
        code = ("%s = visual.RadialStim(\n" % inits['name'] +
                "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                "    tex=%(tex)s, mask=%(mask)s,\n" % inits +
                "    ori=%(ori)s, pos=%(pos)s, size=%(size)s,\n" % inits +
                "    radialCycles=%(radialCycles)s, angularCycles=%(angularCycles)s,\n" % inits +
                "    radialPhase=%(radialPhase)s, angularPhase=%(angularPhase)s,\n" % inits +
                "    visibleWedge=%(visibleWedge)s,\n" % inits +
                "    color=%(color)s, colorSpace=%(colorSpace)s,\n" % inits +
                "    opacity=%(opacity)s, contrast=%(contrast)s,\n" % inits +
                # no newline - start optional parameters
                "    texRes=%(texture resolution)s" % inits)

        if self.params['interpolate'].val == 'linear':
            code += ", interpolate=True"
        else:
            code += ", interpolate=False"
        code += ")\n"
        buff.writeIndentedLines(code)
