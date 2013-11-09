import pandas as pd
import numpy as np
import itertools as itls

##
## All these functions are just to generate the data frames
##
def generate_trial_starts():
    return [np.random.uniform(x, x+2) for x,y in trial_times]*len(sessions)

def generate_trial_ends():
    return [np.random.uniform(y-2, y) for x,y in trial_times]*len(sessions)

def generate_data_times():
    dtimes = []
    for _ in sessions:
        for x,y in trial_times:
            times = np.random.uniform(x-2, y+2, size=data_per_trial)
            times.sort()
            dtimes.append(times)
    return list(itls.chain(*dtimes))

def generate_data_pos():
    return [np.random.uniform(0.0, 100.0) for _ in range(data_per_trial)
                                          for _ in trial_times
                                          for _ in sessions]
    
def generate_time_periods():
    time_periods = {}
    time_periods['session_id'] = list(itls.chain(*[[s]*len(trial_times) 
                                                                for s in sessions]))
    time_periods['trial_id'] = range(1,len(trial_times)+1) * 2
    time_periods['start_time'] = generate_trial_starts()
    time_periods['end_time'] = generate_trial_ends()
    time_periods = pd.DataFrame(time_periods)
    return time_periods[['session_id','trial_id','start_time','end_time']]

def generate_messages_data():
    messages = {}
    messages['session_id'] = list(itls.chain(*[[s]*len(trial_times) 
                                                       for s in sessions]))*2
    messages['trial_id'] = range(1,len(trial_times)+1) * 2 * 2
    messages['message_text'] = ['TRIAL_START']*(len(messages['session_id'])/2) + \
                                   ['TRIAL_END']*(len(messages['session_id'])/2)
    messages['event_time'] = generate_trial_starts() + generate_trial_ends()
    messages = pd.DataFrame(messages)
    messages = messages.sort(['session_id','trial_id','message_text'], ascending=[1,1,0])
    return messages[['session_id','trial_id','message_text','event_time']]
    
def generate_mouse_data():
    mouse_data = {}
    mouse_data['session_id'] = list(itls.chain(*[[s]*len(trial_times)*data_per_trial
                                                                for s in sessions]))
    mouse_data['trial_id'] = list(itls.chain(*[[i]*data_per_trial
                          for i in range(1,len(trial_times)+1)]))*len(sessions)
    mouse_data['event_time'] = generate_data_times()
    mouse_data['event_data'] = generate_data_pos()
    mouse_data = pd.DataFrame(mouse_data)
    return mouse_data[['session_id','trial_id','event_time','event_data']]

##
## Parameters for data generation
##
sessions = [1, 2]
trial_times = [(2.0,8.0), (12.0, 18.0), (22.0, 28.0), (32.0, 38.0)]
data_per_trial = 10

time_periods = generate_time_periods()
print time_periods
mouse_data = generate_mouse_data()
print mouse_data.head(20)
##
## Merge the two data frames and trim
##
df = pd.merge(time_periods, mouse_data, on=['session_id','trial_id'])
print '---------BEFORE TRIM---------'
print 'Length: ',len(df)
print df.head(20)
df = df[(df['event_time'] > df['start_time']) &
        (df['event_time'] < df['end_time'])]
print '---------AFTER TRIM---------'
print 'Length: ',len(df)
print df.head(20)

##
## Works even if you don't have a dedicated 'trial_id' second-level indicator
##
df = pd.merge(time_periods, mouse_data, on='session_id')
print '---------BEFORE TRIM---------'
print 'Length (too big without second-level trial_id indicator): ',len(df)
print df.head(20)
df = df[(df['event_time'] > df['start_time']) &
        (df['event_time'] < df['end_time'])]
print '---------AFTER TRIM---------'
print 'Length (but still works just fine): ',len(df)
print df.head(20)

##
## We can also do the same from just the messages (one option is to use a pivot table)
##
messages = generate_messages_data()
# equivalent to: messages = messages[(messages['event_text']=='TRIAL_START') | (messages['event_text']=='TRIAL_END')]
messages = pd.pivot_table(messages, values='event_time', rows=['session_id','trial_id'],
                          cols=['message_text'])
messages = messages.reset_index(level=['session_id','trial_id'])
df = pd.merge(messages, mouse_data, on=['session_id','trial_id'])
df = df[(df['event_time'] > df['TRIAL_START']) &
        (df['event_time'] < df['TRIAL_END'])]


