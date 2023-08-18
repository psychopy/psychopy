#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Language localization for PsychoPy.

Sets the locale value as a wx languageID (int) and initializes gettext
translation _translate():
    from psychopy.app import localization
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

try:
    from ._localization import (
        _translate, _localized, setLocaleWX, locname, available)
except ModuleNotFoundError:
    # if wx doesn't exist we can't translate but most other parts
    # of the _localization lib will not be relevant
    def _translate(val):
        return val
    _localized = {
        # for BaseComponent:
        'name': _translate('Name'),  # fieldName: display label
        'startType': _translate('start type'),
        'stopType': _translate('stop type'),
        'startVal': _translate('Start'),
        'stopVal': _translate('Stop'),
        'startEstim': _translate('Expected start (s)'),
        'durationEstim': _translate('Expected duration (s)'),

        # for BaseVisualComponent:
        'units': _translate('Spatial Units'),
        'color': _translate('Foreground Color'),
        'colorSpace': _translate('Color Space'),
        'fillColor': _translate('Fill Color'),
        'fillColorSpace': _translate('Fill Color Space'),
        'borderColor': _translate('Border Color'),
        'borderColorSpace': _translate('Border Color Space'),
        'contrast': _translate('Contrast'),
        'opacity': _translate('Opacity'),
        'pos': _translate('Position [x,y]'),
        'ori': _translate('Orientation'),
        'size': _translate('Size [w,h]'),

        # for loops
        'Name': _translate('Name'),
        'nReps': _translate('nReps'),
        'conditions': _translate('Conditions'),  # not the same
        'conditionsFile':_translate('conditionsFile'),
        'endPoints': _translate('endPoints'),
        'Selected rows': _translate('Selected rows'),
        'loopType': _translate('loopType'),
        'random seed': _translate('random seed'),
        'Is trials': _translate('Is trials'),
        'min value': _translate('min value'),
        'N reversals': _translate('N reversals'),
        'start value': _translate('start value'),
        'N up': _translate('N up'),
        'max value': _translate('max value'),
        'N down': _translate('N down'),
        'step type': _translate('step type'),
        'step sizes': _translate('step sizes'),
        'stairType': _translate('stairType'),
        'switchMethod': _translate('switchMethod')
    }
