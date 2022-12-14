from psychopy.experiment.components import getInitVals
from psychopy.experiment.routines import BaseStandaloneRoutine
from psychopy.localization import _translate
from psychopy.experiment import Param
from pathlib import Path


class PavloviaSurveyComponent(BaseStandaloneRoutine):
    categories = ['Responses']
    targets = ["PsychoJS"]
    iconFile = Path(__file__).parent / "survey.png"
    tooltip = _translate("Run a SurveyJS survey in Pavlovia")
    beta = True

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
                {'label': _translate("Survey ID"),
                 'body': _translate(
                     "Linking to a survey ID from Pavlovia Surveys means that the content will automatically update "
                     "if that survey changes (better for dynamic use)"),
                 'linkText': _translate("Take me to Pavlovia..."),
                 'link': "https://pavlovia.org/dashboard?tab=4",
                 'startShown': 'always'},

                {'label': _translate("Survey Model File"),
                 'body': _translate(
                    "Inserting a JSON file (exported from Pavlovia Surveys) means that the survey is embedded within "
                    "this project and will not change unless you import it again (better for archiving)"),
                 'linkText': _translate("Take me to Pavlovia..."),
                 'link': "https://pavlovia.org/dashboard?tab=4",
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
                "ID of the survey on Pavlovia"
            ),
            label=_translate("Survey"))

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
            label=_translate("Survey"))

    def writeInitCodeJS(self, buff):
        inits = getInitVals(self.params, target="PsychoJS")

        code = (
            "%(name)s = new visual.Survey({\n"
            "    win: psychoJS.window,\n"
            "    name: '%(name)s',\n"
        )
        buff.writeIndentedLines(code % inits)
        # Write either survey ID or model
        if self.params['surveyType'] == "id":
            code = (
            "    surveyId: %(surveyId)s,\n"
            )
        else:
            code = (
            "    model: %(surveyJson)s,\n"
            )
        buff.writeIndentedLines(code % inits)
        code = (
            "});\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeRoutineBeginCodeJS(self, buff, modular):
        # create the frame loop for this routine

        code = (
                "\n"
                "function %(name)sRoutineBegin(snapshot) {\n"
                "  return async function () {\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(2, relative=True)

        # Usual routine setup stuff
        code = ("TrialHandler.fromSnapshot(snapshot); // ensure that .thisN vals are up to date\n"
                "\n"
                "//--- Prepare to start Routine '%(name)s' ---\n"
                "continueRoutine = true; // until we're told otherwise\n"
                )
        buff.writeIndentedLines(code % self.params)

        # Set survey to draw
        code = (
            "//--- Starting Routine '%(name)s' ---\n"
            "%(name)s.setAutoDraw(true);\n"
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
            "// if %(name)s is completed, move on\n"
            "if (%(name)s.isFinished) {\n"
            "  %(name)s.setAutoDraw(false);\n"
            "  return Scheduler.Event.NEXT;\n"
        )
        buff.writeIndentedLines(code % self.params)
        # Check for escape
        if self.exp.settings.params['Enable Escape'].val:
            code = ("// check for quit (typically the Esc key)\n"
                    "if (psychoJS.experiment.experimentEnded || psychoJS.eventManager.getKeys({keyList:['escape']}).length > 0) {\n"
                    "  return quitPsychoJS('The [Escape] key was pressed. Goodbye!', false);\n"
                    "}\n")
            buff.writeIndentedLines(code)

        buff.setIndentLevel(-2, relative=True)
        code = (
            "  }\n"
            "}\n"
        )
        buff.writeIndentedLines(code % self.params)

    def writeRoutineEndCodeJS(self, buff, modular):
        code = (
                "\n"
                "function %(name)sRoutineEnd() {\n"
                "  return async function () {\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(2, relative=True)

        code = (
            "//--- Ending Routine '%(name)s' ---\n"
            "%(name)s.status = PsychoJS.Status.FINISHED;\n"
            "// get data from %(name)s\n"
            "let resp = %(name)s.getResponse();\n"
            "psychoJS.experiment.addData('%(name)s.firstname', resp.firstname);\n"
            "await questionnaire.save();\n"
        )
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(-2, relative=True)
        code = (
            "  }\n"
            "}\n"
        )
        buff.writeIndentedLines(code % self.params)
