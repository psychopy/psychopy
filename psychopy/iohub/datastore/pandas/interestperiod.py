# -*- coding: utf-8 -*-
# ioHub DataStore to Pandas DataFrames - Event Filtering Support
# Part of the psychopy.iohub library.
# .. moduleauthor:: Sol Simpson <sol@isolver-software.com> and
#                   Pierce Edmiston <pierce.edmiston@gmail.com>
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).
from __future__ import division, absolute_import, print_function

import numpy as np
import pandas as pd


class InterestPeriodDefinition(object):
    """InterestPeriodDefinition Class.

    Parent class of InterestPeriodDefinition implementations.

    """
    next_ipid = 1

    def __init__(self, name=None):
        self._name = name
        self._ipid = self.next_ipid
        self.__class__.next_ipid += 1
        if name is None:
            self._name = self.__class__.__name__ + '_' + str(self._ipid)

        self._ip_df = None

    @property
    def name(self):
        return self._name

    @property
    def ipid(self):
        return self._ipid

    def find(self, target, ip_cols=None):
        df = target[:]
        df['ip_id_num'] = np.nan
        df['ip_id'] = self.ipid
        df['ip_name'] = self.name
        df = df.groupby(level=[0, 1], group_keys=False).apply(self.__find)

        if ip_cols is not None:
            df = self._merge_ip_cols(df, ip_cols)

        return df

    def __find(self, target_group):
        group_id = target_group.index[0]
        group_ips = self.ip_df.ix[group_id]
        if len(group_ips) > 0:
            overlapping = []
            for index, ip in group_ips.iterrows():
                in_ip = ((target_group['time'] >= ip['start_time']) &
                         (target_group['time'] <= ip['end_time']))
                target_in_ip = target_group[in_ip]
                target_in_ip['ip_id_num'] = ip['ip_id_num']
                overlapping += [target_in_ip]
            target_filtered = pd.concat(overlapping)
        else:
            target_filtered = target_group[[False] * len(target_group)]
        return target_filtered

    def filter(self, target, ip_cols=None):
        df = target[:]
        df['ip_id'] = self.ipid
        df['ip_name'] = self.name
        df = target.groupby(
            level=[
                0, 1], group_keys=False).apply(
            self.__filter)

        if ip_cols is not None:
            df = self._merge_ip_cols(df, ip_cols)

        return df

    def __filter(self, group):
        """
        HT http://stackoverflow.com/a/21370058/2506078
        """
        ips = self.ip_df.ix[group.index[0]]
        start_idx = np.searchsorted(ips['start_time'], group['time']) - 1
        end_idx = np.searchsorted(ips['end_time'], group['time'])
        mask = (start_idx == end_idx)
        group['ip_id_num'] = np.nan
        group['ip_id_num'][mask] = start_idx
        return group[mask]

    def _merge_ip_cols(self, target, cols):
        if not isinstance(cols, dict):
            if not hasattr(cols, '__iter__'):
                cols = [cols]
            cols = dict(zip(cols, cols))

        temp_target = target.set_index('ip_id_num', append=True)
        temp_ips = self.ip_df.set_index('ip_id_num', append=True)
        temp_ips = temp_ips[cols.keys()]

        temp_target = temp_target.merge(
            temp_ips, left_index=True, right_index=True)
        temp_target = temp_target.rename(columns=cols)
        temp_target = temp_target.reset_index('ip_id_num')
        return temp_target

    def _extract_criteria_match(self, source, criteria, return_cols, exact):
        col = list(criteria.keys())[0]  # eventually we'll want to allow for
        val = criteria[col]      # multiple criteria matches

        if exact:
            is_match = (source[col] == val)
        else:
            is_match = (source[col].str.contains(val))

        if not isinstance(return_cols, dict):
            return_cols = dict(zip(return_cols, return_cols))

        keep_cols = list(return_cols.keys())
        matches = source[is_match][keep_cols].rename(columns=return_cols)

        return matches

    def __enumerate_ips(self, group):
        group['ip_id_num'] = range(len(group))
        return group

    def _ip_zipper(self, start, end, temp_index='ip_id_num'):
        # TODO: make sure the two dfs "zip" nicely
        _start = start.groupby(level=[0, 1]).apply(self.__enumerate_ips)
        _end = end.groupby(level=[0, 1]).apply(self.__enumerate_ips)

        _start.set_index(temp_index, append=True, inplace=True)
        _end.set_index(temp_index, append=True, inplace=True)

        _all = pd.merge(_start, _end, left_index=True, right_index=True)
        return _all.reset_index(temp_index)

#############################################


