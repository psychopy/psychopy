from pathlib import Path
from .._base import BaseComponent
from psychopy.localization import _translate
from ...params import Param


class StartPreloadingComponent(BaseComponent):
    categories = ['Custom']
    targets = ['PsychoPy', 'PsychoJS']
    iconFile = Path(__file__).parent / "preload_start.png"
    tooltip = _translate("Pre-load some resources into memory so that components using them can start without having "
                         "to load first")
    beta = True

    def __init__(self, exp, parentName, name='preloadResources',
                 startType='time (s)', startVal=0,
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 resources="",
                 saveStartStop=True, syncScreenRefresh=False,
                 disabled=False):
        BaseComponent.__init__(self, exp, parentName, name=name,
                               startType=startType, startVal=startVal,
                               stopType=stopType, stopVal=stopVal,
                               startEstim=startEstim, durationEstim=durationEstim,
                               saveStartStop=saveStartStop, syncScreenRefresh=syncScreenRefresh,
                               disabled=disabled)

        self.params['resources'] = Param(resources,
            valType='list', inputType="fileList", categ='Basic', allowedUpdates=['constant', 'set every repeat'],
            hint=_translate("Resources to download, specify a file to load it or specify the name of a component to "
                            "load all files it needs."),
            direct=False, label=_translate("Resources"))
