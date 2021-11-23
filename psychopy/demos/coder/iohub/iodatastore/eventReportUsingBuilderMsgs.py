#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example for reading events from an iohub hdf5 file created using a Builder eye tracking experiment.

SAVE_EVENT_TYPE and SAVE_EVENT_FIELDS specify the event type, and which event fields, are saved.

Events are split into trials by reading the time of the experiment Message event text specified using the
TRIAL_START_MESSAGE and TRIAL_END_MESSAGE variables. Each saved event includes 'TRIAL_INDEX', 'TRIAL_START_TIME',
and 'TRIAL_STOP_TIME' columns.

Each event is saved as a row in a tab delimited text file.
"""
import sys
import os
from psychopy.iohub.datastore.util import ExperimentDataAccessUtility
from psychopy.iohub.datastore.util import displayDataFileSelectionDialog

# Specify the experiment message text used to split events into trial periods.
TRIAL_START_MESSAGE = 'target.started'
TRIAL_END_MESSAGE = 'target.stopped'
# Specify which event type and event fields to save
SAVE_EVENT_TYPE = 'MonocularEyeSampleEvent'
SAVE_EVENT_FIELDS = ['time', 'gaze_x', 'gaze_y', 'pupil_measure1', 'status']
# SAVE_EVENT_TYPE = 'BinocularEyeSampleEvent'
# SAVE_EVENT_FIELDS = ['time', 'left_gaze_x', 'left_gaze_y', 'left_pupil_measure1',
#                     'right_gaze_x', 'right_gaze_y', 'right_pupil_measure1', 'status']
# SAVE_EVENT_TYPE = 'MessageEvent'
# SAVE_EVENT_FIELDS = ['time', 'text']

if __name__ == '__main__':
    # Select the hdf5 file to process.
    data_file_path = displayDataFileSelectionDialog(os.path.dirname(os.path.abspath(__file__)))
    if data_file_path is None:
        print("File Selection Cancelled, exiting...")
        sys.exit(0)
    data_file_path = data_file_path[0]
    dpath, dfile = os.path.split(data_file_path)

    datafile = ExperimentDataAccessUtility(dpath, dfile)

    # Create a table of trial_index, trial_start_time, trial_end_time for each trial by
    # getting the time of 'TRIAL_START' and 'TRIAL_END' experiment messages.
    trial_times = []
    mgs_table = datafile.getEventTable('MessageEvent')
    trial_start_msgs = mgs_table.where('text == b"%s"' % TRIAL_START_MESSAGE)
    for mix, msg in enumerate(trial_start_msgs):
        trial_times.append([mix + 1, msg['time']-0.0001, 0])
    trial_end_msgs = mgs_table.where('text == b"%s"' % TRIAL_END_MESSAGE)
    for mix, msg in enumerate(trial_end_msgs):
        trial_times[mix][2] = msg['time']+0.0001
    ecount = 0
    del mgs_table

    # Get the event table to generate report for
    event_table = datafile.getEventTable(SAVE_EVENT_TYPE)

    if SAVE_EVENT_TYPE == 'MessageEvent':
        # Sort experiment messages by time since they may not be ordered chronologically.
        event_table = event_table.read()
        event_table.sort(order='time')

    # Open a file to save the tab delimited output to.
    output_file_name = os.path.join(dpath, "%s.txt" % (dfile[:-5]))
    with open(output_file_name, 'w') as output_file:
        print('Writing Data to %s:\n' % (output_file_name))

        # Save header row to file
        column_names = ['TRIAL_INDEX', 'TRIAL_START_TIME', 'TRIAL_STOP_TIME'] + SAVE_EVENT_FIELDS
        output_file.write('\t'.join(column_names))
        output_file.write('\n')

        for tindex, tstart, tstop in trial_times:
            if SAVE_EVENT_TYPE == 'MessageEvent':
                trial_events = event_table[(event_table['time'] >= tstart) & (event_table['time'] <= tstop)]
            else:
                trial_events = event_table.where("(time >= %f) & (time <= %f)" % (tstart, tstop))

            # Save a row for each event within the trial period
            for event in trial_events:
                event_data = [str(event[c]) for c in SAVE_EVENT_FIELDS]
                output_file.write('\t'.join([str(tindex), str(tstart), str(tstop)] + event_data))
                output_file.write('\n')
                ecount += 1
                if ecount % 100 == 0:
                    sys.stdout.write('.')

    print("\n\nWrote %d events." % ecount)
    datafile.close()
