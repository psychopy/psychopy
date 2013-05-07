# -*- coding: utf-8 -*-
"""
NOTE: New example, not commented yet and may not be stable. It will **not** 
damage any DataStore file.
-------------------------------------------------------------------------------

IMPORTANT:
===========
    
This DataStore reading example REQUIRES that the experiment used the ExperimentVariableProvider
class to read in trial conditions and condition values for the experiment, as well as
saving any defined dependent variables using the ExperimentVariableProvider as well.
If your experiment events.hdf5 file does not contain the data from the 
ExperimentVariableProvider saved to it, this example will be of no use. ;) Don't worry
though, more examples releated to DataStore file reading coming. 

---

Script for reading an ioHub DataStore file and saving the session metadata and 
trial condition variables together in a tab delimited file.

Run this script to start, and a file chooser will be displayed to let you pick
which DataStore file you wish to process.

The output file (events.xls, really just tab delimited) will be saved in the 
same directory s the selected hdf5 file.

 
@author: Sol
"""

import sys,os

from psychopy import iohub
from iohub.datastore.util import ExperimentDataAccessUtility
from iohub.util import FileDialog

def chooseDataFile():
    """
    Shows a FileDialog and lets you select a .hdf5 file to open for processing.
    """
    script_dir=iohub.util.module_directory(chooseDataFile)
    
    fdlg=iohub.util.FileDialog(message="Select a ioHub DataStore Events File", 
                    defaultDir=script_dir,fileTypes=FileDialog.IODATA_FILES,display_index=0)
                    
    status,filePathList=fdlg.show()
    
    if status != FileDialog.OK_RESULT:
        print " Data File Selection Cancelled. Exiting..."
        sys.exit(0)
            
    return filePathList[0]
    
def writeOutputFileHeader(output_file, session_metadata_columns,session_uservar_columns,condition_variable_names):
    """
    Writes the header line at the top of the output file. Session metadata columns
    are first, followed by any user_variables defined for the session dialog,
    followed by all the trial condition variables.
    
    Session data is associated with each trial variable row using the session_id field.
    """
    allcols=session_metadata_columns+session_uservar_columns+condition_variable_names
    output_file.write('\t'.join(allcols))
    output_file.write('\n')

def writeDataRow(output_file,session_info,session_uservar_names,cvdata):
    """
    Save a row of data to the output file, in tab delimited format. See comment
    for writeOutputFileHeader function for order of saved columns.
    """
    session_data=[str(i) for i in session_info[:-1]]
    condition_variable_data=[str(i) for i in cvdata]
    session_user_data=[]
    for sud_name in session_uservar_names:
        session_user_data.append(session_info.user_variables[sud_name])

    all_data= session_data+session_user_data+condition_variable_data
    output_file.write('\t'.join(all_data))
    output_file.write('\n')
    
#
## Main Script Start
#

if __name__ == '__main__':
    # Some variables to hold the lists of different column names.
    session_metadata_columns=None
    session_uservar_columns=None
    condition_variable_names=None
    
    # A lookup dict with keys being session_id and values being the 
    # session meta data object for that id.
    sesion_meta_data_dict=dict()
    
    # Select the hdf5 file to process.
    data_file_path= chooseDataFile()  
    dpath,dfile=os.path.split(data_file_path)

    print 'Loading data from :',data_file_path
    # Create an instance of the ExperimentDataAccessUtility class
    # for the selected DataStore file.
    dataAccessUtil=ExperimentDataAccessUtility(dpath,dfile, experimentCode=None,sessionCodes=[])
    
    print 'Creating Output File Header....'
    # Read the session metadata tables for all sessions saved to the file.
    session_metadata=dataAccessUtil.getSessionMetaData()
    if len(session_metadata):
        if session_metadata_columns is None:
            session_metadata_columns = list(session_metadata[0]._fields[:-1] )
            session_uservar_columns=list(session_metadata[0].user_variables.keys())
            for s in session_metadata:
               sesion_meta_data_dict[s.session_id]=s
    
    # Get the column names for the trial variable condition table saved for the 
    # experiment.
    condition_variable_names=dataAccessUtil.getConditionVariableNames()
        
    # Get the actual data from the trial variable condition table saved for the 
    # experiment.
    condition_variable_data=dataAccessUtil.getConditionVariables()

    # Open a file to save the ouput to
    with open("results.xls",'w') as output_file:
        
        # write header
        writeOutputFileHeader(output_file,session_metadata_columns,
                              session_uservar_columns,condition_variable_names)
        print 'Writing Data ',
        #For each line / row in the trial variable table, save out the data.
        for cvdata in condition_variable_data:
            writeDataRow(output_file,sesion_meta_data_dict[cvdata.session_id],
                         session_uservar_columns,cvdata)
            print '.',
    
    # Be sure to close the ExperimentDataAccessUtility object; 
    # that closes the hdf5 file too.
    dataAccessUtil.close()
    print
    print 'Output Complete. results.xls will be in the same directory as the hdf5.' 