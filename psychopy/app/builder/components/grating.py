# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _visual import * #to get the template visual component
from os import path
from psychopy.app.builder.components import getInitVals

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'grating.png')
tooltip = _translate('Grating: present cyclic textures, prebuilt or from a file')

# only use _localized values for label values, nothing functional:
_localized = {'tex': _translate('Texture'), 'mask': _translate('Mask'), 'sf': _translate('Spatial frequency'),
              'phase': _translate('Phase (in cycles)'), 'texture resolution': _translate('Texture resolution'),
              'interpolate': _translate('Interpolate')
              }

class GratingComponent(VisualComponent):
    """A class for presenting grating stimuli"""
    def __init__(self, exp, parentName, name='grating', image='sin', mask='None', sf='None', interpolate='linear',
                units='from exp settings', color='$[1,1,1]', colorSpace='rgb',
                pos=[0,0], size=[0.5,0.5], ori=0, phase=0.0, texRes='128',
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                startEstim='', durationEstim=''):
        #initialise main parameters from base stimulus
        super(GratingComponent, self).__init__(exp,parentName,name=name, units=units,
                    color=color, colorSpace=colorSpace,
                    pos=pos, size=size, ori=ori,
                    startType=startType, startVal=startVal,
                    stopType=stopType, stopVal=stopVal,
                    startEstim=startEstim, durationEstim=durationEstim)
        self.type='Grating'
        self.url="http://www.psychopy.org/builder/components/grating.html"
        self.order=['tex','mask']
        #params
        self.params['tex']=Param(image, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint=_translate("The (2D) texture of the grating - can be sin, sqr, sinXsin... or a filename (including path)"),
            label=_localized['tex'], categ="Grating")
        self.params['mask']=Param(mask, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint=_translate("An image to define the alpha mask (ie shape)- gauss, circle... or a filename (including path)"),
            label=_localized['mask'], categ="Grating")
        self.params['sf']=Param(sf, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint=_translate("Spatial frequency of image repeats across the grating in 1 or 2 dimensions, e.g. 4 or [2,3]"),
            label=_localized['sf'], categ="Grating")
        self.params['phase']=Param(phase, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint=_translate("Spatial positioning of the image on the grating (wraps in range 0-1.0)"),
            label=_localized['phase'], categ="Grating")
        self.params['texture resolution']=Param(texRes, valType='code', allowedVals=['32','64','128','256','512'],
            updates='constant', allowedUpdates=[],
            hint=_translate("Resolution of the texture for standard ones such as sin, sqr etc. For most cases a value of 256 pixels will suffice"),
            label=_localized['texture resolution'], categ="Grating")
        self.params['interpolate']=Param(interpolate, valType='str', allowedVals=['linear','nearest'],
            updates='constant', allowedUpdates=[],
            hint=_translate("How should the image be interpolated if/when rescaled"),
            label=_localized['interpolate'], categ="Grating")

    def writeInitCode(self,buff):
        #do we need units code?
        if self.params['units'].val=='from exp settings': unitsStr=""
        else: unitsStr="units=%(units)s, " %self.params
        inits = getInitVals(self.params)#replaces variable params with defaults
        buff.writeIndented("%s = visual.GratingStim(win=win, name='%s',%s\n" %(inits['name'],inits['name'],unitsStr))
        buff.writeIndented("    tex=%(tex)s, mask=%(mask)s,\n" %(inits))
        buff.writeIndented("    ori=%(ori)s, pos=%(pos)s, size=%(size)s, sf=%(sf)s, phase=%(phase)s,\n" %(inits) )
        buff.writeIndented("    color=%(color)s, colorSpace=%(colorSpace)s, opacity=%(opacity)s,\n" %(inits) )
        buff.writeIndented("    texRes=%(texture resolution)s" %(inits))# no newline - start optional parameters
        if self.params['interpolate'].val=='linear':
            buff.write(", interpolate=True")
        else: buff.write(", interpolate=False")
        depth = -self.getPosInRoutine()
        buff.write(", depth=%.1f)\n" %depth)#finish with newline
