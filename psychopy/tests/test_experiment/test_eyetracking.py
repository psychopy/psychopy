"""Tests for compiling experiments which use eyetrackers, either from Device Manager or from
Experiment Settings (legacy).
"""
from psychopy import experiment
from psychopy.preferences import prefs
from psychopy.experiment.routines import Routine
from psychopy.experiment.components.eyetracker_record import EyetrackerRecordComponent
from psychopy.experiment.components.roi import RegionOfInterestComponent
from psychopy.experiment.routines.eyetracker_calibrate import EyetrackerCalibrationRoutine
from psychopy.experiment.routines.eyetracker_validate import EyetrackerValidationRoutine
from psychopy.experiment.devices import DeviceBackend
from psychopy.experiment.eyetracking import MouseGazeEyetrackerDeviceBackend


def _makeExperiment(deviceLabel="", legacyEyetracker=None):
    """
    Make an experiment with every eyetracking Component and Routine, all pointed at the given
    device.
    """
    exp = experiment.Experiment()
    if legacyEyetracker is not None:
        exp.settings.params['eyetracker'].val = legacyEyetracker
    # calibration
    cal = EyetrackerCalibrationRoutine(exp, name="cal", deviceLabel=deviceLabel)
    exp.addStandaloneRoutine("cal", cal)
    exp.flow.addRoutine(cal, 0)
    # trial with record and roi
    trial = exp.addRoutine("trial", Routine("trial", exp))
    trial.addComponent(
        EyetrackerRecordComponent(exp, "trial", name="etRecord", deviceLabel=deviceLabel)
    )
    trial.addComponent(
        RegionOfInterestComponent(exp, "trial", name="roi", deviceLabel=deviceLabel)
    )
    exp.flow.addRoutine(trial, 1)
    # validation
    val = EyetrackerValidationRoutine(exp, name="val", deviceLabel=deviceLabel)
    exp.addStandaloneRoutine("val", val)
    exp.flow.addRoutine(val, 2)

    return exp


def _lineOf(script, text):
    """
    Get the index of the first line in a script containing the given text.
    """
    for i, line in enumerate(script.splitlines()):
        if text in line:
            return i
    raise AssertionError(f"Could not find `{text}` in script")


class TestEyetrackerCompile:
    deviceName = "testEyetracker"

    def setup_method(self):
        # add a MouseGaze eyetracker to Device Manager
        backend = MouseGazeEyetrackerDeviceBackend({
            'deviceName': "MouseGaze",
            'deviceClass': MouseGazeEyetrackerDeviceBackend.deviceClass,
        })
        backend.params['name'].val = self.deviceName
        prefs.devices[self.deviceName] = backend

    def teardown_method(self):
        prefs.devices.pop(self.deviceName, None)

    def test_backend_registered(self):
        # backend should be visible to Device Manager
        assert MouseGazeEyetrackerDeviceBackend in DeviceBackend.getAllBackends()
        # and selectable by every eyetracking element
        for cls in (
            EyetrackerRecordComponent,
            RegionOfInterestComponent,
            EyetrackerCalibrationRoutine,
            EyetrackerValidationRoutine,
        ):
            assert MouseGazeEyetrackerDeviceBackend in cls.backends

    def test_device_manager_eyetracker(self):
        exp = _makeExperiment(deviceLabel=self.deviceName)
        assert exp.usesEyetracker()
        script = exp.writeScript(target="PsychoPy")
        # should compile
        compile(script, "<test_device_manager_eyetracker>", "exec")
        # ioHub is needed
        assert "import psychopy.iohub as io" in script
        # tracker should be configured before ioHub launches and added to DeviceManager after
        configLine = _lineOf(script, ").getIoConfig(")
        launchLine = _lineOf(script, "io.launchHubServer(")
        addLine = _lineOf(
            script, "deviceClass='psychopy.hardware.eyetracker.MouseGazeEyetracker'"
        )
        aliasLine = _lineOf(
            script, f"deviceManager.addDeviceAlias('{self.deviceName}', 'eyetracker')"
        )
        assert configLine < launchLine < addLine < aliasLine
        # legacy eyetracker setup shouldn't be written
        assert "ioConfig['eyetracker.hw.mouse.EyeTracker']" not in script
        assert "IoHubEyetrackerDevice" not in script
        # elements should get the tracker from DeviceManager
        getter = f"deviceManager.getDevice('{self.deviceName}')"
        assert f"tracker={getter}" in script
        assert f"device={getter}" in script
        assert f"{getter}, calTarget" in script
        assert f"{getter}, valTarget" in script
        # validation should go via the device, not ioHub directly
        assert "val = EyetrackerValidation(win," in script
        assert "iohub.ValidationProcedure" not in script

    def test_legacy_eyetracker(self):
        exp = _makeExperiment(legacyEyetracker="eyetracker.hw.mouse.EyeTracker")
        assert exp.usesEyetracker()
        script = exp.writeScript(target="PsychoPy")
        # should compile
        compile(script, "<test_legacy_eyetracker>", "exec")
        # tracker should be configured from Experiment Settings
        configLine = _lineOf(script, "ioConfig['eyetracker.hw.mouse.EyeTracker'] = {")
        launchLine = _lineOf(script, "io.launchHubServer(")
        # and added to DeviceManager by wrapping whatever tracker ioHub is running
        addLine = _lineOf(
            script, "deviceClass='psychopy.hardware.eyetracker.IoHubEyetrackerDevice'"
        )
        assert configLine < launchLine < addLine
        assert "deviceManager.devices['eyetracker']" not in script
        # elements should use the `eyetracker` variable
        assert "tracker=eyetracker," in script
        assert "device=eyetracker," in script
        assert "eyetracker, calTarget" in script
        assert "eyetracker, valTarget" in script

    def test_device_manager_overrides_legacy(self):
        exp = _makeExperiment(
            deviceLabel=self.deviceName, legacyEyetracker="eyetracker.hw.mouse.EyeTracker"
        )
        script = exp.writeScript(target="PsychoPy")
        # only the eyetracker from Device Manager should be set up
        assert ").getIoConfig(" in script
        assert "ioConfig['eyetracker.hw.mouse.EyeTracker']" not in script
        assert "IoHubEyetrackerDevice" not in script

    def test_no_eyetracker(self):
        exp = _makeExperiment()
        assert not exp.usesEyetracker()
        assert not exp.settings.needIoHub
        script = exp.writeScript(target="PsychoPy")
        assert "io.launchHubServer(" not in script
