# -*- coding: utf-8 -*-
"""
ioHub
Common Eye Tracker Interface for the TheEyeTribe system.
.. file: ioHub/devices/eyetracker/hw/theeyetribe/eyetracker.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License
(GPL version 3 or any later version).

.. moduleauthor:: ????
.. fileauthor:: ???
"""

import numpy as np 
from ..... import print2err,printExceptionDetailsToStdErr
from .....constants import EventConstants, EyeTrackerConstants
from .... import Computer
from ... import EyeTrackerDevice
from ...eye_events import *
from gevent import socket
from pyTribe import TheEyeTribe
#try:
#    from tetCalibrationGraphics import TETPsychopyCalibrationGraphics
#except:
#    print2err("Error importing TETPsychopyCalibrationGraphics")
#    printExceptionDetailsToStdErr()


class EyeTracker(EyeTrackerDevice):
    """
    TheEyeTribe implementation of the Common Eye Tracker Interface can be used
    by providing the following EyeTracker path as the device class in 
    the iohub_config.yaml device settings file:
        
        eyetracker.hw.theeyetribe.EyeTracker
        
    """

    # TODO Change DEVICE_TIMEBASE_TO_SEC based on the systems native time base
    # Currently it is set expecting eye tracker times received to be in
    # microseconds
    #
    DEVICE_TIMEBASE_TO_SEC=0.000001
    EVENT_CLASS_NAMES=['MonocularEyeSampleEvent','BinocularEyeSampleEvent','FixationStartEvent',
                         'FixationEndEvent', 'SaccadeStartEvent', 'SaccadeEndEvent',
                         'BlinkStartEvent', 'BlinkEndEvent']

    # Set in the __init__ to to be the instance of the pyTribe.TheEyeTribe
    # interface.
    _eyetribe=None
    _recording=False
    __slots__=[]

    def __init__(self,*args,**kwargs):        
        EyeTrackerDevice.__init__(self,*args,**kwargs)
        # Could do any TET device config based on device config settings in yaml
        # file here.
        # ...
        #

        # Used to hold the last sample processed by iohub.
        self._latest_sample=None

        # Used to hold the last valid gaze position processed by ioHub.
        # If the last sample received from the TET indicates missing eye
        # position, then this is set to None
        #
        self._latest_gaze_position=None

        print2err("TET setConnectionState....")
        
        r=self.setConnectionState(True)
        
        print2err("TET init complete:", r)
        
    def trackerTime(self):
        """
        Current eye tracker time in the eye tracker's native time base. 
        The TET system uses a usec timebase.
        
        Args: 
            None
            
        Returns:
            float: current native eye tracker time. (in usec for the TET)
        """
        if self._eyetribe:
            return 0.0 # TODO Replace with TET code to get crrent device's time.
        return EyeTrackerConstants.EYETRACKER_ERROR
        
    def trackerSec(self):
        """
        Current eye tracker time, normalized to sec.msec format.

        Args: 
            None
            
        Returns:
            float: current native eye tracker time in sec.msec-usec format.
        """
        if self._eyetribe:
            return 0.0 # TODO *self.DEVICE_TIMEBASE_TO_SEC
        return EyeTrackerConstants.EYETRACKER_ERROR

    def setConnectionState(self,enable):
        """
        setConnectionState is a no-op when using the TET system, as the
        connection is established when the TheEyeTribe EyeTracker class is created,
        and remains active until the program ends, or a error occurs resulting
        in the loss of the tracker connection.

        Args:
            enable (bool): True = enable the connection, False = disable the connection.

        Return:
            bool: indicates the current connection state to the eye tracking hardware.
        """
        if enable is True and self._eyetribe is None:
            try:
                EyeTracker._eyetribe=TheEyeTribe()
                # set the iohub eyetracker _handleNativeEvent to be what
                # id called by TheEyeTribe when a sample is received.
                self._eyetribe.processSample=self._handleNativeEvent
                return True
            except:
                print2err("Error connecting to TheEyeTribe Device.")
                printExceptionDetailsToStdErr()            
        elif enable is False and self._eyetribe is not None:
            try:
                EyeTracker._eyetribe.close()
                self._eyetribe.processSample=None
                EyeTracker._eyetribe=None
                return False
            except:
                print2err("Error disconnecting from TheEyeTribe Device.")
                printExceptionDetailsToStdErr()            
        return EyeTrackerConstants.EYETRACKER_ERROR    
        
        
    def isConnected(self):
        """
        isConnected returns whether the TheEyeTribe is connected to the experiment PC
        and if the tracker state is valid. Returns True if the tracker can be 
        put into Record mode, etc and False if there is an error with the tracker
        or tracker connection with the experiment PC.

        Args:
            None
            
        Return:
            bool:  True = the eye tracking hardware is connected. False otherwise.

        """
        if self._eyetribe:
            return True
        return False
 
    def sendMessage(self,message_contents,time_offset=None):
        """
        The sendMessage method is not supported by the TheEyeTribe implementation
        of the Common Eye Tracker Interface, as the TheEyeTribe SDK does not support
        saving eye data to a native data file during recording.
        """
        # TODO TET Implementation
        return EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED

    def sendCommand(self, key, value=None):
        """
        The sendCommand method is not supported by the TheEyeTribe Common Eye Tracker
        Interface.
        """
        # TODO TET Implementation
        return EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED

