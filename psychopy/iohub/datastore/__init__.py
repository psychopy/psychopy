# -*- coding: utf-8 -*-
from __future__ import division
"""
ioHub
.. file: ioHub/datastore/__init__.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>

"""
import os, atexit

import tables
from tables import *
from tables import parameters

import numpy as N

from psychopy.iohub import printExceptionDetailsToStdErr, print2err, ioHubError, DeviceEvent, EventConstants


parameters.MAX_NUMEXPR_THREADS=None
"""The maximum number of threads that PyTables should use internally in
Numexpr.  If `None`, it is automatically set to the number of cores in
your machine. In general, it is a good idea to set this to the number of
cores in your machine or, when your machine has many of them (e.g. > 4),
perhaps one less than this. < S. Simpson Note: These are 'not' GIL bound
threads and therefore actually improve performance > """

parameters.MAX_BLOSC_THREADS=None
"""The maximum number of threads that PyTables should use internally in
Blosc.  If `None`, it is automatically set to the number of cores in
your machine. In general, it is a good idea to set this to the number of
cores in your machine or, when your machine has many of them (e.g. > 4),
perhaps one less than this.  < S. Simpson Note: These are 'not' GIL bound
threads and therefore actually improve performance > """

DATA_FILE_TITLE="ioHub DataStore - Experiment Data File."
FILE_VERSION = '0.7.0'
SCHEMA_AUTHORS='Sol Simpson'
SCHEMA_MODIFIED_DATE='May 6th, 2013'

        
class ioHubpyTablesFile():
    
    def __init__(self,fileName,folderPath,fmode='a',ioHubsettings=None):
        self.fileName=fileName
        self.folderPath=folderPath
        self.filePath=os.path.join(folderPath,fileName)

        self.settings=ioHubsettings

        self.active_experiment_id=None
        self.active_session_id=None
        
        self.flushCounter=self.settings.get('flush_interval',32)
        self._eventCounter=0
        
        self.TABLES=dict()
        self._eventGroupMappings=dict()
        self.emrtFile = openFile(self.filePath, mode = fmode)
               
        atexit.register(close_open_data_files, False)
        
        if len(self.emrtFile.title) == 0:
            self.buildOutTemplate()
            self.flush()
        else:
            self.loadTableMappings()
    
    def updateDataStoreStructure(self,device_instance,event_class_dict):
        dfilter = Filters(complevel=0, complib='zlib', shuffle=False, fletcher32=False)
        
        def eventTableLabel2ClassName(event_table_label):
            tokens=str(event_table_label[0]+event_table_label[1:].lower()+'Event').split('_') 
            return ''.join([t[0].upper()+t[1:] for t in tokens])

        for event_cls_name,event_cls in event_class_dict.iteritems():
            if event_cls.IOHUB_DATA_TABLE:
                event_table_label=event_cls.IOHUB_DATA_TABLE
                if event_table_label not in self.TABLES:
                    self.TABLES[event_table_label]=self.emrtFile.createTable(self._eventGroupMappings[event_table_label],eventTableLabel2ClassName(event_table_label),event_cls.NUMPY_DTYPE, title="%s Data"%(device_instance.__class__.__name__,),filters=dfilter.copy())
                    self.flush()
    
                self.addClassMapping(event_cls,self.TABLES[event_table_label])


    def loadTableMappings(self):
        # create meta-data tables
        
        self._buildEventGroupMappingDict()
        
        self.TABLES['EXPERIMENT_METADETA']=self.emrtFile.root.data_collection.experiment_meta_data
        self.TABLES['SESSION_METADETA']=self.emrtFile.root.data_collection.session_meta_data
        self.TABLES['CLASS_TABLE_MAPPINGS']=self.emrtFile.root.class_table_mapping
        
        # create tables dict of hdf5 path mappings

        try:
            self.TABLES['KEYBOARD_KEY']=self.emrtFile.root.data_collection.events.keyboard.KeyboardKeyEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass
        
        try:
            self.TABLES['KEYBOARD_CHAR']=self.emrtFile.root.data_collection.events.keyboard.KeyboardCharEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass

        try:
            self.TABLES['MOUSE_INPUT']=self.emrtFile.root.data_collection.events.mouse.MouseInputEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass

        try:
            self.TABLES['TOUCH']=self.emrtFile.root.data_collection.events.touch.TouchEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass

        try:
            self.TABLES['GAMEPAD_STATE_CHANGE']=self.emrtFile.root.data_collection.events.gamepad.GamepadStateChangeEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass

        try:
            self.TABLES['MESSAGE']=self.emrtFile.root.data_collection.events.experiment.MessageEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass

        try:
            self.TABLES['LOG']=self.emrtFile.root.data_collection.events.experiment.LogEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass

        try:
            self.TABLES['MULTI_CHANNEL_ANALOG_INPUT']=self.emrtFile.root.data_collection.events.analog_input.MultiChannelAnalogInputEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass

        try:
            self.TABLES['ANALOG_INPUT']=self.emrtFile.root.data_collection.events.mcu.AnalogInputEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass

        try:
            self.TABLES['DIGITAL_INPUT']=self.emrtFile.root.data_collection.events.mcu.DigitalInputEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass

        try:
            self.TABLES['MONOCULAR_EYE_SAMPLE']=self.emrtFile.root.data_collection.events.eyetracker.MonocularEyeSampleEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass

        try:
            self.TABLES['BINOCULAR_EYE_SAMPLE']=self.emrtFile.root.data_collection.events.eyetracker.BinocularEyeSampleEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass

        try:
            self.TABLES['FIXATION_START']=self.emrtFile.root.data_collection.events.eyetracker.FixationStartEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass

        try:
            self.TABLES['FIXATION_END']=self.emrtFile.root.data_collection.events.eyetracker.FixationEndEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass

        try:
            self.TABLES['SACCADE_START']=self.emrtFile.root.data_collection.events.eyetracker.SaccadeStartEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass

        try:
            self.TABLES['SACCADE_END']=self.emrtFile.root.data_collection.events.eyetracker.SaccadeEndEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass

        try:
            self.TABLES['BLINK_START']=self.emrtFile.root.data_collection.events.eyetracker.BlinkStartEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass

        try:
            self.TABLES['BLINK_END']=self.emrtFile.root.data_collection.events.eyetracker.BlinkEndEvent
        except:
            # Just means the table for this event type has not been created as the event type is not being recorded
            pass
        
    def buildOutTemplate(self): 
        self.emrtFile.title=DATA_FILE_TITLE
        self.emrtFile.FILE_VERSION=FILE_VERSION
        self.emrtFile.SCHEMA_DESIGNER=SCHEMA_AUTHORS
        self.emrtFile.SCHEMA_MODIFIED=SCHEMA_MODIFIED_DATE
        
        #CREATE GROUPS

        #self.emrtFile.createGroup(self.emrtFile.root, 'analysis', title='Data Analysis Files, notebooks, scripts and saved results tables.')

        self.TABLES['CLASS_TABLE_MAPPINGS']=self.emrtFile.createTable(self.emrtFile.root,'class_table_mapping', ClassTableMappings, title='Mapping of ioHub DeviceEvent Classes to ioHub DataStore Tables.')

        self.emrtFile.createGroup(self.emrtFile.root, 'data_collection', title='Data Collected using the ioHub Event Framework.')
        self.flush()

        self.emrtFile.createGroup(self.emrtFile.root.data_collection, 'events', title='All Events that were Saved During Experiment Sessions.')

        self.emrtFile.createGroup(self.emrtFile.root.data_collection, 'condition_variables', title="Tables created to Hold Experiment DV and IV's Values Saved During an Experiment Session.")
        self.flush()

        
        self.TABLES['EXPERIMENT_METADETA']=self.emrtFile.createTable(self.emrtFile.root.data_collection,'experiment_meta_data', ExperimentMetaData, title='Information About Experiments Saved to This ioHub DataStore File.')
        self.TABLES['SESSION_METADETA']=self.emrtFile.createTable(self.emrtFile.root.data_collection,'session_meta_data', SessionMetaData, title='Information About Sessions Saved to This ioHub DataStore File.')
        self.flush()


        self.emrtFile.createGroup(self.emrtFile.root.data_collection.events, 'experiment', title='Experiment Device Events.')
        self.emrtFile.createGroup(self.emrtFile.root.data_collection.events, 'keyboard', title='Keyboard Device Events.')
        self.emrtFile.createGroup(self.emrtFile.root.data_collection.events, 'mouse', title='Mouse Device Events.')
        self.emrtFile.createGroup(self.emrtFile.root.data_collection.events, 'touch', title='Touch Device Events.')
        self.emrtFile.createGroup(self.emrtFile.root.data_collection.events, 'gamepad', title='GamePad Device Events.')
        self.emrtFile.createGroup(self.emrtFile.root.data_collection.events, 'analog_input', title='AnalogInput Device Events.')
        self.emrtFile.createGroup(self.emrtFile.root.data_collection.events, 'eyetracker', title='EyeTracker Device Events.')
        self.emrtFile.createGroup(self.emrtFile.root.data_collection.events, 'mcu', title='MCU Device Events.')
        self.flush()

        self._buildEventGroupMappingDict()
        

    def _buildEventGroupMappingDict(self):
        self._eventGroupMappings['KEYBOARD_KEY']=self.emrtFile.root.data_collection.events.keyboard
        self._eventGroupMappings['KEYBOARD_CHAR']=self.emrtFile.root.data_collection.events.keyboard
        self._eventGroupMappings['MOUSE_INPUT']=self.emrtFile.root.data_collection.events.mouse
        self._eventGroupMappings['TOUCH']=self.emrtFile.root.data_collection.events.touch
        self._eventGroupMappings['GAMEPAD_STATE_CHANGE']=self.emrtFile.root.data_collection.events.gamepad
        self._eventGroupMappings['MULTI_CHANNEL_ANALOG_INPUT']=self.emrtFile.root.data_collection.events.analog_input
        self._eventGroupMappings['ANALOG_INPUT']=self.emrtFile.root.data_collection.events.mcu
        self._eventGroupMappings['DIGITAL_INPUT']=self.emrtFile.root.data_collection.events.mcu
        self._eventGroupMappings['MESSAGE']=self.emrtFile.root.data_collection.events.experiment
        self._eventGroupMappings['LOG']=self.emrtFile.root.data_collection.events.experiment
        self._eventGroupMappings['MONOCULAR_EYE_SAMPLE']=self.emrtFile.root.data_collection.events.eyetracker
        self._eventGroupMappings['BINOCULAR_EYE_SAMPLE']=self.emrtFile.root.data_collection.events.eyetracker
        self._eventGroupMappings['FIXATION_START']=self.emrtFile.root.data_collection.events.eyetracker
        self._eventGroupMappings['FIXATION_END']=self.emrtFile.root.data_collection.events.eyetracker
        self._eventGroupMappings['SACCADE_START']=self.emrtFile.root.data_collection.events.eyetracker
        self._eventGroupMappings['SACCADE_END']=self.emrtFile.root.data_collection.events.eyetracker
        self._eventGroupMappings['BLINK_START']=self.emrtFile.root.data_collection.events.eyetracker
        self._eventGroupMappings['BLINK_END']=self.emrtFile.root.data_collection.events.eyetracker

    
    def addClassMapping(self,ioClass,ctable):
        names = [ x['class_id'] for x in self.TABLES['CLASS_TABLE_MAPPINGS'].where("(class_id == %d)"%(ioClass.EVENT_TYPE_ID)) ]
        if len(names)==0:
            trow=self.TABLES['CLASS_TABLE_MAPPINGS'].row
            trow['class_id']=ioClass.EVENT_TYPE_ID
            trow['class_type_id'] = 1 # Device or Event etc.
            trow['class_name'] = ioClass.__name__
            trow['table_path']  = ctable._v_pathname
            trow.append()            
            self.flush()    
          
    def createOrUpdateExperimentEntry(self,experimentInfoList):
        #ioHub.print2err("createOrUpdateExperimentEntry called with: ",experimentInfoList)
        experiment_metadata=self.TABLES['EXPERIMENT_METADETA']

        result = [ row for row in experiment_metadata.iterrows() if row['code'] == experimentInfoList[1] ]
        if len(result)>0:
            result=result[0]
            self.active_experiment_id=result['experiment_id']
            return self.active_experiment_id
        
        max_id=0
        id_col=experiment_metadata.col('experiment_id')

        if len(id_col) > 0:
            max_id=N.amax(id_col)
            
        self.active_experiment_id=max_id+1
        experimentInfoList[0]=self.active_experiment_id
        experiment_metadata.append([experimentInfoList,])
        self.flush()
        #ioHub.print2err("Experiment ID set to: ",self.active_experiment_id)
        return self.active_experiment_id
    
    def createExperimentSessionEntry(self,sessionInfoDict):
        #ioHub.print2err("createExperimentSessionEntry called with: ",sessionInfoDict)
        session_metadata=self.TABLES['SESSION_METADETA']

        max_id=0
        id_col=session_metadata.col('session_id')
        if len(id_col) > 0:
            max_id=N.amax(id_col)
        
        self.active_session_id=int(max_id+1)
        
        values=(self.active_session_id,self.active_experiment_id,sessionInfoDict['code'],sessionInfoDict['name'],sessionInfoDict['comments'],sessionInfoDict['user_variables'])
        session_metadata.append([values,])
        self.flush()

        #ioHub.print2err("Session ID set to: ",self.active_session_id)
        return self.active_session_id

    def _initializeConditionVariableTable(self,experiment_id,session_id,np_dtype):
        experimentConditionVariableTable=None
        exp_session=[('EXPERIMENT_ID','i4'),('SESSION_ID','i4')]
        exp_session.extend(np_dtype)
        np_dtype=exp_session
        #print2err('np_dtype: ',np_dtype,' ',type(np_dtype))
        self._EXP_COND_DTYPE=N.dtype(np_dtype)
        try:
            expCondTableName="EXP_CV_%d"%(experiment_id)
            experimentConditionVariableTable=self.emrtFile.root.data_collection.condition_variables._f_getChild(expCondTableName)
            self.TABLES['EXP_CV']=experimentConditionVariableTable
        except NoSuchNodeError, nsne:
            try:
                experimentConditionVariableTable=self.emrtFile.createTable(self.emrtFile.root.data_collection.condition_variables,expCondTableName,self._EXP_COND_DTYPE,title='Condition Variable Values for Experiment ID %d'%(experiment_id))
                self.TABLES['EXP_CV']=experimentConditionVariableTable
                self.emrtFile.flush()
            except:
                printExceptionDetailsToStdErr()
                return False
        except Exception:
            print2err('Error getting experimentConditionVariableTable for experiment %d, table name: %s'%(experiment_id,expCondTableName))
            printExceptionDetailsToStdErr()
            return False
        self._activeRunTimeConditionVariableTable=experimentConditionVariableTable
        return True

    def _addRowToConditionVariableTable(self,experiment_id,session_id,data):
        if self.emrtFile and 'EXP_CV' in self.TABLES and self._EXP_COND_DTYPE is not None:
            temp=[experiment_id,session_id]
            temp.extend(data)
            data=temp            
            try:
                etable=self.TABLES['EXP_CV']
                #print2err('data: ',data,' ',type(data))

                for i,d in enumerate(data):
                    if isinstance(d,(list,tuple)):
                        data[i]=tuple(d)

                np_array= N.array([tuple(data),],dtype=self._EXP_COND_DTYPE)
                etable.append(np_array)

                self.bufferedFlush()
                return True

            except:
                printExceptionDetailsToStdErr()
        return False

    def addMetaDataToFile(self,metaData):
        pass

    def checkForExperimentAndSessionIDs(self,event=None):
        if self.active_experiment_id is None or self.active_session_id is None:
            exp_id=self.active_experiment_id
            if exp_id is None:
                exp_id=0
            sess_id=self.active_session_id
            if sess_id is None:
                sess_id=0

            #import iohub
            #iohub.print2err(Computer.getTime()," Experiment or Session ID is None, event not being saved: "+str(event),' exp_id: ',exp_id,' sess_id: ', sess_id)
            return False
        return True
        
    def checkIfSessionCodeExists(self,sessionCode):
        if self.emrtFile:
            sessionsForExperiment=self.emrtFile.root.data_collection.session_meta_data.where("experiment_id == %d"%(self.active_experiment_id,))
            sessionCodeMatch=[sess for sess in sessionsForExperiment if sess['code'] == sessionCode]
            if len(sessionCodeMatch)>0:
                return True
            return False
            
    def _handleEvent(self, event):
        try:
            eventClass=None

            if self.checkForExperimentAndSessionIDs(event) is False:
                return False

            etype=event[DeviceEvent.EVENT_TYPE_ID_INDEX]

