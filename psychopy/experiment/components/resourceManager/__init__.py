from pathlib import Path
from .._base import BaseComponent
from psychopy.localization import _translate
from ...params import Param


class ResourceManagerComponent(BaseComponent):
    categories = ['Custom']
    targets = ['PsychoJS']
    iconFile = Path(__file__).parent / "resource_manager.png"
    tooltip = _translate("Pre-load some resources into memory so that components using them can start without having "
                         "to load first")
    beta = True

    def __init__(self, exp, parentName, name='preloadResources',
                 startType='time (s)', startVal=0,
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 resources="", actionType='Start and Check',
                 saveStartStop=True, syncScreenRefresh=False,
                 disabled=False):
        BaseComponent.__init__(self, exp, parentName, name=name,
                               startType=startType, startVal=startVal,
                               stopType=stopType, stopVal=stopVal,
                               startEstim=startEstim, durationEstim=durationEstim,
                               saveStartStop=saveStartStop, syncScreenRefresh=syncScreenRefresh,
                               disabled=disabled)

        self.params['resources'] = Param(resources,
            valType='list', inputType="fileList", categ='Basic', updates='set every repeat',
            hint=_translate("Resources to download/check"),
            direct=False, label=_translate("Resources"))

        self.params['actionType'] = Param(actionType,
            valType='str', inputType='choice', categ='Basic',
            allowedVals=["Start and Check", "Start Only", "Check Only"],
            hint=_translate("Should this component start and / or stop eye tracker recording?"),
            label=_translate("Record Actions")
        )

        self.params['stopVal'].label = "Check"

        self.depends.append(
             {"dependsOn": "actionType",  # must be param name
              "condition": "=='Start Only'",  # val to check for
              "param": "stop",  # param property to alter
              "true": "hide",  # what to do with param if condition is True
              "false": "show",  # permitted: hide, show, enable, disable
              }
        )
        self.depends.append(
             {"dependsOn": "actionType",  # must be param name
              "condition": "=='Check Only'",  # val to check for
              "param": "start",  # param property to alter
              "true": "hide",  # what to do with param if condition is True
              "false": "show",  # permitted: hide, show, enable, disable
              }
         )