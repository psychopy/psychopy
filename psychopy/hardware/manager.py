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

    An instance of this class is used to manage various hardware peripherals 
    used by PsychoPy. It can be used to access devices such as microphones, 
    button boxes, and cameras though a common interface. It can also be used to 
    get information about available devices installed on the system, such as 
    their settings and capabilities prior to initializing them.
    
    It is recommended that devices are initialized through the device manager
    rather than directly. The device manager is responsible for keeping track
    of devices and ensuring that they are properly closed when the program
    exits. 

    This class is implemented as a singleton, so there is only one
    instance of it per ssession after its initialized. The instance can be 
    accessed through the global variable `deviceManager` or by calling 
    `getDeviceManager()`.

    Any subclass of BaseDevice is added to DeviceManager's `.deviceClasses`
    list upon import, so devices matching that class become available through
    `DeviceManager.getAvailableDevices("*")`.

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
        # store/update ref to liaison
        if liaison is not None or not hasattr(cls._instance, "liaison"):
            cls._instance.liaison = liaison

        return cls._instance

    # --- utility ---

    def _getSerialPortsInUse(self):
        """Get serial ports that are being used and the names of the devices
        that are using them.

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
    def registerAlias(alias, deviceClass):
        """
        Register an alias to rever to a particular class, for convenience.

        Parameters
        ----------
        alias : str
            Short, convenient string to refer to the class by. For example, "keyboard".
        deviceClass : str
            Full import path for the class, in PsychoPy, of the device. For example `psychopy.hardware.keyboard.Keyboard`
        """
        # if device class is an already registered alias, get the actual class str
        deviceClass = DeviceManager._resolveAlias(deviceClass)
        # register alias
        DeviceManager.aliases[alias] = deviceClass

    @staticmethod
    def _resolveAlias(alias):
        """
        Get a device class string from a previously registered alias. Returns the alias unchanged if
        not found.

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
            Full import path for the class, in PsychoPy, of the device. For example `psychopy.hardware.keyboard.Keyboard`

        Returns
        -------
        type
            Class pointed to by deviceClass
        """
        # get package and class names from deviceClass string
        parts = deviceClass.split(".")
        pkgName = ".".join(parts[:-1])
        clsName = parts[-1]
        # import package
        pkg = importlib.import_module(pkgName)
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
            Full import path for the class, in PsychoPy, of the device. For example `psychopy.hardware.keyboard.Keyboard`
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
        Similar to addDevice, but rather than accepting arguments and keyword arguments, simply accepts a dict of
        params. This is useful when receiving parameters from Liaison, communicating with a keyword-less language like
        JavaScript. This is relatively niche and in most cases addDevice will work fine.

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
    def getDeviceBy(attr, value, deviceClass="*"):
        """
        Get a device by the value of a particular attribute. e.g. get a Microphone device by its index.

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
        for dev in devices:
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
            Full import path for the class, in PsychoPy, of the device. For example `psychopy.hardware.keyboard.Keyboard`

        Returns
        -------
        list[BaseDevice]
            List of devices matching requested class
        """
        # if device class is an already registered alias, get the actual class str
        deviceClass = DeviceManager._resolveAlias(deviceClass)

        foundDevices = {}
        # iterate through devices and names
        for name, device in DeviceManager.devices.items():
            # get class name for this device
            thisDeviceClass = ".".join((type(device).__module__, type(device).__qualname__))
            # add device to array if device class matches requested
            if deviceClass in (thisDeviceClass, "*"):
                foundDevices[name] = device

        return foundDevices

    @staticmethod
    def getAvailableDevices(deviceClass="*"):
        """
        Get all devices of a given type which are known by the operating system.

        Parameters
        ----------
        deviceClass : str or list
            Full import path for the class, in PsychoPy, of the device. For example
            `psychopy.hardware.keyboard.Keyboard`. If given a list, will run iteratively for all items in the list.

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
            f"Could not get available devices of type `{deviceClass}` as device class does not have a "
            f"`getAvailableDevices` method."
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

        Close all devices that have been initialized. This is usually called on
        exit to free resources cleanly. It is not necessary to call this method
        manually as it is registered as an `atexit` handler.

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

    def addListener(self, deviceName, listener):
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

        Returns
        -------
        BaseListener
            Listener created/added
        """
        from psychopy.hardware import listener as lsnr
        # get device
        device = self.getDevice(deviceName)
        # make listener if needed
        if not isinstance(listener, lsnr.BaseListener):
            if listener == "liaison":
                if self.liaison is None:
                    raise AttributeError(
                        "Cannot create a `liaison` listener as no liaison server is connected to DeviceManager."
                    )
                listener = lsnr.LiaisonListener(self.liaison)
            if listener == "print":
                listener = lsnr.PrintListener()
            if listener == "log":
                listener = lsnr.LoggingListener()
        # add listener to device
        if hasattr(device, "addListener"):
            device.addListener(listener)
        else:
            raise AttributeError(
                f"Could not add a listener to device {deviceName} ({type(device).__name__}) as it does not "
                f"have an `addListener` method."
            )

        return listener
            
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

    Close all devices that have been initialized. This is usually called on
    exit to free resources cleanly. It is not necessary to call this method
    manually as it's registed as an `atexit` handler.

    """
    devMgr = getDeviceManager()
    if devMgr is not None:
        devMgr.closeAll()


# register closeAllDevices as an atexit handler
atexit.register(closeAllDevices)


if __name__ == "__main__":
    pass
