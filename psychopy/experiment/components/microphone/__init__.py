#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

# Author: Jeremy R. Gray, 2012

from __future__ import absolute_import, print_function
from builtins import super  # provides Py3-style super() using python-future

from os import path
from pathlib import Path
from psychopy.experiment.components import BaseComponent, Param, getInitVals, _translate
from psychopy.sound.microphone import Microphone
from psychopy.sound.audiodevice import sampleRateQualityLevels
from psychopy.sound.audioclip import AUDIO_SUPPORTED_CODECS
from psychopy.localization import _localized as __localized

_localized = __localized.copy()
_localized.update({'stereo': _translate('Stereo'),
                   'channel': _translate('Channel')})

devices = {d.deviceName: d for d in Microphone.getDevices()}
sampleRates = {r[1]: r[0] for r in sampleRateQualityLevels.values()}
devices['default'] = None


class MicrophoneComponent(BaseComponent):
    """An event class for capturing short sound stimuli"""
    categories = ['Responses']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'microphone.png'
    tooltip = _translate('Microphone: basic sound capture (fixed onset & '
                         'duration), okay for spoken words')

    def __init__(self, exp, parentName, name='mic',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=2.0,
                 startEstim='', durationEstim='',
                 channels='stereo', device="default",
                 sampleRate='DVD Audio (48kHz)', maxSize=24000,
                 outputType='wav', speakTimes=True, trimSilent=False,
                 #legacy
                 stereo=None, channel=None):
        super(MicrophoneComponent, self).__init__(
            exp, parentName, name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Microphone'
        self.url = "https://www.psychopy.org/builder/components/microphone.html"
        self.exp.requirePsychopyLibs(['sound'])

        self.order += []

        self.params['stopType'].allowedVals = ['duration (s)']
        msg = _translate(
            'The duration of the recording in seconds; blank = 0 sec')
        self.params['stopType'].hint = msg

        # params
        msg = _translate("What microphone device would you like the use to record? This will only affect local "
                         "experiments - online experiments ask the participant which mic to use.")
        self.params['device'] = Param(
            device, valType='str', inputType="choice", categ="Basic",
            allowedVals=list(devices),
            hint=msg,
            label=_translate("Device")
        )

        msg = _translate(
            "Record two channels (stereo) or one (mono, smaller file). Select 'auto' to use as many channels "
            "as the selected device allows.")
        if stereo is not None:
            # If using a legacy mic component, work out channels from old bool value of stereo
            channels = ['mono', 'stereo'][stereo]
        self.params['channels'] = Param(
            channels, valType='str', inputType="choice", categ='Hardware',
            allowedVals=['auto', 'mono', 'stereo'],
            hint=msg,
            label=_translate('Channels'))

        msg = _translate(
            "How many samples per second (Hz) to record at")
        self.params['sampleRate'] = Param(
            sampleRate, valType='num', inputType="choice", categ='Hardware',
            allowedVals=list(sampleRates),
            hint=msg,
            label=_translate('Sample Rate (Hz)'))

        msg = _translate(
            "To avoid excessively large output files, what is the biggest file size you are likely to expect?")
        self.params['maxSize'] = Param(
            maxSize, valType='num', inputType="single", categ='Hardware',
            hint=msg,
            label=_translate('Max Recording Size (kb)'))

        msg = _translate(
            "What file type should output audio files be saved as?")
        self.params['outputType'] = Param(
            outputType, valType='code', inputType='choice', categ='Data',
            allowedVals=AUDIO_SUPPORTED_CODECS,
            hint=msg,
            label=_translate("Output File Type")
        )

        msg = _translate(
            "Tick this to save times when the participant starts and stops speaking")
        self.params['speakTimes'] = Param(
            speakTimes, valType='bool', inputType='bool', categ='Data',
            hint=msg,
            label=_translate("Speaking Start / Stop Times")
        )

        msg = _translate(
            "Trim periods of silence from the output file")
        self.params['trimSilent'] = Param(
            trimSilent, valType='bool', inputType='bool', categ='Data',
            hint=msg,
            label=_translate("Trim Silent")
        )

    def writeStartCode(self, buff):
        inits = getInitVals(self.params)
        # Use filename with a suffix to store recordings
        code = (
            "# Make folder to store recordings from %(name)s\n"
            "%(name)sRecFolder = filename + '_%(name)s_recorded'\n"
            "if not os.path.isdir(%(name)sRecFolder):\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
                "os.mkdir(%(name)sRecFolder)\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)

    def writeInitCode(self, buff):
        inits = getInitVals(self.params)
        # Substitute sample rate value for numeric equivalent
        inits['sampleRate'] = sampleRates[inits['sampleRate'].val]
        # Substitute channel value for numeric equivalent
        inits['channels'] = {'mono': 1, 'stereo': 2, 'auto': None}[self.params['channels'].val]
        # Substitute device name for device index
        device = devices[self.params['device'].val]
        if hasattr(device, "deviceIndex"):
            inits['device'] = device.deviceIndex
        else:
            inits['device'] = None
        # Create Microphone object and clips dict
        code = (
            "%(name)s = sound.microphone.Microphone(\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
                "device=%(device)s, channels=%(channels)s, \n"
                "sampleRateHz=%(sampleRate)s, maxRecordingSize=%(maxSize)s\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
            ")\n"
            "%(name)sClips = {}\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame"""
        inits = getInitVals(self.params)
        inits['routine'] = self.parentName
        # Start the recording
        code = (
            "\n"
            "# %(name)s updates"
        )
        buff.writeIndentedLines(code % inits)
        self.writeStartTestCode(buff)
        code = (
                "# start recording with %(name)s\n"
                "%(name)s.start()\n"
                "%(name)s.status = STARTED\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        # Get clip each frame
        code = (
            "if %(name)s.status == STARTED:\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
                "# update recorded clip for %(name)s\n"
                "%(name)s.poll()\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        # Stop recording
        self.writeStopTestCode(buff)
        code = (
            "# stop recording with %(name)s\n"
            "%(name)s.stop()\n"
            "%(name)s.status = FINISHED\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-2, relative=True)

    def writeRoutineEndCode(self, buff):
        inits = getInitVals(self.params)
        inits['routine'] = self.parentName
        # Store recordings from this routine
        code = (
            "%(name)s.bank('%(routine)s')\n"
        )
        buff.writeIndentedLines(code % inits)
        # Write base end routine code
        BaseComponent.writeRoutineEndCode(self, buff)

    def writeExperimentEndCode(self, buff):
        """Write the code that will be called at the end of
        an experiment (e.g. save log files or reset hardware)
        """
        inits = getInitVals(self.params)
        # Save recording
        code = (
            "# Save %(name)s recordings\n"
            "%(name)sClips = %(name)s.flush()\n"
            "for rt in %(name)sClips:\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
                "for i, clip in enumerate(%(name)sClips[rt]):\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
                    "clipName = os.path.join(%(name)sRecFolder, f'recording_{rt}_{i}.%(outputType)s')\n"
                    "clip.save(clipName)\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-2, relative=True)
