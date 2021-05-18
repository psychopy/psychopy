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
    iconFile = Path(__file__).parent / "eyetracker_valid.png"
    tooltip = _translate("Validation routine for eyetrackers")

    def __init__(self, exp, name='validation',
                 showCursor=True,
                 innerFillColor="red", innerBorderColor="", innerBorderWidth="", outerRadius=0.025,
                 fillColor="", borderColor="white", borderWidth=2, innerRadius=0.005,
                 colorSpace="rgb", units='from exp settings',
                 randomisePos=True, targetLayout="NINE_POINTS", targetPositions="NINE_POINTS",
                 progressMode="key", progressKey="'ENTER',", progressTime=1,
                 movementAnimation=True, movementDur=1.25,
                 expandAnimation=True, expandScale=3, expandDur=0.5,
                 saveAsImg=False, showResults=True
                 ):
        # Initialise base routine
        BaseStandaloneRoutine.__init__(self, exp, name=name)

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
            "targetPositions"
            "randomisePos",
            "showCursor",
        ]

        self.params['targetLayout'] = Param(targetLayout,
                                            valType='str', inputType="choice", categ='Basic',
                                            allowedVals=positions + ["CUSTOM..."],
                                            hint=_translate("Pre-defined target layouts"),
                                            label=_translate("Target Layout"))

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
                                               label=_translate("Target Positions"))

        self.params['randomisePos'] = Param(randomisePos,
                                            valType='bool', inputType="bool", categ='Basic',
                                            hint=_translate("Should the order of target positions be randomised?"),
                                            label=_translate("Randomise Target Positions"))

        self.params['showCursor'] = Param(showCursor,
            valType="bool", inputType="bool", categ="Basic",
            hint=_translate("Should a cursor be visible, showing where the participant is looking?"),
            label=_translate("Show Gaze Cursor"))

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
                                              label=_translate("Inner Fill Color"))

        self.params['innerBorderColor'] = Param(innerBorderColor,
                                                valType='color', inputType="color", categ='Target',
                                                hint=_translate("Border color of the inner part of the target"),
                                                label=_translate("Inner Border Color"))

        self.params['fillColor'] = Param(fillColor,
                                         valType='color', inputType="color", categ='Target',
                                         hint=_translate("Fill color of the outer part of the target"),
                                         label=_translate("Outer Fill Color"))

        self.params['borderColor'] = Param(borderColor,
                                           valType='color', inputType="color", categ='Target',
                                           hint=_translate("Border color of the outer part of the target"),
                                           label=_translate("Outer Border Color"))

        self.params['colorSpace'] = Param(colorSpace,
                                          valType='str', inputType="choice", categ='Target',
                                          allowedVals=['rgb', 'dkl', 'lms', 'hsv'],
                                          hint=_translate(
                                              "In what format (color space) have you specified the colors? (rgb, dkl, lms, hsv)"),
                                          label=_translate("Color Space"))

        self.params['borderWidth'] = Param(borderWidth,
                                           valType='num', inputType="single", categ='Target',
                                           hint=_translate("Width of the line around the outer part of the target"),
                                           label=_translate("Outer Border Width"))

        self.params['innerBorderWidth'] = Param(innerBorderWidth,
                                                valType='num', inputType="single", categ='Target',
                                                hint=_translate(
                                                    "Width of the line around the inner part of the target"),
                                                label=_translate("Inner Border Width"))

        self.params['outerRadius'] = Param(outerRadius,
                                           valType='num', inputType="single", categ='Target',
                                           hint=_translate("Size (radius) of the outer part of the target"),
                                           label=_translate("Outer Radius"))

        self.params['innerRadius'] = Param(innerRadius,
                                           valType='num', inputType="single", categ='Target',
                                           hint=_translate("Size (radius) of te inner part of the target"),
                                           label=_translate("Inner Radius"))

        self.params['units'] = Param(units,
                                     valType='str', inputType="choice", categ='Target',
                                     allowedVals=['from exp settings', 'deg', 'cm', 'pix', 'norm',
                                                  'height', 'degFlatPos', 'degFlat'],
                                     hint=_translate("Units of dimensions for this stimulus"),
                                     label=_translate("Spatial Units"))

        # Animation Params
        self.order += [
            "progressMode",
            "progressKey",
            "progressTime",
            "expandAnimation",
            "expandScale",
            "expandDur",
            "movementAnimation",
            "movementDur",
        ]

        self.params['progressMode'] = Param(progressMode,
                                            valType="str", inputType="choice", categ="Animation",
                                            allowedVals=["key", "time", "either"],
                                            hint=_translate("Should the target move to the next position after a "
                                                            "keypress or after an amount of time?"),
                                            label=_translate("Progress Mode"))

        self.depends.append(
            {"dependsOn": "progressMode",  # must be param name
             "condition": "in ['key', 'either']",  # val to check for
             "param": "progressKey",  # param property to alter
             "true": "show",  # what to do with param if condition is True
             "false": "hide",  # permitted: hide, show, enable, disable
             }
        )

        self.params['progressKey'] = Param(progressKey,
                                           valType='list', inputType="single", categ='Animation',
                                           hint=_translate(
                                               "Key or keys to press to progress to next position"),
                                           label=_translate("Progress Key(s)"))

        self.depends.append(
            {"dependsOn": "progressMode",  # must be param name
             "condition": "in ['time', 'either']",  # val to check for
             "param": "progressTime",  # param property to alter
             "true": "show",  # what to do with param if condition is True
             "false": "hide",  # permitted: hide, show, enable, disable
             }
        )

        self.params['progressTime'] = Param(progressTime,
                                            valType='num', inputType="single", categ='Animation',
                                            hint=_translate(
                                                "Time limit (s) after which progress to next position"),
                                            label=_translate("Progress Time"))

        self.params['movementAnimation'] = Param(movementAnimation,
                                           valType='bool', inputType="bool", categ='Animation',
                                           hint=_translate("Enable / disable animations as target stim changes position"),
                                           label=_translate("Animate Position Changes"))

        self.depends.append(
            {"dependsOn": "movementAnimation",  # must be param name
             "condition": "== True",  # val to check for
             "param": "movementDur",  # param property to alter
             "true": "enable",  # what to do with param if condition is True
             "false": "disable",  # permitted: hide, show, enable, disable
             }
        )

        self.params['movementDur'] = Param(movementDur,
                                           valType='num', inputType="single", categ='Animation',
                                           hint=_translate(
                                               "Duration of the animation during position changes. If position changes"
                                               " are not animated, this is the duration of the delay between positions."),
                                           label=_translate("Movement Duration"))

        self.params['expandAnimation'] = Param(expandAnimation,
                                               valType='bool', inputType="bool", categ='Animation',
                                               hint=_translate(
                                                   "Add an expand/contract animation"),
                                               label=_translate("Expand / Contract Animation"))

        self.depends.append(
            {"dependsOn": "expandAnimation",  # must be param name
             "condition": "== True",  # val to check for
             "param": "expandScale",  # param property to alter
             "true": "enable",  # what to do with param if condition is True
             "false": "disable",  # permitted: hide, show, enable, disable
             }
        )

        self.params['expandScale'] = Param(expandScale,
                                           valType='num', inputType="single", categ='Animation',
                                           hint=_translate("How many times bigger than its size the target grows"),
                                           label=_translate("Expand Scale"))

        self.depends.append(
            {"dependsOn": "expandAnimation",  # must be param name
             "condition": "== True",  # val to check for
             "param": "expandDur",  # param property to alter
             "true": "enable",  # what to do with param if condition is True
             "false": "disable",  # permitted: hide, show, enable, disable
             }
        )

        self.params['expandDur'] = Param(expandDur,
                                         valType='code', inputType='single', categ='Animation',
                                         hint=_translate("How long does the expand/contract animation take? Can be a "
                                                         "single value for a uniform animation or two for separate "
                                                         "expand/contract durations."),
                                         label=_translate("Expand / Contract Duration"))

        # Data params
        self.order += [
            "saveAsImg",
            "showResults",
        ]

        self.params['saveAsImg'] = Param(saveAsImg,
            valType='bool', inputType="bool", categ='Data',
            hint=_translate(
                "Save results as an image"),
            label=_translate("Save As Image"))

        self.params['showResults'] = Param(showResults,
            valType='bool', inputType="bool", categ='Data',
            hint=_translate(
                "Show a screen with results after completion?"),
            label=_translate("Show Results Screen"))

    def writeMainCode(self, buff):
        # Alert user if eyetracking isn't setup
        if self.exp.eyetracking == "None":
            alert(code=4505)

        # Alert user if validation can't progress
        if (self.params['progressKey'].val in ["", None, "None"]
                and self.params['progressTime'].val in ["", None, "None"]):
            alert(code=4515, strFields={'name': self.params['name'].val})

        # Get inits
        inits = deepcopy(self.params)
        # Code-ify 'from exp settings'
        if inits['units'].val == 'from exp settings':
            inits['units'].val = None
        # Split expandDur into two if needed
        if len(inits['expandDur'].val) == 2:
            inits['expandDur'] = self.params['expandDur'].val[0]
            inits['contractDur'] = self.params['expandDur'].val[1]
        else:
            inits['expandDur'] = self.params['expandDur'].val
            inits['contractDur'] = self.params['expandDur'].val
        # If positions are preset, override param value
        if inits['targetLayout'].val in positions:
            inits['targetPositions'].val = inits['targetLayout'].val

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
            "%(name)s = ValidationProcedure(win,\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)

        code = (
                "target=%(name)sTarget,\n"
                "positions=%(targetPositions)s, randomize_positions=%(randomisePos)s,\n"
                "animation_velocity=%(velocity)s, animation_scale=%(expandScale)s,\n"
                "animation_duration=(%(expandDur)s, %(contractDur)s),\n"
                "color_space=%(colorSpace)s, unit_type=%(units)s\n"
                "progress_on_timeout=%(autoPace)s, "
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
