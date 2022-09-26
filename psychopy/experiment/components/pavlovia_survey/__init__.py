from .. import BaseComponent, getInitVals
from psychopy.localization import _translate
from psychopy.experiment import Param
from pathlib import Path


class AdvancedSurveyComponent(BaseComponent):
    categories = ['Responses']
    targets = ["PsychoJS"]
    iconFile = Path(__file__).parent / "survey.png"
    tooltip = _translate("Run a SurveyJS survey in Pavlovia")
    beta = True

    def __init__(self, exp, parentName, name='survey',
                 startType='time (s)', startVal='0',
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 forceEndRoutine=True,
                 units="norm", size="(1, 1)", pos="(0, 0)",
                 surveyType="id", surveyId="", surveyJson="",
                 saveStartStop=True, syncScreenRefresh=False,
                 disabled=False
                 ):
        # Initialise base routine
        BaseComponent.__init__(self, exp=exp, parentName=parentName, name=name,
                               startType=startType, startVal=startVal,
                               stopType=stopType, stopVal=stopVal,
                               startEstim=startEstim, durationEstim=durationEstim,
                               saveStartStop=saveStartStop, syncScreenRefresh=syncScreenRefresh,
                               disabled=disabled)
        self.url = "https://psychopy.org/builder/components/advanced_survey.html"

        # Define relationships
        self.depends = []

        self.order += [
            'surveyType',
            'surveyId',
            'surveyJson',
            'forceEndRoutine',
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

        msg = _translate("Should the Routine end when the survey is complete? (e.g end the trial)?")
        self.params['forceEndRoutine'] = Param(
            forceEndRoutine, valType='bool', inputType="bool", allowedTypes=[], categ='Basic',
            updates='constant',
            hint=msg,
            label=_translate('Force end of Routine'))

        # --- Layout ---
        msg = _translate("Units of dimensions for this stimulus")
        self.params['units'] = Param(
            units,
            valType='str', inputType="choice", categ='Layout',
            allowedVals=['from exp settings', 'deg', 'cm', 'pix', 'norm',
                         'height', 'degFlatPos', 'degFlat'],
            hint=msg,
            label=_translate('units'))

        msg = _translate("Position of this stimulus (e.g. [1,2] )")
        self.params['pos'] = Param(
            pos,
            valType='list', inputType="single", categ='Layout',
            updates='constant', allowedTypes=[],
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate('Position [x,y]'))

        msg = _translate("Size of this stimulus (either a single value or "
                         "x,y pair, e.g. 2.5, [1,2] ")
        self.params['size'] = Param(
            size,
            valType='list', inputType="single", categ='Layout',
            updates='constant', allowedTypes=[],
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate('Size [w,h]'))

    def writeInitCodeJS(self, buff):
        inits = getInitVals(self.params, target="PsychoJS")

        code = (
            "%(name)s = new visual.Survey({\n"
            "    win: psychoJS.window,\n"
            "    name: '%(name)s',\n"
            "    units: %(units)s,\n"
            "    size: %(size)s,\n"
            "    pos: %(pos)s,\n"
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

    def writeFrameCodeJS(self, buff):
        """Write the code that will be called every frame
        """
        # Write start code
        if self.writeStartTestCodeJS(buff):
            code = (
                "%(name)s.setAutoDraw(true);\n"
            )
            buff.writeIndentedLines(code % self.params)
            self.exitStartTestJS(buff)
        # Write each frame active code
        self.writeActiveTestCodeJS(buff)
        code = (
            "// if %(name)s is marked as complete online, set status to FINISHED\n"
            "if (%(name)s.complete) {\n"
            "    %(name)s.status = PsychoJS.Status.FINISHED;\n"
        )
        buff.writeIndentedLines(code % self.params)
        if self.params['forceEndRoutine']:
            code = (
            "    continueRoutine = false;\n"
            )
            buff.writeIndentedLines(code % self.params)
        code = (
            "}\n"
        )
        buff.writeIndentedLines(code % self.params)
        self.exitActiveTestJS(buff)
        # Write stop code
        if self.writeStopTestCodeJS(buff):
            if self.params['forceEndRoutine']:
                code = (
                    "// End the routine when %(name)s is completed\n"
                    "continueRoutine = false;\n"
                )
                buff.writeIndentedLines(code % self.params)
            self.exitStopTestJS(buff)
