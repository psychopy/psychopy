"""Eyetracker devices for use with `DeviceManager`, plus helpers used by Builder experiments.

:class:`BaseEyetrackerDevice` defines the interface which every eyetracker device provides. It
doesn't depend on any particular way of talking to an eyetracker, so Components, Routines and
experiment code should only use the methods it defines.

At present all eyetrackers run inside the ioHub server process, and are represented by subclasses
of :class:`IoHubEyetrackerDevice`. This wraps the ioHub eyetracker so that it can be created,
looked up and closed through :class:`~psychopy.hardware.manager.DeviceManager` like any other
hardware device. Eyetrackers which don't use ioHub can subclass :class:`BaseEyetrackerDevice`
directly.

ioHub only monitors the devices which were in its configuration when it was launched. This means
an ioHub eyetracker has to be configured *before* anything else (e.g. an ioHub keyboard) starts
ioHub. In Builder experiments this is handled for you: the tracker's ioHub config is collected
(via :meth:`IoHubEyetrackerDevice.getIoConfig`) before ioHub is launched, and the device is added
to DeviceManager afterwards, at which point it wraps the tracker which ioHub created. In Coder, if
ioHub isn't running yet, creating an ioHub eyetracker device will launch ioHub for you. Only one
ioHub eyetracker can be used per session.

Adding support for a new eyetracker (e.g. in a plugin)
------------------------------------------------------
For an eyetracker which runs in ioHub:

1. Subclass :class:`IoHubEyetrackerDevice`, setting ``ioClass`` to the ioHub class path of the
   tracker (e.g. ``"eyetracker.hw.mouse.EyeTracker"``). Its ``__init__`` should accept whatever
   settings the tracker needs, and pass ``ioConfig=cls.getIoConfig(...)`` to
   ``IoHubEyetrackerDevice.__init__``.
2. Override :meth:`IoHubEyetrackerDevice.getIoConfig` to convert those same settings into the
   ioHub config dict for the tracker.
3. Implement ``getAvailableDevices`` to return a profile for each tracker which can be found (or a
   single profile, if trackers of this kind can't be detected).
4. In Builder, subclass :class:`psychopy.experiment.eyetracking.IoHubEyetrackerDeviceBackend` and
   register it with the eyetracking Components and Routines using
   :func:`psychopy.experiment.eyetracking.registerEyetrackerDeviceBackend`, so the tracker can
   be configured in Device Manager.

See :class:`MouseGazeEyetracker` for a complete example.

For an eyetracker which doesn't use ioHub, subclass :class:`BaseEyetrackerDevice` and implement its
methods, then subclass :class:`psychopy.experiment.eyetracking.EyetrackerDeviceBackend` (with
``needsIoHub = False``) for Builder.
"""

from psychopy.constants import STARTED, NOT_STARTED, PAUSED, STOPPED, FINISHED
from psychopy.alerts import alert
from psychopy import logging
from psychopy.hardware.base import BaseDevice
from psychopy.tools.attributetools import AttributeGetSetMixin
import sys

__all__ = [
    'BaseEyetrackerDevice',
    'IoHubEyetrackerDevice',
    'MouseGazeEyetracker',
    'EyetrackerControl',
    'EyetrackerCalibration',
    'EyetrackerValidation',
]


def _normaliseIoClass(ioClass):
    """
    Normalise an ioHub device class path so that paths given in different forms can be compared.

    ioHub refers to device classes either relative to `psychopy.iohub.devices` (e.g.
    `"eyetracker.hw.mouse.EyeTracker"`, as used in ioHub config) or fully qualified with a
    lowercase module path (as returned by `ioHubDeviceView.getIOHubDeviceClass(full=True)`).

    Parameters
    ----------
    ioClass : str or None
        Class path to normalise

    Returns
    -------
    str or None
        Lowercase class path relative to `psychopy.iohub.devices`
    """
    if ioClass is None:
        return None
    ioClass = str(ioClass).lower()
    prefix = "psychopy.iohub.devices."
    if ioClass.startswith(prefix):
        ioClass = ioClass[len(prefix):]

    return ioClass


