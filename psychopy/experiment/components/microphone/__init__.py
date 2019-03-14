#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# Author: Jeremy R. Gray, 2012

from __future__ import absolute_import, print_function
from builtins import super  # provides Py3-style super() using python-future

from os import path
from psychopy.experiment.components import BaseComponent, Param, getInitVals, _translate

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'microphone.png')
tooltip = _translate('Microphone: basic sound capture (fixed onset & '
                     'duration), okay for spoken words')

_localized = {'stereo': _translate('Stereo'),'channel': _translate('Channel')}


class MicrophoneComponent(BaseComponent):
    """An event class for capturing short sound stimuli"""
    categories = ['Responses']

    def __init__(self, exp, parentName, name='mic_1',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=2.0, startEstim='',
                 durationEstim='', stereo=False, channel=0):
        super(MicrophoneComponent, self).__init__(
            exp, parentName, name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Microphone'
        self.url = "http://www.psychopy.org/builder/components/microphone.html"
        self.exp.requirePsychopyLibs(['microphone'])

        # params
        msg = _translate(
            "Record two channels (stereo) or one (mono, smaller file)")
        self.params['stereo'] = Param(
            stereo, valType='bool',
            hint=msg,
            label=_localized['stereo'])

        self.params['stopType'].allowedVals = ['duration (s)']

        msg = _translate(
            'The duration of the recording in seconds; blank = 0 sec')
        self.params['stopType'].hint = msg

        msg = _translate("Enter a channel number. Default value is 0. If unsure, run 'sound.backend.get_input_devices()' to locate the system's selected device/channel.")

        self.params['channel'] = Param(channel, valType='str', hint=msg, label=_localized['channel'])
    def writeStartCode(self, buff):
        # filename should have date_time, so filename_wav should be unique
        buff.writeIndented("wavDirName = filename + '_wav'\n")
        buff.writeIndented("if not os.path.isdir(wavDirName):\n"
                           "    os.makedirs(wavDirName)  # to hold .wav "
                           "files\n")

    def writeRoutineStartCode(self, buff):
        inits = getInitVals(self.params)
        code = ("%(name)s = microphone.AdvAudioCapture(name='%(name)s', "
                "saveDir=wavDirName, stereo=%(stereo)s, chnl=%(channel)s)\n")
        buff.writeIndented(code % inits)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame"""
        duration = "%s" % self.params['stopVal']  # type is code
        if not len(duration):
            duration = "0"
        # starting condition:
        buff.writeIndented("\n")
        buff.writeIndented("# *%s* updates\n" % self.params['name'])
        self.writeStartTestCode(buff)  # writes an if statement
        buff.writeIndented("%(name)s.status = STARTED\n" % self.params)
        code = "%s.record(sec=%s, block=False)  # start the recording thread\n"
        buff.writeIndented(code % (self.params['name'], duration))
        buff.setIndentLevel(-1, relative=True)  # ends the if statement
        buff.writeIndented("\n")
        # these lines handle both normal end of rec thread, and user .stop():
        code = ("if %(name)s.status == STARTED and not "
                "%(name)s.recorder.running:\n")
        buff.writeIndented(code % self.params)
        buff.writeIndented("    %s.status = FINISHED\n" % self.params['name'])

    def writeRoutineEndCode(self, buff):
        # some shortcuts
        name = self.params['name']
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler

        # write the actual code
        buff.writeIndented("# %(name)s stop & responses\n" % self.params)
        buff.writeIndented("%s.stop()  # sometimes helpful\n" %
                           self.params['name'])
        buff.writeIndented("if not %(name)s.savedFile:\n" % self.params)
        buff.writeIndented("    %(name)s.savedFile = None\n" % self.params)
        buff.writeIndented("# store data for %s (%s)\n" %
                           (currLoop.params['name'], currLoop.type))

        # always add saved file name
        buff.writeIndented("%s.addData('%s.filename', %s.savedFile)\n" %
                           (currLoop.params['name'], name, name))

        # get parent to write code too (e.g. store onset/offset times)
        super().writeRoutineEndCode(buff)

        if currLoop.params['name'].val == self.exp._expHandler.name:
            buff.writeIndented("%s.nextEntry()\n" % self.exp._expHandler.name)
        # best not to do loudness / rms or other processing here
