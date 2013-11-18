# -*- coding: utf-8 -*-
"""
Demonstrates how to use event dataframe columns and value matching to 
define an interest period. An Interest Period is a temporal filter that can be used
to remove events from a dataframe that did not occur within the IP's start and 
end time period. In this example MESSAGE events are queried, retrieving
any messages that where written with specific start and end trial text. The
time of each start and end message set is used to form each IP instance that
can be used for filtering.

@author: Sol
"""

from psychopy.iohub.datastore.pandas import ioHubPandasDataView
from psychopy.iohub.datastore.pandas.interestperiod import EventBasedIP

exp_data=ioHubPandasDataView('io_stroop.hdf5')

# Display the first 20 unfiltered MOUSE_MOVE events
print '** KEY_PRESS Events (first 20):'
print 
print exp_data.KEYBOARD_PRESS.head(20)
print

# Create an Event based Interest Period. Interest Periods define a start and 
# end time; any events that have a time >= an IP start time and <= an IP
# end time would be kept after filtering with the IP. Here the interest 
# period start time is based on MESSAGE events that have the text of 
# 'TRIAL_START'. The IP end time is based on MESSAGE events
# with a text field equal to 'TRIAL_END'.
#
ip=EventBasedIP(name='trial_ip',
              start_source_df=exp_data.MESSAGE,
              start_criteria={'text':'TRIAL_START'},
              end_source_df=exp_data.MESSAGE,
              end_criteria={'text':'TRIAL_END'})

# Display the first 20 IP 's found using the criteria specified when creating 
# the EventBasedIP
#
print '** MESSAGE Interest Periods (TRIAL_START to TRIAL_END):'
print 
print ip.ip_df
print

# Now we can filter out events from any event dataframe using the IP created.
# Any events that do not occur within one of the interest periods found in the
# data will be removed.  
#
ip_events=ip.filter(exp_data.KEYBOARD_PRESS)

print '** KEYBOARD_PRESS events which occurred during an IP:'
print 
print ip_events.head(20)
print 

exp_data.close()