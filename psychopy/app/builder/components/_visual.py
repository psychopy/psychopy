# Part of the PsychoPy library
# Copyright (C) 2011 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import _base
from os import path
from psychopy.app.builder.experiment import Param

class VisualComponent(_base.BaseComponent):
    """Base class for most visual stimuli
    """
    def __init__(self, parentName, name='', units='window units', color='$[1,1,1]',
        pos=[0,0], size=[0,0], ori=0, startTime=0.0, duration='', colorSpace='rgb'):
        self.psychopyLibs=['visual']#needs this psychopy lib to operate
        self.order=['name','startTime','duration']#make name come first (others don't matter)
        self.params={}
        self.params['name']=Param(name,  valType='code', updates='constant', 
            hint="Name of this stimulus")
        self.params['units']=Param(units, valType='str', allowedVals=['window units', 'deg', 'cm', 'pix', 'norm'],
            hint="Units of dimensions for this stimulus")
        self.params['color']=Param(color, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Color of this stimulus (e.g. $[1,1,0], red ); Right-click to bring up a color-picker (rgb only)")
        self.params['colorSpace']=Param(colorSpace, valType='str', allowedVals=['rgb','dkl','lms'],
            updates='constant', allowedUpdates=['constant'],
            hint="Choice of color space for the color (rgb, dkl, lms)")
        self.params['pos']=Param(pos, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Position of this stimulus (e.g. [1,2] ")
        self.params['size']=Param(size, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Size of this stimulus (either a single value or x,y pair, e.g. 2.5, [1,2] ")
        self.params['ori']=Param(ori, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Orientation of this stimulus (in deg)")
        self.params['startTime']=Param(startTime, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="The time that the stimulus is first presented")
        self.params['duration']=Param(duration, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="The duration for which the stimulus is presented")
            
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        self.writeTimeTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.setIndentLevel(1, relative=True)#because of the 'if' statement of the time test
        #set parameters that need updating every frame
        self.writeParamUpdates(buff, 'set every frame')
        #draw the stimulus
        buff.writeIndented("%(name)s.draw()\n" %(self.params))
        buff.setIndentLevel(-1, relative=True)
       
    def writeParamUpdates(self, buff, updateType):
        """write updates to the buffer for each parameter that needs it
        updateType can be 'experiment', 'routine' or 'frame'
        """
        for thisParamName in self.params.keys():
            thisParam=self.params[thisParamName]
            #capitalise params
            if thisParamName=='advancedParams':
                continue
            elif thisParamName=='letterHeight':
                paramCaps='Height' #setHeight for TextStim
            elif thisParamName=='image':
                paramCaps='Tex' #setTex for PatchStim
            elif thisParamName=='sf':
                paramCaps='SF' #setSF, not SetSf
            else:
                paramCaps = thisParamName.capitalize()
            #color is slightly special
            if thisParam.updates==updateType:
                if thisParamName=='color':
                    buff.writeIndented("%(name)s.setColor(%(color)s, colorSpace=%(colorSpace)s)\n" %(self.params))
                else: buff.writeIndented("%s.set%s(%s)\n" %(self.params['name'], paramCaps, thisParam)) 

