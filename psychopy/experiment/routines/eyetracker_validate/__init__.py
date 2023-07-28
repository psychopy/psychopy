from copy import deepcopy

from .. import BaseStandaloneRoutine
from psychopy.localization import _translate
from psychopy.experiment import Param
from pathlib import Path
from psychopy.alerts import alert

positions = ['THREE_POINTS', 'FIVE_POINTS', 'NINE_POINTS', "THIRTEEN_POINTS", "SEVENTEEN_POINTS"]


class EyetrackerValidationRoutine(BaseStandaloneRoutine):
    categories = ['Eyetracking']
    targets = ["PsychoPy"]
    version = "2021.2.0"
    iconFile = Path(__file__).parent / "eyetracker_valid.png"
    tooltip = _translate("Validation routine for eyetrackers")
    beta = True

    def __init__(self, exp, name='validation',
                 showCursor=True, cursorFillColor="green",
                 innerFillColor='green', innerBorderColor='black', innerBorderWidth=2, innerRadius=0.0035,
                 fillColor='', borderColor="black", borderWidth=2, outerRadius=0.01,
                 colorSpace="rgb", units='from exp settings', textColor="auto",
                 randomisePos=True, targetLayout="NINE_POINTS", targetPositions="NINE_POINTS",
                 progressMode="time", targetDur=1.5, expandDur=1, expandScale=1.5,
                 movementAnimation=True, movementDur=1.0, targetDelay=1.0,
                 saveAsImg=False, showResults=True,
                 disabled=False
                 ):
        # Initialise base routine
        BaseStandaloneRoutine.__init__(self, exp, name=name, disabled=disabled)
        self.url = "https://psychopy.org/builder/components/eyetracker_validation.html"

        self.exp.requirePsychopyLibs(['iohub', 'hardware'])

        # Define relationships
        self.depends = [  # allows params to turn each other off/on
            # Only enable positions if targetLayout is custom
            {"dependsOn": "targetLayout",  # must be param name
             "condition": "=='custom...'",  # val to check for
             "param": "positions",  # param property to alter
             "true": "show",  # what to do with param if condition is True
             "false": "hide",  # permitted: hide, show, enable, disable
             },
        ]

        # Basic params
        del self.params['stopVal']
        del self.params['stopType']

        self.order += [
            "targetLayout",
            "targetPositions",
            "randomisePos",
            "showCursor",
            "cursorFillColor",
            "textColor"
        ]

        self.params['targetLayout'] = Param(targetLayout,
                                            valType='str', inputType="choice", categ='Basic',
                                            allowedVals=positions + ["CUSTOM..."],
                                            hint=_translate("Pre-defined target layouts"),
                                            label=_translate("Target layout"))

        self.depends.append(
            {"dependsOn": "targetLayout",  # must be param name
             "condition": "not in {}".format(positions),  # val to check for
             "param": "targetPositions",  # param property to alter
             "true": "show",  # what to do with param if condition is True
             "false": "hide",  # permitted: hide, show, enable, disable
             }
        )

        self.params['targetPositions'] = Param(targetPositions,
                                               valType='list', inputType="single", categ='Basic',
                                               hint=_translate(
                                                   "List of positions (x, y) at which the target can appear"),
                                               label=_translate("Target positions"))

        self.params['randomisePos'] = Param(randomisePos,
                                            valType='bool', inputType="bool", categ='Basic',
                                            hint=_translate("Should the order of target positions be randomised?"),
                                            label=_translate("Randomise target positions"))

        self.params['cursorFillColor'] = Param(cursorFillColor,
                                               valType="color", inputType="color", categ="Basic",
                                               hint=_translate("Fill color of the gaze cursor"),
                                               label=_translate("Gaze cursor color"))

        self.params['textColor'] = Param(textColor,
                                               valType="color", inputType="color", categ="Basic",
                                               hint=_translate("Color of text used in validation procedure."),
                                               label=_translate("Text color"))

        # Target Params
        self.order += [
            "targetStyle",
            "fillColor",
            "borderColor",
            "innerFillColor",
            "innerBorderColor",
            "colorSpace",
            "borderWidth",
            "innerBorderWidth",
            "outerRadius",
            "innerRadius",
        ]

        self.params['innerFillColor'] = Param(innerFillColor,
                                              valType='color', inputType="color", categ='Target',
                                              hint=_translate("Fill color of the inner part of the target"),
                                              label=_translate("Inner fill color"))

        self.params['innerBorderColor'] = Param(innerBorderColor,
                                                valType='color', inputType="color", categ='Target',
                                                hint=_translate("Border color of the inner part of the target"),
                                                label=_translate("Inner border color"))

        self.params['fillColor'] = Param(fillColor,
                                         valType='color', inputType="color", categ='Target',
                                         hint=_translate("Fill color of the outer part of the target"),
                                         label=_translate("Outer fill color"))

        self.params['borderColor'] = Param(borderColor,
                                           valType='color', inputType="color", categ='Target',
                                           hint=_translate("Border color of the outer part of the target"),
                                           label=_translate("Outer border color"))

        self.params['colorSpace'] = Param(colorSpace,
                                          valType='str', inputType="choice", categ='Target',
                                          allowedVals=['rgb', 'dkl', 'lms', 'hsv'],
                                          hint=_translate(
                                              "In what format (color space) have you specified the colors? (rgb, dkl, lms, hsv)"),
                                          label=_translate("Color space"))

        self.params['borderWidth'] = Param(borderWidth,
                                           valType='num', inputType="single", categ='Target',
                                           hint=_translate("Width of the line around the outer part of the target"),
                                           label=_translate("Outer border width"))

        self.params['innerBorderWidth'] = Param(innerBorderWidth,
                                                valType='num', inputType="single", categ='Target',
                                                hint=_translate(
                                                    "Width of the line around the inner part of the target"),
                                                label=_translate("Inner border width"))

        self.params['outerRadius'] = Param(outerRadius,
                                           valType='num', inputType="single", categ='Target',
                                           hint=_translate("Size (radius) of the outer part of the target"),
                                           label=_translate("Outer radius"))

        self.params['innerRadius'] = Param(innerRadius,
                                           valType='num', inputType="single", categ='Target',
                                           hint=_translate("Size (radius) of the inner part of the target"),
                                           label=_translate("Inner radius"))

        self.params['units'] = Param(units,
                                     valType='str', inputType="choice", categ='Target',
                                     allowedVals=['from exp settings'], direct=False,
                                     hint=_translate("Units of dimensions for this stimulus"),
                                     label=_translate("Spatial units"))

        # Animation Params
        self.order += [
            "progressMode",
            "targetDur",
            "expandDur",
            "expandScale",
            "movementAnimation",
            "movementDur",
            "targetDelay"
        ]

        self.params['progressMode'] = Param(progressMode,
                                            valType="str", inputType="choice", categ="Animation",
                                            allowedVals=["space key", "time"],
                                            hint=_translate("Should the target move to the next position after a "
                                                            "keypress or after an amount of time?"),
                                            label=_translate("Progress mode"))

        self.depends.append(
            {"dependsOn": "progressMode",  # must be param name
             "condition": "in ['time', 'either']",  # val to check for
             "param": "targetDur",  # param property to alter
             "true": "show",  # what to do with param if condition is True
             "false": "hide",  # permitted: hide, show, enable, disable
             }
        )

        self.params['targetDur'] = Param(targetDur,
                                            valType='num', inputType="single", categ='Animation',
                                            hint=_translate(
                                                "Time limit (s) after which progress to next position"),
                                            label=_translate("Target duration"))

        self.depends.append(
            {"dependsOn": "progressMode",  # must be param name
             "condition": "in ['space key', 'either']",  # val to check for
             "param": "expandDur",  # param property to alter
             "true": "show",  # what to do with param if condition is True
             "false": "hide",  # permitted: hide, show, enable, disable
             }
        )

        self.params['expandDur'] = Param(expandDur,
                                           valType='num', inputType="single", categ='Animation',
                                           hint=_translate(
                                               "Duration of the target expand/contract animation"),
                                           label=_translate("Expand / contract duration"))

        self.params['expandScale'] = Param(expandScale,
                                           valType='num', inputType="single", categ='Animation',
                                           hint=_translate("How many times bigger than its size the target grows"),
                                           label=_translate("Expand scale"))

        self.params['movementAnimation'] = Param(movementAnimation,
                                           valType='bool', inputType="bool", categ='Animation',
                                           hint=_translate("Enable / disable animations as target stim changes position"),
                                           label=_translate("Animate position changes"))

        self.depends.append(
            {"dependsOn": "movementAnimation",  # must be param name
             "condition": "== True",  # val to check for
             "param": "movementDur",  # param property to alter
             "true": "show",  # what to do with param if condition is True
             "false": "hide",  # permitted: hide, show, enable, disable
             }
        )

        self.params['movementDur'] = Param(movementDur,
                                           valType='num', inputType="single", categ='Animation',
                                           hint=_translate(
                                               "Duration of the animation during position changes."),
                                           label=_translate("Movement duration"))

        self.depends.append(
            {"dependsOn": "movementAnimation",  # must be param name
             "condition": "== False",  # val to check for
             "param": "targetDelay",  # param property to alter
             "true": "show",  # what to do with param if condition is True
             "false": "hide",  # permitted: hide, show, enable, disable
             }
        )

        self.params['targetDelay'] = Param(targetDelay,
                                           valType='num', inputType="single", categ='Animation',
                                           hint=_translate(
                                               "Duration of the delay between positions."),
                                           label=_translate("Target delay"))

        # Data params
        self.order += [
            "saveAsImg",
            "showResults",
        ]

        self.params['saveAsImg'] = Param(saveAsImg,
            valType='bool', inputType="bool", categ='Data',
            hint=_translate(
                "Save results as an image"),
            label=_translate("Save as image"))

        self.params['showResults'] = Param(showResults,
            valType='bool', inputType="bool", categ='Data',
            hint=_translate(
                "Show a screen with results after completion?"),
            label=_translate("Show results screen"))

    def writeMainCode(self, buff):
        # Alert user if eyetracking isn't setup
        if self.exp.eyetracking == "None":
            alert(code=4505)

        # Get inits
        inits = deepcopy(self.params)
        # Code-ify 'from exp settings'
        if inits['units'].val == 'from exp settings':
            inits['units'].val = None
        # Synonymise expand dur and target dur
        if inits['progressMode'].val == 'time':
            inits['expandDur'] = inits['targetDur']
        if inits['progressMode'].val == 'space key':
            inits['targetDur'] = inits['expandDur']
        # Synonymise movement dur and target delay
        if inits['movementAnimation'].val:
            inits['targetDelay'] = inits['movementDur']
        else:
            inits['movementDur'] = inits['targetDelay']
        # Convert progress mode to ioHub format
        if inits['progressMode'].val == 'space key':
            inits['progressKey'] = "'space'"
        else:
            inits['progressKey'] = "None"
        # If positions are preset, override param value
        if inits['targetLayout'].val in positions:
            inits['targetPositions'].val = inits['targetLayout'].val
            inits['targetPositions'].valType = 'str'

        BaseStandaloneRoutine.writeMainCode(self, buff)

        # Make target
        code = (
            "# define target for %(name)s\n"
            "%(name)sTarget = visual.TargetStim(win, \n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
                "name='%(name)sTarget',\n"
                "radius=%(outerRadius)s, fillColor=%(fillColor)s, borderColor=%(borderColor)s, lineWidth=%(borderWidth)s,\n"
                "innerRadius=%(innerRadius)s, innerFillColor=%(innerFillColor)s, innerBorderColor=%(innerBorderColor)s, innerLineWidth=%(innerBorderWidth)s,\n"
                "colorSpace=%(colorSpace)s, units=%(units)s\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
            ")"
        )
        buff.writeIndentedLines(code % inits)

        # Make validation object
        code = (
            "# define parameters for %(name)s\n"
            "%(name)s = iohub.ValidationProcedure(win,\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)

        code = (
                "target=%(name)sTarget,\n"
                "gaze_cursor=%(cursorFillColor)s, \n"
                "positions=%(targetPositions)s, randomize_positions=%(randomisePos)s,\n"
                "expand_scale=%(expandScale)s, target_duration=%(targetDur)s,\n"
                "enable_position_animation=%(movementAnimation)s, target_delay=%(targetDelay)s,\n"
                "progress_on_key=%(progressKey)s, text_color=%(textColor)s,\n"
                "show_results_screen=%(showResults)s, save_results_screen=%(saveAsImg)s,\n"
                "color_space=%(colorSpace)s, unit_type=%(units)s\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
            ")\n"
        )
        buff.writeIndentedLines(code % inits)
        # Run
        code = (
            "# run %(name)s\n"
            "%(name)s.run()\n"
            "# clear any keypresses from during %(name)s so they don't interfere with the experiment\n"
            "defaultKeyboard.clearEvents()\n"
        )
        buff.writeIndentedLines(code % inits)
