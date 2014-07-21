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


from ...... import printExceptionDetailsToStdErr, print2err
from ......constants import EventConstants, EyeTrackerConstants
from ..... import Computer
from .... import EyeTrackerDevice
from ....eye_events import *

import pEyeGaze

import sys
from ctypes import byref, sizeof

def localfunc():
    pass

class EyeTracker(EyeTrackerDevice):
    """The EyeGaze EyeTracker class implements support of the LC Technologies
    eye tracker lines for the ioHub Common Eye Tracker Interface. 
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
        trackerTime returns the current time reported by the 
        eye tracker device. EyeGaze reports tracker time in usec. 
        
        Args:
            None
        
        Return:
            float: The eye tracker hardware's reported current time.
        """
        return pEyeGaze.lct_TimerRead(None)-(pEyeGaze.EgGetApplicationStartTimeSec()/self.DEVICE_TIMEBASE_TO_SEC)
        
    def trackerSec(self):
        """
        trackerSec takes the time received by the EyeTracker.trackerTime() method
        and returns the time in sec.usec-msec format.
        
        Args:
            None
        
        Return:
            float: The eye tracker hardware's reported current time in sec.msec-usec format.        
        """
        return (pEyeGaze.lct_TimerRead(None)*self.DEVICE_TIMEBASE_TO_SEC) - pEyeGaze.EgGetApplicationStartTimeSec()

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
        enableEventReporting(bool) method to start and stop eye data recording.

        Args:
            enable (bool): True = enable the connection, False = disable the connection.

        Return:
            bool: indicates the current connection state to the eye tracking hardware.
            
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
                return print2err("INVALID_METHOD_ARGUMENT_VALUE. ","EyeTracker.setConnectionState: ",enable)
        except Exception,e:
                return printExceptionDetailsToStdErr()#("IOHUB_DEVICE_EXCEPTION",error_message="An unhandled exception occurred on the ioHub Server Process.",method="EyeTracker.setConnectionState",arguement='enable', value=enable, error=e)            
            
    def isConnected(self):
        """
        isConnected returns whether the ioHub EyeTracker Device is connected to the
        eye tracker hardware or not. An eye tracker must be connected to the ioHub 
        for any of the Common Eye Tracker Interface functionality to work.
        
        Args:
            None
            
        Return:
            bool:  True = the eye tracking hardware is connected. False otherwise.
        """
        try:
            return self._eyegaze_control != None
        except Exception, e:
            return printExceptionDetailsToStdErr()#("IOHUB_DEVICE_EXCEPTION",
                    #error_message="An unhandled exception occurred on the ioHub Server Process.",
                    #method="EyeTracker.isConnected", error=e)            
            
    def sendCommand(self, key, value=None):
        """
        sendCommand accepts the following two comman key values:
            
        * get_control_status : returns a dictionary with all control structure attributes and current values.
        * get_config: returns a dictionary in the form {'iNVis':egConfig.iNVis, 'bEyefollower': egConfig.bEyefollower}


        Args:
            key: either 'get_control_status' or 'get_config'
            
        Returns:
            dict: result of the command request.
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
            return printExceptionDetailsToStdErr()#("IOHUB_DEVICE_EXCEPTION",
                    #error_message="An unhandled exception occurred on the ioHub Server Process.",
                    #method="EyeTracker.sendCommand", key=key,value=value, error=e)            
        
    def sendMessage(self,message_contents,time_offset=None):
        """
        sendMessage is not supported by this implementation of the Common Eye Tracker Interface.
        """
        try:
            if self._eyegaze_control:
                print2err("EyeGaze sendMessage not yet implemented")
                return EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED
        except Exception, e:
            return printExceptionDetailsToStdErr()#("IOHUB_DEVICE_EXCEPTION",
                    #error_message="An unhandled exception occurred on the ioHub Server Process.",
                    #method="EyeTracker.sendMessage", message_contents=message_contents,time_offset=time_offset, error=e)            

    def runSetupProcedure(self,starting_state=EyeTrackerConstants.DEFAULT_SETUP_PROCEDURE):
        """
        The runSetupProcedure allows the eye tracker interface to perform 
        such things as participant placement validation, camera setup, calibration,
        and validation type activities.
        
        For the EyeGaze implementation, the DEFAULT_SETUP_PROCEDURE starting state is 
        supported, which launches the external EyeGaze calibrate.exe calibration routine.
        When the calibration program completes, control is returned to the PsychoPy Process.
        
        Args:
            None
            
        Returns:
            None
        """                    
        try:
            #calibration_properties=self.getConfiguration().get('calibration',None)

            if self._eyegaze_control and self.isRecordingEnabled() is False:                
                # pEyeGaze         
                # when using the external calibrate.exe to 
                # run calibration, need todisconnect from the tracker
                # and reconnect after calibration is done.
                self.setConnectionState(False)
                
                import subprocess,gevent,os
                #p = subprocess.Popen(('calibrate.exe', ''), env={"PATH": "/usr/bin"})
                #from psychopy.iohub import module_directory
                #runthis=os.path.join(module_directory(localfunc),'calibrate_lc.bat')
                #runthis=os.path.join(module_directory(localfunc),'calibrate_lc.bat')
                org_cwd = os.getcwdu()
                print2err("==========")
                print2err("CWD Prior to calibrate.exe launch: ",org_cwd)
                p = subprocess.Popen((u'calibrate.exe', u''), cwd = u'c:\\eyegaze\\' )
                while p.poll() is None:
                    gevent.sleep(0.05)
                self.setConnectionState(True)
                new_cwd=os.getcwdu()
                print2err("CWD after calibrate.exe: ",new_cwd)
                print2err("==========")


          
#            circle_attributes=calibration_properties.get('circle_attributes')
#            targetForegroundColor=circle_attributes.get('outer_color') # [r,g,b] of outer circle of targets
#            targetBackgroundColor=circle_attributes.get('inner_color') # [r,g,b] of inner circle of targets
#            screenColor=calibration_properties.get('screen_background_color')                     # [r,g,b] of screen
#            targetOuterDiameter=circle_attributes.get('outer_diameter')     # diameter of outer target circle (in px)
#            targetInnerDiameter=circle_attributes.get('inner_diameter')     # diameter of inner target circle (in px)
            
        except Exception,e:
            return printExceptionDetailsToStdErr()#("IOHUB_DEVICE_EXCEPTION",
                    #error_message="An unhandled exception occurred on the ioHub Server Process.",
                    #method="EyeTracker.runSetupProcedure", 
                    #starting_state=starting_state,
                    #error=e)            

    def isRecordingEnabled(self):
        """
        The isRecordingEnabled method indicates if the eye tracker device is currently
        recording data or not. 
   
        Args:
           None
  
        Return:
            bool: True == the device is recording data; False == Recording is not occurring
        """
        try:
            return self._eyegaze_control is not None and self._eyegaze_control.bTrackingActive in [1,True]
        except Exception, e:
            return printExceptionDetailsToStdErr()#("IOHUB_DEVICE_EXCEPTION",
                    #error_message="An unhandled exception occurred on the ioHub Server Process.",
                    #method="EyeTracker.isRecordingEnabled", error=e)

    def enableEventReporting(self,enabled=True):
        """
        Device type independent method equal to the EyeTracker.setRecordingState method.
        Please see setRecordingState for details.
        """
        try:
            if self._eyegaze_control:
                enabled=self.setRecordingState(self,enabled)
            return self.setRecordingState(enabled)
        except Exception, e:
            return printExceptionDetailsToStdErr()#("IOHUB_DEVICE_EXCEPTION",
                    #error_message="An unhandled exception occurred on the ioHub Server Process.",
                    #method="EyeTracker.enableEventReporting", error=e)            

    def setRecordingState(self,recording):
        """
        The setRecordingState method is used to start or stop the recording 
        and transmition of eye data from the eye tracking device.
        
        Args:
            recording (bool): if True, the eye tracker will start recordng data.; false = stop recording data.
           
        Return:
            bool: the current recording state of the eye tracking device
        """
        try:
            if not isinstance(recording,bool):
                return printExceptionDetailsToStdErr()#("INVALID_METHOD_ARGUMENT_VALUE",
                    #error_message="The recording arguement value provided is not a boolean.",
                    #method="EyeTracker.setRecordingState",arguement='recording', value=recording)
             
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
            return printExceptionDetailsToStdErr()#("IOHUB_DEVICE_EXCEPTION",
                    #error_message="An unhandled exception occurred on the ioHub Server Process.",
                    #method="EyeTracker.setRecordingState", error=e)            

    def getLastSample(self):
        """
        The getLastSample method returns the most recent ioHub sample event available.
        The eye tracker must be recording data for a sample event to be returned, otherwise None is returned.

        Args: 
            None

        Returns:
            None: If the eye tracker is not currently recording data.

            EyeSample: If the eye tracker is recording in a monocular tracking mode, the latest sample event of this event type is returned.

            BinocularEyeSample:  If the eye tracker is recording in a binocular tracking mode, the latest sample event of this event type is returned.
        """

        try:
            return self._latest_sample
        except Exception, e:
            return printExceptionDetailsToStdErr()#("IOHUB_DEVICE_EXCEPTION",
                    #error_message="An unhandled exception occurred on the ioHub Server Process.",
                    #method="EyeTracker.getLastSample", error=e)            

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
            None: If the eye tracker is not currently recording data or no eye samples have been received.

            tuple: Latest (gaze_x,gaze_y) position of the eye(s)
        """
        try:
            return self._latest_gaze_position
        except Exception, e:
            return printExceptionDetailsToStdErr()#("IOHUB_DEVICE_EXCEPTION",
                    #error_message="An unhandled exception occurred on the ioHub Server Process.",
                    #method="EyeTracker.getLastGazePosition", error=e)             
    
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
                event_delay=current_tracker_time-device_event_timestamp
                
                iohub_time=logged_time-event_delay

                pupil_measure1_type = EyeTrackerConstants.PUPIL_RADIUS_MM
                
                if self._camera_count == 1: #monocular
                    event_type=EventConstants.MONOCULAR_EYE_SAMPLE
                    eye = EyeTrackerConstants.UNKNOWN_MONOCULAR
                    gaze_x, gaze_y = sample_data0.iIGaze, sample_data0.iJGaze
                    pupil_measure1 = sample_data0.fPupilRadiusMm
                    status=0
                    if gaze_x != 0.0 and gaze_y != 0.0 and pupil_measure1 > 0.0:                   
                        gaze_x, gaze_y = self._eyeTrackerToDisplayCoords((gaze_x, gaze_y))
                    else:
                        status=2
                        gaze_x, gaze_y = EyeTrackerConstants.UNDEFINED, EyeTrackerConstants.UNDEFINED
                        pupil_measure1=0
                    #status = int(sample_data0.bGazeVectorFound)

                    monoSample=[
                                0,                            # experiment_id (filled in by ioHub)
                                0,                            # session_id (filled in by ioHub)
                                0, #device id (always 0 now) 
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
                    
                    if status==0:            
                        self._latest_gaze_position=gaze_x,gaze_y
                    else:
                        self._latest_gaze_position=None
                    self._latest_sample=monoSample
                    self._addNativeEventToBuffer(monoSample)


                elif self._camera_count == 2: #binocular
                    event_type=EventConstants.BINOCULAR_EYE_SAMPLE

                    sample_data1=self._eyegaze_control.pstEgData[1]
                    sample_data4=self._eyegaze_control.pstEgData[4]
                    
                    status=0

                    left_pupil_measure1 = sample_data4.fPupilRadiusMm
                    left_gaze_x, left_gaze_y = sample_data4.iIGaze,sample_data4.iJGaze     
                    if left_gaze_x != 0.0 and left_gaze_y != 0.0 and left_pupil_measure1 > 0.0:
                        left_gaze_x, left_gaze_y=self._eyeTrackerToDisplayCoords((left_gaze_x, left_gaze_y))
                    else:
                        status=20
                        left_pupil_measure1=0
                        left_gaze_x=EyeTrackerConstants.UNDEFINED
                        left_gaze_y=EyeTrackerConstants.UNDEFINED
                        
                    right_gaze_x, right_gaze_y = sample_data1.iIGaze,sample_data1.iJGaze                                                            
                    right_pupil_measure1 = sample_data1.fPupilRadiusMm                    
                    if right_gaze_x != 0.0 and right_gaze_y != 0.0 and left_pupil_measure1 > 0.0:
                        right_gaze_x, right_gaze_y=self._eyeTrackerToDisplayCoords((right_gaze_x, right_gaze_y))
                    else:
                        status+=2
                        right_pupil_measure1=0
                        right_gaze_x=EyeTrackerConstants.UNDEFINED
                        right_gaze_y=EyeTrackerConstants.UNDEFINED

                    #status = int(sample_data4.bGazeVectorFound*2+sample_data1.bGazeVectorFound)
                    binocSample=[
                                 0,                            # experiment_id (filled in by ioHub)
                                 0,                            # session_id (filled in by ioHub)
                                 0, #device id (always 0 now) 
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
                                 pupil_measure1_type,
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
       