#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Part of the PsychoPy library
Copyright (C) 2015 Jonathan Peirce
Distributed under the terms of the GNU General Public License (GPL).
"""

from __future__ import absolute_import, print_function

from os import path
from psychopy.experiment.components import BaseComponent, Param, getInitVals, _translate

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'sound.png')
tooltip = _translate('Sound: play recorded files or generated sounds')

# only use _localized values for label values, nothing functional:
_localized = {'sound': _translate('Sound'), 'volume': _translate('Volume')}


class SoundComponent(BaseComponent):
    """An event class for presenting sound stimuli"""
    categories = ['Stimuli']

    def __init__(self, exp, parentName, name='sound_1', sound='A', volume=1,
                 startType='time (s)', startVal='0.0',
                 stopType='duration (s)', stopVal='1.0',
                 startEstim='', durationEstim=''):
        super(SoundComponent, self).__init__(
            exp, parentName, name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)
        self.type = 'Sound'
        self.url = "http://www.psychopy.org/builder/components/sound.html"
        self.exp.requirePsychopyLibs(['sound'])
        # params
        self.params['stopType'].allowedVals = ['duration (s)']
        self.params['stopType'].hint = _translate('The maximum duration of a'
                                                  ' sound in seconds')
        hnt = _translate("When does the component end? (blank to use the "
                         "duration of the media)")
        self.params['stopVal'].hint = hnt

        hnt = _translate("A sound can be a note name (e.g. A or Bf), a number"
                         " to specify Hz (e.g. 440) or a filename")
        self.params['sound'] = Param(
            sound, valType='str', allowedTypes=[], updates='constant',
            allowedUpdates=['constant', 'set every repeat'],
            hint=hnt,
            label=_localized['sound'])
        _allowed = ['constant', 'set every repeat', 'set every frame']
        self.params['volume'] = Param(
            volume, valType='code', allowedTypes=[], updates='constant',
            allowedUpdates=_allowed[:],  # use a copy
            hint=_translate("The volume (in range 0 to 1)"),
            label=_localized["volume"])

    def writeInitCode(self, buff):
        # replaces variable params with sensible defaults
        inits = getInitVals(self.params)
        if float(inits['stopVal'].val) > 2:
            inits['stopVal'].val = -1
        buff.writeIndented("%s = sound.Sound(%s, secs=%s)\n" %
                           (inits['name'], inits['sound'], inits['stopVal']))
        buff.writeIndented("%(name)s.setVolume(%(volume)s)\n" % (inits))

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        # the sound object is unusual, because it is
        buff.writeIndented("# start/stop %(name)s\n" % (self.params))
        # do this EVERY frame, even before/after playing?
        self.writeParamUpdates(buff, 'set every frame')
        self.writeStartTestCode(buff)
        code = "%s.play()  # start the sound (it finishes automatically)\n"
        buff.writeIndented(code % self.params['name'])
        # because of the 'if' statement of the time test
        buff.setIndentLevel(-1, relative=True)
        if not float(self.params['stopVal'].val) < 2: # Reduce spectral splatter but not stopping short sounds
            if not self.params['stopVal'].val in ['', None, -1, 'None']:
                self.writeStopTestCode(buff)
                code = "%s.stop()  # stop the sound (if longer than duration)\n"
                buff.writeIndented(code % self.params['name'])
                # because of the 'if' statement of the time test
                buff.setIndentLevel(-1, relative=True)

    def writeRoutineEndCode(self, buff):
        code = "%s.stop()  # ensure sound has stopped at end of routine\n"
        buff.writeIndented(code % self.params['name'])
