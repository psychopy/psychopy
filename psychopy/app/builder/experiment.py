# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import StringIO, sys, codecs
from components import *#getComponents('') and getAllComponents([])
import psychopy
from psychopy import data, __version__, logging
from psychopy.constants import *
from lxml import etree
import numpy, numpy.random # want to query their name-spaces
import re, os
import locale

# predefine some regex's; deepcopy complains if do in NameSpace.__init__()
_unescapedDollarSign_re = re.compile(r"^\$|[^\\]\$")  # detect "code wanted"
_valid_var_re = re.compile(r"^[a-zA-Z_][\w]*$")  # filter for legal var names
_nonalphanumeric_re = re.compile(r'\W') # will match all bad var name chars

# used when writing scripts and in namespace:
_numpyImports = ['sin', 'cos', 'tan', 'log', 'log10', 'pi', 'average', 'sqrt', 'std',
                  'deg2rad', 'rad2deg', 'linspace', 'asarray']
_numpyRandomImports = ['random', 'randint', 'normal', 'shuffle']

"""
Exception thrown by a component when it is unable to generate its code.
"""
class CodeGenerationException(Exception):
    def __init__(self, source, message = ""):
        self.source = source
        self.message = str(message)

    def __str__(self):
        return str(self.source) + ": " + self.message


"""the code that writes out an actual experiment file is (in order):
    experiment.Experiment.writeScript() - starts things off, calls other parts
    settings.SettingsComponent.writeStartCode()
    experiment.Flow.writeCode()
        which will call .writeCode() bits from each component
    settings.SettingsComponent.writeEndCode()
"""

class IndentingBuffer(StringIO.StringIO):
    def __init__(self, *args, **kwargs):
        StringIO.StringIO.__init__(self, *args, **kwargs)
        self.oneIndent="    "
        self.indentLevel=0
    def writeIndented(self,text):
        """Write to the StringIO buffer, but add the current indent.
        Use write() if you don't want the indent.

        To test if the prev character was a newline use::
            self.getvalue()[-1]=='\n'

        """
        self.write(self.oneIndent*self.indentLevel + text)
    def writeIndentedLines(self,text):
        """As writeIndented(text) except that each line in text gets the indent level rather
        than the first line only.
        """
        for line in text.splitlines():
            self.write(self.oneIndent*self.indentLevel + line + '\n')
    def setIndentLevel(self, newLevel, relative=False):
        """Change the indent level for the buffer to a new value.

        Set relative to True if you want to increment or decrement the current value.
        """
        if relative:
            self.indentLevel+=newLevel
        else:
            self.indentLevel=newLevel