#            print2err("*** ",DeviceEvent.EVENT_TYPE_ID_INDEX, '_handleEvent: ',etype,' : event list: ',event)
            eventClass=EventConstants.getClass(etype)
                
            etable=self.TABLES[eventClass.IOHUB_DATA_TABLE]
            event[DeviceEvent.EVENT_EXPERIMENT_ID_INDEX]=self.active_experiment_id
            event[DeviceEvent.EVENT_SESSION_ID_INDEX]=self.active_session_id

            np_array= N.array([tuple(event),],dtype=eventClass.NUMPY_DTYPE)
            etable.append(np_array)

            self.bufferedFlush()

        except:
            print2err("Error saving event: ",event)
            printExceptionDetailsToStdErr()

    def _handleEvents(self, events):
        # saves many events to pytables table at once.
        # EVENTS MUST ALL BE OF SAME TYPE!!!!!
        try:
            #ioHub.print2err("_handleEvent: ",self.active_experiment_id,self.active_session_id)

            if self.checkForExperimentAndSessionIDs(len(events)) is False:
                return False

            event=events[0]

            etype=event[DeviceEvent.EVENT_TYPE_ID_INDEX]
            #ioHub.print2err("etype: ",etype)
            eventClass=EventConstants.getClass(etype)
            etable=self.TABLES[eventClass.IOHUB_DATA_TABLE]
            #ioHub.print2err("eventClass: etable",eventClass,etable)

            np_events=[]
            for event in events:
                event[DeviceEvent.EVENT_EXPERIMENT_ID_INDEX]=self.active_experiment_id
                event[DeviceEvent.EVENT_SESSION_ID_INDEX]=self.active_session_id
                np_events.append(tuple(event))

            np_array= N.array(np_events,dtype=eventClass.NUMPY_DTYPE)
            #ioHub.print2err('np_array:',np_array)
            etable.append(np_array)

            self.bufferedFlush(len(np_events))

        except ioHubError, e:
            print2err(e)
        except:
            printExceptionDetailsToStdErr()

    def bufferedFlush(self,eventCount=1):
        # if flushCounter threshold is >=0 then do some checks. If it is < 0, then
        # flush only occurs when command is sent to ioHub, so do nothing here.
        if self.flushCounter>=0:
            if self.flushCounter==0:
                self.flush()
                return True
            if self.flushCounter<=self._eventCounter:
                self.flush()
                self._eventCounter=0
                return True
            self._eventCounter+=eventCount
            return False


    def flush(self):
        try:
            if self.emrtFile:
                self.emrtFile.flush()
        except ClosedFileError:
            pass
        except:
            printExceptionDetailsToStdErr()

    def close(self):
        self.flush()
        self._activeRunTimeConditionVariableTable=None
        self.emrtFile.close()
        
    def __del__(self):
        try:
            self.close()
        except:
            pass    

