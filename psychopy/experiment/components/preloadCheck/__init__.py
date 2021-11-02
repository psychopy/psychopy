from pathlib import Path
from .._base import BaseComponent
from psychopy.localization import _translate
from ...params import Param


class CheckPreloadingComponent(BaseComponent):
    categories = ['Custom']
    targets = ['PsychoPy', 'PsychoJS']
    iconFile = Path(__file__).parent / "preload_check.png"
    tooltip = _translate("Check whether a resource has finished loading and, optionally, pause the experiment "
                         "until it finishes.")
    beta = True

    def __init__(self, exp, parentName, name='checkResources',
                 startType='time (s)', startVal=0, startEstim='',
                 resources="", stall=True,
                 saveStartStop=True, syncScreenRefresh=False,
                 disabled=False):
        BaseComponent.__init__(self, exp, parentName, name=name,
                               startType=startType, startVal=startVal,
                               stopType='duration (s)', stopVal=0,
                               startEstim=startEstim, durationEstim="",
                               saveStartStop=saveStartStop, syncScreenRefresh=syncScreenRefresh,
                               disabled=disabled)

        self.params['resources'] = Param(resources,
            valType='list', inputType="fileList", categ='Basic', allowedUpdates=['constant', 'set every repeat'],
            hint=_translate("Resources to download, specify a file to load it or specify the name of a component to "
                            "load all files it needs."),
            direct=False, label=_translate("Resources"))

        self.params['stall'] = Param(stall,
            valType='bool', inputType="bool", categ='Basic',
            hint=_translate("If files haven't downloaded, should the experiment pause?"), direct=False,
            label=_translate("Stall?"))

        del self.params['stopType']
        del self.params['stopVal']
        del self.params['durationEstim']