"""ioHub Common Eye Tracker Interface for SMI iViewX (C) Systems"""
 # Part of the psychopy.iohub library.
 # Copyright (C) 2012-2016 iSolver Software Solutions
 # Distributed under the terms of the GNU General Public License (GPL).
from __future__ import division
from __future__ import absolute_import

import sys
import copy


from ......util import convertCamelToSnake
from ......constants import EventConstants, EyeTrackerConstants
from ..... import DeviceEvent, Computer, Device
from .... import EyeTrackerDevice
from ....eye_events import *
from ......errors import print2err, printExceptionDetailsToStdErr

from . import pyViewX
from ctypes import byref, c_longlong, c_int, c_void_p, POINTER

import gevent


class EyeTracker(EyeTrackerDevice):
    """
    The SMI iViewX implementation of the Common Eye Tracker Interface
    can be used by providing the following EyeTracker path as the device
    class in the iohub_config.yaml device settings file:

        eyetracker.hw.smi.iviewx.EyeTracker
    """

    pyviewx2ivewxParamMappings = {
        EyeTrackerConstants.LEFT_EYE: pyViewX.ET_PARAM_EYE_LEFT,
        EyeTrackerConstants.RIGHT_EYE: pyViewX.ET_PARAM_EYE_RIGHT,
        EyeTrackerConstants.BINOCULAR: pyViewX.ET_PARAM_EYE_BOTH,
        EyeTrackerConstants.BINOCULAR_CUSTOM: pyViewX.ET_PARAM_SMARTBINOCULAR,
        EyeTrackerConstants.MONOCULAR: pyViewX.ET_PARAM_MONOCULAR
    }

    # >>> Overwritten class attributes
    DEVICE_TIMEBASE_TO_SEC = 0.000001

    # The iViewX currently supports a subset of all the eye tracker events listed
    # below, but due to an outstanding bug in the ioHUb device interface, all event types
    # possible for the given device class must be listed in the class
    # definition.
    EVENT_CLASS_NAMES = [
        'MonocularEyeSampleEvent',
        'BinocularEyeSampleEvent',
        'FixationStartEvent',
        'FixationEndEvent',
        'SaccadeStartEvent',
        'SaccadeEndEvent',
        'BlinkStartEvent',
        'BlinkEndEvent']

    __slots__ = [
        '_api_pc_ip',
        '_api_pc_port',
        '_et_pc_ip',
        '_et_pc_port',
        '_enable_data_filter',
        '_ioKeyboardHandler',
        '_kbEventQueue',
        '_last_setup_result',
        '_handle_sample_callback']

    def __init__(self, *args, **kwargs):
        EyeTrackerDevice.__init__(self, *args, **kwargs)
        try:
            self._ioKeyboardHandler = None

            # Get network config (used in setConnectionState(True).
            iviewx_network_config = self.getConfiguration().get('network_settings')
            self._api_pc_ip = iviewx_network_config['send_ip_address']
            self._api_pc_port = iviewx_network_config['send_port']
            self._et_pc_ip = iviewx_network_config['receive_ip_address']
            self._et_pc_port = iviewx_network_config['receive_port']

            # Connect to the iViewX.
            self.setConnectionState(True)

            # Callback sample notification support.
            self._handle_sample_callback = pyViewX.pDLLSetSample(
                self._handleNativeEvent)

            # Set the filtering level......
            filter_type, filter_level = self._runtime_settings['sample_filtering'].items()[
                0]
            INT_POINTER = POINTER(c_int)
            if filter_type == 'FILTER_ALL':
                level_int = EyeTrackerConstants.getID(filter_level)
                if not level_int:
                    try:
                        # Try to disable any filtering using the
                        # new ConfigureFilter function added in Feb 2014 SMI API
                        # release.
                        disable_it = c_int(0)
                        filter_state_set = POINTER(c_int)(disable_it)
                        pyViewX.ConfigureFilter(
                            pyViewX.etFilterType.get('Average_Enabled'),
                            pyViewX.etFilterAction.get('Set'),
                            filter_state_set)
                    except Exception as e:
                        print2err(
                            'Note: pyViewX.ConfigureFilter to disable filtering call failed.')

                    # Try disabling filtering using the DisableGazeDataFilter
                    # SMI C func. Not sure if this is 'officially' supported.
                    pyViewX.DisableGazeDataFilter()
                elif 0 < level_int <= EyeTrackerConstants.FILTER_ALL:
                    # Try to enable filtering using the
                    # new ConfigureFilter function added in Feb 2014 SMI API
                    # release.
                    try:
                        enable_it = c_int(1)
                        filter_state_set = POINTER(c_int)(enable_it)
                        pyViewX.ConfigureFilter(
                            pyViewX.etFilterType.get('Average_Enabled'),
                            pyViewX.etFilterAction.get('Set'),
                            filter_state_set)
                    except Exception as e:
                        print2err(
                            'Note: pyViewX.ConfigureFilter to disable filtering call failed.')

                    # Try enabling filtering using the DisableGazeDataFilter
                    # SMI C func. Not sure if this is 'officially' supported.
                    pyViewX.EnableGazeDataFilter()
                else:
                    print2err(
                        'Warning: Unsupported iViewX sample filter level value: ',
                        filter_level,
                        '=',
                        level_int)
            else:
                print2err(
                    'Warning: Unsupported iViewX sample filter type: ',
                    filter_type,
                    '. Only FILTER_ALL is supported.')

            ####
            # Native file saving...
            ####
            #print2err("NOTE: Native file saving for the iViewX has not yet been implemented.")

            ####
            # Get the iViewX device's system info,
            # and update appropriate attributes.
            ####
            sys_info = self._TrackerSystemInfo()
            if sys_info != EyeTrackerConstants.EYETRACKER_ERROR:
                sampling_rate = sys_info['sampling_rate']
                eyetracking_engine_version = sys_info[
                    'eyetracking_engine_version']
                client_sdk_version = sys_info['client_sdk_version']
                model_name = sys_info['model_name']

                self.software_version = 'Client SDK: {0} ; Tracker Engine: {1}'.format(
                    client_sdk_version, eyetracking_engine_version)
                self.getConfiguration()[
                    'software_version'] = self.software_version
                self.getConfiguration()['model_name'] = model_name
                self.model_name = model_name

                ####
                # Set sampling rate CHECK ONLY.....
                ####
                requested_sampling_rate = self._runtime_settings[
                    'sampling_rate']
                if requested_sampling_rate != sampling_rate:
                    print2err(
                        'WARNING: iViewX requested frame rate of {0} != current rate of {1}:'.format(
                            requested_sampling_rate, sampling_rate))

                self._runtime_settings['sampling_rate'] = sampling_rate

            self._last_setup_result = EyeTrackerConstants.EYETRACKER_OK
        except Exception:
            print2err(
                ' ---- Error during SMI iView EyeTracker Initialization ---- ')
            printExceptionDetailsToStdErr()
            print2err(
                ' ---- Error during SMI iView EyeTracker Initialization ---- ')

    def trackerTime(self):
        """trackerTime returns the current iViewX Application or Server time in
        usec format as a long integer."""
        tracker_time = c_longlong(0)
        r = pyViewX.GetCurrentTimestamp(byref(tracker_time))
        if r == pyViewX.RET_SUCCESS:
            return tracker_time.value
        print2err(
            'iViewX trackerTime FAILED: error: {0} timeval: {1}'.format(
                r, tracker_time))
        return EyeTrackerConstants.EYETRACKER_ERROR

    def trackerSec(self):
        """
        trackerSec returns the current iViewX Application or Server time in
        sec.msec-usec format.
        """
        tracker_time = c_longlong(0)
        r = pyViewX.GetCurrentTimestamp(byref(tracker_time))
        if r == pyViewX.RET_SUCCESS:
            return tracker_time.value * self.DEVICE_TIMEBASE_TO_SEC
        print2err(
            'iViewX trackerSec FAILED: error: {0} timeval: {1}'.format(
                r, tracker_time))
        return EyeTrackerConstants.EYETRACKER_ERROR

    def isConnected(self):
        """isConnected indicates if there is an active connection between the
        ioHub Server and the eye tracking device.

        Note that when the SMI iViewX EyeTracker class is created when the ioHub server starts,
        a connection is automatically created with the eye tracking device.

        The ioHub must be connected to the eye tracker device for it to be able to receive
        events from the eye tracking system. Eye tracking events are received when
        isConnected() == True and when isRecordingEnabled() == True.

        """
        try:
            r = pyViewX.IsConnected()
            if r == pyViewX.RET_SUCCESS:
                connected = True
            elif r == pyViewX.ERR_NOT_CONNECTED:
                connected = False
            else:
                print2err(
                    'iViewX isConnected() returned unexpected value {0}'.format(r))
                connected = EyeTrackerConstants.EYETRACKER_ERROR
            return connected
        except Exception as e:
            print2err(' ---- SMI EyeTracker isConnected ERROR ---- ')
            printExceptionDetailsToStdErr()
        print2err('isConnected error!!: ', connected)
        return False

    def setConnectionState(self, enable):
        """setConnectionState connects the ioHub Server to the SMI iViewX
        device if the enable arguement is True, otherwise an open connection is
        closed with the device. Calling this method multiple times with the
        same value has no effect.

        Note that when the SMI iViewX EyeTracker class is created when the ioHub server starts,
        a connection is automatically created with the eye tracking device.

        If the eye tracker is currently recording eye data and sending it to the
        ioHub server, the recording will be stopped prior to closing the connection.

        """
        try:
            if enable is True or enable is False:
                if enable is True and not self.isConnected():
                    r = pyViewX.Connect(pyViewX.String(self._api_pc_ip),
                                        self._api_pc_port,
                                        pyViewX.String(self._et_pc_ip),
                                        self._et_pc_port)
                    if r != pyViewX.RET_SUCCESS:
                        print2err(
                            'iViewX ERROR connecting to tracker: {0}'.format(r))
                    return self.isConnected()
                elif enable is False and self.isConnected():
                    if self.isRecordingEnabled():
                        self.setRecordingState(False)
                    r = pyViewX.Disconnect()
                    if r != pyViewX.RET_SUCCESS:
                        print2err(
                            'iViewX ERROR disconnecting from tracker: {0}'.format(r))
                    return self.isConnected()
            else:
                print2err(
                    ' ---- SMI EyeTracker setConnectionState INVALID_METHOD_ARGUMENT_VALUE ---- ')
                printExceptionDetailsToStdErr()
        except Exception as e:
            print2err(' ---- SMI EyeTracker isConnected ERROR ---- ')
            printExceptionDetailsToStdErr()

    def sendMessage(self, message_contents, time_offset=None):
        """The sendMessage method is currently not supported by the SMI iViewX
        implementation of the Common Eye Tracker Interface.

        Once native data file saving is implemented for the iViewX, this
        method will become available.

        """
        try:
            # Possible return codes:
            #
            # RET_SUCCESS - intended functionality has been fulfilled
            # ERR_NOT_CONNECTED - no connection established
            r = pyViewX.SendImageMessage(pyViewX.String(message_contents))
            if r != pyViewX.RET_SUCCESS:
                print2err(
                    'iViewX ERROR {0} when sendMessage to tracker: {1}'.format(
                        r, message_contents))
                return EyeTrackerConstants.EYETRACKER_ERROR
            return EyeTrackerConstants.EYETRACKER_OK

        except Exception as e:
            printExceptionDetailsToStdErr()

    def sendCommand(self, key, value=None):
        """The sendCommand method can be used to make calls to the iViewX
        iV_SetTrackingParameter function. The sendCommand method requires valid
        key and value arguements.

        Currently supported 'key' arguement values, with their mapping to the
        associated iViewX API constant, are:

        EyeTrackerConstants.LEFT_EYE:   pyViewX.ET_PARAM_EYE_LEFT
        EyeTrackerConstants.RIGHT_EYE:  pyViewX.ET_PARAM_EYE_RIGHT
        EyeTrackerConstants.BINOCULAR:  pyViewX.ET_PARAM_EYE_BOTH

        If the key arguement supplied does not match one of the three
        EyeTrackerConstants values listed above, the method will return:

        EyeTrackerConstants.EYETRACKER_RECEIVED_INVALID_INPUT

        Currently supported 'value' arguement values, with their mapping to the
        associated iViewX API constant, are:

        EyeTrackerConstants.BINOCULAR_CUSTOM:  pyViewX.ET_PARAM_SMARTBINOCULAR
        EyeTrackerConstants.MONOCULAR:         pyViewX.ET_PARAM_MONOCULAR

        If the value arguement supplied does not match one of the two
        SMI iView ioHub interface specific constants listed above,
        the method will return:

        EyeTrackerConstants.EYETRACKER_RECEIVED_INVALID_INPUT

        Possible return values from the method are:

        EyeTrackerConstants.EYETRACKER_OK:  intended functionality has been fulfilled
        EyeTrackerConstants.EYETRACKER_NOT_CONNECTED:  no connection established
        EyeTrackerConstants.EYETRACKER_RECEIVED_INVALID_INPUT:  parameter out of range

        If the iV_* function returns a code that is not expected, then the
        invalid (or undocumented) return code from the iV_* function call is
        returned as is by sendCommand.

        Examples, assuming an eyetracker device called 'tracker' has been
        created by ioHub:

        tracker = <iohub connection variable name>.devices.tracker

        tracker.sendCommand(EyeTrackerConstants.BINOCULAR,EyeTrackerConstants.BINOCULAR_CUSTOM)

        tracker.sendCommand(EyeTrackerConstants.LEFT_EYE,EyeTrackerConstants.BINOCULAR_CUSTOM)

        tracker.sendCommand(EyeTrackerConstants.RIGHT_EYE,EyeTrackerConstants.BINOCULAR_CUSTOM)

        tracker.sendCommand(EyeTrackerConstants.LEFT_EYE,EyeTrackerConstants.MONOCULAR)

        tracker.sendCommand(EyeTrackerConstants.RIGHT_EYE,EyeTrackerConstants.MONOCULAR)

        """

        if self.isConnected() is False:
            return EyeTrackerConstants.EYETRACKER_NOT_CONNECTED

        if key not in [EyeTrackerConstants.LEFT_EYE,
                       EyeTrackerConstants.RIGHT_EYE,
                       EyeTrackerConstants.BINOCULAR]:
            return EyeTrackerConstants.EYETRACKER_RECEIVED_INVALID_INPUT

        if value not in [
                EyeTrackerConstants.BINOCULAR_CUSTOM,
                EyeTrackerConstants.MONOCULAR]:
            return EyeTrackerConstants.EYETRACKER_RECEIVED_INVALID_INPUT

        result = pyViewX.SetTrackingParameter(
            self.pyviewx2ivewxParamMappings[key],
            self.pyviewx2ivewxParamMappings[value],
            0)

        if result == pyViewX.RET_SUCCESS:
            return EyeTrackerConstants.EYETRACKER_OK
        if result == pyViewX.ERR_NOT_CONNECTED:
            return EyeTrackerConstants.EYETRACKER_NOT_CONNECTED
        if result == pyViewX.ERR_WRONG_PARAMETER:
            return EyeTrackerConstants.EYETRACKER_RECEIVED_INVALID_INPUT

        # if the return code does not map to one of the valid return codes
        # based on the iViewX SDK docs, then return the native error code
        # so it can be figured out.
        return result

    def runSetupProcedure(
            self,
            starting_state=EyeTrackerConstants.DEFAULT_SETUP_PROCEDURE):
        """
        The SMI iViewX implementation of the runSetupProcedure supports the following
        starting_state values:

            #. DEFAULT_SETUP_PROCEDURE: This (default) mode starts by showing a dialog with the various options available during user setup.
            #. CALIBRATION_STATE: The eye tracker will immediately perform a calibration and then return to the experiment script.
            #. VALIDATION_STATE: The eye tracker will immediately perform a validation and then return to the experiment script. The return result is a dict containing the validation results.
            #. TRACKER_FEEDBACK_STATE: The eye tracker will display the eye image window and tracker graphics if either has been enabled in the device config, and then return to the experiment script.

        """
        if self.isConnected() is False:
            return EyeTrackerConstants.EYETRACKER_ERROR

        try:
            IMPLEMENTATION_SUPPORTED_STATES = [
                EyeTrackerConstants.DEFAULT_SETUP_PROCEDURE,
                EyeTrackerConstants.CALIBRATION_STATE,
                EyeTrackerConstants.VALIDATION_STATE,
                EyeTrackerConstants.TRACKER_FEEDBACK_STATE]

            if isinstance(starting_state, basestring):
                starting_state = EyeTrackerConstants.getID(starting_state)

            self._registerKeyboardMonitor()

            self._last_setup_result = EyeTrackerConstants.EYETRACKER_OK

            if starting_state not in IMPLEMENTATION_SUPPORTED_STATES:
                self._last_setup_result = EyeTrackerConstants.EYETRACKER_RECEIVED_INVALID_INPUT
            elif starting_state == EyeTrackerConstants.DEFAULT_SETUP_PROCEDURE:
                self._showSetupKeyOptionsDialog()
                next_state = None
                key_mapping = {'C': self._calibrate,
                               'V': self._validate,
                               'T': self._showTrackingMonitor,
                               'E': self._showEyeImageMonitor,
                               'ESCAPE': 'CONTINUE',
                               'F1': self._showSetupKeyOptionsDialog}
                while True:
                    if next_state is None:
                        next_state = self._getKeyboardPress(key_mapping)

                    if callable(next_state):
                        next_state()
                        next_state = None

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
                self._last_setup_result = EyeTrackerConstants.EYETRACKER_RECEIVED_INVALID_INPUT
            self._unregisterKeyboardMonitor()

            return self._last_setup_result
        except Exception as e:
            self._unregisterKeyboardMonitor()
            printExceptionDetailsToStdErr()

        try:
            hide_funcs = [pyViewX.HideAccuracyMonitor,
                          pyViewX.HideEyeImageMonitor,
                          pyViewX.HideSceneVideoMonitor,
                          pyViewX.HideTrackingMonitor
                          ]
            for f in hide_funcs:
                f()
        except Exception:
            print2err('Exception while trying to call: {0}'.format(f))

    def _showSimpleWin32Dialog(self, message, caption):
        import win32gui
        win32gui.MessageBox(None, message, caption, 0)

    def _showSetupKeyOptionsDialog(self):
        msg_text = 'The following Keyboard Commands will be available during User Setup:\n'
        msg_text += '\n\tE : Display Eye Image Window.\n'
        msg_text += '\tT : Display Tracking Monitor Window.\n'
        msg_text += '\tC : Start Calibration Routine.\n'
        msg_text += '\tV : Start Validation Routine.\n'
        msg_text += '\tESCAPE : Exit the Setup Procedure.\n'
        msg_text += '\tF1 : Show this Dialog.\n'
        msg_text += '\nPress OK to begin'

        self._showSimpleWin32Dialog(
            msg_text, 'Common Eye Tracker Interface - iViewX Calibration')

    def _showEyeImageMonitor(self):

        # pyViewX.ShowEyeImageMonitor return codes:
        #
        # RET_SUCCESS - intended functionality has been fulfilled
        # ERR_NOT_CONNECTED - no connection established
        # ERR_WRONG_DEVICE - eye tracking device required for
        #                    this function is not connected
        result = pyViewX.ShowEyeImageMonitor()

        if result == pyViewX.ERR_NOT_CONNECTED:
            self._showSimpleWin32Dialog(
                'Eye Image Monitor can not be Displayed. An iViewX System is not Connected to the ioHub.',
                'Common Eye Tracker Interface - ERROR')
            self._last_setup_result = EyeTrackerConstants.EYETRACKER_NOT_CONNECTED
        if result == pyViewX.ERR_WRONG_DEVICE:
            self._showSimpleWin32Dialog(
                'Eye Image Monitor can not be Displayed. The iViewX Model being used does not support this Operation.',
                'Common Eye Tracker Interface - ERROR')
            self._last_setup_result = EyeTrackerConstants.EYETRACKER_MODEL_NOT_SUPPORTED

    def _showTrackingMonitor(self):
        # pyViewX.ShowTrackingMonitor return codes:
        #
        # RET_SUCCESS - intended functionality has been fulfilled
        # ERR_NOT_CONNECTED - no connection established
        # ERR_WRONG_DEVICE - eye tracking device required for
        #                    this function is not connected
        result = pyViewX.ShowTrackingMonitor()
        # TODO: Handle possible return codes
        #ioHub.print2err('ShowTrackingMonitor result: ',result)
        if result == pyViewX.ERR_NOT_CONNECTED:
            self._showSimpleWin32Dialog(
                'Tracking Monitor can not be Displayed. An iViewX System is not Connected to the ioHub.',
                'Common Eye Tracker Interface - ERROR')
            self._last_setup_result = EyeTrackerConstants.EYETRACKER_NOT_CONNECTED
        if result == pyViewX.ERR_WRONG_DEVICE:
            self._showSimpleWin32Dialog(
                'Tracking Monitor can not be Displayed. The iViewX Model being used does not support this Operation.',
                'Common Eye Tracker Interface - ERROR')
            self._last_setup_result = EyeTrackerConstants.EYETRACKER_MODEL_NOT_SUPPORTED

    def _calibrate(self):
        calibrationData = pyViewX.CalibrationStruct()
        _iViewConfigMappings._createCalibrationStruct(self, calibrationData)

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
            self._showSimpleWin32Dialog(
                'Calibration Could not be Performed. An invalid setting was passed to the procedure.',
                'Common Eye Tracker Interface - ERROR')
            self._last_setup_result = EyeTrackerConstants.EYETRACKER_RECEIVED_INVALID_INPUT

        elif result == pyViewX.ERR_WRONG_DEVICE:
            self._showSimpleWin32Dialog(
                'Calibration Could not be Performed. The iViewX Model being used does not support this Operation.',
                'Common Eye Tracker Interface - ERROR')
            self._last_setup_result = EyeTrackerConstants.EYETRACKER_MODEL_NOT_SUPPORTED

        elif result == pyViewX.ERR_WRONG_CALIBRATION_METHOD:
            self._showSimpleWin32Dialog(
                'Calibration Could not be Performed. The Calibration Type being used is not Supported by the attached iViewX Model.',
                'Common Eye Tracker Interface - ERROR')
            self._last_setup_result = EyeTrackerConstants.EYETRACKER_MODEL_NOT_SUPPORTED

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
            self._showSimpleWin32Dialog(
                'Tracking Monitor can not be Displayed. An iViewX System is not Connected to the ioHub.',
                'Common Eye Tracker Interface - ERROR')
            self._last_setup_result = EyeTrackerConstants.EYETRACKER_NOT_CONNECTED
        elif result == pyViewX.RET_CALIBRATION_ABORTED:
            self._showSimpleWin32Dialog(
                'The Calibration Procedure was Aborted.',
                'Common Eye Tracker Interface - WARNING')
            self._last_setup_result = EyeTrackerConstants.EYETRACKER_SETUP_ABORTED
        elif result == pyViewX.ERR_WRONG_DEVICE:
            self._showSimpleWin32Dialog(
                'Calibration Could not be Performed. The iViewX Model being used does not support this Operation.',
                'Common Eye Tracker Interface - ERROR')
            self._last_setup_result = EyeTrackerConstants.EYETRACKER_MODEL_NOT_SUPPORTED
        elif result == pyViewX.ERR_WRONG_CALIBRATION_METHOD:
            self._showSimpleWin32Dialog(
                'Calibration Could not be Performed. The Calibration Type being used is not Supported by the attached iViewX Model.',
                'Common Eye Tracker Interface - ERROR')
            self._last_setup_result = EyeTrackerConstants.EYETRACKER_MODEL_NOT_SUPPORTED
        else:
            self._last_setup_result = EyeTrackerConstants.EYETRACKER_OK
            self._showSimpleWin32Dialog(
                "Calibration Completed. Press 'V' to Validate, ESCAPE to exit Setup, F1 to view all Options.",
                'Common Eye Tracker Interface')

    def _validate(self):
        # pyViewX.Validate return codes:
        #
        # RET_SUCCESS - intended functionality has been fulfilled
        # ERR_NOT_CONNECTED - no connection established
        # ERR_NOT_CALIBRATED - system is not calibrated
        # ERR_WRONG_DEVICE - eye tracking device required for this
        #                    function is not connected
        result = pyViewX.Validate()

        if result == pyViewX.ERR_NOT_CONNECTED:
            self._showSimpleWin32Dialog(
                'Validation Procedure Failed. An iViewX System is not Connected to the ioHub.',
                'Common Eye Tracker Interface - ERROR')
            self._last_setup_result = EyeTrackerConstants.EYETRACKER_NOT_CONNECTED
        elif result == pyViewX.ERR_NOT_CALIBRATED:
            self._showSimpleWin32Dialog(
                'Validation can only be Performed after a Successful Calibration.',
                'Common Eye Tracker Interface - WARNING')
            self._last_setup_result = EyeTrackerConstants.EYETRACKER_VALIDATION_ERROR
        elif result == pyViewX.ERR_WRONG_DEVICE:
            self._showSimpleWin32Dialog(
                'Validation Procedure Failed. The iViewX Model being used does not support this Operation.',
                'Common Eye Tracker Interface - ERROR')
            self._last_setup_result = EyeTrackerConstants.EYETRACKER_MODEL_NOT_SUPPORTED
        else:
            self._last_setup_result = EyeTrackerConstants.EYETRACKER_OK

            show_validation_results = self.getConfiguration()['calibration'].get(
                'show_validation_accuracy_window', False)

            # pyViewX.GetAccuracy return codes:
            #
            # RET_SUCCESS - intended functionality has been fulfilled
            # RET_NO_VALID_DATA - No new data available
            # ERR_NOT_CONNECTED - no connection established
            # ERR_NOT_CALIBRATED - system is not calibrated
            # ERR_NOT_VALIDATED - system is not validated
            # ERR_WRONG_PARAMETER - parameter out of range
            accuracy_results = pyViewX.AccuracyStruct()
            result = pyViewX.GetAccuracy(
                byref(accuracy_results), show_validation_results)

            if result == pyViewX.ERR_NOT_CONNECTED:
                self._showSimpleWin32Dialog(
                    'Validation Procedure Failed. An iViewX System is not Connected to the ioHub.',
                    'Common Eye Tracker Interface - ERROR')
                self._last_setup_result = EyeTrackerConstants.EYETRACKER_NOT_CONNECTED
            elif result == pyViewX.ERR_NOT_CALIBRATED:
                self._showSimpleWin32Dialog(
                    'Validation can only be Performed after a Successful Calibration.',
                    'Common Eye Tracker Interface - WARNING')
                self._last_setup_result = EyeTrackerConstants.EYETRACKER_VALIDATION_ERROR
            elif result == pyViewX.ERR_NOT_VALIDATED:
                self._showSimpleWin32Dialog(
                    'Validation Accuracy Calculation Failed. The System has not been Validated.',
                    'Common Eye Tracker Interface - ERROR')
                self._last_setup_result = EyeTrackerConstants.EYETRACKER_VALIDATION_ERROR
            elif result == pyViewX.ERR_WRONG_PARAMETER:
                self._showSimpleWin32Dialog(
                    'Validation Accuracy Calculation Failed. An invalid setting was passed to the procedure.',
                    'Common Eye Tracker Interface - ERROR')
                self._last_setup_result = EyeTrackerConstants.EYETRACKER_RECEIVED_INVALID_INPUT
            else:
                self._last_setup_result = dict()
                for a in accuracy_results.__slots__:
                    self._last_setup_result[a] = getattr(accuracy_results, a)

                self._showSimpleWin32Dialog(
                    'Validation Completed. Press ESCAPE to return to the Experiment Script, F1 to view all Options.',
                    'Common Eye Tracker Interface')

    def _getKeyboardPress(self, key_mappings):
        from ..... import KeyboardPressEvent
        while True:
            while len(self._kbEventQueue) > 0:
                event = copy.deepcopy((self._kbEventQueue.pop(0)))
                ke = KeyboardPressEvent.createEventAsNamedTuple(event)
                key = ke.key.upper()
                if key in key_mappings:
                    del self._kbEventQueue[:]
                    return key_mappings[key]
            gevent.sleep(0.02)

    def _registerKeyboardMonitor(self):
        kbDevice = None
        if self._iohub_server:
            for dev in self._iohub_server.devices:
                if dev.__class__.__name__ == 'Keyboard':
                    kbDevice = dev

        if kbDevice:
            eventIDs = []
            for event_class_name in kbDevice.__class__.EVENT_CLASS_NAMES:
                eventIDs.append(
                    getattr(
                        EventConstants,
                        convertCamelToSnake(
                            event_class_name[
                                :-5],
                            False)))

            class KeyboardEventHandler(object):

                def __init__(self, et, kb):
                    self.et = et
                    self.kb = kb
                    self.kb._addEventListener(self, eventIDs)
                    self.et._kbEventQueue = []

                def _handleEvent(self, ioe):
                    event_type_index = DeviceEvent.EVENT_TYPE_ID_INDEX
                    if ioe[event_type_index] == EventConstants.KEYBOARD_PRESS:
                        self.et._kbEventQueue.append(ioe)

                def free(self):
                    self.kb._removeEventListener(self)
                    del self.et._kbEventQueue[:]
                    self.et = None
                    self.kb = None

            self._ioKeyboardHandler = KeyboardEventHandler(self, kbDevice)

    def _unregisterKeyboardMonitor(self):
        if self._ioKeyboardHandler:
            self._ioKeyboardHandler.free()
            self._ioKeyboardHandler = None

    def isRecordingEnabled(self, *args, **kwargs):
        """isRecordingEnabled returns True if the eye tracking device is
        currently connected and sending eye event data to the ioHub server.

        If the eye tracker is not recording, or is not connected to the
        ioHub server, False will be returned.

        """
        try:
            return self.isConnected() and self.isReportingEvents()
        except Exception as e:
            printExceptionDetailsToStdErr()

    def setRecordingState(self, recording):
        """
        setRecordingState enables (recording=True) or disables (recording=False)
        the recording of eye data by the eye tracker and the sending of any eye
        data to the ioHub Server. The eye tracker must be connected to the ioHub Server
        by using the setConnectionState() method for recording to be possible.
        """
        try:
            if not isinstance(recording, bool):
                printExceptionDetailsToStdErr()

            elif recording is True and not self.isRecordingEnabled():
                pyViewX.SetSampleCallback(self._handle_sample_callback)
                self._latest_sample = None
                self._latest_gaze_position = None

                # just incase recording is running ,
                # try to stop it and clear the smi memory buffers.
                pyViewX.StopRecording()
                pyViewX.ClearRecordingBuffer()

                r = pyViewX.StartRecording()
                if r == pyViewX.RET_SUCCESS or r == pyViewX.ERR_RECORDING_DATA_BUFFER or r == pyViewX.ERR_FULL_DATA_BUFFER:
                    EyeTrackerDevice.enableEventReporting(self, True)
                    return self.isRecordingEnabled()
                if r == pyViewX.ERR_NOT_CONNECTED:
                    print2err(
                        'StartRecording FAILED: pyViewX.ERR_NOT_CONNECTED', r)
                    pyViewX.SetSampleCallback(pyViewX.pDLLSetSample(0))
                    EyeTrackerDevice.enableEventReporting(self, False)
                    return False  # EyeTrackerConstants.EYETRACKER_ERROR
                if r == pyViewX.ERR_WRONG_DEVICE:
                    print2err(
                        'iViewX setRecordingState True Failed: ERR_WRONG_DEVICE')
                    pyViewX.SetSampleCallback(pyViewX.pDLLSetSample(0))
                    EyeTrackerDevice.enableEventReporting(self, False)
                    return False  # EyeTrackerConstants.EYETRACKER_ERROR

            elif recording is False and self.isRecordingEnabled():
                self._latest_sample = None
                self._latest_gaze_position = None
                # clear the smi memory buffers.
                pyViewX.ClearRecordingBuffer()
                r = pyViewX.StopRecording()

                pyViewX.SetSampleCallback(pyViewX.pDLLSetSample(0))

                if r == pyViewX.RET_SUCCESS or r == pyViewX.ERR_EMPTY_DATA_BUFFER or r == pyViewX.ERR_FULL_DATA_BUFFER:
                    EyeTrackerDevice.enableEventReporting(self, False)
                    return self.isRecordingEnabled()

                if r == pyViewX.ERR_NOT_CONNECTED:
                    print2err(
                        'iViewX setRecordingState(False) Failed: ERR_NOT_CONNECTED')
                    return False  # EyeTrackerConstants.EYETRACKER_ERROR
                if r == pyViewX.ERR_WRONG_DEVICE:
                    print2err(
                        'iViewX setRecordingState(False) Failed: ERR_WRONG_DEVICE')
                    return False  # EyeTrackerConstants.EYETRACKER_ERROR

        except Exception as e:
            printExceptionDetailsToStdErr()

    def enableEventReporting(self, enabled=True):
        """enableEventReporting is the device type independent method that is
        equivalent to the EyeTracker specific setRecordingState method."""
        try:
            result2 = self.setRecordingState(enabled)
            EyeTrackerDevice.enableEventReporting(self, enabled)
            return result2
        except Exception as e:
            printExceptionDetailsToStdErr()
        return False

    def getLastSample(self):
        """getLastSample returns the most recent BinocularEyeSampleEvent
        received from the iViewX system.

        Any position fields are in Display device coordinate space. If
        the eye tracker is not recording or is not connected, then None
        is returned.

        """
        try:
            return self._latest_sample
        except Exception as e:
            printExceptionDetailsToStdErr()

    def getLastGazePosition(self):
        """getLastGazePosition returns the most recent x,y eye position, in
        Display device coordinate space, received by the ioHub server from the
        iViewX device.

        In the case of binocular recording, and if both eyes are
        successfully being tracked, then the average of the two eye
        positions is returned. If the eye tracker is not recording or is
        not connected, then None is returned.

        """
        try:
            return self._latest_gaze_position
        except Exception as e:
            printExceptionDetailsToStdErr()

    def _handleNativeEvent(self, *args, **kwargs):
        """
        TODO: Add support for Fixation events. Currently callback only supports samples.

        The _handleEvent method can be used by the native device interface (implemented
        by the ioHub Device class) to register new native device events
        by calling this method of the ioHub Device class.

        When a native device interface uses the _handleNativeEvent method it is
        employing an event callback approach to notify the ioHub Process when new
        native device events are available. This is in contrast to devices that use
        a polling method to check for new native device events, which would implement
        the _poll() method instead of this method.

        Generally speaking this method is called by the native device interface
        once for each new event that is available for the ioHub Process. However,
        with good cause, there is no reason why a single call to this
        method could not handle multiple new native device events.

        .. note::
            If using _handleNativeEvent, be sure to remove the device_timer
            property from the devices configuration section of the iohub_config.yaml.

        Any arguments or kwargs passed to this method are determined by the ioHub
        Device implementation and should contain all the information needed to create
        an ioHub Device Event.

        Since any callbacks should take as little time to process as possible,
        a two stage approach is used to turn a native device event into an ioHub
        Device event representation:
            #. This method is called by the native device interface as a callback, providing the necessary information to be able to create an ioHub event. As little processing should be done in this method as possible.
            #. The data passed to this method, along with the time the callback was called, are passed as a tuple to the Device classes _addNativeEventToBuffer method.
            #. During the ioHub Servers event processing routine, any new native events that have been added to the ioHub Server using the _addNativeEventToBuffer method are passed individually to the _getIOHubEventObject method, which must also be implemented by the given Device subclass.
            #. The _getIOHubEventObject method is responsible for the actual conversion of the native event representation to the required ioHub Event representation for the accociated event type.

        Args:
            args(tuple): tuple of non keyword arguements passed to the callback.

        Kwargs:
            kwargs(dict): dict of keyword arguements passed to the callback.

        Returns:
            None
        """
        try:
            poll_time = Computer.getTime()
            tracker_time = self.trackerSec()
            confidence_interval = 0.0
            DEVICE_TIMEBASE_TO_SEC = EyeTracker.DEVICE_TIMEBASE_TO_SEC

            sample = args[0]

            event_type = EventConstants.BINOCULAR_EYE_SAMPLE
            # TODO: Detrmine if binocular data is averaged or not for
            #       given model , tracking params, and indicate
            #       so using the recording_eye_type
            #       EyeTrackerConstants.BINOCULAR or EyeTrackerConstants.BINOCULAR_AVERAGED
            logged_time = poll_time
            event_timestamp = sample.timestamp * DEVICE_TIMEBASE_TO_SEC
            event_delay = tracker_time - event_timestamp
            iohub_time = poll_time - event_delay

            plane_number = sample.planeNumber

            left_eye_data = sample.leftEye
            right_eye_data = sample.rightEye

            status = 0

            left_pupil_measure = left_eye_data.diam
            right_pupil_measure = right_eye_data.diam
            pupil_measure_type = EyeTrackerConstants.PUPIL_DIAMETER

            left_gazeX = left_eye_data.gazeX
            right_gazeX = right_eye_data.gazeX
            left_gazeY = left_eye_data.gazeY
            right_gazeY = right_eye_data.gazeY

            if right_pupil_measure > 0.0 and right_gazeX != 0.0 and right_gazeY != 0.0:
                right_gazeX, right_gazeY = self._eyeTrackerToDisplayCoords(
                    (right_gazeX, right_gazeY))
            else:
                right_pupil_measure = 0
                right_gazeX = EyeTrackerConstants.UNDEFINED
                right_gazeY = EyeTrackerConstants.UNDEFINED
                status = 2

            if left_pupil_measure > 0.0 and left_gazeX != 0.0 and left_gazeY != 0.0:
                left_gazeX, left_gazeY = self._eyeTrackerToDisplayCoords(
                    (left_gazeX, left_gazeY))
            else:
                left_pupil_measure = 0
                left_gazeX = EyeTrackerConstants.UNDEFINED
                left_gazeY = EyeTrackerConstants.UNDEFINED
                status += 20

            left_eyePositionX = left_eye_data.eyePositionX
            right_eyePositionX = right_eye_data.eyePositionX
            left_eyePositionY = left_eye_data.eyePositionY
            right_eyePositionY = right_eye_data.eyePositionY
            left_eyePositionZ = left_eye_data.eyePositionZ
            right_eyePositionZ = right_eye_data.eyePositionZ

            binocSample = [
                0,
                0,
                0,  # device id (not currently used)
                Device._getNextEventID(),
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
                status
            ]

            self._addNativeEventToBuffer(binocSample)
        except Exception:
            print2err('ERROR occurred during iViewX Sample Callback.')
            printExceptionDetailsToStdErr()
        finally:
            return 0

    def _getIOHubEventObject(self, native_event_data):
        """The _getIOHubEventObject method is called by the ioHub Process to
        convert new native device event objects that have been received to the
        appropriate ioHub Event type representation.

        Args:
            native_event_data: object or tuple of (callback_time, native_event_object)

        Returns:
            tuple: The appropriate ioHub Event type in list form.

        """

        self._latest_sample = native_event_data

        getAttribIndex = BinocularEyeSampleEvent.CLASS_ATTRIBUTE_NAMES.index

        left_pupil_measure = native_event_data[
            getAttribIndex('left_pupil_measure1')]
        left_gazeX = native_event_data[getAttribIndex('left_gaze_x')]
        left_gazeY = native_event_data[getAttribIndex('left_gaze_y')]
        right_gazeX = native_event_data[getAttribIndex('right_gaze_x')]
        right_gazeY = native_event_data[getAttribIndex('right_gaze_y')]
        right_pupil_measure = native_event_data[
            getAttribIndex('right_pupil_measure1')]

        ic = 0
        EyeTracker._gx = 0.0
        EyeTracker._gy = 0.0
        if right_pupil_measure > 0.0 and right_gazeX != 0.0 and right_gazeY != 0.0:
            EyeTracker._gx = EyeTracker._gx + right_gazeX
            EyeTracker._gy = EyeTracker._gy + right_gazeY
            ic += 1

        if left_pupil_measure > 0.0 and left_gazeX != 0.0 and left_gazeY != 0.0:
            EyeTracker._gx = EyeTracker._gx + left_gazeX
            EyeTracker._gy = EyeTracker._gy + left_gazeY
            ic += 1

        if ic == 2:
            EyeTracker._gx = EyeTracker._gx / 2.0
            EyeTracker._gy = EyeTracker._gy / 2.0

        if ic > 0:
            self._latest_gaze_position = (EyeTracker._gx, EyeTracker._gy)
        else:
            self._latest_gaze_position = None
        return native_event_data

    def _eyeTrackerToDisplayCoords(self, eyetracker_point):
        """"""
        try:
            gaze_x, gaze_y = eyetracker_point
            dw, dh = self._display_device.getPixelResolution()
            gaze_x = gaze_x / dw
            gaze_y = gaze_y / dh
            left, top, right, bottom = self._display_device.getCoordBounds()
            w, h = right - left, top - bottom
            x, y = left + w * gaze_x, bottom + h * (1.0 - gaze_y)
            return x, y
        except Exception as e:
            printExceptionDetailsToStdErr()

    def _displayToEyeTrackerCoords(self, display_x, display_y):
        """"""
        try:
            cl, ct, cr, cb = self._display_device.getCoordBounds()
            cw, ch = cr - cl, ct - cb

            dl, dt, dr, db = self._display_device.getBounds()
            dw, dh = dr - dl, db - dt

            cxn, cyn = (display_x + cw / 2) / cw, 1.0 - \
                (display_y - ch / 2) / ch
            return cxn * dw, cyn * dh

        except Exception as e:
            printExceptionDetailsToStdErr()

    def _TrackerSystemInfo(self):
        try:
            systemInfo = pyViewX.SystemInfoStruct()
            res = pyViewX.GetSystemInfo(byref(systemInfo))
            if res == pyViewX.RET_SUCCESS:
                return dict(
                    sampling_rate=int(
                        systemInfo.samplerate),
                    eyetracking_engine_version='{0}.{1}.{2}'.format(
                        systemInfo.iV_MajorVersion,
                        systemInfo.iV_MinorVersion,
                        systemInfo.iV_Buildnumber),
                    client_sdk_version='{0}.{1}.{2}'.format(
                        systemInfo.API_MajorVersion,
                        systemInfo.API_MinorVersion,
                        systemInfo.API_Buildnumber),
                    model_name=systemInfo.iV_ETDevice)
            print2err('GetSystemInfo FAILED: ' + str(res))
            return EyeTrackerConstants.EYETRACKER_ERROR
        except Exception as e:
            printExceptionDetailsToStdErr()

    def _close(self):
        self.setRecordingState(False)
        self.setConnectionState(False)

