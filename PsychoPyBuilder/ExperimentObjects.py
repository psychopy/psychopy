import StringIO, sys

class LoopHandler(list):    
    """A looping experimental control object
            (e.g. generating a psychopy TrialHandler or StairHandler).
            """
    def __init__(self, name, loopType, nReps, trialList):
        """
        @param name: name of the loop e.g. trials
        @type name: string
        @param loopType:
        @type loopType: string ('rand', 'seq', 'stair'...)
        @param nReps: number of reps (for all trial types)
        @type nReps:int
        @param trialList: list of different trial conditions to be used
        @type trialList: list (of dicts?)
        """
        list.__init__(self)
        self.loopType=loopType
        self.name = name
        self.nReps=nReps
        self.trialList=trialList
    def generateInitCode(self,buff):
        buff.write("init loop '%s' (%s)\n" %(self.name, self.loopType))
        buff.write("%s=data.TrialHandler(trialList=%s,nReps=%i,\n)" \
            %(self.name, self.trialList, self.nReps))
    def generateRunCode(self,buff, indent):
        #work out a name for e.g. thisTrial in trials:
        thisName = ("this"+self.name.capitalize()[:-1])
        buff.write("for %s in %s:\n" %(thisName, self.name))
    def getType(self):
        return 'LoopHandler'        
class LoopInitiator:
    """A simple class for inserting into the flow.
    This is created automatically when the loop is created"""
    def __init__(self, loop):
        self.loop=loop        
    def generateInitCode(self,buff):
        self.loop.generateInitCode(buff)
    def generateRunCode(self,buff, indent):
        self.loop.generateRunCode(buff, indent)
    def getType(self):
        return 'LoopInitiator'
class LoopTerminator:
    """A simple class for inserting into the flow.
    This is created automatically when the loop is created"""
    def __init__(self, loop):
        self.loop=loop
    def generateInitCode(self,buff):
        pass
    def generateRunCode(self,buff, indent):
        #todo: dedent
        buff.write("# end of '%s' after %i repeats (of each entry in trialList)\n" %(self.loop.name, self.loop.nReps))
    def getType(self):
        return 'LoopTerminator'
class Flow(list):
    """The flow of the experiment is a list of L{Procedure}s, L{LoopInitiator}s and
    L{LoopTerminator}s, that will define the order in which events occur
    """
    def addLoop(self, loop, startPos, endPos):
        """Adds initiator and terminator objects for the loop
        into the Flow list"""
        self.insert(int(endPos), LoopTerminator(loop))
        self.insert(int(startPos), LoopInitiator(loop))
    def addProcedure(self, newProc, pos):
        """Adds the object to the Flow list"""
        self.insert(int(pos), newProc)
        
    def generateCode(self, s):
        s.write("from PsychoPy import visual, core, event, sound\n")
        s.write("win = visual.Window([400,400])\n")
        
        #initialise objects
        for entry in self:
            entry.generateInitCode(s)
        
        #run-time code       
        indentLevel = 0  
        for entry in self:
            #tell the object to write its code at given level
            if indentLevel==0:indent=""
            else: indent="    "*indentLevel#insert 4 spaces for each level

            entry.generateRunCode(s, indent)
            #if object was part of a loop then update level
            if isinstance(entry, LoopInitiator):
                indentLevel+=1
            if isinstance(entry, LoopTerminator):
                indentLevel-=1
        
class Procedure(list):
    """
    A Procedure determines a single sequence of events, such
    as the presentation of trial. Multiple Procedures might be
    used to comprise an Experiment (e.g. one for presenting
    instructions, one for trials, one for debriefing subjects).
    
    In practice a Procedure is simply a python list of Event objects,
    each of which knows when it starts and stops.
    """
    def __init__(self, name):
        self.name=name
        list.__init__(self)
    def generateInitCode(self,buff):
        buff.write('\n#Initialise objects for %s procedure\n' %self.name)
        for thisEvt in self:
            thisEvt.generateInitCode(buff)
    def generateRunCode(self,buff,indent):
        for event in self:
            event.generateRunCode(buff, indent)
    def getType(self):
        return 'Procedure'            
