"""Routines for handling data structures and analysis"""

from psychopy import misc, gui, log
import cPickle, shelve, string, sys, os, time, copy
import numpy
from scipy import optimize, special

def ObjectArray(inputSeq):
    #a wrapper of numpy array(xx,'O') objects
    return numpy.array(inputSeq, 'O')
    
class TrialType(dict):
    """This is just like a dict, except that you can access keys
    """
    def __getattribute__(self, name):
        try:#to get attr from dict in normal way (passing self)
            return dict.__getattribute__(self, name)
        except AttributeError:
            try:
                return self[name]
            except KeyError:
#                print 'TrialType has no attribute (or key) \'%s\'' %(name)
                raise AttributeError, ('TrialType has no attribute (or key) \'%s\'' %(name))

        
class TrialHandler:
    """Class to handle smoothly the selection of the next trial
    and report current values etc.
    Calls to .next() will fetch the next object given to this
    handler, according to the method specified and will raise a 
    StopIteration error if trials have finished
    
    See demo_trialHandler.py
    """
    def __init__(self,
                 trialList, 
                 nReps, 
                 method='random',
                 dataTypes=None,
                 extraInfo=None,
                 seed=None):
        """
        trialList: a simple list (or flat array) of trials.
            
            """
        self.trialList =trialList
        #convert any entry in the TrialList into a TrialType object (with obj.key or obj[key] access)
        for n, entry in enumerate(trialList):
            if type(entry)==dict:
                trialList[n]=TrialType(entry)
        self.nReps = nReps
        self.nTotal = nReps*len(self.trialList)
        self.nRemaining =self.nTotal #subtract 1 each trial
        self.method = method
        self.thisRepN = 0		#records which repetition or pass we are on
        self.thisTrialN = -1	#records which trial number within this repetition
        self.thisIndex = 0		#the index of the current trial in the original matrix
        self.thisTrial = []
        self.notFinished=True
        self.extraInfo=extraInfo
        self._warnUseOfNext=True
        self.seed=seed
        #create dataHandler
        self.data = DataHandler(trials=self)
        if dataTypes!=None: 
            self.data.addDataType(dataTypes)
        self.data.addDataType('ran')
        #generate stimulus sequence
        if self.method in ['random','sequential']:
            self.sequenceIndices = self._createSequence()
        else: self.sequenceIndices=[]
    def __iter__(self):
        return self
    def __repr__(self): 
        """prints a more verbose version of self as string"""
        return self.__str__(verbose=True)
        
    def __str__(self, verbose=False):
        """string representation of the object"""
        strRepres = 'psychopy.data.TrialHandler(\n'
        attribs = dir(self)
        
        #print data first, then all others
        try: data=self.data
        except: data=None
        if data:
            strRepres += str('\tdata=')
            strRepres +=str(data)+'\n'

        for thisAttrib in attribs:
            #can handle each attribute differently
            if 'instancemethod' in str(type(getattr(self,thisAttrib))):
                #this is a method
                continue
            elif thisAttrib[0]=='_':
                #the attrib is private
                continue
            elif thisAttrib=='data':
                #we handled this first
                continue
            elif len(str(getattr(self,thisAttrib)))>20 and \
                 not verbose:
                #just give type of LONG public attribute
                strRepres += str('\t'+thisAttrib+'=')
                strRepres += str(type(getattr(self,thisAttrib)))+'\n'
            else:
                #give the complete contents of attribute
                strRepres += str('\t'+thisAttrib+'=')
                strRepres += str(getattr(self,thisAttrib))+'\n'
                
        strRepres+=')'
        return strRepres
    
    def _createSequence(self):
        """
        Pre-generates the sequence of trial presentations
        (for non-adaptive methods). This is called automatically
        when the TrialHandler is initialised so doesn't need an
        explicit call from the user.
        
        sequence has form indices[stimN][repN]
        """
        
        if self.method == 'random':            
            sequenceIndices = []
            # create indices for a single rep
            indices = numpy.asarray(self._makeIndices(self.trialList), dtype=int)
            seed=self.seed
            for thisRep in range(self.nReps):
                thisRepSeq = misc.shuffleArray(indices.flat, seed=seed).tolist()
                seed=None#so that we only seed the first pass through!
                sequenceIndices.append(thisRepSeq)
            return numpy.transpose(sequenceIndices)
        
        if self.method == 'sequential':
            sequenceIndices = []
            indices = numpy.asarray(self._makeIndices(self.trialList), dtype=int)
            sequenceIndices = numpy.repeat(indices,self.nReps,1)
            return sequenceIndices
        
    def _makeIndices(self,inputArray):
        """
        Creates an array of tuples the same shape as the input array
        where each tuple contains the indices to itself in the array.
        
        Useful for shuffling and then using as a reference.
        """
        inputArray  = ObjectArray(inputArray)#make sure its an array
        #get some simple variables for later
        dims=inputArray.shape
        dimsProd=numpy.product(dims)
        dimsN = len(dims)
        dimsList = range(dimsN)
        listOfLists = []
        arrayOfTuples = ObjectArray(numpy.ones(dimsProd))#this creates space for an array of any objects
        
        #for each dimension create list of its indices (using modulo)
        for thisDim in dimsList:        
            prevDimsProd = numpy.product(dims[:thisDim])
            thisDimVals = numpy.arange(dimsProd)/prevDimsProd % dims[thisDim] #NB this means modulus in python
            listOfLists.append(thisDimVals)
            
        #convert to array
        indexArr = numpy.asarray(listOfLists)
        for n in range(dimsProd):
            arrayOfTuples[n] = tuple((indexArr[:,n]))
        return (numpy.reshape(arrayOfTuples,dims)).tolist()
    
    def next(self):
        """Advances to next trial and returns it.        
        Updates attributes; thisTrial, thisTrialN and thisIndex        
        If the trials have ended this method will raise a StopIteration error.
        This can be handled with code such as 
        
        ::
        
            trials = TrialHandler(.......)
            for eachTrial in trials:#automatically stops when done
                #do stuff           
                
        or
        
        ::
        
            trials = TrialHandler(.......)
            while True: #ie forever
                try:
                    thisTrial = trials.next()
                except StopIteration:#we got a StopIteration error
                    break #break out of the forever loop
                #do stuff here for the trial                   
        """
        #update pointer for next trials
        self.thisTrialN+=1
        self.nRemaining-=1
        if self.thisTrialN==len(self.trialList):
            #start a new repetition
            self.thisTrialN=0
            self.thisRepN+=1
        if self.thisRepN==self.nReps:
            #all reps complete
            self.thisTrial=[]
            self.notFinished=False
            raise StopIteration
        
        #fetch the trial info
        if self.method in ['random','sequential']:
            self.thisIndex = self.sequenceIndices[self.thisTrialN][self.thisRepN]
            self.thisTrial = self.trialList[self.thisIndex]
            self.data.add('ran',1)
        return self.thisTrial
    def saveAsText(self,fileName, 
                   stimOut=[], 
                   dataOut=['n','rt_mean','rt_std', 'acc_raw'],
                   delim='\t',
                   matrixOnly=False,
                   appendFile=True,
                  ):
        """
        Write a text file with the data and various chosen stimulus attributes
        
         **arguments:**
            fileName
                will have .dlm appended (so you can double-click it to
                open in excel) and can include path info.       
            
            stimOut 
                the stimulus attributes to be output. To use this you need to
                use a list of dictionaries and give here the names of dictionary keys
                that you want as strings         
            
            dataOut
                a list of strings specifying the dataType and the analysis to
                be performed. The data can be any of the types that
                you added using trialHandler.data.add() and the anal can be either
                'raw' or most things in the numpy library, including;
                'mean','std','median','max','min'...
            
            delim
                allows the user to use a delimiter other than tab
            
            matrixOnly
                outputs the data with no header row or extraInfo attached
            
            appendFile
                will add this output to the end of the specified file if it already exists
            
        """
        
        #do the necessary analysis on the data
        dataHead=[]#will store list of data headers
        dataAnal=dict([])	#will store data that has been analyzed
        if type(dataOut)!=list: dataOut = [dataOut]
        for thisDataOutN,thisDataOut in enumerate(dataOut):
            
            if thisDataOut=='n': 
                #n is really just hte sum of the ran trials
                thisDataOut='ran_sum' 
                dataOut[thisDataOutN] = 'ran_sum'
                
            dataType, analType =string.split(thisDataOut, '_', 1)
            if not self.data.has_key(dataType): 
                dataOut.remove(thisDataOut)#that analysis can't be done
                continue
            thisData = self.data[dataType]
            
            #set the header
            dataHead.append(dataType+'_'+analType)
            
            #analyse thisData using numpy module
            if analType in dir(numpy):
                exec("thisAnal = numpy.%s(thisData,1)" %analType)
            elif analType=='raw':
                thisAnal=thisData
            else:
                raise 'psychopyErr', 'you can only use analyses from numpy'
            #add extra cols to header if necess
            if len(thisAnal.shape)>1:
                for n in range(thisAnal.shape[1]-1):
                    dataHead.append("")
            dataAnal[thisDataOut]=thisAnal
            
        #create the file or print to stdout
        if appendFile: writeFormat='a'
        else: writeFormat='w' #will overwrite a file        
        if fileName=='stdout':
            f = sys.stdout
        elif fileName[-4:] in ['.dlm','.DLM']:
            f= file(fileName,writeFormat)
        else:
            f= file(fileName+'.dlm',writeFormat)
            
        if not matrixOnly:
            #write a header line
            for heading in stimOut+dataHead:
                if heading=='ran_sum': heading ='n'
                f.write('%s	' %heading)
            f.write('\n')
        
        #loop through stimuli, writing data
        for stimN in range(len(self.trialList)):
            #first the params for this stim (from self.trialList)
            for heading in stimOut:
                thisType = type(self.trialList[stimN][heading])
                if thisType==float: f.write('%.4f%s' %(self.trialList[stimN][heading],delim))
                else: f.write('%s%s' %(self.trialList[stimN][heading],delim))
                
            #then the data for this stim (from self.data)
            for thisDataOut in dataOut:
                #make a string version of the data and then format it
                tmpData = dataAnal[thisDataOut][stimN]
                if hasattr(tmpData,'tolist'): strVersion = str(tmpData.tolist())
                else: strVersion = str(tmpData)
                
                for brackets in ['[', ']','(',')']: #some objects may have these surrounding their string representation
                    strVersion=string.replace(strVersion, brackets,"")
                for newCell in [', ', '  ', ',']: #some objects may already have these as delimitters
                    strVersion=string.replace(strVersion, newCell,delim)
                #remove any multiple delimitters
                while string.find(strVersion, delim+delim)>(-1):
                    strVersion=string.replace(strVersion, delim+delim, delim)
                #remove final delim
                if strVersion[-1]==delim: 
                    strVersion=strVersion[:-1]
                f.write('%s%s' %(strVersion, delim))
            f.write('\n')
            
        #add self.extraInfo
        if (self.extraInfo != None) and not matrixOnly:
            strInfo = str(self.extraInfo)
            #dict begins and ends with {} - remove
            strInfo = strInfo[1:-1] #string.replace(strInfo, '{','');strInfo = string.replace(strInfo, '}','');
            strInfo = string.replace(strInfo, ': ', ':\n')#separate value from keyname
            strInfo = string.replace(strInfo, ',', '\n')#separate values from each other
            strInfo = string.replace(strInfo, 'array([ ', '')
            strInfo = string.replace(strInfo, '])', '')
            
            f.write('\n%s\n' %strInfo)
            
        f.write("\n")
        if f != sys.stdout: f.close()

    def saveAsPickle(self,fileName):
        """Basically just saves a copy of self (with data) to a pickle file.
        
        This can be reloaded if necess and further analyses carried out.
        """
        #otherwise use default location
        f = open(fileName+'.psydat', "wb")
        cPickle.dump(self, f)
        f.close()
        
    def printAsText(self, stimOut=[], 
                    dataOut=['rt_mean','rt_std', 'acc_raw'],
                    delim='\t',
                    matrixOnly=False,
                  ):
        """Exactly like saveAsText except that the output goes
        to the screen instead of a file"""
        self.saveAsText('stdout', stimOut, dataOut, delim, matrixOnly)
    def nextTrial(self):
        """DEPRECATION WARNING: TrialHandler.nextTrial() will be deprecated
        please use Trialhandler.next() instead.
        jwp: 19/6/06
        """
        if self._warnUseOfNext:
            log.warning("""DEPRECATION WARNING: TrialHandler.nextTrial() will be deprecated
        please use Trialhandler.next() instead.
        jwp: 19/6/06
        """)
            self._warnUseOfNext=False     
        return self.next()
        
