# Part of the PsychoPy library
# Copyright (C) 2010 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _visual import * #to get the template visual component
from os import path

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'patch.png')

class PatchComponent(VisualComponent):
    """An event class for presenting image-based stimuli"""
    def __init__(self, exp, parentName, name='', image='sin', mask='none', sf=1, interpolate='linear',
        units='window units', color='$[1,1,1]', colorSpace='rgb',
        pos=[0,0], size=[0.5,0.5], ori=0, phase=0.0, texRes='128',
        startTime=0.0, duration=1.0):
        #initialise main parameters from base stimulus
        VisualComponent.__init__(self,parentName,name=name, units=units, 
                    color=color, colorSpace=colorSpace,
                    pos=pos, size=size, ori=ori, startTime=startTime, duration=duration)
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
        buff.writeIndented("%(name)s=visual.PatchStim(win=win, tex=%(image)s, mask=%(mask)s,\n" %(self.params))
        buff.writeIndented("    ori=%(ori)s, pos=%(pos)s, size=%(size)s, sf=%(sf)s, phase=%(phase)s,\n" %(self.params) )
        buff.writeIndented("    texRes=%(texture resolution)s" %(self.params))# no newline - start optional parameters
        if self.params['units'].val!='window units': buff.write(", units=%(units)s" %(self.params) )
        if self.params['interpolate']=='linear': buff.write(", interpolate=True")
        else: buff.write(", interpolate=False")
        buff.write(")\n" %(self.params))#finish with newline

