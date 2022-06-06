#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
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

import os
import codecs
import xml.etree.ElementTree as xml
from xml.dom import minidom
from copy import deepcopy, copy
from pathlib import Path
from pkg_resources import parse_version

import psychopy
from psychopy import data, __version__, logging
from .components.resourceManager import ResourceManagerComponent
from .components.static import StaticComponent
from .exports import IndentingBuffer, NameSpace
from .flow import Flow
from .loops import TrialHandler, LoopInitiator, \
    LoopTerminator, StairHandler, MultiStairHandler
from .params import _findParam, Param, legacyParams
from psychopy.experiment.routines._base import Routine, BaseStandaloneRoutine
from psychopy.experiment.routines import getAllStandaloneRoutines
from . import utils, py2js
from .components import getComponents, getAllComponents

from psychopy.localization import _translate
import locale

from collections import namedtuple, OrderedDict

from ..alerts import alert

RequiredImport = namedtuple('RequiredImport',
                            field_names=('importName',
                                         'importFrom',
                                         'importAs'))


# Some params have previously had types which cause errors compiling in new versions, so we need to keep track of them and force them to the new type if needed
forceType = {
    'pos': 'list',
    'size': 'list',
    ('KeyboardComponent', 'allowedKeys'): 'list',
    ('cedrusButtonBoxComponent', 'allowedKeys'): 'list',
    ('DotsComponent', 'fieldPos'): 'list',
    ('JoyButtonsComponent', 'allowedKeys'): 'list',
    ('JoyButtonsComponent', 'correctAns'): 'list',
    ('JoystickComponent', 'clickable'): 'list',
    ('JoystickComponent', 'saveParamsClickable'): 'list',
    ('JoystickComponent', 'allowedButtons'): 'list',
    ('MicrophoneComponent', 'transcribeWords'): 'list',
    ('MouseComponent', 'clickable'): 'list',
    ('MouseComponent', 'saveParamsClickable'): 'list',
    ('NoiseStimComponent', 'noiseElementSize'): 'list',
    ('PatchComponent', 'sf'): 'list',
    ('RatingScaleComponent', 'categoryChoices'): 'list',
    ('RatingScaleComponent', 'labels'): 'list',
    ('RegionOfInterestComponent', 'vertices'): 'list',
    ('SettingsComponent', 'Window size (pixels)'): 'list',
    ('SettingsComponent', 'Resources'): 'list',
    ('SettingsComponent', 'mgBlink'): 'list',
    ('SliderComponent', 'ticks'): 'list',
    ('SliderComponent', 'labels'): 'list',
    ('SliderComponent', 'styleTweaks'): 'list'
}

# # Code to generate force list
# comps = experiment.components.getAllComponents()
# exp = experiment._experiment.Experiment()
# rt = experiment.routines.Routine("routine", exp)
# exp.addRoutine("routine", rt)
#
# forceType = {
#     'pos': 'list',
#     'size': 'list',
#     'vertices': 'list',
# }
# for Comp in comps.values():
#     comp = Comp(exp=exp, parentName="routine")
#     for key, param in comp.params.items():
#         if param.valType == 'list' and key not in forceType:
#             forceType[(Comp.__name__, key)] = 'list'


