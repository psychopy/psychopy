# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
from collections import defaultdict
from datetime import time
from psychopy.iohub.constants import EventConstants, EyeTrackerConstants
from psychopy.iohub.devices import Computer, Device
from psychopy.iohub.devices.eyetracker import EyeTrackerDevice, MonocularEyeSampleEvent, BinocularEyeSampleEvent
from psychopy.iohub.devices.eyetracker.eye_events import *


from psychopy.iohub.devices.eyetracker.hw.pupil_labs.pupil_core.pupil_remote import PupilRemote
from psychopy.iohub.devices.eyetracker.hw.pupil_labs.pupil_core.data_parse import eye_sample_from_gaze_3d, gaze_position_from_gaze_3d
from psychopy.iohub.devices.eyetracker.hw.pupil_labs.pupil_core.bisector import MutableBisector


class EyeTracker(EyeTrackerDevice):
    """The EyeTrackerDevice class is the main class for the ioHub Common Eye
    Tracker interface.

    The Common Eye Tracker Interface--a set of common functions and methods
    such that the same experiment script and data analyses can be shared,
    used, and compared regardless of the actual eye tracker used--works by
    extending the EyeTrackerDevice class to configure device monitoring and
    data access to individual eye tracker manufacturers and models.

    Not every EyeTrackerDevice subclass will support all of the umbrella functionality
    within the Common Eye Tracker Interface, but a core set of critical functions are
    supported by all eye tracker models to date. Any Common Eye Tracker Interface
    method not supported by the configured Eye Tracker hardware returns a constant
    (EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED).

    Methods in the EyeTrackerDevice class are broken down into several categories:

    #. Initializing the Eye Tracker / Setting the Device State.
    #. Defining the Graphics Layer for Calibration / System Setup.
    #. Starting and Stopping of Data Recording.
    #. Sending Messages or Codes to Synchronize the ioHub with the Eye Tracker.
    #. Accessing Eye Tracker Data During Recording.
    #. Accessing the Eye Tracker native time base.
    #. Synchronizing the ioHub time base with the Eye Tracker time base

    .. note::

        Only **one** instance of EyeTracker can be created within an experiment.
        Attempting to create > 1 instance will raise an exception.

    """

    # EyeTrackerDevice Interface

    # #: The multiplier needed to convert a device's native time base to sec.msec-usec times.
    # DEVICE_TIMEBASE_TO_SEC = 1.0

    # Used by pyEyeTrackerDevice implementations to store relationships between an eye
    # trackers command names supported for EyeTrackerDevice sendCommand method and
    # a private python function to call for that command. This allows an implementation
    # of the interface to expose functions that are not in the core EyeTrackerDevice spec
    # without have to use the EXT extension class.
    _COMMAND_TO_FUNCTION = {}

    EVENT_CLASS_NAMES = [
        "MonocularEyeSampleEvent",
        "BinocularEyeSampleEvent",
    ]

    def __init__(self, *args, **kwargs):
        EyeTrackerDevice.__init__(self, *args, **kwargs)

        self._latest_sample = None
        self._latest_gaze_position = None
        self._actively_recording = False

        self._surface_name = self._runtime_settings["surface_name"]

        pupil_remote_settings = self._runtime_settings["pupil_remote"]
        self._pupil_remote_ip_address = pupil_remote_settings["ip_address"]
        self._pupil_remote_port = pupil_remote_settings["port"]
        self._pupil_remote_timeout_ms = pupil_remote_settings["timeout_ms"]
        self._pupil_remote_subscriptions = ["gaze.3d.", self.surface_topic]

        capture_recording_settings = self._runtime_settings["pupil_capture_recording"]
        self._capture_recording_enabled = capture_recording_settings["enabled"]
        self._capture_recording_location = capture_recording_settings["location"]

        self._gaze_bisectors_by_topic = defaultdict(MutableBisector)
        self._pupil_remote = None
        self.setConnectionState(True)

    @property
    def surface_topic(self):
        return f"surfaces.{self._surface_name}"

    def trackerTime(self):
        """trackerTime returns the current time reported by the eye tracker
        device. The time base is implementation dependent.

        Args:
            None

        Return:
            float: The eye tracker hardware's reported current time.

        """
        return self._psychopyTimeInTrackerTime(Computer.getTime())

    def trackerSec(self):
        """
        trackerSec takes the time received by the EyeTracker.trackerTime() method
        and returns the time in sec.usec-msec format.

        Args:
            None

        Return:
            float: The eye tracker hardware's reported current time in sec.msec-usec format.
        """
        return self.trackerTime()

    def setConnectionState(self, enable):
        """setConnectionState either connects ( setConnectionState(True) ) or
        disables ( setConnectionState(False) ) active communication between the
        ioHub and the Eye Tracker.

        .. note::
            A connection to the Eye Tracker is automatically established
            when the ioHub Process is initialized (based on the device settings
            in the iohub_config.yaml), so there is no need to
            explicitly call this method in the experiment script.

        .. note::
            Connecting an Eye Tracker to the ioHub does **not** necessarily collect and send
            eye sample data to the ioHub Process. To start actual data collection,
            use the Eye Tracker method setRecordingState(bool) or the ioHub Device method (device type
            independent) enableEventRecording(bool).

        Args:
            enable (bool): True = enable the connection, False = disable the connection.

        Return:
            bool: indicates the current connection state to the eye tracking hardware.

        """
        if enable and self._pupil_remote is None:
            self._pupil_remote = PupilRemote(
                subscription_topics=self._pupil_remote_subscriptions,
                ip_address=self._pupil_remote_ip_address,
                port=self._pupil_remote_port,
                timeout_ms=self._pupil_remote_timeout_ms,
            )
        elif not enable and self._pupil_remote is not None:
            self._pupil_remote.cleanup()
            self._pupil_remote = None

    def isConnected(self):
        """isConnected returns whether the ioHub EyeTracker Device is connected
        to the eye tracker hardware or not. An eye tracker must be connected to
        the ioHub for any of the Common Eye Tracker Interface functionality to
        work.

        Args:
            None

        Return:
            bool:  True = the eye tracking hardware is connected. False otherwise.

        """
        return self._pupil_remote is not None

    def runSetupProcedure(self, calibration_args={}):
        """
        The runSetupProcedure method starts the eye tracker calibration
        routine. If calibration_args are provided, they should be used to
        update calibration related settings prior to starting the calibration.

        The details of this method are implementation-specific.

        .. note::
            This is a blocking call for the PsychoPy Process
            and will not return to the experiment script until the necessary steps
            have been completed so that the eye tracker is ready to start collecting
            eye sample data when the method returns.

        Args:
            None
        """
        return self._pupil_remote.start_calibration()

    def setRecordingState(self, should_be_recording):
        """The setRecordingState method is used to start or stop the recording
        and transmission of eye data from the eye tracking device to the ioHub
        Process.

        Args:
            recording (bool): if True, the eye tracker will start recordng data.; false = stop recording data.

        Return:
            bool: the current recording state of the eye tracking device

        """
        if not self.isConnected():
            return False
        if self._capture_recording_enabled:
            if should_be_recording:
                self._pupil_remote.start_recording(
                    rec_name=self._capture_recording_location
                )
            else:
                self._pupil_remote.stop_recording()
            self._actively_recording = self._pupil_remote.is_recording
        else:
            self._actively_recording = should_be_recording

        is_recording_enabled = self.isRecordingEnabled()

        if not is_recording_enabled:
            self._latest_sample = None
            self._latest_gaze_position = None

        return is_recording_enabled

    def isRecordingEnabled(self):
        """The isRecordingEnabled method indicates if the eye tracker device is
        currently recording data.

        Args:
           None

        Return:
            bool: True == the device is recording data; False == Recording is not occurring

        """
        if not self.isConnected():
            return False
        return self._actively_recording

    def getLastSample(self):
        """The getLastSample method returns the most recent eye sample received
        from the Eye Tracker. The Eye Tracker must be in a recording state for
        a sample event to be returned, otherwise None is returned.

        Args:
            None

        Returns:
            int: If this method is not supported by the eye tracker interface, EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED is returned.

            None: If the eye tracker is not currently recording data.

            EyeSample: If the eye tracker is recording in a monocular tracking mode, the latest sample event of this event type is returned.

            BinocularEyeSample:  If the eye tracker is recording in a binocular tracking mode, the latest sample event of this event type is returned.

        """
        return self._latest_sample

    def getLastGazePosition(self):
        """The getLastGazePosition method returns the most recent eye gaze
        position received from the Eye Tracker. This is the position on the
        calibrated 2D surface that the eye tracker is reporting as the current
        eye position. The units are in the units in use by the ioHub Display
        device.

        If binocular recording is being performed, the average position of both
        eyes is returned.

        If no samples have been received from the eye tracker, or the
        eye tracker is not currently recording data, None is returned.

        Args:
            None

        Returns:
            int: If this method is not supported by the eye tracker interface, EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED is returned.

            None: If the eye tracker is not currently recording data or no eye samples have been received.

            tuple: Latest (gaze_x,gaze_y) position of the eye(s)
        """
        return self._latest_gaze_position

    def _poll(self):
        if not self.isConnected():
            return

        logged_time = Computer.getTime()

        for topic, payload in self._pupil_remote.fetch():
            if topic.startswith("gaze.3d."):
                gaze_bisector = self._gaze_bisectors_by_topic[topic]
                gaze_bisector.insert(
                    datum=payload,
                    timestamp=payload["timestamp"]
                )
                # Remove gaze datums older than 3sec (200Hz)
                if len(gaze_bisector) >= 200 * 3:
                    gaze_bisector.delete(index=0)
            if topic == self.surface_topic:
                for gaze_on_surface in payload["gaze_on_surfaces"]:
                    if gaze_on_surface["on_surf"] is not True:
                        continue
                    gaze_topic, gaze_timestamp = gaze_on_surface["base_data"]
                    gaze_bisector = self._gaze_bisectors_by_topic[gaze_topic]
                    try:
                        gaze_datum = gaze_bisector.find_datum_by_timestamp(
                            timestamp=gaze_timestamp
                        )
                    except ValueError:
                        # Skip surface-mapped gaze if no gaze is avalable
                        return
                    self._add_gaze_sample(
                        surface_datum=payload,
                        gaze_on_surface_datum=gaze_on_surface,
                        gaze_datum=gaze_datum,
                        logged_time=logged_time
                    )

    def _add_gaze_sample(self, surface_datum, gaze_on_surface_datum, gaze_datum, logged_time):

        native_time = gaze_datum["timestamp"]
        iohub_time = self._trackerTimeInPsychopyTime(native_time)

        metadata = {
            'experiment_id': 0,  # experiment_id, iohub fills in automatically
            'session_id': 0,  # session_id, iohub fills in automatically
            'device_id': 0,  # device_id, keep at 0
            'event_id': Device._getNextEventID(),  # iohub event unique ID
            'device_time': native_time,
            'logged_time': logged_time,
            'time': iohub_time,
            'confidence_interval': -1.0,
            'delay': (logged_time - iohub_time),
            'filter_id': False,
        }

        sample = eye_sample_from_gaze_3d(
            surface_datum, gaze_on_surface_datum, gaze_datum, metadata)
        position = gaze_position_from_gaze_3d(
            surface_datum, gaze_on_surface_datum, gaze_datum)

        self._addNativeEventToBuffer(sample)

        self._latest_sample = sample
        self._latest_gaze_position = position

    def _psychopyTimeInTrackerTime(self, psychopy_time):
        return psychopy_time + self._pupil_remote.psychopy_pupil_clock_offset

    def _trackerTimeInPsychopyTime(self, tracker_time):
        return tracker_time - self._pupil_remote.psychopy_pupil_clock_offset

    def __del__(self):
        """Do any final cleanup of the eye tracker before the object is
        destroyed."""
        self.setRecordingState(False)
        self.setConnectionState(False)
        self.__class__._INSTANCE = None