class Experiment:
    """
    An experiment contains a single Flow and at least one
    Routine. The Flow controls how Routines are organised
    e.g. the nature of repeats and branching of an experiment.
    """
    def __init__(self, prefs=None):
        self.name=''
        self.flow = Flow(exp=self)#every exp has exactly one flow
        self.routines={}
        #get prefs (from app if poss or from cfg files)
        if prefs==None:
            prefs = psychopy.prefs
        #deepCopy doesn't like the full prefs object to be stored, so store each subset
        self.prefsAppDataCfg=prefs.appDataCfg
        self.prefsGeneral=prefs.general
        self.prefsApp=prefs.app
        self.prefsCoder=prefs.coder
        self.prefsBuilder=prefs.builder
        self.prefsPaths=prefs.paths
        #this can be checked by the builder that this is an experiment and a compatible version
        self.psychopyVersion=__version__ #imported from components
        self.psychopyLibs=['visual','core','data','event','logging','sound']
        self.settings=getComponents(fetchIcons=False)['SettingsComponent'](parentName='', exp=self)
        self._doc=None#this will be the xml.dom.minidom.doc object for saving
        self.namespace = NameSpace(self) # manage variable names
    def requirePsychopyLibs(self, libs=[]):
        """Add a list of top-level psychopy libs that the experiment will need.
        e.g. [visual, event]
        """
        if type(libs)!=list:
            libs=list(libs)
        for lib in libs:
            if lib not in self.psychopyLibs:
                self.psychopyLibs.append(lib)
    def addRoutine(self,routineName, routine=None):
        """Add a Routine to the current list of them.

        Can take a Routine object directly or will create
        an empty one if none is given.
        """
        if routine==None:
            self.routines[routineName]=Routine(routineName, exp=self)#create a deafult routine with this name
        else:
            self.routines[routineName]=routine
    def writeScript(self, expPath=None):
        """Write a PsychoPy script for the experiment
        """
        self.flow._prescreenValues()
        self.expPath = expPath
        script = IndentingBuffer(u'') #a string buffer object

        #get date info, in format preferred by current locale as set by app:
        if hasattr(locale,'nl_langinfo'):
            localDateTime = data.getDateStr(format=locale.nl_langinfo(locale.D_T_FMT))
        else:
            localDateTime = data.getDateStr(format="%B %d, %Y, at %H:%M")

        script.write('#!/usr/bin/env python\n' +
                    '# -*- coding: utf-8 -*-\n' +
                    '"""\nThis experiment was created using PsychoPy2 Experiment Builder (v%s), %s\n' % (
                        self.psychopyVersion, localDateTime ) +
                    'If you publish work using this script please cite the relevant PsychoPy publications\n' +
                    '  Peirce, JW (2007) PsychoPy - Psychophysics software in Python. Journal of Neuroscience Methods, 162(1-2), 8-13.\n' +
                    '  Peirce, JW (2009) Generating stimuli for neuroscience using PsychoPy. Frontiers in Neuroinformatics, 2:10. doi: 10.3389/neuro.11.010.2008\n"""\n')
        script.write(
                    "\nfrom __future__ import division  # so that 1/3=0.333 instead of 1/3=0\n" +
                    "from psychopy import %s\n" % ', '.join(self.psychopyLibs) +
                    "from psychopy.constants import *  # things like STARTED, FINISHED\n" +
                    "import numpy as np  # whole numpy lib is available, prepend 'np.'\n" +
                    "from numpy import %s\n" % ', '.join(_numpyImports) +
                    "from numpy.random import %s\n" % ', '.join(_numpyRandomImports) +
                    "import os  # handy system and path functions\n")
        if self.prefsApp['locale']:
            # if locale is set explicitly as a pref, add it to the script:
            localeValue = '.'.join(locale.getlocale())
            script.write("import locale\n" +
                     "locale.setlocale(locale.LC_ALL, '%s')\n" % localeValue)
        script.write("\n")
        self.settings.writeStartCode(script) #present info dlg, make logfile
        self.flow.writeStartCode(script) #writes any components with a writeStartCode()
        self.settings.writeWindowCode(script)#create our visual.Window()
        self.flow.writeCode(script) #write the rest of the code for the components
        self.settings.writeEndCode(script) #close log file

        return script

    def saveToXML(self, filename):
        #create the dom object
        self.xmlRoot = etree.Element("PsychoPy2experiment")
        self.xmlRoot.set('version', __version__)
        self.xmlRoot.set('encoding', 'utf-8')
        #store settings
        settingsNode=etree.SubElement(self.xmlRoot, 'Settings')
        for name, setting in self.settings.params.iteritems():
            settingNode=self._setXMLparam(parent=settingsNode,param=setting,name=name)
        #store routines
        routinesNode=etree.SubElement(self.xmlRoot, 'Routines')
        for routineName, routine in self.routines.iteritems():#routines is a dict of routines
            routineNode = self._setXMLparam(parent=routinesNode,param=routine,name=routineName)
            for component in routine: #a routine is based on a list of components
                componentNode=self._setXMLparam(parent=routineNode,param=component,name=component.params['name'].val)
                for name, param in component.params.iteritems():
                    paramNode=self._setXMLparam(parent=componentNode,param=param,name=name)
        #implement flow
        flowNode=etree.SubElement(self.xmlRoot, 'Flow')
        for element in self.flow:#a list of elements(routines and loopInit/Terms)
            elementNode=etree.SubElement(flowNode, element.getType())
            if element.getType() == 'LoopInitiator':
                loop=element.loop
                name = loop.params['name'].val
                elementNode.set('loopType',loop.getType())
                elementNode.set('name', name)
                for paramName, param in loop.params.iteritems():
                    paramNode = self._setXMLparam(parent=elementNode,param=param,name=paramName)
                    if paramName=='conditions': #override val with repr(val)
                        paramNode.set('val',repr(param.val))
            elif element.getType() == 'LoopTerminator':
                elementNode.set('name', element.loop.params['name'].val)
            elif element.getType() == 'Routine':
                elementNode.set('name', '%s' %element.params['name'])
        #write to disk
        f=codecs.open(filename, 'wb', 'utf-8')
        f.write(etree.tostring(self.xmlRoot, encoding=unicode, pretty_print=True))
        f.close()
    def _getShortName(self, longName):
        return longName.replace('(','').replace(')','').replace(' ','')
    def _setXMLparam(self,parent,param,name):
        """Add a new child to a given xml node.
        name can include spaces and parens, which will be removed to create child name
        """
        if hasattr(param,'getType'):
            thisType = param.getType()
        else: thisType='Param'
        thisChild = etree.SubElement(parent,thisType)#creates and appends to parent
        thisChild.set('name',name)
        if hasattr(param,'val'): thisChild.set('val',unicode(param.val))
        if hasattr(param,'valType'): thisChild.set('valType',param.valType)
        if hasattr(param,'updates'): thisChild.set('updates',unicode(param.updates))
        return thisChild
    def _getXMLparam(self,params,paramNode):
        """params is the dict of params of the builder component (e.g. stimulus) into which
        the parameters will be inserted (so the object to store the params should be created first)
        paramNode is the parameter node fetched from the xml file
        """
        name=paramNode.get('name')
        valType = paramNode.get('valType')
        if name=='storeResponseTime':
            return#deprecated in v1.70.00 because it was redundant
        elif name=='startTime':#deprecated in v1.70.00
            params['startType'].val =unicode('time (s)')
            params['startVal'].val = unicode(paramNode.get('val'))
            return #times doesn't need to update its type or 'updates' rule
        elif name=='forceEndTrial':#deprecated in v1.70.00
            params['forceEndRoutine'].val = bool(paramNode.get('val'))
            return #forceEndTrial doesn't need to update its type or 'updates' rule
        elif name=='forceEndTrialOnPress':#deprecated in v1.70.00
            params['forceEndRoutineOnPress'].val = bool(paramNode.get('val'))
            return #forceEndTrial doesn't need to update its type or 'updates' rule
        elif name=='trialList':#deprecated in v1.70.00
            params['conditions'].val = eval(paramNode.get('val'))
            return #forceEndTrial doesn't need to update its type or 'updates' rule
        elif name=='trialListFile':#deprecated in v1.70.00
            params['conditionsFile'].val = unicode(paramNode.get('val'))
            return #forceEndTrial doesn't need to update its type or 'updates' rule
        elif name=='duration':#deprecated in v1.70.00
            params['stopType'].val =u'duration (s)'
            params['stopVal'].val = unicode(paramNode.get('val'))
            return #times doesn't need to update its type or 'updates' rule
        elif name=='allowedKeys' and valType=='str':#changed in v1.70.00
            #ynq used to be allowed, now should be 'y','n','q' or ['y','n','q']
            val=paramNode.get('val')
            if len(val)==0:
                newVal=val
            elif val[0]=='$':
                newVal=val[1:]#they were using code (which we can resused)
            elif val.startswith('[') and val.endswith(']'):
                newVal=val[1:-1]#they were using code (slightly incorectly!)
            elif val in ['return','space','left','right','escape']:
                newVal=val#they were using code
            else:
                newVal=repr(list(val))#convert string to list of keys then represent again as a string!
            params['allowedKeys'].val = newVal
            params['allowedKeys'].valType='code'
        elif name=='correctIf':#deprecated in v1.60.00
            corrIf=paramNode.get('val')
            corrAns=corrIf.replace('resp.keys==unicode(','').replace(')','')
            params['correctAns'].val=corrAns
            name='correctAns'#then we can fetch thte other aspects correctly below
        elif 'olour' in name:#colour parameter was Americanised in v1.61.00
            name=name.replace('olour','olor')
            params[name].val = paramNode.get('val')
        elif name=='times':#deprecated in v1.60.00
            exec('times=%s' %paramNode.get('val'))
            params['startType'].val =unicode('time (s)')
            params['startVal'].val = unicode(times[0])
            params['stopType'].val =unicode('time (s)')
            params['stopVal'].val = unicode(times[1])
            return #times doesn't need to update its type or 'updates' rule
        elif name in ['Begin Experiment', 'Begin Routine', 'Each Frame', 'End Routine', 'End Experiment']:
            params[name].val = paramNode.get('val')
            params[name].valType = 'extendedCode' #changed in 1.78.00
            return #so that we don't update valTyp again below
        elif 'val' in paramNode.keys():
            if paramNode.get('val')=='window units':#changed this value in 1.70.00
                params[name].val = 'from exp settings'
            else:
                params[name].val = paramNode.get('val')
        #get the value type and update rate
        if 'valType' in paramNode.keys():
            params[name].valType = paramNode.get('valType')
            # compatibility checks:
            if name in ['correctAns','text'] and paramNode.get('valType')=='code':
                params[name].valType='str'# these components were changed in v1.60.01
            elif name in ['allowedKeys'] and paramNode.get('valType')=='str':
                params[name].valType='code'# these components were changed in v1.70.00
            #conversions based on valType
            if params[name].valType=='bool': exec("params[name].val=%s" %params[name].val)
        if 'updates' in paramNode.keys():
            params[name].updates = paramNode.get('updates')
    def loadFromXML(self, filename):
        """Loads an xml file and parses the builder Experiment from it
        """
        #open the file using a parser that ignores prettyprint blank text
        parser = etree.XMLParser(remove_blank_text=True)
        f=open(filename)
        folder = os.path.split(filename)[0]
        if folder: #might be ''
            os.chdir(folder)
        self._doc=etree.XML(f.read(),parser)
        f.close()
        root=self._doc#.getroot()

        #some error checking on the version (and report that this isn't valid .psyexp)?
        filename_base = os.path.basename(filename)
        if root.tag != "PsychoPy2experiment":
            logging.error('%s is not a valid .psyexp file, "%s"' % (filename_base, root.tag))
            # the current exp is already vaporized at this point, oops
            return
        self.psychopyVersion = root.get('version')
        version_f = float(self.psychopyVersion.rsplit('.',1)[0]) # drop bugfix
        if version_f < 1.63:
            logging.warning('note: v%s was used to create %s ("%s")' % (self.psychopyVersion, filename_base, root.tag))

        #Parse document nodes
        #first make sure we're empty
        self.flow = Flow(exp=self)#every exp has exactly one flow
        self.routines={}
        self.namespace = NameSpace(self) # start fresh
        modified_names = []

        #fetch exp settings
        settingsNode=root.find('Settings')
        for child in settingsNode:
            self._getXMLparam(params=self.settings.params, paramNode=child)
        #name should be saved as a settings parameter (only from 1.74.00)
        if self.settings.params['expName'].val in ['',None,'None']:
            shortName = os.path.splitext(filename_base)[0]
            self.setExpName(shortName)
        #fetch routines
        routinesNode=root.find('Routines')
        for routineNode in routinesNode:#get each routine node from the list of routines
            routine_good_name = self.namespace.makeValid(routineNode.get('name'))
            if routine_good_name != routineNode.get('name'):
                modified_names.append(routineNode.get('name'))
            self.namespace.user.append(routine_good_name)
            routine = Routine(name=routine_good_name, exp=self)
            #self._getXMLparam(params=routine.params, paramNode=routineNode)
            self.routines[routineNode.get('name')]=routine
            for componentNode in routineNode:
                componentType=componentNode.tag
                #create an actual component of that type
                component=getAllComponents(self.prefsBuilder['componentsFolders'])[componentType](\
                    name=componentNode.get('name'),
                    parentName=routineNode.get('name'), exp=self)
                # check for components that were absent in older versions of the builder and change the default behavior (currently only the new behavior of choices for RatingScale, HS, November 2012)
                if componentType=='RatingScaleComponent':
                    if not componentNode.get('choiceLabelsAboveLine'): #this rating scale was created using older version of psychopy
                        component.params['choiceLabelsAboveLine'].val=True  #important to have .val here
                #populate the component with its various params
                for paramNode in componentNode:
                    self._getXMLparam(params=component.params, paramNode=paramNode)
                comp_good_name = self.namespace.makeValid(componentNode.get('name'))
                if comp_good_name != componentNode.get('name'):
                    modified_names.append(componentNode.get('name'))
                self.namespace.add(comp_good_name)
                component.params['name'].val = comp_good_name
                routine.append(component)
        # for each component that uses a Static for updates, we need to set that
        for thisRoutine in self.routines.values():
            for thisComp in thisRoutine:
                for thisParamName in thisComp.params:
                    thisParam = thisComp.params[thisParamName]
                    if thisParamName=='advancedParams':
                        continue#advanced isn't a normal param
                    elif thisParam.updates and "during:" in thisParam.updates:
                        updates = thisParam.updates.split(': ')[1] #remove the part that says 'during'
                        routine, static =  updates.split('.')
                        self.routines[routine].getComponentFromName(static).addComponentUpdate(
                            routine, thisComp.params['name'], thisParamName)
        #fetch flow settings
        flowNode=root.find('Flow')
        loops={}
        for elementNode in flowNode:
            if elementNode.tag=="LoopInitiator":
                loopType=elementNode.get('loopType')
                loopName=self.namespace.makeValid(elementNode.get('name'))
                if loopName != elementNode.get('name'):
                    modified_names.append(elementNode.get('name'))
                self.namespace.add(loopName)
                exec('loop=%s(exp=self,name="%s")' %(loopType,loopName))
                loops[loopName]=loop
                for paramNode in elementNode:
                    self._getXMLparam(paramNode=paramNode,params=loop.params)
                    #for conditions convert string rep to actual list of dicts
                    if paramNode.get('name')=='conditions':
                        param=loop.params['conditions']
                        exec('param.val=%s' %(param.val))#e.g. param.val=[{'ori':0},{'ori':3}]
                # get condition names from within conditionsFile, if any:
                try: conditionsFile = loop.params['conditionsFile'].val #psychophysicsstaircase demo has no such param
                except: conditionsFile = None
                if conditionsFile in ['None', '']:
                    conditionsFile = None
                if conditionsFile:
                    try:
                        _, fieldNames = data.importConditions(conditionsFile, returnFieldNames=True)
                        for fname in fieldNames:
                            if fname != self.namespace.makeValid(fname):
                                logging.warning('loadFromXML namespace conflict: "%s" in file %s' % (fname, conditionsFile))
                            else:
                                self.namespace.add(fname)
                    except:
                        pass#couldn't load the conditions file for now
                self.flow.append(LoopInitiator(loop=loops[loopName]))
            elif elementNode.tag=="LoopTerminator":
                self.flow.append(LoopTerminator(loop=loops[elementNode.get('name')]))
            elif elementNode.tag=="Routine":
                self.flow.append(self.routines[elementNode.get('name')])

        if modified_names:
            logging.warning('duplicate variable name(s) changed in loadFromXML: %s\n' % ' '.join(modified_names))

    def setExpName(self, name):
        self.settings.params['expName'].val=name
    def getExpName(self):
        return self.settings.params['expName'].val

