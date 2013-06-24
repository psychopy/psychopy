The ioHub Process
##################

This section of documentation will help to familarize your with the basic usage of the
ioHub Event Framework. 

How to create an ioHub Process is reviewed, including two different approaches for 
doing so:
    
* The psychopy.iohub.launchHubProcess function provides a quick way to get the ioHub Process up and running for simple device configurations. 
* The ioHubExperimentRuntime Class includes built-in support for experiment, session, and ioHub Device level configuartion using two external property files,  providing a framework where device configuration is cleanly seperated from the python code defining experiment logic. This is benifical since the ioHub Event Framework provides a common propgramming interface to devices,  even when multiple manufacturer's of a device type are supported. This promotes the reuse of experiment scripts across different device makes and models, by simply changing the device configuration files.

Finally, a review of the lifecycle of an ioHub event is given, and some code examples
for accessing event within your experiment script are given. 
 
.. toctree::
    :maxdepth: 3
    
    * Getting Connected <getting_connected>
    * The launchHubProcess Function <launchHubServer>
    * The ioHubExperimentRuntime Class <ioHubExperimentRuntime>
    * Experiment and Device Configuration <config_files>
    * Using ioHub Devices and Events <iohub_event_model>