class BaseEyetrackerDevice(BaseDevice, aliases=["eyetracker"]):
    """
    Interface for eyetracker devices which can be managed by `DeviceManager`.

    This class doesn't talk to an eyetracker itself: use the subclass for a particular kind of
    eyetracker (e.g. :class:`MouseGazeEyetracker`). Subclasses must implement `startRecording`,
    `stopRecording`, `isRecording` and `getPos`, and should implement whichever of the other
    methods their eyetracker supports.
    """

    # --- BaseDevice methods ---

    def isSameDevice(self, other):
        """
        Determine whether this object represents the same eyetracker as a given other object.

        Parameters
        ----------
        other : BaseEyetrackerDevice, dict
            Other device object to compare against, or a dict of params.

        Returns
        -------
        bool
            True if the two objects represent the same physical device
        """
        if isinstance(other, BaseEyetrackerDevice):
            return other is self
        if isinstance(other, dict):
            otherCls = self._resolveProfileClass(other)
            return otherCls is not None and isinstance(self, otherCls)

        return False

    @staticmethod
    def _resolveProfileClass(profile):
        """
        Get the device class referred to by a device profile, or None if it can't be resolved.
        """
        from psychopy.hardware.manager import DeviceManager

        clsStr = profile.get('deviceClass', None)
        if clsStr is None:
            return None
        try:
            cls = DeviceManager.getDeviceClass(clsStr)
        except Exception:
            # if the class can't be resolved, it can't be this device
            return None
        if not isinstance(cls, type):
            return None

        return cls

    @staticmethod
    def getAvailableDevices():
        """
        Get profiles for all eyetrackers which can be created, from every known subclass of
        BaseEyetrackerDevice (including those from plugins).

        Returns
        -------
        list[dict]
            List of dictionaries containing the parameters needed to initialise each device.
        """
        from psychopy.hardware.manager import DeviceManager

        # classes whose getAvailableDevices only aggregates from subclasses
        aggregators = (
            BaseEyetrackerDevice.getAvailableDevices,
            IoHubEyetrackerDevice.getAvailableDevices,
        )

        devices = []
        for clsStr in DeviceManager.deviceClasses:
            try:
                cls = DeviceManager._resolveClassString(clsStr)
            except Exception:
                continue
            # skip anything which isn't a specific kind of eyetracker
            if not isinstance(cls, type) or not issubclass(cls, BaseEyetrackerDevice):
                continue
            if cls.getAvailableDevices in aggregators:
                continue
            try:
                devices += cls.getAvailableDevices()
            except Exception as err:
                logging.warn(f"Could not get available devices for {cls.__name__}: {err}")

        return devices

    def close(self):
        """
        Stop recording, if recording.
        """
        try:
            if self.isRecording():
                self.stopRecording()
        except Exception:
            # the connection to the tracker may already have closed
            pass

    # --- required methods ---

    def startRecording(self):
        """
        Start recording eye data.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement `startRecording`."
        )

    def stopRecording(self):
        """
        Stop recording eye data.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement `stopRecording`."
        )

    def isRecording(self):
        """
        Whether the eyetracker is currently recording.

        Returns
        -------
        bool
            True if recording
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement `isRecording`."
        )

    def getPos(self):
        """
        Get the current gaze position (in window units).

        Returns
        -------
        list[float] or None
            Gaze position as [x, y], or None if there is no current gaze position (e.g. during a
            blink).
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement `getPos`."
        )

    @property
    def pos(self):
        """
        The current gaze position (in window units), or None if there isn't one.
        """
        return self.getPos()

    # --- optional methods ---

    def getLastSample(self):
        """
        Get the most recent eye sample.

        Returns
        -------
        object or None
            The most recent sample (format depends on the eyetracker), or None if there isn't one.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support getting samples."
        )

    def sendMessage(self, message):
        """
        Send a text message to the eyetracker, to be stored with its data.

        Parameters
        ----------
        message : str
            Message to send
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support sending messages."
        )

    def clearEvents(self):
        """
        Clear any eye events which have been received but not yet retrieved. Does nothing if the
        eyetracker doesn't store events.
        """
        pass

    def enableEventReporting(self, enabled=True):
        """
        Enable / disable reporting of eye events. Does nothing if the eyetracker doesn't report
        events.
        """
        pass

    def calibrate(self, calibration):
        """
        Run the eyetracker's calibration procedure.

        Parameters
        ----------
        calibration : EyetrackerCalibration
            Calibration settings (target, layout, pacing, etc.)

        Returns
        -------
        object
            Result of the calibration (format depends on the eyetracker)
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support calibration."
        )

    def validate(self, validation):
        """
        Run a validation procedure, measuring the accuracy of gaze positions from the eyetracker.

        Parameters
        ----------
        validation : EyetrackerValidation
            Validation settings (target, positions, pacing, etc.)

        Returns
        -------
        dict or None
            Validation results, or None if validation was ended early.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support validation."
        )