class StairHandler:
    """Class to handle smoothly the selection of the next trial
    and report current values etc.
    Calls to nextTrial() will fetch the next object given to this
    handler, according to the method specified.
    
    See ``demo_trialHandler.py``
        
    The staircase will terminate when *nTrials* AND *nReversals* have been exceeded. If *stepSizes* was an array
    and has been exceeded before nTrials is exceeded then the staircase will continue
    to reverse
     
    """
    def __init__(self,
                 startVal, 
                 nReversals=None,
                 stepSizes=4,  #dB stepsize
                 nTrials=0,
                 nUp=1,
                 nDown=3, #correct responses before stim goes down
                 extraInfo=None,
                 method = '2AFC',
                 stepType='db',
                 minVal=None,
                 maxVal=None):
        """
        stepType 
            specifies whether each step will be a jump of the given size in 
            'db', 'log' or 'lin' units ('lin' means this intensity will be added/subtracted)     
     
            """
        
        self.startVal=startVal
        self.nReversals=nReversals
        self.nUp=nUp
        self.nDown=nDown
        self.extraInfo=extraInfo
        self.method=method
        self.stepType=stepType
        
        self.stepSizes=stepSizes
        if type(stepSizes) in [int, float]:
            self.stepSizeCurrent=stepSizes
            self._variableStep=False
        else:#list, tuple or array
            self.stepSizeCurrent=stepSizes[0]
            self.nReversals= max(len(stepSizes),self.nReversals)
            self._variableStep=True          
            
        self.nTrials = nTrials#to terminate the nTrials must be exceeded and either 
        self.notFinished=True
        self.thisTrialN = -1
        self.data = []
        self.intensities=[]
        self.reversalPoints = []
        self.reversalIntensities=[]
        self.currentDirection='start' #initially it goes down but on every step
        self.correctCounter=0  #correct since last stim change (minus are incorrect)
        self._nextIntensity=self.startVal
        self._warnUseOfNext=True
        self.minVal = minVal
        self.maxVal = maxVal
        
    def __iter__(self):
        return self
        
    def addData(self, result):
        self.data.append(result)
        
        #increment the counter of correct scores
        if result==1: 
            if len(self.data)>1 and self.data[-2]==result:
                #increment if on a run
                self.correctCounter+=1
            else:
                #or reset
                self.correctCounter = 1
                
        else:
            if  len(self.data)>1 and self.data[-2]==result:
                #increment if on a run
                self.correctCounter-=1
            else:
                #or reset
                self.correctCounter = -1
                
        self.calculateNextIntensity()
                                        
    def calculateNextIntensity(self):
        """based on current intensity, counter of correct responses and current direction"""
        
        if len(self.reversalIntensities)<1:
            #always using a 1-down, 1-up rule initially 
            if self.data[-1]==1:    #last answer correct
                #got it right
                self._intensityDec()
                if self.currentDirection=='up':
                    reversal=True
                else:#direction is 'down' or 'start'
                    reversal=False
                    self.currentDirection='down'
            else:
                #got it wrong
                self._intensityInc()
                if self.currentDirection=='down':
                    reversal=True
                else:#direction is 'up' or 'start'
                    reversal=False
                #now:
                self.currentDirection='up'
            
        elif self.correctCounter >= self.nDown: #n right, time to go down!
            #make it harder
            self._intensityDec()
            if self.currentDirection!='down':
                reversal=True
            else:
                reversal=False
            self.currentDirection='down'
            
        elif self.correctCounter <= -self.nUp: #n wrong, time to go up!            
            #make it easier
            self._intensityInc()
            #note current direction
            if self.currentDirection!='up':
                reversal=True
            else:
                reversal=False
            self.currentDirection='up'
                
        else:
            #same as previous trial
            reversal=False
            
        
        #add reversal info 
        if reversal:
            self.reversalPoints.append(self.thisTrialN)
            self.reversalIntensities.append(self.intensities[-1])
            #and test if we're done
            if len(self.reversalIntensities)>=self.nReversals and \
                len(self.intensities)>=self.nTrials:
                    self.notFinished=False
            #new step size if necessary
            if self._variableStep and self.notFinished:
                if len(self.reversalIntensities) >= len(self.stepSizes):
                    #we've gone beyond the list of step sizes so just use the last one
                    self.stepSizeCurrent = self.stepSizes[-1]
                else:
                    self.stepSizeCurrent = self.stepSizes[len(self.reversalIntensities)]
                
                
    def next(self):
        """Advances to next trial and returns it.
        Updates attributes: thisTrial, thisTrialN and thisIndex       
        
        If the trials have ended this method will raise a StopIteration error.
        This can be handled with code such as 
        
        ::
            
            staircase = StairHandler(.......)
            for eachTrial in staircase:#automatically stops when done
                #do stuff
           
        or
            
        ::
            
            staircase = StairHandler(.......)
            while True: #ie forever
                try:
                    thisTrial = staircase.next()
                except StopIteration:#we got a StopIteration error
                    break #break out of the forever loop
                #do stuff here for the trial
            
        """
        if self.notFinished:
            #update pointer for next trial
            self.thisTrialN+=1        
            self.intensities.append(self._nextIntensity)
            return self._nextIntensity
        else:
            raise StopIteration
        
    def _intensityInc(self):
        """increment the current intensity and reset counter"""
        if self.stepType=='db':
            self._nextIntensity *= 10.0**(self.stepSizeCurrent/20.0)
        elif self.stepType=='log':
            self._nextIntensity *= 10.0**self.stepSizeCurrent
        elif self.stepType=='lin':
            self._nextIntensity += self.stepSizeCurrent
        #check we haven't gone out of the legal range
        if (self._nextIntensity > self.maxVal) and self.maxVal is not None: 
            self._nextIntensity = self.maxVal
        self.correctCounter =0
        
    def _intensityDec(self):
        """decrement the current intensity and reset counter"""
        if self.stepType=='db':
            self._nextIntensity /= 10.0**(self.stepSizeCurrent/20.0)
        if self.stepType=='log':
            self._nextIntensity /= 10.0**self.stepSizeCurrent
        elif self.stepType=='lin':
            self._nextIntensity -= self.stepSizeCurrent
        self.correctCounter =0
        #check we haven't gone out of the legal range
        if (self._nextIntensity < self.minVal) and self.minVal is not None: 
            self._nextIntensity = self.minVal
        
        
    def saveAsText(self,fileName, 
                   delim='\t',
                   matrixOnly=False,
                  ):
        """
        Write a text file with the data and various chosen stimulus attributes
        
        Arguments:
            fileName 
                will have .dlm appended (so you can double-click it to
            	open in excel) and can include path info.            
             
            stimOut 
                the stimulus attributes to be output. To use this you need to
                use a list of dictionaries and give here the names of dictionary keys
                that you want as strings            
            dataOut 
                a list of strings specifying the dataType and the analysis to
                be performed. The data can be any of the types that
                you added using trialHandler.data.add() and the anal can be either
                'raw' or most things in the numpy library, including;
                'mean','std','median','max','min'...
            
        """
        
        #create the file or print to stdout
        if fileName=='stdout':
            f = sys.stdout
        elif fileName[-4:] in ['.dlm','.DLM']:
            f= file(fileName,'w')
        else:
            f= file(fileName+'.dlm','w')
            
        #write the data
        reversalStr = str(self.reversalIntensities)
        reversalStr = string.replace( reversalStr, ',', '\t')
        reversalStr = string.replace( reversalStr, '[', '')
        reversalStr = string.replace( reversalStr, ']', '')
        f.write('\nreversalIntensities=\t%s\n' %reversalStr)
        
        reversalPts = str(self.reversalPoints)
        reversalPts = string.replace( reversalPts, ',', '\t')
        reversalPts = string.replace( reversalPts, '[', '')
        reversalPts = string.replace( reversalPts, ']', '')
        f.write('reversalIndices=\t%s\n' %reversalPts)
        
        rawIntens = str(self.intensities)
        rawIntens = string.replace( rawIntens, ',', '\t')
        rawIntens = string.replace( rawIntens, '[', '')
        rawIntens = string.replace( rawIntens, ']', '')
        f.write('\nintensities=\t%s\n' %rawIntens)
        
        responses = str(self.data)
        responses = string.replace( responses, ',', '\t')
        responses = string.replace( responses, '[', '')
        responses = string.replace( responses, ']', '')
        f.write('responses=\t%s\n' %responses)
        
        #add self.extraInfo
        if (self.extraInfo != None) and not matrixOnly:
            strInfo = str(self.extraInfo)
            #dict begins and ends with {} - remove
            strInfo = strInfo[1:-1] #string.replace(strInfo, '{','');strInfo = string.replace(strInfo, '}','');
            strInfo = string.replace(strInfo, ': ', ':\n')#separate value from keyname
            strInfo = string.replace(strInfo, ',', '\n')#separate values from each other
            strInfo = string.replace(strInfo, 'array([ ', '')
            strInfo = string.replace(strInfo, '])', '')
            
            f.write('\n%s\n' %strInfo)
            
        f.write("\n")
        f.close()

    def saveAsPickle(self,fileName):
        """Basically just saves a copy of self (with data) to a pickle file.
        
        This can be reloaded if necess and further analyses carried out.
        """
        #otherwise use default location
        f = open(fileName+'.psydat', "wb")
        cPickle.dump(self, f)
        f.close()
        
    def printAsText(self, stimOut=[], 
                    dataOut=['rt_mean','rt_std', 'acc_raw'],
                    delim='\t',
                    matrixOnly=False,
                  ):
        """Exactly like saveAsText except that the output goes
        to the screen instead of a file"""
        self.saveAsText('stdout',  delim, matrixOnly)
    
    def nextTrial(self):
        """DEPRECATION WARNING: StairHandler.nextTrial() will be deprecated
        please use StairHandler.next() instead.
        jwp: 19/6/06
        """
        if self._warnUseOfNext:
            log.warning("""DEPRECATION WARNING: StairHandler.nextTrial() will be deprecated
        please use StairHandler.next() instead.
        jwp: 19/6/06
        """)
            self._warnUseOfNext=False
        return self.next()
        
