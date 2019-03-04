#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

from os import path
from psychopy.experiment.components import BaseComponent, Param, _translate
from psychopy import prefs

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))

iconFile = path.join(prefs.paths['resources'], 'base.png')
tooltip = _translate('Unknown: A component that is not known by the current '
                     'installed version of PsychoPy\n(most likely from the '
                     'future)')

# only use _localized values for label values, nothing functional:
_localized = {'name': _translate('Name')}


class UnknownComponent(BaseComponent):
    """This is used by Builder to represent a component that was not known
    by the current installed version of PsychoPy (most likely from the future).
    We want this to be loaded, represented and saved but not used in any
    script-outputs. It should have nothing but a name - other params will be
    added by the loader
    """

    def __init__(self, exp, parentName, name=''):
        self.type = 'Unknown'
        self.exp = exp  # so we can access the experiment if necess
        self.parentName = parentName  # to access the routine too if needed
        self.params = {}
        self.depends = []
        _hint = _translate("Name of this component (alpha-numeric or _, "
                           "no spaces)")
        self.params['name'] = Param(name, valType='code',
                                    hint=_hint,
                                    label=_localized['name'])
        self.order = ['name']  # name first, then timing, then others
    # make sure nothing gets written into experiment for an unknown object
    # class!

    def writeRoutineStartCode(self, buff):
        pass

    def writeStartCode(self, buff):
        pass

    def writeInitCode(self, buff):
        pass

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
