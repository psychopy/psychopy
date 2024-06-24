#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from psychopy.experiment.components import BaseComponent, Param, _translate
from psychopy.experiment.utils import CodeGenerationException


class RoutineSettingsComponent(BaseComponent):
    """
    """
    categories = ['Other']
    targets = ['PsychoPy', 'PsychoJS']
    iconFile = Path(__file__).parent / 'routineSettings.png'
    tooltip = _translate('Settings for this Routine.')
    version = "2023.2.0"

    def __init__(
            self, exp, parentName,
            # Basic
            name='',
            desc="",
            # Flow
            skipIf="",
            forceNonSlip=False,
            # Window
            useWindowParams=False,
            color="$[0,0,0]",
            colorSpace="rgb",
            backgroundImg="",
            backgroundFit="none",
            # Testing
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
        del self.params['syncScreenRefresh']

        # Modify disabled label
        self.params['disabled'].label = _translate("Disable Routine")
        # Modify stop type param
        self.params['stopType'].categ = "Flow"
        self.params['stopType'].allowedVals = ['duration (s)', 'frame N', 'condition']
        self.params['stopType'].hint = _translate(
            "When should this Routine end, if not already ended by a Component?"
        )
        # Mofidy stop val param
        self.params['stopVal'].categ = "Flow"
        self.params['stopVal'].label = _translate("Timeout")
        self.params['stopVal'].hint = _translate(
            "When should this Routine end, if not already ended by a Component? Leave blank for endless."
        )
        # Modify stop estim param
        self.params['durationEstim'].categ = "Flow"

        # --- Flow params ---
        self.order += [
            "forceNonSlip",
            "skipIf",
        ]
        self.params['forceNonSlip'] = Param(
            forceNonSlip, valType="code", inputType="bool", categ="Flow",
            hint=_translate(
                "If this Routine ended by hitting its max duration, reset the timer by subtracting the max duration rather than resetting to 0. Only tick this if you're sure you know how long the Routine is going to take, otherwise you'll get incorrect timestamps in the next Routine!"
            ),
            label=_translate("Non-slip timing")
        )
        self.params['skipIf'] = Param(
            skipIf, valType='code', inputType="single", categ='Flow',
            updates='constant',
            hint=_translate(
                "Skip this Routine if the value in this contorl evaluates to True. Leave blank to not skip."
            ),
            label=_translate("Skip if..."))

        # --- Documentation params ---
        self.params['desc'] = Param(
            desc, valType="str", inputType="multi", categ="Basic",
            updates="constant",
            hint=_translate(
                "Some descriptive text to give information about this Routine. "
                "This won't affect how it runs, it's purely for your own "
                "reference!"
            ),
            label=_translate("Description"),
            direct=False
        )

        # --- Window params ---
        self.order += [
            "useWindowParams",
            "color",
            "colorSpace",
            "backgroundImg",
            "backgroundFit"
        ]

        self.params['useWindowParams'] = Param(
            useWindowParams, valType="bool", inputType="bool", categ="Window",
            label=_translate("Different window settings?"),
            hint=_translate(
                "Should the appearance of the window change while this Routine "
                "is running?"
            ))
        self.params['color'] = Param(
            color, valType='color', inputType="color", categ="Window",
            label=_translate("Background color"),
            hint=_translate(
                "Color of the screen this Routine (e.g. black, $[1.0,1.0,1.0],"
                " $variable. Right-click to bring up a "
                "color-picker.)"
            ))
        self.params['colorSpace'] = Param(
            colorSpace, valType='str', inputType="choice", categ="Window",
            hint=_translate("Needed if color is defined numerically (see "
                            "PsychoPy documentation on color spaces)"),
            allowedVals=['rgb', 'dkl', 'lms', 'hsv', 'hex'],
            label=_translate("Color space"))
        self.params['backgroundImg'] = Param(
            backgroundImg, valType="str", inputType="file", categ="Window",
            hint=_translate("Image file to use as a background (leave blank for no image)"),
            label=_translate("Background image")
        )
        self.params['backgroundFit'] = Param(
            backgroundFit, valType="str", inputType="choice", categ="Window",
            allowedVals=("none", "cover", "contain", "fill", "scale-down"),
            hint=_translate("How should the background image scale to fit the window size?"),
            label=_translate("Background fit")
        )
        # useWindowParams should toggle all window params
        for thisParam in (
                "color", "colorSpace", "backgroundImg", "backgroundFit"):
            self.depends += [{
                "dependsOn": "useWindowParams",  # if...
                "condition": "",  # is...
                "param": thisParam,  # then...
                "true": "show",  # should...
                "false": "hide",  # otherwise...
            }]

        # --- Data params ---
        self.params['saveStartStop'].hint = _translate(
            "Save the start and stop times of this Routine (according to the global clock) to the data file."
        )

    def writeRoutineStartCode(self, buff):
        # Sanitize
        params = self.params.copy()
        if params['stopVal'] in ("None", None, ""):
            params['stopVal'].val = "None"
        # store start times
        code = (
            "# store start times for %(name)s\n"
            "%(name)s.tStartRefresh = win.getFutureFlipTime(clock=globalClock)\n"
            "%(name)s.tStart = globalClock.getTime(format='float')\n"
            "%(name)s.status = STARTED\n"
        )
        buff.writeIndentedLines(code % self.params)
        # add to data file if requested
        if self.params['saveStartStop']:
            code = (
            "thisExp.addData('%(name)s.started', %(name)s.tStart)\n"
            )
            buff.writeIndentedLines(code % params)
        # calculate expected Routine duration
        if self.params['stopType'] == "duration (s)":
            code = (
                "%(name)s.maxDuration = %(stopVal)s\n"
            )
            buff.writeIndentedLines(code % params)
        # Skip Routine if condition is met
        if params['skipIf'].val not in ('', None, -1, 'None'):
            code = (
                "# skip Routine %(name)s if its 'Skip if' condition is True\n"
                "%(name)s.skipped = continueRoutine and not (%(skipIf)s)\n"
                "continueRoutine = %(name)s.skipped\n"
            )
            buff.writeIndentedLines(code % params)
        # Change window appearance for this Routine (if requested)
        if params['useWindowParams']:
            code = (
                "win.color = %(color)s\n"
                "win.colorSpace = %(colorSpace)s\n"
                "win.backgroundImage = %(backgroundImg)s\n"
                "win.backgroundFit = %(backgroundFit)s\n"
            )
            buff.writeIndentedLines(code % params)

    def writeRoutineStartCodeJS(self, buff):
        # Sanitize
        params = self.params.copy()
        if params['stopVal'] in ("None", None, ""):
            params['stopVal'].val = "None"
        # Store Routine start time (UTC)
        if self.params['saveStartStop']:
            code = (
                "psychoJS.experiment.addData('%(name)s.started', globalClock.getTime());\n"
            )
            buff.writeIndentedLines(code % params)
        # Skip Routine if condition is met
        if params['skipIf'].val not in ('', None, -1, 'None'):
            code = (
                "// skip this Routine if its 'Skip if' condition is True\n"
                "continueRoutine = continueRoutine && !(%(skipIf)s);\n"
                "maxDurationReached = False\n"
            )
            buff.writeIndentedLines(code % params)
        # calculate expected Routine duration
        if self.params['stopType'] == "duration (s)":
            code = (
                "%(name)sMaxDuration = %(stopVal)s\n"
            )
            buff.writeIndentedLines(code % params)
        # Change window appearance for this Routine (if requested)
        if params['useWindowParams']:
            code = (
                "%(name)sStartWinParams = {\n"
                "    'color': psychoJS.window.color,\n"
                "    'colorSpace': psychoJS.window.colorSpace,\n"
                "    'backgroundImage': psychoJS.window.backgroundImage,\n"
                "    'backgroundFit': psychoJS.window.backgroundFit,\n"
                "};\n"
                "psychoJS.window.color = %(color)s;\n"
                "psychoJS.window.colorSpace = %(colorSpace)s;\n"
                "psychoJS.window.backgroundImage = %(backgroundImg)s;\n"
                "psychoJS.window.backgroundFit = %(backgroundFit)s;\n"
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
                    f"# is it time to end the Routine? (based on local clock)\n"
                    f"if tThisFlip > %(name)s.maxDuration-frameTolerance:\n"
                    f"    %(name)s.maxDurationReached = True\n"
                )
            elif self.params['stopType'].val == 'frame N':
                # Stop at given frame num
                code = (
                    f"# is it time to end the Routine? (based on frames since Routine start)\n"
                    f"if frameN >= %(stopVal)s:\n"
                )
            elif self.params['stopType'].val == 'condition':
                # Stop when condition is True
                code = (
                    f"# is it time to end the Routine? (based on condition)\n"
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

    def writeFrameCodeJS(self, buff):
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
                    f"// is it time to end the Routine? (based on local clock)\n"
                    f"if (t > %(name)sMaxDuration) {{\n"
                    f"    maxDurationReached = True\n"
                )
            elif self.params['stopType'].val == 'frame N':
                # Stop at given frame num
                code = (
                    f"// is it time to end the Routine? (based on frames since Routine start)\n"
                    f"if (frameN >= %(stopVal)s) {{\n"
                )
            elif self.params['stopType'].val == 'condition':
                # Stop when condition is True
                code = (
                    f"// is it time to end the Routine? (based on condition)\n"
                    f"if (Boolean(%(stopVal)s)) {{\n"
                )
            else:
                msg = "Didn't write any stop line for stopType=%(stopType)s"
                raise CodeGenerationException(msg % params)
            # Contents of if statement
            code += (
                "    continueRoutine = false\n"
                "}\n"
            )
            buff.writeIndentedLines(code % self.params)

    def writeRoutineEndCode(self, buff):
        params = self.params.copy()
        # store stop times
        code = (
            "# store stop times for %(name)s\n"
            "%(name)s.tStop = globalClock.getTime(format='float')\n"
            "%(name)s.tStopRefresh = tThisFlipGlobal\n"
        )
        buff.writeIndentedLines(code % params)
        # add to data file if requested
        if self.params['saveStartStop']:
            code = (
                "thisExp.addData('%(name)s.stopped', %(name)s.tStop)\n"
            )
            buff.writeIndentedLines(code % params)
        # Restore window appearance after this Routine (if changed)
        if params['useWindowParams']:
            code = (
                "setupWindow(expInfo=expInfo, win=win)\n"
            )
            buff.writeIndentedLines(code % params)

    def writeRoutineEndCodeJS(self, buff):
        params = self.params.copy()
        # Store Routine start time (UTC)
        if self.params['saveStartStop']:
            code = (
                "psychoJS.experiment.addData('%(name)s.stopped', globalClock.getTime());\n"
            )
            buff.writeIndentedLines(code % params)
        # Restore window appearance after this Routine (if changed)
        if params['useWindowParams']:
            code = (
                "psychoJS.window.color = %(name)sStartWinParams['color'];\n"
                "psychoJS.window.colorSpace = %(name)sStartWinParams['colorSpace'];\n"
                "psychoJS.window.backgroundImage = %(name)sStartWinParams['backgroundImage'];\n"
                "psychoJS.window.backgroundFit = %(name)sStartWinParams['backgroundFit'];\n"
            )
            buff.writeIndentedLines(code % params)

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
