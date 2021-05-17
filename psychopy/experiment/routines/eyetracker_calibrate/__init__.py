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
                 targetDelay=1.25, targetDuration=0.5, autoPace=True,
                 innerFillColor="red", innerBorderColor="", innerBorderWidth="", outerRadius=0.025,
                 fillColor="", borderColor="white", borderWidth=2, innerRadius=0.005,
                 colorSpace="rgb", units='from exp settings',
                 targetLayout="NINE_POINTS", randomisePos=True,
                 enableAnimation=False, expandScale=3):
        # Initialise base routine
        BaseStandaloneRoutine.__init__(self, exp, name=name)

        self.exp.requirePsychopyLibs(['iohub', 'hardware'])

        # Basic params
        del self.params['stopVal']
        del self.params['stopType']

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
                                           hint=_translate("Width of the line around the inner part of the target"),
                                           label=_translate("Inner Border Width"))

        self.params['outerRadius'] = Param(outerRadius,
                                           valType='num', inputType="single", categ='Target',
                                           hint=_translate("Size (radius) of the outer part of the target"),
                                           label=_translate("Outer Radius"))

        self.params['innerRadius'] = Param(innerRadius,
                                           valType='num', inputType="single", categ='Target',
                                           hint=_translate("Size (radius) of te inner part of the target"),
                                           label=_translate("Inner Radius"))

        # Layout Params
        self.order += [
            "targetLayout",
            "randomisePos",
            "units",
        ]

        self.params['units'] = Param(units,
                                     valType='str', inputType="choice", categ='Target',
                                     allowedVals=['from exp settings', 'deg', 'cm', 'pix', 'norm',
                                                  'height', 'degFlatPos', 'degFlat'],
                                     hint=_translate("Units of dimensions for this stimulus"),
                                     label=_translate("Spatial Units"))

        self.params['targetLayout'] = Param(targetLayout,
                                            valType='str', inputType="choice", categ='Basic',
                                            allowedVals=['THREE_POINTS', 'FIVE_POINTS', 'NINE_POINTS', "THIRTEEN_POINTS"],
                                            hint=_translate("Pre-defined target layouts"),
                                            label=_translate("Target Layout"))

        self.params['randomisePos'] = Param(randomisePos,
                                            valType='bool', inputType="bool", categ='Basic',
                                            hint=_translate("Should the order of target positions be randomised?"),
                                            label=_translate("Randomise Target Positions"))

        # Animation Params
        self.order += [
            "autoPace",
            "targetDuration",
            "contractOnly",
            "expandScale",
            "expandDur",
        ]

        self.params['autoPace'] = Param(autoPace,
                                        valType='bool', inputType="bool", categ='Animation',
                                        hint=_translate(
                                            "If True, calibration progresses after a fixation, if False, calibration has to "
                                            "be progressed by pushing a button."),
                                        label=_translate("Auto-Pace"))

        self.params['targetDuration'] = Param(targetDuration,
                                        valType='num', inputType="single", categ='Animation',
                                        hint=_translate(
                                            "How long to display each target. If auto-pace is off, this is just how "
                                            "long the expand / contract animation takes."),
                                        label=_translate("Target Duration"))

        self.params['targetDelay'] = Param(targetDelay,
                                           valType='num', inputType="single", categ='Animation',
                                           hint=_translate(
                                               "Number of seconds to wait between each calibration point presentation."),
                                           label=_translate("Target Delay"))

        self.params['enableAnimation'] = Param(enableAnimation,
                                           valType='bool', inputType="bool", categ='Animation',
                                           hint=_translate("Enable / disable animations as target stim changes position, "
                                                           "only applicable for Tobii eyetrackers"),
                                           label=_translate("Animate Position Changes"))

        self.params['expandScale'] = Param(expandScale,
                                           valType='num', inputType="single", categ='Animation',
                                           hint=_translate("How many times bigger than its size the target grows"),
                                           label=_translate("Expand Scale"))

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
                "targetDelay=%(targetDelay)s, targetDuration=%(targetDuration)s, autoPace=%(autoPace)s,\n"
                "targetLayout=%(targetLayout)s, randomisePos=%(randomisePos)s,\n"
                "enableAnimation=%(enableAnimation)s, velocity=%(velocity)s,\n"
                "expandScale=%(expandScale)s\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
            ")\n"
            "# run calibration\n"
            "%(name)s.run()"
        )
        buff.writeIndentedLines(code % inits)
