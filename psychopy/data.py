# -*- coding: utf-8 -*-
"""Routines for handling data structures and analysis"""
# Part of the PsychoPy library
# Copyright (C) 2010 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy import misc, gui, log
import psychopy
import cPickle, string, sys, platform, os, time, copy, csv
import numpy
from scipy import optimize, special
from matplotlib import mlab#used for importing csv files

try:
    import openpyxl
    from openpyxl.cell import get_column_letter
    from openpyxl.reader.excel import load_workbook
    haveOpenpyxl=True
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
        
         :Parameters:
         
            fileName:
                will have .dlm appended (so you can double-click it to
                open in excel) and can include path info.       
            
            stimOut:
                the stimulus attributes to be output. To use this you need to
                use a list of dictionaries and give here the names of dictionary keys
                that you want as strings         
            
            dataOut:
                a list of strings specifying the dataType and the analysis to
                be performed,in the form `dataType_analysis`. The data can be any of the types that
                you added using trialHandler.data.add() and the analysis can be either
                'raw' or most things in the numpy library, including;
                'mean','std','median','max','min'...
                The default values will output the raw, mean and std of all datatypes found 
            
            delim:
                allows the user to use a delimiter other than tab ("," is popular with file extension ".csv")
            
            matrixOnly:
                outputs the data with no header row or extraInfo attached
            
            appendFile:
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
        """Add data for the current trial
        """
        self.data.add(thisType, value, position=None)
    
    def saveAsExcel(self,fileName, sheetName='rawData',
                    stimOut=[], 
                    dataOut=('n','all_mean','all_std', 'all_raw'),
                    matrixOnly=False,                    
                    appendFile=True,
                    ):
        """
        Save a summary data file in Excel OpenXML format workbook (:term:`xlsx`) for processing 
        in most spreadsheet packages. This format is compatible with 
        versions of Excel (2007 or greater) and and with OpenOffice (>=3.0).
        
        It has the advantage over the simpler text files (see :func:`TrialHandler.saveAsText()` )
        that data can be stored in multiple named sheets within the file. So you could have a single file
        named after your experiment and then have one worksheet for each participant. Or you could have 
        one file for each participant and then multiple sheets for repeated sessions etc. 
        
        The file extension `.xlsx` will be added if not given already.
        
        :Parameters:
        
            fileName: string
                the name of the file to create or append. Can include relative or absolute path
        
            sheetName: string
                the name of the worksheet within the file 
                
            stimOut: list of strings
                the attributes of the trial characteristics to be output. To use this you need to have provided  
                a list of dictionaries specifying to trialList parameter of the TrialHandler 
                and give here the names of strings specifying entries in that dictionary         
            
            dataOut: list of strings
                specifying the dataType and the analysis to
                be performed, in the form `dataType_analysis`. The data can be any of the types that
                you added using trialHandler.data.add() and the analysis can be either
                'raw' or most things in the numpy library, including 
                'mean','std','median','max','min'. e.g. `rt_max` will give a column of max reaction 
                times across the trials assuming that `rt` values have been stored. 
                The default values will output the raw, mean and std of all datatypes found 
            
            appendFile: True or False
                If False any existing file with this name will be overwritten. If True then a new worksheet will be appended.
                If a worksheet already exists with that name a number will be added to make it unique.
            
        
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
            wb.properties.creator='PsychoPy'+psychopy.__version__
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
                    try: 
                        ws.cell(_getExcelCellName(col=colN,row=stimN+1)).value = float(tmpData)#if it can conver to a number (from numpy) then do it
                    except:#some thi
                        ws.cell(_getExcelCellName(col=colN,row=stimN+1)).value = unicode(tmpData)#else treat as unicode
                    colN+=1
                else:
                    for entry in tmpData:
                        try: 
                            ws.cell(_getExcelCellName(col=colN,row=stimN+1)).value = float(entry)
                        except:#some thi
                            ws.cell(_getExcelCellName(col=colN,row=stimN+1)).value = unicode(entry)
                        colN+=1
        
        #add self.extraInfo
        rowN = len(self.trialList)+2
        if (self.extraInfo != None) and not matrixOnly:
            ws.cell(_getExcelCellName(0,rowN)).value = 'extraInfo'; rowN+=1
            for key,val in self.extraInfo.items():
                ws.cell(_getExcelCellName(0,rowN)).value = unicode(key)+':'
                ws.cell(_getExcelCellName(1,rowN)).value = (val)
                rowN+=1

        ew.save(filename = fileName)



def importTrialList(fileName):
        """Imports a list of TrialTypes from an Excel (.xlsx) or comma-separated-value file. 
        
        If `fileName` ends .csv then import as a comma-separated-value file will be used. 
        All other filenames will be treated as Excel 2007 (xlsx) files. Sorry no 
        support for older versions of Excel file are planned.
        
        The file should contain one row per type of trial needed and one column 
        for each parameter that defines the trial type. The first row should give
        parameter names, which should;
            
            - be unique
            - begin with a letter (upper or lower case)
            - contain no spaces or other punctuation (underscores are permitted)
        
        """
        if not os.path.isfile(fileName):
            raise ImportError, 'TrialTypes file not found: %s' %os.path.abspath(fileName)
        
        if fileName.endswith('.csv'):
            #use csv import library to fetch the fieldNames
            f = open(fileName,'rU')#the U converts lineendings to os.linesep
            #lines = f.read().split(os.linesep)#csv module is temperamental with line endings
            reader = csv.reader(f)#.split(os.linesep))
            fieldNames = reader.next()
            #use matplotlib to import data and intelligently check for data types
            #all data in one column will be given a single type (e.g. if one cell is string, all will be set to string)
            trialsArr = mlab.csv2rec(f)
            f.close()
            #convert the record array into a list of dicts
            trialList = []
            for trialN, trialType in enumerate(trialsArr):
                thisTrial ={}
                for fieldN, fieldName in enumerate(fieldNames):
                    OK, msg = isValidVariableName(fieldName)
                    if not OK:
                        #provide error message about incorrect header
                        msg.replace('Variables','Parameters (column headers)') #tailor message to this usage
                        raise ImportError, '%s: %s' %(fieldName, msg)
                    val = trialsArr[trialN][fieldN]
                    #if it looks like a list, convert it
                    if type(val)==numpy.string_ and val.startswith('[') and val.endswith(']'):
                        exec('val=%s' %val)
                    thisTrial[fieldName] = val
                trialList.append(thisTrial)
        else:
            wb = load_workbook(filename = fileName)
            ws = wb.worksheets[0]
            nCols = ws.get_highest_column()
            nRows = ws.get_highest_row()
                       
            #get headers
            fieldNames = [] 
            for colN in range(nCols):
                #get filedName and chack valid
                fieldName = ws.cell(_getExcelCellName(col=colN, row=0)).value
                OK, msg = isValidVariableName(fieldName)
                if not OK:
                    #provide error message about incorrect header
                    msg.replace('Variables','Parameters (column headers)') #tailor message to this usage
                    raise ImportError, '%s: %s' %(fieldName, msg)
                else: 
                    fieldNames.append(fieldName)
                
            #loop trialTypes
            trialList = []
            for rowN in range(nRows)[1:]:#not first row
                thisTrial={}
                for colN in range(nCols):
                    fieldName = fieldNames[colN]
                    val = ws.cell(_getExcelCellName(col=colN, row=rowN)).value
                    #if it looks like a list, convert it
                    if type(val)==str and val.startswith('[') and val.endswith(']'):
                        exec('val=%s' %val)
                    thisTrial[fieldName] = val
                trialList.append(thisTrial)
            
        return trialList

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
        
    def saveAsExcel(self,fileName, sheetName=None,
                   matrixOnly=False,
                  ):
        """
        Save a summary data file in Excel OpenXML format workbook (:term:`xlsx`) for processing 
        in most spreadsheet packages. This format is compatible with 
        versions of Excel (2007 or greater) and and with OpenOffice (>=3.0).
        
        It has the advantage over the simpler text files (see :func:`TrialHandler.saveAsText()` )
        that data can be stored in multiple named sheets within the file. So you could have a single file
        named after your experiment and then have one worksheet for each participant. Or you could have 
        one file for each participant and then multiple sheets for repeated sessions etc. 
        
        The file extension `.xlsx` will be added if not given already.
        
        The file will contain a set of values specifying the staircase level ('intensity') at each
        reversal, a list of reversal indices (trial numbers), the raw staircase/intensity 
        level on *every* trial and the corresponding responses of the participant on every trial.
        
        :Parameters:
        
            fileName: string
                the name of the file to create or append. Can include relative or absolute path
        
            sheetName: string
                the name of the worksheet within the file 
                
            appendFile: True or False
                If False any existing file with this name will be overwritten. If True then a new worksheet will be appended.
                If a worksheet already exists with that name a number will be added to make it unique.
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
            wb.properties.creator='PsychoPy'+psychopy.__version__
            newWorkbook=True
        
        ew = ExcelWriter(workbook = wb)
        
        if newWorkbook:
            ws = wb.worksheets[0]
            ws.title=sheetName
        else:
            ws=wb.create_sheet()
            ws.title=sheetName

        #write the data
        #reversals data
        ws.cell('A1').value = 'Reversal Intensities'
        ws.cell('B1').value = 'Reversal Indices'
        for revN, revIntens in enumerate(self.reversalIntensities):
            ws.cell(_getExcelCellName(col=0,row=revN+1)).value = revIntens
            ws.cell(_getExcelCellName(col=1,row=revN+1)).value = self.reversalPoints[revN]
        
        #trials data
        ws.cell('C1').value = 'All Intensities'
        ws.cell('D1').value = 'All Responses'
        for intenN, intensity in enumerate(self.intensities):
            ws.cell(_getExcelCellName(col=2,row=intenN+1)).value = intensity
            ws.cell(_getExcelCellName(col=3,row=intenN+1)).value = self.responses[intenN]
        
        #add self.extraInfo
        rowN = 0
        if (self.extraInfo != None) and not matrixOnly:
            ws.cell(_getExcelCellName(col=6,row=rowN)).value = 'extraInfo'; rowN+=1
            for key,val in self.extraInfo.items():
                ws.cell(_getExcelCellName(col=6,row=rowN)).value = unicode(key)+u':'
                ws.cell(_getExcelCellName(col=7,row=rowN)).value = unicode(val)
                rowN+=1

        ew.save(filename = fileName)
        
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

