#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

# from future import standard_library
# standard_library.install_aliases()
from builtins import str
from builtins import range
from past.builtins import basestring
import os
import re
import pickle
import time
import codecs
import numpy as np
import pandas as pd

from collections import OrderedDict
from pkg_resources import parse_version

from psychopy import logging
from psychopy.constants import PY3
from psychopy.tools.filetools import pathToString

try:
    import openpyxl
    if parse_version(openpyxl.__version__) >= parse_version('2.4.0'):
        # openpyxl moved get_column_letter to utils.cell
        from openpyxl.utils.cell import get_column_letter
    else:
        from openpyxl.cell import get_column_letter
    from openpyxl.reader.excel import load_workbook
    haveOpenpyxl = True
except ImportError:
    haveOpenpyxl = False

try:
    import xlrd
    haveXlrd = True
except ImportError:
    haveXlrd = False

_nonalphanumeric_re = re.compile(r'\W')  # will match all bad var name chars


def checkValidFilePath(filepath, makeValid=True):
    """Checks whether file path location (e.g. is a valid folder)

    This should also check whether we have write-permissions to the folder
    but doesn't currently do that!

    added in: 1.90.00
    """
    folder = os.path.split(os.path.abspath(filepath))[0]
    if not os.path.isdir(folder):
        os.makedirs(folder)  # spit an error if we fail
    return True


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
    >>> isValidVariableName('')
    (False, "Variables cannot be missing, None, or ''")
    >>> isValidVariableName(None)
    (False, "Variables cannot be missing, None, or ''")
    >>> isValidVariableName(23)
    (False, "Variables must be string-like")
    >>> isValidVariableName('a_b_c')
    (True, '')
    """
    if not name:
        return False, "Variables cannot be missing, None, or ''"
    if not isinstance(name, basestring):
        return False, "Variables must be string-like"
    try:
        name = str(name)  # convert from unicode if possible
    except Exception:
        if type(name) in [str, np.unicode_]:
            msg = ("name %s (type %s) contains non-ASCII characters"
                   " (e.g. accents)")
            raise AttributeError(msg % (name, type(name)))
        else:
            msg = "name %s (type %s) could not be converted to a string"
            raise AttributeError(msg % (name, type(name)))

    if name[0].isdigit():
        return False, "Variables cannot begin with numeric character"
    if _nonalphanumeric_re.search(name):
        return False, "Variables cannot contain punctuation or spaces"
    return True, ''


def _getExcelCellName(col, row):
    """Returns the excel cell name for a row and column (zero-indexed)

    >>> _getExcelCellName(0,0)
    'A1'
    >>> _getExcelCellName(2,1)
    'C2'
    """
    # BEWARE - openpyxl uses indexing at 1, to fit with Excel
    return "%s%i" % (get_column_letter(col + 1), row + 1)


def importTrialTypes(fileName, returnFieldNames=False):
    """importTrialTypes is DEPRECATED (as of v1.70.00)
    Please use `importConditions` for identical functionality.
    """
    logging.warning("importTrialTypes is DEPRECATED (as of v1.70.00). "
                    "Please use `importConditions` for identical "
                    "functionality.")
    return importConditions(fileName, returnFieldNames)


def sliceFromString(sliceString):
    """Convert a text string into a valid slice object
    which can be used as indices for a list or array.

    >>> sliceFromString("0:10")
    slice(0,10,None)
    >>> sliceFromString("0::3")
    slice(0,None,3)
    >>> sliceFromString("-8:")
    slice(-8,None,None)
    """
    sliceArgs = []
    for val in sliceString.split(':'):
        if len(val) == 0:
            sliceArgs.append(None)
        else:
            sliceArgs.append(int(round(float(val))))
            # nb int(round(float(x))) is needed for x='4.3'
    return slice(*sliceArgs)


def indicesFromString(indsString):
    """Convert a text string into a valid list of indices
    """
    # "6"
    try:
        inds = int(round(float(indsString)))
        return [inds]
    except Exception:
        pass
    # "-6::2"
    try:
        inds = sliceFromString(indsString)
        return inds
    except Exception:
        pass
    # "1,4,8"
    try:
        inds = list(eval(indsString))
        return inds
    except Exception:
        pass


def importConditions(fileName, returnFieldNames=False, selection=""):
    """Imports a list of conditions from an .xlsx, .csv, or .pkl file

    The output is suitable as an input to :class:`TrialHandler`
    `trialTypes` or to :class:`MultiStairHandler` as a `conditions` list.

    If `fileName` ends with:

        - .csv:  import as a comma-separated-value file
            (header + row x col)
        - .xlsx: import as Excel 2007 (xlsx) files.
            No support for older (.xls) is planned.
        - .pkl:  import from a pickle file as list of lists
            (header + row x col)

    The file should contain one row per type of trial needed and one column
    for each parameter that defines the trial type. The first row should give
    parameter names, which should:

        - be unique
        - begin with a letter (upper or lower case)
        - contain no spaces or other punctuation (underscores are permitted)


    `selection` is used to select a subset of condition indices to be used
    It can be a list/array of indices, a python `slice` object or a string to
    be parsed as either option.
    e.g.:

        - "1,2,4" or [1,2,4] or (1,2,4) are the same
        - "2:5"       # 2, 3, 4 (doesn't include last whole value)
        - "-10:2:"    # tenth from last to the last in steps of 2
        - slice(-10, 2, None)  # the same as above
        - random(5) * 8  # five random vals 0-8

    """

    def _assertValidVarNames(fieldNames, fileName):
        """screens a list of names as candidate variable names. if all
        names are OK, return silently; else raise  with msg
        """
        fileName = pathToString(fileName)
        if not all(fieldNames):
            msg = ('Conditions file %s: Missing parameter name(s); '
                   'empty cell(s) in the first row?')
            raise ValueError(msg % fileName)
        for name in fieldNames:
            OK, msg = isValidVariableName(name)
            if not OK:
                # tailor message to importConditions
                msg = msg.replace('Variables', 'Parameters (column headers)')
                raise ValueError('Conditions file %s: %s%s"%s"' %
                                  (fileName, msg, os.linesep * 2, name))

    if fileName in ['None', 'none', None]:
        if returnFieldNames:
            return [], []
        return []
    if not os.path.isfile(fileName):
        msg = 'Conditions file not found: %s'
        raise ValueError(msg % os.path.abspath(fileName))

    def pandasToDictList(dataframe):
        """Convert a pandas dataframe to a list of dicts.
        This helper function is used by csv or excel imports via pandas
        """
        # convert the resulting dataframe to a numpy recarray
        trialsArr = dataframe.to_records(index=False)
        # Check for new line characters in strings, and replace escaped characters
        for record in trialsArr:
            for idx, element in enumerate(record):
                if isinstance(element, str):
                    record[idx] = element.replace('\\n', '\n')
        if trialsArr.shape == ():
            # convert 0-D to 1-D with one element:
            trialsArr = trialsArr[np.newaxis]
        fieldNames = list(trialsArr.dtype.names)
        _assertValidVarNames(fieldNames, fileName)

        # convert the record array into a list of dicts
        trialList = []
        for trialN, trialType in enumerate(trialsArr):
            thisTrial = OrderedDict()
            for fieldN, fieldName in enumerate(fieldNames):
                val = trialsArr[trialN][fieldN]

                if isinstance(val, basestring):
                    if val.startswith('[') and val.endswith(']'):
                        # val = eval('%s' %unicode(val.decode('utf8')))
                        val = eval(val)
                elif type(val) == np.string_:
                    val = str(val.decode('utf-8-sig'))
                    # if it looks like a list, convert it:
                    if val.startswith('[') and val.endswith(']'):
                        # val = eval('%s' %unicode(val.decode('utf8')))
                        val = eval(val)
                elif np.isnan(val):
                    val = None
                thisTrial[fieldName] = val
            trialList.append(thisTrial)
        return trialList, fieldNames

    if fileName.endswith('.csv') or (fileName.endswith(('.xlsx','.xls','.xlsm'))
                                     and haveXlrd):
        if fileName.endswith('.csv'):
            trialsArr = pd.read_csv(fileName, encoding='utf-8-sig')
            logging.debug(u"Read csv file with pandas: {}".format(fileName))
        else:
            trialsArr = pd.read_excel(fileName)
            logging.debug(u"Read Excel file with pandas: {}".format(fileName))

        unnamed = trialsArr.columns.to_series().str.contains('^Unnamed: ')
        trialsArr = trialsArr.loc[:, ~unnamed]  # clear unnamed cols
        logging.debug(u"Clearing unnamed columns from {}".format(fileName))
        trialList, fieldNames = pandasToDictList(trialsArr)

    elif fileName.endswith(('.xlsx','.xlsm')):
        if not haveOpenpyxl:
            raise ImportError('openpyxl or xlrd is required for loading excel '
                              'files, but neither was found.')

        # data_only was added in 1.8
        if parse_version(openpyxl.__version__) < parse_version('1.8'):
            wb = load_workbook(filename=fileName)
        else:
            wb = load_workbook(filename=fileName, data_only=True)
        ws = wb.worksheets[0]

        logging.debug(u"Read excel file with openpyxl: {}".format(fileName))
        try:
            # in new openpyxl (2.3.4+) get_highest_xx is deprecated
            nCols = ws.max_column
            nRows = ws.max_row
        except Exception:
            # version openpyxl 1.5.8 (in Standalone 1.80) needs this
            nCols = ws.get_highest_column()
            nRows = ws.get_highest_row()

        # get parameter names from the first row header
        fieldNames = []
        for colN in range(nCols):
            if parse_version(openpyxl.__version__) < parse_version('2.0'):
                fieldName = ws.cell(_getExcelCellName(col=colN, row=0)).value
            else:
                # From 2.0, cells are referenced with 1-indexing: A1 == cell(row=1, column=1)
                fieldName = ws.cell(row=1, column=colN + 1).value
            fieldNames.append(fieldName)
        _assertValidVarNames(fieldNames, fileName)

        # loop trialTypes
        trialList = []
        for rowN in range(1, nRows):  # skip header first row
            thisTrial = {}
            for colN in range(nCols):
                if parse_version(openpyxl.__version__) < parse_version('2.0'):
                    val = ws.cell(_getExcelCellName(col=colN, row=0)).value
                else:
                    # From 2.0, cells are referenced with 1-indexing: A1 == cell(row=1, column=1)
                    val = ws.cell(row=rowN + 1, column=colN + 1).value
                # if it looks like a list or tuple, convert it
                if (isinstance(val, basestring) and
                        (val.startswith('[') and val.endswith(']') or
                                 val.startswith('(') and val.endswith(')'))):
                    val = eval(val)
                fieldName = fieldNames[colN]
                thisTrial[fieldName] = val
            trialList.append(thisTrial)

    elif fileName.endswith('.pkl'):
        f = open(fileName, 'rb')
        # Converting newline characters.
        if PY3:
            # 'b' is necessary in Python3 because byte object is 
            # returned when file is opened in binary mode.
            buffer = f.read().replace(b'\r\n',b'\n').replace(b'\r',b'\n')
        else:
            buffer = f.read().replace('\r\n','\n').replace('\r','\n')
        try:
            trialsArr = pickle.loads(buffer)
        except Exception:
            raise IOError('Could not open %s as conditions' % fileName)
        f.close()
        trialList = []
        if PY3:
            # In Python3, strings returned by pickle() is unhashable.
            # So, we have to convert them to str.
            trialsArr = [[str(item) if isinstance(item, str) else item
                          for item in row] for row in trialsArr]
        fieldNames = trialsArr[0]  # header line first
        _assertValidVarNames(fieldNames, fileName)
        for row in trialsArr[1:]:
            thisTrial = {}
            for fieldN, fieldName in enumerate(fieldNames):
                # type is correct, being .pkl
                thisTrial[fieldName] = row[fieldN]
            trialList.append(thisTrial)
    else:
        raise IOError('Your conditions file should be an '
                      'xlsx, csv or pkl file')

    # if we have a selection then try to parse it
    if isinstance(selection, basestring) and len(selection) > 0:
        selection = indicesFromString(selection)
        if not isinstance(selection, slice):
            for n in selection:
                try:
                    assert n == int(n)
                except AssertionError:
                    raise TypeError("importConditions() was given some "
                                    "`indices` but could not parse them")

    # the selection might now be a slice or a series of indices
    if isinstance(selection, slice):
        trialList = trialList[selection]
    elif len(selection) > 0:
        allConds = trialList
        trialList = []
        for ii in selection:
            trialList.append(allConds[int(round(ii))])

    logging.exp('Imported %s as conditions, %d conditions, %d params' %
                (fileName, len(trialList), len(fieldNames)))
    if returnFieldNames:
        return (trialList, fieldNames)
    else:
        return trialList


def createFactorialTrialList(factors):
    """Create a trialList by entering a list of factors with names (keys)
    and levels (values) it will return a trialList in which all factors
    have been factorially combined (so for example if there are two factors
    with 3 and 5 levels the trialList will be a list of 3*5 = 15, each
    specifying the values for a given trial

    Usage::

        trialList = createFactorialTrialList(factors)

    :Parameters:

        factors : a dictionary with names (keys) and levels (values) of the
            factors

    Example::

        factors={"text": ["red", "green", "blue"],
                 "letterColor": ["red", "green"],
                 "size": [0, 1]}
        mytrials = createFactorialTrialList(factors)
    """

    # the first step is to place all the factorial combinations in a list of
    # lists
    tempListOfLists = [[]]
    for key in factors:
        # this takes the levels of each factor as a set of values
        # (a list) at a time
        alist = factors[key]
        tempList = []
        for value in alist:
            # now we loop over the values in a given list,
            # and add each value of the other lists
            for iterList in tempListOfLists:
                tempList.append(iterList + [key, value])
        tempListOfLists = tempList

    # this second step is so we can return a list in the format of trialList
    trialList = []
    for atrial in tempListOfLists:
        keys = atrial[0::2]  # the even elements are keys
        values = atrial[1::2]  # the odd elements are values
        atrialDict = {}
        for i in range(len(keys)):
            # this combines the key with the value
            atrialDict[keys[i]] = values[i]
        # append one trial at a time to the final trialList
        trialList.append(atrialDict)

    return trialList


def bootStraps(dat, n=1):
    """Create a list of n bootstrapped resamples of the data

    SLOW IMPLEMENTATION (Python for-loop)

    Usage:
        ``out = bootStraps(dat, n=1)``

    Where:
        dat
            an NxM or 1xN array (each row is a different condition, each
            column is a different trial)
        n
            number of bootstrapped resamples to create

        out
            - dim[0]=conditions
            - dim[1]=trials
            - dim[2]=resamples
    """
    dat = np.asarray(dat)
    if len(dat.shape) == 1:
        # have presumably been given a series of data for one stimulus
        # adds a dimension (arraynow has shape (1,Ntrials))
        dat = np.array([dat])

    nTrials = dat.shape[1]
    # initialise a matrix to store output
    resamples = np.zeros(dat.shape + (n,), dat.dtype)
    rand = np.random.rand
    for stimulusN in range(dat.shape[0]):
        thisStim = dat[stimulusN, :]  # fetch data for this stimulus
        for sampleN in range(n):
            indices = np.floor(nTrials * rand(nTrials)).astype('i')
            resamples[stimulusN, :, sampleN] = np.take(thisStim, indices)
    return resamples


def functionFromStaircase(intensities, responses, bins=10):
    """Create a psychometric function by binning data from a staircase
    procedure. Although the default is 10 bins Jon now always uses 'unique'
    bins (fewer bins looks pretty but leads to errors in slope estimation)

    usage::

        intensity, meanCorrect, n = functionFromStaircase(intensities,
                                                          responses, bins)

    where:
            intensities
                are a list (or array) of intensities to be binned

            responses
                are a list of 0,1 each corresponding to the equivalent
                intensity value

            bins
                can be an integer (giving that number of bins) or 'unique'
                (each bin is made from aa data for exactly one intensity
                value)

            intensity
                a numpy array of intensity values (where each is the center
                of an intensity bin)

            meanCorrect
                a numpy array of mean % correct in each bin

            n
                a numpy array of number of responses contributing to each mean
    """
    # convert to arrays
    try:
        # concatenate if multidimensional
        intensities = np.concatenate(intensities)
        responses = np.concatenate(responses)
    except Exception:
        intensities = np.array(intensities)
        responses = np.array(responses)

    # sort the responses
    sort_ii = np.argsort(intensities)
    sortedInten = np.take(intensities, sort_ii)
    sortedResp = np.take(responses, sort_ii)

    binnedResp = []
    binnedInten = []
    nPoints = []
    if bins == 'unique':
        intensities = np.round(intensities, decimals=8)
        uniqueIntens = np.unique(intensities)
        for thisInten in uniqueIntens:
            theseResps = responses[intensities == thisInten]
            binnedInten.append(thisInten)
            binnedResp.append(np.mean(theseResps))
            nPoints.append(len(theseResps))
    else:
        pointsPerBin = len(intensities)/bins
        for binN in range(bins):
            start = int(round(binN * pointsPerBin))
            stop = int(round((binN + 1) * pointsPerBin))
            thisResp = sortedResp[start:stop]
            thisInten = sortedInten[start:stop]
            binnedResp.append(np.mean(thisResp))
            binnedInten.append(np.mean(thisInten))
            nPoints.append(len(thisInten))

    return binnedInten, binnedResp, nPoints


def getDateStr(format="%Y_%b_%d_%H%M"):
    """Uses ``time.strftime()``_ to generate a string of the form
    2012_Apr_19_1531 for 19th April 3.31pm, 2012.
    This is often useful appended to data filenames to provide unique names.
    To include the year: getDateStr(format="%Y_%b_%d_%H%M")
    returns '2011_Mar_16_1307' depending on locale, can have unicode chars
    in month names, so utf_8_decode them
    For date in the format of the current localization, do:
        data.getDateStr(format=locale.nl_langinfo(locale.D_T_FMT))
    """
    now = time.strftime(format, time.localtime())
    if PY3:
        return now
    else:
        try:
            now_decoded = codecs.utf_8_decode(now)[0]
        except UnicodeDecodeError:
            # '2011_03_16_1307'
            now_decoded = time.strftime("%Y_%m_%d_%H%M", time.localtime())

        return now_decoded
