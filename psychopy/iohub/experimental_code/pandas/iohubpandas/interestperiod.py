# -*- coding: utf-8 -*-
from __future__ import division
"""
ioHub DataStore to Pandas DataFrame Module with Event Filtering Support

.. file: ..../iohubpandas/interestperiod.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License 
(GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> and
                  Pierce Edmiston <pierce.edmiston@gmail.com>
"""

import numpy as np
import pandas as pd

class InterestPeriodDefinition(object):
    """
    InterestPeriodDefinition Class
    
    Parent class of InterestPeriodDefinition implementations.

    """
    next_ipid=1
    def __init__(self,name=None):
        self._name=name
        self._ipid=self.next_ipid
        self.__class__.next_ipid+=1
        if name is None:
            self._name=self.__class__.__name__+'_'+str(self._ipid)

        self._ip_df=None
    
    @property
    def name(self):
        return self._name

    @property
    def ipid(self):
        return self._ipid
        
    def _filter_group(self, target_group):
        group_id = target_group.index[0]
        group_ips = self.ip_df.ix[group_id]
        if len(group_ips) > 0:
            overlapping = []
            for index, ip in group_ips.iterrows():
                in_ip = ((target_group['time'] >= ip['start_time']) &
                         (target_group['time'] <= ip['end_time']))
                target_in_ip = target_group[in_ip]
                target_in_ip['ip_id_num'] = ip['ip_id_num']
                target_in_ip['ip_id'] = ip['ip_id']
                target_in_ip['ip_name'] = ip['ip_name']
                overlapping += [target_in_ip]
            target_filtered = pd.concat(overlapping)
        else:
            target_filtered = target_group[[False]*len(target_group)]
        return target_filtered
        
    def filter(self, target_df):
        filtered_df = target_df[:]
        filtered_df['ip_id_num'] = np.nan        
        filtered_df['ip_id'] = np.nan
        filtered_df['ip_name'] = np.nan
        return filtered_df.groupby(level=[0,1], group_keys=False).apply(self._filter_group)
        
        
#############################################

class MessageBasedIP(InterestPeriodDefinition):
    """
    MessageBasedIP Class
    
    trial_ip=BoundingEventsIP(name='trial_ip',
                              start_source_df=exp_data.MESSAGE,
                              start_criteria={'text':'TRIAL_START'},
                              end_source_df=exp_data.MESSAGE,
                              end_criteria={'text':'TRIAL_END'}
                              )

    """
    next_ipid=1
    def __init__(self,name=None,start_source_df=None,start_criteria=None,end_source_df=None,end_criteria=None):
        InterestPeriodDefinition.__init__(self,name)

        self._start_source_df=start_source_df
        self._end_source_df=end_source_df
        self._start_criteria=start_criteria
        self._end_criteria=end_criteria

            
    @property
    def ip_df(self):  
        """
        Return a Pandas DF where each row represents a start and end time
        instance that matches the InterestPeriodDefinition criteria.

        ip_df is indexed on:
            experiment_id
            session_id
            
        ip_df has columns:
            start_time
            start_event_id
            end_time
            end_event_id
            ip_name
            ip_id
            ip_id_num
        """
        if self._ip_df is None:
            # Match start_source_df[start_criteria.key]==start_criteria.value
            # Currently only support ip criteria in the form of 
            # {*_df_col_name:*_df_col_value} for ip start time and ip end time
            # selections, where rows from start_source_df will be selected when:
            #
            #   start_source_df[df_col_name] == df_col_value, 
            #            
            # and rows from end_source_df will be selected when:
            #
            #   start_source_df[start_df_col_name] == start_df_col_value
            start_source_df=self.start_source_df
            start_criteria_col=self.start_criteria.keys()[0]
            start_criteria_val=self.start_criteria[start_criteria_col]
            self._ip_df = start_source_df[start_source_df[start_criteria_col] == start_criteria_val][['time','event_id']]
            self._ip_df = self._ip_df.rename(columns={'time': 'start_time', 'event_id': 'start_event_id'})
            
            # Add ip end cols to rows
            # TODO: Is this really a safe way to add ip start time 
            #       and end time matches ??
            end_source_df=self.end_source_df
            if end_source_df is None:
                end_source_df=start_source_df
            end_criteria_col=self.end_criteria.keys()[0]
            end_criteria_val=self.end_criteria[end_criteria_col]
            self._ip_df[['end_time','end_event_id']]=end_source_df \
                        [end_source_df[end_criteria_col] == end_criteria_val] \
                        [['time','event_id']]
            
            # Add ip identifier cols
            self._ip_df['ip_name']=self.name            
            self._ip_df['ip_id']=self.ipid            
            self._ip_df['ip_id_num']=range(1,len(self._ip_df)+1)   
            
        return self._ip_df  


    @property        
    def start_source_df(self):
        return self._start_source_df

    @start_source_df.setter        
    def start_source_df(self,v):
        self._start_source_df=v
        self._ip_df=None

    @property        
    def end_source_df(self):
        return self._end_source_df

    @end_source_df.setter        
    def end_source_df(self,v):
        self._end_source_df=v
        self._ip_df =None

    @property        
    def start_criteria(self):
        return self._start_criteria

    @start_criteria.setter        
    def start_criteria(self,v):
        self._start_criteria=v
        self._ip_df=None

    @property        
    def end_criteria(self):
        return self._end_criteria

    @end_criteria.setter        
    def end_criteria(self,v):
        self._end_criteria=v
        self._ip_df=None


##########################################

class ConditionVariableBasedIP(InterestPeriodDefinition):
    """
    ConditionVariableBasedIP Class
    
    cv_ip=ConditionVariableBasedIP(name='cv_ip',
                        source_df=[some df],
                      start_col_name='TRIAL_START',
                      end_col_name='TRIAL_END'
                      criteria={}
                      )

    """
    next_ipid=1
    def __init__(self,name=None,source_df=None,start_col_name=None,end_col_name=None,criteria=[]):
        InterestPeriodDefinition.__init__(self,name)

        self._source_df=source_df
        self._start_col_name=start_col_name
        self._end_col_name=end_col_name
        self._criteria=criteria
    
    @property    
    def ip_df(self):  
        """
        Return a Pandas DF where each row represents a start and end time
        instance that matches the InterestPeriodDefinition criteria.

        ip_df is indexed on:
            experiment_id
            session_id
            
        ip_df has columns:
            start_time
            end_time
            ip_name
            ip_id
            ip_id_num        
        """
        if self._ip_df is None:
            self._ip_df=self._source_df[[self._start_col_name,self.end_col_name]]
            self._ip_df = self._ip_df.rename(columns={self._start_col_name: 'start_time', self.end_col_name: 'end_time'})             

            for a_critera in self._criteria:
                #TODO: Support filtering of cond_var rows based on critera 
                pass

            # Add ip identifier cols
            self._ip_df['ip_name']=self.name            
            self._ip_df['ip_id']=self.ipid            
            self._ip_df['ip_id_num']=range(1,len(self._ip_df)+1)   
            
        return self._ip_df
                     
    @property        
    def source_df(self):
        return self._source_df

    @property        
    def start_col_name(self):
        return self._start_col_name

    @start_col_name.setter        
    def start_col_name(self,v):
        self._start_col_name=v
        self._ip_df=None

    @property        
    def end_col_name(self):
        return self._end_col_name

    @end_col_name.setter        
    def end_col_name(self,v):
        self._end_col_name=v
        self._ip_df =None

    @property        
    def criteria(self):
        return self._criteria

    @criteria.setter        
    def criteria(self,v):
        self._criteria=v
        self._ip_df=None