def getDateStr():
    """Uses ``time.strftime()``_ to generate a string of the form
    Apr_19_1531 for 19th April 3.31pm.
    This is often useful appended to data filenames to provide unique names
    """
    return time.strftime("%b_%d_%H%M", time.localtime())

def isValidVariableName(name):
    """Checks whether a certain string could be used as a valid variable.
    
    Usage:: 
        
        OK, msg = isValidVariableName(name)
        
    >>> isValidVariableName('name')
    (True, '')
    >>> isValidVariableName('0name')
    (False, 'Variables cannot begin with numeric character')
    >>> isValidVariableName('first second')
    (False, 'Variables cannot contain punctuation or spaces')
    """
    punctuation = " -[]()+*¬£@!$%^&/\{}~.,?'|:;"
    try:
        name=str(name)#convert from unicode if possible
    except:
        if type(name)==unicode:
            raise AttributeError, "name %s (type %s) contains non-ASCII characters (e.g. accents)" %name
        else:
            raise AttributeError, "name %s (type %s) could not be converted to a string" %name
            
    if name[0].isdigit():
        return False, "Variables cannot begin with numeric character"
    for chr in punctuation:
        if chr in name: return False, "Variables cannot contain punctuation or spaces"
    return True, ""
    
def _getExcelCellName(col, row):
    """Returns the excel cell name for a row and column (zero-indexed)
    
    >>> _getExcelCellName(0,0)
    'A1'
    >>> _getExcelCellName(2,1)
    'C2'
    """
    return "%s%i" %(get_column_letter(col+1), row+1)#BEWARE - openpyxl uses indexing at 1, to fit with Excel
    