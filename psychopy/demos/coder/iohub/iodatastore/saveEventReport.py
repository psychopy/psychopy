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

# Specify the experiment message text used to split events into trial periods.
# Set both to None to save all events.
TRIAL_START_MESSAGE = None #  'target.started'
TRIAL_END_MESSAGE = None #  'fix_end_stim.started'

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
    result = saveEventReport(hdf5FilePath=None, eventType=SAVE_EVENT_TYPE, eventFields=SAVE_EVENT_FIELDS,
                             trialStartMessage=TRIAL_START_MESSAGE, trialStopMessage=TRIAL_END_MESSAGE)
    if result:
        file_saved, events_saved = result
        print("Saved %d events to %s." % (events_saved, file_saved))
    else:
        raise RuntimeError("saveEventReport failed.")
