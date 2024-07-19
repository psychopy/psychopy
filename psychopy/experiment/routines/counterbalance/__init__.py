from .. import BaseStandaloneRoutine
from ... import Param
from pathlib import Path
from psychopy.localization import _translate


class CounterbalanceRoutine(BaseStandaloneRoutine):
    categories = ['Custom']
    targets = ["PsychoPy", "PsychoJS"]
    iconFile = Path(__file__).parent / "counterbalance.png"
    label = _translate("Counter-balance")
    tooltip = _translate(
        "Counterbalance Routine: use the Shelf to choose a value taking into account previous runs of this experiment."
    )

    def __init__(
            self, exp, name='counterbalance',
            specMode="uniform",
            conditionsFile="", conditionsVariable="",
            nGroups=2, nSlots=10,
            nReps=1, endExperimentOnDepletion="ignore",
            saveData=True, saveRemaining=True
    ):
        BaseStandaloneRoutine.__init__(self, exp, name=name)
        self.url = "https://psychopy.org/builder/components/counterbalanceComponent.html"

        # we don't need a stop time
        del self.params['stopVal']
        del self.params['stopType']

        self.type = "CounterBalance"

        # --- Basic ---
        self.order += [
            'specMode',
            'conditionsFile',
            'nGroups',
            'nSlots',
            'nReps',
            'endExperimentOnDepletion'
        ]

        self.params['specMode'] = Param(
            specMode, valType="str", inputType="choice", categ="Basic",
            allowedVals=["uniform", "file"],
            allowedLabels=[_translate("Num. groups"), _translate("Conditions file (local only)")],
            label=_translate("Groups from..."),
            hint=_translate(
                "Specify groups using an Excel file (for fine tuned control), specify as a variable name, or specify a "
                "number of groups to create equally likely groups with a uniform cap."
            )
        )

        self.params['nReps'] = Param(
            nReps, valType="code", inputType="single", categ="Basic",
            label=_translate("Num. repeats"),
            hint=_translate(
                "How many times to run slots down to depletion?"
            )
        )

        self.depends += [{
            "dependsOn": "specMode",  # must be param name
            "condition": "=='file'",  # val to check for
            "param": 'conditionsFile',  # param property to alter
            "true": "show",  # what to do with param if condition is True
            "false": "hide",  # permitted: hide, show, enable, disable
        },  {
            "dependsOn": "specMode",  # must be param name
            "condition": "=='variable'",  # val to check for
            "param": 'conditionsVariable',  # param property to alter
            "true": "show",  # what to do with param if condition is True
            "false": "hide",  # permitted: hide, show, enable, disable
        }, {
            "dependsOn": "specMode",  # must be param name
            "condition": "=='uniform'",  # val to check for
            "param": 'nGroups',  # param property to alter
            "true": "show",  # what to do with param if condition is True
            "false": "hide",  # permitted: hide, show, enable, disable
        }, {
            "dependsOn": "specMode",  # must be param name
            "condition": "=='uniform'",  # val to check for
            "param": 'nSlots',  # param property to alter
            "true": "show",  # what to do with param if condition is True
            "false": "hide",  # permitted: hide, show, enable, disable
        }]

        self.params['conditionsFile'] = Param(
            conditionsFile, valType='file', inputType="table", categ="Basic",
            label=_translate('Conditions'),
            hint=_translate(
                "Name of a file specifying the parameters for each group (.csv, .xlsx, or .pkl). Browse to select "
                "a file. Right-click to preview file contents, or create a new file."
            ),
            ctrlParams={
                'template': Path(__file__).parent / "counterbalanceItems.xltx"
            }
        )

        self.params['conditionsVariable'] = Param(
            conditionsVariable, valType='code', inputType="single", categ="Basic",
            label=_translate('Conditions'),
            hint=_translate(
                "Name of a variable specifying the parameters for each group. Should be a list of dicts, like the "
                "output of data.conditionsFromFile"
            ))

        self.params['nGroups'] = Param(
            nGroups, valType="code", inputType="single", categ="Basic",
            label=_translate("Num. groups"),
            hint=_translate(
                "Number of groups to use."
            )
        )

        self.params['nSlots'] = Param(
            nSlots, valType="code", inputType="single", categ="Basic",
            label=_translate("Slots per group"),
            hint=_translate(
                "Max number of participants in each group for each repeat."
            )
        )

        self.params['endExperimentOnDepletion'] = Param(
            endExperimentOnDepletion, valType="code", inputType="bool", categ="Basic",
            label=_translate("End experiment on depletion"),
            hint=_translate(
                "When all slots and repetitions are depleted, should the experiment end or "
                "continue with .finished on this Routine as True?"
            )
        )

        # --- Data ---
        self.order += [
            'saveData',
            'saveRemaining',
        ]
        self.params['saveData'] = Param(
            saveData, valType="bool", inputType="bool", categ="Data",
            label=_translate("Save data"),
            hint=_translate(
                "Save chosen group and associated params this repeat to the data file?"
            )
        )

        self.params['saveRemaining'] = Param(
            saveRemaining, valType="bool", inputType="bool", categ="Data",
            label=_translate("Save remaining cap"),
            hint=_translate(
                "Save the remaining cap for the chosen group this repeat to the data file?"
            )
        )

    def writeInitCode(self, buff):
        code = (
            "expShelf = data.shelf.Shelf(scope='experiment', expPath=_thisDir)"
        )
        buff.writeOnceIndentedLines(code % self.params)

        if self.params['specMode'] == "file":
            # if we're going from a file, read in file to get conditions
            code = (
                "# load in conditions for %(name)s\n"
                "%(name)sConditions = data.utils.importConditions(%(conditionsFile)s);\n"
            )
        elif self.params['specMode'] == "variable":
            code = (
                "# get conditions for %(name)s\n"
                "%(name)sConditions = %(conditionsVariable)s\n"
            )
        else:
            # otherwise, create conditions
            code = (
                "# create uniform conditions for %(name)s\n"
                "%(name)sConditions = []\n"
                "for n in range(%(nGroups)s):\n"
                "    %(name)sConditions.append({\n"
                "        'group': n,\n"
                "        'probability': 1/%(nGroups)s,\n"
                "        'cap': %(nSlots)s\n"
                "    })\n"
            )
        buff.writeIndentedLines(code % self.params)
        # make Counterbalancer object
        code = (
            "\n"
            "# create counterbalance object for %(name)s \n"
            "%(name)s = data.Counterbalancer(\n"
            "    shelf=expShelf,\n"
            "    entry='%(name)s',\n"
            "    conditions=%(name)sConditions,\n"
            "    nReps=%(nReps)s\n"
            ")\n"
        )
        buff.writeIndentedLines(code % self.params)

    def writeMainCode(self, buff):
        # get group
        code = (
            "# get group from shelf\n"
            "%(name)s.allocateGroup()"
            "\n"
        )
        buff.writeIndentedLines(code % self.params)
        # if ending experiment on depletion, write the code to do so
        if self.params['endExperimentOnDepletion']:
            msg = _translate(
                "Slots for Counterbalancer %(name)s have been fully depleted, ending experiment."
            )
            code = (
                f"# if slots and repeats are fully depleted, end the experiment now\n"
                f"if %(name)s.finished:\n"
                f"    # first print and log a message to make it clear why the experiment ended\n"
                f"    print('{msg}')\n"
                f"    logging.exp('{msg}')\n"
                f"    endExperiment(thisExp, win=win)\n"
            )
            buff.writeIndentedLines(code % self.params)
        # save data
        if self.params['saveData']:
            code = (
            "thisExp.addData('%(name)s.group', %(name)s.group)\n"
            "for _key, _val in %(name)s.params.items():\n"
            "    thisExp.addData(f'%(name)s.{_key}', _val)\n"
            )
            buff.writeIndentedLines(code % self.params)
        # save remaining cap
        if self.params['saveRemaining']:
            code = (
            "thisExp.addData('%(name)s.remaining', %(name)s.remaining)"
            )
            buff.writeIndentedLines(code % self.params)

    def writeRoutineBeginCodeJS(self, buff, modular=True):
        # enter function def
        code = (
                "\n"
                "function %(name)sRoutineBegin(snapshot) {\n"
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
                "    %(name)sConditions.push({\n"
                "        'group': n,\n"
                "        'probability': 1/%(nGroups)s,\n"
                "        'cap': %(nSlots)s\n"
                "    });\n"
                "}\n"
            )
        buff.writeIndentedLines(code % self.params)

        code = (
            "\n"
            "// get counterbalancing group \n"
            "%(name)s = await psychoJS.shelf.counterbalanceSelect({\n"
            "    key: ['%(name)s', '@designer', '@experiment'],\n"
            "    groups: %(name)sConditions.map(row => row.group),\n"
            "    groupSizes: %(name)sConditions.map(row => row.cap),\n"
            "});\n"
        )
        buff.writeIndentedLines(code % self.params)
        # if ending experiment on depletion, write the code to do so
        if self.params['endExperimentOnDepletion']:
            code = (
                "// if slots and repeats are fully depleted, end the experiment now\n"
                "if (%(name)s.finished) {\n"
                "    quitPsychoJS('No more slots remaining for this study.', true)\n"
                "}\n"
            )
            buff.writeIndentedLines(code % self.params)
        # save data
        if self.params['saveData']:
            code = (
                "psychoJS.experiment.addData('%(name)s.group', %(name)s.group)\n"
                "for (let _key in %(name)s.params) {\n"
                "    psychoJS.experiment.addData(`%(name)s.${_key}`, %(name)s.params[_key])\n"
                "}\n"
            )
            buff.writeIndentedLines(code % self.params)
        # save remaining cap
        if self.params['saveRemaining']:
            code = (
                "psychoJS.experiment.addData('%(name)s.remaining', %(name)s.remaining)\n"
            )
            buff.writeIndentedLines(code % self.params)

        # exit function def
        code = (
            "    return Scheduler.Event.NEXT;\n"
            "  }\n"
            "}\n"
        )
        buff.setIndentLevel(-2, relative=True)
        buff.writeIndentedLines(code % self.params)

    def writeExperimentEndCodeJS(self, buff):
        code = (
            "if (%(name)s && !%(name)s.finished) {\n"
            "  await psychoJS.shelf.counterbalanceConfirm(\n"
            "    ['%(name)s', '@designer', '@experiment'],\n"
            "    %(name)s.participantToken,\n"
            "    isCompleted\n"
            "  );\n"
            "}\n"
        )
        buff.writeIndentedLines(code % self.params)