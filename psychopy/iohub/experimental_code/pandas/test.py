# -*- coding: utf-8 -*-
"""
Created on Fri Nov 01 09:32:29 2013

@author: Sol
"""

import pandas as pd
from iohubpandas import ioHubPandasDataView
from iohubpandas.interestarea import Circle,Ellipse,Rectangle
from iohubpandas.interestperiod import InterestPeriodDefinition

pd.set_option('max_columns',30)

import timeit
getTime=timeit.default_timer

exp_data=ioHubPandasDataView('io_stroop.hdf5')

print 'Event Constant Mapping:'
print exp_data.event_constants
print

print 'Available Event Tables:'
print
print exp_data.event_table_info
print

print 'Experiment Info:'
print
print exp_data.experiment_meta_data
print

print 'Session Info:'
print
print exp_data.session_meta_data
print

print 'Condition Variable Info:'
print
print exp_data.condition_variables
print

print 'MESSAGE events:'
print exp_data.MESSAGE.head(25)
print

print 'MOUSE_BUTTON_PRESS events:'
print exp_data.MOUSE_BUTTON_PRESS.head(25)
print

print 'All Event Info:'
print
print exp_data.all_events.head(25)
print '...'
print exp_data.all_events.tail(25)
print

print 'MOUSE_MOVE events:'
print exp_data.MOUSE_MOVE.head(25)
print


try:      
    print 'BAD_EVENT_TYPE events:'
    print exp_data.BAD_EVENT_TYPE.head(25)
    print
except Exception, e:
    print 'Attempt to get BAD_EVENT_TYPE failed (which it should have).'
    print e
    print
    
print '==== IP Tests ===='
print
trial_ip=InterestPeriodDefinition(name='trial_ip',
                                  start_source_df=exp_data.MESSAGE,
                                  start_criteria={'text':'TRIAL_START'},
                                  end_source_df=exp_data.MESSAGE,
                                  end_criteria={'text':'TRIAL_END'})
print '## Data Interest Periods for "{0}"; count: {1}'.format(trial_ip.name,
                                                                len(trial_ip.ip_df))
print
print trial_ip.ip_df.head(25)
print

trial_ip_kb_presses=trial_ip.filter(exp_data.KEYBOARD_PRESS)
print '## KEYBOARD_PRESS events within a Interest Period:',len(trial_ip_kb_presses)
print trial_ip_kb_presses.head(25)
print

print '==== IA Tests ===='
print '( Currently, this can take a while ... )'
print

################

circle = Circle('Circle IA',[0,0],400)
rect=Rectangle('Rect IA',-200,200,200,-200)
ellipse=Ellipse('Ellipse IA',[300,300],100,200,45)
spot=Circle('Spot IA',[300,300],10)


#############                        
print
print 'MOUSE_BUTTON_RELEASE circle IAs:'
print circle.filter(exp_data.MOUSE_BUTTON_RELEASE).head(25)
print
print 'MOUSE_BUTTON_PRESS ellipse IAs:'
print ellipse.filter(exp_data.MOUSE_BUTTON_PRESS).head(25)
print

exp_data.close()