class IoHubEyetrackerDevice(BaseEyetrackerDevice, aliases=["iohubEyetracker"]):
    """
    Eyetracker device wrapping an eyetracker which runs in the ioHub server process.

    This class can wrap whichever eyetracker ioHub is already running (which is how eyetrackers
    configured in Experiment Settings are handled). To create a specific kind of tracker, use the
    subclass for it (e.g. :class:`MouseGazeEyetracker`).

    Parameters
    ----------
    ioServer : psychopy.iohub.client.ioHubConnection, optional
        ioHub connection to get the tracker from. If None, will use `DeviceManager.ioServer`, then
        the active ioHub connection (if any).
    win : psychopy.visual.Window, optional
        Window to give ioHub, only used if this device needs to launch ioHub itself.
    ioConfig : dict, optional
        Config to launch ioHub with if it isn't already running, in the form
        `{<ioHub class path>: {<tracker settings>}}`. Subclasses should make this using
        `getIoConfig`.
    """
    # ioHub class path of the tracker this class creates (None to wrap whatever tracker is running)
    ioClass = None
    # name by which the tracker is known to ioHub
    ioName = "tracker"
    # names of ioHub tracker attributes we've already warned about using directly
    _warnedAttrs = set()

    def __init__(self, ioServer=None, win=None, ioConfig=None):
        from psychopy.hardware.manager import DeviceManager
        # get ioHub connection
        conn = self._getConnection(ioServer)
        # if ioHub isn't running, launch it with this tracker configured
        if conn is None:
            conn = self._launchIoHub(win=win, ioConfig=ioConfig)
        # make sure DeviceManager knows about the connection
        if DeviceManager.ioServer is None:
            DeviceManager.ioServer = conn
        self.ioServer = conn
        # get tracker from ioHub
        tracker = conn.getDevice(self.ioName)
        if tracker is None:
            raise RuntimeError(
                f"Could not create {type(self).__name__} as ioHub is already running without an "
                f"eyetracker named '{self.ioName}'. ioHub can only use devices which were "
                f"configured when it launched, so the eyetracker needs to be added before anything "
                f"else starts ioHub (e.g. a Keyboard using the ioHub backend)."
            )
        # make sure the tracker is the kind this class expects
        if self.ioClass is not None:
            expected = _normaliseIoClass(self.ioClass)
            actual = _normaliseIoClass(tracker.getIOHubDeviceClass(full=True))
            if expected != actual:
                raise RuntimeError(
                    f"Could not create {type(self).__name__} as ioHub is already running a "
                    f"different eyetracker ({tracker.getIOHubDeviceClass(full=True)}). Only one "
                    f"eyetracker can be used per session."
                )
        # store tracker
        self._tracker = tracker

    @staticmethod
    def _getConnection(ioServer=None):
        """
        Get the ioHub connection to use, if there is one.
        """
        from psychopy.hardware.manager import DeviceManager
        from psychopy.iohub.client import ioHubConnection

        for conn in (ioServer, DeviceManager.ioServer, ioHubConnection.getActiveConnection()):
            if conn is not None:
                return conn

    def _launchIoHub(self, win=None, ioConfig=None):
        """
        Launch ioHub with this tracker configured.
        """
        from psychopy.iohub import launchHubServer

        if ioConfig is None:
            if self.ioClass is None:
                raise RuntimeError(
                    f"Could not create {type(self).__name__} as ioHub is not running. Either "
                    f"launch ioHub with an eyetracker configured, or use the device class for a "
                    f"specific eyetracker."
                )
            ioConfig = self.getIoConfig()
        logging.info(f"Launching ioHub for {type(self).__name__}")

        return launchHubServer(window=win, **ioConfig)

    @classmethod
    def getIoConfig(cls, **kwargs):
        """
        Get the ioHub config for this kind of tracker, to be passed to `launchHubServer`.
        Subclasses should overload this to convert their init arguments into ioHub settings.

        Parameters
        ----------
        **kwargs
            The same settings as would be given to this class's `__init__`.

        Returns
        -------
        dict
            Dict in the form `{<ioHub class path>: {<tracker settings>}}`
        """
        if cls.ioClass is None:
            raise NotImplementedError(
                f"{cls.__name__} doesn't represent a specific kind of eyetracker, so has no ioHub "
                f"config."
            )

        return {cls.ioClass: {'name': cls.ioName}}

    # --- BaseDevice methods ---

    def isSameDevice(self, other):
        """
        Determine whether this object represents the same eyetracker as a given other object.

        As ioHub only supports one eyetracker per session, any two objects pointing to the same
        kind of ioHub eyetracker are considered the same device.

        Parameters
        ----------
        other : BaseEyetrackerDevice, dict
            Other device object to compare against, or a dict of params.

        Returns
        -------
        bool
            True if the two objects represent the same physical device
        """
        if isinstance(other, IoHubEyetrackerDevice):
            return other._tracker is self._tracker
        if isinstance(other, dict):
            otherCls = self._resolveProfileClass(other)
            if otherCls is None or not issubclass(otherCls, IoHubEyetrackerDevice):
                return False
            # a profile which doesn't specify a tracker could refer to any ioHub tracker
            if otherCls.ioClass is None:
                return True
            # otherwise compare tracker classes
            return _normaliseIoClass(otherCls.ioClass) == _normaliseIoClass(
                self.getIOHubDeviceClass(full=True)
            )

        return False

    @staticmethod
    def getAvailableDevices():
        """
        Get profiles for all ioHub eyetrackers which can be created.

        Returns
        -------
        list[dict]
            List of dictionaries containing the parameters needed to initialise each device.
        """
        return [
            profile for profile in BaseEyetrackerDevice.getAvailableDevices()
            if issubclass(
                BaseEyetrackerDevice._resolveProfileClass(profile) or object,
                IoHubEyetrackerDevice
            )
        ]

    def close(self):
        """
        Stop recording, if ioHub is still running. ioHub itself (and so the connection to the
        tracker) is closed separately, when the ioHub connection is closed.
        """
        if not self._ioHubRunning():
            return
        BaseEyetrackerDevice.close(self)

    def _ioHubRunning(self):
        """
        Whether the ioHub connection this device uses is still open.
        """
        from psychopy.iohub.client import ioHubConnection

        try:
            conn = self.__dict__.get('ioServer', None)
            if conn is None or getattr(conn, "_shutdown_attempted", False):
                return False
            # real connections are cleared from the active connection when ioHub quits
            if isinstance(conn, ioHubConnection) or type(conn).__name__ == "weakproxy":
                return ioHubConnection.getActiveConnection() is not None
        except ReferenceError:
            # connection has been garbage collected
            return False

        return True

    # --- ioHub tracker access ---

    @staticmethod
    def _checkSupported(value, method):
        """
        Convert ioHub's "not supported" return code into None, with a warning.
        """
        from psychopy.iohub.constants import EyeTrackerConstants

        if isinstance(value, int) and not isinstance(value, bool) and (
            value == EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED
        ):
            logging.warn(f"Eyetracker method `{method}` is not supported by this eyetracker.")
            return None

        return value

    def __getattr__(self, name):
        # pass anything not defined here on to the ioHub tracker, so that code written for the
        # ioHub tracker object keeps working - but warn, as this ties code to ioHub
        tracker = self.__dict__.get('_tracker', None)
        if tracker is None or name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )
        value = getattr(tracker, name)
        if name not in IoHubEyetrackerDevice._warnedAttrs:
            IoHubEyetrackerDevice._warnedAttrs.add(name)
            logging.warn(
                f"`{name}` was accessed directly on the ioHub eyetracker, via "
                f"{type(self).__name__}. Accessing ioHub eyetracker attributes this way is "
                f"deprecated and will stop working when ioHub is removed; use the methods of "
                f"BaseEyetrackerDevice instead."
            )

        return value

    @property
    def tracker(self):
        """
        The ioHub eyetracker object which this device wraps.
        """
        return self._tracker

    # --- BaseEyetrackerDevice interface ---

    def startRecording(self):
        return self.setRecordingState(True)

    def stopRecording(self):
        return self.setRecordingState(False)

    def isRecording(self):
        return bool(self.isRecordingEnabled())

    def getPos(self):
        return self._checkSupported(self._tracker.getPos(), "getPos")

    def getLastSample(self):
        return self._checkSupported(self._tracker.getLastSample(), "getLastSample")

    def sendMessage(self, message, time_offset=None):
        return self._checkSupported(
            self._tracker.sendMessage(message, time_offset), "sendMessage"
        )

    def clearEvents(self, *args, **kwargs):
        """
        Clear eye events from ioHub. Takes the same arguments as ioHub's `clearEvents`.
        """
        return self._tracker.clearEvents(*args, **kwargs)

    def enableEventReporting(self, enabled=True):
        return self._tracker.enableEventReporting(enabled)

    def calibrate(self, calibration):
        # warn about settings which this tracker doesn't use
        _ioHubCalibrationAlerts(self.getIOHubDeviceClass(full=True), calibration)
        # run the tracker's setup procedure with the calibration in ioHub format
        return self.runSetupProcedure(_getIoHubCalibrationDict(self, calibration))

    def validate(self, validation):
        return _runIoHubValidation(validation, ioServer=self.ioServer)

    # --- ioHub-specific methods ---

    def getIOHubDeviceClass(self, full=False):
        """
        Get the ioHub class path of the wrapped tracker.

        Parameters
        ----------
        full : bool
            If True, returns the fully qualified class path.
        """
        return self._tracker.getIOHubDeviceClass(full=full)

    def setConnectionState(self, enable):
        """
        Connect to / disconnect from the eyetracker hardware.
        """
        return self._checkSupported(
            self._tracker.setConnectionState(enable), "setConnectionState"
        )

    def isConnected(self):
        """
        Whether the eyetracker hardware is currently connected.
        """
        return self._checkSupported(self._tracker.isConnected(), "isConnected")

    def runSetupProcedure(self, calibration_args=None):
        """
        Run the eyetracker's setup (calibration) procedure, with settings in ioHub format.
        Prefer `calibrate`.
        """
        if calibration_args is None:
            calibration_args = {}
        return self._checkSupported(
            self._tracker.runSetupProcedure(calibration_args), "runSetupProcedure"
        )

    def setRecordingState(self, recording):
        """
        Start or stop recording eye data. Prefer `startRecording` / `stopRecording`.
        """
        return self._checkSupported(
            self._tracker.setRecordingState(recording), "setRecordingState"
        )

    def isRecordingEnabled(self):
        """
        Whether the eyetracker is currently recording. Prefer `isRecording`.
        """
        return self._checkSupported(self._tracker.isRecordingEnabled(), "isRecordingEnabled")

    def getLastGazePosition(self):
        """
        Get the most recent gaze position (in window units), or None if there isn't one.
        """
        return self._checkSupported(
            self._tracker.getLastGazePosition(), "getLastGazePosition"
        )

    def sendCommand(self, key, value=None):
        """
        Send a tracker-specific command to the eyetracker.
        """
        return self._checkSupported(self._tracker.sendCommand(key, value), "sendCommand")

    def getEvents(self, *args, **kwargs):
        """
        Get eye events from ioHub. Takes the same arguments as ioHub's `getEvents`.
        """
        return self._tracker.getEvents(*args, **kwargs)

    def trackerTime(self):
        """
        Current time according to the eyetracker's own clock (in tracker units).
        """
        return self._checkSupported(self._tracker.trackerTime(), "trackerTime")

    def trackerSec(self):
        """
        Current time according to the eyetracker's own clock, in seconds.
        """
        return self._checkSupported(self._tracker.trackerSec(), "trackerSec")