class DataHandler(dict):
    """For handling data (used by TrialHandler, principally, rather than
    by users directly)
    
    Attributes:
        - ['key']=data arrays containing values for that key
            (e.g. data['accuracy']=...)
        - dataShape=shape of data (x,y,...z,nReps)
        - dataTypes=list of keys as strings
    
    """
    def __init__(self, dataTypes=None, trials=None, dataShape=None):
        self.trials=trials
        self.dataTypes=[]#names will be added during addDataType
        
        #if given dataShape use it - otherwise guess!
        if dataShape: self.dataShape=dataShape
        elif self.trials:
            self.dataShape=list(ObjectArray(trials.trialList).shape)
            self.dataShape.append(trials.nReps)
            
        #initialise arrays now if poss
        if dataTypes and self.dataShape:
            for thisType in dataTypes: 
                self.addDataType(thisType)
    
    def addDataType(self, names, shape=None):
        """Add a new key to the data dictionary of
        particular shape if specified (otherwise the
        shape of the trial matrix in the trial handler.
        Data are initialised to be zero everywhere.
        Not needed by user: appropriate types will be added
        during initialisation and as each xtra type is needed.
        """
        if not shape: shape = self.dataShape
        if type(names) != str:
            #recursively call this function until we have a string
            for thisName in names: self.addDataType(thisName)
        else:
            #create the appropriate array in the dict
            self[names]=numpy.zeros(shape,'f')
            #add the name to the list
            self.dataTypes.append(names)
    
    def add(self, thisType, value, position=None):
        """Add data to an existing data type
        (and add a new one if necess)
        """
        if not self.has_key(thisType):
            log.warning("New data type being added: "+thisType)
            self.addDataType(thisType)
        if position==None: 
            #make a list where 1st digit is trial number
            position= [self.trials.thisIndex]
            position.append(self.trials.thisRepN)
            
        #check whether data falls within bounds
        posArr = numpy.asarray(position)
        shapeArr = numpy.asarray(self.dataShape)
        if not numpy.alltrue(posArr<shapeArr):
            #array isn't big enough
            log.warning('need a bigger array for:'+thisType)
            self[thisType]=misc.extendArr(self[thisType],posArr)#not implemented yet!
            
        #insert the value
        self[thisType][position[0]][position[1]]=value
        
      

