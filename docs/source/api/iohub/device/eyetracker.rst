.. _iohub_eyetracker:

########################################
ioHub Common Eye Tracker Interface
########################################

The iohub commmon eye tracker interface provides a consistent way to configure,
calibrate, and collected data from several different eye tracker manufacturers,
including GazePoint, SR Research, and Tobii.

.. Eye Tracker Status::

    Porting of the iohub eye tracker device interfaces to PsychoPy 3 / Python 3
    is ongoing. Thank you for your patience. Please report any issues you find; 
    reporting and helping to test fixes for a specific eye tracker goes a long
    way in helping to keep eye tracker functionality up to date.
    
Eye Tracking Hardware Implementations
########################################

The following links provide details on the Common Eye Tracker Interface
implementation for each currently supported eye tracking system. 
It is very important to review the documentation for your eye tracker, both for
correct configuration and event access during the experiment.

Eye Tracker implementations are listed in alphabetical order.

.. toctree::
    :maxdepth: 2
    
    GazePoint<eyetracker_interface/GazePoint_Implementation_Notes>
    SR Research<eyetracker_interface/SR_Research_Implementation_Notes>
    Tobii<eyetracker_interface/Tobii_Implementation_Notes>
    
EyeTracker Device Configuration Settings
###########################################

While all supported eye trackers have the same user-level methods through the
Common Eye Tracker Interface, differences between eye trackers are reflected 
in the different configuration settings based on the capabilities and design
of individual eye tracker models. Please see the implementation page for your
Eye Tracker hardware for configuration specifics. These configurations settings
are specified in the iohub_config.yaml or passed to launchHubServer().