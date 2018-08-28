# -*- coding: utf-8 -*-
"""Demonstrates how to use two Condition Variables to specify a temporal filter
based on a start and end time. With the ConditionVariableBasedIP two columns of
the condition variables are used for each start time and each end time; forming
the instances of the IP.

@author: Sol

"""
from __future__ import print_function

from psychopy.iohub.datastore.pandas import ioHubPandasDataView
from psychopy.iohub.datastore.pandas.interestperiod import ConditionVariableBasedIP

exp_data = ioHubPandasDataView('io_stroop.hdf5')

# Display the first 20 unfiltered MOUSE_MOVE events
print('** KEYBOARD_PRESS Events (first 20):')
print()
print(exp_data.KEYBOARD_PRESS.head(20))
print()

# Create a Condition Variable based Interest Period.
# Interest Periods define a start and end time; any events that have a
# time >= an IP start time and <= an IP end time would be kept after
# filtering with the IP. When a ConditionVariableBasedIP is used, you
# provide the exp_data.condition_variables data frame and the name of the
# condition values column that will be used to read the ip start and end times from.
#
ip = ConditionVariableBasedIP(
    name='cv_ip',
    source_df=exp_data.condition_variables,
    start_col_name='TRIAL_START',
    end_col_name='TRIAL_END',
    criteria=[])

# Display the first 20 IP 's found using the criteria specified when creating
# the ConditionVariableBasedIP
#
print('** Condition Variable Interest Periods:')
print()
print(ip.ip_df)
print()

# Now we can filter out events from any event dataframe using the IP created.
# Any events that do not occur within one of the interest periods found in the
# data will be removed.
#
ip_events = ip.filter(exp_data.KEYBOARD_PRESS)

print('** KEYBOARD_PRESS events which occurred during an IP:')
print()
print(ip_events.head(20))
print()

exp_data.close()
