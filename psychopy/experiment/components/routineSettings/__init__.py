#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from psychopy.experiment.components import BaseComponent, Param, _translate
from psychopy import prefs

# only use _localized values for label values, nothing functional:
_localized = {'name': _translate('Name')}


class RoutineSettingsComponent(BaseComponent):
    """
    """
    targets = ['PsychoPy']

    categories = ['Other']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'routineSettings.png'
    tooltip = _translate('Settings for this Routine.')

    def __init__(
            self, exp, parentName, name='',
            abortTrialOn="", endRoutineOn=""
    ):
        self.type = 'RoutineSettings'
        self.exp = exp  # so we can access the experiment if necess
        self.parentName = parentName  # to access the routine too if needed
        self.params = {}
        self.depends = []
        super(RoutineSettingsComponent, self).__init__(exp, parentName, name=name)
        self.order += []

        # --- Params ---

        # Delete base params
        del self.params['startType']
        del self.params['stopType']
        del self.params['startVal']
        del self.params['stopVal']
        del self.params['startEstim']
        del self.params['durationEstim']
        del self.params['saveStartStop']
        del self.params['syncScreenRefresh']

        # Flow params
        self.params['endRoutineOn'] = Param(
            endRoutineOn, valType='code', inputType="single", allowedTypes=[], categ='Basic',
            updates='constant',
            hint=_translate("When the statement entered here evaluates to True, the Routine will end."),
            label=_translate("End Routine if..."))

        self.params['abortTrialOn'] = Param(
            abortTrialOn, valType='code', inputType="single", allowedTypes=[], categ='Basic',
            updates='constant',
            hint=_translate("When the statement entered here evaluates to True, the trial will be aborted."),
            label=_translate("Abort trial if..."))


    def writeRoutineStartCode(self, buff):
        pass

    def writeStartCode(self, buff):
        pass

    def writeInitCode(self, buff):
        pass

    def writeInitCodeJS(self, buff):
        pass

    def writeFrameCode(self, buff):
        # Sanitize
        params = self.params.copy()
        if params['endRoutineOn'].val == "":
            params['endRoutineOn'].val = "False"
        if params['abortTrialOn'].val == "":
            params['abortTrialOn'].val = "False"
        # Write code
        code = (
            "# end Routine '%(name)s'?\n"
            "if %(endRoutineOn)s:\n"
            "    continueRoutine = False\n"
            # "# abort trial?\n"
            # "if %(abortTrialOn)s:\n"
            # "    continueRoutine = False\n"
        )
        buff.writeIndentedLines(code % self.params)

    def writeRoutineEndCode(self, buff):
        pass

    def writeExperimentEndCode(self, buff):
        pass

    def writeTimeTestCode(self, buff):
        pass

    def writeStartTestCode(self, buff):
        pass

    def writeStopTestCode(self, buff):
        pass

    def writeParamUpdates(self, buff, updateType, paramNames=None):
        pass

    def writeParamUpdate(self, buff, compName, paramName, val, updateType,
                         params=None):
        pass
