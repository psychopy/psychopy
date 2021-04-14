from .. import BaseStandaloneRoutine
from psychopy.localization import _translate
from psychopy.experiment import Param
from pathlib import Path


class EyetrackerCalibrationRoutine(BaseStandaloneRoutine):
    categories = ['Eyetracking']
    targets = ["PsychoPy"]
    iconFile = Path(__file__).parent / "eyetracker_calib.png"
    tooltip = _translate("Calibration routine for eyetrackers")

    def __init__(self, exp, name='validation'):
        # Initialise base routine
        BaseStandaloneRoutine.__init__(self, exp, name=name)
        # Define order
        self.order += [

        ]

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
