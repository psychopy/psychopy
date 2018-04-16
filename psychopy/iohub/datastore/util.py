#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).
from __future__ import division, absolute_import, print_function

from builtins import next
from past.builtins import basestring
from builtins import object
import numbers  # numbers.Integral is like (int, long) but supports Py3
from tables import *
import os
from collections import namedtuple
import json

from ..errors import print2err

from pkg_resources import parse_version
import tables
if parse_version(tables.__version__) < parse_version('3'):
    from tables import openFile as open_file
    walk_groups = "walkGroups"
    list_nodes = "listNodes"
    get_node = "getNode"
    read_where = "readWhere"
else:
    from tables import open_file
    walk_groups = "walk_groups"
    list_nodes = "list_nodes"
    get_node = "get_node"
    read_where = "read_where"


_hubFiles = []

def openHubFile(filepath, filename, mode):
    """
    Open an HDF5 DataStore file and register it so that it is closed even on interpreter crash.
    """
    global _hubFiles
    hubFile = open_file(os.path.join(filepath, filename), mode)
    _hubFiles.append(hubFile)
    return hubFile


def displayDataFileSelectionDialog(starting_dir=None):
    """Shows a FileDialog and lets you select a .hdf5 file to open for
    processing."""
    from psychopy.gui.qtgui import fileOpenDlg

    fdlg = FileDialog(
        message="Select a ioHub DataStore File",
        defaultDir=starting_dir,
        fileTypes=FileDialog.IODATA_FILES,
        display_index=0)

    status, filePathList = fdlg.show()

    if status != FileDialog.OK_RESULT:
        print(" Data File Selection Cancelled.")
        return None

    return filePathList[0]


def displayEventTableSelectionDialog(
        title,
        list_label,
        list_values,
        default=u'Select'):
    from psychopy import gui
    if default not in list_values:
        list_values.insert(0, default)
    else:
        list_values.remove(list_values)
        list_values.insert(0, default)

    selection_dict = dict(list_label=list_values)
    dlg_info = dict(selection_dict)
    infoDlg = gui.DlgFromDict(dictionary=dlg_info, title=title)
    if not infoDlg.OK:
        return None

    while list(dlg_info.values())[0] == default and infoDlg.OK:
            dlg_info=dict(selection_dict)
            infoDlg = gui.DlgFromDict(dictionary=dlg_info, title=title)

    if not infoDlg.OK:
        return None

    return list(dlg_info.values())[0]
########### Experiment / Experiment Session Based Data Access #################


