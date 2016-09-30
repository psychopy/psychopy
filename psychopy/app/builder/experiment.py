# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
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

import re
import os
import xml.etree.ElementTree as xml
from xml.dom import minidom
import StringIO
import codecs
import keyword

from .components import getInitVals, getComponents, getAllComponents
import psychopy
from psychopy import data, __version__, logging, constants
from psychopy.constants import FOREVER

from ..localization import _translate
import locale

# predefine some regex's; deepcopy complains if do in NameSpace.__init__()
_unescapedDollarSign_re = re.compile(r"^\$|[^\\]\$")  # detect "code wanted"
_valid_var_re = re.compile(r"^[a-zA-Z_][\w]*$")  # filter for legal var names
_nonalphanumeric_re = re.compile(r'\W')  # will match all bad var name chars

# used when writing scripts and in namespace:
_numpyImports = ['sin', 'cos', 'tan', 'log', 'log10', 'pi', 'average',
                 'sqrt', 'std', 'deg2rad', 'rad2deg', 'linspace', 'asarray']
_numpyRandomImports = ['random', 'randint', 'normal', 'shuffle']

# _localized separates internal (functional) from displayed strings:
# expose to poedit autodiscovery:
_localized = {
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
    'switchMethod': _translate('switchMethod')}
#_localized = {k: _translate(k) for k in _loKeys}  # hides string from poedit


class CodeGenerationException(Exception):
    """
    Exception thrown by a component when it is unable to generate its code.
    """

    def __init__(self, source, message=""):
        super(CodeGenerationException, self).__init__()
        self.source = source
        self.message = str(message)

    def __str__(self):
        return str(self.source) + ": " + self.message


class IndentingBuffer(StringIO.StringIO):

    def __init__(self, *args, **kwargs):
        StringIO.StringIO.__init__(self, *args, **kwargs)
        self.oneIndent = "    "
        self.indentLevel = 0

    def writeIndented(self, text):
        """Write to the StringIO buffer, but add the current indent.
        Use write() if you don't want the indent.

        To test if the prev character was a newline use::
            self.getvalue()[-1]=='\n'

        """
        self.write(self.oneIndent * self.indentLevel + text)

    def writeIndentedLines(self, text):
        """As writeIndented(text) except that each line in text gets
        the indent level rather than the first line only.
        """
        for line in text.splitlines():
            self.write(self.oneIndent * self.indentLevel + line + '\n')

    def setIndentLevel(self, newLevel, relative=False):
        """Change the indent level for the buffer to a new value.

        Set relative to True to increment or decrement the current value.
        """
        if relative:
            self.indentLevel += newLevel
        else:
            self.indentLevel = newLevel