class Param:
    """Defines parameters for Experiment Components
    A string representation of the parameter will depend on the valType:

    >>> print Param(val=[3,4], valType='num')
    asarray([3, 4])
    >>> print Param(val=3, valType='num') # num converts int to float
    3.0
    >>> print Param(val=3, valType='str') # str keeps as int, converts to code
    3
    >>> print Param(val='3', valType='str') # ... and keeps str as str
    '3'
    >>> print Param(val=[3,4], valType='str') # val is <type 'list'> -> code
    [3, 4]
    >>> print Param(val='[3,4]', valType='str')
    '[3,4]'
    >>> print Param(val=[3,4], valType='code')
    [3, 4]

    >>> #### auto str -> code:  at least one non-escaped '$' triggers str -> code: ####
    >>> print Param('[x,y]','str') # str normally returns string
    '[x,y]'
    >>> print Param('$[x,y]','str') # code, as triggered by $
    [x,y]
    >>> print Param('[$x,$y]','str') # code, redundant $ ok, cleaned up
    [x,y]
    >>> print Param('[$x,y]','str') # code, a $ anywhere means code
    [x,y]
    >>> print Param('[x,y]$','str') # ... even at the end
    [x,y]
    >>> print Param('[x,\$y]','str') # string, because the only $ is escaped
    '[x,$y]'
    >>> print Param('[x,\ $y]','str') # improper escape -> code (note that \ is not adjacent to $)
    [x,\ y]
    >>> print Param('/$[x,y]','str') # improper escape -> code (/ is not the same as \)
    /[x,y]
    >>> print Param('[\$x,$y]','str') # code, python syntax error
    [$x,y]
    >>> print Param('["\$x",$y]','str') # ... python syntax ok
    ["$x",y]
    >>> print Param("'$a'",'str') # code, with the code being a string, $ removed
    'a'
    >>> print Param("'\$a'",'str') # string, with the string containing a string, $ escaped (\ removed)
    "'$a'"
    >>> print Param('$$$$$myPathologicalVa$$$$$rName','str')
    myPathologicalVarName
    >>> print Param('\$$$$$myPathologicalVa$$$$$rName','str')
    $myPathologicalVarName
    >>> print Param('$$$$\$myPathologicalVa$$$$$rName','str')
    $myPathologicalVarName
    >>> print Param('$$$$\$$$myPathologicalVa$$$\$$$rName','str')
    $myPathologicalVa$rName
    """

    def __init__(self, val, valType, allowedVals=[],allowedTypes=[], hint="", label="", updates=None, allowedUpdates=None):
        """
        @param val: the value for this parameter
        @type val: any
        @param valType: the type of this parameter ('num', 'str', 'code')
        @type valType: string
        @param allowedVals: possible vals for this param (e.g. units param can only be 'norm','pix',...)
        @type allowedVals: any
        @param allowedTypes: if other types are allowed then this is the possible types this parameter can have (e.g. rgb can be 'red' or [1,0,1])
        @type allowedTypes: list
        @param hint: describe this parameter for the user
        @type hint: string
        @param updates: how often does this parameter update ('experiment', 'routine', 'set every frame')
        @type updates: string
        @param allowedUpdates: conceivable updates for this param [None, 'routine', 'set every frame']
        @type allowedUpdates: list
        """
        self.label=label
        self.val=val
        self.valType=valType
        self.allowedTypes=allowedTypes
        self.hint=hint
        self.updates=updates
        self.allowedUpdates=allowedUpdates
        self.allowedVals=allowedVals
        self.staticUpdater = None
    def __str__(self):
        if self.valType == 'num':
            try:
                return str(float(self.val))#will work if it can be represented as a float
            except:#might be an array
                return "asarray(%s)" %(self.val)
        elif self.valType == 'str':
            # at least 1 non-escaped '$' anywhere --> code wanted; only '\' will escape
            # return str if code wanted
            # return repr if str wanted; this neatly handles "it's" and 'He says "hello"'
            if type(self.val) in [str, unicode]:
                codeWanted = _unescapedDollarSign_re.search(self.val)
                if codeWanted:
                    return "%s" % getCodeFromParamStr(self.val)
                else: # str wanted
                    return repr(re.sub(r"[\\]\$", '$', self.val)) # remove \ from all \$
            return repr(self.val)
        elif self.valType in ['code', 'extendedCode']:
            if (type(self.val) in [str, unicode]) and self.val.startswith("$"):
                return "%s" %(self.val[1:])#a $ in a code parameter is unecessary so remove it
            elif (type(self.val) in [str, unicode]) and self.val.startswith("\$"):
                return "%s" %(self.val[1:])#the user actually wanted just the $
            elif (type(self.val) in [str, unicode]):
                return "%s" %(self.val)#the user actually wanted just the $
            else: #if the value was a tuple it needs converting to a string first
                return "%s" %(repr(self.val))
        elif self.valType == 'bool':
            return "%s" %(self.val)
        else:
            raise TypeError, "Can't represent a Param of type %s" %self.valType

