"""
ioHub
ioHub Common Eye Tracker Interface
.. file: ioHub/devices/eyetracker/__init__.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com>
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

from ... import print2err, createErrorResult
from .. import Device,ioDeviceError
from ...constants import DeviceConstants,EyeTrackerConstants
import hw

#noinspection PyUnusedLocal,PyTypeChecker
class EyeTrackerDevice(Device):
    """
    The EyeTrackerDevice class is the main class for the common eye tracker 
    interface API built into ioHub.

    The common eye tracker interface class is implemented for different
    eye tracker models by creating a subclass of the EyeTrackerDevice class
    and implementing the common eye tracker API components that can be supported
    by the given eye tracking hardware. It is these sub classes of the
    EyeTrackerDevice that are used to define which implementation of the 
    common eye tracker interface is to be used during an experiment,
    based on which eye tracker hardware you plan on using.

    Not every eye tracker implementation of the Common Eye Tracker Interface
    will support all of the interface functionality, however a core set of minimum
    functionality is expected to be supported by all implementation. 
    
    Methods in the EyeTrackerDevice class are broken down into several categories
    within the EyeTracker class:

    #. Eye Tracker Initialization / State Setting.
    #. Ability to Define the Graphics Layer for the Eye Tracker to Use During Calibration / System Setup.
    #. Starting and Stopping of Data Recording.
    #. Sending Synchronization messages or codes to the Eye Tracker.
    #. Accessing Eye Tracker Data During Recording.
    #. Accessing the Eye Tracker Timebase.
    #. Synchronizing the ioHub time base with the Eye Tracker time base, so Eye Tracker events can be provided with local time stamps when that is appropriate.

    .. note:: 

        Only **one** instance of EyeTracker can be created within an experiment. Attempting to create > 1
        instance will raise an exception. To get the current instance of the EyeTracker you can call the
        class method EyeTracker.getInstance(); this is useful as it saves needing to pass an eyeTracker
        instance variable around your code.
    """

    # Used to hold the EyeTracker subclass instance to ensure only one instance of
    # a given eye tracker type is created. This is a current ioHub limitation, not the limitation of
    # all eye tracking hardware.
    _INSTANCE=None
    
    # the multiplier needed to convert device times to sec.msec times.
    DEVICE_TIMEBASE_TO_SEC=1.0

    # Used by pyEyeTrackerDevice implementations to store relationships between an eye
    # trackers command names supported for EyeTrackerDevice sendCommand method and
    # a private python function to call for that command. This allows an implementation
    # of the interface to expose functions that are not in the core EyeTrackerDevice spec
    # without have to use the EXT extension class.
    _COMMAND_TO_FUNCTION = {}

    DEVICE_TYPE_ID=DeviceConstants.EYETRACKER
    DEVICE_TYPE_STRING='EYETRACKER'
    __slots__=['_latest_sample','_latest_gaze_position', '_runtime_settings']

    def __init__(self,*args,**kwargs):
        if self.__class__._INSTANCE is not None:
            raise ioDeviceError(self,"EyeTracker object has already been created; "
                                                    "only one instance can exist. Delete existing "
                                                    "instance before recreating EyeTracker object.")
        else:
            self.__class__._INSTANCE=self
                
        Device.__init__(self,*args,**kwargs['dconfig'])

        # hold last received ioHub eye sample (in ordered array format) from tracker.
        self._latest_sample=EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED
    
        # holds the last gaze position read from the eye tracker as an x,y tuple. If binocular recording is
        # being performed, this is an average of the left and right gaze position x,y fields.
        self._latest_gaze_position=EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED                                        

        # stores the eye tracker runtime related configuration settings from the ioHub .yaml config file
        self._runtime_settings=kwargs['dconfig']['runtime_settings']                                          
    
        #TODO: Add support for message ID to Message text lookup table in ioDataStore
        # data table that can be used by ET systems that support sending int codes,
        # but not text to tracker at runtime for syncing.
        
    def trackerTime(self):
        """
        trackerTime returns the current time eye tracker reported by the 
        eye tracker device. The time base is implementation dependent. 
        
        Args:
            None
        
        Return:
            float: The eye tracker hardware's reported current time.
        """
        return EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED
   
    def trackerSec(self):
        """
        trackerSec takes the time received by the EyeTracker.trackerTime() method
        and returns the time in sec.usec-msec format.
        
        Args:
            None
        
        Return:
            float: The eye tracker hardware's reported current time in sec.msec-usec format.        
        """
        return EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED
        
   
    def setConnectionState(self,enable):
        """
        setConnectionState is used to connect ( setConnectionState(True) ) 
        or disable ( setConnectionState(False) ) the connection of the ioHub 
        to the eyetracker hardware.
        
        Note that a connection to the eye tracking hardware is automatically
        openned when the ioHub Server process is started. So there is no need to
        call this method at the start of your experiment. Doing so will have no
        effect on the connection state.
        
        When an eye tracker device is connected to the ioHub it is **not** also recording
        eye data and sending the data to the ioHub Server. To start actual eye data
        recording, use the setRecordingState(bool) or device type independent
        enableEventReporting(bool) methods to start and stop eye data recording.

        Args:
            enable (bool): True = enable the connection, False = disable the connection.

        Return:
            bool: indicates the current connection state to the eye tracking hardware.
            
        """
        return EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED
            
    def isConnected(self):
        """
        isConnected returns whether the EyeTrackerDevice is connected to the
        eye tracker hardware or not. An eye tracker muct be connected to the ioHub 
        for any of the Common Eye Tracker Interface functionality to work.
        
        Args:
            None
            
        Return:
            bool:  True = the eye tracking hardware is connected. False otherwise.
        """
        return EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED
            
    def sendCommand(self, key, value=None):
        """
        The sendCommand method allows arbitrary *commands* or *requests* to be
        issued to the eye tracker device. Valid values for the arguements of this 
        method are completely implementation specific, so please refer to the 
        eye tracker implentation page for the eye tracker being used for a list of 
        valid key and value combinations (if any). 
        
        In general, eye tracker implementations should **not** need to support 
        this method unless there is critical eye tracker functionality that is 
        not accessable using the other methods in the EyeTrackerDevice class.
        
        Args:
            key (str): the command or function name that should be run.
            value (object): the (optional) value associated with the key. 


        Return:
            object: the result of the command call
            int: EyeTrackerConstants.EYETRACKER_OK
            int: EyeTrackerConstants.EYETRACKER_ERROR
            int: EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED
        """

        return EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED
        
    def sendMessage(self,message_contents,time_offset=None):
        """
        The sendMessage method sends a text message to the eye tracker. 
        
        Messages are generally used to send information you want 
        saved with the native eye data file and are often used to 
        synchronize stimulus changes in the experiment with the eye
        data stream being saved to the native eye tracker data file (if any).
        
        This means that the sendMessage implementation needs to 
        perform in real-time, with a delay of <1 msec from when a message is 
        sent to when it is time stamped by the eye tracker, for it to be 
        accurate in this regard.

        If this standard can not be met, the expected delay and message 
        timing precision (variability) should be provided in the eye tracker's 
        implementation notes.
        
        Note that if using the ioDataStore to save the eye tracker data, the use of 
        this method is quite optional, and instead Experiment Device Message Events
        should be used instead, as they are stored in the ioDataSTore along with all event
        information for post hoc use.

        Args:
           message_contents (str): 
               If message_contents is a string, check with the implementations documentation if there are any string length limits.

        Kwargs:
           time_offset (float): sec.msec_usec time offset that the time stamp of
                              the message should be offset in the eye tracker data file.
                              time_offset can be used so that a message can be sent
                              for a display change **BEFORE** or **AFTER** the actual
                              flip occurred, using the following formula:
                                  
                              time_offset = sendMessage_call_time - event_time_message_represent
                              
                              Both times should be based on the ioHub.Computer.getTime() time base.
                              
                              If time_offset is not supported by the eye tracker implementation being used, a warning message will be printed to stdout.
        
        Return:
            (int): EyeTrackerConstants.EYETRACKER_OK, EyeTrackerConstants.EYETRACKER_ERROR, or EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED                      
        """
            
        return EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED
    
    def runSetupProcedure(self, starting_state=EyeTrackerConstants.DEFAULT_SETUP_PROCEDURE):
        """
        The runSetupProcedure allows the eye tracker interface to perform 
        such things as participant placement validation, camera setup, calibration,
        and validation type activities. The details of what this method does exactly
        is implementation specific. This is a blocking call for the experiment process
        and will not return until the necessary steps have been done so that the
        eye tracker is ready to start collecting eye data when the method returns.
        
        Args: 
            None
            
        Kwargs: 
            starting_state (int): The state that the eye tracker should start with or perform when the runSetupProcedure method is called. Valid options are:
				* EyeTrackerConstants.DEFAULT_SETUP_PROCEDURE (the default) indicates that the standard setup and calibration procedure should be performed.
				* EyeTrackerConstants.CALIBRATION_STATE indicates the eye tracker should immediately start the calibration procedure when the method is called.
				* EyeTrackerConstants.VALIDATION_STATE indicates the eye tracker should immediately start the validation procedure when the method is called.
				* EyeTrackerConstants.DRIFT_CORRECTION_STATE indicates the eye tracker should immediately start the validation procedure when the method is called.
				* EyeTrackerConstants.TRACKER_FEEDBACK_STATE indicates that any supported operator feeback graphics or windows should be displayed when the method is called..
            
			An eye tracker implementation is only required to support the EyeTrackerConstants.DEFAULT_SETUP_PROCEDURE setting.
                
        Return:
            int: EyeTrackerConstants.EYETRACKER_OK if this method and starting_state is supported and the runSetupProcedure ran successfully. If the starting state specified was anything other the EyeTrackerConstants.VALIDATION_START_STATE, the performed calibration routine must have also passed (been sucessful). Possible values:
                 * EyeTrackerConstants.EYETRACKER_CALIBRATION_ERROR if this method and starting_state is supported but either calibration or drift correction (depending on the state argument provided) failed. In this case; the method can be called again to attempt a sucessful calibration and or drift correction.                
                 * EyeTrackerConstants.EYETRACKER_ERROR if this method is supported and starting_state is, but an error occurred during the method (other than a failed calibration or drift correct result).
                 * EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED if the eye tracker implementation does not support this method or the specified starting_state.
        """
        
        # Implementation Note: Change this list to only include the states your eye tracker can support.
        IMPLEMENTATION_SUPPORTED_STATES=[EyeTrackerConstants.getName(EyeTrackerConstants.DEFAULT_SETUP_PROCEDURE),
                                         EyeTrackerConstants.getName(EyeTrackerConstants.CALIBRATION_START_STATE),
                                         EyeTrackerConstants.getName(EyeTrackerConstants.VALIDATION_START_STATE)]
        
        if starting_state in IMPLEMENTATION_SUPPORTED_STATES:

            if starting_state == EyeTrackerConstants.getName(EyeTrackerConstants.DEFAULT_SETUP_PROCEDURE):
                # Implementation Note: Run your custom implementation logic for the method here
                print2err("EyeTracker should handle runSetupProcedure method with starting_state of {0} now.".format(starting_state))
                
                # Implementation Note: result should be changed to return one of
                #       EyeTrackerConstants.EYETRACKER_OK 
                #       EyeTrackerConstants.EYETRACKER_CALIBRATION_ERROR 
                #       EyeTrackerConstants.EYETRACKER_ERROR 
                result = EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED
                return result
            else:
                return EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED
        else:
            return createErrorResult("INVALID_METHOD_ARGUMENT_VALUE",error_message="The starting_state arguement value provided is not recognized",method="EyeTracker.runSetupProcedure",arguement='starting_state', value=starting_state)            

                
    def setRecordingState(self,recording):
        """
        The setRecordingState method is used to start or stop the recording 
        and transmition of eye data from the eye tracking device.
        
        Args:
            recording (bool): if True, the eye tracker will start recordng data.; false = stop recording data.
           
        Return:
            bool: the current recording state of the eye tracking device
        """
        
        if not isinstance(recording,bool):
            return createErrorResult("INVALID_METHOD_ARGUMENT_VALUE",error_message="The recording arguement value provided is not a boolean.",method="EyeTracker.setRecordingState",arguement='recording', value=recording)
        
        # Implementation Note: Perform your implementation specific logic for this method here
        print2err("EyeTracker should handle setRecordingState method with recording value of {0} now.".format(recording))
        
        # Implementation Note: change current_recording_state to be True or False, based on whether the eye tracker is now recording or not.
        current_recording_state=EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED
        return current_recording_state

    def isRecordingEnabled(self):
        """
        The isRecordingEnabled method indicates if the eye tracker device is currently
        recording data or not. 
   
        Args:
           None
  
        Return:
            bool: True == the device is recording data; False == Recording is not occurring
        """
        
        # Implementation Note: Perform your implementation specific logic for this method here
        print2err("EyeTracker should handle isRecordingEnabled method now.")

        # Implementation Note: change is_recording to be True or False, based on whether the eye tracker is recording or not.
        is_recording=EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED
        
        return is_recording
        
    def getLastSample(self):
        """
        The getLastSample method returns the most recent ioHub sample event available.
        The eye tracker must be recording data for a sample event to be returned, otherwise None is returned.

        Args: 
            None

        Returns:
            int: If this method is not supported by the eye tracker interface, EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED is returned.

            None: If the eye tracker is not currently recording data.

            EyeSample: If the eye tracker is recording in a monocular tracking mode, the latest sample event of this event type is returned.

            BinocularEyeSample:  If the eye tracker is recording in a binocular tracking mode, the latest sample event of this event type is returned.
        """
        
        return self._latest_sample

    def getLastGazePosition(self):
        """
        The getLastGazePosition method returns the most recent eye gaze position
        retieved from the eye tracker device. This is the position on the 
        calibrated 2D surface that the eye tracker is reporting as the current
        eye position. The units are in the units in use by the Display device. 
        
        If binocular recording is being performed, the average position of both
        eyes is returned. 
        
        If no samples have been received from the eye tracker, or the 
        eye tracker is not currently recording data, None is returned.

        Args: 
            None

        Returns:
            int: If this method is not supported by the eye tracker interface, EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED is returned.

            None: If the eye tracker is not currently recording data or no eye samples have been received.

            tuple: Latest (gaze_x,gaze_y) position of the eye(s)
        """
        return self._latest_gaze_position


    def _eyeTrackerToDisplayCoords(self,eyetracker_point):
        """
        The _eyeTrackerToDisplayCoords method must be used by an eye trackers implementation
        of the Common Eye Tracker Interface to convert eye trackers coordinate space
        to the ioHub.devices.Display coordinate space being used. 
        Any screen based coordinates that exist in the data provided to the ioHub 
        by the device implementation must use this method to
        convert the x,y eye tracker point to the correct coordinate space.
        
        Default implementation is to call the Display device method:
            
            self._display_device._pixel2DisplayCoord(gaze_x,gaze_y,self._display_device.getIndex())
            
        where gaze_x,gaze_y = eyetracker_point, which is assumed to be in screen pixel
        coordinates, with a top-left origin. If the eye tracker provides the eye position
        data in a coordinate space other than screen pixel position with top-left origin,
        the eye tracker position should first be converted to this coordinate space before
        passing the position data px,py to the _pixel2DisplayCoord method.
        
        self._display_device.getIndex() provides the index of the display for multi display setups.
        0 is the default index, and valid values are 0 - N-1, where N is the number
        of connected, active, displays on the computer being used.

        Args:
            eyetracker_point (object): eye tracker implementation specific data type representing an x, y position on the calibrated 2D plane (typically a computer display screen).

        Returns:
            (x,y): The x,y eye position on the calibrated surface in the current ioHub.devices.Display coordinate type and space.
        """
        gaze_x=eyetracker_point[0]
        gaze_y=eyetracker_point[1]
        
        # If the eyetracker_point does not represent eye data as display 
        # pixel position using a top-left origin, convert the naive eye tracker
        # gaze coordinate space to a display pixel position using a top-left origin
        # here before passing gaze_x,gaze_y to the _pixel2DisplayCoord method.
        # ....
        
        return self._display_device._pixel2DisplayCoord(gaze_x,gaze_y,self._display_device.getIndex()) 
   
    def _displayToEyeTrackerCoords(self,display_x,display_y):
        """
        The _displayToEyeTrackerCoords method must be used by an eye trackers implementation
        of the Common Eye Tracker Interface to convert any gaze positions provided
        by the ioHub to the appropriate x,y gaze position coordinate space for the
        eye tracking device in use.
        
        This method is simply the inverse operation performed by the _eyeTrackerToDisplayCoords
        method.
        
        Default implementation is to just return the result of self._display_device.display2PixelCoord(...).

        Args:
            display_x (float): The horizontal eye position on the calibrated 2D surface in ioHub.devices.Display coordinate space.
            display_y (float): The vertical eye position on the calibrated 2D surface in ioHub.devices.Display coordinate space.
            
        Returns:
            (object): eye tracker implementation specific data type representing an x, y position on the calibrated 2D plane (typically a computer display screen).
        """

        pixel_x, pixel_y=self._display_device.display2PIxelCoord(display_x,display_y,self._display_device.getIndex()) 
        return pixel_x,pixel_y

    def __del__(self):
        """
        Do any final cleanup of the eye tracker before the object is destroyed.
        """
        self.__class__._INSTANCE=None
        
from eye_events import (MonocularEyeSampleEvent, BinocularEyeSampleEvent,
                        FixationStartEvent,FixationEndEvent,SaccadeStartEvent,
                        SaccadeEndEvent,BlinkStartEvent,BlinkEndEvent)
        