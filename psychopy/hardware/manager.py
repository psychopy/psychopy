#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hardware device management.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'deviceManager', 
    'getDeviceManager', 
    'DeviceManager',
    'closeAllDevices'
]


from psychopy.tools import systemtools as st
from serial.tools import list_ports
from psychopy import logging
import atexit
import importlib
import json
from pathlib import Path

__folder__ = Path(__file__).parent


class DeviceManager:
    """Class for managing hardware devices.

    An instance of this class is used to manage various hardware peripherals used by PsychoPy. It
    can be used to access devices such as microphones, button boxes, and cameras though a common
    interface. It can also be used to get information about available devices installed on the
    system, such as their settings and capabilities prior to initializing them.
    
    It is recommended that devices are initialized through the device manager rather than
    directly. The device manager is responsible for keeping track of devices and ensuring that
    they are properly closed when the program exits.

    This class is implemented as a singleton, so there is only one instance of it per ssession
    after its initialized. The instance can be accessed through the global variable
    `deviceManager` or by calling `getDeviceManager()`.

    Any subclass of BaseDevice is added to DeviceManager's `.deviceClasses` list upon import,
    so devices matching that class become available through `DeviceManager.getAvailableDevices(
    "*")`.

    """
    _instance = None  # singleton instance
    deviceClasses = []  # subclasses of BaseDevice which we know about
    liaison = None
    ioServer = None  # reference to currently running ioHub ioServer object
    devices = {}  # devices stored
    aliases = {}  # aliases to get device classes by

    with (__folder__ / "knownDevices.json").open("rb") as f:
        knownDevices = json.load(f)  # dict of known device classes

    def __new__(cls, liaison=None):
        # when making a new DeviceManager, if an instance already exists, just return it
        # this means that all DeviceManager handles are the same object
        if cls._instance is None:
            cls._instance = super(DeviceManager, cls).__new__(cls)

        return cls._instance

    def __init__(self, liaison=None):
        # set liaison
        if liaison is not None:
            DeviceManager.liaison = liaison

        # make sure we have at least one response device
        if "defaultKeyboard" not in self.devices:
            self.addDevice(
                deviceClass="psychopy.hardware.keyboard.KeyboardDevice",
                deviceName="defaultKeyboard"
            )

    # --- utility ---

    def _getSerialPortsInUse(self):
        """Get serial ports that are being used and the names of the devices that are using them.

        This will only work if the devices have a `portString` attribute, which
        requires they inherit from `SerialDevice`.

        Returns
        -------
        dict
            Mapping of serial port names to the names of the devices that are
            using them as a list.

        """
        ports = {}
        for devClass in DeviceManager._devices:
            for devName, devObj in DeviceManager._devices[devClass].items():
                if hasattr(devObj, 'portString'):
                    ports.setdefault(devObj.portString, []).append(devName)

        return ports

    @staticmethod
    def registerClassAlias(alias, deviceClass):
        """
        Register an alias to rever to a particular class, for convenience.

        Parameters
        ----------
        alias : str
            Short, convenient string to refer to the class by. For example, "keyboard".
        deviceClass : str
            Full import path for the class, in PsychoPy, of the device. For example
            `psychopy.hardware.keyboard.Keyboard`
        """
        # if device class is an already registered alias, get the actual class str
        deviceClass = DeviceManager._resolveAlias(deviceClass)
        # register alias
        DeviceManager.aliases[alias] = deviceClass

    @staticmethod
    def _resolveAlias(alias):
        """
        Get a device class string from a previously registered alias. Returns the alias unchanged
        if not found.

        Parameters
        ----------
        alias : str
            Short, convenient string to refer to the class by. For example, "keyboard".

        Returns
        -------
        str
            Either the device class corresponding to the given alias, or the alias if there is none.
        """
        return DeviceManager.aliases.get(alias, alias)

    @staticmethod
    def _resolveClassString(deviceClass):
        """
        Get a `class` object from an import path string.

        Parameters
        ----------
        deviceClass : str
            Full import path for the class, in PsychoPy, of the device. For example
            `psychopy.hardware.keyboard.Keyboard`

        Returns
        -------
        type
            Class pointed to by deviceClass
        """
        if deviceClass in (None, "*"):
            # resolve "any" flags to BaseDevice
            deviceClass = "psychopy.hardware.base.BaseDevice"
        # get package and class names from deviceClass string
        parts = deviceClass.split(".")
        pkgName = ".".join(parts[:-1])
        clsName = parts[-1]
        # import package
        try:
            pkg = importlib.import_module(pkgName)
        except:
            raise ModuleNotFoundError(
                f"Could not find module: {pkgName}"
            )
        # get class
        cls = getattr(pkg, clsName)

        return cls

    # --- device management ---
    @staticmethod
    def addDevice(deviceClass, deviceName, *args, **kwargs):
        """
        Calls the add method for the specified device type

        Parameters
        ----------
        deviceClass : str
            Full import path for the class, in PsychoPy, of the device. For example
            `psychopy.hardware.keyboard.Keyboard`
        deviceName : str
            Arbitrary name to store device under.
        args : list
            Whatever arguments would be passed to the device class's init function
        kwargs : dict
            Whatever keyword arguments would be passed to the device class's init function

        Returns
        -------
        BaseDevice
            Device created by the linked class init
        """
        # if device class is an already registered alias, get the actual class str
        deviceClass = DeviceManager._resolveAlias(deviceClass)
        # get device class
        cls = DeviceManager._resolveClassString(deviceClass)
        # initialise device
        device = cls(*args, **kwargs)
        # store device by name
        DeviceManager.devices[deviceName] = device

        return device

    @staticmethod
    def addDeviceFromParams(params):
        """
        Similar to addDevice, but rather than accepting arguments and keyword arguments,
        simply accepts a dict of params. This is useful when receiving parameters from Liaison,
        communicating with a keyword-less language like JavaScript. This is relatively niche and
        in most cases addDevice will work fine.

        Parameters
        ----------
        params : dict
            Keyword arguments to be passed to DeviceManager.addDevice

        Returns
        -------
        BaseDevice
            Device created by the linked class init
        """
        return DeviceManager.addDevice(**params)

    @staticmethod
    def addDeviceAlias(deviceName, alias):
        """
        Store an already added device by an additional name

        Parameters
        ----------
        deviceName : str
            Key by which the device to alias is currently stored.
        alias
            Alias to create
        Returns
        -------
        bool
            True if completed successfully
        """
        # if given a list, call iteratively
        if isinstance(alias, (list, tuple)):
            for thisAlias in alias:
                DeviceManager.addDeviceAlias(deviceName, thisAlias)
        # store same device by new handle
        DeviceManager.devices[alias] = DeviceManager.getDevice(deviceName)

        return True

    @staticmethod
    def getDeviceAliases(deviceName):
        """
        Get all aliases by which a device is known to DeviceManager

        Parameters
        ----------
        deviceName : str
            One name by which the device is known to DeviceManager

        Returns
        -------
        list[str]
            All names by which the device is known to DeviceManager
        """
        # get device object
        obj = DeviceManager.getDevice(deviceName)
        # array to store aliases in
        aliases = []
        # iterate through devices
        for key, device in DeviceManager.devices.items():
            if device is obj:
                # append device name if it's the same device
                aliases.append(key)

        return aliases

    @staticmethod
    def updateDeviceName(oldName, newName):
        """
        Store an already added device by an additional name

        Parameters
        ----------
        oldName : str
            Key by which the device to alias is currently stored.
        newName
            Key to change to.
        Returns
        -------
        bool
            True if completed successfully
        """
        # store same device by new handle
        DeviceManager.addDeviceAlias(oldName, alias=newName)
        # remove old name
        DeviceManager.devices.pop(oldName)

        return True

    @staticmethod
    def removeDevice(deviceName):
        """
        Remove the device matching a specified device type and name.

        Parameters
        ----------
        deviceName : str
            Arbitrary name device is stored under.

        Returns
        -------
        bool
            True if completed successfully
        """
        device = DeviceManager.devices[deviceName]
        DeviceManager.clearListeners(deviceName)
        if hasattr(device, "close"):
            device.close()
        del DeviceManager.devices[deviceName]

        return True

    @staticmethod
    def getDevice(deviceName):
        """
        Get the device matching a specified device type and name.

        Parameters
        ----------
        deviceName : str
            Arbitrary name device is stored under.

        Returns
        -------
        BaseDevice
            Matching device handle
        """
        return DeviceManager.devices.get(deviceName, None)

    @staticmethod
    def hasDevice(deviceName, deviceClass="*"):
        """
        Query whether the named device exists and, if relevant, whether it is an instance of the
        expected class.

        Parameters
        ----------
        deviceName : str
            Arbitrary name device is stored under.
        deviceClass : str
            Full import path for the class, in PsychoPy, of the device. For
            example `psychopy.hardware.keyboard.Keyboard`

        Returns
        -------
        bool
            True if device exists and matches deviceClass, False otherwise
        """
        # try to get device
        device = DeviceManager.getDevice(deviceName)
        # if device is None, we don't have it
        if device is None:
            return False
        # if device class is an already registered alias, get the actual class str
        deviceClass = DeviceManager._resolveAlias(deviceClass)
        # get device class
        cls = DeviceManager._resolveClassString(deviceClass)
        # assess whether device matches class
        return isinstance(device, cls)

    @staticmethod
    def getDeviceBy(attr, value, deviceClass="*"):
        """
        Get a device by the value of a particular attribute. e.g. get a Microphone device by its
        index.

        Parameters
        ----------
        attr : str
            Name of the attribute to query each device for
        value : *
            Value which the attribute should return for the device to be a match
        deviceClass : str
            Filter search only to devices of a particular class (optional)

        Returns
        -------
        BaseDevice
            Device matching given parameters, or None if none found
        """
        # get devices by class
        devices = DeviceManager.getInitialisedDevices(deviceClass=deviceClass)
        # try each matching device
        for dev in devices.values():
            if hasattr(dev, attr):
                # if device matches attribute, return it
                if getattr(dev, attr) == value:
                    return dev

    @staticmethod
    def getInitialisedDevices(deviceClass="*"):
        """
        Get all devices of a given type which have been `add`ed to this DeviceManager

        Parameters
        ----------
        deviceClass : str
            Full import path for the class, in PsychoPy, of the device. For example
            `psychopy.hardware.keyboard.Keyboard`

        Returns
        -------
        dict[str:BaseDevice]
            Dict of devices matching requested class against their names
        """
        # if device class is an already registered alias, get the actual class str
        deviceClass = DeviceManager._resolveAlias(deviceClass)
        # get actual device class from class str
        cls = DeviceManager._resolveClassString(deviceClass)

        foundDevices = {}
        # iterate through devices and names
        for name, device in DeviceManager.devices.items():
            # add device to array if device class matches requested
            if isinstance(device, cls) or deviceClass == "*":
                foundDevices[name] = device

        return foundDevices

    @staticmethod
    def getInitialisedDeviceNames(deviceClass="*"):
        """
        Get names of all devices of a given type which have been `add`ed to this DeviceManager

        Parameters
        ----------
        deviceClass : str
            Full import path for the class, in PsychoPy, of the device. For
            example `psychopy.hardware.keyboard.Keyboard`

        Returns
        -------
        list[str]
            List of device names
        """
        return list(DeviceManager.getInitialisedDevices(deviceClass))

    @staticmethod
    def getAvailableDevices(deviceClass="*"):
        """
        Get all devices of a given type which are known by the operating system.

        Parameters
        ----------
        deviceClass : str or list
            Full import path for the class, in PsychoPy, of the device. For example
            `psychopy.hardware.keyboard.Keyboard`. If given a list, will run iteratively for all
            items in the list.

        Returns
        -------
        list[dict]
            List of dicts specifying parameters needed to initialise each device.
        """
        # if deviceClass is *, call for all types
        if deviceClass == "*":
            deviceClass = DeviceManager.deviceClasses
        # if given multiple types, call for each
        if isinstance(deviceClass, (list, tuple)):
            devices = {}
            for thisClass in deviceClass:
                try:
                    devices[thisClass] = DeviceManager.getAvailableDevices(deviceClass=thisClass)
                except NotImplementedError:
                    # ignore any NotImplementedErrors
                    pass
            return devices

        # if device class is an already registered alias, get the actual class str
        deviceClass = DeviceManager._resolveAlias(deviceClass)
        # get device class
        cls = DeviceManager._resolveClassString(deviceClass)
        # make sure cass has a getAvailableDevices method
        assert hasattr(cls, "getAvailableDevices"), (
            f"Could not get available devices of type `{deviceClass}` as device class does not "
            f"have a `getAvailableDevices` method."
        )
        # use class method
        devices = []
        for profile in cls.getAvailableDevices():
            # add device class
            profile['deviceClass'] = deviceClass
            # append
            devices.append(profile)

        return devices

    @staticmethod
    def closeAll():
        """Close all devices.

        Close all devices that have been initialized. This is usually called on exit to free
        resources cleanly. It is not necessary to call this method manually as it is registered
        as an `atexit` handler.

        The device manager will be reset after this method is called.

        Returns
        -------
        bool
            True if completed successfully

        """
        # iterate through devices
        for name, device in DeviceManager.devices.items():
            # if it has a close method, call it
            if hasattr(device, "close"):
                device.close()
        # delete devices
        DeviceManager.devices = {}

        return True

    @staticmethod
    def callDeviceMethod(deviceName, method, *args, **kwargs):
        """
        Call the method of a known device and return its output.

        Parameters
        ----------
        deviceName : str
            Arbitrary name device is stored under.
        method : str
            Name of the method to run.
        args : list
            Whatever arguments would be passed to the method
        kwargs : dict
            Whatever keyword arguments would be passed to the method

        Returns
        -------
        *
            The output of the requested function
        """
        # get device
        device = DeviceManager.getDevice(deviceName)
        # call method
        return getattr(device, method)(*args, **kwargs)

    @staticmethod
    def addListener(deviceName, listener, startLoop=False):
        """
        Add a listener to a managed device.

        Parameters
        ----------
        deviceName : str
            Name of the device to add a listener to
        listener : str or psychopy.hardware.listener.BaseListener
            Either a Listener object, or use one of the following strings to create one:
            - "liaison": Create a LiaisonListener with self.liaison as the server
            - "print": Create a PrintListener with default settings
            - "log": Create a LoggingListener with default settings
        startLoop : bool
            If True, then upon adding the listener, start up an asynchronous loop to dispatch
            messages.

        Returns
        -------
        BaseListener
            Listener created/added
        """
        # get device
        device = DeviceManager.getDevice(deviceName)
        # add listener to device
        if hasattr(device, "addListener"):
            listener = device.addListener(listener, startLoop=startLoop)
        else:
            raise AttributeError(
                f"Could not add a listener to device {deviceName} ({type(device).__name__}) as it "
                f"does not have an `addListener` method."
            )

        return listener

    @staticmethod
    def clearListeners(deviceName):
        """
        Remove any listeners attached to a particular device.

        Parameters
        ----------
        deviceName : str
            Name of the device to remove listeners from

        Returns
        -------
        bool
            True if completed successfully
        """
        # get device
        device = DeviceManager.getDevice(deviceName)
        # add listener to device
        if hasattr(device, "clearListeners"):
            device.clearListeners()

        return True

    @staticmethod
    def getResponseParams(deviceClass="*"):
        """
        Get the necessary params for initialising a response for the given device.

        Parameters
        ----------
        deviceClass : str
            Full import path for the class, in PsychoPy, of the device. For example
            `psychopy.hardware.keyboard.Keyboard`. Use "*" to get for all currently imported
            classes.

        Returns
        -------
        list[str]
            List of param names for the given device's response object
        OR
        dict[str:list[str]]
            Lists of param names for all devices' response objects, in a dict against device class
            strings
        """
        from psychopy.hardware.base import BaseResponseDevice, BaseDevice

        if deviceClass == "*":
            # if deviceClass is *, call for all types
            params = {}
            for deviceClass in DeviceManager.deviceClasses:
                # skip base classes
                if deviceClass in (BaseResponseDevice, BaseDevice):
                    continue
                params[deviceClass] = DeviceManager.getResponseParams(deviceClass)
            return params

        # resolve class string
        deviceClass = DeviceManager._resolveAlias(deviceClass)
        deviceClass = DeviceManager._resolveClassString(deviceClass)
        # if device isn't a ResponseDevice, return None
        if not issubclass(deviceClass, BaseResponseDevice):
            return
        # use inspect to get input params of response class
        args = list(deviceClass.responseClass.__init__.__code__.co_varnames)
        # remove "self" arg
        if "self" in args:
            args.remove("self")

        return args

    @staticmethod
    def getScreenCount():
        """
        Get the number of currently connected screens

        Returns
        -------
        int
            Number of screens
        """
        import pyglet
        # get screens
        display = pyglet.canvas.Display()
        allScrs = display.get_screens()

        return len(allScrs)

    @staticmethod
    def showScreenNumbers(dur=5):
        """
        Spawn some PsychoPy windows to display each monitor's number.

        Parameters
        ----------
        dur : float, int
            How many seconds to show each window for
        """
        from psychopy import visual
        import time

        # make a window on each screen showing the screen number
        wins = []
        lbls = []
        bars = []
        for n in range(DeviceManager.getScreenCount()):
            # create a window on the appropriate screen
            win = visual.Window(
                pos=(0, 0),
                size=(128, 128),
                units="norm",
                screen=n,
                color="black",
                checkTiming=False
            )
            wins.append(win)
            # create textbox with screen num
            lbl = visual.TextBox2(
                win, text=str(n + 1),
                size=1, pos=0,
                alignment="center", anchor="center",
                letterHeight=0.5, bold=True,
                fillColor=None, color="white"
            )
            lbls.append(lbl)
            # progress bar to countdown dur
            bar = visual.Rect(
                win, anchor="bottom left",
                pos=(-1, -1), size=(0, 0.1),
                fillColor='white'
            )
            bars.append(bar)

            # start a frame loop
            start = time.time()
            t = 0
            while t < dur:
                t = time.time() - start
                # update progress bar
                bar.size = (t / 5 * 2, 0.1)
                # draw
                bar.draw()
                lbl.draw()
                # flip
                win.flip()

            # close window
            win.close()


# handle to the device manager, which is a singleton
deviceManager = DeviceManager()


def getDeviceManager():
    """Get the device manager.

    Returns an instance of the device manager.

    Returns
    -------
    DeviceManager
        The device manager.

    """
    global deviceManager
    if deviceManager is None:
        deviceManager = DeviceManager()  # initialize

    return deviceManager


def closeAllDevices():
    """Close all devices.

    Close all devices that have been initialized. This is usually called on exit to free
    resources cleanly. It is not necessary to call this method manually as it's registed as an
    `atexit` handler.

    """
    devMgr = getDeviceManager()
    if devMgr is not None:
        devMgr.closeAll()


# register closeAllDevices as an atexit handler
atexit.register(closeAllDevices)


if __name__ == "__main__":
    pass
