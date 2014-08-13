# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path
from psychopy.app.builder import components #for getInitVals()

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'sound.png')
tooltip = 'Sound: play recorded files or generated sounds'

class SoundComponent(BaseComponent):
    """An event class for presenting sound stimuli"""
    categories = ['Stimuli']
    def __init__(self, exp, parentName, name='sound_1', sound='A',volume=1,
                startType='time (s)', startVal='0.0',
                stopType='duration (s)', stopVal='1.0',
                startEstim='', durationEstim=''):
        self.type='Sound'
        self.url="http://www.psychopy.org/builder/components/sound.html"
        self.parentName=parentName
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['sound'])
        #params
        self.order=[]#order for things (after name and timing params)
        self.params={}
        self.params['name']=Param(name, valType='code', hint="Everything needs a name (no spaces or punctuation)",
            label="Name")
        self.params['sound']=Param(sound, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat'],
            hint="A sound can be a note name (e.g. A or Bf), a number to specify Hz (e.g. 440) or a filename",
            label="Sound")
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
            hint="The volume (in range 0 to 1)",
            label="Volume")

    def writeInitCode(self,buff):
        inits = components.getInitVals(self.params)#replaces variable params with sensible defaults
        if self.params['stopType'].val=='duration (s)' and len(self.params['stopVal'].val)>0:
            durationSetting=", secs=%(stopVal)s" %self.params
        else:
            durationSetting=""
        buff.writeIndented("%s = sound.Sound(%s%s)\n" %(inits['name'], inits['sound'], durationSetting))
        buff.writeIndented("%(name)s.setVolume(%(volume)s)\n" %(inits))
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        #the sound object is unusual, because it is
        buff.writeIndented("# start/stop %(name)s\n" %(self.params))
        self.writeParamUpdates(buff, 'frame')#do this EVERY frame, even before/after playing?
        self.writeStartTestCode(buff)
        buff.writeIndented("%s.play()  # start the sound (it finishes automatically)\n" %(self.params['name']))
        buff.setIndentLevel(-1, relative=True)#because of the 'if' statement of the time test
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            self.writeStopTestCode(buff)
            buff.writeIndented("%s.stop()  # stop the sound (if longer than duration)\n" %(self.params['name']))
            buff.setIndentLevel(-1, relative=True)#because of the 'if' statement of the time test
