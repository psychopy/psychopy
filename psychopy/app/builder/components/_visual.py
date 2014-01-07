# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import _base
from os import path
from psychopy.app.builder.experiment import Param

class VisualComponent(_base.BaseComponent):
    """Base class for most visual stimuli
    """
    categories = ['Stimuli']#an attribute of the class, determines the section in the components panel
    def __init__(self, exp, parentName, name='', units='from exp settings', color='$[1,1,1]',
                pos=[0,0], size=[0,0], ori=0 , colorSpace='rgb', opacity=1,
                startType='time (s)',startVal='',
                stopType='duration (s)', stopVal='',
                startEstim='', durationEstim=''):
        self.psychopyLibs=['visual']#needs this psychopy lib to operate
        self.order=[]#make sure these are at top (after name and time params)
        self.params={}
        self.exp=exp
        self.parentName=parentName
        self.params['startType']=Param(startType, valType='str',
            allowedVals=['time (s)', 'frame N', 'condition'],
            hint="How do you want to define your start point?")
        self.params['stopType']=Param(stopType, valType='str',
            allowedVals=['duration (s)', 'duration (frames)', 'time (s)', 'frame N', 'condition'],
            hint="How do you want to define your end point?")
        self.params['startVal']=Param(startVal, valType='code', allowedTypes=[],
            hint="When does the stimulus start?")
        self.params['stopVal']=Param(stopVal, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="When does the stimulus end?")
        self.params['startEstim']=Param(startEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected start (s) of stimulus, purely for representing in the timeline")
        self.params['durationEstim']=Param(durationEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected duration (s) of stimulus, purely for representing in the timeline")
        self.params['name']=Param(name,  valType='code', updates='constant',
            hint="Name of this stimulus",
            label="Name")
        self.params['units']=Param(units, valType='str', allowedVals=['from exp settings', 'deg', 'cm', 'pix', 'norm'],
            hint="Units of dimensions for this stimulus",
            label="Units")
        self.params['color']=Param(color, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Color of this stimulus (e.g. $[1,1,0], red ); Right-click to bring up a color-picker (rgb only)",
            label="Color")
        self.params['opacity']=Param(opacity, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Opacity of the stimulus (1=opaque, 0=fully transparent, 0.5=translucent)",
            label="Opacity")
        self.params['colorSpace']=Param(colorSpace, valType='str', allowedVals=['rgb','dkl','lms'],
            updates='constant',
            hint="Choice of color space for the color (rgb, dkl, lms)",
            label="Color space")
        self.params['pos']=Param(pos, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Position of this stimulus (e.g. [1,2] )",
            label="Position [x,y]")
        self.params['size']=Param(size, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Size of this stimulus (either a single value or x,y pair, e.g. 2.5, [1,2] ",
            label="Size [w,h]")
        self.params['ori']=Param(ori, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="Orientation of this stimulus (in deg)",
            label="Orientation")
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        buff.writeIndented("\n")
        buff.writeIndented("# *%s* updates\n" %(self.params['name']))
        self.writeStartTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.writeIndented("%(name)s.setAutoDraw(True)\n" %(self.params))
        buff.setIndentLevel(-1, relative=True)#to get out of the if statement
        #test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            self.writeStopTestCode(buff)#writes an if statement to determine whether to draw etc
            buff.writeIndented("%(name)s.setAutoDraw(False)\n" %(self.params))
            buff.setIndentLevel(-1, relative=True)#to get out of the if statement
        #set parameters that need updating every frame
        if self.checkNeedToUpdate('set every frame'):#do any params need updating? (this method inherited from _base)
            buff.writeIndented("if %(name)s.status == STARTED:  # only update if being drawn\n" %(self.params))
            buff.setIndentLevel(+1, relative=True)#to enter the if block
            self.writeParamUpdates(buff, 'set every frame')
            buff.setIndentLevel(-1, relative=True)#to exit the if block
