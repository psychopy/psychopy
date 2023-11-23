#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from psychopy.experiment import Param
from psychopy.experiment.components import getInitVals
from psychopy.experiment.routines import Routine, BaseValidatorRoutine
from psychopy.localization import _translate


class PhotodiodeValidatorRoutine(BaseValidatorRoutine):
    """
    Use a photodiode to confirm that stimuli are presented when they should be.
    """
    targets = ['PsychoPy']

    categories = ['Validation']
    iconFile = Path(__file__).parent / 'photodiode_validator.png'
    tooltip = _translate('')

    def __init__(
            self,
            # basic
            exp, name='photodiode',
            variability="1/60", report="log",
            findThreshold=True, threshold=127,
            # layout
            findDiode=True, diodePos="(1, 1)", diodeSize="(0.1, 0.1)", diodeUnits="norm",
            # device
            backend="bbtk-tpad", port="", channel="1",
            # data
            saveValid=True,
    ):

        self.exp = exp  # so we can access the experiment if necess
        self.params = {}
        self.depends = []
        super(PhotodiodeValidatorRoutine, self).__init__(exp, name=name)
        self.order += []
        self.type = 'PhotodiodeValidator'

        exp.requireImport(
            importName="photodiode",
            importFrom="psychopy.hardware",
            importAs="phd"
        )
        exp.requireImport(
            importName="tpad",
            importFrom="psychopy_bbtk"
        )

        # --- Basic ---
        self.order += [
            "variability",
            "report",
            "findThreshold",
            "threshold",
            "findDiode",
            "diodePos",
            "diodeSize",
            "diodeUnits",
        ]

        self.params['variability'] = Param(
            variability, valType="code", inputType="single", categ="Basic",
            label=_translate("Variability (s)"),
            hint=_translate(
                "How much variation from intended presentation times (in seconds) is acceptable?"
            )
        )
        self.params['report'] = Param(
            report, valType="str", inputType="choice", categ="Basic",
            allowedVals=["log", "err"],
            allowedLabels=[_translate("Log warning"), _translate("Raise error")],
            label=_translate("On fail..."),
            hint=_translate(
                "What to do when the validation fails. Just log, or stop the script and raise an error?"
            )
        )
        self.params['findThreshold'] = Param(
            findThreshold, valType="bool", inputType="bool", categ="Basic",
            label=_translate("Find best threshold?"),
            hint=_translate(
                "Run a brief Routine to find the best threshold for the photodiode at experiment start?"
            )
        )
        self.params['threshold'] = Param(
            threshold, valType="code", inputType="single", categ="Basic",
            label=_translate("Threshold"),
            hint=_translate(
                "Light threshold at which the photodiode should register a positive, units go from 0 (least light) to "
                "255 (most light)."
            )
        )
        self.depends.append({
            "dependsOn": "findThreshold",  # if...
            "condition": "==True",  # is...
            "param": "threshold",  # then...
            "true": "hide",  # should...
            "false": "show",  # otherwise...
        })
        self.params['findDiode'] = Param(
            findDiode, valType="code", inputType="bool", categ="Basic",
            label=_translate("Find diode?"),
            hint=_translate(
                "Run a brief Routine to find the size and position of the photodiode at experiment start?"
            )
        )
        self.params['diodePos'] = Param(
            diodePos, valType="list", inputType="single", categ="Basic",
            updates="constant", allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            label=_translate("Position [x,y]"),
            hint=_translate(
                "Position of the photodiode on the window."
            )
        )
        self.params['diodeSize'] = Param(
            diodeSize, valType="list", inputType="single", categ="Basic",
            updates="constant", allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            label=_translate("Size [x,y]"),
            hint=_translate(
                "Size of the area covered by the photodiode on the window."
            )
        )
        self.params['diodeUnits'] = Param(
            diodeUnits, valType="str", inputType="choice", categ="Basic",
            allowedVals=['from exp settings', 'deg', 'cm', 'pix', 'norm', 'height', 'degFlatPos', 'degFlat'],
            label=_translate("Spatial units"),
            hint=_translate(
                "Spatial units in which the photodiode size and position are specified."
            )
        )
        for param in ("diodePos", "diodeSize", "diodeUnits"):
            self.depends.append({
                "dependsOn": "findDiode",  # if...
                "condition": "==True",  # is...
                "param": param,  # then...
                "true": "hide",  # should...
                "false": "show",  # otherwise...
            })

        del self.params['stopType']
        del self.params['stopVal']

        # --- Device ---
        self.order += [
            "backend",
            "port",
            "number",
        ]
        self.params['backend'] = Param(
            backend, valType="code", inputType="choice", categ="Device",
            allowedVals=["bbtk-tpad"],
            allowedLabels=["Black Box Toolkit (BBTK) TPad"],
            label=_translate("Photodiode type"),
            hint=_translate(
                "Type of photodiode to use."
            )
        )
        def getPorts():
            """
            Get list of available serial ports via hardware.serialdevice.
            """
            from psychopy.hardware.serialdevice import ports
            return list(ports)

        self.params['port'] = Param(
            port, valType="str", inputType="choice", categ="Device",
            allowedVals=getPorts,
            allowedLabels=getPorts,
            label=_translate("Serial port"),
            hint=_translate(
                "Serial port which the photodiode is connected to."
            )
        )
        self.params['channel'] = Param(
            channel, valType="code", inputType="single", categ="Device",
            label=_translate("Photodiode channel"),
            hint=_translate(
                "If relevant, a channel number attached to the photodiode, to distinguish it from other photodiodes on "
                "the same port."
            )
        )

        # --- Data ---
        self.params['saveValid'] = Param(
            saveValid, valType="code", inputType="bool", categ="Data",
            label=_translate('Save validation results'),
            hint=_translate(
                "Save validation results after validating on/offset times for stimuli"
            )
        )

    def _makeDeviceName(self):
        # get port
        port = self.params['port'].val
        # construct string
        name = f"photodiode{port}"

        return name

    def writeDeviceCode(self, buff):
        """
        Code to setup the CameraDevice for this component.

        Parameters
        ----------
        buff : io.StringIO
            Text buffer to write code to.
        """
        inits = getInitVals(self.params)

        # make device name
        inits['deviceName'] = self._makeDeviceName()
        # make deviceClass string
        if self.params['backend'] == "bbtk-tpad":
            inits['deviceClass'] = "psychopy_bbtk.tpad.TPadPhotodiodeGroup"
        else:
            raise NotImplementedError(f"Backend %(backend)s is not supported." % self.params)
        # initialise diode device
        code = (
            "# initialise photodiode\n"
            "%(deviceName)s = deviceManager.getDevice('%(deviceName)s')\n"
            "if %(deviceName)s is None:\n"
            "    %(deviceName)s = deviceManager.addDevice(\n"
            "        deviceClass='%(deviceClass)s',\n"
            "        deviceName='%(deviceName)s',\n"
            "        pad=%(port)s,\n"
            "        channels=2\n"
            "    )\n"
        )
        buff.writeOnceIndentedLines(code % inits)
        # find threshold if indicated
        if self.params['findThreshold']:
            code = (
                "# find threshold for photodiode\n"
                "if %(deviceName)s.getThreshold() is None:\n"
                "    %(deviceName)s.findThreshold(win, channel=%(channel)s)\n"
            )
            buff.writeOnceIndentedLines(code % inits)
        # find pos if indicated
        if self.params['findDiode']:
            code = (
                "# find position and size of photodiode\n"
                "if %(deviceName)s.pos is None and %(deviceName)s.size is None and %(deviceName)s.units is None:\n"
                "    %(deviceName)s.findPhotodiode(win, channel=%(channel)s)\n"
            )
            buff.writeOnceIndentedLines(code % inits)

    def writeMainCode(self, buff):
        inits = getInitVals(self.params)
        # make device name
        inits['deviceName'] = self._makeDeviceName()
        # get diode
        code = (
            "# diode object for %(name)s\n"
            "%(name)sDiode = deviceManager.getDevice('%(deviceName)s')\n"
        )
        buff.writeIndentedLines(code % inits)

        if self.params['threshold'] and not self.params['findThreshold']:
            code = (
                "%(name)sDiode.setThreshold(%(threshold)s, channels=[%(channel)s])\n"
            )
            buff.writeIndentedLines(code % inits)
        # find/set diode position
        if not self.params['findDiode']:
            code = ""
            # set units (unless None)
            if self.params['units']:
                code += (
                    "%(name)sDiode.units = %(units)s\n"
                )
            # set pos (unless None)
            if self.params['pos']:
                code += (
                    "%(name)sDiode.pos = %(pos)s\n"
                )
            # set size (unless None)
            if self.params['size']:
                code += (
                    "%(name)sDiode.size = %(size)s\n"
                )
            buff.writeIndentedLines(code % inits)
        # create validator object
        code = (
            "# validator object for %(name)s\n"
            "%(name)s = phd.PhotodiodeValidator(\n"
            "    win, %(name)sDiode, %(channel)s,\n"
            "    variability=%(variability)s,\n"
            "    report=%(report)s,\n"
            ")\n"
        )
        buff.writeIndentedLines(code % self.params)
        # connect stimuli
        for stim in self.findConnectedStimuli():
            code = (
                "# connect {stim} to %(name)s\n"
                "%(name)s.connectStimulus({stim})\n"
            ).format(stim=stim.params['name'])
            buff.writeIndentedLines(code % self.params)

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
            "    %(name)s.tStart, %(name)s.tStartValid = %(name)s.validate(state=True, t={name}.tStart)\n"
            "    if %(name)s.tStart is not None:\n"
            "        %(name)s.status = FINISHED\n"
        )
        if stim.params['saveStartStop']:
            # save validated start time if stim requested
            code += (
            "        thisExp.addData('{name}.%(name)s.started', %(name)s.tStart)\n"
            )
        if self.params['saveValid']:
            # save validation result if params requested
            code += (
            "        thisExp.addData('{name}.started.valid', %(name)s.tStartValid)\n"
            )
        buff.writeIndentedLines(code.format(**stim.params) % self.params)

        # validate stop time
        code = (
            "# validate {name} stop time\n"
            "if {name}.status == FINISHED and %(name)s.status == STARTED:\n"
            "    %(name)s.tStop, %(name)s.tStopValid = %(name)s.validate(state=False, t={name}.tStop)\n"
            "    if %(name)s.tStop is not None:\n"
            "        %(name)s.status = FINISHED\n"
        )
        if stim.params['saveStartStop']:
            # save validated start time if stim requested
            code += (
            "        thisExp.addData('{name}.%(name)s.stopped', %(name)s.tStop)\n"
            )
        if self.params['saveValid']:
            # save validation result if params requested
            code += (
            "        thisExp.addData('{name}.stopped.valid', %(name)s.tStopValid)\n"
            )
        buff.writeIndentedLines(code.format(**stim.params) % self.params)

        # return change in indent level
        return buff.indentLevel - startIndent

    def findConnectedStimuli(self):
        # list of linked components
        stims = []
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

        return stims

