#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Control joysticks and gamepads from within PsychoPy.

Joysticks are managed by `DeviceManager`, so a joystick may be configured once
and referred to by name::

    from psychopy.hardware import DeviceManager

    joy = DeviceManager.addDevice(
        deviceClass="psychopy.hardware.joystick.JoystickDevice",
        deviceName="myGamepad", device=0)

The `Joystick` class below wraps a `JoystickDevice` and is what Builder
generates. Creating one registers the underlying device with `DeviceManager` if
it isn't registered already.

Which input library is used depends on the backend. The `'pyglet'` backend needs
an open pyglet window which is being flipped in order to update, while the
`'glfw'` backend needs no window at all and works alongside a window created by
any library. A `'virtual'` backend emulates a joystick with the keyboard and
mouse. Backends may be selected per device::

    joy = Joystick(0, backend='glfw')

"""

__all__ = [
    'Joystick',
    'JoystickDevice',
    'JoystickResponse',
    'XboxController',
    'JoystickError',
    'JoystickBackendNotAvailableError',
    'JoystickAxisNotAvailableError',
    'JoystickButtonNotAvailableError',
    'InvalidInputNameError',
    'getBackend',
    'setBackend',
    'getJoystickInterfaces',
    'getAllJoysticks',
    'getNumJoysticks',
    'mappings',
    # legacy names, kept so existing code and plugins keep importing
    'BaseJoystickDevice',
    'BaseJoystickInterface',
]

from psychopy import logging
from psychopy.constants import NOT_STARTED
from psychopy.hardware.manager import DeviceManager
from psychopy.hardware.exceptions import (
    DeviceNotConnectedError, ManagedDeviceError)
from psychopy.hardware.joystick._base import (
    JoystickDevice,
    JoystickResponse,
    JoystickError,
    JoystickBackendNotAvailableError,
    JoystickAxisNotAvailableError,
    JoystickButtonNotAvailableError,
    InvalidInputNameError,
    # re-exported for backwards compatibility, these named the same concept
    # before the DeviceManager migration
    BaseJoystickDevice,
    BaseJoystickInterface,
)
# re-exported so `joystick.mappings` keeps working for existing code
import psychopy.hardware.joystick.mappings as mappings
import psychopy.core as core

# Default backend used when a joystick doesn't name one. This stays a plain
# module attribute because assigning to it directly is long-standing public
# usage, e.g. `joystick.backend = 'glfw'`.
backend = 'pyglet'

# constants
JOYSTICK_AXIS_X = JOYSTICK_BUTTON_A = 0
JOYSTICK_AXIS_Y = JOYSTICK_BUTTON_B = 1
JOYSTICK_AXIS_Z = JOYSTICK_BUTTON_X = 2
JOYSTICK_AXIS_RX = JOYSTICK_BUTTON_Y = 3
JOYSTICK_AXIS_RY = 4
JOYSTICK_AXIS_RZ = 5


class Joystick:
    """A joystick or gamepad.

    This wraps a `JoystickDevice` registered with `DeviceManager`, and adds the
    per-experiment state that Builder needs (a status flag, clocks, and the
    data arrays a Routine fills in). Creating one registers the underlying
    device if it isn't registered already, so two Components naming the same
    device share one piece of hardware.

    Parameters
    ----------
    device : str, int, JoystickDevice or None
        The device to use. A `str` names a device in `DeviceManager`, an `int`
        is a legacy device index, and `None` resolves automatically.
    index : int or None
        Legacy device index, used only when `device` is `None`. This is what
        Builder's deprecated "device number" param feeds in.
    backend : str or None
        Input library to use for this joystick (`'pyglet'`, `'glfw'`,
        `'virtual'`). `None` uses the module-level default.
    win : psychopy.visual.Window or None
        Window used to work out the scaling applied to `getX`/`getY` when the
        window is in `'height'` units.
    deviceName : str or None
        Name to register the device under. Defaults to a name derived from the
        backend and index, so repeated calls reuse one device.
    fallback : bool or None
        Whether to fall back to the emulated keyboard-and-mouse joystick when no
        physical device can be found. `None` (the default) means fall back only
        on the legacy index path -- an experiment which names a device gets an
        error instead, so a missing gamepad can't silently become keyboard data.

    Notes
    -----
    * The `'pyglet'` backend needs an open pyglet window which is being flipped
      in order for the joystick state to update.
    * The `'glfw'` backend can be used without a window, and alongside a window
      created by any other library.

    """
    def __init__(self, device=None, index=None, backend=None, win=None,
                 deviceName=None, fallback=None, **kwargs):
        self.device = self._resolveDevice(
            device, index, backend, deviceName, fallback, kwargs)
        # deprecated alias, some code reached into `joy._joy`
        self._joy = self.device

        # scaling applied by `getX`/`getY` so a joystick maps onto a window in
        # 'height' units
        self.xFactor = self.yFactor = 1.0
        self.setWindow(win)

        # Builder state
        self.status = NOT_STARTED
        self.clock = core.Clock()
        self.joystickClock = core.Clock()
        self.device_number = self.device.deviceIndex
        self.numButtons = self.device.getNumButtons()
        self.activeButtons = list(range(self.numButtons))
        self.oldButtonState = self.device.getAllButtons()[:]
        self.clearData()

    @staticmethod
    def _resolveDevice(device, index, backend, deviceName, fallback, kwargs):
        """Work out which `JoystickDevice` this wrapper should drive."""
        # an already-constructed device
        if isinstance(device, JoystickDevice):
            return device

        # a named device in DeviceManager
        if isinstance(device, str):
            found = DeviceManager.getDevice(device)
            if not isinstance(found, JoystickDevice):
                raise JoystickError(
                    "No joystick named '{}' has been set up. Add it in Device "
                    "Manager, or check the device name for typos.".format(
                        device))
            return Joystick._reuse(found)

        # a legacy integer index, either given as `device` or as `index`
        if isinstance(device, int) and not isinstance(device, bool):
            index = device
        if fallback is None:
            # lenient on the legacy path only
            fallback = True

        wanted = backend or getBackend()
        if deviceName is None:
            deviceName = "joystick_{}_{}".format(
                wanted, index if index is not None else 0)

        # NB: reuse sits inside the `try` so that a registration left behind for
        # a stick which has since been unplugged falls back the same way a fresh
        # open would, rather than raising out of the lenient legacy path
        try:
            # reuse an existing registration under this name
            found = DeviceManager.getDevice(deviceName)
            if isinstance(found, JoystickDevice):
                return Joystick._reuse(found)

            # reuse an already-initialised device at this index. NB: the backend
            # has to match too -- an experiment which asked for one explicitly
            # must not be handed a device from another backend that happens to
            # sit at the same index, or Components bind to the wrong stick
            if index is not None:
                for existing in DeviceManager.getInitialisedDevices(
                        JoystickDevice).values():
                    if (existing.inputLib == wanted
                            and existing.deviceIndex == index):
                        return Joystick._reuse(existing)

            return DeviceManager.addDevice(
                deviceClass="psychopy.hardware.joystick.JoystickDevice",
                deviceName=deviceName,
                device=index, backend=backend, **kwargs)
        # NB: both hardware exceptions derive from BaseException rather than
        # Exception, so they have to be named explicitly or the fallback below
        # would never run
        except (Exception, DeviceNotConnectedError, ManagedDeviceError) as err:
            if not fallback:
                raise
            logging.warning(
                "No joystick or gamepad was found ({}). Falling back to "
                "keyboard and mouse emulation -- hold 'ctrl' + 'alt' and press "
                "a number key to press a joystick button.".format(err))
            return DeviceManager.addDevice(
                deviceClass="psychopy.hardware.joystick.JoystickDevice",
                deviceName=deviceName + "_virtual",
                device=0, backend='virtual')

    @staticmethod
    def _reuse(device):
        """Hand back a device shared with another wrapper, ready for use.

        A `JoystickDevice` outlives the wrappers around it -- it stays
        registered with `DeviceManager` once any wrapper has closed it -- so
        reopen it here. Without this, a second `Joystick(...)` gets the closed
        device back and `poll()` silently returns no input.

        """
        if not device.isOpen:
            device.open()
        return device

    def setWindow(self, win):
        """Set the window used to scale `getX`/`getY` in 'height' units."""
        self.win = win
        if win is not None and getattr(win, 'units', None) == 'height':
            self.xFactor = 0.5 * win.size[0] / win.size[1]
            self.yFactor = 0.5
        else:
            self.xFactor = self.yFactor = 1.0

    def clearData(self):
        """Clear the per-Routine data arrays Builder fills in."""
        # NB: written through `__dict__` because `XboxController` repurposes the
        # names `x` and `y` as read-only properties for its X and Y buttons, so
        # a plain assignment raises and makes that subclass impossible to
        # construct. Builder only ever drives the base class, where the two
        # forms are equivalent
        self.__dict__['x'] = []
        self.__dict__['y'] = []
        self.time = []
        self.buttons = []
        self.pressedButtons = []
        self.releasedButtons = []
        self.newPressedButtons = []
        self.buttonLogs = [[] for _ in range(self.numButtons)]

    def __getattr__(self, name):
        """Forward anything we don't define ourselves to the device."""
        # NB: guard against recursion before `device` has been assigned
        if name in ("device", "_joy"):
            raise AttributeError(name)
        device = self.__dict__.get("device", None)
        if device is None:
            raise AttributeError(name)
        return getattr(device, name)

    # --------------------------------------------------------------------------
    # Discovery
    #

    @staticmethod
    def getAvailableDevices():
        """Return a list of available joystick devices.

        Returns
        -------
        list of dict
            Device profiles. These carry the `'index'` and `'name'` keys this
            method has always returned, in addition to the `'deviceName'` and
            `'deviceClass'` keys `DeviceManager` uses.

        """
        profiles = []
        for profile in JoystickDevice.getAvailableDevices():
            profile = profile.copy()
            # legacy keys, kept at the legacy entry points only -- 'index' is
            # not a valid constructor argument, so it can't live in a profile
            # that DeviceManager will splat into `addDevice`
            profile['index'] = profile.get('device', None)
            profile['name'] = profile.get('deviceName', None)
            profiles.append(profile)

        return profiles

    @staticmethod
    def getNumJoysticks():
        """Return the number of available joystick devices (`int`)."""
        return len(Joystick.getAvailableDevices())

    # --------------------------------------------------------------------------
    # Delegated to the device
    #

    def poll(self):
        """Sample the device and update its state.

        Returns
        -------
        float
            The time at which the device was sampled.

        """
        return self.device.poll()

    def open(self):
        """Open the joystick device."""
        return self.device.open()

    def close(self):
        """Close the joystick device."""
        return self.device.close()

    @property
    def isOpen(self):
        """Whether the joystick device is open (`bool`)."""
        return self.device.isOpen

    @property
    def name(self):
        """Name of the joystick reported by the system (`str`)."""
        return self.device.getName()

    @property
    def deviceIndex(self):
        """The backend's index for this joystick (`int`)."""
        return self.device.deviceIndex

    @property
    def inputLib(self):
        """Name of the input library backing this device (`str`)."""
        return self.device.inputLib

    @property
    def hasTracking(self):
        """Whether the device reports position and orientation (`bool`)."""
        return self.device.hasTracking

    @property
    def trackerData(self):
        """Raw tracking data, if the device provides any."""
        return self.device.trackerData

    def lastUpdateTime(self):
        """Time at which the device state was last sampled (`float`)."""
        return self.device.lastUpdateTime()

    def isSameDevice(self, other):
        """Whether `other` refers to the same physical device."""
        if isinstance(other, Joystick):
            other = other.device
        return self.device.isSameDevice(other)

    def getName(self):
        """Return the manufacturer-defined name describing the device."""
        return self.device.getName()

    # axes
    def getNumAxes(self):
        """Number of axes on the device (`int`)."""
        return self.device.getNumAxes()

    def getAllAxes(self):
        """All current axis values, with scaling and deadzone applied."""
        return self.device.getAllAxes()

    def getAxis(self, axisId):
        """Get the value of an axis, by index or name."""
        return self.device.getAxis(axisId)

    def getX(self):
        """Return the X axis value, scaled to the window units."""
        return self.xFactor * self.device.getX()

    def getY(self):
        """Return the Y axis value, scaled to the window units."""
        return self.yFactor * self.device.getY()

    def getXY(self):
        """Return the X and Y axis values, scaled to the window units."""
        return [self.getX(), self.getY()]

    def getZ(self):
        """Return the Z axis value."""
        return self.device.getZ()

    def getRX(self):
        """Return the RX axis value."""
        return self.device.getRX()

    def getRY(self):
        """Return the RY axis value."""
        return self.device.getRY()

    def getRZ(self):
        """Return the RZ axis value."""
        return self.device.getRZ()

    def getAxisScale(self, axisId=None):
        """Get the scale factor applied to an axis."""
        return self.device.getAxisScale(axisId)

    def setAxisScale(self, axisId, scale):
        """Set the scale factor applied to an axis."""
        return self.device.setAxisScale(axisId, scale)

    def getAxisDeadzone(self, axisId=None):
        """Get the deadzone applied to an axis."""
        return self.device.getAxisDeadzone(axisId)

    def setAxisDeadzone(self, axisId=None, deadzone=0.1):
        """Set the deadzone applied to an axis."""
        return self.device.setAxisDeadzone(axisId, deadzone)

    # buttons
    def getNumButtons(self):
        """Number of buttons on the device (`int`)."""
        return self.device.getNumButtons()

    def getAllButtons(self):
        """State of every button, as a list of `bool`."""
        return self.device.getAllButtons()

    def getButton(self, buttonId):
        """Get the state of a button, by index or name."""
        return self.device.getButton(buttonId)

    # hats
    def getNumHats(self):
        """Number of hats on the device (`int`)."""
        return self.device.getNumHats()

    def getAllHats(self):
        """Position of every hat, as a list of (x, y) tuples."""
        return self.device.getAllHats()

    def getHat(self, hatId=0):
        """Get the position of a hat, by index or name."""
        return self.device.getHat(hatId)

    # naming
    def setInputScheme(self, mapping):
        """Apply a named input scheme to this device."""
        return self.device.setInputScheme(mapping)

    def setInputName(self, inputType, inputIndex, name):
        """Give an input a name, so it can be addressed by that name."""
        return self.device.setInputName(inputType, inputIndex, name)

    # events and responses
    def setEventCallback(self, evt, callback):
        """Set a callback to be invoked when a joystick event occurs."""
        return self.device.setEventCallback(evt, callback)

    def dispatchMessages(self):
        """Sample the device and emit a response for anything which changed."""
        return self.device.dispatchMessages()

    def getResponses(self, state=None, channel=None, inputType=None,
                     clear=True):
        """Get responses matching the given criteria."""
        return self.device.getResponses(
            state=state, channel=channel, inputType=inputType, clear=clear)

    def getState(self, channel, inputType="button"):
        """Get the current state of a single input."""
        return self.device.getState(channel, inputType=inputType)

    def clearResponses(self):
        """Clear the response queue."""
        return self.device.clearResponses()

    def addListener(self, listener, startLoop=False):
        """Attach a listener to the underlying device."""
        return self.device.addListener(listener, startLoop=startLoop)

    def clearListeners(self):
        """Remove every listener from the underlying device."""
        return self.device.clearListeners()

    def resetTimer(self, clock=None):
        """Reset the clock used to timestamp responses."""
        return self.device.resetTimer(clock)


