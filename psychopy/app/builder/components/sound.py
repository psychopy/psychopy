# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path
from psychopy.app.builder import components #for getInitVals()

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'sound.png')
tooltip = _translate('Sound: play recorded files or generated sounds')

# only use _localized values for label values, nothing functional:
_localized = {'sound': _translate('Sound'), 'volume': _translate('Volume')}

class SoundComponent(BaseComponent):
    """An event class for presenting sound stimuli"""
    categories = ['Stimuli']
    def __init__(self, exp, parentName, name='sound_1', sound='A',volume=1,
                startType='time (s)', startVal='0.0',
                stopType='duration (s)', stopVal='1.0',
                startEstim='', durationEstim=''):
        super(SoundComponent, self).__init__(exp, parentName, name,
                startType=startType,startVal=startVal,
                stopType=stopType, stopVal=stopVal,
                startEstim=startEstim, durationEstim=durationEstim)
        self.type='Sound'
        self.url="http://www.psychopy.org/builder/components/sound.html"
        self.exp.requirePsychopyLibs(['sound'])
        #params
        self.params['stopType'].allowedVals = ['duration (s)']
        self.params['stopType'].hint = _translate('The maximum duration of a sound in seconds')
        self.params['stopVal'].hint = _translate("When does the component end? (blank to use the duration of the media)")
        self.params['sound']=Param(sound, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat'],
            hint=_translate("A sound can be a note name (e.g. A or Bf), a number to specify Hz (e.g. 440) or a filename"),
            label=_localized['sound'])
        self.params['volume']=Param(volume, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat','set every frame'],
            hint=_translate("The volume (in range 0 to 1)"),
            label=_localized["volume"])

    def writeInitCode(self,buff):
        inits = components.getInitVals(self.params)#replaces variable params with sensible defaults
        buff.writeIndented("%s = sound.Sound(%s, secs=-1)\n" %(inits['name'], inits['sound']))
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
    def writeRoutineEndCode(self,buff):
        buff.writeIndented("%s.stop() #ensure sound has stopped at end of routine\n" %(self.params['name']))