class EventBase:
    """A general template for event objects"""
    def __init__(self, name='', times=[0,1]):
        self.type='Base'
        self.params['name']=name
        self.hints['name']= 'A name for the object'
    def generateInitCode(self,buff):
        pass
    def generateRunCode(self,buff, indent):
        pass  
        
class EventText(EventBase):
    """An event class for presenting image-based stimuli"""
    def __init__(self, name='', text='', font='arial', 
        pos=[0,0], size=[0,0], ori=0, times=[0,1]):
        self.params={}
        self.type='Text'
        self.params['name']=name
        self.params['text']= text
        self.params['font']= font
        self.params['pos']=pos
        self.params['size']=size
        self.params['ori']=ori
        self.params['times']=times
        
        #params that can change in time
        self.changeable=['ori','pos','rgb','size']
        
        self.hints={}
        self.hints['name']="A name for the object"
        self.hints['text']="The text to be displayed"
        self.hints['font']= "The font name, or a list of names, e.g. ['arial','verdana']"
        self.hints['pos']= "Position of the text as [X,Y], e.g. [-2.5,3]"
        self.hints['size']= "Specifies the height of the letter (the width is then determined by the font)"
        self.hints['ori']= "The orientation of the text in degrees"
        self.hints['times']="A series of one or more onset/offset times, e.g. [2.0,2.5] or [[2.0,2.5],[3.0,3.8]]"
        
    def generateInitCode(self,buff):
        s = "%s=TextStim(win=win, pos=%s, size=%s" %(self['name'], self['pos'],self['size'])
        buff.write(s)   
        
        buff.write(")\n")
    def generateRunCode(self,buff, indent):
        buff.write("%sdrawing TextStim '%s'\n" %(indent, self['name']))
        
class EventPatch(EventBase):
    """An event class for presenting image-based stimuli"""
    def __init__(self, name='', image='sin', mask='none', pos=[0,0], 
            sf=1, size=1, ori=0, times=[0,1]):
        self.type='Patch'
        self.params={}
        self.hints={}
        self.params['name']=name
        self.params['mask']=mask
        self.params['image']= image
        self.params['pos']=pos
        self.params['size']=size
        self.params['sf']=sf
        self.params['ori']=ori
        self.params['times']=times
        
        self.hints['name']="A name for the object"
        self.hints['image']="The image to use (a filename or 'sin', 'sqr'...)"
        self.hints['mask']= "The image that defines the mask (a filename or 'gauss', 'circle'...)"
        self.hints['pos']= "Position of the image centre as [X,Y], e.g. [-2.5,3]"
        self.hints['size']= "Specifies the size of the stimulus (a single value or [w,h] )"
        self.hints['ori']= "The orientation of the stimulus in degrees"
        self.hints['sf']= "The spatial frequency of cycles of the image on the stimulus"
        self.hints['times']="A series of one or more onset/offset times, e.g. [2.0,2.5] or [[2.0,2.5],[3.0,3.8]]"
                
    def generateInitCode(self,buff):
        s = "%s=PatchStim(win=win, pos=%s, size=%s" %(self['name'], self['pos'],self['size'])
        buff.write(s)   
        
        buff.write(")\n")
    def generateRunCode(self,buff, indent):
        buff.write("%sdrawing PatchStim '%s'\n" %(indent, self['name']))