class Experiment(object):
    """
    An experiment contains a single Flow and at least one
    Routine. The Flow controls how Routines are organised
    e.g. the nature of repeats and branching of an experiment.
    """

    def __init__(self, prefs=None):
        super(Experiment, self).__init__()
        self.name = ''
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
        self.psychopyLibs = ['gui', 'visual', 'core',
                             'data', 'event', 'logging', 'sound']
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
        """
        if not isinstance(libs, list):
            libs = list(libs)
        for lib in libs:
            if lib not in self.psychopyLibs:
                self.psychopyLibs.append(lib)

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

    def writeScript(self, expPath=None, target="PsychoPy"):
        """Write a PsychoPy script for the experiment
        """
        self.flow._prescreenValues()
        self.expPath = expPath
        script = IndentingBuffer(u'')  # a string buffer object

        # get date info, in format preferred by current locale as set by app:
        if hasattr(locale, 'nl_langinfo'):
            fmt = locale.nl_langinfo(locale.D_T_FMT)
            localDateTime = data.getDateStr(format=fmt)
        else:
            localDateTime = data.getDateStr(format="%B %d, %Y, at %H:%M")

        if target == "PsychoPy":
            self.settings.writeInitCode(script,
                                        self.psychopyVersion, localDateTime)
            self.settings.writeStartCode(script)  # present info, make logfile
            # writes any components with a writeStartCode()
            self.flow.writeStartCode(script)
            self.settings.writeWindowCode(script)  # create our visual.Window()
            # write the rest of the code for the components
            self.flow.writeBody(script)
            self.settings.writeEndCode(script)  # close log file

        elif target == "PsychoJS":
            script.oneIndent = "  "  # use 2 spaces rather than python 4
            self.settings.writeInitCodeJS(script,
                                          self.psychopyVersion, localDateTime)
            self.settings.writeWindowCodeJS(script)
            self.flow.writeResourcesCodeJS(script)
            self.flow.writeBodyJS(script)  # includes compon init and run code

            self.settings.writeEndCodeJS(script)

        return script

    def saveToXML(self, filename):
        # create the dom object
        self.xmlRoot = xml.Element("PsychoPy2experiment")
        self.xmlRoot.set('version', __version__)
        self.xmlRoot.set('encoding', 'utf-8')
        # store settings
        settingsNode = xml.SubElement(self.xmlRoot, 'Settings')
        for name, setting in self.settings.params.iteritems():
            settingNode = self._setXMLparam(
                parent=settingsNode, param=setting, name=name)
        # store routines
        routinesNode = xml.SubElement(self.xmlRoot, 'Routines')
        # routines is a dict of routines
        for routineName, routine in self.routines.iteritems():
            routineNode = self._setXMLparam(
                parent=routinesNode, param=routine, name=routineName)
            # a routine is based on a list of components
            for component in routine:
                componentNode = self._setXMLparam(
                    parent=routineNode, param=component,
                    name=component.params['name'].val)
                for name, param in component.params.iteritems():
                    paramNode = self._setXMLparam(
                        parent=componentNode, param=param, name=name)
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
                for paramName, param in loop.params.iteritems():
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
        f = codecs.open(filename, 'wb', 'utf-8')
        f.write(pretty)
        f.close()
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
            thisChild.set('val', unicode(param.val).replace("\n", "&#10;"))
        if hasattr(param, 'valType'):
            thisChild.set('valType', param.valType)
        if hasattr(param, 'updates'):
            thisChild.set('updates', unicode(param.updates))
        return thisChild

    def _getXMLparam(self, params, paramNode):
        """params is the dict of params of the builder component
        (e.g. stimulus) into which the parameters will be inserted
        (so the object to store the params should be created first)
        paramNode is the parameter node fetched from the xml file
        """
        name = paramNode.get('name')
        valType = paramNode.get('valType')
        val = paramNode.get('val')
        if not name == 'advancedParams':
            val = val.replace("&#10;", "\n")
        if name == 'storeResponseTime':
            return  # deprecated in v1.70.00 because it was redundant
        elif name == 'startTime':  # deprecated in v1.70.00
            params['startType'].val = unicode('time (s)')
            params['startVal'].val = unicode(val)
            return  # times doesn't need to update its type or 'updates' rule
        elif name == 'forceEndTrial':  # deprecated in v1.70.00
            params['forceEndRoutine'].val = bool(val)
            return  # forceEndTrial doesn't need to update type or 'updates'
        elif name == 'forceEndTrialOnPress':  # deprecated in v1.70.00
            params['forceEndRoutineOnPress'].val = bool(val)
            return  # forceEndTrial doesn't need to update  type or 'updates'
        elif name == 'trialList':  # deprecated in v1.70.00
            params['conditions'].val = eval(val)
            return  # forceEndTrial doesn't need to update  type or 'updates'
        elif name == 'trialListFile':  # deprecated in v1.70.00
            params['conditionsFile'].val = unicode(val)
            return  # forceEndTrial doesn't need to update  type or 'updates'
        elif name == 'duration':  # deprecated in v1.70.00
            params['stopType'].val = u'duration (s)'
            params['stopVal'].val = unicode(val)
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
            params['startType'].val = unicode('time (s)')
            params['startVal'].val = unicode(times[0])
            params['stopType'].val = unicode('time (s)')
            params['stopVal'].val = unicode(times[1])
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
        elif 'val' in paramNode.keys():
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
        if 'valType' in paramNode.keys():
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
        if 'updates' in paramNode.keys():
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
            self._getXMLparam(params=self.settings.params, paramNode=child)
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
                                      paramNode=paramNode)
                compGoodName = self.namespace.makeValid(
                    componentNode.get('name'))
                if compGoodName != componentNode.get('name'):
                    modifiedNames.append(componentNode.get('name'))
                self.namespace.add(compGoodName)
                component.params['name'].val = compGoodName
                routine.append(component)
        # for each component that uses a Static for updates, we need to set
        # that
        for thisRoutine in self.routines.values():
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
                            self.routines[routine].getComponentFromName(static).addComponentUpdate(
                                routine, thisComp.params['name'], thisParamName)
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
                        param.val = eval('%s' % (param.val))
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
                                 "may need to re-insert it"
                                 .format(elementNode.get('name')))
                    logging.flush()

        if modifiedNames:
            msg = 'duplicate variable name(s) changed in loadFromXML: %s\n'
            logging.warning(msg % ', '.join(list(set(modifiedNames))))
        if duplicateNames:
            msg = 'duplicate variable names: %s'
            logging.warning(msg % ', '.join(list(set(duplicateNames))))

    def setExpName(self, name):
        self.settings.params['expName'].val = name

    def getExpName(self):
        return self.settings.params['expName'].val


class Param(object):
    """Defines parameters for Experiment Components
    A string representation of the parameter will depend on the valType:

    >>> print(Param(val=[3,4], valType='num'))
    asarray([3, 4])
    >>> print(Param(val=3, valType='num')) # num converts int to float
    3.0
    >>> print(Param(val=3, valType='str') # str keeps as int, converts to code
    3
    >>> print(Param(val='3', valType='str')) # ... and keeps str as str
    '3'
    >>> print(Param(val=[3,4], valType='str')) # val is <type 'list'> -> code
    [3, 4]
    >>> print(Param(val='[3,4]', valType='str'))
    '[3,4]'
    >>> print(Param(val=[3,4], valType='code'))
    [3, 4]

    >>> #### auto str -> code:  at least one non-escaped '$' triggers
    >>> print(Param('[x,y]','str')) # str normally returns string
    '[x,y]'
    >>> print(Param('$[x,y]','str')) # code, as triggered by $
    [x,y]
    >>> print(Param('[$x,$y]','str')) # code, redundant $ ok, cleaned up
    [x,y]
    >>> print(Param('[$x,y]','str')) # code, a $ anywhere means code
    [x,y]
    >>> print(Param('[x,y]$','str')) # ... even at the end
    [x,y]
    >>> print(Param('[x,\$y]','str')) # string, because the only $ is escaped
    '[x,$y]'
    >>> print(Param('[x,\ $y]','str')) # improper escape -> code
    [x,\ y]
    >>> print(Param('/$[x,y]','str')) # improper escape -> code
    /[x,y]
    >>> print(Param('[\$x,$y]','str')) # code, python syntax error
    [$x,y]
    >>> print(Param('["\$x",$y]','str') # ... python syntax ok
    ["$x",y]
    >>> print(Param("'$a'",'str')) # code, with the code being a string
    'a'
    >>> print(Param("'\$a'",'str')) # str, with the str containing a str
    "'$a'"
    >>> print(Param('$$$$$myPathologicalVa$$$$$rName','str'))
    myPathologicalVarName
    >>> print(Param('\$$$$$myPathologicalVa$$$$$rName','str'))
    $myPathologicalVarName
    >>> print(Param('$$$$\$myPathologicalVa$$$$$rName','str'))
    $myPathologicalVarName
    >>> print(Param('$$$$\$$$myPathologicalVa$$$\$$$rName','str'))
    $myPathologicalVa$rName
    """

    def __init__(self, val, valType, allowedVals=None, allowedTypes=None,
                 hint="", label="", updates=None, allowedUpdates=None,
                 categ="Basic"):
        """
        @param val: the value for this parameter
        @type val: any
        @param valType: the type of this parameter ('num', 'str', 'code')
        @type valType: string
        @param allowedVals: possible vals for this param
            (e.g. units param can only be 'norm','pix',...)
        @type allowedVals: any
        @param allowedTypes: if other types are allowed then this is
            the possible types this parameter can have
            (e.g. rgb can be 'red' or [1,0,1])
        @type allowedTypes: list
        @param hint: describe this parameter for the user
        @type hint: string
        @param updates: how often does this parameter update
            ('experiment', 'routine', 'set every frame')
        @type updates: string
        @param allowedUpdates: conceivable updates for this param
            [None, 'routine', 'set every frame']
        @type allowedUpdates: list
        @param categ: category for this parameter
            will populate tabs in Component Dlg
        @type allowedUpdates: string
        """
        super(Param, self).__init__()
        self.label = label
        self.val = val
        self.valType = valType
        self.allowedTypes = allowedTypes or []
        self.hint = hint
        self.updates = updates
        self.allowedUpdates = allowedUpdates
        self.allowedVals = allowedVals or []
        self.staticUpdater = None
        self.categ = categ
        self.readOnly = False

    def __str__(self):
        if self.valType == 'num':
            try:
                # will work if it can be represented as a float
                return str(float(self.val))
            except Exception:  # might be an array
                return "asarray(%s)" % (self.val)
        elif self.valType == 'int':
            try:
                return "%i" % self.val  # int and float -> str(int)
            except TypeError:
                return unicode(self.val)  # try array of float instead?
        elif self.valType == 'str':
            # at least 1 non-escaped '$' anywhere --> code wanted
            # return str if code wanted
            # return repr if str wanted; this neatly handles "it's" and 'He
            # says "hello"'
            if type(self.val) in [str, unicode]:
                codeWanted = _unescapedDollarSign_re.search(self.val)
                if codeWanted:
                    return "%s" % getCodeFromParamStr(self.val)
                else:  # str wanted
                    # remove \ from all \$
                    return repr(re.sub(r"[\\]\$", '$', self.val))
            return repr(self.val)
        elif self.valType in ['code', 'extendedCode']:
            isStr = isinstance(self.val, basestring)
            if isStr and self.val.startswith("$"):
                # a $ in a code parameter is unecessary so remove it
                return "%s" % self.val[1:]
            elif isStr and self.val.startswith("\$"):
                # the user actually wanted just the $
                return "%s" % self.val[1:]
            elif isStr:
                return "%s" % self.val  # user actually wanted just the $
            else:  # if val was a tuple it needs converting to a string first
                return "%s" % repr(self.val)
        elif self.valType == 'bool':
            return "%s" % self.val
        else:
            raise TypeError("Can't represent a Param of type %s" %
                            self.valType)


class TrialHandler(object):
    """A looping experimental control object
            (e.g. generating a psychopy TrialHandler or StairHandler).
            """

    def __init__(self, exp, name, loopType='random', nReps=5,
                 conditions=(), conditionsFile='', endPoints=(0, 1),
                 randomSeed='', selectedRows='', isTrials=True):
        """
        @param name: name of the loop e.g. trials
        @type name: string
        @param loopType:
        @type loopType: string ('rand', 'seq')
        @param nReps: number of reps (for all conditions)
        @type nReps:int
        @param conditions: list of different trial conditions to be used
        @type conditions: list (of dicts?)
        @param conditionsFile: filename of the .csv file that
            contains conditions info
        @type conditions: string (filename)
        """
        super(TrialHandler, self).__init__()
        self.type = 'TrialHandler'
        self.exp = exp
        self.order = ['name']  # make name come first (others don't matter)
        self.params = {}
        self.params['name'] = Param(
            name, valType='code', updates=None, allowedUpdates=None,
            label=_localized['Name'],
            hint=_translate("Name of this loop"))
        self.params['nReps'] = Param(
            nReps, valType='code', updates=None, allowedUpdates=None,
            label=_localized['nReps'],
            hint=_translate("Number of repeats (for each condition)"))
        self.params['conditions'] = Param(
            list(conditions), valType='str',
            updates=None, allowedUpdates=None,
            label=_localized['conditions'],
            hint=_translate("A list of dictionaries describing the "
                            "parameters in each condition"))
        self.params['conditionsFile'] = Param(
            conditionsFile, valType='str', updates=None, allowedUpdates=None,
            label=_localized['conditions'],
            hint=_translate("Name of a file specifying the parameters for "
                            "each condition (.csv, .xlsx, or .pkl). Browse "
                            "to select a file. Right-click to preview file "
                            "contents, or create a new file."))
        self.params['endPoints'] = Param(
            list(endPoints), valType='num', updates=None, allowedUpdates=None,
            label=_localized['endPoints'],
            hint=_translate("The start and end of the loop (see flow "
                            "timeline)"))
        self.params['Selected rows'] = Param(
            selectedRows, valType='code',
            updates=None, allowedUpdates=None,
            label=_localized['Selected rows'],
            hint=_translate("Select just a subset of rows from your condition"
                            " file (the first is 0 not 1!). Examples: 0, "
                            "0:5, 5:-1"))
        # NB staircase is added for the sake of the loop properties dialog:
        self.params['loopType'] = Param(
            loopType, valType='str',
            allowedVals=['random', 'sequential', 'fullRandom',
                         'staircase', 'interleaved staircases'],
            label=_localized['loopType'],
            hint=_translate("How should the next condition value(s) be "
                            "chosen?"))
        self.params['random seed'] = Param(
            randomSeed, valType='code', updates=None, allowedUpdates=None,
            label=_localized['random seed'],
            hint=_translate("To have a fixed random sequence provide an "
                            "integer of your choosing here. Leave blank to "
                            "have a new random sequence on each run of the "
                            "experiment."))
        self.params['isTrials'] = Param(
            isTrials, valType='bool', updates=None, allowedUpdates=None,
            label=_localized["Is trials"],
            hint=_translate("Indicates that this loop generates TRIALS, "
                            "rather than BLOCKS of trials or stimuli within "
                            "a trial. It alters how data files are output"))

    def writeInitCode(self, buff):
        # no longer needed - initialise the trial handler just before it runs
        pass

    def writeResourcesCodeJS(self, buff):
        buff.writeIndented("resourceManager.addResource({});\n"
                           .format(self.params["conditionsFile"]))

    def writeLoopStartCode(self, buff):
        """Write the code to create and run a sequence of trials
        """
        # first create the handler init values
        inits = getInitVals(self.params)
        # import conditions from file?
        if self.params['conditionsFile'].val in ['None', None, 'none', '']:
            condsStr = "[None]"
        elif self.params['Selected rows'].val in ['None', None, 'none', '']:
            # just a conditions file with no sub-selection
            _con = "data.importConditions(%s)"
            condsStr = _con % self.params['conditionsFile']
        else:
            # a subset of a conditions file
            condsStr = ("data.importConditions(%(conditionsFile)s, selection="
                        "%(Selected rows)s)") % self.params
        # also a 'thisName' for use in "for thisTrial in trials:"
        makeLoopIndex = self.exp.namespace.makeLoopIndex
        self.thisName = makeLoopIndex(self.params['name'].val)
        # write the code
        code = ("\n# set up handler to look after randomisation of conditions etc\n"
                "%(name)s = data.TrialHandler(nReps=%(nReps)s, method=%(loopType)s, \n"
                "    extraInfo=expInfo, originPath=-1,\n")
        buff.writeIndentedLines(code % inits)
        # the next line needs to be kept separate to preserve potential string formatting 
        # by the user in condStr (i.e. it shouldn't be a formatted string itself
        code = "    trialList=" + condsStr + ",\n"  # conditions go here
        buff.writeIndented(code)
        code = "    seed=%(random seed)s, name='%(name)s')\n"
        buff.writeIndentedLines(code % inits)

        code = ("thisExp.addLoop(%(name)s)  # add the loop to the experiment\n" +
                self.thisName + " = %(name)s.trialList[0]  " +
                "# so we can initialise stimuli with some values\n")
        buff.writeIndentedLines(code % self.params)
        # unclutter the namespace
        if not self.exp.prefsBuilder['unclutteredNamespace']:
            code = ("# abbreviate parameter names if possible (e.g. rgb = %(name)s.rgb)\n"
                    "if %(name)s != None:\n"
                    "    for paramName in %(name)s.keys():\n"
                    "        exec(paramName + '= %(name)s.' + paramName)\n")
            buff.writeIndentedLines(code % {'name': self.thisName})

        # then run the trials loop
        code = "\nfor %s in %s:\n"
        buff.writeIndentedLines(code % (self.thisName, self.params['name']))
        # fetch parameter info from conditions
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("currentLoop = %s\n" % self.params['name'])
        # unclutter the namespace
        if not self.exp.prefsBuilder['unclutteredNamespace']:
            code = ("# abbreviate parameter names if possible (e.g. rgb = %(name)s.rgb)\n"
                    "if %(name)s != None:\n"
                    "    for paramName in %(name)s.keys():\n"
                    "        exec(paramName + '= %(name)s.' + paramName)\n")
            buff.writeIndentedLines(code % {'name': self.thisName})

    def writeLoopEndCode(self, buff):
        # Just within the loop advance data line if loop is whole trials
        if self.params['isTrials'].val == True:
            buff.writeIndentedLines("thisExp.nextEntry()\n\n")
        # end of the loop. dedent
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("# completed %s repeats of '%s'\n"
                           % (self.params['nReps'], self.params['name']))
        buff.writeIndented("\n")
        # save data
        if self.params['isTrials'].val == True:
            # a string to show all the available variables (if the conditions
            # isn't just None or [None])
            saveExcel = self.exp.settings.params['Save excel file'].val
            saveCSV = self.exp.settings.params['Save csv file'].val
            # get parameter names
            if saveExcel or saveCSV:
                code = ("# get names of stimulus parameters\n"
                        "if %(name)s.trialList in ([], [None], None):\n"
                        "    params = []\n"
                        "else:\n"
                        "    params = %(name)s.trialList[0].keys()\n")
                buff.writeIndentedLines(code % self.params)
            # write out each type of file
            if saveExcel or saveCSV:
                buff.writeIndented("# save data for this loop\n")
            if saveExcel:
                code = ("%(name)s.saveAsExcel(filename + '.xlsx', sheetName='%(name)s',\n"
                        "    stimOut=params,\n"
                        "    dataOut=['n','all_mean','all_std', 'all_raw'])\n")
                buff.writeIndentedLines(code % self.params)
            if saveCSV:
                code = ("%(name)s.saveAsText(filename + '%(name)s.csv', "
                        "delim=',',\n"
                        "    stimOut=params,\n"
                        "    dataOut=['n','all_mean','all_std', 'all_raw'])\n")
                buff.writeIndentedLines(code % self.params)

    def getType(self):
        return 'TrialHandler'


class StairHandler(object):
    """A staircase experimental control object.
    """

    def __init__(self, exp, name, nReps='50', startVal='', nReversals='',
                 nUp=1, nDown=3, minVal=0, maxVal=1,
                 stepSizes='[4,4,2,2,1]', stepType='db', endPoints=(0, 1),
                 isTrials=True):
        """
        @param name: name of the loop e.g. trials
        @type name: string
        @param nReps: number of reps (for all conditions)
        @type nReps:int
        """
        super(StairHandler, self).__init__()
        self.type = 'StairHandler'
        self.exp = exp
        self.order = ['name']  # make name come first (others don't matter)
        self.params = {}
        self.params['name'] = Param(
            name, valType='code',
            hint=_translate("Name of this loop"),
            label=_localized['Name'])
        self.params['nReps'] = Param(
            nReps, valType='code',
            label=_localized['nReps'],
            hint=_translate("(Minimum) number of trials in the staircase"))
        self.params['start value'] = Param(
            startVal, valType='code',
            label=_localized['start value'],
            hint=_translate("The initial value of the parameter"))
        self.params['max value'] = Param(
            maxVal, valType='code',
            label=_localized['max value'],
            hint=_translate("The maximum value the parameter can take"))
        self.params['min value'] = Param(
            minVal, valType='code',
            label=_localized['min value'],
            hint=_translate("The minimum value the parameter can take"))
        self.params['step sizes'] = Param(
            stepSizes, valType='code',
            label=_localized['step sizes'],
            hint=_translate("The size of the jump at each step (can change"
                            " on each 'reversal')"))
        self.params['step type'] = Param(
            stepType, valType='str', allowedVals=['lin', 'log', 'db'],
            label=_localized['step type'],
            hint=_translate("The units of the step size (e.g. 'linear' will"
                            " add/subtract that value each step, whereas "
                            "'log' will ad that many log units)"))
        self.params['N up'] = Param(
            nUp, valType='code',
            label=_localized['N up'],
            hint=_translate("The number of 'incorrect' answers before the "
                            "value goes up"))
        self.params['N down'] = Param(
            nDown, valType='code',
            label=_localized['N down'],
            hint=_translate("The number of 'correct' answers before the "
                            "value goes down"))
        self.params['N reversals'] = Param(
            nReversals, valType='code',
            label=_localized['N reversals'],
            hint=_translate("Minimum number of times the staircase must "
                            "change direction before ending"))
        # these two are really just for making the dialog easier (they won't
        # be used to generate code)
        self.params['loopType'] = Param(
            'staircase', valType='str',
            allowedVals=['random', 'sequential', 'fullRandom', 'staircase',
                         'interleaved staircases'],
            label=_localized['loopType'],
            hint=_translate("How should the next trial value(s) be chosen?"))
        # NB this is added for the sake of the loop properties dialog
        self.params['endPoints'] = Param(
            list(endPoints), valType='num',
            label=_localized['endPoints'],
            hint=_translate('Where to loop from and to (see values currently'
                            ' shown in the flow view)'))
        self.params['isTrials'] = Param(
            isTrials, valType='bool', updates=None, allowedUpdates=None,
            label=_localized["Is trials"],
            hint=_translate("Indicates that this loop generates TRIALS, "
                            "rather than BLOCKS of trials or stimuli within"
                            " a trial. It alters how data files are output"))

    def writeInitCode(self, buff):
        # not needed - initialise the staircase only when needed
        pass

    def writeResourcesCodeJS(self, buff):
        pass  # no resources needed for staircase

    def writeLoopStartCode(self, buff):
        # create the staircase
        # also a 'thisName' for use in "for thisTrial in trials:"
        makeLoopIndex = self.exp.namespace.makeLoopIndex
        self.thisName = makeLoopIndex(self.params['name'].val)
        if self.params['N reversals'].val in ("", None, 'None'):
            self.params['N reversals'].val = '0'
        # write the code
        code = ('\n# --------Prepare to start Staircase "%(name)s" --------\n'
                "# set up handler to look after next chosen value etc\n"
                "%(name)s = data.StairHandler(startVal=%(start value)s, extraInfo=expInfo,\n"
                "    stepSizes=%(step sizes)s, stepType=%(step type)s,\n"
                "    nReversals=%(N reversals)s, nTrials=%(nReps)s, \n"
                "    nUp=%(N up)s, nDown=%(N down)s,\n"
                "    minVal=%(min value)s, maxVal=%(max value)s,\n"
                "    originPath=-1, name='%(name)s')\n"
                "thisExp.addLoop(%(name)s)  # add the loop to the experiment")
        buff.writeIndentedLines(code % self.params)
        code = "level = %s = %s  # initialise some vals\n"
        buff.writeIndented(code % (self.thisName, self.params['start value']))
        # then run the trials
        # work out a name for e.g. thisTrial in trials:
        code = "\nfor %s in %s:\n"
        buff.writeIndentedLines(code % (self.thisName, self.params['name']))
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("currentLoop = %s\n" % self.params['name'])
        buff.writeIndented("level = %s\n" % self.thisName)

    def writeLoopEndCode(self, buff):
        # Just within the loop advance data line if loop is whole trials
        if self.params['isTrials'].val == True:
            buff.writeIndentedLines("thisExp.nextEntry()\n\n")
        # end of the loop. dedent
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("# staircase completed\n")
        buff.writeIndented("\n")
        # save data
        if self.params['isTrials'].val == True:
            if self.exp.settings.params['Save excel file'].val:
                code = ("%(name)s.saveAsExcel(filename + '.xlsx',"
                        " sheetName='%(name)s')\n")
                buff.writeIndented(code % self.params)
            if self.exp.settings.params['Save csv file'].val:
                code = ("%(name)s.saveAsText(filename + "
                        "'%(name)s.csv', delim=',')\n")
                buff.writeIndented(code % self.params)

    def getType(self):
        return 'StairHandler'


class MultiStairHandler(object):
    """To handle multiple interleaved staircases
    """

    def __init__(self, exp, name, nReps='50', stairType='simple',
                 switchStairs='random',
                 conditions=(), conditionsFile='', endPoints=(0, 1),
                 isTrials=True):
        """
        @param name: name of the loop e.g. trials
        @type name: string
        @param nReps: number of reps (for all conditions)
        @type nReps:int
        """
        super(MultiStairHandler, self).__init__()
        self.type = 'MultiStairHandler'
        self.exp = exp
        self.order = ['name']  # make name come first
        self.params = {}
        self.params['name'] = Param(
            name, valType='code',
            label=_localized['Name'],
            hint=_translate("Name of this loop"))
        self.params['nReps'] = Param(
            nReps, valType='code',
            label=_localized['nReps'],
            hint=_translate("(Minimum) number of trials in *each* staircase"))
        self.params['stairType'] = Param(
            stairType, valType='str',
            allowedVals=['simple', 'QUEST', 'quest'],
            label=_localized['stairType'],
            hint=_translate("How to select the next staircase to run"))
        self.params['switchMethod'] = Param(
            switchStairs, valType='str',
            allowedVals=['random', 'sequential', 'fullRandom'],
            label=_localized['switchMethod'],
            hint=_translate("How to select the next staircase to run"))
        # these two are really just for making the dialog easier (they won't
        # be used to generate code)
        self.params['loopType'] = Param(
            'staircase', valType='str',
            allowedVals=['random', 'sequential', 'fullRandom', 'staircase',
                         'interleaved staircases'],
            label=_localized['loopType'],
            hint=_translate("How should the next trial value(s) be chosen?"))
        self.params['endPoints'] = Param(
            list(endPoints), valType='num',
            label=_localized['endPoints'],
            hint=_translate('Where to loop from and to (see values currently'
                            ' shown in the flow view)'))
        self.params['conditions'] = Param(
            list(conditions), valType='str', updates=None,
            allowedUpdates=None,
            label=_localized['conditions'],
            hint=_translate("A list of dictionaries describing the "
                            "differences between each staircase"))
        self.params['conditionsFile'] = Param(
            conditionsFile, valType='str', updates=None, allowedUpdates=None,
            label=_localized['conditions'],
            hint=_translate("An xlsx or csv file specifying the parameters "
                            "for each condition"))
        self.params['isTrials'] = Param(
            isTrials, valType='bool', updates=None, allowedUpdates=None,
            label=_localized["Is trials"],
            hint=_translate("Indicates that this loop generates TRIALS, "
                            "rather than BLOCKS of trials or stimuli within "
                            "a trial. It alters how data files are output"))
        pass  # don't initialise at start of exp, create when needed

    def writeResourcesCodeJS(self, buff):
        buff.writeIndented("resourceManager.addResource({});"
                           .format(self.params["conditionsFile"]))

    def writeLoopStartCode(self, buff):
        # create a 'thisName' for use in "for thisTrial in trials:"
        makeLoopIndex = self.exp.namespace.makeLoopIndex
        self.thisName = makeLoopIndex(self.params['name'].val)
        # create the MultistairHander
        code = ("\n# set up handler to look after randomisation of trials etc\n"
                "conditions = data.importConditions(%(conditionsFile)s)\n"
                "%(name)s = data.MultiStairHandler(stairType=%(stairType)s, "
                "name='%(name)s',\n"
                "    nTrials=%(nReps)s,\n"
                "    conditions=conditions,\n"
                "    originPath=-1)\n"
                "thisExp.addLoop(%(name)s)  # add the loop to the experiment\n"
                "# initialise values for first condition\n"
                "level = %(name)s._nextIntensity  # initialise some vals\n"
                "condition = %(name)s.currentStaircase.condition\n"
                # start the loop:
                "\nfor level, condition in %(name)s:\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("currentLoop = %(name)s\n" % (self.params))
        # uncluttered namespace
        if not self.exp.prefsBuilder['unclutteredNamespace']:
            code = ("# abbreviate parameter names if possible (e.g. "
                    "rgb=condition.rgb)\n"
                    "for paramName in condition.keys():\n"
                    "    exec(paramName + '= condition[paramName]')\n")
            buff.writeIndentedLines(code)

    def writeLoopEndCode(self, buff):
        # Just within the loop advance data line if loop is whole trials
        if self.params['isTrials'].val == True:
            buff.writeIndentedLines("thisExp.nextEntry()\n\n")
        # end of the loop. dedent
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("# all staircases completed\n")
        buff.writeIndented("\n")
        # save data
        if self.params['isTrials'].val == True:
            if self.exp.settings.params['Save excel file'].val:
                code = "%(name)s.saveAsExcel(filename + '.xlsx')\n"
                buff.writeIndented(code % self.params)
            if self.exp.settings.params['Save csv file'].val:
                code = ("%(name)s.saveAsText(filename + '%(name)s.csv', "
                        "delim=',')\n")
                buff.writeIndented(code % self.params)

    def getType(self):
        return 'MultiStairHandler'

    def writeInitCode(self, buff):
        # not needed - initialise the staircase only when needed
        pass


class LoopInitiator(object):
    """A simple class for inserting into the flow.
    This is created automatically when the loop is created"""

    def __init__(self, loop):
        super(LoopInitiator, self).__init__()
        self.loop = loop
        self.exp = loop.exp
        loop.initiator = self

    def writeResourcesCodeJS(self, buff):
        self.loop.writeResourcesCodeJS(buff)

    def writeInitCode(self, buff):
        self.loop.writeInitCode(buff)

    def writeMainCode(self, buff):
        self.loop.writeLoopStartCode(buff)
        # we are now the inner-most loop
        self.exp.flow._loopList.append(self.loop)

    def getType(self):
        return 'LoopInitiator'

    def writeExperimentEndCode(self, buff):  # not needed
        pass


class LoopTerminator(object):
    """A simple class for inserting into the flow.
    This is created automatically when the loop is created"""

    def __init__(self, loop):
        super(LoopTerminator, self).__init__()
        self.loop = loop
        self.exp = loop.exp
        loop.terminator = self

    def writeInitCode(self, buff):
        pass

    def writeResourcesCodeJS(self, buff):
        pass

    def writeMainCode(self, buff):
        self.loop.writeLoopEndCode(buff)
        # _loopList[-1] will now be the inner-most loop
        self.exp.flow._loopList.remove(self.loop)

    def getType(self):
        return 'LoopTerminator'

    def writeExperimentEndCode(self, buff):  # not needed
        pass


class Flow(list):
    """The flow of the experiment is a list of L{Routine}s, L{LoopInitiator}s
    and L{LoopTerminator}s, that will define the order in which events occur
    """

    def __init__(self, exp):
        list.__init__(self)
        self.exp = exp
        self._currentRoutine = None
        self._loopList = []  # will be used while we write the code

    def __repr__(self):
        return "psychopy.experiment.Flow(%s)" % (str(list(self)))

    def addLoop(self, loop, startPos, endPos):
        """Adds initiator and terminator objects for the loop
        into the Flow list"""
        self.insert(int(endPos), LoopTerminator(loop))
        self.insert(int(startPos), LoopInitiator(loop))
        self.exp.requirePsychopyLibs(['data'])  # needed for TrialHandlers etc

    def addRoutine(self, newRoutine, pos):
        """Adds the routine to the Flow list"""
        self.insert(int(pos), newRoutine)

    def removeComponent(self, component, id=None):
        """Removes a Loop, LoopTerminator or Routine from the flow

        For a Loop (or initiator or terminator) to be deleted we can simply
        remove the object using normal list syntax. For a Routine there may
        be more than one instance in the Flow, so either choose which one
        by specifying the id, or all instances will be removed (suitable if
        the Routine has been deleted).
        """
        if component.getType() in ['LoopInitiator', 'LoopTerminator']:
            component = component.loop  # and then continue to do the next
        handlers = ('StairHandler', 'TrialHandler', 'MultiStairHandler')
        if component.getType() in handlers:
            # we need to remove the loop's termination points
            toBeRemoved = []
            for comp in self:
                # bad to change the contents of self when looping through self
                if comp.getType() in ['LoopInitiator', 'LoopTerminator']:
                    if comp.loop == component:
                        # self.remove(comp) --> skips over loop terminator if
                        # its an empty loop
                        toBeRemoved.append(comp)
            for comp in toBeRemoved:
                self.remove(comp)
        elif component.getType() == 'Routine':
            if id is None:
                # a Routine may come up multiple times - remove them all
                # self.remove(component)  # cant do this - two empty routines
                # (with diff names) look the same to list comparison
                toBeRemoved = []
                for id, compInFlow in enumerate(self):
                    if (hasattr(compInFlow, 'name') and
                            component.name == compInFlow.name):
                        toBeRemoved.append(id)
                # need to delete from the end backwards or the order changes
                toBeRemoved.reverse()
                for id in toBeRemoved:
                    del self[id]
            else:
                # just delete the single entry we were given (e.g. from
                # right-click in GUI)
                del self[id]

    def _dubiousConstantUpdates(self, component):
        """Return a list of fields in component that are set to be constant
        but seem intended to be dynamic. Some code fields are constant, and
        some denoted as code by $ are constant.
        """
        warnings = []
        # treat expInfo as likely to be constant; also treat its keys as
        # constant because its handy to make a short-cut in code:
        # exec(key+'=expInfo[key]')
        expInfo = eval(self.exp.settings.params['Experiment info'].val)
        keywords = self.exp.namespace.nonUserBuilder[:]
        keywords.extend(['expInfo'] + expInfo.keys())
        reserved = set(keywords).difference({'random', 'rand'})
        for key in component.params:
            field = component.params[key]
            if (not hasattr(field, 'val') or
                    not isinstance(field.val, basestring)):
                continue  # continue == no problem, no warning
            if not (field.allowedUpdates and
                    isinstance(field.allowedUpdates, list) and
                    len(field.allowedUpdates) and
                    field.updates == 'constant'):
                continue
            # now have only non-empty, possibly-code, and 'constant' updating
            if field.valType == 'str':
                if not bool(_unescapedDollarSign_re.search(field.val)):
                    continue
                code = getCodeFromParamStr(field.val)
            elif field.valType == 'code':
                code = field.val
            else:
                continue
            # get var names in the code; no names == constant
            try:
                names = compile(code, '', 'eval').co_names
            except SyntaxError:
                continue
            # ignore reserved words:
            if not set(names).difference(reserved):
                continue
            warnings.append((field, key))
        return warnings or [(None, None)]

    def _prescreenValues(self):
        # pre-screen and warn about some conditions in component values:
        trailingWhitespace = []
        constWarnings = []
        for entry in self:
            # NB each entry is a routine or LoopInitiator/Terminator
            if not isinstance(entry, Routine):
                continue
            for component in entry:
                # detect and strip trailing whitespace (can cause problems):
                for key in component.params:
                    field = component.params[key]
                    if not hasattr(field, 'label'):
                        continue  # no problem, no warning
                    if (field.label.lower() == 'text' or
                            not field.valType in ('str', 'code')):
                        continue
                    if (isinstance(field.val, basestring) and
                            field.val != field.val.strip()):
                        trailingWhitespace.append(
                            (field.val, key, component, entry))
                        field.val = field.val.strip()
                # detect 'constant update' fields that seem intended to be
                # dynamic:
                for field, key in self._dubiousConstantUpdates(component):
                    if field:
                        constWarnings.append(
                            (field.val, key, component, entry))
        if trailingWhitespace:
            warnings = []
            msg = '"%s", in Routine %s (%s: %s)'
            for field, key, component, routine in trailingWhitespace:
                vals = (field, routine.params['name'],
                        component.params['name'], key.capitalize())
                warnings.append(msg % vals)
            print('Note: Trailing white-space removed:\n ', end='')
            # non-redundant, order unknown
            print('\n  '.join(list(set(warnings))))
        if constWarnings:
            warnings = []
            msg = '"%s", in Routine %s (%s: %s)'
            for field, key, component, routine in constWarnings:
                vals = (field, routine.params['name'],
                        component.params['name'], key.capitalize())
                warnings.append(msg % vals)
            print('Note: Dynamic code seems intended but updating '
                  'is "constant":\n ', end='')
            # non-redundant, order unknown
            print('\n  '.join(list(set(warnings))))

    def writeStartCode(self, script):
        """Write the code that comes before the Window is created
        """
        script.writeIndentedLines("\n# Start Code - component code to be "
                                  "run before the window creation\n")
        for entry in self:
            # NB each entry is a routine or LoopInitiator/Terminator
            self._currentRoutine = entry
            # very few components need writeStartCode:
            if hasattr(entry, 'writeStartCode'):
                entry.writeStartCode(script)

    def writeResourcesCodeJS(self, script):
        """For JS we need to create a function to fetch all resources needed
        by each loop
        """
        startResources = """\nfunction setupResources() {{"""
        script.writeIndentedLines(startResources.format())
        script.setIndentLevel(1, relative=True)
        # ask each Routine/Loop to insert what it needs
        for entry in self:
            entry.writeResourcesCodeJS(script)
        #
        endResources = ("// then add that scheduler to the resource manager\n"
                        "resourceManager.scheduleResources(resourceScheduler);\n"
                        "return NEXT;")
        script.writeIndentedLines(endResources)
        script.setIndentLevel(-1, relative=True)
        script.writeIndentedLines("}\n")

    def writeBody(self, script):
        """Write the rest of the code
        """
        # writeStartCode and writeInitCode:
        for entry in self:
            # NB each entry is a routine or LoopInitiator/Terminator
            self._currentRoutine = entry
            entry.writeInitCode(script)
        # create clocks (after initialising stimuli)
        code = ("\n# Create some handy timers\n"
                "globalClock = core.Clock()  # to track the "
                "time since experiment started\n"
                "routineTimer = core.CountdownTimer()  # to "
                "track time remaining of each (non-slip) routine \n")
        script.writeIndentedLines(code)
        # run-time code
        for entry in self:
            self._currentRoutine = entry
            entry.writeMainCode(script)
        # tear-down code (very few components need this)
        for entry in self:
            self._currentRoutine = entry
            entry.writeExperimentEndCode(script)

    def writeBodyJS(self, script):
        """Initialise each component and then write the per-frame code too
        """
        # initialise the components for all Routines in a single function
        script.writeIndentedLines("\nfunction experimentInit() {")
        script.setIndentLevel(1, relative=True)
        code = ("// Initialize resource loading component\n"
                "resourceManagerClock = new core.Clock();\n"
                "resourceManager = new io.ResourceManager("
                " {win:win, target:'OSF', projectName:'stroop', "
                " projectContributor:'Alain Pitiot', projectStatus:'PUBLIC',"
                " clock:resourceManagerClock});\n")
        script.writeIndentedLines(code)

        # routine init sections
        for entry in self:
            # NB each entry is a routine or LoopInitiator/Terminator
            self._currentRoutine = entry
            if hasattr(entry, 'writeInitCodeJS'):
                entry.writeInitCodeJS(script)

        # create globalClock etc
        code = ("\n// Create some handy timers\n"
                "globalClock = new core.Clock();"
                "  // to track the time since experiment started\n"
                "routineTimer = new core.CountdownTimer();"
                "  // to track time remaining of each (non-slip) routine\n"
                "\nreturn NEXT;"
                )
        script.writeIndentedLines(code)
        script.setIndentLevel(-1, relative=True)
        script.writeIndentedLines("}")

        # then for each Routine write the Begin, EachFrame and End functions
        for thisRoutine in self:
            if hasattr(thisRoutine, 'writeMainCodeJS'):
                thisRoutine.writeMainCodeJS(script)
        for thisRoutine in self:
            if hasattr(thisRoutine, 'writeEndCodeJS'):
                thisRoutine.writeEndCodeJS(script)


class Routine(list):
    """
    A Routine determines a single sequence of events, such
    as the presentation of trial. Multiple Routines might be
    used to comprise an Experiment (e.g. one for presenting
    instructions, one for trials, one for debriefing subjects).

    In practice a Routine is simply a python list of Components,
    each of which knows when it starts and stops.
    """

    def __init__(self, name, exp, components=()):
        super(Routine, self).__init__()
        self.params = {'name': name}
        self.name = name
        self.exp = exp
        self._clockName = None  # for scripts e.g. "t = trialClock.GetTime()"
        self.type = 'Routine'
        list.__init__(self, list(components))

    def __repr__(self):
        _rep = "psychopy.experiment.Routine(name='%s', exp=%s, components=%s)"
        return _rep % (self.name, self.exp, str(list(self)))

    @property
    def name(self):
        return self.params['name']
    @name.setter
    def name(self, name):
        self.params['name'] = name

    def addComponent(self, component):
        """Add a component to the end of the routine"""
        self.append(component)

    def removeComponent(self, component):
        """Remove a component from the end of the routine"""
        name = component.params['name']
        self.remove(component)
        # check if the component was using any Static Components for updates
        for thisParamName, thisParam in component.params.items():
            if (hasattr(thisParam, 'updates') and
                    thisParam.updates and
                    'during:' in thisParam.updates):
                # remove the part that says 'during'
                updates = thisParam.updates.split(': ')[1]
                routine, static = updates.split('.')
                comp = self.exp.routines[routine].getComponentFromName(static)
                comp.remComponentUpdate(routine, name, thisParamName)

    def getStatics(self):
        """Return a list of Static components
        """
        statics = []
        for comp in self:
            if comp.type == 'Static':
                statics.append(comp)
        return statics

    def writeStartCode(self, buff):
        """This is start of the *experiment* (before window is created)
        """
        # few components will have this
        for thisCompon in self:
            # check just in case; try to ensure backwards compatibility _base
            if hasattr(thisCompon, 'writeStartCode'):
                thisCompon.writeStartCode(buff)

    def writeStartCodeJS(self, buff):
        """This is start of the *experiment*
        """
        # few components will have this
        for thisCompon in self:
            # check just in case; try to ensure backwards compatibility _base
            if hasattr(thisCompon, 'writeStartCodeJS'):
                thisCompon.writeStartCodeJS(buff)

    def writeInitCode(self, buff):
        code = '\n# Initialize components for Routine "%s"\n'
        buff.writeIndentedLines(code % self.name)
        self._clockName = self.name + "Clock"
        buff.writeIndented('%s = core.Clock()\n' % self._clockName)
        for thisCompon in self:
            thisCompon.writeInitCode(buff)

    def writeInitCodeJS(self, buff):
        code = '\n// Initialize components for Routine "%s"\n'
        buff.writeIndentedLines(code % self.name)
        self._clockName = self.name + "Clock"
        buff.writeIndented('%s = new core.Clock();\n' % self._clockName)
        for thisCompon in self:
            if hasattr(thisCompon, 'writeInitCodeJS'):
                thisCompon.writeInitCodeJS(buff)

    def writeResourcesCodeJS(self, buff):
        buff.writeIndented("// <<maybe need to load images for {}?>>\n"
                           .format(self.name))

    def writeMainCode(self, buff):
        """This defines the code for the frames of a single routine
        """
        # create the frame loop for this routine
        code = ('\n# ------Prepare to start Routine "%s"-------\n'
                't = 0\n'
                '%s.reset()  # clock\n'
                'frameN = -1\n'
                'continueRoutine = True\n')
        buff.writeIndentedLines(code % (self.name, self._clockName))
        # can we use non-slip timing?
        maxTime, useNonSlip = self.getMaxTime()
        if useNonSlip:
            buff.writeIndented('routineTimer.add(%f)\n' % (maxTime))

        code = "# update component parameters for each repeat\n"
        buff.writeIndentedLines(code)
        # This is the beginning of the routine, before the loop starts
        for event in self:
            event.writeRoutineStartCode(buff)

        code = '# keep track of which components have finished\n'
        buff.writeIndentedLines(code)
        compStr = ', '.join([c.params['name'].val for c in self
                             if 'startType' in c.params])
        buff.writeIndented('%sComponents = [%s]\n' % (self.name, compStr))
        code = ("for thisComponent in %sComponents:\n"
                "    if hasattr(thisComponent, 'status'):\n"
                "        thisComponent.status = NOT_STARTED\n"
                '\n# -------Start Routine "%s"-------\n')
        buff.writeIndentedLines(code % (self.name, self.name))
        if useNonSlip:
            code = 'while continueRoutine and routineTimer.getTime() > 0:\n'
        else:
            code = 'while continueRoutine:\n'
        buff.writeIndented(code)

        buff.setIndentLevel(1, True)
        # on each frame
        code = ('# get current time\n'
                't = %s.getTime()\n'
                'frameN = frameN + 1  # number of completed frames '
                '(so 0 is the first frame)\n')
        buff.writeIndentedLines(code % self._clockName)

        # write the code for each component during frame
        buff.writeIndentedLines('# update/draw components on each frame\n')
        # just 'normal' components
        for event in self:
            if event.type == 'Static':
                continue  # we'll do those later
            event.writeFrameCode(buff)
        # update static component code last
        for event in self.getStatics():
            event.writeFrameCode(buff)

        # are we done yet?
        code = (
            '\n# check if all components have finished\n'
            'if not continueRoutine:  # a component has requested a '
            'forced-end of Routine\n'
            '    break\n'
            'continueRoutine = False  # will revert to True if at least '
            'one component still running\n'
            'for thisComponent in %sComponents:\n'
            '    if hasattr(thisComponent, "status") and '
            'thisComponent.status != FINISHED:\n'
            '        continueRoutine = True\n'
            '        break  # at least one component has not yet finished\n')
        buff.writeIndentedLines(code % self.name)

        # allow subject to quit via Esc key?
        if self.exp.settings.params['Enable Escape'].val:
            code = ('\n# check for quit (the Esc key)\n'
                    'if endExpNow or event.getKeys(keyList=["escape"]):\n'
                    '    core.quit()\n')
            buff.writeIndentedLines(code)
        # update screen
        code = ('\n# refresh the screen\n'
                "if continueRoutine:  # don't flip if this routine is over "
                "or we'll get a blank screen\n"
                '    win.flip()\n')
        buff.writeIndentedLines(code)

        # that's done decrement indent to end loop
        buff.setIndentLevel(-1, True)

        # write the code for each component for the end of the routine
        code = ('\n# -------Ending Routine "%s"-------\n'
                'for thisComponent in %sComponents:\n'
                '    if hasattr(thisComponent, "setAutoDraw"):\n'
                '        thisComponent.setAutoDraw(False)\n')
        buff.writeIndentedLines(code % (self.name, self.name))
        for event in self:
            event.writeRoutineEndCode(buff)

        # reset routineTimer at the *very end* of all non-nonSlip routines
        if not useNonSlip:
            code = ('# the Routine "%s" was not non-slip safe, so reset '
                    'the non-slip timer\n'
                    'routineTimer.reset()\n')
            buff.writeIndentedLines(code % self.name)


    def writeMainCodeJS(self, buff):
        """This defines the code for the frames of a single routine
        """

        # create the frame loop for this routine
        code = ("\n"
                "function {0}Begin() {{\n")
        buff.writeIndentedLines(code.format(self.name))
        buff.setIndentLevel(1, relative=True)
        code = ("//------Prepare to start Routine '{0}'-------\n"
                "t = 0;\n"
                "{0}Clock.reset(); // clock\n"
                "frameN = -1;\n"
                )
        # can we use non-slip timing?
        maxTime, useNonSlip = self.getMaxTime()
        if useNonSlip:
            buff.writeIndented('routineTimer.add(%f)\n' % (maxTime))

        code = "// update component parameters for each repeat\n"
        buff.writeIndentedLines(code)
        # This is the beginning of the routine, before the loop starts
        for thisCompon in self:
            if "PsychoJS" in thisCompon.targets:
                thisCompon.writeRoutineStartCodeJS(buff)

        code = ("// keep track of which components have finished\n"
                "{0}Components = [];\n").format(self.name)
        buff.writeIndentedLines(code)
        for thisCompon in self:
            if ('startType' in thisCompon.params
                    and "PsychoJS" in thisCompon.targets):
                code = "{}Components.push({});\n".format(
                    self.name, thisCompon.params['name'])
                buff.writeIndentedLines(code)
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines("}\n")

        # write code for each frame
        code = ("\n"
                "function {0}EachFrame() {{\n")
        buff.writeIndentedLines(code.format(self.name))
        buff.setIndentLevel(1, relative=True)
        code = ("//------Loop for each frame of Routine '{0}'-------\n"
                "continueRoutine = true;\n // until we're told otherwise"
                "\n// get current time\n"
                "t = {0}Clock.getTime();\n"
                "frameN = frameN + 1;"
                "// number of completed frames (so 0 is the first frame)\n"
                )
        buff.writeIndentedLines(code.format(self.name))
        # write the code for each component during frame
        buff.writeIndentedLines('// update/draw components on each frame\n')
        # just 'normal' components
        for comp in self:
            if ("PsychoJS" in comp.targets and comp.type != 'Static'):
                comp.writeFrameCodeJS(buff)
        # update static component code last
        for comp in self.getStatics():
            if "PsychoJS" in comp.targets:
                comp.writeFrameCodeJS(buff)

        # are we done yet?
        code = ("\n// check if the Routine should terminate\n"
                "if (!continueRoutine) {{"
                "  // a component has requested a forced-end of Routine\n"
                "  return NEXT;\n"
                "}}\n"
                "continueRoutine = false;"
                "// reverts to True if at least one component still running\n"
                "for(var i = 0; i < {0}Components.length; ++i) {{\n"
                "  thisComponent = {0}Components[i];\n"
                "  if ('status' in thisComponent && thisComponent.status != FINISHED) {{\n"
                "    continueRoutine = true;\n"
                "    break;\n"
                "  }}\n"
                "}}\n"
                "// check for quit (the Esc key)\n"
                "if (endExpNow || event.getKeys({{keyList:['escape']}}).length > 0) {{\n"
                "  core.quit();\n"
                "}}\n")
        buff.writeIndentedLines(code.format(self.name))

        buff.writeIndentedLines("\n// refresh the screen if continuing\n")
        if useNonSlip:
            buff.writeIndentedLines("if (continueRoutine "
                                    "&& routineTimer.getTime() > 0) {")
        else:
            buff.writeIndentedLines("if (continueRoutine) {")
        code = ("  return FLIP_REPEAT;\n"
                "}\n"
                "else {\n"
                "  return NEXT;\n"
                "}\n")
        buff.writeIndentedLines(code)

        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines("}\n")

        code = ("\n"
                "function {0}End() {{\n")
        buff.writeIndentedLines(code.format(self.name))
        buff.setIndentLevel(1, relative=True)

        code = ("//------Ending Routine '{0}'-------\n"
                "for (var i = 0; i < instructComponents.length; ++i) {{\n"
                '  if ("setAutoDraw" in thisComponent) {{\n'
                "    thisComponent.setAutoDraw(false);\n"
                '  }}\n'
                "}}\n")
        buff.writeIndentedLines(code.format(self.params['name']))
        # add the EndRoutine code for each component
        for compon in self:
            if "PsychoJS" in compon.targets:
                compon.writeRoutineEndCodeJS(buff)
#
#        # reset routineTimer at the *very end* of all non-nonSlip routines
#        if not useNonSlip:
#            code = ('# the Routine "%s" was not non-slip safe, so reset '
#                    'the non-slip timer\n'
#                    'routineTimer.reset()\n')
#            buff.writeIndentedLines(code % self.name)

        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines("}\n")

        # CURRENTLY HERE WORKING THROUGH ROUTINE MAIN CODE
#
#        # write the code for each component for the end of the routine
#        code = ('\n# -------Ending Routine "%s"-------\n'
#                'for thisComponent in %sComponents:\n'
#                '    if hasattr(thisComponent, "setAutoDraw"):\n'
#                '        thisComponent.setAutoDraw(False)\n')
#        buff.writeIndentedLines(code % (self.name, self.name))

#



    def writeExperimentEndCode(self, buff):
        """This defines the code for the frames of a single routine
        """
        # This is the beginning of the routine, before the loop starts
        for component in self:
            component.writeExperimentEndCode(buff)

    def getType(self):
        return 'Routine'

    def getComponentFromName(self, name):
        for comp in self:
            if comp.params['name'].val == name:
                return comp
        return None

    def hasOnlyStaticComp(self):
        return all([comp.type == 'Static' for comp in self])

    def getMaxTime(self):
        """What the last (predetermined) stimulus time to be presented. If
        there are no components or they have code-based times then will
        default to 10secs
        """
        maxTime = 0
        nonSlipSafe = True  # if possible
        for component in self:
            if 'startType' in component.params:
                start, duration, nonSlip = component.getStartAndDuration()
                if not nonSlip:
                    nonSlipSafe = False
                if duration == FOREVER:
                    # only the *start* of an unlimited event should contribute
                    # to maxTime
                    duration = 1  # plus some minimal duration so it's visible
                # now see if we have a end t value that beats the previous max
                try:
                    # will fail if either value is not defined:
                    thisT = start + duration
                except Exception:
                    thisT = 0
                maxTime = max(maxTime, thisT)
        if maxTime == 0:  # if there are no components
            maxTime = 10
            nonSlipSafe = False
        return maxTime, nonSlipSafe


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


class NameSpace(object):
    """class for managing variable names in builder-constructed experiments.

    The aim is to help detect and avoid name-space collisions from
    user-entered variable names.
    Track four groups of variables:
        numpy =    part of numpy or numpy.random
        psychopy = part of psychopy, such as event or data; include os here
        builder =  used internally by the builder when constructing an expt
        user =     used 'externally' by a user when programming an experiment
    Some vars, like core, are part of both psychopy and numpy, so the order of
    operations can matter

    Notes for development:
    are these all of the ways to get into the namespace?
    - import statements at top of file: numpy, psychopy, os, etc
    - a handful of things that always spring up automatically, like t and win
    - routines: user-entered var name = routine['name'].val, plus sundry
        helper vars, like theseKeys
    - flow elements: user-entered = flowElement['name'].val
    - routine & flow from either GUI or .psyexp file
    - each routine and flow element potentially has a ._clockName,
        loops have thisName, albeit thisNam (missing end character)
    - column headers in condition files
    - abbreviating parameter names (e.g. rgb=thisTrial.rgb)

    :Author:
        2011 Jeremy Gray
    """

    def __init__(self, exp):
        """Set-up an experiment's namespace: reserved words and user space
        """
        super(NameSpace, self).__init__()
        self.exp = exp
        # deepcopy fails if you pre-compile regular expressions and stash here

        self.numpy = _numpyImports + _numpyRandomImports + ['np']
        self.keywords = keyword.kwlist + dir(__builtins__)
        # these are based on a partial test, known to be incomplete:
        self.psychopy = psychopy.__all__ + ['psychopy', 'os'] + dir(constants)
        self.builder = ['KeyResponse', 'key_resp', 'buttons',
                        'continueRoutine', 'expInfo', 'expName', 'thisExp',
                        'filename', 'logFile', 'paramName',
                        't', 'frameN', 'currentLoop', 'dlg', '_thisDir',
                        'endExpNow',
                        'globalClock', 'routineTimer', 'frameDur',
                        'theseKeys', 'win', 'x', 'y', 'level', 'component',
                        'thisComponent']
        # user-entered, from Builder dialog or conditions file:
        self.user = []
        self.nonUserBuilder = self.numpy + self.keywords + self.psychopy

        # strings used as codes, separate function from display value:
        # need the actual strings to be inside _translate for poedit discovery
        self._localized = {
            None: '',
            "one of your Components, Routines, or condition parameters":
                _translate(
                    "one of your Components, Routines, or condition parameters"),
            " Avoid `this`, `these`, `continue`, `Clock`, or `component` in name":
                _translate(
                    " Avoid `this`, `these`, `continue`, `Clock`, or `component` in name"),
            "Builder variable": _translate("Builder variable"),
            "Psychopy module": _translate("Psychopy module"),
            "numpy function": _translate("numpy function"),
            "python keyword": _translate("python keyword")}

    def __str__(self, numpy_count_only=True):
        vars = self.user + self.builder + self.psychopy
        if numpy_count_only:
            return "%s + [%d numpy]" % (str(vars), len(self.numpy))
        else:
            return str(vars + self.numpy)

    def getDerived(self, basename):
        """ buggy
        idea: return variations on name, based on its type, to flag name that
        will come to exist at run-time;
        more specific than is_possibly-derivable()
        if basename is a routine, return continueBasename and basenameClock,
        if basename is a loop, return makeLoopIndex(name)
        """
        derived_names = []
        for flowElement in self.exp.flow:
            if flowElement.getType() in ('LoopInitiator', 'LoopTerminator'):
                flowElement = flowElement.loop  # we want the loop itself
                # basename can be <type 'instance'>
                derived_names += [self.makeLoopIndex(basename)]
            if (basename == str(flowElement.params['name']) and
                    basename + 'Clock' not in derived_names):
                derived_names += [basename + 'Clock',
                                  'continue' + basename.capitalize()]
        # other derived_names?
        #
        return derived_names

    def getCollisions(self):
        """return None, or a list of names in .user that are also in
        one of the other spaces
        """
        standard = set(self.builder + self.psychopy + self.numpy)
        duplicates = list(set(self.user).intersection(standard))
        su = sorted(self.user)
        duplicates += [var for i, var in enumerate(su)
                       if i < len(su) - 1 and su[i + 1] == var]
        return duplicates or None

    def isValid(self, name):
        """var-name compatible? return True if string name is
        alphanumeric + underscore only, with non-digit first
        """
        return bool(_valid_var_re.match(name))

    def isPossiblyDerivable(self, name):
        """catch all possible derived-names, regardless of whether currently
        """
        derivable = (name.startswith('this') or
                     name.startswith('these') or
                     name.startswith('continue') or
                     name.endswith('Clock') or
                     name.lower().find('component') > -1)
        if derivable:
            return (" Avoid `this`, `these`, `continue`, `Clock`,"
                    " or `component` in name")
        return None

    def exists(self, name):
        """returns None, or a message indicating where the name is in use.
        cannot guarantee that a name will be conflict-free.
        does not check whether the string is a valid variable name.

        >>> exists('t')
        Builder variable
        """
        try:
            name = str(name)  # convert from unicode if possible
        except Exception:
            pass

        # check getDerived:

        # check in this order: return a key from NameSpace._localized.keys(),
        # not a localized value
        if name in self.user:
            return "one of your Components, Routines, or condition parameters"
        if name in self.builder:
            return "Builder variable"
        if name in self.psychopy:
            return "Psychopy module"
        if name in self.numpy:
            return "numpy function"
        if name in self.keywords:
            return "python keyword"

        return  # None, meaning does not exist already

    def add(self, name, sublist='default'):
        """add name to namespace by appending a name or list of names to a
        sublist, eg, self.user
        """
        if name is None:
            return
        if sublist == 'default':
            sublist = self.user
        if not isinstance(name, list):
            sublist.append(name)
        else:
            sublist += name

    def remove(self, name, sublist='default'):
        """remove name from the specified sublist (and hence from the
        name-space), eg, self.user
        """
        if name is None:
            return
        if sublist == 'default':
            sublist = self.user
        if not isinstance(name, list):
            name = [name]
        for n in list(name):
            if n in sublist:
                del sublist[sublist.index(n)]

    def rename(self, name, newName, sublist='default'):
        if name is None:
            return
        if sublist == 'default':
            sublist = self.user
        if not isinstance(name, list):
            name = [name]
        for n in list(name):
            if n in sublist:
                sublist[sublist.index(n)] = newName

    def makeValid(self, name, prefix='var'):
        """given a string, return a valid and unique variable name.
        replace bad characters with underscore, add an integer suffix until
        its unique

        >>> makeValid('Z Z Z')
        'Z_Z_Z'
        >>> makeValid('a')
        'a'
        >>> makeValid('a')
        'a_2'
        >>> makeValid('123')
        'var_123'
        """

        # make it legal:
        try:
            # convert from unicode, flag as uni if can't convert
            name = str(name)
        except Exception:
            prefix = 'uni'
        if not name:
            name = prefix + '_1'
        if name[0].isdigit():
            name = prefix + '_' + name
        # replace all bad chars with _
        name = _nonalphanumeric_re.sub('_', name)

        # try to make it unique; success depends on accuracy of self.exists():
        i = 2  # skip _1: user can rename the first one to be _1 if desired
        # maybe it already has _\d+? if so, increment from there
        if self.exists(name) and '_' in name:
            basename, count = name.rsplit('_', 1)
            try:
                i = int(count) + 1
                name = basename
            except Exception:
                pass
        nameStem = name + '_'
        while self.exists(name):  # brute-force a unique name
            name = nameStem + str(i)
            i += 1
        return name

    def makeLoopIndex(self, name):
        """return a valid, readable loop-index name:
            'this' + (plural->singular).capitalize() [+ (_\d+)]
        """
        try:
            newName = str(name)
        except Exception:
            newName = name
        prefix = 'this'
        irregular = {'stimuli': 'stimulus',
                     'mice': 'mouse', 'people': 'person'}
        for plural, singular in irregular.items():
            nn = re.compile(plural, re.IGNORECASE)
            newName = nn.sub(singular, newName)
        if (newName.endswith('s') and
                not newName.lower() in irregular.values()):
            newName = newName[:-1]  # trim last 's'
        else:  # might end in s_2, so delete that s; leave S
            match = re.match(r"^(.*)s(_\d+)$", newName)
            if match:
                newName = match.group(1) + match.group(2)
        # retain CamelCase:
        newName = prefix + newName[0].capitalize() + newName[1:]
        newName = self.makeValid(newName)
        return newName


def getCodeFromParamStr(val):
    """Convert a Param.val string to its intended python code
    (as triggered by special char $)
    """
    tmp = re.sub(r"^(\$)+", '', val)  # remove leading $, if any
    # remove all nonescaped $, squash $$$$$
    tmp2 = re.sub(r"([^\\])(\$)+", r"\1", tmp)
    return re.sub(r"[\\]\$", '$', tmp2)  # remove \ from all \$
