# Part of the PsychoPy library
# Copyright (C) 2010 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import wx, copy
from os import path
from psychopy.app.builder.experiment import Param

class BaseComponent:
    """A template for components, defining the methods to be overridden"""
    def __init__(self, exp, parentName, name='', startTime=0.0, duration=1.0):
        self.type='Base'
        self.exp=exp#so we can access the experiment if necess
        self.params={}
        self.params['name']=Param(name, valType='code', 
            hint="Name of this component")
        self.order=['name','startTime','duration']#make name come first (others don't matter)
    def writeInitCode(self,buff):
        pass
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        pass
    def writeRoutineStartCode(self,buff):
        """Write the code that will be called at the beginning of 
        a routine (e.g. to update stimulus parameters)
        """
        self.writeParamUpdates(buff, 'set every repeat')
    def writeRoutineEndCode(self,buff):
        """Write the code that will be called at the end of 
        a routine (e.g. to save data)
        """
        pass
    def writeExperimentEndCode(self,buff):
        """Write the code that will be called at the end of 
        an experiment (e.g. save log files or reset hardware)
        """
        pass
    def writeTimeTestCode(self,buff):
        """Write the code for each frame that tests whether the component is being
        drawn/used.
        """
        exec('times=%s,%s' %(self.params['startTime'],self.params['duration']))
        start=times[0]
        #determine end from start and duration (if it exists)
        if len(times)>1:end=sum(times)
        else:end=-1
        if self.params['duration'].val=='':
            buff.writeIndented("if (%(startTime)s <= t):\n" %(self.params))            
        else:
            buff.writeIndented("if (%(startTime)s<= t < (%(startTime)s+%(duration)s)):\n" %(self.params))
    def writeParamUpdates(self, buff, updateType):
        """write updates to the buffer for each parameter that needs it
        updateType can be 'experiment', 'routine' or 'frame'
        """
        for thisParamName in self.params.keys():
            thisParam=self.params[thisParamName]
            if thisParam.updates==updateType:
                if thisParamName=='color': 
                    paramCaps=self.params['colorSpace'].upper() #setRGB, not setColor
                else:paramCaps=thisParamName.capitalize()
                buff.writeIndented("%s.set%s(%s)\n" %(self.params['name'],paramCaps, thisParam) )
    def getType(self):
        return self.__class__.__name__
    def getShortType(self):
        return self.getType().replace('Component','')