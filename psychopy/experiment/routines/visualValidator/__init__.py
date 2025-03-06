#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from psychopy.alerts._alerts import alert
from psychopy.experiment import Param
from psychopy.experiment.plugins import PluginDevicesMixin, DeviceBackend
from psychopy.experiment.components import getInitVals
from psychopy.experiment.routines import Routine, BaseValidatorRoutine
from psychopy.localization import _translate


class VisualValidatorRoutine(BaseValidatorRoutine, PluginDevicesMixin):
    """
    Use a light sensor to confirm that visual stimuli are presented when they should be.
    """
    targets = ['PsychoPy']

    categories = ['Validation']
    iconFile = Path(__file__).parent / 'visual_validator.png'
    tooltip = _translate(
        "Use a light sensor to confirm that visual stimuli are presented when they should be."
    )
    deviceClasses = []
    version = "2025.1.0"

    def __init__(
            self,
            # basic
            exp, name='visualVal',
            findThreshold=True, threshold=0.5,
            # layout
            findSensor=True, sensorPos="(1, 1)", sensorSize="(0.1, 0.1)", sensorUnits="norm",
            # device
            deviceLabel="", deviceBackend="screenbuffer", channel="0",
    ):

        self.exp = exp  # so we can access the experiment if necess
        self.params = {}
        self.depends = []
        super(VisualValidatorRoutine, self).__init__(exp, name=name)
        self.order += []
        self.type = 'VisualValidator'

        exp.requirePsychopyLibs(['validation'])

        # --- Basic ---
        self.order += [
            "findThreshold",
            "threshold",
            "findSensor",
            "sensorPos",
            "sensorSize",
            "sensorUnits",
        ]
        self.params['findThreshold'] = Param(
            findThreshold, valType="bool", inputType="bool", categ="Basic",
            label=_translate("Find best threshold?"),
            hint=_translate(
                "Run a brief Routine to find the best threshold for the light sensor at experiment start?"
            )
        )
        self.params['threshold'] = Param(
            threshold, valType="code", inputType="single", categ="Basic",
            label=_translate("Threshold"),
            hint=_translate(
                "Light threshold at which the light sensor should register a positive, units go from 0 (least sensitive) to "
                "1 (most sensitive)."
            )
        )
        self.depends.append({
            "dependsOn": "findThreshold",  # if...
            "condition": "==True",  # is...
            "param": "threshold",  # then...
            "true": "hide",  # should...
            "false": "show",  # otherwise...
        })
        self.params['findSensor'] = Param(
            findSensor, valType="code", inputType="bool", categ="Basic",
            label=_translate("Find sensor?"),
            hint=_translate(
                "Run a brief Routine to find the size and position of the light sensor at experiment start?"
            )
        )
        self.params['sensorPos'] = Param(
            sensorPos, valType="list", inputType="single", categ="Basic",
            updates="constant", allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            label=_translate("Position [x,y]"),
            hint=_translate(
                "Position of the light sensor on the window."
            )
        )
        self.params['sensorSize'] = Param(
            sensorSize, valType="list", inputType="single", categ="Basic",
            updates="constant", allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            label=_translate("Size [x,y]"),
            hint=_translate(
                "Size of the area covered by the light sensor on the window."
            )
        )
        self.params['sensorUnits'] = Param(
            sensorUnits, valType="str", inputType="choice", categ="Basic",
            allowedVals=['from exp settings', 'deg', 'cm', 'pix', 'norm', 'height', 'degFlatPos', 'degFlat'],
            label=_translate("Spatial units"),
            hint=_translate(
                "Spatial units in which the light sensor size and position are specified."
            )
        )
        for param in ("sensorPos", "sensorSize", "sensorUnits"):
            self.depends.append({
                "dependsOn": "findSensor",  # if...
                "condition": "==True",  # is...
                "param": param,  # then...
                "true": "hide",  # should...
                "false": "show",  # otherwise...
            })

        del self.params['stopType']
        del self.params['stopVal']

        # --- Device ---
        self.order += [
            "deviceLabel",
            "deviceBackend",
            "channel",
        ]
        self.params['deviceLabel'] = Param(
            deviceLabel, valType="str", inputType="single", categ="Device",
            label=_translate("Device name"),
            hint=_translate(
                "A name to refer to this Component's associated hardware device by. If using the "
                "same device for multiple components, be sure to use the same name here."
            )
        )
        self.params['deviceBackend'] = Param(
            deviceBackend, valType="code", inputType="choice", categ="Device",
            allowedVals=self.getBackendKeys,
            allowedLabels=self.getBackendLabels,
            label=_translate("Light sensor type"),
            hint=_translate(
                "Type of light sensor to use."
            ),
            direct=False
        )
        self.params['channel'] = Param(
            channel, valType="code", inputType="single", categ="Device",
            label=_translate("Light sensor channel"),
            hint=_translate(
                "If relevant, a channel number attached to the light sensor, to distinguish it "
                "from other light sensors on the same port. Leave blank to use the first light sensor "
                "which can detect the Window."
            )
        )

        self.loadBackends()

    def writeDeviceCode(self, buff):
        """
        Code to setup the CameraDevice for this component.

        Parameters
        ----------
        buff : io.StringIO
            Text buffer to write code to.
        """
        # do usual backend-specific device code writing
        PluginDevicesMixin.writeDeviceCode(self, buff)
        # get inits
        inits = getInitVals(self.params)
        # get device handle
        code = (
            "%(deviceLabelCode)s = deviceManager.getDevice(%(deviceLabel)s)"
        )
        buff.writeOnceIndentedLines(code % inits)
        # find threshold if indicated
        if self.params['findThreshold']:
            code = (
                "# find threshold for light sensor\n"
                "%(deviceLabelCode)s.findThreshold(win, channel=%(channel)s)\n"
            )
        else:
            code = (
                "%(deviceLabelCode)s.setThreshold(%(threshold)s, channel=%(channel)s)"
            )
        buff.writeOnceIndentedLines(code % inits)
        # find pos if indicated
        if self.params['findSensor']:
            code = (
                "# find position and size of the light sensor\n"
                "%(deviceLabelCode)s.findSensor(win, channel=%(channel)s)\n"
            )
            buff.writeOnceIndentedLines(code % inits)

    def writeMainCode(self, buff):
        inits = getInitVals(self.params)
        # get Sensor
        code = (
            "# Sensor object for %(name)s\n"
            "%(name)sSensor = deviceManager.getDevice(%(deviceLabel)s)\n"
        )
        buff.writeIndentedLines(code % inits)

        if self.params['threshold'] and not self.params['findThreshold']:
            code = (
                "%(name)sSensor.setThreshold(%(threshold)s, channel=%(channel)s)\n"
            )
            buff.writeIndentedLines(code % inits)
        # find/set Sensor position
        if not self.params['findSensor']:
            code = ""
            # set units (unless None)
            if self.params['sensorUnits']:
                code += (
                    "%(name)sSensor.units = %(sensorUnits)s\n"
                )
            # set pos (unless None)
            if self.params['sensorPos']:
                code += (
                    "%(name)sSensor.pos = %(sensorPos)s\n"
                )
            # set size (unless None)
            if self.params['sensorSize']:
                code += (
                    "%(name)sSensor.size = %(sensorSize)s\n"
                )
            buff.writeIndentedLines(code % inits)
        # create validator object
        code = (
            "# validator object for %(name)s\n"
            "%(name)s = validation.VisualValidator(\n"
            "    win, %(name)sSensor, %(channel)s,\n"
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
            clockStr = "clock=globalClock"
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
        # choose attributes based on sync status
        if "syncScreenRefresh" in stim.params and stim.params['syncScreenRefresh']:
            startAttr = "tStartRefresh"
            stopAttr = "tStopRefresh"
        else:
            startAttr = "tStart"
            stopAttr = "tStop"
        # validate start time
        code = (
            "# validate {name} start time\n"
            "if {name}.status == STARTED and %(name)s.status == STARTED:\n"
            "    %(name)s.tStart, %(name)s.tStartDelay = %(name)s.validate(state=True, t={name}.{startAttr})\n"
            "    if %(name)s.tStart is not None:\n"
            "        %(name)s.status = FINISHED\n"
        )
        if stim.params['saveStartStop']:
            # save validated start time if stim requested
            code += (
            "        thisExp.addData('{name}.%(name)s.started', %(name)s.tStart)\n"
            "        thisExp.addData('%(name)s.startDelay', %(name)s.tStartDelay)\n"
            )
        buff.writeIndentedLines(code.format(startAttr=startAttr, **stim.params) % self.params)

        # validate stop time
        code = (
            "# validate {name} stop time\n"
            "if {name}.status == FINISHED and %(name)s.status == STARTED:\n"
            "    %(name)s.tStop, %(name)s.tStopDelay = %(name)s.validate(state=False, t={name}.{stopAttr})\n"
            "    if %(name)s.tStop is not None:\n"
            "        %(name)s.status = FINISHED\n"
        )
        if stim.params['saveStartStop']:
            # save validated start time if stim requested
            code += (
            "        thisExp.addData('{name}.%(name)s.stopped', %(name)s.tStop)\n"
            "        thisExp.addData('{name}.%(name)s.stopDelay', %(name)s.tStopDelay)\n"
            )
        buff.writeIndentedLines(code.format(stopAttr=stopAttr, **stim.params) % self.params)

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


class ScreenBufferVisualValidatorBackend(DeviceBackend):
    """
    Adds a basic screen buffer emulation backend for VisualValidator, as well as acting as an
    example for implementing other light sensor device backends.
    """

    key = "screenbuffer"
    label = _translate("Screen Buffer (Debug)")
    component = VisualValidatorRoutine
    deviceClasses = ["psychopy.hardware.lightsensor.ScreenBufferSampler"]

    def getParams(self: VisualValidatorRoutine):
        # define order
        order = [
        ]
        # define params
        params = {}

        return params, order

    def addRequirements(self):
        # no requirements needed - so just return
        return

    def writeDeviceCode(self: VisualValidatorRoutine, buff):
        # get inits
        inits = getInitVals(self.params)
        # make ButtonGroup object
        code = (
            "deviceManager.addDevice(\n"
            "    deviceClass='psychopy.hardware.lightsensor.ScreenBufferSampler',\n"
            "    deviceName=%(deviceLabel)s,\n"
            "    win=win,\n"
            ")\n"
        )
        buff.writeOnceIndentedLines(code % inits)
