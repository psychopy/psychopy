# Part of the PsychoPy library
# Copyright (C) 2011 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _visual import * #to get the template visual component
from os import path
from psychopy.app.builder.components import getInitVals

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'patch.png')
tooltip = 'Patch: present images (bmp, jpg, tif...) or textures like gratings'

class PatchComponent(VisualComponent):
    """An event class for presenting image-based stimuli"""
    def __init__(self, exp, parentName, name='patch', image='sin', mask='None', sf='None', interpolate='linear',
                units='from exp settings', color='$[1,1,1]', colorSpace='rgb',
                pos=[0,0], size=[0.5,0.5], ori=0, phase=0.0, texRes='128',
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                startEstim='', durationEstim=''):
        #initialise main parameters from base stimulus
        VisualComponent.__init__(self,parentName,name=name, units=units,
                    color=color, colorSpace=colorSpace,
                    pos=pos, size=size, ori=ori,
                    startType=startType, startVal=startVal,
                    stopType=stopType, stopVal=stopVal,
                    startEstim=startEstim, durationEstim=durationEstim)
        self.type='Patch'
        self.url="http://www.psychopy.org/builder/components/patch.html"
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['visual'])
        #params
        self.params['advancedParams']=['color', 'colorSpace','sf','phase','texture resolution','interpolate']
        self.params['image']=Param(image, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="The image to be displayed - 'sin','sqr'... or a filename (including path)")
        self.params['mask']=Param(mask, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="An image to define the alpha mask (ie shape)- 'gauss','circle'... or a filename (including path)")
        self.params['sf']=Param(sf, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Spatial frequency of image repeats across the patch, e.g. 4 or [2,3]")
        self.params['phase']=Param(phase, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Spatial positioning of the image on the patch (in range 0-1.0)")
        self.params['texture resolution']=Param(texRes, valType='code', allowedVals=['32','64','128','256','512'],
            updates='constant', allowedUpdates=[],
            hint="Spatial positioning of the image on the patch (in range 0-1.0)")
        self.params['interpolate']=Param(mask, valType='str', allowedVals=['linear','nearest'],
            updates='constant', allowedUpdates=[],
            hint="How should the image be interpolated if/when rescaled")

    def writeInitCode(self,buff):
        #do we need units code?
        if self.params['units'].val=='from exp settings': unitsStr=""
        else: unitsStr="units=%(units)s, " %self.params

        inits = getInitVals(self.params)#replaces variable params with defaults
        buff.writeIndented("%(name)s=visual.PatchStim(win=win, name='%s',%s\n" %(inits['name'],unitsStr))
        buff.writeIndented("    tex=%(image)s, mask=%(mask)s,\n" %(inits))
        buff.writeIndented("    ori=%(ori)s, pos=%(pos)s, size=%(size)s, sf=%(sf)s, phase=%(phase)s,\n" %(inits) )
        buff.writeIndented("    color=%(color)s, colorSpace=%(colorSpace)s,\n" %(inits) )
        buff.writeIndented("    texRes=%(texture resolution)s" %(inits))# no newline - start optional parameters
        if self.params['units'].val!='from exp settings': buff.write(", units=%(units)s" %(inits) )
        if self.params['interpolate']=='linear':
            buff.write(", interpolate=True")
        else: buff.write(", interpolate=False")
        buff.write(")\n")#finish with newline

