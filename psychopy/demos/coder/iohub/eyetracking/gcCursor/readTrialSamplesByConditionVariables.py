#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example of reading MONOCULAR_EYE_SAMPLE's from a hdf5 file, saving to a tab delimited text file.
The condition variables table is used to split samples into trial groupings,
saving condition variable columns with each eye sample.

This example can process hdf5 files saved by running the gcCursor demo.
"""
import sys, os
from psychopy import core
import psychopy.iohub
from psychopy.iohub.constants import EventConstants
from psychopy.iohub.datastore.util import displayDataFileSelectionDialog, ExperimentDataAccessUtility

SAVE_EVENT_TYPE = EventConstants.MONOCULAR_EYE_SAMPLE
SAVE_EVENT_FIELDS = ['time', 'gaze_x', 'gaze_y', 'pupil_measure1', 'status']


def getTime():
    return core.getTime()


if __name__ == '__main__':
    # Select the hdf5 file to process.
    data_file_path = displayDataFileSelectionDialog(psychopy.iohub.module_directory(getTime))
    if data_file_path is None:
        print("File Selection Cancelled, exiting...")
        sys.exit(0)
    data_file_path = data_file_path[0]
    dpath, dfile = os.path.split(data_file_path)

    datafile = ExperimentDataAccessUtility(dpath, dfile)

    samples_by_trial = datafile.getEventAttributeValues(SAVE_EVENT_TYPE, SAVE_EVENT_FIELDS,
                                                        startConditions={'time': ('>=', '@TRIAL_START@')},
                                                        endConditions={'time': ('<=', '@TRIAL_END@')})

    scount = 0

    # Open a file to save the tab delimited output to.
    #
    output_file_name = "%s.txt" % (dfile[:-5])
    with open(output_file_name, 'w') as output_file:
        print('Writing Data to %s:\n' % (output_file_name))
        column_names = samples_by_trial[0].condition_set._fields[2:] + samples_by_trial[0]._fields[:-2]
        output_file.write('\t'.join(column_names))
        output_file.write('\n')

        for trial_data in samples_by_trial:
            cv_fields = [str(cv) for cv in trial_data.condition_set[2:]]
            scount += len(trial_data.time)
            for six, sample_time in enumerate(trial_data.time):
                sample_data = [str(sample_time), str(trial_data.gaze_x[six]), str(trial_data.gaze_y[six]),
                               str(trial_data.pupil_measure1[six]), str(trial_data.status[six])]
                output_file.write('\t'.join(cv_fields + sample_data))
                output_file.write('\n')

                if six % 100 == 0:
                    sys.stdout.write('.')

    print("\n\nWrote %d samples." % scount)
    datafile.close()