class MouseGazeEyetracker(IoHubEyetrackerDevice, aliases=["mousegaze"]):
    """
    Simulated eyetracker which uses the mouse to control gaze position, for testing eyetracking
    experiments without an eyetracker connected.

    Parameters
    ----------
    move : str or list[str]
        Mouse button(s) which must be held for gaze to move, or "CONTINUOUS" (or an empty list) for
        gaze to always follow the mouse. Buttons are "LEFT_BUTTON", "MIDDLE_BUTTON" or
        "RIGHT_BUTTON".
    blink : str or list[str]
        Mouse button(s) to press to simulate a blink.
    saccadeThreshold : float
        Distance (in degrees of visual angle) the mouse must move for a saccade event to be created.
    ioServer : psychopy.iohub.client.ioHubConnection, optional
        ioHub connection to get the tracker from (see `IoHubEyetrackerDevice`).
    win : psychopy.visual.Window, optional
        Window to give ioHub, only used if this device needs to launch ioHub itself.
    """
    ioClass = "eyetracker.hw.mouse.EyeTracker"

    def __init__(
            self,
            move="CONTINUOUS",
            blink=("MIDDLE_BUTTON",),
            saccadeThreshold=0.5,
            ioServer=None,
            win=None,
    ):
        IoHubEyetrackerDevice.__init__(
            self,
            ioServer=ioServer,
            win=win,
            ioConfig=self.getIoConfig(
                move=move, blink=blink, saccadeThreshold=saccadeThreshold
            ),
        )

    @staticmethod
    def _buttonList(value):
        """
        Sanitize a button spec into a list of button names.
        """
        if value in (None, "", "CONTINUOUS"):
            return []
        if isinstance(value, str):
            return [value]

        return [val for val in value if val not in (None, "", "CONTINUOUS")]

    @classmethod
    def getIoConfig(
            cls, move="CONTINUOUS", blink=("MIDDLE_BUTTON",), saccadeThreshold=0.5, **kwargs
    ):
        return {
            cls.ioClass: {
                'name': cls.ioName,
                'controls': {
                    'move': cls._buttonList(move),
                    'blink': cls._buttonList(blink),
                    'saccade_threshold': saccadeThreshold,
                },
            }
        }

    @staticmethod
    def getAvailableDevices():
        # MouseGaze only needs a mouse, so is always available
        return [{
            'deviceName': "MouseGaze",
            'deviceClass': "psychopy.hardware.eyetracker.MouseGazeEyetracker",
        }]


