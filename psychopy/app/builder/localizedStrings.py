#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""
Discover all _localized strings from all Builder components, etc.

Mainly used by validators.py -- need access to _translate()d field names.
"""
from __future__ import absolute_import, print_function

import copy
import os
import glob
from psychopy.localization import _localized as _localizedBase
from psychopy.localization import _translate

_localizedDialogs = {
    # strings for all allowedVals (from all components) go here:
    # interpolation
    'linear': _translate('linear'),
    'nearest': _translate('nearest'),
    # color spaces not translated:
    'rgb': 'rgb', 'dkl': 'dkl', 'lms': 'lms', 'hsv': 'hsv',
    'last key': _translate('last key'),
    'first key': _translate('first key'),
    'all keys': _translate('all keys'),
    'nothing': _translate('nothing'),
    'last button': _translate('last button'),
    'first button': _translate('first button'),
    'all buttons': _translate('all buttons'),
    'final': _translate('final'),
    'on click': _translate('on click'),
    'every frame': _translate('every frame'),
    'never': _translate('never'),
    'from exp settings': _translate('from exp settings'),
    'from prefs': _translate('from preferences'),
    'circle': _translate('circle'),
    'square': _translate('square'),  # dots
    # dots
    'direction': _translate('direction'),
    'position': _translate('position'),
    'walk': _translate('walk'),
    # dots
    'same': _translate('same'),
    'different': _translate('different'),
    'experiment': _translate('Experiment'),
    # startType & stopType:
    'time (s)': _translate('time (s)'),
    'frame N': _translate('frame N'),
    'condition': _translate('condition'),
    'duration (s)': _translate('duration (s)'),
    'duration (frames)': _translate('duration (frames)'),
    # units not translated:
    'pix': 'pix', 'deg': 'deg', 'cm': 'cm',
    'norm': 'norm', 'height': 'height',
    # tex resolution:
    '32': '32', '64': '64', '128': '128', '256': '256', '512': '512',
    'routine': 'Routine',
    # strings for allowedUpdates:
    'constant': _translate('constant'),
    'set every repeat': _translate('set every repeat'),
    'set every frame': _translate('set every frame'),
    # strings for allowedVals in settings:
    'add': _translate('add'),
    'avg': _translate('average'),  # blend mode
    'use prefs': _translate('use preferences'),
    # logging level:
    'debug': _translate('debug'),
    'info': _translate('info'),
    'exp': _translate('exp'),
    'data': _translate('data'),
    'warning': _translate('warning'),
    'error': _translate('error'),
    # Experiment info dialog:
    'Field': _translate('Field'),
    'Default': _translate('Default'),
    # Mouse:
    'any click': _translate('any click'),
    'valid click': _translate('valid click'),
    'mouse onset':_translate('mouse onset'),
    'Routine': _translate('Routine'),
    # Polygon:
    'line': _translate('line'),
    'triangle': _translate('triangle'),
    'rectangle': _translate('rectangle'),
    'cross': _translate('cross'),
    'star': _translate('star'),
    'regular polygon...': _translate('regular polygon...'),
    # Variable component
    'first': _translate('first'),
    'last': _translate('last'),
    'all': _translate('all'),
    'average': _translate('average')}

_localized = copy.copy(_localizedBase)
_localized.update(_localizedDialogs)

thisDir = os.path.dirname(os.path.abspath(__file__))
modules = glob.glob(os.path.join(thisDir, 'components', '*.py'))
components = [os.path.basename(m).replace('.py', '') for m in modules
              if not m.endswith('patch.py')]

for comp in components:
    try:
        exec('from psychopy.experiment.components.' + comp + ' import _localized as _loc')
        _localized.update(_loc)
    except ImportError:
        pass

if __name__ == '__main__':
    for key, val in _localized.items():
        print(key, val)