class EventBasedIP(InterestPeriodDefinition):
    """EventBasedIP Class.

    trial_ip=BoundingEventsIP(name='trial_ip',
                              start_source_df=exp_data.MESSAGE,
                              start_criteria={'text':'TRIAL_START'},
                              end_source_df=exp_data.MESSAGE,
                              end_criteria={'text':'TRIAL_END'}
                              )

    """
    next_ipid = 1

    def __init__(
            self,
            name=None,
            start_source_df=None,
            start_criteria=None,
            end_source_df=None,
            end_criteria=None,
            exact=True):
        InterestPeriodDefinition.__init__(self, name)

        self._start_source_df = start_source_df
        self._end_source_df = end_source_df or start_source_df[:]
        self._start_criteria = start_criteria
        self._end_criteria = end_criteria
        self._exact = exact

    @property
    def ip_df(self):
        """Return a Pandas DF where each row represents a start and end time
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

            start_cols = {'time': 'start_time', 'event_id': 'start_event_id'}
            start_ip_df = self._extract_criteria_match(
                self.start_source_df,
                criteria=self.start_criteria,
                return_cols=start_cols,
                exact=self._exact)

            end_cols = {'time': 'end_time', 'event_id': 'end_event_id'}
            end_ip_df = self._extract_criteria_match(
                self.end_source_df,
                criteria=self.end_criteria,
                return_cols=end_cols,
                exact=self._exact)

            self._ip_df = self._ip_zipper(start_ip_df, end_ip_df)

            # Add ip identifier cols
            self._ip_df['ip_name'] = self.name
            self._ip_df['ip_id'] = self.ipid

        return self._ip_df

    @property
    def start_source_df(self):
        return self._start_source_df

    @start_source_df.setter
    def start_source_df(self, v):
        self._start_source_df = v
        self._ip_df = None

    @property
    def end_source_df(self):
        return self._end_source_df

    @end_source_df.setter
    def end_source_df(self, v):
        self._end_source_df = v
        self._ip_df = None

    @property
    def start_criteria(self):
        return self._start_criteria

    @start_criteria.setter
    def start_criteria(self, v):
        self._start_criteria = v
        self._ip_df = None

    @property
    def end_criteria(self):
        return self._end_criteria

    @end_criteria.setter
    def end_criteria(self, v):
        self._end_criteria = v
        self._ip_df = None


##########################################

class MessageBasedIP(EventBasedIP):
    next_ipid = 1

    def __init__(self, name=None, message_df=None, start_text='TRIAL_START',
                 end_text='TRIAL_END', exact=True):
        EventBasedIP.__init__(self, name, message_df,
                              start_criteria={'text': start_text},
                              end_criteria={'text': end_text},
                              exact=exact)

##########################################


class ConditionVariableBasedIP(InterestPeriodDefinition):
    """ConditionVariableBasedIP Class.

    cv_ip=ConditionVariableBasedIP(name='cv_ip',
                        source_df=[some df],
                      start_col_name='TRIAL_START',
                      end_col_name='TRIAL_END'
                      criteria={}
                      )

    """
    next_ipid = 1

    def __init__(
            self,
            name=None,
            source_df=None,
            start_col_name=None,
            end_col_name=None,
            criteria=[]):
        InterestPeriodDefinition.__init__(self, name)

        self._source_df = source_df
        self._start_col_name = start_col_name
        self._end_col_name = end_col_name
        self._criteria = criteria

    @property
    def ip_df(self):
        """Return a Pandas DF where each row represents a start and end time
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
            self._ip_df = self._source_df[
                [self._start_col_name, self.end_col_name]]
            self._ip_df = self._ip_df.rename(
                columns={
                    self._start_col_name: 'start_time',
                    self.end_col_name: 'end_time'})

            for a_critera in self._criteria:
                # TODO: Support filtering of cond_var rows based on criteria
                pass

            # Add ip identifier cols
            self._ip_df['ip_name'] = self.name
            self._ip_df['ip_id'] = self.ipid
            self._ip_df['ip_id_num'] = range(1, len(self._ip_df) + 1)

        return self._ip_df

    @property
    def source_df(self):
        return self._source_df

    @property
    def start_col_name(self):
        return self._start_col_name

    @start_col_name.setter
    def start_col_name(self, v):
        self._start_col_name = v
        self._ip_df = None

    @property
    def end_col_name(self):
        return self._end_col_name

    @end_col_name.setter
    def end_col_name(self, v):
        self._end_col_name = v
        self._ip_df = None

    @property
    def criteria(self):
        return self._criteria

    @criteria.setter
    def criteria(self, v):
        self._criteria = v
        self._ip_df = None