class ExperimentDataAccessUtility(object):
    """The ExperimentDataAccessUtility  provides a simple, high level, way to
    access data saved in an ioHub DataStore HDF5 file. Data access is done by
    providing information at an experiment and session level, as well as
    specifying the ioHub Event types you want to retieve data for.

    An instance of the ExperimentDataAccessUtility class is created by providing
    the location and name of the file to read, as well as any session code
    filtering you want applied to the retieved datasets.

    Args:
        hdfFilePath (str): The path of the directory the DataStore HDF5 file is in.

        hdfFileName (str): The name of the DataStore HDF5 file.

        experimentCode (str): If multi-experiment support is enabled for the DataStore file, this arguement can be used to specify what experiment data to load based on the experiment_code given. NOTE: Multi-experiment data file support is not well tested and should not be used at this point.

        sessionCodes (str or list): The experiment session code to filter data by. If a list of codes is given, then all codes in the list will be used.

    Returns:
        object: the created instance of the ExperimentDataAccessUtility, ready to get your data!

    """

    def __init__(
            self,
            hdfFilePath,
            hdfFileName,
            experimentCode=None,
            sessionCodes=[],
            mode='r'):
        """An instance of the ExperimentDataAccessUtility class is created by
        providing the location and name of the file to read, as well as any
        session code filtering you want applied to the retieved datasets.

        Args:
            hdfFilePath (str): The path of the directory the DataStore HDF5 file is in.

            hdfFileName (str): The name of the DataStore HDF5 file.

            experimentCode (str): If multi-experiment support is enabled for the DataStore file, this arguement can be used to specify what experiment data to load based on the experiment_code given. NOTE: Multi-experiment data file support is not well tested and should not be used at this point.

            sessionCodes (str or list): The experiment session code to filter data by. If a list of codes is given, then all codes in the list will be used.

        Returns:
            object: the created instance of the ExperimentDataAccessUtility, ready to get your data!

        """
        self.hdfFilePath = hdfFilePath
        self.hdfFileName = hdfFileName
        self.mode = mode
        self.hdfFile = None

        self._experimentCode = experimentCode
        self._sessionCodes = sessionCodes
        self._lastWhereClause = None

        try:
            self.hdfFile = openHubFile(hdfFilePath, hdfFileName, mode)
        except Exception as e:
            print(e)
            raise ExperimentDataAccessException(e)

        self.getExperimentMetaData()

    def printTableStructure(self,tableName):
        """Print to stdout the current structure and content statistics of the
        specified DataStore table. To print out the complete structure of the
        DataStore file, including the name of all available tables, see the
        printHubFileStructure method.

        Args:
            tableName (str): The DataStore table name to print metadata information out for.

        """
        if self.hdfFile:
            hubFile = self.hdfFile
            for group in getattr(hubFile, walk_groups)("/"):
                for table in getattr(hubFile, listNodes)(group, classname='Table'):
                    if table.name == tableName:
                        print('------------------')
                        print('Path:', table)
                        print('Table name:', table.name)
                        print('Number of rows in table:', table.nrows)
                        print('Number of cols in table:', len(table.colnames))
                        print('Attribute name := type, shape:')
                        for name in table.colnames:
                            print('\t', name, ':= %s, %s' % (table.coldtypes[name], table.coldtypes[name].shape))
                        print('------------------')
                        return

    def printHubFileStructure(self):
        """Print to stdout the current global structure of the loaded DataStore
        File."""
        if self.hdfFile:
            print(self.hdfFile)

    def getExperimentMetaData(self):
        """Returns the the metadata for the experiment the datStore file is
        for.

        **Docstr TBC.**

        """
        if self.hdfFile:
            expcols = self.hdfFile.root.data_collection.experiment_meta_data.colnames
            if 'sessions' not in expcols:
                expcols.append('sessions')
            ExperimentMetaDataInstance = namedtuple(
                'ExperimentMetaDataInstance', expcols)
            experiments=[]
            for e in self.hdfFile.root.data_collection.experiment_meta_data:
                self._experimentID = e['experiment_id']
                a_exp = list(e[:])
                a_exp.append(self.getSessionMetaData())
                experiments.append(ExperimentMetaDataInstance(*a_exp))
            return experiments

    def getSessionMetaData(self, sessions=None):
        """
        Returns the the metadata associated with the experiment session codes in use.

        **Docstr TBC.**

        """
        if self.hdfFile:
            if sessions is None:
                sessions = []

            sessionCodes = self._sessionCodes
            sesscols = self.hdfFile.root.data_collection.session_meta_data.colnames
            SessionMetaDataInstance = namedtuple('SessionMetaDataInstance', sesscols)
            for r in self.hdfFile.root.data_collection.session_meta_data:
                if (len(sessionCodes) == 0 or r['code'] in sessionCodes) and r[
                        'experiment_id'] == self._experimentID:
                    rcpy=list(r[:])
                    rcpy[-1]=json.loads(rcpy[-1])
                    sessions.append(SessionMetaDataInstance(*rcpy))
            return sessions

    def getTableForPath(self, path):
        """
        Given a valid table path within the DataStore file, return the accociated table.
        """
        getattr(self.hdfFile, get_node)(path)

    def getEventTable(self, event_type):
        """
        Returns the DataStore table that contains events of the specified type.

        **Docstr TBC.**

        """
        if self.hdfFile:
            klassTables = self.hdfFile.root.class_table_mapping
            deviceEventTable = None
            event_column = None
            event_value = None

            if isinstance(event_type, basestring):
                if event_type.find('Event') >= 0:
                    event_column = 'class_name'
                    event_value = event_type
                else:
                    event_value = ''
                    tokens = event_type.split('_')
                    for t in tokens:
                        event_value += t[0].upper()+t[1:].lower()
                    event_value = event_type+'Event'
                event_value = '"%s"' % (event_value)
            elif isinstance(event_type, numbers.Integral):
                event_column = 'class_id'
                event_value = event_type
            else:
                print2err(
                    'getEventTable error: event_type arguement must be a string or and int')
                return None

            result = [
                row.fetch_all_fields() for row in klassTables.where(
                    '({0} == {1}) & (class_type_id == 1)'.format(
                        event_column, event_value))]

            if len(result) == 0:
                    return None
                    
            if len(result)!= 1:
                print2err(
                    'event_type_id passed to getEventAttribute can only return one row from CLASS_MAPPINGS: ',
                    len(result))
                return None

            tablePathString = result[0][3]
            return getattr(self.hdfFile, get_node)(tablePathString)
        return None

    def getEventMappingInformation(self):
        """Returns details on how ioHub Event Types are mapped to tables within
        the given DataStore file."""
        if self.hdfFile:
            eventMappings=dict()
            class_2_table=self.hdfFile.root.class_table_mapping
            EventTableMapping = namedtuple(
                'EventTableMapping',
                self.hdfFile.root.class_table_mapping.colnames)
            for row in class_2_table[:]:
                eventMappings[row['class_id']] = EventTableMapping(*row)
            return eventMappings
        return None

    def getEventsByType(self, condition_str = None):
        """Returns a dict of all event tables within the DataStore file that
        have at least one event instance saved.

        Keys are Event Type constants, as specified by
        iohub.EventConstants. Each value is a row iterator for events of
        that type.

        """
        eventTableMappings = self.getEventMappingInformation()
        if eventTableMappings:
            events_by_type = dict()
            for event_type_id, event_mapping_info in eventTableMappings.items():
                try:
                    cond = '(type == %d)' % (event_type_id)
                    if condition_str:
                        cond += ' & ' + condition_str
                    events_by_type[event_type_id] = next(self.hdfFile.getNode(
                        event_mapping_info.table_path).where(cond))
                except StopIteration:
                    pass
            return events_by_type
        return None

    def getConditionVariablesTable(self):
        """
        **Docstr TBC.**
        """
        cv_group = self.hdfFile.root.data_collection.condition_variables
        ecv = 'EXP_CV_%d' % (self._experimentID,)
        if ecv in cv_group._v_leaves:
            return cv_group._v_leaves[ecv]
        return None

    def getConditionVariableNames(self):
        """
        **Docstr TBC.**
        """
        cv_group = self.hdfFile.root.data_collection.condition_variables
        ecv = "EXP_CV_%d" % (self._experimentID,)
        if ecv in cv_group._v_leaves:
            ecvTable = cv_group._v_leaves[ecv]
            return ecvTable.colnames
        return None

    def getConditionVariables(self, filter=None):
        """
        **Docstr TBC.**
        """
        if filter is None:
            session_ids = []
            for s in self.getExperimentMetaData()[0].sessions:
                session_ids.append(s.session_id)
            filter = dict(session_id=(' in ', session_ids))

        ConditionSetInstance = None

        for conditionVarName, conditionVarComparitor in filter.items():
            avComparison, value = conditionVarComparitor

            cv_group = self.hdfFile.root.data_collection.condition_variables
            cvrows = []
            ecv = "EXP_CV_%d" % (self._experimentID,)
            if ecv in cv_group._v_leaves:
                ecvTable = cv_group._v_leaves[ecv]

                if ConditionSetInstance is None:
                    colnam = ecvTable.colnames
                    ConditionSetInstance = namedtuple('ConditionSetInstance', colnam)

                cvrows.extend(
                    [
                        ConditionSetInstance(
                            *
                            r[:]) for r in ecvTable if all(
                            [
                                eval(
                                    '{0} {1} {2}'.format(
                                        r[conditionVarName],
                                        conditionVarComparitor[0],
                                        conditionVarComparitor[1])) for conditionVarName,
                                conditionVarComparitor in filter.items()])])
        return cvrows

    def getValuesForVariables(self, cv, value, cvNames):
        """
        **Docstr TBC.**
        """

        if isinstance(value, (list, tuple)):
            resolvedValues = []
            for v in value:
                if isinstance(value, basestring) and value.startswith(
                        '@') and value.endswith('@'):
                    value=value[1:-1]
                    if value in cvNames:
                        resolvedValues.append(getattr(cv, v))
                    else:
                        raise ExperimentDataAccessException(
                            'getEventAttributeValues: {0} is not a valid attribute name in {1}'.format(
                                v, cvNames))
                elif isinstance(value, basestring):
                    resolvedValues.append(value)
            return resolvedValues
        elif isinstance(value, basestring) and value.startswith('@') and value.endswith('@'):
            value = value[1:-1]
            if value in cvNames:
                return getattr(cv, value)
            else:
                raise ExperimentDataAccessException(
                    'getEventAttributeValues: {0} is not a valid attribute name in {1}'.format(
                        value, cvNames))
        else:
            raise ExperimentDataAccessException(
                'Unhandled value type !: {0} is not a valid type for value {1}'.format(
                    type(value), value))

    def getEventAttributeValues(
            self,
            event_type_id,
            event_attribute_names,
            filter_id=None,
            conditionVariablesFilter=None,
            startConditions=None,
            endConditions=None):
        """
        **Docstr TBC.**

        Args:
            event_type_id
            event_attribute_names
            conditionVariablesFilter
            startConditions
            endConditions

        Returns:
            Values for the specified event type and event attribute columns which match the provided experiment condition variable filter, starting condition filer, and ending condition filter criteria.
        """
        if self.hdfFile:
            klassTables = self.hdfFile.root.class_table_mapping

            deviceEventTable = None

            result = [
                row.fetch_all_fields() for row in klassTables.where(
                    '(class_id == %d) & (class_type_id == 1)' %
                    (event_type_id))]
            if len(result) is not 1:
                raise ExperimentDataAccessException("event_type_id passed to getEventAttribute should only return one row from CLASS_MAPPINGS.")
            tablePathString = result[0][3]
            deviceEventTable = getattr(self.hdfFile, get_node)(tablePathString)

            for ename in event_attribute_names:
                if ename not in deviceEventTable.colnames:
                    raise ExperimentDataAccessException(
                        'getEventAttribute: %s does not have a column named %s' %
                        (deviceEventTable.title, event_attribute_names))

            resultSetList = []

            csier = list(event_attribute_names)
            csier.append('query_string')
            csier.append('condition_set')
            EventAttributeResults = namedtuple('EventAttributeResults', csier)

            if deviceEventTable is not None:
                if not isinstance(event_attribute_names, (list, tuple)):
                    event_attribute_names = [event_attribute_names, ]

                filteredConditionVariableList = None
                if conditionVariablesFilter is None:
                    filteredConditionVariableList= self.getConditionVariables()
                else:
                    filteredConditionVariableList = self.getConditionVariables(
                        conditionVariablesFilter)

                cvNames = self.getConditionVariableNames()

                # no further where clause building needed; get reseults and
                # return
                if startConditions is None and endConditions is None:
                    for cv in filteredConditionVariableList:

                        wclause = '( experiment_id == {0} ) & ( session_id == {1} )'.format(
                            self._experimentID, cv.session_id)

                        wclause += ' & ( type == {0} ) '.format(event_type_id)

                        if filter_id is not None:
                            wclause += '& ( filter_id == {0} ) '.format(
                                filter_id)

                        resultSetList.append([])

                        for ename in event_attribute_names:
                            resultSetList[-1].append(getattr(deviceEventTable, read_where)(wclause, field=ename))
                        resultSetList[-1].append(wclause)
                        resultSetList[-1].append(cv)

                        eventAttributeResults = EventAttributeResults(
                            *resultSetList[-1])
                        resultSetList[-1]=eventAttributeResults

                    return resultSetList

                #start or end conditions exist....
                for cv in filteredConditionVariableList:
                    resultSetList.append([])

                    wclause = '( experiment_id == {0} ) & ( session_id == {1} )'.format(
                        self._experimentID, cv.session_id)

                    wclause += ' & ( type == {0} ) '.format(event_type_id)

                    if filter_id is not None:
                        wclause += '& ( filter_id == {0} ) '.format(filter_id)

                    # start Conditions need to be added to where clause
                    if startConditions is not None:
                        wclause += '& ('
                        for conditionAttributeName, conditionAttributeComparitor in startConditions.items():
                            avComparison,value=conditionAttributeComparitor
                            value = self.getValuesForVariables(
                                cv, value, cvNames)
                            wclause += ' ( {0} {1} {2} ) & '.format(
                                conditionAttributeName, avComparison, value)
                        wclause=wclause[:-3]
                        wclause += ' ) '

                    # end Conditions need to be added to where clause
                    if endConditions is not None:
                        wclause += ' & ('
                        for conditionAttributeName, conditionAttributeComparitor in endConditions.items():
                            avComparison,value=conditionAttributeComparitor
                            value = self.getValuesForVariables(
                                cv, value, cvNames)
                            wclause += ' ( {0} {1} {2} ) & '.format(
                                conditionAttributeName, avComparison, value)
                        wclause=wclause[:-3]
                        wclause += ' ) '

                    for ename in event_attribute_names:
                        resultSetList[-1].append(getattr(deviceEventTable, read_where)(wclause, field=ename))
                    resultSetList[-1].append(wclause)
                    resultSetList[-1].append(cv)

                    eventAttributeResults = EventAttributeResults(
                        *resultSetList[-1])
                    resultSetList[-1]=eventAttributeResults

                return resultSetList

            return None

    def getEventIterator(self, event_type):
        """
        **Docstr TBC.**

        Args:
            event_type

        Returns:
            (iterator): An iterator providing access to each matching event  as a numpy recarray.
        """
        return self.getEventTable(event_type).iterrows()

    def close(self):
        """Close the ExperimentDataAccessUtility and associated DataStore
        File."""
        global _hubFiles
        if self.hdfFile in _hubFiles:
            _hubFiles.remove(self.hdfFile)
        self.hdfFile.close()

        self.experimentCodes = None
        self.hdfFilePath = None
        self.hdfFileName = None
        self.mode = None
        self.hdfFile = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class ExperimentDataAccessException(Exception):
    pass
