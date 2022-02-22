# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import logging
from collections import defaultdict
from sys import flags
from typing import Optional, Dict, Tuple, Union

from psychopy.iohub.constants import EyeTrackerConstants
from psychopy.iohub.devices import Computer, Device
from psychopy.iohub.devices.eyetracker import EyeTrackerDevice
from psychopy.iohub.devices.eyetracker.hw.pupil_labs.pupil_core import (
    data_parse,
    pupil_remote,
)
from psychopy.iohub.devices.eyetracker.hw.pupil_labs.pupil_core.bisector import (
    DatumNotFoundError,
    MutableBisector,
)
from psychopy.iohub.errors import print2err, printExceptionDetailsToStdErr

logger = logging.getLogger(__name__)


class EyeTracker(EyeTrackerDevice):
    """
    Implementation of the :py:class:`Common Eye Tracker Interface <.EyeTrackerDevice>`
    for the Pupil Core headset.

    Uses ioHub's polling method to process data from `Pupil Capture's Network API
    <https://docs.pupil-labs.com/developer/core/network-api/>`_.

    To synchronize time between Pupil Capture and PsychoPy, the integration estimates
    the offset between their clocks and applies it to the incoming data. This step
    effectively transforms time between the two softwares while taking the transmission
    delay into account. For details, see this `real-time time-sync tutorial
    <https://github.com/pupil-labs/pupil-helpers/blob/master/python/simple_realtime_time_sync.py>`_.

    This class operates in two modes, depending on the ``pupillometry_only`` runtime
    setting:

    #. Pupillometry-only mode
        If the ``pupillometry_only`` setting is to ``True``, the integration will only
        receive eye-camera based metrics, e.g. pupil size, its location in eye camera
        coordinates, etc. The advatage of this mode is that it does not require
        calibrating the eye tracker or setting up AprilTag markers for the AoI tracking.
        To receive gaze data in PsychoPy screen coordinates, see the Pupillometry+Gaze
        mode below.

        Internally, this is implemented by subscribing to the ``pupil.`` data topic.

    #. Pupillometry+Gaze mode
        If the ``Pupillometry only`` setting is set to ``False``, the integration will
        receive positional data in addition to the pupillometry data mentioned above.
        For this to work, one has to setup Pupil Capture's built-in AoI tracking system
        and perform a calibration for each subject.

        The integration takes care of translating the spatial coordinates to PsychoPy
        display coordinates.

        Internally, this mode is implemented by subscribing to the ``gaze.3d.`` and the
        corresponding surface name data topics.only

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

    def __init__(self, *args, **kwargs) -> None:
        EyeTrackerDevice.__init__(self, *args, **kwargs)

        self._latest_sample = None
        self._latest_gaze_position = None
        self._actively_recording = False

        self._surface_name = self._runtime_settings["surface_name"]
        self._confidence_threshold = self._runtime_settings["confidence_threshold"]

        pupil_remote_settings = self._runtime_settings["pupil_remote"]
        self._pupil_remote_ip_address = pupil_remote_settings["ip_address"]
        self._pupil_remote_port = pupil_remote_settings["port"]
        self._pupil_remote_timeout_ms = pupil_remote_settings["timeout_ms"]
        if self._runtime_settings["pupillometry_only"]:
            self._pupil_remote_subscriptions = ["pupil"]
        else:
            self._pupil_remote_subscriptions = ["gaze.3d.", self.surface_topic]
        # Calibration notifications are only being handled during runSetupProcedure()
        # and are otherwise ignored.
        self._pupil_remote_subscriptions.append("notify.calibration")

        capture_recording_settings = self._runtime_settings["pupil_capture_recording"]
        self._capture_recording_enabled = capture_recording_settings["enabled"]
        self._capture_recording_location = capture_recording_settings["location"]

        self._gaze_bisectors_by_topic = defaultdict(MutableBisector)
        self._pupil_remote = None
        self.setConnectionState(True)

    @property
    def surface_topic(self) -> str:
        """Read-ony Pupil Capture subscription topic to receive data from the configured
        surface"""
        return f"surfaces.{self._surface_name}"

    def trackerTime(self) -> float:
        """Returns the current time reported by the eye tracker device.

        Implementation measures the current time in PsychoPy time and applies the
        estimated clock offset to transform the measurement into tracker time.

        :return: The eye tracker hardware's reported current time.

        """
        return self._psychopyTimeInTrackerTime(Computer.getTime())

    def trackerSec(self) -> float:
        """
        Returns :py:func:`.EyeTracker.trackerTime`

        :return: The eye tracker hardware's reported current time in sec.msec-usec format.
        """
        return self.trackerTime()

    def setConnectionState(self, enable: bool) -> None:
        """setConnectionState either connects (``setConnectionState(True)``) or
        disables (``setConnectionState(False)``) active communication between the
        ioHub and Pupil Capture.

        .. note::
            A connection to the Eye Tracker is automatically established
            when the ioHub Process is initialized (based on the device settings
            in the iohub_config.yaml), so there is no need to
            explicitly call this method in the experiment script.

        .. note::
            Connecting an Eye Tracker to the ioHub does **not** necessarily collect and
            send eye sample data to the ioHub Process. To start actual data collection,
            use the Eye Tracker method ``setRecordingState(bool)`` or the ioHub Device
            method (device type independent) ``enableEventRecording(bool)``.

        Args:
            enable (bool): True = enable the connection, False = disable the connection.

        :return:
            bool: indicates the current connection state to the eye tracking hardware.
        """
        if enable and self._pupil_remote is None:
            self._pupil_remote = pupil_remote.PupilRemote(
                subscription_topics=self._pupil_remote_subscriptions,
                ip_address=self._pupil_remote_ip_address,
                port=self._pupil_remote_port,
                timeout_ms=self._pupil_remote_timeout_ms,
            )
        elif not enable and self._pupil_remote is not None:
            self._pupil_remote.cleanup()
            self._pupil_remote = None

    def isConnected(self) -> bool:
        """isConnected returns whether the ioHub EyeTracker Device is connected
        to Pupil Capture or not. A Pupil Core headset must be connected and working
        properly for any of the Common Eye Tracker Interface functionality to work.

        Args:
            None

        :return:
            bool:  True = the eye tracking hardware is connected. False otherwise.

        """
        return self._pupil_remote is not None

    def runSetupProcedure(self, calibration_args: Optional[Dict] =None) -> int:
        """
        The runSetupProcedure method starts the Pupil Capture calibration choreography.

        .. note::
            This is a blocking call for the PsychoPy Process and will not return to the
            experiment script until the calibration procedure was either successful,
            aborted, or failed.

        :param calibration_args: This argument will be ignored and has only been added
            for the purpose of compatibility with the Common Eye Tracker Interface
        
        :return:
            - :py:attr:`.EyeTrackerConstants.EYETRACKER_OK`
                if the calibration was succesful
            - :py:attr:`.EyeTrackerConstants.EYETRACKER_SETUP_ABORTED`
                if the choreography was aborted by the user
            - :py:attr:`.EyeTrackerConstants.EYETRACKER_CALIBRATION_ERROR`
                if the calibration failed, check logs for details
            - :py:attr:`.EyeTrackerConstants.EYETRACKER_ERROR`
                if any other error occured, check logs for details
        """
        self._pupil_remote.start_calibration()
        logger.info("Waiting for calibration to complete")
        try:
            for topic, payload in self._pupil_remote.fetch(endless=True):
                if topic.startswith("notify.calibration"):
                    if topic.endswith("successful"):
                        return EyeTrackerConstants.EYETRACKER_OK
                    elif topic.endswith("stopped"):
                        return EyeTrackerConstants.EYETRACKER_SETUP_ABORTED
                    elif topic.endswith("failed"):
                        print2err(f"Calibration failed: {payload}")
                        return EyeTrackerConstants.EYETRACKER_CALIBRATION_ERROR
                    elif "setup" in topic or "should" in topic or "start" in topic:
                        # ignore setup data notification (includes raw reference and
                        # pupil data that can be used to reproduce the calibration),
                        # and calibration should_start/stop + started notifications.
                        pass
                    else:
                        print2err(f"Handling for {topic} not implemented ({payload})")
        except Exception:
            print2err("Error during runSetupProcedure")
            printExceptionDetailsToStdErr()
        return EyeTrackerConstants.EYETRACKER_ERROR

    def setRecordingState(self, should_be_recording: bool) -> bool:
        """The setRecordingState method is used to start or stop the recording
        and transmission of eye data from the eye tracking device to the ioHub
        Process.

        If the ``pupil_capture_recording.enabled`` runtime setting is set to ``True``,
        a corresponding raw recording within Pupil Capture will be started or stopped.

        ``should_be_recording`` will also be passed to
        :py:func:`.EyeTrackerDevice.enableEventReporting`.

        Args:
            recording (bool): if True, the eye tracker will start recordng data.;
                false = stop recording data.

        :return:
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

        return EyeTrackerDevice.enableEventReporting(self, self._actively_recording)

    def isRecordingEnabled(self) -> bool:
        """The isRecordingEnabled method indicates if the eye tracker device is
        currently recording data.

        :return: ``True`` == the device is recording data; ``False`` == Recording is not
            occurring

        """
        if not self.isConnected():
            return False
        return self._actively_recording

    def getLastSample(self) -> Union[
        None,
        "psychopy.iohub.devices.eyetracker.MonocularEyeSampleEvent",
        "psychopy.iohub.devices.eyetracker.BinocularEyeSampleEvent",
    ]:
        """The getLastSample method returns the most recent eye sample received
        from the Eye Tracker. The Eye Tracker must be in a recording state for
        a sample event to be returned, otherwise None is returned.

        :return:

            - MonocularEyeSampleEvent:
                Gaze mapping result from a single pupil detection.
                Only emitted if a second eye camera is not being operated or the
                confidence of the pupil detection was insufficient for a binocular pair.
                See also this high-level overview of the `Pupil Capture Data Matching
                algorithm <https://github.com/N-M-T/pupil-docs/commit/1dafe298565720a4bb7500a245abab7a6a2cd92f>`_
            - BinocularEyeSample:
                Gaze mapping result from two combined pupil detections
            - None:
                If the eye tracker is not currently recording data.

        """
        return self._latest_sample

    def getLastGazePosition(self) -> Optional[Tuple[float,float]]:
        """The getLastGazePosition method returns the most recent eye gaze
        position received from the Eye Tracker. This is the position on the
        calibrated 2D surface that the eye tracker is reporting as the current
        eye position. The units are in the units in use by the ioHub Display
        device.

        If binocular recording is being performed, the average position of both
        eyes is returned.

        If no samples have been received from the eye tracker, or the
        eye tracker is not currently recording data, None is returned.

        :return:

            - None:
                If the eye tracker is not currently recording data or no eye samples
                have been received.

            - tuple:
                Latest (gaze_x,gaze_y) position of the eye(s)
        """
        return self._latest_gaze_position

    def _poll(self):
        if not self.isConnected():
            return

        logged_time = Computer.getTime()

        for topic, payload in self._pupil_remote.fetch():
            if topic.startswith("gaze.3d."):
                self._cache_gaze_datum(topic, payload)
            if topic == self.surface_topic:
                for gaze_on_surface in payload["gaze_on_surfaces"]:
                    if gaze_on_surface["on_surf"] is not True:
                        continue
                    if gaze_on_surface["confidence"] < self._confidence_threshold:
                        continue
                    gaze_datum = self._lookup_corresponding_gaze_datum(gaze_on_surface)
                    if gaze_datum is None:
                        continue  # Skip surface-mapped gaze if no gaze is avalable
                    self._add_gaze_sample(
                        gaze_on_surface_datum=gaze_on_surface,
                        gaze_datum=gaze_datum,
                        logged_time=logged_time,
                    )
            if (
                topic.startswith("pupil")
                and payload["confidence"] < self._confidence_threshold
            ):
                self._add_pupil_sample(pupil_datum=payload, logged_time=logged_time)

    def _lookup_corresponding_gaze_datum(self, gaze_on_surface):
        gaze_topic, gaze_timestamp = gaze_on_surface["base_data"]
        gaze_bisector = self._gaze_bisectors_by_topic[gaze_topic]
        try:
            return gaze_bisector.find_datum_by_timestamp(timestamp=gaze_timestamp)
        except DatumNotFoundError:
            pass

    def _cache_gaze_datum(self, topic, payload):
        gaze_bisector = self._gaze_bisectors_by_topic[topic]
        gaze_bisector.insert(datum=payload, timestamp=payload["timestamp"])
        # Remove gaze datums older than 3sec (200Hz)
        if len(gaze_bisector) >= 200 * 3:
            gaze_bisector.delete(index=0)

    def _add_gaze_sample(self, gaze_on_surface_datum, gaze_datum, logged_time):

        native_time = gaze_datum["timestamp"]
        iohub_time = self._trackerTimeInPsychopyTime(native_time)

        metadata = {
            "experiment_id": 0,  # experiment_id, iohub fills in automatically
            "session_id": 0,  # session_id, iohub fills in automatically
            "device_id": 0,  # device_id, keep at 0
            "event_id": Device._getNextEventID(),  # iohub event unique ID
            "device_time": native_time,
            "logged_time": logged_time,
            "time": iohub_time,
            "confidence_interval": -1.0,
            "delay": (logged_time - iohub_time),
            "filter_id": False,
        }

        position = self._gaze_in_display_coords(gaze_on_surface_datum)
        sample = data_parse.eye_sample_from_gaze_3d(position, gaze_datum, metadata)

        self._addNativeEventToBuffer(sample)

        self._latest_sample = sample
        self._latest_gaze_position = position

    def _add_pupil_sample(self, pupil_datum, logged_time):
        native_time = pupil_datum["timestamp"]
        iohub_time = self._trackerTimeInPsychopyTime(native_time)

        metadata = {
            "experiment_id": 0,  # experiment_id, iohub fills in automatically
            "session_id": 0,  # session_id, iohub fills in automatically
            "device_id": 0,  # device_id, keep at 0
            "event_id": Device._getNextEventID(),  # iohub event unique ID
            "device_time": native_time,
            "logged_time": logged_time,
            "time": iohub_time,
            "confidence_interval": -1.0,
            "delay": (logged_time - iohub_time),
            "filter_id": False,
        }

        sample = data_parse.eye_sample_from_pupil(pupil_datum, metadata)

        self._addNativeEventToBuffer(sample)

        self._latest_sample = sample

    def _gaze_in_display_coords(self, gaze_on_surface_datum):
        gaze_x, gaze_y = gaze_on_surface_datum["norm_pos"]
        width, height = self._display_device.getPixelResolution()
        # normalized to pixel coordinates:
        gaze_in_display_coords = int(gaze_x * width), int((1.0 - gaze_y) * height)
        return self._eyeTrackerToDisplayCoords(gaze_in_display_coords)

    def _psychopyTimeInTrackerTime(self, psychopy_time):
        return psychopy_time + self._pupil_remote.psychopy_pupil_clock_offset

    def _trackerTimeInPsychopyTime(self, tracker_time):
        return tracker_time - self._pupil_remote.psychopy_pupil_clock_offset

    def _close(self):
        """Do any final cleanup of the eye tracker before the object is
        destroyed."""
        self.setRecordingState(False)
        self.setConnectionState(False)
        self.__class__._INSTANCE = None
        super()._close()