## -------------------- Utility Functions ------------------------ ##

def close_open_data_files(verbose):
    open_files = tables.file._open_files
    are_open_files = len(open_files) > 0
    if verbose and are_open_files:
        print "Closing remaining open data files:"
    for fileh in open_files.keys():
        if verbose:
            print "%s..." % (open_files[fileh].filename,)
        open_files[fileh].close()
        if verbose:
            print "done"

try:
    global registered_close_open_data_files
    if registered_close_open_data_files is True:
        pass
except:
    registered_close_open_data_files = True
    atexit.register(close_open_data_files, False)

## ---------------------- Pytable Definitions ------------------- ##
class ClassTableMappings(IsDescription):
    class_id = UInt32Col(pos=1)
    class_type_id = UInt32Col(pos=2) # Device or Event etc.
    class_name = StringCol(32,pos=3)
    table_path  = StringCol(128,pos=4)


class ExperimentMetaData(IsDescription):
    experiment_id = UInt32Col(pos=1)
    code = StringCol(24,pos=2)
    title = StringCol(48,pos=3)
    description  = StringCol(256,pos=4)
    version = StringCol(6,pos=5)
    total_sessions_to_run = UInt16Col(pos=9)    
 
class SessionMetaData(IsDescription):
    session_id = UInt32Col(pos=1)
    experiment_id = UInt32Col(pos=2)
    code = StringCol(24,pos=3)
    name = StringCol(48,pos=4)
    comments  = StringCol(256,pos=5)
    user_variables = StringCol(2048,pos=6) # will hold json encoded version of user variable dict for session


