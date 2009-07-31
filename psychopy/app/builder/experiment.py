import StringIO, sys

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
run on any platform on which PsychoPy (www.psychopy.org) can be installed\n \
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
        buff.writeIndented("# end of '%s' after %i repeats (of each entry in trialList)\n" %(self.loop.params['name'], self.loop.params['nReps']))
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
        self.loop.writeLoopStartCode(buff)
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
    
class BaseComponent:
    """A general template for components"""
    def __init__(self, parentName, name='', times=[0,1]):
        self.type='Base'
        self.params={}
        self.params['name']=Param(name, valType='code', 
            hint="Name of this loop")
        self.order=['name']#make name come first (others don't matter)
    def writeInitCode(self,buff):
        pass
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        pass
    def writeRoutineStartCode(self,buff):
        """Write the code that will be called at the beginning of 
        a routine (e.g. to update stimulus parameters)
        """
        self.writeParamUpdates(buff, 'routine')
    def writeRoutineEndCode(self,buff):
        """Write the code that will be called at the end of 
        a routine (e.g. to save data)
        """
        pass
    def writeTimeTestCode(self, buff):
        """Write the code for each frame that tests whether the component is being
        drawn/used.
        """
        exec("times=%s" %self.params['times'].val)
        if type(times[0]) in [int, float]:
            times=[times]#make a list of lists
        print times
        #write the code for the first repeat of the stimulus
        buff.writeIndented("if (%.f <= t < %.f)" %(times[0][0], times[0][1]))
        if len(times)>1:
            for epoch in times[1:]: 
                buff.write("\n")
                buff.writeIndented("    or (%.f <= t < %.f)" %(epoch[0], epoch[1]))
        buff.write(':\n')#the condition is done add the : and new line to finish        
    def writeParamUpdates(self, buff, updateType):
        """write updates to the buffer for each parameter that needs it
        updateType can be 'experiment', 'routine' or 'frame'
        """
        for thisParamName in self.params.keys():
            thisParam=self.params[thisParamName]
            if thisParam.updates=='frame':
                buff.writeIndented("%s.set%s(%s)\n" %(self.params['name'], thisParamName.capitalize(), thisParam) )
    

