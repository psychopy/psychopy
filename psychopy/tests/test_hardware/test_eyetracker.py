"""Tests for eyetrackers managed by DeviceManager (psychopy.hardware.eyetracker).

These use a fake ioHub connection, so no ioHub server or eyetracker is needed.
"""
import pytest

from psychopy import logging
from psychopy.hardware import DeviceManager
from psychopy.hardware.eyetracker import (
    BaseEyetrackerDevice, IoHubEyetrackerDevice, MouseGazeEyetracker,
    EyetrackerControl, EyetrackerCalibration, EyetrackerValidation,
)
from psychopy.hardware.exceptions import ManagedDeviceError
from psychopy.iohub.constants import EyeTrackerConstants


class FakeTracker:
    """Stand-in for the ioHubDeviceView of an eyetracker."""

    def __init__(self, ioClass="psychopy.iohub.devices.eyetracker.hw.mouse.EyeTracker"):
        self.ioClass = ioClass
        self.recording = False
        self.cleared = 0
        self.setupArgs = None

    def getIOHubDeviceClass(self, full=False):
        return self.ioClass if full else self.ioClass.split(".")[-1]

    def setRecordingState(self, recording):
        self.recording = recording
        return recording

    def isRecordingEnabled(self):
        return self.recording

    def clearEvents(self, *args, **kwargs):
        self.cleared += 1

    def getPos(self):
        return [0.1, 0.2]

    def trackerTime(self):
        return EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED

    def runSetupProcedure(self, calibration_args):
        self.setupArgs = calibration_args
        return {'RESULT': "CALIBRATION_OK"}

    def someTrackerSpecificMethod(self):
        return "passed through"


class FakeConnection:
    """Stand-in for an ioHubConnection."""

    def __init__(self, tracker=None):
        self.tracker = tracker

    def getDevice(self, name):
        if name == "tracker":
            return self.tracker


class FakeWindow:
    """Stand-in for a Window, with just what calibration needs."""
    units = "height"
    colorSpace = "rgb"
    _isFullScr = False

    def __init__(self):
        from psychopy.colors import Color
        self._color = Color("grey")

    def flip(self):
        pass


class FakeTarget:
    """Stand-in for a calibration target, which can be serialized for ioHub."""

    def serialize(self):
        return {'__class__': "psychopy.visual.TargetStim"}


class NonIoHubEyetracker(BaseEyetrackerDevice):
    """
    Minimal eyetracker which doesn't use ioHub, to check the interface stands on its own.
    """

    def __init__(self):
        self.recording = False
        self.calibrated = None
        self.validated = None

    def startRecording(self):
        self.recording = True

    def stopRecording(self):
        self.recording = False

    def isRecording(self):
        return self.recording

    def getPos(self):
        return [0.3, 0.4]

    def calibrate(self, calibration):
        self.calibrated = calibration
        return "calibrated"

    def validate(self, validation):
        self.validated = validation
        return {'accuracy': 1}

    @staticmethod
    def getAvailableDevices():
        return [{
            'deviceName': "NonIoHub",
            'deviceClass': "psychopy.tests.test_hardware.test_eyetracker.NonIoHubEyetracker",
        }]


