#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Control joysticks and gamepads from within PsychoPy.

For most backends, you do need a window using the same backend (and you need to 
be flipping it) for the joystick to be updated.

"""

__all__ = [
    'Joystick', 
    'JoystickError',
    'JoystickAxisNotAvailableError',
    'JoysticButtonNotAvailableError',
    'getJoystickInterfaces']

from psychopy import logging, visual
from psychopy.hardware.joystick._base import BaseJoystickInterface
from psychopy.hardware.joystick.backend_pyglet import JoystickInterfacePyglet
from psychopy.hardware.joystick.backend_glfw import JoystickInterfaceGLFW
import psychopy.hardware.joystick.mappings as mappings
import psychopy.core as core

import math
import numpy as np

# backend to use when creating joystick objects
backend = 'pyglet'  # 'pyglet' or 'pygame'

# constants
JOYSTICK_AXIS_X = JOYSTICK_BUTTON_A = 0
JOYSTICK_AXIS_Y = JOYSTICK_BUTTON_B = 1
JOYSTICK_AXIS_Z = JOYSTICK_BUTTON_X = 2
JOYSTICK_AXIS_RX = JOYSTICK_BUTTON_Y = 3
JOYSTICK_AXIS_RY = 4
JOYSTICK_AXIS_RZ = 5


class JoystickError(Exception):
    """Exception raised for errors in the joystick module.
    """
    pass


class JoystickBackendNotAvailableError(JoystickError):
    """Exception raised when the backend is not available.
    """
    pass


class JoystickAxisNotAvailableError(JoystickError):
    """Exception raised when an axis is not available on the joystick.
    """
    pass


class InvalidInputNameError(JoystickError):
    """Exception raised when an input name is not valid.
    """
    pass


class JoysticButtonNotAvailableError(JoystickError):
    """Exception raised when a button is not available on the joystick.
    """
    pass


class Joystick:
    """Class for interfacing with a multi-axis joystick or gamepad.

    Upon creating a `Joystick` object, the joystick device is opened and the 
    states of the device's axes and buttons can be read.

    Values for the axes are returned as floating point numbers, typically
    between -1.0 and +1.0 unless scaling is applied. The values for the buttons
    are returned as booleans, where True indicates the button is pressed down
    at the time the device was last polled.

    Scaling factors can be set for each axis to adjust the range of the axis
    values. The scaling factor is a floating point value that is multiplied by
    the axis value. If the scaling factor is negative, the axis value is
    inverted. Deadzones can also be applied for each axis to prevent small 
    fluctuations in the joystick's resting position from being interpreted as 
    valid input. The deadzone is a floating point value between 0.0 and 1.0. If 
    the absolute value of the axis value is less than the deadzone, the axis 
    value is set to zero.

    Device inputs can be named to provide a more human-readable interface. The 
    names can be set for axes, buttons, and hats where they can be used to get 
    the input values instead of using the integer indices. Furthermore,
    like inputs can be grouped together under a single name. For example, both
    X and Y of a thumbstick can be grouped together under the name 'thumbstick'.
    When getting the value of the thumbstick, a tuple of the X and Y values is
    returned instead of having to get each axis individually.

    Parameters
    ----------
    device : int or str
        The index or name of the joystick to control.

    Examples
    --------
    Typical usage::

        from psychopy.hardware import joystick
        from psychopy import visual

        joystick.backend='pyglet'  # must match the Window
        win = visual.Window([400,400], winType='pyglet')

        nJoys = joystick.getNumJoysticks()  # to check if we have any
        id = 0
        joy = joystick.Joystick(id)  # id must be <= nJoys - 1

        nAxes = joy.getNumAxes()  # for interest
        while True:  # while presenting stimuli
            joyX = joy.getX()
            # ...
            win.flip()  # flipping implicitly updates the joystick info
    
    Set the deadzone for axis 0 to 0.1::

        joy.setAxisDeadzone(0, 0.1)

    Set the scaling factor for 1 axis to 2.0::

        joy.setAxisScale(1, 2.0)

    Setting the names of the inputs can be useful for debugging and for
    providing a more human-readable interface::

        joy.setInputName('axis', 0, 'x')
        joy.setInputName('axis', 1, 'y')

    You can get the imput value by name by passing it to the get method for the
    input type::

        joy.getAxis('axis', 'x')  # instead of joy.getAxis(0)

    Automatically set the input names to the default Xbox controller mapping
    scheme::

        joy.setInputScheme('xbox')
        # ...
        xVal, yVal = joy.getAxis('left_thumbstick')
        leftTrigger, rightTrigger = joy.getAxis('triggers')

    Notes
    -----
    * You do need to be flipping frames (or dispatching events manually) in 
      order for the values of the joystick to be updated.
    * Currently under pyglet backends the axis values initialise to zero
      rather than reading the current true value. This gets fixed on the first 
      change to each axis.
    * Currently pygame (1.9.1) spits out lots of debug messages about the
      joystick and these can't be turned off :-/
    * The GLFW backend can be used without first opening a window and can be 
      used with other window backends.

    """
    def __init__(self, device=0, **kwargs):
        # get the joystick device interface
        try:
            joyInterface = getJoystickInterfaces()[backend]
            logging.info(
                "Using joystick interface '{}' for backend '{}'".format(
                    joyInterface.__name__, backend))
        except KeyError:
            logging.error(
                "No joystick interface found for backend '{}'".format(
                    backend))

        # create a device interface
        self._joy = joyInterface(device, **kwargs)

        # input counts for the device, these don't chnage after opening
        self._numAxes = self._joy.getNumAxes()
        self._numButtons = self._joy.getNumButtons()
        self._numHats = self._joy.getNumHats()

        # axis value modifiers
        self._axisScale = [1.0] * self._numAxes
        self._axisDeadzone = [0.0] * self._numAxes

        # device states
        self._lastUpdateTime = 0.0  # in experiment time
        self._axisVals = np.zeros(self._numAxes, dtype=np.float32)
        self._btnStates = np.zeros(self._numButtons, dtype=bool)
        self._hatStates = np.zeros((self._numHats, 2), dtype=np.int8)

        # VR and motion tracking properties
        self._pos = np.zeros(3, dtype=np.float32)
        self._ori = np.array([0., 0., 0., 1.], dtype=np.float32)
        self._angularVel = np.zeros(3, dtype=np.float32)
        self._linearVel = np.zeros(3, dtype=np.float32)

        # axis name mapping, some defaults are provided for common axes
        self._inputNames = {}
        self.setInputScheme('default')  # use default mapping scheme

    def __del__(self):
        """Close the joystick device when the object is deleted.
        """
        if hasattr(self, '_joy'):
            self.close()

    def lastUpdateTime(self):
        """Return the time of the last update to the joystick state.

        Returns
        -------
        float
            The time of the last update to the joystick state.

        """
        return self._lastUpdateTime

    def poll(self):
        """Poll the joystick device for the current state.

        This method should be called at the beginning of each frame to update
        the state of the joystick device. The time of the last update is stored
        and can be accessed using the `lastUpdateTime` property.

        """
        self._joy.update()

        # update the internal state of the joystick
        self._axisVals[:] = self.getAllAxes()
        self._btnStates[:] = self.getAllButtons()

        if backend != 'glfw':  # cannot use hats with GLFW
            self._hatStates[:] = self.getAllHats()

        # update the VR properties
        if self.hasTracking:
            self._pos = self.getPos()
            self._ori = self.getOri()
            self._angularVel = self.getAngularVelocity()
            self._linearVel = self.getLinearVelocity()

        if self._joy.trackerData is None:
            self._lastUpdateTime = core.getTime()
        else:
            self._lastUpdateTime = self._joy.trackerData._absSampleTime

        return self._lastUpdateTime
        
    @staticmethod
    def getAvailableDevices():
        """Return a list of available joystick devices.

        This method is used by `DeviceManager` to get a list of available
        devices.

        Returns
        -------
        list
            A list of available joystick devices.

        """
        # use the selected backend class to get the available devices
        return getJoystickInterfaces()[backend].getAvailableDevices()

    @property
    def inputLib(self):
        """Input interface library used (`str`).
        """
        if not hasattr(self, '_joy'):
            return None
            
        return self._joy.inputLib

    @property
    def hasTracking(self):
        """Check if the joystick has tracking capabilities.

        Returns
        -------
        bool
            True if the joystick has tracking capabilities, False otherwise.

        """
        return self._joy.hasTracking

    def isSameDevice(self, otherDevice):
        """Check if the device is the same as another device.

        Parameters
        ----------
        otherDevice : Joystick
            The other device to compare against.

        Returns
        -------
        bool
            True if the devices are the same, False otherwise.

        """
        # only need to check the index since the device ID is unique
        return self._joy.isSameDevice(otherDevice._device)

    def open(self):
        """Open the joystick device.
        """
        if self.isOpen:
            return

        self._joy.open()

    @property
    def isOpen(self):
        """Check if the joystick device is open.

        Returns
        -------
        bool
            True if the joystick device is open, False otherwise.

        """
        return self._joy.isOpen

    def close(self):
        """Close the joystick device.
        """
        if not self.isOpen:
            return

        self._joy.close()

    @property
    def name(self):
        """Name of the joystick reported by the system (`str`).
        """
        return self.getName()
    
    @property
    def deviceIndex(self):
        """The index of the joystick (`int`).
        """
        return self._deviceIndex

    @property
    def x(self):
        """The X axis value (`float`).
        """
        return self.getX()

    @property
    def y(self):
        """The Y axis value (`float`).
        """
        return self.getY()

    @property
    def z(self):
        """The Z axis value (`float`).
        """
        return self.getZ()

    @property
    def rx(self):
        """The RX axis value (`float`).
        """
        return self.getRX()

    @property
    def ry(self):
        """The RY axis value (`float`).
        """
        return self.getRY()

    @property
    def rz(self):
        """The RZ axis value (`float`).
        """
        return self.getRZ()
    
    @property
    def trackerData(self):
        """Tracker data for the controller.

        Returns
        -------
        `TrackerData` or `None`
            The tracker data.

        """
        return self._joy.trackerData

    def getName(self):
        """Return the manufacturer-defined name describing the device (`str`).
        """
        return self._joy.getName()

    def setInputScheme(self, mapping):
        """Set the input mapping scheme for the joystick.

        The input mapping scheme determines the names of the inputs for the
        joystick. The mapping scheme can be set to 'default', 'xbox', or
        'custom'. The default mapping scheme provides names for the axes and
        buttons that are common to most joysticks.

        Note that setting the mapping scheme will overwrite any custom input
        names that have been set prior to calling this method.

        Parameters
        ----------
        mapping : str
            The mapping scheme to set. Must be one of 'default', 'xbox', or
            'custom'.

        """
        # get the mapping scheme
        inputMap = mappings.getInputScheme(mapping, self.inputLib)
        if inputMap is None:
            raise ValueError("Invalid mapping scheme '{}'.".format(mapping))

        logging.info(
            "Setting input scheme for joystick to '{}'.".format(mapping))

        # set the input names
        self._inputNames = inputMap
    
    def setInputName(self, inputType, inputIndex, name):
        """Set the name of an input.

        Parameters
        ----------
        inputType : str
            The type of input to set the name for. Must be one of 'axis',
            'button', or 'hat'.
        inputIndex : int or list of int
            The index of the input to set the name for. If a list of indices is
            supplied, multiple axes will be grouped together.
        name : str or None
            The name to set for the axis. If None, the name for the axis is
            removed.

        Raises
        ------
        ValueError
            If the inputType is not 'axis', 'button', or 'hat'.
        
        Examples
        --------
        Set the name of axis `0` to 'x' and get its value by name::

            joy.setInputName('axis', 0, 'x')
            xVal = joy.getAxis('x')  # instead of joy.getAxis(0)

        Joystick inputs often have multiple axes ganged together on a single
        control, such as a thumbstick. You can group axes together by passing a 
        list of indices::

            joy.setInputName('axis', [0, 1], 'left_thumbstick')
            xVal, yVal = joy.getAxis('left_thumbstick')  # returns 2 values

        """
        if inputType not in ('axes', 'buttons', 'hats'):
            raise ValueError("Input type must be 'axes', 'buttons', or 'hats'.")

        if name is None:
            if inputIndex in self._inputNames[inputType]:
                del self._inputNames[inputType][inputIndex]
            return

        self._inputNames[inputType][inputIndex] = name

    def _getIndexFromName(self, inputType, name):
        """Get the index of an input from its name.

        Parameters
        ----------
        inputType : str
            The type of input to get the index for. Must be one of 'axis',
            'button', or 'hat'.
        name : str
            The name of the input to get the index for.

        Returns
        -------
        int or None
            The index of the input. If the input name is not found, `None` is
            returned.

        Raises
        ------
        InvalidInputNameError
            If the input name is not valid or has not been set.
        
        """
        inputIndex = self._inputNames[inputType].get(name, None)
        if inputIndex is not None:
            return inputIndex

        raise InvalidInputNameError("Input name '{}' is not valid.".format(name))

    # --------------------------------------------------------------------------
    # Axis filtering methods
    #

    def getAxisScale(self, axisId):
        """Get the scale factor for a given axis.

        Parameters
        ----------
        axisId : int
            The axis ID to get the scale factor for.

        Returns
        -------
        float
            The scale factor for the given axis.

        """
        return self._axisScale[axisId]

    def setAxisScale(self, axisId, scale):
        """Set the scale factor for a given axis.

        Parameters
        ----------
        axisId : int or None
            The axis ID to set the scale factor for. If None, set the scale
            factor for all axes to the given value.
        scale : float
            The scale factor to set. This factor will be multiplied by the
            axis value. If negative, the axis value will be inverted.

        """
        if not isinstance(scale, (int, float)):
            raise TypeError("Scaling factor must be a numeric type.")

        if isinstance(axisId, str):
            axisId = self._getIndexFromName('axes', axisId)

        if axisId is None:
            self._axisScale = [scale] * len(self._axisScale)
        else:
            self._axisScale[axisId] = scale
        
    def getAxisDeadzone(self, axisId):
        """Get the deadzone for a given axis.

        Parameters
        ----------
        axisId : int
            The axis ID to get the deadzone for.

        Returns
        -------
        float
            The deadzone for the given axis.

        """
        if axisId is None:
            return self._axisDeadzone

        if isinstance(axisId, str):
            axisId = self._getIndexFromName('axes', axisId)

        if isinstance(axisId, (list, tuple)):
            return [self.getAxisDeadzone(ax) for ax in axisId]

        return self._axisDeadzone[axisId]

    def setAxisDeadzone(self, axisId=None, deadzone=0.1):
        """Set the deadzone for a given axis.

        Parameters
        ----------
        axisId : int, str, list or None
            The axis ID to set the deadzone for. If None, set the deadzone for
            all axes to the given value. A string can be supplied to set the
            deadzone for an axis by name. A list of axes can also be supplied to
            set the deadzone for multiple axes at once.
        deadzone : float
            The deadzone to set, must be between 0.0 and 1.0.

        """
        if not isinstance(deadzone, (int, float)):
            raise TypeError("Deadzone must be a numeric type.")

        deadzone = min(1.0, max(0.0, deadzone))
        if axisId is None:
            self._axisDeadzone = [deadzone] * len(self._axisDeadzone)
            return

        if isinstance(axisId, str):  # name supplied
            axisId = self._getIndexFromName('axes', axisId)

        if isinstance(axisId, (list, tuple)):
            for ax in axisId:
                self.setAxisDeadzone(ax, deadzone)
            return

        self._axisDeadzone[axisId] = deadzone

    # --------------------------------------------------------------------------
    # Axis methods
    #

    def getAllAxes(self):
        """Get a list of all current axis values (`int`).
        """
        allAxes = self._joy.getAllAxes()

        # apply scaling and deadzone to axes
        for i, axisVal in enumerate(allAxes):
            allAxes[i] = axisVal * self._axisScale[i] \
                if abs(axisVal) >= self._axisDeadzone[i] else 0.0

        return allAxes

    def getNumAxes(self):
        """Get the number of available joystick axes.

        The first axis usually corresponds to the X axis, the second to the Y
        axis for most joysticks. Additional axes may be present for other 
        controls such as addtional thumbsticks or throttle lever.

        Returns
        -------
        int
            The number of axes found on the joystick.

        """
        return self._numAxes

    def getAxis(self, axisId):
        """Get the value of an axis by an integer id.

        Parameters
        ----------
        axisId : int, str or list
            The axis ID to get the value for. If a string is supplied, the name
            of the axis is used to get the value. If a list of axes indices or
            names is supplied, a list of values is returned.

        Returns
        -------
        float or list
            The value of the axis. If a list of axes is supplied, a list of
            values is returned.

        """
        if isinstance(axisId, str):  # name supplied
            axisId = self._getIndexFromName('axes', axisId)

        # is axisId a sequence?
        if isinstance(axisId, (list, tuple)):
            return [self.getAxis(ax) for ax in axisId]  # recusively called

        # get the axis value from `int` axisId
        axisVal = self._joy.getAxis(axisId)
        return axisVal * self._axisScale[axisId] \
            if abs(axisVal) >= self._axisDeadzone[axisId] else 0.0

    def getX(self):
        """Return the X axis value (equivalent to joystick.getAxis(0))."""
        return self.getAxis(JOYSTICK_AXIS_X)

    def getY(self):
        """Return the Y axis value (equivalent to joystick.getAxis(1))."""
        return self.getAxis(JOYSTICK_AXIS_Y)
    
    def getXY(self):
        """Return the X and Y axis values as a tuple.

        Returns
        -------
        tuple
            The X and Y axis values as a tuple.

        """
        return self.getAxis([JOYSTICK_AXIS_X, JOYSTICK_AXIS_Y])

    def getZ(self):
        """Return the Z axis value (equivalent to joystick.getAxis(2))."""
        return self.getAxis(JOYSTICK_AXIS_Z)

    def getRX(self):
        """Return the RX axis value (equivalent to joystick.getAxis(3))."""
        return self.getAxis(JOYSTICK_AXIS_RX)

    def getRY(self):
        """Return the RY axis value (equivalent to joystick.getAxis(4))."""
        return self.getAxis(JOYSTICK_AXIS_RY)

    def getRZ(self):
        """Return the RZ axis value (equivalent to joystick.getAxis(5))."""
        return self.getAxis(JOYSTICK_AXIS_RZ)

    # --------------------------------------------------------------------------
    # Button methods
    #

    def getNumButtons(self):
        """Get the number of buttons on the device (`int`).

        Returns
        -------
        int
            The number of buttons on the joystick.

        """
        return self._numButtons

    def getAllButtons(self):
        """Get the state of all buttons on the devics.

        Returns
        -------
        list
            A list of button states. Each state is a boolean.

        """
        return self._joy.getAllButtons()

    def getButton(self, buttonId):
        """Get the state of a given button on the device (`bool`).

        Parameters
        ----------
        buttonId : int, str or list
            The button ID to get the state for. If a string is supplied, the
            name of the button is used to get the state. If a list of button
            indices or names is supplied, a list of states is returned.

        Returns
        -------
        bool or list
            The state of the button. If a list of buttons was passed as 
            `buttonId`, a list of states is returned where each state is a
            boolean.

        """
        if isinstance(buttonId, str):  # name supplied
            buttonId = self._getIndexFromName('buttons', buttonId)

        if isinstance(buttonId, (list, tuple)):
            return [self.getButton(b) for b in buttonId]

        return self._joy.getButton(buttonId)

    # --------------------------------------------------------------------------
    # Hat methods
    #
    def getNumHats(self):
        """Get the number of hats on this joystick.

        The GLFW backend makes no distinction between hats and buttons. Calling
        'getNumHats()' will return 0.

        """
        return self._numHats

    def getAllHats(self):
        """Get the current values of all available hats.

        Returns
        -------
        list
            Each value is a tuple (x, y) where x and y axis states are trinary
            (-1, 0, +1)

        """
        return self._joy.getAllHats()

    def getHat(self, hatId=0):
        """Get the position of a particular hat.

        Parameters
        ----------
        hatId : int or str
            The hat ID to get the position for. If a string is supplied, the
            name of the hat is used to get the position.

        Returns
        -------
        tuple
            The position returned is an (x, y) tuple where x and y can be -1, 0 
            or +1.

        """
        if isinstance(hatId, str):  # name supplied
            hatId = self._getIndexFromName('hats', hatId)

        if isinstance(hatId, (list, tuple)):
            return [self.getHat(h) for h in hatId]

        return self._joy.getHat(hatId)


class XboxController(Joystick):
    """Joystick template class for the XBox 360 controller.

    Usage:

        xbctrl = XboxController(0)  # joystick ID
        y_btn_state = xbctrl.y  # get the state of the 'Y' button

    """
    def __init__(self, deviceIndex, **kwargs):
        deviceIndex = kwargs.get('id', deviceIndex)  # legacy param
        super(XboxController, self).__init__(deviceIndex)

        # validate if this is an Xbox controller by its reported name
        if self.name.find("Xbox 360") == -1:
            logging.warning("The connected controller does not appear "
                            "compatible with the 'XboxController' template. "
                            "Unexpected input behaviour may result!")

        if backend != 'glfw':
            logging.error("Controller templates are only supported when using "
                          "the GLFW window backend. You must also set "
                          "joystick.backend='glfw' prior to creating a "
                          "joystick.")


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
    
    Successive instances of `Joystick` will use the backend set here. If the
    backend is not available, a `ValueError` is raised.

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
        if not visual.openWindows:
            raise ValueError("Cannot determine the window backend.")
        
        win = visual.openWindows[0]()
        inputLib = win.backend.winTypeName  # get window backend name

    # get available backends and check if the requested backend is available
    availableBackends = getJoystickInterfaces()
    if inputLib not in availableBackends.keys():
        raise JoystickBackendNotAvailableError(
            "Joystick backend '{}' is not available.".format(inputLib))

    global backend  # set the global backend
    backend = inputLib 


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
    foundJoystickInterfaces = {}

    # look for subclasses of JoystickInterface in this module's namespace
    for name in globals():
        obj = globals()[name]
        if isinstance(obj, type) and issubclass(obj, BaseJoystickInterface):
            if obj != BaseJoystickInterface:
                foundJoystickInterfaces[obj._inputLib] = obj

    return foundJoystickInterfaces.copy()


def getAllJoysticks():
    """Enumerate all available joysticks and return a dictionary of their
    information.

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
    return Joystick.getAllJoysticks()


if __name__ == "__main__":
    pass