# --- ioHub helpers (used by IoHubEyetrackerDevice, and for raw ioHub trackers) ---

def _getIoHubCalibrationDict(tracker, calibration):
    """
    Convert an `EyetrackerCalibration` to the calibration dict for an ioHub tracker.

    Parameters
    ----------
    tracker : IoHubEyetrackerDevice or psychopy.iohub.client.ioHubDeviceView
        ioHub tracker to make the calibration dict for
    calibration : EyetrackerCalibration
        Calibration settings

    Returns
    -------
    dict
        Calibration settings in the tracker's ioHub format
    """
    from psychopy.iohub.devices import importDeviceModule

    ioClass = tracker.getIOHubDeviceClass(full=True)
    # split into package and class name
    pkgName = ".".join(ioClass.split(".")[:-1])
    clsName = ioClass.split(".")[-1]
    # make sure pkgName is fully qualified
    if not pkgName.startswith("psychopy.iohub.devices."):
        pkgName = "psychopy.iohub.devices." + pkgName
    # get tracker class
    trackerCls = getattr(importDeviceModule(pkgName), clsName)

    return trackerCls.getCalibrationDict(calibration)


def _ioHubCalibrationAlerts(ioClass, calibration):
    """
    Raise alerts for calibration settings which a given ioHub tracker doesn't support.
    """
    ioClass = _normaliseIoClass(ioClass)
    if ioClass == _normaliseIoClass('eyetracker.hw.sr_research.eyelink.EyeTracker'):
        if calibration.movementAnimation:
            # alert user that their animation params aren't used
            alert(code=4520, strFields={"brand": "EyeLink"})
    elif ioClass == _normaliseIoClass('eyetracker.hw.gazepoint.gp3.EyeTracker'):
        if not calibration.progressMode == "time":
            # as GazePoint doesn't use auto-pace, alert user
            alert(4530, strFields={"brand": "GazePoint"})


