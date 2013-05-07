"""
ioHub
Common Eye Tracker Interface
.. file: ioHub/devices/eyetracker/hw/smi/iViewX/eyetracker.py

Copyright (C) 2012-2013 ???????, iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com>
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

import sys
import copy


from ...... import print2err, convertCamelToSnake, createErrorResult
from ......constants import EventConstants, EyeTrackerConstants
from ..... import Computer
from .... import EyeTrackerDevice
from ....eye_events import *

import pyViewX
from ctypes import byref, c_longlong ,c_int

import gevent

class EyeTracker(EyeTrackerDevice):
    """
    The SMI iViewX implementation of the Common Eye Tracker Interface 
    can be used by providing the following EyeTracker path as the device
    class in the iohub_config.yaml device settings file:
        
        eyetracker.hw.smi.iviewx.EyeTracker
        
    See the configuration options section of the iViewX Common Eye Tracker 
    Interface documentation for a full description and listing of all 
    valid configuration settings for this device.
    """
    # >>> Overwritten class attributes
    DEVICE_TIMEBASE_TO_SEC=0.000001
    
    # The iViewX currently supports a subset of all the eye tracker events listed
    # below, but due to an outstanding bug in the ioHUb device interface, all event types 
    # possible for the given device class must be listed in the class definition.
    EVENT_CLASS_NAMES=['MonocularEyeSampleEvent','BinocularEyeSampleEvent','FixationStartEvent',
                         'FixationEndEvent', 'SaccadeStartEvent', 'SaccadeEndEvent',
                         'BlinkStartEvent', 'BlinkEndEvent']

    __slots__=['_api_pc_ip','_api_pc_port','_et_pc_ip','_et_pc_port',
               '_enable_data_filter','_ioKeyboard','_kbEventQueue','_last_setup_result']
    # <<<

    def __init__(self, *args,**kwargs):
        """
        """

        EyeTrackerDevice.__init__(self,*args,**kwargs)
        try:             
            self._ioKeyboard=None
            
            ####
            # Get network config (used in setConnectionState(True).
            ####
            iviewx_network_config=self.getConfiguration().get('network_settings')
            self._api_pc_ip=iviewx_network_config['send_ip_address']
            self._api_pc_port=iviewx_network_config['send_port']
            self._et_pc_ip=iviewx_network_config['receive_ip_address']
            self._et_pc_port=iviewx_network_config['receive_port']

            ####
            # Connect to the iViewX.
            ####
            self.setConnectionState(True)

            ####
            # Callback sample notification support.
            # Causes python to sig term after 1 - 5 mointes recording. 
            # Use polling method instead!
            ####
            #self._handle_sample_callback=pyViewX.pDLLSetSample(self._handleNativeEvent)            
            #pyViewX.SetSampleCallback(self._handle_sample_callback)
                        
            ####
            # Set the filtering level......
            ####            
            filter_type,filter_level=self._runtime_settings['sample_filtering'].items()[0]
            if filter_type == 'FILTER_ALL':
                level_int=EyeTrackerConstants.getID(filter_level)                
                if level_int==0:
                    pyViewX.DisableGazeDataFilter()
                elif level_int <= EyeTrackerConstants.FILTER_ALL:
                    pyViewX.EnableGazeDataFilter()
                else:
                    print2err("Warning: Unsupported iViewX sample filter level value: ",filter_level,"=",level_int)
            else:
                    print2err("Warning: Unsupported iViewX sample filter type: ",filter_type,". Only FILTER_ALL is supported.")
                
            ####
            # Native file saving...
            ####            
            #print2err("NOTE: Native file saving for the iViewX has not yet been implemented.") 
            
            ####
            # Get the iViewX device's system info, 
            # and update appropriate attributes.            
            ####
            sys_info=self._TrackerSystemInfo()
            if sys_info != EyeTrackerConstants.EYETRACKER_ERROR:
                sampling_rate=sys_info['sampling_rate']
                eyetracking_engine_version=sys_info['eyetracking_engine_version']
                client_sdk_version=sys_info['client_sdk_version']
                model_name=sys_info['model_name']
                
                self.software_version='Client SDK: {0} ; Tracker Engine: {1}'.format(client_sdk_version,eyetracking_engine_version)
                self.getConfiguration()['software_version']=self.software_version
                self.getConfiguration()['model_name']=model_name
                self.model_name=model_name
                
                ####
                # Set sampling rate CHECK ONLY.....
                ####
                requested_sampling_rate=self._runtime_settings['sampling_rate']
                if requested_sampling_rate != sampling_rate:
                    print2err("WARNING: iViewX requested frame rate of {0} != current rate of {1}:".format(requested_sampling_rate,sampling_rate))
                    
                self._runtime_settings['sampling_rate']=sampling_rate
            
            self._last_setup_result=EyeTrackerConstants.EYETRACKER_OK
        except:
            print2err(" ---- Error during EyeLink EyeTracker Initialization ---- ")
            printExceptionDetailsToStdErr()
            print2err(" ---- Error during EyeLink EyeTracker Initialization ---- ")
                    
    def trackerTime(self):
        """
        trackerTime returns the current iViewX Application or Server time in 
        usec format as a long integer.        
        """
        tracker_time=c_longlong(0)
        r=pyViewX.GetCurrentTimestamp(byref(tracker_time))
        if r == pyViewX.RET_SUCCESS:    
            return tracker_time.value
        print2err("iViewX trackerTime FAILED: error: {0} timeval: {1}".format(r,tracker_time))            
        return EyeTrackerConstants.EYETRACKER_ERROR

    def trackerSec(self):
        """
        trackerSec returns the current iViewX Application or Server time in 
        sec.msec-usec format.
        """
        tracker_time=c_longlong(0)
        r=pyViewX.GetCurrentTimestamp(byref(tracker_time))
        if r == pyViewX.RET_SUCCESS:    
            return tracker_time.value*self.DEVICE_TIMEBASE_TO_SEC
        print2err("iViewX trackerSec FAILED: error: {0} timeval: {1}".format(r,tracker_time))            
        return EyeTrackerConstants.EYETRACKER_ERROR

    def isConnected(self):
        """
        isConnected indicates if there is an active connection between the ioHub
        Server and the eye tracking device.

        Note that when the SMI iViewX EyeTracker class is created when the ioHub server starts, 
        a connection is automatically created with the eye tracking device.

        The ioHub must be connected to the eye tracker device for it to be able to receive
        events from the eye tracking system. Eye tracking events are received when 
        isConnected() == True and when isRecordingEnabled() == True.
        """
        try:
            r=pyViewX.IsConnected()
            if r == pyViewX.RET_SUCCESS:
                connected=True
            elif r == pyViewX.ERR_NOT_CONNECTED:
                connected=False
            else:
                print2err("iViewX isConnected() returned unexpected value {0}".format(r))
                return EyeTrackerConstants.EYETRACKER_ERROR
            return connected            
        except Exception, e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.isConnected", error=e)            

    def setConnectionState(self,enable):
        """
        setConnectionState connects the ioHub Server to the SMI iViewX device if 
        the enable arguement is True, otherwise an open connection is closed with
        the device. Calling this method multiple times with the same value has no effect.
        
        Note that when the SMI iViewX EyeTracker class is created when the ioHub server starts, 
        a connection is automatically created with the eye tracking device.
        
        If the eye tracker is currently recording eye data and sending it to the
        ioHub server, the recording will be stopped prior to closing the connection.
        """
        try:
            if enable is True or enable is False:
                if enable is True and not self.isConnected():
                    r = pyViewX.Connect(pyViewX.StringBuffer(self._api_pc_ip,16),
                                        self._api_pc_port,
                                        pyViewX.StringBuffer(self._et_pc_ip,16),
                                        self._et_pc_port)
                    if r != pyViewX.RET_SUCCESS:
                        print2err("iViewX ERROR connecting to tracker: {0}".format(r))
                        sys.exit(0)
                    return self.isConnected()
                elif enable is False and self.isConnected():
                    if self.isRecordingEnabled():
                        self.setRecordingState(False)
                    r = pyViewX.Disconnect()
                    if r != pyViewX.RET_SUCCESS:
                        print2err("iViewX ERROR disconnecting from tracker: {0}".format(r))
                    return self.isConnected()
            else:
                return createErrorResult("INVALID_METHOD_ARGUMENT_VALUE",error_message="The enable arguement value provided is not recognized",method="EyeTracker.setConnectionState",arguement='enable', value=enable)            
        except Exception,e:
                return createErrorResult("IOHUB_DEVICE_EXCEPTION",error_message="An unhandled exception occurred on the ioHub Server Process.",method="EyeTracker.setConnectionState",arguement='enable', value=enable, error=e)            
            
    def sendMessage(self,message_contents,time_offset=None):
        """
        The sendMessage method is currently not supported by the SMI iViewX 
        implementation of the Common Eye Tracker Interface. Once native data file
        saving is implemented for the iViewX, this method will become available.
        """
        try:   
            # Possible return codes:
            #
            # RET_SUCCESS - intended functionality has been fulfilled
            # ERR_NOT_CONNECTED - no connection established
            r=pyViewX.SendImageMessage(pyViewX.StringBuffer(message_contents,256))
            if r != pyViewX.RET_SUCCESS:
                print2err("iViewX ERROR {0} when sendMessage to tracker: {1}".format(r,message_contents))
                return EyeTrackerConstants.EYETRACKER_ERROR           
            return EyeTrackerConstants.EYETRACKER_OK     

        except Exception, e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.sendMessage", message_contents=message_contents,time_offset=time_offset, error=e)            

    def sendCommand(self, key, value=None):
        """
        The sendCommand method is currently not supported by the SMI iViewX 
        implementation of the Common Eye Tracker Interface.
        """

#        TODO: Add support using the sendCommand method for:
#            SetEventDetectionParameter
#            SetConnectionTimeout
#            
#        * Also see page 28 of iViewX SDK Manual.pfd, which lists a set
#          of defines that can be used with SetTrackingParameter(),
#          TODO: Determine which of these are safe to expose via this method:
#              
#              ET_PARAM_EYE_LEFT 0
#              ET_PARAM_EYE_RIGHT 1
#              ET_PARAM_PUPIL_THRESHOLD 0
#              ET_PARAM_REFLEX_THRESHOLD 1
#              ET_PARAM_SHOW_AOI 2
#              ET_PARAM_SHOW_CONTOUR 3
#              ET_PARAM_SHOW_PUPIL 4
#              ET_PARAM_SHOW_REFLEX 5
#              ET_PARAM_DYNAMIC_THRESHOLD 6
#              ET_PARAM_PUPIL_AREA 11
#              ET_PARAM_PUPIL_PERIMETER 12
#              ET_PARAM_PUPIL_DENSITY 13
#              ET_PARAM_REFLEX_PERIMETER 14
#              ET_PARAM_RELFEX_PUPIL_DISTANCE 15
#              ET_PARAM_MONOCULAR 16
#              ET_PARAM_SMARTBINOCULAR 17

        print2err("iViewX sendCommand is not implemented yet.")
        return EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED

    def runSetupProcedure(self,starting_state=EyeTrackerConstants.DEFAULT_SETUP_PROCEDURE):
        """
        The SMI iViewX implementation of the runSetupProcedure supports the following 
        starting_state values:
            
            #. DEFAULT_SETUP_PROCEDURE: This (default) mode starts by showing a dialog with the various options available during user setup.
            #. CALIBRATION_STATE: The eye tracker will immediately preform a calibration and then return to the experiment script.
            #. VALIDATION_STATE: The eye tracker will immediately preform a validation and then return to the experiment script. The return result is a dict containing the validation results.
            #. TRACKER_FEEDBACK_STATE: The eye tracker will display the eye image window and tracker graphics if either has been enabled in the device config, and then return to the experiment script.

        """
        if self.isConnected() is False:
            return EyeTrackerConstants.EYETRACKER_ERROR
            
        try:       
            IMPLEMENTATION_SUPPORTED_STATES=[EyeTrackerConstants.DEFAULT_SETUP_PROCEDURE,
                                             EyeTrackerConstants.CALIBRATION_STATE,
                                             EyeTrackerConstants.VALIDATION_STATE,
                                             EyeTrackerConstants.TRACKER_FEEDBACK_STATE]            

            if isinstance(starting_state,basestring):
                starting_state=EyeTrackerConstants.getID(starting_state)
                        
            self._registerKeyboardMonitor()

            self._last_setup_result=EyeTrackerConstants.EYETRACKER_OK
                        
            if starting_state not in IMPLEMENTATION_SUPPORTED_STATES:
                self._last_setup_result=EyeTrackerConstants.EYETRACKER_RECEIVED_INVALID_INPUT
            elif starting_state == EyeTrackerConstants.DEFAULT_SETUP_PROCEDURE:                                
                self._showSetupKeyOptionsDialog()                    
                next_state=None
                key_mapping={'C':self._calibrate,
                             'V':self._validate,
                             'T':self._showTrackingMonitor,
                             'E':self._showEyeImageMonitor,
                             'ESCAPE':'CONTINUE',
                             'F1':self._showSetupKeyOptionsDialog}
                while 1:
                    if next_state is None:                    
                        next_state=self._getKeyboardPress(key_mapping)
                    
                    if callable(next_state):
                        next_state()
                        next_state=None                            
                                            
                    elif next_state == 'CONTINUE':
                        break
                       
            elif starting_state == EyeTrackerConstants.CALIBRATION_STATE:
                self._calibrate()
            elif starting_state == EyeTrackerConstants.VALIDATION_STATE:
                self._validate()
            elif starting_state == EyeTrackerConstants.TRACKER_FEEDBACK_STATE:
                self._showEyeImageMonitor()
                self._showTrackingMonitor()
            else:    
                self._last_setup_result=EyeTrackerConstants.EYETRACKER_RECEIVED_INVALID_INPUT
                
            self._unregisterKeyboardMonitor()
            return self._last_setup_result
        except Exception,e:
            self._unregisterKeyboardMonitor()
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.runSetupProcedure", 
                    starting_state=starting_state,
                    error=e)   

    def _showSimpleWin32Dialog(self,message,caption):
        import win32gui
        win32gui.MessageBox(None,message,caption,0)
                    
    def _showSetupKeyOptionsDialog(self):
        msg_text="The following Keyboard Commands will be available during User Setup:\n"
        msg_text+="\n\tE : Display Eye Image Window.\n"
        msg_text+="\tT : Display Tracking Monitor Window.\n"
        msg_text+="\tC : Start Calibration Routine.\n"
        msg_text+="\tV : Start Validation Routine.\n"
        msg_text+="\tESCAPE : Exit the Setup Procedure.\n"
        msg_text+="\tF1 : Show this Dialog.\n"  
        msg_text+="\nPress OK to begin"
        
        self._showSimpleWin32Dialog(msg_text,"Common Eye Tracker Interface - iViewX Calibration")                
        
    def _showEyeImageMonitor(self):

        # pyViewX.ShowEyeImageMonitor return codes:
        #
        # RET_SUCCESS - intended functionality has been fulfilled
        # ERR_NOT_CONNECTED - no connection established
        # ERR_WRONG_DEVICE - eye tracking device required for 
        #                    this function is not connected
        result=pyViewX.ShowEyeImageMonitor()
        
        if result == pyViewX.ERR_NOT_CONNECTED:
            self._showSimpleWin32Dialog("Eye Image Monitor can not be Displayed. An iViewX System is not Connected to the ioHub.",
                                  "Common Eye Tracker Interface - ERROR")
            self._last_setup_result=EyeTrackerConstants.EYETRACKER_NOT_CONNECTED
        if result == pyViewX.ERR_WRONG_DEVICE:
            self._showSimpleWin32Dialog("Eye Image Monitor can not be Displayed. The iViewX Model being used does not support this Operation.",
                                  "Common Eye Tracker Interface - ERROR")
            self._last_setup_result=EyeTrackerConstants.EYETRACKER_MODEL_NOT_SUPPORTED


    def _showTrackingMonitor(self):
        # pyViewX.ShowTrackingMonitor return codes:
        #
        # RET_SUCCESS - intended functionality has been fulfilled
        # ERR_NOT_CONNECTED - no connection established
        # ERR_WRONG_DEVICE - eye tracking device required for
        #                    this function is not connected
        result=pyViewX.ShowTrackingMonitor()
        # TODO: Handle possible return codes
        #ioHub.print2err('ShowTrackingMonitor result: ',result)
        if result == pyViewX.ERR_NOT_CONNECTED:
            self._showSimpleWin32Dialog("Tracking Monitor can not be Displayed. An iViewX System is not Connected to the ioHub.",
                                  "Common Eye Tracker Interface - ERROR")
            self._last_setup_result=EyeTrackerConstants.EYETRACKER_NOT_CONNECTED
        if result == pyViewX.ERR_WRONG_DEVICE:
            self._showSimpleWin32Dialog("Tracking Monitor can not be Displayed. The iViewX Model being used does not support this Operation.",
                                  "Common Eye Tracker Interface - ERROR")
            self._last_setup_result=EyeTrackerConstants.EYETRACKER_MODEL_NOT_SUPPORTED
        
    def _calibrate(self):
        calibrationData=pyViewX.CalibrationStruct()
        _iViewConfigMappings._createCalibrationStruct(self,calibrationData)
        
        # pyViewX.SetupCalibration return codes:
        #
        # RET_SUCCESS - intended functionality has been fulfilled
        # ERR_WRONG_PARAMETER - parameter out of range
        # ERR_WRONG_DEVICE - eye tracking device required for this
        #                    function is not connected
        # ERR_WRONG_CALIBRATION_METHOD - eye tracking device required
        #                                for this calibration method 
        #                                is not connected

        result = pyViewX.SetupCalibration(byref(calibrationData))

        if result == pyViewX.ERR_WRONG_PARAMETER:
            self._showSimpleWin32Dialog("Calibration Could not be Performed. An invalid setting was passed to the procedure.",
                                  "Common Eye Tracker Interface - ERROR")
            self._last_setup_result=EyeTrackerConstants.EYETRACKER_RECEIVED_INVALID_INPUT
            
        elif result == pyViewX.ERR_WRONG_DEVICE:
            self._showSimpleWin32Dialog("Calibration Could not be Performed. The iViewX Model being used does not support this Operation.",
                                  "Common Eye Tracker Interface - ERROR")
            self._last_setup_result=EyeTrackerConstants.EYETRACKER_MODEL_NOT_SUPPORTED

        elif result == pyViewX.ERR_WRONG_CALIBRATION_METHOD:
            self._showSimpleWin32Dialog("Calibration Could not be Performed. The Calibration Type being used is not Supported by the attached iViewX Model.",
                                  "Common Eye Tracker Interface - ERROR")
            self._last_setup_result=EyeTrackerConstants.EYETRACKER_MODEL_NOT_SUPPORTED

        
        # pyViewX.Calibrate return codes:
        #
        # RET_SUCCESS - intended functionality has been fulfilled
        # RET_CALIBRATION_ABORTED - Calibration was aborted
        # ERR_NOT_CONNECTED - no connection established
        # ERR_WRONG_DEVICE - eye tracking device required for 
        #                    this function is not connected
        # ERR_WRONG_CALIBRATION_METHOD - eye tracking device required
        #                    for this calibration method is not connected            
        result = pyViewX.Calibrate()  

        if result == pyViewX.ERR_NOT_CONNECTED:
            self._showSimpleWin32Dialog("Tracking Monitor can not be Displayed. An iViewX System is not Connected to the ioHub.",
                                  "Common Eye Tracker Interface - ERROR")
            self._last_setup_result=EyeTrackerConstants.EYETRACKER_NOT_CONNECTED
        elif result == pyViewX.RET_CALIBRATION_ABORTED:
            self._showSimpleWin32Dialog("The Calibration Procedure was Aborted.",
                                  "Common Eye Tracker Interface - WARNING")
            self._last_setup_result=EyeTrackerConstants.EYETRACKER_SETUP_ABORTED
        elif result == pyViewX.ERR_WRONG_DEVICE:
            self._showSimpleWin32Dialog("Calibration Could not be Performed. The iViewX Model being used does not support this Operation.",
                                  "Common Eye Tracker Interface - ERROR")
            self._last_setup_result=EyeTrackerConstants.EYETRACKER_MODEL_NOT_SUPPORTED
        elif result == pyViewX.ERR_WRONG_CALIBRATION_METHOD:
            self._showSimpleWin32Dialog("Calibration Could not be Performed. The Calibration Type being used is not Supported by the attached iViewX Model.",
                                  "Common Eye Tracker Interface - ERROR")
            self._last_setup_result=EyeTrackerConstants.EYETRACKER_MODEL_NOT_SUPPORTED
        else:
            self._last_setup_result=EyeTrackerConstants.EYETRACKER_OK
            self._showSimpleWin32Dialog("Calibration Completed. Press 'V' to Validate, ESCAPE to exit Setup, F1 to view all Options.",
                                  "Common Eye Tracker Interface")
            
    def _validate(self):
        # pyViewX.Validate return codes:
        #
        # RET_SUCCESS - intended functionality has been fulfilled
        # ERR_NOT_CONNECTED - no connection established
        # ERR_NOT_CALIBRATED - system is not calibrated
        # ERR_WRONG_DEVICE - eye tracking device required for this
        #                    function is not connected               
        result=pyViewX.Validate()

        if result == pyViewX.ERR_NOT_CONNECTED:
            self._showSimpleWin32Dialog("Validation Procedure Failed. An iViewX System is not Connected to the ioHub.",
                                  "Common Eye Tracker Interface - ERROR")
            self._last_setup_result=EyeTrackerConstants.EYETRACKER_NOT_CONNECTED
        elif result == pyViewX.ERR_NOT_CALIBRATED:
            self._showSimpleWin32Dialog("Validation can only be Performed after a Successful Calibration.",
                                  "Common Eye Tracker Interface - WARNING")
            self._last_setup_result=EyeTrackerConstants.EYETRACKER_VALIDATION_ERROR
        elif result == pyViewX.ERR_WRONG_DEVICE:
            self._showSimpleWin32Dialog("Validation Procedure Failed. The iViewX Model being used does not support this Operation.",
                                  "Common Eye Tracker Interface - ERROR")
            self._last_setup_result=EyeTrackerConstants.EYETRACKER_MODEL_NOT_SUPPORTED
        else:
            self._last_setup_result=EyeTrackerConstants.EYETRACKER_OK
            
            show_validation_results= self.getConfiguration()['calibration'].get('show_validation_accuracy_window',False)
    
            # pyViewX.GetAccuracy return codes:
            #
            # RET_SUCCESS - intended functionality has been fulfilled
            # RET_NO_VALID_DATA - No new data available
            # ERR_NOT_CONNECTED - no connection established
            # ERR_NOT_CALIBRATED - system is not calibrated
            # ERR_NOT_VALIDATED - system is not validated
            # ERR_WRONG_PARAMETER - parameter out of range
            accuracy_results=pyViewX.AccuracyStruct()
            result = pyViewX.GetAccuracy(byref(accuracy_results),show_validation_results)
    
            if result == pyViewX.ERR_NOT_CONNECTED:
                self._showSimpleWin32Dialog("Validation Procedure Failed. An iViewX System is not Connected to the ioHub.",
                                      "Common Eye Tracker Interface - ERROR")
                self._last_setup_result=EyeTrackerConstants.EYETRACKER_NOT_CONNECTED
            elif result == pyViewX.ERR_NOT_CALIBRATED:
                self._showSimpleWin32Dialog("Validation can only be Performed after a Successful Calibration.",
                                      "Common Eye Tracker Interface - WARNING")
                self._last_setup_result=EyeTrackerConstants.EYETRACKER_VALIDATION_ERROR
            elif result == pyViewX.ERR_NOT_VALIDATED:
                self._showSimpleWin32Dialog("Validation Accuracy Calculation Failed. The System has not been Validated.",
                                      "Common Eye Tracker Interface - ERROR")
                self._last_setup_result=EyeTrackerConstants.EYETRACKER_VALIDATION_ERROR
            elif result == pyViewX.ERR_WRONG_PARAMETER:
                self._showSimpleWin32Dialog("Validation Accuracy Calculation Failed. An invalid setting was passed to the procedure.",
                                      "Common Eye Tracker Interface - ERROR")
                self._last_setup_result=EyeTrackerConstants.EYETRACKER_RECEIVED_INVALID_INPUT
            else:
                self._last_setup_result=dict()
                for a in accuracy_results.__slots__:
                    self._last_setup_result[a]=getattr(accuracy_results,a)
            
                self._showSimpleWin32Dialog("Validation Completed. Press ESCAPE to return to the Experiment Script, F1 to view all Options.",
                                      "Common Eye Tracker Interface")
        
    def _getKeyboardPress(self,key_mappings):
        from ..... import KeyboardPressEvent
        while 1:
            while len(self._kbEventQueue)>0:
                event=copy.deepcopy((self._kbEventQueue.pop(0)))
                ke=KeyboardPressEvent.createEventAsNamedTuple(event)
                key=ke.key.upper() 
                if key in key_mappings.keys():
                    del self._kbEventQueue[:]
                    return key_mappings[key]
            gevent.sleep(0.02)
                        
    def _registerKeyboardMonitor(self):
        kbDevice=None        
        if self._iohub_server:
            for dev in self._iohub_server.devices:
                if dev.__class__.__name__ == 'Keyboard':             
                    kbDevice=dev

        if kbDevice:
            eventIDs=[]
            for event_class_name in kbDevice.__class__.EVENT_CLASS_NAMES:
                eventIDs.append(getattr(EventConstants,convertCamelToSnake(event_class_name[:-5],False)))

            self._ioKeyboard=kbDevice
            self._ioKeyboard._addEventListener(self,eventIDs)
            self._kbEventQueue=[]
             
    def _unregisterKeyboardMonitor(self):
        if self._ioKeyboard:
            self._ioKeyboard._removeEventListener(self)
            self._ioKeyboard=None
            del self._kbEventQueue[:]
            
    def _handleEvent(self,ioe):
        event_type_index=DeviceEvent.EVENT_TYPE_ID_INDEX
        if ioe[event_type_index] == EventConstants.KEYBOARD_PRESS:
            self._kbEventQueue.append(ioe)
            
    def isRecordingEnabled(self,*args,**kwargs):
        """
        isRecordingEnabled returns True if the eye tracking device is currently connected and
        sending eye event data to the ioHub server. If the eye tracker is not recording, or is not
        connected to the ioHub server, False will be returned.
        """
        try:
            return self.isConnected() and self.isReportingEvents()
        except Exception, e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.isRecordingEnabled", error=e)

    def setRecordingState(self,recording):
        """
        setRecordingState enables (recording=True) or disables (recording=False)
        the recording of eye data by the eye tracker and the sending of any eye 
        data to the ioHub Server. The eye tracker must be connected to the ioHub Server
        by using the setConnectionState() method for recording to be possible.
        """
        try:
            if not isinstance(recording,bool):
                return createErrorResult("INVALID_METHOD_ARGUMENT_VALUE",
                    error_message="The recording arguement value provided is not a boolean.",
                    method="EyeTracker.setRecordingState",arguement='recording', value=recording)             

            if recording is True and not self.isRecordingEnabled(): 
                self._latest_sample=None
                self._latest_gaze_position=None

                r=pyViewX.StartRecording()
                
                if r == pyViewX.RET_SUCCESS or r == pyViewX.ERR_RECORDING_DATA_BUFFER:
                    EyeTrackerDevice.enableEventReporting(self,True)
                    return self.isRecordingEnabled()
                    
                if r == pyViewX.ERR_NOT_CONNECTED:
                    print2err("iViewX setRecordingState True Failed: ERR_NOT_CONNECTED") 
                    return EyeTrackerConstants.EYETRACKER_ERROR
                if r == pyViewX.ERR_WRONG_DEVICE:
                    print2err("iViewX setRecordingState True Failed: ERR_WRONG_DEVICE") 
                    return EyeTrackerConstants.EYETRACKER_ERROR
                            
            elif recording is False and self.isRecordingEnabled():
                self._latest_sample=None
                self._latest_gaze_position=None

                r=pyViewX.StopRecording() 
                
                if r == pyViewX.RET_SUCCESS or r == pyViewX.ERR_EMPTY_DATA_BUFFER:
                    EyeTrackerDevice.enableEventReporting(self,False)
                    return self.isRecordingEnabled()
                
                if r == pyViewX.ERR_NOT_CONNECTED:
                    print2err("iViewX setRecordingState(False) Failed: ERR_NOT_CONNECTED") 
                    return EyeTrackerConstants.EYETRACKER_ERROR
                if r == pyViewX.ERR_WRONG_DEVICE:
                    print2err("iViewX setRecordingState(False) Failed: ERR_WRONG_DEVICE") 
                    return EyeTrackerConstants.EYETRACKER_ERROR

        except Exception, e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.setRecordingState", error=e)            

    def enableEventReporting(self,enabled=True):
        """
        enableEventReporting is the device type independent method that is equivelent
        to the EyeTracker specific setRecordingState method.
        """
        try:        
            enabled=EyeTrackerDevice.enableEventReporting(self,enabled)
            return self.setRecordingState(enabled)
        except Exception, e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.enableEventReporting", error=e)            

    def getLastSample(self):
        """
        getLastSample returns the most recent BinocularEyeSampleEvent received
        from the iViewX system. Any position fields are in Display 
        device coordinate space. If the eye tracker is not recording or is not 
        connected, then None is returned.        
        """
        try:
            return self._latest_sample
        except Exception, e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.getLastSample", error=e)            

    def getLastGazePosition(self):
        """
        getLastGazePosition returns the most recent x,y eye position, in Display 
        device coordinate space, received by the ioHub server from the iViewX device.
        In the case of binocular recording, and if both eyes are successfully being tracked,
        then the average of the two eye positions is returned.
        If the eye tracker is not recording or is not connected, then None is returned.
        """
        try:
            return self._latest_gaze_position
        except Exception, e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker.getLastGazePosition", error=e)             
        
    def _poll(self):
        if self.isRecordingEnabled():        
            try:
                poll_time=Computer.getTime()
                tracker_time=self.trackerSec()
                confidence_interval=poll_time-self._last_poll_time
               
                DEVICE_TIMEBASE_TO_SEC=EyeTracker.DEVICE_TIMEBASE_TO_SEC
    
                nSamples=[]
                while 1:
                    sample=pyViewX.SampleStruct()
                    r=pyViewX.GetSample(byref(sample))	
                    if r == pyViewX.RET_SUCCESS:
                        nSamples.append(sample)
                    elif r == pyViewX.RET_NO_VALID_DATA:
                        break
                    elif r == pyViewX.ERR_NOT_CONNECTED:
                        break
                
                nEvents=[]
                while 1:
                    eventDataSample=pyViewX.EventStruct()
                    r=pyViewX.GetEvent(byref(eventDataSample))	
                    if r == pyViewX.RET_SUCCESS:
                        nEvents.append(eventDataSample)
                    elif r == pyViewX.RET_NO_VALID_DATA:
                        break
                    elif r == pyViewX.ERR_NOT_CONNECTED:
                        break
    
                    
                # process any sample events we got.....     
                if nSamples:                    
                    while nSamples:
                        sample=nSamples.pop(0)
    
                        event_type=EventConstants.BINOCULAR_EYE_SAMPLE
                        # TODO: Detrmine if binocular data is averaged or not for 
                        #       given model , tracking params, and indicate 
                        #       so using the recording_eye_type
                        #       EyeTrackerConstants.BINOCULAR or EyeTrackerConstants.BINOCULAR_AVERAGED
                        logged_time=poll_time
                        event_timestamp=sample.timestamp*DEVICE_TIMEBASE_TO_SEC
                        event_delay=tracker_time-event_timestamp
                        iohub_time=poll_time-event_delay
                        
                        plane_number=sample.planeNumber
                        
                        left_eye_data=sample.leftEye
                        right_eye_data=sample.rightEye
    
                        left_pupil_measure=left_eye_data.diam
                        right_pupil_measure=right_eye_data.diam
                        # TODO: ensure corrrect pupil measure type is being saved with pupl data to datastore.                    
                        pupil_measure_type=EyeTrackerConstants.PUPIL_DIAMETER
                        
                        left_gazeX=left_eye_data.gazeX
                        right_gazeX=right_eye_data.gazeX
                        left_gazeY=left_eye_data.gazeY
                        right_gazeY=right_eye_data.gazeY
  
                        right_gazeX,right_gazeY=self._eyeTrackerToDisplayCoords((right_gazeX,right_gazeY))
                        left_gazeX,left_gazeY=self._eyeTrackerToDisplayCoords((left_gazeX,left_gazeY))
                      
                        left_eyePositionX=left_eye_data.eyePositionX
                        right_eyePositionX=right_eye_data.eyePositionX
                        left_eyePositionY=left_eye_data.eyePositionY
                        right_eyePositionY=right_eye_data.eyePositionY
                        left_eyePositionZ=left_eye_data.eyePositionZ
                        right_eyePositionZ=right_eye_data.eyePositionZ
                        # TODO: Translate gaze position into ioHUb Display coords.
    
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
                                     left_gazeX,
                                     left_gazeY,
                                     EyeTrackerConstants.UNDEFINED,
                                     left_eyePositionX,
                                     left_eyePositionY,
                                     left_eyePositionZ,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     left_pupil_measure,
                                     pupil_measure_type,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     right_gazeX,
                                     right_gazeY,
                                     EyeTrackerConstants.UNDEFINED,
                                     right_eyePositionX,
                                     right_eyePositionY,
                                     right_eyePositionZ,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     right_pupil_measure,
                                     pupil_measure_type,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     EyeTrackerConstants.UNDEFINED,
                                     plane_number    # Since the sample struct has not status field
                                     ]               # we are using it to hold the 
                                                     # 'plane number' from the iViewX native sample.
    
                        self._latest_sample=binocSample
            
                        g=None
                        ic=0
                        if right_pupil_measure>0.0:
                            g=[0.0,0.0]                            
                            g[0]=right_gazeX
                            g[1]=right_gazeY
                            ic+=1
                        if left_pupil_measure>0.0:
                            if g is None:
                                g=[0.0,0.0]  
                            g[0]=+left_gazeX
                            g[1]=+left_gazeY
                            ic+=1
                        if ic == 2:
                             g[0]= g[0]/2.0
                             g[1]= g[1]/2.0
        
                        self._latest_gaze_position=g
                        self._addNativeEventToBuffer(binocSample)
    
                # process any fixation events we got.....
                if nEvents:
                    # each fixation event is both a start and end fixation, so we will
                    # create both a STartFix and EndFix ioHub event for each fix event
                    # we get from the iViewX
                    
                    while nEvents:
                        fix_event=nEvents.pop(0)
                        
                        # common fields
                        logged_time=poll_time
                        confidence_interval=poll_time-self._last_poll_time
    
                        if fix_event.eye == 'r':
                            which_eye=EyeTrackerConstants.RIGHT_EYE
                        elif fix_event.eye == 'l':
                            which_eye=EyeTrackerConstants.LEFT_EYE
    
                        event_start_time=fix_event.startTime*DEVICE_TIMEBASE_TO_SEC
                        event_end_time=fix_event.endTime*DEVICE_TIMEBASE_TO_SEC
                        event_duration=fix_event.duration*DEVICE_TIMEBASE_TO_SEC
    
                        event_avg_x=fix_event.positionX
                        event_avg_y=fix_event.positionY
                        
                        event_avg_x,event_avg_y=self._eyeTrackerToDisplayCoords((event_avg_x,event_avg_y))
                        start_event_delay=tracker_time-event_start_time
                        end_event_delay=tracker_time-event_end_time
                        
                        start_iohub_time=poll_time-start_event_delay
                        end_iohub_time=poll_time-end_event_delay
                        
                        # create fix start event......
                        event_type=EventConstants.FIXATION_START
    
                        se=[
                            0,                              # exp ID
                            0,                              # sess ID
                            0, #device id (not currently used)
                            Computer._getNextEventID(),     # event ID
                            event_type,                     # event type
                            event_start_time,
                            logged_time,
                            start_iohub_time,
                            confidence_interval,
                            start_event_delay,
                            0,                                      # ioHub filter ID
                            which_eye,                              # eye
                            EyeTrackerConstants.UNDEFINED,          # gaze x
                            EyeTrackerConstants.UNDEFINED,          # gaze y
                            EyeTrackerConstants.UNDEFINED,          # gaze z
                            EyeTrackerConstants.UNDEFINED,          # angle x
                            EyeTrackerConstants.UNDEFINED,          # angle y
                            EyeTrackerConstants.UNDEFINED,          # raw x
                            EyeTrackerConstants.UNDEFINED,          # raw y
                            EyeTrackerConstants.UNDEFINED,          # pupil area
                            EyeTrackerConstants.UNDEFINED,          # pupil measure type 1
                            EyeTrackerConstants.UNDEFINED,          # pupil measure 2
                            EyeTrackerConstants.UNDEFINED,          # pupil measure 2 type
                            EyeTrackerConstants.UNDEFINED,          # ppd x
                            EyeTrackerConstants.UNDEFINED,          # ppd y
                            EyeTrackerConstants.UNDEFINED,          # velocity x
                            EyeTrackerConstants.UNDEFINED,          # velocity y
                            EyeTrackerConstants.UNDEFINED,          # velocity xy
                            EyeTrackerConstants.UNDEFINED           # status
                            ]
        
                        self._addNativeEventToBuffer(se)
                    
                    
                        # create fix end event........
    
                        event_type=EventConstants.FIXATION_END
    
                        fee=[0,
                             0,
                             0, #device id (not currently used)
                             Computer._getNextEventID(),
                             event_type,
                             event_end_time,
                             logged_time,
                             end_iohub_time,
                             confidence_interval,
                             end_event_delay,
                             0,
                             which_eye,
                             event_duration,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             event_avg_x,
                             event_avg_y,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED,
                             EyeTrackerConstants.UNDEFINED
                             ]
                        
                        self._addNativeEventToBuffer(fee)
    
#                print2err("pyViewX done poll ",confidence_interval)
                self._last_poll_time=poll_time
                return True
            
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
        except Exception,e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker._eyeTrackerToDisplayCoords", 
                    error=e)            
        
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
           
        except Exception,e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker._displayToEyeTrackerCoords", 
                    error=e)

    def _TrackerSystemInfo(self):
        try:
            systemInfo=pyViewX.SystemInfoStruct()
            res = pyViewX.GetSystemInfo(byref(systemInfo))
            if res == pyViewX.RET_SUCCESS:
                return dict(sampling_rate=int(systemInfo.samplerate),
                            eyetracking_engine_version =  "{0}.{1}.{2}".format(systemInfo.iV_MajorVersion,
                                                                               systemInfo.iV_MinorVersion,
                                                                               systemInfo.iV_Buildnumber
                                                                               ),
                            client_sdk_version =  "{0}.{1}.{2}".format(systemInfo.API_MajorVersion,
                                                                        systemInfo.API_MinorVersion,
                                                                        systemInfo.API_Buildnumber
                                                                       ),
                            model_name = systemInfo.iV_ETDevice
                                        
                            )
            print2err("GetSystemInfo FAILED: " + str(res))  
            return EyeTrackerConstants.EYETRACKER_ERROR         
        except Exception,e:
            return createErrorResult("IOHUB_DEVICE_EXCEPTION",
                    error_message="An unhandled exception occurred on the ioHub Server Process.",
                    method="EyeTracker._eyeLinkHardwareAndSoftwareVersion", 
                    error=e)            

    def _close(self):
        self.setRecordingState(False)
        self.setConnectionState(False)

# C DLL to ioHub settings mappings

class _iViewConfigMappings(object):
    # supported calibration modes    
    calibration_methods = dict( NO_POINTS=0,TWO_POINTS=2,THREE_POINTS=3,FIVE_POINTS=5, NINE_POINTS=9, THIRTEEN_POINTS=13)
    graphics_env = dict(INTERNAL=1, EXTERNAL=0)
    auto_pace = dict (True=1, False=0, Yes=1, No=0, On=1, Off=0)
    pacing_speed = dict(SLOW=0, FAST=1)
    target_type= dict(IMAGE=0, CIRCLE_TARGET=1, CIRCLE_TARGET_V2=2, CROSS=3)
                        
    @classmethod
    def _createCalibrationStruct(cls,eyetracker, calibration_struct):
        #method: Select Calibration Method (default: 5) 
        #visualization: Set Visualization Status [0: visualization by external stimulus program 1: visualization by SDK (default)] 
        #displayDevice: Set Display Device and resolution [0: primary device (default), 1: secondary device] 
        #speed: Set Calibration/Validation Speed [0: slow (default), 1: fast] 
        #autoAccept: Set Calibration/Validation Point Acceptance [1: automatic (default) 0: manual]
        #foregroundBrightness: Set Calibration/Validation Target Brightness [0..255] (default: 20) 
        #backgroundBrightness: Set Calibration/Validation Background Brightness [0..255] (default: 239) 
        #targetShape: Set Calibration/Validation Target Shape [IMAGE = 0, CIRCLE1 = 1 (default), CIRCLE2 = 2, CROSS = 3] 
        #targetSize: Set Calibration/Validation Target Size (default: 10 pixels) 
        #targetFilename: Select Custom Calibration/Validation Target
        calibration_config=eyetracker.getConfiguration()['calibration']

        calibration_struct.method=c_int(_iViewConfigMappings.calibration_methods[calibration_config.get('type','FIVE_POINTS')])
        calibration_struct.visualization=c_int(_iViewConfigMappings.graphics_env[calibration_config.get('graphics_env','INTERNAL')])
        calibration_struct.displayDevice=c_int(eyetracker._display_device.getIndex())
        calibration_struct.speed=c_int(_iViewConfigMappings.pacing_speed[calibration_config.get('pacing_speed',0)])
        calibration_struct.autoAccept=c_int(calibration_config.get('auto_pace',1))
        calibration_struct.backgroundBrightness=c_int(calibration_config.get('screen_background_color',239))
        calibration_struct.targetShape=c_int(_iViewConfigMappings.target_type[calibration_config.get('target_type','CIRCLE_TARGET')])
        calibration_struct.targetFilename=b''
        
        if calibration_config['target_type'] in ['CIRCLE_TARGET_V2', 'CIRCLE_TARGET']:
            target_settings=calibration_config['target_attributes'] 
            calibration_struct.foregroundBrightness=c_int(target_settings.get('target_color',20))
            calibration_struct.targetSize=c_int(target_settings.get('target_size',30))

        elif calibration_config['target_type'] =='IMAGE_TARGET':
            calibration_struct.targetFilename=pyViewX.StringBuffer(calibration_config['image_attributes'].get('file_name',b''))
            calibration_struct.targetSize=c_int(calibration_config['image_attributes'].get('target_size',30))
        
        elif calibration_config['target_type'] == 'CROSSHAIR_TARGET':
            target_settings=calibration_config['crosshair_attributes'] 
            calibration_struct.foregroundBrightness=c_int(target_settings.get('target_color',20))
            calibration_struct.targetSize=c_int(target_settings.get('target_size',30))
        else:
            print2err('Unknown Calibration Target Type: ', calibration_config['target_type'])
