#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import copy
import numpy as np
import pandas as pd

from psychopy import logging
from psychopy.tools.filetools import (openOutputFile, genDelimiter,
                                      genFilenameFromDelimiter)
from .utils import importConditions
from .base import _BaseTrialHandler, DataHandler


class TrialType(dict):
    """This is just like a dict, except that you can access keys with obj.key
    """
    def __getattribute__(self, name):
        try:  # to get attr from dict in normal way (passing self)
            return dict.__getattribute__(self, name)
        except AttributeError:
            try:
                return self[name]
            except KeyError:
                msg = "TrialType has no attribute (or key) \'%s\'"
                raise AttributeError(msg % name)


class TrialHandler(_BaseTrialHandler):
    """Class to handle trial sequencing and data storage.

    Calls to .next() will fetch the next trial object given to this handler,
    according to the method specified (random, sequential, fullRandom).
    Calls will raise a StopIteration error if trials have finished.

    See demo_trialHandler.py

    The psydat file format is literally just a pickled copy of the
    TrialHandler object that saved it. You can open it with::

            from psychopy.tools.filetools import fromFile
            dat = fromFile(path)

    Then you'll find that `dat` has the following attributes that
    """

    def __init__(self,
                 trialList,
                 nReps,
                 method='random',
                 dataTypes=None,
                 extraInfo=None,
                 seed=None,
                 originPath=None,
                 name='',
                 autoLog=True):
        """

        :Parameters:

            trialList: a simple list (or flat array) of dictionaries
                specifying conditions. This can be imported from an
                excel/csv file using :func:`~psychopy.data.importConditions`

            nReps: number of repeats for all conditions

            method: *'random',* 'sequential', or 'fullRandom'
                'sequential' obviously presents the conditions in the order
                they appear in the list. 'random' will result in a shuffle
                of the conditions on each repeat, but all conditions
                occur once before the second repeat etc. 'fullRandom'
                fully randomises the trials across repeats as well,
                which means you could potentially run all trials of
                one condition before any trial of another.

            dataTypes: (optional) list of names for data storage.
                e.g. ['corr','rt','resp']. If not provided then these
                will be created as needed during calls to
                :func:`~psychopy.data.TrialHandler.addData`

            extraInfo: A dictionary
                This will be stored alongside the data and usually
                describes the experiment and subject ID, date etc.

            seed: an integer
                If provided then this fixes the random number generator to
                use the same pattern of trials, by seeding its startpoint

            originPath: a string describing the location of the
                script / experiment file path. The psydat file format will
                store a copy of the experiment if possible. If
                `originPath==None` is provided here then the TrialHandler
                will still store a copy of the script where it was
                created. If `OriginPath==-1` then nothing will be stored.

        :Attributes (after creation):

            .data - a dictionary (or more strictly, a `DataHandler` sub-
                class of a dictionary) of numpy arrays, one for each data 
                type stored

            .trialList - the original list of dicts, specifying the conditions

            .thisIndex - the index of the current trial in the original
                conditions list

            .nTotal - the total number of trials that will be run

            .nRemaining - the total number of trials remaining

            .thisN - total trials completed so far

            .thisRepN - which repeat you are currently on

            .thisTrialN - which trial number *within* that repeat

            .thisTrial - a dictionary giving the parameters of the current
                trial

            .finished - True/False for have we finished yet

            .extraInfo - the dictionary of extra info as given at beginning

            .origin - the contents of the script or builder experiment that
                created the handler

        """
        self.name = name
        self.autoLog = autoLog

        if trialList in (None, []):  # user wants an empty trialList
            # which corresponds to a list with a single empty entry
            self.trialList = [None]
        # user has hopefully specified a filename
        elif isinstance(trialList, str) and os.path.isfile(trialList):
            # import conditions from that file
            self.trialList = importConditions(trialList)
        else:
            self.trialList = trialList
        # convert any entry in the TrialList into a TrialType object (with
        # obj.key or obj[key] access)
        for n, entry in enumerate(self.trialList):
            if type(entry) == dict:
                self.trialList[n] = TrialType(entry)
        self.nReps = int(nReps)
        self.nTotal = self.nReps * len(self.trialList)
        self.nRemaining = self.nTotal  # subtract 1 each trial
        self.method = method
        self.thisRepN = 0  # records which repetition or pass we are on
        self.thisTrialN = -1  # records trial number within this repetition
        self.thisN = -1
        self.thisIndex = 0  # index of current trial in the conditions list
        self.thisTrial = []
        self.finished = False
        self.extraInfo = extraInfo
        self.seed = seed
        # create dataHandler
        self.data = DataHandler(trials=self)
        if dataTypes != None:
            self.data.addDataType(dataTypes)
        self.data.addDataType('ran')
        self.data['ran'].mask = False  # this is a bool; all entries are valid
        self.data.addDataType('order')
        # generate stimulus sequence
        if self.method in ['random', 'sequential', 'fullRandom']:
            self.sequenceIndices = self._createSequence()
        else:
            self.sequenceIndices = []

        self.originPath, self.origin = self.getOriginPathAndFile(originPath)
        self._exp = None  # the experiment handler that owns me!

    def __iter__(self):
        return self

    def __repr__(self):
        """prints a more verbose version of self as string
        """
        return self.__str__(verbose=True)

    def __str__(self, verbose=False):
        """string representation of the object
        """
        strRepres = 'psychopy.data.{}(\n'.format(self.__class__.__name__)
        attribs = dir(self)

        # data first, then all others
        try:
            data = self.data
        except Exception:
            data = None
        if data:
            strRepres += str('\tdata=')
            strRepres += str(data) + '\n'

        method_string = "<class 'method'>"

        for thisAttrib in attribs:
            # can handle each attribute differently
            if method_string in str(type(getattr(self, thisAttrib))):
                # this is a method
                continue
            elif thisAttrib[0] == '_':
                # the attrib is private
                continue
            elif thisAttrib == 'data':
                # we handled this first
                continue
            elif len(str(getattr(self, thisAttrib))) > 20 and not verbose:
                # just give type of LONG public attribute
                strRepres += str('\t' + thisAttrib + '=')
                strRepres += str(type(getattr(self, thisAttrib))) + '\n'
            else:
                # give the complete contents of attribute
                strRepres += str('\t' + thisAttrib + '=')
                strRepres += str(getattr(self, thisAttrib)) + '\n'

        strRepres += ')'
        return strRepres

    def _createSequence(self):
        """Pre-generates the sequence of trial presentations
        (for non-adaptive methods). This is called automatically when
        the TrialHandler is initialised so doesn't need an explicit call
        from the user.

        The returned sequence has form indices[stimN][repN]
        Example: sequential with 6 trialtypes (rows), 5 reps (cols), returns::

        [[0 0 0 0 0]
        [1 1 1 1 1]
        [2 2 2 2 2]
        [3 3 3 3 3]
        [4 4 4 4 4]
        [5 5 5 5 5]]

        These 30 trials will be returned by .next() in the order:
            0, 1, 2, 3, 4, 5,   0, 1, 2, ...  ... 3, 4, 5

        To add a new type of sequence (as of v1.65.02):
        - add the sequence generation code here
        - adjust "if self.method in [ ...]:" in both __init__ and .next()
        - adjust allowedVals in experiment.py -> shows up in DlgLoopProperties
        Note that users can make any sequence whatsoever outside of PsychoPy,
        and specify sequential order; any order is possible this way.
        """
        # create indices for a single rep
        indices = np.asarray(self._makeIndices(self.trialList), dtype=int)

        rng = np.random.default_rng(seed=self.seed)
        if self.method == 'random':
            sequenceIndices = []
            for thisRep in range(self.nReps):
                thisRepSeq = rng.permutation(indices.flat).tolist()
                sequenceIndices.append(thisRepSeq)
            sequenceIndices = np.transpose(sequenceIndices)
        elif self.method == 'sequential':
            sequenceIndices = np.repeat(indices, self.nReps, 1)
        elif self.method == 'fullRandom':
            # indices*nReps, flatten, shuffle, unflatten; only use seed once
            sequential = np.repeat(indices, self.nReps, 1)  # = sequential
            randomFlat = rng.permutation(sequential.flat)
            sequenceIndices = np.reshape(
                randomFlat, (len(indices), self.nReps))
        if self.autoLog:
            msg = 'Created sequence: %s, trialTypes=%d, nReps=%i, seed=%s'
            vals = (self.method, len(indices), self.nReps, str(self.seed))
            logging.exp(msg % vals)
        return sequenceIndices

    def _makeIndices(self, inputArray):
        """
        Creates an array of tuples the same shape as the input array
        where each tuple contains the indices to itself in the array.

        Useful for shuffling and then using as a reference.
        """
        # make sure its an array of objects (can be strings etc)
        inputArray = np.asarray(inputArray, 'O')
        # get some simple variables for later
        dims = inputArray.shape
        dimsProd = np.product(dims)
        dimsN = len(dims)
        dimsList = list(range(dimsN))
        listOfLists = []
        # this creates space for an array of any objects
        arrayOfTuples = np.ones(dimsProd, 'O')

        # for each dimension create list of its indices (using modulo)
        for thisDim in dimsList:
            prevDimsProd = np.product(dims[:thisDim])
            # NB this means modulus in python
            thisDimVals = np.arange(dimsProd) / prevDimsProd % dims[thisDim]
            listOfLists.append(thisDimVals)

        # convert to array
        indexArr = np.asarray(listOfLists)
        for n in range(dimsProd):
            arrayOfTuples[n] = tuple((indexArr[:, n]))
        return (np.reshape(arrayOfTuples, dims)).tolist()

    def __next__(self):
        """Advances to next trial and returns it.
        Updates attributes; thisTrial, thisTrialN and thisIndex
        If the trials have ended this method will raise a StopIteration error.
        This can be handled with code such as::

            trials = data.TrialHandler(.......)
            for eachTrial in trials:  # automatically stops when done
                # do stuff

        or::

            trials = data.TrialHandler(.......)
            while True:  # ie forever
                try:
                    thisTrial = trials.next()
                except StopIteration:  # we got a StopIteration error
                    break #break out of the forever loop
                # do stuff here for the trial
        """
        # update pointer for next trials
        self.thisTrialN += 1  # number of trial this pass
        self.thisN += 1  # number of trial in total
        self.nRemaining -= 1
        if self.thisTrialN == len(self.trialList):
            # start a new repetition
            self.thisTrialN = 0
            self.thisRepN += 1
        if self.thisRepN >= self.nReps:
            # all reps complete
            self.thisTrial = []
            self.finished = True

        if self.finished == True:
            self._terminate()

        # fetch the trial info
        if self.method in ('random', 'sequential', 'fullRandom'):
            self.thisIndex = self.sequenceIndices[
                self.thisTrialN][self.thisRepN]
            self.thisTrial = self.trialList[self.thisIndex]
            self.data.add('ran', 1)
            self.data.add('order', self.thisN)
        if self.autoLog:
            msg = 'New trial (rep=%i, index=%i): %s'
            vals = (self.thisRepN, self.thisTrialN, self.thisTrial)
            logging.exp(msg % vals, obj=self.thisTrial)
        return self.thisTrial

    next = __next__  # allows user to call without a loop `val = trials.next()`

    def getCurrentTrial(self):
        """Returns the condition for the current trial, without
        advancing the trials.
        """
        return self.trialList[self.thisIndex]

    def getFutureTrial(self, n=1):
        """Returns the condition for n trials into the future,
        without advancing the trials. A negative n returns a previous (past)
        trial. Returns 'None' if attempting to go beyond the last trial.
        """
        # check that we don't go out of bounds for either positive or negative
        if n > self.nRemaining or self.thisN + n < 0:
            return None
        seqs = np.array(self.sequenceIndices).transpose().flat
        condIndex = seqs[self.thisN + n]
        return self.trialList[condIndex]

    def getEarlierTrial(self, n=-1):
        """Returns the condition information from n trials previously.
        Useful for comparisons in n-back tasks. Returns 'None' if trying
        to access a trial prior to the first.
        """
        # treat positive offset values as equivalent to negative ones:
        return self.getFutureTrial(-abs(n))

    def _createOutputArray(self, stimOut, dataOut, delim=None,
                           matrixOnly=False):
        """Does the leg-work for saveAsText and saveAsExcel.
        Combines stimOut with ._parseDataOutput()
        """
        if (stimOut == [] and
                len(self.trialList) and
                hasattr(self.trialList[0], 'keys')):
            stimOut = list(self.trialList[0].keys())
            # these get added somewhere (by DataHandler?)
            if 'n' in stimOut:
                stimOut.remove('n')
            if 'float' in stimOut:
                stimOut.remove('float')

        lines = []
        # parse the dataout section of the output
        dataOut, dataAnal, dataHead = self._createOutputArrayData(dataOut)
        if not matrixOnly:
            thisLine = []
            lines.append(thisLine)
            # write a header line
            for heading in list(stimOut) + dataHead:
                if heading == 'ran_sum':
                    heading = 'n'
                elif heading == 'order_raw':
                    heading = 'order'
                thisLine.append(heading)

        # loop through stimuli, writing data
        for stimN in range(len(self.trialList)):
            thisLine = []
            lines.append(thisLine)
            # first the params for this stim (from self.trialList)
            for heading in stimOut:
                thisLine.append(self.trialList[stimN][heading])

            # then the data for this stim (from self.data)
            for thisDataOut in dataOut:
                # make a string version of the data and then format it
                tmpData = dataAnal[thisDataOut][stimN]
                if hasattr(tmpData, 'tolist'):  # is a numpy array
                    strVersion = str(tmpData.tolist())
                    # for numeric data replace None with a blank cell
                    if tmpData.dtype.kind not in ['SaUV']:
                        strVersion = strVersion.replace('None', '')
                elif tmpData in [None, 'None']:
                    strVersion = ''
                else:
                    strVersion = str(tmpData)

                if strVersion == '()':
                    # 'no data' in masked array should show as "--"
                    strVersion = "--"
                # handle list of values (e.g. rt_raw )
                if (len(strVersion) and
                            strVersion[0] in '[(' and
                            strVersion[-1] in '])'):
                    strVersion = strVersion[1:-1]  # skip first and last chars
                # handle lists of lists (e.g. raw of multiple key presses)
                if (len(strVersion) and
                            strVersion[0] in '[(' and
                            strVersion[-1] in '])'):
                    tup = eval(strVersion)  # convert back to a tuple
                    for entry in tup:
                        # contents of each entry is a list or tuple so keep in
                        # quotes to avoid probs with delim
                        thisLine.append(str(entry))
                else:
                    thisLine.extend(strVersion.split(','))

        # add self.extraInfo
        if (self.extraInfo != None) and not matrixOnly:
            lines.append([])
            # give a single line of space and then a heading
            lines.append(['extraInfo'])
            for key, value in list(self.extraInfo.items()):
                lines.append([key, value])
        return lines

    def _createOutputArrayData(self, dataOut):
        """This just creates the dataOut part of the output matrix.
        It is called by _createOutputArray() which creates the header
        line and adds the stimOut columns
        """
        dataHead = []  # will store list of data headers
        dataAnal = dict([])  # will store data that has been analyzed
        if type(dataOut) == str:
            # don't do list convert or we get a list of letters
            dataOut = [dataOut]
        elif type(dataOut) != list:
            dataOut = list(dataOut)

        # expand any 'all' dataTypes to be full list of available dataTypes
        allDataTypes = list(self.data.keys())
        # treat these separately later
        allDataTypes.remove('ran')
        # ready to go through standard data types
        dataOutNew = []
        for thisDataOut in dataOut:
            if thisDataOut == 'n':
                # n is really just the sum of the ran trials
                dataOutNew.append('ran_sum')
                continue  # no need to do more with this one
            # then break into dataType and analysis
            dataType, analType = thisDataOut.rsplit('_', 1)
            if dataType == 'all':
                dataOutNew.extend(
                    [key + "_" + analType for key in allDataTypes])
                if 'order_mean' in dataOutNew:
                    dataOutNew.remove('order_mean')
                if 'order_std' in dataOutNew:
                    dataOutNew.remove('order_std')
            else:
                dataOutNew.append(thisDataOut)
        dataOut = dataOutNew
        # sort so all datatypes come together, rather than all analtypes
        dataOut.sort()

        # do the various analyses, keeping track of fails (e.g. mean of a
        # string)
        dataOutInvalid = []
        # add back special data types (n and order)
        if 'ran_sum' in dataOut:
            # move n to the first column
            dataOut.remove('ran_sum')
            dataOut.insert(0, 'ran_sum')
        if 'order_raw' in dataOut:
            # move order_raw to the second column
            dataOut.remove('order_raw')
            dataOut.append('order_raw')
        # do the necessary analysis on the data
        for thisDataOutN, thisDataOut in enumerate(dataOut):
            dataType, analType = thisDataOut.rsplit('_', 1)
            if not dataType in self.data:
                # that analysis can't be done
                dataOutInvalid.append(thisDataOut)
                continue
            thisData = self.data[dataType]

            # set the header
            dataHead.append(dataType + '_' + analType)
            # analyse thisData using numpy module
            if analType in dir(np):
                try:
                    # will fail if we try to take mean of a string for example
                    if analType == 'std':
                        thisAnal = np.std(thisData, axis=1, ddof=0)
                        # normalise by N-1 instead. This should work by
                        # setting ddof=1 but doesn't as of 08/2010 (because
                        # of using a masked array?)
                        N = thisData.shape[1]
                        if N == 1:
                            thisAnal *= 0  # prevent a divide-by-zero error
                        else:
                            sqrt = np.sqrt
                            thisAnal = thisAnal * sqrt(N) / sqrt(N - 1)
                    else:
                        thisAnal = eval("np.%s(thisData,1)" % analType)
                except Exception:
                    # that analysis doesn't work
                    dataHead.remove(dataType + '_' + analType)
                    dataOutInvalid.append(thisDataOut)
                    continue  # to next analysis
            elif analType == 'raw':
                thisAnal = thisData
            else:
                raise AttributeError('You can only use analyses from numpy')
            # add extra cols to header if necess
            if len(thisAnal.shape) > 1:
                for n in range(thisAnal.shape[1] - 1):
                    dataHead.append("")
            dataAnal[thisDataOut] = thisAnal

        # remove invalid analyses (e.g. average of a string)
        for invalidAnal in dataOutInvalid:
            dataOut.remove(invalidAnal)
        return dataOut, dataAnal, dataHead

    def saveAsWideText(self, fileName,
                       delim=None,
                       matrixOnly=False,
                       appendFile=True,
                       encoding='utf-8-sig',
                       fileCollisionMethod='rename'):
        """Write a text file with the session, stimulus, and data values
        from each trial in chronological order. Also, return a
        pandas DataFrame containing same information as the file.

        That is, unlike 'saveAsText' and 'saveAsExcel':
         - each row comprises information from only a single trial.
         - no summarizing is done (such as collapsing to produce mean and
           standard deviation values across trials).

        This 'wide' format, as expected by R for creating dataframes, and
        various other analysis programs, means that some information must
        be repeated on every row.

        In particular, if the trialHandler's 'extraInfo' exists, then each
        entry in there occurs in every row. In builder, this will include
        any entries in the 'Experiment info' field of the
        'Experiment settings' dialog. In Coder, this information can be
        set using something like::

            myTrialHandler.extraInfo = {'SubjID': 'Joan Smith',
                                        'Group': 'Control'}

        :Parameters:

            fileName:
                if extension is not specified, '.csv' will be appended
                if the delimiter is ',', else '.tsv' will be appended.
                Can include path info.

            delim:
                allows the user to use a delimiter other than the default
                tab ("," is popular with file extension ".csv")

            matrixOnly:
                outputs the data with no header row.

            appendFile:
                will add this output to the end of the specified file if
                it already exists.

            fileCollisionMethod:
                Collision method passed to
                :func:`~psychopy.tools.fileerrortools.handleFileCollision`

            encoding:
                The encoding to use when saving a the file.
                Defaults to `utf-8-sig`.

        """
        if self.thisTrialN < 0 and self.thisRepN < 0:
            # if both are < 1 we haven't started
            logging.info('TrialHandler.saveAsWideText called but no '
                         'trials completed. Nothing saved')
            return -1

        # set default delimiter if none given
        if delim is None:
            delim = genDelimiter(fileName)

        # create the file or send to stdout
        fileName = genFilenameFromDelimiter(fileName, delim)
        f = openOutputFile(fileName, append=appendFile,
                           fileCollisionMethod=fileCollisionMethod,
                           encoding=encoding)

        # collect parameter names related to the stimuli:
        if self.trialList[0]:
            header = list(self.trialList[0].keys())
        else:
            header = []
        # and then add parameter names related to data (e.g. RT)
        header.extend(self.data.dataTypes)
        # get the extra 'wide' parameter names into the header line:
        header.insert(0, "TrialNumber")
        # this is wide format, so we want fixed information
        # (e.g. subject ID, date, etc) repeated every line if it exists:
        if self.extraInfo is not None:
            for key in self.extraInfo:
                header.insert(0, key)
        df = pd.DataFrame(columns=header)

        # loop through each trial, gathering the actual values:
        dataOut = []
        trialCount = 0
        # total number of trials = number of trialtypes * number of
        # repetitions:

        repsPerType = {}
        entriesList = []
        for rep in range(self.nReps):
            for trialN in range(len(self.trialList)):
                # find out what trial type was on this trial
                trialTypeIndex = self.sequenceIndices[trialN, rep]
                # determine which repeat it is for this trial
                if trialTypeIndex not in repsPerType:
                    repsPerType[trialTypeIndex] = 0
                else:
                    repsPerType[trialTypeIndex] += 1
                # what repeat are we on for this trial type?
                trep = repsPerType[trialTypeIndex]

                # create a dictionary representing each trial:
                nextEntry = {}

                # add a trial number so the original order of the data can
                # always be recovered if sorted during analysis:
                trialCount += 1

                # now collect the value from each trial of vars in header:
                for prmName in header:
                    # the header includes both trial and data variables, so
                    # need to check before accessing:
                    tti = trialTypeIndex
                    if self.trialList[tti] and prmName in self.trialList[tti]:
                        nextEntry[prmName] = self.trialList[tti][prmName]
                    elif prmName in self.data:
                        nextEntry[prmName] = self.data[prmName][tti][trep]
                    elif self.extraInfo != None and prmName in self.extraInfo:
                        nextEntry[prmName] = self.extraInfo[prmName]
                    else:
                        # allow a null value if this parameter wasn't
                        # explicitly stored on this trial:
                        if prmName == "TrialNumber":
                            nextEntry[prmName] = trialCount
                        else:
                            nextEntry[prmName] = ''

                # store this trial's data
                dataOut.append(nextEntry)
                # df = df.append(nextEntry, ignore_index=True)
                entriesList.append(nextEntry)
        df = pd.concat([df, pd.DataFrame(entriesList)])

        if not matrixOnly:
            # write the header row:
            nextLine = ''
            for prmName in header:
                nextLine = nextLine + prmName + delim
            # remove the final orphaned tab character
            f.write(nextLine[:-1] + '\n')

        # write the data matrix:
        for trial in dataOut:
            nextLine = ''
            for prmName in header:
                nextLine = nextLine + str(trial[prmName]) + delim
            # remove the final orphaned tab character
            nextLine = nextLine[:-1]
            f.write(nextLine + '\n')

        if f != sys.stdout:
            f.close()
            logging.info('saved wide-format data to %s' % f.name)

        # Converts numbers to numeric, such as float64, boolean to bool.
        # Otherwise they all are "object" type, i.e. strings
        # df = df.convert_objects()
        return df

    def saveAsJson(self,
                   fileName=None,
                   encoding='utf-8',
                   fileCollisionMethod='rename'):
        raise NotImplementedError('Not implemented for TrialHandler.')

    def addData(self, thisType, value, position=None):
        """Add data for the current trial
        """
        self.data.add(thisType, value, position=None)
        if self.getExp() != None:  # update the experiment handler too
            self.getExp().addData(thisType, value)


