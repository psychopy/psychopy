# -*- coding: utf-8 -*-
"""
Created on Fri Nov 01 09:32:29 2013

@author: Sol
"""

import pandas as pd
from iohubpandas import ioHubPandasDataView
from iohubpandas.interestarea import Circle,Ellipse,Rectangle
from iohubpandas.interestperiod import MessageBasedIP,ConditionVariableBasedIP

pd.set_option('max_columns',30)
pd.set_option('max_rows',30)

import timeit
getTime=timeit.default_timer

exp_data=ioHubPandasDataView('io_stroop.hdf5')#events_fiona_rz.hdf5')

print 'Available Event Tables:'
print
print exp_data.event_table_info
print

print 'Condition Variable Info (first 10):',exp_data.condition_variables.shape
print
print exp_data.condition_variables.head(10)
print

print 'All Event Info (first and last 10):',exp_data.all_events.shape
print
print exp_data.all_events.head(10)
print '...'
print exp_data.all_events.tail(10)
print

print 'KEYBOARD_PRESS events (first 10):',exp_data.KEYBOARD_PRESS.shape
print exp_data.KEYBOARD_PRESS
print
print 'MESSAGE events (first 10):',exp_data.MESSAGE.shape
print exp_data.MESSAGE.head(10)
print
#print 'MULTI_CHANNEL_ANALOG_INPUT events (first 10):',exp_data.MULTI_CHANNEL_ANALOG_INPUT.shape
#print exp_data.MULTI_CHANNEL_ANALOG_INPUT.head(10)
#print
#print 'MULTI_CHANNEL_ANALOG_INPUT Event Count:',exp_data.MULTI_CHANNEL_ANALOG_INPUT.delay.count()
#print 'MULTI_CHANNEL_ANALOG_INPUT Min Delay:',exp_data.MULTI_CHANNEL_ANALOG_INPUT.delay.min()
#print 'MULTI_CHANNEL_ANALOG_INPUT Max Delay:',exp_data.MULTI_CHANNEL_ANALOG_INPUT.delay.max()
#print 'MULTI_CHANNEL_ANALOG_INPUT Average Delay:',exp_data.MULTI_CHANNEL_ANALOG_INPUT.delay.mean()
print

#exp_data.close()
    
print '==== IP Tests ===='
print
print '>> MessageBasedIP:'
print
ip=MessageBasedIP(name='trial_ip',
                                  start_source_df=exp_data.MESSAGE,
                                  start_criteria={'text':'TRIAL_START'},
                                  end_source_df=exp_data.MESSAGE,
                                  end_criteria={'text':'TRIAL_END'})
print '## BoundingEventsIP instances for "{0}"; count: {1}'.format(ip.name,
                                                                len(ip.ip_df))
print
print ip.ip_df
print

ip_events=ip.filter(exp_data.KEYBOARD_PRESS)
if ip_events:
    print '## KEYBOARD_PRESS events within BoundingEventsIP:',len(ip_events)
    print ip_events
else:
    print '!! NO MATCHING EVENTS FOUND within BoundingEventsIP !!'
print
print '<< MessageBasedIP:'
print
print '================================'

print
print '>> ConditionVariableBasedIP:'
print
ip=ConditionVariableBasedIP(name='cv_ip',source_df=exp_data.condition_variables,
                       start_col_name='TRIAL_START',
                       end_col_name='TRIAL_END',
                       criteria=[])
print
print                       
print '## ConditionVariableBasedIP instances for "{0}"; count: {1}'.format(ip.name,len(ip.ip_df))
print
print ip.ip_df.head(25)
print

print 'Getting events....'
print
ip_events=ip.filter(exp_data.KEYBOARD_PRESS)
if ip_events:
    print '## KEYBOARD_PRESS events within ConditionVariableBasedIP:',len(ip_events)
    print ip_events
    print
else:
    print '!! NO MATCHING EVENTS FOUND within ConditionVariableBasedIP !!'







#
#print '==== IA Tests ===='
#print '( Currently, this can take a while ... )'
#print
#
#################
#
#circle = Circle('Circle IA',[0,0],400)
#rect=Rectangle('Rect IA',-200,200,200,-200)
#ellipse=Ellipse('Ellipse IA',[300,300],100,200,45)
#spot=Circle('Spot IA',[300,300],10)
#
#
##############                        
#print
#print 'MOUSE_BUTTON_RELEASE circle IAs:'
#print circle.filter(exp_data.MOUSE_BUTTON_RELEASE).head(25)
#print
#print 'MOUSE_BUTTON_PRESS ellipse IAs:'
#print ellipse.filter(exp_data.MOUSE_BUTTON_PRESS).head(25)
#print
#
#exp_data.close()