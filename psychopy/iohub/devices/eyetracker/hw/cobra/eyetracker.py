# -*- coding: utf-8 -*-
"""
ioHub
Common Eye Tracker Interface for the TheEyeTribe system.
.. file: ioHub/devices/eyetracker/hw/cobra/eyetracker.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License
(GPL version 3 or any later version).

.. moduleauthor:: ????
.. fileauthor:: ???
"""

import numpy as np
from ..... import print2err, printExceptionDetailsToStdErr
from .....constants import EventConstants, EyeTrackerConstants
from .... import Computer
from ... import EyeTrackerDevice
from ...eye_events import *
from pycobra import CobraEyeTrackerClient

getTime = Computer.getTime


class EyeTracker(EyeTrackerDevice):
    """
    COBRA implementation of the Common Eye Tracker Interface can be used
    by providing the following EyeTracker path as the device class in 
    the iohub_config.yaml device settings file:
        
        eyetracker.hw.cobra.EyeTracker
        
    """

    # COBRA tracker times are received as sec
    #
    DEVICE_TIMEBASE_TO_SEC = 1.0
    EVENT_CLASS_NAMES = ['MonocularEyeSampleEvent', 'BinocularEyeSampleEvent',
                         'FixationStartEvent',
                         'FixationEndEvent', 'SaccadeStartEvent',
                         'SaccadeEndEvent',
                         'BlinkStartEvent', 'BlinkEndEvent']

    _cobra = None
    _calibration = None # Can hold dict or something with calibration info
                        # set using the sendCommand() interface method.
                        #
                        # TODO: Perhaps psychopy side calibration graphics,
                        # could be implemented using a tracker independent
                        # calibration routine. Code can use validation
                        # procedure code that already exists.
                        # Then any eye tracker that provides raw_x and raw_y
                        # data can use common calibration logic.
    _recording = False
    __slots__ = []

    def __init__(self, *args, **kwargs):
        EyeTrackerDevice.__init__(self, *args, **kwargs)

        # Used to hold the last sample processed by iohub.
        self._latest_sample = None

        # TODO: Implement when calibrated data is supported
        # Used to hold the last valid gaze position processed by ioHub.
        # If the last sample received from the COBRA indicates missing eye
        # position, then this is set to None
        #
        self._latest_gaze_position = None

        self.setConnectionState(True)

    def trackerTime(self):
        """
        Current eye tracker time in the eye tracker's native time base. 
        The COBRA system uses a sec.msec timebase.
        
        Args: 
            None
            
        Returns:
            float: current native eye tracker time. (in sec.msec for the COBRA)
        """
        if self._cobra:
            return self._cobra.getTrackerTime()
        return EyeTrackerConstants.EYETRACKER_ERROR

    def trackerSec(self):
        """
        Current eye tracker time, normalized to sec.msec format.

        Args: 
            None
            
        Returns:
            float: current native eye tracker time in sec.msec-usec format.
        """
        if self._cobra:
            return self.trackerTime() * self.DEVICE_TIMEBASE_TO_SEC
        return EyeTrackerConstants.EYETRACKER_ERROR

    def setConnectionState(self, enable):
        """
        setConnectionState is a no-op when using the COBRA system, as the
        connection is established when the cobra EyeTracker class is created,
        and remains active until the program ends, or a error occurs resulting
        in the loss of the tracker connection.

        Args:
            enable (bool): True = enable the connection, False = disable the
            connection.

        Return:
            bool: indicates the current connection state to the eye tracking
            hardware.
        """
        if enable is True and self._cobra is None:
            try:
                net_settings = self.getConfiguration().get('network_settings')
                broadcast_port = net_settings.get('broadcast_port')
                EyeTracker._cobra = CobraEyeTrackerClient(portnum=broadcast_port)
                return True
            except:
                print2err("Error connecting to cobra Device.")
                printExceptionDetailsToStdErr()
        elif enable is False and self._cobra is not None:
            try:
                EyeTracker._cobra.close()
                EyeTracker._cobra = None
                return False
            except:
                print2err("Error disconnecting from cobra Device.")
                printExceptionDetailsToStdErr()
        return EyeTrackerConstants.EYETRACKER_ERROR


    def isConnected(self):
        """
        isConnected returns whether the cobra is connected to the experiment PC
        and if the tracker state is valid. Returns True if the tracker can be 
        put into Record mode, etc and False if there is an error with the
        tracker
        or tracker connection with the experiment PC.

        Args:
            None
            
        Return:
            bool:  True = the eye tracking hardware is connected. False
            otherwise.

        """
        return self._cobra and self._cobra.isServerActive()

    def enableEventReporting(self, enabled=True):
        """
        enableEventReporting is functionally identical to the eye tracker
        device specific setRecordingState method.
        """

        try:
            if not self.isConnected():
                enabled = False
            enabled = EyeTrackerDevice.enableEventReporting(self, enabled)
            self.setRecordingState(enabled)
            return enabled
        except Exception, e:
            print2err("EyeTracker.enableEventReporting", str(e))

    def setRecordingState(self, recording):
        """
        setRecordingState is used to start or stop the recording of data from 
        the eye tracking device.
        
        args:
           recording (bool): if True, the eye tracker will start recordng
           available
              eye data and sending it to the experiment program if data
              streaming
              was enabled for the device. If recording == False, then the eye
              tracker stops recording eye data and streaming it to the
              experiment.
              
        If the eye tracker is already recording, and setRecordingState(True) is
        called, the eye tracker will simple continue recording and the method
        call
        is a no-op. Likewise if the system has already stopped recording and 
        setRecordingState(False) is called again.

        Args:
            recording (bool): if True, the eye tracker will start recordng
            data.; false = stop recording data.
           
        Return:trackerTime
            bool: the current recording state of the eye tracking device
        """
        if self._cobra is None:
            return False

        if recording is True:
            EyeTracker._cobra.open()
        else:
            EyeTracker._cobra.close()
            self._latest_gaze_position = None
            self._latest_sample = None

        EyeTracker._recording = recording
        return EyeTrackerDevice.enableEventReporting(self, recording)

    def isRecordingEnabled(self):
        """
        isRecordingEnabled returns the recording state from the eye tracking 
        device.

        Args:
           None
  
        Return:
            bool: True == the device is recording data; False == Recording is
            not occurring
        """
        return self._recording

    def getLastSample(self):
        """
        Returns the latest MonocularEyeSample retrieved from the COBRA device.

        Args: 
            None

        Returns:
            None: If the eye tracker is not currently recording data.
            otherwise a MonocularEyeSampleEvent is returned.
        """
        return self._latest_sample

    def getLastGazePosition(self):
        """
        Returns the last calculated x,y gaze position.
        TODO: Implement fort COBRA once calibration routine is working.
        """
        return self._latest_gaze_position

    def sendCommand(self, key, value=None):
        """
        Used by the COBRA eye tracker to inform the device of calibration
        related settings for raw -> gaze data conversion.
        """
        if key == 'CAL_CLEAR':
            EyeTracker._calibration = None
        else:
            print2err("COBRA EyeTracker.sendCommand ERROR: Unknown Key:Value of {0}: {1}".format(key, value))

    def _poll(self):
        """
        This method is called by the iohub server to check for new sample
        data from the COBRA server.

        Data Mapping Notes:
        -------------------

        Some fields of the sample event are used to hold values that do not
        correspond to what the event field name suggests. Currently:

        * confidence_interval: Used to hold tx_time of COBRA sample.
        * velocity_xy: Holds frame_num of COBRA sample.

        Monitoring Samples and COBRA Calibration
        -----------------------------------------

        Calibration for this system is done by psychopy and iohub, not by the
        COBRA server. TODO: Determine how to handle getting samples during
        the period of 'calibration'. Save to hdf5 file, etc.??
        """
        try:
            if not self.isConnected() or not self.isRecordingEnabled():
                return

            sample = self._cobra.getNextSample()
            if sample:
                logged_time = Computer.getTime()
                event_type = EventConstants.MONOCULAR_EYE_SAMPLE
                # TODO: Set to correct eye being tracked when supported by COBRA
                tracked_eye = EyeTrackerConstants.RIGHT_EYE

                status = sample.status
                # COBRA Status 0 == OK data, 1 == invalid data. Convert to iohub
                # status values ( 0 == OK, 2 == invalid right eye data)
                status = status * 2

                event_timestamp = sample.time
                event_delay = sample.delay
                iohub_time = logged_time - event_delay
                frame_num = sample.frame_num
                device_tx_time = sample.tx_time
                rawPupil = (sample.pupil_x, sample.pupil_y)
                pupilSize = sample.pupil_area

                gaze = (0.0, 0.0)

                if status == 0:
                    if self._calibration:
                        # Run raw data through calibration mapping....
                        gaze = self._raw2gaze(rawPupil)
                        gaze = self._eyeTrackerToDisplayCoords(gaze)
                    else:
                        gaze = (0.5, 0.5)

                    self._latest_gaze_position = gaze
                else:
                    self._latest_gaze_position = None

                monocSample = [
                    0,
                    0,
                    0,  # device id (not currently used)
                    Computer._getNextEventID(),
                    event_type,
                    event_timestamp,
                    logged_time,
                    iohub_time,
                    device_tx_time, # Using confidence interval to hold COBRA
                                    # sample tx_time field
                    event_delay,
                    0,
                    tracked_eye,
                    gaze[0],
                    gaze[1],
                    EyeTrackerConstants.UNDEFINED,
                    EyeTrackerConstants.UNDEFINED,
                    EyeTrackerConstants.UNDEFINED,
                    EyeTrackerConstants.UNDEFINED,
                    EyeTrackerConstants.UNDEFINED,
                    EyeTrackerConstants.UNDEFINED,
                    rawPupil[0],
                    rawPupil[1],
                    pupilSize,
                    EyeTrackerConstants.PUPIL_AREA,
                    EyeTrackerConstants.UNDEFINED,
                    EyeTrackerConstants.UNDEFINED,
                    EyeTrackerConstants.UNDEFINED,
                    EyeTrackerConstants.UNDEFINED,
                    EyeTrackerConstants.UNDEFINED,
                    EyeTrackerConstants.UNDEFINED,
                    frame_num, #using velocity_xy field to hold COBRA frame number
                    status
                    ]

                self._latest_sample = monocSample
                self._addNativeEventToBuffer(monocSample)
        except Exception:
            print2err("ERROR occurred during Cobra _poll.")
            printExceptionDetailsToStdErr()
        finally:
            return 0

    def _raw2gaze(self, raw_pos):
        """
        Converts a raw sensor position to a calibrated gaze position (2D).
        if ._calibration is None, return 0,0
        :param raw_pos:
        :return:
        """
        if self._calibration is None:
            return 0.0, 0.0
        else:
            # T0DO: ....
            pass

    def _getIOHubEventObject(self, native_event_data):
        """
        The _getIOHubEventObject method is called by the ioHub Process to
        convert
        new native device event objects that have been received to the
        appropriate
        ioHub Event type representation. 
        """
        return native_event_data

    def _eyeTrackerToDisplayCoords(self, eyetracker_point):
        """
        TODO: Update based on the COBRA calibrated gaze data space
        once implemented. Currently assumes gaze data from COBRA will be
        normalized from 0.0 to 1.0 in each dimension.

        Converts Cobra gaze positions to the Display device coordinate space.
        """
        try:
            gaze_x,gaze_y=eyetracker_point
            left,top,right,bottom=self._display_device.getCoordBounds()
            w,h=right-left,top-bottom
            return left+w*gaze_x,bottom+h*(1.0-gaze_y)

        except Exception, e:
            printExceptionDetailsToStdErr()

    def _displayToEyeTrackerCoords(self, display_x, display_y):
        """
        TODO: Update based on the COBRA calibrated gaze data space
        once implemented. Currently assumes gaze data from COBRA will be
        normalized from 0.0 to 1.0 in each dimension.

        Converts a Display device point to Cobra gaze position
        coordinate space.
        """
        try:
            left,top,right,bottom=self._display_device.getCoordBounds()
            w,h=right-left,top-bottom
            return (left-display_x)/w,(top-display_y)/h
        except Exception, e:
            printExceptionDetailsToStdErr()

    def _close(self):
        if self._cobra:
            self.enableEventReporting(False)
            self.setConnectionState(False)
        EyeTrackerDevice._close(self)