class FitFunction:
    """Deprecated - use the specific functions; FitWeibull, FitLogistic...
    """
    
    def __init__(self, fnName, xx, yy, sems=1.0, guess=None, display=1,
                 expectedMin=0.5):
        self.fnName = fnName
        self.xx = numpy.asarray(xx)
        self.yy = numpy.asarray(yy)
        self.sems = numpy.asarray(sems)
        self.params = guess
        self.display=display
        # for holding error calculations:
        self.ssq=0
        self.rms=0
        self.chi=0
        
        if fnName[-4:] in ['2AFC', 'TAFC']:
            self.expectedMin = 0.5
        elif fnName[-2:] =='YN':
            self.expectedMin=0.0
        else:
            self.expectedMin=expectedMin
            
        #do the calculations:
        self._doFit()
        
    def _doFit(self):
        #get some useful variables to help choose starting fit vals
        xMin = min(self.xx); xMax = max(self.xx)
        xRange=xMax-xMin; xMean= (xMax+xMin)/2.0
        if self.fnName in ['weibullTAFC','weibullYN']:
            if self.params==None: guess=[xMean, xRange/5.0]
            else: guess= numpy.asarray(self.params,'d')
        elif self.fnName in ['cumNorm','erf']:
            if self.params==None: guess=[xMean, xRange/5.0]#c50, xScale (slope)
            else: guess= numpy.asarray(self.params,'d')
        elif self.fnName in ['logisticTAFC','logistYN', 'logistic']:
            if self.params==None: guess=[xMin, 5.0/xRange]#x0, xRate
            else: guess= numpy.asarray(self.params,'d')  
        elif self.fnName in ['nakaRush', 'nakaRushton', 'NR']: 
            if self.params==None: guess=[xMean, 2.0]#x50, expon
            else: guess= numpy.asarray(self.params,'d')  
        
        self.params = optimize.fmin_cg(self._getErr, guess, None, (self.xx,self.yy,self.sems),disp=self.display)
        self.ssq = self._getErr(self.params, self.xx, self.yy, 1.0)
        self.chi = self._getErr(self.params, self.xx, self.yy, self.sems)
        self.rms = self.ssq/len(self.xx)
        
    def _getErr(self, params, xx,yy,sems):
        mod = self.eval(xx, params)
        err = sum((yy-mod)**2/sems)
        return err

    def eval(self, xx=None, params=None):
        if xx==None: xx=self.xx
        if params==None: params=self.params
        if self.fnName in ['weibullTAFC', 'weibull2AFC']:
            alpha = params[0]; 
            if alpha<=0: alpha=0.001
            beta = params[1]
            xx = numpy.asarray(xx)
            yy =  1.0 - 0.5*numpy.exp( - (xx/alpha)**beta ) 
        elif self.fnName == 'weibullYN':
            alpha = params[0]; 
            if alpha<=0: alpha=0.001
            beta = params[1]
            xx = numpy.asarray(xx)
            yy =  1.0 - numpy.exp( - (xx/alpha)**beta )         
        elif self.fnName in ['nakaRush', 'nakaRushton', 'NR']:
            c50 = params[0]
            if c50<=0: c50=0.001
            n = params[1]
            if n<=0: n=0.001
            xx = numpy.asarray(xx)
            yy = rMax*(xx**n/(xx**n+c50**n))
        elif self.fnName in [ 'erf', 'cumNorm']:
            xShift = params[0]
            xScale = params[1]
            if xScale<=0: xScale=0.001
            xx = numpy.asarray(xx)
            yy = special.erf(xx*xScale - xShift)*0.5+0.5#numpy.special.erf() goes from -1:1
        elif self.fnName in [ 'logisticYN', 'logistYN']:
            x0 = params[0]
            xRate = params[1]
            if xRate<=0: xRate=0.001
            xx = numpy.asarray(xx)
            yy = 1.0/(1+(1.0/x0-1)*numpy.exp(-xRate*xx))
        return yy
    
    def inverse(self, yy, params=None):
        """Returns fitted xx for any given yy value(s).
        
        If params is specified this will override the current model params.
        """
        yy = numpy.asarray(yy)
        if params==None: params=self.params
        if self.fnName== 'weibullTAFC':
            alpha = params[0]
            beta = params[1]            
            xx = alpha * (-numpy.log(2.0 * (1.0-yy))) **(1.0/beta)
        elif self.fnName== 'weibullYN':
            alpha = params[0]
            beta = params[1]            
            xx = alpha * (-numpy.log(1.0-yy))**(1.0/beta)
        elif self.fnName in [ 'erf', 'cumNorm']:
            xShift = params[0]
            xScale = params[1]
            xx = (special.erfinv(yy*2.0-1.0)+xShift)/xScale
        elif self.fnName in [ 'logisticYN', 'logistYN']:
            x0 = params[0]
            xRate = params[1]
            xx = -numpy.log( (1/yy-1)/(1/x0-1) )/xRate      
        elif self.fnName in ['nakaRush', 'nakaRushton', 'NR']:
            c50 = params[0]
            n = params[1]
            xx = c50/(1/yy-1)
        return xx