class XboxController(Joystick):
    """Joystick template class for the XBox 360 controller.

    Usage:

        xbctrl = XboxController(0)  # joystick ID
        y_btn_state = xbctrl.y  # get the state of the 'Y' button

    """
    def __init__(self, deviceIndex=None, **kwargs):
        deviceIndex = kwargs.pop('id', deviceIndex)  # legacy param
        super(XboxController, self).__init__(deviceIndex, **kwargs)

        # validate if this is an Xbox controller by its reported name
        if self.name.find("Xbox 360") == -1:
            logging.warning("The connected controller does not appear "
                            "compatible with the 'XboxController' template. "
                            "Unexpected input behaviour may result!")

        # button mapping for the XBox controller
        self._button_mapping = {'a': 0,
                                'b': 1,
                                'x': 2,
                                'y': 3,
                                'left_shoulder': 4,
                                'right_shoulder': 5,
                                'back': 6,
                                'start': 7,
                                'left_stick': 8,
                                'right_stick': 9,
                                'up': 10,  # hat
                                'down': 11,
                                'left': 12,
                                'right': 13}

        # axes groups
        self._axes_mapping = {'left_thumbstick': (0, 1),
                              'right_thumbstick': (2, 3),
                              'triggers': (4, 5),
                              'dpad': (6, 7)}

    @property
    def a(self):
        return self.get_a()

    def get_a(self):
        """Get the 'A' button state.

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['a'])

    @property
    def b(self):
        return self.get_b()

    def get_b(self):
        """Get the 'B' button state.

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['b'])

    @property
    def x(self):
        return self.get_x()

    def get_x(self):
        """Get the 'X' button state.

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['x'])

    @property
    def y(self):
        return self.get_y()

    def get_y(self):
        """Get the 'Y' button state.

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['y'])

    @property
    def left_shoulder(self):
        return self.get_left_shoulder()

    def get_left_shoulder(self):
        """Get left 'shoulder' trigger state.

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['left_shoulder'])

    @property
    def right_shoulder(self):
        return self.get_right_shoulder()

    def get_right_shoulder(self):
        """Get right 'shoulder' trigger state.

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['right_shoulder'])

    @property
    def back(self):
        return self.get_back()

    def get_back(self):
        """Get 'back' button state (button to the right of the left joystick).

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['back'])

    @property
    def start(self):
        return self.get_start()

    def get_start(self):
        """Get 'start' button state (button to the left of the 'X' button).

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['start'])

    @property
    def hat_axis(self):
        return self.get_hat_axis()

    def get_hat_axis(self):
        """Get the states of the hat (sometimes called the 'directional pad').
        The hat can only indicate direction but not displacement.

        This function reports hat values in the same way as a joystick so it may
        be used interchangeably with existing analog joystick code.

        Returns a tuple (X,Y) indicating which direction the hat is pressed
        between -1.0 and +1.0. Positive values indicate presses in the right or
        up direction.

        :return: tuple, zero centered X, Y values.
        """
        # get button states
        button_states = self.getAllButtons()
        up = button_states[self._button_mapping['up']]
        dn = button_states[self._button_mapping['down']]
        lf = button_states[self._button_mapping['left']]
        rt = button_states[self._button_mapping['right']]

        # convert button states to 'analog' values
        return -1.0 * lf + rt, -1.0 * dn + up

    @property
    def left_thumbstick(self):
        return self.get_left_thumbstick()

    def get_left_thumbstick(self):
        """Get the state of the left joystick button; activated by pressing
        down on the stick.

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['left_stick'])

    @property
    def right_thumbstick(self):
        return self.get_right_thumbstick()

    def get_right_thumbstick(self):
        """Get the state of the right joystick button; activated by pressing
        down on the stick.

        :return: bool, True if pressed down
        """
        return self.getButton(self._button_mapping['right_stick'])

    def get_named_buttons(self, button_names):
        """Get the states of multiple buttons using names. A list of button
        states is returned for each string in list 'names'.

        :param button_names: tuple or list of button names
        :return:
        """

        button_states = []
        for button in button_names:
            button_states.append(self.getButton(self._button_mapping[button]))

        return button_states

    @property
    def left_thumbstick_axis(self):
        return self.get_left_thumbstick_axis()

    def get_left_thumbstick_axis(self):
        """Get the axis displacement values of the left thumbstick.

        Returns a tuple (X,Y) indicating thumbstick displacement between -1.0
        and +1.0. Positive values indicate the stick is displaced right or up.

        :return: tuple, zero centered X, Y values.
        """
        ax, ay = self._axes_mapping['left_thumbstick']

        # we sometimes get values slightly outside the range of -1.0 < x < 1.0,
        # so clip them to give the user what they expect
        ax_val = self._clip_range(self.getAxis(ax))
        ay_val = self._clip_range(self.getAxis(ay))

        return ax_val, ay_val

    @property
    def right_thumbstick_axis(self):
        return self.get_right_thumbstick_axis()

    def get_right_thumbstick_axis(self):
        """Get the axis displacement values of the right thumbstick.

        Returns a tuple (X,Y) indicating thumbstick displacement between -1.0
        and +1.0. Positive values indicate the stick is displaced right or up.

        :return: tuple, zero centered X, Y values.
        """
        ax, ay = self._axes_mapping['right_thumbstick']

        ax_val = self._clip_range(self.getAxis(ax))
        ay_val = self._clip_range(self.getAxis(ay))

        return ax_val, ay_val

    @property
    def trigger_axis(self):
        return self.get_trigger_axis()

    def get_trigger_axis(self):
        """Get the axis displacement values of both index triggers.

        Returns a tuple (L,R) indicating index trigger displacement between -1.0
        and +1.0. Values increase from -1.0 to 1.0 the further a trigger is
        pushed.

        :return: tuple, zero centered L, R values.
        """
        al, ar = self._axes_mapping['triggers']

        al_val = self._clip_range(self.getAxis(al))
        ar_val = self._clip_range(self.getAxis(ar))

        return al_val, ar_val

    def _clip_range(self, val):
        """Clip the range of a value between -1.0 and +1.0. Needed for joystick
        axes.

        :param val:
        :return:
        """
        if -1.0 > val:
            val = -1.0

        if val > 1.0:
            val = 1.0

        return val


# Setter and getter methods for the joystick backend, this allows us to sanity
# check the backend value before setting it.

def getBackend():
    """Get the joystick backend in use.

    Returns
    -------
    str
        The name of the joystick backend in use.

    """
    return backend


def setBackend(inputLib):
    """Set the joystick backend (input library) to use.

    Successive instances of `Joystick` will use the backend set here unless they
    name one of their own. If the backend is not available, a
    `JoystickBackendNotAvailableError` is raised.

    Parameters
    ----------
    inputLib : str or None
        The name of the joystick input library to use. If None, the value will
        be set to match the window backend name. You cannot set the backend to
        None if there are no open windows.

    Examples
    --------
    Set the joystick backend to 'glfw'::

        joystick.setBackend('glfw')
        joy = joystick.Joystick(0)  # uses the GLFW backend

        joy.inputLib == 'glfw'  # True

    Use the window backend as the joystick backend::

        win = visual.Window([400, 400], winType='pyglet')  # create first!
        joystick.setBackend(None)  # set to window backend
        print(joystick.getBackend())  # 'pyglet'

    """
    if inputLib is None:
        # imported here rather than at module scope -- `psychopy.visual` imports
        # `psychopy.hardware`, so a top-level import risks a cycle
        from psychopy import visual
        if not visual.openWindows:
            raise ValueError("Cannot determine the window backend.")

        win = visual.openWindows[0]()
        inputLib = win.backend.winTypeName  # get window backend name

    # check the backend is known and can actually be imported
    if inputLib not in JoystickDevice.backends:
        raise JoystickBackendNotAvailableError(
            "Joystick backend '{}' is not available, known backends are: "
            "{}".format(inputLib, list(JoystickDevice.backends)))

    JoystickDevice.resolveBackend(inputLib, allowFallback=False)

    global backend  # set the global backend
    backend = inputLib
    # clear any class-level override so the global reliably wins from here on
    JoystickDevice.backend = None


def getJoystickInterfaces():
    """Get available joystick input interfaces.

    Returns
    -------
    dict
        A mapping of joystick interfaces available where the key is the input
        library identifier and the value is the joystick interface class.
        Setting the backend to one of these keys will use the corresponding
        joystick interface.

    """
    found = {}
    for name in list(JoystickDevice.backends):
        try:
            found[name] = JoystickDevice.resolveBackend(
                name, allowFallback=False)
        except (JoystickBackendNotAvailableError, ImportError):
            continue

    return found


def getAllJoysticks():
    """Enumerate all available joysticks and return a list of their information.

    Uses the presently set joystick backend to get the available joysticks.

    Returns
    -------
    list
        A list of dictionaries containing information about each available
        joystick. Information varies depending on the joystick interface used,
        however the `'index'` key is always present and contains the index of
        the joystick. Passing this index to the `Joystick` constructor will
        create a joystick object for that device.

    Examples
    --------
    Get information about all available joysticks::

        joysticks = getAllJoysticks()
        for joy in joysticks:
            print(joy)

    Create a `Joystick` object for the first joystick found::

        joy = Joystick(joysticks[0]['index'])

    """
    return Joystick.getAvailableDevices()


def getNumJoysticks():
    """Return the number of available joysticks.

    Uses the presently set joystick backend to get the available joysticks.

    Returns
    -------
    int
        The number of available joysticks.

    """
    return Joystick.getNumJoysticks()


if __name__ == "__main__":
    pass
