import wx, copy
from os import path
from psychopy.app.builder.experiment import Param

class BaseComponent:
    """A template for components, defining the methods to be overridden"""
    def __init__(self, parentName, name='', times=[0,1]):
        self.type='Base'
        self.params={}
        self.params['name']=Param(name, valType='code', 
            hint="Name of this loop")
        self.order=['name']#make name come first (others don't matter)
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
        self.writeParamUpdates(buff, 'routine')
    def writeRoutineEndCode(self,buff):
        """Write the code that will be called at the end of 
        a routine (e.g. to save data)
        """
        pass
    def writeTimeTestCode(self, buff):
        """Write the code for each frame that tests whether the component is being
        drawn/used.
        """
        exec("times=%s" %self.params['times'].val)
        if type(times[0]) in [int, float]:
            times=[times]#make a list of lists
        print times
        #write the code for the first repeat of the stimulus
        buff.writeIndented("if (%.f <= t < %.f)" %(times[0][0], times[0][1]))
        if len(times)>1:
            for epoch in times[1:]: 
                buff.write("\n")
                buff.writeIndented("    or (%.f <= t < %.f)" %(epoch[0], epoch[1]))
        buff.write(':\n')#the condition is done add the : and new line to finish        
    def writeParamUpdates(self, buff, updateType):
        """write updates to the buffer for each parameter that needs it
        updateType can be 'experiment', 'routine' or 'frame'
        """
        for thisParamName in self.params.keys():
            thisParam=self.params[thisParamName]
            if thisParam.updates=='frame':
                buff.writeIndented("%s.set%s(%s)\n" %(self.params['name'], thisParamName.capitalize(), thisParam) )
    def getType(self):
        return self.__class__.__name__
    def getShortType(self):
        return self.getType().replace('Component','')