#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""
Discover all _localized strings from all Builder components, etc.

Mainly used by validators.py -- need access to _translate()d field names.
"""
import copy
import os
import glob
from psychopy.localization import _localized as _localizedBase
from psychopy.localization import _translate

_localizedCategories = {
    'Basic': _translate('Basic'),
    'Color': _translate('Color'),
    'Layout': _translate('Layout'),
    'Data': _translate('Data'),
    'Screen': _translate('Screen'),
    'Input': _translate('Input'),
    'Dots': _translate('Dots'),
    'Grating': _translate('Grating'),
    'Advanced': _translate('Advanced'),
    'Custom': _translate('Custom'),
    'Carrier': _translate('Carrier'),
    'Envelope': _translate('Envelope'),
    'Appearance': _translate('Appearance'),
    'Save': _translate('Save'),
    'Online':_translate('Online'),
    'Testing':_translate('Testing'),
    'Audio':_translate('Audio'),
    'Format':_translate('Format'),
    'Formatting':_translate('Formatting'),
    'Eyetracking':_translate('Eyetracking'),
    'Target':_translate('Target'),
    'Animation':_translate('Animation'),
    'Transcription':_translate('Transcription'),
    'Timing':_translate('Timing'),
    'Playback':_translate('Playback')
}

_localizedDialogs = {
    # strings for all allowedVals (from all components) go here:
    # interpolation
    'linear': _translate('linear'),
    'nearest': _translate('nearest'),
    # color spaces (except "named") should not be translated:
    'named': _translate('named'),
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
    'same': _translate('same'),
    'different': _translate('different'),
    'experiment': _translate('Experiment'),
    'repeat': _translate('repeat'),
    'none': _translate('none'),
    # startType & stopType:
    'time (s)': _translate('time (s)'),
    'frame N': _translate('frame N'),
    'condition': _translate('condition'),
    'duration (s)': _translate('duration (s)'),
    'duration (frames)': _translate('duration (frames)'),
    # units not translated:
    'pix': 'pix', 'deg': 'deg', 'cm': 'cm',
    'norm': 'norm', 'height': 'height',
    'degFlat': 'degFlat', 'degFlatPos':'degFlatPos',
    # anchor
    'center': _translate('center'),
    'top-center': _translate('top-center'),
    'bottom-center': _translate('bottom-center'),
    'center-left': _translate('center-left'),
    'center-right': _translate('center-right'),
    'top-left': _translate('top-left'),
    'top-right': _translate('top-right'),
    'bottom-left': _translate('bottom-left'),
    'bottom-right': _translate('bottom-right'),
    # tex resolution:
    '32': '32', '64': '64', '128': '128', '256': '256', '512': '512',
    'routine': 'Routine',
    # strings for allowedUpdates:
    'constant': _translate('constant'),
    'set every repeat': _translate('set every repeat'),
    'set every frame': _translate('set every frame'),
    # strings for allowedVals in settings:
    'add': _translate('add'),
    'avg': _translate('average'),
    'average (no FBO)': _translate('average (no FBO)'),  # blend mode
    'use prefs': _translate('use preferences'),
    'on Sync': _translate('on Sync'), # export HTML
    'on Save': _translate('on Save'),
    'manually': _translate('manually'),
    # Data file delimiter
    'auto': _translate('auto'),
    'comma': _translate('comma'),
    'semicolon': _translate('semicolon'),
    'tab': _translate('tab'),
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
    # Keyboard:
    'press': _translate('press'),
    'release': _translate('release'),
    # Mouse:
    'any click': _translate('any click'),
    'valid click': _translate('valid click'),
    'on valid click': _translate('on valid click'),
    'correct click': _translate('correct click'),
    'mouse onset':_translate('mouse onset'),
    'Routine': _translate('Routine'),
    # Joystick:
    'joystick onset':_translate('joystick onset'),
    # Button:
    'every click': _translate('every click'),
    'first click': _translate('first click'),
    'last click': _translate('last click'),
    'button onset': _translate('button onset'),
    # Polygon:
    'line': _translate('line'),
    'triangle': _translate('triangle'),
    'rectangle': _translate('rectangle'),
    'cross': _translate('cross'),
    'star': _translate('star'),
    'arrow': _translate('arrow'),
    'regular polygon...': _translate('regular polygon...'),
    'custom polygon...': _translate('custom polygon...'),
    # Form
    'rows': _translate('rows'),
    'columns': _translate('columns'),
    # Variable component
    'first': _translate('first'),
    'last': _translate('last'),
    'all': _translate('all'),
    'average': _translate('average'),
    # NameSpace
    'one of your Components, Routines, or condition parameters': 
    _translate('one of your Components, Routines, or condition parameters'),
    ' Avoid `this`, `these`, `continue`, `Clock`, or `component` in name': 
    _translate(' Avoid `this`, `these`, `continue`, `Clock`, or `component` in name'),
    'Builder variable': _translate('Builder variable'),
    'Psychopy module': _translate('Psychopy module'),
    'numpy function': _translate('numpy function'),
    'python keyword': _translate('python keyword'),
    # Eyetracker - ROI
    'look at': _translate('look at'),
    'look away': _translate('look away'),
    'every look': _translate('every look'),
    'first look': _translate('first look'),
    'last look': _translate('last look'),
    'roi onset': _translate('roi onset'),
    # Eyetracker - Recording
    'Start and Stop': _translate('Start and Stop'),
    'Start Only': _translate('Start Only'),
    'Stop Only': _translate('Stop Only'),
    'None': _translate('None'),
    # ResourceManager
    'Start and Check': _translate('Start and Check'),
    # 'Start Only': _translate('Start Only'),  # defined in Eyetracker - Recording
    'Check Only': _translate('Check Only'),
    # Panorama
    'Mouse': _translate('Mouse'),
    'Drag': _translate('Drag'),
    'Keyboard (Arrow Keys)': _translate('Keyboard (Arrow Keys)'),
    'Keyboard (WASD)': _translate('Keyboard (WASD)'),
    'Keyboard (Custom keys)': _translate('Keyboard (Custom keys)'),
    'Mouse Wheel': _translate('Mouse Wheel'),
    'Mouse Wheel (Inverted)': _translate('Mouse Wheel (Inverted)'),
    'Keyboard (+-)': _translate('Keyboard (+-)'),
    'Custom': _translate('Custom'),
    # TextBox
    'visible': _translate('visible'),
    'scroll': _translate('scroll'),
    'hidden': _translate('hidden'),
    # Form
    'custom...': _translate('custom...')
}


_localized = copy.copy(_localizedBase)
_localized.update(_localizedCategories)
_localized.update(_localizedDialogs)

thisDir = os.path.dirname(os.path.abspath(__file__))
modules = glob.glob(os.path.join(thisDir, 'components', '*.py'))
components = [os.path.basename(m).replace('.py', '') for m in modules
              if not m.endswith('patch.py')]

for comp in components:
    try:
        exec('from psychopy.experiment.components.' + comp + ' import _localized as _loc')
        _localized.update(_loc)  # noqa: F821  # exists through exec import
    except ImportError:
        pass

if __name__ == '__main__':
    for key, val in _localized.items():
        print(key, val)
