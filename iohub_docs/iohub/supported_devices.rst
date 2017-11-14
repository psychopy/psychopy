###################################
Operating System and Device Support
###################################
    

Operating System Support
#########################

ioHub is currently available for use on the following Operating Systems:

#. Windows XP SP3, 7, and 8
#. Linux 2.6 +
#. OSX 10.6 - 10.8.5 (OS X 10.9+ is not supported)

.. note:: Regardless of the Operating System being used, Python 2.6 or 2.7 
    **32-bit** is required. Even if a 64 bit OS is being used, install the 32 bit 
    version of Python and any package dependencies.

.. Important:: When running ioHub on macOS, ensure that "enable access for assistive
    devices" is selected in the macOS System Preferences and headed over to the
    Accessibility Pane. 

    
Current Device Support
#######################
    
The list of available ioHub device types is OS dependent. Unavilable devices
can (and will) be ported to all OS's when time permits. One exception to this
is the eye tracker (through the Common Eye Tracking Device Interface), where
OS support is determined by the underlying eye tracker hardware interface.

The current state (October, 2013) of device support for each OS is as follows:

===================== ============= =========== =============== 
Device Type           Windows       Linux       Mac OS X
===================== ============= =========== =============== 
Analog Input          Yes           Yes         Yes
Display               Yes           Yes         Yes
Eye Tracker           Yes           H/W Dep.    H/W Dep.
Experiment*           Yes           Yes         Yes
Event Pub-Sub*        Yes           Yes         Yes
GamePad               Yes (XInput)  No          No
Keyboard              Yes           Yes         Yes
Mouse                 Yes           Yes         Yes
Elo Touch Screen      Yes           Yes         Yes
Teensy 3.x / ioSync   Yes           Yes         Yes
===================== ============= =========== =============== 

_Devices marked with a '*' are __Software Virtual__ Devices with no corresponding
device hardware required._ 

If there is a device you think would be useful to add support for in the ioHub,
please let us know as it will help with development prioritization, 
and please consider helping with the implementation by contributing some time to the
project.


