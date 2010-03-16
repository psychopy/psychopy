# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path
from psychopy.app.builder.experiment import Param

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'mouse.png')

class MouseComponent(BaseComponent):
    """An event class for checking the mouse location and buttons at given timepoints"""
    def __init__(self, exp, parentName, name='mouse', startTime=0.0, duration=1.0, save='final'):
        self.type='Mouse'
        self.url="http://www.psychopy.org/builder/components/mouse.html"
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['event'])
        #params
        self.order = ['name']#make sure that 'name' is at top of dlg
        self.params={}
        self.params['name']=Param(name, valType='str', allowedTypes=[],
            hint="Even mice have names!")            
        self.params['startTime']=Param(startTime, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="The time that the mouse starts being checked")
        self.params['duration']=Param(duration, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="The duration for which the mouse is checked")
        self.params['save mouse pos']=Param(save, valType='str', allowedVals=['final values','every frame'])
    def writeInitCode(self,buff):
        buff.writeIndented("%(name)s=event.Mouse()\n" %(self.params))
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        self.writeTimeTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.setIndentLevel(1, relative=True)#because of the 'if' statement of the time test
        self.writeParamUpdates(buff, 'frame')
        buff.writeIndented("TODO: check mouse")
        buff.setIndentLevel(-1, relative=True)#because of the 'if' statement of the time test
        
              