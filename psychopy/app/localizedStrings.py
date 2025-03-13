#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""
Collections of strings that do not appear explicitly in the source code but need to be localized.
"""
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
    'Favorites': _translate('Favorites'),
    'Stimuli': _translate('Stimuli'),
    'Responses': _translate('Responses'),
    'I/O': _translate('I/O'),
    'Custom': _translate('Custom'),
    'Validation': _translate('Validation'),
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
    'Playback':_translate('Playback'),
    'Window':_translate('Window')
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
    # background image:
    'cover':_translate('cover'),
    'contain':_translate('contain'),
    'fill':_translate('fill'),
    'scale-down':_translate('scale-down'),
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
    'average': _translate('average'),
    'avg': _translate('avg'),
    'average (no FBO)': _translate('average (no FBO)'),  # blend mode
    'use prefs': _translate('use prefs'),
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
    # Clock format:
    'Experiment start':_translate('Experiment start'),
    'Wall clock':_translate('Wall clock'),
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
    'Line': _translate('Line'),
    'Triangle': _translate('Triangle'),
    'Rectangle': _translate('Rectangle'),
    'Circle': _translate('Circle'),
    'Cross': _translate('Cross'),
    'Star': _translate('Star'),
    'Arrow': _translate('Arrow'),
    'Regular polygon...': _translate('Regular polygon...'),
    'Custom polygon...': _translate('Custom polygon...'),
    # Form
    'rows': _translate('rows'),
    'columns': _translate('columns'),
    'custom...': _translate('custom...'),
    # Variable component
    'first': _translate('first'),
    'last': _translate('last'),
    'all': _translate('all'),
    # 'average': _translate('average'), # "appaered at strings for allowedVals in settings"
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
}

_localizedPreferences = {
    # category labels
    'General': _translate('General'),
    'Application': _translate('Application'),
    'Pilot mode': _translate('Pilot mode'),
    'Key Bindings': _translate('Key Bindings'),
    'Hardware': _translate('Hardware'),
    'Connections': _translate('Connections'),
    # section labels
    'general': _translate('general'),
    'app': _translate('app'),
    'builder': "Builder",  # not localized
    'coder': "Coder",  # not localized
    'runner': "Runner",  # not localized
    'piloting': _translate("piloting"), 
    'keyBindings': _translate('keyBindings'),
    'hardware': _translate('hardware'),
    'connections': _translate('connections'),
    # pref labels in General section
    'winType': _translate("window type"),
    'units': _translate("units"),
    'fullscr': _translate("fullscr"),
    'allowGUI': _translate("allowGUI"),
    'paths': _translate('paths'),
    'flac': _translate('flac'),
    'shutdownKey': _translate("shutdownKey"),
    'shutdownKeyModifiers': _translate("shutdownKeyModifiers"),
    'gammaErrorPolicy': _translate("gammaErrorPolicy"),
    'startUpPlugins': _translate("startUpPlugins"),
    'appKeyGoogleCloud':_translate('appKeyGoogleCloud'),
    #'transcrKeyAzure':_translate('transcrKeyAzure'),
    # pref labels in App section
    'showStartupTips': _translate("showStartupTips"),
    'defaultView': _translate("defaultView"),
    'resetPrefs': _translate('resetPrefs'),
    'autoSavePrefs': _translate('autoSavePrefs'),
    'debugMode': _translate('debugMode'),
    'locale': _translate('locale'),
    'errorDialog': _translate('errorDialog'),
    'theme': _translate('theme'),
    'showSplash': _translate('showSplash'),
    # pref labels in Builder section
    'reloadPrevExp': _translate('reloadPrevExp'),
    'codeComponentLanguage': _translate('codeComponentLanguage'),
    'unclutteredNamespace': _translate('unclutteredNamespace'),
    'componentsFolders': _translate('componentsFolders'),
    'componentFilter':_translate('componentFilter'),
    'hiddenComponents': _translate('hiddenComponents'),
    'abbreviateLongCompNames': _translate('abbreviateLongCompNames'),
    'unpackedDemosDir': _translate('unpackedDemosDir'),
    'savedDataFolder': _translate('savedDataFolder'),
    'builderLayout': _translate('builderLayout'),
    'alwaysShowReadme': _translate('alwaysShowReadme'),
    'maxFavorites': _translate('maxFavorites'),
    'confirmRoutineClose': _translate('confirmRoutineClose'),
    # pref labels in Coder section
    'readonly': _translate('readonly'),
    'outputFont': _translate('outputFont'),
    'codeFont': _translate('codeFont'),
    'outputFontSize': _translate('outputFontSize'),
    'codeFontSize': _translate('codeFontSize'),
    'lineSpacing': _translate('lineSpacing'),
    'edgeGuideColumn': _translate('edgeGuideColumn'),
    'showSourceAsst': _translate('showSourceAsst'),
    'showOutput': _translate('showOutput'),
    'autocomplete': _translate('autocomplete'),
    'reloadPrevFiles': _translate('reloadPrevFiles'),
    'preferredShell': _translate('preferredShell'),
    # pref labels in Pilot mode section
    'forceWindowed': _translate('forceWindowed'),
    'forceMouseVisible': _translate('forceMouseVisible'),
    'forcedWindoweSize': _translate('forcedWindowSize'),
    'pilotLoggingLevel': _translate('pilotLoggingLevel'),
    'pilotConsoleLoggingLevel': _translate('pilotConsoleLoggingLevel'),
    'showPilotingIndicator': _translate('showPilotingIndicator'),
    'forceNonRush': _translate('forceNonRush'),
    'replaceParticipantID': _translate('replaceParticipantID'),
    # pref labels in KeyBindings section
    'open': _translate('open'),
    'new': _translate('new'),
    'save': _translate('save'),
    'saveAs': _translate('saveAs'),
    'revealFolder':_translate('revealFolder'),
    'print': _translate('print'),
    'close': _translate('close'),
    'quit': _translate('quit'),
    'preferences': _translate('preferences'),
    'exportHTML': _translate('exportHTML'),
    'cut': _translate('cut'),
    'copy': _translate('copy'),
    'paste': _translate('paste'),
    'duplicate': _translate('duplicate'),
    'indent': _translate('indent'),
    'dedent': _translate('dedent'),
    'smartIndent': _translate('smartIndent'),
    'find': _translate('find'),
    'findAgain': _translate('findAgain'),
    'undo': _translate('undo'),
    'redo': _translate('redo'),
    'comment': _translate('comment'),
    'uncomment': _translate('uncomment'),
    'toggle comment': _translate('toggle comment'),
    'fold': _translate('fold'),
    'enlargeFont': _translate('enlargeFont'),
    'shrinkFont': _translate('shrinkFont'),
    'analyseCode': _translate('analyseCode'),
    'compileScript': _translate('compileScript'),
    'runScript': _translate('runScript'),
    'runnerScript': _translate('runnerScript'),
    'stopScript': _translate('stopScript'),
    'toggleWhitespace': _translate('toggleWhitespace'),
    'toggleEOLs': _translate('toggleEOLs'),
    'toggleIndentGuides': _translate('toggleIndentGuides'),
    'expSettings': _translate('expSettings'),
    'newRoutine': _translate('newRoutine'),
    'copyRoutine': _translate('copyRoutine'),
    'pasteRoutine': _translate('pasteRoutine'),
    'pasteCompon': _translate('pasteCompon'),
    'builderFind': _translate('builderFind'),
    'toggleOutputPanel': _translate('toggleOutputPanel'),
    'renameRoutine': _translate('renameRoutine'),
    'cycleWindows': _translate('cycleWindows'),
    'largerFlow': _translate('largerFlow'),
    'smallerFlow': _translate('smallerFlow'),
    'largerRoutine': _translate('largerRoutine'),
    'smallerRoutine': _translate('smallerRoutine'),
    'toggleReadme': _translate('toggleReadme'),
    'pavlovia_logIn': _translate('pavlovia_logIn'),
    'OSF_logIn': _translate('OSF_logIn'),
    'projectsSync': _translate('projectsSync'),
    'projectsFind': _translate('projectsFind'),
    'projectsOpen': _translate('projectsOpen'),
    'projectsNew': _translate('projectsNew'),
    # pref labels in Hardware section
    'audioWASAPIOnly': _translate('audioWASAPIOnly'),
    #'audioLib': _translate("audio library")
    #'audioLatencyMode': _translate("audio latency mode"),
    'audioDriver': _translate("audioDriver"),
    'audioDevice': _translate("audioDevice"),
    'parallelPorts': _translate("parallelPorts"),
    'qmixConfiguration': _translate("qmixConfiguration"),
    #'highDPI': _translate('Try to support display high DPI'),
    # pref labels in Connections section
    'proxy': _translate('proxy'),
    'autoProxy': _translate('autoProxy'),
    'allowUsageStats': _translate('allowUsageStats'),
    'checkForUpdates': _translate('checkForUpdates'),
    'timeout': _translate('timeout'),
    # pref wxChoice lists:
    'all': _translate('Builder, Coder and Runner'),
    'keep': _translate('same as in the file'),  # line endings
    'abort': _translate('abort'), # gammaErrorPolicy
    'warn': _translate('warn'), # gammaErrorPolicy
    # not translated:
    'pix': 'pix',
    'deg': 'deg',
    'cm': 'cm',
    'norm': 'norm',
    'height': 'height',
    'pyshell': 'pyshell',
    'iPython': 'iPython',
    # font
    'From theme...': _translate('From theme...'),
}


if __name__ == '__main__':
    for collection in (_localizedCategories, 
                       _localizedDialogs,
                       _localizedPreferences):
        for key, val in collection.items():
            print(key, val)
