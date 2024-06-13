#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import numbers  # numbers.Integral is like (int, long) but supports Py3
import os
from collections import namedtuple
import json
import numpy

from ..errors import print2err

from packaging.version import Version
import tables

if Version(tables.__version__) < Version('3'):
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


def displayDataFileSelectionDialog(starting_dir=None, prompt="Select a ioHub HDF5 File", allowed="HDF5 Files (*.hdf5)"):
    """
    Shows a FileDialog and lets you select a .hdf5 file to open for processing.
    """
    from psychopy.gui.qtgui import fileOpenDlg

    filePath = fileOpenDlg(tryFilePath=starting_dir,
                           prompt=prompt,
                           allowed=allowed)

    if filePath is None:
        return None

    return filePath


def displayEventTableSelectionDialog(title, list_label, list_values, default='Select'):
    from psychopy import gui
    if default not in list_values:
        list_values.insert(0, default)
    else:
        list_values.remove(list_values)
        list_values.insert(0, default)

    selection_dict = {list_label: list_values}
    dlg_info = dict(selection_dict)
    infoDlg = gui.DlgFromDict(dictionary=dlg_info, title=title)
    if not infoDlg.OK:
        return None

    while list(dlg_info.values())[0] == default and infoDlg.OK:
        dlg_info = dict(selection_dict)
        infoDlg = gui.DlgFromDict(dictionary=dlg_info, title=title)

    if not infoDlg.OK:
        return None

    return list(dlg_info.values())[0]


def getEyeSampleTypesInFile(hdf5FilePath):
    """
    Return the eye sample type(s) saved in the hdf5 file located in hdf5FilePath.
    If no eye samples have been saved to the file return []. Possible return list values are defined in
    psychopy.iohub.constants.EYE_SAMPLE_TYPES.

    :param returnType: (type)
    :return: (list)
    """
    dpath, dfile = os.path.split(hdf5FilePath)
    datafile = ExperimentDataAccessUtility(dpath, dfile)
    result = datafile.getAvailableEyeSampleTypes()
    datafile.close()
    return result