class _baseFunctionFit:
    """Not needed by most users except as a superclass for developping your own functions
    
    You must overide the eval and inverse methods and a good idea to overide the _initialGuess
    method aswell.
    """
    
    def __init__(self, xx, yy, sems=1.0, guess=None, display=1,
                 expectedMin=0.5):
        self.xx = numpy.asarray(xx)
        self.yy = numpy.asarray(yy)
        self.sems = numpy.asarray(sems)
        self.expectedMin = expectedMin
        self.display=display
        # for holding error calculations:
        self.ssq=0
        self.rms=0
        self.chi=0
        #initialise parameters
        if guess==None:
            self.params = self._initialGuess()
        else:
            self.params = guess
                
        #do the calculations:
        self._doFit()
        
    def _doFit(self):
        #get some useful variables to help choose starting fit vals     
        self.params = optimize.fmin_powell(self._getErr, self.params, (self.xx,self.yy,self.sems),disp=self.display)
        self.ssq = self._getErr(self.params, self.xx, self.yy, 1.0)
        self.chi = self._getErr(self.params, self.xx, self.yy, self.sems)
        self.rms = self.ssq/len(self.xx)
    
    def _initialGuess(self):
        xMin = min(self.xx); xMax = max(self.xx)
        xRange=xMax-xMin; xMean= (xMax+xMin)/2.0
        guess=[xMean, xRange/5.0]
        return guess

    def _getErr(self, params, xx,yy,sems):
        mod = self.eval(xx, params)
        err = sum((yy-mod)**2/sems)
        return err

    def eval(self, xx=None, params=None):
        """Returns fitted yy for any given xx value(s).
        Uses the original xx values (from which fit was calculated)
        if none given.
        
        If params is specified this will override the current model params."""
        yy=xx
        return yy
    
    def inverse(self, yy, params=None):
        """Returns fitted xx for any given yy value(s).
        
        If params is specified this will override the current model params.
        """
        #define the inverse for your function here
        xx=yy
        return xx


