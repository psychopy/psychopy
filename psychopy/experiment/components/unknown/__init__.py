#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from psychopy.experiment.components import BaseComponent, Param, _translate


class UnknownComponent(BaseComponent):
    """This is used by Builder to represent a component that was not known
    by the current installed version of PsychoPy (most likely from the future).
    We want this to be loaded, represented and saved but not used in any
    script-outputs. It should have nothing but a name - other params will be
    added by the loader
    """
    targets = ['PsychoPy']

    categories = ['Other']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'unknown.png'
    tooltip = _translate('Unknown: A component that is not known by the current '
                         'installed version of PsychoPy\n(most likely from the '
                         'future)')
    # hide from the Components panel
    hidden = True

    def __init__(self, exp, parentName, name='', compType="UnknownComponent"):
        self.exp = exp  # so we can access the experiment if necess
        self.parentName = parentName  # to access the routine too if needed
        self.params = {}
        self.depends = []
        super(UnknownComponent, self).__init__(exp, parentName, name=name)
        self.type = compType

    @property
    def _xml(self):
        # make XML node with tag from self.type rather than class name
        return self.makeXmlNode(self.type)

    # make sure nothing gets written into experiment for an unknown object
    # class!

    def writeRoutineStartCode(self, buff):
        pass

    def writeStartCode(self, buff):
        pass

    def writeInitCode(self, buff):
        code = (
            "\n"
            "# Unknown component ignored: %(name)s\n"
            "\n"
        )
        buff.writeIndentedLines(code % self.params)

    def writeInitCodeJS(self, buff):
        code = (
            "\n"
            "// Unknown component ignored: %(name)s\n"
            "\n"
        )
        buff.writeIndentedLines(code % self.params)

    def writeFrameCode(self, buff):
        pass

    def writeRoutineEndCode(self, buff):
        pass

    def writeExperimentEndCode(self, buff):
        pass

    def writeTimeTestCode(self, buff):
        pass

    def writeStartTestCode(self, buff):
        pass

    def writeStopTestCode(self, buff):
        pass

    def writeParamUpdates(self, buff, updateType, paramNames=None):
        pass

    def writeParamUpdate(self, buff, compName, paramName, val, updateType,
                         params=None):
        pass