class TrialHandler:
    """A looping experimental control object
            (e.g. generating a psychopy TrialHandler or StairHandler).
            """
    def __init__(self, exp, name, loopType='random', nReps=5,
        conditions=[], conditionsFile='',endPoints=[0,1],randomSeed=''):
        """
        @param name: name of the loop e.g. trials
        @type name: string
        @param loopType:
        @type loopType: string ('rand', 'seq')
        @param nReps: number of reps (for all conditions)
        @type nReps:int
        @param conditions: list of different trial conditions to be used
        @type conditions: list (of dicts?)
        @param conditionsFile: filename of the .csv file that contains conditions info
        @type conditions: string (filename)
        """
        self.type='TrialHandler'
        self.exp=exp
        self.order=['name']#make name come first (others don't matter)
        self.params={}
        self.params['name']=Param(name, valType='code', updates=None, allowedUpdates=None,
            hint="Name of this loop")
        self.params['nReps']=Param(nReps, valType='code', updates=None, allowedUpdates=None,
            hint="Number of repeats (for each condition)")
        self.params['conditions']=Param(conditions, valType='str', updates=None, allowedUpdates=None,
            hint="A list of dictionaries describing the parameters in each condition")
        self.params['conditionsFile']=Param(conditionsFile, valType='str', updates=None, allowedUpdates=None,
            hint="Name of a file specifying the parameters for each condition (.csv, .xlsx, or .pkl). Browse to select a file. Right-click to preview file contents, or create a new file.")
        self.params['endPoints']=Param(endPoints, valType='num', updates=None, allowedUpdates=None,
            hint="The start and end of the loop (see flow timeline)")
        self.params['loopType']=Param(loopType, valType='str',
            allowedVals=['random','sequential','fullRandom','staircase','interleaved staircases'],
            hint="How should the next condition value(s) be chosen?")#NB staircase is added for the sake of the loop properties dialog
        #these two are really just for making the dialog easier (they won't be used to generate code)
        self.params['endPoints']=Param(endPoints,valType='num',
            hint='Where to loop from and to (see values currently shown in the flow view)')
        self.params['random seed']=Param(randomSeed, valType='code', updates=None, allowedUpdates=None,
            hint="To have a fixed random sequence provide an integer of your choosing here. Leave blank to have a new random sequence on each run of the experiment.")
    def writeInitCode(self,buff):
        #no longer needed - initialise the trial handler just before it runs
        pass
    def writeLoopStartCode(self,buff):
        """Write the code to create and run a sequence of trials
        """
        ##first create the handler
        #init values
        inits=getInitVals(self.params)
        #import conditions from file
        if self.params['conditionsFile'].val in ['None',None,'none','']:
            condsStr="[None]"
        else: condsStr="data.importConditions(%s)" %self.params['conditionsFile']
        #also a 'thisName' for use in "for thisTrial in trials:"
        self.thisName = self.exp.namespace.makeLoopIndex(self.params['name'].val)
        #write the code
        buff.writeIndentedLines("\n# set up handler to look after randomisation of conditions etc\n")
        buff.writeIndented("%(name)s = data.TrialHandler(nReps=%(nReps)s, method=%(loopType)s, \n" %(inits))
        buff.writeIndented("    extraInfo=expInfo, originPath=%s,\n" %repr(self.exp.expPath))
        buff.writeIndented("    trialList=%s,\n" %(condsStr))
        buff.writeIndented("    seed=%(random seed)s, name='%(name)s')\n" %(inits))
        buff.writeIndented("thisExp.addLoop(%(name)s)  # add the loop to the experiment\n" %self.params)
        buff.writeIndented("%s = %s.trialList[0]  # so we can initialise stimuli with some values\n" %(self.thisName, self.params['name']))
        #create additional names (e.g. rgb=thisTrial.rgb) if user doesn't mind cluttered namespace
        if not self.exp.prefsBuilder['unclutteredNamespace']:
            buff.writeIndented("# abbreviate parameter names if possible (e.g. rgb=%s.rgb)\n" %self.thisName)
            buff.writeIndented("if %s != None:\n" %self.thisName)
            buff.writeIndented(buff.oneIndent+"for paramName in %s.keys():\n" %self.thisName)
            buff.writeIndented(buff.oneIndent*2+"exec(paramName + '= %s.' + paramName)\n" %self.thisName)

        ##then run the trials
        #work out a name for e.g. thisTrial in trials:
        buff.writeIndented("\n")
        buff.writeIndented("for %s in %s:\n" %(self.thisName, self.params['name']))
        #fetch parameter info from conditions
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("currentLoop = %s\n" %(self.params['name']))
        #create additional names (e.g. rgb=thisTrial.rgb) if user doesn't mind cluttered namespace
        if not self.exp.prefsBuilder['unclutteredNamespace']:
            buff.writeIndented("# abbreviate parameter names if possible (e.g. rgb = %s.rgb)\n" %self.thisName)
            buff.writeIndented("if %s != None:\n" %self.thisName)
            buff.writeIndented(buff.oneIndent+"for paramName in %s.keys():\n" %self.thisName)
            buff.writeIndented(buff.oneIndent*2+"exec(paramName + '= %s.' + paramName)\n" %self.thisName)
    def writeLoopEndCode(self,buff):
        buff.writeIndentedLines("thisExp.nextEntry()\n\n")
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("# completed %s repeats of '%s'\n" \
            %(self.params['nReps'], self.params['name']))
        buff.writeIndented("\n")

        #save data
        ##a string to show all the available variables (if the conditions isn't just None or [None])
        saveExcel=self.exp.settings.params['Save excel file'].val
        saveCSV = self.exp.settings.params['Save csv file'].val
        #get parameter names
        if saveExcel or saveCSV:
            buff.writeIndented("# get names of stimulus parameters\n" %self.params)
            buff.writeIndented("if %(name)s.trialList in ([], [None], None):  params = []\n" %self.params)
            buff.writeIndented("else:  params = %(name)s.trialList[0].keys()\n" %self.params)
        #write out each type of file
        if saveExcel or saveCSV:
            buff.writeIndented("# save data for this loop\n")
        if saveExcel:
            buff.writeIndented("%(name)s.saveAsExcel(filename + '.xlsx', sheetName='%(name)s',\n" %self.params)
            buff.writeIndented("    stimOut=params,\n")
            buff.writeIndented("    dataOut=['n','all_mean','all_std', 'all_raw'])\n")
        if saveCSV:
            buff.writeIndented("%(name)s.saveAsText(filename + '%(name)s.csv', delim=',',\n" %self.params)
            buff.writeIndented("    stimOut=params,\n")
            buff.writeIndented("    dataOut=['n','all_mean','all_std', 'all_raw'])\n")
    def getType(self):
        return 'TrialHandler'

