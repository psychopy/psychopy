# -*- coding: utf-8 -*-
from __future__ import division
"""
ioHub DataStore to Pandas DataFrame Module with Event Filtering Support

.. file: ..../iohubpandas/__init__.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License 
(GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> and
                  Pierce Edmiston <pierce.edmiston@gmail.com>
"""

import numpy as np
import pandas as pd
#import matplotlib as mpl
#import matplotlib.pyplot as plt

from interestarea import Polygon

#from interestperiod import InterestPeriodDefinition

# TODO Replace with EventConstants.getConstants()
# when code change is added to iohub source.
def getEventConstants():
    from psychopy.iohub import EventConstants
    return EventConstants._names

                  
class ioHubPandasDataView(object):
    def __init__(self,datastore_file):
        self._hdf_store=pd.HDFStore(datastore_file)        
        self._event_constants=None
        self._event_table_info=None
        self._experiment_meta_data=None
        self._session_meta_data=None
        self._condition_variables=None

        self._event_data_by_type=dict()
        self._all_events=None
        
    @property
    def hdf_store(self):
        """
        hdf_store
        """
        return self._hdf_store

    @property
    def event_constants(self):
        """
        event_constants
        """
        if self._event_constants is None:
            self._event_constants=getEventConstants()
        return self._event_constants
        
    @property
    def event_table_info(self):
        """event_table_info property."""
        if self._event_table_info is None:
            self._event_table_info=self._hdf_store.select('class_table_mapping', columns=['class_id','class_name','table_path'])
            self._event_table_info['class_id']=self._event_table_info['class_id'].map(self.event_constants)            
            self._event_table_info.set_index('class_id',inplace=True)
        return self._event_table_info

    @property
    def experiment_meta_data(self):
        """experiment_meta_data property."""
        if self._experiment_meta_data is None:
            self._experiment_meta_data=self._hdf_store.select('/data_collection/experiment_meta_data')
            self._experiment_meta_data.replace('', np.nan,inplace=True)
            self._experiment_meta_data.set_index(['experiment_id','code'],inplace=True)             
        return self._experiment_meta_data

    @property
    def session_meta_data(self):
        """session_meta_data property."""
        if self._session_meta_data is None:
            self._session_meta_data=self._hdf_store.select('/data_collection/session_meta_data')
            self._session_meta_data.replace('', np.nan,inplace=True)
            self._session_meta_data.set_index(['session_id'],inplace=True)
        return self._session_meta_data

    @property
    def condition_variables(self):
        """condition_variables property."""
        if self._condition_variables is None:
            cv_table_proto='/data_collection/condition_variables/EXP_CV_%d'
            for experiment_id in self.experiment_meta_data.index.levels[0].values:
                exp_cv=cv_table_proto%experiment_id
                try:            
                    cv_df=self._hdf_store.select(exp_cv)
                    cv_df.set_index(['EXPERIMENT_ID','SESSION_ID'],inplace=True)
                    if self._condition_variables is None:
                        self._condition_variables=cv_df
                    else:
                        self._condition_variables.add(cv_df)
                except Exception, e:
                    print 'Error loading experiment CV: ', e
        return self._condition_variables
        
    @property
    def all_events(self):
        """all_events property."""
        if self._all_events is None:
            self._createGlobalEventData()
        return self._all_events

    def __getattr__(self,n):
        if not self._event_data_by_type.get(n):
            try:
                row=self.event_table_info.ix[n]
                if not row['table_path'].endswith('KeyboardCharEvent'):
                    event_data=self._hdf_store.select(row['table_path'])
                    event_data=event_data[event_data.type == self.event_constants[n]]
                    event_data['type']=n
                    event_data.set_index(['experiment_id','session_id','time'],inplace=True)   
                    event_data.sort_index()
                    event_data.reset_index('time',inplace=True)
                    self._event_data_by_type[n]=event_data
                else:            
                    raise AttributeError(self.__class__.__name__+" does not support "+n)
            except Exception, e:
                raise AttributeError(self.__class__.__name__+" does not have a data frame for "+n)
                raise e
        return self._event_data_by_type[n]

    def _createGlobalEventData(self):
        global_event_fields=['time','device_id','event_id','type','device_time',
                             'logged_time','confidence_interval','delay',
                             'filter_id']
                             
        for index,row in self.event_table_info.iterrows():
            if not row['table_path'].endswith('KeyboardCharEvent'):
                event_data=getattr(self,index,None)
                if event_data is None:                    
                    raise AttributeError("_createGlobalEventData:"+index+" event type does not exist.")
                    
                if self._all_events is None:
                    self._all_events=event_data[global_event_fields]
                else:
                    self._all_events=pd.concat([self._all_events,event_data[global_event_fields]],axis=0)
            else:
                print '** TODO: LOAD KeyboardCharEvent table. **'
        self._all_events.sort()
            

    def closeDataStoreFile(self):
        if self._hdf_store:
            self._hdf_store.close()
            self._hdf_store=None

    def close(self):
        self.closeDataStoreFile()
        
    def __del__(self):
        self.close()