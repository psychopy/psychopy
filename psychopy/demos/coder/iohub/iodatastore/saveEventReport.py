#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example for reading events from an iohub hdf5 file.

SAVE_EVENT_TYPE and SAVE_EVENT_FIELDS specify the event type, and which event fields, are saved. Set to None
to be prompted for the event type.

Events are (optionally) split into groups (trials) by reading the time of the experiment Message event text specified
using the TRIAL_START_MESSAGE and TRIAL_END_MESSAGE variables.

Each event is saved as a row in a tab delimited text file.
"""
from psychopy.iohub.datastore.util import saveEventReport

# Specify the iohub .hdf5 file to process. None will prompt for file selection when script is run.
IOHUB_DATA_FILE = 'D:\\DEV\\my-code\\psychopy\\psychopy\\demos\\builder\\Experiments\\navon\\data\\sol_2022_Jan_11_0911.hdf5'

# Specify the PsychoPy data (results) .csv file used to group events.
# Set to None to not use a PsychoPy data file when creating event report.
PSYCHOPY_DATA_FILE = 'D:\\DEV\\my-code\\psychopy\\psychopy\\demos\\builder\\Experiments\\navon\\data\\sol_2022_Jan_11_0911.csv'

# Specify the experiment message text used to split events into trial periods.
# Set both to None to save all events.
TRIAL_START_MESSAGE = 'fixate.started' #  'target.started'
TRIAL_END_MESSAGE = 'resp.stopped' #  'fix_end_stim.started'

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
    result = saveEventReport(hdf5FilePath=IOHUB_DATA_FILE, eventType=SAVE_EVENT_TYPE, eventFields=SAVE_EVENT_FIELDS,
                             trialStart=TRIAL_START_MESSAGE, trialStop=TRIAL_END_MESSAGE,
                             psychopyDataFile=PSYCHOPY_DATA_FILE)
    if result:
        file_saved, events_saved = result
        print("Saved %d events to %s." % (events_saved, file_saved))
    else:
        raise RuntimeError("saveEventReport failed.")
