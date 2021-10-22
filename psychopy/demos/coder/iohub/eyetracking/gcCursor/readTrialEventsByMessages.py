#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example of reading events from a hdf5 file, saving to a tab delimited text file.

Events are split into trials by reading the time of 'TRIAL_START' and
'TRIAL_END' experiment Message events.

SAVE_EVENT_TYPE and SAVE_EVENT_FIELDS specify the event type, and which event fields, are saved.

This example can process hdf5 files saved by running the gcCursor demo.
"""
import sys
import os
from psychopy.iohub.datastore.util import ExperimentDataAccessUtility
from psychopy.iohub.datastore.util import displayDataFileSelectionDialog

# Specify which event type and event fields to save
SAVE_EVENT_TYPE = 'MonocularEyeSampleEvent'
SAVE_EVENT_FIELDS = ['time', 'gaze_x', 'gaze_y', 'pupil_measure1', 'status']

#SAVE_EVENT_TYPE = 'BinocularEyeSampleEvent'
#SAVE_EVENT_FIELDS = ['time', 'left_gaze_x', 'left_gaze_y', 'left_pupil_measure1',
#                     'right_gaze_x', 'right_gaze_y', 'right_pupil_measure1', 'status']

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
    trial_start_msgs = datafile.getEventTable('MessageEvent').where('text == b"TRIAL_START"')
    for mix, msg in enumerate(trial_start_msgs):
        trial_times.append([mix + 1, msg['time'], 0])

    trial_end_msgs = datafile.getEventTable('MessageEvent').where('text == b"TRIAL_END"')
    for mix, msg in enumerate(trial_end_msgs):
        trial_times[mix][2] = msg['time']

    ecount = 0

    # str prototype used to select events within a trial time period
    event_select_proto = "(time >= %f) & (time <= %f)"

    # Open a file to save the tab delimited output to.
    #
    output_file_name = "%s.txt" % (dfile[:-5])
    with open(output_file_name, 'w') as output_file:
        print('Writing Data to %s:\n' % (output_file_name))

        # Save header row to file
        column_names = ['TRIAL_INDEX', ] + SAVE_EVENT_FIELDS
        output_file.write('\t'.join(column_names))
        output_file.write('\n')

        for tindex, tstart, tstop in trial_times:
            trial_events = datafile.getEventTable(SAVE_EVENT_TYPE).where(event_select_proto % (tstart, tstop))
            # Save a row for each event within the trial period
            for event in trial_events:
                event_data = [str(event[c]) for c in SAVE_EVENT_FIELDS]
                output_file.write('\t'.join([str(tindex), ] + event_data))
                output_file.write('\n')
                ecount += 1
                if ecount % 100 == 0:
                    sys.stdout.write('.')

    print("\n\nWrote %d events." % ecount)
    datafile.close()
