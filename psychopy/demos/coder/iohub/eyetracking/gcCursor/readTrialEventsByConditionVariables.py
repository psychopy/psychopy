#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example of reading events from an iohub hdf5 file, saving to a tab delimited text file.
The condition variables table is used to split samples into trial groupings,
saving condition variable columns with each event.

SAVE_EVENT_TYPE and SAVE_EVENT_FIELDS specify the event type, and which event fields, are saved.

This example can process hdf5 files saved by running the gcCursor demo.
"""
import sys
import os
from psychopy.iohub.constants import EventConstants
from psychopy.iohub.datastore.util import displayDataFileSelectionDialog
from psychopy.iohub.datastore.util import ExperimentDataAccessUtility

SAVE_EVENT_TYPE = EventConstants.MONOCULAR_EYE_SAMPLE
SAVE_EVENT_FIELDS = ['time', 'gaze_x', 'gaze_y', 'pupil_measure1', 'status']

#SAVE_EVENT_TYPE = EventConstants.BINOCULAR_EYE_SAMPLE
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

    events_by_trial = datafile.getEventAttributeValues(SAVE_EVENT_TYPE, SAVE_EVENT_FIELDS,
                                                       startConditions={'time': ('>=', '@TRIAL_START@')},
                                                       endConditions={'time': ('<=', '@TRIAL_END@')})

    ecount = 0

    # Open a file to save the tab delimited output to.
    #
    output_file_name = "%s.txt" % (dfile[:-5])
    with open(output_file_name, 'w') as output_file:
        print('Writing Data to %s:\n' % (output_file_name))
        column_names = events_by_trial[0].condition_set._fields[2:] + events_by_trial[0]._fields[:-2]
        output_file.write('\t'.join(column_names))
        output_file.write('\n')

        for trial_data in events_by_trial:
            cv_fields = [str(cv) for cv in trial_data.condition_set[2:]]
            # Convert trial_data namedtuple to list of arrays.
            # len(trial_data) == len(SAVE_EVENT_FIELDS)
            trial_data = trial_data[:-2]
            for eix in range(len(trial_data[0])):
                # Step through each event, saving condition variable and event fields
                ecount += 1
                event_data = [str(c[eix]) for c in trial_data]
                output_file.write('\t'.join(cv_fields + event_data))
                output_file.write('\n')

                if eix % 100 == 0:
                    sys.stdout.write('.')

    print("\n\nWrote %d events." % ecount)
    datafile.close()