class Trial(dict):
    def __init__(self, parent, thisN, thisRepN, thisTrialN, thisIndex, data=None):
        dict.__init__(self)
        # TrialHandler containing this trial
        self.parent = parent
        # state information about this trial
        self.thisN = thisN
        self.thisRepN = thisRepN
        self.thisTrialN = thisTrialN
        self.thisIndex = thisIndex
        # data for this trial
        if data is None:
            data = {}
        else:
            data = data.copy()
        self.data = data

    def __repr__(self):
        return (
            f"<Trial {self.thisN} ({self.thisTrialN} in rep {self.thisRepN}) "
            f"data={ {key: val for key,val in self.items()} }>"
        )

    @property
    def data(self):
        # return self when getting data (so it's modified by modifying data)
        return self

    @data.setter
    def data(self, value: dict):
        # when setting data, clear self...
        self.clear()
        # ... and set each value from the given dict
        for key, val in value.items():
            self[key] = val


class TrialHandler2(_BaseTrialHandler):
    """Class to handle trial sequencing and data storage.

    Calls to .next() will fetch the next trial object given to this handler,
    according to the method specified (random, sequential, fullRandom).
    Calls will raise a StopIteration error if trials have finished.

    See demo_trialHandler.py

    The psydat file format is literally just a pickled copy of the
    TrialHandler object that saved it. You can open it with::

            from psychopy.tools.filetools import fromFile
            dat = fromFile(path)

    Then you'll find that `dat` has the following attributes that
    """

    def __init__(self,
                 trialList,
                 nReps,
                 method='random',
                 dataTypes=None,
                 extraInfo=None,
                 seed=None,
                 originPath=None,
                 name='',
                 autoLog=True):
        """

        :Parameters:

            trialList: filename or a simple list (or flat array) of
                dictionaries specifying conditions

            nReps: number of repeats for all conditions

            method: *'random',* 'sequential', or 'fullRandom'
                'sequential' obviously presents the conditions in the order
                they appear in the list. 'random' will result in a shuffle
                of the conditions on each repeat, but all conditions occur
                once before the second repeat etc. 'fullRandom' fully
                randomises the trials across repeats as well, which means
                you could potentially run all trials of one condition
                before any trial of another.

            dataTypes: (optional) list of names for data storage.
                e.g. ['corr','rt','resp']. If not provided then these
                will be created as needed during calls to
                :func:`~psychopy.data.TrialHandler.addData`

            extraInfo: A dictionary
                This will be stored alongside the data and usually describes
                the experiment and subject ID, date etc.

            seed: an integer
                If provided then this fixes the random number generator to
                use the same pattern of trials, by seeding its startpoint.

            originPath: a string describing the location of the script /
                experiment file path. The psydat file format will store a
                copy of the experiment if possible. If `originPath==None`
                is provided here then the TrialHandler will still store a
                copy of the script where it was
                created. If `OriginPath==-1` then nothing will be stored.

        :Attributes (after creation):

            .data - a dictionary of numpy arrays, one for each data type
                stored

            .trialList - the original list of dicts, specifying the conditions

            .thisIndex - the index of the current trial in the original
                conditions list

            .nTotal - the total number of trials that will be run

            .nRemaining - the total number of trials remaining

            .thisN - total trials completed so far

            .thisRepN - which repeat you are currently on

            .thisTrialN - which trial number *within* that repeat

            .thisTrial - a dictionary giving the parameters of the current
                trial

            .finished - True/False for have we finished yet

            .extraInfo - the dictionary of extra info as given at beginning

            .origin - the contents of the script or builder experiment that
                created the handler

        """
        self.name = name
        self.autoLog = autoLog

        if trialList in [None, [None], []]:  # user wants an empty trialList
            # which corresponds to a list with a single empty entry
            self.trialList = [None]
            self.columns = []
        # user has hopefully specified a filename
        elif isinstance(trialList, str) and os.path.isfile(trialList):
            # import conditions from that file
            self.trialList, self.columns = importConditions(
                trialList,
                returnFieldNames=True)
        else:
            self.trialList = trialList
            self.columns = list(trialList[0].keys())
        # convert any entry in the TrialList into a TrialType object (with
        # obj.key or obj[key] access)
        for n, entry in enumerate(self.trialList):
            if type(entry) == dict:
                self.trialList[n] = TrialType(entry)
        self.nReps = int(nReps)
        self.nTotal = self.nReps * len(self.trialList)
        self.nRemaining = self.nTotal  # subtract 1 each trial
        self.remainingIndices = []
        self.prevIndices = []
        self.method = method
        self.finished = False
        self.extraInfo = extraInfo
        self.seed = seed
        self._rng = np.random.default_rng(seed=seed)
        self._trialAborted = False

        # store a list of dicts, convert to pandas DataFrame on access
        self.elapsed = []
        self.upcoming = None
        self.thisTrial = None

        self.originPath, self.origin = self.getOriginPathAndFile(originPath)
        self._exp = None  # the experiment handler that owns me!

    def __iter__(self):
        return self

    def __repr__(self):
        """prints a more verbose version of self as string
        """
        return self.__str__(verbose=True)

    def __str__(self, verbose=False):
        """string representation of the object
        """
        strRepres = 'psychopy.data.{}(\n'.format(self.__class__.__name__)
        attribs = dir(self)
        # data first, then all others
        try:
            data = self.data
        except Exception:
            strRepres += '\t(no data)\n'
        else:
            strRepres += str('\tdata=')
            strRepres += str(data) + '\n'

        method_string = "<class 'method'>"

        for thisAttrib in attribs:
            # can handle each attribute differently
            if method_string in str(type(getattr(self, thisAttrib))):
                # this is a method
                continue
            elif thisAttrib[0] == '_':
                # the attrib is private
                continue
            elif thisAttrib == 'data':
                # we handled this first
                continue
            elif (len(str(getattr(self, thisAttrib))) > 20 and
                      not verbose):
                # just give type of LONG public attribute
                strRepres += str('\t' + thisAttrib + '=')
                strRepres += str(type(getattr(self, thisAttrib))) + '\n'
            else:
                # give the complete contents of attribute
                strRepres += str('\t' + thisAttrib + '=')
                strRepres += str(getattr(self, thisAttrib)) + '\n'
        strRepres += ')'
        return strRepres

    def __eq__(self, other):
        # We want to ignore the RNG object when doing the comparison.
        self_copy = copy.deepcopy(self)
        other_copy = copy.deepcopy(other)
        del self_copy._rng, other_copy._rng

        result = super(TrialHandler2, self_copy).__eq__(other_copy)
        return result

    @property
    def data(self):
        """Returns a pandas DataFrame of the trial data so far
        Read only attribute - you can't directly modify TrialHandler.data

        Note that data are stored internally as a list of dictionaries,
        one per trial. These are converted to a DataFrame on access.
        """
        return pd.DataFrame(self.elapsed)

    def __next__(self):
        """Advances to next trial and returns it.
        Updates attributes; thisTrial, thisTrialN and thisIndex
        If the trials have ended this method will raise a StopIteration error.
        This can be handled with code such as::

            trials = data.TrialHandler(.......)
            for eachTrial in trials:  # automatically stops when done
                # do stuff

        or::

            trials = data.TrialHandler(.......)
            while True:  # ie forever
                try:
                    thisTrial = trials.next()
                except StopIteration:  # we got a StopIteration error
                    break  # break out of the forever loop
                # do stuff here for the trial
        """
        # mark previous trial as elapsed
        if self.thisTrial is not None:
            self.elapsed.append(self.thisTrial)
        # if upcoming is None, recaculate
        if self.upcoming is None:
            self.calculateUpcoming()
        # if upcoming is empty, finish
        if not self.upcoming:
            self.finished = True
            self.thisTrial = None
            self._terminate()
            raise StopIteration
        # get first upcoming trial
        self.thisTrial = self.upcoming.pop(0)

        # update data structure with new info
        self.addData('thisN', self.thisN)
        self.addData('thisTrialN', self.thisTrialN)
        self.addData('thisRepN', self.thisRepN)
        if self.autoLog:
            msg = 'New trial (rep=%i, index=%i): %s'
            vals = (self.thisRepN, self.thisTrialN, self.thisTrial)
            logging.exp(msg % vals, obj=self.thisTrial)
        
        return self.thisTrial

    next = __next__  # allows user to call without a loop `val = trials.next()`

    @property
    def thisN(self):
        if self.thisTrial is None:
            if len(self.elapsed):
                return self.elapsed[-1].thisN
            else:
                return -1
        return self.thisTrial.thisN

    @property
    def thisTrialN(self):
        if self.thisTrial is None:
            if len(self.elapsed):
                return self.elapsed[-1].thisTrialN
            else:
                return -1
        return self.thisTrial.thisTrialN

    @property
    def thisRepN(self):
        if self.thisTrial is None:
            if len(self.elapsed):
                return self.elapsed[-1].thisRepN
            else:
                return -1
        return self.thisTrial.thisRepN
    
    def calculateUpcoming(self, fromIndex=-1):
        """Rebuild the sequence of trial/state info as if running the trials

        Args:
            fromIndex (int, optional): the point in the sequnce from where to rebuild. Defaults to -1.
        """
        # clear upcoming
        self.upcoming = []
        # start off at 0 trial
        thisTrialN = 0
        thisN = 0
        thisRepN = 0
        # empty array to store indices once taken
        prevIndices = []
        # empty array to store remaining indices
        remainingIndices = []
        # iterate a while loop until we run out of trials
        while thisN < (self.nReps * len(self.trialList)):
            if not remainingIndices:
                # we've just started, or just starting a new repeat
                sequence = list(range(len(self.trialList)))
                if (self.method == 'fullRandom' and
                        thisN < (self.nReps * len(self.trialList))):
                    # we've only just started on a fullRandom sequence
                    sequence *= self.nReps
                    # NB permutation *returns* a shuffled array
                    remainingIndices = list(self._rng.permutation(sequence))
                elif (self.method in ('sequential', 'random') and
                      thisRepN < self.nReps):
                    thisTrialN = 0
                    thisRepN += 1
                    if self.method == 'random':
                        self._rng.shuffle(sequence)  # shuffle (is in-place)
                    remainingIndices = list(sequence)
                else:
                    # we've finished
                    break

            if thisN < len(self.elapsed):
                # trial has already happened - get its value
                thisTrial = self.elapsed[thisN]
                # remove from remaining
                remainingIndices.pop(remainingIndices.index(thisTrial.thisIndex))
            else:
                # fetch the trial info
                if len(self.trialList) == 0:
                    thisIndex = 0
                    thisTrial = {}
                else:
                    thisIndex = remainingIndices.pop(0)
                    # if None then use empty dict
                    thisTrial = self.trialList[thisIndex] or {}
                    thisTrial = copy.copy(thisTrial)
                # make Trial object
                thisTrial = Trial(
                    self,
                    thisN=thisN,
                    thisRepN=thisRepN,
                    thisTrialN=thisTrialN,
                    thisIndex=thisIndex,
                    data=thisTrial
                )
                # otherwise, append trial
                self.upcoming.append(thisTrial)
            # for fullRandom check how many times this has come up before
            if self.method == 'fullRandom':
                thisTrial.thisRepN = prevIndices.count(thisTrial.thisIndex)
            # update prev indices
            prevIndices.append(thisTrial.thisIndex)
            # update pointer for next trials
            thisTrialN += 1  # number of trial this pass
            thisN += 1  # number of trial in total

    def abortCurrentTrial(self, action='random'):
        """Abort the current trial.

        Calling this during an experiment replace this trial. The condition
        related to the aborted trial will be replaced elsewhere in the session
        depending on the `method` in use for sampling conditions.

        Parameters
        ----------
        action : str
            Action to take with the aborted trial. Can be either of `'random'`,
            or `'append'`. The default action is `'random'`.

        Notes
        -----
        * When using `action='random'`, the RNG state for the trial handler is
          not used.

        """
        # clear this trial so it's not appended to elapsed
        self.thisTrial = None
        # clear upcoming trials so they're recalculated on next iteration
        self.upcoming = None

    def getFutureTrial(self, n=1):
        """Returns the condition for n trials into the future, without
        advancing the trials. Returns 'None' if attempting to go beyond
        the last trial.
        """
        # return None if requesting beyond last trial
        if n > len(self.upcoming):
            return None
        # return the corresponding trial from upcoming trials array
        return self.upcoming[n-1]

    def getEarlierTrial(self, n=-1):
        """Returns the condition information from n trials previously.
        Useful for comparisons in n-back tasks. Returns 'None' if trying
        to access a trial prior to the first.
        """
        # treat positive offset values as equivalent to negative ones:
        if n > 0:
            n = n * -1
        # return None if requesting before first trial
        if abs(n) > len(self.upcoming):
            return None
        # return the corresponding trial from elapsed trials array
        return self.elapsed[n]

    def _createOutputArray(self, stimOut, dataOut, delim=None,
                           matrixOnly=False):
        """Does the leg-work for saveAsText and saveAsExcel.
        Combines stimOut with ._parseDataOutput()
        """
        if (stimOut == [] and
                len(self.trialList) and
                hasattr(self.trialList[0], 'keys')):
            stimOut = list(self.trialList[0].keys())
            # these get added somewhere (by DataHandler?)
            if 'n' in stimOut:
                stimOut.remove('n')
            if 'float' in stimOut:
                stimOut.remove('float')

        lines = []
        # parse the dataout section of the output
        dataOut, dataAnal, dataHead = self._createOutputArrayData(dataOut)
        if not matrixOnly:
            thisLine = []
            lines.append(thisLine)
            # write a header line
            for heading in list(stimOut) + dataHead:
                if heading == 'ran_sum':
                    heading = 'n'
                elif heading == 'order_raw':
                    heading = 'order'
                thisLine.append(heading)

        # loop through stimuli, writing data
        for stimN in range(len(self.trialList)):
            thisLine = []
            lines.append(thisLine)
            # first the params for this stim (from self.trialList)
            for heading in stimOut:
                thisLine.append(self.trialList[stimN][heading])

            # then the data for this stim (from self.data)
            for thisDataOut in dataOut:
                # make a string version of the data and then format it
                tmpData = dataAnal[thisDataOut][stimN]
                if hasattr(tmpData, 'tolist'):  # is a numpy array
                    strVersion = str(tmpData.tolist())
                    # for numeric data replace None with a blank cell
                    if tmpData.dtype.kind not in ['SaUV']:
                        strVersion = strVersion.replace('None', '')
                elif tmpData in [None, 'None']:
                    strVersion = ''
                else:
                    strVersion = str(tmpData)

                if strVersion == '()':
                    # 'no data' in masked array should show as "--"
                    strVersion = "--"
                # handle list of values (e.g. rt_raw )
                if (len(strVersion) and
                            strVersion[0] in '[(' and
                            strVersion[-1] in '])'):
                    strVersion = strVersion[1:-1]  # skip first and last chars
                # handle lists of lists (e.g. raw of multiple key presses)
                if (len(strVersion) and
                            strVersion[0] in '[(' and
                            strVersion[-1] in '])'):
                    tup = eval(strVersion)  # convert back to a tuple
                    for entry in tup:
                        # contents of each entry is a list or tuple so keep in
                        # quotes to avoid probs with delim
                        thisLine.append(str(entry))
                else:
                    thisLine.extend(strVersion.split(','))

        # add self.extraInfo
        if (self.extraInfo != None) and not matrixOnly:
            lines.append([])
            # give a single line of space and then a heading
            lines.append(['extraInfo'])
            for key, value in list(self.extraInfo.items()):
                lines.append([key, value])
        return lines

    def _createOutputArrayData(self, dataOut):
        """This just creates the dataOut part of the output matrix.
        It is called by _createOutputArray() which creates the header
        line and adds the stimOut columns
        """
        dataHead = []  # will store list of data headers
        dataAnal = dict([])  # will store data that has been analyzed
        if type(dataOut) == str:
            # don't do list convert or we get a list of letters
            dataOut = [dataOut]
        elif type(dataOut) != list:
            dataOut = list(dataOut)

        # expand any 'all' dataTypes to be full list of available dataTypes
        allDataTypes = list(self.data.keys())
        # ready to go through standard data types
        dataOutNew = []
        for thisDataOut in dataOut:
            if thisDataOut == 'n':
                # n is really just the sum of the ran trials
                dataOutNew.append('ran_sum')
                continue  # no need to do more with this one
            # then break into dataType and analysis
            dataType, analType = thisDataOut.rsplit('_', 1)
            if dataType == 'all':
                dataOutNew.extend(
                    [key + "_" + analType for key in allDataTypes])
                if 'order_mean' in dataOutNew:
                    dataOutNew.remove('order_mean')
                if 'order_std' in dataOutNew:
                    dataOutNew.remove('order_std')
            else:
                dataOutNew.append(thisDataOut)
        dataOut = dataOutNew
        # sort so all datatypes come together, rather than all analtypes
        dataOut.sort()

        # do the various analyses, keeping track of fails (e.g. mean of a
        # string)
        dataOutInvalid = []
        # add back special data types (n and order)
        if 'ran_sum' in dataOut:
            # move n to the first column
            dataOut.remove('ran_sum')
            dataOut.insert(0, 'ran_sum')
        if 'order_raw' in dataOut:
            # move order_raw to the second column
            dataOut.remove('order_raw')
            dataOut.append('order_raw')
        # do the necessary analysis on the data
        for thisDataOutN, thisDataOut in enumerate(dataOut):
            dataType, analType = thisDataOut.rsplit('_', 1)
            if not dataType in self.data:
                # that analysis can't be done
                dataOutInvalid.append(thisDataOut)
                continue
            thisData = self.data[dataType]

            # set the header
            dataHead.append(dataType + '_' + analType)
            # analyse thisData using numpy module
            if analType in dir(np):
                try:
                    # will fail if we try to take mean of a string for example
                    if analType == 'std':
                        thisAnal = np.std(thisData, axis=1, ddof=0)
                        # normalise by N-1 instead. This should work by
                        # setting ddof=1 but doesn't as of 08/2010 (because
                        # of using a masked array?)
                        N = thisData.shape[1]
                        if N == 1:
                            thisAnal *= 0  # prevent a divide-by-zero error
                        else:
                            sqrt = np.sqrt
                            thisAnal = thisAnal * sqrt(N) / sqrt(N - 1)
                    else:
                        thisAnal = eval("np.%s(thisData,1)" % analType)
                except Exception:
                    # that analysis doesn't work
                    dataHead.remove(dataType + '_' + analType)
                    dataOutInvalid.append(thisDataOut)
                    continue  # to next analysis
            elif analType == 'raw':
                thisAnal = thisData
            else:
                raise AttributeError('You can only use analyses from numpy')
            # add extra cols to header if necess
            if len(thisAnal.shape) > 1:
                for n in range(thisAnal.shape[1] - 1):
                    dataHead.append("")
            dataAnal[thisDataOut] = thisAnal

        # remove invalid analyses (e.g. average of a string)
        for invalidAnal in dataOutInvalid:
            dataOut.remove(invalidAnal)
        return dataOut, dataAnal, dataHead

    def saveAsWideText(self, fileName,
                       delim=None,
                       matrixOnly=False,
                       appendFile=True,
                       encoding='utf-8-sig',
                       fileCollisionMethod='rename'):
        """Write a text file with the session, stimulus, and data values
        from each trial in chronological order. Also, return a
        pandas DataFrame containing same information as the file.

        That is, unlike 'saveAsText' and 'saveAsExcel':
         - each row comprises information from only a single trial.
         - no summarising is done (such as collapsing to produce mean and
           standard deviation values across trials).

        This 'wide' format, as expected by R for creating dataframes, and
        various other analysis programs, means that some information must
        be repeated on every row.

        In particular, if the trialHandler's 'extraInfo' exists, then each
        entry in there occurs in every row. In builder, this will include
        any entries in the 'Experiment info' field of the
        'Experiment settings' dialog. In Coder, this information can be set
        using something like::

            myTrialHandler.extraInfo = {'SubjID': 'Joan Smith',
                                        'Group': 'Control'}

        :Parameters:

            fileName:
                if extension is not specified, '.csv' will be appended if
                the delimiter is ',', else '.tsv' will be appended.
                Can include path info.

            delim:
                allows the user to use a delimiter other than the default
                tab ("," is popular with file extension ".csv")

            matrixOnly:
                outputs the data with no header row.

            appendFile:
                will add this output to the end of the specified file if
                it already exists.

            fileCollisionMethod:
                Collision method passed to
                :func:`~psychopy.tools.fileerrortools.handleFileCollision`

            encoding:
                The encoding to use when saving a the file.
                Defaults to `utf-8-sig`.

        """
        if self.thisTrialN < 0 and self.thisRepN < 0:
            # if both are < 1 we haven't started
            logging.info('TrialHandler.saveAsWideText called but no '
                         'trials completed. Nothing saved')
            return -1

        # set default delimiter if none given
        if delim is None:
            delim = genDelimiter(fileName)

        # create the file or send to stdout
        fileName = genFilenameFromDelimiter(fileName, delim)

        with openOutputFile(fileName=fileName, append=appendFile,
                            fileCollisionMethod=fileCollisionMethod,
                            encoding=encoding) as f:
            csvData = self.data.to_csv(sep=delim,
                                       encoding=encoding,
                                       columns=self.columns,  # sets the order
                                       header=(not matrixOnly),
                                       index=False)
            f.write(csvData)

        if (fileName is not None) and (fileName != 'stdout'):
            logging.info('saved wide-format data to %s' % f.name)

    def saveAsJson(self,
                   fileName=None,
                   encoding='utf-8',
                   fileCollisionMethod='rename'):
        """
        Serialize the object to the JSON format.

        Parameters
        ----------
        fileName: string, or None
            the name of the file to create or append. Can include a relative or
            absolute path. If `None`, will not write to a file, but return an
            in-memory JSON object.

        encoding : string, optional
            The encoding to use when writing the file.

        fileCollisionMethod : string
            Collision method passed to
            :func:`~psychopy.tools.fileerrortools.handleFileCollision`. Can be
            either of `'rename'`, `'overwrite'`, or `'fail'`.

        Notes
        -----
        Currently, a copy of the object is created, and the copy's .origin
        attribute is set to an empty string before serializing
        because loading the created JSON file would sometimes fail otherwise.

        The RNG self._rng cannot be serialized as-is, so we store its state in
        self._rng_state so we can restore it when loading.

        """
        self_copy = copy.deepcopy(self)
        self_copy._rng_state = self_copy._rng.bit_generator.state
        del self_copy._rng

        r = (super(TrialHandler2, self_copy)
             .saveAsJson(fileName=fileName,
                         encoding=encoding,
                         fileCollisionMethod=fileCollisionMethod))

        if fileName is None:
            return r

    def addData(self, thisType, value):
        """Add a piece of data to the current trial
        """
        # store in the columns list to help ordering later
        if thisType not in self.columns:
            self.columns.append(thisType)
        # make sure we have a thisTrial
        if self.thisTrial is None:
            if self.upcoming:
                self.thisTrial = self.upcoming.pop(0)
            else:
                self.thisTrial = Trial(
                        self,
                        thisN=0,
                        thisRepN=0,
                        thisTrialN=0,
                        thisIndex=0,
                        data={}
                    )
        # save the actual value in a data dict
        self.thisTrial[thisType] = value
        if self.getExp() is not None:
            # update the experiment handler too
            self.getExp().addData(thisType, value)


