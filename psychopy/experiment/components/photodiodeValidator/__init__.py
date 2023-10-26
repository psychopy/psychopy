#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from psychopy.experiment import Param
from psychopy.experiment.components import BaseComponent, getInitVals
from psychopy.experiment.routines import Routine
from psychopy.localization import _translate


class PhotodiodeValidatorComponent(BaseComponent):
    """
    Use a photodiode to confirm that stimuli are presented when they should be.
    """
    targets = ['PsychoPy']

    categories = ['Validation']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'photodiode_validator.png'
    tooltip = _translate('Unknown: A component that is not known by the current '
                         'installed version of PsychoPy\n(most likely from the '
                         'future)')

    def __init__(
            self,
            # basic
            exp, parentName, name='photodiode',
            variability="1/60", report="log",
            findThreshold=True, threshold=127,
            # layout
            findDiode=True, diodePos="(1, 1)", diodeSize="(0.1, 0.1)", diodeUnits="norm",
            # device
            backend="bbtk-tpad", port="", number="1",
            # data
            saveValid=True,
    ):

        self.exp = exp  # so we can access the experiment if necess
        self.params = {}
        self.depends = []
        super(PhotodiodeValidatorComponent, self).__init__(exp, parentName, name=name)
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
        del self.params['durationEstim']
        del self.params['startVal']
        del self.params['startType']
        del self.params['startEstim']

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
        self.params['number'] = Param(
            number, valType="code", inputType="single", categ="Device",
            label=_translate("Device number"),
            hint=_translate(
                "If relevant, a device number attached to the photodiode, to distinguish it from other photodiodes on "
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

    def writeInitCode(self, buff):
        inits = getInitVals(self.params)
        # construct tpad name
        inits['padName'] = "TPad" + inits['port'].val
        # add TPad (only once per pad)
        code = (
            "# add TPad to device manager\n"
            "%(padName)s = tpad.TPad(name='%(padName)s', port=%(port)s)\n"
        )
        buff.writeOnceIndentedLines(code % inits)
        # initialise diode
        if self.params['backend'] == "bbtk-tpad":
            code = (
                "# diode object for %(name)s\n"
                "%(name)sTPad = %(padName)s\n"
                "%(name)sDiode = %(name)sTPad.photodiodes[%(number)s]\n"
            )
            buff.writeIndentedLines(code % inits)
        else:
            raise NotImplementedError(f"Backend %(backend)s is not supported." % self.params)
        # create validator object
        code = (
            "# validator object for %(name)s\n"
            "%(name)s = phd.PhotodiodeValidator(\n"
            "    win, %(name)sDiode,\n"
        )
        if not self.params['findDiode']:
            # specify pos, size and units if told not to find diode
            code += (
            "    diodePos=%(diodePos)s, diodeSize=%(diodeSize)s, diodeUnits=%(diodeUnits)s,\n"
            )
        if not self.params['findThreshold']:
            code += (
            "    diodeThreshold=%(threshold)s,"
            )
        code += (
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

    def writeRoutineStartCode(self, buff):
        # sync component start/stop timers with validator clocks
        for comp in self.findConnectedStimuli():
            # choose a clock to sync to according to component's params
            if "syncScreenRefresh" in comp.params and comp.params['syncScreenRefresh']:
                clockStr = ""
            else:
                clockStr = "clock=routineTimer"
            # otherwise sync its clock
            code = (
                f"# synchronise device clock for %(name)s with Routine timer\n"
                f"%(name)s.resetTimer({clockStr})\n"
            )
            buff.writeIndentedLines(code % self.params)

    def writeFrameCode(self, buff):
        # write validation code for each stim
        for stim in self.findConnectedStimuli():
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

