# -*- coding: utf-8 -*-
"""
ioHub
.. file: ioHub/examples/dataStore/saveDataStoreLog.py

-------------------------------------------------------------------------------

saveDataStoreLog
+++++++++++++++++

Overview:
---------

This script demonstrates how to load a ioDataStrore hdf5 file, read the 
session variable data collected via the Experiment Session Variable Dialog 
at the start of each experiment run ( if you did so, otherwise that is ignored)
and combine it with columns from a Device Event Table, 
saving the output as a tab delimited file.close

This example saves the experiment.LogEvent entries from an experiment, however the
script could easily be modified to save events for any Device Event type.  

To create an ioDataStoreFile that has lots of LogEvents, you can run the 
iohub/examples/psychopyIntegrationTest example by running the run.py inwith that
folder. The saved .hdf5 file can be used as the file selected to process by 
this script.

To Run:
-------

1. Ensure you have followed the ioHub installation instructions 
   in the ioHub documentation.
2. Open a command prompt to the directory containing this file.
3. Start the test program by running:
   python.exe saveDataStoreLog.py


@author: Sol
"""
import sys,os
from psychopy import iohub
from iohub.datastore.util import ExperimentDataAccessUtility
from iohub.util import FileDialog
from iohub import getTime

# Get the logging level strings and level ID associations, so we can 
# always save the string version to the output file.
_log_levels = iohub.devices.experiment.LogEvent._levelNames

#
## Functions used by the __main__ script:
#

def chooseDataFile():
    """
    Shows a FileDialog and lets you select a .hdf5 file to open for processing.
    """
    script_dir=iohub.util.module_directory(chooseDataFile)
    
    fdlg=FileDialog(message="Select a ioHub DataStore Events File", 
                    defaultDir=script_dir,fileTypes=FileDialog.IODATA_FILES,display_index=0)
                    
    status,filePathList=fdlg.show()
    
    if status != FileDialog.OK_RESULT:
        print " Data File Selection Cancelled. Exiting..."
        sys.exit(0)
            
    return filePathList[0]
    
def writeOutputFileHeader(output_file, session_metadata_columns,log_entry_names):
    """
    Writes the header line at the top of the Log file.
    
    Currently uses format:
        
    experiment_id  session_id  session_name  log_time  log_level  log_text  [session_user_variable_columns]
    
    Session data is associated with each log entry row using the session_id field.
    """
    allcols=session_metadata_columns+log_entry_names+session_uservar_columns
    output_file.write('\t'.join(allcols))
    output_file.write('\n')

def writeDataRow(output_file,session_info,session_uservar_names,log_entry_data):
    """
    Save a row of data to the output file, in tab delimited format. See comment
    for writeOutputFileHeader function for order of saved columns.
    """
    time,log_level,text=log_entry_data
    session_data=[str(i) for i in session_info[:-1]]
    session_user_data=[]
    for sud_name in session_uservar_names:
        session_user_data.append(session_info.user_variables[sud_name])

    all_data= session_data+log_entry_data+session_user_data
    output_file.write('\t'.join(all_data))
    output_file.write('\n')
#
## Main Script Start
#

if __name__ == '__main__':
    
    # Some variables to hold the lists of different column names.
    session_metadata_columns=None
    session_uservar_columns=None
    
    # A lookup dict with keys being session_id and values being the 
    # session meta data object for that id.
    sesion_meta_data_dict=dict()
    
    # Select the hdf5 file to process.
    data_file_path= chooseDataFile()  
    dpath,dfile=os.path.split(data_file_path)
    
    start_time=getTime()
    print 'Loading data from :',data_file_path,'\n'

    # Create an instance of the ExperimentDataAccessUtility class
    # for the selected DataStore file. This allows us to access data
    # in the file based on Device Event names and attributes, as well
    # as access the experiment session metadata saved with each session run.
    dataAccessUtil=ExperimentDataAccessUtility(dpath,dfile, experimentCode=None,sessionCodes=[])
    
    # Read the session metadata table for all sessions saved to the file.
    session_metadata=dataAccessUtil.getSessionMetaData()
    if len(session_metadata):
        session_metadata_columns = list(session_metadata[0]._fields[:-1] )
        session_uservar_columns=list(session_metadata[0].user_variables.keys())
        for s in session_metadata:
           sesion_meta_data_dict[s.session_id]=s
    
    log_entries=dataAccessUtil.getEventIterator('LogEvent')
    
    # Open a file to save the tab delimited ouput to
    log_file_name="%s.log"%(dfile[:-5])
    with open(log_file_name,'w') as output_file:
        
        # write column header
        writeOutputFileHeader(output_file,session_metadata_columns,
                              ['log_time','log_level','log_text'])

        print 'Writing Data:\n',
        #For each event in the event table, save out the data.
        i=0        
        for le in log_entries:
            # Only want to save some of the event attributes to the output file. 
            # This is were they are selected and read.
            log_entry= ["%.6f"%(le['time']),_log_levels[le['log_level']],le['text']]
            
            writeDataRow(output_file,sesion_meta_data_dict[le['session_id']],
                         session_uservar_columns,log_entry)

            if i%100==0:
                print '.',
            i+=1

    output_file.close()
    
    # Be sure to close the ExperimentDataAccessUtility object; 
    # that closes the hdf5 file too.
    dataAccessUtil.close()
    end_time=getTime()
    task_duration=end_time-start_time
    print
    print '\nOutput Complete. %d Events Saved to %s in %.3f seconds (%.2f events/seconds).\n'%(i,log_file_name,task_duration,i/task_duration)
    print '%s will be in the same directory as the selected .hdf5 file'%(log_file_name)