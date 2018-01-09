#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""These are probably going to get used a lot so translate them once and reuse
"""

from ..localization import _translate

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
    'units': _translate('Units'),
    'color': _translate('Color'),
    'colorSpace': _translate('Color space'),
    'opacity': _translate('Opacity'),
    'pos': _translate('Position [x,y]'),
    'ori': _translate('Orientation'),
    'size': _translate('Size [w,h]'),

    # for loops
    'Name': _translate('Name'),
    'nReps': _translate('nReps'),
    'conditions': _translate('Conditions'),  # not the same
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
