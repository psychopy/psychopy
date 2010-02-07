# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import StringIO, sys
from components import *#getComponents('') and getAllComponents([])
from lxml import etree

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
    def __init__(self):
        self.name=None
        self.flow = Flow(exp=self)#every exp has exactly one flow
        self.routines={}

        #this can be checked by the builder that this is an experiment and a compatible version
        self.psychopyVersion=psychopy.__version__ #imported from components
        self.psychopyLibs=['core','data', 'event']
        self.settings=getAllComponents()['SettingsComponent'](parentName='', exp=self)
        self._doc=None#this will be the xml.dom.minidom.doc object for saving
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

    def writeScript(self):
        """Write a PsychoPy script for the experiment
        """
        self.noKeyResponse=True#if keyboard is used (and data stored) this will be False
        s=IndentingBuffer(u'') #a string buffer object
        s.writeIndented('#!/usr/bin/env python\n')
        s.writeIndented('"""This experiment was created using PsychoPy2 Experiment Builder ')
        s.writeIndented('If you publish work using this script please cite the relevant papers (e.g. Peirce, 2007;2009)"""\n\n')

        #import psychopy libs
        libString=""; separator=""
        for lib in self.psychopyLibs:
            libString = libString+separator+lib
            separator=", "#for the second lib upwards we need a comma
        s.writeIndented("from numpy import * #many different maths functions\n")
        s.writeIndented("import os #handy system and path functions\n")
        s.writeIndented("from psychopy import %s\n" %libString)
        s.writeIndented("import psychopy.log #import like this so it doesn't interfere with numpy.log\n\n")

        self.settings.writeStartCode(s)#present info dlg, make logfile, Window
        #delegate rest of the code-writing to Flow
        self.flow.writeCode(s)
        self.settings.writeEndCode(s)#close log file

        return s
    def getUsedName(self, name):
        """Check the exp._usedNames dict and return None for unused or
        the type of object using it otherwise
        """
        #look for routines and loop names
        for flowElement in self.flow:
            if flowElement.getType()in ['LoopInitiator','LoopTerminator']:
                flowElement=flowElement.loop #we want the loop itself
            if flowElement.params['name']==name: return flowElement.getType()
        for routineName in self.routines.keys():
            for comp in self.routines[routineName]:
                if name==comp.params['name'].val: return comp.getType()
        return#we didn't find an existing name :-)
    def saveToXML(self, filename):
        #create the dom object
        self.xmlRoot = etree.Element("PsychoPy2experiment")
        self.xmlRoot.set('version', self.psychopyVersion)
        self.xmlRoot.set('encoding', 'utf-8')
        ##in the following, anything beginning '
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
                    if paramName=='trialList': #override val with repr(val)
                        paramNode.set('val',repr(param.val))
            elif element.getType() == 'LoopTerminator':
                elementNode.set('name', element.loop.params['name'].val)
            elif element.getType() == 'Routine':
                elementNode.set('name', '%s' %element.params['name'])
        #write to disk
        f=open(filename, 'wb')
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
        if hasattr(param,'val'): thisChild.set('val',str(param.val))
        if hasattr(param,'valType'): thisChild.set('valType',param.valType)
        if hasattr(param,'updates'): thisChild.set('updates',str(param.updates))
        return thisChild
    def _getXMLparam(self,params,paramNode):
        """params is the dict of params of the builder component (e.g. stimulus) into which
        the parameters will be inserted (so the object to store the params should be created first)
        paramNode is the parameter node fetched from the xml file
        """
        name=paramNode.get('name')
        if name=='times':#handle this parameter, deprecated in v1.60.00
            exec('times=%s' %paramNode.get('val'))
            params['startTime'].val =str(times[0])
            params['duration'].val = str(times[1]-times[0])
            return #times doesn't need to update its type or 'updates' rule
        elif name=='correctIf':#handle this parameter, deprecated in v1.60.00
            corrIf=paramNode.get('val')
            corrAns=corrIf.replace('resp.keys==str(','').replace(')','')
            params['correctAns'].val=corrAns
            name='correctAns'#then we can fetch thte other aspects correctly below
        elif 'val' in paramNode.keys(): params[name].val = paramNode.get('val')
        #get the value type and update rate
        if 'valType' in paramNode.keys(): 
            params[name].valType = paramNode.get('valType')
            # compatibility checks: 
            if name in ['correctAns','allowedKeys','text'] and paramNode.get('valType')=='code':
                params[name].valType='str'# these components were changed in v1.60.01
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
        self._doc=etree.XML(f.read(),parser)
        f.close()
        root=self._doc#.getroot()
        
        self.psychopyVersion = root.get('version')
        #todo: some error checking on the version (or report that this isn't .psyexp)?
        #Parse document nodes
        #first make sure we're empty
        self.flow = Flow(exp=self)#every exp has exactly one flow
        self.routines={}
        #fetch exp settings
        settingsNode=root.find('Settings')
        for child in settingsNode:
            self._getXMLparam(params=self.settings.params, paramNode=child)
        #fetch routines
        routinesNode=root.find('Routines')
        for routineNode in routinesNode:#get each routine node from the list of routines
            routine = Routine(name=routineNode.get('name'), exp=self)
            #self._getXMLparam(params=routine.params, paramNode=routineNode)
            #then create the
            self.routines[routineNode.get('name')]=routine
            for componentNode in routineNode:
                componentType=componentNode.tag
                componentName=componentNode.get('name')
                #create an actual component of that type
                component=getAllComponents()[componentType](\
                    name=componentName,
                    parentName=routineNode.get('name'), exp=self)
                #populate the component with its various params
                for paramNode in componentNode:
                    self._getXMLparam(params=component.params, paramNode=paramNode)
                routine.append(component)
        #fetch flow settings
        flowNode=root.find('Flow')
        loops={}
        for elementNode in flowNode:
            if elementNode.tag=="LoopInitiator":
                loopType=elementNode.get('loopType')
                loopName=elementNode.get('name')
                exec('loop=%s(exp=self,name="%s")' %(loopType,loopName))
                loops[loopName]=loop
                for paramNode in elementNode:
                    self._getXMLparam(paramNode=paramNode,params=loop.params)
                    #for trialList convert string rep to actual list of dicts
                    if paramNode.get('name')=='trialList':
                        param=loop.params['trialList']
                        exec('param.val=%s' %(param.val))#e.g. param.val=[{'ori':0},{'ori':3}]
                self.flow.append(LoopInitiator(loop=loops[loopName]))
            elif elementNode.tag=="LoopTerminator":
                self.flow.append(LoopTerminator(loop=loops[elementNode.get('name')]))
            elif elementNode.tag=="Routine":
                self.flow.append(self.routines[elementNode.get('name')])
                
    def setExpName(self, name):
        self.name=name
        self.settings.expName=name