# C DLL to ioHub settings mappings


class _iViewConfigMappings(object):
    # supported calibration modes
    calibration_methods = dict(
        NO_POINTS=0,
        TWO_POINTS=2,
        THREE_POINTS=3,
        FIVE_POINTS=5,
        NINE_POINTS=9,
        THIRTEEN_POINTS=13)
    graphics_env = dict(INTERNAL=1, EXTERNAL=0)
    auto_pace = {'True': 1, 'False': 0, 'Yes': 1, 'No': 0, 'On': 1, 'Off': 0}
    pacing_speed = dict(SLOW=0, FAST=1)
    target_type = dict(IMAGE=0, CIRCLE_TARGET=1, CIRCLE_TARGET_V2=2, CROSS=3)

    @classmethod
    def _createCalibrationStruct(cls, eyetracker, calibration_struct):
        # method: Select Calibration Method (default: 5)
        # visualization: Set Visualization Status [0: visualization by external stimulus program 1: visualization by SDK (default)]
        # displayDevice: Set Display Device and resolution [0: primary device (default), 1: secondary device]
        # speed: Set Calibration/Validation Speed [0: slow (default), 1: fast]
        # autoAccept: Set Calibration/Validation Point Acceptance [1: automatic (default) 0: manual]
        # foregroundBrightness: Set Calibration/Validation Target Brightness [0..255] (default: 20)
        # backgroundBrightness: Set Calibration/Validation Background Brightness [0..255] (default: 239)
        # targetShape: Set Calibration/Validation Target Shape [IMAGE = 0, CIRCLE1 = 1 (default), CIRCLE2 = 2, CROSS = 3]
        # targetSize: Set Calibration/Validation Target Size (default: 10 pixels)
        # targetFilename: Select Custom Calibration/Validation Target
        calibration_config = eyetracker.getConfiguration()['calibration']

        calibration_struct.method = c_int(
            _iViewConfigMappings.calibration_methods[
                calibration_config.get(
                    'type', 'FIVE_POINTS')])
        calibration_struct.visualization = c_int(
            _iViewConfigMappings.graphics_env[
                calibration_config.get(
                    'graphics_env', 'INTERNAL')])
        calibration_struct.displayDevice = c_int(
            eyetracker._display_device.getIndex())
        calibration_struct.speed = c_int(
            _iViewConfigMappings.pacing_speed[
                calibration_config.get(
                    'pacing_speed', 0)])
        calibration_struct.autoAccept = c_int(
            calibration_config.get('auto_pace', 1))
        calibration_struct.backgroundBrightness = c_int(
            calibration_config.get('screen_background_color', 239))
        calibration_struct.targetShape = c_int(
            _iViewConfigMappings.target_type[
                calibration_config.get(
                    'target_type', 'CIRCLE_TARGET')])
        calibration_struct.targetFilename = ''

        if calibration_config['target_type'] in [
                'CIRCLE_TARGET_V2', 'CIRCLE_TARGET']:
            target_settings = calibration_config['target_attributes']
            calibration_struct.foregroundBrightness = c_int(
                target_settings.get('target_color', 20))
            calibration_struct.targetSize = c_int(
                target_settings.get('target_size', 30))

        elif calibration_config['target_type'] == 'IMAGE_TARGET':
            calibration_struct.targetFilename = pyViewX.String(
                calibration_config['image_attributes'].get('file_name', b''))
            calibration_struct.targetSize = c_int(
                calibration_config['image_attributes'].get(
                    'target_size', 30))

        elif calibration_config['target_type'] == 'CROSSHAIR_TARGET':
            target_settings = calibration_config['crosshair_attributes']
            calibration_struct.foregroundBrightness = c_int(
                target_settings.get('target_color', 20))
            calibration_struct.targetSize = c_int(
                target_settings.get('target_size', 30))
        else:
            print2err(
                'Unknown Calibration Target Type: ',
                calibration_config['target_type'])
