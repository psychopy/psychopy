#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from os import path
from psychopy.experiment.components import BaseVisualComponent, Param, \
    getInitVals, _translate
from psychopy.localization import _localized as __localized
_localized = __localized.copy()

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'grating.png')
tooltip = _translate('Grating: present cyclic textures, prebuilt or from a '
                     'file')

# only use _localized values for label values, nothing functional:
_localized.update({'tex': _translate('Texture'),
                   'mask': _translate('Mask'),
                   'sf': _translate('Spatial frequency'),
                   'phase': _translate('Phase (in cycles)'),
                   'texture resolution': _translate('Texture resolution'),
                   'blendmode': _translate('OpenGL blend mode'),
                   'interpolate': _translate('Interpolate')})


class GratingComponent(BaseVisualComponent):
    """A class for presenting grating stimuli"""

    targets = ['PsychoPy']

    def __init__(self, exp, parentName, name='grating', image='sin',
                 mask='', sf='', interpolate='linear',
                 units='from exp settings', color='$[1,1,1]', colorSpace='rgb',
                 contrast=1.0, pos=(0, 0), size=(0.5, 0.5), ori=0, phase=0.0, texRes='128',
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
            label=_localized['tex'])

        msg = _translate("An image to define the alpha mask (ie shape)- "
                         "gauss, circle... or a filename (including path)")
        self.params['mask'] = Param(
            mask, valType='file', inputType="file", allowedVals=["gauss", "circle"], allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['mask'])

        msg = _translate("Spatial frequency of image repeats across the "
                         "grating in 1 or 2 dimensions, e.g. 4 or [2,3]")
        self.params['sf'] = Param(
            sf, valType='num', inputType="single",  allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['sf'])

        msg = _translate("Spatial positioning of the image on the grating "
                         "(wraps in range 0-1.0)")
        self.params['phase'] = Param(
            phase, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['phase'])

        msg = _translate(
            "Resolution of the texture for standard ones such as sin, sqr "
            "etc. For most cases a value of 256 pixels will suffice")
        self.params['texture resolution'] = Param(
            texRes,
            valType='num', inputType="choice", allowedVals=['32', '64', '128', '256', '512'], categ='Texture',
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['texture resolution'])

        msg = _translate("How should the image be interpolated if/when "
                         "rescaled")
        self.params['interpolate'] = Param(
            interpolate, valType='str', inputType="choice", allowedVals=['linear', 'nearest'], categ='Texture',
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['interpolate'])

        msg = _translate("OpenGL Blendmode: avg gives traditional transparency,"
                         " add is important to combine gratings)]")
        self.params['blendmode'] = Param(
            blendmode, valType='str', inputType="choice", allowedVals=['avg', 'add'], categ='Appearance',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['blendmode'])

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
                "    tex=%(tex)s, mask=%(mask)s,\n" % inits +
                "    ori=%(ori)s, pos=%(pos)s, size=%(size)s, " % inits +
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