def saveEventReport(hdf5FilePath=None, eventType=None, eventFields=[], useConditionsTable=False,
                    usePsychopyDataFile=None, columnNames=[],
                    trialStart=None, trialStop=None, timeMargins=(0.0, 0.0)
                    ):
    """
    Save a tab delimited event report from an iohub .hdf5 data file.


    Events can optionally be split into groups using either a Psychopy .csv data file (usePsychopyDataFile),
    iohub experiment message events, or the hdf5 condition variables table (useConditionsTable=True).

    If usePsychopyDataFile is True, trialStart and trialStop must be provided, or a dialog will prompt the user
    to select a column from the Psychopy .cvs file. The column must have a float or int data type. Each non nan / None
    row will be used to split events.

    If usePsychopyDataFile and useConditionsTable are False and trialStart and trialStop are provided as text,
    events are split based on the time of iohub Experiment Message events that match the trialStart and trialStop text.

    :param hdf5FilePath: (str or None)
    :param eventType: (str or None)
    :param eventFields: (list)
    :param useConditionsTable: (bool)
    :param usePsychopyDataFile: (bool)
    :param columnNames: (list)
    :param trialStart: (str or None)
    :param trialStop: (str or None)
    :param timeMargins: ([float, float] or None)
    :return:
    """
    # Select the hdf5 file to process.
    if usePsychopyDataFile is True and useConditionsTable is True:
        raise RuntimeError("saveEventReport: useConditionsTable and usePsychopyDataFile can both not be True")

    if not hdf5FilePath:
        selectedFilePath = displayDataFileSelectionDialog(os.getcwd())
        if selectedFilePath:
            hdf5FilePath = selectedFilePath[0]
    if not hdf5FilePath:
        raise RuntimeError("Warning: saveEventReport requires hdf5FilePath. No report saved.")

    dpath, dfile = os.path.split(hdf5FilePath)
    datafile = ExperimentDataAccessUtility(dpath, dfile)

    if not eventType:
        # Get a dict of all event types -> DataStore table info for the selected DataStore file.
        eventTableMappings = datafile.getEventMappingInformation()
        # Get event tables that have data...
        events_with_data = datafile.getEventsByType()

        # Select which event table to output
        eventNameList = []
        for event_id in list(events_with_data.keys()):
            eventNameList.append(eventTableMappings[event_id].class_name.decode('utf-8'))
        eventType = displayEventTableSelectionDialog("Select Event Type to Save", "Event Type:", eventNameList)
        if eventType is None:
            datafile.close()
            raise RuntimeError("saveEventReport requires eventType. No report saved.")

    #print("getAvailableEyeSampleTypes: ", datafile.getAvailableEyeSampleTypes())
    # Get the event table to generate report for
    event_table = datafile.getEventTable(eventType)

    if not eventFields:
        # If no event fields were specified, report (almost) all event fields.
        eventFields = [c for c in event_table.colnames if c not in ['experiment_id', 'session_id', 'device_id',
                                                                    'type', 'filter_id']]
    trial_times = []
    column_names = []

    psychoResults = None
    psychopyDataFile = None
    if usePsychopyDataFile is True:
        psychopyDataFile = hdf5FilePath[:-4] + 'csv'
        if not os.path.isfile(psychopyDataFile):
            datafile.close()
            raise RuntimeError("saveEventReport: Could not find .csv file: %s" % psychopyDataFile)

        import pandas
        psychoResults = pandas.read_csv(psychopyDataFile, delimiter=",", encoding='utf-8')

        if trialStart is None or trialStop is None:
            # get list of possible column names from
            columnNames = []
            for columnName in psychoResults.columns:
                if columnName.endswith('.started') or columnName.endswith('.stopped'):
                    if psychoResults[columnName].dtype in [float, int]:
                        columnNames.append(columnName)
            if trialStart is None:
                trialStart = displayEventTableSelectionDialog("Select Event Grouping Start Time Column",
                                                              "Columns", list(columnNames))
            if trialStop is None:
                trialStop = displayEventTableSelectionDialog("Select Event Grouping End Time Column",
                                                              "Columns", [cn for cn in columnNames if cn != trialStart])
                print('trialStop:', trialStop)

        if trialStart and trialStop:
            if trialStart not in psychoResults.columns:
                datafile.close()
                raise ValueError("saveEventReport trialStart column not found in psychopyDataFile: %s" % trialStart)
            if trialStop not in psychoResults.columns:
                datafile.close()
                raise ValueError("saveEventReport trialStop column not found in psychopyDataFile: %s" % trialStop)

            for t_ix, r in psychoResults.iterrows():
                if r[trialStart] != 'None' and r[trialStop] != 'None' and pandas.notna(r[trialStart]) and pandas.notna(
                        r[trialStop]):
                    trial_times.append([t_ix, r[trialStart] - timeMargins[0], r[trialStop] + timeMargins[1]])

        else:
            datafile.close()
            raise ValueError("saveEventReport trialStart and trialStop must be specified when using psychopyDataFile.")

    cvTable = None
    if useConditionsTable is True:
        # Use hdf5 conditions table columns 'trialStart' and 'trialStop' to group events
        if trialStart is None or trialStop is None:
            # If either trialStart and trialStop are None, display selection dialogs
            try:
                cvColumnNames = datafile.getConditionVariableNames()[2:]
            except Exception as e:
                #datastore Conditions table must not exist
                datafile.close()
                raise RuntimeError("saveEventReport: Error calling datafile.getConditionVariableNames().\n{}".format(e))

            if trialStart is None:
                trialStart = displayEventTableSelectionDialog("Select Event Grouping Start Time Column",
                                                              "Columns", list(cvColumnNames))
            if trialStop is None:
                trialStop = displayEventTableSelectionDialog("Select Event Grouping End Time Column",
                                                              "Columns", [cn for cn in cvColumnNames if cn != trialStart])


        if trialStart is None or trialStop is None:
            datafile.close()
            raise ValueError("saveEventReport: trialStart and trialStop must be specified "
                             "when useConditionsTable is True.")

        if trialStart not in cvColumnNames:
            datafile.close()
            raise ValueError("saveEventReport:"
                             " trialStart column not found in trial condition variables table: %s" % trialStart)
        if trialStop not in cvColumnNames:
            datafile.close()
            raise ValueError("saveEventReport:"
                             " trialStop column not found in trial condition variables table: %s" % trialStop)

        cvTable = datafile.getConditionVariablesTable()
        for t_ix, r in enumerate(cvTable):
            trial_times.append([t_ix, r[trialStart] - timeMargins[0], r[trialStop] + timeMargins[1]])

    if useConditionsTable is False and psychoResults is None and trialStart and trialStop:
        # Create a table of trial_index, trial_start_time, trial_end_time for each trial by
        # getting the time of 'TRIAL_START' and 'TRIAL_END' experiment messages.
        mgs_table = datafile.getEventTable('MessageEvent')
        trial_start_msgs = mgs_table.where('text == b"%s"' % trialStart)
        for mix, msg in enumerate(trial_start_msgs):
            trial_times.append([mix + 1, msg['time'] - timeMargins[0], 0])
        trial_end_msgs = mgs_table.where('text == b"%s"' % trialStop)
        for mix, msg in enumerate(trial_end_msgs):
            trial_times[mix][2] = msg['time'] + timeMargins[1]
        del mgs_table
    elif trialStart is None and trialStop is None:
        # do not split events into trial groupings
        pass
    elif trialStart is None or trialStop is None:
        datafile.close()
        raise RuntimeError("Warning: saveEventReport requires trialStart and trialStop to be strings or both None."
                           " No report saved.")

    if eventType == 'MessageEvent':
        # Sort experiment messages by time since they may not be ordered chronologically.
        event_table = event_table.read()
        event_table.sort(order='time')

    ecount = 0
    # Open a file to save the tab delimited output to.
    output_file_name = os.path.join(dpath, "%s.%s.txt" % (dfile[:-5], eventType))
    with open(output_file_name, 'w') as output_file:
        # Save header row to file
        if trial_times:
            if useConditionsTable:
                cvtColumnNames = datafile.getConditionVariableNames()[2:]
                if columnNames:
                    for cname in columnNames:
                        if cname not in cvtColumnNames:
                            datafile.close()
                            raise ValueError("saveEventReport: .hdf5 conditions table column '%s' not found." % cname)
                    column_names = list(columnNames) + eventFields
                else:
                    column_names = list(cvtColumnNames) + eventFields
                    columnNames = list(cvtColumnNames)

            elif hasattr(psychoResults, 'columns'):
                if columnNames:
                    for cname in columnNames:
                        if cname not in psychoResults.columns:
                            datafile.close()
                            raise ValueError(
                                "saveEventReport: psychopyDataFileColumn '%s' not found in .csv file." % cname)
                    column_names = list(columnNames) + eventFields
                else:
                    column_names = list(psychoResults.columns) + eventFields
                    columnNames = list(psychoResults.columns)
            else:
                column_names = ['TRIAL_INDEX', trialStart, trialStop] + eventFields
        else:
            column_names = eventFields

        output_file.write('\t'.join(column_names))
        output_file.write('\n')

        event_groupings = []
        if trial_times:
            # Split events into trials
            for tindex, tstart, tstop in trial_times:
                if eventType == 'MessageEvent':
                    event_groupings.append(event_table[(event_table['time'] >= tstart) & (event_table['time']
                                                                                          <= tstop)])
                else:
                    event_groupings.append(event_table.where("(time >= %f) & (time <= %f)" % (tstart, tstop)))
        else:
            # Report events without splitting them into trials
            if eventType == 'MessageEvent':
                event_groupings.append(event_table)
            else:
                event_groupings.append(event_table.iterrows())

        # Save a row for each event within the trial period
        for tid, trial_events in enumerate(event_groupings):
            for event in trial_events:
                event_data = []
                for c in eventFields:
                    cv = event[c]
                    if type(cv) == numpy.bytes_:
                        cv = event[c].decode('utf-8')
                    if type(cv) == str and len(cv) == 0:
                        cv = '.'
                    event_data.append(str(cv))
                if trial_times:
                    tindex, tstart, tstop = trial_times[tid]
                    if useConditionsTable:
                        cvRow=cvTable.read(tindex, tindex+1)
                        cvrowdat = [cvRow[c][0] for c in columnNames]
                        for ri, cv in enumerate(cvrowdat):
                            if type(cv) == numpy.bytes_:
                                cvrowdat[ri] = cvrowdat[ri].decode('utf-8')
                            else:
                                cvrowdat[ri] = str(cvrowdat[ri])
                            if type(cv) == str and len(cv) == 0:
                                cvrowdat[ri] = '.'
                        output_file.write('\t'.join(cvrowdat + event_data))
                    elif hasattr(psychoResults, 'columns'):
                        drow = psychoResults.iloc[tindex]
                        prowdat = [str(drow[c]) for c in columnNames]
                        output_file.write('\t'.join(prowdat + event_data))
                    else:
                        output_file.write('\t'.join([str(tindex), str(tstart), str(tstop)] + event_data))
                else:
                    output_file.write('\t'.join(event_data))
                output_file.write('\n')
                ecount += 1

    # Done report creation, close input file
    datafile.close()
    return output_file_name, ecount


