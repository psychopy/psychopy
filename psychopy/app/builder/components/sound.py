from _base import *
from os import path

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'sound.png')

class SoundComponent(BaseComponent):
    """An event class for presenting image-based stimuli"""
    def __init__(self, parentName, name='', sound='A', 
            size=1, ori=0, times=[0,1]):
        self.psychopyLibs=['sound']#needs this psychopy lib to operate
        self.order=['name']#make sure name comes first
        self.type='Sound'
        self.params={}
        self.params['name']=Param(name,  valType='code', hint="A filename for the movie (including path)")  
        self.params['sound']=Param(sound, valType='str', allowedTypes=['str','num','code'],
            updates="never", allowedUpdates=["never","routine"],
            hint="A sound can be a string (e.g. 'A' or 'Bf') or a number to specify Hz, or a filename")  
        self.params['times']=Param(times, valType='code', allowedTypes=['code'],
            updates="never", allowedUpdates=["never"],
            hint="A series of one or more onset/offset times, e.g. [2.0,2.5] or [[2.0,2.5],[3.0,3.8]]")  

    def writeInitCode(self,buff):
        s = "%(name)s=Sound(%(sound)s, secs=%s\n" %(self.params,self.params['times'][1]-self.params['times'][0])
        buff.writeIndented(s)  
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        self.writeTimeTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.setIndentLevel(1, relative=True)#because of the 'if' statement of the times test
        #set parameters that need updating every frame
        self.writeParamUpdates(buff, 'frame')
        buff.writeIndented("%s.play()\n" %(self.params['name'])) 
        buff.setIndentLevel(-1, relative=True)#because of the 'if' statement of the times test
            