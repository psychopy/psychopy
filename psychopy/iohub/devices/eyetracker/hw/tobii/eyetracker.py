# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).

"""ioHub Common Eye Tracker Interface for Tobii (C) Eye Tracking System"""
from __future__ import absolute_import
import math
from .....constants import EventConstants, EyeTrackerConstants
from .... import Computer, Device
from ... import EyeTrackerDevice
from ...eye_events import *
from .....errors import print2err, printExceptionDetailsToStdErr
try:
    from .tobiiwrapper import TobiiTracker
except Exception:
    print2err('Error importing tobiiwrapper.TobiiTracker')
    printExceptionDetailsToStdErr()


class EyeTracker(EyeTrackerDevice):
    """
    The Tobii implementation of the Common Eye Tracker Interface can be used
    by providing the following EyeTracker path as the device class in
    the iohub_config.yaml device settings file:

        eyetracker.hw.tobii.EyeTracker

    """
    _tobii = None

    DEVICE_TIMEBASE_TO_SEC = 0.000001
    EVENT_CLASS_NAMES = [
        'MonocularEyeSampleEvent',
        'BinocularEyeSampleEvent',
        'FixationStartEvent',
        'FixationEndEvent',
        'SaccadeStartEvent',
        'SaccadeEndEvent',
        'BlinkStartEvent',
        'BlinkEndEvent']
    __slots__ = []

    def __init__(self, *args, **kwargs):
        EyeTrackerDevice.__init__(self, *args, **kwargs)

        model_name = self.model_name
        serial_num = self.serial_number

        if model_name and len(model_name) == 0:
            model_name = None
        if serial_num and len(serial_num) == 0:
            serial_num = None

        EyeTracker._tobii = None
        try:
            EyeTracker._tobii = TobiiTracker(serial_num, model_name)
        except Exception:
            print2err('Error creating Tobii Device class')
            printExceptionDetailsToStdErr()

        srate = self._runtime_settings['sampling_rate']
        if srate and srate in self._tobii.getAvailableSamplingRates():
            self._tobii.setSamplingRate(srate)

        self._latest_sample = None
        self._latest_gaze_position = None

    def trackerTime(self):
        """Current eye tracker time in the eye tracker's native time base. The
        Tobii system uses a usec timebase.

        Args:
            None

        Returns:
            float: current native eye tracker time. (in usec for the Tobii)

        """
        if self._tobii:
            return self._tobii.getCurrentEyeTrackerTime()
        return EyeTrackerConstants.EYETRACKER_ERROR

    def trackerSec(self):
        """Current eye tracker time, normalized to sec.msec format.

        Args:
            None

        Returns:
            float: current native eye tracker time in sec.msec-usec format.

        """
        if self._tobii:
            return self._tobii.getCurrentEyeTrackerTime() * self.DEVICE_TIMEBASE_TO_SEC
        return EyeTrackerConstants.EYETRACKER_ERROR

    def setConnectionState(self, enable):
        """
        setConnectionState is a no-op when using the Tobii system, as the
        connection is established when the Tobii EyeTracker classes are created,
        and remains active until the program ends, or a error occurs resulting
        in the loss of the tracker connection.

        Args:
            enable (bool): True = enable the connection, False = disable the connection.

        Return:
            bool: indicates the current connection state to the eye tracking hardware.
        """
        if self._tobii:
            return True
        return False
    
    def isConnected(self):
        """isConnected returns whether the Tobii is connected to the experiment
        PC and if the tracker state is valid. Returns True if the tracker can
        be put into Record mode, etc and False if there is an error with the
        tracker or tracker connection with the experiment PC.

        Args:
            None

        Return:
            bool:  True = the eye tracking hardware is connected. False otherwise.

        """
        if self._tobii:
            return True
        return False

    def sendMessage(self, message_contents, time_offset=None):
        """The sendMessage method is not supported by the Tobii implementation
        of the Common Eye Tracker Interface, as the Tobii SDK does not support
        saving eye data to a native data file during recording."""
        return EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED

    def sendCommand(self, key, value=None):
        """The sendCommand method is not supported by the Tobii Common Eye
        Tracker Interface."""
        return EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED

    def runSetupProcedure(
            self,
            starting_state=EyeTrackerConstants.DEFAULT_SETUP_PROCEDURE):
        """runSetupProcedure performs a calibration routine for the Tobii eye
        tracking system. The current calibration options are relatively limited
        for the Tobii ioHub interface compared to a standard Tobii calibration
        procedure. It is hoped that this will be improved in the ioHub Tobii
        interface as time permits.

        Result:
            bool: True if setup / calibration procedue passed, False otherwise. If false, should likely exit experiment.

        """
        try:
            from .tobiiCalibrationGraphics import TobiiPsychopyCalibrationGraphics

            calibration_properties = self.getConfiguration().get('calibration')
            screenColor = calibration_properties.get(
                'screen_background_color')                     # [r,g,b] of screen

            genv = TobiiPsychopyCalibrationGraphics(
                self, screenColor=screenColor)

            calibrationOK = genv.runCalibration()

            # On some graphics cards, we have to minimize before closing or the calibration window will stay visible
            # after close is called.
            genv.window.winHandle.set_visible(False)
            genv.window.winHandle.minimize()

            genv.window.close()

            genv._unregisterEventMonitors()
            genv.clearAllEventBuffers()

            return calibrationOK

        except Exception:
            print2err('Error during runSetupProcedure')
            printExceptionDetailsToStdErr()
        return EyeTrackerConstants.EYETRACKER_ERROR

    def enableEventReporting(self, enabled=True):
        """enableEventReporting is functionally identical to the eye tracker
        device specific enableEventReporting method."""

        try:
            enabled = EyeTrackerDevice.enableEventReporting(self, enabled)
            self.setRecordingState(enabled)
            return enabled
        except Exception as e:
            print2err('Error during enableEventReporting')
            printExceptionDetailsToStdErr()
        return EyeTrackerConstants.EYETRACKER_ERROR

    def setRecordingState(self, recording):
        """setRecordingState is used to start or stop the recording of data
        from the eye tracking device.

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
        if self._tobii and recording is True and not self.isRecordingEnabled():
            #ioHub.print2err("Starting Tracking... ")
            self._tobii.startTracking(self._handleNativeEvent)
            return EyeTrackerDevice.enableEventReporting(self, True)

        elif self._tobii and recording is False and self.isRecordingEnabled():
            self._tobii.stopTracking()
            #ioHub.print2err("Stopping Tracking... ")
            self._latest_sample = None
            self._latest_gaze_position = None
            return EyeTrackerDevice.enableEventReporting(self, False)

        return self.isRecordingEnabled()

    def isRecordingEnabled(self):
        """isRecordingEnabled returns the recording state from the eye tracking
        device.

        Args:
           None

        Return:
            bool: True == the device is recording data; False == Recording is not occurring

        """
        if self._tobii:
            return self._tobii._isRecording
        return False

    def getLastSample(self):
        """Returns the latest sample retrieved from the Tobii device. The Tobii
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
        """Returns the latest 2D eye gaze position retrieved from the Tobii
        device. This represents where the eye tracker is reporting each eye
        gaze vector is intersecting the calibrated surface.

        In general, the y or vertical component of each eyes gaze position should
        be the same value, since in typical user populations the two eyes are
        yoked vertically when they move. Therefore any difference between the
        two eyes in the y dimension is likely due to eye tracker error.

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

    def _setSamplingRate(self, sampling_rate):
        return self._tobii.setSamplingRate(sampling_rate)

    def _poll(self):
        """The Tobii system uses a callback approach to providing new eye data
        as it becomes available, so polling (and therefore this method) are not
        used."""
        pass

    def _handleNativeEvent(self, *args, **kwargs):
        """This method is called every time there is new eye data available
        from the Tobii system, which will be roughly equal to the sampling rate
        eye data is being recorded at.

        The callback needs to return as quickly as possible so there is
        no chance of overlapping calls being made to the callback.
        Therefore this method simply puts the event data received from
        the eye tracker device, and the local ioHub time the callback
        was called, into a buffer for processing by the ioHub event
        system.
        """
        if self.isReportingEvents():
            try:
                logged_time = Computer.getTime()
                tobii_logged_time = self._tobii.getCurrentLocalTobiiTime() * self.DEVICE_TIMEBASE_TO_SEC
                
                eye_data_event = args[0]
                
                device_event_time = eye_data_event['system_time_stamp'] * self.DEVICE_TIMEBASE_TO_SEC
        
                data_delay = tobii_logged_time-device_event_time
        
                iohub_event_time = (logged_time - data_delay)
                self._addNativeEventToBuffer(
                    (logged_time,
                     device_event_time,
                     iohub_event_time,
                     data_delay,
                     eye_data_event))
                return True
            except Exception:
                print2err('ERROR IN _handleNativeEvent')
                printExceptionDetailsToStdErr()
        else:
            print2err(
                'self._handleNativeEvent called but isReportingEvents == false')


    def _getIOHubEventObject(self, native_event_data):
        """The _getIOHubEventObject method is called by the ioHub Server to
        convert new native device event objects that have been received to the
        appropriate ioHub Event type representation.

        The Tobii ioHub eye tracker implementation uses a callback method
        to register new native device events with the ioHub Server.
        Therefore this method converts the native Tobii event data into
        an appropriate ioHub Event representation.

        Args:
            native_event_data: object or tuple of (callback_time, native_event_object)

        Returns:
            tuple: The appropriate ioHub Event type in list form.

        """
        try:
            logged_time, device_event_time, iohub_event_time, data_delay, eye_data_event = native_event_data

#         'system_time_stamp': 295431587453,
#         'device_time_stamp': 1554911175642814,
#         'right_gaze_point_on_display_area': (0.6514113545417786, 0.6740643382072449)
#         'right_gaze_point_validity': 1,
#         'right_pupil_diameter': 2.0828399658203125, 
#         'right_pupil_validity': 1, 
#         'left_gaze_point_on_display_area': (0.6300967931747437, 0.6632571816444397), 
#         'left_gaze_point_validity': 1,
#         'left_pupil_diameter': 2.2154541015625, 
#         'left_pupil_validity': 1,
#
#         'right_gaze_origin_in_user_coordinate_system': (26.230587005615234, 30.770994186401367, 584.1049194335938), 
#         'right_gaze_origin_in_trackbox_coordinate_system': (0.4429018795490265, 0.339368999004364, 0.4470163881778717), 
#         'left_gaze_origin_in_trackbox_coordinate_system': (0.6209999918937683, 0.35132133960723877, 0.4568300247192383),
#         'right_gaze_origin_validity': 1,
#         'right_gaze_point_in_user_coordinate_system': (51.17703628540039, 115.1743392944336, 27.5936222076416),
#         'left_gaze_origin_validity': 1, 
#         'left_gaze_origin_in_user_coordinate_system': (-33.106361389160156, 26.86952018737793, 587.0490112304688), 
#         'left_gaze_point_in_user_coordinate_system': (43.972713470458984, 117.93881225585938, 28.65477752685547), 
    
    #        eyes[LEFT]['gaze_mm'][0]=eye_data_event.LeftGazePoint3D.x
    #        eyes[LEFT]['gaze_mm'][1]=eye_data_event.LeftGazePoint3D.y
    #        eyes[LEFT]['gaze_mm'][2]=eye_data_event.LeftGazePoint3D.z
    #        eyes[LEFT]['eye_location_norm'][0]=eye_data_event.LeftEyePosition3DRelative.x
    #        eyes[LEFT]['eye_location_norm'][1]=eye_data_event.LeftEyePosition3DRelative.y
    #        eyes[LEFT]['eye_location_norm'][2]=eye_data_event.LeftEyePosition3DRelative.z
    #        eyes[RIGHT]['gaze_mm'][0]=eye_data_event.RightGazePoint3D.x
    #        eyes[RIGHT]['gaze_mm'][1]=eye_data_event.RightGazePoint3D.y
    #        eyes[RIGHT]['gaze_mm'][2]=eye_data_event.RightGazePoint3D.z
    #        eyes[RIGHT]['eye_location_norm'][0]=eye_data_event.RightEyePosition3DRelative.x
    #        eyes[RIGHT]['eye_location_norm'][1]=eye_data_event.RightEyePosition3DRelative.y
    #        eyes[RIGHT]['eye_location_norm'][2]=eye_data_event.RightEyePosition3DRelative.z
    
            event_type = EventConstants.BINOCULAR_EYE_SAMPLE
    
            left_gaze_x, left_gaze_y = eye_data_event['left_gaze_point_on_display_area']
            right_gaze_x, right_gaze_y = eye_data_event['right_gaze_point_on_display_area']
    
            status = 0

            if eye_data_event['left_gaze_point_validity'] > 0:
                left_gaze_x, left_gaze_y = self._eyeTrackerToDisplayCoords(
                    (left_gaze_x, left_gaze_y))
            else:
                status += 20
                
            if eye_data_event['right_gaze_point_validity'] > 0:
                right_gaze_x, right_gaze_y = self._eyeTrackerToDisplayCoords(
                    (right_gaze_x, right_gaze_y))
            else:
                status += 2                

            right_gx, right_gy, right_gz = eye_data_event['right_gaze_origin_in_trackbox_coordinate_system']
            left_gx, left_gy, left_gz = eye_data_event['left_gaze_origin_in_trackbox_coordinate_system']

            confidenceInterval = 0.0
            binocSample = [
                0,
                0,
                0,  # device id (not currently used)
                Device._getNextEventID(),
                event_type,
                device_event_time,
                logged_time,
                iohub_event_time,
                confidenceInterval,
                data_delay,
                0,  # filtered id (always 0 right now)
                left_gaze_x,
                left_gaze_y,
                EyeTrackerConstants.UNDEFINED,
                left_gx,
                left_gy,
                left_gz,
                EyeTrackerConstants.UNDEFINED,  # Left Eye Angle x
                EyeTrackerConstants.UNDEFINED,  # Left Eye Angle y
                EyeTrackerConstants.UNDEFINED,  # Left Camera Sensor position x
                EyeTrackerConstants.UNDEFINED,  # Left Camera Sensor position y
                eye_data_event['left_pupil_diameter'],
                EyeTrackerConstants.PUPIL_DIAMETER_MM,
                EyeTrackerConstants.UNDEFINED,  # Left pupil size measure 2
                EyeTrackerConstants.UNDEFINED,  # Left pupil size measure 2 type
                EyeTrackerConstants.UNDEFINED,  # Left PPD x
                EyeTrackerConstants.UNDEFINED,  # Left PPD y
                EyeTrackerConstants.UNDEFINED,  # Left velocity x
                EyeTrackerConstants.UNDEFINED,  # Left velocity y
                EyeTrackerConstants.UNDEFINED,  # Left velocity xy
                right_gaze_x,
                right_gaze_y,
                EyeTrackerConstants.UNDEFINED,  # Right Eye Angle z
                right_gx,
                right_gy,
                right_gz,
                EyeTrackerConstants.UNDEFINED,  # Right Eye Angle x
                EyeTrackerConstants.UNDEFINED,  # Right Eye Angle y
                EyeTrackerConstants.UNDEFINED,  # Right Camera Sensor position x
                EyeTrackerConstants.UNDEFINED,  # Right Camera Sensor position y
                eye_data_event['right_pupil_diameter'],
                EyeTrackerConstants.PUPIL_DIAMETER_MM,
                EyeTrackerConstants.UNDEFINED,  # Right pupil size measure 2
                EyeTrackerConstants.UNDEFINED,  # Right pupil size measure 2 type
                EyeTrackerConstants.UNDEFINED,  # Right PPD x
                EyeTrackerConstants.UNDEFINED,  # Right PPD y
                EyeTrackerConstants.UNDEFINED,  # right velocity x
                EyeTrackerConstants.UNDEFINED,  # right velocity y
                EyeTrackerConstants.UNDEFINED,  # right velocity xy
                status
            ]
    
            self._latest_sample = binocSample
    
            if eye_data_event['left_gaze_point_validity'] == eye_data_event['right_gaze_point_validity'] == 0:
                self._latest_gaze_position = None
            elif eye_data_event['left_gaze_point_validity'] == eye_data_event['right_gaze_point_validity'] == 1:
                self._latest_gaze_position = [(right_gaze_x + left_gaze_x) / 2.0,
                                              (right_gaze_y + left_gaze_y) / 2.0]
            elif eye_data_event['left_gaze_point_validity'] == 1:
                self._latest_gaze_position = [left_gaze_x, left_gaze_y]
            elif eye_data_event['right_gaze_point_validity'] == 1:
                self._latest_gaze_position = [right_gaze_x, right_gaze_y]
    
            self._last_callback_time = logged_time
    
            return binocSample
        except Exception:
            printExceptionDetailsToStdErr()
        return None

    def _eyeTrackerToDisplayCoords(self, eyetracker_point):
        """Converts Tobii gaze positions to the Display device coordinate
        space."""

        gaze_x, gaze_y = eyetracker_point
        left, top, right, bottom = self._display_device.getCoordBounds()
        w, h = right - left, top - bottom
        x, y = left + w * gaze_x, bottom + h * (1.0 - gaze_y)

        #print2err("Tobii: ",(eyetracker_point),(left,top,right,bottom),(x,y))
        return x, y

    def _displayToEyeTrackerCoords(self, display_x, display_y):
        """Converts a Display device point to Tobii gaze position coordinate
        space."""
        left, top, right, bottom = self._display_device.getCoordBounds()
        w, h = right - left, top - bottom

        return (left - display_x) / w, (top - display_y) / h

    def _close(self):
        if EyeTracker._tobii:
            EyeTracker._tobii.disconnect()
            EyeTracker._tobii = None
        EyeTrackerDevice._close(self)
