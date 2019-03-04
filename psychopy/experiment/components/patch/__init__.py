#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from os import path
from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals, _translate

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'patch.png')
tooltip = _translate('Patch: present images (bmp, jpg, tif...) or textures '
                     'like gratings')

# only use _localized values for label values, nothing functional:
_localized = {'image': _translate('Image/tex'),
              'mask': _translate('Mask'),
              'sf': _translate('Spatial frequency'),
              'phase': _translate('Phase (in cycles)'),
              'texture resolution': _translate('Texture resolution'),
              'interpolate': _translate('Interpolate')}


class PatchComponent(BaseVisualComponent):
    """An event class for presenting image-based stimuli"""

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
        self.url = "http://www.psychopy.org/builder/components/patch.html"
        # params
        self.params['color'].categ = "Advanced"
        self.params['colorSpace'].categ = "Advanced"

        msg = _translate("The image to be displayed - 'sin','sqr'... or a "
                         "filename (including path)")
        self.params['image'] = Param(
            image, valType='str', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['image'])

        msg = _translate("An image to define the alpha mask (ie shape)- "
                         "gauss, circle... or a filename (including path)")
        self.params['mask'] = Param(
            mask, valType='str', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['mask'])

        msg = _translate("Spatial frequency of image repeats across the "
                         "patch, e.g. 4 or [2,3]")
        self.params['sf'] = Param(
            sf, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['sf'], categ="Advanced")

        msg = _translate(
            "Spatial positioning of the image on the patch (in range 0-1.0)")
        self.params['phase'] = Param(
            phase, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['phase'], categ="Advanced")

        msg = _translate(
            "Resolution of the texture for standard ones such as sin, sqr "
            "etc. For most cases a value of 256 pixels will suffice")
        self.params['texture resolution'] = Param(
            texRes, valType='code',
            allowedVals=['32', '64', '128', '256', '512'],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['texture resolution'], categ="Advanced")

        msg = _translate(
            "How should the image be interpolated if/when rescaled")
        self.params['interpolate'] = Param(
            interpolate, valType='str', allowedVals=['linear', 'nearest'],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['interpolate'], categ="Advanced")

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