def _runIoHubValidation(validation, ioServer=None):
    """
    Run an `EyetrackerValidation` using ioHub's validation procedure.

    Parameters
    ----------
    validation : EyetrackerValidation
        Validation settings
    ioServer : psychopy.iohub.client.ioHubConnection, optional
        ioHub connection whose tracker to validate. The validation procedure uses the active ioHub
        connection, so this is only used to check that one is running.

    Returns
    -------
    dict or None
        Validation results, or None if validation was ended early.
    """
    from psychopy.iohub.client import ioHubConnection
    from psychopy.iohub.client.eyetracker.validation import ValidationProcedure

    if ioServer is None and ioHubConnection.getActiveConnection() is None:
        raise RuntimeError("Could not run eyetracker validation as ioHub is not running.")
    # make validation procedure
    validation.procedure = ValidationProcedure(
        validation.win,
        target=validation.target,
        gaze_cursor=validation.cursorColor,
        positions=validation.positions,
        randomize_positions=validation.randomisePos,
        expand_scale=validation.expandScale,
        target_duration=validation.targetDur,
        enable_position_animation=validation.movementAnimation,
        target_delay=validation.targetDelay,
        progress_on_key=validation.progressKey,
        text_color=validation.textColor,
        show_results_screen=validation.showResults,
        save_results_screen=validation.saveAsImg,
        color_space=validation.colorSpace,
        unit_type=validation.units,
    )

    return validation.procedure.run()


