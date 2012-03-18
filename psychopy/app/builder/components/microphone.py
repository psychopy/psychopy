# Part of the PsychoPy library
# Copyright (C) 2012 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path
from psychopy.app.builder import components #for getInitVals()

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'microphone.png')
tooltip = 'Microphone: basic sound capture (fixed onset & duration), okay for spoken words'

class MicrophoneComponent(BaseComponent):
    """An event class for capturing short sound stimuli"""
    def __init__(self, exp, parentName, name='mic_1', 
                 startType='time (s)', startVal=0.0, rate=22050,
                 stopType='duration (s)', stopVal=2.0, startEstim='', durationEstim='',
                ):
        self.type='Microphone'
        self.url="http://www.psychopy.org/builder/components/microphone.html"
        self.parentName=parentName
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['microphone'])
        #params
        self.order=[]#order for things (after name and timing params)
        self.params={}
        self.params['name']=Param(name, valType='code', hint="Everything needs a name (no spaces or punctuation)",
            label="Name")
        self.params['startType']=Param(startType, valType='str',
            allowedVals=['time (s)', 'frame N', 'condition'],
            hint="How do you want to define your start point?")
        self.params['stopType']=Param(stopType, valType='str',
            allowedVals=['duration (s)'],
            hint="The duration of the recording in seconds")
        self.params['startVal']=Param(startVal, valType='code', allowedTypes=[],
            hint="When does the sound start recording?")
        self.params['stopVal']=Param(stopVal, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="")
        self.params['startEstim']=Param(startEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected start (s), purely for representing in the timeline")
        self.params['durationEstim']=Param(durationEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected duration (s), purely for representing in the timeline")
        self.params['rate']=Param(rate, valType='str', hint="Sampling rate (Hz)",
            label="rate")

    def writeInitCode(self,buff):
        if self.params['stopType']=='duration (s)':
            durationSetting="secs=%(stopVal)s" %self.params
        else:
            durationSetting=""
    def writeRoutineStartCode(self,buff):
        inits = components.getInitVals(self.params) #replaces variable params with sensible defaults
        saveToDir = self.exp.settings.getSaveDataDir()
        '''saveToDir = self.exp.settings.params['Saved data folder'].val.strip()
        if not saveToDir:
            saveToDir = self.exp.prefsBuilder['savedDataFolder'].strip()
            if not saveToDir:
                saveToDir = 'data'
        '''
        buff.writeIndented("%s = microphone.SimpleAudioCapture(name='%s', rate=%s, saveDir='%s')\n" %(
            inits['name'], inits['name'], inits['rate'], saveToDir))
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame"""
        if self.params['stopType'].val == 'duration (s)':
            duration = float(self.params['stopVal'].val)
        else:
            duration = float(self.params['stopVal'].val) - float(self.params['startVal'].val)
        buff.writeIndented("#start/stop %(name)s\n" %(self.params))
        buff.writeIndented("if t >= %(startVal)s and %(name)s.status == NOT_STARTED:\n" % self.params)
        buff.writeIndented("    %s.record(sec=%.3f) #start the recording (it finishes automatically)\n" %
                            (self.params['name'], duration))
        buff.writeIndented("    %s.status = FINISHED\n" % self.params['name'])
