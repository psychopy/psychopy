#######################
Tobii EyeTracker Class
#######################

**Platforms:** 

* Windows (tested)
* Linux (not tested yet, but should be possible given Tobii python package is available for Linux)
    
**Supported Models:**

* Tobii X120
* Tobii X60 
* Tobii T120 (tested on this model to date)
* Tobii T60
* Tobii T60 XL
* Tobii TX300
* Tobii IS-1
    
.. note::    
    The Common Eye Tracker Interface for Tobii can be used with Python 2.6 if the Tobii Analytics SDK 3.0 RC 1 32 bit package. To use Python 2.7, the 
    Tobii Analytics SDK 3.0 (released May, 2013) 32-bit version must be installed and used.

.. autoclass:: psychopy.iohub.devices.eyetracker.hw.tobii.EyeTracker
    :exclude-members: ALL_EVENT_CLASSES, CLASS_ATTRIBUTE_NAMES, DEVICE_BUFFER_LENGTH_INDEX, DEVICE_CLASS_NAME_INDEX, DEVICE_MAX_ATTRIBUTE_INDEX, DEVICE_TIMEBASE_TO_SEC, DEVICE_TYPE_ID, DEVICE_TYPE_ID_INDEX, DEVICE_TYPE_STRING, DEVICE_USER_LABEL_INDEX, NUMPY_DTYPE, e, DEVICE_FIRMWARE_VERSION_INDEX, DEVICE_HARDWARE_VERSION_INDEX,DEVICE_MANUFACTURER_NAME_INDEX,DEVICE_MODEL_NAME_INDEX, DEVICE_MODEL_NUMBER_INDEX, DEVICE_NUMBER_INDEX, DEVICE_SERIAL_NUMBER_INDEX, DEVICE_SOFTWARE_VERSION_INDEX, EVENT_CLASS_NAMES
    :member-order: bysource

Installing other Necessary Tobii Software
##################################################

The ioHub Common Eye Tracker Interface implementation for Tobii uses the Python 2.6
package that is provided by Tobii as part of their 32-bit Tobii Analytics SDK 3.0 RC 1 package; 
or the  Python 2.7 package that is provided by Tobii as part of their 32-bit Tobii Analytics SDK 3.0
(released May, 2013).

Please ensure that the Following files and folder are in your Python Path and system PATH.
This is often most easily done by copying these file and folder to your Python 2.6
site-packages folder, located at something like C:\Python26\Lib\site-packages.

Python 2.6 Support
==================

Required files / folder from the Tobii Analytics SDK 3.0 RC 1 package for use with Python 2.6:

    *  The directory named 'tobii' found in the Python files area of the 32-bit Tobii Analytics SDK 3.0 RC 1 package.
    *  tobiisdk.dll
    *  _tobiisdkpy26.pyd
    *  boost_python-vc90-mt-1_41.dll

Again, the one directory and 3 files listed above must be in a directory in your
Python 2.6 Python Path, as well as in your system PATH environment variable setting.
You do not need to change your system environment variables if you place these
four items in your Python 2.6 site-packages directory.

Python 2.7 Support
==================

Required files / folder from the Tobii Analytics SDK 3.0 package for use with Python 2.7:

    *  The directory named 'tobii' found in the Python27\Modules files area of the 32-bit Tobii Analytics SDK 3.0.
    *  tetio.dll
    *  _tetiopy27.pyd
    *  tetio_boost_python-vc90-mt-1_51.dll
    *  tetio_boost_python-vc90-mt-gd-1_51.dll

Again, the one directory and 4 files listed above must be in a directory in your
Python 2.7 Python Path, as well as in your system PATH environment variable setting.
You do not need to change your system environment variables if you place these
five items in your Python 2.7 site-packages directory.


Default Tobii EyeTracker Device Settings
############################################

.. literalinclude:: ../default_yaml_configs/default_tobii_eyetracker.yaml
    :language: yaml

Supported EyeTracker Device Event Types
########################################

The Tobii Analytics SDK 3.0 RC 1 provides real-time access to binocular sample data.
Therefore the BinocularEyeSample event type is supported when using a Tobii as 
the ioHub EyeTracker device. The following fields of the BinocularEyeSample event are 
supported:

    #. psychopy.iohub.devices.eyetracker.BinocularEyeSampleEvent:
        #. Attributes supported:
            #. experiment_id
            #. session_id
            #. event_id
            #. event_type
            #. logged_time
            #. device_time
            #. time
            #. delay
            #. confidence_interval
            #. left_gaze_x:             maps to Tobii eye sample field LeftGazePoint2D.x
            #. left_gaze_y:             maps to LeftGazePoint2D.y
            #. left_eye_cam_x:          maps to LeftEyePosition3DRelative.x
            #. left_eye_cam_y:          maps to LeftEyePosition3DRelative.y
            #. left_eye_cam_z:          maps to LeftEyePosition3DRelative.z
            #. left_pupil_measure_1:    maps to LeftPupil
            #. left_pupil_measure1_type: PUPIL_DIAMETER_MM
            #. right_gaze_x:            maps to Tobii eye sample field RightGazePoint2D.x
            #. right_gaze_y:            maps to RightGazePoint2D.y
            #. right_eye_cam_x:         maps to RightEyePosition3DRelative.x
            #. right_eye_cam_y:         maps to RightEyePosition3DRelative.y
            #. right_eye_cam_z:         maps to RightEyePosition3DRelative.z
            #. right_pupil_measure_1:   maps to RightPupil
            #. right_pupil_measure1_type: PUPIL_DIAMETER_MM
            #. status:                  both left and right eye validity codes are encoded as LeftValidity*10+RightValidity

General Considerations
#######################

**Last Updated:** May 5th, 2013

Known Issues:              
==============

None at this time.

Limitations:
==============

    #. There is no way to present the 'tracking status' graphics display that shows each eye location in the head box and status indications for distance validity and eye tracking stability.
    #. The current calibration procedure is not visually similar to the standard Tobii calibration graphics set. This should be added when time permits.

To Do / Wish List:
===================

    #. Add 'tracking status' graphics display.
    #. Show calibration results graphics after calibration.    
    #. Offer calibratio graphics mode that is more  "Tobii like".