class Param:
    """Defines parameters for Experiment Components
    A string representation of the parameter will depend on the valType:

    >>> sizeParam = Param(val=[3,4], valType='num')
    >>> print sizeParam
    numpy.asarray([3,4])

    >>> sizeParam = Param(val=[3,4], valType='str')
    >>> print sizeParam
    "[3,4]"

    >>> sizeParam = Param(val=[3,4], valType='code')
    >>> print sizeParam
    [3,4]

    """
    def __init__(self, val, valType, allowedVals=[],allowedTypes=[], hint="", updates=None, allowedUpdates=None):
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
        self.val=val
        self.valType=valType
        self.allowedTypes=allowedTypes
        self.hint=hint
        self.updates=updates
        self.allowedUpdates=allowedUpdates
        self.allowedVals=allowedVals
    def __str__(self):
        if self.valType == 'num':
            try:
                return str(float(self.val))#will work if it can be represented as a float
            except:#might be an array
                return "asarray(%s)" %(self.val)
        elif self.valType == 'str':
            if (type(self.val) in [str, unicode]) and self.val.startswith("$"):
                return "%s" %(self.val[1:])#override the string type and return as code
            else:
                return repr(self.val)#this neatly handles like "it's" and 'He says "hello"'
        elif self.valType == 'code':
            if (type(self.val) in [str, unicode]) and self.val.startswith("$"):
                return "%s" %(self.val[1:])#a $ in a code parameter is unecessary so remove it
            else: return "%s" %(self.val)
        elif self.valType == 'bool':
            return "%s" %(self.val)
        else:
            raise TypeError, "Can't represent a Param of type %s" %self.valType

