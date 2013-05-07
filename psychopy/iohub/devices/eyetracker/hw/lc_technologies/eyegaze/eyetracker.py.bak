"""
ioHub
Common Eye Tracker Interface
.. file: ioHub/devices/eyetracker/hw/lc_technologies/eyegaze/EyeTracker.py

Copyright (C) 2012-2013 iSolver Software Solutions

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""


from ...... import printExceptionDetailsToStdErr, print2err, createErrorResult
from ......constants import EventConstants, EyeTrackerConstants
from ..... import Computer
from .... import EyeTrackerDevice
from ....eye_events import *

import pEyeGaze

import sys
from ctypes import byref, sizeof

class EyeTracker(EyeTrackerDevice):
    """The EyeGaze EyeTracker class implements support of the LC Technologies
    eye tracker lines for the ioHub Common Eye Tracker Interface. 
    
    Please see the eyetracker/hw/lc_technologies/eyegaze/EyeTracker documentation page for 
    details on the supported ioHub configuration settings, implementation notes regarding 
    the EyeGaze implementation of the Common Eye Tracker Interface API, and other
    useful information.
    
    The EyeGaze implementation of the ioHub Common Eye Tracker Interface is currently supported under
    Windows XP and Windows 7. 
    """
    DEVICE_TIMEBASE_TO_SEC=0.000001
    
    EVENT_CLASS_NAMES=['MonocularEyeSampleEvent','BinocularEyeSampleEvent','FixationStartEvent',
                         'FixationEndEvent', 'SaccadeStartEvent', 'SaccadeEndEvent',
                         'BlinkStartEvent', 'BlinkEndEvent']
    __slots__=['_eyegaze_control','_camera_count','_is_eye_follower']
    # <<<

    def __init__(self, *args,**kwargs):
        """
        EyeGaze EyeTracker class. 
        """
        EyeTrackerDevice.__init__(self,*args,**kwargs)

        self._eyegaze_control=None
               
        self.setConnectionState(True)
        
        tracker_type_info=self.sendCommand('get_config')
        
        self._camera_count=int(tracker_type_info['iNVis'])
        self._is_eye_follower=bool(tracker_type_info['bEyefollower'])
                    
    def trackerTime(self):
        """
        """
        return pEyeGaze.lct_TimerRead(None) 
        
    def trackerSec(self):
        """
        """
        return pEyeGaze.lct_TimerRead(None) * self.DEVICE_TIMEBASE_TO_SEC

    def setConnectionState(self,enable):
        """
        """
        try:
            if isinstance(enable,bool):
                if enable is True and not self.isConnected():
                    self._eyegaze_control=pEyeGaze.initializeEyeGazeDevice(self._display_device, self.getConfiguration())           
                    if self._eyegaze_control is None:
                        print2err("Could not connect to EyeGaze. Exiting app..")
                        sys.exit(0)                                        
                    if self._eyegaze_control:
                        return True
                    return False
                elif enable is False and self.isConnected():
                    result=pEyeGaze.EgExit(byref(self._eyegaze_control))
                    self._eyegaze_control=None
                    return False
            else:
                return createErrorResult("INVALID_METHOD_ARGUMENT_VALUE",error_message="The enable arguement value provided is not recognized",method="EyeTracker.setConnectionState",arguement='enable', value=enable)            
        except Exception,e:
                return createErrorResult("IOHUB_DEVICE_EXCEPTION",error_message="An unhandled exception occurred on the ioHub Server Process.",method="EyeTracker.setConnectionState",arguement='enable', value=enable, error=e)            
            
    def isConnected(self):
        """
        """
        try:
            return self._eyegaze_control != None
        except Exception, e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.isConnected", error=e)            
            
    def sendCommand(self, key, value=None):
        """
        """
        try:
            if self._eyegaze_control:
                if key == 'get_control_status':
                    rdict=dict()                    
                    for a in self._eyegaze_control.__slots__:
                        v=getattr(self._eyegaze_control,a)
                        rdict[a]=v
                    return rdict
                elif key == 'get_config':
                    egConfig=pEyeGaze._stEgConfig(0,0)
                    
                    r = pEyeGaze.EgGetConfig(byref(self._eyegaze_control),byref(egConfig),sizeof(egConfig))
                    rdict=None
                    if r==0:                    
                        rdict= {'iNVis':egConfig.iNVis, 'bEyefollower': egConfig.bEyefollower}
                    
                    egConfig=None
                    return rdict
                else:
                    print2err('WARNING: EyeGaze command not handled: {0} = {1}.'.format())
        except Exception, e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.sendCommand", key=key,value=value, error=e)            
        
    def sendMessage(self,message_contents,time_offset=None):
        """
        """
        try:
            if self._eyegaze_control:
                print2err("EyeGaze sendMessage not yet implemented")
                return EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED
        except Exception, e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.sendMessage", message_contents=message_contents,time_offset=time_offset, error=e)            

    def runSetupProcedure(self,starting_state=EyeTrackerConstants.DEFAULT_SETUP_PROCEDURE):
        """
        """                    
        try:
            calibration_properties=self.getConfiguration().get('calibration',None)

            if self._eyegaze_control and self.isRecordingEnabled() is False:                
                # pEyeGaze         
                # when using the external calibrate.exe to 
                # run calibration, need todisconnect from the tracker
                # and reconnect after calibration is done.
                self.setConnectionState(False)
                
                import subprocess,gevent
                #p = subprocess.Popen(('calibrate.exe', ''), env={"PATH": "/usr/bin"})
                p = subprocess.Popen(('calibrate.exe', ''))
                while p.poll() is None:
                    gevent.sleep(0.05)
                self.setConnectionState(True)
          
#            circle_attributes=calibration_properties.get('circle_attributes')
#            targetForegroundColor=circle_attributes.get('outer_color') # [r,g,b] of outer circle of targets
#            targetBackgroundColor=circle_attributes.get('inner_color') # [r,g,b] of inner circle of targets
#            screenColor=calibration_properties.get('screen_background_color')                     # [r,g,b] of screen
#            targetOuterDiameter=circle_attributes.get('outer_diameter')     # diameter of outer target circle (in px)
#            targetInnerDiameter=circle_attributes.get('inner_diameter')     # diameter of inner target circle (in px)
            
        except Exception,e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.runSetupProcedure", 
                    starting_state=starting_state,
                    error=e)            

    def isRecordingEnabled(self,*args,**kwargs):
        """
        """
        try:
            return self._eyegaze_control is not None and self._eyegaze_control.bTrackingActive in [1,True]
        except Exception, e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.isRecordingEnabled", error=e)

    def enableEventReporting(self,enabled=True):
        """
        """
        try:
            if self._eyegaze_control:
                enabled=self.setRecordingState(self,enabled)
            return self.setRecordingState(enabled)
        except Exception, e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.enableEventReporting", error=e)            

    def setRecordingState(self,recording):
        """
        """
        try:
            if not isinstance(recording,bool):
                return createErrorResult("INVALID_METHOD_ARGUMENT_VALUE",
                    error_message="The recording arguement value provided is not a boolean.",
                    method="EyeTracker.setRecordingState",arguement='recording', value=recording)
             
            if self._eyegaze_control and recording is True and not self.isRecordingEnabled():                
                self._last_poll_time=0.0                
                self._eyegaze_control.bTrackingActive=1
                EyeTrackerDevice.enableEventReporting(self,True)            
            elif self._eyegaze_control and recording is False and self.isRecordingEnabled():
                self._eyegaze_control.bTrackingActive=0
                EyeTrackerDevice.enableEventReporting(self,False)
                self._latest_sample=None
                self._latest_gaze_position=None
            return self.isRecordingEnabled()
        except Exception, e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.setRecordingState", error=e)            

    def getLastSample(self):
        """
        """
        try:
            return self._latest_sample
        except Exception, e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.getLastSample", error=e)            

    def getLastGazePosition(self):
        """
        """
        try:
            return self._latest_gaze_position
        except Exception, e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.getLastGazePosition", error=e)             
    
    def _poll(self):
        try:
            if self._eyegaze_control is None or not self.isRecordingEnabled():
                return False
            
            logged_time=Computer.getTime()
            current_tracker_time=self.trackerSec()
            sample_count_available=self._eyegaze_control.iNPointsAvailable

            confidence_interval=logged_time-self._last_poll_time
            self._last_poll_time=logged_time

            if sample_count_available ==0:
                return True
                
            if self._eyegaze_control.iNBufferOverflow > 0:
                # Eye Samples were lost.
                # TBD what to do here (lof to dataStore log?, log to LC data file?)
                print2err("\nWARNING: %d EyeGaze Eye Samples Have Been Lost.\n"%(self._eyegaze_control.iNBufferOverflow))
            
            for i in range(sample_count_available):
                pEyeGaze.EgGetData(byref(self._eyegaze_control))        
                sample_data0=self._eyegaze_control.pstEgData[0]

                device_event_timestamp=sample_data0.dGazeTimeSec               
                # is this really calculating delay??
                event_delay = (current_tracker_time - device_event_timestamp) - (sample_data0.dReportTimeSec - device_event_timestamp)
                iohub_time=logged_time-event_delay

                pupil_measure1_type = EyeTrackerConstants.PUPIL_RADIUS_MM
                
                if self._camera_count == 1: #monocular
                    event_type=EventConstants.MONOCULAR_EYE_SAMPLE
                    eye = EyeTrackerConstants.UNKNOWN_MONOCULAR
                    gaze_x, gaze_y = self._eyeTrackerToDisplayCoords((sample_data0.iIGaze, sample_data0.iJGaze))
                    pupil_measure1 = sample_data0.fPupilRadiusMm
                    status = int(sample_data0.bGazeVectorFound)

                    monoSample=[
                                0,                            # experiment_id (filled in by ioHub)
                                0,                            # session_id (filled in by ioHub)
                                Computer._getNextEventID(),
                                event_type,
                                device_event_timestamp,
                                logged_time,
                                iohub_time,
                                confidence_interval,
                                event_delay,
                                0,                             # ioHub filter id (always 0 now) 
                                eye,
                                gaze_x,
                                gaze_y,
                                EyeTrackerConstants.UNDEFINED, # gaze z
                                EyeTrackerConstants.UNDEFINED, # x eye pos in space
                                EyeTrackerConstants.UNDEFINED, # y eye pos in space
                                EyeTrackerConstants.UNDEFINED, # z eye pos in space
                                EyeTrackerConstants.UNDEFINED, # eye angle in head x
                                EyeTrackerConstants.UNDEFINED, # eye angle in head y
                                EyeTrackerConstants.UNDEFINED, # uncalibrated x eye pos
                                EyeTrackerConstants.UNDEFINED, # uncalibrated y eye pos
                                pupil_measure1,
                                pupil_measure1_type,
                                EyeTrackerConstants.UNDEFINED,  # pupil measure 2
                                EyeTrackerConstants.UNDEFINED,  # pupil measure 2 type  
                                EyeTrackerConstants.UNDEFINED,  # pixels per degree x
                                EyeTrackerConstants.UNDEFINED,  # pixels per degree y
                                EyeTrackerConstants.UNDEFINED,  # sample velocity x
                                EyeTrackerConstants.UNDEFINED,  # sample velocity y
                                EyeTrackerConstants.UNDEFINED,  # 2D sample velocity
                                status
                                ]
                                
                    self._latest_gaze_position=gaze_x,gaze_y
                    self._latest_sample=monoSample
                    self._addNativeEventToBuffer(monoSample)


                elif self._camera_count == 2: #binocular
                    event_type=EventConstants.MONOCULAR_EYE_SAMPLE

                    sample_data1=self._eyegaze_control.pstEgData[1]
                    sample_data4=self._eyegaze_control.pstEgData[4]

                    left_gaze_x, left_gaze_y = self._eyeTrackerToDisplayCoords(
                                        (sample_data4.iIGaze,sample_data4.iJGaze))
                    right_gaze_x, right_gaze_y = self._eyeTrackerToDisplayCoords(
                                        (sample_data1.iIGaze,sample_data1.iJGaze))
                                        
                    left_pupil_measure1 = sample_data4.fPupilRadiusMm
                    right_pupil_measure1 = sample_data1.fPupilRadiusMm

                    status = int(sample_data4.bGazeVectorFound*2+sample_data1.bGazeVectorFound)
                    binocSample=[
                                 0,                            # experiment_id (filled in by ioHub)
                                 0,                            # session_id (filled in by ioHub)
                                 Computer._getNextEventID(),
                                 event_type,
                                 device_event_timestamp,
                                 logged_time,
                                 iohub_time,
                                 confidence_interval,
                                 event_delay,
                                 0,                             # ioHub filter id (always 0 now) 
                                 # LEFT EYE DATA
                                 left_gaze_x, 
                                 left_gaze_y,
                                 EyeTrackerConstants.UNDEFINED, # gaze z
                                 EyeTrackerConstants.UNDEFINED, # x eye pos in space
                                 EyeTrackerConstants.UNDEFINED, # y eye pos in space
                                 EyeTrackerConstants.UNDEFINED, # z eye pos in space
                                 EyeTrackerConstants.UNDEFINED, # eye angle in head x
                                 EyeTrackerConstants.UNDEFINED, # eye angle in head y
                                 EyeTrackerConstants.UNDEFINED, # uncalibrated x eye pos
                                 EyeTrackerConstants.UNDEFINED, # uncalibrated y eye pos
                                 left_pupil_measure1,
                                 pupil_measure_type,
                                 EyeTrackerConstants.UNDEFINED,  # pupil measure 2
                                 EyeTrackerConstants.UNDEFINED,  # pupil measure 2 type  
                                 EyeTrackerConstants.UNDEFINED,  # pixels per degree x
                                 EyeTrackerConstants.UNDEFINED,  # pixels per degree y
                                 EyeTrackerConstants.UNDEFINED,  # sample velocity x
                                 EyeTrackerConstants.UNDEFINED,  # sample velocity y
                                 EyeTrackerConstants.UNDEFINED,  # 2D sample velocity
                                 right_gaze_x,
                                 right_gaze_y,
                                 EyeTrackerConstants.UNDEFINED, # gaze z
                                 EyeTrackerConstants.UNDEFINED, # x eye pos in space
                                 EyeTrackerConstants.UNDEFINED, # y eye pos in space
                                 EyeTrackerConstants.UNDEFINED, # z eye pos in space
                                 EyeTrackerConstants.UNDEFINED, # eye angle in head x
                                 EyeTrackerConstants.UNDEFINED, # eye angle in head y
                                 EyeTrackerConstants.UNDEFINED, # uncalibrated x eye pos
                                 EyeTrackerConstants.UNDEFINED, # uncalibrated y eye pos
                                 right_pupil_measure1,
                                 pupil_measure_type,
                                 EyeTrackerConstants.UNDEFINED,  # pupil measure 2
                                 EyeTrackerConstants.UNDEFINED,  # pupil measure 2 type  
                                 EyeTrackerConstants.UNDEFINED,  # pixels per degree x
                                 EyeTrackerConstants.UNDEFINED,  # pixels per degree y
                                 EyeTrackerConstants.UNDEFINED,  # sample velocity x
                                 EyeTrackerConstants.UNDEFINED,  # sample velocity y
                                 EyeTrackerConstants.UNDEFINED,  # 2D sample velocity
                                 status
                                 ]

                    self._latest_sample=binocSample

                    g=[0.0,0.0]                    
                    if right_pupil_measure1>0.0 and left_pupil_measure1>0.0:
                        g=[(left_gaze_x+right_gaze_x)/2.0,(left_gaze_y+right_gaze_y)/2.0]
                    elif left_pupil_measure1>0.0:
                        g=[left_gaze_x,left_gaze_y]
                    elif right_pupil_measure1>0.0:
                        g=[right_gaze_x,right_gaze_y]
                    self._latest_gaze_position=g

                    self._addNativeEventToBuffer(binocSample)

                else: # WTF   
                    print2err("ERROR: EyeGaze reported camers count is invalid: ",self._camera_count)

            # Code below can be reused if fixation event detection is added.
            #
            #                elif isinstance(ne,pylink.EndFixationEvent):
            #                    etype=EventConstants.FIXATION_END
            #
            #                    estatus = ne.getStatus()
            #
            #                    which_eye=ne.getEye()
            #                    if which_eye:
            #                        which_eye=EyeTrackerConstants.RIGHT_EYE
            #                    else:
            #                        which_eye=EyeTrackerConstants.LEFT_EYE
            #
            #                    start_event_time= ne.getStartTime()*DEVICE_TIMEBASE_TO_SEC
            #                    end_event_time = ne.event_timestamp
            #                    event_duration = end_event_time-start_event_time
            #
            #                    fee=[0,
            #                         0,
            #                         Computer._getNextEventID(),
            #                         etype,
            #                         ne.event_timestamp,
            #                         ne.logged_time,
            #                         ne.timestamp,
            #                         confidenceInterval,
            #                         ne.event_delay,
            #                         0,
            #                        which_eye,
            #                        event_duration,
            #                        s_gaze[0],
            #                        s_gaze[1],
            #                        EyeTrackerConstants.UNDEFINED,
            #                        s_href[0],
            #                        s_href[1],
            #                        EyeTrackerConstants.UNDEFINED,
            #                        EyeTrackerConstants.UNDEFINED,
            #                        s_pupilsize,
            #                        EyeTrackerConstants.PUPIL_AREA,
            #                        EyeTrackerConstants.UNDEFINED,
            #                        EyeTrackerConstants.UNDEFINED,
            #                        s_ppd[0],
            #                        s_ppd[1],
            #                        EyeTrackerConstants.UNDEFINED,
            #                        EyeTrackerConstants.UNDEFINED,
            #                        s_vel,
            #                        e_gaze[0],
            #                        e_gaze[1],
            #                        EyeTrackerConstants.UNDEFINED,
            #                        e_href[0],
            #                        e_href[1],
            #                        EyeTrackerConstants.UNDEFINED,
            #                        EyeTrackerConstants.UNDEFINED,
            #                        e_pupilsize,
            #                        EyeTrackerConstants.PUPIL_AREA,
            #                        EyeTrackerConstants.UNDEFINED,
            #                        EyeTrackerConstants.UNDEFINED,
            #                        e_ppd[0],
            #                        e_ppd[1],
            #                        EyeTrackerConstants.UNDEFINED,
            #                        EyeTrackerConstants.UNDEFINED,
            #                        e_vel,
            #                        a_gaze[0],
            #                        a_gaze[1],
            #                        EyeTrackerConstants.UNDEFINED,
            #                        a_href[0],
            #                        a_href[1],
            #                        EyeTrackerConstants.UNDEFINED,
            #                        EyeTrackerConstants.UNDEFINED,
            #                        a_pupilsize,
            #                        EyeTrackerConstants.PUPIL_AREA,
            #                        EyeTrackerConstants.UNDEFINED,
            #                        EyeTrackerConstants.UNDEFINED,
            #                        EyeTrackerConstants.UNDEFINED,
            #                        EyeTrackerConstants.UNDEFINED,
            #                        EyeTrackerConstants.UNDEFINED,
            #                        EyeTrackerConstants.UNDEFINED,
            #                        a_vel,
            #                        EyeTrackerConstants.UNDEFINED,
            #                        EyeTrackerConstants.UNDEFINED,
            #                        peak_vel,
            #                        estatus
            #                        ]
            #                    #EyeTracker._eventArrayLengths['FIXATION_END']=len(fee)
            #                    self._addNativeEventToBuffer(fee)
            #                elif isinstance(ne,pylink.StartFixationEvent):
            #                    etype=EventConstants.FIXATION_START
            #
            #                    which_eye=ne.getEye()
            #                    if which_eye:
            #                        which_eye=EyeTrackerConstants.RIGHT_EYE
            #                    else:
            #                        which_eye=EyeTrackerConstants.LEFT_EYE
            #
            #
            #                    se=[
            #                        0,                                      # exp ID
            #                        0,                                      # sess ID
            #                        Computer._getNextEventID(),              # event ID
            #                        etype,                                  # event type
            #                        ne.event_timestamp,
            #                        ne.logged_time,
            #                        ne.timestamp,
            #                        confidenceInterval,
            #                        ne.event_delay,
            #                        0,
            #                        which_eye,                              # eye
            #                        gaze[0],                                # gaze x
            #                        gaze[1],                                # gaze y
            #                        EyeTrackerConstants.UNDEFINED,                                     # gaze z
            #                        href[0],                                # angle x
            #                        href[1],                                # angle y
            #                        EyeTrackerConstants.UNDEFINED,                                   # raw x
            #                        EyeTrackerConstants.UNDEFINED,                                   # raw y
            #                        pupil_size,                             # pupil area
            #                        EyeTrackerConstants.PUPIL_AREA,                    # pupil measure type 1
            #                        EyeTrackerConstants.UNDEFINED,                                   # pupil measure 2
            #                        EyeTrackerConstants.UNDEFINED,     # pupil measure 2 type
            #                        ppd[0],                                 # ppd x
            #                        ppd[1],                                 # ppd y
            #                        EyeTrackerConstants.UNDEFINED,                                    # velocity x
            #                        EyeTrackerConstants.UNDEFINED,                                    # velocity y
            #                       velocity,                                # velocity xy
            #                       estatus                                  # status
            #                        ]
            #                    self._addNativeEventToBuffer(se)
        except Exception:
            print2err("ERROR occurred during poll:")
            printExceptionDetailsToStdErr()
                
def _eyeTrackerToDisplayCoords(self,eyetracker_point):
        """
        """
        try:
            cl,ct,cr,cb=self._display_device.getCoordBounds()
            cw,ch=cr-cl,ct-cb
            
            dl,dt,dr,db=self._display_device.getBounds()
            dw,dh=dr-dl,db-dt

            gxn,gyn=eyetracker_point[0]/dw,eyetracker_point[1]/dh                        
            return cl+cw*gxn,cb+ch*(1.0-gyn)   
        except Exception:
            print2err("ERROR occurred during _eyeTrackerToDisplayCoords:")
            printExceptionDetailsToStdErr()          
        
        
def _displayToEyeTrackerCoords(self,display_x,display_y):
        """
        """
        try:                        
            cl,ct,cr,cb=self._display_device.getCoordBounds()
            cw,ch=cr-cl,ct-cb
            
            dl,dt,dr,db=self._display_device.getBounds()
            dw,dh=dr-dl,db-dt
            
            cxn,cyn=(display_x+cw/2)/cw , 1.0-(display_y-ch/2)/ch       
            return cxn*dw,  cyn*dh          
           
        except Exception:
            print2err("ERROR occurred during _displayToEyeTrackerCoords:")
            printExceptionDetailsToStdErr()          
       