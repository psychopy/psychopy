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
                 color="red", fillColor="", borderColor="white", cursorColor="red", colorSpace="rgb",
                 borderWidth=0.005,
                 units='from exp settings', targetSize=0.025, dotSize=0.005, randomisePos=True,
                 targetLayout="nine-point",
                 enableAnimation=False, velocity=0.5, expandScale=3, expandDur=0.75):
        # Initialise base routine
        BaseStandaloneRoutine.__init__(self, exp, name=name)

        # Basic params
        self.params['pacingSpeed'] = Param(pacingSpeed,
            valType='code', inputType="single", categ='Basic',
            hint=_translate(
                "Number of seconds to wait between each calibration point presentation."),
            label=_translate("Pacing Speed"))

        self.params['autoPace'] = Param(pacingSpeed,
            valType='bool', inputType="bool", categ='Basic',
            hint=_translate(
                "If True, calibration progresses after a fixation, if False, calibration has to "
                "be progressed by pushing a button."),
            label=_translate("Auto-Pace"))

        # Appearance Params
        self.order += [
            "targetStyle",
            "color",
            "fillColor",
            "borderColor",
            "cursorColor",
            "colorSpace",
            "borderWidth",
        ]

        self.params['color'] = Param(color,
                                     valType='color', inputType="color", categ='Appearance',
                                     hint=_translate("Color of the dot inside the target"),
                                     label=_translate("Target Inner Color"))

        self.params['fillColor'] = Param(fillColor,
                                         valType='color', inputType="color", categ='Appearance',
                                         hint=_translate("Color of the inside of the target"),
                                         label=_translate("Target Fill Color"))

        self.params['borderColor'] = Param(borderColor,
                                           valType='color', inputType="color", categ='Appearance',
                                           hint=_translate("Color of the line around the target"),
                                           label=_translate("Target Border Color"))

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
                                           hint=_translate("Width of the line around the target"),
                                           label=_translate("Target Border Width"))

        # Layout Params
        self.order += [
            "targetLayout",
            "randomisePos",
            "targetSize",
            "dotSize",
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
                                            allowedVals=['THREE_POINTS', 'FIVE_POINTS', 'NINE_POINTS', "THIRTEEN_POINTS", 'custom...'],
                                            hint=_translate("Pre-defined point layouts"),
                                            label=_translate("Target Layout"))

        self.params['randomisePos'] = Param(randomisePos,
                                            valType='bool', inputType="bool", categ='Layout',
                                            hint=_translate("Should the order of target positions be randomised?"),
                                            label=_translate("Randomise Target Positions"))

        self.params['targetSize'] = Param(targetSize,
                                          valType='num', inputType="single", categ='Layout',
                                          hint=_translate("Size (radius) of each target"),
                                          label=_translate("Target Size"))

        self.params['dotSize'] = Param(dotSize,
                                       valType='num', inputType="single", categ='Layout',
                                       hint=_translate("Size (radius) of the dot in each target and the gaze cursor"),
                                       label=_translate("Target / Cursor Dot Size"))

        # Animation Params
        self.order += [
            "enableAnimation",
            "velocity",
            "expandScale",
            "expandDur",
        ]

        self.params['enableAnimation'] = Param(enableAnimation,
                                           valType='bool', inputType="bool", categ='Animation',
                                           hint=_translate("Enable / disable animations, only applicable for Tobii "
                                                           "eyetrackers"),
                                           label=_translate("Enable Animation"))

        for depParam in ["velocity", "expandScale", "expandDur"]:
            self.depends.append(
                {"dependsOn": "eyetracker",  # must be param name
                 "condition": "=='enableAnimation'",  # val to check for
                 "param": depParam,  # param property to alter
                 "true": "enable",  # what to do with param if condition is True
                 "false": "disable",  # permitted: hide, show, enable, disable
                 }
            )

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

        BaseStandaloneRoutine.writeMainCode(self, buff)

        # Make target
        code = (
            "# define target for %(name)s\n"
            "%(name)sTarget = visual.TargetStim(win, \n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(1, relative=True)
        code = (
                "name='%(name)sTarget',\n"
                "outerRadius=%(targetSize)s, innerRadius=%(dotSize)s, lineWidth=%(borderWidth)s,\n"
                "color=%(color)s, fillColor=%(fillColor)s, borderColor=%(borderColor)s,\n"
                "colorSpace=%(colorSpace)s, units=%(units)s\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)
        code = (
            ")"
        )
        buff.writeIndentedLines(code % self.params)
        # Make config dict
        code = (
            "# define attributes for calibration for %(name)s\n"
            "%(name)sCalib = {\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(1, relative=True)

        # Eyelink
        code = (
            "'eyetracker.hw.sr_research.eyelink.EyeTracker': {\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(1, relative=True)
        # EyeLink doesn't allow custom positions, so if it's custom, approximate
        elPositions = self.params['targetLayout'].val
        if elPositions not in ['THREE_POINTS', 'FIVE_POINTS', 'NINE_POINTS', "THIRTEEN_POINTS"]:
            if len(elPositions) <= 4:
                elPositions = "'THREE_POINTS'"
            elif len(elPositions) <= 7:
                elPositions = "'FIVE_POINTS'"
            elif len(elPositions) <= 11:
                elPositions = "'NINE_POINTS'"
            else:
                elPositions = "'THIRTEEN_POINTS'"
        code = (
                    "'target_attributes': %(name)sTarget.getCalibSettings('SR Research Ltd'),\n"
                    "'type': " + elPositions + ",\n"
                    "'auto_pace': %(autoPace),\n"
                    "'pacing_speed': " + str(self.params['pacingSpeed'].val or 1.5) + ",\n"
                    "'screen_background_color': win._color.rgb255\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)
        code = (
                "},\n"
        )
        buff.writeIndentedLines(code % self.params)

        # GazePoint
        gpTargetDur = self.params['expandDur'].val
        if isinstance(gpTargetDur, (list, tuple)):
            gpTargetDur = sum(gpTargetDur)
        code = (
                "'eyetracker.hw.gazepoint.gp3.EyeTracker': {\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(1, relative=True)
        code = (
                "'target_delay': %(velocity)s,\n"
                "'target_duration': %(pacingSpeed)s\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)
        code = (
                "},\n"
        )
        buff.writeIndentedLines(code % self.params)

        # Tobii
        if elPositions == 'THIRTEEN_POINTS':
            tbPositions = 'NINE_POINTS'
        else:
            tbPositions = elPositions
        code = (
            "'eyetracker.hw.tobii.EyeTracker': {\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(1, relative=True)
        code = (
                "'target_attributes': %(name)sTarget.getCalibSettings('Tobii Technology'),\n"
                "'type': " + tbPositions + ",\n"
                "'randomize': %(randomisePos)s,\n"
                "'auto_pace': %(autoPace)s,\n"
                "'pacing_speed': " + str(self.params['pacingSpeed'].val or 1) + ",\n"
                "'screen_background_color': win.color\n"
                "'animate': {"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(1, relative=True)
        # Animation settings
        code = (
                    "'enable': %(enableAnimation)s,\n"
                    "'movement_velocity': %(velocity)s,\n"
                    "'expansion_ratio': %(expandScale)s,\n"
                    "'expansion_speed': %(expandDur)s"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)
        code = (
                "},\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)
        code = (
            "},\n"
        )
        buff.writeIndentedLines(code % self.params)

        # MouseGaze & unknown
        code = (
            "'eyetracker.hw.mouse.EyeTracker': {},\n"
            "'unknown': {}\n"
        )
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(-1, relative=True)
        code = (
            "}\n"
        )
        buff.writeIndentedLines(code % self.params)
        code = (
            "# run calibration\n"
            "eyetracker.runSetupProcedure(%(name)sCalib[eyetracker.getIOHubDeviceClass(full=True)])\n"
        )
        buff.writeIndentedLines(code % self.params)
