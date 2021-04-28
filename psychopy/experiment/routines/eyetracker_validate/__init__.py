from .. import BaseStandaloneRoutine
from psychopy.localization import _translate
from psychopy.experiment import Param
from pathlib import Path
from psychopy.alerts import alert


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


class EyetrackerValidationRoutine(BaseStandaloneRoutine):
    categories = ['Eyetracking']
    targets = ["PsychoPy"]
    iconFile = Path(__file__).parent / "eyetracker_valid.png"
    tooltip = _translate("Validation routine for eyetrackers")

    def __init__(self, exp, name='validation',
                 showCursor=True, progressKey=["ENTER"], progressTime="", showResults=False,
                 color="red", fillColor="", borderColor="white", cursorColor="red", colorSpace="rgb",
                 targetStyle="dot", borderWidth=0.005,
                 units='from exp settings', targetSize=0.025, dotSize=0.005, randomisePos=True,
                 targetLayout="nine-point", positions=positionsMap['nine-point'],
                 velocity=1, expandScale=3, expandDur=0.2,
                 saveAsImg=False
                 ):
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
        self.order += [
            "progressKey",
            "progressTime",
            "showCursor",
            "showResults",
        ]

        self.params['showCursor'] = Param(showCursor,
            valType="bool", inputType="bool", categ="Basic",
            hint=_translate("Should a cursor be visible, showing where the participant is looking?"),
            label=_translate("Show Gaze Cursor"))

        self.params['showResults'] = Param(velocity,
            valType='bool', inputType="bool", categ='Basic',
            hint=_translate(
                "Show a screen with results after completion?"),
            label=_translate("Show Results Screen"))

        self.params['progressKey'] = Param(progressKey,
            valType='list', inputType="single", categ='Basic',
            hint=_translate(
                "Key or keys to press to progress to next position (leave blank for no keys)"),
            label=_translate("Progress On Key..."))

        self.params['progressTime'] = Param(progressTime,
            valType='num', inputType="single", categ='Basic',
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
            hint=_translate("In what format (color space) have you specified the colors? (rgb, dkl, lms, hsv)"),
            label=_translate("Color Space"))

        self.params['targetStyle'] = Param(targetStyle,
           valType='str', inputType="choice", categ='Appearance',
           allowedVals=['dot', 'ring'],
           hint=_translate(
               "Style of the target stim - should it have a solid dot or a hollow ring in the middle?"),
           label=_translate("Target Style"))

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
            hint=_translate("How many seconds it takes the target to expand/contract. Supply a single value for a "
                            "uniform animation or two (expand, contract) for differing speeds."),
            label=_translate("Animation Duration"))

        self.params['velocity'] = Param(velocity,
            valType='num', inputType="single", categ='Animation',
            hint=_translate(
                "How long it takes the target stimulus to move from one position to the next"),
            label=_translate("Velocity"))

        # Data params
        self.order += [
            "saveAsImg"
        ]
        self.params['saveAsImg'] = Param(velocity,
            valType='bool', inputType="bool", categ='Data',
            hint=_translate(
                "Save results as an image"),
            label=_translate("Save As Image"))

    def writeMainCode(self, buff):
        # Alert user if eyetracking isn't setup
        if self.exp.eyetracking == "None":
            alert(code=4505)

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