class EyetrackerControl(AttributeGetSetMixin):
    """
    Object to start and stop eyetracker recording, used by the Eyetracker Record Component.

    Parameters
    ----------
    tracker : BaseEyetrackerDevice
        Eyetracker to control. A raw ioHub eyetracker is also accepted, for backwards
        compatibility.
    actionType : str
        Whether this object starts and/or stops recording ("Start and Stop", "Start Only" or
        "Stop Only")
    """

    def __init__(self, tracker, actionType="Start and Stop"):
        self.tracker = tracker
        self.actionType = actionType
        self.status = NOT_STARTED

    def _isRecording(self):
        if isinstance(self.tracker, BaseEyetrackerDevice):
            return self.tracker.isRecording()
        # raw ioHub tracker
        return self.tracker.isRecordingEnabled()

    def _setRecording(self, recording):
        if isinstance(self.tracker, BaseEyetrackerDevice):
            if recording:
                return self.tracker.startRecording()
            else:
                return self.tracker.stopRecording()
        # raw ioHub tracker
        return self.tracker.setRecordingState(recording)

    def start(self):
        """
        Start recording
        """
        # if previously at a full stop, clear events
        if not self._isRecording():
            logging.exp("eyetracker.clearEvents()")
            self.tracker.clearEvents()
        # start recording
        self._setRecording(True)
        logging.exp("eyetracker.startRecording()")

    def stop(self):
        """
        Stop recording
        """
        self._setRecording(False)
        logging.exp("eyetracker.stopRecording()")

    @property
    def currentlyRecording(self):
        """
        Check if the eyetracker is currently recording
        added for backwards compatibility, should be removed in future
        """
        return self._isRecording()

    @property
    def pos(self):
        """
        Get the current position of the eyetracker
        """
        return self.tracker.getPos()

    def getPos(self):
        return self.pos


class EyetrackerCalibration:
    """
    Calibration settings for an eyetracker, used by the Eyetracker Calibration Routine.

    Parameters
    ----------
    win : psychopy.visual.Window
        Window to run calibration in
    eyetracker : BaseEyetrackerDevice
        Eyetracker to calibrate. A raw ioHub eyetracker is also accepted, for backwards
        compatibility.
    target : psychopy.visual.TargetStim
        Target to show at each calibration position
    """
    def __init__(self, win,
                 eyetracker, target,
                 units="height", colorSpace="rgb",
                 progressMode="time", targetDur=1.5, expandScale=1.5,
                 targetLayout="NINE_POINTS", randomisePos=True,
                 movementAnimation=False, targetDelay=1.0, textColor='Auto'
                 ):
        # Store params
        self.win = win
        self.eyetracker = eyetracker
        self.target = target
        self.progressMode = progressMode
        self.targetLayout = targetLayout
        self.randomisePos = randomisePos
        self.textColor = textColor
        self.units = units or self.win.units
        self.colorSpace = colorSpace or self.win.colorSpace
        # Animation
        self.movementAnimation = movementAnimation
        self.targetDelay = targetDelay
        self.targetDur = targetDur
        self.expandScale = expandScale
        # Attribute to store data from last run
        self.last = None

    def __iter__(self):
        """Overload dict() method to return in ioHub format"""
        for key, value in _getIoHubCalibrationDict(self.eyetracker, self).items():
            yield key, value

    def run(self):
        # Minimise PsychoPy window
        if self.win._isFullScr and sys.platform == 'win32':
            self.win.winHandle.set_fullscreen(False)
            self.win.winHandle.minimize()

        # Run
        if isinstance(self.eyetracker, BaseEyetrackerDevice):
            self.last = self.eyetracker.calibrate(self)
        else:
            # raw ioHub tracker
            _ioHubCalibrationAlerts(self.eyetracker.getIOHubDeviceClass(full=True), self)
            self.last = self.eyetracker.runSetupProcedure(dict(self))

        # Bring back PsychoPy window
        if self.win._isFullScr and sys.platform == 'win32':
            self.win.winHandle.set_fullscreen(True)
            self.win.winHandle.maximize()
            # Not 100% sure activate is necessary, but does not seem to hurt.
            self.win.winHandle.activate()

        # SS: Flip otherwise black screen has been seen, not sure why this just started....
        self.win.flip()


