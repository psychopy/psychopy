# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _visual import * #to get the template visual component
from os import path

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'patch.png')

class PatchComponent(VisualComponent):
    """An event class for presenting image-based stimuli"""
    def __init__(self, exp, parentName, name='', image='sin', mask='none', sf=1, interpolate='linear',
        units='window units', colour=[1,1,1], colourSpace='rgb',
        pos=[0,0], size=[0,0], ori=0, times=[0,1]):
        #initialise main parameters from base stimulus
        VisualComponent.__init__(self,parentName,name=name, units=units, 
                    colour=colour, colourSpace=colourSpace,
                    pos=pos, size=size, ori=ori, times=times)
        self.type='Patch'
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['visual'])
        #params
        self.params['image']=Param(image, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="The image to be displayed - 'sin','sqr'... or a filename (including path)")        
        self.params['mask']=Param(mask, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="An image to define the alpha mask (ie shape)- 'gauss','circle'... or a filename (including path)")        
        self.params['sf']=Param(sf, valType='num', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Spatial frequency of image repeats across the patch, e.g. 4 or [2,3]")        
        self.params['interpolate']=Param(mask, valType='str', allowedVals=['linear','nearest'],
            updates='constant', allowedUpdates=[],
            hint="How should the image be interpolated if/when rescaled")
            
    def writeInitCode(self,buff):
        buff.writeIndented("%(name)s=visual.PatchStim(win=win, tex=%(image)s, mask=%(mask)s,\n" %(self.params))
        buff.writeIndented("    pos=%(pos)s, size=%(size)s)\n" %(self.params) )

