# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import math
from psychopy.iohub.constants import EventConstants, EyeTrackerConstants
from psychopy.iohub.devices import Computer, Device
from psychopy.iohub.devices.eyetracker import EyeTrackerDevice
from psychopy.iohub.devices.eyetracker.hw.tobii.tobiiCalibrationGraphics import TobiiPsychopyCalibrationGraphics
from psychopy.iohub.devices.eyetracker.eye_events import *
from psychopy.iohub.errors import print2err, printExceptionDetailsToStdErr
try:
    from .tobiiwrapper import TobiiTracker
except Exception:
    print2err('Error importing tobiiwrapper.TobiiTracker')
    printExceptionDetailsToStdErr()


class EyeTracker(EyeTrackerDevice):
    """
    To start iohub with a Tobii eye tracker device, add the Tobii
    device to the dictionary passed to launchHubServer or the 
    experiment's iohub_config.yaml::

        eyetracker.hw.tobii.EyeTracker
        
    Examples:
        A. Start ioHub with a Tobii device and run tracker calibration::
    
            from psychopy.iohub import launchHubServer
            from psychopy.core import getTime, wait

            iohub_config = {'eyetracker.hw.tobii.EyeTracker':
                {'name': 'tracker', 'runtime_settings': {'sampling_rate': 120}}}
                
            io = launchHubServer(**iohub_config)
            
            # Get the eye tracker device.
            tracker = io.devices.tracker
                            
            # run eyetracker calibration
            r = tracker.runSetupProcedure()
            
        B. Print all eye tracker events received for 2 seconds::
                        
            # Check for and print any eye tracker events received...
            tracker.setRecordingState(True)
            
            stime = getTime()
            while getTime()-stime < 2.0:
                for e in tracker.getEvents():
                    print(e)
            
        C. Print current eye position for 5 seconds::
                        
            # Check for and print current eye position every 100 msec.
            stime = getTime()
            while getTime()-stime < 5.0:
                print(tracker.getPosition())
                wait(0.1)
            
            tracker.setRecordingState(False)
            
            # Stop the ioHub Server
            io.quit()
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

        if self.model_name:
            self.model_name = self.model_name.strip()
            if len(self.model_name) == 0:
                self.model_name = None
        model_name = self.model_name
        serial_num = self.getConfiguration().get('serial_number')

        EyeTracker._tobii = None
        try:
            EyeTracker._tobii = TobiiTracker(serial_num, model_name)
        except Exception:
            print2err('Error creating Tobii Device class')
            printExceptionDetailsToStdErr()

        # Apply license file if needed
        try:
            license_file = self.getConfiguration().get('license_file', "")
            if license_file != "":
                with open(license_file, "rb") as f:
                    license = f.read()
                    res = self._tobii._eyetracker.apply_licenses(license)
                    if len(res) == 0:
                        print2err("Successfully applied Tobii license from: {}".format(license_file))
                    else:
                        print2err("Error: Failed to apply Tobii license from single key. "
                                  "Validation result: %s." % (res[0].validation_result))
            else:
                print2err("No Tobii license_file in config. Skipping.")
        except Exception:
            print2err("Error calling Tobii.apply_licenses with file {}.".format(license_file))
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

    def runSetupProcedure(self, calibration_args={}):
        """runSetupProcedure performs a calibration routine for the Tobii eye
        tracking system.
        """
        try:
            genv = TobiiPsychopyCalibrationGraphics(self, calibration_args)

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
        retrieved from the eye tracker device. This is the position on the
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
                
                data_delay = tobii_logged_time - (eye_data_event['system_time_stamp'] * self.DEVICE_TIMEBASE_TO_SEC)
        
                device_event_time = eye_data_event['device_time_stamp']
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
