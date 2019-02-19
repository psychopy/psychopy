#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Part of the PsychoPy library
Copyright (C) 2018 Jonathan Peirce
Distributed under the terms of the GNU General Public License (GPL).
"""

from __future__ import absolute_import, print_function
from builtins import super  # provides Py3-style super() using python-future

from os import path
from psychopy.experiment.components import BaseComponent, Param, getInitVals, _translate
from psychopy.sound._base import knownNoteNames

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'sound.png')
tooltip = _translate('Sound: play recorded files or generated sounds',)

# only use _localized values for label values, nothing functional:
_localized = {'sound': _translate('Sound'),
              'volume': _translate('Volume'),
              'syncScreenRefresh': _translate('sync RT with screen')}


class SoundComponent(BaseComponent):
    """An event class for presenting sound stimuli"""
    categories = ['Stimuli']

    def __init__(self, exp, parentName, name='sound_1', sound='A', volume=1,
                 startType='time (s)', startVal='0.0',
                 stopType='duration (s)', stopVal='1.0',
                 startEstim='', durationEstim='',
                 syncScreenRefresh=True):
        super(SoundComponent, self).__init__(
            exp, parentName, name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)
        self.type = 'Sound'
        self.url = "http://www.psychopy.org/builder/components/sound.html"
        self.exp.requirePsychopyLibs(['sound'])
        self.targets = ['PsychoPy', 'PsychoJS']
        self.order = ["sound", "volume"]
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
        msg = _translate(
            "A reaction time to a sound stimulus should be based on when "
            "the screen flipped")
        self.params['syncScreenRefresh'] = Param(
            syncScreenRefresh, valType='bool',
            updates='constant',
            hint=msg,
            label=_localized['syncScreenRefresh'])

    def writeInitCode(self, buff):
        # replaces variable params with sensible defaults
        inits = getInitVals(self.params)
        if '$' in inits['stopVal'].val:
            inits['stopVal'].val = -1
        else:
            if inits['stopVal'].val in ['', None, 'None']:
                inits['stopVal'].val = -1
            elif float(inits['stopVal'].val) > 2:
                inits['stopVal'].val = -1
        buff.writeIndented("%s = sound.Sound(%s, secs=%s, stereo=%s)\n" %
                           (inits['name'], inits['sound'], inits['stopVal'], self.exp.settings.params['Force stereo']))
        buff.writeIndented("%(name)s.setVolume(%(volume)s)\n" % (inits))

    def writeRoutineStartCode(self, buff):
        if self.params['stopVal'].val in [None, 'None', '']:
            buff.writeIndentedLines("%(name)s.setSound(%(sound)s)\n"
                                    "%(name)s.setVolume(%(volume)s, log=False)\n" % self.params)
        else:
            buff.writeIndentedLines("%(name)s.setSound(%(sound)s, secs=%(stopVal)s)\n"
                                    "%(name)s.setVolume(%(volume)s, log=False)\n" % self.params)

    def writeInitCodeJS(self, buff):
        # replaces variable params with sensible defaults
        inits = getInitVals(self.params)
        if '$' in inits['stopVal'].val:
            inits['stopVal'].val = -1
        elif inits['stopVal'].val in ['', None, 'None']:
            inits['stopVal'].val = -1
        elif float(inits['stopVal'].val) > 2:
            inits['stopVal'].val = -1
        buff.writeIndented("%s = new Sound({\n"
                           "    win: psychoJS.window,\n"
                           "    value: %s,\n"
                           "    secs: %s,\n"
                           "    });\n" % (inits['name'],
                                          inits['sound'],
                                          inits['stopVal']))
        buff.writeIndented("%(name)s.setVolume(%(volume)s);\n" % (inits))

    def writeRoutineStartCodeJS(self, buff):
        stopVal = self.params['stopVal'].val
        if stopVal in ['', None, 'None']:
            stopVal = -1

        if self.params['sound'].updates == 'set every repeat':
            buff.writeIndented("%s = new Sound({\n"
                               "    win: psychoJS.window,\n"
                               "    value: %s,\n"
                               "    secs: %s,\n"
                               "    });\n" % (self.params['name'],
                                              self.params['sound'],
                                              stopVal))
        if stopVal == -1:
            buff.writeIndentedLines("%(name)s.setVolume(%(volume)s)\n" % self.params)
        else:
            buff.writeIndentedLines("%(name)s.secs=%(stopVal)s\n"
                                    "%(name)s.setVolume(%(volume)s)\n" % self.params)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        # the sound object is unusual, because it is
        buff.writeIndented("# start/stop %(name)s\n" % (self.params))
        # do this EVERY frame, even before/after playing?
        self.writeParamUpdates(buff, 'set every frame')
        self.writeStartTestCode(buff)
        if self.params['syncScreenRefresh'].val:
            code = ("win.callOnFlip(%(name)s.play)  # screen flip\n") % self.params
        else:
            code = "%(name)s.play()  # start the sound (it finishes automatically)\n" % self.params
        buff.writeIndented(code)
        # because of the 'if' statement of the time test
        buff.setIndentLevel(-1, relative=True)
        if not self.params['stopVal'].val in ['', None, -1, 'None']:

            if '$' in self.params['stopVal'].val:
                code = 'if %(name)s.status == STARTED and t >= %(stopVal)s:\n' \
                       '    %(name)s.stop()  # stop the sound (if longer than duration)\n'
                buff.writeIndentedLines(code % self.params)
            elif not float(self.params['stopVal'].val) < 2:  # Reduce spectral splatter but not stopping short sounds
                self.writeStopTestCode(buff)
                code = "%s.stop()  # stop the sound (if longer than duration)\n"
                buff.writeIndented(code % self.params['name'])
                # because of the 'if' statement of the time test
                buff.setIndentLevel(-1, relative=True)

    def writeFrameCodeJS(self, buff):
        """Write the code that will be called every frame
        """
        # the sound object is unusual, because it is
        buff.writeIndented("// start/stop %(name)s\n" % (self.params))
        # do this EVERY frame, even before/after playing?
        self.writeParamUpdates(buff, 'set every frame')
        self.writeStartTestCodeJS(buff)
        if self.params['syncScreenRefresh'].val:
            code = ("psychoJS.window.callOnFlip(function(){ %(name)s.play(); });  // screen flip\n")
        else:
            code = "%(name)s.play();  // start the sound (it finishes automatically)\n"
        code += "%(name)s.status = PsychoJS.Status.STARTED;\n"
        buff.writeIndentedLines(code % self.params)
        # because of the 'if' statement of the time test
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines('}\n')
        knownNote = (self.params['sound'] in knownNoteNames) or (self.params['sound'].val.isdigit())
        if self.params['stopVal'].val in [None, 'None', '']:
            code = ('if (t >= (%(name)s.getDuration() + %(name)s.tStart) '
                    '&& %(name)s.status === PsychoJS.Status.STARTED) {\n'
                    '  %(name)s.stop();  // stop the sound (if longer than duration)\n'
                    '  %(name)s.status = PsychoJS.Status.FINISHED;\n'
                    '}\n')
            if not knownNote:  # Known notes have no getDuration function because duration is infinite or not None
                buff.writeIndentedLines(code % self.params)
        elif '$' in self.params['stopVal'].val:
            code = ('if (t >= (%(stopVal)s && %(name)s.status === PsychoJS.Status.STARTED)) {\n'
                    '  %(name)s.stop();  // stop the sound (if longer than duration)\n'
                    '  %(name)s.status = PsychoJS.Status.FINISHED;\n'
                    '}\n')
            buff.writeIndentedLines(code % self.params)
        elif not float(self.params['stopVal'].val) < 2:  # Reduce spectral splatter but not stopping short sounds
            self.writeStopTestCodeJS(buff)
            code = "%s.stop();  // stop the sound (if longer than duration)\n"
            buff.writeIndented(code % self.params['name'])
            # because of the 'if' statement of the time test
            buff.setIndentLevel(-1, relative=True)
            buff.writeIndented('}\n')

    def writeRoutineEndCode(self, buff):
        code = "%s.stop()  # ensure sound has stopped at end of routine\n"
        buff.writeIndented(code % self.params['name'])
        # get parent to write code too (e.g. store onset/offset times)
        super().writeRoutineEndCode(buff)

    def writeRoutineEndCodeJS(self, buff):
        code = "%s.stop();  // ensure sound has stopped at end of routine\n"
        buff.writeIndented(code % self.params['name'])
