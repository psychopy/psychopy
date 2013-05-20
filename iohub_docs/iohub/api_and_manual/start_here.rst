####################################
ioHub API Manual and Specification
####################################

We believe ioHub users will benefit from big picture understanding of the ioHub Event Monitoring Framework
along with descriptions of implemented functions and classes. The documentation within the API Manual describes how to 
maximze full functionality of the ioHub Event Monitoring Framework, from an overview of
ioHub at the process level, to the ioHub Event Model, to data storage and utility
classes, and finally to full integration of ioHub with PsychoPy. 

This User Manual does not cover *back-end* related API's that
are only of importance to a developer working on the ioHub 
source code, or creating a new Device class or Common Eye Tracker
Implementation.

**The ioHub Event Framework can be broken down into four areas based on the functionality provided.**
   
.. toctree::
    :maxdepth: 3

    * Overview of the ioHub Process <iohub_process/iohub_process>
    * Devices and DeviceEvents <devices>
    * ioHub DataStore <datastore/iodatastore_api>
    * PsychoPy Coder *Extra's* API <utilities>
