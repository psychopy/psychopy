# Part of the PsychoPy library
# Copyright (C) 2011 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'sound.png')

class SoundComponent(BaseComponent):
    """An event class for presenting image-based stimuli"""
    def __init__(self, exp, parentName, name='sound', sound='A', 
            size=1, ori=0, startTime=0.0, duration='', volume=1):
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
            hint="The maximum duration the sound should play") 
        self.params['volume']=Param(volume, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="The volume (in range 0 to 1)") 

    def writeInitCode(self,buff):
        buff.writeIndented("#initialise %(name)s\n" %(self.params))
        if str(self.params['duration'])=='':
            buff.writeIndented("%(name)s=sound.Sound(%(sound)s)\n" %(self.params))
        else:
            buff.writeIndented("%(name)s=sound.Sound(%(sound)s, secs=%(duration)s)\n" %(self.params))
        buff.writeIndented("%(name)s.setVolume(%(volume)s)\n" %(self.params))
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        #the sound object is unusual, because it is 
        buff.writeIndented("#start/stop %(name)s\n" %(self.params))
        self.writeParamUpdates(buff, 'frame')#do this EVERY frame, even before/after playing?
        buff.writeIndented("if %(startTime)s <= t and %(name)s.status==sound.NOT_STARTED:\n" %(self.params))
        buff.writeIndented("    %s.play()#start the sound (it finishes automatically)\n" %(self.params['name']))
        if str(self.params['duration'])!='':
            buff.writeIndented("if t > (%(startTime)s+%(duration)s) and %(name)s.status==sound.STARTED:\n" %(self.params))
            buff.writeIndented("    %s.stop()#stop the sound (if longer than duration)\n" %(self.params['name']))
            