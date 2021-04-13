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
    tooltip = _translate("Calibration or validation routine for eyetrackers")

    def __init__(self, exp, name='validation',
                 mode="calibrate", showCursor=True,
                 color="red", fillColor="gray", borderColor="black", colorSpace="rgb", borderWidth=0.005,
                 units="height", targetSize=0.025, dotSize=0.005, randomisePos=True,
                 targetLayout="nine-point", positions=positionsMap['nine-point'],
                 velocity=1, expandScale=3, expandDur=0.2
                 ):
        # Initialise base routine
        BaseStandaloneRoutine.__init__(self, exp, name=name)
        # Define order
        self.order += [
            "mode"
            "color",
            "fillColor",
            "borderColor",
            "colorSpace",
            "size",
            "targetLayout",
            "positions",
            "randomisePos",
            "targetSize",
            "dotSize",
            "units",
        ]
        # Define relationships
        self.depends = [  # allows params to turn each other off/on
            # Only enable positions if targetLayout is custom
            {"dependsOn": "targetLayout",  # must be param name
             "condition": "=='custom...'",  # val to check for
             "param": "positions",  # param property to alter
             "true": "enable",  # what to do with param if condition is True
             "false": "disable",  # permitted: hide, show, enable, disable
             },
        ]
        # Disable all parameters which aren't implemented for calibration yet if mode is set to calibration
        for depParam in ["showCursor", "colorSpace", "color", "fillColor", "borderColor", "borderWidth", "units", "targetLayout", "positions", "randomisePos", "targetSize", "dotSize", "velocity", "expandScale", "expandDur", ]:
            self.depends.append(
                {"dependsOn": "mode",  # must be param name
                 "condition": "=='validate'",  # val to check for
                 "param": depParam,  # param property to alter
                 "true": "enable",  # what to do with param if condition is True
                 "false": "disable",  # permitted: hide, show, enable, disable
                 }
            )


        # Basic Params
        self.params['mode'] = Param(mode,
            valType="str", inputType="choice", categ="Basic",
            allowedVals=["validate", "calibrate"],
            hint=_translate("Are you using this to calibrate an eye tracker, or validate it?"),
            label=_translate("Validate / Calibrate"))

        self.params['showCursor'] = Param(showCursor,
            valType="bool", inputType="bool", categ="Basic",
            hint=_translate("Should a cursor be visible, showing where the participant is looking?"),
            label=_translate("Show Gaze Cursor"))

        # Appearance Params
        self.params['colorSpace'] = Param(colorSpace,
            valType='str', inputType="choice", categ='Appearance',
            hint=_translate("In what format (color space) have you specified the colors? (rgb, dkl, lms, hsv)"),
            label=_translate("Color Space"))

        self.params['color'] = Param(color,
            valType='color', inputType="color", categ='Appearance',
            hint=_translate("Color of the gaze cursor and the dot inside the target"),
            label=_translate("Target / Cursor Dot Color"))

        self.params['fillColor'] = Param(fillColor,
            valType='color', inputType="color", categ='Appearance',
            hint=_translate("Color of the inside of the target"),
            label=_translate("Target Fill Color"))

        self.params['borderColor'] = Param(borderColor,
            valType='color', inputType="color", categ='Appearance',
            hint=_translate("Color of the line around the target"),
            label=_translate("Target Border Color"))

        self.params['borderWidth'] = Param(borderWidth,
            valType='num', inputType="single", categ='Appearance',
            hint=_translate("Width of the line around the target"),
            label=_translate("Target Border Width"))

        # Layout Params
        self.params['units'] = Param(units,
            valType='str', inputType="choice", categ='Layout',
            allowedVals=['from exp settings', 'deg', 'cm', 'pix', 'norm',
                         'height', 'degFlatPos', 'degFlat'],
            hint=_translate("Units of dimensions for this stimulus"),
            label=_translate("Spatial Units"))

        self.params['targetLayout'] = Param(targetLayout,
            valType='str', inputType="choice", categ='Layout',
            allowedVals=['three-point', 'five-point', 'nine-point', 'custom...'],
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
        self.params['velocity'] = Param(velocity,
            valType='num', inputType="single", categ='Animation',
            hint=_translate("How long it takes the target stimulus to move from one position to the next"),
            label=_translate("Velocity"))

        self.params['expandScale'] = Param(expandScale,
            valType='num', inputType="single", categ='Animation',
            hint=_translate("How many times bigger than its size the target grows"),
            label=_translate("Expand / Contract Scale"))

        self.params['expandDur'] = Param(expandDur,
            valType='list', inputType="single", categ='Animation',
            hint=_translate("How many seconds it takes the target to expand/contract. Supply a single value for a "
                            "uniform animation or two (expand, contract) for differing speeds."),
            label=_translate("Expand / Contract Duration"))

    def writeMainCode(self, buff):
        # If positions are preset, override param value
        if self.params['targetLayout'].val in positionsMap:
            self.params['positions'].val = positionsMap[self.params['targetLayout'].val]

        # Make target
        code = (
            "%(name)sTarget = visual.TargetStim(win, \n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(1, relative=True)
        code = (
                "radius=%(targetSize)s, dotradius=%(dotSize)s, edgewidth=%(borderWidth)s,\n"
                "fillcolor=%(fillColor)s, edgecolor=%(borderColor)s, dotcolor=%(color)s,\n"
                "units=%(units)s, colorspace=%(colorSpace)s)\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)
        if self.params['mode'].val == "validation":
            # Setup validation
            code = (
                "%(name)s = ValidationProcedure(win, %(name)sTarget,\n"
            )
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(1, relative=True)
            # Split expandDur into two if needed
            if len(self.params['expandDur'].val) == 2:
                expString = f"expandDur={self.params['expandDur'].val[0]}, contractDur={self.params['expandDur'].val[1]}, \n"
            else:
                expString = f"expandDur={self.params['expandDur'].val}, contractDur={self.params['expandDur'].val}, \n"
            code = (
                    "positions=%(positions)s,\n"
                    "velocity=%(velocity)s, expandScale=%(expandScale)s,\n"
                    +expString+
                    "randomize_positions=%(randomisePos)s)\n"
            )
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(-1, relative=True)
        if self.params['mode'].val == "calibration":
            pass
