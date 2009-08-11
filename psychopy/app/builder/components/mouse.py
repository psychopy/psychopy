from _base import *
from os import path
from psychopy.app.builder.experiment import Param

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'mouse.png')

class MouseComponent(BaseComponent):
    """An event class for checking the mouse location and buttons at given times"""
    def __init__(self, parentName, name='mouse', times=[0,1], save='final'):
        self.type='Mouse'
        self.psychopyLibs=['event']#needs this psychopy lib to operate
        self.order = ['name']#make sure that 'name' is at top of dlg
        self.params={}
        self.params['name']=Param(name, valType='str', allowedTypes=[],
            hint="Even mice have names!") 
        self.params['times']=Param(times, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="A series of one or more periods to read the mouse, e.g. [2.0,2.5] or [[2.0,2.5],[3.0,3.8]]")
        self.params['save']=Param(save, valType='str', allowedVals=['final values','every frame'])
    def writeInitCode(self,buff):
        pass#no need to initialise?
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        self.writeTimeTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.setIndentLevel(1, relative=True)#because of the 'if' statement of the times test
        self.writeParamUpdates(buff, 'frame')
        buff.writeIndented("TODO: check mouse")
        buff.setIndentLevel(-1, relative=True)#because of the 'if' statement of the times test
        
              