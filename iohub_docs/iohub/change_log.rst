#################
ioHub Change Log
#################


Release 0.7
#############

This release of ioHub is **dedicated to Pierce Edmiston**, who provided a huge amount of help giving documentation feedback and general suggestions, as well as doing a lot of Windows tests of all forms and types. **Thank you Pierce, 0.7 would not have made it without your help!**

#. Created a NumPyRingBuffer class, useful for cases where you want a moving window of the last X previous data points and want to be able to use numpy.array.XXXX methods with the current data in the RingBuffer / Window. Implemented used a zero array copy algorithm when items are added to the buffer, event when full.

#. Implemented psychopy integration for the default time base used in PsychoPy and in ioHub so they use the same time base when running together.

#. Implemented a LogEvent type in the Experiment Device, which is used by ioHub to integrate with the psychopy.logging module.

#. Created first version of the LC Technologies EyeGaze Common Eye Tracker Interface. Tested with a monocular head fixed version of the EyeGaze, single PC mode only. No Binocular data support is in place yet.

#. Tobii Common Eye Tracker Interface has been updated to support

	* 3, 5 and 9 point calibrations. 
	* Target position order can also be randomized. 
	* The calibration auto_pace and pacing_speed parameters have also been implemented.

#. Re-wrote the SMI Common Eye Tracker Interface from scratch. Tested with an SMI iViewX-M tracker. tested in single PC mode only at this point.

#. Updated EyeLink Common Eye Tracker Interface: all listed config options should now actually work. Tested on a EyeLink 1000 Desktop system that has monocular support only.

#. Created the first release for the Mac OS X port.

#. Implemented Unicode support for keyboard events. Unicode support for other text attributes of events should be checked and fixed when possible. 

#. Tested and fixed several issues with the Linux port. Unicode support on Linux is still flakey I would say.

#. Created the first version of the ioHub documentation using Sphinx.

#. Refactored project layout to it better meets Python Package standards.

#. Moved around some classes and functions as part of the Sphinx documentation process. Most of this was within the iohub.util folder.
 
 
Release 0.6rc1
##############

#. Refactored the Display Device class towards the goal of, well making more of it being easier to integrate *properly* with PsychoPy.

#. Added proper conversion logic allowing mapping of any Display Coordinate Space to the Display Screen's Pixel Space. Only 'pix' coord type is still supported, but adding other coord type support will be quite easy now. 

#. Did a major overhaul of the EyeTrackerDevice interface:

    #. Simplified the interface definition, removing several methods that were clearly going to be almost never implemented.
    #. Removed args, kwargs parameter passing to interface methods and replaced with clearly defined parameter expectations.
    #. Improved the documentation of each interface method, outlining expected behaviour of each and the valid return object types.
    #. Interface supported the device configuration verification framework put in place for all ioHub Devices.
 
#. Added a FullScreenWindow class to iohub.util, greatly simplifying the creation of a PsychoPy Window with the expected ioHub Display settings.

#. Added support for devices running on the ioHub Server to be able to return exceptions that are then raised by the Experiment Process. (experimental and buggy)

#. Added several new attributes to the Device class, mainly related to being able to optionally specify much more information about the actual device being used (manufacturer, make, model, serial number, etc).

#. Created a framework that allows the definition of what the 'valid' configuration options and value types and ranges are for each device type, and device model specific implementations where appropriate. (BETA, usability of how errors found are reported to user should be improved, right now it just dumps the list of configuration issues to stderr.)   

#. Added ability to lock the Mouse device to a Display region on a multi-monitor computer.

#. Added a 'display_id' field to the Mouse Device's events, so the display device the mouse was on is known, and therefore how the mouse pixel position information reported in an event can be interpreted properly.

#. Changed the MessageEvent.msg_offset attribute to be type float32 so offsets can be represented in the standard sec.msec-usec format.

#. LabJack implementation of AnalogInput Device now uses a fixed fequency streaming mode for sample collection instead of a polled channel value method.

#. Removed unused 'os_device_code' attribute from device classes.

#. Changed the MouseInputEvent 'windowID' attribute to 'window_id'; to make it consistent with the KeyboardInputEvent attribute of the same meaning.

#. Updated the example scripts folder by moving all eye tracking related examples to a subdirectory.

#. Created a 'headlessEventMonitoring' example, console based, showing how ioHub can be used to get events from supported devices even when no application   graphics environment is in use.