class TrialHandler:
    """A looping experimental control object
            (e.g. generating a psychopy TrialHandler or StairHandler).
            """
    def __init__(self, exp, name, loopType='random', nReps=5,
        trialList=[], trialListFile='',endPoints=[0,1]):
        """
        @param name: name of the loop e.g. trials
        @type name: string
        @param loopType:
        @type loopType: string ('rand', 'seq')
        @param nReps: number of reps (for all trial types)
        @type nReps:int
        @param trialList: list of different trial conditions to be used
        @type trialList: list (of dicts?)
        @param trialListFile: filename of the .csv file that contains trialList info
        @type trialList: string (filename)
        """
        self.type='TrialHandler'
        self.exp=exp
        self.order=['name']#make name come first (others don't matter)
        self.params={}
        self.params['name']=Param(name, valType='code', updates=None, allowedUpdates=None,
            hint="Name of this loop")
        self.params['nReps']=Param(nReps, valType='num', updates=None, allowedUpdates=None,
            hint="Number of repeats (for each type of trial)")
        self.params['trialList']=Param(trialList, valType='str', updates=None, allowedUpdates=None,
            hint="A list of dictionaries describing the differences between each trial type")
        self.params['trialListFile']=Param(trialListFile, valType='str', updates=None, allowedUpdates=None,
            hint="A comma-separated-value (.csv) file specifying the parameters for each trial")
        self.params['endPoints']=Param(endPoints, valType='num', updates=None, allowedUpdates=None,
            hint="The start and end of the loop (see flow timeline)")
        self.params['loopType']=Param(loopType, valType='str', allowedVals=['random','sequential','staircase'],
            hint="How should the next trial value(s) be chosen?")#NB staircase is added for the sake of the loop properties dialog
        #these two are really just for making the dialog easier (they won't be used to generate code)
        self.params['endPoints']=Param(endPoints,valType='num',
            hint='Where to loop from and to (see values currently shown in the flow view)')
    def writeInitCode(self,buff):
        #todo: write code to fetch trialList from file?
        #create nice line-separated list of trialTypes
        if self.params['trialList'].val==None:
            trialStr="[None]"
        else:
            trialStr="[ \\\n"
            for line in self.params['trialList'].val:
                trialStr += "        %s,\n" %line
            trialStr += "        ]"
        #also a 'thisName' for use in "for thisTrial in trials:"
        self.thisName = ("this"+self.params['name'].val.capitalize()[:-1])
        #write the code
        buff.writeIndented("\n#set up handler to look after randomisation of trials etc\n")
        buff.writeIndented("%s=data.TrialHandler(nReps=%s, method=%s, extraInfo=expInfo, trialList=%s)\n" \
            %(self.params['name'], self.params['nReps'], self.params['loopType'], trialStr))
        buff.writeIndented("%s=%s.trialList[0]#so we can initialise stimuli with first trial values\n" %(self.thisName, self.params['name']))

    def writeLoopStartCode(self,buff):
        #work out a name for e.g. thisTrial in trials:
        buff.writeIndented("\n")
        buff.writeIndented("for %s in %s:\n" %(self.thisName, self.params['name']))
        buff.setIndentLevel(1, relative=True)
    def writeLoopEndCode(self,buff):
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("\n")
        buff.writeIndented("#completed %s repeats of '%s' repeats\n" \
            %(self.params['nReps'], self.params['name']))
        buff.writeIndented("\n")

        #save data
        ##a string to show all the available variables (if the trialList isn't just None or [None])
        stimOutStr="["
        if self.params['trialList'].val not in [None, [None]]:
            for variable in self.params['trialList'].val[0].keys():#get the keys for the first trialType
                stimOutStr+= "'%s', " %variable
        stimOutStr+= "]"
        buff.writeIndented("%(name)s.saveAsPickle(filename)\n" %self.params)
        buff.writeIndented("%(name)s.saveAsText(filename+'.dlm',\n" %self.params)
        buff.writeIndented("    stimOut=%s,\n" %stimOutStr)
        buff.writeIndented("    dataOut=['n','all_mean','all_std', 'all_raw'])\n")
        buff.writeIndented("psychopy.log.info('saved data to '+filename+'.dlm')\n" %self.params)

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
        @param nReps: number of reps (for all trial types)
        @type nReps:int
        """
        self.type='StairHandler'
        self.exp=exp
        self.order=['name']#make name come first (others don't matter)
        self.params={}
        self.params['name']=Param(name, valType='code', hint="Name of this loop")
        self.params['nReps']=Param(nReps, valType='num',
            hint="(Minimum) number of trials in the staircase")
        self.params['start value']=Param(startVal, valType='num',
            hint="The initial value of the parameter")
        self.params['max value']=Param(maxVal, valType='num',
            hint="The maximum value the parameter can take")
        self.params['min value']=Param(minVal, valType='num',
            hint="The minimum value the parameter can take")
        self.params['step sizes']=Param(stepSizes, valType='num',
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
        self.params['loopType']=Param('staircase', valType='str', allowedVals=['random','sequential','staircase'],
            hint="How should the next trial value(s) be chosen?")#NB this is added for the sake of the loop properties dialog
        self.params['endPoints']=Param(endPoints,valType='num',
            hint='Where to loop from and to (see values currently shown in the flow view)')

    def writeInitCode(self,buff):

        #also a 'thisName' for use in "for thisTrial in trials:"
        self.thisName = ("this"+self.params['name'].val.capitalize()[:-1])
        #write the code
        if self.params['N reversals'].val in ["", None, 'None']:
            self.params['N reversals'].val='0' 
        buff.writeIndented("\n#set up handler to look after randomisation of trials etc\n")
        buff.writeIndented("%(name)s=data.StairHandler(startVal=%(start value)s, extraInfo=expInfo,\n" %(self.params))
        buff.writeIndented("    stepSizes=%(step sizes)s, stepType=%(step type)s,\n" %self.params)
        buff.writeIndented("    nReversals=%(N reversals)s, nTrials=%(nReps)s, \n" %self.params)
        buff.writeIndented("    nUp=%(N up)s, nDown=%(N down)s)\n" %self.params)
    def writeLoopStartCode(self,buff):
        #work out a name for e.g. thisTrial in trials:
        buff.writeIndented("\n")
        buff.writeIndented("for %s in %s:\n" %(self.thisName, self.params['name']))
        buff.setIndentLevel(1, relative=True)
    def writeLoopEndCode(self,buff):
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("\n")
        buff.writeIndented("#staircase completed\n")
        buff.writeIndented("\n")
        #save data
        buff.writeIndented("%(name)s.saveAsText(filename+'.dlm')\n" %self.params)
        buff.writeIndented("%(name)s.saveAsPickle(filename)\n" %self.params)
        buff.writeIndented("psychopy.log.info('saved data to '+filename+'.dlm')\n" %self.params)
    def getType(self):
        return 'StairHandler'

class LoopInitiator:
    """A simple class for inserting into the flow.
    This is created automatically when the loop is created"""
    def __init__(self, loop):
        self.loop=loop
        self.exp=loop.exp
    def writeInitCode(self,buff):
        self.loop.writeInitCode(buff)
    def writeMainCode(self,buff):
        self.loop.writeLoopStartCode(buff)
        self.exp.flow._loopList.append(self.loop)#we are now the inner-most loop
    def getType(self):
        return 'LoopInitiator'
class LoopTerminator:
    """A simple class for inserting into the flow.
    This is created automatically when the loop is created"""
    def __init__(self, loop):
        self.loop=loop
        self.exp=loop.exp
    def writeInitCode(self,buff):
        pass
    def writeMainCode(self,buff):
        self.loop.writeLoopEndCode(buff)
        self.exp.flow._loopList.remove(self.loop)# _loopList[-1] will now be the inner-most loop
    def getType(self):
        return 'LoopTerminator'
class Flow(list):
    """The flow of the experiment is a list of L{Routine}s, L{LoopInitiator}s and
    L{LoopTerminator}s, that will define the order in which events occur
    """
    def __init__(self, exp):
        list.__init__(self)
        self.exp=exp
        self._currentRoutine=None
        self._loopList=[]#will be used while we write the code
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
        if component.getType() in ['StairHandler', 'TrialHandler']:
            #we need to remove the termination points that correspond to the loop
            for comp in self:
                if comp.getType() in ['LoopInitiator','LoopTerminator']:
                    if comp.loop==component: self.remove(comp)
        elif component.getType()=='Routine':
            if id==None: 
                #if the user removes an entire Routine we need to remove all antries in the Flow
                #self.remove(component)#cant do this - two empty routines (with diff names) look the same to list comparison
                for id, compToDel in enumerate(self):
                    if component.name==compToDel.name: del self[id]
            else: del self[id]#just delete the single entry we were given (e.g. from right-click in GUI)

    def writeCode(self, s):

        #initialise
        for entry in self: #NB each entry is a routine or LoopInitiator/Terminator
            self._currentRoutine=entry
            entry.writeInitCode(s)

        #run-time code
        for entry in self:
            self._currentRoutine=entry
            entry.writeMainCode(s)

class Routine(list):
    """
    A Routine determines a single sequence of events, such
    as the presentation of trial. Multiple Routines might be
    used to comprise an Experiment (e.g. one for presenting
    instructions, one for trials, one for debriefing subjects).

    In practice a Routine is simply a python list of Components,
    each of which knows when it starts and stops.
    """
    def __init__(self, name, exp):
        self.params={'name':name}
        self.name=name
        self.exp=exp
        self._continueName=''#this is used for script-writing e.g. "while continueTrial:"
        self._clockName=None#this is used for script-writing e.g. "t=trialClock.GetTime()"
        list.__init__(self)
    def addComponent(self,component):
        """Add a component to the end of the routine"""
        self.append(component)
    def removeComponent(self,component):
        """Remove a component from the end of the routine"""
        self.remove(component)
    def writeInitCode(self,buff):
        buff.writeIndented('\n')
        buff.writeIndented('#Initialise components for routine:%s\n' %(self.name))
        self._clockName = self.name+"Clock"
        self._continueName = "continue%s" %self.name.capitalize()
        buff.writeIndented('%s=core.Clock()\n' %(self._clockName))
        for thisEvt in self:
            thisEvt.writeInitCode(buff)

    def writeMainCode(self,buff):
        """This defines the code for the frames of a single routine
        """
        #This is the beginning of the routine, before the loop starts
        for event in self:
            event.writeRoutineStartCode(buff)

        #create the frame loop for this routine
        buff.writeIndented('\n')
        buff.writeIndented('#run the trial\n')
        buff.writeIndented('%s=True\n' %self._continueName)
        buff.writeIndented('t=0; %s.reset()\n' %(self._clockName))
        buff.writeIndented('while %s and (t<%.4f):\n' %(self._continueName, self.getMaxTime()))
        buff.setIndentLevel(1,True)

        #on each frame
        buff.writeIndented('#get current time\n')
        buff.writeIndented('t=%s.getTime()\n\n' %self._clockName)

        #write the code for each component during frame
        buff.writeIndented('#update each component (where necess)\n')
        for event in self:
            event.writeFrameCode(buff)

        #update screen
        buff.writeIndented('\n')
        buff.writeIndented('#check for quit (the [Esc] key)\n')
        buff.writeIndented('if event.getKeys("escape"): core.quit()\n')
        buff.writeIndented("event.clearEvents()#so that it doesn't get clogged with other events\n")
        buff.writeIndented('#refresh the screen\n')
        buff.writeIndented('win.flip()\n')

        #that's done decrement indent to end loop
        buff.setIndentLevel(-1,True)

        #write the code for each component for the end of the routine
        buff.writeIndented('\n')
        buff.writeIndented('#end of this routine (e.g. trial)\n')
        for event in self:
            event.writeRoutineEndCode(buff)

    def getType(self):
        return 'Routine'
    def getComponentFromName(self, name):
        for comp in self:
            if comp.params['name']==name:
                return comp
        return None
    def getMaxTime(self):
        maxTime=0
        times=[]
        for event in self:
            if event.params['duration'].val in ['-1', '']: maxTime=1000000
            else:
                exec("maxTime=%s" %event.params['duration'])#convert params['duration'].val into numeric
            times.append(maxTime)
            maxTime=float(max(times))
        return maxTime
    
def _XMLremoveWhitespaceNodes(parent):
    """Remove all text nodes from an xml document (likely to be whitespace)
    """
    for child in list(parent.childNodes):
        if child.nodeType==node.TEXT_NODE and node.data.strip()=='':
            parent.removeChild(child)
        else:
            removeWhitespaceNodes(child)
