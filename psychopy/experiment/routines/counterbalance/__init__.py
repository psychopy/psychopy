from .. import BaseStandaloneRoutine
from ... import Param
from pathlib import Path
from psychopy.localization import _translate


class CounterBalanceRoutine(BaseStandaloneRoutine):
    categories = ['Custom']
    targets = ["PsychoJS"]
    iconFile = Path(__file__).parent / "counterbalance.png"
    tooltip = _translate(
        "Counterbalance Routine: use the Shelf to choose a value taking into account previous runs of this experiment."
    )

    def __init__(
            self, exp, name='counterbalance',
            specMode="file",
            conditionsFile="",
            nGroups=2, pCap=10,
    ):
        BaseStandaloneRoutine.__init__(self, exp, name=name)

        # we don't need a stop time
        del self.params['stopVal']
        del self.params['stopType']

        self.type = "CounterBalance"

        # --- Basic ---
        self.order += [
            'specMode',
            'conditionsFile',
            'nGroups',
            'pCap'
        ]

        self.params['specMode'] = Param(
            specMode, valType="str", inputType="choice", categ="Basic",
            allowedVals=["file", "spec"],
            allowedLabels=[_translate("Conditions file"), _translate("Num. groups")],
            label=_translate("Groups from..."),
            hint=_translate(
                "Specify groups using an Excel file (for fine tuned control) or specify a number of groups to create "
                "equally likely groups with a uniform cap."
            )
        )

        self.depends += [{
            "dependsOn": "specMode",  # must be param name
            "condition": "=='file'",  # val to check for
            "param": 'conditionsFile',  # param property to alter
            "true": "show",  # what to do with param if condition is True
            "false": "hide",  # permitted: hide, show, enable, disable
        }, {
            "dependsOn": "specMode",  # must be param name
            "condition": "=='spec'",  # val to check for
            "param": 'nGroups',  # param property to alter
            "true": "show",  # what to do with param if condition is True
            "false": "hide",  # permitted: hide, show, enable, disable
        }, {
            "dependsOn": "specMode",  # must be param name
            "condition": "=='spec'",  # val to check for
            "param": 'pCap',  # param property to alter
            "true": "show",  # what to do with param if condition is True
            "false": "hide",  # permitted: hide, show, enable, disable
        }]

        self.params['conditionsFile'] = Param(
            conditionsFile, valType='file', inputType="table", categ="Basic",
            label=_translate('Conditions'),
            hint=_translate(
                "Name of a file specifying the parameters for each group (.csv, .xlsx, or .pkl). Browse to select "
                "a file. Right-click to preview file contents, or create a new file."
            ))

        self.params['nGroups'] = Param(
            nGroups, valType="code", inputType="single", categ="Basic",
            label=_translate("Num. groups"),
            hint=_translate(
                "Number of groups to use."
            )
        )

        self.params['pCap'] = Param(
            pCap, valType="code", inputType="single", categ="Basic",
            label=_translate("Participant cap"),
            hint=_translate(
                "Max number of participants in each group."
            )
        )

    def writeMainCode(self, buff):
        code = (
            "\n"
            "# Unknown standalone routine ignored: %(name)s\n"
            "\n"
        )
        buff.writeIndentedLines(code % self.params)

    def writeRoutineBeginCodeJS(self, buff, modular=True):
        code = (
                "\n"
                "var %(name)s"
                "function %(name)sRoutine(snapshot) {\n"
                "  return async function () {\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(2, relative=True)

        if self.params['specMode'] == "file":
            # if we're going from a file, read in file to get conditions
            code = (
                "// load in conditions for %(name)s\n"
                "let %(name)sConditions = data.conditionsFromFile(%(conditionsFile)s);\n"
            )
        else:
            # otherwise, create conditions
            code = (
                "// create uniform conditions for %(name)s\n"
                "let %(name)sConditions = [];\n"
                "for (let n = 0; n < %(nGroups)s; n++) {\n"
                "    %(name)sConditions.push({"
                "        'group': n,\n"
                "        'probability': 1/%(nGroups)s,\n"
                "        'cap': %(pCap)s\n"
                "    });\n"
                "}\n"
            )
        buff.writeIndentedLines(code % self.params)

        code = (
            "\n"
            "// create counterbalance object for %(name)s \n"
            "%(name)s = data.Counterbalancer({\n"
            "    'entry': '%(name)s',\n"
            "    'conditions': %(name)sConditions,\n"
            "});\n"
            "// get group from online\n"
            "%(name)s.allocateGroup();"
            "\n"
        )
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(-2, relative=True)
        code = (
            "  }\n"
            "}\n"
        )
        buff.writeIndentedLines(code % self.params)
