#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from psychopy.experiment.components import BaseComponent, Param, _translate, getInitVals
from psychopy import prefs

devices = ["default"]


class WebcamComponent(BaseComponent):
    """

    """
    categories = ['Responses']
    targets = ["PsychoPy"]
    iconFile = Path(__file__).parent / 'webcam.png'
    tooltip = _translate('Webcam: Record video from a webcam.')
    beta = True

    def __init__(
            # Basic
            self, exp, parentName,
            name='webcam',
            startType='time (s)', startVal='0', startEstim='',
            stopType='duration (s)', stopVal='', durationEstim='',
            device="Default",
            # Data
            outputFileType=".mp4",
            saveStartStop=True, syncScreenRefresh=False,
            # Testing
            disabled=False,
    ):
        # Mark as type
        self.type = 'Webcam'
        # Store exp references
        self.exp = exp
        self.parentName = parentName
        # Initialise superclass
        super(WebcamComponent, self).__init__(
            exp, parentName,
            name=name,
            startType=startType, startVal=startVal, startEstim=startEstim,
            stopType=stopType, stopVal=stopVal, durationEstim=durationEstim,
            # Data
            saveStartStop=saveStartStop, syncScreenRefresh=syncScreenRefresh,
            # Testing
            disabled=disabled,
        )
        # Define parameters
        msg = _translate("What webcam device would you like the use to record? This will only affect local "
                         "experiments - online experiments ask the participant which webcam to use.")
        self.params['device'] = Param(
            device, valType='str', inputType="choice", categ="Basic",
            allowedVals=list(devices),
            allowedLabels=[d.title() for d in list(devices)],
            hint=msg,
            label=_translate("Device")
        )

        msg = _translate("What file format would you like the video to be saved as?")
        self.params['outputFileType'] = Param(
            outputFileType, valType='str', inputType="choice", categ="Data",
            allowedVals=[".mp4", ".mov", ".mpeg", ".mkv"],
            hint=msg,
            label=_translate("Output File Type")
        )

    def writeRoutineStartCode(self, buff):
        pass

    def writeStartCode(self, buff):
        pass

    def writeInitCode(self, buff):
        inits = getInitVals(self.params, "PsychoPy")

        code = (
            "%(name)s = hardware.webcam.Webcam(\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(+1, relative=True)
        code = (
            "win, name=%(name)s,\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
            ")\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeInitCodeJS(self, buff):
        code = (
            "\n"
            "// Unknown component ignored: %(name)s\n"
            "\n"
        )
        buff.writeIndentedLines(code % self.params)

    def writeFrameCode(self, buff):
        # Start webcam at component start
        self.writeStartTestCode(buff)
        code = (
            "%(name)s.start()\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)

        # Stop webcam at component stop
        self.writeStopTestCode(buff)
        code = (
            "%(name)s.stop()\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)

    def writeRoutineEndCode(self, buff):
        pass

    def writeExperimentEndCode(self, buff):
        pass
