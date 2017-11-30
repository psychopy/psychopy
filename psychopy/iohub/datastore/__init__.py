# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).
from __future__ import division, absolute_import

import os
import atexit

import tables
from tables import UInt32Col, StringCol, UInt16Col
import numpy as np

from ..errors import print2err, printExceptionDetailsToStdErr, ioHubError
from ..constants import EventConstants
from ..devices import DeviceEvent

DATA_FILE_TITLE = 'ioHub DataStore - Experiment Data File.'
FILE_VERSION = '1.2'
SCHEMA_AUTHORS = 'Sol Simpson'
SCHEMA_MODIFIED_DATE = 'November 24th, 2016'


class DataStoreFile():
    def __init__(self, fileName, folderPath, fmode='a', iohub_settings=None):
        self.fileName = fileName
        self.folderPath = folderPath
        self.filePath = os.path.join(folderPath, fileName)

        if iohub_settings.get('multiple_sessions', True)  is False:
            fmode='w'

        self.settings = iohub_settings

        self.active_experiment_id = None
        self.active_session_id = None

        self.flushCounter = self.settings.get('flush_interval', 32)
        self._eventCounter = 0

        self.TABLES = dict()
        self.emrtFile = tables.openFile(self.filePath, mode=fmode)

        atexit.register(close_open_data_files, False)

        if fmode == 'w' or len(self.emrtFile.title) == 0:
            self.buildOutTemplate()
            self.flush()
        else:
            self.loadTableMappings()

    def buildOutTemplate(self):
        self.emrtFile.title = DATA_FILE_TITLE
        self.emrtFile.FILE_VERSION = FILE_VERSION
        self.emrtFile.SCHEMA_DESIGNER = SCHEMA_AUTHORS
        self.emrtFile.SCHEMA_MODIFIED = SCHEMA_MODIFIED_DATE

        # CREATE GROUPS
        froot = self.emrtFile.root
        ttitle = 'ioHub DeviceEvent Class to DataStore Table Mappings.'
        self.TABLES['CLASS_TABLE_MAPPINGS'] = self.emrtFile.createTable(froot,
                                                        'class_table_mapping',
                                                        ClassTableMappings,
                                                        title=ttitle)

        ttitle = 'Data Collected using the ioHub Event Framework.'
        self.emrtFile.createGroup(froot, 'data_collection', title=ttitle)
        self.flush()

        datcol_node = self.emrtFile.root.data_collection

        ttitle = 'All Saved ioHub Device Events.'
        self.emrtFile.createGroup(datcol_node, 'events', title=ttitle)

        ttitle = "Experiment Session DV and IV's Values."
        self.emrtFile.createGroup(datcol_node, 'condition_variables',
                                  title=ttitle)
        self.flush()

        self.TABLES['EXPERIMENT_METADETA'] = self.emrtFile.createTable(
            datcol_node, 'experiment_meta_data',
            ExperimentMetaData, title='Experiment Metadata.')
        self.TABLES['SESSION_METADETA'] = self.emrtFile.createTable(
            datcol_node, 'session_meta_data',
            SessionMetaData, title='Session MetaData.')

        self.flush()

    def loadTableMappings(self):
        # create meta-data tables
        datcol_node = self.emrtFile.root.data_collection
        self.TABLES[
            'EXPERIMENT_METADETA'] = datcol_node.experiment_meta_data
        self.TABLES[
            'SESSION_METADETA'] = datcol_node.session_meta_data
        self.TABLES[
            'CLASS_TABLE_MAPPINGS'] = self.emrtFile.root.class_table_mapping

        # Note: Event Tables are added to self.TABLES during runtime.

    @staticmethod
    def eventTableLabel2ClassName(event_table_label):
        tokens = str(
            event_table_label[0] +
            event_table_label[
                1:].lower() +
            'Event').split('_')
        return ''.join([t[0].upper() + t[1:] for t in tokens])

    def groupNodeForEvent(self, event_cls):
        evt_group_label = event_cls.PARENT_DEVICE.DEVICE_TYPE_STRING.lower()
        datevts_node = self.emrtFile.root.data_collection.events
        try:
            # If group for event table already exists return it....
            return datevts_node._f_get_child(evt_group_label)
        except tables.NoSuchNodeError:
            # Create the group node for the event....
            egtitle = "%s%s Device Events."%(evt_group_label[0].upper(),
                                             evt_group_label[1:])
            self.emrtFile.createGroup(datevts_node, evt_group_label,
                                      title=egtitle)
            return datevts_node._f_get_child(evt_group_label)

    def updateDataStoreStructure(self, device_instance, event_class_dict):
        dfilter = tables.Filters(
            complevel=0,
            complib='zlib',
            shuffle=False,
            fletcher32=False)

        for event_cls_name, event_cls in event_class_dict.iteritems():
            if event_cls.IOHUB_DATA_TABLE:
                event_table_label = event_cls.IOHUB_DATA_TABLE
                if event_table_label not in self.TABLES.keys():
                    try:
                        self.TABLES[event_table_label] = self.emrtFile.createTable(
                            self.groupNodeForEvent(event_cls),
                            self.eventTableLabel2ClassName(event_table_label),
                            event_cls.NUMPY_DTYPE,
                            title='%s Data' %
                            (device_instance.__class__.__name__,
                             ),
                            filters=dfilter.copy())
                        self.flush()
                    except tables.NodeError:
                        self.TABLES[event_table_label] = self.groupNodeForEvent(event_cls)._f_get_child(self.eventTableLabel2ClassName(event_table_label))
                    except Exception, e:
                        print2err('---------------ERROR------------------')
                        print2err(
                            'Exception %s in iohub.datastore.updateDataStoreStructure:' %
                            (e.__class__.__name__))
                        print2err('\tevent_cls: {0}'.format(event_cls))
                        print2err(
                            '\tevent_cls_name: {0}'.format(event_cls_name))
                        print2err(
                            '\tevent_table_label: {0}'.format(event_table_label))
                        print2err(
                            '\teventTableLabel2ClassName: {0}'.format(
                                self.eventTableLabel2ClassName(event_table_label)))
                        print2err(
                            '\tgroupNodeForEvent(event_cls): {0}'.format(
                                self.groupNodeForEvent(event_cls)))
                        print2err('\nException:')
                        printExceptionDetailsToStdErr()
                        print2err('--------------------------------------')

                if event_table_label in self.TABLES:
                    self.addClassMapping(event_cls,
                                         self.TABLES[event_table_label])
                else:
                    print2err(
                        '---- IOHUB.DATASTORE CANNOT ADD CLASS MAPPING ----')
                    print2err(
                        '\t** TABLES missing key: {0}'.format(event_table_label))
                    print2err('\tevent_cls: {0}'.format(event_cls))
                    print2err('\tevent_cls_name: {0}'.format(event_cls_name))
                    print2err(
                        '\teventTableLabel2ClassName: {0}'.format(
                            self.eventTableLabel2ClassName(event_table_label)))
                    print2err('----------------------------------------------')

    def addClassMapping(self, ioClass, ctable):
        names = [
            x['class_id'] for x in self.TABLES['CLASS_TABLE_MAPPINGS'].where(
                '(class_id == %d)' %
                (ioClass.EVENT_TYPE_ID))]
        if len(names) == 0:
            trow = self.TABLES['CLASS_TABLE_MAPPINGS'].row
            trow['class_id'] = ioClass.EVENT_TYPE_ID
            trow['class_type_id'] = 1  # Device or Event etc.
            trow['class_name'] = ioClass.__name__
            trow['table_path'] = ctable._v_pathname
            trow.append()
            self.flush()

    def createOrUpdateExperimentEntry(self, experimentInfoList):
        experiment_metadata = self.TABLES['EXPERIMENT_METADETA']
        result = [row for row in experiment_metadata.iterrows() if row[
            'code'] == experimentInfoList[1]]
        if len(result) > 0:
            result = result[0]
            self.active_experiment_id = result['experiment_id']
            return self.active_experiment_id
        max_id = 0
        id_col = experiment_metadata.col('experiment_id')
        if len(id_col) > 0:
            max_id = np.amax(id_col)
        self.active_experiment_id = max_id + 1
        experimentInfoList[0] = self.active_experiment_id
        experiment_metadata.append([experimentInfoList, ])
        self.flush()
        return self.active_experiment_id

    def createExperimentSessionEntry(self, sessionInfoDict):
        session_metadata = self.TABLES['SESSION_METADETA']
        max_id = 0
        id_col = session_metadata.col('session_id')
        if len(id_col) > 0:
            max_id = np.amax(id_col)
        self.active_session_id = int(max_id + 1)
        values = (
            self.active_session_id,
            self.active_experiment_id,
            sessionInfoDict['code'],
            sessionInfoDict['name'],
            sessionInfoDict['comments'],
            sessionInfoDict['user_variables'])
        session_metadata.append([values, ])
        self.flush()
        return self.active_session_id

    def initConditionVariableTable(
            self, experiment_id, session_id, np_dtype):
        expcv_table = None
        expcv_node = self.emrtFile.root.data_collection.condition_variables
        exp_session = [('EXPERIMENT_ID', 'i4'), ('SESSION_ID', 'i4')]
        exp_session.extend(np_dtype)
        np_dtype = []
        for npctype in exp_session:
            if isinstance(npctype[0], unicode):
                nv = [str(npctype[0]),]
                nv.extend(npctype[1:])
                np_dtype.append(tuple(nv))
            else:
                np_dtype.append(npctype)
        self._EXP_COND_DTYPE = np.dtype(np_dtype)
        try:
            expCondTableName = 'EXP_CV_%d' % (experiment_id)
            expcv_table = expcv_node._f_getChild(
                expCondTableName)
            self.TABLES['EXP_CV'] = expcv_table
        except tables.NoSuchNodeError:
            try:
                expcv_table = self.emrtFile.createTable(
                    expcv_node,
                    expCondTableName,
                    self._EXP_COND_DTYPE,
                    title='Condition Variable Values for Experiment ID %d' %
                    (experiment_id))
                self.TABLES['EXP_CV'] = expcv_table
                self.emrtFile.flush()
            except Exception:
                printExceptionDetailsToStdErr()
                return False
        except Exception:
            print2err(
                'Error getting expcv_table for experiment %d, table name: %s' %
                (experiment_id, expCondTableName))
            printExceptionDetailsToStdErr()
            return False
        self._activeRunTimeConditionVariableTable = expcv_table
        return True


    def extendConditionVariableTable(self, experiment_id, session_id, data):
        if self._EXP_COND_DTYPE is None:
            return False
        if self.emrtFile and 'EXP_CV' in self.TABLES:
            temp = [experiment_id, session_id]
            temp.extend(data)
            data = temp
            try:
                etable = self.TABLES['EXP_CV']
                for i, d in enumerate(data):
                    if isinstance(d, (list, tuple)):
                        data[i] = tuple(d)
                np_array = np.array([tuple(data), ],
                                    dtype=self._EXP_COND_DTYPE)
                etable.append(np_array)
                self.bufferedFlush()
                return True
            except Exception:
                printExceptionDetailsToStdErr()
        return False

    def addMetaDataToFile(self, metaData):
        pass

    def checkForExperimentAndSessionIDs(self, event=None):
        if self.active_experiment_id is None or self.active_session_id is None:
            exp_id = self.active_experiment_id
            if exp_id is None:
                exp_id = 0
            sess_id = self.active_session_id
            if sess_id is None:
                sess_id = 0
            return False
        return True

    def checkIfSessionCodeExists(self, sessionCode):
        if self.emrtFile:
            sessionsForExperiment = self.emrtFile.root.data_collection.session_meta_data.where(
                'experiment_id == %d' % (self.active_experiment_id,))
            sessionCodeMatch = [
                sess for sess in sessionsForExperiment if sess['code'] == sessionCode]
            if len(sessionCodeMatch) > 0:
                return True
            return False

    def _handleEvent(self, event):
        try:
            if self.checkForExperimentAndSessionIDs(event) is False:
                return False
            etype = event[DeviceEvent.EVENT_TYPE_ID_INDEX]
            eventClass = EventConstants.getClass(etype)
            etable = self.TABLES[eventClass.IOHUB_DATA_TABLE]
            event[DeviceEvent.EVENT_EXPERIMENT_ID_INDEX] = self.active_experiment_id
            event[DeviceEvent.EVENT_SESSION_ID_INDEX] = self.active_session_id
            np_array = np.array([tuple(event), ], dtype=eventClass.NUMPY_DTYPE)
            etable.append(np_array)
            self.bufferedFlush()
        except Exception:
            print2err('Error saving event: ', event)
            printExceptionDetailsToStdErr()

    def _handleEvents(self, events):
        try:
            if self.checkForExperimentAndSessionIDs(len(events)) is False:
                return False

            event = events[0]

            etype = event[DeviceEvent.EVENT_TYPE_ID_INDEX]
            eventClass = EventConstants.getClass(etype)
            etable = self.TABLES[eventClass.IOHUB_DATA_TABLE]

            np_events = []
            for event in events:
                event[DeviceEvent.EVENT_EXPERIMENT_ID_INDEX] = self.active_experiment_id
                event[DeviceEvent.EVENT_SESSION_ID_INDEX] = self.active_session_id
                np_events.append(tuple(event))

            np_array = np.array(np_events, dtype=eventClass.NUMPY_DTYPE)
            etable.append(np_array)
            self.bufferedFlush(len(np_events))
        except ioHubError as e:
            print2err(e)
        except Exception:
            printExceptionDetailsToStdErr()

    def bufferedFlush(self, eventCount=1):
        '''
        If flushCounter threshold is >=0 then do some checks. If it is < 0,
        then flush only occurs when command is sent to ioHub,
        so do nothing here.
        '''
        if self.flushCounter >= 0:
            if self.flushCounter == 0:
                self.flush()
                return True
            if self.flushCounter <= self._eventCounter:
                self.flush()
                self._eventCounter = 0
                return True
            self._eventCounter += eventCount
            return False

    def flush(self):
        try:
            if self.emrtFile:
                self.emrtFile.flush()
        except tables.ClosedFileError:
            pass
        except Exception:
            printExceptionDetailsToStdErr()

    def close(self):
        self.flush()
        self._activeRunTimeConditionVariableTable = None
        self.emrtFile.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

