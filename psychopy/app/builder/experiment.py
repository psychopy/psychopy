import StringIO, sys
from components import *#getComponents('') and getAllComponents([])

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
        self.flow = Flow()
        self.routines={}
        #this can be checked by the builder that this is an experiment and a compatible version
        self.psychopyExperimentVersion='0.1' 
    def addRoutine(self,routineName, routine=None):
        """Add a Routine to the current list of them. 
        
        Can take a Routine object directly or will create
        an empty one if none is given.
        """
        if routine==None:
            self.routines[routineName]=Routine(routineName)#create a deafult routine with this name
        else:
            self.routines[routineName]=routine
        
    def writeScript(self):
        """Write a PsychoPy script for the experiment
        """
        s=IndentingBuffer(u'') #a string buffer object
        s.writeIndented('"""This experiment was created using PsychoPy2 (Experiment Builder) and will\n \
run on any platform on which PsychoPy can be installed\n \
\nIf you publish work using this script please cite the relevant papers (e.g. Peirce, 2007;2009)"""\n\n')
        
        #delegate most of the code-writing to Flow
        self.flow.writeCode(s)
        
        return s
    def getAllObjectNames(self):
        """Return the names of all objects (routines, loops and components) in the experiment
        """
        names=[]
        for thisRoutine in self.routines:
            names.append(thisRoutine.name)
            for thisEntry in thisRoutine: 
                if isinstance(thisEntry, LoopInitiator):
                    names.append( thisEntry.loop.name )
                    print 'found loop initiator: %s' %names[-1]
                elif hasattr(thisEntry, 'params'):
                    names.append(thisEntry.params['name'])
                    print 'found component: %s' %names[-1]
                    

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
        @param updates: how often does this parameter update ('experiment', 'routine', 'frame')
        @type updates: string
        @param allowedUpdates: conceivable updates for this param [None, 'routine', 'frame']
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
                return "numpy.asarray(%s)" %(self.val)
        elif self.valType == 'str':
            return repr(self.val)#this neatly handles like "it's" and 'He says "hello"'
        elif self.valType == 'code':
            return "%s" %(self.val)
        else:
            raise TypeError, "Can't represent a Param of type %s" %self.valType
            
