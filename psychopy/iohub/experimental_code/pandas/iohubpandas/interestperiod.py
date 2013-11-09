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


class InterestPeriodDefinition(object):
    """
    InterestPeriodDefinition Class
    
    trial_ip=InterestPeriodDefinition(name='trial_ip',
                                      start_source_df=exp_data.MESSAGE,
                                      start_criteria={'text':'TRIAL_START'},
                                      end_source_df=exp_data.MESSAGE,
                                      end_criteria={'text':'TRIAL_END'}
                                      )

    """
    next_ipid=1
    def __init__(self,name=None,start_source_df=None,start_criteria=None,end_source_df=None,end_criteria=None):
        self._name=name
        self._ipid=self.next_ipid
        self.__class__.next_ipid+=1
        if name is None:
            self._name=self.__class__.__name__+'_'+str(self._ipid)

        self._start_source_df=start_source_df
        self._end_source_df=end_source_df
        self._start_criteria=start_criteria
        self._end_criteria=end_criteria
        self._ip_df=None
    
    @property
    def name(self):
        return self._name

    @property
    def ipid(self):
        return self._ipid
        
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
        
    def filter(self,target_df):
        """
        For the target_df (an ioHub Event Pandas DF created by the 
        ioHubPandasDataView class), return all events within target_df where:

            ip_start_time <= event_time <= ip_end_time

        for each row of self.ip_df.
        """
        ip_evts=target_df.merge(self.ip_df,left_index =True, right_index=True)
        return ip_evts[(ip_evts['time'] >= ip_evts['start_time']) 
                     & (ip_evts['time'] <= ip_evts['end_time'])]
        

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