########### Experiment / Experiment Session Based Data Access #################


class ExperimentDataAccessUtility:
    """The ExperimentDataAccessUtility  provides a simple, high level, way to
    access data saved in an ioHub DataStore HDF5 file. Data access is done by
    providing information at an experiment and session level, as well as
    specifying the ioHub Event types you want to retrieve data for.

    An instance of the ExperimentDataAccessUtility class is created by providing
    the location and name of the file to read, as well as any session code
    filtering you want applied to the retrieved datasets.

    Args:
        hdfFilePath (str): The path of the directory the DataStore HDF5 file is in.

        hdfFileName (str): The name of the DataStore HDF5 file.

        experimentCode (str): If multi-experiment support is enabled for the DataStore file, this argument can be used to specify what experiment data to load based on the experiment_code given. NOTE: Multi-experiment data file support is not well tested and should not be used at this point.

        sessionCodes (str or list): The experiment session code to filter data by. If a list of codes is given, then all codes in the list will be used.

    Returns:
        object: the created instance of the ExperimentDataAccessUtility, ready to get your data!

    """

    def __init__(self, hdfFilePath, hdfFileName, experimentCode=None, sessionCodes=[], mode='r'):
        """An instance of the ExperimentDataAccessUtility class is created by
        providing the location and name of the file to read, as well as any
        session code filtering you want applied to the retrieved datasets.

        Args:
            hdfFilePath (str): The path of the directory the DataStore HDF5 file is in.

            hdfFileName (str): The name of the DataStore HDF5 file.

            experimentCode (str): If multi-experiment support is enabled for the DataStore file, this argument can be used to specify what experiment data to load based on the experiment_code given. NOTE: Multi-experiment data file support is not well tested and should not be used at this point.

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
            raise ExperimentDataAccessException(e)

        self.getExperimentMetaData()

    def printTableStructure(self, tableName):
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
                for table in getattr(hubFile, list_nodes)(group, classname='Table'):
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
        """Returns the metadata for the experiment the datStore file is
        for.

        **Docstr TBC.**

        """
        if self.hdfFile:
            expcols = self.hdfFile.root.data_collection.experiment_meta_data.colnames
            if 'sessions' not in expcols:
                expcols.append('sessions')
            ExperimentMetaDataInstance = namedtuple(
                'ExperimentMetaDataInstance', expcols)
            experiments = []
            for e in self.hdfFile.root.data_collection.experiment_meta_data:
                self._experimentID = e['experiment_id']
                a_exp = list(e[:])
                a_exp.append(self.getSessionMetaData())
                experiments.append(ExperimentMetaDataInstance(*a_exp))
            return experiments

    def getSessionMetaData(self, sessions=None):
        """
        Returns the metadata associated with the experiment session codes in use.

        **Docstr TBC.**

        """
        if self.hdfFile:
            if sessions is None:
                sessions = []

            sessionCodes = self._sessionCodes
            sesscols = self.hdfFile.root.data_collection.session_meta_data.colnames
            SessionMetaDataInstance = namedtuple('SessionMetaDataInstance', sesscols)
            for r in self.hdfFile.root.data_collection.session_meta_data:
                if (len(sessionCodes) == 0 or r['code'] in sessionCodes) and r['experiment_id'] == self._experimentID:
                    rcpy = list(r[:])
                    rcpy[-1] = json.loads(rcpy[-1])
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
            event_column = None
            event_value = None

            if isinstance(event_type, str):
                if event_type.find('Event') >= 0:
                    event_column = 'class_name'
                    event_value = event_type
                else:
                    event_value = ''
                    tokens = event_type.split('_')
                    for t in tokens:
                        event_value += t[0].upper() + t[1:].lower()
                    event_value = event_type + 'Event'
            elif isinstance(event_type, numbers.Integral):
                event_column = 'class_id'
                event_value = event_type
            else:
                print2err(
                    'getEventTable error: event_type argument must be a string or and int')
                return None

            result = []
            where_cls = '(%s == b"%s") & (class_type_id == 1)' % (event_column, event_value)
            for row in klassTables.where(where_cls):
                result.append(row.fetch_all_fields())

            if len(result) == 0:
                return None

            if len(result) != 1:
                print2err('event_type_id passed to getEventAttribute can only return one row from CLASS_MAPPINGS.')
                return None
            tablePathString = result[0][3]
            if isinstance(tablePathString, bytes):
                tablePathString = tablePathString.decode('utf-8')
            return getattr(self.hdfFile, get_node)(tablePathString)
        return None

    def getEventMappingInformation(self):
        """Returns details on how ioHub Event Types are mapped to tables within
        the given DataStore file."""
        if self.hdfFile:
            eventMappings = dict()
            class_2_table = self.hdfFile.root.class_table_mapping
            EventTableMapping = namedtuple(
                'EventTableMapping',
                self.hdfFile.root.class_table_mapping.colnames)
            for row in class_2_table[:]:
                eventMappings[row['class_id']] = EventTableMapping(*row)
            return eventMappings
        return None

    def getEventsByType(self, condition_str=None):
        """Returns a dict of all event tables within the DataStore file that
        have at least one event instance saved.

        Keys are Event Type constants, as specified by
        iohub.EventConstants. Each value is a row iterator for events of
        that type.

        """
        eventTableMappings = self.getEventMappingInformation()
        if eventTableMappings:
            events_by_type = dict()
            getNode = getattr(self.hdfFile, get_node)
            for event_type_id, event_mapping_info in eventTableMappings.items():
                try:
                    cond = '(type == %d)' % (event_type_id)
                    if condition_str:
                        cond += ' & ' + condition_str
                    et_path = event_mapping_info.table_path
                    if isinstance(et_path, bytes):
                        et_path = et_path.decode('utf-8')
                    events_by_type[event_type_id] = next(getNode(et_path).where(cond))
                except StopIteration:
                    pass
            return events_by_type
        return None

    def getAvailableEyeSampleTypes(self, returnType=str):
        """
        Return the eye sample type(s) saved to the current hdf5 file.
        If no eye samples have been saved to the file return []. Possible return list values are defined in
        psychopy.iohub.constants.EYE_SAMPLE_TYPES.

        :param returnType: (type)
        :return: (list)
        """
        from psychopy.iohub.constants import EYE_SAMPLE_TYPES

        if returnType == int:
            return [etype for etype in self.getEventsByType() if etype in EYE_SAMPLE_TYPES]

        if returnType == str:
            eventTableMappings = self.getEventMappingInformation()
            sampleTypes = [etype for etype in self.getEventsByType() if etype in EYE_SAMPLE_TYPES]
            eventList = []
            for event_id in sampleTypes:
                eventList.append(eventTableMappings[event_id].class_name.decode('utf-8'))
            return eventList

        raise RuntimeError("getAvailableEyeSampleTypes returnType arg must be set to either int or str type.")

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
            filter = dict(SESSION_ID=(' in ', session_ids))

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
                if isinstance(value, str) and value.startswith('@') and value.endswith('@'):
                    value = value[1:-1]
                    if value in cvNames:
                        resolvedValues.append(getattr(cv, v))
                    else:
                        raise ExperimentDataAccessException('getEventAttributeValues: {0} is not a valid attribute '
                                                            'name in {1}'.format(v, cvNames))
                elif isinstance(value, str):
                    resolvedValues.append(value)
            return resolvedValues
        elif isinstance(value, str) and value.startswith('@') and value.endswith('@'):
            value = value[1:-1]
            if value in cvNames:
                return getattr(cv, value)
            else:
                raise ExperimentDataAccessException('getEventAttributeValues: {0} is not a valid attribute name'
                                                    ' in {1}'.format(value, cvNames))
        else:
            raise ExperimentDataAccessException('Unhandled value type !: {0} is not a valid type for value '
                                                '{1}'.format(type(value), value))

    def getEventAttributeValues(self, event_type_id, event_attribute_names, filter_id=None,
                                conditionVariablesFilter=None, startConditions=None, endConditions=None):
        """
        **Docstr TBC.**

        Args:
            event_type_id
            event_attribute_names
            filter_id
            conditionVariablesFilter
            startConditions
            endConditions

        Returns:
            Values for the specified event type and event attribute columns which match the provided experiment
            condition variable filter, starting condition filer, and ending condition filter criteria.
        """
        if self.hdfFile:
            klassTables = self.hdfFile.root.class_table_mapping

            deviceEventTable = None

            result = [row.fetch_all_fields() for row in klassTables.where('(class_id == %d) &'
                                                                          ' (class_type_id == 1)' % (event_type_id))]
            if len(result) != 1:
                raise ExperimentDataAccessException("event_type_id returned > 1 row from CLASS_MAPPINGS.")
            tablePathString = result[0][3]
            if isinstance(tablePathString, bytes):
                tablePathString = tablePathString.decode('utf-8')
            deviceEventTable = getattr(self.hdfFile, get_node)(tablePathString)

            for ename in event_attribute_names:
                if ename not in deviceEventTable.colnames:
                    raise ExperimentDataAccessException('getEventAttribute: %s does not have a column named %s' %
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
                    filteredConditionVariableList = self.getConditionVariables()
                else:
                    filteredConditionVariableList = self.getConditionVariables(conditionVariablesFilter)

                cvNames = self.getConditionVariableNames()

                # no further where clause building needed; get reseults and
                # return
                if startConditions is None and endConditions is None:
                    for cv in filteredConditionVariableList:

                        wclause = '( experiment_id == {0} ) & ( SESSION_ID == {1} )'.format(self._experimentID,
                                                                                            cv.SESSION_ID)

                        wclause += ' & ( type == {0} ) '.format(event_type_id)

                        if filter_id is not None:
                            wclause += '& ( filter_id == {0} ) '.format(filter_id)

                        resultSetList.append([])

                        for ename in event_attribute_names:
                            resultSetList[-1].append(getattr(deviceEventTable, read_where)(wclause, field=ename))
                        resultSetList[-1].append(wclause)
                        resultSetList[-1].append(cv)

                        eventAttributeResults = EventAttributeResults(*resultSetList[-1])
                        resultSetList[-1] = eventAttributeResults

                    return resultSetList

                # start or end conditions exist....
                for cv in filteredConditionVariableList:
                    resultSetList.append([])

                    wclause = '( experiment_id == {0} ) & ( session_id == {1} )'.format(self._experimentID,
                                                                                        cv.SESSION_ID)

                    wclause += ' & ( type == {0} ) '.format(event_type_id)

                    if filter_id is not None:
                        wclause += '& ( filter_id == {0} ) '.format(filter_id)

                    # start Conditions need to be added to where clause
                    if startConditions is not None:
                        wclause += '& ('
                        for conditionAttributeName, conditionAttributeComparitor in startConditions.items():
                            avComparison, value = conditionAttributeComparitor
                            value = self.getValuesForVariables(cv, value, cvNames)
                            wclause += ' ( {0} {1} {2} ) & '.format(conditionAttributeName, avComparison, value)
                        wclause = wclause[:-3]
                        wclause += ' ) '

                    # end Conditions need to be added to where clause
                    if endConditions is not None:
                        wclause += ' & ('
                        for conditionAttributeName, conditionAttributeComparitor in endConditions.items():
                            avComparison, value = conditionAttributeComparitor
                            value = self.getValuesForVariables(cv, value, cvNames)
                            wclause += ' ( {0} {1} {2} ) & '.format(conditionAttributeName, avComparison, value)
                        wclause = wclause[:-3]
                        wclause += ' ) '

                    for ename in event_attribute_names:
                        resultSetList[-1].append(getattr(deviceEventTable, read_where)(wclause, field=ename))
                    resultSetList[-1].append(wclause)
                    resultSetList[-1].append(cv)

                    eventAttributeResults = EventAttributeResults(*resultSetList[-1])
                    resultSetList[-1] = eventAttributeResults

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
