####################
The ioHub DataStore
####################

The ioHub DataStore contains the fucntionality responsible for saving Device Events
to the HDF5 file format used by the ioHub Process. The DataStore also includes
a simple API to access the events and experiment information saved to it, but using
the ExperimentDataAccessUtility class.

Advantages of using the ioHub DataStore are:

* Save all Device events received by the ioHub Process; regardless of whether the PsychoPy Process and your experiment script needs access to them in realtime. This saves on the number of events that need to be transfered to, and reduces filtering and processing time required by,  the PsychoPy Process.
* Send Experiment Message Events to the ioHub DataStore during your experiment, providing the dataStore file with necessary / important experiment events for use when performing data analysis.
* The HDF5 file format and access API is well recognized for it's superior ability at providing access to very large datasets very quickly and with very good memory management. 
* Two open source, free to use, HDF5 file viewers are available and work with the files saved by the DataStore.
* HDF5 files can be read directly within Matlab.
* When using the ExperimentDataAccessUtility class, or the pytables HDF5 Python module directly, events are returned as numpy recarrays, allowing very fast, direct use of the data within packages like MatPlotLib and SciPy, or with the numpy module's processing capabilities as well.


Data File Viewers
###################

Both of these program's are very useful for openning the HDF5 files saved by 
the ioHub DataStore and viewing the data saved quickly and efficiently. 
Both programs are cross-platform, open source, and free to use.

* `ViTables <http://vitables.org/>`_ : Written in Python using the PyQt GUI package. 
* `HDFView <http://www.hdfgroup.org/hdf-java-html/hdfview/>`_ : Written in Java, maybe a bit more up to date given it is written and maintained by the HDFGroup. 

Data File Access
##################

ioHub DataStore data files are standard HDF5 formatted files with an experiment
and session metadata, as well as device and experiment event structure specified. 

Therefore any HDF5 API can be used to read the files saved. 
For Python, these include:

* `pytables <http://pytables.org/>`_ 
* `h5py <http://h5py.org/>`_

If you *need* to use Matlab, the files can also be read natively by using `information found here <http://www.mathworks.com/help/matlab/hdf5-files.html>`_.

You can also use the ExperimentDataAccessUtility class prodied as part of the ioHub DataStore 
to access the files based on experiment and session code(s), and retrieve 
event information based on ioHub Event Types.

ioHub DataStore File Structure 
################################

HDF5 Files saved by the ioHub DataStore all use a common structure for the data
saved.

/(RootGroup) 'ioHub DataStore - Experiment Data File.'
    /class_table_mapping (Table) 'Mapping of ioHub DeviceEvent Classes to ioHub DataStore Tables.'
    /data_collection (Group) 'Data Collected using the ioHub Event Framework.'
        /data_collection/experiment_meta_data (Table) 'Information About Experiments Saved to This ioHub DataStore File.'
        /data_collection/session_meta_data (Table) 'Information About Sessions Saved to This ioHub DataStore File.'
        /data_collection/condition_variables (Group) 'Tables created to Hold Experiment DV and IV's Values Saved During an Experiment Session.'
        /data_collection/events (Group) 'All Events that were Saved During Experiment Sessions.'
            /data_collection/events/analog_input (Group) 'AnalogInput Device Events.'
            /data_collection/events/experiment (Group) 'Experiment Device Events.'
                /data_collection/events/experiment/LogEvent (Table) 'LogEvent Data.'
                /data_collection/events/experiment/MessageEvent (Table) 'MessageEvent Data.'
            /data_collection/events/eyetracker (Group) 'EyeTracker Device Events.'
            /data_collection/events/gamepad (Group) 'GamePad Device Events.'
            /data_collection/events/keyboard (Group) 'Keyboard Device Events.'
                /data_collection/events/keyboard/KeyboardCharEvent (Table) 'KeyboardCharEvent Data.'
                /data_collection/events/keyboard/KeyboardKeyEvent (Table(114,)) 'KeyboardKeyEvent Data.'
            /data_collection/events/mouse (Group) 'Mouse Device Events.'
                /data_collection/events/mouse/MouseInputEvent (Table(0,)) 'MouseInputEvent Data.'


The ExperimentDataAccessUtility Class
#######################################

**Intro to be Added.** 
 

.. autoclass:: psychopy.iohub.datastore.util.ExperimentDataAccessUtility
	

Examples
#########

**Intro to be added.** 