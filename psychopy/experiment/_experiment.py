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
# from future import standard_library
from past.builtins import basestring
from builtins import object
import os
import codecs
import xml.etree.ElementTree as xml
from xml.dom import minidom
from copy import deepcopy

import psychopy
from psychopy import data, __version__, logging
from .exports import IndentingBuffer, NameSpace
from .flow import Flow
from .loops import TrialHandler, LoopInitiator, \
    LoopTerminator, StairHandler, MultiStairHandler
from .params import _findParam, Param
from .routine import Routine
from . import utils, py2js
from .components import getComponents, getAllComponents

from psychopy.localization import _translate
import locale

# standard_library.install_aliases()

from collections import OrderedDict, namedtuple
RequiredImport = namedtuple('RequiredImport',
                            field_names=('importName',
                                         'importFrom',
                                         'importAs'))


class Experiment(object):
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
                'logging', 'clock')
        self.requirePsychopyLibs(libs=libs)
        self.requireImport(importName='keyboard',
                           importFrom='psychopy.hardware')
        self._runOnce = []

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
        self._expHandler.name = self._expHandler.params['name'].val  # thisExp

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

    def runOnce(self, code):
        """Add code to the experiment that is only run exactly once, after
        all `import`s were done.

        Parameters
        ----------
        code : str
            The code to run. May include newline characters to write several
            lines of code at once.

        Notes
        -----
        For running an `import`, use meth:~`Experiment.requireImport` or
        :meth:~`Experiment.requirePsychopyLibs` instead.

        See also
        --------
        :meth:~`Experiment.requireImport`,
        :meth:~`Experiment.requirePsychopyLibs`
        """
        if code not in self._runOnce:
            self._runOnce.append(code)

    def addRoutine(self, routineName, routine=None):
        """Add a Routine to the current list of them.

        Can take a Routine object directly or will create
        an empty one if none is given.
        """
        if routine is None:
            # create a deafult routine with this name
            self.routines[routineName] = Routine(routineName, exp=self)
        else:
            self.routines[routineName] = routine

    def writeScript(self, expPath=None, target="PsychoPy", modular=True):
        """Write a PsychoPy script for the experiment
        """
        self.psychopyVersion = psychopy.__version__  # make sure is current
        # set this so that params write for approp target
        utils.scriptTarget = target
        self.flow._prescreenValues()
        self.expPath = expPath
        script = IndentingBuffer(u'')  # a string buffer object

        # get date info, in format preferred by current locale as set by app:
        if hasattr(locale, 'nl_langinfo'):
            fmt = locale.nl_langinfo(locale.D_T_FMT)
            localDateTime = data.getDateStr(format=fmt)
        else:
            localDateTime = data.getDateStr(format="%B %d, %Y, at %H:%M")

        # Remove disabled components, but leave original experiment unchanged.
        self_copy = deepcopy(self)
        for _, routine in list(self_copy.routines.items()):  # PY2/3 compat
            for component in routine:
                try:
                    if component.params['disabled'].val:
                        routine.removeComponent(component)
                except KeyError:
                    pass

        if target == "PsychoPy":
            self_copy.settings.writeInitCode(script, self_copy.psychopyVersion,
                                             localDateTime)
            # present info, make logfile
            self_copy.settings.writeStartCode(script, self_copy.psychopyVersion)
            # writes any components with a writeStartCode()
            self_copy.flow.writeStartCode(script)
            self_copy.settings.writeWindowCode(script)  # create our visual.Window()
            # for JS the routine begin/frame/end code are funcs so write here

            # write the rest of the code for the components
            self_copy.flow.writeBody(script)
            self_copy.settings.writeEndCode(script)  # close log file
            script = script.getvalue()
        elif target == "PsychoJS":
            script.oneIndent = "  "  # use 2 spaces rather than python 4
            self_copy.settings.writeInitCodeJS(script,self_copy.psychopyVersion,
                                               localDateTime, modular)
            self_copy.flow.writeFlowSchedulerJS(script)
            self_copy.settings.writeExpSetupCodeJS(script,
                                                   self_copy.psychopyVersion)

            # initialise the components for all Routines in a single function
            script.writeIndentedLines("\nfunction experimentInit() {")
            script.setIndentLevel(1, relative=True)

            # routine init sections
            for entry in self_copy.flow:
                # NB each entry is a routine or LoopInitiator/Terminator
                self_copy._currentRoutine = entry
                if hasattr(entry, 'writeInitCodeJS'):
                    entry.writeInitCodeJS(script)

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
            routinesToWrite = list(self_copy.routines)
            for thisItem in self_copy.flow:
                if thisItem.getType() in ['LoopInitiator', 'LoopTerminator']:
                    self_copy.flow.writeLoopHandlerJS(script, modular)
                elif thisItem.name in routinesToWrite:
                    self_copy._currentRoutine = self_copy.routines[thisItem.name]
                    self_copy._currentRoutine.writeRoutineBeginCodeJS(script, modular)
                    self_copy._currentRoutine.writeEachFrameCodeJS(script, modular)
                    self_copy._currentRoutine.writeRoutineEndCodeJS(script, modular)
                    routinesToWrite.remove(thisItem.name)
            self_copy.settings.writeEndCodeJS(script)

            try:
                script = py2js.addVariableDeclarations(script.getvalue())
            except py2js.esprima.error_handler.Error:
                script = script.getvalue()
                print("Failed to parse as JS by esprima")

            # Reset loop controller ready for next call to writeScript
            self_copy.flow._resetLoopController()

        return script

    def saveToXML(self, filename):
        self.psychopyVersion = psychopy.__version__  # make sure is current
        # create the dom object
        self.xmlRoot = xml.Element("PsychoPy2experiment")
        self.xmlRoot.set('version', __version__)
        self.xmlRoot.set('encoding', 'utf-8')
        # store settings
        settingsNode = xml.SubElement(self.xmlRoot, 'Settings')
        for settingName in sorted(self.settings.params):
            setting = self.settings.params[settingName]
            self._setXMLparam(
                parent=settingsNode, param=setting, name=settingName)
        # store routines
        routinesNode = xml.SubElement(self.xmlRoot, 'Routines')
        # routines is a dict of routines
        for routineName, routine in self.routines.items():
            routineNode = self._setXMLparam(
                parent=routinesNode, param=routine, name=routineName)
            # a routine is based on a list of components
            for component in routine:
                componentNode = self._setXMLparam(
                    parent=routineNode, param=component,
                    name=component.params['name'].val)
                for paramName in sorted(component.params):
                    param = component.params[paramName]
                    self._setXMLparam(
                        parent=componentNode, param=param, name=paramName)
        # implement flow
        flowNode = xml.SubElement(self.xmlRoot, 'Flow')
        # a list of elements(routines and loopInit/Terms)
        for element in self.flow:
            elementNode = xml.SubElement(flowNode, element.getType())
            if element.getType() == 'LoopInitiator':
                loop = element.loop
                name = loop.params['name'].val
                elementNode.set('loopType', loop.getType())
                elementNode.set('name', name)
                for paramName in sorted(loop.params):
                    param = loop.params[paramName]
                    paramNode = self._setXMLparam(
                        parent=elementNode, param=param, name=paramName)
                    # override val with repr(val)
                    if paramName == 'conditions':
                        paramNode.set('val', repr(param.val))
            elif element.getType() == 'LoopTerminator':
                elementNode.set('name', element.loop.params['name'].val)
            elif element.getType() == 'Routine':
                elementNode.set('name', '%s' % element.params['name'])
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

    def _setXMLparam(self, parent, param, name):
        """Add a new child to a given xml node. name can include
        spaces and parens, which will be removed to create child name
        """
        if hasattr(param, 'getType'):
            thisType = param.getType()
        else:
            thisType = 'Param'
        # creates and appends to parent
        thisChild = xml.SubElement(parent, thisType)
        thisChild.set('name', name)
        if hasattr(param, 'val'):
            thisChild.set('val', u"{}".format(param.val).replace("\n", "&#10;"))
        if hasattr(param, 'valType'):
            thisChild.set('valType', param.valType)
        if hasattr(param, 'updates'):
            thisChild.set('updates', "{}".format(param.updates))
        return thisChild

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
            params[name].val = eval('list({})'.format(val))
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
                # they were using code (slightly incorectly!)
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
        elif name in ('Begin Experiment', 'Begin Routine', 'Each Frame',
                      'End Routine', 'End Experiment'):
            params[name].val = val
            params[name].valType = 'extendedCode'  # changed in 1.78.00
            return  # so that we don't update valTyp again below
        elif name == 'Saved data folder':
            # deprecated in 1.80 for more complete data filename control
            params[name] = Param(
                val, valType='code', allowedTypes=[],
                hint=_translate("Name of the folder in which to save data"
                                " and log files (blank defaults to the "
                                "builder pref)"),
                categ='Data')
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
            else:
                if name in params:
                    params[name].val = val
                else:
                    # we found an unknown parameter (probably from the future)
                    params[name] = Param(
                        val, valType=paramNode.get('valType'),
                        allowedTypes=[],
                        hint=_translate(
                            "This parameter is not known by this version "
                            "of PsychoPy. It might be worth upgrading"))
                    params[name].allowedTypes = paramNode.get('allowedTypes')
                    if params[name].allowedTypes is None:
                        params[name].allowedTypes = []
                    params[name].readOnly = True
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
        versionf = float(self.psychopyVersion.rsplit('.', 1)[0])
        if versionf < 1.63:
            msg = 'note: v%s was used to create %s ("%s")'
            vals = (self.psychopyVersion, filenameBase, root.tag)
            logging.warning(msg % vals)

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
        # get each routine node from the list of routines
        for routineNode in routinesNode:
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
                # HS's modification superceded Jan 2014, removing several
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
            elif elementNode.tag == "Routine":
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
        # if we succeeded then save current filename to self
        self.filename = filename

    def setExpName(self, name):
        self.settings.params['expName'].val = name

    def getExpName(self):
        return self.settings.params['expName'].val

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

    def getComponentFromType(self, type):
        """Searches all the Routines in the Experiment for a matching component type

        :param name: str type of a component e.g., 'KeyBoard'
        :return: True if component exists in experiment
        """
        for routine in self.routines.values():
            exists = routine.getComponentFromType(type)
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
            thisFile = {}
            if len(filePath) > 2 and (filePath[0] == "/" or filePath[1] == ":"):
                thisFile['abs'] = filePath
                thisFile['rel'] = os.path.relpath(filePath, srcRoot)
            else:
                thisFile['rel'] = filePath
                thisFile['abs'] = os.path.normpath(join(srcRoot, filePath))
            if os.path.isfile(thisFile['abs']):
                return thisFile
            else:
                return None

        def findPathsInFile(filePath):
            """Recursively search a conditions file (xlsx or csv)
             extracting valid file paths in any param/cond

            :param filePath: str to a potential file path (rel or abs)
            :return: list of dicts{'rel','abs'} of valid file paths
            """

            # Clean up filePath that cannot be eval'd
            if '$' in filePath:
                try:
                    filePath = filePath.strip('$')
                    filePath = eval(filePath)
                except NameError:
                    # List files in director and get condition files
                    if 'xlsx' in filePath or 'xls' in filePath or 'csv' in filePath:
                        # Get all xlsx and csv files
                        expPath = self.expPath
                        if 'html' in self.expPath:  # Get resources from parent directory i.e, original exp path
                            expPath = self.expPath.split('html')[0]
                        fileList = (
                        [getPaths(condFile) for condFile in os.listdir(expPath)
                         if len(condFile.split('.')) > 1
                         and condFile.split('.')[1] in ['xlsx', 'xls', 'csv']])
                        return fileList
            paths = []
            # does it look at all like an excel file?
            if (not isinstance(filePath, basestring)
                    or not os.path.splitext(filePath)[1] in ['.csv', '.xlsx',
                                                             '.xls']):
                return paths
            thisFile = getPaths(filePath)
            # does it exist?
            if not thisFile:
                return paths
            # this file itself is valid so add to resources if not already
            if thisFile not in paths:
                paths.append(thisFile)
            conds = data.importConditions(thisFile['abs'])  # load the abs path
            for thisCond in conds:  # thisCond is a dict
                for param, val in list(thisCond.items()):
                    if isinstance(val, basestring) and len(val):
                        subFile = getPaths(val)
                    else:
                        subFile = None
                    if subFile:
                        paths.append(subFile)
                        # if it's a possible conditions file then recursive
                        if thisFile['abs'][-4:] in ["xlsx", ".xls", ".csv"]:
                            contained = findPathsInFile(subFile['abs'])
                            paths.extend(contained)
            return paths

        resources = []
        for thisEntry in self.flow:
            if thisEntry.getType() == 'LoopInitiator':
                # find all loops and check for conditions filename
                params = thisEntry.loop.params
                if 'conditionsFile' in params:
                    condsPaths = findPathsInFile(params['conditionsFile'].val)
                    resources.extend(condsPaths)
            elif thisEntry.getType() == 'Routine':
                # find all params of all compons and check if valid filename
                for thisComp in thisEntry:
                    for paramName in thisComp.params:
                        thisParam = thisComp.params[paramName]
                        thisFile = ''
                        if isinstance(thisParam, basestring):
                            thisFile = getPaths(thisParam)
                        elif isinstance(thisParam.val, basestring):
                            thisFile = getPaths(thisParam.val)
                        # then check if it's a valid path
                        if thisFile:
                            resources.append(thisFile)

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
        list.__init__(self, components)

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
