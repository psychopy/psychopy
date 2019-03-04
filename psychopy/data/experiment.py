#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

# from future import standard_library
# standard_library.install_aliases()
from builtins import str
import sys
import copy
import pickle
import atexit

from psychopy import logging
from psychopy.tools.filetools import (openOutputFile, genDelimiter,
                                      genFilenameFromDelimiter)
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
                 dataFileName='',
                 autoLog=True):
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
                Containining information about the system as detected at
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
        self.thisEntry = {}
        self.entries = []  # chronological list of entries
        self._paramNamesSoFar = []
        self.dataNames = []  # names of all the data (eg. resp.keys)
        self.autoLog = autoLog
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

    def addData(self, name, value):
        """Add the data with a given name to the current experiment.

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
        """
        if name not in self.dataNames:
            self.dataNames.append(name)
        # could just copy() every value, but not always needed, so check:
        try:
            hash(value)
        except TypeError:
            # unhashable type (list, dict, ...) == mutable, so need a copy()
            value = copy.deepcopy(value)
        self.thisEntry[name] = value

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
                       delim=None,
                       matrixOnly=False,
                       appendFile=False,
                       encoding='utf-8-sig',
                       fileCollisionMethod='rename',
                       sortColumns=False):
        """Saves a long, wide-format text file, with one line representing
        the attributes and data for a single trial. Suitable for analysis
        in R and SPSS.

        If `appendFile=True` then the data will be added to the bottom of
        an existing file. Otherwise, if the file exists already it will
        be overwritten

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

            sortColumns:
                will sort columns alphabetically by header name if True

        """
        # set default delimiter if none given
        if delim is None:
            delim = genDelimiter(fileName)

        # create the file or send to stdout
        fileName = genFilenameFromDelimiter(fileName, delim)
        f = openOutputFile(fileName, append=appendFile,
                           fileCollisionMethod=fileCollisionMethod,
                           encoding=encoding)

        names = self._getAllParamNames()
        names.extend(self.dataNames)
        # names from the extraInfo dictionary
        names.extend(self._getExtraInfo()[0])
        # sort names if requested
        if sortColumns:
            names.sort()
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