class FitWeibull(_baseFunctionFit):
    """Fit a Weibull function (either 2AFC or YN)
    of the form::
    
    	y = chance + (1.0-chance)*(1-exp( -(xx/alpha)**(beta) ))
    
    and with inverse::
    
        x = alpha * (-log((1.0-y)/(1-chance)))**(1.0/beta)
        
    After fitting the function you can evaluate an array of x-values
    with ``fit.eval(x)``, retrieve the inverse of the function with 
    ``fit.inverse(y)`` or retrieve the parameters from ``fit.params`` 
    (a list with ``[alpha, beta]``)"""
    def eval(self, xx=None, params=None):
        if params==None:  params=self.params #so the user can set params for this particular eval
        alpha = params[0]; 
        if alpha<=0: alpha=0.001
        beta = params[1]
        xx = numpy.asarray(xx)
        yy =  self.expectedMin + (1.0-self.expectedMin)*(1-numpy.exp( -(xx/alpha)**(beta) ))
        return yy
    def inverse(self, yy, params=None):
        if params==None: params=self.params #so the user can set params for this particular inv
        alpha = params[0]
        beta = params[1]            
        xx = alpha * (-numpy.log((1.0-yy)/(1-self.expectedMin))) **(1.0/beta)
        return xx
class FitNakaRushton(_baseFunctionFit):
    """Fit a Naka-Rushton function
    of the form::
    
        yy = rMin + (rMax-rMin) * xx**n/(xx**n+c50**n)
    
    After fitting the function you can evaluate an array of x-values
    with ``fit.eval(x)``, retrieve the inverse of the function with 
    ``fit.inverse(y)`` or retrieve the parameters from ``fit.params`` 
    (a list with ``[rMin, rMax, c50, n]``)
    
    Note that this differs from most of the other functions in
    not using a value for the expected minimum. Rather, it fits this
    as oe of the parameters of the model."""
    def __init__(self, xx, yy, sems=1.0, guess=None, display=1):
        self.xx = numpy.asarray(xx)
        self.yy = numpy.asarray(yy)
        self.sems = numpy.asarray(sems)
        self.display=display
        # for holding error calculations:
        self.ssq=0
        self.rms=0
        self.chi=0
        #initialise parameters
        if guess==None:
            self.params = self._initialGuess()
        else:
            self.params = guess
                
        #do the calculations:
        self._doFit()
    def _initialGuess(self):
        xMin = min(self.xx); xMax = max(self.xx)
        xRange=xMax-xMin; xMean= (xMax+xMin)/2.0
        guess=[xMean, 2.0, min(self.yy), max(self.yy)-min(self.yy)]
        return guess 
    def eval(self, xx=None, params=None):
        if params==None:  params=self.params #so the user can set params for this particular eval
        c50 = params[0]
        n = params[1]
        rMin = params[2]
        rMax = params[3]
        #all params should be >0
        if c50<=0: c50=0.001
        if n<=0: n=0.001
        if rMax<=0: n=0.001
        if rMin<=0: n=0.001
        
        xx = numpy.asarray(xx)
        yy = rMin + (rMax-rMin)*(xx**n/(xx**n+c50**n))
        #yy = (xx**n/(xx**n+c50**n))
        return yy
    
    def inverse(self, yy, params=None):
        if params==None: params=self.params #so the user can set params for this particular inv
        yy=numpy.asarray(yy)
        c50 = params[0]
        n = params[1]
        rMin = params[2]
        rMax = params[3]
        
        yScaled = (yy-rMin)/(rMax-rMin) #remove baseline and scale
        xx = (yScaled*c50**n/(1-yScaled))**(1/n)
        return xx
    