#    def runSetupProcedure(self,starting_state=EyeTrackerConstants.DEFAULT_SETUP_PROCEDURE):
#        """
#        runSetupProcedure performs a calibration routine for the TheEyeTribe
#        eye tracking system.
#        
#        Result:
#            bool: True if setup / calibration procedure passed, False otherwise. If false, should likely exit experiment.
#        """
#        try:
#            # TODO TET Implementation
#            calibration_properties=self.getConfiguration().get('calibration')
#            screenColor=calibration_properties.get('screen_background_color')
#            # [r,g,b] of screen
#
#            #genv=TETPsychopyCalibrationGraphics(self,screenColor=screenColor)
#
#            #calibrationOK=genv.runCalibration()
#            #genv.window.close()
#            
#            #genv._unregisterEventMonitors()
#            #genv.clearAllEventBuffers()
#            
#            return EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED
#            
#        except:
#            print2err("Error during runSetupProcedure")
#            printExceptionDetailsToStdErr()
#        return EyeTrackerConstants.EYETRACKER_ERROR

    def enableEventReporting(self,enabled=True):
        """
        enableEventReporting is functionally identical to the eye tracker
        device specific setRecordingState method.
        """
        
        try:        
            enabled=EyeTrackerDevice.enableEventReporting(self,enabled)
            self.setRecordingState(enabled)
            return enabled
        except Exception, e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.enself._eyetribe.ableEventReporting", error=e)

    def setRecordingState(self,recording):
        """
        setRecordingState is used to start or stop the recording of data from 
        the eye tracking device.
        
        args:
           recording (bool): if True, the eye tracker will start recordng available
              eye data and sending it to the experiment program if data streaming
              was enabled for the device. If recording == False, then the eye
              tracker stops recording eye data and streaming it to the experiment.
              
        If the eye tracker is already recording, and setRecordingState(True) is
        called, the eye tracker will simple continue recording and the method call
        is a no-op. Likewise if the system has already stopped recording and 
        setRecordingState(False) is called again.

        Args:
            recording (bool): if True, the eye tracker will start recordng data.; false = stop recording data.
           
        Return:
            bool: the current recording state of the eye tracking device
        """
        if self._eyetribe and recording is True and not self.isRecordingEnabled():
            # TODO TET Implementation
            self._eyetribe.sendSetMessage(push=True, version=1)
            EyeTracker._recording=True
            return EyeTrackerDevice.enableEventReporting(self,True)
        elif self._eyetribe and recording is False and self.isRecordingEnabled():
            # TODO TET Implementation
            self._latest_sample=None
            self._latest_gaze_position=None
            EyeTracker._recording=False
            return self._eyetribe.sendSetMessage(push=False, version=1)

        return self.isRecordingEnabled() 

    def isRecordingEnabled(self):
        """
        isRecordingEnabled returns the recording state from the eye tracking 
        device.

        Args:
           None
  
        Return:
            bool: True == the device is recording data; False == Recording is not occurring
        """
        if self._eyetribe:
            return self._recording# TODO TET Implementation
        return False
        
    def getLastSample(self):
        """
        Returns the latest sample retrieved from the TheEyeTribe device. The TheEyeTribe
        system always using the BinocularSample Event type.

        Args: 
            None

        Returns:
            None: If the eye tracker is not currently recording data.

            EyeSample: If the eye tracker is recording in a monocular tracking mode, the latest sample event of this event type is returned.

            BinocularEyeSample:  If the eye tracker is recording in a binocular tracking mode, the latest sample event of this event type is returned.
        """
        return self._latest_sample

    def getLastGazePosition(self):
        """
        Returns the latest 2D eye gaze position retrieved from the TheEyeTribe device.
        This represents where the eye tracker is reporting each eye gaze vector
        is intersecting the calibrated surface.
        
        In general, the y or vertical component of each eyes gaze position should
        be the same value, since in typical user populations the two eyes are
        yoked vertically when they move. Therefore any difference between the 
        two eyes in the y dimention is likely due to eye tracker error.
        
        Differences between the x, or horizontal component of the gaze position,
        indicate that the participant is being reported as looking behind or
        in front of the calibrated plane. When a user is looking at the 
        calibration surface , the x component of the two eyes gaze position should be the same.
        Differences between the x value for each eye either indicates that the
        user is not focussing at the calibrated depth, or that there is error in the eye data.
        
        The above remarks are true for any eye tracker in general.
        
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
            None: If the eye tracker is not currently recording data or no eye samples have been received.

            tuple: Latest (gaze_x,gaze_y) position of the eye(s)
        """
        return self._latest_gaze_position


    def _handleNativeEvent(self,*args,**kwargs):
        """
        This method is called every time there is new eye data available from
        the TheEyeTribe system, which will be roughly equal to the sampling rate eye
        data is being recorded at. The callback needs to return as quickly as 
        possible so there is no chance of overlapping calls being made to the
        callback. Therefore this method simply puts the event data received from 
        the eye tracker device, and the local ioHub time the callback was
        called, into a buffer for processing by the ioHub event system.
        
        Native sample format:
        
            {
                "category": "tracker",
                "statuscode": 200,
                "values": {
                    "frame" : {
                        "time": int,              //timestamp
                        "fix": bool,           //is fixated?
                        "state": int,             //32bit masked state integer
                        "raw": {                  //raw gaze coordinates in pixels
                            "x": int,
                            "y": int
                        },
                        "avg": {                  //smoothed gaze coordinates in pix
                            "x": int,
                            "y": int
                        },
            
                        "lefteye": {
                            "raw": {              //raw coordinates in pixels
                                "x": int,
                                "y": int
                            },
            
                            "avg": {              //smoothed coordinates in pix
                                "x": int,
                                "y": int
                            },
                            "psize": float,       //pupil size
                            "pcenter": {          //pupil coordinates normalized
                                "x": float,
                                "y": float
                            }
                        },
            
                        "righteye": {
                            "raw": {             //raw coordinates in pixels
                                "x": int,
                                "y": int
                            },
                            "avg": {             //smoothed coordinates in pix
                                "x": int,
                                "y": int
                            },
                            "psize": float,     //pupil size
                            "pcenter": {        //pupil coordinates normalized
                                "x": float,
                                "y": float
                            }
                        }
                    }
                }
            }        
        """
        native_sample=args[0]
        print2err("iohub TET got:", native_sample)
        # TODO TET Implementation ?????
        return True#EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED

