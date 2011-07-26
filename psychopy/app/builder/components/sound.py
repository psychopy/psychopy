# Part of the PsychoPy library
# Copyright (C) 2011 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path
from psychopy.app.builder.components import getInitVals

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'sound.png')

class SoundComponent(BaseComponent):
    """An event class for presenting image-based stimuli"""
    def __init__(self, exp, parentName, name='sound', sound='A',volume=1,
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                startEstim='', durationEstim=''):
        self.type='Sound'
        self.url="http://www.psychopy.org/builder/components/sound.html"
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['sound'])
        #params
        self.order=[]#order for things (after name and timing params)
        self.params={}
        self.params['name']=Param(name, valType='code', hint="Everything needs a name (no spaces or punctuation)")
        self.params['sound']=Param(sound, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat'],
            hint="A sound can be a note name (e.g. A or Bf), a number to specify Hz (e.g. 440) or a filename")
        self.params['startType']=Param(startType, valType='str',
            allowedVals=['time (s)', 'frame N', 'condition'],
            hint="How do you want to define your start point?")
        self.params['stopType']=Param(stopType, valType='str',
            allowedVals=['duration (s)'],
            hint="The maximum duration of a sound in seconds")
        self.params['startVal']=Param(startVal, valType='code', allowedTypes=[],
            hint="When does the sound start playing?")
        self.params['stopVal']=Param(stopVal, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="The maximum duration for the sound (blank to use the duration of the sound file)")
        self.params['startEstim']=Param(startEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected start (s), purely for representing in the timeline")
        self.params['durationEstim']=Param(durationEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected duration (s), purely for representing in the timeline")
        self.params['volume']=Param(volume, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint="The volume (in range 0 to 1)")

    def writeInitCode(self,buff):
        inits = getInitVals(self.params)#replaces variable params with sensible defaults
        if self.params['stopType']=='duration (s)':
            durationSetting="secs=%(stopVal)s" %self.paramss
        buff.writeIndented("%s=sound.Sound(%(sound)s,%s)\n" %(inits, durationSetting))
        buff.writeIndented("%(name)s.setVolume(%(volume)s)\n" %(inits))
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