class FitLogistic(_baseFunctionFit):
    """Fit a Logistic function (either 2AFC or YN) 
    of the form::
    
    	y = chance + (1-chance)/(1+exp((PSE-xx)*JND))
    
    and with inverse::
    
        x = PSE - log((1-chance)/(yy-chance) - 1)/JND
    
    After fitting the function you can evaluate an array of x-values
    with ``fit.eval(x)``, retrieve the inverse of the function with 
    ``fit.inverse(y)`` or retrieve the parameters from ``fit.params`` 
    (a list with ``[PSE, JND]``)
    """
    def eval(self, xx=None, params=None):
        if params==None:  params=self.params #so the user can set params for this particular eval
        PSE = params[0]
        JND = params[1]
        chance = self.expectedMin
        xx = numpy.asarray(xx)
        yy = chance + (1-chance)/(1+numpy.exp((PSE-xx)*JND))
        return yy
    def inverse(self, yy, params=None):
        if params==None: params=self.params #so the user can set params for this particular inv
        PSE = params[0]
        JND = params[1]
        chance = self.expectedMin
        yy = numpy.asarray(yy)
        xx = PSE - numpy.log((1-chance)/(yy-chance) - 1)/JND
        return xx

class FitCumNormal(_baseFunctionFit):
    """Fit a Cumulative Normal function (aka error function or erf) 
    of the form::
    
    	y = chance + (1-chance)*(special.erf(xx*xScale - xShift)/2.0+0.5)
    
    and with inverse::
    
        x = (erfinv((yy-chance)/(1-chance)*2.0-1)+xShift)/xScale
        
    After fitting the function you can evaluate an array of x-values
    with fit.eval(x), retrieve the inverse of the function with 
    fit.inverse(y) or retrieve the parameters from fit.params 
    (a list with [xShift, xScale])
    """
    def eval(self, xx=None, params=None):
        if params==None:  params=self.params #so the user can set params for this particular eval
        xShift = params[0]
        xScale = params[1]
        chance = self.expectedMin        
        if xScale<=0: xScale=0.001
        xx = numpy.asarray(xx)
        yy = chance + (1-chance)*(special.erf(xx*xScale - xShift)/2.0+0.5)#NB numpy.special.erf() goes from -1:1
        return yy
    def inverse(self, yy, params=None):
        if params==None: params=self.params #so the user can set params for this particular inv
        xShift = params[0]
        xScale = params[1]
        chance = self.expectedMin
        xx = (special.erfinv((yy-chance)/(1-chance)*2.0-1)+xShift)/xScale#NB numpy.special.erf() goes from -1:1
        return xx

