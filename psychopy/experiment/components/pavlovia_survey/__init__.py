from copy import deepcopy

from .. import BaseComponent
from psychopy.localization import _translate
from psychopy.experiment import Param
from pathlib import Path


class PavloviaSurveyComponent(BaseComponent):
    categories = ['Responses']
    targets = ["PsychoJS"]
    iconFile = Path(__file__).parent / "survey.png"
    tooltip = _translate("Run a SurveyJS survey in Pavlovia")
    beta = True

    def __init__(self, exp, parentName, name='survey',
                 startType='time (s)', startVal='0',
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
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
        self.url = "https://psychopy.org/builder/components/pavlovia_curvey.html"

        # Define relationships
        self.depends = []

        self.order += [
            'surveyType',
            'surveyId',
            'surveyJson',
            'urlParams'
        ]

        self.params['surveyType'] = Param(
            surveyType, valType='code', inputType="richChoice", categ='Basic',
            allowedVals=["id", "json"], allowedLabels=[
                [_translate("Pavlovia ID"), _translate(
                    "Input the ID of a survey created on Pavlovia and linked to your account. Click 'Help' for "
                    "more info on creating a survey in Pavlovia.")],
                [_translate("JSON File"), _translate(
                    "Input the file location of a JSON file from which to construct the survey. You can export "
                    "a survey from Pavlovia in this format via the 'Export Survey' button, and you can use these "
                    "files with any other SurveyJS based system.")],
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

        # self.params['urlParams'] = Param(
        #     urlParams, valType='str', inputType="dict", categ='Basic',
        #     hint=_translate(
        #         "Key/value pairs to pass to the survey via url when running"
        #     ),
        #     label=_translate("URL Parameters"))
