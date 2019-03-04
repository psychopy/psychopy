#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
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

from __future__ import absolute_import, print_function

from .params import getCodeFromParamStr, Param
from .components import getInitVals, getComponents, getAllComponents
from ._experiment import Experiment
from .utils import unescapedDollarSign_re, valid_var_re, \
     nonalphanumeric_re
from psychopy.experiment.utils import CodeGenerationException
