#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Experiment classes:
    Experiment, Flow, Routine, Param, Loop*, *Handlers, and NameSpace

The code that writes out a *_lastrun.py experiment file is (in order):
    experiment.Experiment.writeScript() - starts things off, calls other parts
    settings.SettingsComponent.writeStartCode()
    experiment.Flow.writeBody()
        which will call the .writeBody() methods from each component
    settings.SettingsComponent.writeEndCode()
"""

from .params import getCodeFromParamStr, Param
from .components import getInitVals, getComponents, getAllComponents
from .routines import getAllStandaloneRoutines
from ._experiment import Experiment
from .utils import unescapedDollarSign_re, valid_var_re, nonalphanumeric_re
from psychopy.experiment.utils import CodeGenerationException


def getAllElements(fetchIcons=True):
    """
    Get all components and all standalone routines
    """
    comps = getAllComponents(fetchIcons=fetchIcons)
    rts = getAllStandaloneRoutines(fetchIcons=fetchIcons)
    comps.update(rts)

    return comps


def getAllCategories():
    """
    Get all categories which components and standalone routines can be
    sorted into
    """
    categories = []
    # For each component/standalone routine...
    for name, thisComp in getAllElements().items():
        for thisCat in thisComp.categories:
            # If category is not already present, append it
            if thisCat not in categories:
                categories.append(thisCat)

    return categories
