# Part of the PsychoPy library
# Copyright (C) 2010 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'sound.png')

class SoundComponent(BaseComponent):
    """An event class for presenting image-based stimuli"""
    def __init__(self, exp, parentName, name='sound', sound='A', 
            size=1, ori=0, startTime=0.0, duration=''):
        self.type='Sound'
        self.url="http://www.psychopy.org/builder/components/sound.html"
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['sound'])
        #params
        self.order=['name','startTime','duration']#make sure name comes first
        self.params={}
        self.params['name']=Param(name, valType='code', hint="Everything needs a name (no spaces or punctuation)")  
        self.params['sound']=Param(sound, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat'],
            hint="A sound can be a note name (e.g. A or Bf) or dollar then a number (e.g. $440) to specify Hz, or a filename")        
        self.params['startTime']=Param(startTime, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="The time that the sound starts")
        self.params['duration']=Param(duration, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="The duration of the sound (ignored if sound is a file with fixed length)") 

    def writeInitCode(self,buff):
        s = "%s=sound.Sound(%s, secs=%s)\n" %(self.params['name'], self.params['sound'], self.params['duration'])
        buff.writeIndented(s)
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        self.writeTimeTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.setIndentLevel(1, relative=True)#because of the 'if' statement of the start/end time test
        #set parameters that need updating every frame
        self.writeParamUpdates(buff, 'frame')
        buff.writeIndented("%s.play()#NB. this is safe when already playing\n" %(self.params['name'])) 
        buff.setIndentLevel(-1, relative=True)#because of the 'if' statement of the start/end time test
        
