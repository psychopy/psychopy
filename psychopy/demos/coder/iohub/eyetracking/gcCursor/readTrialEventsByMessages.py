#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example of reading events from an iohub hdf5 file, saving to a tab delimited text file.

Events are split into trials by reading the time of 'TRIAL_START' and
'TRIAL_END' experiment Message events.

SAVE_EVENT_TYPE and SAVE_EVENT_FIELDS specify the event type, and which event fields, are saved.

This example can process hdf5 files saved by running the gcCursor demo.
"""
from psychopy.iohub.datastore.util import saveEventReport

# Specify which event type and event fields to save
SAVE_EVENT_TYPE = 'MonocularEyeSampleEvent'
SAVE_EVENT_FIELDS = ['time', 'gaze_x', 'gaze_y', 'pupil_measure1', 'status']
#SAVE_EVENT_TYPE = 'BinocularEyeSampleEvent'
#SAVE_EVENT_FIELDS = ['time', 'left_gaze_x', 'left_gaze_y', 'left_pupil_measure1',
#                     'right_gaze_x', 'right_gaze_y', 'right_pupil_measure1', 'status']

# Specify the experiment message text used to split events into trial periods.
# Set both to None to save all events.
TRIAL_START_MESSAGE = "TRIAL_START"
TRIAL_END_MESSAGE = "TRIAL_END"

if __name__ == '__main__':
    result = saveEventReport(hdf5FilePath=None, eventType=SAVE_EVENT_TYPE, eventFields=SAVE_EVENT_FIELDS,
                             trialStart=TRIAL_START_MESSAGE, trialStop=TRIAL_END_MESSAGE)
    if result:
        file_saved, events_saved = result
        print("Saved %d events to %s." % (events_saved, file_saved))
    else:
        raise RuntimeError("saveEventReport failed.")