def bootStraps(dat, n=1):
    """Create a list of n bootstrapped resamples of the data
    SLOW IMPLEMENTATION (Python for-loop)
    
    Usage:
        ``out = bootStraps(dat, n=1)``
    
    Where:
        dat
            an NxM or 1xN array (each row is a different condition, each column is a different trial)
        n
            number of bootstrapped resamples to create
            
        out
            - dim[0]=conditions
            - dim[1]=trials
            - dim[2]=resamples
    """
    dat = numpy.asarray(dat)
    if len(dat.shape)==1: #have presumably been given a series of data for one stimulus
        dat=numpy.array([dat])#adds a dimension (arraynow has shape (1,Ntrials))
    
    nTrials = dat.shape[1]
    #initialise a matrix to store output
    resamples = numpy.zeros(dat.shape+(n,), dat.dtype)
    for stimulusN in range(dat.shape[0]):
        thisStim = dat[stimulusN,:]#fetch data for this stimulus
        for sampleN in range(n):
            indices = numpy.floor(nTrials*numpy.random.rand(nTrials)).astype('i')
            resamples[stimulusN,:,sampleN] = numpy.take(thisStim, indices)
    return resamples

def functionFromStaircase(intensities, responses, bins = 10):
    """Create a psychometric function by binning data from a staircase procedure
    
    usage::
    
    	[intensity, meanCorrect, n] = functionFromStaircase(intensities, responses, bins)
        
    where:
            intensities 
                are a list of intensities to be binned
                
            responses 
                are a list of 0,1 each corresponding to the equivalent intensity value
                
            bins 
                can be an integer (giving that number of bins) or 'unique' (where each bin is made from ALL data for exactly one intensity value)

            intensity 
                is the center of an intensity bin
                
            meanCorrect 
                is mean % correct in that bin
                
            n 
                is number of responses contributing to that mean
    """
    #convert to arrays
    try:#concatenate if multidimensional
        intensities = numpy.concatenate(intensities)
        responses = numpy.concatenate(responses)
    except:
        intensities = numpy.array(intensities)
        responses = numpy.array(responses)
    
    #sort the responses
    sort_ii = numpy.argsort(intensities)
    sortedInten = numpy.take(intensities, sort_ii)
    sortedResp = numpy.take(responses, sort_ii)
    
    binnedResp=[]; binnedInten=[]; nPoints = []
    if bins=='unique':
        intensities = numpy.round(intensities, decimals=8)
        uniqueIntens=numpy.unique(intensities)
        for thisInten in uniqueIntens:
            theseResps = responses[intensities==thisInten]
            binnedInten.append(thisInten)
            binnedResp.append(numpy.mean(theseResps))
            nPoints.append(len(theseResps))
    else:
        pointsPerBin = len(intensities)/float(bins)
        for binN in range(bins):
            thisResp = sortedResp[int(round(binN*pointsPerBin)) : int(round((binN+1)*pointsPerBin))]
            thisInten = sortedInten[int(round(binN*pointsPerBin)) : int(round((binN+1)*pointsPerBin))]
            
            binnedResp.append( numpy.mean(thisResp))
            binnedInten.append( numpy.mean(thisInten))
            nPoints.append( len(thisInten) )
        
    return binnedInten, binnedResp, nPoints

def getDateStr():
    """Uses ``time.strftime()``_ to generate a string of the form
    Apr_19_1531 for 19th April 3.31pm.
    This is often useful appended to data filenames to provide unique names
    """
    return time.strftime("%b_%d_%H%M", time.localtime())