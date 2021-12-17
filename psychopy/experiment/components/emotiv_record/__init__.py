# -*- coding: utf-8 -*-
"""
Created on Fri Apr 28 11:20:49 2017

@author: mrbki
"""
from os import path
import json
from pathlib import Path
from psychopy.experiment.components import BaseComponent, getInitVals
from psychopy.localization import _translate, _localized as __localized

_localized = __localized.copy()

CORTEX_OBJ = 'cortex_obj'


class EmotivRecordingComponent(BaseComponent):  # or (VisualComponent)

    categories = ['EEG']
    targets = ['PsychoPy', 'PsychoJS']
    iconFile = Path(__file__).parent / 'emotiv_record.png'
    tooltip = _translate('Initialize EMOTIV hardware connection')

    def __init__(self, exp, parentName, name='cortex_rec'):
        super(EmotivRecordingComponent, self).__init__(
            exp, parentName, name=name,
            startType='time (s)', startVal=0,
            stopType='duration (s)', stopVal=1,
            startEstim='', durationEstim='',
            saveStartStop=False
        )
        self.exp.requireImport(importName='emotiv',
                               importFrom='psychopy.hardware')
        self.type = 'EmotivRecording'

    def writeInitCode(self, buff):
        inits = getInitVals(self.params, 'PsychoPy')
        code = ('{} = visual.BaseVisualStim('.format(inits['name']) +
                'win=win, name="{}")\n'.format(inits['name'])
                )
        buff.writeIndentedLines(code)
        code = ("{} = emotiv.Cortex(subject=expInfo['participant'])\n"
                .format(CORTEX_OBJ))
        buff.writeIndentedLines(code)

    def writeInitCodeJS(self, buff):
        inits = getInitVals(self.params, 'PsychoJS')
        obj = {"status": "PsychoJS.Status.NOT_STARTED"}
        code = '{} = {};\n'
        buff.writeIndentedLines(
            code.format(inits['name'], json.dumps(obj)))
        for param in inits:
            if inits[param] in [None, 'None', '']:
                inits[param].val = 'undefined'
                if param == 'text':
                    inits[param].val = ""

    def writeFrameCode(self, buff):
        pass

    def writeFrameCodeJS(self, buff):
        pass

    def writeExperimentEndCode(self, buff):
        code = (
                "core.wait(1) # Wait for EEG data to be packaged\n" +
                "{}.close_session()\n".format(CORTEX_OBJ)
        )
        buff.writeIndentedLines(code)

    def writeExperimentEndCodeJS(self, buff):
        code = 'if (typeof emotiv != "undefined") {\n'
        buff.writeIndented(code)
        buff.setIndentLevel(1, relative=True)
        code = 'if (typeof emotiv.end_experiment != "undefined") {\n'
        buff.writeIndented(code)
        buff.setIndentLevel(1, relative=True)
        code = 'emotiv.end_experiment();\n'
        buff.writeIndented(code)
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented('}\n')
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented('}\n')
