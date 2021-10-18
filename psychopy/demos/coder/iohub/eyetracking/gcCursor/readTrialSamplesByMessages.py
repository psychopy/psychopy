#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example of reading MonocularEyeSampleEvent's from a hdf5 file, saving to a tab delimited text file.

Samples are split into trials by reading the time of 'TRIAL_START' and 'TRIAL_END' experiment Message events.

This example can process hdf5 files saved by running the gcCursor demo.
"""
import sys, os
from psychopy import core
import psychopy.iohub
from psychopy.iohub.datastore.util import displayDataFileSelectionDialog, ExperimentDataAccessUtility

SAVE_EVENT_TYPE = 'MonocularEyeSampleEvent'
SAVE_EVENT_FIELDS = ['time', 'gaze_x', 'gaze_y', 'pupil_measure1', 'status']

def getTime():
    return core.getTime()

if __name__ == '__main__':
    # Select the hdf5 file to process.
    data_file_path = displayDataFileSelectionDialog(psychopy.iohub.module_directory(getTime))
    if data_file_path is None:
        print("File Selection Canceled, exiting...")
        sys.exit(0)
    data_file_path = data_file_path[0]
    dpath, dfile = os.path.split(data_file_path)

    datafile = ExperimentDataAccessUtility(dpath, dfile)

    # Create a table of trial_index, trial_start_time, trial_end_time for each trial by
    # getting the time of 'TRIAL_START' and 'TRIAL_END' experiment messages.
    trial_times = []
    trial_start_msgs = datafile.getEventTable('MessageEvent').where('text == b"TRIAL_START"')
    for mix, msg in enumerate(trial_start_msgs):
        trial_times.append([mix+1, msg['time'], 0])

    trial_end_msgs = datafile.getEventTable('MessageEvent').where('text == b"TRIAL_END"')
    for mix, msg in enumerate(trial_end_msgs):
        trial_times[mix][2] = msg['time']

    scount = 0

    # str prototype used to select samples within a trial time period
    sample_select_proto = "(time >= %f) & (time <= %f)"

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
            trial_samples = datafile.getEventTable(SAVE_EVENT_TYPE).where(sample_select_proto % (tstart, tstop))
            # Save a row for each eye sample within the trial period
            for sample in trial_samples:
                sample_data = [str(sample[c]) for c in SAVE_EVENT_FIELDS]
                output_file.write('\t'.join([str(tindex),]+sample_data))
                output_file.write('\n')
                scount += 1
                if scount % 100 == 0:
                    sys.stdout.write('.')

    print("\n\nWrote %d samples." % scount)
    datafile.close()