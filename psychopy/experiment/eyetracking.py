"""
Device Manager backends for eyetrackers.

These let eyetrackers be configured in Device Manager (and so stored per-machine in
`devices.json`) rather than in Experiment Settings. Eyetracking Components and Routines then
select which tracker to use via their "Device" param.

Eyetrackers can need code in `setupDevices` both before and after other devices are set up:

1. `writePreDeviceCode` is written first, before ioHub (if used) is launched. ioHub can only use
   devices which were configured when it launched, so ioHub eyetrackers use this to add their
   settings to `ioConfig` (see `IoHubEyetrackerDeviceBackend`).
2. `writeDeviceCode` is written along with other devices from Device Manager, and adds the device
   to DeviceManager.

To add a new kind of eyetracker (e.g. from a plugin), subclass `EyetrackerDeviceBackend` (or
`IoHubEyetrackerDeviceBackend`, if the tracker runs in ioHub), setting `deviceClass` to a subclass
of `psychopy.hardware.eyetracker.BaseEyetrackerDevice` and overloading `getParams` and
`getDeviceKwargs`, then call `registerEyetrackerDeviceBackend` on it.
"""

from psychopy.experiment.devices import DeviceBackend
from psychopy.experiment.params import Param
from psychopy.localization import _translate


def registerEyetrackerDeviceBackend(backend):
    """
    Register an eyetracker device backend with all of the Components and Routines which use
    eyetrackers, so that it appears in Device Manager and can be selected by them.

    Parameters
    ----------
    backend : type
        Subclass of `EyetrackerDeviceBackend` to register
    """
    from psychopy.experiment.components.eyetracker_record import EyetrackerRecordComponent
    from psychopy.experiment.components.roi import RegionOfInterestComponent
    from psychopy.experiment.routines.eyetracker_calibrate import EyetrackerCalibrationRoutine
    from psychopy.experiment.routines.eyetracker_validate import EyetrackerValidationRoutine

    for emt in (
        EyetrackerRecordComponent,
        RegionOfInterestComponent,
        EyetrackerCalibrationRoutine,
        EyetrackerValidationRoutine,
    ):
        emt.registerBackend(backend)


def getEyetrackerDeviceCode(deviceLabel):
    """
    Get the code to refer to the eyetracker for a given value of a Component's "Device" param.

    Parameters
    ----------
    deviceLabel : psychopy.experiment.Param
        Value of the Component's `deviceLabel` param

    Returns
    -------
    str
        Code to get the eyetracker: from DeviceManager if a device is named, otherwise the
        `eyetracker` variable (set up from Experiment Settings).
    """
    if deviceLabel is None or deviceLabel.val in (None, "", "None"):
        return "eyetracker"

    return "deviceManager.getDevice(%s)" % deviceLabel


class EyetrackerDeviceBackend(DeviceBackend):
    """
    Base class for Device Manager backends representing an eyetracker.
    """
    # information about this backend's needs (for raising alerts and etc.)
    needsFullscreen = True
    needsCalibration = True
    # does this eyetracker need ioHub to be running?
    needsIoHub = False

    def getDeviceKwargs(self):
        """
        Get the keyword arguments which configure this tracker, as code. These are given to
        `DeviceManager.addDevice`, so should match the device class's `__init__` arguments.

        Returns
        -------
        str
            Code for keyword arguments, one per line, each ending in a comma, e.g.
            `"move='CONTINUOUS',\\nblink=['MIDDLE_BUTTON'],\\n"`
        """
        return ""

    def getSessionKwargs(self):
        """
        Get any keyword arguments for `DeviceManager.addDevice` which come from the experiment
        session rather than the tracker's settings (e.g. the window), as code.

        Returns
        -------
        str
            Code for keyword arguments, one per line, each ending in a comma.
        """
        return ""

    def writePreDeviceCode(self, buff):
        """
        Write any code which needs to run before devices are set up (and before ioHub is
        launched, if used). Does nothing unless overloaded.

        Parameters
        ----------
        buff : io.StringIO
            Buffer to write to
        """
        pass

    def writeDeviceCode(self, buff):
        """
        Write code to add this tracker to DeviceManager.

        Parameters
        ----------
        buff : io.StringIO
            Buffer to write to
        """
        # make sure the profile includes the device class
        self.profile.setdefault('deviceClass', self.deviceClass)
        # open addDevice call
        self.writeBaseDeviceCode(buff, close=False)
        # add tracker settings
        buff.setIndentLevel(+1, relative=True)
        buff.writeIndentedLines(self.getDeviceKwargs())
        buff.writeIndentedLines(self.getSessionKwargs())
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines(")\n")
        # store under "eyetracker" too, so the `eyetracker` variable picks it up
        if self.params['name'].val != "eyetracker":
            code = (
                "deviceManager.addDeviceAlias(%(name)s, 'eyetracker')\n"
            )
            buff.writeIndentedLines(code % self.params)


