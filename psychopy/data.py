"""Routines for handling data structures and analysis"""
# Part of the PsychoPy library
# Copyright (C) 2010 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy import misc, gui, log
import cPickle, string, sys, platform, os, time, copy
import numpy
from scipy import optimize, special

# imports for RuntimeInfo()
from psychopy.visual import getMsPerFrame
from psychopy import visual
from core import shellCall
from psychopy.ext import rush
from psychopy import __version__ as psychopyVersion
from pyglet.gl import gl_info
import scipy, matplotlib, pyglet
try: import ctypes
except: pass
try: import hashlib # python 2.5
except: import sha
import random

try:
    import openpyxl
    haveOpenpyxl=True
    from openpyxl.cell import get_column_letter
except:
    haveOpenpyxl=False
    
class TrialType(dict):
    """This is just like a dict, except that you can access keys with obj.key
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
        if trialList in [None, []]:#user wants an empty trialList
            self.trialList = [None]#which corresponds to a list with a single empty entry
        else:
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
        self.data['ran'].mask=False#this is a bool - all entries are valid
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
            for thisRep in range(int(self.nReps)):
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
        inputArray  = numpy.asarray(inputArray, 'O')#make sure its an array of objects (can be strings etc)
        #get some simple variables for later
        dims=inputArray.shape
        dimsProd=numpy.product(dims)
        dimsN = len(dims)
        dimsList = range(dimsN)
        listOfLists = []
        arrayOfTuples = numpy.ones(dimsProd, 'O')#this creates space for an array of any objects
        
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
        This can be handled with code such as::
        
            trials = TrialHandler(.......)
            for eachTrial in trials:#automatically stops when done
                #do stuff           
                
        or::
        
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
    def _parseDataOutput(self, dataOut):
        
        dataHead=[]#will store list of data headers
        dataAnal=dict([])	#will store data that has been analyzed
        if type(dataOut)==str: dataout=[dataOut]#don't do list convert or we get a list of letters
        elif type(dataOut)!=list: dataOut = list(dataOut)
        
        #expand any 'all' dataTypes to be the full list of available dataTypes
        allDataTypes=self.data.keys()
        allDataTypes.remove('ran')
        dataOutNew=[]
        for thisDataOut in dataOut:
            if thisDataOut=='n': 
                #n is really just the sum of the ran trials
                dataOutNew.append('ran_sum')
                continue#no need to do more with this one
            #then break into dataType and analysis 
            dataType, analType =string.rsplit(thisDataOut, '_', 1)
            if dataType=='all':
                dataOutNew.extend([key+"_"+analType for key in allDataTypes])
            else:
                dataOutNew.append(thisDataOut)
        dataOut=dataOutNew        
        dataOut.sort()#so that all datatypes come together, rather than all analtypes
        dataOutInvalid=[]
        if 'ran_sum' in dataOut:#move n to the first column
            dataOut.remove('ran_sum')
            dataOut.insert(0,'ran_sum')
        #do the necessary analysis on the data
        for thisDataOutN,thisDataOut in enumerate(dataOut):
            dataType, analType =string.rsplit(thisDataOut, '_', 1)
            if not self.data.has_key(dataType): 
                dataOutInvalid.append(thisDataOut)#that analysis can't be done
                continue
            thisData = self.data[dataType]
            
            #set the header
            dataHead.append(dataType+'_'+analType)
            #analyse thisData using numpy module
            if analType in dir(numpy):
                try:#this will fail if we try to take mean of a string for example
                    exec("thisAnal = numpy.%s(thisData,1)" %analType)
                except:
                    dataHead.remove(dataType+'_'+analType)#that analysis doesn't work
                    dataOutInvalid.append(thisDataOut)
                    continue#to next analysis
            elif analType=='raw':
                thisAnal=thisData
            else:
                raise AttributeError, 'You can only use analyses from numpy'
            #add extra cols to header if necess
            if len(thisAnal.shape)>1:                
                for n in range(thisAnal.shape[1]-1):
                    dataHead.append("")
            dataAnal[thisDataOut]=thisAnal
        
        #remove invalid analyses (e.g. average of a string)
        for invalidAnal in dataOutInvalid: dataOut.remove(invalidAnal)
        return dataOut, dataAnal, dataHead
    def saveAsText(self,fileName, 
                   stimOut=[], 
                   dataOut=('n','all_mean','all_std', 'all_raw'),
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
                be performed,in the form /dataType_analysis/. The data can be any of the types that
                you added using trialHandler.data.add() and the analysis can be either
                'raw' or most things in the numpy library, including;
                'mean','std','median','max','min'...
                The default values will output the raw, mean and std of all datatypes found 
            
            delim
                allows the user to use a delimiter other than tab ("," is popular with file extension ".csv")
            
            matrixOnly
                outputs the data with no header row or extraInfo attached
            
            appendFile
                will add this output to the end of the specified file if it already exists
            
        """
        dataOut, dataAnal, dataHead = self._parseDataOutput(dataOut=dataOut)
        
        #create the file or print to stdout
        if appendFile: writeFormat='a'
        else: writeFormat='w' #will overwrite a file        
        if fileName=='stdout':
            f = sys.stdout
        elif fileName[-4:] in ['.dlm','.DLM', '.csv', '.CSV']:
            f= file(fileName,writeFormat)
        else:
            f= file(fileName+'.dlm',writeFormat)
            
        if not matrixOnly:
            #write a header line
            for heading in stimOut+dataHead:
                if heading=='ran_sum': heading ='n'
                f.write('%s%s' %(heading,delim))
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
                
                if strVersion=='()': strVersion="--"#no data in masked array should show as "--"
                
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
        if not fileName.endswith('.psydat'):
            fileName+='.psydat'
        f = open(fileName, "wb")
        cPickle.dump(self, f)
        f.close()
        
    def printAsText(self, stimOut=[], 
                    dataOut=('all_mean', 'all_std', 'all_raw'),
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
    def addData(self, thisType, value, position=None):
        """Add data for the current trial to the `~psychopy.data.DataHandler`
        """
        self.data.add(thisType, value, position=None)
    
    def saveAsExcel(self,fileName, sheetName='rawData',
                    stimOut=[], 
                    dataOut=('n','all_mean','all_std', 'all_raw'),
                    matrixOnly=False,                    
                    appendFile=True,
                    ):
        """
        Write an Excel (.xlsx) file containing the data and various chosen stimulus attributes.
        
        If appendFile is True (and the .xlsx file already exists then a new worksheet will simply be created within
        it
        """
        #NB this was based on the limited documentation (1 page wiki) for openpyxl v1.0
        if not haveOpenpyxl: 
            raise ImportError, 'openpyxl is required for saving files in Excel (xlsx) format, but was not found.'
            return -1
        dataOut, dataAnal, dataHead = self._parseDataOutput(dataOut=dataOut)
        
        #import necessary subpackages - they are small so won't matter to do it here
        from openpyxl.workbook import Workbook
        from openpyxl.writer.excel import ExcelWriter
        from openpyxl.reader.excel import load_workbook
        
        if not fileName.endswith('.xlsx'): fileName+='.xlsx'
        #create or load the file
        if appendFile and os.path.isfile(fileName): 
            wb = load_workbook(fileName)
            newWorkbook=False
        else:
            if not appendFile: #the file exists but we're not appending, so will be overwritten
                log.warning('Data file, %s, will be overwritten' %fileName)
            wb = Workbook()#create new workbook
            wb.properties.creator='PsychoPy'+psychopyVersion
            newWorkbook=True
        
        ew = ExcelWriter(workbook = wb)
        
        if newWorkbook:
            ws = wb.worksheets[0]
            ws.title=sheetName
        else:
            ws=wb.create_sheet()
            ws.title=sheetName

        #write the header line
        if not matrixOnly:
            #write a header line
            for colN, heading in enumerate(stimOut+dataHead):
                if heading=='ran_sum': heading ='n'
                ws.cell(_getExcelCellName(col=colN,row=0)).value=unicode(heading)
                
        #loop through lines (trialTypes), writing data
        for stimN in range(len(self.trialList)):
            #first the params for this trialType (from self.trialList)
            for colN, heading in enumerate(stimOut):
                ws.cell(_getExcelCellName(col=colN,row=stimN+1)).value = unicode(self.trialList[stimN][heading])
            colN = len(stimOut)
            #then the data for this stim (from self.data)
            for thisDataOut in dataOut:
                tmpData = dataAnal[thisDataOut][stimN]
                datType = type(tmpData)
                if tmpData is None:#just go to next column
                    colN+=1
                    continue
                elif not hasattr(tmpData,'__iter__'): 
                    ws.cell(_getExcelCellName(col=colN,row=stimN+1)).value = unicode(tmpData)
                    colN+=1
                else:
                    for entry in tmpData:
                        ws.cell(_getExcelCellName(col=colN,row=stimN+1)).value = unicode(entry)
                        colN+=1
        
        #add self.extraInfo
        rowN = len(self.trialList)+2
        if (self.extraInfo != None) and not matrixOnly:
            ws.cell(_getExcelCellName(0,rowN)).value = 'extraInfo'; rowN+=1
            for key,val in self.extraInfo.items():
                ws.cell(_getExcelCellName(0,rowN)).value = unicode(key)+u':'
                ws.cell(_getExcelCellName(1,rowN)).value = unicode(val)
                rowN+=1

        ew.save(filename = fileName)


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
        :Parameters:
            
            startVal:
                The initial value for the staircase.
            
            nReversals:
                The minimum number of reversals permitted. If stepSizes is a list then there must
                also be enough reversals to satisfy this list.
    
            stepSizes:
                The size of steps as a single value or a list (or array). For a single value the step
                size is fixed. For an array or list the step size will progress to the next entry
                at each reversal.
            
            nTrials:
                The minimum number of trials to be conducted. If the staircase has not reached the
                required number of reversals then it will continue.
                
            nUp:
                The number of 'incorrect' (or 0) responses before the staircase level increases.
                
            nDown:
                The number of 'correct' (or 1) responses before the staircase level decreases.
                
            extraInfo:
                A dictionary (typically) that will be stored along with collected data using 
                :func:`~psychopy.data.StairHandler.saveAsPickle` or 
                :func:`~psychopy.data.StairHandler.saveAsText` methods. 
                
            stepType:
                specifies whether each step will be a jump of the given size in 
                'db', 'log' or 'lin' units ('lin' means this intensity will be added/subtracted)     
            
            method:
                Not used and may be deprecated in future releases.
            
            stepType: *'db'*, 'lin', 'log'
                The type of steps that should be taken each time. 'lin' will simply add or subtract that
                amount each step, 'db' and 'log' will step by a certain number of decibels or log units
                (note that this will prevent your value ever reaching zero or less)
                
            minVal: *None*, or a number
                The smallest legal value for the staircase, which can be used to prevent it
                reaching impossible contrast values, for instance.
            
            maxVal: *None*, or a number
                The largest legal value for the staircase, which can be used to prevent it
                reaching impossible contrast values, for instance.
                
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
        """Add a 1 or 0 to signify a correct/detected or incorrect/missed trial
        """
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
        Updates attributes; `thisTrial`, `thisTrialN` and `thisIndex`.   
        
        If the trials have ended, calling this method will raise a StopIteration error.
        This can be handled with code such as::
            
            staircase = StairHandler(.......)
            for eachTrial in staircase:#automatically stops when done
                #do stuff
           
        or::
            
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
        
        :Parameters:
        
            fileName: a string
                The name of the file, including path if needed. The extension 
                `.dlm` will be added if not included.
            
            delim: a string
                the delimitter to be used (e.g. '\t' for tab-delimitted, ',' for csv files)
                
            matrixOnly: True/False
                If True, prevents the output of the `extraInfo` provided at initialisation.
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
                    dataOut=('rt_mean','rt_std', 'acc_raw'),
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
        
class QuestHandler:
    """(place-holder for future integration of _quest.py as a Trial/StairHandler)
    """
    def __init__(self):
        self = None

class DataHandler(dict):
    """For handling data (used by TrialHandler, principally, rather than
    by users directly)
    
    Numeric data are stored as numpy masked arrays where the mask is set True for missing entries.
    When any non-numeric data (string, list or array) get inserted using DataHandler.add(val) the array
    is converted to a standard (not masked) numpy array with dtype='O' and where missing entries have
    value="--"
    
    Attributes:
        - ['key']=data arrays containing values for that key
            (e.g. data['accuracy']=...)
        - dataShape=shape of data (x,y,...z,nReps)
        - dataTypes=list of keys as strings
    
    """
    def __init__(self, dataTypes=None, trials=None, dataShape=None):
        self.trials=trials
        self.dataTypes=[]#names will be added during addDataType
        self.isNumeric={}
        #if given dataShape use it - otherwise guess!
        if dataShape: self.dataShape=dataShape
        elif self.trials:
            self.dataShape=list(numpy.asarray(trials.trialList,'O').shape)
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
            #initially use numpy masked array of floats with mask=True for missing vals
            #convert to a numpy array with dtype='O' if non-numeric data given
            #NB don't use masked array with dytpe='O' together -they don't unpickle
            self[names]=numpy.ma.zeros(shape,'f')#masked array of floats
            self[names].mask=True
            #add the name to the list
            self.dataTypes.append(names)
            self.isNumeric[names]=True#until we need otherwise
    def add(self, thisType, value, position=None):
        """Add data to an existing data type
        (and add a new one if necess)
        """
        if not self.has_key(thisType):
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
        #check for ndarrays with more than one value and for non-numeric data
        if self.isNumeric[thisType] and \
            ((type(value)==numpy.ndarray and len(value)>1) or (type(value) not in [float, int])):
                self._convertToObjectArray(thisType)
        #insert the value
        self[thisType][position[0],position[1]]=value
    def _convertToObjectArray(self, thisType):
        """Convert this datatype from masked numeric array to unmasked object array
        """
        dat = self[thisType]
        self[thisType] = numpy.asarray(dat, dtype='O')#create an array of Object type
        self[thisType] = numpy.where(dat.mask, '--',dat)#masked vals should be "--", others keep data
        self.isNumeric[thisType]=False

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
    as one of the parameters of the model."""
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

class RunTimeInfo(dict):
    """Returns a snapshot of your configuration at run-time, for immediate or archival use.
    
    Returns a dict-like object with info about PsychoPy, your experiment script, the system & OS,
    your window and monitor settings (if any), python & packages, and openGL.
    
    If you want to skip testing the refresh rate, use 'refreshTest=None'
    
    Example usage: see runtimeInfo.py in coder demos.
    
    :Author:
        - 2010 written by Jeremy Gray, with input from Jon Peirce and Alex Holcombe
    """
    def __init__(self, author=None, version=None, win=None, refreshTest='grating',
                 userProcsDetailed=False, verbose=False, randomSeed=None ):
        """
        :Parameters:
            
            win : *None*, False, :class:`~psychopy.visual.Window` instance
                what window to use for refresh rate testing (if any) and settings. None -> temporary window using
                defaults; False -> no window created, used, nor profiled; a Window() instance you have already created
            
            author : *None*, string
                None = try to autodetect first __author__ in sys.argv[0]; string = user-supplied author info (of an experiment)
            
            version : *None*, string
                None = try to autodetect first __version__ in sys.argv[0]; string = user-supplied version info (of an experiment)
            
            verbose : *False*, True; how much detail to assess
            
            refreshTest : None, False, True, *'grating'*
                True or 'grating' = assess refresh average, median, and SD of 60 win.flip()s, using visual.getMsPerFrame()
                'grating' = show a visual during the assessment; True = assess without a visual
                
            userProcsDetailed: *False*, True
                get details about concurrent user's processses (command, process-ID)
                
            randomSeed: *None*
                a way for the user to record, and optionally set, a random seed for making reproducible random sequences
                'set:XYZ' will both record the seed, 'XYZ', and set it: random.seed('XYZ'); numpy.random.seed() is NOT set
                None defaults to python default;
                'time' = use time.time() as the seed, as obtained during RunTimeInfo()
                randomSeed='set:time' will give a new random seq every time the script is run, with the seed recorded.
                
        :Returns: 
            a flat dict (but with several groups based on key names):
            
            psychopy : version, rush() availability
                psychopyVersion, psychopyHaveExtRush
                
            experiment : author, version, directory, name, current time-stamp, 
                SHA1 digest, VCS info (if any, svn or hg only),
                experimentAuthor, experimentVersion, ...
                
            system : hostname, platform, user login, count of users, user process info (count, cmd + pid), flagged processes
                systemHostname, systemPlatform, ...
                
            window : (see output; many details about the refresh rate, window, and monitor; units are noted)
                windowWinType, windowWaitBlanking, ...windowRefreshTimeSD_ms, ... windowMonitor.<details>, ...
                
            python : version of python, versions of key packages (numpy, scipy, matplotlib, pyglet, pygame)
                pythonVersion, pythonScipyVersion, ...
                
            openGL : version, vendor, rendering engine, plus info on whether several extensions are present
                openGLVersion, ..., openGLextGL_EXT_framebuffer_object, ...
        """
        dict.__init__(self)  # this will cause an object to be created with all the same methods as a dict
        
        self['psychopyVersion'] = psychopyVersion
        self['psychopyHaveExtRush'] = rush(False) # NB: this looks weird, but avoids setting high-priority incidentally
        
        self._setExperimentInfo(author, version, verbose, randomSeed)
        self._setSystemUserInfo()
        self._setCurrentProcessInfo(verbose, userProcsDetailed)
        
        # need a window for frame-timing, and some openGL drivers want a window open
        if win == None: # make a temporary window, later close it
            win = visual.Window(fullscr=True, monitor="testMonitor")
            refreshTest = 'grating'
            usingTempWin = True
        else: # either False, or we were passed a window instance, use it for timing and profile it:
            usingTempWin = False
        if win: 
            self._setWindowInfo(win, verbose, refreshTest, usingTempWin)
       
        self['pythonVersion'] = sys.version.split()[0]
        if verbose:
            self._setPythonInfo()
            if win: self._setOpenGLInfo()
        if usingTempWin:
            win.close() # close after doing openGL
            
    def _setExperimentInfo(self, author, version, verbose, randomSeedFlag=None):
        # try to auto-detect __author__ and __version__ in sys.argv[0] (= the users's script)
        if not author or not version:
            f = open(sys.argv[0],'r')
            lines = f.read()
            f.close()
        if not author and lines.find('__author__')>-1:
            linespl = lines.splitlines()
            while linespl[0].find('__author__') == -1:
                linespl.pop(0)
            auth = linespl[0]
            if len(auth) and auth.find('=') > 0:
                try:
                    author = str(eval(auth[auth.find('=')+1 :]))
                except:
                    pass
        if not version and lines.find('__version__')>-1:
            linespl = lines.splitlines()
            while linespl[0].find('__version__') == -1:
                linespl.pop(0)
            ver = linespl[0]
            if len(ver) and ver.find('=') > 0:
                try:
                    version = str(eval(ver[ver.find('=')+1 :]))
                except:
                    pass
        
        if author or verbose:  
            self['experimentAuthor'] = author
        if version or verbose: 
            self['experimentAuthVersion'] = version
        
        # script identity & integrity information:
        self['experimentScript'] = os.path.basename(sys.argv[0])  # file name
        scriptDir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self['experimentScript.directory'] = scriptDir
        # sha1 digest, text-format compatibility
        self['experimentScript.digestSHA1'] = _getSha1hexDigest(os.path.abspath(sys.argv[0]))
        # subversion revision?
        try:
            svnrev, last, url = _getSvnVersion(os.path.abspath(sys.argv[0])) # svn revision
            if svnrev: # or verbose:
                self['experimentScript.svnRevision'] = svnrev
                self['experimentScript.svnRevLast'] = last
                self['experimentScript.svnRevURL'] = url
        except:
            pass
        # mercurical revision?
        try:
            hgChangeSet = _getHgVersion(os.path.abspath(sys.argv[0])) 
            if hgChangeSet: # or verbose:
                self['experimentScript.hgChangeSet'] = hgChangeSet
        except:
            pass
        
        # when was this run?
        self['experimentRunTime.epoch'] = time.time() # basis for default random.seed()
        self['experimentRunTime'] = time.ctime(self['experimentRunTime.epoch'])+' '+time.tzname[time.daylight] # a "right now" time-stamp
        
        # random.seed -- record the value, and initialize random.seed() if 'set:'
        if randomSeedFlag: 
            randomSeedFlag = str(randomSeedFlag)
            while randomSeedFlag.find('set: ') == 0:
                randomSeedFlag = randomSeedFlag.replace('set: ','set:',1) # spaces between set: and value could be confusing after deleting 'set:'
            randomSeed = randomSeedFlag.replace('set:','',1).strip()
            if randomSeed in ['time']:
                randomSeed = self['experimentRunTime.epoch']
            self['experimentRandomSeed.string'] = randomSeed
            if randomSeedFlag.find('set:') == 0:
                random.seed(self['experimentRandomSeed.string']) # seed it
                self['experimentRandomSeed.isSet'] = True
            else:
                self['experimentRandomSeed.isSet'] = False
        else:
            self['experimentRandomSeed.string'] = None
            self['experimentRandomSeed.isSet'] = False
            
    def _setSystemUserInfo(self):
        # machine name
        self['systemHostName'] = platform.node()
        
        # platform name, etc
        if sys.platform in ['darwin']:
            OSXver, junk, architecture = platform.mac_ver()
            platInfo = 'darwin '+OSXver+' '+architecture
            # powerSource = ...
        elif sys.platform in ['linux2']:
            platInfo = 'linux2 '+platform.release()
            # powerSource = ...
        elif sys.platform in ['win32']:
            platInfo = 'windowsversion='+repr(sys.getwindowsversion())
            # powerSource = ...
        else:
            platInfo = ' [?]'
            # powerSource = ...
        self['systemPlatform'] = platInfo
        #self['systemPowerSource'] = powerSource
        
        # count all unique people (user IDs logged in), and find current user name & UID
        self['systemUser'],self['systemUserID'] = _getUserNameUID()
        try:
            users = shellCall("who -q").splitlines()[0].split()
            self['systemUsersCount'] = len(set(users))
        except:
            self['systemUsersCount'] = False
        
        # when last rebooted?
        try:
            lastboot = shellCall("who -b").split()
            self['systemRebooted'] = ' '.join(lastboot[2:])
        except: # windows
            sysInfo = shellCall('systeminfo').splitlines()
            lastboot = [line for line in sysInfo if line.find("System Up Time") == 0 or line.find("System Boot Time") == 0]
            lastboot += ['[?]'] # put something in the list just in case
            self['systemRebooted'] = lastboot[0].strip()
        
        # is R available (for stats)?
        try:
            Rver,err = shellCall("R --version",stderr=True)
            Rversion = Rver.splitlines()[0]
            if Rversion.find('R version') == 0:
                self['systemRavailable'] = Rversion.strip()
            else: raise
        except:
            self['systemRavailable'] = False
        
        """try:
            import rpy2
            self['systemRpy2'] = rpy2.__version__
        except:
            self['systemRpy2'] = False
        
        # openssl version--maybe redundant with python distribution info?
        # for a sha1 digest, python's hashlib is better than a shell call to openssl
        try:
            self['systemOpenSSLVersion'],err = shellCall('openssl version',stderr=True)
            if err:
                raise
        except:
            self['systemOpenSSLVersion'] = None
        """
        
    def _setCurrentProcessInfo(self, verbose=False, userProcsDetailed=False):
        # what other processes are currently active for this user?
        profileInfo = ''
        appFlagList = [# flag these apps if active, case-insensitive match:
            'Firefox','Safari','Explorer','Netscape', 'Opera', # web browsers can burn CPU cycles
            'BitTorrent', 'iTunes', # but also matches iTunesHelper (add to ignore-list)
            'mdimport', # can have high CPU
            'Office', 'KeyNote', 'Pages', 'LaunchCFMApp', # productivity; on mac, MS Office (Word etc) can be launched by 'LaunchCFMApp'
            'VirtualBox','VBoxClient', # virtual machine as host or client
            'Parallels', 'Coherence', 'prl_client_app','prl_tools_service',
            'VMware'] # just a guess
        appIgnoreList = [# always ignore these, exact match:
            'ps','login','-tcsh','bash', 'iTunesHelper']
        
        # assess concurrently active processes owner by the current user:
        try:
            # ps = process status, -c to avoid full path (potentially having spaces) & args, -U for user
            if sys.platform in ['darwin']:
                proc = shellCall("ps -c -U "+os.environ['USER'])
                cmdStr = 'COMMAND'
            elif sys.platform in ['linux2']:
                proc = shellCall("ps -c -U "+os.environ['USER'])
                cmdStr = 'CMD'
            elif sys.platform in ['win32']: 
                proc, err = shellCall("tasklist", stderr=True) # "tasklist /m" gives modules as well
                if err:
                    print 'tasklist error:', err
                    raise
            else: # guess about freebsd based on darwin... 
                proc,err = shellCall("ps -U "+os.environ['USER'],stderr=True)
                if err: raise
                cmdStr = 'COMMAND' # or 'CMD'?
            systemProcPsu = []
            systemProcPsuFlagged = [] 
            systemUserProcFlaggedPID = []
            procLines = proc.splitlines() 
            headerLine = procLines.pop(0) # column labels
            if sys.platform not in ['win32']:
                cmd = headerLine.split().index(cmdStr) # columns and column labels can vary across platforms
                pid = headerLine.split().index('PID')  # process id's extracted in case you want to os.kill() them from psychopy
            else: # this works for win XP, for output from 'tasklist'
                procLines.pop(0) # blank
                procLines.pop(0) # =====
                pid = -5 # pid next after command, which can have
                cmd = 0  # command is first, but can have white space, so end up taking line[0:pid]
            for p in procLines:
                pr = p.split() # info fields for this process
                if pr[cmd] in appIgnoreList:
                    continue
                if sys.platform in ['win32']:  #allow for spaces in app names
                    systemProcPsu.append([' '.join(pr[cmd:pid]),pr[pid]]) # later just count these unless want details
                else:
                    systemProcPsu.append([' '.join(pr[cmd:]),pr[pid]]) #
                matchingApp = [a for a in appFlagList if p.lower().find(a.lower())>-1]
                for app in matchingApp:
                    systemProcPsuFlagged.append([app, pr[pid]])
                    systemUserProcFlaggedPID.append(pr[pid])
            self['systemUserProcCount'] = len(systemProcPsu)
            self['systemUserProcFlagged'] = systemProcPsuFlagged
            
            if verbose and userProcsDetailed:
                self['systemUserProcCmdPid'] = systemProcPsu
                self['systemUserProcFlaggedPID'] = systemUserProcFlaggedPID
        except:
            if verbose:
                self['systemUserProcCmdPid'] = None
                self['systemUserProcFlagged'] = None
    
    def _setWindowInfo(self, win, verbose=False, refreshTest='grating', usingTempWin=True):
        """find and store info about the window: refresh rate, configuration info
        """
        
        if refreshTest in ['grating', True]:
            msPFavg, msPFstd, msPFmd6 = getMsPerFrame(win, nFrames=120, showVisual=bool(refreshTest=='grating'))
            self['windowRefreshTimeAvg_ms'] = msPFavg
            self['windowRefreshTimeMedian_ms'] = msPFmd6
            self['windowRefreshTimeSD_ms'] = msPFstd
        if usingTempWin:
            return
        
        # These 'configuration lists' control what attributes are reported.
        # All desired attributes/properties need a legal internal name, e.g., win.winType.
        # If an attr is callable, its gets called with no arguments, e.g., win.monitor.getWidth()
        winAttrList = ['winType', '_isFullScr', 'units', 'monitor', 'pos', 'screen', 'rgb', 'size']
        winAttrListVerbose = ['allowGUI', 'useNativeGamma', 'recordFrameIntervals','waitBlanking', '_haveShaders', '_refreshThreshold']
        if verbose: winAttrList += winAttrListVerbose
        
        monAttrList = ['name', 'getDistance', 'getWidth', 'currentCalibName']
        monAttrListVerbose = ['_gammaInterpolator', '_gammaInterpolator2']
        if verbose: monAttrList += monAttrListVerbose
        if 'monitor' in winAttrList: # replace 'monitor' with all desired monitor.<attribute>
            i = winAttrList.index('monitor') # retain list-position info, put monitor stuff there
            del(winAttrList[i])
            for monAttr in monAttrList:
                winAttrList.insert(i, 'monitor.' + monAttr)
                i += 1
        for winAttr in winAttrList: 
            try:
                attrValue = eval('win.'+winAttr)
            except AttributeError:
                log.warning('AttributeError in RuntimeInfo._setWindowInfo(): Window instance has no attribute', winAttr)
                continue
            if hasattr(attrValue, '__call__'):
                try:
                    a = attrValue()
                    attrValue = a
                except:
                    print 'Warning: could not get a value from win.'+winAttr+'()  (expects arguments?)'
                    continue
            while winAttr[0]=='_':
                winAttr = winAttr[1:]
            winAttr = winAttr[0].capitalize()+winAttr[1:]
            winAttr = winAttr.replace('Monitor._','Monitor.')
            if winAttr in ['Pos','Size']:
                winAttr += '_pix'
            if winAttr in ['Monitor.getWidth','Monitor.getDistance']:
                winAttr += '_cm'
            if winAttr in ['RefreshThreshold']:
                winAttr += '_sec'
            self['window'+winAttr] = attrValue
        
    def _setPythonInfo(self):
        # External python packages:
        self['pythonNumpyVersion'] = numpy.__version__
        self['pythonScipyVersion'] = scipy.__version__
        self['pythonMatplotlibVersion'] = matplotlib.__version__
        self['pythonPygletVersion'] = pyglet.__version__
        try: from pygame import __version__ as pygameVersion
        except: pygameVersion = '(no pygame)'
        self['pythonPygameVersion'] = pygameVersion
            
        # Python gory details:
        self['pythonFullVersion'] = sys.version.replace('\n',' ')
        self['pythonExecutable'] = sys.executable
        
    def _setOpenGLInfo(self):
        # OpenGL info:
        self['openGLVendor'] = gl_info.get_vendor()
        self['openGLRenderingEngine'] = gl_info.get_renderer()
        self['openGLVersion'] = gl_info.get_version()
        GLextensionsOfInterest=['GL_ARB_multitexture', 'GL_EXT_framebuffer_object','GL_ARB_fragment_program',
            'GL_ARB_shader_objects','GL_ARB_vertex_shader', 'GL_ARB_texture_non_power_of_two','GL_ARB_texture_float']
    
        for ext in GLextensionsOfInterest:
            self['openGLext.'+ext] = bool(gl_info.have_extension(ext))
        
    def __repr__(self):
        """ Return a string that is a legal python (dict), and close to YAML, .ini, and configObj syntax
        """
        info = '{\n#[ PsychoPy2 RuntimeInfoStart ]\n'
        sections = ['PsychoPy', 'Experiment', 'System', 'Window', 'Python', 'OpenGL']
        for sect in sections:
            info += '  #[[ %s ]] #---------\n' % (sect)
            sectKeys = [k for k in self.keys() if k.lower().find(sect.lower()) == 0]
            # get keys for items matching this section label; use reverse-alpha order if easier to read:
            sectKeys.sort(key=str.lower, reverse=bool(sect in ['PsychoPy', 'Window', 'Python', 'OpenGL']))
            for k in sectKeys:
                selfk = self[k] # alter a copy for display purposes
                try:
                    if type(selfk) == type('abc'):
                        selfk = selfk.replace('"','').replace('\n',' ')
                    elif k.find('_ms')> -1: #type(selfk) == type(0.123):
                        selfk = "%.3f" % selfk
                    elif k.find('_sec')> -1:
                        selfk = "%.4f" % selfk
                    elif k.find('_cm')>-1:
                        selfk = "%.1f" % selfk
                except:
                    pass
                if k in ['systemUserProcFlagged','systemUserProcCmdPid'] and len(selfk): # then strcat unique proc names
                    prSet = []
                    for pr in self[k]: # str -> list of lists
                        if pr[0].find(' ')>-1: # add single quotes around file names that contain spaces
                            pr[0] = "'"+pr[0]+"'"
                        prSet += [pr[0]] # first item in sublist is proc name (CMD)
                    selfk = ' '.join(list(set(prSet)))
                if k not in ['systemUserProcFlaggedPID']: # suppress display PID info -- useful at run-time, never useful in an archive
                    #if type(selfk) == type('abc'): 
                        info += '    "%s": "%s",\n' % (k, selfk) 
                    #else:
                    #    info += '    "%s": %s,\n' % (k, selfk)
        info += '#[ PsychoPy2 RuntimeInfoEnd ]\n}\n'
        return info
    
    def __str__(self):
        """ Return a string intended for printing to a log file
        """
        infoLines = self.__repr__()
        info = infoLines.splitlines()[1:-1] # remove enclosing braces from repr
        for i,line in enumerate(info):
            if line.find('openGLext')>-1: # swap order for OpenGL extensions -- much easier to read
                tmp = line.split(':')
                info[i] = ': '.join(['   '+tmp[1].replace(',',''),tmp[0].replace('    ','')+','])
            info[i] = info[i].rstrip(',')
        info = '\n'.join(info).replace('"','')+'\n'
        return info
    
    def _type(self):
        # for debugging
        sk = self.keys()
        sk.sort()
        for k in sk:
            print k,type(self[k]),self[k]
            
def _getSvnVersion(file):
    """Tries to discover the svn version (revision #) for a file.
    
    Not thoroughly tested; completely untested on Windows Vista, Win 7, FreeBSD
    
    :Author:
        - 2010 written by Jeremy Gray
    """
    if not (os.path.exists(file) and os.path.isdir(os.path.join(os.path.dirname(file),'.svn'))):
        return None, None, None
    svnRev, svnLastChangedRev, svnUrl = None, None, None
    if sys.platform in ['darwin', 'linux2', 'freebsd']:
        svninfo,stderr = shellCall('svn info "'+file+'"', stderr=True) # expects a filename, not dir
        for line in svninfo.splitlines():
            if line.find('URL:') == 0:
                svnUrl = line.split()[1]
            elif line.find('Revision: ') == 0:
                svnRev = line.split()[1]
            elif line.find('Last Changed Rev') == 0:
                svnLastChangedRev = line.split()[3]
    else: # worked for me on Win XP sp2 with TortoiseSVN (SubWCRev.exe)
        stdout,stderr = shellCall('subwcrev "'+file+'"', stderr=True)
        for line in stdout.splitlines():
            if line.find('Last committed at revision') == 0:
                svnRev = line.split()[4]
            elif line.find('Updated to revision') == 0:
                svnLastChangedRev = line.split()[3]
    return svnRev, svnLastChangedRev, svnUrl

def _getHgVersion(file):
    """Tries to discover the mercurial (hg) parent and id of a file.
    
    Not thoroughly tested; completely untested on Windows Vista, Win 7, FreeBSD
    
    :Author:
        - 2010 written by Jeremy Gray
    """
    if not os.path.exists(file) or not os.path.isdir(os.path.join(os.path.dirname(file),'.hg')):
        return None
    try:
        hgParentLines,err = shellCall('hg parents "'+file+'"', stderr=True)
        changeset = hgParentLines.splitlines()[0].split()[-1]
    except:
        changeset = ''
    #else: changeset = hgParentLines.splitlines()[0].split()[-1]
    try:
        hgID,err = shellCall('hg id -nibt "'+os.path.dirname(file)+'"', stderr=True)
    except:
        if err: hgID = ''
    
    if len(hgID) or len(changeset):
        return hgID.strip()+' | parent: '+changeset.strip()
    else:
        return None

def _getUserNameUID():
    """Return user name, UID: -1=undefined, 0=assume full root, >499=assume non-root; but its >999 on debian
    
    :Author:
        - 2010 written by Jeremy Gray
    """
    try:
        user = os.environ['USER']
    except:
        user = os.environ['USERNAME']
    uid = '-1' 
    try:
        if sys.platform not in ['win32']:
            uid = os.popen('id -u').read()
        else:
            try:
                uid = '1000'
                if ctypes.windll.shell32.IsUserAnAdmin():
                    uid = '0'
            except:
                raise
    except:
        pass
    return str(user), int(uid)

def _getSha1hexDigest(str):
    """Returns base64 / hex encoded sha1 digest of a file or string, using hashlib.sha1() if available
    
    :Author:
        - 2010 written by Jeremy Gray

    >>> _getSha1hexDigest('1')
    '356a192b7913b04c54574d18c28d46e6395428ab'
    """
    try:
        sha1 = hashlib.sha1()
    except:
        sha1 = sha.new() # deprecated, here for python 2.4
    if os.path.isfile(str):
        f = open(str,'r')
        sha1.update(f.read())
        f.close()
    else:
        sha1.update(str)
    return sha1.hexdigest()
        
def getDateStr():
    """Uses ``time.strftime()``_ to generate a string of the form
    Apr_19_1531 for 19th April 3.31pm.
    This is often useful appended to data filenames to provide unique names
    """
    return time.strftime("%b_%d_%H%M", time.localtime())

def _getExcelCellName(col, row):
    """Returns the excel cell name for a row and column (zero-indexed)
    
    >>> _getExcelCellName(0,0)
    'A1'
    >>> _getExcelCellName(2,1)
    'C2'
    """
    return "%s%i" %(get_column_letter(col+1), row+1)#BEWARE - openpyxl uses indexing at 1, to fit with Excel
    