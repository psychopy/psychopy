#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Base classes for joystick and gamepad devices.

This module defines `JoystickDevice`, the `DeviceManager`-aware base class for
all joystick and gamepad backends, along with the `JoystickResponse` class used
to report button, hat and axis events.

Note that this module must never import `psychopy.visual` at module scope, since
`psychopy.visual` imports `psychopy.hardware`.

"""

__all__ = [
    'JoystickError',
    'JoystickBackendNotAvailableError',
    'JoystickAxisNotAvailableError',
    'JoystickButtonNotAvailableError',
    'InvalidInputNameError',
    'JoystickResponse',
    'JoystickDevice',
    'BaseJoystickDevice',
    'BaseJoystickInterface',
]

import copy
import importlib.metadata

from psychopy import logging
from psychopy.hardware.base import BaseResponse, BaseResponseDevice
from psychopy.hardware.exceptions import DeviceNotConnectedError
import psychopy.hardware.joystick.mappings as mappings


# entry point group which plugins may use to contribute joystick backends
BACKEND_ENTRY_POINT_GROUP = "psychopy.hardware.joystick.backends"


# ------------------------------------------------------------------------------
# Exceptions
#

class JoystickError(Exception):
    """Exception raised for errors in the joystick module."""
    pass


class JoystickBackendNotAvailableError(JoystickError):
    """Exception raised when the requested backend is not available."""
    pass


class JoystickAxisNotAvailableError(JoystickError):
    """Exception raised when an axis is not available on the joystick."""
    pass


class InvalidInputNameError(JoystickError):
    """Exception raised when an input name is not valid."""
    pass


class JoystickButtonNotAvailableError(JoystickError):
    """Exception raised when a button is not available on the joystick."""
    pass


# ------------------------------------------------------------------------------
# Responses
#

class JoystickResponse(BaseResponse):
    """A timestamped joystick event.

    A single response class is used for buttons, hats and axes; the `inputType`
    field discriminates between them.

    Parameters
    ----------
    t : float
        Time at which the event was detected, according to the device's clock.
    value : bool, tuple or float
        The new state of the input. `bool` for buttons, an (x, y) `tuple` for
        hats, and `float` for axes.
    channel : int
        Index of the button, hat or axis which changed.
    inputType : str
        One of `'button'`, `'hat'` or `'axis'`.
    name : str or None
        Name of the input according to the device's active input scheme, if it
        has one.
    device : JoystickDevice or None
        The device which generated this response.

    """
    fields = ["t", "value", "channel", "inputType", "name"]

    def __init__(self, t, value, channel, inputType="button", name=None,
                 device=None):
        BaseResponse.__init__(self, t=t, value=value, device=device)
        self.channel = channel
        self.inputType = inputType
        self.name = name

    def __repr__(self):
        return "<{} from {}: t={}, {}={}, value={}>".format(
            type(self).__name__, self.getDeviceName(), self.t,
            self.inputType, self.name if self.name is not None else self.channel,
            self.value)

    def __eq__(self, other):
        # another response, compare input identity and value
        if isinstance(other, JoystickResponse):
            return (other.inputType == self.inputType
                    and other.channel == self.channel
                    and other.value == self.value)
        # NB: bool must be tested before int, as bool subclasses int
        if isinstance(other, bool):
            return self.inputType == "button" and other == self.value
        # a name from the active input scheme
        if isinstance(other, str):
            return other == self.name
        # a channel index
        if isinstance(other, int):
            return other == self.channel
        # a hat position
        if isinstance(other, (tuple, list)):
            return (isinstance(self.value, (tuple, list))
                    and tuple(other) == tuple(self.value))
        # an axis value
        if isinstance(other, float):
            return self.inputType == "axis" and other == self.value
        # a dict describing a response
        if isinstance(other, dict):
            try:
                return JoystickResponse(**other) == self
            except (TypeError, KeyError):
                return False
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


# ------------------------------------------------------------------------------
# Device
#

class JoystickDevice(BaseResponseDevice, aliases=["joystick", "gamepad"]):
    """A joystick or gamepad.

    This class is both the abstract base class for joystick backends and the
    dispatcher which selects one. Instantiating `JoystickDevice` directly
    returns an instance of the appropriate backend subclass::

        joy = JoystickDevice(0)                   # uses the default backend
        joy = JoystickDevice(0, backend='glfw')   # uses GLFW explicitly

    Because the backends subclass this class, `isinstance(joy, JoystickDevice)`
    holds for every joystick, which is what allows `DeviceManager.hasDevice`,
    `getInitialisedDevices` and `resolveDevice` to find them.

    Parameters
    ----------
    device : int, str or None
        Index or name of the joystick to open. `None` selects the first
        available device.
    backend : str, type or None
        Name of the input library to use (`'pyglet'`, `'glfw'`, `'virtual'`), or
        a `JoystickDevice` subclass. `None` uses the class-level `backend`
        attribute, falling back to the module-level `psychopy.hardware.joystick`
        `backend` value.
    deadzone : float
        Axis values whose magnitude falls below this are reported as zero.
        Applied to every axis.
    axisResponseThreshold : float or None
        If not `None`, axes emit `JoystickResponse` objects when they change by
        at least this much. `None` (the default) means axes are read by polling
        only and emit no responses, which avoids flooding listeners and the log
        with analogue noise.
    clock : psychopy.core.Clock or None
        Clock used to timestamp responses. Defaults to `logging.defaultClock`,
        matching the keyboard and button box devices.
    inputScheme : str
        Name of the input naming scheme to apply, see
        `psychopy.hardware.joystick.mappings`.

    """
    # name of the input library this backend uses, set by subclasses
    _inputLib = None
    # class-level backend override; None means "use the module-level default"
    backend = None
    # known backends, keyed by input library name
    backends = {
        'pyglet': importlib.metadata.EntryPoint(
            name="pyglet",
            value="psychopy.hardware.joystick.backend_pyglet:JoystickDevicePyglet",
            group=BACKEND_ENTRY_POINT_GROUP),
        'glfw': importlib.metadata.EntryPoint(
            name="glfw",
            value="psychopy.hardware.joystick.backend_glfw:JoystickDeviceGLFW",
            group=BACKEND_ENTRY_POINT_GROUP),
        'virtual': importlib.metadata.EntryPoint(
            name="virtual",
            value="psychopy.hardware.joystick.backend_virtual:JoystickDeviceVirtual",
            group=BACKEND_ENTRY_POINT_GROUP),
    }

    responseClass = JoystickResponse

    # --------------------------------------------------------------------------
    # Backend resolution
    #

    def __new__(cls, *args, **kwargs):
        # a concrete backend constructs itself as normal
        if cls is not JoystickDevice:
            return super().__new__(cls)
        # find the requested backend, allowing it as the 2nd positional arg
        backend = kwargs.get('backend', None)
        if backend is None and len(args) > 1 and isinstance(args[1], str):
            backend = args[1]
        backendCls = cls.resolveBackend(backend)
        # returning an instance of a *subclass* means Python still calls
        # __init__ exactly once, on the backend class
        return super().__new__(backendCls)

    @classmethod
    def resolveBackend(cls, backend=None, allowFallback=None):
        """Resolve a backend name to a `JoystickDevice` subclass.

        Precedence is: the `backend` argument, then the class-level `backend`
        attribute, then the module-level `psychopy.hardware.joystick.backend`
        global (read lazily, so assigning to it still works).

        Parameters
        ----------
        backend : str, type or None
            Name of the backend to resolve, or a `JoystickDevice` subclass.
        allowFallback : bool or None
            Whether to silently try another backend if this one fails to import.
            Defaults to `True` only when no backend was explicitly requested --
            asking for a specific backend and silently getting another one would
            hide a real configuration problem.

        Returns
        -------
        type
            A `JoystickDevice` subclass.

        Raises
        ------
        JoystickBackendNotAvailableError
            If the named backend is unknown, or could not be imported and no
            fallback was permitted.

        """
        # only fall back silently if the caller didn't ask for anything specific
        if allowFallback is None:
            allowFallback = backend is None
        # class-level override
        if backend is None:
            backend = cls.backend
        # module-level default, read lazily so `joystick.backend = 'glfw'` works
        if backend is None:
            import psychopy.hardware.joystick as _joystickmod
            backend = getattr(_joystickmod, "backend", "pyglet")
        # a list may be supplied, e.g. from prefs, so take the first known entry
        if isinstance(backend, (list, tuple)):
            known = [val for val in backend if val in cls.backends]
            backend = known[0] if known else (backend[0] if backend else None)
        # a class may be passed directly
        if isinstance(backend, type) and issubclass(backend, JoystickDevice):
            return backend

        if backend not in cls.backends:
            raise JoystickBackendNotAvailableError(
                "Joystick backend '{}' is not available, known backends are: "
                "{}".format(backend, list(cls.backends)))

        try:
            return cls.backends[backend].load()
        except ImportError as err:
            # drop the broken backend so we don't retry it this session
            del cls.backends[backend]
            if not allowFallback:
                raise JoystickBackendNotAvailableError(
                    "Joystick backend '{}' could not be loaded: {}".format(
                        backend, err))
            if not len(cls.backends):
                raise JoystickBackendNotAvailableError(
                    "All joystick backends failed to load.")
            nxt = list(cls.backends)[0]
            logging.error(
                "Failed to load joystick backend '{}', trying '{}'...".format(
                    backend, nxt))
            return cls.resolveBackend(nxt, allowFallback=True)

    # --------------------------------------------------------------------------
    # Lifecycle
    #

    def __init__(self, device=None, backend=None, deadzone=0.0,
                 axisResponseThreshold=None, clock=None,
                 inputScheme='default', **kwargs):
        BaseResponseDevice.__init__(self)

        # clock used to timestamp responses
        if clock is None:
            clock = logging.defaultClock
        self.clock = clock

        # resolve which physical device we're talking to
        self._deviceIndex = self._resolveDeviceIndex(device)
        self._device = None     # backend-specific handle
        self._isOpen = False
        self._trackerData = None
        # windows we've registered ourselves with for event dispatch
        self._dispatchWindows = []

        self.open()

        # input counts, these don't change once open
        self._numAxes = len(self._getRawAxes())
        self._numButtons = len(self._getRawButtons())
        self._numHats = len(self._getRawHats())

        # axis value modifiers
        self._axisScale = [1.0] * self._numAxes
        self._axisDeadzone = [float(deadzone)] * self._numAxes
        # per-axis response threshold; None means "don't emit responses"
        self._axisResponseThreshold = [
            axisResponseThreshold] * self._numAxes

        # cached states, used for edge detection when dispatching
        self._lastUpdateTime = 0.0
        self._axisVals = [0.0] * self._numAxes
        self._btnStates = [False] * self._numButtons
        self._hatStates = [(0, 0)] * self._numHats

        # VR and motion tracking properties
        self._pos = (0.0, 0.0, 0.0)
        self._ori = (0.0, 0.0, 0.0, 1.0)
        self._angularVel = (0.0, 0.0, 0.0)
        self._linearVel = (0.0, 0.0, 0.0)

        # input name mapping
        self._inputNames = {}
        self.setInputScheme(inputScheme)

    @classmethod
    def _resolveDeviceIndex(cls, device):
        """Resolve a device name or index to a canonical backend index.

        Both backends previously duplicated this logic and both got it wrong in
        different ways, so it lives here now.

        Parameters
        ----------
        device : int, str, dict or None
            Index, name, or profile of the device to resolve. `None` selects the
            first available device.

        Returns
        -------
        int
            The backend's canonical index for the device.

        """
        profiles = cls.getAvailableDevices()
        indices = [profile['device'] for profile in profiles]

        # a profile dict was handed to us
        if isinstance(device, dict):
            device = device.get('device', device.get('index', None))

        # first available device
        if device in (None, -1, 'None', 'default'):
            if not profiles:
                raise DeviceNotConnectedError(
                    "No joysticks are connected.", deviceClass=cls)
            return indices[0]

        # by name, accepting the backend-suffixed form too
        if isinstance(device, str):
            for profile in profiles:
                name = profile['deviceName']
                if device in (name, name.rsplit(" (", 1)[0]):
                    return profile['device']
            raise DeviceNotConnectedError(
                "No joystick found with the name '{}'".format(device),
                deviceClass=cls)

        # by index
        if device not in indices:
            raise DeviceNotConnectedError(
                "No joystick at index {} ({} joystick(s) connected)".format(
                    device, len(indices)),
                deviceClass=cls)

        return int(device)

    def open(self):
        """Open the joystick device."""
        if self.isOpen:
            return
        self._openDevice()
        self._isOpen = True
        self._registerWithWindows()

    def close(self):
        """Close the joystick device."""
        if not self.isOpen:
            return
        self._deregisterFromWindows()
        self._closeDevice()
        self._isOpen = False

    @property
    def isOpen(self):
        """Whether the joystick device is open (`bool`)."""
        return self._isOpen

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # Window event dispatch
    #

    # `Window` calls `dispatch_events` on everything in `_eventDispatchers`
    def dispatch_events(self):
        """Alias of `dispatchMessages`, called by `Window.flip`."""
        return self.dispatchMessages()

    def _registerWithWindows(self):
        """Register with any open windows so `win.flip()` dispatches us."""
        from psychopy import visual
        for ref in visual.openWindows:
            win = ref()
            if win is None or win in self._dispatchWindows:
                continue
            if self not in win._eventDispatchers:
                win._eventDispatchers.append(self)
            self._dispatchWindows.append(win)

    def _deregisterFromWindows(self):
        """Remove ourselves from any windows we registered with.

        `_eventDispatchers` holds a strong reference, so failing to do this
        would keep the device alive after it was closed.

        """
        for win in self._dispatchWindows:
            try:
                if self in win._eventDispatchers:
                    win._eventDispatchers.remove(self)
            except Exception:
                pass
        self._dispatchWindows = []

    # --------------------------------------------------------------------------
    # DeviceManager contract
    #

    def isSameDevice(self, other):
        """Whether `other` refers to the same physical device as this one.

        Accepts another device, a profile `dict` (which
        `BaseDevice.getDeviceProfile` passes in), or a bare index or name.

        """
        # another joystick -- the backend must match too, or a pyglet stick and
        # a GLFW stick at the same index would compare equal
        if isinstance(other, JoystickDevice):
            return (other.inputLib == self.inputLib
                    and other.deviceIndex == self.deviceIndex)

        if isinstance(other, dict):
            # if a backend is named, it has to be ours
            if other.get('backend', None) not in (None, self.inputLib):
                return False
            # match on index
            for key in ('device', 'index'):
                val = other.get(key, None)
                if isinstance(val, int) and not isinstance(val, bool):
                    return val == self.deviceIndex
            # otherwise match on name
            for key in ('deviceName', 'name', 'device'):
                val = other.get(key, None)
                if isinstance(val, str):
                    return val in (
                        self.getName(),
                        "{} ({})".format(self.getName(), self.inputLib))
            return False

        if isinstance(other, bool):
            return False
        if isinstance(other, int):
            return other == self.deviceIndex
        if isinstance(other, str):
            return other == self.getName()

        return False

    @classmethod
    def getAvailableDevices(cls):
        """Return a list of available joystick devices.

        On the base class this delegates to the currently selected backend,
        preserving the historical behaviour that enumeration reflects the active
        backend. Backends must override it.

        Returns
        -------
        list of dict
            Device profiles. Every key other than `deviceName` and
            `deviceClass` must be a valid `__init__` keyword argument.

        """
        if cls is not JoystickDevice:
            raise NotImplementedError(
                "{} must implement getAvailableDevices()".format(cls.__name__))
        return cls.resolveBackend().getAvailableDevices()

    # --------------------------------------------------------------------------
    # Backend hooks -- subclasses must implement these
    #

    def _openDevice(self):
        """Acquire the underlying device handle."""
        raise NotImplementedError

    def _closeDevice(self):
        """Release the underlying device handle."""
        raise NotImplementedError

    def _getRawAxes(self):
        """Raw, unscaled axis values as a `list` of `float`."""
        raise NotImplementedError

    def _getRawButtons(self):
        """Raw button states as a `list` of `bool`."""
        raise NotImplementedError

    def _getRawHats(self):
        """Raw hat states as a `list` of (x, y) `tuple`."""
        raise NotImplementedError

    def getName(self):
        """The manufacturer-defined name describing the device (`str`)."""
        raise NotImplementedError

    def update(self):
        """Pump the backend's event queue, if it has one.

        Some backends update automatically and need do nothing here.

        """
        pass

    def setEventCallback(self, evt, callback):
        """Set a callback to be invoked when a joystick event occurs.

        Only supported by some backends.

        """
        raise NotImplementedError(
            "Event callbacks are not supported by the '{}' joystick "
            "backend.".format(self.inputLib))

    def setVibration(self, motor, strength=1.0):
        """Set the strength of a vibration motor."""
        raise NotImplementedError(
            "Vibration is not supported by the '{}' joystick backend.".format(
                self.inputLib))

    def setVibrationSamples(self, motor, samples, sampleRate=None):
        """Upload vibration samples to the device's sample buffer."""
        raise NotImplementedError(
            "Vibration is not supported by the '{}' joystick backend.".format(
                self.inputLib))

    # --------------------------------------------------------------------------
    # Properties
    #

    @property
    def inputLib(self):
        """Name of the input library backing this device (`str`)."""
        return self._inputLib

    @property
    def name(self):
        """Name of the joystick reported by the system (`str`)."""
        return self.getName()

    @property
    def deviceIndex(self):
        """The backend's index for this joystick (`int`)."""
        return self._deviceIndex

    @property
    def hasTracking(self):
        """Whether the device reports position and orientation (`bool`)."""
        return False

    @property
    def trackerData(self):
        """Raw tracking data, if the device provides any."""
        return self._trackerData

    def lastUpdateTime(self):
        """Time at which the device state was last sampled (`float`)."""
        return self._lastUpdateTime

    # --------------------------------------------------------------------------
    # Motion tracking
    #

    def getPos(self):
        """Position of the device, if it has tracking."""
        if not self.hasTracking:
            raise NotImplementedError(
                "The '{}' joystick backend does not support position "
                "tracking.".format(self.inputLib))
        return self._pos

    def getOri(self):
        """Orientation of the device as a quaternion, if it has tracking."""
        if not self.hasTracking:
            raise NotImplementedError(
                "The '{}' joystick backend does not support orientation "
                "tracking.".format(self.inputLib))
        return self._ori

    def getLinearVelocity(self):
        """Linear velocity of the device, if it has tracking."""
        if not self.hasTracking:
            raise NotImplementedError(
                "The '{}' joystick backend does not support velocity "
                "tracking.".format(self.inputLib))
        return self._linearVel

    def getAngularVelocity(self):
        """Angular velocity of the device, if it has tracking."""
        if not self.hasTracking:
            raise NotImplementedError(
                "The '{}' joystick backend does not support velocity "
                "tracking.".format(self.inputLib))
        return self._angularVel

    @property
    def pos(self):
        return self.getPos()

    @property
    def ori(self):
        return self.getOri()

    @property
    def linearVelocity(self):
        return self.getLinearVelocity()

    @property
    def angularVelocity(self):
        return self.getAngularVelocity()

    # --------------------------------------------------------------------------
    # Input naming
    #

    def setInputScheme(self, mapping):
        """Apply a named input scheme to this device.

        Parameters
        ----------
        mapping : str
            Name of the scheme, e.g. `'default'`, `'xbox'`, `'hotasx'`. See
            `psychopy.hardware.joystick.mappings.getAvailableInputSchemes`.

        """
        inputMap = mappings.getInputScheme(mapping, self.inputLib)
        if inputMap is None:
            raise ValueError("Invalid mapping scheme '{}'.".format(mapping))

        logging.info(
            "Setting input scheme for joystick to '{}'.".format(mapping))

        # deep copy, otherwise mutating our names would mutate the module-level
        # mapping table and leak into every joystick created afterwards
        self._inputNames = copy.deepcopy(inputMap)
        # make sure every input type is present
        for inputType in ('axes', 'buttons', 'hats'):
            self._inputNames.setdefault(inputType, {})

    def setInputName(self, inputType, inputIndex, name):
        """Give an input a name, so it can be addressed by that name.

        Parameters
        ----------
        inputType : str
            One of `'axes'`, `'buttons'` or `'hats'`.
        inputIndex : int or list of int
            Index of the input. A list groups several inputs under one name.
        name : str or None
            Name to assign. `None` removes the name.

        Examples
        --------
        Name axis 0 and read it back by name::

            joy.setInputName('axes', 0, 'x')
            xVal = joy.getAxis('x')

        Group two axes under one name::

            joy.setInputName('axes', [0, 1], 'left_thumbstick')
            xVal, yVal = joy.getAxis('left_thumbstick')

        """
        if inputType not in ('axes', 'buttons', 'hats'):
            raise ValueError("Input type must be 'axes', 'buttons', or 'hats'.")

        if name is None:
            # remove by name, not by index
            self._inputNames[inputType].pop(name, None)
            return

        if isinstance(inputIndex, list):
            inputIndex = tuple(inputIndex)

        # names map to indices, not the other way around
        self._inputNames[inputType][name] = inputIndex

    def getInputName(self, inputType, inputIndex):
        """Get the name of an input by its index, or `None` if it has none."""
        for name, idx in self._inputNames.get(inputType, {}).items():
            if idx == inputIndex:
                return name
        return None

    def _getIndexFromName(self, inputType, name):
        """Resolve an input name to its index.

        Raises
        ------
        InvalidInputNameError
            If the name has not been set.

        """
        inputIndex = self._inputNames.get(inputType, {}).get(name, None)
        if inputIndex is not None:
            return inputIndex

        raise InvalidInputNameError(
            "Input name '{}' is not valid.".format(name))

    # --------------------------------------------------------------------------
    # Axis filtering
    #

    def getAxisScale(self, axisId=None):
        """Get the scale factor applied to an axis."""
        if axisId is None:
            return list(self._axisScale)

        if isinstance(axisId, str):
            axisId = self._getIndexFromName('axes', axisId)

        if isinstance(axisId, (list, tuple)):
            return [self.getAxisScale(ax) for ax in axisId]

        return self._axisScale[axisId]

    def setAxisScale(self, axisId, scale):
        """Set the scale factor applied to an axis.

        Parameters
        ----------
        axisId : int, str, list or None
            Axis to set, by index or name. A name may map to several axes, and
            a list sets each in turn. `None` sets every axis.
        scale : float
            Factor multiplied into the axis value. Negative inverts the axis.

        """
        if not isinstance(scale, (int, float)):
            raise TypeError("Scaling factor must be a numeric type.")

        if isinstance(axisId, str):
            axisId = self._getIndexFromName('axes', axisId)

        if axisId is None:
            self._axisScale = [scale] * len(self._axisScale)
            return

        # a name may resolve to several ganged axes, e.g. 'XY' -> (0, 1)
        if isinstance(axisId, (list, tuple)):
            for ax in axisId:
                self.setAxisScale(ax, scale)
            return

        self._axisScale[axisId] = scale

    def getAxisDeadzone(self, axisId=None):
        """Get the deadzone applied to an axis."""
        if axisId is None:
            return list(self._axisDeadzone)

        if isinstance(axisId, str):
            axisId = self._getIndexFromName('axes', axisId)

        if isinstance(axisId, (list, tuple)):
            return [self.getAxisDeadzone(ax) for ax in axisId]

        return self._axisDeadzone[axisId]

    def setAxisDeadzone(self, axisId=None, deadzone=0.1):
        """Set the deadzone applied to an axis.

        Parameters
        ----------
        axisId : int, str, list or None
            Axis to set, by index or name. `None` sets every axis.
        deadzone : float
            Magnitude below which the axis reads as zero, between 0 and 1.

        """
        if not isinstance(deadzone, (int, float)):
            raise TypeError("Deadzone must be a numeric type.")

        deadzone = min(1.0, max(0.0, deadzone))
        if axisId is None:
            self._axisDeadzone = [deadzone] * len(self._axisDeadzone)
            return

        if isinstance(axisId, str):
            axisId = self._getIndexFromName('axes', axisId)

        if isinstance(axisId, (list, tuple)):
            for ax in axisId:
                self.setAxisDeadzone(ax, deadzone)
            return

        self._axisDeadzone[axisId] = deadzone

    def getAxisResponseThreshold(self, axisId=None):
        """Get the change in an axis required to emit a response."""
        if axisId is None:
            return list(self._axisResponseThreshold)

        if isinstance(axisId, str):
            axisId = self._getIndexFromName('axes', axisId)

        if isinstance(axisId, (list, tuple)):
            return [self.getAxisResponseThreshold(ax) for ax in axisId]

        return self._axisResponseThreshold[axisId]

    def setAxisResponseThreshold(self, threshold, axisId=None):
        """Make an axis emit `JoystickResponse` objects when it moves.

        Axes emit no responses by default: an analogue stick at rest would
        otherwise produce a response on every dispatch, flooding the log and any
        attached listeners. The threshold is applied after scaling and deadzone,
        so a stick released to centre emits exactly one response.

        Parameters
        ----------
        threshold : float or None
            Minimum change in the axis value needed to emit a response. `None`
            disables responses for this axis.
        axisId : int, str, list or None
            Axis to set, by index or name. `None` sets every axis.

        """
        if threshold is not None and not isinstance(threshold, (int, float)):
            raise TypeError("Axis response threshold must be numeric or None.")

        if isinstance(axisId, str):
            axisId = self._getIndexFromName('axes', axisId)

        if axisId is None:
            self._axisResponseThreshold = [
                threshold] * len(self._axisResponseThreshold)
            return

        if isinstance(axisId, (list, tuple)):
            for ax in axisId:
                self.setAxisResponseThreshold(threshold, ax)
            return

        self._axisResponseThreshold[axisId] = threshold

    # --------------------------------------------------------------------------
    # Axes
    #

    def getNumAxes(self):
        """Number of axes on the device (`int`)."""
        return self._numAxes

    def getAllAxes(self):
        """All current axis values, with scaling and deadzone applied."""
        allAxes = list(self._getRawAxes())

        for i, axisVal in enumerate(allAxes):
            if axisVal is None:
                allAxes[i] = 0.0
                continue
            allAxes[i] = axisVal * self._axisScale[i] \
                if abs(axisVal) >= self._axisDeadzone[i] else 0.0

        return allAxes

    def getAxis(self, axisId):
        """Get the value of an axis, by index or name.

        Parameters
        ----------
        axisId : int, str or list
            Axis to read. A name which maps to several axes, or a list, returns
            a list of values.

        Returns
        -------
        float or list

        """
        if isinstance(axisId, str):
            axisId = self._getIndexFromName('axes', axisId)

        if isinstance(axisId, (list, tuple)):
            return [self.getAxis(ax) for ax in axisId]

        return self.getAllAxes()[axisId]

    def getX(self):
        """Return the X axis value."""
        return self.getAxis(0)

    def getY(self):
        """Return the Y axis value."""
        return self.getAxis(1)

    def getXY(self):
        """Return the X and Y axis values as a list."""
        return [self.getAxis(0), self.getAxis(1)]

    def getZ(self):
        """Return the Z axis value."""
        return self.getAxis(2)

    def getRX(self):
        """Return the RX axis value."""
        return self.getAxis(3)

    def getRY(self):
        """Return the RY axis value."""
        return self.getAxis(4)

    def getRZ(self):
        """Return the RZ axis value."""
        return self.getAxis(5)

    # --------------------------------------------------------------------------
    # Buttons
    #

    def getNumButtons(self):
        """Number of buttons on the device (`int`)."""
        return self._numButtons

    def getAllButtons(self):
        """State of every button, as a list of `bool`."""
        return [bool(state) for state in self._getRawButtons()]

    def getButton(self, buttonId):
        """Get the state of a button, by index or name.

        Parameters
        ----------
        buttonId : int, str or list
            Button to read. A name which maps to several buttons, or a list,
            returns a list of states.

        Returns
        -------
        bool or list

        """
        if isinstance(buttonId, str):
            buttonId = self._getIndexFromName('buttons', buttonId)

        if isinstance(buttonId, (list, tuple)):
            return [self.getButton(b) for b in buttonId]

        return self.getAllButtons()[buttonId]

    # --------------------------------------------------------------------------
    # Hats
    #

    def getNumHats(self):
        """Number of hats on the device (`int`)."""
        return self._numHats

    def getAllHats(self):
        """Position of every hat, as a list of (x, y) tuples."""
        return [tuple(hat) for hat in self._getRawHats()]

    def getHat(self, hatId=0):
        """Get the position of a hat, by index or name.

        Returns
        -------
        tuple or list
            An (x, y) tuple where each value is -1, 0 or +1.

        """
        if isinstance(hatId, str):
            hatId = self._getIndexFromName('hats', hatId)

        if isinstance(hatId, (list, tuple)):
            return [self.getHat(h) for h in hatId]

        hats = self.getAllHats()
        if not hats:
            return ()

        return hats[hatId]

    # --------------------------------------------------------------------------
    # Responses
    #

    def resetTimer(self, clock=None):
        """Reset the clock used to timestamp responses."""
        if clock is None:
            clock = logging.defaultClock
        self.clock = clock
        self.clock.reset()

    def parseMessage(self, message):
        """Responses are built directly in `dispatchMessages`, so this is a
        pass-through.
        """
        return message

    def dispatchMessages(self):
        """Sample the device and emit a response for anything which changed.

        Joysticks are polled rather than event-driven, so this does edge
        detection against the cached state. Buttons and hats always emit
        responses; axes only do so where a response threshold has been set via
        `setAxisResponseThreshold`.

        Note that response times are quantised to the interval at which this is
        called, which is usually once per screen refresh.

        """
        if not self.isOpen:
            return False

        # make sure a window opened after us also dispatches us
        self._registerWithWindows()
        self.update()

        # one timestamp for the whole sweep
        t = self.clock.getTime()
        self._lastUpdateTime = t

        # buttons
        for i, state in enumerate(self.getAllButtons()[:self._numButtons]):
            state = bool(state)
            if state != self._btnStates[i]:
                self._btnStates[i] = state
                self.receiveMessage(JoystickResponse(
                    t=t, value=state, channel=i, inputType="button",
                    name=self.getInputName('buttons', i), device=self))

        # hats
        for i, state in enumerate(self.getAllHats()[:self._numHats]):
            state = tuple(state)
            if state != self._hatStates[i]:
                self._hatStates[i] = state
                self.receiveMessage(JoystickResponse(
                    t=t, value=state, channel=i, inputType="hat",
                    name=self.getInputName('hats', i), device=self))

        # axes, opt-in only
        for i, val in enumerate(self.getAllAxes()[:self._numAxes]):
            threshold = self._axisResponseThreshold[i]
            if threshold is None:
                # keep the cache fresh even when not reporting
                self._axisVals[i] = val
                continue
            if abs(val - self._axisVals[i]) >= threshold:
                self._axisVals[i] = val
                self.receiveMessage(JoystickResponse(
                    t=t, value=float(val), channel=i, inputType="axis",
                    name=self.getInputName('axes', i), device=self))

        return True

    def getResponses(self, state=None, channel=None, inputType=None,
                     clear=True):
        """Get responses matching the given criteria.

        Parameters
        ----------
        state : bool, tuple, float or None
            Only return responses with this value.
        channel : int, str, list or None
            Only return responses from these channels. Names are resolved
            against the active input scheme.
        inputType : str or None
            Only return responses of this type, one of `'button'`, `'hat'` or
            `'axis'`.
        clear : bool
            Whether to remove the returned responses from the queue.

        Returns
        -------
        list of JoystickResponse

        """
        # normalise the channel filter
        if isinstance(channel, (list, tuple)) and not len(channel):
            channel = None
        if channel is not None and not isinstance(channel, (list, tuple)):
            channel = [channel]
        if channel is not None:
            resolved = []
            for chan in channel:
                if isinstance(chan, str):
                    chan = self._getIndexFromName(
                        {'button': 'buttons', 'hat': 'hats',
                         'axis': 'axes'}.get(inputType, 'buttons'), chan)
                if isinstance(chan, (list, tuple)):
                    resolved.extend(chan)
                else:
                    resolved.append(chan)
            channel = resolved

        self.dispatchMessages()

        # NB: rebuild rather than index()/pop() -- __eq__ is deliberately
        # liberal, so index() would find the first *equal* response and pop the
        # wrong object, giving it the wrong timestamp
        matches, remaining = [], []
        for resp in self.responses:
            matched = (
                (state is None or resp.value == state)
                and (channel is None or resp.channel in channel)
                and (inputType is None or resp.inputType == inputType))
            if matched:
                matches.append(resp)
            if not (matched and clear):
                remaining.append(resp)

        if clear:
            self.responses = remaining

        return matches

    def getState(self, channel, inputType="button"):
        """Get the current state of a single input, dispatching first."""
        self.dispatchMessages()
        if inputType == "button":
            return self.getButton(channel)
        if inputType == "hat":
            return self.getHat(channel)
        return self.getAxis(channel)

    # --------------------------------------------------------------------------
    # Polling
    #

    def poll(self):
        """Sample the device and update its cached state.

        This also dispatches responses, so code which polls still populates the
        response queue.

        Returns
        -------
        float
            The time at which the device was sampled.

        """
        self.dispatchMessages()

        if self.hasTracking:
            self._pos = self.getPos()
            self._ori = self.getOri()
            self._angularVel = self.getAngularVelocity()
            self._linearVel = self.getLinearVelocity()

        if self._trackerData is not None:
            self._lastUpdateTime = getattr(
                self._trackerData, '_absSampleTime', self._lastUpdateTime)

        return self._lastUpdateTime


# register plugin-provided backends
for _ep in importlib.metadata.entry_points(group=BACKEND_ENTRY_POINT_GROUP):
    JoystickDevice.backends[_ep.name] = _ep


# legacy aliases -- these named the same concept before the DeviceManager
# migration and are kept so existing code and plugins keep importing
BaseJoystickDevice = JoystickDevice
BaseJoystickInterface = JoystickDevice


if __name__ == "__main__":
    pass
