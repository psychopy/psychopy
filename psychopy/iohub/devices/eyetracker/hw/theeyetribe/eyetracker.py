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

getTime=Computer.getTime

#try:
#    from tetCalibrationGraphics import TETPsychopyCalibrationGraphics
#except Exception:
#    print2err("Error importing TETPsychopyCalibrationGraphics")
#    printExceptionDetailsToStdErr()


class EyeTracker(EyeTrackerDevice):
    """
    TheEyeTribe implementation of the Common Eye Tracker Interface can be used
    by providing the following EyeTracker path as the device class in 
    the iohub_config.yaml device settings file:
        
        eyetracker.hw.theeyetribe.EyeTracker
        
    """

    # EyeTribe tracker times are received as msec
    #
    DEVICE_TIMEBASE_TO_SEC=0.001
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
        
        r=self.setConnectionState(True)
        
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
             # TODO Replace with TET code to get crrent device's time.
            return getTime()*1000.0
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
            return self.trackerTime()*self.DEVICE_TIMEBASE_TO_SEC
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
                net_settings = self.getConfiguration().get('network_settings')
                host_ip = net_settings.get('server_address')
                host_port = net_settings.get('server_port')
                EyeTracker._eyetribe=TheEyeTribe(server_ip=host_ip,
                                                 server_port=host_port)
                # set the iohub eyetracker _handleNativeEvent to be what
                # id called by TheEyeTribe when a sample is received.
                self._eyetribe.processSample=self._handleNativeEvent
                return True
            except Exception:
                print2err("Error connecting to TheEyeTribe Device.")
                printExceptionDetailsToStdErr()            
        elif enable is False and self._eyetribe is not None:
            try:
                EyeTracker._eyetribe.close()
                self._eyetribe.processSample=None
                EyeTracker._eyetribe=None
                return False
            except Exception:
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
#        except Exception:
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
            print2err("EyeTracker.enableEventReporting", str(e))

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
           
        Return:trackerTime
            bool: the current recording state of the eye tracking device
        """
        if self._eyetribe and recording is True and not self.isRecordingEnabled():
            self._eyetribe.sendSetMessage(push=True, version=1)
            EyeTracker._recording=True
            return EyeTrackerDevice.enableEventReporting(self,True)
        elif self._eyetribe and recording is False and self.isRecordingEnabled():
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
        user is not focusstrackerTimeing at the calibrated depth, or that there is error in the eye data.
        
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
        This method is called by pyTribe.TheEyeTribe class each time an eye
        sample is received from the eye tracker.
        """
        try:
            logged_time=Computer.getTime()
            tracker_time=self.trackerSec()           

            sample_dict=args[0]
            statuscode=sample_dict.get('statuscode',0)
            
            if statuscode != 200:
                print2err("** TODO: How to handle eye sample with statuscode of: ",statuscode)    
            
            sample_values=sample_dict.get('values')          
            sample = sample_values.get('frame')  
  
            if len(sample_values)>1:
                print2err("** Warning: Received Sample with extra values:")
                for k,v in sample_values.iteritems():
                    if k != 'frame':
                        print2err(k," : ",v)

            event_type=EventConstants.BINOCULAR_EYE_SAMPLE
            
            status=sample.get('state',0)
            if sample.get('fix') is True:
                status+=TheEyeTribe.STATE_TRACKING_FIXATED
                
            event_timestamp=sample.get('time',0)*self.DEVICE_TIMEBASE_TO_SEC
            event_delay=tracker_time-event_timestamp
            iohub_time=logged_time-event_delay      
            # TODO: Determine how to calc CI for TET Samples
            confidence_interval=0.0

            tracking_failed=(status & TheEyeTribe.STATE_TRACKING_FAIL)!=0
            tracking_lost=(status& TheEyeTribe.STATE_TRACKING_LOST)!=0
            
            if tracking_failed or tracking_lost:
                combined_gaze_x,combined_gaze_y=None,None
                combined_avg_gaze_x,combined_avg_gaze_y=None,None
                left_pupil_pos_x=EyeTrackerConstants.UNDEFINED
                left_pupil_pos_y=EyeTrackerConstants.UNDEFINED
                left_gaze_x=left_gaze_y=EyeTrackerConstants.UNDEFINED
                left_avg_gaze_x=left_avg_gaze_y=EyeTrackerConstants.UNDEFINED
                left_pupil_size=EyeTrackerConstants.UNDEFINED
                right_pupil_pos_x=EyeTrackerConstants.UNDEFINED
                right_pupil_pos_y=EyeTrackerConstants.UNDEFINED
                right_gaze_x=right_gaze_y=EyeTrackerConstants.UNDEFINED
                right_avg_gaze_x=right_avg_gaze_y=EyeTrackerConstants.UNDEFINED
                right_pupil_size=EyeTrackerConstants.UNDEFINED
            
            else:
                combined_gaze_x=sample.get('raw',{}).get('x')
                combined_gaze_y=sample.get('raw',{}).get('y')
                combined_gaze_x,combined_gaze_y=self._eyeTrackerToDisplayCoords(
                                                (combined_gaze_x,combined_gaze_y))
    
                combined_avg_gaze_x=sample.get('avg',{}).get('x')
                combined_avg_gaze_y=sample.get('avg',{}).get('y')
                combined_avg_gaze_x,combined_avg_gaze_y=self._eyeTrackerToDisplayCoords(
                                                (combined_avg_gaze_x,
                                                 combined_avg_gaze_y))
            
                left_eye_data=sample.get('lefteye')
                
                left_gaze_x=left_eye_data.get('raw',{}).get('x')
                left_gaze_y=left_eye_data.get('raw',{}).get('y')
                left_avg_gaze_x=left_eye_data.get('avg',{}).get('x')
                left_avg_gaze_y=left_eye_data.get('avg',{}).get('y')
                left_pupil_size=left_eye_data.get('psize')
                left_pupil_pos_x=left_eye_data.get('pcenter',{}).get('x')
                left_pupil_pos_y=left_eye_data.get('pcenter',{}).get('y')
                left_gaze_x,left_gaze_y=self._eyeTrackerToDisplayCoords(
                                                (left_gaze_x,
                                                 left_gaze_y))
                left_avg_gaze_x,left_avg_gaze_y=self._eyeTrackerToDisplayCoords(
                                                (left_avg_gaze_x,left_avg_gaze_y))

                right_eye_data=sample.get('righteye')
                right_gaze_x=right_eye_data.get('raw',{}).get('x')
                right_gaze_y=right_eye_data.get('raw',{}).get('y')
                right_avg_gaze_x=right_eye_data.get('avg',{}).get('x')
                right_avg_gaze_y=right_eye_data.get('avg',{}).get('y')
                right_pupil_size=right_eye_data.get('psize')
                right_pupil_pos_x=right_eye_data.get('pcenter',{}).get('x')
                right_pupil_pos_y=right_eye_data.get('pcenter',{}).get('y')
                right_gaze_x,right_gaze_y=self._eyeTrackerToDisplayCoords(
                                                (right_gaze_x,right_gaze_y))
                right_avg_gaze_x,right_avg_gaze_y=self._eyeTrackerToDisplayCoords(
                                                (right_avg_gaze_x,
                                                 right_avg_gaze_y))       

            binocSample=[
                     0,
                     0,
                     0, #device id (not currently used)
                     Computer._getNextEventID(),
                     event_type,
                     event_timestamp,
                     logged_time,
                     iohub_time,
                     confidence_interval,
                     event_delay,
                     0,
                     left_avg_gaze_x,
                     left_avg_gaze_y,
                     EyeTrackerConstants.UNDEFINED,
                     left_pupil_pos_x,
                     left_pupil_pos_y,
                     EyeTrackerConstants.UNDEFINED,
                     EyeTrackerConstants.UNDEFINED,
                     EyeTrackerConstants.UNDEFINED,
                     left_gaze_x,
                     left_gaze_y,
                     left_pupil_size,
                     # TODO: Confirm what 'pupil size' actually is in TET
                     EyeTrackerConstants.PUPIL_AREA,
                     EyeTrackerConstants.UNDEFINED,
                     EyeTrackerConstants.UNDEFINED,
                     EyeTrackerConstants.UNDEFINED,
                     EyeTrackerConstants.UNDEFINED,
                     EyeTrackerConstants.UNDEFINED,
                     EyeTrackerConstants.UNDEFINED,
                     EyeTrackerConstants.UNDEFINED,
                     right_avg_gaze_x,
                     right_avg_gaze_y,
                     EyeTrackerConstants.UNDEFINED,
                     right_pupil_pos_x,
                     right_pupil_pos_y,
                     EyeTrackerConstants.UNDEFINED,
                     EyeTrackerConstants.UNDEFINED,
                     EyeTrackerConstants.UNDEFINED,
                     right_gaze_x,
                     right_gaze_y,
                     right_pupil_size,
                     # TODO: Confirm what 'pupil size' actually is in TET
                     EyeTrackerConstants.PUPIL_AREA,
                     EyeTrackerConstants.UNDEFINED,
                     EyeTrackerConstants.UNDEFINED,
                     EyeTrackerConstants.UNDEFINED,
                     EyeTrackerConstants.UNDEFINED,
                     EyeTrackerConstants.UNDEFINED,
                     EyeTrackerConstants.UNDEFINED,
                     EyeTrackerConstants.UNDEFINED,
                     status    
                     ]
                         
            cgp=(combined_gaze_x,combined_gaze_y)
            cagp=(combined_avg_gaze_x,combined_avg_gaze_y)
            
            self._addNativeEventToBuffer((binocSample,(cgp,cagp)))
        except Exception:
            print2err("ERROR occurred during TheEyeTribe Sample Callback.")
            printExceptionDetailsToStdErr()
        finally:
            return 0
            
    def _getIOHubEventObject(self,native_event_data):
        """
        The _getIOHubEventObject method is called by the ioHub Process to convert 
        new native device event objects that have been received to the appropriate 
        ioHub Event type representation. 
        """        
        self._latest_sample,(cyclo_gz_pos,cyclo_avg_gz_pos)=native_event_data

        if cyclo_gz_pos[0] is not None and cyclo_gz_pos[1] is not None:
            self._latest_gaze_position=cyclo_gz_pos
        else:
            self._latest_gaze_position=None

        return self._latest_sample
        
    def _eyeTrackerToDisplayCoords(self,eyetracker_point):
        """
        Converts TheEyeTribe gaze positions to the 
        Display device coordinate space.
        """
        try:
            gaze_x,gaze_y=eyetracker_point
            dw,dh=self._display_device.getPixelResolution()
            gaze_x=gaze_x/dw
            gaze_y=gaze_y/dh
            left,top,right,bottom=self._display_device.getCoordBounds()
            w,h=right-left,top-bottom            
            x,y=left+w*gaze_x,bottom+h*(1.0-gaze_y) 
            return x,y
        except Exception,e:
            printExceptionDetailsToStdErr()
        
    def _displayToEyeTrackerCoords(self,display_x,display_y):
        """
        Converts a Display device point to TheEyeTribe gaze position 
        coordinate space.
        """
        try:                        
            cl,ct,cr,cb=self._display_device.getCoordBounds()
            cw,ch=cr-cl,ct-cb
            
            dl,dt,dr,db=self._display_device.getBounds()
            dw,dh=dr-dl,db-dt
            
            cxn,cyn=(display_x+cw/2)/cw , 1.0-(display_y-ch/2)/ch       
            return cxn*dw,  cyn*dh          
           
        except Exception,e:
            printExceptionDetailsToStdErr()

    def _close(self):
        if self._eyetribe:
            self.setConnectionState(False)
        EyeTrackerDevice._close(self)