"""
# NEEDS TO BE COMPLETED    
class ParticipantMetaData(IsDescription):
    participant_id = UInt32Col(pos=1) 
    participant_code = StringCol(8,pos=2)

# NEEDS TO BE COMPLETED       
class SiteMetaData(IsDescription):
    site_id = UInt32Col(pos=1) 
    site_code = StringCol(8,pos=2)

# NEEDS TO BE COMPLETED       
class MemberMetaData(IsDescription):
    member_id =UInt32Col(pos=1) 
    username = StringCol(16,pos=2)
    password = StringCol(16,pos=3)
    email = StringCol(32,pos=4)
    secretPhrase = StringCol(64,pos=5)
    dateAdded = Int64Col(pos=6)

# NEEDS TO BE COMPLETED       
class DeviceInformation(IsDescription):
    device_id = UInt32Col(pos=1) 
    device_code = StringCol(7,pos=2)
    name =StringCol(32,pos=3)
    manufacturer =StringCol(32,pos=3)

# NEEDS TO BE COMPLETED       
class CalibrationAreaInformation(IsDescription):
    cal_id = UInt32Col(pos=1)

# NEEDS TO BE COMPLETED       
class EyeTrackerInformation(IsDescription):
    et_id = UInt32Col(pos=1)

# NEEDS TO BE COMPLETED   
class EyeTrackerSessionConfiguration(IsDescription):
    et_config_id = UInt32Col(pos=1)

# NEEDS TO BE COMPLETED       
class ApparatusSetupMetaData(IsDescription):
    app_setup_id = UInt32Col(pos=1)
    
"""