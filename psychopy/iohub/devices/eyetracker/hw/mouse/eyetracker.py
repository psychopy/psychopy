# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
from psychopy.iohub.errors import print2err, printExceptionDetailsToStdErr
from psychopy.iohub.constants import EyeTrackerConstants, EventConstants
from psychopy.iohub.devices import Computer, Device
from psychopy.iohub.devices.eyetracker import EyeTrackerDevice
from psychopy.iohub.devices.eyetracker.hw.mouse.calibration import MouseGazeCalibrationProcedure
import math
ET_UNDEFINED = EyeTrackerConstants.UNDEFINED
getTime = Computer.getTime


class EyeTracker(EyeTrackerDevice):
    """
    To start iohub with a Mouse Simulated eye tracker, add the full iohub device name
    as a kwarg passed to launchHubServer::

        eyetracker.hw.mouse.EyeTracker
              
    Examples:
        A. Start ioHub with the Mouse Simulated eye tracker::
    
            from psychopy.iohub import launchHubServer
            from psychopy.core import getTime, wait

            iohub_config = {'eyetracker.hw.mouse.EyeTracker': {}}
                
            io = launchHubServer(**iohub_config)
            
            # Get the eye tracker device.
            tracker = io.devices.tracker
            
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

    DEVICE_TIMEBASE_TO_SEC = 1.0
    EVENT_CLASS_NAMES = [
        'MonocularEyeSampleEvent',
        'FixationStartEvent',
        'FixationEndEvent',
        'SaccadeStartEvent',
        'SaccadeEndEvent',
        'BlinkStartEvent',
        'BlinkEndEvent']
    __slots__ = []
    _ioMouse = None
    _recording = False
    _eye_state = "NONE"
    _last_mouse_event_time = 0
    _ISI = 0.01  # Later set by runtime_settings.sampling_rate
    _saccade_threshold = 0.5 # Later set by runtime_settings.sampling_rate
    _move_eye_buttons = [False, False, False]
    _blink_eye_buttons = [False, False, False]
    _last_event_start = 0.0
    _last_start_event_pos = None
    _sacc_end_time = 0.0
    _sacc_amplitude = 0.0, 0.0
    _button_ix = dict(LEFT_BUTTON=0, MIDDLE_BUTTON=1, RIGHT_BUTTON=2)

    def __init__(self, *args, **kwargs):
        EyeTrackerDevice.__init__(self, *args, **kwargs)
        config = self.getConfiguration()
        # Used to hold the last sample processed by iohub.
        self._latest_sample = None
        # Calculate the desired ISI for the mouse sample stream.
        EyeTracker._ISI = 1.0/config.get('runtime_settings').get('sampling_rate')
        EyeTracker._saccade_threshold = config.get('controls').get('saccade_threshold')

        mb_list = config.get('controls').get('move')
        if isinstance(mb_list, str):
            mb_list = (mb_list,)
        if "CONTINUOUS" in mb_list:
            # CONTINUOUS == no buttons required to move == []
            mb_list = []

        bb_list = config.get('controls').get('blink')
        if isinstance(bb_list, str):
            bb_list = (bb_list,)

        for mb in mb_list:
            self._move_eye_buttons[self._button_ix.get(mb)] = True
        for mb in bb_list:
            self._blink_eye_buttons[self._button_ix.get(mb)] = True
        EyeTracker._move_eye_buttons = tuple(self._move_eye_buttons)
        EyeTracker._blink_eye_buttons = tuple(self._blink_eye_buttons)

        # Used to hold the last valid gaze position processed by ioHub.
        # If the last mouse tracker in a blink state, then this is set to None
        #
        self._latest_gaze_position = None

    def _connectMouse(self):
        if self._iohub_server:
            for dev in self._iohub_server.devices:
                if dev.__class__.__name__ == 'Mouse':
                    EyeTracker._ioMouse = dev

    def _poll(self):
        if self.isConnected() and self.isRecordingEnabled():
            if EyeTracker._last_mouse_event_time == 0:
                EyeTracker._last_mouse_event_time = getTime() - self._ISI
                # Start off mousegaze pos with current mouse position
                self._latest_gaze_position = self._ioMouse.getPosition()
            while getTime() - EyeTracker._last_mouse_event_time >= self._ISI:
                # Generate an eye sample every ISI seconds
                button_states = self._ioMouse.getCurrentButtonStates()

                last_gpos = self._latest_gaze_position

                if EyeTracker._eye_state == 'SACC' and getTime() >= EyeTracker._sacc_end_time:
                    # Create end saccade event.
                    end_pos = self._latest_gaze_position
                    start_pos = self._last_start_event_pos
                    self._addSaccadeEvent(False, start_pos, end_pos)
                    self._addFixationEvent(True)

                create_blink_start = False
                if button_states == self._blink_eye_buttons:
                    # In blink state....
                    # None means eyes are missing.
                    if self._latest_gaze_position:
                        # Blink just started, create event....
                        create_blink_start = True
                else:
                    if self._eye_state == "BLINK":
                        # Not in blink state anymore, create BlinkEndEvent
                        self._latest_gaze_position = self._ioMouse.getPosition()
                        self._addBlinkEvent(False)

                    if button_states == self._move_eye_buttons:
                        if self._eye_state == "FIX":
                            display = self._display_device
                            sacc_end_pos = self._ioMouse.getPosition()
                            sacc_start_pos = self._latest_gaze_position
                            spix = display._displayCoord2Pixel(sacc_start_pos[0], sacc_start_pos[1])
                            epix = display._displayCoord2Pixel(sacc_end_pos[0], sacc_end_pos[1])
                            sx = (epix[0]-spix[0])/display.getPixelsPerDegree()[0]
                            sy = (epix[1]-spix[1])/display.getPixelsPerDegree()[1]
                            sacc_amp_xy = math.fabs(math.hypot(sx, sy))
                            if sacc_amp_xy > EyeTracker._saccade_threshold:
                                EyeTracker._sacc_amplitude = sx, sy
                                self._addFixationEvent(False, sacc_start_pos)
                                self._addSaccadeEvent(True, sacc_start_pos, sacc_end_pos)
                            else:
                                self._latest_gaze_position = self._ioMouse.getPosition()
                        else:
                            self._latest_gaze_position = self._ioMouse.getPosition()

                if self._eye_state not in ["FIX","SACC"] and self._latest_gaze_position:
                    # Fixation start
                    self._addFixationEvent(True)
                elif self._eye_state == "FIX" and create_blink_start:
                    # Fixation End
                    self._addFixationEvent(False, last_gpos)

                if create_blink_start:
                    self._latest_gaze_position = None
                    self._addBlinkEvent(True)

                EyeTracker._last_mouse_event_time += self._ISI
                next_sample_time = EyeTracker._last_mouse_event_time
                self._addSample(next_sample_time)

    def _addSaccadeEvent(self, startEvent, sacc_start_pos, sacc_end_pos):
        stime = EyeTracker._last_mouse_event_time
        if startEvent:
            eye_evt = [0, 0, 0, Device._getNextEventID(), EventConstants.SACCADE_START,
                       stime, stime, stime, 0, 0, 0, EyeTrackerConstants.RIGHT_EYE,
                       sacc_start_pos[0], sacc_start_pos[1], ET_UNDEFINED,  ET_UNDEFINED, ET_UNDEFINED,
                       ET_UNDEFINED, ET_UNDEFINED, 5, EyeTrackerConstants.PUPIL_DIAMETER_MM,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, 0]
            EyeTracker._eye_state = 'SACC'
            EyeTracker._last_event_start = stime
            sacc_amp_xy = math.fabs(math.hypot(*EyeTracker._sacc_amplitude))
            saccade_duration = 2.2 * sacc_amp_xy + 21.0
            saccade_duration = saccade_duration/1000.0 # convert to seconds
            EyeTracker._sacc_end_time = stime + saccade_duration
            EyeTracker._last_start_event_pos = sacc_start_pos
            self._latest_gaze_position = sacc_end_pos
        else:

            start_event_time = EyeTracker._last_event_start
            end_event_time = EyeTracker._sacc_end_time
            event_duration = end_event_time - start_event_time
            s_gaze = sacc_start_pos
            s_pupilsize = 4

            e_gaze = sacc_end_pos
            e_pupilsize = 5

            eye_evt = [0, 0, 0, Device._getNextEventID(), EventConstants.SACCADE_END,
                       end_event_time, end_event_time, end_event_time, 0, 0, 0, EyeTrackerConstants.RIGHT_EYE,
                       event_duration,
                       EyeTracker._sacc_amplitude[0], # e_amp[0],
                       EyeTracker._sacc_amplitude[1], # e_amp[1],
                       0, # e_angle,
                       s_gaze[0], s_gaze[1],
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                       s_pupilsize, EyeTrackerConstants.PUPIL_DIAMETER_MM,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                       e_gaze[0], e_gaze[1],
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                       e_pupilsize, EyeTrackerConstants.PUPIL_DIAMETER_MM,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, 0]
            EyeTracker._eye_state = 'FIX'
            EyeTracker._sacc_end_time = 0

        self._addNativeEventToBuffer(eye_evt)

    def _addFixationEvent(self, startEvent, end_pos=None):
        ftime = EyeTracker._last_mouse_event_time
        gaze = self._latest_gaze_position
        if startEvent:
            eye_evt = [0, 0, 0, Device._getNextEventID(), EventConstants.FIXATION_START,
                       ftime, ftime, ftime, 0, 0, 0, EyeTrackerConstants.RIGHT_EYE,
                       gaze[0], gaze[1], ET_UNDEFINED,  ET_UNDEFINED, ET_UNDEFINED,
                       ET_UNDEFINED, ET_UNDEFINED, 5, EyeTrackerConstants.PUPIL_DIAMETER_MM,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, 0]
            EyeTracker._last_event_start = ftime
            EyeTracker._last_start_event_pos = gaze
            EyeTracker._eye_state = "FIX"
        else:
            start_event_time = EyeTracker._last_event_start
            end_event_time = ftime
            event_duration = end_event_time - start_event_time
            s_gaze = self._last_start_event_pos
            e_gaze = end_pos
            a_gaze = (s_gaze[0]+e_gaze[0])/2, (s_gaze[1]+e_gaze[1])/2

            EyeTracker._last_event_start = 0.0
            EyeTracker._last_start_event_pos = None

            eye_evt = [0, 0, 0, Device._getNextEventID(), EventConstants.FIXATION_END,
                       ftime, ftime, ftime, 0, 0, 0, EyeTrackerConstants.RIGHT_EYE,
                       event_duration, s_gaze[0], s_gaze[1], ET_UNDEFINED,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                       4, EyeTrackerConstants.PUPIL_DIAMETER_MM, ET_UNDEFINED,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                       e_gaze[0], e_gaze[1], ET_UNDEFINED,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                       5, EyeTrackerConstants.PUPIL_DIAMETER_MM,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                       a_gaze[0], a_gaze[1], ET_UNDEFINED,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                       4.5, EyeTrackerConstants.PUPIL_DIAMETER_MM, ET_UNDEFINED,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                       ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                       ET_UNDEFINED, 0]

        self._addNativeEventToBuffer(eye_evt)

    def _addBlinkEvent(self, startEvent):
        btime = EyeTracker._last_mouse_event_time
        if startEvent:
            # Create a blink start
            EyeTracker._last_event_start = btime
            EyeTracker._eye_state = "BLINK"
            eye_evt = [0, 0, 0,  # device id (not currently used)
                       Device._getNextEventID(), EventConstants.BLINK_START,
                       btime, btime, btime,
                       0, 0, 0, EyeTrackerConstants.RIGHT_EYE, 0]
        else:
            # Create a blink end
            eye_evt = [
                        0,
                        0,
                        0,
                        Device._getNextEventID(),
                        EventConstants.BLINK_END,
                        btime,
                        btime,
                        btime,
                        0,
                        0,
                        0,
                        EyeTrackerConstants.RIGHT_EYE,
                        btime - EyeTracker._last_event_start,
                        0
                    ]
            EyeTracker._last_event_start = 0.0
        self._addNativeEventToBuffer(eye_evt)

    def _addSample(self, sample_time):
        if self._latest_gaze_position:
            gx, gy = self._latest_gaze_position
            status = 0
        else:
            gx, gy = EyeTrackerConstants.UNDEFINED, EyeTrackerConstants.UNDEFINED
            status = 2

        pupilSize = 5
        monoSample = [0, 0, 0, Device._getNextEventID(), EventConstants.MONOCULAR_EYE_SAMPLE,
                      sample_time, sample_time, sample_time,
                      0, 0, 0,
                      EyeTrackerConstants.RIGHT_EYE, gx, gy,
                      ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                      ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                      pupilSize, EyeTrackerConstants.PUPIL_DIAMETER_MM,
                      ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                      ET_UNDEFINED, ET_UNDEFINED, ET_UNDEFINED,
                      status
                      ]
        self._latest_sample = monoSample
        self._addNativeEventToBuffer(monoSample)

    def trackerTime(self):
        """
        Current eye tracker time.

        Returns:
            float: current eye tracker time in seconds.
        """
        return getTime()

    def trackerSec(self):
        """
        Same as trackerTime().
        """
        return getTime()

    def setConnectionState(self, enable):
        """
        When 'connected', the Mouse Simulated Eye Tracker taps into the ioHub Mouse event stream.
        """
        if enable and self._ioMouse is None:
            self._connectMouse()
        elif enable is False and self._ioMouse:
            EyeTracker._ioMouse = None
        return self.isConnected()

    def isConnected(self):
        """
        """
        return self._ioMouse is not None

    def enableEventReporting(self, enabled=True):
        """enableEventReporting is functionally identical to the eye tracker
        device specific setRecordingState method."""

        try:
            self.setRecordingState(enabled)
            enabled = EyeTrackerDevice.enableEventReporting(self, enabled)
            return enabled
        except Exception as e:
            print2err('Exception in EyeTracker.enableEventReporting: ', str(e))
            printExceptionDetailsToStdErr()

    def setRecordingState(self, recording):
        """
        setRecordingState is used to start or stop the recording of data
        from the eye tracking device.
        """
        current_state = self.isRecordingEnabled()
        if recording is True and current_state is False:
            EyeTracker._recording = True
            if self._ioMouse is None:
                self._connectMouse()
        elif recording is False and current_state is True:
            EyeTracker._recording = False
            self._latest_sample = None
            EyeTracker._last_mouse_event_time = 0
        return EyeTrackerDevice.enableEventReporting(self, recording)

    def isRecordingEnabled(self):
        """
        isRecordingEnabled returns the recording state from the eye tracking device.

        Return:
            bool: True == the device is recording data; False == Recording is not occurring
        """
        return self._recording

    def runSetupProcedure(self, calibration_args={}):
        """
        runSetupProcedure displays a mock calibration procedure. No calibration is actually done.
        """
        calibration = MouseGazeCalibrationProcedure(self, calibration_args)
        cal_run = calibration.runCalibration()
        calibration.window.close()

        calibration._unregisterEventMonitors()
        calibration.clearAllEventBuffers()

        if cal_run:
            return {"RESULT": "CALIBRATION_OK"}
        else:
            return {"RESULT": "CALIBRATION_ABORTED"}

    def _getIOHubEventObject(self, native_event_data):
        """The _getIOHubEventObject method is called by the ioHub Process to
        convert new native device event objects that have been received to the
        appropriate ioHub Event type representation."""
        self._latest_sample = native_event_data
        return self._latest_sample

    def _eyeTrackerToDisplayCoords(self, eyetracker_point=()):
        """Converts MouseGaze positions to the Display device coordinate space.
        """

        return eyetracker_point[0], eyetracker_point[1]

    def _displayToEyeTrackerCoords(self, display_x, display_y):
        """Converts a Display device point to MouseGaze position coordinate
        space.
        """
        return display_x, display_y

    def _close(self):
        self.setRecordingState(False)
        self.setConnectionState(False)
        EyeTrackerDevice._close(self)