class StairHandler:
    """A staircase experimental control object.
    """
    def __init__(self, exp, name, nReps='50', startVal='', nReversals='',
            nUp=1, nDown=3, minVal=0,maxVal=1,
            stepSizes='[4,4,2,2,1]', stepType='db', endPoints=[0,1]):
        """
        @param name: name of the loop e.g. trials
        @type name: string
        @param nReps: number of reps (for all conditions)
        @type nReps:int
        """
        self.type='StairHandler'
        self.exp=exp
        self.order=['name']#make name come first (others don't matter)
        self.params={}
        self.params['name']=Param(name, valType='code', hint="Name of this loop")
        self.params['nReps']=Param(nReps, valType='code',
            hint="(Minimum) number of trials in the staircase")
        self.params['start value']=Param(startVal, valType='code',
            hint="The initial value of the parameter")
        self.params['max value']=Param(maxVal, valType='code',
            hint="The maximum value the parameter can take")
        self.params['min value']=Param(minVal, valType='code',
            hint="The minimum value the parameter can take")
        self.params['step sizes']=Param(stepSizes, valType='code',
            hint="The size of the jump at each step (can change on each 'reversal')")
        self.params['step type']=Param(stepType, valType='str', allowedVals=['lin','log','db'],
            hint="The units of the step size (e.g. 'linear' will add/subtract that value each step, whereas 'log' will ad that many log units)")
        self.params['N up']=Param(nUp, valType='code',
            hint="The number of 'incorrect' answers before the value goes up")
        self.params['N down']=Param(nDown, valType='code',
            hint="The number of 'correct' answers before the value goes down")
        self.params['N reversals']=Param(nReversals, valType='code',
            hint="Minimum number of times the staircase must change direction before ending")
        #these two are really just for making the dialog easier (they won't be used to generate code)
        self.params['loopType']=Param('staircase', valType='str',
            allowedVals=['random','sequential','fullRandom','staircase','interleaved staircases'],
            hint="How should the next trial value(s) be chosen?")#NB this is added for the sake of the loop properties dialog
        self.params['endPoints']=Param(endPoints,valType='num',
            hint='Where to loop from and to (see values currently shown in the flow view)')
    def writeInitCode(self,buff):
        #not needed - initialise the staircase only when needed
        pass
    def writeLoopStartCode(self,buff):
        ##create the staircase
        #also a 'thisName' for use in "for thisTrial in trials:"
        self.thisName = self.exp.namespace.makeLoopIndex(self.params['name'].val)
        if self.params['N reversals'].val in ["", None, 'None']:
            self.params['N reversals'].val='0'
        #write the code
        buff.writeIndentedLines('\n#--------Prepare to start Staircase "%(name)s" --------\n' %self.params)
        buff.writeIndentedLines("# set up handler to look after next chosen value etc\n")
        buff.writeIndented("%(name)s = data.StairHandler(startVal=%(start value)s, extraInfo=expInfo,\n" %(self.params))
        buff.writeIndented("    stepSizes=%(step sizes)s, stepType=%(step type)s,\n" %self.params)
        buff.writeIndented("    nReversals=%(N reversals)s, nTrials=%(nReps)s, \n" %self.params)
        buff.writeIndented("    nUp=%(N up)s, nDown=%(N down)s,\n" %self.params)
        buff.writeIndented("    originPath=%s" %repr(self.exp.expPath))
        buff.write(", name='%(name)s')\n"%self.params)
        buff.writeIndented("thisExp.addLoop(%(name)s)  # add the loop to the experiment" %self.params)
        buff.writeIndented("level = %s = %s  # initialise some vals\n" %(self.thisName, self.params['start value']))
        ##then run the trials
        #work out a name for e.g. thisTrial in trials:
        buff.writeIndented("\n")
        buff.writeIndented("for %s in %s:\n" %(self.thisName, self.params['name']))
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("currentLoop = %s\n" %(self.params['name']))
        buff.writeIndented("level = %s\n" %(self.thisName))
    def writeLoopEndCode(self,buff):
        buff.writeIndentedLines("thisExp.nextEntry()\n\n")
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("# staircase completed\n")
        buff.writeIndented("\n")
        #save data
        if self.exp.settings.params['Save excel file'].val:
            buff.writeIndented("%(name)s.saveAsExcel(filename + '.xlsx', sheetName='%(name)s')\n" %self.params)
        if self.exp.settings.params['Save csv file'].val:
            buff.writeIndented("%(name)s.saveAsText(filename + '%(name)s.csv', delim=',')\n" %self.params)
    def getType(self):
        return 'StairHandler'

class MultiStairHandler:
    """To handle multiple interleaved staircases
    """
    def __init__(self, exp, name, nReps='50', stairType='simple',
        switchStairs='random',
        conditions=[], conditionsFile='', endPoints=[0,1]):
        """
        @param name: name of the loop e.g. trials
        @type name: string
        @param nReps: number of reps (for all conditions)
        @type nReps:int
        """
        self.type='MultiStairHandler'
        self.exp=exp
        self.order=['name']#make name come first
        self.params={}
        self.params['name']=Param(name, valType='code', hint="Name of this loop")
        self.params['nReps']=Param(nReps, valType='code',
            hint="(Minimum) number of trials in *each* staircase")
        self.params['stairType']=Param(nReps, valType='str', allowedVals=['simple','QUEST'],
            hint="How to select the next staircase to run")
        self.params['switchMethod']=Param(nReps, valType='str', allowedVals=['random','sequential','fullRandom'],
            hint="How to select the next staircase to run")
        #these two are really just for making the dialog easier (they won't be used to generate code)
        self.params['loopType']=Param('staircase', valType='str',
        allowedVals=['random','sequential','fullRandom','staircase','interleaved staircases'],
            hint="How should the next trial value(s) be chosen?")#NB this is added for the sake of the loop properties dialog
        self.params['endPoints']=Param(endPoints,valType='num',
            hint='Where to loop from and to (see values currently shown in the flow view)')
        self.params['conditions']=Param(conditions, valType='str', updates=None, allowedUpdates=None,
            hint="A list of dictionaries describing the differences between each staircase")
        self.params['conditionsFile']=Param(conditionsFile, valType='str', updates=None, allowedUpdates=None,
            hint="An xlsx or csv file specifying the parameters for each condition")
    def writeInitCode(self,buff):
        #also a 'thisName' for use in "for thisTrial in trials:"
        self.thisName = self.exp.namespace.makeLoopIndex(self.params['name'].val)
        #write the code
        buff.writeIndentedLines("\n# set up handler to look after randomisation of trials etc\n")
        buff.writeIndentedLines("conditions = data.importConditions(%s)" %self.params['conditionsFile'])
        buff.writeIndented("%(name)s = data.MultiStairHandler(stairType=%(stairType)s, name='%(name)s',\n" %(self.params))
        buff.writeIndented("    nTrials=%(nReps)s,\n" %self.params)
        buff.writeIndented("    conditions=conditions,\n")
        buff.writeIndented("    originPath=%s" %repr(self.exp.expPath))
        buff.write(")\n"%self.params)
        buff.writeIndented("thisExp.addLoop(%(name)s)  # add the loop to the experiment\n" %self.params)
        buff.writeIndented("# initialise values for first condition\n")
        buff.writeIndented("level = %(name)s._nextIntensity  # initialise some vals\n" %(self.params))
        buff.writeIndented("condition = %(name)s.currentStaircase.condition\n" %(self.params))
    def writeLoopStartCode(self,buff):
        #work out a name for e.g. thisTrial in trials:
        buff.writeIndented("\n")
        buff.writeIndented("for level, condition in %(name)s:\n" %(self.params))
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("currentLoop = %(name)s\n" %(self.params))
        #create additional names (e.g. rgb=thisTrial.rgb) if user doesn't mind cluttered namespace
        if not self.exp.prefsBuilder['unclutteredNamespace']:
            buff.writeIndented("# abbreviate parameter names if possible (e.g. rgb=condition.rgb)\n")
            buff.writeIndented("for paramName in condition.keys():\n")
            buff.writeIndented(buff.oneIndent+"exec(paramName + '= condition[paramName]')\n")
    def writeLoopEndCode(self,buff):
        buff.writeIndentedLines("thisExp.nextEntry()\n\n")
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("# all staircases completed\n")
        buff.writeIndented("\n")
        #save data
        if self.exp.settings.params['Save excel file'].val:
            buff.writeIndented("%(name)s.saveAsExcel(filename + '.xlsx')\n" %self.params)
        if self.exp.settings.params['Save csv file'].val:
            buff.writeIndented("%(name)s.saveAsText(filename + '%(name)s.csv', delim=',')\n" %self.params)
    def getType(self):
        return 'MultiStairHandler'

class LoopInitiator:
    """A simple class for inserting into the flow.
    This is created automatically when the loop is created"""
    def __init__(self, loop):
        self.loop=loop
        self.exp=loop.exp
        loop.initiator=self
    def writeInitCode(self,buff):
        self.loop.writeInitCode(buff)
    def writeMainCode(self,buff):
        self.loop.writeLoopStartCode(buff)
        self.exp.flow._loopList.append(self.loop)#we are now the inner-most loop
    def getType(self):
        return 'LoopInitiator'
    def writeExperimentEndCode(self,buff):#not needed
        pass
class LoopTerminator:
    """A simple class for inserting into the flow.
    This is created automatically when the loop is created"""
    def __init__(self, loop):
        self.loop=loop
        self.exp=loop.exp
        loop.terminator=self
    def writeInitCode(self,buff):
        pass
    def writeMainCode(self,buff):
        self.loop.writeLoopEndCode(buff)
        self.exp.flow._loopList.remove(self.loop)# _loopList[-1] will now be the inner-most loop
    def getType(self):
        return 'LoopTerminator'
    def writeExperimentEndCode(self,buff):#not needed
        pass