## -------------------- Utility Functions ------------------------ ##


def close_open_data_files(verbose):
    open_files = tables.file._open_files
    clall = hasattr(open_files, 'close_all')
    if clall:
        open_files.close_all()
    else:
        are_open_files = len(open_files) > 0
        if verbose and are_open_files:
            print2err('Closing remaining open data files:')
        for fileh in open_files.keys():
            if verbose:
                print2err('%s...' % (open_files[fileh].filename,))
            open_files[fileh].close()
            if verbose:
                print2err('done')


registered_close_open_data_files = True
atexit.register(close_open_data_files, False)

## ---------------------- Pytable Definitions ------------------- ##


class ClassTableMappings(tables.IsDescription):
    class_id = UInt32Col(pos=1)
    class_type_id = UInt32Col(pos=2)  # Device or Event etc.
    class_name = StringCol(32, pos=3)
    table_path = StringCol(128, pos=4)


class ExperimentMetaData(tables.IsDescription):
    experiment_id = UInt32Col(pos=1)
    code = StringCol(24, pos=2)
    title = StringCol(48, pos=3)
    description = StringCol(256, pos=4)
    version = StringCol(6, pos=5)
    total_sessions_to_run = UInt16Col(pos=9)


class SessionMetaData(tables.IsDescription):
    session_id = UInt32Col(pos=1)
    experiment_id = UInt32Col(pos=2)
    code = StringCol(24, pos=3)
    name = StringCol(48, pos=4)
    comments = StringCol(256, pos=5)
    # will hold json encoded version of user variable dict for session
    user_variables = StringCol(2048, pos=6)
