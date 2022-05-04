# -*- coding: utf-8 -*-
"""
Created on Fri Apr 28 11:20:49 2017

@author: mrbki
"""
from os import path
import json
from pathlib import Path
from psychopy.experiment.components import getInitVals
from psychopy.experiment.routines import BaseStandaloneRoutine
from psychopy.localization import _translate, _localized as __localized

_localized = __localized.copy()

CORTEX_OBJ = 'cortex_obj'


class EmotivRecordingRoutine(BaseStandaloneRoutine):  # or (VisualComponent)

    categories = ['EEG']
    targets = ['PsychoPy', 'PsychoJS']
    iconFile = Path(__file__).parent / 'emotiv_record.png'
    tooltip = _translate('Initialize EMOTIV hardware connection')

    def __init__(self, exp, name='cortex_rec'):
        super(EmotivRecordingRoutine, self).__init__(
            exp, name=name
        )
        self.exp.requireImport(importName='emotiv',
                               importFrom='psychopy.hardware')
        self.type = 'EmotivRecording'

        del self.params['stopType']
        del self.params['stopVal']

    def writeMainCode(self, buff):
        inits = getInitVals(self.params, 'PsychoPy')
        code = ('{} = visual.BaseVisualStim('.format(inits['name']) +
                'win=win, name="{}")\n'.format(inits['name'])
                )
        buff.writeIndentedLines(code)
        code = ("{} = emotiv.Cortex(subject=expInfo['participant'])\n"
                .format(CORTEX_OBJ))
        buff.writeIndentedLines(code)

    def writeRoutineBeginCodeJS(self, buff):
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