class TrialHandlerExt(TrialHandler):
    """A class for handling trial sequences in a *non-counterbalanced design*
    (i.e. *oddball paradigms*). Its functions are a superset of the
    class TrialHandler, and as such, can also be used for normal trial
    handling.

    TrialHandlerExt has the same function names for data storage facilities.

    To use non-counterbalanced designs, all TrialType dict entries in the
    trial list must have a key called "weight". For example, if you want
    trial types A, B, C, and D to have 10, 5, 3, and 2 repetitions per
    block, then the trialList can look like:

    [{Name:'A', ..., weight:10},
     {Name:'B', ..., weight:5},
     {Name:'C', ..., weight:3},
     {Name:'D', ..., weight:2}]

    For experimenters using an excel or csv file for trial list, a column
    called weight is appropriate for this purpose.

    Calls to .next() will fetch the next trial object given to this handler,
    according to the method specified (random, sequential, fullRandom).
    Calls will raise a StopIteration error when all trials are exhausted.

    *Authored by Suddha Sourav at BPN, Uni Hamburg - heavily borrowing
    from the TrialHandler class*
    """

    def __init__(self,
                 trialList,
                 nReps,
                 method='random',
                 dataTypes=None,
                 extraInfo=None,
                 seed=None,
                 originPath=None,
                 name='',
                 autoLog=True):
        """

        :Parameters:

            trialList: a simple list (or flat array) of dictionaries
                specifying conditions. This can be imported from an
                excel / csv file using :func:`~psychopy.data.importConditions`
                For non-counterbalanced designs, each dict entry in
                trialList must have a key called weight!

            nReps: number of repeats for all conditions. When using a
                non-counterbalanced design, nReps is analogous to the number
                of blocks.

            method: *'random',* 'sequential', or 'fullRandom'
                When the weights are not specified:
                'sequential' presents the conditions in the order they appear
                in the list. 'random' will result in a shuffle of the
                conditions on each  repeat, but all conditions occur once
                before the second repeat etc. 'fullRandom' fully randomises
                the trials across repeats as well, which means you could
                potentially run all trials of one condition before any trial
                of another.

                In the presence of weights:
                'sequential' presents each trial type the number of times
                specified by its weight, before moving on to the next type.
                'random' randomizes the presentation order within block.
                'fulLRandom' shuffles trial order across weights an nRep,
                that is, a full shuffling.


            dataTypes: (optional) list of names for data storage. e.g.
                ['corr','rt','resp']. If not provided then these will be
                created as needed during calls to
                :func:`~psychopy.data.TrialHandler.addData`

            extraInfo: A dictionary
                This will be stored alongside the data and usually describes
                the experiment and subject ID, date etc.

            seed: an integer
                If provided then this fixes the random number generator
                to use the same pattern
                of trials, by seeding its startpoint

            originPath: a string describing the location of the script /
                experiment file path. The psydat file format will store a
                copy of the experiment if possible. If `originPath==None`
                is provided here then the TrialHandler will still store a
                copy of the script where it was created. If `OriginPath==-1`
                then nothing will be stored.

        :Attributes (after creation):

            .data - a dictionary of numpy arrays, one for each data type
                stored

            .trialList - the original list of dicts, specifying the conditions

            .thisIndex - the index of the current trial in the original
                conditions list

            .nTotal - the total number of trials that will be run

            .nRemaining - the total number of trials remaining

            .thisN - total trials completed so far

            .thisRepN - which repeat you are currently on

            .thisTrialN - which trial number *within* that repeat

            .thisTrial - a dictionary giving the parameters of the current
                trial

            .finished - True/False for have we finished yet

            .extraInfo - the dictionary of extra info as given at beginning

            .origin - the contents of the script or builder experiment that
                created the handler

            .trialWeights - None if all weights are not specified. If all
                weights are specified, then a list containing the weights
                of the trial types.

        """
        self.name = name
        self.autoLog = autoLog

        if trialList in (None, []):
            # user wants an empty trialList
            # which corresponds to a list with a single empty entry
            self.trialList = [None]
        # user has hopefully specified a filename
        elif isinstance(trialList, str) and os.path.isfile(trialList):
            # import conditions from that file
            self.trialList = importConditions(trialList)
        else:
            self.trialList = trialList
        # convert any entry in the TrialList into a TrialType object (with
        # obj.key or obj[key] access)
        for n, entry in enumerate(self.trialList):
            if type(entry) == dict:
                self.trialList[n] = TrialType(entry)
        self.nReps = nReps
        # Add Su
        if not trialList or not all('weight' in d for d in trialList):
            self.trialWeights = None
            self.nTotal = self.nReps * len(self.trialList)
        else:
            self.trialWeights = [d['weight'] for d in trialList]
            self.nTotal = self.nReps * sum(self.trialWeights)
        self.nRemaining = self.nTotal  # subtract 1 each trial
        self.method = method
        self.thisRepN = 0  # records which repetition or pass we are on
        self.thisTrialN = -1  # records trial number within this repetition
        self.thisN = -1
        self.thisIndex = 0  # index of current trial in the conditions list
        self.thisTrial = []
        self.finished = False
        self.extraInfo = extraInfo
        self.seed = seed
        # create dataHandler
        if self.trialWeights is None:
            self.data = DataHandler(trials=self)
        else:
            self.data = DataHandler(trials=self,
                                    dataShape=[sum(self.trialWeights), nReps])
        if dataTypes is not None:
            self.data.addDataType(dataTypes)
        self.data.addDataType('ran')
        self.data['ran'].mask = False  # bool - all entries are valid
        self.data.addDataType('order')
        # generate stimulus sequence
        if self.method in ('random', 'sequential', 'fullRandom'):
            self.sequenceIndices = self._createSequence()
        else:
            self.sequenceIndices = []

        self.originPath, self.origin = self.getOriginPathAndFile(originPath)
        self._exp = None  # the experiment handler that owns me!

    def _createSequence(self):
        """Pre-generates the sequence of trial presentations (for
        non-adaptive methods). This is called automatically when the
        TrialHandler is initialised so doesn't need an explicit call
        from the user.

        The returned sequence has form indices[stimN][repN]
        Example: sequential with 6 trialtypes (rows), 5 reps (cols), returns::

        [[0 0 0 0 0]
        [1 1 1 1 1]
        [2 2 2 2 2]
        [3 3 3 3 3]
        [4 4 4 4 4]
        [5 5 5 5 5]]

        These 30 trials will be returned by .next() in the order:
            0, 1, 2, 3, 4, 5,   0, 1, 2, ...  ... 3, 4, 5

        Example: random, with 3 trialtypes, where the weights of
        conditions 0,1, and 2 are 3,2, and 1 respectively,
        and a rep value of 5, might return::

        [[0 1 2 0 1]
        [1 0 1 1 1]
        [0 2 0 0 0]
        [0 0 0 1 0]
        [2 0 1 0 2]
        [1 1 0 2 0]]

        These 30 trials will be returned by .next() in the order:
            0, 1, 0, 0, 2, 1,   1, 0, 2, 0, 0, 1, ...
            ... 0, 2, 0  *stopIteration*

        To add a new type of sequence (as of v1.65.02):
        - add the sequence generation code here
        - adjust "if self.method in [ ...]:" in both __init__ and .next()
        - adjust allowedVals in experiment.py -> shows up in DlgLoopProperties
        Note that users can make any sequence whatsoever outside of PsychoPy,
        and specify sequential order; any order is possible this way.
        """
        # create indices for a single rep
        indices = np.asarray(self._makeIndices(self.trialList), dtype=int)

        repeat = np.repeat
        reshape = np.reshape
        rng = np.random.default_rng(seed=self.seed)
        if self.method == 'random':
            seqIndices = []
            if self.trialWeights is None:
                thisRepSeq = indices.flat  # take a fresh copy
            else:
                thisRepSeq = repeat(indices, self.trialWeights)
            for thisRep in range(self.nReps):
                seqIndices.append(rng.permutation(thisRepSeq))
            seqIndices = np.transpose(seqIndices)
        elif self.method == 'sequential':
            if self.trialWeights is None:
                seqIndices = repeat(indices, self.nReps, 1)
            else:
                _base = repeat(indices, self.trialWeights, 0)
                seqIndices = repeat(_base, self.nReps, 1)
        elif self.method == 'fullRandom':
            if self.trialWeights is None:
                # indices * nReps, flatten, shuffle, unflatten;
                # only use seed once
                sequential = np.repeat(indices, self.nReps, 1)  # = sequential
                randomFlat = rng.permutation(sequential.flat)
                seqIndices = np.reshape(
                    randomFlat, (len(indices), self.nReps))
            else:
                _base = repeat(indices, self.trialWeights, 0)
                sequential = repeat(_base, self.nReps, 1)
                randomFlat = rng.permutation(sequential.flat)
                seqIndices = reshape(randomFlat,
                                     (sum(self.trialWeights), self.nReps))

        if self.autoLog:
            # Change
            msg = 'Created sequence: %s, trialTypes=%d, nReps=%d, seed=%s'
            vals = (self.method, len(indices), self.nReps, str(self.seed))
            logging.exp(msg % vals)
        return seqIndices

    def __next__(self):
        """Advances to next trial and returns it.
        Updates attributes; thisTrial, thisTrialN and thisIndex
        If the trials have ended this method will raise a StopIteration error.
        This can be handled with code such as::

            trials = data.TrialHandler(.......)
            for eachTrial in trials:  # automatically stops when done
                # do stuff

        or::

            trials = data.TrialHandler(.......)
            while True:  # ie forever
                try:
                    thisTrial = trials.next()
                except StopIteration:  # we got a StopIteration error
                    break  # break out of the forever loop
                # do stuff here for the trial
        """
        # update pointer for next trials
        self.thisTrialN += 1  # number of trial this pass
        self.thisN += 1  # number of trial in total
        self.nRemaining -= 1

        if self.trialWeights is None:
            if self.thisTrialN == len(self.trialList):
                # start a new repetition
                self.thisTrialN = 0
                self.thisRepN += 1
        else:
            if self.thisTrialN == sum(self.trialWeights):
                # start a new repetition
                self.thisTrialN = 0
                self.thisRepN += 1

        if self.thisRepN >= self.nReps:
            # all reps complete
            self.thisTrial = []
            self.finished = True

        if self.finished == True:
            self._terminate()

        # fetch the trial info
        if self.method in ('random', 'sequential', 'fullRandom'):
            if self.trialWeights is None:
                idx = self.sequenceIndices[self.thisTrialN]
                self.thisIndex = idx[self.thisRepN]
                self.thisTrial = self.trialList[self.thisIndex]
                self.data.add('ran', 1)
                self.data.add('order', self.thisN)
            else:
                idx = self.sequenceIndices[self.thisTrialN]
                self.thisIndex = idx[self.thisRepN]
                self.thisTrial = self.trialList[self.thisIndex]

                self.data.add('ran', 1,
                              position=self.getNextTrialPosInDataHandler())
                # The last call already adds a ran to this trial, so get the
                # current pos now
                self.data.add('order', self.thisN,
                              position=self.getCurrentTrialPosInDataHandler())

        if self.autoLog:
            msg = 'New trial (rep=%i, index=%i): %s'
            vals = (self.thisRepN, self.thisTrialN, self.thisTrial)
            logging.exp(msg % vals, obj=self.thisTrial)
        return self.thisTrial

    next = __next__  # allows user to call without a loop `val = trials.next()`

    def getCurrentTrialPosInDataHandler(self):
        # if there's no trial weights, then the current position is simply
        # [trialIndex, nRepetition]
        if self.trialWeights is None:
            repN = sum(self['ran'][self.trials.thisIndex]) - 1
            position = [self.trials.thisIndex, repN]
        else:
            # if there are trial weights, the situation is slightly more
            # involved, because the same index can be repeated for a number
            # of times. If we had a sequential array, then the rows in
            # DataHandler for that trialIndex would be from
            # sum(trialWeights[begin:trialIndex]) to
            # sum(trialWeights[begin:trialIndex+1]).

            # if we haven't begun the experiment yet, then the last row
            # of the first column is used as the current position,
            # emulating what TrialHandler does. The following two lines
            # also prevents calculating garbage position values in case
            # the first row has a null weight
            if self.thisN < 0:
                return [0, -1]

            firstRowIndex = sum(self.trialWeights[:self.thisIndex])
            lastRowIndex = sum(self.trialWeights[:self.thisIndex + 1])

            # get the number of the trial presented by summing in ran for the
            # rows above and all columns
            # BF-Sourav-29032021: numpy returns float, so cast to int
            nThisTrialPresented = int(round(np.sum(
                self.data['ran'][firstRowIndex:lastRowIndex, :])))

            _tw = self.trialWeights[self.thisIndex]
            dataRowThisTrial = firstRowIndex + (nThisTrialPresented - 1) % _tw
            dataColThisTrial = int((nThisTrialPresented - 1) // _tw)

            position = [dataRowThisTrial, dataColThisTrial]

        return position

    def getNextTrialPosInDataHandler(self):
        # if there's no trial weights, then the current position is
        # simply [trialIndex, nRepetition]
        if self.trialWeights is None:
            repN = sum(self['ran'][self.trials.thisIndex])
            position = [self.trials.thisIndex, repN]
        else:
            # if there are trial weights, the situation is slightly more
            # involved, because the same index can be repeated for a
            # number of times. If we had a sequential array, then the
            # rows in DataHandler for that trialIndex would
            # be from sum(trialWeights[begin:trialIndex]) to
            # sum(trialWeights[begin:trialIndex+1]).

            firstRowIndex = sum(self.trialWeights[:self.thisIndex])
            lastRowIndex = sum(self.trialWeights[:self.thisIndex + 1])

            # get the number of the trial presented by summing in ran for the
            # rows above and all columns
            # BF-Sourav-29032021: numpy returns float, so cast to int
            nThisTrialPresented = int(round(np.sum(
                self.data['ran'][firstRowIndex:lastRowIndex, :])))

            _tw = self.trialWeights[self.thisIndex]
            dataRowThisTrial = firstRowIndex + nThisTrialPresented % _tw
            dataColThisTrial = int(nThisTrialPresented // _tw)

            position = [dataRowThisTrial, dataColThisTrial]

        return position

    def addData(self, thisType, value, position=None):
        """Add data for the current trial
        """

        if self.trialWeights is None:
            pos = None
        else:
            pos = self.getCurrentTrialPosInDataHandler()
        self.data.add(thisType, value, position=pos)
        # change this!
        if self.getExp() is not None:
            # update the experiment handler too:
            self.getExp().addData(thisType, value)

    def _createOutputArrayData(self, dataOut):
        """This just creates the dataOut part of the output matrix.
        It is called by _createOutputArray() which creates the header
        line and adds the stimOut columns
        """

        if self.trialWeights is not None:
            # remember to use other array instead of self.data
            _vals = np.arange(len(self.trialList))
            idx_data = np.repeat(_vals, self.trialWeights)

        # list of data headers
        dataHead = []
        # will store data that has been analyzed
        dataAnal = dict([])
        if type(dataOut) == str:
            # don't do list convert or we get a list of letters
            dataOut = [dataOut]
        elif type(dataOut) != list:
            dataOut = list(dataOut)

        # expand any 'all' dataTypes to the full list of available dataTypes
        allDataTypes = list(self.data.keys())
        # treat these separately later
        allDataTypes.remove('ran')
        # ready to go through standard data types
        dataOutNew = []
        for thisDataOut in dataOut:
            if thisDataOut == 'n':
                # n is really just the sum of the ran trials
                dataOutNew.append('ran_sum')
                continue  # no need to do more with this one
            # then break into dataType and analysis
            dataType, analType = thisDataOut.rsplit('_', 1)
            if dataType == 'all':
                keyType = [key + "_" + analType for key in allDataTypes]
                dataOutNew.extend(keyType)
                if 'order_mean' in dataOutNew:
                    dataOutNew.remove('order_mean')
                if 'order_std' in dataOutNew:
                    dataOutNew.remove('order_std')
            else:
                dataOutNew.append(thisDataOut)
        dataOut = dataOutNew
        # sort so that all datatypes come together, rather than all analtypes
        dataOut.sort()

        # do the various analyses, keeping track of fails (e.g. mean of a
        # string)
        dataOutInvalid = []
        # add back special data types (n and order)
        if 'ran_sum' in dataOut:
            # move n to the first column
            dataOut.remove('ran_sum')
            dataOut.insert(0, 'ran_sum')
        if 'order_raw' in dataOut:
            # move order_raw to the second column
            dataOut.remove('order_raw')
            dataOut.append('order_raw')
        # do the necessary analysis on the data
        for thisDataOutN, thisDataOut in enumerate(dataOut):
            dataType, analType = thisDataOut.rsplit('_', 1)
            if not dataType in self.data:
                # that analysis can't be done
                dataOutInvalid.append(thisDataOut)
                continue

            if self.trialWeights is None:
                thisData = self.data[dataType]
            else:
                # BF_202302210_trialHandlerExt_save_nonnumeric_excel
                # Allow saving non-numeric data to the excel format
                # Previous case: masked arrays for numeric data
                if self.data.isNumeric[dataType]:
                    resizedData = np.ma.masked_array(
                        np.zeros((len(self.trialList),
                                     max(self.trialWeights) * self.nReps)),
                        np.ones((len(self.trialList),
                                    max(self.trialWeights) * self.nReps),
                                   dtype=bool))
                    for curTrialIndex in range(len(self.trialList)):
                        thisDataChunk = self.data[dataType][
                                        idx_data == curTrialIndex, :]
                        padWidth = (max(self.trialWeights) * self.nReps -
                                    np.prod(thisDataChunk.shape))
                        thisDataChunkRowPadded = np.pad(
                            thisDataChunk.transpose().flatten().data,
                            (0, padWidth), mode='constant',
                            constant_values=(0, 0))
                        thisDataChunkRowPaddedMask = np.pad(
                            thisDataChunk.transpose().flatten().mask,
                            (0, padWidth), mode='constant',
                            constant_values=(0, True))

                        thisDataChunkRow = np.ma.masked_array(
                            thisDataChunkRowPadded,
                            mask=thisDataChunkRowPaddedMask)
                        resizedData[curTrialIndex, :] = thisDataChunkRow
                # For non-numeric data, Psychopy uses typical object arrays in-
                # stead of masked arrays. Adjust accordingly, filling with '--'
                # instead of masks
                else:
                    resizedData = np.array(np.zeros((len(self.trialList),
                                                     max(self.trialWeights) *
                                                     self.nReps)), dtype='O')
                    for curTrialIndex in range(len(self.trialList)):
                        thisDataChunk = self.data[dataType][
                                        idx_data == curTrialIndex, :]
                        padWidth = (max(self.trialWeights) * self.nReps -
                                    np.prod(thisDataChunk.shape))
                        thisDataChunkRowPadded = np.pad(
                            thisDataChunk.transpose().flatten().data,
                            (0, padWidth), mode='constant',
                            constant_values=('--', '--'))
                        resizedData[curTrialIndex, :] = thisDataChunkRowPadded

                thisData = resizedData

            # set the header
            dataHead.append(dataType + '_' + analType)
            # analyse thisData using numpy module
            if analType in dir(np):
                try:
                    # this will fail if we try to take mean of a string
                    if analType == 'std':
                        thisAnal = np.std(thisData, axis=1, ddof=0)
                        # normalise by N-1 instead. This should work by
                        # setting ddof=1 but doesn't as of 08/2010
                        # (because of using a masked array?)
                        N = thisData.shape[1]
                        if N == 1:
                            thisAnal *= 0  # prevent a divide-by-zero error
                        else:
                            sqrt = np.sqrt
                            thisAnal = thisAnal * sqrt(N) / sqrt(N - 1)
                    else:
                        thisAnal = eval("np.%s(thisData,1)" % analType)
                except Exception:
                    # that analysis doesn't work
                    dataHead.remove(dataType + '_' + analType)
                    dataOutInvalid.append(thisDataOut)
                    continue  # to next analysis
            elif analType == 'raw':
                thisAnal = thisData
            else:
                raise AttributeError('You can only use analyses from numpy')
            # add extra cols to header if necess
            if len(thisAnal.shape) > 1:
                for n in range(thisAnal.shape[1] - 1):
                    dataHead.append("")
            dataAnal[thisDataOut] = thisAnal

        # remove invalid analyses (e.g. average of a string)
        for invalidAnal in dataOutInvalid:
            dataOut.remove(invalidAnal)
        return dataOut, dataAnal, dataHead

    def saveAsWideText(self,
                       fileName,
                       delim='\t',
                       matrixOnly=False,
                       appendFile=True,
                       encoding='utf-8-sig',
                       fileCollisionMethod='rename'):
        """Write a text file with the session, stimulus, and data values
        from each trial in chronological order.

        That is, unlike 'saveAsText' and 'saveAsExcel':
         - each row comprises information from only a single trial.
         - no summarizing is done (such as collapsing to produce mean and
           standard deviation values across trials).

        This 'wide' format, as expected by R for creating dataframes, and
        various other analysis programs, means that some information must
        be repeated on every row.

        In particular, if the trialHandler's 'extraInfo' exists, then each
        entry in there occurs in every row. In builder, this will include
        any entries in the 'Experiment info' field of the
        'Experiment settings' dialog. In Coder, this information can be set
        using something like::

            myTrialHandler.extraInfo = {'SubjID':'Joan Smith',
                                        'Group':'Control'}

        :Parameters:

            fileName:
                if extension is not specified, '.csv' will be appended if
                the delimiter is ',', else '.txt' will be appended.
                Can include path info.

            delim:
                allows the user to use a delimiter other than the default
                tab ("," is popular with file extension ".csv")

            matrixOnly:
                outputs the data with no header row.

            appendFile:
                will add this output to the end of the specified file if
                it already exists.

            fileCollisionMethod:
                Collision method passed to
                :func:`~psychopy.tools.fileerrortools.handleFileCollision`

            encoding:
                The encoding to use when saving a the file.
                Defaults to `utf-8-sig`.

        """
        if self.thisTrialN < 0 and self.thisRepN < 0:
            # if both are < 1 we haven't started
            logging.info('TrialHandler.saveAsWideText called but no trials'
                         ' completed. Nothing saved')
            return -1

        # set default delimiter if none given
        if delim is None:
            delim = genDelimiter(fileName)

        # create the file or send to stdout
        fileName = genFilenameFromDelimiter(fileName, delim)
        f = openOutputFile(fileName=fileName, append=appendFile,
                           fileCollisionMethod=fileCollisionMethod,
                           encoding=encoding)

        # collect parameter names related to the stimuli:
        if self.trialList[0]:
            header = list(self.trialList[0].keys())
        else:
            header = []
        # and then add parameter names related to data (e.g. RT)
        header.extend(self.data.dataTypes)

        # loop through each trial, gathering the actual values:
        dataOut = []
        trialCount = 0
        # total number of trials = number of trialtypes * number of
        # repetitions:

        repsPerType = {}
        for rep in range(self.nReps):
            if self.trialWeights is None:
                nRows = len(self.trialList)
            else:
                nRows = sum(self.trialWeights)

            for trialN in range(nRows):
                # find out what trial type was on this trial
                trialTypeIndex = self.sequenceIndices[trialN, rep]
                # determine which repeat it is for this trial
                if trialTypeIndex not in repsPerType:
                    repsPerType[trialTypeIndex] = 0
                else:
                    repsPerType[trialTypeIndex] += 1

                # create a dictionary representing each trial:
                # this is wide format, so we want fixed information (e.g.
                # subject ID, date, etc) repeated every line if it exists:
                if self.extraInfo != None:
                    nextEntry = self.extraInfo.copy()
                else:
                    nextEntry = {}

                # add a trial number so the original order of the data can
                # always be recovered if sorted during analysis:
                trialCount += 1
                nextEntry["TrialNumber"] = trialCount

                # what repeat are we on for this trial type?
                trep = repsPerType[trialTypeIndex]
                # collect the value from each trial of the vars in the header:
                tti = trialTypeIndex
                for prmName in header:
                    # the header includes both trial and data variables, so
                    # need to check before accessing:
                    if self.trialList[tti] and prmName in self.trialList[tti]:
                        nextEntry[prmName] = self.trialList[tti][prmName]
                    elif prmName in self.data:
                        if self.trialWeights is None:
                            nextEntry[prmName] = self.data[prmName][tti][trep]
                        else:
                            firstRowIndex = sum(self.trialWeights[:tti])
                            _tw = self.trialWeights[tti]
                            row = firstRowIndex + rep % _tw
                            col = int(rep // _tw)
                            nextEntry[prmName] = self.data[prmName][row][col]
                    else:
                        # allow a null value if this parameter wasn't
                        # explicitly stored on this trial:
                        nextEntry[prmName] = ''

                # store this trial's data
                dataOut.append(nextEntry)

        # get the extra 'wide' parameter names into the header line:
        header.insert(0, "TrialNumber")
        if self.extraInfo is not None:
            for key in self.extraInfo:
                header.insert(0, key)

        # write a header row:
        if not matrixOnly:
            f.write(delim.join(header) + '\n')
        # write the data matrix:
        for trial in dataOut:
            line = delim.join([str(trial[prm]) for prm in header])
            f.write(line + '\n')

        if (fileName is not None) and (fileName != 'stdout'):
            f.close()
            logging.info('saved wide-format data to %s' % f.name)

    def saveAsJson(self,
                   fileName=None,
                   encoding='utf-8',
                   fileCollisionMethod='rename'):
        raise NotImplementedError('Not implemented for TrialHandlerExt.')
