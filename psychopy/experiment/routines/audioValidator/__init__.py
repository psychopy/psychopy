#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from psychopy.preferences import prefs
from psychopy.alerts._alerts import alert
from psychopy.experiment import Param
from psychopy.experiment.plugins import DeviceBackend
from psychopy.experiment.components import getInitVals
from psychopy.experiment.routines import Routine, BaseDeviceRoutine
from psychopy.localization import _translate


class AudioValidatorRoutine(BaseDeviceRoutine):
    """
    Use a sound sensor (voicekey or microphone) to confirm that audio stimuli are presented when they should be.
    """
    targets = ['PsychoPy']

    categories = ['Validation']
    iconFile = Path(__file__).parent / 'audio_validator.png'
    tooltip = _translate(
        "Use a sound sensor to confirm that audio stimuli are presented when they should "
        "be."
    )
    version = "2025.1.0"

    def __init__(
            self,
            # basic
            exp, name='audioVal',
            threshold=0.5,
            # device
            deviceLabel="", deviceBackend="microphone", channel="0",
    ):

        self.exp = exp  # so we can access the experiment if necess
        self.params = {}
        self.depends = []
        super(AudioValidatorRoutine, self).__init__(exp, name=name)
        self.order += []
        self.type = 'AudioValidator'

        exp.requirePsychopyLibs(["validation"])

        # --- Basic ---
        self.order += [
            "threshold",
        ]
        self.params['threshold'] = Param(
            threshold, valType="code", inputType="single", categ="Basic",
            label=_translate("Threshold"),
            hint=_translate(
                "Arbitrary volume threshold at which the sound sensor should register a positive, units go from 0 (least volume) to 1 (most volume)."
            )
        )
        del self.params['stopType']
        del self.params['stopVal']

        # --- Device ---
        self.order += [
            "channel",
        ]
        self.params['channel'] = Param(
            channel, valType="code", inputType="single", categ="Device",
            label=_translate("Sound sensor channel"),
            hint=_translate(
                "If relevant, a channel number attached to the sound sensor, to distinguish it "
                "from other sound sensors on the same port. Leave blank to use the first sound sensor "
                "which can detect the speaker."
            )
        )

    def writeMainCode(self, buff):
        inits = getInitVals(self.params)
        # get diode
        code = (
            "# diode object for %(name)s\n"
            "%(name)sDevice = deviceManager.getDevice(%(deviceLabel)s)\n"
        )
        buff.writeIndentedLines(code % inits)

        if self.params['threshold']:
            code = (
                "%(name)sDevice.setThreshold(%(threshold)s, channel=%(channel)s)\n"
            )
            buff.writeIndentedLines(code % inits)
        # create validator object
        code = (
            "# validator object for %(name)s\n"
            "%(name)s = validation.AudioValidator(\n"
            "    %(name)sDevice, %(channel)s,\n"
            ")\n"
        )
        buff.writeIndentedLines(code % inits)
        # connect stimuli
        for stim in self.findConnectedStimuli():
            code = (
                "# connect {stim} to %(name)s\n"
                "%(name)s.connectStimulus({stim})\n"
            ).format(stim=stim.params['name'])
            buff.writeIndentedLines(code % inits)

    def writeRoutineStartValidationCode(self, buff, stim):
        """
        Write the routine start code to validate a given stimulus using this validator.

        Parameters
        ----------
        buff : StringIO
            String buffer to write code to.
        stim : BaseComponent
            Stimulus to validate

        Returns
        -------
        int
            Change in indentation level after writing
        """
        # get starting indent level
        startIndent = buff.indentLevel

        # choose a clock to sync to according to component's params
        if "syncScreenRefresh" in stim.params and stim.params['syncScreenRefresh']:
            clockStr = ""
        else:
            clockStr = "clock=routineTimer"
        # sync component start/stop timers with validator clocks
        code = (
            f"# synchronise device clock for %(name)s with Routine timer\n"
            f"%(name)s.resetTimer({clockStr})\n"
        )
        buff.writeIndentedLines(code % self.params)

        # return change in indent level
        return buff.indentLevel - startIndent

    def writeEachFrameValidationCode(self, buff, stim):
        """
        Write the each frame code to validate a given stimulus using this validator.

        Parameters
        ----------
        buff : StringIO
            String buffer to write code to.
        stim : BaseComponent
            Stimulus to validate

        Returns
        -------
        int
            Change in indentation level after writing
        """
        # get starting indent level
        startIndent = buff.indentLevel

        # validate start time
        code = (
            "# validate {name} start time\n"
            "if {name}.status == STARTED and %(name)s.status == STARTED:\n"
            "    %(name)s.tStart, %(name)s.tStartDelay = %(name)s.validate(state=True, t={name}.tStartRefresh)\n"
            "    if %(name)s.tStart is not None:\n"
            "        %(name)s.status = FINISHED\n"
        )
        if stim.params['saveStartStop']:
            # save validated start time if stim requested
            code += (
            "        thisExp.addData('{name}.%(name)s.started', %(name)s.tStart)\n"
            "        thisExp.addData('{name}.%(name)s.startDelay', %(name)s.tStartDelay)\n"
            )
        buff.writeIndentedLines(code.format(**stim.params) % self.params)

        # validate stop time
        code = (
            "# validate {name} stop time\n"
            "if {name}.status == FINISHED and %(name)s.status == STARTED:\n"
            "    %(name)s.tStop, %(name)s.tStopDelay = %(name)s.validate(state=False, t={name}.tStopRefresh)\n"
            "    if %(name)s.tStop is not None:\n"
            "        %(name)s.status = FINISHED\n"
        )
        if stim.params['saveStartStop']:
            # save validated start time if stim requested
            code += (
            "        thisExp.addData('{name}.%(name)s.stopped', %(name)s.tStop)\n"
            "        thisExp.addData('{name}.%(name)s.stopDelay', %(name)s.tStopDelay)\n"
            )
        buff.writeIndentedLines(code.format(**stim.params) % self.params)

        # return change in indent level
        return buff.indentLevel - startIndent

    def findConnectedStimuli(self):
        # list of linked components
        stims = []
        routines = []
        # inspect each Routine
        for emt in self.exp.flow:
            # skip non-standard Routines
            if not isinstance(emt, Routine):
                continue
            # inspect each Component
            for comp in emt:
                # get validators for this component
                compValidator = comp.getValidator()
                # look for self
                if compValidator == self:
                    # if found, add the comp to the list
                    stims.append(comp)
                    # add to list of Routines containing comps
                    if emt not in routines:
                        routines.append(emt)
        # if any rt has two validated comps, warn
        if len(routines) < len(stims):
            alert(3610, obj=self, strFields={'validator': self.name})

        return stims


from ...components.soundsensor import MicrophoneSoundSensorBackend
AudioValidatorRoutine.registerBackend(MicrophoneSoundSensorBackend)
