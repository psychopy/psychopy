# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import _base
from os import path
from psychopy.app.builder.experiment import Param

class VisualComponent(_base.BaseComponent):
    """Base class for most visual stimuli
    """
    def __init__(self, parentName, name='', units='window units', colour=[1,1,1],
        pos=[0,0], size=[0,0], ori=0, startTime=0.0, duration=1.0, colourSpace='rgb'):
        self.psychopyLibs=['visual']#needs this psychopy lib to operate
        self.order=['name','startTime','duration']#make name come first (others don't matter)
        self.params={}
        self.params['name']=Param(name,  valType='code', updates='constant', 
            hint="Name of this stimulus")
        self.params['units']=Param(units, valType='str', allowedVals=['window units', 'deg', 'cm', 'pix', 'norm'],
            hint="Units of dimensions for this stimulus")
        self.params['colour']=Param(colour, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Colour of this stimulus (e.g. [1,1,0], 'red' )")
        self.params['colourSpace']=Param(colourSpace, valType='code', allowedVals=['rgb','dkl','lms'],
            updates='constant', allowedUpdates=['constant'],
            hint="Choice of colour space for the colour (rgb, dkl, lms)")
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
            if thisParamName=='image':
                paramCaps='Tex' #setTex for PatchStim
            elif thisParamName=='sf':
                paramCaps='SF' #setSF, not SetSf
            elif thisParamName=='colour':
                #we need setRGB=colour (not setColour=colour)
                paramCaps= self.params['colourSpace'].val.upper()#thisParam is the correct value, but the name is the space!
            else:
                paramCaps = thisParamName.capitalize()
            if thisParam.updates==updateType:
                buff.writeIndented("%s.set%s(%s)\n" %(self.params['name'], paramCaps, thisParam)) 
    