class Flow(list):
    """The flow of the experiment is a list of L{Routine}s, L{LoopInitiator}s and
    L{LoopTerminator}s, that will define the order in which events occur
    """
    def __init__(self, exp):
        list.__init__(self)
        self.exp=exp
        self._currentRoutine=None
        self._loopList=[]#will be used while we write the code
    def __repr__(self):
        return "psychopy.experiment.Flow(%s)" %(str(list(self)))
    def addLoop(self, loop, startPos, endPos):
        """Adds initiator and terminator objects for the loop
        into the Flow list"""
        self.insert(int(endPos), LoopTerminator(loop))
        self.insert(int(startPos), LoopInitiator(loop))
        self.exp.requirePsychopyLibs(['data'])#needed for TrialHandlers etc
    def addRoutine(self, newRoutine, pos):
        """Adds the routine to the Flow list"""
        self.insert(int(pos), newRoutine)
    def removeComponent(self,component,id=None):
        """Removes a Loop, LoopTerminator or Routine from the flow

        For a Loop (or initiator or terminator) to be deleted we can simply remove
        the object using normal list syntax. For a Routine there may be more than
        one instance in the Flow, so either choose which one by specifying the id, or all
        instances will be removed (suitable if the Routine has been deleted).
        """
        if component.getType() in ['LoopInitiator', 'LoopTerminator']:
            component=component.loop#and then continue to do the next
        if component.getType() in ['StairHandler', 'TrialHandler', 'MultiStairHandler']:
            #we need to remove the termination points that correspond to the loop
            toBeRemoved = []
            for comp in self: # cant safely change the contents of self when looping through self
                if comp.getType() in ['LoopInitiator','LoopTerminator']:
                    if comp.loop==component:
                        #self.remove(comp) --> skips over loop terminator if its an empty loop
                        toBeRemoved.append(comp)
            for comp in toBeRemoved:
                self.remove(comp)
        elif component.getType()=='Routine':
            if id==None:
                #a Routine may come up multiple times - remove them all
                #self.remove(component)#cant do this - two empty routines (with diff names) look the same to list comparison
                toBeRemoved = []
                for id, compInFlow in enumerate(self):
                    if hasattr(compInFlow, 'name') and component.name==compInFlow.name:
                        toBeRemoved.append(id)
                toBeRemoved.reverse()#need to delete from the end backwards or the order changes
                for id in toBeRemoved:
                    del self[id]
            else:
                del self[id]#just delete the single entry we were given (e.g. from right-click in GUI)

    def _dubiousConstantUpdates(self, component):
        """Return a list of fields in component that are set to be constant but
        seem intended to be dynamic. Some code fields are constant, and some
        denoted as code by $ are constant.
        """
        warnings = []
        # treat expInfo as likely to be constant; also treat its keys as constant
        # because its handy to make a short-cut in code: exec(key+'=expInfo[key]')
        e = eval(self.exp.settings.params['Experiment info'].val)  # dict
        expInfo = e.keys()
        keywords = self.exp.namespace.nonUserBuilder[:] + ['expInfo'] + expInfo
        ignore = set(keywords).difference(set(['random', 'rand']))
        for key in component.params:
            field = component.params[key]
            if not hasattr(field, 'val') or not isinstance(field.val, basestring):
                continue  # continue == no problem, no warning
            if not (field.allowedUpdates and type(field.allowedUpdates) == list and
                len(field.allowedUpdates) and field.updates == 'constant'):
                continue
            # only non-empty, possibly-code, and 'constant' updating at this point
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
                names = compile(code,'','eval').co_names
            except SyntaxError:
                continue
            # ignore reserved words:
            if not set(names).difference(ignore):
                continue
            warnings.append( (field, key) )
        if warnings:
            return warnings
        return [(None, None)]
    def _prescreenValues(self):
        # pre-screen and warn about some conditions in component values:
        trailingWhitespace = []
        constWarnings = []
        for entry in self:  #NB each entry is a routine or LoopInitiator/Terminator
            if type(entry) != Routine:
                continue
            for component in entry:
                # detect and strip trailing whitespace (can cause problems):
                for key in component.params:
                    field = component.params[key]
                    if not hasattr(field, 'label'):
                        continue  # no problem, no warning
                    if field.label.lower() == 'text' or not field.valType in ['str', 'code']:
                        continue
                    if type(field.val) == basestring and field.val != field.val.strip():
                        trailingWhitespace.append((field.val, key, component, entry))
                        field.val = field.val.strip()
                # detect 'constant update' fields that seem intended to be dynamic:
                for field, key in self._dubiousConstantUpdates(component):
                    if field:
                        constWarnings.append((field.val, key, component, entry))
        if trailingWhitespace:
            warnings = []
            msg = '"%s", in Routine %s (%s: %s)'
            for field, key, component, routine in trailingWhitespace:
                warnings.append( msg % (field, routine.params['name'],
                                component.params['name'], key.capitalize()) )
            print 'Note: Trailing white-space removed:\n ',
            print '\n  '.join(list(set(warnings)))  # non-redundant, order unknown
        if constWarnings:
            warnings = []
            msg = '"%s", in Routine %s (%s: %s)'
            for field, key, component, routine in constWarnings:
                warnings.append( msg % (field, routine.params['name'],
                                component.params['name'], key.capitalize()) )
            print 'Note: Dynamic code seems intended but updating is "constant":\n ',
            print '\n  '.join(list(set(warnings)))  # non-redundant, order unknown
    def writeStartCode(self, script):
        """Write the code that comes before the Window is created
        """
        script.writeIndentedLines("\n# Start Code - component code to be run before the window creation\n")
        for entry in self:  #NB each entry is a routine or LoopInitiator/Terminator
            self._currentRoutine=entry
            # very few components need writeStartCode:
            if hasattr(entry, 'writeStartCode'):
                entry.writeStartCode(script)

    def writeCode(self, script):
        """Write the rest of the code
        """
        # writeStartCode and writeInitCode:
        for entry in self: #NB each entry is a routine or LoopInitiator/Terminator
            self._currentRoutine=entry
            entry.writeInitCode(script)
        #create clocks (after initialising stimuli)
        script.writeIndentedLines("\n# Create some handy timers\n")
        script.writeIndented("globalClock = core.Clock()  # to track the time since experiment started\n")
        script.writeIndented("routineTimer = core.CountdownTimer()  # to track time remaining of each (non-slip) routine \n")
        #run-time code
        for entry in self:
            self._currentRoutine=entry
            entry.writeMainCode(script)
        #tear-down code (very few components need this)
        for entry in self:
            self._currentRoutine=entry
            entry.writeExperimentEndCode(script)