class VisualComponent(BaseComponent):
    """Base class for most visual stimuli
    """
    def __init__(self, parentName, name='', units='window units', colour=[1,1,1],
        pos=[0,0], size=[0,0], ori=0, times=[0,1], colourSpace='rgb'):
        self.order=['name']#make name come first (others don't matter)
        self.params={}
        self.params['name']=Param(name,  valType='code', updates="never", 
            hint="Name of this stimulus")
        self.params['units']=Param(units, valType='str', allowedVals=['window units', 'deg', 'cm', 'pix', 'norm'],
            hint="Units of dimensions for this stimulus")
        self.params['colour']=Param(colour, valType='num', allowedTypes=['num','str','code'],
            updates="never", allowedUpdates=["never","routine","frame"],
            hint="Colour of this stimulus (e.g. [1,1,0], 'red' )")
        self.params['colourSpace']=Param(colourSpace, valType='str', allowedVals=['rgb','dkl','lms'],
            hint="Choice of colour space for the colour (rgb, dkl, lms)")
        self.params['pos']=Param(pos, valType='num', allowedTypes=['num','code'],
            updates="never", allowedUpdates=["never","routine","frame"],
            hint="Position of this stimulus (e.g. [1,2] ")
        self.params['size']=Param(size, valType='num', allowedTypes=['num','code'],
            updates="never", allowedUpdates=["never","routine","frame"],
            hint="Size of this stimulus (either a single value or x,y pair, e.g. 2.5, [1,2] ")
        self.params['ori']=Param(ori, valType='num', allowedTypes=['num','code'],
            updates="never", allowedUpdates=["never","routine","frame"],
            hint="Orientation of this stimulus (in deg)")
        self.params['times']=Param(times, valType='code', allowedTypes=['code'],
            updates="never", allowedUpdates=["never"],
            hint="Start and end times for this stimulus (e.g. [0,1] or [[0,1],[2,3]] for a repeated appearance")
            
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """    
        self.writeTimeTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.setIndentLevel(1, relative=True)#because of the 'if' statement of the times test
        #set parameters that need updating every frame
        self.writeParamUpdates(buff, 'frame')
        #draw the stimulus
        buff.writeIndented("%(name)s.draw()\n" %(self.params))
        buff.setIndentLevel(-1, relative=True)

class TextComponent(VisualComponent):
    """An event class for presenting image-based stimuli"""
    def __init__(self, parentName, name='', text='', font='arial',
        units='window units', colour=[1,1,1], colourSpace='rgb',
        pos=[0,0], size=[0,0], ori=0, times=[0,1]):
        #initialise main parameters from base stimulus
        VisualComponent.__init__(self,parentName,name=name, units=units, 
                    colour=colour, colourSpace=colourSpace,
                    pos=pos, size=size, ori=ori, times=times)
        self.type='Text'
        self.params['text']=Param(text, valType='str', allowedTypes=['str','code'],
            updates="never", allowedUpdates=["never","routine","frame"],
            hint="The text to be displayed")
        self.params['font']=Param(font, valType='str', allowedTypes=['str','code'],
            updates="never", allowedUpdates=["never","routine","frame"],
            hint="The font name, or a list of names, e.g. ['arial','verdana']")
        #change the hint for size
        self.params['size'].hint="Specifies the height of the letter (the width is then determined by the font)"
    def writeInitCode(self,buff):
        s = "%s=TextStim(win=win, pos=%s, size=%s" %(self.params['name'], self.params['pos'],self.params['size'])
        buff.writeIndented(s)   
        
        buff.writeIndented(")\n")
        
class PatchComponent(VisualComponent):
    """An event class for presenting image-based stimuli"""
    def __init__(self, parentName, name='', image='sin', mask='none', sf=1, interpolate='linear',
        units='window units', colour=[1,1,1], colourSpace='rgb',
        pos=[0,0], size=[0,0], ori=0, times=[0,1]):
        #initialise main parameters from base stimulus
        VisualComponent.__init__(self,parentName,name=name, units=units, 
                    colour=colour, colourSpace=colourSpace,
                    pos=pos, size=size, ori=ori, times=times)
                        
        self.type='Patch'
        self.params['image']=Param(image, valType='str', allowedTypes=['str','code'],
            updates="never", allowedUpdates=["never","routine","frame"],
            hint="The image to be displayed - 'sin','sqr'... or a filename (including path)")        
        self.params['mask']=Param(mask, valType='str', allowedTypes=['str','code'],
            updates="never", allowedUpdates=["never","routine","frame"],
            hint="An image to define the alpha mask (ie shape)- 'gauss','circle'... or a filename (including path)")        
        self.params['sf']=Param(sf, valType='num', allowedTypes=['num','code'],
            updates="never", allowedUpdates=["never","routine","frame"],
            hint="Spatial frequency of image repeats across the patch, e.g. 4 or [2,3]")        
        self.params['interpolate']=Param(mask, valType='str', allowedVals=['linear','nearest'],
            updates="never", allowedUpdates=["never"],
            hint="How should the image be interpolated if/when rescaled")
                
    def writeInitCode(self,buff):
        buff.writeIndented("%(name)s=PatchStim(win=win, tex=%(image)s, mask=%(mask)s,\n" %(self.params))
        buff.writeIndented("    pos=%(pos)s, size=%(size)s)\n" %(self.params) )

class MovieComponent(VisualComponent):
    """An event class for presenting image-based stimuli"""
    def __init__(self, parentName, name='', movie='', 
        units='window units', 
        pos=[0,0], size=[0,0], ori=0, times=[0,1]):
        #initialise main parameters from base stimulus
        VisualComponent.__init__(self,parentName,name=name, units=units, 
                    pos=pos, size=size, ori=ori, times=times)
        #these are normally added but we don't want them for a movie            
        del self.params['colour']
        del self.params['colourSpace']
        self.type='Movie'
        self.params['movie']=Param(movie, valType='str', allowedTypes=['str','code'],
            updates="never", allowedUpdates=["never","routine"],
            hint="A filename for the movie (including path)")        
                
    def writeInitCode(self,buff):
        buff.writeIndented("%(name)s=MovieStim(win=win, movie=%(movie)s,\n" %(self.params))
        buff.writeIndented("    ori=%(ori)s, pos=%(pos)s, size=%(size)s)\n" %(self.params))
        
class SoundComponent(BaseComponent):
    """An event class for presenting image-based stimuli"""
    def __init__(self, parentName, name='', sound='A', 
            size=1, ori=0, times=[0,1]):
        self.order=['name']#make sure name comes first
        self.type='Sound'
        self.params={}
        self.params['name']=Param(name,  valType='code', hint="A filename for the movie (including path)")  
        self.params['sound']=Param(sound, valType='str', allowedTypes=['str','num','code'],
            updates="never", allowedUpdates=["never","routine"],
            hint="A sound can be a string (e.g. 'A' or 'Bf') or a number to specify Hz, or a filename")  
        self.params['times']=Param(times, valType='code', allowedTypes=['code'],
            updates="never", allowedUpdates=["never"],
            hint="A series of one or more onset/offset times, e.g. [2.0,2.5] or [[2.0,2.5],[3.0,3.8]]")  

    def writeInitCode(self,buff):
        s = "%(name)s=Sound(%(sound)s, secs=%s\n" %(self.params,self.params['times'][1]-self.params['times'][0])
        buff.writeIndented(s)  
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        self.writeTimeTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.setIndentLevel(1, relative=True)#because of the 'if' statement of the times test
        #set parameters that need updating every frame
        self.writeParamUpdates(buff, 'frame')
        buff.writeIndented("%s.play()\n" %(self.params['name'])) 
        buff.setIndentLevel(-1, relative=True)#because of the 'if' statement of the times test
            
class KeyboardComponent(BaseComponent):
    """An event class for checking the keyboard at given times"""
    def __init__(self, parentName, name='', allowedKeys='q,left,right',storeWhat='first key',
            forceEndTrial=True,storeCorrect=False,correctIf="==thisTrial.corrAns",times=[0,1]):
        self.type='Keyboard'
        self.parentName=parentName
        self.params={}
        self.order=['name','allowedKeys',
            'storeWhat','storeCorrect','correctIf',
            'forceEndTrial','times']
        self.params['name']=Param(name,  valType='code', hint="A name for this keyboard object (e.g. response)")  
        self.params['allowedKeys']=Param(allowedKeys, valType='str', allowedTypes=['str','code'],
            updates="never", allowedUpdates=["never","routine"],
            hint="The keys the user may press, e.g. a,b,q,left,right")  
        self.params['times']=Param(times, valType='code', allowedTypes=['code'],
            updates="never", allowedUpdates=["never"],
            hint="A series of one or more periods to read the keyboard, e.g. [2.0,2.5] or [[2.0,2.5],[3.0,3.8]]")
        self.params['storeWhat']=Param(storeWhat, valType='str', allowedTypes=['str'],allowedVals=['first key', 'all keys'],
            updates="never", allowedUpdates=["never"],
            hint="Store a single key, or append to a list of all keys pressed during the routine")  
        self.params['forceEndTrial']=Param(forceEndTrial, valType='bool', allowedTypes=['bool'],
            updates="never", allowedUpdates=["never"],
            hint="Should the keypress force the end of the routine (e.g end the trial)?")
        self.params['storeCorrect']=Param(storeCorrect, valType='bool', allowedTypes=['bool'],
            updates="never", allowedUpdates=["never"],
            hint="Do you want to save the response as correct/incorrect?")
        self.params['correctIf']=Param(correctIf, valType='code', allowedTypes=['code'],
            updates="never", allowedUpdates=["never"],
            hint="Do you want to save the response as correct/incorrect? Might be helpful to add a corrAns column in the trialList")
    def writeInitCode(self,buff):
        pass#no need to initialise keyboards?
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        self.writeTimeTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.setIndentLevel(1, relative=True)#because of the 'if' statement of the times test
        #draw the stimulus
        buff.writeIndented("%(name)s = event.getKeys(allowed=%(allowedKeys)s)\n" %(self.params))
        buff.setIndentLevel(-1, relative=True)        
    def writeRoutineEndCode(buff):
        buff.writeIndented("%s.addData(%s)" %(self.parentName, self.params.name))
class MouseComponent(BaseComponent):
    """An event class for checking the mouse location and buttons at given times"""
    def __init__(self, parentName, name='mouse', times=[0,1], save='final'):
        self.type='Mouse'
        self.order = ['name']
        self.params={}
        self.params['name']=Param(name, valType='str', allowedTypes=['str','code'],
            hint="Even mice have names!") 
        self.params['times']=Param(times, valType='code', allowedTypes=['code'],
            updates="never", allowedUpdates=["never"],
            hint="A series of one or more periods to read the mouse, e.g. [2.0,2.5] or [[2.0,2.5],[3.0,3.8]]")
        self.params['save']=Param(save, valType='str', allowedVals=['final values','every frame'])
    def writeInitCode(self,buff):
        pass#no need to initialise?
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        self.writeTimeTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.setIndentLevel(1, relative=True)#because of the 'if' statement of the times test
        self.writeParamUpdates(buff, 'frame')
        buff.writeIndented("TODO: check mouse")
        buff.setIndentLevel(-1, relative=True)#because of the 'if' statement of the times test
        
                
