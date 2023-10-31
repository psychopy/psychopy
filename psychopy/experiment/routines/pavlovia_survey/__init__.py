from psychopy.experiment.components import getInitVals
from psychopy.experiment.routines import BaseStandaloneRoutine
from psychopy.localization import _translate
from psychopy.experiment import Param
from pathlib import Path


class PavloviaSurveyRoutine(BaseStandaloneRoutine):
    categories = ['Responses']
    targets = ["PsychoJS"]
    version = "2023.1.0"
    iconFile = Path(__file__).parent / "survey.png"
    tooltip = _translate("Run a SurveyJS survey in Pavlovia")
    beta = False

    def __init__(self, exp, name='survey',
                 surveyType="id", surveyId="", surveyJson="",
                 disabled=False
                 ):
        # Initialise base routine
        BaseStandaloneRoutine.__init__(
            self, exp=exp, name=name,
            disabled=disabled
        )
        del self.params['stopVal']
        del self.params['stopType']
        self.url = "https://psychopy.org/builder/components/advanced_survey.html"
        self.type = "PavloviaSurvey"

        # Define relationships
        self.depends = []

        self.order += [
            'surveyType',
            'surveyId',
            'surveyJson',
        ]

        self.params['surveyType'] = Param(
            surveyType, valType='code', inputType="richChoice", categ='Basic',
            allowedVals=["id", "json"], allowedLabels=[
                {'label': _translate("Survey id"),
                 'body': _translate(
                     "Linking to a survey ID from Pavlovia Surveys means that the content will automatically update "
                     "if that survey changes (better for dynamic use)"),
                 'linkText': _translate("How do I get my survey ID?"),
                 'link': "https://psychopy.org/builder/components/advanced_survey.html#get-id",
                 'startShown': 'always'},

                {'label': _translate("Survey Model File"),
                 'body': _translate(
                    "Inserting a JSON file (exported from Pavlovia Surveys) means that the survey is embedded within "
                    "this project and will not change unless you import it again (better for archiving)"),
                 'linkText': _translate("How do I get my survey model file?"),
                 'link': "https://psychopy.org/builder/components/advanced_survey.html#get-json",
                 'startShown': 'always'},
            ],
            label=_translate("Survey type"))

        self.depends += [{
            "dependsOn": "surveyType",  # must be param name
            "condition": "=='id'",  # val to check for
            "param": 'surveyId',  # param property to alter
            "true": "show",  # what to do with param if condition is True
            "false": "hide",  # permitted: hide, show, enable, disable
        }]

        self.params['surveyId'] = Param(
            surveyId, valType='str', inputType="survey", categ='Basic',
            hint=_translate(
                "The ID for your survey on Pavlovia. Tip: Right click to open the survey in your browser!"
            ),
            label=_translate("Survey id"))

        self.depends += [{
            "dependsOn": "surveyType",  # must be param name
            "condition": "=='json'",  # val to check for
            "param": 'surveyJson',  # param property to alter
            "true": "show",  # what to do with param if condition is True
            "false": "hide",  # permitted: hide, show, enable, disable
        }]

        self.params['surveyJson'] = Param(
            surveyJson, valType='str', inputType="file", categ='Basic',
            hint=_translate(
                "File path of the JSON file used to construct the survey"
            ),
            label=_translate("Survey JSON"))

    def writeRoutineBeginCodeJS(self, buff, modular):
        code = (
                "\n"
                "function %(name)sRoutineBegin(snapshot) {\n"
                "  return async function () {\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(2, relative=True)

        # Usual routine setup stuff
        code = (
            "TrialHandler.fromSnapshot(snapshot); // ensure that .thisN vals are up to date\n"
            "\n"
            "//--- Prepare to start Routine '%(name)s' ---\n"
            "t = 0;\n"
            "frameN = -1;\n"
            "continueRoutine = true; // until we're told otherwise\n"
        )
        buff.writeIndentedLines(code % self.params)

        # Create Survey object
        code = (
            "//--- Starting Routine '%(name)s' ---\n"
            "%(name)s = new visual.Survey({\n"
            "    win: psychoJS.window,\n"
            "    name: '%(name)s',\n"
        )
        buff.writeIndentedLines(code % self.params)
        # Write either survey ID or model
        if self.params['surveyType'] == "id":
            code = (
            "    surveyId: %(surveyId)s,\n"
            )
        else:
            code = (
            "    model: %(surveyJson)s,\n"
            )
        buff.writeIndentedLines(code % self.params)
        code = (
            "});\n"
            "%(name)sClock = new util.Clock();\n"
            "%(name)s.setAutoDraw(true);\n"
            "%(name)s.status = PsychoJS.Status.STARTED;\n"
            "%(name)s.isFinished = false;\n"
            "%(name)s.tStart = t;  // (not accounting for frame time here)\n"
            "%(name)s.frameNStart = frameN;  // exact frame index\n"
            "return Scheduler.Event.NEXT;\n"
        )
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(-2, relative=True)
        code = (
            "  }\n"
            "}\n"
        )
        buff.writeIndentedLines(code % self.params)

    def writeEachFrameCodeJS(self, buff, modular):
        code = (
                "\n"
                "function %(name)sRoutineEachFrame() {\n"
                "  return async function () {\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(2, relative=True)

        # Write each frame active code
        code = (
            "t = %(name)sClock.getTime();\n"
            "frameN = frameN + 1;  // number of completed frames (so 0 is the first frame)\n"
            "// if %(name)s is completed, move on\n"
            "if (%(name)s.isFinished) {\n"
            "  %(name)s.setAutoDraw(false);\n"
            "  %(name)s.status = PsychoJS.Status.FINISHED;\n"
            "  // survey routines are not non-slip safe, so reset the non-slip timer\n"
            "  routineTimer.reset();\n"
            "  return Scheduler.Event.NEXT;\n"
            "}\n"
        )
        buff.writeIndentedLines(code % self.params)
        # Check for escape
        if self.exp.settings.params['Enable Escape'].val:
            code = ("// check for quit (typically the Esc key)\n"
                    "if (psychoJS.experiment.experimentEnded || psychoJS.eventManager.getKeys({keyList:['escape']}).length > 0) {\n"
                    "  return quitPsychoJS('The [Escape] key was pressed. Goodbye!', false);\n"
                    "}\n")
            buff.writeIndentedLines(code)
        # Flip frame
        code = (
            "return Scheduler.Event.FLIP_REPEAT;\n"
        )
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(-2, relative=True)
        code = (
            "  }\n"
            "}\n"
        )
        buff.writeIndentedLines(code % self.params)

    def writeRoutineEndCodeJS(self, buff, modular):
        code = (
                "\n"
                "function %(name)sRoutineEnd(snapshot) {\n"
                "  return async function () {\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(2, relative=True)

        code = (
            "//--- Ending Routine '%(name)s' ---\n"
            "// get data from %(name)s\n"
            "const %(name)sResponse =  %(name)s.getResponse();\n"
            "function addRecursively(resp, name) {\n"
            "    if (resp.constructor === Object) {\n"
            "        // if resp is an object, add each part as a column\n"
            "        for (let subquestion in resp) {\n"
            "            addRecursively(resp[subquestion], `${name}.${subquestion}`);\n"
            "        }\n"
            "    } else {\n"
            "        psychoJS.experiment.addData(name, resp);\n"
            "    }\n"
            "}\n"
            "// recursively add survey responses\n"
            "addRecursively(%(name)sResponse, '%(name)s');\n"
        )
        if self.params['surveyType'] == "id":
            # Only call save if using an ID, otherwise saving is just to exp file
            code += (
                "await %(name)s.save();\n"
            )
        buff.writeIndentedLines(code % self.params)
        code = (
            "// Routines running outside a loop should always advance the datafile row\n"
            "if (currentLoop === psychoJS.experiment) {\n"
            "  psychoJS.experiment.nextEntry(snapshot);\n"
            "}\n"
            "return Scheduler.Event.NEXT;\n"
        )
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(-2, relative=True)
        code = (
            "  }\n"
            "}\n"
        )
        buff.writeIndentedLines(code % self.params)