class IoHubEyetrackerDeviceBackend(EyetrackerDeviceBackend):
    """
    Base class for Device Manager backends representing an eyetracker which runs in ioHub. The
    device class should be a subclass of `psychopy.hardware.eyetracker.IoHubEyetrackerDevice`.
    """
    needsIoHub = True

    def getSessionKwargs(self):
        return (
            "ioServer=ioServer,\n"
            "win=win,\n"
        )

    def writePreDeviceCode(self, buff):
        """
        Write code to add this tracker's settings to `ioConfig`, which must happen before ioHub is
        launched. Uses the same keyword arguments as `addDevice` (from `getDeviceKwargs`).

        Parameters
        ----------
        buff : io.StringIO
            Buffer to write to
        """
        code = (
            "# configure eyetracker %(name)s\n"
            "ioConfig.update(\n"
            "    deviceManager.getDeviceClass(\n"
        ) % self.params
        code += f"        {repr(self.deviceClass)}\n"
        code += (
            "    ).getIoConfig(\n"
        )
        buff.writeIndentedLines(code)
        buff.setIndentLevel(+2, relative=True)
        buff.writeIndentedLines(self.getDeviceKwargs())
        buff.setIndentLevel(-2, relative=True)
        code = (
            "    )\n"
            ")\n"
        )
        buff.writeIndentedLines(code)


class MouseGazeEyetrackerDeviceBackend(IoHubEyetrackerDeviceBackend):
    """
    Device Manager backend for MouseGaze, a simulated eyetracker controlled by the mouse.
    """
    backendLabel = "MouseGaze"
    deviceClass = "psychopy.hardware.eyetracker.MouseGazeEyetracker"
    icon = "components/eyetracker_record/light/eyetracker_record.png"

    needsFullscreen = False
    needsCalibration = False

    def getParams(self):
        # define order
        order = [
            "mgMove",
            "mgBlink",
            "mgSaccade",
        ]
        # define params
        params = {}
        params['mgMove'] = Param(
            "CONTINUOUS", valType='str', inputType="choice",
            allowedVals=['CONTINUOUS', 'LEFT_BUTTON', 'MIDDLE_BUTTON', 'RIGHT_BUTTON'],
            hint=_translate(
                "Mouse button to hold for gaze to move (or CONTINUOUS for gaze to always follow "
                "the mouse)."
            ),
            label=_translate("Move button")
        )
        params['mgBlink'] = Param(
            ["MIDDLE_BUTTON"], valType='list', inputType="multiChoice",
            allowedVals=['LEFT_BUTTON', 'MIDDLE_BUTTON', 'RIGHT_BUTTON'],
            hint=_translate("Mouse button to press for a blink."),
            label=_translate("Blink button")
        )
        params['mgSaccade'] = Param(
            0.5, valType='num', inputType="single",
            hint=_translate("Visual degree threshold for Saccade event creation."),
            label=_translate("Saccade threshold")
        )

        return params, order

    def getDeviceKwargs(self):
        code = (
            "move=%(mgMove)s,\n"
            "blink=%(mgBlink)s,\n"
            "saccadeThreshold=%(mgSaccade)s,\n"
        )

        return code % self.params
