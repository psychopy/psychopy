from .. import BaseStandaloneRoutine
from psychopy.localization import _translate
from psychopy.experiment import Param
from pathlib import Path
from psychopy.alerts import alert


class EyetrackerCalibrationRoutine(BaseStandaloneRoutine):
    categories = ['Eyetracking']
    targets = ["PsychoPy"]
    iconFile = Path(__file__).parent / "eyetracker_calib.png"
    tooltip = _translate("Calibration routine for eyetrackers")
    limit = 1

    def __init__(self, exp, name='calibration',
                 pacingSpeed="", autoPace=True,
                 innerFillColor="red", innerBorderColor="", innerBorderWidth="", outerRadius=0.025,
                 fillColor="", borderColor="white", borderWidth=2, innerRadius=0.005,
                 cursorColor="red", colorSpace="rgb", units='from exp settings',
                 targetLayout="NINE_POINTS", randomisePos=True,
                 enableAnimation=False, contractOnly=False, velocity=0.5, expandScale=3, expandDur=0.75):
        # Initialise base routine
        BaseStandaloneRoutine.__init__(self, exp, name=name)

        # Basic params
        self.params['pacingSpeed'] = Param(pacingSpeed,
            valType='num', inputType="single", categ='Basic',
            hint=_translate(
                "Number of seconds to wait between each calibration point presentation."),
            label=_translate("Pacing Speed"))

        self.params['autoPace'] = Param(autoPace,
            valType='bool', inputType="bool", categ='Basic',
            hint=_translate(
                "If True, calibration progresses after a fixation, if False, calibration has to "
                "be progressed by pushing a button."),
            label=_translate("Auto-Pace"))

        # Appearance Params
        self.order += [
            "targetStyle",
            "fillColor",
            "borderColor",
            "innerFillColor",
            "innerBorderColor",
            "cursorColor",
            "colorSpace",
            "borderWidth",
            "innerBorderWidth",
        ]

        self.params['innerFillColor'] = Param(innerFillColor,
                                     valType='color', inputType="color", categ='Appearance',
                                     hint=_translate("Fill color of the inner part of the target"),
                                     label=_translate("Inner Fill Color"))

        self.params['innerBorderColor'] = Param(innerBorderColor,
                                           valType='color', inputType="color", categ='Appearance',
                                           hint=_translate("Border color of the inner part of the target"),
                                           label=_translate("Inner Border Color"))

        self.params['fillColor'] = Param(fillColor,
                                         valType='color', inputType="color", categ='Appearance',
                                         hint=_translate("Fill color of the outer part of the target"),
                                         label=_translate("Outer Fill Color"))

        self.params['borderColor'] = Param(borderColor,
                                           valType='color', inputType="color", categ='Appearance',
                                           hint=_translate("Border color of the outer part of the target"),
                                           label=_translate("Outer Border Color"))

        self.params['cursorColor'] = Param(cursorColor,
                                           valType='color', inputType="color", categ='Appearance',
                                           hint=_translate("Color of the gaze cursor"),
                                           label=_translate("Gaze Cursor Color"))

        self.params['colorSpace'] = Param(colorSpace,
                                          valType='str', inputType="choice", categ='Appearance',
                                          allowedVals=['rgb', 'dkl', 'lms', 'hsv'],
                                          hint=_translate(
                                              "In what format (color space) have you specified the colors? (rgb, dkl, lms, hsv)"),
                                          label=_translate("Color Space"))

        self.params['borderWidth'] = Param(borderWidth,
                                           valType='num', inputType="single", categ='Appearance',
                                           hint=_translate("Width of the line around the outer part of the target"),
                                           label=_translate("Outer Border Width"))

        self.params['innerBorderWidth'] = Param(innerBorderWidth,
                                           valType='num', inputType="single", categ='Appearance',
                                           hint=_translate("Width of the line around the inner part of the target"),
                                           label=_translate("Inner Border Width"))

        # Layout Params
        self.order += [
            "targetLayout",
            "targetPositions",
            "randomisePos",
            "outerRadius",
            "innerRadius",
            "units",
        ]

        self.params['units'] = Param(units,
                                     valType='str', inputType="choice", categ='Layout',
                                     allowedVals=['from exp settings', 'deg', 'cm', 'pix', 'norm',
                                                  'height', 'degFlatPos', 'degFlat'],
                                     hint=_translate("Units of dimensions for this stimulus"),
                                     label=_translate("Spatial Units"))

        self.params['targetLayout'] = Param(targetLayout,
                                            valType='str', inputType="choice", categ='Layout',
                                            allowedVals=['THREE_POINTS', 'FIVE_POINTS', 'NINE_POINTS', "THIRTEEN_POINTS"],
                                            hint=_translate("Pre-defined target layouts"),
                                            label=_translate("Target Layout"))

        self.params['randomisePos'] = Param(randomisePos,
                                            valType='bool', inputType="bool", categ='Layout',
                                            hint=_translate("Should the order of target positions be randomised?"),
                                            label=_translate("Randomise Target Positions"))

        self.params['outerRadius'] = Param(outerRadius,
                                          valType='num', inputType="single", categ='Layout',
                                          hint=_translate("Size (radius) of the outer part of the target"),
                                          label=_translate("Outer Radius"))

        self.params['innerRadius'] = Param(innerRadius,
                                       valType='num', inputType="single", categ='Layout',
                                       hint=_translate("Size (radius) of te inner part of the target"),
                                       label=_translate("Inner Radius"))

        # Animation Params
        self.order += [
            "enableAnimation",
            "velocity",
            "contractOnly",
            "expandScale",
            "expandDur",
        ]

        self.params['enableAnimation'] = Param(enableAnimation,
                                           valType='bool', inputType="bool", categ='Animation',
                                           hint=_translate("Enable / disable animations, only applicable for Tobii "
                                                           "eyetrackers"),
                                           label=_translate("Enable Animation"))

        for depParam in ["velocity", "contractOnly", "expandScale", "expandDur"]:
            self.depends.append(
                {"dependsOn": "enableAnimation",  # must be param name
                 "condition": "==True",  # val to check for
                 "param": depParam,  # param property to alter
                 "true": "enable",  # what to do with param if condition is True
                 "false": "disable",  # permitted: hide, show, enable, disable
                 }
            )

        self.params['contractOnly'] = Param(contractOnly,
                                           valType='bool', inputType="bool", categ='Animation',
                                           hint=_translate("If True, then target stim won't expand in the animation, "
                                                           "only contract"),
                                           label=_translate("Contract Only"))

        self.params['expandScale'] = Param(expandScale,
                                           valType='num', inputType="single", categ='Animation',
                                           hint=_translate("How many times bigger than its size the target grows"),
                                           label=_translate("Expand / Contract Scale"))

        self.params['expandDur'] = Param(expandDur,
                                         valType='num', inputType="single", categ='Animation',
                                         hint=_translate(
                                             "How many seconds it takes the target to expand/contract."),
                                         label=_translate("Expand / Contract Duration"))

        self.params['velocity'] = Param(velocity,
                                        valType='num', inputType="single", categ='Animation',
                                        hint=_translate(
                                            "How long it takes the target stimulus to move from one position to "
                                            "the next"),
                                        label=_translate("Velocity"))

    def writeMainCode(self, buff):
        # Alert user if eyetracking isn't setup
        if self.exp.eyetracking == "None":
            alert(code=4505)
        # Get inits
        inits = self.params
        if self.params['units'].val == 'from exp settings':
            inits['units'].val = None

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
        # Make config object
        code = (
            "# define config object\n"
            "%(name)s = hardware.eyetracker.EyetrackerCalibration(win, \n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
                "eyetracker, %(name)sTarget,\n"
                "units=%(units)s, colorSpace=%(colorSpace)s,\n"
                "pacingSpeed=%(pacingSpeed)s, autoPace=%(autoPace)s,\n"
                "targetLayout=%(targetLayout)s, randomisePos=%(randomisePos)s,\n"
                "enableAnimation=%(enableAnimation)s, velocity=%(velocity)s,\n"
                "contractOnly=%(contractOnly)s, expandScale=%(expandScale)s, expandDur=%(expandDur)s\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
            ")\n"
            "# run calibration\n"
            "%(name)s.run()"
        )
        buff.writeIndentedLines(code % inits)
