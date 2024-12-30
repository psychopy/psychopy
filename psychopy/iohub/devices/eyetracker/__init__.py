# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
from .. import Device, ioDeviceError
from ...constants import DeviceConstants, EyeTrackerConstants
from . import hw
from ...errors import print2err
from psychopy.tools.stimulustools import serialize, actualize


class EyeTrackerDevice(Device):
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

    # Used to hold the EyeTracker subclass instance to ensure only one instance of
    # a given eye tracker type is created. This is a current ioHub limitation, not the limitation of
    # all eye tracking hardware.
    _INSTANCE = None

    #: The multiplier needed to convert a device's native time base to sec.msec-usec times.
    DEVICE_TIMEBASE_TO_SEC = 1.0

    # Used by pyEyeTrackerDevice implementations to store relationships between an eye
    # trackers command names supported for EyeTrackerDevice sendCommand method and
    # a private python function to call for that command. This allows an implementation
    # of the interface to expose functions that are not in the core EyeTrackerDevice spec
    # without have to use the EXT extension class.
    _COMMAND_TO_FUNCTION = {}

    DEVICE_TYPE_ID = DeviceConstants.EYETRACKER
    DEVICE_TYPE_STRING = 'EYETRACKER'
    __slots__ = [
        '_latest_sample',
        '_latest_gaze_position',
        '_runtime_settings']

    def __init__(self, *args, **kwargs):
        if self.__class__._INSTANCE is not None:
            raise ioDeviceError(
                self, 'EyeTracker object has already been created; '
                'only one instance can exist. Delete existing '
                'instance before recreating EyeTracker object.')
        else:
            self.__class__._INSTANCE = self

        Device.__init__(self, *args, **kwargs['dconfig'])

        # hold last received ioHub eye sample (in ordered array format) from
        # tracker.
        self._latest_sample = EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED

        # holds the last gaze position read from the eye tracker as an x,y tuple. If binocular recording is
        # being performed, this is an average of the left and right gaze
        # position x,y fields.
        self._latest_gaze_position = EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED

        # stores the eye tracker runtime related configuration settings from
        # the ioHub .yaml config file
        self._runtime_settings = kwargs[
            'dconfig'].get('runtime_settings', None)

        # TODO: Add support for message ID to Message text lookup table in ioDataStore
        # data table that can be used by ET systems that support sending int codes,
        # but not text to tracker at runtime for syncing.

    def trackerTime(self):
        """trackerTime returns the current time reported by the eye tracker
        device. The time base is implementation dependent.

        Args:
            None

        Return:
            float: The eye tracker hardware's reported current time.

        """
        return EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED

    def trackerSec(self):
        """
        trackerSec takes the time received by the EyeTracker.trackerTime() method
        and returns the time in sec.usec-msec format.

        Args:
            None

        Return:
            float: The eye tracker hardware's reported current time in sec.msec-usec format.
        """
        return EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED

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
        return EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED

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
        return EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED

    def sendCommand(self, key, value=None):
        """
        The sendCommand method allows arbitrary *commands* or *requests* to be
        issued to the eye tracker device. Valid values for the arguments of this
        method are completely implementation-specific, so please refer to the
        eye tracker implementation page for the eye tracker being used for a list of
        valid key and value combinations (if any).

        In general, eye tracker implementations should **not** need to support
        this method unless there is critical eye tracker functionality that is
        not accessible using the other methods in the EyeTrackerDevice class.

        Args:
            key (str): the command or function name that should be run.
            value (object): the (optional) value associated with the key.

        Return:
            object: the result of the command call
            int: EyeTrackerConstants.EYETRACKER_OK
            int: EyeTrackerConstants.EYETRACKER_ERROR
            int: EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED
        """

        return EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED

    def sendMessage(self, message_contents, time_offset=None):
        """The sendMessage method sends a text message to the eye tracker.

        Messages are generally used to send information you want
        saved with the native eye data file and are often used to
        synchronize stimulus changes in the experiment with the eye
        data stream being saved to the native eye tracker data file (if any).

        This means that the sendMessage implementation needs to
        perform in real-time, with a delay of <1 msec from when a message is
        sent to when it is time stamped by the eye tracker, for it to be
        accurate in this regard.

        If this standard can not be met, the expected delay and message
        timing precision (variability) should be provided in the eye tracker's
        implementation notes.

        .. note::
            If using the ioDataStore to save the eye tracker data, the use of
            this method is quite optional, as Experiment Device Message Events
            will likely be preferred. ioHub Message Events are stored in the ioDataStore,
            alongside all other device data collected via the ioHub, and not
            in the native eye tracker data.

        Args:
           message_contents (str):
               If message_contents is a string, check with the implementations documentation if there are any string length limits.

        Kwargs:
           time_offset (float): sec.msec_usec time offset that the time stamp of
                              the message should be offset in the eye tracker data file.
                              time_offset can be used so that a message can be sent
                              for a display change **BEFORE** or **AFTER** the actual
                              flip occurred, using the following formula:

                              time_offset = sendMessage_call_time - event_time_message_represent

                              Both times should be based on the iohub.devices.Computer.getTime() time base.

                              If time_offset is not supported by the eye tracker implementation being used, a warning message will be printed to stdout.

        Return:
            (int): EyeTrackerConstants.EYETRACKER_OK, EyeTrackerConstants.EYETRACKER_ERROR, or EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED

        """

        return EyeTrackerConstants.FUNCTIONALITY_NOT_SUPPORTED

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
        return EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED
    
    @staticmethod
    def getCalibrationDict(calib):
        """
        Create a dict describing the given Calibration object, respecting this 
        eyetracker's specific limitations. If not overloaded by a subclass, this 
        will use the same fields and values as MouseGaze.

        Parameters
        ----------
        calib : psychopy.hardware.eyetracker.EyetrackerCalibration
            Object to create a dict from
        
        Returns
        -------
        dict
            Dict describing the given Calibration object
        """
        targetAttributes = serialize(calib.target, includeClass=True)
        # target animation
        targetAttributes['animate'] = {
            'enable': calib.movementAnimation,
            'expansion_ratio': calib.expandScale,
            'contract_only': calib.expandScale == 1,
        }
        
        return {
            'target_attributes': targetAttributes,
            'type': calib.targetLayout,
            'randomize': calib.randomisePos,
            'auto_pace': calib.progressMode == "time",
            'pacing_speed': calib.targetDelay,
            'unit_type': calib.units,
            'color_type': calib.colorSpace,
            'text_color': calib.textColor if str(calib.textColor).lower() != "auto" else None,
            'screen_background_color': getattr(calib.win._color, calib.colorSpace),
        }

    def setRecordingState(self, recording):
        """The setRecordingState method is used to start or stop the recording
        and transmission of eye data from the eye tracking device to the ioHub
        Process.

        Args:
            recording (bool): if True, the eye tracker will start recordng data.; false = stop recording data.

        Return:
            bool: the current recording state of the eye tracking device

        """
        # Implementation Note: Perform your implementation specific logic for
        # this method here
        print2err(
            'EyeTracker should handle setRecordingState method with recording value of {0} now.'.format(recording))

        # Implementation Note: change current_recording_state to be True or
        # False, based on whether the eye tracker is now recording or not.
        current_recording_state = EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED
        return current_recording_state

    def isRecordingEnabled(self):
        """The isRecordingEnabled method indicates if the eye tracker device is
        currently recording data.

        Args:
           None

        Return:
            bool: True == the device is recording data; False == Recording is not occurring

        """

        # Implementation Note: Perform your implementation specific logic for
        # this method here
        print2err('EyeTracker should handle isRecordingEnabled method now.')

        # Implementation Note: change is_recording to be True or False, based
        # on whether the eye tracker is recording or not.
        is_recording = EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED

        return is_recording

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

    def getPosition(self):
        """
        See getLastGazePosition().
        """
        return self.getLastGazePosition()

    def getPos(self):
        """
        See getLastGazePosition().
        """
        return self.getLastGazePosition()

    def _eyeTrackerToDisplayCoords(self, eyetracker_point):
        """The _eyeTrackerToDisplayCoords method is required for implementation
        of the Common Eye Tracker Interface in order to convert the native Eye
        Tracker coordinate space to the ioHub.devices.Display coordinate space
        being used in the PsychoPy experiment. Any screen based coordinates
        that exist in the data provided to the ioHub by the device
        implementation must use this method to convert the x,y eye tracker
        point to the correct coordinate space.

        Default implementation is to call the Display device method:

            self._display_device._pixel2DisplayCoord(gaze_x,gaze_y,self._display_device.getIndex())

        where gaze_x,gaze_y = eyetracker_point, which is assumed to be in screen pixel
        coordinates, with a top-left origin. If the eye tracker provides the eye position
        data in a coordinate space other than screen pixel position with top-left origin,
        the eye tracker position should first be converted to this coordinate space before
        passing the position data px,py to the _pixel2DisplayCoord method.

        self._display_device.getIndex() provides the index of the display for multi display setups.
        0 is the default index, and valid values are 0 - N-1, where N is the number
        of connected, active, displays on the computer being used.

        Args:
            eyetracker_point (object): eye tracker implementation specific data type representing an x, y position on the calibrated 2D plane (typically a computer display screen).

        Returns:
            (x,y): The x,y eye position on the calibrated surface in the current ioHub.devices.Display coordinate type and space.

        """
        gaze_x = eyetracker_point[0]
        gaze_y = eyetracker_point[1]

        # If the eyetracker_point does not represent eye data as display
        # pixel position using a top-left origin, convert the naive eye tracker
        # gaze coordinate space to a display pixel position using a top-left origin
        # here before passing gaze_x,gaze_y to the _pixel2DisplayCoord method.
        # ....

        return self._display_device._pixel2DisplayCoord(
            gaze_x, gaze_y, self._display_device.getIndex())

    def _displayToEyeTrackerCoords(self, display_x, display_y):
        """The _displayToEyeTrackerCoords method must be used by an eye
        trackers implementation of the Common Eye Tracker Interface to convert
        any gaze positions provided by the ioHub to the appropriate x,y gaze
        position coordinate space for the eye tracking device in use.

        This method is simply the inverse operation performed by the _eyeTrackerToDisplayCoords
        method.

        Default implementation is to just return the result of self._display_device.display2PixelCoord(...).

        Args:
            display_x (float): The horizontal eye position on the calibrated 2D surface in ioHub.devices.Display coordinate space.
            display_y (float): The vertical eye position on the calibrated 2D surface in ioHub.devices.Display coordinate space.

        Returns:
            (object): eye tracker implementation specific data type representing an x, y position on the calibrated 2D plane (typically a computer display screen).

        """

        pixel_x, pixel_y = self._display_device.display2PIxelCoord(
            display_x, display_y, self._display_device.getIndex())
        return pixel_x, pixel_y

    def __del__(self):
        """Do any final cleanup of the eye tracker before the object is
        destroyed."""
        self.__class__._INSTANCE = None

from .eye_events import (
    EyeSampleEvent,
    MonocularEyeSampleEvent,
    BinocularEyeSampleEvent,
    FixationStartEvent,
    FixationEndEvent,
    SaccadeStartEvent,
    SaccadeEndEvent,
    BlinkStartEvent,
    BlinkEndEvent)
