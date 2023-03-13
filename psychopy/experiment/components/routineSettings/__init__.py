#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from psychopy.experiment.components import BaseComponent, Param, _translate
from psychopy.experiment.utils import CodeGenerationException
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
            skipIf="",
            disabled=False
    ):
        self.type = 'RoutineSettings'
        self.exp = exp  # so we can access the experiment if necess
        self.parentName = parentName  # to access the routine too if needed
        self.params = {}
        self.depends = []
        super(RoutineSettingsComponent, self).__init__(exp, parentName, name=parentName, disabled=disabled)
        self.order += []

        # --- Params ---

        # Delete inapplicable params
        del self.params['startType']
        del self.params['startVal']
        del self.params['startEstim']
        del self.params['saveStartStop']
        del self.params['syncScreenRefresh']

        # Modify disabled label
        self.params['disabled'].label = _translate("Disable Routine")
        # Modify stop type param
        self.params['stopType'].allowedVals = ['duration (s)', 'frame N', 'condition']
        self.params['stopVal'].label = _translate("Timeout")
        self.params['stopVal'].hint = _translate(
            "When should this Routine end, if not already ended by a Component? Leave blank for endless."
        )
        self.params['stopType'].hint = _translate(
            "When should this Routine end, if not already ended by a Component?"
        )

        # Flow params
        self.params['skipIf'] = Param(
            skipIf, valType='code', inputType="single", allowedTypes=[], categ='Basic',
            updates='constant',
            hint=_translate(
                "Skip this Routine if the value in this contorl evaluates to True. Leave blank to not skip."
            ),
            label=_translate("Skip if..."))

    def writeRoutineStartCode(self, buff):
        # Sanitize
        params = self.params.copy()
        # Skip Routine if condition is met
        if params['skipIf'].val not in ('', None, -1, 'None'):
            code = (
                "# skip this Routine if its 'Skip if' condition is True\n"
                "continueRoutine = continueRoutine and not (%(skipIf)s)\n"
            )
            buff.writeIndentedLines(code % params)

    def writeStartCode(self, buff):
        pass

    def writeInitCode(self, buff):
        pass

    def writeInitCodeJS(self, buff):
        pass

    def writeFrameCode(self, buff):
        # Sanitize
        params = self.params.copy()
        # Get current loop
        if len(self.exp.flow._loopList):
            params['loop'] = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            params['loop'] = self.exp._expHandler
        # Write stop test
        if self.params['stopVal'].val not in ('', None, -1, 'None'):
            if self.params['stopType'].val == 'duration (s)':
                # Stop after given number of seconds
                code = (
                    f"# is it time to end the routine? (based on local clock)\n"
                    f"if tThisFlip > %(stopVal)s-frameTolerance:\n"
                )
            elif self.params['stopType'].val == 'frame N':
                # Stop at given frame num
                code = (
                    f"# is it time to end the routine? (based on frames since Routine start)\n"
                    f"if frameN >= %(stopVal)s:\n"
                )
            elif self.params['stopType'].val == 'condition':
                # Stop when condition is True
                code = (
                    f"# is it time to end the routine? (based on condition)\n"
                    f"if bool(%(stopVal)s):\n"
                )
            else:
                msg = "Didn't write any stop line for stopType=%(stopType)s"
                raise CodeGenerationException(msg % params)
            # Contents of if statement
            code += (
                "    continueRoutine = False\n"
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