class TestEyetrackerDevice:
    def setup_method(self):
        self._ioServer = DeviceManager.ioServer
        DeviceManager.ioServer = None
        self.names = []

    def teardown_method(self):
        for name in self.names:
            if DeviceManager.getDevice(name) is not None:
                DeviceManager.removeDevice(name)
        DeviceManager.ioServer = self._ioServer

    def addDevice(self, deviceClass, deviceName, **kwargs):
        self.names.append(deviceName)
        return DeviceManager.addDevice(deviceClass, deviceName, **kwargs)

    def test_aliases(self):
        assert DeviceManager.getDeviceClass("eyetracker") is BaseEyetrackerDevice
        assert DeviceManager.getDeviceClass("iohubEyetracker") is IoHubEyetrackerDevice
        assert DeviceManager.getDeviceClass("mousegaze") is MouseGazeEyetracker

    def test_base_is_interface(self):
        # base class doesn't talk to any eyetracker, so required methods aren't implemented
        device = object.__new__(BaseEyetrackerDevice)
        for method in ("startRecording", "stopRecording", "isRecording", "getPos"):
            with pytest.raises(NotImplementedError):
                getattr(device, method)()
        # optional methods without a meaningful default also aren't implemented
        with pytest.raises(NotImplementedError):
            device.calibrate(None)
        with pytest.raises(NotImplementedError):
            device.validate(None)
        # event methods do nothing by default
        device.clearEvents()
        device.enableEventReporting()

    def test_non_iohub_eyetracker(self):
        device = self.addDevice(NonIoHubEyetracker, "testTracker")
        assert DeviceManager.hasDevice("testTracker", "eyetracker")
        assert not DeviceManager.hasDevice("testTracker", "iohubEyetracker")
        assert device.pos == [0.3, 0.4]
        # helpers should work with it via the interface
        ctrl = EyetrackerControl(device)
        ctrl.start()
        assert device.isRecording()
        ctrl.stop()
        assert not device.isRecording()
        win = FakeWindow()
        calib = EyetrackerCalibration(win, device, target=None)
        calib.run()
        assert device.calibrated is calib and calib.last == "calibrated"
        valid = EyetrackerValidation(win, device, target=None)
        assert valid.run() == {'accuracy': 1}
        assert device.validated is valid and valid.results == {'accuracy': 1}
        # should show up in available devices
        classes = [profile['deviceClass'] for profile in BaseEyetrackerDevice.getAvailableDevices()]
        assert NonIoHubEyetracker.getAvailableDevices()[0]['deviceClass'] in classes
        iohubClasses = [
            profile['deviceClass'] for profile in IoHubEyetrackerDevice.getAvailableDevices()
        ]
        assert NonIoHubEyetracker.getAvailableDevices()[0]['deviceClass'] not in iohubClasses

    def test_wrap_running_tracker(self):
        tracker = FakeTracker()
        conn = FakeConnection(tracker)
        device = self.addDevice("iohubEyetracker", "testTracker", ioServer=conn)
        # should be a managed eyetracker which wraps the ioHub tracker
        assert isinstance(device, IoHubEyetrackerDevice)
        assert device.tracker is tracker
        assert DeviceManager.hasDevice("testTracker", "eyetracker")
        assert DeviceManager.ioServer is conn
        # recording methods are passed on to the tracker
        device.startRecording()
        assert tracker.recording and device.isRecording()
        device.stopRecording()
        assert not tracker.recording and not device.isRecording()
        assert device.pos == device.getPos() == [0.1, 0.2]

    def test_attribute_fallthrough_warns(self):
        device = self.addDevice(
            "iohubEyetracker", "testTracker", ioServer=FakeConnection(FakeTracker())
        )
        IoHubEyetrackerDevice._warnedAttrs.discard("someTrackerSpecificMethod")
        warnings = []
        _warn = logging.warn
        logging.warn = warnings.append
        try:
            # methods not defined on the device should come from the ioHub tracker...
            assert device.someTrackerSpecificMethod() == "passed through"
            assert device.someTrackerSpecificMethod() == "passed through"
        finally:
            logging.warn = _warn
        # ...with a deprecation warning, given once
        assert len(warnings) == 1 and "deprecated" in warnings[0]
        with pytest.raises(AttributeError):
            device.notAMethod

    def test_unsupported_returns_none(self):
        device = self.addDevice(
            "iohubEyetracker", "testTracker", ioServer=FakeConnection(FakeTracker())
        )
        assert device.trackerTime() is None

    def test_iohub_running_without_tracker(self):
        with pytest.raises(ManagedDeviceError, match="without an eyetracker"):
            self.addDevice("iohubEyetracker", "testTracker", ioServer=FakeConnection(None))

    def test_iohub_running_different_tracker(self):
        conn = FakeConnection(
            FakeTracker("psychopy.iohub.devices.eyetracker.hw.tobii.EyeTracker")
        )
        with pytest.raises(ManagedDeviceError, match="different eyetracker"):
            self.addDevice(
                "psychopy.hardware.eyetracker.MouseGazeEyetracker", "testTracker", ioServer=conn
            )

    def test_mousegaze_wraps_mousegaze(self):
        device = self.addDevice(
            "psychopy.hardware.eyetracker.MouseGazeEyetracker", "testTracker",
            ioServer=FakeConnection(FakeTracker())
        )
        assert isinstance(device, MouseGazeEyetracker)
        assert device.isSameDevice({'deviceClass': "mousegaze"})
        assert device.isSameDevice({'deviceClass': "iohubEyetracker"})
        assert not device.isSameDevice({'deviceClass': "keyboard"})

    def test_mousegaze_io_config(self):
        config = MouseGazeEyetracker.getIoConfig(
            move="CONTINUOUS", blink=["MIDDLE_BUTTON"], saccadeThreshold=0.5
        )
        assert config == {
            "eyetracker.hw.mouse.EyeTracker": {
                'name': "tracker",
                'controls': {
                    'move': [],
                    'blink': ["MIDDLE_BUTTON"],
                    'saccade_threshold': 0.5,
                },
            }
        }
        # single button given as a string should become a list
        config = MouseGazeEyetracker.getIoConfig(move="LEFT_BUTTON", blink="RIGHT_BUTTON")
        controls = config["eyetracker.hw.mouse.EyeTracker"]['controls']
        assert controls['move'] == ["LEFT_BUTTON"]
        assert controls['blink'] == ["RIGHT_BUTTON"]

    def test_wrapper_has_no_io_config(self):
        with pytest.raises(NotImplementedError):
            IoHubEyetrackerDevice.getIoConfig()

    def test_available_devices(self):
        for cls in (BaseEyetrackerDevice, IoHubEyetrackerDevice):
            classes = [profile['deviceClass'] for profile in cls.getAvailableDevices()]
            assert "psychopy.hardware.eyetracker.MouseGazeEyetracker" in classes

    def test_eyetracker_control(self):
        tracker = FakeTracker()
        device = self.addDevice(
            "iohubEyetracker", "testTracker", ioServer=FakeConnection(tracker)
        )
        ctrl = EyetrackerControl(device)
        ctrl.start()
        # events should be cleared when starting from a full stop
        assert tracker.cleared == 1
        assert ctrl.currentlyRecording
        ctrl.stop()
        assert not ctrl.currentlyRecording
        assert ctrl.getPos() == [0.1, 0.2]

    def test_eyetracker_control_raw_iohub(self):
        # raw ioHub trackers should still work, for backwards compatibility
        tracker = FakeTracker()
        ctrl = EyetrackerControl(tracker)
        ctrl.start()
        assert tracker.recording and tracker.cleared == 1
        ctrl.stop()
        assert not tracker.recording

    def test_iohub_calibrate(self):
        tracker = FakeTracker()
        device = self.addDevice(
            "iohubEyetracker", "testTracker", ioServer=FakeConnection(tracker)
        )
        calib = EyetrackerCalibration(
            FakeWindow(), device, target=FakeTarget(), targetLayout="FIVE_POINTS"
        )
        calib.run()
        # tracker should get the calibration in ioHub format
        assert tracker.setupArgs['type'] == "FIVE_POINTS"
        assert calib.last == {'RESULT': "CALIBRATION_OK"}
        # converting to dict should give the same thing, for backwards compatibility
        assert dict(calib) == tracker.setupArgs

    def test_close_stops_recording(self):
        tracker = FakeTracker()
        device = self.addDevice(
            "iohubEyetracker", "testTracker", ioServer=FakeConnection(tracker)
        )
        device.startRecording()
        DeviceManager.removeDevice("testTracker")
        assert not tracker.recording