class EventMovie(EventBase):
    """An event class for presenting image-based stimuli"""
    def __init__(self, name='', movie='', pos=[0,0], 
            size=1, ori=0, times=[0,1]):
        
        self.type='Movie'
        self.params={}
        self.hints={}
        self.params['name']=name
        self.params['movie']= movie
        self.params['pos']=pos
        self.params['size']=size
        self.params['ori']=ori
        self.params['times']=times
        
        self.hints['name']="A name for the object"
        self.hints['image']="The image to use (a filename or 'sin', 'sqr'...)"
        self.hints['mask']= "The image that defines the mask (a filename or 'gauss', 'circle'...)"
        self.hints['pos']= "Position of the image centre as [X,Y], e.g. [-2.5,3]"
        self.hints['size']= "Specifies the size of the stimulus (a single value or [w,h] )"
        self.hints['ori']= "The orientation of the stimulus in degrees"
        self.hints['times']="A series of one or more onset/offset times, e.g. [2.0,2.5] or [[2.0,2.5],[3.0,3.8]]"
                
    def generateInitCode(self,buff):
        s = "%s=PatchStim(win=win, pos=%s, size=%s" %(self['name'], self['pos'],self['size'])
        buff.write(s)   
        
        buff.write(")\n")
    def generateRunCode(self,buff, indent):
        buff.write("%sdrawing MovieStim '%s'\n" %(indent, self['name']))
class EventSound(EventBase):
    """An event class for presenting image-based stimuli"""
    def __init__(self, name='', sound='', 
            size=1, ori=0, times=[0,1]):
        
        self.type='Sound'
        self.params={}
        self.hints={}
        self.params['name']=name
        self.params['sound']= ''
        self.params['times']=times
        
        self.hints['name']="A name for the object"
        self.hints['sound']="A sound can be a string (e.g. 'A' or 'Bf') or a number to specify Hz, or a filename"
        self.hints['times']="A series of one or more onset/offset times, e.g. [2.0,2.5] or [[2.0,2.5],[3.0,3.8]]"
                
    def generateInitCode(self,buff):
        s = "%s=Sound(win=win, pos=%s, size=%s" %(self['name'], self['pos'],self['size'])
        buff.write(s)   
        
        buff.write(")\n")
    def generateRunCode(self,buff, indent):
        buff.write("%splaying Sound '%s'\n" %(indent, self['name']))        
class EventKeyboard(EventBase):
    """An event class for checking the keyboard at given times"""
    def __init__(self, name='', allowedKeys='q,left,right',onTimes=[0,1]):
        self.type='Keyboard'
                
        self.params={}
        self.params['name']=name
        self.params['allowedKeys']=allowedKeys
        self.params['onTimes']=onTimes
        
        self.hints={}
        self.hints['name']=""
        self.hints['allowedKeys']="The keys that the user may press"
        self.hints['onTimes']="A series of one or more periods to read the keyboard, e.g. [2.0,2.5] or [[2.0,2.5],[3.0,3.8]]"
    def generateInitCode(self,buff):
        pass#no need to initialise keyboards?
    def generateRunCode(self,buff,indent):
        buff.write("%sChecking keys" %indent)

class EventMouse(EventBase):
    """An event class for checking the mouse location and buttons at given times"""
    def __init__(self, name='', onTimes=[0,1]):
        self.type='Mouse'
        self.params={}
        self.params['onTimes']=onTimes
        
        self.hints={}
        self.hints['onTimes']="A series of one or more periods to read the mouse, e.g. [2.0,2.5] or [[2.0,2.5],[3.0,3.8]]"
    def generateInitCode(self,buff):
        pass#no need to initialise?
    def generateRunCode(self,buff,indent):
        buff.write("%sChecking keys" %indent)
                
class Experiment:
    """
    An experiment contains a single Flow and at least one
    Procedure. The Flow controls how Procedures are organised
    e.g. the nature of repeats and branching of an experiment.
    """
    def __init__(self):
        self.flow = Flow()
        self.procs={}

    def addProcedure(self,procName, proc=None):
        """Add a Procedure to the current list of them. 
        
        Can take a Procedure object directly or will create
        an empty one if none is given.
        """
        if proc==None:
            self.procs[procName]=Procedure(procName)
        else:
            self.procs=proc
            
    def generateScript(self):
        """Generate a PsychoPy script for the experiment
        """
        s=StringIO.StringIO(u'') #a string buffer object
        s.write("""#This experiment was created using PsychoPyGEN and will
        run on any platform on which PsychoPy (www.psychopy.org) can be installed\n\n""")
        
        #delegate most of the code-writing to Flow
        self.flow.generateCode(s)
            
        return s