#        if self.isReportingEvents():
#            try:
#                eye_data_event=args[1]
#                logged_time_iohub_usec=Computer.getTime()/self.DEVICE_TIMEBASE_TO_SEC
#                logged_time_tobii_local_usec=self._tobii._getTobiiClockTime()
#                data_time_in_tobii_local_time=self._tobii._sync_manager.convert_from_remote_to_local(eye_data_event.Timestamp)
#
#                data_delay=logged_time_tobii_local_usec-data_time_in_tobii_local_time
#
#                logged_time=logged_time_iohub_usec*self.DEVICE_TIMEBASE_TO_SEC
#                device_event_time=data_time_in_tobii_local_time*self.DEVICE_TIMEBASE_TO_SEC
#                iohub_event_time=(logged_time_iohub_usec-data_delay)*self.DEVICE_TIMEBASE_TO_SEC # in sec.msec_usec
#                data_delay=data_delay*self.DEVICE_TIMEBASE_TO_SEC
#
#                self._addNativeEventToBuffer((logged_time,device_event_time,iohub_event_time,data_delay,eye_data_event))
#                return True
#            except:
#                print2err("ERROR IN _handleNativeEvent")
#                printExceptionDetailsToStdErr()
#        else:
#            print2err("self._handleNativeEvent called but isReportingEvents == false")
   
    def _getIOHubEventObject(self,native_event_data):
        """
        The _getIOHubEventObject method is called by the ioHub Server to convert 
        new native device event objects that have been received to the appropriate 
        ioHub Event type representation. 
               
        The TheEyeTribe ioHub eye tracker implementation uses a callback method
        to register new native device events with the ioHub Server. 
        Therefore this method converts the native TheEyeTribe event data into
        an appropriate ioHub Event representation. 
        
        Args:
            native_event_data: object or tuple of (callback_time, native_event_object)
           
        Returns:
            tuple: The appropriate ioHub Event type in list form.
        """
        # TODO TET Implementation
        return EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED

