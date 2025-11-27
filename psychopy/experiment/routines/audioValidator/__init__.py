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
    legacyParams = [
        # old device setup params, no longer needed as this is handled by DeviceManager
        "deviceBackend",
        "meMicrophone",
        "meThreshold",
        "meRange",
        "meSamplingWindow",
    ]

    def __init__(
            self,
            # basic
            exp, name='audioVal',
            # device
            deviceLabel="", channel="0",
            # legacy
            threshold=0.5, deviceBackend="microphone",
    ):

        self.exp = exp  # so we can access the experiment if necess
        self.params = {}
        self.depends = []
        super(AudioValidatorRoutine, self).__init__(exp, name=name)
        self.order += []
        self.type = 'AudioValidator'

        exp.requirePsychopyLibs(["validation"])

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
        # create validator object
        code = (
            "# validator object for %(name)s\n"
            "%(name)s = validation.AudioValidator(\n"
            "    deviceManager.getDevice(%(deviceLabel)s), \n"
            "    %(channel)s,\n"
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
            f"%(name)s.status = NOT_STARTED\n"
            f"# synchronise device clock for %(name)s with Routine timer\n"
            f"%(name)s.resetTimer({clockStr})\n"
        )
        buff.writeIndentedLines(code % self.params)
        # add blank entries for validation results
        if stim.params['saveStartStop']:
            code += (
            "thisExp.addData('{name}.%(name)s.started', None)\n"
            "thisExp.addData('%(name)s.startDelay', None)\n"
            "thisExp.addData('{name}.%(name)s.stopped', None)\n"
            "thisExp.addData('{name}.%(name)s.stopDelay', None)\n"
            )
        buff.writeIndentedLines(code.format(**stim.params) % self.params)

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

        # if stimulus ends with the Routine, raise an alert
        if stim.endsWithRoutine():
            alert(4160, strFields={'name': stim.name})
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

    def writeRoutineEndValidationCode(self, buff, stim):
        # end validator after Routine is finished
        code = (
            "%(name)s.status = FINISHED\n"
        )
        buff.writeIndentedLines(code % self.params)

        return 0

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