class Routine(list):
    """
    A Routine determines a single sequence of events, such
    as the presentation of trial. Multiple Routines might be
    used to comprise an Experiment (e.g. one for presenting
    instructions, one for trials, one for debriefing subjects).

    In practice a Routine is simply a python list of Components,
    each of which knows when it starts and stops.
    """
    def __init__(self, name, exp, components=[]):
        self.params={'name':name}
        self.name=name
        self.exp=exp
        self._clockName=None#this is used for script-writing e.g. "t=trialClock.GetTime()"
        self.type='Routine'
        list.__init__(self, components)
    def __repr__(self):
        return "psychopy.experiment.Routine(name='%s',exp=%s,components=%s)" %(self.name,self.exp,str(list(self)))
    def addComponent(self,component):
        """Add a component to the end of the routine"""
        self.append(component)
    def removeComponent(self,component):
        """Remove a component from the end of the routine"""
        self.remove(component)
        #check if the component was using any Static Components for updates
        for thisParamName, thisParam in component.params.items():
            if hasattr(thisParam,'updates') and thisParam.updates and 'during:' in thisParam.updates:
                updates = thisParam.updates.split(': ')[1] #remove the part that says 'during'
                routine, static =  updates.split('.')
                self.exp.routines[routine].getComponentFromName(static).remComponentUpdate(
                    routine, component.params['name'], thisParamName)
    def getStatics(self):
        """Return a list of Static components
        """
        statics=[]
        for comp in self:
            if comp.type=='Static':
                statics.append(comp)
        return statics
    def writeStartCode(self,buff):
        # few components will have this
        for thisCompon in self:
            # check just in case; try to ensure backwards compatibility in _base,py
            if hasattr(thisCompon, 'writeStartCode'):
                thisCompon.writeStartCode(buff)
    def writeInitCode(self,buff):
        buff.writeIndented('\n')
        buff.writeIndented('# Initialize components for Routine "%s"\n' %(self.name))
        self._clockName = self.name+"Clock"
        buff.writeIndented('%s = core.Clock()\n' %(self._clockName))
        for thisCompon in self:
            thisCompon.writeInitCode(buff)
    def writeMainCode(self,buff):
        """This defines the code for the frames of a single routine
        """
        #create the frame loop for this routine
        buff.writeIndentedLines('\n#------Prepare to start Routine "%s"-------\n' %(self.name))

        buff.writeIndented('t = 0\n')
        buff.writeIndented('%s.reset()  # clock \n' %(self._clockName))
        buff.writeIndented('frameN = -1\n')
        #can we use non-slip timing?
        maxTime, useNonSlip, onlyStaticComps = self.getMaxTime()
        if useNonSlip:
            buff.writeIndented('routineTimer.add(%f)\n' %(maxTime))

        buff.writeIndentedLines("# update component parameters for each repeat\n")
        #This is the beginning of the routine, before the loop starts
        for event in self:
            event.writeRoutineStartCode(buff)

        buff.writeIndented('# keep track of which components have finished\n')
        buff.writeIndented('%sComponents = []\n' %(self.name))
        for thisCompon in self:
            if thisCompon.params.has_key('startType'):
                buff.writeIndented('%sComponents.append(%s)\n' %(self.name, thisCompon.params['name']))
        buff.writeIndented("for thisComponent in %sComponents:\n"%(self.name))
        buff.writeIndented("    if hasattr(thisComponent, 'status'):\n")
        buff.writeIndented("        thisComponent.status = NOT_STARTED\n")

        buff.writeIndentedLines('\n#-------Start Routine "%s"-------\n' %(self.name))
        buff.writeIndented('continueRoutine = True\n')
        if useNonSlip:
            buff.writeIndented('while continueRoutine and routineTimer.getTime() > 0:\n')
        else:
            buff.writeIndented('while continueRoutine:\n')
        buff.setIndentLevel(1,True)

        #on each frame
        buff.writeIndented('# get current time\n')
        buff.writeIndented('t = %s.getTime()\n' %self._clockName)
        buff.writeIndented('frameN = frameN + 1  # number of completed frames (so 0 is the first frame)\n')

        #write the code for each component during frame
        buff.writeIndentedLines('# update/draw components on each frame\n')
        #just 'normal' components
        for event in self:
            if event.type=='Static':
                continue #we'll do those later
            event.writeFrameCode(buff)
        #update static component code last
        for event in self.getStatics():
            event.writeFrameCode(buff)

        #are we done yet?
        buff.writeIndentedLines('\n# check if all components have finished\n')
        buff.writeIndentedLines('if not continueRoutine:  # a component has requested a forced-end of Routine\n')
        buff.writeIndentedLines('    routineTimer.reset()  # if we abort early the non-slip timer needs reset\n')
        buff.writeIndentedLines('    break\n')
        buff.writeIndentedLines('continueRoutine = False  # will revert to True if at least one component still running\n')
        buff.writeIndentedLines('for thisComponent in %sComponents:\n' %self.name)
        buff.writeIndentedLines('    if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:\n')
        buff.writeIndentedLines('        continueRoutine = True\n')
        buff.writeIndentedLines('        break  # at least one component has not yet finished\n')

        #allow subject to quit via Esc key?
        if self.exp.settings.params['Enable Escape'].val:
            buff.writeIndentedLines('\n# check for quit (the [Esc] key)')
            buff.writeIndentedLines('if event.getKeys(["escape"]):\n')
            buff.writeIndentedLines('    core.quit()\n')
        #update screen
        buff.writeIndentedLines('\n# refresh the screen\n')
        buff.writeIndented("if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen\n")
        buff.writeIndented('    win.flip()\n')
        if not useNonSlip:
            buff.writeIndented("else:  # this Routine was not non-slip safe so reset non-slip timer\n")
            buff.writeIndented('    routineTimer.reset()\n')

        #that's done decrement indent to end loop
        buff.setIndentLevel(-1,True)

        #write the code for each component for the end of the routine
        buff.writeIndented('\n')
        buff.writeIndented('#-------Ending Routine "%s"-------\n' %(self.name))
        buff.writeIndentedLines('for thisComponent in %sComponents:\n' %self.name)
        buff.writeIndentedLines('    if hasattr(thisComponent, "setAutoDraw"):\n        thisComponent.setAutoDraw(False)\n')
        for event in self:
            event.writeRoutineEndCode(buff)

    def writeExperimentEndCode(self,buff):
        """This defines the code for the frames of a single routine
        """
        #This is the beginning of the routine, before the loop starts
        for component in self:
            component.writeExperimentEndCode(buff)
    def getType(self):
        return 'Routine'
    def getComponentFromName(self, name):
        for comp in self:
            if comp.params['name'].val==name:
                return comp
        return None
    def getMaxTime(self):
        """What the last (predetermined) stimulus time to be presented. If
        there are no components or they have code-based times then will default
        to 10secs
        """
        maxTime=0
        nonSlipSafe = True # if possible
        onlyStaticComps = True
        for n, component in enumerate(self):
            if component.params.has_key('startType'):
                start, duration, nonSlip = component.getStartAndDuration()
                if not nonSlip:
                    nonSlipSafe=False
                if duration==FOREVER:
                    # only the *start* of an unlimited event should contribute to maxTime
                    duration = 1 # plus some minimal duration so it's visible
                #now see if we have a end t value that beats the previous max
                try:
                    thisT=start+duration#will fail if either value is not defined
                except:
                    thisT=0
                maxTime=max(maxTime,thisT)
                #update onlyStaticComps if needed
                if component.type != 'Static':
                    onlyStaticComps = False
        if maxTime==0:#if there are no components
            maxTime=10
            nonSlipSafe=False
        return maxTime, nonSlipSafe, onlyStaticComps

class ExpFile(list):
    """An ExpFile is similar to a Routine except that it generates its code
    from the Flow of a separate, complete psyexp file.
    """
    def __init__(self, name, exp, filename=''):
        self.params={'name':name}
        self.name=name
        self.exp=exp #the exp we belong to
        self.expObject = None #the experiment we represent on disk (see self.loadExp)
        self.filename-filename
        self._clockName=None#this is used for script-writing e.g. "t=trialClock.GetTime()"
        self.type='ExpFile'
        list.__init__(self, components)
    def __repr__(self):
        return "psychopy.experiment.ExpFile(name='%s',exp=%s,filename='%s')" %(self.name, self.exp, self.filename)
    def writeStartCode(self,buff):
        #tell each object on our flow to write its start code
        for entry in self.flow:  #NB each entry is a routine or LoopInitiator/Terminator
            self._currentRoutine=entry
            if hasattr(entry, 'writeStartCode'):
                entry.writeStartCode(script) # used by microphone comp to create a .wav directory once
    def loadExp(self):
        #fetch the file
        self.expObject = Experiment()
        self.expObject.loadFromXML(sel.filename)
        self.flow = self.expObject.flow #extract the flow, which is the key part for us
    def writeInitCode(self,buff):
        #tell each object on our flow to write its init code
        for entry in self.flow: #NB each entry is a routine or LoopInitiator/Terminator
            self._currentRoutine=entry
            entry.writeInitCode(script)
    def writeMainCode(self,buff):
        """This defines the code for the frames of a single routine
        """
        #tell each object on our flow to write its run code
        for entry in self.flow:
            self._currentRoutine=entry
            entry.writeMainCode(script)
    def writeExperimentEndCode(self,buff):
        """This defines the code for the frames of a single routine
        """
        for entry in self.flow:
            self._currentRoutine=entry
            entry.writeExperimentEndCode(script)
    def getType(self):
        return 'ExpFile'
    def getMaxTime(self):
        """What the last (predetermined) stimulus time to be presented. If
        there are no components or they have code-based times then will default
        to 10secs
        """
        pass
        #todo?: currently only Routines perform this action

