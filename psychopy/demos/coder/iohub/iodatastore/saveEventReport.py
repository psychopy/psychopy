#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example for reading events from an iohub hdf5 file. Events can optionally be grouped (typically into trials) by either:
    1. Reading iohub experiment messages
    2. Reading the iohub .hdf5 condition variables table
    3. Reading a psychopy trial-by-trial .csv data (results) file
When grouping events, use the TRIAL_START and TRIAL_END variables to specify the message text or column names to use
to find the start and end time for each trial period.

SAVE_EVENT_TYPE and SAVE_EVENT_FIELDS specify the event type, and which event fields, are saved. Set to None
to be prompted for the event type.

Each event is saved as a row in a tab delimited text file.
"""
from psychopy.iohub.datastore.util import saveEventReport

# Specify the iohub .hdf5 file to process. None will prompt for file selection when script is run.
IOHUB_DATA_FILE = None

# If True, psychopy .csv file with same path as IOHUB_DATA_FILE will be used
USE_PSYCHOPY_DATA_FILE = False

# If True, iohub .hdf5 condition variable table will be used to split events based on TRIAL_START and TRIAL_END
USE_CONDITIONS_TABLE = False

# Specify the experiment message text used to split events into trial periods.
# Set both to None to save all events.
TRIAL_START = None#'text.started' #  'target.started'
TRIAL_END = None#'fix_end_stim.started' #  'fix_end_stim.started'

# Specify which event type to save. Setting to None will prompt to select an event table
SAVE_EVENT_TYPE = None  # 'MonocularEyeSampleEvent'
# Specify which event fields to save. Setting to None will save all event fields.
SAVE_EVENT_FIELDS = None  # ['time', 'gaze_x', 'gaze_y', 'pupil_measure1', 'status']

# SAVE_EVENT_TYPE = 'BinocularEyeSampleEvent'
# SAVE_EVENT_FIELDS = ['time', 'left_gaze_x', 'left_gaze_y', 'left_pupil_measure1',
#                     'right_gaze_x', 'right_gaze_y', 'right_pupil_measure1', 'status']

# SAVE_EVENT_TYPE = 'MessageEvent'
# SAVE_EVENT_FIELDS = ['time', 'text']

if __name__ == '__main__':
    result = saveEventReport(hdf5FilePath=IOHUB_DATA_FILE,
                             eventType=SAVE_EVENT_TYPE,
                             eventFields=SAVE_EVENT_FIELDS,
                             useConditionsTable=USE_CONDITIONS_TABLE,
                             usePsychopyDataFile=USE_PSYCHOPY_DATA_FILE,
                             trialStart=TRIAL_START,
                             trialStop=TRIAL_END)
    if result:
        file_saved, events_saved = result
        print("Saved %d events to %s." % (events_saved, file_saved))
    else:
        raise RuntimeError("saveEventReport failed.")
