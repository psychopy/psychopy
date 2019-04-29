.. _iohub_eyetracker:

########################################
ioHub Common Eye Tracker Interface
########################################

The iohub commmon eye tracker interface provides a consistent way to configure
and collected data from several different eye tracker manufacturers,
including GazePoint, SR Research, and Tobii.

.. Eye Tracker Status::

    Porting of the iohub eye tracker device interfaces to PsychoPy 3 / Python 3
    is ongoing. Thank you for your patience. Please report any issues you find; 
    reporting and helping to test fixes for a specific eye tracker goes a long
    way in helping to keep eye tracker functionality up to date.
    
Supported Eye Trackers
######################

The following eye trackers are currently supported by iohub.

.. toctree::
    :maxdepth: 2
    
    GazePoint<eyetracker_interface/GazePoint_Implementation_Notes>
    SR Research<eyetracker_interface/SR_Research_Implementation_Notes>
    Tobii<eyetracker_interface/Tobii_Implementation_Notes>