class Experiment:
    """
    An experiment contains a single Flow and at least one
    Routine. The Flow controls how Routines are organised
    e.g. the nature of repeats and branching of an experiment.
    """

    def __init__(self, prefs=None):
        super(Experiment, self).__init__()
        self.name = ''
        self.filename = ''  # update during load/save xml
        self.flow = Flow(exp=self)  # every exp has exactly one flow
        self.routines = {}
        # get prefs (from app if poss or from cfg files)
        if prefs is None:
            prefs = psychopy.prefs
        # deepCopy doesn't like the full prefs object to be stored, so store
        # each subset
        self.prefsAppDataCfg = prefs.appDataCfg
        self.prefsGeneral = prefs.general
        self.prefsApp = prefs.app
        self.prefsCoder = prefs.coder
        self.prefsBuilder = prefs.builder
        self.prefsPaths = prefs.paths
        # this can be checked by the builder that this is an experiment and a
        # compatible version
        self.psychopyVersion = __version__

        # What libs are needed (make sound come first)
        self.requiredImports = []
        libs = ('sound', 'gui', 'visual', 'core', 'data', 'event',
                'logging', 'clock', 'colors', 'layout')
        self.requirePsychopyLibs(libs=libs)
        self.requireImport(importName='keyboard',
                           importFrom='psychopy.hardware')

        _settingsComp = getComponents(fetchIcons=False)['SettingsComponent']
        self.settings = _settingsComp(parentName='', exp=self)
        # this will be the xml.dom.minidom.doc object for saving
        self._doc = xml.ElementTree()
        self.namespace = NameSpace(self)  # manage variable names

        #  _expHandler is a hack to allow saving data from components not
        # inside a loop. data-saving machinery relies on loops, not worth
        # rewriting. `thisExp` will be an ExperimentHandler when used in
        # the generated script, but its easier to use treat it as a
        # TrialHandler during script generation to avoid effectively
        # duplicating code just to work around any differences
        # in writeRoutineEndCode
        self._expHandler = TrialHandler(exp=self, name='thisExp')
        self._expHandler.type = 'ExperimentHandler'  # true at run-time

    def requirePsychopyLibs(self, libs=()):
        """Add a list of top-level psychopy libs that the experiment
        will need. e.g. [visual, event]

        Notes
        -----
        This is a convenience method for `requireImport()`.
        """
        for lib in libs:
            self.requireImport(importName=lib,
                               importFrom='psychopy')

    @property
    def eyetracking(self):
        """What kind of eyetracker this experiment is set up for"""
        return self.settings.params['eyetracker']

    def requireImport(self, importName, importFrom='', importAs=''):
        """Add a top-level import to the experiment.

        Parameters
        ----------
        importName : str
            Name of the package or module to import.
        importFrom : str
            Where to import ``from``.
        importAs : str
            Import ``as`` this name.
        """
        import_ = RequiredImport(importName=importName,
                                 importFrom=importFrom,
                                 importAs=importAs)

        if import_ not in self.requiredImports:
            self.requiredImports.append(import_)

    def addRoutine(self, routineName, routine=None):
        """Add a Routine to the current list of them.

        Can take a Routine object directly or will create
        an empty one if none is given.
        """
        if routine is None:
            # create a default routine with this name
            self.routines[routineName] = Routine(routineName, exp=self)
        else:
            self.routines[routineName] = routine
        return self.routines[routineName]

    def addStandaloneRoutine(self, routineName, routine):
        """Add a standalone Routine to the current list of them.

        Can take a Routine object directly or will create
        an empty one if none is given.
        """
        self.routines[routineName] = routine
        return self.routines[routineName]

    def integrityCheck(self):
        """Check the integrity of the Experiment"""
        # add some checks for things outside the Flow?
        # then check the contents 1-by-1 from the Flow
        self.flow.integrityCheck()

    def writeScript(self, expPath=None, target="PsychoPy", modular=True):
        """Write a PsychoPy script for the experiment
        """
        # self.integrityCheck()

        self.psychopyVersion = psychopy.__version__  # make sure is current
        # set this so that params write for approp target
        utils.scriptTarget = target
        self.expPath = expPath
        script = IndentingBuffer(target=target)  # a string buffer object

        # get date info, in format preferred by current locale as set by app:
        if hasattr(locale, 'nl_langinfo'):
            fmt = locale.nl_langinfo(locale.D_T_FMT)
            localDateTime = data.getDateStr(format=fmt)
        else:
            localDateTime = data.getDateStr(format="%B %d, %Y, at %H:%M")

        # Remove disabled components, but leave original experiment unchanged.
        self_copy = deepcopy(self)
        for key, routine in list(self_copy.routines.items()):  # PY2/3 compat
            # Remove disabled / unimplemented routines
            if routine.disabled or target not in routine.targets:
                for node in self_copy.flow:
                    if node == routine:
                        self_copy.flow.removeComponent(node)
                        if target not in routine.targets:
                            # If this routine isn't implemented in target library, print alert and mute it
                            alertCode = 4335 if target == "PsychoPy" else 4340
                            alert(alertCode, strFields={'comp': type(routine).__name__})
            # Remove disabled / unimplemented components within routine
            if isinstance(routine, Routine):
                for component in [comp for comp in routine]:
                    if component.disabled or target not in component.targets:
                        routine.removeComponent(component)
                        if component.targets and target not in component.targets:
                            # If this component isn't implemented in target library, print alert and mute it
                            alertCode = 4335 if target == "PsychoPy" else 4340
                            alert(alertCode, strFields={'comp': type(component).__name__})

        if target == "PsychoPy":
            self_copy.settings.writeInitCode(script, self_copy.psychopyVersion,
                                             localDateTime)

            # Write "run once" code sections
            for entry in self_copy.flow:
                # NB each entry is a routine or LoopInitiator/Terminator
                self_copy._currentRoutine = entry
                if hasattr(entry, 'writeRunOnceInitCode'):
                    entry.writeRunOnceInitCode(script)
                if hasattr(entry, 'writePreCode'):
                    entry.writePreCode(script)
            script.write("\n\n")

            # present info, make logfile
            self_copy.settings.writeStartCode(script, self_copy.psychopyVersion)
            # writes any components with a writeStartCode()
            self_copy.flow.writeStartCode(script)
            self_copy.settings.writeWindowCode(script)  # create our visual.Window()
            self_copy.settings.writeIohubCode(script)
            # for JS the routine begin/frame/end code are funcs so write here

            # write the rest of the code for the components
            self_copy.flow.writeBody(script)
            self_copy.settings.writeEndCode(script)  # close log file
            script = script.getvalue()

        elif target == "PsychoJS":
            script.oneIndent = "  "  # use 2 spaces rather than python 4

            self_copy.settings.writeInitCodeJS(script, self_copy.psychopyVersion,
                                               localDateTime, modular)

            script.writeIndentedLines("// Start code blocks for 'Before Experiment'")
            toWrite = list(self_copy.routines)
            toWrite.extend(list(self_copy.flow))
            for entry in self_copy.flow:
                # NB each entry is a routine or LoopInitiator/Terminator
                self_copy._currentRoutine = entry
                if hasattr(entry, 'writePreCodeJS') and entry.name in toWrite:
                    entry.writePreCodeJS(script)
                    toWrite.remove(entry.name)  # this one's done

            # Write window code
            self_copy.settings.writeWindowCodeJS(script)

            self_copy.flow.writeFlowSchedulerJS(script)
            self_copy.settings.writeExpSetupCodeJS(script,
                                                   self_copy.psychopyVersion)

            # initialise the components for all Routines in a single function
            script.writeIndentedLines("\nasync function experimentInit() {")
            script.setIndentLevel(1, relative=True)

            # routine init sections
            toWrite = list(self_copy.routines)
            toWrite.extend(list(self_copy.flow))
            for entry in self_copy.flow:
                # NB each entry is a routine or LoopInitiator/Terminator
                self_copy._currentRoutine = entry
                if hasattr(entry, 'writeInitCodeJS') and entry.name in toWrite:
                    entry.writeInitCodeJS(script)
                    toWrite.remove(entry.name)  # this one's done

            # create globalClock etc
            code = ("// Create some handy timers\n"
                    "globalClock = new util.Clock();"
                    "  // to track the time since experiment started\n"
                    "routineTimer = new util.CountdownTimer();"
                    "  // to track time remaining of each (non-slip) routine\n"
                    "\nreturn Scheduler.Event.NEXT;")
            script.writeIndentedLines(code)
            script.setIndentLevel(-1, relative=True)
            script.writeIndentedLines("}\n")

            # This differs to the Python script. We can loop through all
            # Routines once (whether or not they get used) because we're using
            # functions that may or may not get called later.
            # Do the Routines of the experiment first
            toWrite = list(self_copy.routines)
            for thisItem in self_copy.flow:
                if thisItem.getType() in ['LoopInitiator', 'LoopTerminator']:
                    self_copy.flow.writeLoopHandlerJS(script, modular)
                elif thisItem.name in toWrite:
                    self_copy._currentRoutine = self_copy.routines[thisItem.name]
                    self_copy._currentRoutine.writeRoutineBeginCodeJS(script, modular)
                    self_copy._currentRoutine.writeEachFrameCodeJS(script, modular)
                    self_copy._currentRoutine.writeRoutineEndCodeJS(script, modular)
                    toWrite.remove(thisItem.name)
            self_copy.settings.writeEndCodeJS(script)

            # Add JS variable declarations e.g., var msg;
            script = py2js.addVariableDeclarations(script.getvalue(), fileName=self.expPath)

            # Reset loop controller ready for next call to writeScript
            self_copy.flow._resetLoopController()

        return script

    @property
    def _xml(self):
        # Create experiment root element
        experimentNode = xml.Element("PsychoPy2experiment")
        experimentNode.set('encoding', 'utf-8')
        experimentNode.set('version', __version__)
        # Add settings node
        settingsNode = self.settings._xml
        experimentNode.append(settingsNode)
        # Add routines node
        routineNode = xml.Element("Routines")
        for key, routine in self.routines.items():
            routineNode.append(routine._xml)
        experimentNode.append(routineNode)
        # Add flow node
        flowNode = self.flow._xml
        experimentNode.append(flowNode)

        return experimentNode

    def saveToXML(self, filename):
        self.psychopyVersion = psychopy.__version__  # make sure is current
        # create the dom object
        self.xmlRoot = self._xml
        # convert to a pretty string
        # update our document to use the new root
        self._doc._setroot(self.xmlRoot)
        simpleString = xml.tostring(self.xmlRoot, 'utf-8')
        pretty = minidom.parseString(simpleString).toprettyxml(indent="  ")
        # then write to file
        if not filename.endswith(".psyexp"):
            filename += ".psyexp"

        with codecs.open(filename, 'wb', encoding='utf-8-sig') as f:
            f.write(pretty)

        self.filename = filename
        return filename  # this may have been updated to include an extension

    def _getShortName(self, longName):
        return longName.replace('(', '').replace(')', '').replace(' ', '')

    def _getXMLparam(self, params, paramNode, componentNode=None):
        """params is the dict of params of the builder component
        (e.g. stimulus) into which the parameters will be inserted
        (so the object to store the params should be created first)
        paramNode is the parameter node fetched from the xml file
        """
        name = paramNode.get('name')
        valType = paramNode.get('valType')
        val = paramNode.get('val')
        # many components need web char newline replacement
        if not name == 'advancedParams':
            val = val.replace("&#10;", "\n")

        # custom settings (to be used when
        if valType == 'fixedList':  # convert the string to a list
            try:
                params[name].val = eval('list({})'.format(val))
            except NameError:  # if val is a single string it will look like variable
                params[name].val = [val]
        elif name == 'storeResponseTime':
            return  # deprecated in v1.70.00 because it was redundant
        elif name == 'nVertices':  # up to 1.85 there was no shape param
            # if no shape param then use "n vertices" only
            if _findParam('shape', componentNode) is None:
                if val == '2':
                    params['shape'].val = "line"
                elif val == '3':
                    params['shape'].val = "triangle"
                elif val == '4':
                    params['shape'].val = "rectangle"
                else:
                    params['shape'].val = "regular polygon..."
            params['nVertices'].val = val
        elif name == 'startTime':  # deprecated in v1.70.00
            params['startType'].val = "{}".format('time (s)')
            params['startVal'].val = "{}".format(val)
            return  # times doesn't need to update its type or 'updates' rule
        elif name == 'forceEndTrial':  # deprecated in v1.70.00
            params['forceEndRoutine'].val = bool(val)
            return  # forceEndTrial doesn't need to update type or 'updates'
        elif name == 'forceEndTrialOnPress':  # deprecated in v1.70.00
            params['forceEndRoutineOnPress'].val = bool(val)
            return  # forceEndTrial doesn't need to update  type or 'updates'
        elif name == 'forceEndRoutineOnPress':
            if val == 'True':
                val = "any click"
            elif val == 'False':
                val = "never"
            params['forceEndRoutineOnPress'].val = val
            return
        elif name == 'trialList':  # deprecated in v1.70.00
            params['conditions'].val = eval(val)
            return  # forceEndTrial doesn't need to update  type or 'updates'
        elif name == 'trialListFile':  # deprecated in v1.70.00
            params['conditionsFile'].val = "{}".format(val)
            return  # forceEndTrial doesn't need to update  type or 'updates'
        elif name == 'duration':  # deprecated in v1.70.00
            params['stopType'].val = u'duration (s)'
            params['stopVal'].val = "{}".format(val)
            return  # times doesn't need to update its type or 'updates' rule
        elif name == 'allowedKeys' and valType == 'str':  # changed v1.70.00
            # ynq used to be allowed, now should be 'y','n','q' or
            # ['y','n','q']
            if len(val) == 0:
                newVal = val
            elif val[0] == '$':
                newVal = val[1:]  # they were using code (which we can reuse)
            elif val.startswith('[') and val.endswith(']'):
                # they were using code (slightly incorrectly!)
                newVal = val[1:-1]
            elif val in ['return', 'space', 'left', 'right', 'escape']:
                newVal = val  # they were using code
            else:
                # convert string to list of keys then represent again as a
                # string!
                newVal = repr(list(val))
            params['allowedKeys'].val = newVal
            params['allowedKeys'].valType = 'code'
        elif name == 'correctIf':  # deprecated in v1.60.00
            corrIf = val
            corrAns = corrIf.replace(
                'resp.keys==unicode(', '').replace(')', '')
            params['correctAns'].val = corrAns
            name = 'correctAns'  # then we can fetch other aspects below
        elif 'olour' in name:  # colour parameter was Americanised v1.61.00
            name = name.replace('olour', 'olor')
            params[name].val = val
        elif name == 'times':  # deprecated in v1.60.00
            times = eval('%s' % val)
            params['startType'].val = "{}".format('time (s)')
            params['startVal'].val = "{}".format(times[0])
            params['stopType'].val = "{}".format('time (s)')
            params['stopVal'].val = "{}".format(times[1])
            return  # times doesn't need to update its type or 'updates' rule
        elif name in ('Before Experiment', 'Begin Experiment', 'Begin Routine', 'Each Frame',
                      'End Routine', 'End Experiment',
                      'Before JS Experiment', 'Begin JS Experiment', 'Begin JS Routine', 'Each JS Frame',
                      'End JS Routine', 'End JS Experiment'):
            # up to version 1.78.00 and briefly in 2021.1.0-1.1 these were 'code'
            params[name].val = val
            params[name].valType = 'extendedCode'
            return  # so that we don't update valType again below
        elif name == 'Saved data folder':
            # deprecated in 1.80 for more complete data filename control
            params[name] = Param(
                val, valType='code', allowedTypes=[],
                hint=_translate("Name of the folder in which to save data"
                                " and log files (blank defaults to the "
                                "builder pref)"),
                categ='Data')
        elif name == 'channel':  # was incorrectly set to be valType='str' until 3.1.2
            params[name].val = val
            params[name].valType = 'code'  # override
        elif 'val' in list(paramNode.keys()):
            if val == 'window units':  # changed this value in 1.70.00
                params[name].val = 'from exp settings'
            # in v1.80.00, some RatingScale API and Param fields were changed
            # Try to avoid a KeyError in these cases so can load the expt
            elif name in ('choiceLabelsAboveLine', 'lowAnchorText',
                          'highAnchorText'):
                # not handled, just ignored; want labels=[lowAnchor,
                # highAnchor]
                return
            elif name == 'customize_everything':
                # Try to auto-update the code:
                v = val  # python code, not XML
                v = v.replace('markerStyle', 'marker').replace(
                    'customMarker', 'marker')
                v = v.replace('stretchHoriz', 'stretch').replace(
                    'displaySizeFactor', 'size')
                v = v.replace('textSizeFactor', 'textSize')
                v = v.replace('ticksAboveLine=False', 'tickHeight=-1')
                v = v.replace('showScale=False', 'scale=None').replace(
                    'allowSkip=False', 'skipKeys=None')
                v = v.replace('showAnchors=False', 'labels=None')
                # lowAnchorText highAnchorText will trigger obsolete error
                # when run the script
                params[name].val = v
            elif name == 'storeResponseTime':
                return  # deprecated in v1.70.00 because it was redundant
            elif name == 'Resources':
                # if the xml import hasn't automatically converted from string?
                if type(val) == str:
                    resources = data.utils.listFromString(val)
                if self.psychopyVersion == '2020.2.5':
                    # in 2020.2.5 only, problems were:
                    #   a) resources list was saved as a string and
                    #   b) with wrong root folder
                    resList = []
                    for resourcePath in resources:
                        # doing this the blunt way but should we check for existence?
                        resourcePath = resourcePath.replace("../", "")  # it was created using wrong root
                        resourcePath = resourcePath.replace("\\", "/")  # created using windows \\
                        resList.append(resourcePath)
                    resources = resList  # push our new list back to resources
                params[name].val = resources
            else:
                if name in params:
                    params[name].val = val
                else:
                    # we found an unknown parameter (probably from the future)
                    params[name] = Param(
                        val, valType=paramNode.get('valType'), inputType="inv",
                        allowedTypes=[], label=_translate(name),
                        hint=_translate(
                            "This parameter is not known by this version "
                            "of PsychoPy. It might be worth upgrading, otherwise "
                            "press the X button to remove this parameter."))
                    params[name].allowedTypes = paramNode.get('allowedTypes')
                    if params[name].allowedTypes is None:
                        params[name].allowedTypes = []
                    if name not in legacyParams + ['JS libs', 'OSF Project ID']:
                        # don't warn people if we know it's OK (e.g. for params
                        # that have been removed
                        msg = _translate(
                            "Parameter %r is not known to this version of "
                            "PsychoPy but has come from your experiment file "
                            "(saved by a future version of PsychoPy?). This "
                            "experiment may not run correctly in the current "
                            "version.")
                        logging.warn(msg % name)
                        logging.flush()

        # get the value type and update rate
        if 'valType' in list(paramNode.keys()):
            params[name].valType = paramNode.get('valType')
            # compatibility checks:
            if name in ['allowedKeys'] and paramNode.get('valType') == 'str':
                # these components were changed in v1.70.00
                params[name].valType = 'code'
            elif name == 'Selected rows':
                # changed in 1.81.00 from 'code' to 'str': allow string or var
                params[name].valType = 'str'
            # conversions based on valType
            if params[name].valType == 'bool':
                params[name].val = eval("%s" % params[name].val)
        if 'updates' in list(paramNode.keys()):
            params[name].updates = paramNode.get('updates')

    def loadFromXML(self, filename):
        """Loads an xml file and parses the builder Experiment from it
        """
        self._doc.parse(filename)
        root = self._doc.getroot()

        # some error checking on the version (and report that this isn't valid
        # .psyexp)?
        filenameBase = os.path.basename(filename)

        if root.tag != "PsychoPy2experiment":
            logging.error('%s is not a valid .psyexp file, "%s"' %
                          (filenameBase, root.tag))
            # the current exp is already vaporized at this point, oops
            return
        self.psychopyVersion = root.get('version')
        # If running an experiment from a future version, send alert to change "Use Version"
        if parse_version(psychopy.__version__) < parse_version(self.psychopyVersion):
            alert(code=4051, strFields={'version': self.psychopyVersion})
        # If versions are either side of 2021, send alert
        if parse_version(psychopy.__version__) >= parse_version("2021.1.0") > parse_version(self.psychopyVersion):
            alert(code=4052, strFields={'version': self.psychopyVersion})

        # Parse document nodes
        # first make sure we're empty
        self.flow = Flow(exp=self)  # every exp has exactly one flow
        self.routines = {}
        self.namespace = NameSpace(self)  # start fresh
        modifiedNames = []
        duplicateNames = []

        # fetch exp settings
        settingsNode = root.find('Settings')
        for child in settingsNode:
            self._getXMLparam(params=self.settings.params, paramNode=child,
                              componentNode=settingsNode)
        # name should be saved as a settings parameter (only from 1.74.00)
        if self.settings.params['expName'].val in ['', None, 'None']:
            shortName = os.path.splitext(filenameBase)[0]
            self.setExpName(shortName)
        # fetch routines
        routinesNode = root.find('Routines')
        allCompons = getAllComponents(
            self.prefsBuilder['componentsFolders'], fetchIcons=False)
        allRoutines = getAllStandaloneRoutines(fetchIcons=False)
        # get each routine node from the list of routines
        for routineNode in routinesNode:
            if routineNode.tag == "Routine":
                routineGoodName = self.namespace.makeValid(
                    routineNode.get('name'))
                if routineGoodName != routineNode.get('name'):
                    modifiedNames.append(routineNode.get('name'))
                self.namespace.user.append(routineGoodName)
                routine = Routine(name=routineGoodName, exp=self)
                # self._getXMLparam(params=routine.params, paramNode=routineNode)
                self.routines[routineNode.get('name')] = routine
                for componentNode in routineNode:

                    componentType = componentNode.tag
                    if componentType in allCompons:
                        # create an actual component of that type
                        component = allCompons[componentType](
                            name=componentNode.get('name'),
                            parentName=routineNode.get('name'), exp=self)
                    else:
                        # create UnknownComponent instead
                        component = allCompons['UnknownComponent'](
                            name=componentNode.get('name'),
                            parentName=routineNode.get('name'), exp=self)
                    # check for components that were absent in older versions of
                    # the builder and change the default behavior
                    # (currently only the new behavior of choices for RatingScale,
                    # HS, November 2012)
                    # HS's modification superseded Jan 2014, removing several
                    # RatingScale options
                    if componentType == 'RatingScaleComponent':
                        if (componentNode.get('choiceLabelsAboveLine') or
                                componentNode.get('lowAnchorText') or
                                componentNode.get('highAnchorText')):
                            pass
                        # if not componentNode.get('choiceLabelsAboveLine'):
                        #    # this rating scale was created using older version
                        #    component.params['choiceLabelsAboveLine'].val=True
                    # populate the component with its various params
                    for paramNode in componentNode:
                        self._getXMLparam(params=component.params,
                                          paramNode=paramNode,
                                          componentNode=componentNode)
                    compGoodName = self.namespace.makeValid(
                        componentNode.get('name'))
                    if compGoodName != componentNode.get('name'):
                        modifiedNames.append(componentNode.get('name'))
                    self.namespace.add(compGoodName)
                    component.params['name'].val = compGoodName
                    routine.append(component)
            else:
                if routineNode.tag in allRoutines:
                    # If not a routine, may be a standalone routine
                    routine = allRoutines[routineNode.tag](exp=self, name=routineNode.get('name'))
                else:
                    # Otherwise treat as unknown
                    routine = allRoutines['UnknownRoutine'](exp=self, name=routineNode.get('name'))
                # Apply all params
                for paramNode in routineNode:
                    if paramNode.tag == "Param":
                        for key, val in paramNode.items():
                            setattr(routine.params[paramNode.get("name")], key, val)
                # Add routine to experiment
                self.addStandaloneRoutine(routine.name, routine)
        # for each component that uses a Static for updates, we need to set
        # that
        for thisRoutine in list(self.routines.values()):
            for thisComp in thisRoutine:
                for thisParamName in thisComp.params:
                    thisParam = thisComp.params[thisParamName]
                    if thisParamName == 'advancedParams':
                        continue  # advanced isn't a normal param
                    elif thisParam.updates and "during:" in thisParam.updates:
                        # remove the part that says 'during'
                        updates = thisParam.updates.split(': ')[1]
                        routine, static = updates.split('.')
                        if routine not in self.routines:
                            msg = ("%s was set to update during %s Static "
                                   "Component, but that component no longer "
                                   "exists")
                            logging.warning(msg % (thisParamName, static))
                        else:
                            thisRoutine = \
                                self.routines[routine].getComponentFromName(
                                    static)
                            if thisRoutine is None:
                                continue
                            self.routines[routine].getComponentFromName(
                                static).addComponentUpdate(
                                thisRoutine.params['name'],
                                thisComp.params['name'], thisParamName)

        # fetch flow settings
        flowNode = root.find('Flow')
        loops = {}
        for elementNode in flowNode:
            if elementNode.tag == "LoopInitiator":
                loopType = elementNode.get('loopType')
                loopName = self.namespace.makeValid(elementNode.get('name'))
                if loopName != elementNode.get('name'):
                    modifiedNames.append(elementNode.get('name'))
                self.namespace.add(loopName)
                loop = eval('%s(exp=self,name="%s")' % (loopType, loopName))
                loops[loopName] = loop
                for paramNode in elementNode:
                    self._getXMLparam(paramNode=paramNode, params=loop.params)
                    # for conditions convert string rep to list of dicts
                    if paramNode.get('name') == 'conditions':
                        param = loop.params['conditions']
                        # e.g. param.val=[{'ori':0},{'ori':3}]
                        try:
                            param.val = eval('%s' % (param.val))
                        except SyntaxError:
                            # This can occur if Python2.7 conditions string
                            # contained long ints (e.g. 8L) and these can't be
                            # parsed by Py3. But allow the file to carry on
                            # loading and the conditions will still be loaded
                            # from the xlsx file
                            pass
                # get condition names from within conditionsFile, if any:
                try:
                    # psychophysicsstaircase demo has no such param
                    conditionsFile = loop.params['conditionsFile'].val
                except Exception:
                    conditionsFile = None
                if conditionsFile in ['None', '']:
                    conditionsFile = None
                if conditionsFile:
                    try:
                        trialList, fieldNames = data.importConditions(
                            conditionsFile, returnFieldNames=True)
                        for fname in fieldNames:
                            if fname != self.namespace.makeValid(fname):
                                duplicateNames.append(fname)
                            else:
                                self.namespace.add(fname)
                    except Exception:
                        pass  # couldn't load the conditions file for now
                self.flow.append(LoopInitiator(loop=loops[loopName]))
            elif elementNode.tag == "LoopTerminator":
                self.flow.append(LoopTerminator(
                    loop=loops[elementNode.get('name')]))
            else:
                if elementNode.get('name') in self.routines:
                    self.flow.append(self.routines[elementNode.get('name')])
                else:
                    logging.error("A Routine called '{}' was on the Flow but "
                                  "could not be found (failed rename?). You "
                                  "may need to re-insert it".format(
                        elementNode.get('name')))
                    logging.flush()

        if modifiedNames:
            msg = 'duplicate variable name(s) changed in loadFromXML: %s\n'
            logging.warning(msg % ', '.join(list(set(modifiedNames))))
        if duplicateNames:
            msg = 'duplicate variable names: %s'
            logging.warning(msg % ', '.join(list(set(duplicateNames))))
        # Modernise params
        for rt in self.routines.values():
            if not isinstance(rt, list):
                # Treat standalone routines as a routine with one component
                rt = [rt]
            for comp in rt:
                # For each param, if it's pointed to in the forceType array, set it to the new valType
                for paramName, param in comp.params.items():
                    # Param pointed to by name
                    if paramName in forceType:
                        param.valType = forceType[paramName]
                    if (type(comp).__name__, paramName) in forceType:
                        param.valType = forceType[(type(comp).__name__, paramName)]

        # if we succeeded then save current filename to self
        self.filename = filename

    def setExpName(self, name):
        self.settings.params['expName'].val = name

    def getExpName(self):
        return self.settings.params['expName'].val

    @property
    def htmlFolder(self):
        return self.settings.params['HTML path'].val

    def getComponentFromName(self, name):
        """Searches all the Routines in the Experiment for a matching Comp name

        :param name: str name of a component
        :return: a component class or None
        """
        for routine in self.routines.values():
            comp = routine.getComponentFromName(name)
            if comp:
                return comp
        return None

    def getComponentFromType(self, thisType):
        """Searches all the Routines in the Experiment for a matching component type

        :param name: str type of a component e.g., 'KeyBoard'
        :return: True if component exists in experiment
        """
        for routine in self.routines.values():
            exists = routine.getComponentFromType(type)
            exists = routine.getComponentFromType(thisType)
            if exists:
                return True
        return False

    def getResourceFiles(self):
        """Returns a list of known files needed for the experiment
        Interrogates each loop looking for conditions files and each

        """
        join = os.path.join
        abspath = os.path.abspath
        srcRoot = os.path.split(self.filename)[0]

        def getPaths(filePath):
            """Helper to return absolute and relative paths (or None)

            :param filePath: str to a potential file path (rel or abs)
            :return: dict of 'asb' and 'rel' paths or None
            """
            # Only construct paths if filePath is a string
            if type(filePath) != str:
              return None

            thisFile = {}
            # NB: Pathlib might be neater here but need to be careful
            # e.g. on mac:
            #    Path('C:/test/test.xlsx').is_absolute() returns False
            #    Path('/folder/file.xlsx').relative_to('/Applications') gives error
            #    but os.path.relpath('/folder/file.xlsx', '/Applications') correctly uses ../
            if len(filePath) > 2 and (filePath[0] == "/" or filePath[1] == ":")\
                    and os.path.isfile(filePath):
                thisFile['abs'] = filePath
                thisFile['rel'] = os.path.relpath(filePath, srcRoot)
                return thisFile
            else:
                thisFile['rel'] = filePath
                thisFile['abs'] = os.path.normpath(join(srcRoot, filePath))
                if len(thisFile['abs']) <= 256 and os.path.isfile(thisFile['abs']):
                    return thisFile

        def findPathsInFile(filePath):
            """Recursively search a conditions file (xlsx or csv)
             extracting valid file paths in any param/cond

            :param filePath: str to a potential file path (rel or abs)
            :return: list of dicts{'rel','abs'} of valid file paths
            """
            # Clean up filePath that cannot be eval'd
            if filePath.startswith('$'):
                try:
                    filePath = filePath.strip('$')
                    filePath = eval(filePath)
                except NameError:
                    # List files in directory and get condition files
                    if 'xlsx' in filePath or 'xls' in filePath or 'csv' in filePath:
                        # Get all xlsx and csv files
                        expFolder = Path(self.filename).parent
                        spreadsheets = []
                        for pattern in ['*.xlsx', '*.xls', '*.csv', '*.tsv']:
                            # NB potentially make this search recursive with
                            # '**/*.xlsx' but then need to exclude 'data/*.xlsx'
                            spreadsheets.extend(expFolder.glob(pattern))
                        files = []
                        for condFile in spreadsheets:
                            # call the function recursively for each excel file
                            files.extend(findPathsInFile(str(condFile)))
                        return files

            paths = []
            # is it a file?
            thisFile = getPaths(filePath)  # get the abs/rel paths
            # does it exist?
            if not thisFile:
                return paths
            # OK, this file itself is valid so add to resources
            if thisFile not in paths:
                paths.append(thisFile)
            # does it look at all like an excel file?
            if (not isinstance(filePath, str)
                    or not os.path.splitext(filePath)[1] in ['.csv', '.xlsx',
                                                             '.xls']):
                return paths
            conds = data.importConditions(thisFile['abs'])  # load the abs path
            for thisCond in conds:  # thisCond is a dict
                for param, val in list(thisCond.items()):
                    if isinstance(val, str) and len(val):
                        # only add unique entries (can't use set() on a dict)
                        for thisFile in findPathsInFile(val):
                            if thisFile not in paths:
                                paths.append(thisFile)

            return paths

        # Get resources for components
        compResources = []
        handled = False
        for thisEntry in self.flow:
            if thisEntry.getType() == 'Routine':
                # find all params of all compons and check if valid filename
                for thisComp in thisEntry:
                    # if current component is a Resource Manager, we don't need to pre-load ANY resources
                    if isinstance(thisComp, (ResourceManagerComponent, StaticComponent)):
                        handled = True
                    for paramName in thisComp.params:
                        thisParam = thisComp.params[paramName]
                        thisFile = ''
                        if isinstance(thisParam, str):
                            thisFile = getPaths(thisParam)
                        elif isinstance(thisParam.val, str):
                            thisFile = getPaths(thisParam.val)
                        # then check if it's a valid path and not yet included
                        if thisFile and thisFile not in compResources:
                            compResources.append(thisFile)
            elif thisEntry.getType() == 'LoopInitiator' and "Stair" in thisEntry.loop.type:
                url = 'https://lib.pavlovia.org/vendors/jsQUEST.min.js'
                compResources.append({
                    'rel': url, 'abs': url,
                })
        if handled:
            # If resources are handled, clear all component resources
            compResources = []

        # Get resources for loops
        loopResources = []
        for thisEntry in self.flow:
            if thisEntry.getType() == 'LoopInitiator':
                # find all loops and check for conditions filename
                params = thisEntry.loop.params
                if 'conditionsFile' in params:
                    condsPaths = findPathsInFile(params['conditionsFile'].val)
                    # If handled, remove non-conditions file resources
                    if handled:
                        condsPathsRef = copy(condsPaths)  # copy of condsPaths for reference in loop
                        for thisPath in condsPathsRef:
                            isCondFile = any([
                                str(thisPath['rel']).endswith('.xlsx'),
                                str(thisPath['rel']).endswith('.xls'),
                                str(thisPath['rel']).endswith('.csv'),
                                str(thisPath['rel']).endswith('.tsv'),
                            ])
                            if not isCondFile:
                                condsPaths.remove(thisPath)
                    loopResources.extend(condsPaths)

        # Add files from additional resources box
        chosenResources = []
        val = self.settings.params['Resources'].val
        for thisEntry in val:
            thisFile = getPaths(thisEntry)
            if thisFile:
                chosenResources.append(thisFile)

        # Check for any resources not in experiment path
        resources = loopResources + compResources + chosenResources
        resources = [res for res in resources if res is not None]
        for res in resources:
            if srcRoot not in res['abs'] and 'https://' not in res['abs']:
                psychopy.logging.warning("{} is not in the experiment path and "
                                         "so will not be copied to Pavlovia"
                                         .format(res['rel']))

        return resources