#        try:
#            logged_time,device_event_time,iohub_event_time,data_delay,eye_data_event=native_event_data
#
#            event_type=EventConstants.BINOCULAR_EYE_SAMPLE
#
#            left_gaze_x=eye_data_event.LeftGazePoint2D.x
#            left_gaze_y=eye_data_event.LeftGazePoint2D.y
#            right_gaze_x=eye_data_event.RightGazePoint2D.x
#            right_gaze_y=eye_data_event.RightGazePoint2D.y
#
#            if left_gaze_x != -1 and left_gaze_y != -1:
#                left_gaze_x,left_gaze_y=self._eyeTrackerToDisplayCoords((left_gaze_x,left_gaze_y))#
#
#            if right_gaze_x != -1 and right_gaze_y != -1:
#                right_gaze_x,right_gaze_y=self._eyeTrackerToDisplayCoords((right_gaze_x,right_gaze_y))#
#
#            # TO DO: Set CI to be equal to current time error stated in TheEyeTribe Sync manager
#            confidenceInterval=0.0
#            binocSample=[
#                         0,
#                         0,
#                         0, #device id (not currently used)
#                         Computer._getNextEventID(),
#                         event_type,
#                         device_event_time,
#                         logged_time,
#                         iohub_event_time,
#                         confidenceInterval,
#                         data_delay,
#                         0, # filtered id (always 0 right now)
#                         left_gaze_x,
#                         left_gaze_y,
#                         EyeTrackerConstants.UNDEFINED, # Left Eye Angle z
#
#                         eye_data_event.LeftEyePosition3D.x,
#                         eye_data_event.LeftEyePosition3D.y,
#                         eye_data_event.LeftEyePosition3D.z,
#                         eye_data_event.LeftEyePosition3DRelative.x,
#                         eye_data_event.LeftEyePosition3DRelative.y,
#                         eye_data_event.LeftEyePosition3DRelative.z,
#                         EyeTrackerConstants.UNDEFINED, # Left Eye Angle x
#                         EyeTrackerConstants.UNDEFINED, # Left Eye Angle y
#                         EyeTrackerConstants.UNDEFINED, # Left Camera Sensor position x
#                         EyeTrackerConstants.UNDEFINED, # Left Camera Sensor position y
#                         eye_data_event.LeftPupil,
#                         EyeTrackerConstants.PUPIL_DIAMETER_MM,
#                         EyeTrackerConstants.UNDEFINED, # Left pupil size measure 2
#                         EyeTrackerConstants.UNDEFINED, # Left pupil size measure 2 type
#                         EyeTrackerConstants.UNDEFINED, # Left PPD x
#                         EyeTrackerConstants.UNDEFINED, # Left PPD y
#                         EyeTrackerConstants.UNDEFINED, # Left velocity x
#                         EyeTrackerConstants.UNDEFINED, # Left velocity y
#                         EyeTrackerConstants.UNDEFINED, # Left velocity xy
#                         right_gaze_x,
#                         right_gaze_y,
#                         EyeTrackerConstants.UNDEFINED, # Right Eye Angle z
#                         eye_data_event.RightEyePosition3DRelative.x,
#                         eye_data_event.RightEyePosition3DRelative.y,
#                         eye_data_event.RightEyePosition3DRelative.z,
#                         EyeTrackerConstants.UNDEFINED, # Right Eye Angle x
#                         EyeTrackerConstants.UNDEFINED, # Right Eye Angle y
#                         EyeTrackerConstants.UNDEFINED, #Right Camera Sensor position x
#                         EyeTrackerConstants.UNDEFINED, #Right Camera Sensor position y
#                         eye_data_event.RightPupil,
#                         EyeTrackerConstants.PUPIL_DIAMETER_MM,
#                         EyeTrackerConstants.UNDEFINED, # Right pupil size measure 2
#                         EyeTrackerConstants.UNDEFINED, # Right pupil size measure 2 type
#                         EyeTrackerConstants.UNDEFINED, # Right PPD x
#                         EyeTrackerConstants.UNDEFINED, # Right PPD y
#                         EyeTrackerConstants.UNDEFINED, # right velocity x
#                         EyeTrackerConstants.UNDEFINED, # right velocity y
#                         EyeTrackerConstants.UNDEFINED, # right velocity xy
#                         int(str(eye_data_event.LeftValidity)+str(eye_data_event.RightValidity))
#                         ]
#
#            self._latest_sample=binocSample
#
#            if eye_data_event.LeftValidity>=2 and eye_data_event.RightValidity >=2:
#                self._latest_gaze_position=None
#            elif eye_data_event.LeftValidity<2 and eye_data_event.RightValidity<2:
#                self._latest_gaze_position=[(right_gaze_x+left_gaze_x)/2.0,
#                                                (right_gaze_y+left_gaze_y)/2.0]
#            elif eye_data_event.LeftValidity<2:
#                self._latest_gaze_position=[left_gaze_x,left_gaze_y]
#            elif eye_data_event.RightValidity<2:
#                self._latest_gaze_position=[right_gaze_x,right_gaze_y]
#
#            self._last_callback_time=logged_time
#
#            return binocSample
#        except:
#            printExceptionDetailsToStdErr()
#        return None
        
    def _eyeTrackerToDisplayCoords(self,eyetracker_point):
        """
        Converts TheEyeTribe gaze positions to the Display device coordinate space.
        """
        # TODO TET Implementation
        return EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED

#        gaze_x,gaze_y=eyetracker_point
#        left,top,right,bottom=self._display_device.getCoordBounds()
#        w,h=right-left,top-bottom
#        x,y=left+w*gaze_x,bottom+h*(1.0-gaze_y)
#       return x,y
        
    def _displayToEyeTrackerCoords(self,display_x,display_y):
        """
        Converts a Display device point to TheEyeTribe gaze position coordinate space.
        """
        # TODO TET Implementation
        return EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED
#        left,top,right,bottom=self._display_device.getCoordBounds()
#        w,h=right-left,top-bottom
#        return (left-display_x)/w,(top-display_y)/h

    def _close(self):
        if self._eyetribe:
            # TODO TET Implementation
            self.setConnectionState(False)
        EyeTrackerDevice._close(self)