#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script demonstrates how to load a ioHub DataStore HDF5 file, read the
session variable data collected via the Experiment Session Variable Dialog
at the start of each experiment run ( if you did so, otherwise that is ignored)
and combine it with columns from a Device Event Table, saving the output as a
tab delimited file.

@author: Sol
"""

from __future__ import absolute_import, division, print_function

from builtins import str
import sys,os
import psychopy
from psychopy.core import getTime
import psychopy.iohub
if psychopy.iohub._DATA_STORE_AVAILABLE is False:
    raise ImportError("DataStore module could not be imported. (Likely that pyTables hdf5dll could not be found). Exiting demo...")
    sys.exit(1)

from psychopy.iohub.datastore.util import displayDataFileSelectionDialog,displayEventTableSelectionDialog, ExperimentDataAccessUtility

def writeOutputFileHeader(output_file, session_metadata_columns,log_entry_names):
    """
    Writes the header line at the top of the Log file.
    Currently uses format:

    session_meta_data_cols [session_user_variable_columns] [event_table_cols][3:]

    Session data is associated with each log entry row using the session_id field.
    """
    allcols=session_metadata_columns+log_entry_names+session_uservar_columns
    output_file.write('\t'.join(allcols))
    output_file.write('\n')

def writeDataRow(output_file,session_info,session_uservar_names,event_data):
    """
    Save a row of data to the output file, in tab delimited format. See comment
    for writeOutputFileHeader function for order of saved columns.
    """
    session_data=[str(i) for i in session_info[:-1]]
    session_user_data=[session_info.user_variables[sud_name] for sud_name in session_uservar_names]
    all_data= session_data+session_user_data+[str(e) for e in event_data]+session_user_data
    output_file.write('\t'.join(all_data))
    output_file.write('\n')

if __name__ == '__main__':
    # Select the hdf5 file to process.
    data_file_path= displayDataFileSelectionDialog(psychopy.iohub.module_directory(writeOutputFileHeader))
    if data_file_path is None:
        print("File Selection Cancelled, exiting...")
        sys.exit(0)
    dpath,dfile=os.path.split(data_file_path)

    # Lets time how long processing takes
    #
    start_time=getTime()

    # Create an instance of the ExperimentDataAccessUtility class
    # for the selected DataStore file. This allows us to access data
    # in the file based on Device Event names and attributes, as well
    # as access the experiment session metadata saved with each session run.
    dataAccessUtil=ExperimentDataAccessUtility(dpath,dfile, experimentCode=None,sessionCodes=[])

    # Get a dict of all event types -> DataStore table info
    #   for the selected DataStore file.
    eventTableMappings=dataAccessUtil.getEventMappingInformation()

    # Get event tables that have data...
    #
    events_with_data=dataAccessUtil.getEventsByType()

    duration=getTime()-start_time

    # Select which event table to output by displaying a list of
    #   Event Class Names that have data available to the user...
    event_class_selection=displayEventTableSelectionDialog("Select Event Type to Save", "Event Type:",
                [eventTableMappings[event_id].class_name for event_id in list(events_with_data.keys())])
    if event_class_selection is None:
        print("Event table Selection Cancelled, exiting...")
        dataAccessUtil.close()
        sys.exit(0)

    # restart processing time calculation...
    #
    start_time=getTime()

    # Lookup the correct event iterator fiven the event class name selected.
    #
    event_iterator_for_output=None
    for event_id, mapping_info in eventTableMappings.items():
        if mapping_info.class_name==event_class_selection:
            event_iterator_for_output=events_with_data[event_id]
            break

    # Read the session metadata table for all sessions saved to the file.
    #
    session_metadata=dataAccessUtil.getSessionMetaData()

    sesion_meta_data_dict=dict()

    # Create a session_id -> session metadata mapping for use during
    # file writing.
    #
    if len(session_metadata):
        session_metadata_columns = list(session_metadata[0]._fields[:-1] )
        session_uservar_columns=list(session_metadata[0].user_variables.keys())
        for s in session_metadata:
           sesion_meta_data_dict[s.session_id]=s

    # Open a file to save the tab delimited output to.
    #
    log_file_name="%s.%s.txt"%(dfile[:-5],event_class_selection)
    with open(log_file_name,'w') as output_file:

        # write column header
        #
        writeOutputFileHeader(output_file,session_metadata_columns,
                              dataAccessUtil.getEventTable(event_class_selection).cols._v_colnames[3:])

        print('Writing Data to %s:\n'%(log_file_name))
        for i,event in enumerate(event_iterator_for_output):
            # write out each row of the event data with session
            # data as prepended columns.....
            #
            writeDataRow(output_file,sesion_meta_data_dict[event['session_id']],
                         session_uservar_columns,event[:][3:])

            if i%100==0:
                sys.stdout.write('.')

    duration=duration+(getTime()-start_time)
    print()
    print('\nOutput Complete. %d Events Saved to %s in %.3f seconds (%.2f events/seconds).\n'%(i,log_file_name,duration,i/duration))
    print('%s will be in the same directory as the selected .hdf5 file'%(log_file_name))
