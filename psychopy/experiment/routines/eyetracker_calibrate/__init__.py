from .. import BaseStandaloneRoutine
from psychopy.localization import _translate
from psychopy.experiment import Param
from pathlib import Path


positionsMap = {
    "three-point":
        [(-0.85, +0.00), (+0.00, +0.00), (+0.85, +0.00)],
    "five-point":
        [(+0.00, +0.85),
         (-0.85, +0.00), (+0.00, +0.00), (+0.85, +0.00),
         (+0.85, -0.85)],
    "nine-point":
        [(-0.85, +0.85), (+0.00, +0.85), (+0.85, +0.85),
         (-0.85, +0.00), (+0.00, +0.00), (+0.85, +0.00),
         (-0.85, -0.85), (+0.85, -0.85), (+0.00, -0.85)],
    "thirteen-point":
        [(-0.850, +0.850), (+0.000, +0.850), (+0.850, +0.850),
         (-0.425, +0.425), (+0.425, +0.425),
         (-0.850, +0.000), (+0.000, +0.000), (+0.850, +0.000),
         (-0.425, -0.425), (+0.425, -0.425),
         (-0.850, -0.850), (+0.850, -0.850), (+0.000, -0.850)],
}


class EyetrackerCalibrationRoutine(BaseStandaloneRoutine):
    categories = ['Eyetracking']
    targets = ["PsychoPy"]
    iconFile = Path(__file__).parent / "eyetracker_calib.png"
    tooltip = _translate("Calibration routine for eyetrackers")
    limit = 1

    def __init__(self, exp, name='calibration',
                 progressTime="",
                 color="red", fillColor="", borderColor="white", cursorColor="red", colorSpace="rgb",
                 borderWidth=0.005,
                 units="height", targetSize=0.025, dotSize=0.005, randomisePos=True,
                 targetLayout="nine-point", positions=positionsMap['nine-point'],
                 velocity=1, expandScale=3, expandDur=0.2):
        # Initialise base routine
        BaseStandaloneRoutine.__init__(self, exp, name=name)

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
        self.params['progressTime'] = Param(progressTime,
            valType='code', inputType="single", categ='Basic',
            hint=_translate(
                "Time limit (s) after which progress to next position (leave blank for no limit)"),
            label=_translate("Progress After Time..."))

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
            "positions",
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

        self.params['positions'] = Param(positions,
                                         valType='list', inputType="single", categ='Layout',
                                         hint=_translate("List of positions (x, y) at which the target can appear"),
                                         label=_translate("Target Positions"))

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
            "velocity",
            "expandScale",
            "expandDur",
        ]
        self.params['expandScale'] = Param(expandScale,
                                           valType='num', inputType="single", categ='Animation',
                                           hint=_translate("How many times bigger than its size the target grows"),
                                           label=_translate("Expand / Contract Scale"))

        self.params['expandDur'] = Param(expandDur,
                                         valType='list', inputType="single", categ='Animation',
                                         hint=_translate(
                                             "How many seconds it takes the target to expand/contract. Supply a single value for a "
                                             "uniform animation or two (expand, contract) for differing speeds."),
                                         label=_translate("Animation Duration"))

        self.params['velocity'] = Param(velocity,
                                        valType='num', inputType="single", categ='Animation',
                                        hint=_translate(
                                            "How long it takes the target stimulus to move from one position to the next"),
                                        label=_translate("Velocity"))


    def writeMainCode(self, buff):
        BaseStandaloneRoutine.writeMainCode(self, buff)

        # If positions are preset, override param value
        if self.params['targetLayout'].val in positionsMap:
            self.params['positions'].val = positionsMap[self.params['targetLayout'].val]

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
        progressTime = self.params['progressTime'].val or None
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
                    "'auto_pace': " + str(bool(self.params['progressTime'])) + ",\n"
                    "'pacing_speed': " + str(progressTime) + ",\n"
                    "'screen_background_color': win._color.rgb255\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)
        code = (
                "},\n"
        )
        buff.writeIndentedLines(code % self.params)

        # GazePoint
        targetDur = self.params['expandDur'].val
        if not isinstance(targetDur, (list, tuple)):
            targetDur = [targetDur]
        if len(targetDur) > 1:
            targetDur = sum(targetDur)
        else:
            targetDur = targetDur[0] * 2
        code = (
                "'eyetracker.hw.tobii.EyeTracker': {\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(1, relative=True)
        code = (
                "'target_delay': " + str(self.params['progressTime'].val or 1) + ",\n"
                "'target_duration': " + str(targetDur) + "\n"
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
                "'target_attributes': %(name)sTarget.getCalibSettings('SR Research Ltd'),\n"
                "'type': " + tbPositions + ",\n"
                "'randomize': %(randomisePos)s,\n"
                "'auto_pace': " + str(bool(self.params['progressTime'])) + ",\n"
                "'pacing_speed': " + str(progressTime) + ",\n"
                "'screen_background_color': win._color.rgb255\n"
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
            "eyetracker.runSetupProcedure(%(name)sCalib)\n"
        )
        buff.writeIndentedLines(code % self.params)