class NameSpace():
    """class for managing variable names in builder-constructed experiments.

    The aim is to help detect and avoid name-space collisions from user-entered variable names.
    Track four groups of variables:
        numpy =    part of numpy or numpy.random (maybe its ok for a user to redefine these?)
        psychopy = part of psychopy, such as event or data; include os here
        builder =  used internally by the builder when constructing an experiment
        user =     used 'externally' by a user when programming an experiment
    Some vars, like core, are part of both psychopy and numpy, so the order of operations can matter

    Notes for development:
    are these all of the ways to get into the namespace?
    - import statements at top of file: numpy, psychopy, os, etc
    - a handful of things that always spring up automatically, like t and win
    - routines: user-entered var name = routine['name'].val, plus sundry helper vars, like theseKeys
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
        """Set-up an experiment's namespace: reserved words and user space"""
        self.exp = exp
        #deepcopy fails if you pre-compile regular expressions and stash here

        self.numpy = _numpyImports + _numpyRandomImports + ['np']
        self.keywords = ['and', 'del', 'from', 'not', 'while', 'as', 'elif',
            'with', 'assert', 'else', 'if', 'pass', 'yield', 'break', 'except',
            'import', 'print', 'class', 'exec', 'in', 'raise', 'continue', 'or',
            'finally', 'is', 'return', 'def', 'for', 'lambda', 'try', 'global',
            'abs', 'all', 'any', 'apply', 'basestring', 'bin', 'bool', 'buffer',
            'bytearray', 'bytes', 'callable', 'chr', 'classmethod', 'cmp',
            'compile', 'complex', 'copyright', 'credits', 'delattr', 'dict',
            'divmod', 'enumerate', 'eval', 'execfile', 'exit', 'file', 'filter',
            'float', 'format', 'frozenset', 'getattr', 'globals', 'hasattr',
            'help', 'hex', 'id', 'input', 'int', 'intern', 'isinstance', 'hash',
            'iter', 'len', 'license', 'list', 'locals', 'long', 'map', 'max',
            'min', 'next', 'object', 'oct', 'open', 'ord', 'pow', 'print', 'dir',
            'quit', 'range', 'raw_input', 'reduce', 'reload', 'repr', 'reversed',
            'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum',
            'super', 'tuple', 'type', 'unichr', 'unicode', 'vars', 'xrange',
            'clear', 'copy', 'fromkeys', 'get', 'has_key', 'items', 'iteritems',
            'iterkeys', 'round', 'memoryview', 'issubclass', 'property', 'zip',
            'itervalues', 'keys', 'pop', 'popitem', 'setdefault', 'update',
            'values', 'viewitems', 'viewkeys', 'viewvalues', 'coerce',
            '__builtins__', '__doc__', '__file__', '__name__', '__package__',
            'None', 'True', 'False']
        # these are based on a partial test, known to be incomplete:
        self.psychopy = ['psychopy', 'os', 'core', 'data', 'visual', 'event',
            'gui', 'sound', 'misc', 'logging', 'microphone',
            'NOT_STARTED', 'STARTED', 'FINISHED', 'PAUSED', 'STOPPED',
            'PLAYING', 'FOREVER', 'PSYCHOPY_USERAGENT']
        self.builder = ['KeyResponse', 'key_resp', 'buttons', 'continueRoutine',
            'expInfo', 'expName', 'thisExp', 'filename', 'logFile', 'paramName',
            't', 'frameN', 'currentLoop', 'dlg',
            'globalClock', 'routineTimer',
            'theseKeys', 'win', 'x', 'y', 'level', 'component', 'thisComponent']
        # user-entered, from Builder dialog or conditions file:
        self.user = []
        self.nonUserBuilder = self.numpy + self.keywords + self.psychopy

    def __str__(self, numpy_count_only=True):
        vars = self.user + self.builder + self.psychopy
        if numpy_count_only:
            return "%s + [%d numpy]" % (str(vars), len(self.numpy))
        else:
            return str(vars + self.numpy)

    def getDerived(self, basename):
        """ buggy
        idea: return variations on name, based on its type, to flag name that will come to exist at run-time;
        more specific than is_possibly-derivable()
        if basename is a routine, return continueBasename and basenameClock,
        if basename is a loop, return makeLoopIndex(name)
        """
        derived_names = []
        for flowElement in self.exp.flow:
            if flowElement.getType() in ['LoopInitiator','LoopTerminator']:
                flowElement=flowElement.loop  # we want the loop itself
                # basename can be <type 'instance'>
                derived_names += [self.makeLoopIndex(basename)]
            if basename == str(flowElement.params['name']) and basename+'Clock' not in derived_names:
                derived_names += [basename+'Clock', 'continue'+basename.capitalize()]
        # other derived_names?
        #
        return derived_names

    def getCollisions(self):
        """return None, or a list of names in .user that are also in one of the other spaces"""
        duplicates = list(set(self.user).intersection(set(self.builder + self.psychopy + self.numpy)))
        su = sorted(self.user)
        duplicates += [var for i,var in enumerate(su) if i<len(su)-1 and su[i+1] == var]
        if duplicates != []:
            return duplicates
        return None

    def isValid(self, name):
        """var-name compatible? return True if string name is alphanumeric + underscore only, with non-digit first"""
        return bool(_valid_var_re.match(name))
    def isPossiblyDerivable(self, name):
        """catch all possible derived-names, regardless of whether currently"""
        derivable = (name.startswith('this') or
                     name.startswith('these') or
                     name.startswith('continue') or
                     name.endswith('Clock') or
                     name.lower().find('component') > -1)
        if derivable:
            return " safer to avoid this, these, continue, Clock, or component in name"
        return None
    def exists(self, name):
        """returns None, or a message indicating where the name is in use.
        cannot guarantee that a name will be conflict-free.
        does not check whether the string is a valid variable name.

        >>> exists('t')
        Builder variable
        """
        try: name = str(name) # convert from unicode if possible
        except: pass

        # check getDerived:

        # check in this order:
        if name in self.user: return "one of your Components, Routines, or condition parameters"
        if name in self.builder: return "Builder variable"
        if name in self.psychopy: return "Psychopy module"
        if name in self.numpy: return "numpy function"
        if name in self.keywords: return "python keyword"

        return # None, meaning does not exist already

    def add(self, name, sublist='default'):
        """add name to namespace by appending a name or list of names to a sublist, eg, self.user"""
        if name is None: return
        if sublist == 'default': sublist = self.user
        if type(name) != list:
            sublist.append(name)
        else:
            sublist += name

    def remove(self, name, sublist='default'):
        """remove name from the specified sublist (and hence from the name-space), eg, self.user"""
        if name is None: return
        if sublist == 'default': sublist = self.user
        if type(name) != list:
            name = [name]
        for n in list(name):
            if n in sublist:
                del sublist[sublist.index(n)]

    def makeValid(self, name, prefix='var'):
        """given a string, return a valid and unique variable name.
        replace bad characters with underscore, add an integer suffix until its unique

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
        try: name = str(name) # convert from unicode, flag as uni if can't convert
        except: prefix = 'uni'
        if not name: name = prefix+'_1'
        if name[0].isdigit():
            name = prefix+'_' + name
        name = _nonalphanumeric_re.sub('_', name) # replace all bad chars with _

        # try to make it unique; success depends on accuracy of self.exists():
        i = 2  # skip _1 so that user can rename the first one to be _1 if desired
        if self.exists(name) and '_' in name: # maybe it already has _\d+? if so, increment from there
            basename, count = name.rsplit('_', 1)
            try:
                i = int(count) + 1
                name = basename
            except:
                pass
        nameStem = name + '_'
        while self.exists(name): # brute-force a unique name
            name = nameStem + str(i)
            i += 1
        return name

    def makeLoopIndex(self, name):
        """return a valid, readable loop-index name: 'this' + (plural->singular).capitalize() [+ (_\d+)]"""
        try: newName = str(name)
        except: newName = name
        prefix = 'this'
        irregular = {'stimuli': 'stimulus', 'mice': 'mouse', 'people': 'person'}
        for plural, singular in irregular.items():
            nn = re.compile(plural, re.IGNORECASE)
            newName = nn.sub(singular, newName)
        if newName.endswith('s') and not newName.lower() in irregular.values():
            newName = newName[:-1] # trim last 's'
        else: # might end in s_2, so delete that s; leave S
            match = re.match(r"^(.*)s(_\d+)$", newName)
            if match: newName = match.group(1) + match.group(2)
        newName = prefix + newName[0].capitalize() + newName[1:] # retain CamelCase
        newName = self.makeValid(newName)
        return newName

def _XMLremoveWhitespaceNodes(parent):
    """Remove all text nodes from an xml document (likely to be whitespace)
    """
    for child in list(parent.childNodes):
        if child.nodeType==node.TEXT_NODE and node.data.strip()=='':
            parent.removeChild(child)
        else:
            removeWhitespaceNodes(child)

def getCodeFromParamStr(val):
    """Convert a Param.val string to its intended python code, as triggered by $
    """
    tmp = re.sub(r"^(\$)+", '', val)  # remove leading $, if any
    tmp2 = re.sub(r"([^\\])(\$)+", r"\1", tmp)  # remove all nonescaped $, squash $$$$$
    return re.sub(r"[\\]\$", '$', tmp2)  # remove \ from all \$