class TrialHandler():    
    """A looping experimental control object
            (e.g. generating a psychopy TrialHandler or StairHandler).
            """
    def __init__(self, name, loopType, nReps, 
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
        #todo: need to write code to fetch trialList from file!
        buff.writeIndented("%s=data.TrialHandler(trialList=%s,nReps=%s)\n" \
            %(self.params['name'], self.params['trialList'], self.params['nReps']))
    def writeLoopStartCode(self,buff):
        #work out a name for e.g. thisTrial in trials:
        self.thisName = ("this"+self.params['name'].val.capitalize()[:-1])
        buff.writeIndented("\n")
        buff.writeIndented("for %s in %s:\n" %(self.thisName, self.params['name']))
        buff.setIndentLevel(1, relative=True)
    def writeLoopEndCode(self,buff):
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("# end of '%s' after %s repeats (of each entry in trialList)\n" %(self.params['name'], self.params['nReps']))
    def getType(self):
        return 'TrialHandler'     
class StairHandler():    
    """A staircase experimental control object.
    """
    def __init__(self, name, nReps, nReversals, stepSizes, stepType, startVal, endPoints=[0,1]):
        """
        @param name: name of the loop e.g. trials
        @type name: string
        @param nReps: number of reps (for all trial types)
        @type nReps:int
        """
        self.type='StairHandler'
        self.order=['name']#make name come first (others don't matter)
        self.params={}
        self.params['name']=Param(name, valType='code', hint="Name of this loop")
        self.params['nReps']=Param(nReps, valType='num', 
            hint="(Minimum) number of trials in the staircase")
        self.params['start value']=Param(startVal, valType='num', 
            hint="The size of the jump at each step (can change on each 'reversal')")
        self.params['step sizes']=Param(stepSizes, valType='num', allowedVals=['lin','log','db'],
            hint="The size of the jump at each step (can change on each 'reversal')")
        self.params['step type']=Param(stepType, valType='str', 
            hint="The units of the step size (e.g. 'linear' will add/subtract that value each step, whereas 'log' will ad that many log units)")
        self.params['nReversals']=Param(nReversals, valType='code', 
            hint="Minimum number of times the staircase must change direction before ending")
        #these two are really just for making the dialog easier (they won't be used to generate code)
        self.params['loopType']=Param('staircase', valType='str', allowedVals=['random','sequential','staircase'],
            hint="How should the next trial value(s) be chosen?")#NB this is added for the sake of the loop properties dialog
        self.params['endPoints']=Param(endPoints,valType='num',
            hint='Where to loop from and to (see values currently shown in the flow view)')
    def writeInitCode(self,buff):
        #TODO: code for stair handler init!
        buff.writeIndented("init loop '%s' (%s)\n" %(self.params['name'], self.loopType))
        buff.writeIndented("%s=data.StairHandler(nReps=%i,\n)" \
            %(self.name, self.nReps))
    def writeLoopStartCode(self,buff):
        #work out a name for e.g. thisTrial in trials:
        thisName = ("this"+self.params['name'].capitalize()[:-1])
        buff.writeIndented("for %s in %s:\n" %(thisName, self.params['name']))
        buff.setIndentLevel(1, relative=True)
    def writeLoopEndCode(self,buff):
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("# end of '%s' after %i repeats (of each entry in trialList)\n" %(self.loop.params['name'], self.loop.params['nReps']))
    def getType(self):
        return 'StairHandler'   
class LoopInitiator:
    """A simple class for inserting into the flow.
    This is created automatically when the loop is created"""
    def __init__(self, loop):
        self.loop=loop        
    def writeInitCode(self,buff):
        self.loop.writeInitCode(buff)
    def writeMainCode(self,buff):
        self.loop.writeLoopStartCode(buff)       
    def getType(self):
        return 'LoopInitiator'
class LoopTerminator:
    """A simple class for inserting into the flow.
    This is created automatically when the loop is created"""
    def __init__(self, loop):
        self.loop=loop
    def writeInitCode(self,buff):
        pass
    def writeMainCode(self,buff):
        self.loop.writeLoopEndCode(buff)
    def getType(self):
        return 'LoopTerminator'
class Flow(list):
    """The flow of the experiment is a list of L{Routine}s, L{LoopInitiator}s and
    L{LoopTerminator}s, that will define the order in which events occur
    """
    def addLoop(self, loop, startPos, endPos):
        """Adds initiator and terminator objects for the loop
        into the Flow list"""
        self.insert(int(endPos), LoopTerminator(loop))
        self.insert(int(startPos), LoopInitiator(loop))
    def addRoutine(self, newRoutine, pos):
        """Adds the routine to the Flow list"""
        self.insert(int(pos), newRoutine)
        
    def writeCode(self, s):
        s.writeIndented("from PsychoPy import visual, core, event, sound\n")
        s.writeIndented("win = visual.Window([400,400])\n")
        
        #initialise components
        for entry in self:
            entry.writeInitCode(s)
        
        #run-time code  
        for entry in self:
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
    def __init__(self, name):
        self.name=name
        list.__init__(self)
    def writeInitCode(self,buff):
        buff.writeIndented('\n')
        buff.writeIndented('#Initialise components for routine:%s\n' %(self.name))
        self.clockName = self.name+"Clock"
        buff.writeIndented('%s=core.Clock()\n' %(self.clockName))
        for thisEvt in self:
            thisEvt.writeInitCode(buff)
        
    def writeMainCode(self,buff):
        """This defines the code for the frames of a single routine
        """
        #create the frame loop for this routine
        buff.writeIndented('t=0\n')
        buff.writeIndented('%s.reset()\n' %(self.clockName))
        buff.writeIndented('while t<maxTime:\n')
        buff.setIndentLevel(1,True)
        
        #on each frame
        buff.writeIndented('#get current time\n')
        buff.writeIndented('t=%s.getTime()\n\n' %self.clockName)
        
        #write the code for each component during frame
        for event in self:
            event.writeFrameCode(buff)
            
        #update screen
        buff.writeIndented('\n')
        buff.writeIndented('#refresh the screen\n')
        buff.writeIndented('win.flip()\n')
        
        #that's done decrement indent to end loop
        buff.setIndentLevel(-1,True)
    def getType(self):
        return 'Routine'
    def getComponentFromName(self, name):
        for comp in self:
            if comp.params['name']==name:
                return comp
        return None
    
