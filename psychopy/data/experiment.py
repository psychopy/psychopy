#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import sys
import copy
import pickle
import atexit
import pandas as pd

from psychopy import constants, clock
from psychopy import logging
from psychopy.data.trial import TrialHandler2
from psychopy.tools.filetools import (openOutputFile, genDelimiter,
                                      genFilenameFromDelimiter)
from psychopy.localization import _translate
from .utils import checkValidFilePath
from .base import _ComparisonMixin


class ExperimentHandler(_ComparisonMixin):
    """A container class for keeping track of multiple loops/handlers

    Useful for generating a single data file from an experiment with many
    different loops (e.g. interleaved staircases or loops within loops

    :usage:

        exp = data.ExperimentHandler(name="Face Preference",version='0.1.0')

    """
    
    def __init__(self,
                 name='',
                 version='',
                 extraInfo=None,
                 runtimeInfo=None,
                 originPath=None,
                 savePickle=True,
                 saveWideText=True,
                 sortColumns=False,
                 dataFileName='',
                 autoLog=True,
                 appendFiles=False):
        """
        :parameters:

            name : a string or unicode
                As a useful identifier later

            version : usually a string (e.g. '1.1.0')
                To keep track of which version of the experiment was run

            extraInfo : a dictionary
                Containing useful information about this run
                (e.g. {'participant':'jwp','gender':'m','orientation':90} )

            runtimeInfo : :class:`psychopy.info.RunTimeInfo`
                Containing information about the system as detected at
                runtime

            originPath : string or unicode
                The path and filename of the originating script/experiment
                If not provided this will be determined as the path of the
                calling script.

            dataFileName : string
                This is defined in advance and the file will be saved at any
                point that the handler is removed or discarded (unless
                .abort() had been called in advance).
                The handler will attempt to populate the file even in the
                event of a (not too serious) crash!

            savePickle : True (default) or False

            saveWideText : True (default) or False

            sortColumns : str or bool
                How (if at all) to sort columns in the data file, if none is given to saveAsWideText. Can be:
                - "alphabetical", "alpha", "a" or True: Sort alphabetically by header name
                - "priority", "pr" or "p": Sort according to priority
                - other: Do not sort, columns remain in order they were added


            autoLog : True (default) or False
        """
        self.loops = []
        self.loopsUnfinished = []
        self.name = name
        self.version = version
        self.runtimeInfo = runtimeInfo
        if extraInfo is None:
            self.extraInfo = {}
        else:
            self.extraInfo = extraInfo
        self.originPath = originPath
        self.savePickle = savePickle
        self.saveWideText = saveWideText
        self.dataFileName = dataFileName
        self.sortColumns = sortColumns
        self.thisEntry = {}
        self.entries = []  # chronological list of entries
        self._paramNamesSoFar = []
        self.dataNames = ['thisRow.t', 'notes']  # names of all the data (eg. resp.keys)
        self.columnPriority = {
            'thisRow.t': constants.priority.CRITICAL - 1,
            'notes': constants.priority.MEDIUM - 1,
        }
        self.autoLog = autoLog
        self.appendFiles = appendFiles
        self.status = constants.NOT_STARTED

        if dataFileName in ['', None]:
            logging.warning('ExperimentHandler created with no dataFileName'
                            ' parameter. No data will be saved in the event '
                            'of a crash')
        else:
            # fail now if we fail at all!
            checkValidFilePath(dataFileName, makeValid=True)
        atexit.register(self.close)

    def __del__(self):
        self.close()

    @property
    def currentLoop(self):
        """
        Return the loop which we are currently in, this will either be a handle to a loop, such as
        a :class:`~psychopy.data.TrialHandler` or :class:`~psychopy.data.StairHandler`, or the handle
        of the :class:`~psychopy.data.ExperimentHandler` itself if we are not in a loop.
        """
        # If there are unfinished (aka currently active) loops, return the most recent
        if len(self.loopsUnfinished):
            return self.loopsUnfinished[-1]
        # If we are not in a loop, return handle to experiment handler
        return self

    def addLoop(self, loopHandler):
        """Add a loop such as a :class:`~psychopy.data.TrialHandler`
        or :class:`~psychopy.data.StairHandler`
        Data from this loop will be included in the resulting data files.
        """
        self.loops.append(loopHandler)
        self.loopsUnfinished.append(loopHandler)
        # keep the loop updated that is now owned
        loopHandler.setExp(self)

    def loopEnded(self, loopHandler):
        """Informs the experiment handler that the loop is finished and not to
        include its values in further entries of the experiment.

        This method is called by the loop itself if it ends its iterations,
        so is not typically needed by the user.
        """
        if loopHandler in self.loopsUnfinished:
            self.loopsUnfinished.remove(loopHandler)

    def _getAllParamNames(self):
        """Returns the attribute names of loop parameters (trialN etc)
        that the current set of loops contain, ready to build a wide-format
        data file.
        """
        names = copy.deepcopy(self._paramNamesSoFar)
        # get names (or identifiers) for all contained loops
        for thisLoop in self.loops:
            theseNames, vals = self._getLoopInfo(thisLoop)
            for name in theseNames:
                if name not in names:
                    names.append(name)
        return names

    def _getExtraInfo(self):
        """Get the names and vals from the extraInfo dict (if it exists)
        """
        if type(self.extraInfo) != dict:
            names = []
            vals = []
        else:
            names = list(self.extraInfo)
            vals = list(self.extraInfo.values())
        return names, vals

    def _getLoopInfo(self, loop):
        """Returns the attribute names and values for the current trial
        of a particular loop. Does not return data inputs from the subject,
        only info relating to the trial execution.
        """
        names = []
        vals = []
        name = loop.name
        # standard attributes
        for attr in ('thisRepN', 'thisTrialN', 'thisN', 'thisIndex',
                     'stepSizeCurrent'):
            if hasattr(loop, attr):
                attrName = name + '.' + attr.replace('Current', '')
                # append the attribute name and the current value
                names.append(attrName)
                vals.append(getattr(loop, attr))
        # method of constants
        if hasattr(loop, 'thisTrial'):
            trial = loop.thisTrial
            if hasattr(trial, 'items'):
                # is a TrialList object or a simple dict
                for attr, val in list(trial.items()):
                    if attr not in self._paramNamesSoFar:
                        self._paramNamesSoFar.append(attr)
                    names.append(attr)
                    vals.append(val)
        # single StairHandler
        elif hasattr(loop, 'intensities'):
            names.append(name + '.intensity')
            if len(loop.intensities) > 0:
                vals.append(loop.intensities[-1])
            else:
                vals.append(None)

        return names, vals

    def addData(self, name, value, row=None, priority=None):
        """
        Add the data with a given name to the current experiment.

        Typically the user does not need to use this function; if you added
        your data to the loop and had already added the loop to the
        experiment then the loop will automatically inform the experiment
        that it has received data.

        Multiple data name/value pairs can be added to any given entry of
        the data file and is considered part of the same entry until the
        nextEntry() call is made.

        e.g.::

            # add some data for this trial
            exp.addData('resp.rt', 0.8)
            exp.addData('resp.key', 'k')
            # end of trial - move to next line in data output
            exp.nextEntry()

        Parameters
        ----------
        name : str
            Name of the column to add data as.
        value : any
            Value to add
        row : int or None
            Row in which to add this data. Leave as None to add to the current entry.
        priority : int
            Priority value to set the column to - higher priority columns appear nearer to the start of
            the data file. Use values from `constants.priority` as landmark values:
            - CRITICAL: Always at the start of the data file, generally reserved for Routine start times
            - HIGH: Important columns which are near the front of the data file
            - MEDIUM: Possibly important columns which are around the middle of the data file
            - LOW: Columns unlikely to be important which are at the end of the data file
            - EXCLUDE: Always at the end of the data file, actively marked as unimportant

        """
        if name not in self.dataNames:
            self.dataNames.append(name)
        # could just copy() every value, but not always needed, so check:
        try:
            hash(value)
        except TypeError:
            # unhashable type (list, dict, ...) == mutable, so need a copy()
            value = copy.deepcopy(value)

        # if value is a Timestamp, resolve to a simple value
        if isinstance(value, clock.Timestamp):
            value = value.resolve()

        # get entry from row number
        entry = self.thisEntry
        if row is not None:
            entry = self.entries[row]
        entry[name] = value

        # set priority if given
        if priority is not None:
            self.setPriority(name, priority)

    def getPriority(self, name):
        """
        Get the priority value for a given column. If no priority value is
        stored, returns best guess based on column name.

        Parameters
        ----------
        name : str
            Column name

        Returns
        -------
        int
            The priority value stored/guessed for this column, most likely a value from `constants.priority`, one of:
            - CRITICAL (30): Always at the start of the data file, generally reserved for Routine start times
            - HIGH (20): Important columns which are near the front of the data file
            - MEDIUM (10): Possibly important columns which are around the middle of the data file
            - LOW (0): Columns unlikely to be important which are at the end of the data file
            - EXCLUDE (-10): Always at the end of the data file, actively marked as unimportant
        """
        if name not in self.columnPriority:
            # store priority if not specified already
            self.columnPriority[name] = self._guessPriority(name)
        # return stored priority
        return self.columnPriority[name]

    def _guessPriority(self, name):
        """
        Get a best guess at the priority of a column based on its name

        Parameters
        ----------
        name : str
            Name of the column

        Returns
        -------
        int
            One of the following:
            - HIGH (19): Important columns which are near the front of the data file
            - MEDIUM (9): Possibly important columns which are around the middle of the data file
            - LOW (-1): Columns unlikely to be important which are at the end of the data file

            NOTE: Values returned from this function are 1 less than values in `constants.priority`,
            columns whose priority was guessed are behind equivalently prioritised columns whose priority
            was specified.
        """
        # if there's a dot, get attribute name
        if "." in name:
            name = name.split(".")[-1]

        # start off assuming low priority
        priority = constants.priority.LOW
        # if name is one of identified likely high priority columns, it's medium priority
        if name in [
            "keys", "rt", "x", "y", "leftButton", "numClicks", "numLooks", "clip", "response", "value",
            "frameRate", "participant"
        ]:
            priority = constants.priority.MEDIUM

        return priority - 1

    def setPriority(self, name, value=constants.priority.HIGH):
        """
        Set the priority of a column in the data file.

        Parameters
        ----------
        name : str
            Name of the column, e.g. `text.started`
        value : int
            Priority value to set the column to - higher priority columns appear nearer to the start of
            the data file. Use values from `constants.priority` as landmark values:
            - CRITICAL (30): Always at the start of the data file, generally reserved for Routine start times
            - HIGH (20): Important columns which are near the front of the data file
            - MEDIUM (10): Possibly important columns which are around the middle of the data file
            - LOW (0): Columns unlikely to be important which are at the end of the data file
            - EXCLUDE (-10): Always at the end of the data file, actively marked as unimportant
        """
        self.columnPriority[name] = value

    def addAnnotation(self, value):
        """
        Add an annotation at the current point in the experiment

        Parameters
        ----------
        value : str
            Value of the annotation
        """
        self.addData("notes", value)

    def timestampOnFlip(self, win, name, format=float):
        """Add a timestamp (in the future) to the current row

        Parameters
        ----------

        win : psychopy.visual.Window
            The window object that we'll base the timestamp flip on
        name : str
            The name of the column in the datafile being written,
            such as 'myStim.stopped'
        format : str, class or None
            Format in which to return time, see clock.Timestamp.resolve() for more info. Defaults to `float`.
        """
        # make sure the name is used when writing the datafile
        if name not in self.dataNames:
            self.dataNames.append(name)
        # tell win to record timestamp on flip
        win.timeOnFlip(self.thisEntry, name, format=format)

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        """
        Status of this experiment, from psychopy.constants.

        Parameters
        ----------
        value : int
            One of the values from psychopy.constants.
        """
        # log change
        valStr = {
            constants.NOT_STARTED: "NOT_STARTED",
            constants.STARTED: "STARTED",
            constants.PAUSED: "PAUSED",
            constants.RECORDING: "RECORDING",
            constants.STOPPED: "STOPPED",
            constants.SEEKING: "SEEKING",
            constants.STOPPING: "STOPPING",
            constants.INVALID: "INVALID"
        }[value]
        logging.exp(f"{self.name}: status = {valStr}", obj=self)
        # make change
        self._status = value

    def pause(self):
        """
        Set status to be PAUSED.
        """
        # warn if experiment is already paused
        if self.status == constants.PAUSED:
            logging.warn(_translate(
                "Attempted to pause experiment '{}', but it is already paused. "
                "Status will remain unchanged.".format(self.name)
            ))
        # set own status
        self.status = constants.PAUSED

    def resume(self):
        """
        Set status to be STARTED.
        """
        # warn if experiment is already running
        if self.status == constants.STARTED:
            logging.warn(_translate(
                "Attempted to resume experiment '{}', but it is not paused. "
                "Status will remain unchanged.".format(self.name)
            ))
        # set own status
        self.status = constants.STARTED

    def stop(self):
        """
        Set status to be FINISHED.
        """
        # warn if experiment is already paused
        if self.status == constants.FINISHED:
            logging.warn(_translate(
                "Attempted to stop experiment '{}', but it is already stopping. "
                "Status will remain unchanged.".format(self.name)
            ))
        # set own status
        self.status = constants.STOPPED
    
    def getFutureTrial(self, n=1):
        """
        Returns the condition for n trials into the future, without
        advancing the trials. Returns 'None' if attempting to go beyond
        the last trial in the current loop, or if there is no current loop.
        """
        # return None if there isn't a TrialHandler2 active
        if not isinstance(self.currentLoop, TrialHandler2):
            return None
        # get future trial from current loop
        return self.currentLoop.getFutureTrial(n)
    
        
    def getFutureTrials(self, n=1, start=0):
        """
        Returns Trial objects for a given range in the future. Will start looking at `start` trials 
        in the future and will return n trials from then, so e.g. to get all trials from 2 in the 
        future to 5 in the future you would use `start=2` and `n=3`.

        Parameters
        ----------
        n : int, optional
            How many trials into the future to look, by default 1
        start : int, optional
            How many trials into the future to start looking at, by default 0
        
        Returns
        -------
        list[Trial or None]
            List of Trial objects n long. Any trials beyond the last trial are None.
        """
        # blank list to store trials in
        trials = []
        # iterate through n trials
        for i in range(n):
            # add each to the list
            trials.append(
                self.getFutureTrial(start + i)
            )
        
        return trials

    def nextEntry(self):
        """Calling nextEntry indicates to the ExperimentHandler that the
        current trial has ended and so further addData() calls correspond
        to the next trial.
        """
        this = self.thisEntry
        # fetch data from each (potentially-nested) loop
        for thisLoop in self.loopsUnfinished:
            names, vals = self._getLoopInfo(thisLoop)
            for n, name in enumerate(names):
                this[name] = vals[n]
        # add the extraInfo dict to the data
        if type(self.extraInfo) == dict:
            this.update(self.extraInfo)
        self.entries.append(this)
        # add new entry with its
        self.thisEntry = {}

    def getAllEntries(self):
        """Fetches a copy of all the entries including a final (orphan) entry
        if that exists. This allows entries to be saved even if nextEntry() is
        not yet called.

        :return: copy (not pointer) to entries
        """
        # check for orphan final data (not committed as a complete entry)
        entries = copy.copy(self.entries)
        if self.thisEntry:  # thisEntry is not empty
            entries.append(self.thisEntry)
        return entries

    def saveAsWideText(self,
                       fileName,
                       delim='auto',
                       matrixOnly=False,
                       appendFile=None,
                       encoding='utf-8-sig',
                       fileCollisionMethod='rename',
                       sortColumns=None):
        """Saves a long, wide-format text file, with one line representing
        the attributes and data for a single trial. Suitable for analysis
        in R and SPSS.

        If `appendFile=True` then the data will be added to the bottom of
        an existing file. Otherwise, if the file exists already it will
        be kept and a new file will be created with a slightly different
        name. If you want to overwrite the old file, pass 'overwrite'
        to ``fileCollisionMethod``.

        If `matrixOnly=True` then the file will not contain a header row,
        which can be handy if you want to append data to an existing file
        of the same format.

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

            encoding:
                The encoding to use when saving a the file.
                Defaults to `utf-8-sig`.

            fileCollisionMethod:
                Collision method passed to
                :func:`~psychopy.tools.fileerrortools.handleFileCollision`

            sortColumns : str or bool
                How (if at all) to sort columns in the data file. Can be:
                - "alphabetical", "alpha", "a" or True: Sort alphabetically by header name
                - "priority", "pr" or "p": Sort according to priority
                - other: Do not sort, columns remain in order they were added

        """
        # set default delimiter if none given
        delimOptions = {
                'comma': ",",
                'semicolon': ";",
                'tab': "\t"
            }
        if delim == 'auto':
            delim = genDelimiter(fileName)
        elif delim in delimOptions:
            delim = delimOptions[delim]

        if appendFile is None:
            appendFile = self.appendFiles

        # create the file or send to stdout
        fileName = genFilenameFromDelimiter(fileName, delim)
        f = openOutputFile(fileName, append=appendFile,
                           fileCollisionMethod=fileCollisionMethod,
                           encoding=encoding)

        names = self._getAllParamNames()
        names.extend(self.dataNames)
        # names from the extraInfo dictionary
        names.extend(self._getExtraInfo()[0])
        if len(names) < 1:
            logging.error("No data was found, so data file may not look as expected.")
        # if sort columns not specified, use default from self
        if sortColumns is None:
            sortColumns = self.sortColumns
        # sort names as requested
        if sortColumns in ("alphabetical", "alpha", "a", True):
            # sort alphabetically
            names.sort()
        elif sortColumns in ("priority", "pr" or "p"):
            # map names to their priority
            priorityMap = []
            for name in names:
                priority = self.columnPriority.get(name, self._guessPriority(name))
                priorityMap.append((priority, name))
            names = [name for priority, name in sorted(priorityMap, reverse=True)]
        # write a header line
        if not matrixOnly:
            for heading in names:
                f.write(u'%s%s' % (heading, delim))
            f.write('\n')

        # write the data for each entry
        for entry in self.getAllEntries():
            for name in names:
                if name in entry:
                    ename = str(entry[name])
                    if ',' in ename or '\n' in ename:
                        fmt = u'"%s"%s'
                    else:
                        fmt = u'%s%s'
                    f.write(fmt % (entry[name], delim))
                else:
                    f.write(delim)
            f.write('\n')
        if f != sys.stdout:
            f.close()
        logging.info('saved data to %r' % f.name)

    def saveAsPickle(self, fileName, fileCollisionMethod='rename'):
        """Basically just saves a copy of self (with data) to a pickle file.

        This can be reloaded if necessary and further analyses carried out.

        :Parameters:

            fileCollisionMethod: Collision method passed to
            :func:`~psychopy.tools.fileerrortools.handleFileCollision`
        """
        # Store the current state of self.savePickle and self.saveWideText
        # for later use:
        # We are going to set both to False before saving,
        # so PsychoPy won't try to save again after loading the pickled
        # .psydat file from disk.
        #
        # After saving, the initial state of self.savePickle and
        # self.saveWideText is restored.
        #
        # See
        # https://groups.google.com/d/msg/psychopy-dev/Z4m_UX88q8U/UGuh1eeyjMEJ
        savePickle = self.savePickle
        saveWideText = self.saveWideText

        self.savePickle = False
        self.saveWideText = False

        origEntries = self.entries
        self.entries = self.getAllEntries()

        # otherwise use default location
        if not fileName.endswith('.psydat'):
            fileName += '.psydat'

        with openOutputFile(fileName=fileName, append=False,
                           fileCollisionMethod=fileCollisionMethod) as f:
            pickle.dump(self, f)

        if (fileName is not None) and (fileName != 'stdout'):
            logging.info('saved data to %s' % f.name)

        self.entries = origEntries  # revert list of completed entries post-save
        self.savePickle = savePickle
        self.saveWideText = saveWideText

    def getJSON(self, priorityThreshold=constants.priority.EXCLUDE+1):
        """
        Get the experiment data as a JSON string.

        Parameters
        ----------
        priorityThreshold : int
            Output will only include columns whose priority is greater than or equal to this value. Use values in
            psychopy.constants.priority as a guideline for priority levels. Default is -9 (constants.priority.EXCLUDE +
            1)

        Returns
        -------
        str
            JSON string with the following fields:
            - 'type': Indicates that this is data from an ExperimentHandler (will always be "trials_data")
            - 'trials': `list` of `dict`s representing requested trials data
            - 'priority': `dict` of column names
        """
        # get columns which meet threshold
        cols = [col for col in self.dataNames if self.getPriority(col) >= priorityThreshold]
        # convert just relevant entries to a DataFrame
        trials = pd.DataFrame(self.entries, columns=cols).fillna(value="")
        # put in context
        context = {
            'type': "trials_data",
            'trials': trials.to_dict(orient="records"),
            'priority': self.columnPriority,
            'threshold': priorityThreshold,
        }

        return json.dumps(context, indent=True, allow_nan=False, default=str)
        
    def close(self):
        if self.dataFileName not in ['', None]:
            if self.autoLog:
                msg = 'Saving data for %s ExperimentHandler' % self.name
                logging.debug(msg)
            if self.savePickle:
                self.saveAsPickle(self.dataFileName)
            if self.saveWideText:
                self.saveAsWideText(self.dataFileName + '.csv')
        self.abort()
        self.autoLog = False

    def abort(self):
        """Inform the ExperimentHandler that the run was aborted.

        Experiment handler will attempt automatically to save data
        (even in the event of a crash if possible). So if you quit your
        script early you may want to tell the Handler not to save out
        the data files for this run. This is the method that allows you
        to do that.
        """
        self.savePickle = False
        self.saveWideText = False
