import itertools
import re
import tempfile
import subprocess
import sys
from pathlib import Path

from psychopy.session import Session
from psychopy.experiment import Experiment
from psychopy.hardware.button import ButtonResponse
from psychopy.experiment.routines import Routine
from psychopy.experiment.components.buttonBox import ButtonBoxComponent
from psychopy.experiment.components.code import CodeComponent
from .test_base_components import _TestBaseComponentsMixin


class TestButtonBoxComponent(_TestBaseComponentsMixin):
    def setup_method(self):
        self.exp = Experiment()
        # make blank routine
        self.routine = Routine(name="testRoutine", exp=self.exp)
        self.exp.addRoutine("testRoutine", self.routine)
        self.exp.flow.addRoutine(self.routine, 0)
        # make component
        self.comp = ButtonBoxComponent(
            exp=self.exp, name="testPhotodiodeValidatorRoutine", parentName="testRoutine"
        )

    def test_values(self):
        """
        Test that a variety of different values work when run from Builder.
        """
        # define some fields and possible values
        fields = {
            'forceEndRoutine': [True, False],
            'store': [True, False],
            'allowedButtons': [
                [0, 1, 2],
            ],
            'storeCorrect': [True, False],
            'correctAns': [
                0, 1,
            ],
            'resps': [
                [
                    ButtonResponse(t=0, value=True, channel=0),
                    ButtonResponse(t=0, value=False, channel=0),
                ],
                [
                    ButtonResponse(t=0, value=True, channel=1),
                    ButtonResponse(t=0, value=False, channel=1),
                ],
            ],
        }
        # make keys and values into two lists
        keys = list(fields.keys())
        values = list(fields.values())
        # iterate through all combinations of values
        cases = []
        for vals in itertools.product(*values):
            # make a case
            thisCase = {}
            # populate with values from this iteration
            for i, val in enumerate(vals):
                thisCase[keys[i]] = val
            # add case
            cases.append(thisCase)

        # make an experiment
        exp = Experiment()
        # configure experiment
        exp.requireImport("ButtonResponse", importFrom="psychopy.hardware.button")
        exp.settings.params['Full-screen window'].val = False
        exp.settings.params['Show info dlg'].val = False
        exp.settings.params['Window size (pixels)'].val = "[120, 120]"
        # add a Routine for each case
        for i, case in enumerate(cases):
            # pop response to separate from params
            resps = case.pop("resps")
            if not isinstance(resps, (list, tuple)):
                resps = [resps]
            # make a name
            name = f"rt{i}"
            # make a Routine
            rt = exp.addRoutine(name, Routine(name=name, exp=exp))
            exp.flow.addRoutine(rt, 0)
            # add timeout
            rt.settings.params['stopVal'].val = 0.2
            # make a Component
            comp = ButtonBoxComponent(
                exp, parentName=name, name=name + "_comp", **case
            )
            rt.addComponent(comp)
            # make a Code Component to send responses
            code = (
                "if frameN > 1:\n"
            )
            for resp in resps:
                code += (
                "    {name}.device.receiveMessage(\n"
                "        ButtonResponse(t=t, value={value}, channel={channel})\n"
                "    )\n"
                ).format(
                    name=comp.name, value=resp.value, channel=resp.channel
                )
            codeComp = CodeComponent(
                exp, parentName=name + "_code", eachFrame=code
            )
            rt.addComponent(codeComp)
        # save exp in temp directory
        tmpDir = Path(tempfile.mkdtemp())
        tmpExp = tmpDir / "testButtonBox.psyexp"
        tmpPy = tmpDir / "testButtonBox.py"
        exp.saveToXML(str(tmpExp), makeLegacy=False)
        # write code
        script = exp.writeScript(target="PsychoPy")
        tmpPy.write_text(script, encoding="utf-8")
        # assign ranges of code to cases by their Routine name
        errRanges = {
            0: None
        }
        for n, case in enumerate(cases):
            i = script.find(
                f"# --- Run Routine \"rt{n}\" ---"
            )
            errRanges[i] = case
        # try to run
        try:
            subprocess.run(
                args=[sys.executable, '-u', str(tmpPy)],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as err:
            # if we get any errors, check their line number against error ranges
            matches = re.findall(
                pattern=r"testButtonBox.py\", line (\d*),",
                string=err.stderr
            )
            # if no matches, raise error as is
            if not matches:
                raise err
            # otherwise, get the last line number in the traceback
            line = int(matches[-1])
            # find matching case
            lastCase = None
            for start, case in errRanges.items():
                if start <= line:
                    lastCase = case
                else:
                    break
            # construct new error with case details
            msg = (
                f"Error in Routine with following params:\n"
                f"{lastCase}\n"
                f"Original traceback:\n"
                f"{err.stdout}"
            )
            raise ValueError(msg)


def fullCases():
    """
    Generate an array covering a more complete set of values. Takes far too long to run for this
    to be worth doing every time.

    Returns
    -------
    list[dict]
    List of case dicts for TestButtonBoxComponent.test_values
    """
    # define some fields and possible values
    fields = {
        'forceEndRoutine': [True, False],
        'store': [True, False],
        'allowedButtons': [
            [0, 1, 2],
            "[0, 1, 2]",
        ],
        'storeCorrect': [True, False],
        'correctAns': [
            0, 1, "0", "1"
        ],
        'resps': [
            [
                ButtonResponse(t=0, value=True, channel=0),
                ButtonResponse(t=0, value=False, channel=0),
            ],
            [
                ButtonResponse(t=0, value=True, channel=1),
                ButtonResponse(t=0, value=False, channel=1),
            ],
            [
                ButtonResponse(t=0, value=True, channel=1),
            ],
            [
                ButtonResponse(t=0, value=True, channel=1),
            ],
        ],
    }

    # make keys and values into two lists
    keys = list(fields.keys())
    values = list(fields.values())
    # iterate through all combinations of values
    cases = []
    for vals in itertools.product(*values):
        # make a case
        thisCase = {}
        # populate with values from this iteration
        for i, val in enumerate(vals):
            thisCase[keys[i]] = val
        # add case
        cases.append(thisCase)

    return cases