class ExpFile(list):
    """An ExpFile is similar to a Routine except that it generates its code
    from the Flow of a separate, complete psyexp file.
    """

    def __init__(self, name, exp, filename=''):
        super(ExpFile, self).__init__()
        self.params = {'name': name}
        self.name = name
        self.exp = exp  # the exp we belong to
        # the experiment we represent on disk (see self.loadExp)
        self.expObject = None
        self.filename = filename
        self._clockName = None  # used in script "t = trialClock.GetTime()"
        self.type = 'ExpFile'

    def __repr__(self):
        _rep = "psychopy.experiment.ExpFile(name='%s',exp=%s,filename='%s')"
        return _rep % (self.name, self.exp, self.filename)

    def writeStartCode(self, buff):
        # tell each object on our flow to write its start code
        for entry in self.flow:
            # NB each entry is a routine or LoopInitiator/Terminator
            self._currentRoutine = entry
            if hasattr(entry, 'writeStartCode'):
                entry.writeStartCode(buff)

    def loadExp(self):
        # fetch the file
        self.expObject = Experiment()
        self.expObject.loadFromXML(self.filename)
        # extract the flow, which is the key part for us:
        self.flow = self.expObject.flow

    def writeInitCode(self, buff):
        # tell each object on our flow to write its init code
        for entry in self.flow:
            # NB each entry is a routine or LoopInitiator/Terminator
            self._currentRoutine = entry
            entry.writeInitCode(buff)

    def writeMainCode(self, buff):
        """This defines the code for the frames of a single routine
        """
        # tell each object on our flow to write its run code
        for entry in self.flow:
            self._currentRoutine = entry
            entry.writeMainCode(buff)

    def writeExperimentEndCode(self, buff):
        """This defines the code for the frames of a single routine
        """
        for entry in self.flow:
            self._currentRoutine = entry
            entry.writeExperimentEndCode(buff)

    def getType(self):
        return 'ExpFile'

    def getMaxTime(self):
        """What the last (predetermined) stimulus time to be presented. If
        there are no components or they have code-based times then will
        default to 10secs
        """
        pass
        # todo?: currently only Routines perform this action