class EyetrackerValidation:
    """
    Validation settings for an eyetracker, used by the Eyetracker Validation Routine. Validation
    measures how accurately the eyetracker reports gaze, by showing targets at known positions.

    Parameters
    ----------
    win : psychopy.visual.Window
        Window to run validation in
    eyetracker : BaseEyetrackerDevice
        Eyetracker to validate. A raw ioHub eyetracker is also accepted, for backwards
        compatibility.
    target : psychopy.visual.TargetStim
        Target to show at each validation position
    positions : str or list
        Name of a preset layout (e.g. "NINE_POINTS") or a list of [x, y] positions
    randomisePos : bool
        Whether to show positions in a random order
    expandScale : float
        How much the target expands when it reaches each position
    targetDur : float
        How long (s) the target stays at each position
    movementAnimation : bool
        Whether the target moves smoothly between positions
    targetDelay : float
        How long (s) the target takes to move between positions
    progressKey : str or None
        Key to press to move to the next position, or None to progress automatically
    textColor : color
        Color of text on screen
    cursorColor : color or None
        Color of a cursor to show at the current gaze position, or None for no cursor
    showResults : bool
        Whether to show a screen with the results afterwards
    saveAsImg : bool
        Whether to save the results screen as an image
    colorSpace : str or None
        Color space for colors, or None to use the window's
    units : str or None
        Spatial units for positions, or None to use the window's
    """
    def __init__(self, win,
                 eyetracker, target,
                 positions="NINE_POINTS", randomisePos=True,
                 expandScale=1.5, targetDur=1.5,
                 movementAnimation=True, targetDelay=1.0,
                 progressKey=None, textColor="auto", cursorColor="green",
                 showResults=True, saveAsImg=False,
                 colorSpace=None, units=None):
        self.win = win
        self.eyetracker = eyetracker
        self.target = target
        self.positions = positions
        self.randomisePos = randomisePos
        self.expandScale = expandScale
        self.targetDur = targetDur
        self.movementAnimation = movementAnimation
        self.targetDelay = targetDelay
        self.progressKey = progressKey
        self.textColor = textColor
        self.cursorColor = cursorColor
        self.showResults = showResults
        self.saveAsImg = saveAsImg
        self.colorSpace = colorSpace or getattr(win, "colorSpace", None)
        self.units = units
        # procedure object which ran the last validation, if the eyetracker uses one
        self.procedure = None
        # results from the last run
        self.last = None

    def __getattr__(self, name):
        # pass anything not defined here on to the validation procedure, so that code written for
        # ioHub's ValidationProcedure object keeps working
        procedure = self.__dict__.get('procedure', None)
        if procedure is None or name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

        return getattr(procedure, name)

    def run(self):
        """
        Run the validation.

        Returns
        -------
        dict or None
            Validation results, or None if validation was ended early.
        """
        if isinstance(self.eyetracker, BaseEyetrackerDevice):
            self.last = self.eyetracker.validate(self)
        else:
            # raw ioHub tracker
            self.last = _runIoHubValidation(self)

        return self.last

    @property
    def results(self):
        """
        Results from the last validation run, or None if validation hasn't run (or was ended
        early).
        """
        return self.last

    def getValidationResults(self):
        """
        Get results from the last validation run, or None if validation hasn't run (or was ended
        early).
        """
        return self.last
